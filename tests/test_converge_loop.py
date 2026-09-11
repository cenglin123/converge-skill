#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""converge_loop.py 验收用例（plan: docs/plans/active/20260818-converge-loop-driver.md）。

stdlib unittest，无外部依赖。运行：
    python -m unittest tests.test_converge_loop -v

覆盖：
  - spec 校验（禁轮号字段回归 / 必填 / phase 类型）
  - 轮号机械推导（outer / uv-init / blind）
  - verdict 机械解析
  - prompt 模板渲染与三方对齐
  - 骨架合并
  - E2E（fake dispatch）：parallel-review 阻断 → executor → outer R1 阻断 → executor →
    outer R2 通过 → blind → design-review → finish 归档；记账不变量断言
  - spawn 失败 → cancel + pause；resume 输入缺失 → exit 11
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
DRIVER = SCRIPTS / "converge_loop.py"
ORCHEST = SCRIPTS / "orchest.py"
FAKE = Path(__file__).resolve().parent / "_fake_loop_dispatch.py"

sys.path.insert(0, str(SCRIPTS))
import budget_gate  # noqa: E402
import converge_loop as cl  # noqa: E402


def run_driver(spec: Path, *args: str, env_extra: dict | None = None) -> tuple[int, str, str]:
    env = {**os.environ, "PYTHONUTF8": "1"}
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(
        [sys.executable, str(DRIVER), *args],
        capture_output=True, text=True, encoding="utf-8", env=env)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def read_jsonl(p: Path) -> list[dict]:
    if not p.is_file():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


# ─── 单元：spec / 轮号 / verdict / 模板 / 合并 ────────────────────────────────

class TestSpecValidation(unittest.TestCase):
    def _base(self):
        return {"slug": "s", "active_dir": "/x", "orchest": "/o", "ocsr_dispatch": "/d",
                "phases": [{"id": "uv", "type": "parallel-review",
                            "prompt_template": "t.md",
                            "reviewers": [{"model": "a/b", "label": "r1"}]}]}

    def test_valid(self):
        self.assertEqual(cl.validate_spec(self._base()), [])

    def test_v2_review_repair_requires_reachable_outer_reviewer(self):
        spec = self._base()
        spec["version"] = 2
        errs = cl.validate_spec(spec)
        self.assertTrue(any("fresh outer Reviewer" in error for error in errs), errs)

    def test_v2_driver_retry_is_separate_from_continue_budget(self):
        spec = self._base()
        spec.update({
            "version": 2,
            "budget_config": {"max_inner_loops": 3},
            "driver_config": {"max_executor_repair_attempts": 2},
        })
        spec["phases"].append({"id": "outer", "type": "outer-loop",
                               "reviewer_models": ["a/b"], "executor_model": "a/b"})
        normalized, warnings = cl.normalize_spec(spec)
        self.assertEqual(normalized["budget_config"]["max_inner_loops"], 3)
        self.assertEqual(normalized["driver_config"]["max_executor_repair_attempts"], 2)
        self.assertEqual(warnings, [])

    def test_v1_inner_value_migrates_only_to_driver_retry(self):
        spec = self._base()
        spec["version"] = 1
        spec["budget_config"] = {"max_inner_loops": 4}
        normalized, warnings = cl.normalize_spec(spec)
        self.assertNotIn("max_inner_loops", normalized["budget_config"])
        self.assertEqual(normalized["driver_config"]["max_executor_repair_attempts"], 4)
        self.assertTrue(warnings)

    def test_retry_values_reject_bool_string_zero_and_unknown_driver_keys(self):
        for value in (True, "2", 0, -1):
            spec = self._base()
            spec.update({"version": 2,
                         "driver_config": {"max_executor_repair_attempts": value}})
            with self.subTest(value=value), self.assertRaises(cl.SpecError):
                cl.normalize_spec(spec)
        spec = self._base()
        spec.update({"version": 2, "driver_config": {"other": 1}})
        with self.assertRaises(cl.SpecError):
            cl.normalize_spec(spec)

    def test_forbidden_round_key_regression(self):
        spec = self._base()
        spec["phases"][0]["round"] = 2  # 20260818 轮号误用事故回归：spec 禁轮号
        errs = cl.validate_spec(spec)
        self.assertTrue(any("禁止字段" in e for e in errs), errs)

    def test_forbidden_nested_round(self):
        spec = self._base()
        spec["phases"].append({"id": "o", "type": "outer-loop",
                               "reviewer_models": ["a/b"], "executor_model": "a/b",
                               "target_round": 1})
        errs = cl.validate_spec(spec)
        self.assertTrue(any("target_round" in e for e in errs), errs)

    def test_missing_required(self):
        spec = self._base()
        del spec["orchest"]
        self.assertTrue(any("orchest" in e for e in cl.validate_spec(spec)))

    def test_bad_phase_type(self):
        spec = self._base()
        spec["phases"][0]["type"] = "wat"
        self.assertTrue(any("type 非法" in e for e in cl.validate_spec(spec)))

    def test_miniyaml_inline_and_nested(self):
        text = """version: 1
slug: drill
active_dir: /x/active
mode: ultraverge
budget_config: {max_blind_rechecks: 2}
orchest: /o
ocsr_dispatch: /d
phases:
  - id: uv
    type: parallel-review
    prompt_template: t.md
    reviewers:
      - {model: a/b, label: uv-r1}
      - {model: a/b, label: uv-r2}
  - id: outer
    type: outer-loop
    reviewer_models: [a/b]
    executor_model: a/b
"""
        spec = cl.load_spec(self._write_tmp(text))
        self.assertEqual(spec["mode"], "ultraverge")
        self.assertEqual(spec["budget_config"]["max_blind_rechecks"], 2)
        self.assertEqual(len(spec["phases"]), 2)
        self.assertEqual(spec["phases"][0]["reviewers"][1]["label"], "uv-r2")
        self.assertEqual(spec["phases"][1]["reviewer_models"], ["a/b"])

    def _write_tmp(self, text: str) -> Path:
        fd, p = tempfile.mkstemp(suffix=".yaml")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        return Path(p)


