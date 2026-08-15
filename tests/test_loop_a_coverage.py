#!/usr/bin/env python3
"""Loop A 覆盖性 fixture 实测（plan 20260815-converge-loop-wiring §T1）。

覆盖收敛循环（Loop A）四条路径的全链演练，零代码改动（纯黑盒）：
  1  2 outer + 1 executor 修复轮 + 1 blind 全链（验收标准 4 的实跑版）
  2  盲审 verdict 为最后 record-verdict 时的 finish 终局 owner 语义（T4 注）
  3  executor 崩溃窗口（spawn_succeeded-缺-terminal）finish fail 分支 + 官方恢复
  4  Continue 语义现状：--continue-of 未实现 → unrecognized（T2 事实门）

std库 unittest。运行（仓库根）：python -m pytest tests/test_loop_a_coverage.py -q
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
ORCHEST = SCRIPTS / "orchest.py"
GATE = SCRIPTS / "budget_gate.py"
ARCHIVE = SCRIPTS / "archive_convergence.py"

FINAL_VERDICT = "可执行"


def run_orchest(*args) -> tuple[int, str, str]:
    env = {**os.environ, "PYTHONUTF8": "1"}
    r = subprocess.run([sys.executable, str(ORCHEST), *args],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def run_gate(*args) -> tuple[int, str, str]:
    env = {**os.environ, "PYTHONUTF8": "1"}
    r = subprocess.run([sys.executable, str(GATE), *args],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _read_events(active_dir: Path) -> list[dict]:
    events_dir = active_dir / "evidence" / "events"
    if not events_dir.is_dir():
        return []
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(events_dir.glob("*.json"))]


def _read_gate_ledger(active_dir: Path) -> list[dict]:
    p = active_dir / "gate-ledger.jsonl"
    if not p.is_file():
        return []
    return [json.loads(line) for line in
            p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _fm_of(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    out = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


class LoopABase(unittest.TestCase):
    SLUG = "wiring-fixture"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.active_root = self.root / "converge" / "active"
        self.active = self.active_root / self.SLUG
        self.active_root.mkdir(parents=True)
        self.active.mkdir()
        self.done_root = self.root / "converge" / "done"
        self.done_root.mkdir()
        self.prompt = self.root / "prompt.md"
        self.prompt.write_text("test prompt\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    # ---- 便捷封装（与 test_orchest.py 同风格）--------------------------------

    def reserve(self, role="outer-reviewer", round_no=1, phase="review",
                attempt=1, extra_args: list[str] | None = None) -> tuple[str, str]:
        args = ["reserve-round", "--active-dir", str(self.active),
                "--role", role, "--phase", phase, "--attempt", str(attempt),
                "--prompt-file", str(self.prompt),
                "--requested-provider", "testp", "--requested-model", "testm"]
        if round_no is not None:
            args += ["--round", str(round_no)]
        if extra_args:
            args += extra_args
        rc, out, err = run_orchest(*args)
        self.assertEqual(rc, 0, f"reserve-round rc={rc} stdout={out} stderr={err}")
        rid = next(l.split(":", 1)[1].strip()
                   for l in out.splitlines() if l.startswith("reservation_id:"))
        iid = next(l.split(":", 1)[1].strip()
                   for l in out.splitlines() if l.startswith("invocation_id:"))
        return rid, iid

    def register(self, rid: str, sid: str, output: str | None = None) -> tuple[int, str, str]:
        args = ["register-round", "--active-dir", str(self.active),
                "--reservation-id", rid, "--instance-id", sid]
        if output:
            args += ["--output", output]
        return run_orchest(*args)

    def record_verdict(self, round_no: int, verdict: str,
                       product: str | None = None, severities: str | None = None):
        args = ["record-verdict", "--active-dir", str(self.active),
                "--round", str(round_no), "--verdict", verdict]
        if product:
            args += ["--product", product]
        if severities:
            args += ["--severities", severities]
        return run_orchest(*args)

    def finish(self, verdict=FINAL_VERDICT):
        return run_orchest("finish", "--active-dir", str(self.active),
                           "--verdict", verdict,
                           "--done-root", str(self.done_root),
                           "--slug", self.SLUG)

    def write_retrospective(self):
        (self.active / "retrospective.md").write_text(
            "---\ntype: retrospective\n---\n# Retrospective\n\ntest\n",
            encoding="utf-8")

    def outer_round(self, n: int, verdict: str, severities: str | None = None) -> str:
        """一轮完整 outer reviewer 生命周期（reserve→register→record-verdict）。"""
        rid, _ = self.reserve(round_no=n)
        rc, out, err = self.register(rid, f"inst-r{n}")
        self.assertEqual(rc, 0, f"register r{n} rc={rc} stderr={err}")
        rc, out, err = self.record_verdict(n, verdict, severities=severities)
        self.assertEqual(rc, 0, f"record-verdict r{n} rc={rc} stderr={err}")
        return rid


# ── 1. 全链：2 outer + 1 executor 修复轮 + 1 blind ───────────────────────────

class TestLoopAFullChain(LoopABase):

    def test_full_chain_no_manual_fallback(self):
        # r1 reviewer：阻断（带 severity）
        rid1 = self.outer_round(1, "阻断需修复", severities="structural")
        # r1 executor 修复轮（consumes=none）
        (self.active / "attempts.md").write_text(
            "## Round 1 attempt\n- source: converge_loop\n", encoding="utf-8")
        rid_exe, _ = self.reserve(role="executor", round_no=None, phase="repair")
        rc, out, err = self.register(rid_exe, "inst-exe-1", output="attempts.md")
        self.assertEqual(rc, 0, f"register executor rc={rc} stderr={err}")
        # r2 reviewer：可执行
        self.outer_round(2, FINAL_VERDICT)
        # blind（独立序列编号 1；≥2 轮后触发，verdict 在 gate 三档内）
        rid_blind, _ = self.reserve(role="blind-reviewer", round_no=1, phase="review")
        rc, out, err = self.register(rid_blind, "inst-blind-1")
        self.assertEqual(rc, 0, f"register blind rc={rc} stderr={err}")
        rc, out, err = self.record_verdict(
            1, FINAL_VERDICT, product="blind-recheck-1.md")
        self.assertEqual(rc, 0, f"record-verdict blind rc={rc} stderr={err}")

        self.write_retrospective()

        # 断言：骨架由脚本生成 + frontmatter 契约字段回填
        fm1 = _fm_of(self.active / "round-1.md")
        self.assertEqual(fm1.get("reservation_id"), rid1)
        self.assertEqual(fm1.get("reviewer_instance_id"), "inst-r1")
        self.assertEqual(fm1.get("verdict"), "阻断需修复")
        self.assertIn("invocation_id", fm1)
        self.assertTrue(fm1.get("generated_at"))
        # ledger 零孤儿：每个 reservation 恰好一对 reserve/settle
        ledger = _read_gate_ledger(self.active)
        settled = [e for e in ledger if e.get("event") in
                   ("spawn_succeeded", "spawn_failed", "cancelled")]
        reserved = [e for e in ledger if e.get("event") == "reserved"]
        self.assertEqual(len(settled), len(reserved))
        rids_reserved = {e["reservation_id"] for e in reserved}
        rids_settled = {e["reservation_id"] for e in settled}
        self.assertEqual(rids_settled, rids_reserved)
        # events 零孤儿：每个 invocation-started 都有 terminal
        events = _read_events(self.active)
        started = [e for e in events if e["event_type"] == "invocation-started"]
        terminals = [e for e in events if e["event_type"] == "invocation-terminal"]
        self.assertEqual(len(terminals), len(started))
        # events 无 prompt*.md 留在 active（归位发生在 finish 步骤 6）

        # finish 全链
        rc, out, err = self.finish()
        self.assertEqual(rc, 0, f"finish rc={rc} stdout={out} stderr={err}")
        target = self.done_root / self.SLUG
        self.assertTrue(target.is_dir())
        # 归档后 check
        env = {**os.environ, "PYTHONUTF8": "1"}
        r = subprocess.run([sys.executable, str(ARCHIVE), "check",
                            str(target), "--format", "json"],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["final_decision"]["value"], FINAL_VERDICT)


# ── 2. 盲审为最后 record-verdict 时的 finish 终局 owner 语义（T4 注）──────────

class TestBlindLastTerminalOwnerSemantics(LoopABase):

    def test_fresh_executable_then_blind_blocked_finish_executable(self):
        """R1 阻断 → executor → R2 可执行 → 盲审阻断（最后 record-verdict）→
        finish --verdict 可执行 的现行行为实测（以 orchest.py 现行为准）。"""
        self.outer_round(1, "阻断需修复", severities="structural")
        (self.active / "attempts.md").write_text("attempt\n", encoding="utf-8")
        rid_exe, _ = self.reserve(role="executor", round_no=None, phase="repair")
        rc, _, err = self.register(rid_exe, "inst-exe-1", output="attempts.md")
        self.assertEqual(rc, 0, err)
        self.outer_round(2, FINAL_VERDICT)
        rid_blind, _ = self.reserve(role="blind-reviewer", round_no=1, phase="review")
        rc, _, err = self.register(rid_blind, "inst-blind-1")
        self.assertEqual(rc, 0, err)
        rc, _, err = self.record_verdict(
            1, "阻断需修复", severities="structural", product="blind-recheck-1.md")
        self.assertEqual(rc, 0, err)

        self.write_retrospective()
        # 现行为：finish 复用 record 的终局 decision；实测本会话同形态通过
        # （fresh 最后 reviewer-verdict=可执行 优先于 blind 终端——owner 语义以
        #  本测试钉死现行为，如后续视为缺陷走只加不改上报）
        rc, out, err = self.finish()
        self.assertEqual(rc, 0, f"finish rc={rc} stdout={out} stderr={err}")
        manifest = json.loads((self.done_root / self.SLUG / "manifest.json")
                              .read_text(encoding="utf-8"))
        self.assertEqual(manifest["final_decision"]["value"], FINAL_VERDICT)


# ── 3. executor 崩溃窗口：finish fail 分支 + 官方恢复路径 ─────────────────────

class TestExecutorCrashWindow(LoopABase):

    def _crash_window_setup(self) -> str:
        """r1 完整 + executor 手动 gate settle（spawn_succeeded-缺-terminal）。"""
        self.outer_round(1, "阻断需修复", severities="structural")
        rid_exe, _ = self.reserve(role="executor", round_no=None, phase="repair")
        rc, out, err = run_gate("settle", "--active-dir", str(self.active),
                                "--reservation-id", rid_exe,
                                "--result", "succeeded",
                                "--instance-id", "inst-exe-1")
        self.assertEqual(rc, 0, f"manual gate settle rc={rc} {out} {err}")
        return rid_exe

    def test_finish_fails_on_crash_window_then_register_recovers(self):
        rid_exe = self._crash_window_setup()
        self.write_retrospective()

        # finish 步骤 3：executor consumes=none 无 _product_path 推导 → fail 分支
        rc, out, err = self.finish(verdict="阻断需修复")
        combined = out + err
        self.assertNotEqual(rc, 0, "崩溃窗口 finish 应 fail-closed")
        self.assertIn("产物无法解析", combined)
        # 事务性：未归档
        self.assertFalse((self.done_root / self.SLUG).exists())

        # 官方恢复路径：register-round --output attempts.md（幂等重试）
        (self.active / "attempts.md").write_text(
            "## Round 1 attempt\n- source: converge_loop\n", encoding="utf-8")
        rc, out, err = self.register(rid_exe, "inst-exe-1", output="attempts.md")
        self.assertEqual(rc, 0, f"recovery register rc={rc} stdout={out} stderr={err}")

        # 窗口闭合后 finish 通过
        rc, out, err = self.finish(verdict="阻断需修复")
        self.assertEqual(rc, 0, f"finish after recovery rc={rc} stdout={out} stderr={err}")
        self.assertTrue((self.done_root / self.SLUG).is_dir())


# ── 4. Continue 语义现状（T2 事实门）─────────────────────────────────────────

class TestContinueStatusQuo(LoopABase):
    """T1 差距钉子已由 T2 实现关闭——完整 Continue 链路断言移至
    tests/test_continue_extension.py（begin kind=continue + max_inner_loops
    计数 + register --invocation-id + finish owner 过滤）。本类保留为空锚，
    标记 T1→T2 的差距闭环轨迹。"""


if __name__ == "__main__":
    unittest.main()
