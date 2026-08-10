"""S9e 吃狗粮：终局链路 spec 经真实 OCSR 运行器跑通，产出真实归档。

这里不是「模板长得像那么回事」，而是**真的用 `ocsr_dispatch.py run --spec` 执行**
`refs/run-specs/terminal-chain.yaml`，最后拿 `check` 的 `valid-v1` 作为验收。

全程零模型调用（链路里只有 hook / assert），所以可以进常规测试套件。

ocsr 仓库不在本仓库控制之下，找不到就 skip —— converge 不硬依赖它的检出位置。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TEMPLATE = ROOT / "refs" / "run-specs" / "terminal-chain.yaml"
sys.path.insert(0, str(SCRIPTS))

QUOTE = "够了，就这样"


def _ocsr_dispatch() -> Path | None:
    override = os.environ.get("OCSR_SKILL_DIR")
    candidates = [Path(override)] if override else []
    candidates.append(Path.home() / ".agents" / "skills" / "ocsr")
    for base in candidates:
        script = base / "scripts" / "ocsr_dispatch.py"
        if script.is_file():
            return script
    return None


class TerminalChainSpecTests(unittest.TestCase):
    def setUp(self):
        self.dispatch = _ocsr_dispatch()
        if self.dispatch is None:
            raise unittest.SkipTest("ocsr skill not found (set OCSR_SKILL_DIR)")
        try:
            import yaml  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("the ocsr runner needs PyYAML")

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.active = self.root / "active" / "case"
        self.active.mkdir(parents=True)
        self.done = self.root / "done"
        self.done.mkdir()
        self._populate_active()

    def _populate_active(self):
        """一个「除了终局那几步、其余都已就绪」的 active 目录。"""
        from archive_contract.capture import begin_invocation, complete_invocation

        (self.active / "plan.md").write_text("# Plan\n", encoding="utf-8", newline="\n")
        reserve = {
            "event": "reserved", "reservation_id": "r1", "ts": "2026-08-10T00:00:00+00:00",
            "target_round": 1, "target_role": "outer-reviewer", "consumes": "outer",
            "counts_before": {"outer": 0, "blind": 0, "ultraverge": 0, "total": 0},
            "ceilings": {"outer": 5, "blind": 1, "ultraverge": 3, "total": 42},
            "extension_id": None, "tier": "auditable-only",
        }
        settle = {"event": "spawn_succeeded", "reservation_id": "r1",
                  "ts": "2026-08-10T00:00:01+00:00", "instance_id": "i1"}
        (self.active / "gate-ledger.jsonl").write_text(
            json.dumps(reserve) + "\n" + json.dumps(settle) + "\n",
            encoding="utf-8", newline="\n")

        start = begin_invocation(self.active, invocation_kind="spawn", role="outer-reviewer",
            phase="final-review", round_number=1, attempt=1, reservation_id="r1")
        complete_invocation(self.active, start["invocation_id"],
            terminal_status="succeeded", instance_id="i1", receipt="p1",
            settlement_ref="gate-ledger.jsonl:r1",
            evidence_level="configured", resolution_source="cli_argument",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"review")

        # 这两个文件**故意不带** terminal_decision_* marker —— 由 spec 的 stamp 步骤盖上。
        for name in ("round-1.md", "retrospective.md"):
            (self.active / name).write_text(f"# {name}\n", encoding="utf-8", newline="\n")

    def _render_spec(self, **overrides) -> Path:
        """把模板里的占位 vars 换成本次的真实路径。"""
        import yaml

        spec = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
        spec["run"]["workdir"] = (self.root / "runwd").as_posix()
        spec["vars"].update({
            "cli": (SCRIPTS / "archive_convergence.py").as_posix(),
            "active_root": self.active.parent.as_posix(),
            "done": self.done.as_posix(),
            "slug": "case",
            "quote": QUOTE,
            "host_message_id": "m1",
            "decision_kind": "accept-terminal-c",
        })
        spec["vars"].update(overrides)
        path = self.root / "spec.yaml"
        path.write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False),
                        encoding="utf-8", newline="\n")
        return path

    def _run(self, spec: Path, *extra) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.dispatch), "run", "--spec", str(spec), *extra],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "OCSR_DISABLE_MODEL_CALLS": "1"},
        )

    def test_template_passes_validate(self):
        proc = self._run(self._render_spec(), "--validate")
        self.assertEqual(proc.returncode, 0, f"{proc.stdout}\n{proc.stderr}")

    def test_chain_produces_a_valid_archive(self):
        proc = self._run(self._render_spec())
        self.assertEqual(proc.returncode, 0, f"{proc.stdout}\n{proc.stderr}")

        manifest_path = self.done / "case" / "manifest.json"
        self.assertTrue(manifest_path.is_file(), "archive must have produced a manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        decision = manifest["final_decision"]
        self.assertEqual(decision["type"], "user-decision")
        self.assertEqual(decision["value"], "accepted-stop")

        # 独立复核，不采信 run 的退出码。
        check = subprocess.run(
            [sys.executable, str(SCRIPTS / "archive_convergence.py"),
             "check", str(self.done / "case"), "--format", "json"],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(check.returncode, 0, check.stdout)
        self.assertTrue(json.loads(check.stdout)["valid"])

    def test_nothing_machine_derivable_was_typed(self):
        """这条才是本模板存在的理由：可导出的值一个都没有出现在 spec 里。

        两次归档失败都是手填导出值；模板若把它们写死，等于把同一个坑搬进 YAML。
        """
        text = TEMPLATE.read_text(encoding="utf-8")
        for forbidden in ("supersedes_decision_event_id", "presented_degradations",
                          "--accepted-state", "terminal_decision_event_id"):
            self.assertNotIn(f"{forbidden}, ", text,
                             f"{forbidden} 是可导出值，不得作为 spec 的实参出现")

    def test_derived_fields_match_what_the_archive_demands(self):
        """跑完后，事件图里的两个导出字段确实是归档要的那个值。"""
        proc = self._run(self._render_spec())
        self.assertEqual(proc.returncode, 0, f"{proc.stdout}\n{proc.stderr}")
        events_dir = self.done / "case" / "evidence" / "events"
        decisions = [json.loads(p.read_text(encoding="utf-8"))
                     for p in sorted(events_dir.glob("*.json"))]
        decision = next(e for e in decisions if e["event_type"] == "terminal-decision")
        # 一次 configured 级 provenance 的调用 → 恰好一条 degradation。
        self.assertEqual(decision["presented_degradations"], ["model-provenance:configured"])
        # 链上第一条决策，无前驱。
        self.assertIsNone(decision["supersedes_decision_event_id"])
        self.assertEqual(decision["user_quote"], QUOTE)

    def test_quote_mismatch_fails_the_chain_closed(self):
        """负向：user-message 与 decision 的引用不一致时，链路必须停机而不是照archive。

        用 `--answer` 之外的方式制造分歧不现实（模板两处引用同一个 var），
        所以这里直接篡改事件：先跑通，再用一个引用对不上的 quote 重跑一条决策。
        """
        from archive_contract.capture import record_terminal_decision, record_user_message
        from archive_contract.model import ArchiveError

        message = record_user_message(self.active, host_message_id="m1", user_quote=QUOTE)
        with self.assertRaises(ArchiveError):
            record_terminal_decision(self.active, {
                "decision_type": "user-decision", "decision_kind": "accept-terminal-c",
                "user_quote": "另一句话", "source_ref": message["event_id"],
                "accepted_state": "accepted-stop",
                "presented_degradations": ["model-provenance:configured"],
                "supersedes_decision_event_id": None,
            })


if __name__ == "__main__":
    unittest.main()
