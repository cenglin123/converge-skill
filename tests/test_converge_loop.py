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


if __name__ == "__main__":
    unittest.main()