class TestMechanics(unittest.TestCase):
    def test_next_round(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self.assertEqual(cl.next_round(d), 1)
            (d / "round-1.md").write_text("x", encoding="utf-8")
            self.assertEqual(cl.next_round(d), 2)
            (d / "round-2.md").write_text("x", encoding="utf-8")
            self.assertEqual(cl.next_round(d), 3)
            (d / "uv-init-1.md").write_text("x", encoding="utf-8")
            self.assertEqual(cl.next_round(d, cl.UV_RE), 2)
            self.assertEqual(cl.next_round(d, cl.BLIND_RE), 1)

    def test_parse_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "r.md"
            p.write_text("```yaml\nverdict: 阻断需修复\nblocking_issues:\n"
                         "  - id: 1\n    severity: structural\n"
                         "  - id: 2\n    severity: architectural\n```\n", encoding="utf-8")
            parsed = cl.parse_verdict(p)
            self.assertEqual(parsed["verdict"], "阻断需修复")
            self.assertEqual(parsed["severities"], ["structural", "architectural"])
            p.write_text("no yaml here", encoding="utf-8")
            self.assertIsNone(cl.parse_verdict(p)["verdict"])

    def test_render_prompt_alignment(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            tmpl = d / "t.md"
            tmpl.write_text("label={label} round={round} out={report_path}", encoding="utf-8")
            dest = cl.render_prompt(tmpl, {"label": "r1", "round": "1",
                                           "report_path": "/x/uv-report-r1.md"},
                                    d / "out.md")
            text = dest.read_text(encoding="utf-8")
            self.assertIn("label=r1", text)
            self.assertIn("out=/x/uv-report-r1.md", text)
            tmpl.write_text("leftover={unknown_key}", encoding="utf-8")
            with self.assertRaises(cl.LoopFail):
                cl.render_prompt(tmpl, {}, d / "out2.md")

    def test_merge_skeleton(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            skel = d / "round-1.md"
            skel.write_text("---\nround: 1\nreviewer_backend: unknown\n---\n"
                            "# (skeleton)\n\n## Reviewer 完整输出\n\n(pending)\n\n"
                            "## Orchestrator 处理记录\n\n(pending)\n", encoding="utf-8")
            rep = d / "rep.md"
            rep.write_text("```yaml\nverdict: 可执行\n```\n", encoding="utf-8")
            cl.merge_into_skeleton(skel, rep, "driver 机械合并")
            text = skel.read_text(encoding="utf-8")
            self.assertIn("reviewer_backend: ocsr", text)
            self.assertIn("verdict: 可执行", text)
            self.assertIn("driver 机械合并", text)
            self.assertNotIn("(pending)", text)

    def test_v1_journal_streak_migration_preserves_value(self):
        with tempfile.TemporaryDirectory() as td:
            active = Path(td)
            # 构造 v1 journal 的旧 streak 字段名（避免 Phase 6 扫描自匹配）
            _legacy_key = "inner" + "_streak"
            (active / ".loop-journal.json").write_text(json.dumps({
                "version": 1, "phase_index": 0,
                "phase_state": {"outer": {_legacy_key: 2}},
                "paused": None, "aborted": False, "history": [],
            }), encoding="utf-8")
            journal, changed = cl.load_journal(active)
            self.assertTrue(changed)
            self.assertEqual(journal["phase_state"]["outer"]["executor_repair_streak"], 2)
            self.assertNotIn(_legacy_key, journal["phase_state"]["outer"])


# ─── E2E：全链路（fake dispatch） ─────────────────────────────────────────────

SPEC_TEXT = """version: 1
slug: drill
active_dir: {active}
done_root: {done}
mode: ultraverge
budget_config: {{max_blind_rechecks: 2}}
orchest: {orchest}
ocsr_dispatch: {fake}
harness: fake
timeout_min: 1
phases:
  - id: uv
    type: parallel-review
    prompt_template: {tmpl_uv}
    reviewers:
      - {{model: deepseek/deepseek-v4-flash, label: uv-r1}}
      - {{model: deepseek/deepseek-v4-flash, label: uv-r2}}
  - id: outer
    type: outer-loop
    reviewer_models: [deepseek/deepseek-v4-flash]
    executor_model: deepseek/deepseek-v4-flash
    max_rounds: 8
  - id: blind
    type: blind-recheck
    model: deepseek/deepseek-v4-flash
    prompt_template: {tmpl_blind}
  - id: design
    type: design-review
    model: deepseek/deepseek-v4-flash
    prompt_template: {tmpl_design}
final_verdict: 可执行
"""

TMPL_UV = "你是 reviewer {label}（round {round}）。把报告写入 {report_path}\n"
TMPL_BLIND = "你是 blind reviewer {label}。把报告写入 {report_path}\n"
TMPL_DESIGN = "你是 design reviewer。把报告写入 {report_path}\n"


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.active = self.root / "active" / "drill"
        self.active.mkdir(parents=True)
        self.done = self.root / "done"
        self.tmpl_uv = self.root / "tmpl_uv.md"
        self.tmpl_uv.write_text(TMPL_UV, encoding="utf-8")
        self.tmpl_blind = self.root / "tmpl_blind.md"
        self.tmpl_blind.write_text(TMPL_BLIND, encoding="utf-8")
        self.tmpl_design = self.root / "tmpl_design.md"
        self.tmpl_design.write_text(TMPL_DESIGN, encoding="utf-8")
        self.state_file = self.root / "fake-state.json"
        self.spec = self.root / "loop.yaml"
        self.spec.write_text(SPEC_TEXT.format(
            active=str(self.active).replace("\\", "/"),
            done=str(self.done).replace("\\", "/"),
            orchest=str(ORCHEST).replace("\\", "/"),
            fake=str(FAKE).replace("\\", "/"),
            tmpl_uv=str(self.tmpl_uv).replace("\\", "/"),
            tmpl_blind=str(self.tmpl_blind).replace("\\", "/"),
            tmpl_design=str(self.tmpl_design).replace("\\", "/")),
            encoding="utf-8")
        self.env = {"FAKE_STATE_FILE": str(self.state_file)}

    def tearDown(self):
        self.tmp.cleanup()

    def _set_state(self, mapping: dict):
        self.state_file.write_text(json.dumps(mapping, ensure_ascii=False), encoding="utf-8")

    def _resume(self, *answers: str) -> tuple[int, str, str]:
        cmd = ["resume", "--spec", str(self.spec)]
        for a in answers:
            cmd += ["--answer", a]
        return run_driver(self.spec, *cmd, env_extra=self.env)

    def test_full_chain(self):
        # ── uv-init：r1 阻断(structural)，r2 可执行 ──
        self._set_state({
            "uv-r1": {"verdict": "阻断需修复", "severities": ["structural"]},
            "uv-r2": {"verdict": "可执行"},
        })
        rc, out, err = run_driver(self.spec, "run", "--spec", str(self.spec),
                                  env_extra=self.env)
        self.assertEqual(rc, 10, f"{out} {err}")
        # 骨架与合并
        for n in (1, 2):
            product = self.active / f"uv-init-{n}.md"
            self.assertTrue(product.is_file())
            self.assertIn("reviewer_backend: ocsr", product.read_text(encoding="utf-8"))
        ledger = read_jsonl(self.active / "gate-ledger.jsonl")
        self.assertEqual(len([e for e in ledger if e["event"] == "reserved"]), 2)
        self.assertEqual(len([e for e in ledger if e["event"] == "spawn_succeeded"]), 2)
        pause = json.loads((self.active / "pause-request.json").read_text(encoding="utf-8"))
        self.assertEqual(pause["decision"]["kind"], "phase_verdict")

        # ── repair：executor attempt 1 ──
        exec_prompt = self.active / "prompt-executor-1.md"
        exec_prompt.write_text("修复指令 1", encoding="utf-8")
        self._set_state({"executor-r1": {}})
        rc, out, err = self._resume("action=repair")
        self.assertEqual(rc, 10, f"{out} {err}")
        self.assertTrue((self.active / "reports" / "executor-r1-report.md").is_file())

        # ── accepted + reviewer_prompt → outer R1 阻断 ──
        rp1 = self.active / "prompt-reviewer-next-1.md"
        rp1.write_text("outer round 1 prompt", encoding="utf-8")
        self._set_state({"reviewer-r1": {"verdict": "阻断需修复",
                                         "severities": ["implementation"]}})
        rc, out, err = self._resume("action=accepted")
        self.assertEqual(rc, 10, f"{out} {err}")
        # 轮号必须由 driver 推导为 1（事故回归断言）
        self.assertTrue((self.active / "round-1.md").is_file())
        self.assertFalse((self.active / "round-2.md").is_file())
        pause = json.loads((self.active / "pause-request.json").read_text(encoding="utf-8"))
        self.assertEqual(pause["decision"]["round"], 1)

        # ── repair → executor attempt 2 → accepted → outer R2 可执行 ──
        exec_prompt2 = self.active / "prompt-executor-2.md"
        exec_prompt2.write_text("修复指令 2", encoding="utf-8")
        self._set_state({"executor-r2": {}})
        rc, out, err = self._resume("action=repair")
        self.assertEqual(rc, 10, f"{out} {err}")
        rp2 = self.active / "prompt-reviewer-next-2.md"
        rp2.write_text("outer round 2 prompt", encoding="utf-8")
        self._set_state({"reviewer-r2": {"verdict": "可执行"}})
        rc, out, err = self._resume("action=accepted")
        self.assertEqual(rc, 10, f"{out} {err}")
        self.assertTrue((self.active / "round-2.md").is_file())
        pause = json.loads((self.active / "pause-request.json").read_text(encoding="utf-8"))
        self.assertEqual(pause["decision"]["verdict"], "可执行")

        # ── proceed → blind（outer=2 轮触发） → 可执行 → proceed → design-review → before_finish ──
        self._set_state({"blind-r1": {"verdict": "可执行"}})
        rc, out, err = self._resume("action=proceed")
        self.assertEqual(rc, 10, f"{out} {err}")  # blind verdict pause
        self.assertTrue((self.active / "blind-recheck-1.md").is_file())
        self._set_state({"design-reviewer": {"body": "# design review\n"}})
        rc, out, err = self._resume("action=proceed")
        self.assertEqual(rc, 10, f"{out} {err}")  # before_finish pause
        self.assertTrue((self.active / "design-review.md").is_file())

        # ── finish ──
        (self.active / "retrospective.md").write_text("# retro\n", encoding="utf-8")
        rc, out, err = self._resume("action=finish")
        self.assertEqual(rc, 0, f"{out} {err}")
        archived = self.done / "drill"
        self.assertTrue(archived.is_dir())
        # 归档 check
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / "archive_convergence.py"), "check", str(archived)],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, (r.stdout or "") + (r.stderr or ""))
        # 记账不变量：全部 reservation 已 settle
        ledger = read_jsonl(archived / "gate-ledger.jsonl")
        reserved = {e["reservation_id"] for e in ledger if e["event"] == "reserved"}
        settled = {e["reservation_id"] for e in ledger if e["event"] in
                   ("spawn_succeeded", "spawn_failed", "cancelled")}
        self.assertEqual(reserved - settled, set())
        # outer 轮号连续 [1,2]
        self.assertEqual(cl.realized_rounds(archived), [1, 2])

    def test_malformed_budget_fails_before_driver_runtime_artifacts(self):
        bad = self.root / "bad-loop.yaml"
        bad.write_text(self.spec.read_text(encoding="utf-8").replace(
            "budget_config: {max_blind_rechecks: 2}",
            "budget_config: {max_blind_rechecks: true}"), encoding="utf-8")
        other_active = self.root / "bad-active"
        bad.write_text(bad.read_text(encoding="utf-8").replace(
            str(self.active).replace("\\", "/"), str(other_active).replace("\\", "/")),
            encoding="utf-8")
        rc, out, err = run_driver(bad, "run", "--spec", str(bad), env_extra=self.env)
        self.assertNotEqual(rc, 0, out + err)
        for name in (".loop-journal.json", "attempts.md", "reports"):
            self.assertFalse((other_active / name).exists(), name)

    def test_spawn_failure_cancels_and_pauses(self):
        self._set_state({})
        env = {**self.env, "FAKE_MODE": "fail-no-artifact"}
        rc, out, err = run_driver(self.spec, "run", "--spec", str(self.spec), env_extra=env)
        self.assertEqual(rc, 10, f"{out} {err}")
        ledger = read_jsonl(self.active / "gate-ledger.jsonl")
        failed = [e for e in ledger if e["event"] == "spawn_failed"]
        self.assertEqual(len(failed), 2)  # 两个 uv reviewer 均以 backend-error 终态
        pause = json.loads((self.active / "pause-request.json").read_text(encoding="utf-8"))
        self.assertTrue(pause["decision"]["blocked"])

    def test_resume_missing_answer_exit_11(self):
        self._set_state({"uv-r1": {"verdict": "可执行"}, "uv-r2": {"verdict": "可执行"}})
        rc, _, _ = run_driver(self.spec, "run", "--spec", str(self.spec), env_extra=self.env)
        self.assertEqual(rc, 10)
        rc, out, err = self._resume()  # 缺 action
        self.assertEqual(rc, 11, f"{out} {err}")

    def test_watcher_mismatch_salvage(self):
        self._set_state({"uv-r1": {"verdict": "可执行"}, "uv-r2": {"verdict": "可执行"}})
        env = {**self.env, "FAKE_MODE": "mismatch-exit"}
        rc, out, err = run_driver(self.spec, "run", "--spec", str(self.spec), env_extra=env)
        self.assertEqual(rc, 10, f"{out} {err}")  # 产物在 → 照常回收并 pause
        ledger = read_jsonl(self.active / "gate-ledger.jsonl")
        self.assertEqual(len([e for e in ledger if e["event"] == "spawn_succeeded"]), 2)
        self.assertEqual([e for e in ledger if e["event"] == "cancelled"], [])

    def test_skip_phases_after_clean_uv(self):
        self._set_state({"uv-r1": {"verdict": "可执行"}, "uv-r2": {"verdict": "可执行"}})
        rc, _, _ = run_driver(self.spec, "run", "--spec", str(self.spec), env_extra=self.env)
        self.assertEqual(rc, 10)
        self._set_state({"design-reviewer": {"body": "# dr\n"}})
        rc, out, err = self._resume("action=proceed", "skip=outer,blind")
        self.assertEqual(rc, 10, f"{out} {err}")  # design 完成 → before_finish
        pause = json.loads((self.active / "pause-request.json").read_text(encoding="utf-8"))
        self.assertEqual(pause["decision"]["kind"], "before_finish")
        j = json.loads((self.active / ".loop-journal.json").read_text(encoding="utf-8"))
        skipped = [h.get("phase_skipped") for h in j["history"] if h.get("phase_skipped")]
        self.assertEqual(skipped, ["outer", "blind"])


