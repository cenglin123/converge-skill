#!/usr/bin/env python3
"""budget_gate core 验收用例（plan §测试与验收，host-independent 部分）。

stdlib unittest，无外部依赖。运行：
    python -m unittest tests.test_budget_gate -v
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GATE = Path(__file__).resolve().parent.parent / "scripts" / "budget_gate.py"


def run(*args, cwd=None):
    r = subprocess.run([sys.executable, str(GATE), *args],
                       capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.active = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def reserve(self, role, rid, rnd=None, tier="auditable-only"):
        args = ["reserve", "--active-dir", str(self.active), "--role", role,
                "--reservation-id", rid, "--tier", tier]
        if rnd is not None:
            args += ["--target-round", str(rnd)]
        return run(*args)

    def settle(self, rid, result, **kw):
        args = ["settle", "--active-dir", str(self.active),
                "--reservation-id", rid, "--result", result]
        if kw.get("pre_execution"):
            args += ["--pre-execution"]
        if kw.get("instance_id"):
            args += ["--instance-id", kw["instance_id"]]
        return run(*args)

    def ledger(self):
        p = self.active / "gate-ledger.jsonl"
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

    def set_config(self, **cfg):
        sp = self.active / "_budget-state.json"
        st = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
        st.setdefault("config", {}).update(cfg)
        st.setdefault("extensions", [])
        st.setdefault("fsm", {"mode": "standard", "severities": {}})
        sp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")

    def add_extension(self, **ext):
        sp = self.active / "_budget-state.json"
        st = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {
            "config": {}, "extensions": [], "fsm": {"mode": "standard", "severities": {}}}
        st["extensions"].append(ext)
        sp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")

    def last_block_decision(self, scope):
        for ev in reversed(self.ledger()):
            if ev.get("event") == "decision" and ev.get("scope") == scope \
                    and str(ev.get("verdict", "")).startswith("BLOCK"):
                return ev
        return None


class TestScopeBudget(Base):
    def test_outer_boundary(self):
        self.set_config(max_outer_loops=2)
        # 用 round 产物把 realized 顶到 ceiling-? 我们用 pending 模拟：连续 reserve 不落产物
        c, out, _ = self.reserve("outer-reviewer", "r1", rnd=1)
        self.assertTrue(out.startswith("PROCEED"), out)         # usage 0 < 2
        c, out, _ = self.reserve("outer-reviewer", "r2", rnd=2)
        self.assertTrue(out.startswith("PROCEED"), out)         # usage 1 < 2
        c, out, _ = self.reserve("outer-reviewer", "r3", rnd=3)
        self.assertEqual(out, "BLOCK:budget_exhausted")         # usage 2 == 2
        self.assertEqual(c, 10)

    def test_failed_releases_scope(self):
        self.set_config(max_outer_loops=1)
        c, out, _ = self.reserve("outer-reviewer", "r1", rnd=1)
        self.assertTrue(out.startswith("PROCEED"))
        # 失败释放 scope 额度 → 可再领一格 scope（但总量仍计）
        self.settle("r1", "failed")
        c, out, _ = self.reserve("outer-reviewer", "r2", rnd=2)
        self.assertTrue(out.startswith("PROCEED"), out)

    def test_realized_dedup(self):
        self.set_config(max_outer_loops=1)
        c, out, _ = self.reserve("outer-reviewer", "r1", rnd=1)
        self.assertTrue(out.startswith("PROCEED"))
        # 产物落成：pending→realized，仍只占 1 格（不双计）→ 下一个被 BLOCK
        (self.active / "round-1.md").write_text("x", encoding="utf-8")
        self.settle("r1", "succeeded", instance_id="a1")
        c, out, _ = self.reserve("outer-reviewer", "r2", rnd=2)
        self.assertEqual(out, "BLOCK:budget_exhausted", out)


class TestTotalCap(Base):
    def test_total_cap_monotonic_under_failure(self):
        # 极小总量上限：通过 config 间接（总量由公式算；用极小 budget 压低公式）
        self.set_config(max_outer_loops=1, max_inner_loops=0,
                        max_blind_rechecks=0, ultraverge_min_reviewers=0, total_safety=1.0)
        # base = 3 + 0 + 1*(1+0) + 0 + 1 = 5 → total cap = 5
        ok = 0
        for i in range(5):
            c, out, _ = self.reserve("executor", f"e{i}")   # consumes:none，只压总量
            if out.startswith("PROCEED"):
                ok += 1
                self.settle(f"e{i}", "failed")              # 反复失败
        self.assertEqual(ok, 5)
        c, out, _ = self.reserve("executor", "e_final")
        self.assertEqual(out, "BLOCK:total_spawn_cap", out)  # 失败未释放总量
        self.assertEqual(c, 13)

    def test_pre_execution_cancel_not_counted(self):
        self.set_config(max_outer_loops=1, max_inner_loops=0,
                        max_blind_rechecks=0, ultraverge_min_reviewers=0, total_safety=1.0)
        # total cap = 5
        for i in range(5):
            self.reserve("executor", f"e{i}")
            self.settle(f"e{i}", "cancelled", pre_execution=True)   # 零消耗，不计总量
        c, out, _ = self.reserve("executor", "e_final")
        self.assertTrue(out.startswith("PROCEED"), out)            # 总量未被消耗


class TestRoles(Base):
    def test_unknown_role_deny(self):
        c, out, _ = self.reserve("sneaky-role", "x1")
        self.assertEqual(out, "DENY:unknown_role")
        self.assertEqual(c, 21)

    def test_relabel_billed_by_label_but_total_still_counts(self):
        # auditable-only：reviewer 伪标 executor 拿 consumes:none（绕 scope），
        # 但总量仍计 → 兜底成立（见 total cap 测试）。此处仅验证标签计费行为。
        self.set_config(max_outer_loops=0)   # outer ceiling 0
        c, out, _ = self.reserve("outer-reviewer", "real", rnd=1)
        self.assertEqual(out, "BLOCK:budget_exhausted")           # 诚实标签被 scope 拦
        c, out, _ = self.reserve("executor", "fake", rnd=1)
        self.assertTrue(out.startswith("PROCEED"))               # 伪标绕过 scope（已知残余漏洞）


class TestExtensions(Base):
    def _trigger_block(self, scope_role, rnd):
        self.set_config(max_outer_loops=0)
        c, out, _ = self.reserve(scope_role, "blk", rnd=rnd)
        self.assertEqual(out, "BLOCK:budget_exhausted")
        return self.last_block_decision("outer")

    def test_valid_extension_lifts_ceiling(self):
        d = self._trigger_block("outer-reviewer", 1)
        self.add_extension(extension_id="x1", scope="outer",
                           triggering_block_event_id=d["decision_event_id"],
                           granted_at_usage=d["observed_usage"],
                           prior_ceiling=d["effective_ceiling"],
                           new_ceiling=d["effective_ceiling"] + 1,
                           supersedes=None, user_quote="继续")
        c, out, _ = self.reserve("outer-reviewer", "after", rnd=1)
        self.assertTrue(out.startswith("PROCEED"), out)

    def test_extension_bad_crosscheck_fail_closed(self):
        d = self._trigger_block("outer-reviewer", 1)
        self.add_extension(extension_id="x1", scope="outer",
                           triggering_block_event_id=d["decision_event_id"],
                           granted_at_usage=999,             # 与 decision 不符
                           prior_ceiling=d["effective_ceiling"],
                           new_ceiling=d["effective_ceiling"] + 1,
                           supersedes=None, user_quote="继续")
        c, out, _ = self.reserve("outer-reviewer", "after", rnd=1)
        self.assertTrue(out.startswith("FAIL_CLOSED"), out)
        self.assertEqual(c, 30)

    def test_extension_nonmonotonic_fail_closed(self):
        d = self._trigger_block("outer-reviewer", 1)
        self.add_extension(extension_id="x1", scope="outer",
                           triggering_block_event_id=d["decision_event_id"],
                           granted_at_usage=d["observed_usage"],
                           prior_ceiling=d["effective_ceiling"],
                           new_ceiling=d["effective_ceiling"],   # 不增 → 非法
                           supersedes=None, user_quote="x")
        c, out, _ = self.reserve("outer-reviewer", "after", rnd=1)
        self.assertTrue(out.startswith("FAIL_CLOSED"), out)


class TestSettleLifecycle(Base):
    def test_settle_without_reserve(self):
        c, out, _ = self.settle("ghost", "succeeded")
        self.assertEqual(out, "FAIL_CLOSED:settle_without_reserve")
        self.assertEqual(c, 30)

    def test_duplicate_settlement(self):
        self.reserve("executor", "e1")
        self.settle("e1", "succeeded", instance_id="a1")
        c, out, _ = self.settle("e1", "succeeded", instance_id="a1")
        self.assertEqual(out, "FAIL_CLOSED:duplicate_settlement")

    def test_succeeded_requires_instance_id(self):
        self.reserve("executor", "e1")
        c, out, _ = self.settle("e1", "succeeded")  # 无 instance_id
        self.assertEqual(out, "FAIL_CLOSED:missing_instance_id", out)
        self.assertEqual(c, 30)


class TestFailClosed(Base):
    def test_corrupt_ledger(self):
        self.reserve("executor", "e1")
        (self.active / "gate-ledger.jsonl").write_text("{not json\n", encoding="utf-8")
        c, out, _ = self.reserve("executor", "e2")
        self.assertTrue(out.startswith("FAIL_CLOSED"), out)


class TestModeSwitch(Base):
    def test_impl_streak_triggers_mode_switch(self):
        self.set_config(impl_severity_streak_threshold=2, max_outer_loops=10)
        for rnd in (1, 2):
            run("ingest-verdict", "--active-dir", str(self.active),
                "--target-round", str(rnd), "--verdict", "阻断需修复",
                "--severities", "implementation,implementation,structural")
        c, out, _ = self.reserve("outer-reviewer", "next", rnd=3)
        self.assertEqual(out, "MODE_SWITCH_REQUIRED", out)
        self.assertEqual(c, 20)

    def test_structural_streak_no_switch(self):
        self.set_config(impl_severity_streak_threshold=2, max_outer_loops=10)
        for rnd in (1, 2):
            run("ingest-verdict", "--active-dir", str(self.active),
                "--target-round", str(rnd), "--verdict", "阻断需修复",
                "--severities", "structural,conceptual")
        c, out, _ = self.reserve("outer-reviewer", "next", rnd=3)
        self.assertTrue(out.startswith("PROCEED"), out)


class TestPreflight(Base):
    def test_code_heavy_warns(self):
        plan = self.active / "plan.md"
        code_lines = "\n".join("x = 1" for _ in range(15))
        one_block = "```python\n" + code_lines + "\n```"
        body = "# plan\n" + "\n".join(one_block for _ in range(3))
        plan.write_text(body, encoding="utf-8")
        c, out, _ = run("preflight", "--plan", str(plan))
        self.assertTrue(out.startswith("WARN:code_heavy"), out)

    def test_clean_plan(self):
        plan = self.active / "plan.md"
        plan.write_text("# plan\n任务 / 边界 / 验收，无代码。\n", encoding="utf-8")
        c, out, _ = run("preflight", "--plan", str(plan))
        self.assertEqual(out, "CLEAN")


class TestAdversarial(Base):
    """编码审计 agent 在验收中发现的绕过路径（findings 1-4, 6）。"""

    def test_duplicate_reservation_id_blocked(self):
        # finding 1：同一 reservation_id 重复 reserve 不得绕过预算。
        self.set_config(max_outer_loops=2)
        c, out, _ = self.reserve("outer-reviewer", "same", rnd=1)
        self.assertTrue(out.startswith("PROCEED"), out)
        c, out, _ = self.reserve("outer-reviewer", "same", rnd=2)
        self.assertEqual(out, "FAIL_CLOSED:duplicate_reservation_id", out)
        self.assertEqual(c, 30)

    def test_double_target_blocked(self):
        # finding 2：两个 reservation 指向同一 target round → fail-closed。
        self.set_config(max_outer_loops=5)
        c, out, _ = self.reserve("outer-reviewer", "a", rnd=1)
        self.assertTrue(out.startswith("PROCEED"))
        c, out, _ = self.reserve("outer-reviewer", "b", rnd=1)
        self.assertEqual(out, "FAIL_CLOSED:double_target", out)

    def test_retry_same_target_after_failure_ok(self):
        # 合法对照：失败释放后允许重试同一 round。
        self.set_config(max_outer_loops=5)
        self.reserve("outer-reviewer", "a", rnd=1)
        self.settle("a", "failed")
        c, out, _ = self.reserve("outer-reviewer", "b", rnd=1)
        self.assertTrue(out.startswith("PROCEED"), out)

    def test_round_gap_fail_closed(self):
        # finding 2 续：产物缺号（round-1 + round-3，无 round-2）→ fail-closed。
        (self.active / "round-1.md").write_text("x", encoding="utf-8")
        (self.active / "round-3.md").write_text("x", encoding="utf-8")
        c, out, _ = self.reserve("outer-reviewer", "n", rnd=4)
        self.assertEqual(out, "FAIL_CLOSED:round_gap:outer", out)

    def test_real_reviewer_verdict_accepted(self):
        # finding 3：真实 reviewer verdict `阻断需修复` 必须可接入，不得 verdict_parse 失败。
        c, out, _ = run("ingest-verdict", "--active-dir", str(self.active),
                        "--target-round", "1", "--verdict", "阻断需修复",
                        "--severities", "implementation")
        self.assertEqual(out, "ok", out)
        for v in ("可执行", "需重新设计"):
            c, out, _ = run("ingest-verdict", "--active-dir", str(self.active),
                            "--target-round", "1", "--verdict", v)
            self.assertEqual(out, "ok", f"{v}: {out}")
        c, out, _ = run("ingest-verdict", "--active-dir", str(self.active),
                        "--target-round", "1", "--verdict", "阻断")  # 旧错误字面量
        self.assertEqual(out, "FAIL_CLOSED:verdict_parse")

    def test_extension_chain_must_be_continuous(self):
        # finding 4：0→10 后不得复用旧 decision 写 10→5（prior 必须接上一记录的 new）。
        d = self._block_outer()
        self.add_extension(extension_id="x1", scope="outer",
                           triggering_block_event_id=d["decision_event_id"],
                           granted_at_usage=d["observed_usage"],
                           prior_ceiling=d["effective_ceiling"],
                           new_ceiling=d["effective_ceiling"] + 10,
                           supersedes=None, user_quote="到10")
        # 第二条 supersedes x1，却复用同一旧 decision（prior=0），new=5 → 链不连续
        self.add_extension(extension_id="x2", scope="outer",
                           triggering_block_event_id=d["decision_event_id"],
                           granted_at_usage=d["observed_usage"],
                           prior_ceiling=d["effective_ceiling"],   # 0，应等于 x1.new(=10)
                           new_ceiling=d["effective_ceiling"] + 5,
                           supersedes="x1", user_quote="降到5")
        c, out, _ = self.reserve("outer-reviewer", "after", rnd=1)
        self.assertTrue(out.startswith("FAIL_CLOSED"), out)
        self.assertIn("ext_chain_discontinuous", out)

    def test_malformed_reserved_missing_fields_fail_closed(self):
        # 复验 finding 1：缺必填字段的 reserved 事件不得被接受（否则该 spawn 不计任何 scope）。
        self.reserve("executor", "e1")
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "reserved", "reservation_id": "x"}) + "\n")
        c, out, _ = self.reserve("outer-reviewer", "next", rnd=1)
        self.assertEqual(c, 30, out)
        self.assertTrue(out.startswith("FAIL_CLOSED:event_field:reserved"), out)

    _TS = "2026-06-19T00:00:00+00:00"
    _CB = {"outer": 0, "blind": 0, "ultraverge": 0, "total": 0}

    def test_consumes_mismatch_fail_closed(self):
        # role↔consumes 一致性：reviewer 伪标 consumes:none 注入 ledger → fail-closed。
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "reserved", "reservation_id": "y", "ts": self._TS,
                                "target_role": "outer-reviewer", "consumes": "none",
                                "target_round": 1}) + "\n")
        c, out, _ = self.reserve("outer-reviewer", "next", rnd=2)
        self.assertEqual(out, "FAIL_CLOSED:event_field:reserved.consumes", out)

    def test_non_positive_target_fail_closed(self):
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "reserved", "reservation_id": "z", "ts": self._TS,
                                "target_role": "outer-reviewer", "consumes": "outer",
                                "target_round": 0, "counts_before": self._CB,
                                "ceilings": self._CB, "tier": "auditable-only"}) + "\n")
        c, out, _ = self.reserve("outer-reviewer", "next", rnd=1)
        self.assertEqual(out, "FAIL_CLOSED:event_field:reserved.target_round", out)

    def test_reserved_missing_contract_fields_fail_closed(self):
        # 复验3-1：reserved 缺 ts/counts_before/ceilings/tier 等契约字段 → fail-closed。
        self.reserve("executor", "e1")
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "reserved", "reservation_id": "x",
                                "target_role": "outer-reviewer", "consumes": "outer",
                                "target_round": 1}) + "\n")   # 缺 ts/counts_before/ceilings/tier
        c, out, _ = self.reserve("outer-reviewer", "next", rnd=2)
        self.assertEqual(c, 30, out)
        self.assertTrue(out.startswith("FAIL_CLOSED:event_field:reserved"), out)

    def test_decision_bad_verdict_fail_closed(self):
        # 复验3-2：decision.verdict 非规定枚举（如 BANANA）→ fail-closed。
        self.reserve("executor", "e1")
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "decision", "decision_event_id": "d1",
                                "ts": "2026-06-19T00:00:00+00:00", "verdict": "BANANA",
                                "scope": None, "observed_usage": None,
                                "effective_ceiling": None}) + "\n")
        c, out, _ = self.reserve("executor", "e2")
        self.assertEqual(out, "FAIL_CLOSED:event_field:decision.verdict", out)

    def test_nonblock_decision_with_scope_fail_closed(self):
        # 复验：MODE_SWITCH/DENY 等非 scope 决策带 scope/数值 usage → fail-closed。
        self.reserve("executor", "e1")
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "decision", "decision_event_id": "d1",
                                "ts": self._TS, "verdict": "MODE_SWITCH_REQUIRED",
                                "scope": "outer", "observed_usage": 3,
                                "effective_ceiling": 5}) + "\n")
        c, out, _ = self.reserve("executor", "e2")
        self.assertEqual(out, "FAIL_CLOSED:event_field:decision.nonblock_scope", out)

    def test_nonblock_decision_missing_usage_fields_fail_closed(self):
        # 复验：DENY 缺 observed_usage/effective_ceiling 字段 → fail-closed（须显式 null）。
        self.reserve("executor", "e1")
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "decision", "decision_event_id": "d2",
                                "ts": self._TS, "verdict": "DENY:unknown_role",
                                "scope": None}) + "\n")   # 缺 observed_usage/effective_ceiling
        c, out, _ = self.reserve("executor", "e2")
        self.assertTrue(out.startswith("FAIL_CLOSED:event_field:decision.observed_usage_must_null"), out)

    def test_spawn_succeeded_missing_fields_fail_closed(self):
        # 复验3-3：spawn_succeeded 缺 ts/instance_id → fail-closed。
        self.reserve("executor", "e1")
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "spawn_succeeded", "reservation_id": "e1"}) + "\n")
        c, out, _ = self.reserve("executor", "e2")
        self.assertEqual(c, 30, out)
        self.assertTrue(out.startswith("FAIL_CLOSED:event_field:spawn_succeeded"), out)

    def test_unknown_event_fail_closed(self):
        # finding 6：未知事件类型 → fail-closed。
        self.reserve("executor", "e1")
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "teleport", "reservation_id": "z"}) + "\n")
        c, out, _ = self.reserve("executor", "e2")
        self.assertEqual(out, "FAIL_CLOSED:unknown_event:teleport", out)

    def test_malformed_config_fail_closed_not_crash(self):
        # finding 6：畸形 config 必须 fail-closed(30)，而非未捕获异常 exit 1。
        self.set_config(max_outer_loops="abc")
        c, out, _ = self.reserve("outer-reviewer", "e1", rnd=1)
        self.assertEqual(c, 30, out)
        self.assertTrue(out.startswith("FAIL_CLOSED:config_type"), out)

    def _block_outer(self):
        self.set_config(max_outer_loops=0)
        c, out, _ = self.reserve("outer-reviewer", "blk", rnd=1)
        self.assertEqual(out, "BLOCK:budget_exhausted")
        return self.last_block_decision("outer")


if __name__ == "__main__":
    unittest.main(verbosity=2)