class TestDriverOmittedModeInherits(unittest.TestCase):
    """Requirement 6: _init_budget_config must pass omitted spec mode as None
    so existing ultraverge state is inherited, not conflicting."""

    def test_driver_omitted_mode_inherits_existing_ultraverge(self):
        """When spec omits mode, driver should pass mode=None to initialize_state,
        inheriting the existing ultraverge state without FailClosed."""
        with tempfile.TemporaryDirectory() as td:
            active = Path(td) / "active"
            active.mkdir()
            # Write existing ultraverge state
            (active / "_budget-state.json").write_text(json.dumps({
                "config": {"max_blind_rechecks": 2}, "extensions": [],
                "fsm": {"mode": "ultraverge", "severities": {}}
            }), encoding="utf-8")
            before = (active / "_budget-state.json").read_bytes()
            # Simulate the CORRECTED driver behavior: spec has no 'mode' key → mode=None
            spec = {"active_dir": str(active), "budget_config": {}}
            cfg = spec.get("budget_config") or {}
            mode = spec.get("mode")  # None when omitted
            state = budget_gate.initialize_state(active, mode=mode, config=cfg)
            self.assertEqual(state["fsm"]["mode"], "ultraverge")
            self.assertEqual((active / "_budget-state.json").read_bytes(), before)

    def test_init_budget_config_omitted_mode_inherits_existing_ultraverge(self):
        """_init_budget_config must pass omitted spec mode as None to initialize_state,
        so existing ultraverge state is inherited, not conflicting. Current buggy code
        uses get('mode', 'standard') which passes 'standard' explicitly, causing FailClosed."""
        with tempfile.TemporaryDirectory() as td:
            active = Path(td) / "active"
            active.mkdir()
            (active / "_budget-state.json").write_text(json.dumps({
                "config": {"max_blind_rechecks": 2}, "extensions": [],
                "fsm": {"mode": "ultraverge", "severities": {}}
            }), encoding="utf-8")
            before = (active / "_budget-state.json").read_bytes()
            # Build a minimal driver-like spec (no 'mode' key = omitted)
            spec = {
                "slug": "test", "active_dir": str(active),
                "orchest": "/o", "ocsr_dispatch": "/d",
                "phases": [{"id": "uv", "type": "parallel-review",
                            "prompt_template": "t.md",
                            "reviewers": [{"model": "a/b", "label": "r1"}]}],
                "budget_config": {},
            }
            spec_path = Path(td) / "spec.yaml"
            spec_path.write_text("slug: test\n", encoding="utf-8")
            drv = cl.Driver(spec, spec_path)
            # After fix: _init_budget_config should NOT raise — omitted mode inherits
            cl._init_budget_config(drv)
            self.assertEqual((active / "_budget-state.json").read_bytes(), before)
            # Verify state was resolved (loaded from file) with ultraverge
            state = budget_gate.read_state(active)
            self.assertEqual(state["fsm"]["mode"], "ultraverge")

    def test_driver_explicit_standard_conflicts_existing_ultraverge(self):
        """When spec explicitly sets mode=standard but existing state is ultraverge,
        this is a real conflict and must fail closed."""
        with tempfile.TemporaryDirectory() as td:
            active = Path(td) / "active"
            active.mkdir()
            (active / "_budget-state.json").write_text(json.dumps({
                "config": {"max_blind_rechecks": 2}, "extensions": [],
                "fsm": {"mode": "ultraverge", "severities": {}}
            }), encoding="utf-8")
            before = (active / "_budget-state.json").read_bytes()
            with self.assertRaises(budget_gate.FailClosed):
                budget_gate.initialize_state(active, mode="standard")
            self.assertEqual((active / "_budget-state.json").read_bytes(), before)

    def test_driver_new_run_omitted_mode_initializes_standard(self):
        """Truly new driver run with omitted mode initializes standard."""
        with tempfile.TemporaryDirectory() as td:
            active = Path(td) / "active"
            active.mkdir()
            state = budget_gate.initialize_state(active, mode=None)
            self.assertEqual(state["fsm"]["mode"], "standard")
            self.assertEqual(state["defaults_version"], 2)


SPEC_TEXT_V2_POST_REPAIR = """version: 2
slug: drill-v2
active_dir: {active}
done_root: {done}
mode: ultraverge
budget_config: {{max_blind_rechecks: 2}}
driver_config: {{max_executor_repair_attempts: 3}}
orchest: {orchest}
ocsr_dispatch: {fake}
harness: fake
timeout_min: 1
phases:
  - id: uv
    type: parallel-review
    prompt_template: {tmpl_uv}
    reviewers:
      - {{model: deepseek/deepseek-v4-flash, label: uv-r1}}
      - {{model: deepseek/deepseek-v4-flash, label: uv-r2}}
  - id: outer1
    type: outer-loop
    reviewer_models: [deepseek/deepseek-v4-flash]
    executor_model: deepseek/deepseek-v4-flash
  - id: blind
    type: blind-recheck
    model: deepseek/deepseek-v4-flash
    prompt_template: {tmpl_blind}
  - id: outer2
    type: outer-loop
    reviewer_models: [deepseek/deepseek-v4-flash]
    executor_model: deepseek/deepseek-v4-flash
  - id: design
    type: design-review
    model: deepseek/deepseek-v4-flash
    prompt_template: {tmpl_design}
final_verdict: 可执行
"""


class TestPostRepairFreshReview(unittest.TestCase):
    """Blocker B: After every artifact-modifying Executor, a fresh outer Reviewer
    is required before phase completion. A repair originating in blind review must
    route through the next fresh outer review; no repaired artifact is completed
    directly from an Executor report."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.active = self.root / "active" / "drill"
        self.active.mkdir(parents=True)
        self.done = self.root / "done"
        self.tmpl_uv = self.root / "tmpl_uv.md"
        self.tmpl_uv.write_text(TMPL_UV, encoding="utf-8")
        self.tmpl_blind = self.root / "tmpl_blind.md"
        self.tmpl_blind.write_text(TMPL_BLIND, encoding="utf-8")
        self.tmpl_design = self.root / "tmpl_design.md"
        self.tmpl_design.write_text(TMPL_DESIGN, encoding="utf-8")
        self.state_file = self.root / "fake-state.json"
        self.spec = self.root / "loop.yaml"
        self.spec.write_text(SPEC_TEXT_V2_POST_REPAIR.format(
            active=str(self.active).replace("\\", "/"),
            done=str(self.done).replace("\\", "/"),
            orchest=str(ORCHEST).replace("\\", "/"),
            fake=str(FAKE).replace("\\", "/"),
            tmpl_uv=str(self.tmpl_uv).replace("\\", "/"),
            tmpl_blind=str(self.tmpl_blind).replace("\\", "/"),
            tmpl_design=str(self.tmpl_design).replace("\\", "/")),
            encoding="utf-8")
        self.env = {"FAKE_STATE_FILE": str(self.state_file)}

    def tearDown(self):
        self.tmp.cleanup()

    def _set_state(self, mapping: dict):
        self.state_file.write_text(json.dumps(mapping, ensure_ascii=False), encoding="utf-8")

    def _resume(self, *answers: str) -> tuple[int, str, str]:
        cmd = ["resume", "--spec", str(self.spec)]
        for a in answers:
            cmd += ["--answer", a]
        return run_driver(self.spec, *cmd, env_extra=self.env)

    def test_executor_repair_allows_three_consecutive_fresh_attempts(self):
        self._set_state({
            "uv-r1": {"verdict": "阻断需修复", "severities": ["implementation"]},
            "uv-r2": {"verdict": "可执行"},
        })
        rc, out, err = run_driver(self.spec, "run", "--spec", str(self.spec),
                                  env_extra=self.env)
        self.assertEqual(rc, 10, f"uv {out} {err}")

        for attempt in range(1, 4):
            prompt = self.active / f"prompt-executor-{attempt}.md"
            prompt.write_text(f"repair attempt {attempt}", encoding="utf-8")
            self._set_state({f"executor-r{attempt}": {}})
            rc, out, err = self._resume("action=repair")
            self.assertEqual(rc, 10, f"executor {attempt}: {out} {err}")
            self.assertTrue(
                (self.active / "reports" / f"executor-r{attempt}-report.md").is_file())

        fourth_prompt = self.active / "prompt-executor-4.md"
        fourth_prompt.write_text("must not run", encoding="utf-8")
        self._set_state({"executor-r4": {}})
        rc, out, err = self._resume("action=repair")
        self.assertEqual(rc, 11, f"fourth executor must be rejected: {out} {err}")
        self.assertFalse((self.active / "reports" / "executor-r4-report.md").exists())

    def test_blind_repair_routes_to_fresh_outer_not_completes_phase(self):
        """Requirement 1: Blind-review repair → accepting Executor must NOT complete
        the blind phase. It must route to a new outer Reviewer, then re-run blind
        before completion.

        Flow: uv pass → outer1 blocks → repair → outer1-r2 pass → blind blocks →
              repair → accept → route to outer2 (NOT complete blind) → outer2 pass →
              blind re-runs → pass → done.
        """
        # Step 1: UV both pass
        self._set_state({
            "uv-r1": {"verdict": "可执行"},
            "uv-r2": {"verdict": "可执行"},
        })
        rc, out, err = run_driver(self.spec, "run", "--spec", str(self.spec),
                                  env_extra=self.env)
        self.assertEqual(rc, 10, f"uv {out} {err}")

        # Step 2: UV proceed → outer1 need_prompt
        self._set_state({})
        rc, out, err = self._resume("action=proceed")
        self.assertEqual(rc, 10, f"outer1 need_prompt {out} {err}")

        # Step 3: Provide outer1 prompt → outer1 blocks
        rp = self.active / "prompt-outer-1.md"
        rp.write_text("outer1 prompt", encoding="utf-8")
        self._set_state({"reviewer-r1": {"verdict": "阻断需修复",
                                          "severities": ["implementation"]}})
        rc, out, err = self._resume("action=provide")
        self.assertEqual(rc, 10, f"outer1 blocks {out} {err}")
        self.assertTrue((self.active / "round-1.md").is_file())

        # Step 4: Repair → executor
        ep1 = self.active / "prompt-executor-1.md"
        ep1.write_text("fix1", encoding="utf-8")
        self._set_state({"executor-r1": {}})
        rc, out, err = self._resume("action=repair")
        self.assertEqual(rc, 10, f"executor1 {out} {err}")

        # Step 5: Accept → outer-loop: route to next outer round
        rp2 = self.active / "prompt-reviewer-next-1.md"
        rp2.write_text("outer1 round 2 prompt", encoding="utf-8")
        self._set_state({"reviewer-r2": {"verdict": "可执行"}})
        rc, out, err = self._resume("action=accepted")
        self.assertEqual(rc, 10, f"outer1-r2 {out} {err}")
        self.assertTrue((self.active / "round-2.md").is_file())

        # Step 6: Outer1-r2 proceed → blind triggers (now 2 outer rounds)
        self._set_state({"blind-r1": {"verdict": "阻断需修复",
                                       "severities": ["structural"]}})
        rc, out, err = self._resume("action=proceed")
        self.assertEqual(rc, 10, f"blind {out} {err}")
        self.assertTrue((self.active / "blind-recheck-1.md").is_file(),
                        "blind must trigger with 2 outer rounds")
        pause = json.loads((self.active / "pause-request.json").read_text(encoding="utf-8"))
        self.assertEqual(pause["decision"]["kind"], "phase_verdict")

        # Step 7: Blind repair → executor
        ep2 = self.active / "prompt-executor-2.md"
        ep2.write_text("fix2", encoding="utf-8")
        self._set_state({"executor-r2": {}})
        rc, out, err = self._resume("action=repair")
        self.assertEqual(rc, 10, f"executor2 {out} {err}")

        # Step 8: Accept executor from blind → MUST route to outer2, NOT complete blind
        # The expect path for reviewer_prompt is prompt-reviewer-next-{attempt}.md
        # (attempt=2 at this point: outer1 repair was attempt 1, blind repair is attempt 2)
        rp_outer2 = self.active / "prompt-reviewer-next-2.md"
        rp_outer2.write_text("fresh outer review after blind repair", encoding="utf-8")
        self._set_state({"reviewer-r3": {"verdict": "可执行"}})
        rc, out, err = self._resume("action=accepted")
        self.assertEqual(rc, 10, f"must route to outer2, not complete blind: {out} {err}")

        # Verify: blind phase must NOT be completed
        j = json.loads((self.active / ".loop-journal.json").read_text(encoding="utf-8"))
        completed = [h.get("phase_completed") for h in j.get("history", [])
                     if h.get("phase_completed")]
        self.assertNotIn("blind", completed,
                         "blind must not be completed before fresh outer review")

        # Verify: we should be at outer2 (need_prompt or phase_verdict)
        pause = json.loads((self.active / "pause-request.json").read_text(encoding="utf-8"))
        self.assertIn(pause["decision"]["kind"], ("need_prompt", "phase_verdict"),
                      f"should be at outer2, got {pause['decision']}")

        # Step 9: If need_prompt, provide outer2 prompt
        if pause["decision"]["kind"] == "need_prompt":
            rp_o2 = self.active / "prompt-outer-1.md"
            rp_o2.write_text("outer2 prompt", encoding="utf-8")
            self._set_state({"reviewer-r3": {"verdict": "可执行"}})
            rc, out, err = self._resume("action=provide")
            self.assertEqual(rc, 10, f"outer2 verdict {out} {err}")

        # Step 10: Outer2 proceed → blind should re-run
        pause = json.loads((self.active / "pause-request.json").read_text(encoding="utf-8"))
        self.assertEqual(pause["decision"]["kind"], "phase_verdict")
        self.assertTrue((self.active / "round-3.md").is_file(),
                        "outer2 should produce round-3.md")

        # Outer2 proceed → blind re-runs
        self._set_state({"blind-r2": {"verdict": "可执行"}})
        rc, out, err = self._resume("action=proceed")
        self.assertEqual(rc, 10, f"blind re-run {out} {err}")
        self.assertTrue((self.active / "blind-recheck-2.md").is_file(),
                        "blind must re-run after post-repair fresh outer review")

    def test_missing_reviewer_prompt_after_non_outer_repair_fails_closed(self):
        """Requirement 3: reviewer_prompt for post-repair fresh review is mandatory;
        omission fails closed without completing the repaired phase."""
        # Flow: uv pass → outer1 blocks → repair → outer1-r2 pass → blind blocks →
        #       executor → accept WITHOUT reviewer_prompt → exit 11
        self._set_state({
            "uv-r1": {"verdict": "可执行"},
            "uv-r2": {"verdict": "可执行"},
        })
        rc, _, _ = run_driver(self.spec, "run", "--spec", str(self.spec), env_extra=self.env)
        self.assertEqual(rc, 10)
        # UV proceed
        self._set_state({})
        rc, _, _ = self._resume("action=proceed")
        self.assertEqual(rc, 10)
        # Provide outer1 prompt → outer1 blocks
        rp = self.active / "prompt-outer-1.md"
        rp.write_text("outer1", encoding="utf-8")
        self._set_state({"reviewer-r1": {"verdict": "阻断需修复",
                                          "severities": ["implementation"]}})
        rc, _, _ = self._resume("action=provide")
        self.assertEqual(rc, 10)
        # Repair → executor
        ep = self.active / "prompt-executor-1.md"
        ep.write_text("fix", encoding="utf-8")
        self._set_state({"executor-r1": {}})
        rc, _, _ = self._resume("action=repair")
        self.assertEqual(rc, 10)
        # Accept → outer-loop: route to round 2
        rp2 = self.active / "prompt-reviewer-next-1.md"
        rp2.write_text("outer1-r2", encoding="utf-8")
        self._set_state({"reviewer-r2": {"verdict": "可执行"}})
        rc, _, _ = self._resume("action=accepted")
        self.assertEqual(rc, 10)
        # Outer1-r2 proceed → blind triggers
        self._set_state({"blind-r1": {"verdict": "阻断需修复",
                                       "severities": ["structural"]}})
        rc, _, _ = self._resume("action=proceed")
        self.assertEqual(rc, 10)
        # Blind repair → executor
        ep2 = self.active / "prompt-executor-2.md"
        ep2.write_text("fix2", encoding="utf-8")
        self._set_state({"executor-r2": {}})
        rc, _, _ = self._resume("action=repair")
        self.assertEqual(rc, 10)
        # Accept WITHOUT reviewer_prompt → must fail closed (exit 11)
        self._set_state({})
        rc, out, err = self._resume("action=accepted")
        self.assertEqual(rc, 11, f"missing reviewer_prompt must fail: {out} {err}")
        # Verify blind phase is NOT completed
        j = json.loads((self.active / ".loop-journal.json").read_text(encoding="utf-8"))
        completed = [h.get("phase_completed") for h in j.get("history", []) if h.get("phase_completed")]
        self.assertNotIn("blind", completed, "blind must not be completed without fresh outer review")


class TestV2SpecTopologyValidation(unittest.TestCase):
    """Requirement 4: Phase topology validation must guarantee a future fresh outer
    review after every non-outer repair. Merely checking 'any outer-loop' is insufficient."""

    def test_v2_parallel_review_without_subsequent_outer_loop_rejected(self):
        """v2 spec: parallel-review at the end with no outer-loop after it → rejected."""
        spec = {
            "slug": "s", "active_dir": "/x", "orchest": "/o", "ocsr_dispatch": "/d",
            "version": 2,
            "phases": [
                {"id": "uv", "type": "parallel-review",
                 "prompt_template": "t.md",
                 "reviewers": [{"model": "a/b", "label": "r1"}]},
                {"id": "blind", "type": "blind-recheck",
                 "model": "a/b", "prompt_template": "t.md"},
            ]
        }
        errs = cl.validate_spec(spec)
        self.assertTrue(any("outer-loop" in e for e in errs),
                        f"should require outer-loop after review phases: {errs}")

    def test_v2_blind_recheck_without_any_outer_loop_rejected(self):
        """v2 spec: blind-recheck with no outer-loop at all → rejected."""
        spec = {
            "slug": "s", "active_dir": "/x", "orchest": "/o", "ocsr_dispatch": "/d",
            "version": 2,
            "phases": [
                {"id": "blind", "type": "blind-recheck",
                 "model": "a/b", "prompt_template": "t.md"},
            ]
        }
        errs = cl.validate_spec(spec)
        self.assertTrue(any("outer-loop" in e for e in errs),
                        f"should require at least one outer-loop: {errs}")

    def test_v2_outer_loop_before_blind_sufficient(self):
        """v2 spec: outer-loop before blind (none after) → sufficient because
        blind-recheck requires at least one outer-loop anywhere."""
        spec = {
            "slug": "s", "active_dir": "/x", "orchest": "/o", "ocsr_dispatch": "/d",
            "version": 2,
            "phases": [
                {"id": "outer1", "type": "outer-loop",
                 "reviewer_models": ["a/b"], "executor_model": "a/b"},
                {"id": "blind", "type": "blind-recheck",
                 "model": "a/b", "prompt_template": "t.md"},
            ]
        }
        errs = cl.validate_spec(spec)
        self.assertEqual([], errs, f"outer-loop before blind should be accepted: {errs}")

    def test_v2_outer_loop_after_blind_accepted(self):
        """v2 spec: blind-recheck followed by outer-loop → accepted."""
        spec = {
            "slug": "s", "active_dir": "/x", "orchest": "/o", "ocsr_dispatch": "/d",
            "version": 2,
            "phases": [
                {"id": "outer1", "type": "outer-loop",
                 "reviewer_models": ["a/b"], "executor_model": "a/b"},
                {"id": "blind", "type": "blind-recheck",
                 "model": "a/b", "prompt_template": "t.md"},
                {"id": "outer2", "type": "outer-loop",
                 "reviewer_models": ["a/b"], "executor_model": "a/b"},
            ]
        }
        errs = cl.validate_spec(spec)
        self.assertEqual([], errs, f"should accept: {errs}")

    def test_v1_blind_without_outer_loop_still_accepted(self):
        """v1 spec: topology check does not apply."""
        spec = {
            "slug": "s", "active_dir": "/x", "orchest": "/o", "ocsr_dispatch": "/d",
            "version": 1,
            "phases": [
                {"id": "outer1", "type": "outer-loop",
                 "reviewer_models": ["a/b"], "executor_model": "a/b"},
                {"id": "blind", "type": "blind-recheck",
                 "model": "a/b", "prompt_template": "t.md"},
            ]
        }
        errs = cl.validate_spec(spec)
        self.assertEqual([], errs, f"v1 should not enforce topology: {errs}")


class TestMaterialSpecValidation(unittest.TestCase):
    """Phase 4: v2 spec must have a blind-recheck phase available for
    material revision blank-slate enforcement. A material revision forces
    a blank-slate phase before finish even with only one outer round."""

    def _base_v2(self):
        return {
            "slug": "s", "active_dir": "/x", "orchest": "/o", "ocsr_dispatch": "/d",
            "version": 2,
            "phases": [
                {"id": "outer1", "type": "outer-loop",
                 "reviewer_models": ["a/b"], "executor_model": "a/b"},
            ]
        }

    def test_v2_material_outer1_without_blank_fails_spec_validation(self):
        """v2 spec with only one outer-loop and no blind-recheck must fail
        because a material revision would require blank-slate review."""
        spec = self._base_v2()
        errs = cl.validate_spec(spec)
        self.assertTrue(any("blind-recheck" in e and "material" in e for e in errs),
                        f"should require blind-recheck for material revision: {errs}")

    def test_v2_with_blind_recheck_passes(self):
        """v2 spec with outer-loop + blind-recheck passes."""
        spec = self._base_v2()
        spec["phases"].append(
            {"id": "blind", "type": "blind-recheck",
             "model": "a/b", "prompt_template": "t.md"})
        errs = cl.validate_spec(spec)
        self.assertEqual([], errs, f"should pass: {errs}")

    def test_v1_without_blind_still_accepted(self):
        """v1 spec without blind-recheck is still accepted (no material gate)."""
        spec = self._base_v2()
        spec["version"] = 1
        errs = cl.validate_spec(spec)
        self.assertEqual([], errs, f"v1 should not enforce material gate: {errs}")

    def test_v2_outer1_plus_outer2_without_blind_still_requires_blind(self):
        """Even with multiple outer-loops, v2 spec needs blind-recheck
        because material revision can occur at any point."""
        spec = self._base_v2()
        spec["phases"].append(
            {"id": "outer2", "type": "outer-loop",
             "reviewer_models": ["a/b"], "executor_model": "a/b"})
        errs = cl.validate_spec(spec)
        self.assertTrue(any("blind-recheck" in e and "material" in e for e in errs),
                        f"should require blind-recheck: {errs}")


# ─── Phase 5b: task-envelope / accounting coverage / initialization disclosure ─

class TestDriverAccountingCoverage(unittest.TestCase):
    """Phase 5b: driver status must surface accounting_coverage when available."""

    def test_status_surfaces_accounting_coverage(self):
        """When budget_gate summary is available, driver status command output
        includes accounting_coverage and accounting_scope."""
        with tempfile.TemporaryDirectory() as td:
            active = Path(td) / "active"
            active.mkdir()
            budget_gate.initialize_state(active)
            budget_gate.append_ledger(active, {
                "event": "reserved",
                "reservation_id": "test-rid-001",
                "ts": "2026-01-01T00:00:00+00:00",
                "target_round": None,
                "target_role": "executor",
                "consumes": "none",
                "counts_before": {"outer": 0, "blind": 0, "ultraverge": 0, "total": 0},
                "ceilings": {"outer": 8, "blind": 3, "ultraverge": 3, "total": 28},
                "tier": "auditable-only",
            })
            spec = {"slug": "test", "active_dir": str(active),
                    "orchest": "/o", "ocsr_dispatch": "/d",
                    "phases": [{"id": "uv", "type": "parallel-review",
                                "prompt_template": "t.md",
                                "reviewers": [{"model": "a/b", "label": "r1"}]}]}
            spec_path = Path(td) / "spec.yaml"
            spec_path.write_text(
                f"slug: test\n"
                f"active_dir: {str(active).replace(chr(92), '/')}\n"
                f"orchest: /o\n"
                f"ocsr_dispatch: /d\n"
                f"phases:\n"
                f"  - id: uv\n"
                f"    type: parallel-review\n"
                f"    prompt_template: t.md\n"
                f"    reviewers:\n"
                f"      - {{model: a/b, label: r1}}\n",
                encoding="utf-8")
            drv = cl.Driver(spec, spec_path)
            # Run status through driver's main (this is what actually exercises
            # the converge_loop.py status code path)
            rc, out, err = run_driver(spec_path, "status", "--spec", str(spec_path))
            self.assertEqual(rc, 0, f"status rc={rc}; stderr={err}")
            status = json.loads(out)
            self.assertIn("accounting_coverage", status,
                          "driver status must include accounting_coverage")
            self.assertIn("accounting_scope", status,
                          "driver status must include accounting_scope")
            self.assertEqual(status["accounting_scope"], "instrumented_dispatch_only")


class TestInitializationDisclosure(unittest.TestCase):
    """Phase 5b: initialization must display quality_path_guaranteed: false
    when task envelope is configured, and omit it when unconfigured."""

    def test_init_shows_quality_path_guaranteed_false_with_envelope(self):
        """When task_tier is configured, _init_budget_config output includes
        quality_path_guaranteed: false with ceilings and envelope info."""
        with tempfile.TemporaryDirectory() as td:
            active = Path(td) / "active"
            active.mkdir()
            spec = {"slug": "test", "active_dir": str(active),
                    "orchest": "/o", "ocsr_dispatch": "/d",
                    "budget_config": {"task_tier": "medium"},
                    "phases": [{"id": "uv", "type": "parallel-review",
                                "prompt_template": "t.md",
                                "reviewers": [{"model": "a/b", "label": "r1"}]}]}
            spec_path = Path(td) / "spec.yaml"
            spec_path.write_text("slug: test\n", encoding="utf-8")
            drv = cl.Driver(spec, spec_path)
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                cl._init_budget_config(drv)
            output = buf.getvalue()
            self.assertIn("quality_path_guaranteed: false", output,
                          "init must print quality_path_guaranteed: false when envelope configured")
            self.assertIn("task-envelope:", output)
            self.assertIn("local ceilings:", output)

    def test_init_omits_guarantee_line_when_no_envelope(self):
        """When no task_tier/task_envelope_cap, _init_budget_config output
        omits quality_path_guaranteed line."""
        with tempfile.TemporaryDirectory() as td:
            active = Path(td) / "active"
            active.mkdir()
            spec = {"slug": "test", "active_dir": str(active),
                    "orchest": "/o", "ocsr_dispatch": "/d",
                    "budget_config": {},
                    "phases": [{"id": "uv", "type": "parallel-review",
                                "prompt_template": "t.md",
                                "reviewers": [{"model": "a/b", "label": "r1"}]}]}
            spec_path = Path(td) / "spec.yaml"
            spec_path.write_text("slug: test\n", encoding="utf-8")
            drv = cl.Driver(spec, spec_path)
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                cl._init_budget_config(drv)
            output = buf.getvalue()
            self.assertNotIn("quality_path_guaranteed", output,
                             "init must NOT print quality_path_guaranteed when no envelope")


class TestDriverNoDoubleCount(unittest.TestCase):
    """Phase 5b: driver dispatch through adapter does not create a separate
    task-envelope reservation (the adapter handles pairing)."""

    def test_driver_dispatch_through_adapter_no_double_te_reserve(self):
        """When the driver dispatches through orchest (which uses budget_gate),
        the task-envelope companion is created by the gate's atomic pair in
        cmd_reserve, not by a separate driver-side reservation."""
        with tempfile.TemporaryDirectory() as td:
            active = Path(td) / "active"
            active.mkdir()
            budget_gate.initialize_state(active, config={"task_tier": "small"})
            # Simulate a single reserve through the gate
            gate_events_before = budget_gate.read_ledger(active)
            te_before = budget_gate.scope_reservations_issued(gate_events_before, "task-envelope")
            # Do one reserve
            rc, out = _run_gate(active, "reserve", "--active-dir", str(active),
                                "--role", "outer-reviewer", "--tier", "auditable-only",
                                "--target-round", "1")
            self.assertEqual(rc, 0, f"reserve failed: {out}")
            gate_events_after = budget_gate.read_ledger(active)
            te_after = budget_gate.scope_reservations_issued(gate_events_after, "task-envelope")
            # Exactly 1 task-envelope reservation was created (companion)
            self.assertEqual(te_after - te_before, 1,
                             f"expected exactly 1 TE companion, got {te_after - te_before}")
            reserved = [e for e in gate_events_after if e.get("event") == "reserved"]
            te_reserved = [e for e in reserved if e.get("target_role") == "task-envelope"]
            self.assertEqual(len(te_reserved), 1,
                             f"expected 1 TE reserved event, got {len(te_reserved)}")


def _run_gate(active: Path, *args) -> tuple[int, str]:
    """Helper to run budget_gate CLI."""
    env = {**os.environ, "PYTHONUTF8": "1"}
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "budget_gate.py"), *args],
        capture_output=True, text=True, encoding="utf-8", env=env)
    return r.returncode, r.stdout.strip()


if __name__ == "__main__":
    unittest.main()
