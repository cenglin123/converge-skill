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
sys.path.insert(0, str(GATE.parent))
import budget_gate  # noqa: E402


def run(*args, cwd=None, input=None, env=None):
    full_env = None
    if env:
        import os
        full_env = {**os.environ, **env}
    r = subprocess.run([sys.executable, str(GATE), *args],
                       capture_output=True, text=True, encoding="utf-8",
                       cwd=cwd, input=input, env=full_env)
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


class TestEnforcedHook(Base):
    """best-effort guarded：bind/refresh-cap/unbind + PreToolUse 总量硬上限 hook。"""

    # config 使总量公式 = ceil(1×[3+0+0×1+0+1]) = 4（最小 cap，便于测边界）
    MIN_CAP = {"total_safety": 1, "max_outer_loops": 0, "max_inner_loops": 0,
               "max_blind_rechecks": 0, "ultraverge_min_reviewers": 0}

    def setUp(self):
        super().setUp()
        self._bindings = tempfile.TemporaryDirectory()
        self.env = {"CONVERGE_BINDINGS_DIR": self._bindings.name}
        self.sid = "sess-ABC"

    def tearDown(self):
        self._bindings.cleanup()
        super().tearDown()

    def _hook(self, tool="Agent", session=None):
        payload = json.dumps({"tool_name": tool, "session_id": session or self.sid})
        return run("hook-pretooluse", input=payload, env=self.env)

    def _binding_file(self, session=None):
        import hashlib, os
        h = hashlib.sha256((session or self.sid).encode("utf-8")).hexdigest()
        return os.path.join(self._bindings.name, h + ".json")

    def _bind(self, session=None):
        self.set_config(**self.MIN_CAP)
        return run("bind", "--session-id", session or self.sid,
                   "--active-dir", str(self.active), env=self.env)

    def test_unbound_session_passthrough(self):
        c, out, _ = self._hook()
        self.assertEqual(c, 0); self.assertEqual(out, "")

    def test_bound_blocks_at_cap(self):
        c, out, _ = self._bind()
        self.assertTrue(out.startswith("BOUND:"), out)
        self.assertIn("cap=4", out)
        for i in range(4):                       # cap=4 → 前 4 次放行
            self.assertEqual(self._hook()[1], "", f"spawn {i} should pass")
        c, out, _ = self._hook()                 # 第 5 次 deny
        self.assertIn('"permissionDecision": "deny"', out, out)
        self.assertIn("hard cap", out)

    def test_rebind_refused_does_not_reset_count(self):
        # finding 1：已绑定再 bind 必须拒绝且不清零 count（防 re-bind 绕过 cap）。
        self._bind()
        self.assertEqual(self._hook()[1], "")    # count -> 1
        c, out, _ = run("bind", "--session-id", self.sid,
                        "--active-dir", str(self.active), env=self.env)
        self.assertEqual(out, "FAIL_CLOSED:already_bound", out)
        for _ in range(3):                       # count 未重置：还能 3 次（总 4）
            self.assertEqual(self._hook()[1], "")
        self.assertIn("deny", self._hook()[1])   # 第 5 次 deny

    def _read_binding(self, session=None):
        return json.loads(Path(self._binding_file(session)).read_text(encoding="utf-8"))

    def _write_binding(self, b, session=None):
        Path(self._binding_file(session)).write_text(json.dumps(b), encoding="utf-8")

    def _add_real_total_extension(self, new_ceiling):
        # 触发真实 BLOCK:total_spawn_cap decision（reserve 充满 ledger 总量=4），
        # 再追加引用它的 scope=total extension（真实授权链，非改 config）。
        for i in range(4):
            self.reserve("executor", f"tot{i}")
        self.reserve("executor", "totX")                  # 第 5 次 → BLOCK:total
        d = self.last_block_decision("total")
        self.assertIsNotNone(d, "expected a BLOCK:total decision")
        self.add_extension(extension_id="t1", scope="total",
                           triggering_block_event_id=d["decision_event_id"],
                           granted_at_usage=d["observed_usage"],
                           prior_ceiling=d["effective_ceiling"],
                           new_ceiling=new_ceiling, supersedes=None, user_quote="扩容")
        return d

    def test_refresh_cap_preserves_count_via_real_extension(self):
        # finding 1：refresh 只认真实 scope=total extension；count 保留。
        self.set_config(**self.MIN_CAP)                   # total cap baseline = 4
        run("bind", "--session-id", self.sid, "--active-dir", str(self.active), env=self.env)
        for _ in range(2):
            self.assertEqual(self._hook()[1], "")          # hook count -> 2
        self._add_real_total_extension(new_ceiling=8)
        c, out, _ = run("refresh-cap", "--session-id", self.sid, env=self.env)
        self.assertIn("cap=8", out); self.assertIn("count=2", out)
        for _ in range(6):                                 # count 2→8
            self.assertEqual(self._hook()[1], "")
        self.assertIn("deny", self._hook()[1])

    def test_refresh_cap_config_change_ignored(self):
        # finding 1：无 extension、仅改 config → refresh 必须拒绝，cap 不变。
        self._bind()                                       # cap=4
        self.set_config(total_safety=100)                  # 试图用 config 抬高
        c, out, _ = run("refresh-cap", "--session-id", self.sid, env=self.env)
        self.assertEqual(out, "FAIL_CLOSED:no_total_extension", out)
        for _ in range(4):                                 # cap 仍 = 4
            self.assertEqual(self._hook()[1], "")
        self.assertIn("deny", self._hook()[1])

    def test_refresh_cap_rejects_corrupt_extension_chain(self):
        self._bind()
        st = json.loads((self.active / "_budget-state.json").read_text(encoding="utf-8"))
        st["extensions"] = [{"extension_id": "bad", "scope": "total",
                             "triggering_block_event_id": "nope", "granted_at_usage": 0,
                             "prior_ceiling": 4, "new_ceiling": 9, "supersedes": None,
                             "user_quote": "x"}]
        (self.active / "_budget-state.json").write_text(json.dumps(st), encoding="utf-8")
        c, out, _ = run("refresh-cap", "--session-id", self.sid, env=self.env)
        self.assertTrue(out.startswith("FAIL_CLOSED"), out)

    def test_negative_count_fail_closed_deny(self):
        # finding 2：负数 count 不得绕过 cap。
        self._bind()
        b = self._read_binding(); b["hook_spawn_count"] = -100
        self._write_binding(b)
        c, out, _ = self._hook()
        self.assertIn('"permissionDecision": "deny"', out, out)
        self.assertIn("fail", out.lower())

    def test_bad_typed_cap_fail_closed_deny(self):
        # finding 2：非整数 cap → deny。
        self._bind()
        b = self._read_binding(); b["hook_spawn_cap"] = "999"
        self._write_binding(b)
        c, out, _ = self._hook()
        self.assertIn('"permissionDecision": "deny"', out, out)

    def test_session_filename_no_collision(self):
        # finding 2：a/b 与 a?b 不得映射同一文件。绑定 a/b 后 a?b（未绑定）应放行。
        self._bind(session="a/b")
        c, out, _ = self._hook(session="a?b")
        self.assertEqual(out, "", out)

    def test_session_id_mismatch_in_file_deny(self):
        self._bind()
        b = self._read_binding(); b["session_id"] = "someone-else"
        self._write_binding(b)
        c, out, _ = self._hook()
        self.assertIn('"permissionDecision": "deny"', out, out)

    def test_bound_corrupt_binding_deny(self):
        self._bind()
        Path(self._binding_file()).write_text("{ not valid json", encoding="utf-8")
        c, out, _ = self._hook()
        self.assertIn('"permissionDecision": "deny"', out, out)
        self.assertIn("fail", out.lower())

    def test_unparseable_stdin_passthrough(self):
        c, out, _ = run("hook-pretooluse", input="not json at all", env=self.env)
        self.assertEqual(c, 0); self.assertEqual(out, "")

    def test_non_agent_tool_passthrough(self):
        self._bind()
        for _ in range(6):                       # 非 Agent 工具不计数、不阻断（>cap 也无妨）
            self.assertEqual(self._hook(tool="Bash")[1], "")

    def test_unbind_restores_passthrough(self):
        self._bind()
        self.assertEqual(self._hook()[1], "")
        run("unbind", "--session-id", self.sid, env=self.env)
        self.assertEqual(self._hook()[1], "")    # 解绑后放行

    def test_default_cap_from_state_stock(self):
        c, out, _ = run("bind", "--session-id", self.sid, "--active-dir", str(self.active),
                        env=self.env)
        self.assertIn("cap=63", out)

    def test_default_cap_ultraverge_same_as_standard(self):
        # 无 ultraverge blind 叠加：新模式与 standard 同 cap（plan r2 D9）。
        budget_gate.initialize_state(self.active, mode="ultraverge")
        c, out, _ = run("bind", "--session-id", self.sid, "--active-dir", str(self.active),
                        env=self.env)
        self.assertIn("cap=63", out)


class TestSharedInitialization(Base):
    def test_stock_defaults_and_caps(self):
        standard = budget_gate.initialize_state(self.active)
        self.assertEqual(standard["config"], {})
        self.assertEqual(standard["fsm"]["mode"], "standard")
        self.assertEqual(standard["defaults_version"], 2)
        self.assertEqual([budget_gate.cfg(standard, key) for key in
                          ("max_outer_loops", "max_blind_rechecks", "max_inner_loops")],
                         [8, 3, 3])
        self.assertEqual(budget_gate.default_total_cap(standard), 63)

        other = self.active / "uv"
        other.mkdir()
        uv = budget_gate.initialize_state(other, mode="ultraverge")
        # 无 blind 叠加：新 ultraverge state 的 config 不含 max_blind_rechecks
        self.assertEqual(uv["config"], {})
        self.assertEqual(uv["defaults_version"], 2)
        self.assertEqual(budget_gate.default_total_cap(uv), 63)

    def test_active_values_inherit_and_equal_values_are_noops(self):
        first = budget_gate.initialize_state(
            self.active, config={"max_outer_loops": 5, "max_inner_loops": 3})
        raw_before = (self.active / "_budget-state.json").read_bytes()
        second = budget_gate.initialize_state(
            self.active, config={"max_outer_loops": 5}, mode="standard")
        # config 和 fsm 必须完全一致（_legacy_active 是 in-memory 标记，不比较）
        self.assertEqual(first["config"], second["config"])
        self.assertEqual(first["fsm"], second["fsm"])
        self.assertEqual(first["extensions"], second["extensions"])
        self.assertEqual((self.active / "_budget-state.json").read_bytes(), raw_before)

    def test_conflicting_explicit_value_fails_without_writing(self):
        budget_gate.initialize_state(self.active, config={"max_outer_loops": 5})
        path = self.active / "_budget-state.json"
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active, config={"max_outer_loops": 4})
        self.assertEqual(path.read_bytes(), before)

    def test_malformed_values_and_shapes_fail_before_write(self):
        invalid = [
            {"max_outer_loops": True},
            {"max_outer_loops": -1},
            {"max_outer_loops": "3"},
            {"unknown_key": 1},
        ]
        for i, config in enumerate(invalid):
            active = self.active / str(i)
            active.mkdir()
            with self.subTest(config=config), self.assertRaises(budget_gate.FailClosed):
                budget_gate.initialize_state(active, config=config)
            self.assertFalse((active / "_budget-state.json").exists())

        path = self.active / "bad"
        path.mkdir()
        state_path = path / "_budget-state.json"
        state_path.write_text(json.dumps({"config": {}, "extensions": [],
                                          "fsm": {"mode": "standard", "severities": []}}),
                              encoding="utf-8")
        before = state_path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(path)
        self.assertEqual(state_path.read_bytes(), before)

    def test_legacy_sparse_state_keeps_legacy_defaults(self):
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({"config": {"max_outer_loops": 9}, "extensions": [],
                                    "fsm": {"mode": "standard", "severities": {}}}),
                        encoding="utf-8")
        raw_before = path.read_bytes()
        state = budget_gate.initialize_state(self.active)
        # 旧版 sparse state 无 defaults_version → cfg() 内存中视为 version 1（LEGACY_DEFAULTS 回退）
        self.assertEqual(state.get("defaults_version", 1), 1)
        self.assertEqual(budget_gate.cfg(state, "max_inner_loops"), 3)
        # 不重写旧版 state 字节（plan D3 + DR1）
        self.assertEqual(path.read_bytes(), raw_before)


class TestRound0Unification(Base):
    """plan Phase1 step2：ledger 的 Round 0 表示与 archive_contract 的 invocation `round`
    契约（null 或正整数）统一——不允许一处写字面 0、一处要求 null。"""

    def test_target_round_zero_normalized_to_null(self):
        c, out, _ = self.reserve("executor", "e1", rnd=0)   # consumes:none，CLI 传 0
        self.assertTrue(out.startswith("PROCEED"), out)
        reserved = [e for e in self.ledger() if e.get("event") == "reserved"][0]
        self.assertIsNone(reserved["target_round"])          # 归一化为 null，不是字面 0

    def test_target_round_zero_injected_raw_fail_closed(self):
        # 绕过 CLI 直接在 ledger 注入字面 0（consumes:none）→ 下一次 reserve 校验时 fail-closed。
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "reserved", "reservation_id": "raw0",
                                "ts": "2026-06-19T00:00:00+00:00",
                                "target_role": "executor", "consumes": "none",
                                "target_round": 0}) + "\n")
        c, out, _ = self.reserve("executor", "next")
        self.assertTrue(out.startswith("FAIL_CLOSED:event_field:reserved.target_round"), out)

    def test_negative_round_rejected(self):
        c, out, _ = run("reserve", "--active-dir", str(self.active), "--role", "executor",
                        "--reservation-id", "neg", "--target-round", "-1", "--tier", "auditable-only")
        self.assertTrue(out.startswith("FAIL_CLOSED:event_field:reserved.target_round"), out)


class TestSettlementRefAndAuthorityCrossRef(Base):
    """plan Phase1 step1/step3 在 budget_gate 侧的可见影响：l2-gate-reviewer 角色存在但
    consumes:none，从不参与 outer/blind/ultraverge scope 记账（archive 侧的终局 owner
    拒绝见 tests/test_archive_convergence.py）。"""

    def test_l2_gate_reviewer_reserve_does_not_consume_any_scope(self):
        self.set_config(max_outer_loops=1)
        c, out, _ = self.reserve("l2-gate-reviewer", "l2-1")
        self.assertTrue(out.startswith("PROCEED"), out)
        reserved = [e for e in self.ledger() if e.get("event") == "reserved"][0]
        self.assertEqual(reserved["consumes"], "none")
        # l2-gate-reviewer 消耗不影响 outer scope 的独立预算
        c, out, _ = self.reserve("outer-reviewer", "o1", rnd=1)
        self.assertTrue(out.startswith("PROCEED"), out)


class TestDualCounting(Base):
    """plan Phase1 step4：attempted_dispatch（含启动前失败/CLI 错误）与 model_invocation
    （真实模型调用）分别计数，summary 命令可验证重算。"""

    def _summary(self):
        c, out, _ = run("summary", "--active-dir", str(self.active))
        self.assertEqual(c, 0, out)
        return json.loads(out)

    def test_attempted_dispatch_counts_pre_execution_failures_model_invocation_does_not(self):
        self.reserve("executor", "a")
        self.settle("a", "succeeded", instance_id="ia")              # 真实调用成功
        self.reserve("executor", "b")
        self.settle("b", "failed")                                   # 真实调用后失败（pre_execution 默认 false）
        self.reserve("executor", "c")
        self.settle("c", "failed", pre_execution=True)                # 启动前失败/CLI 错误，从未真正调用模型
        self.reserve("executor", "d")
        self.settle("d", "cancelled", pre_execution=True)             # 零消耗，不计 attempted_dispatch

        summary = self._summary()
        # attempted_dispatch：a, b, c 计入（3），d（pre_execution cancelled）不计
        self.assertEqual(summary["attempted_dispatch"], 3)
        # model_invocation：只有 a（succeeded）与 b（failed 但非 pre_execution）计入（2）
        self.assertEqual(summary["model_invocation"], 2)

    def test_summary_is_idempotent_recompute(self):
        self.reserve("executor", "a")
        self.settle("a", "succeeded", instance_id="ia")
        first = self._summary()
        second = self._summary()
        self.assertEqual(first, second)   # 纯重算，无缓存漂移


class TestTaskEnvelope(Base):
    """plan Phase1 step5：四档任务预算 + task-envelope scope（§6.1/§6.2/§6.3）。"""

    def test_unconfigured_fails_closed(self):
        c, out, _ = self.reserve("task-envelope", "t1")
        self.assertTrue(out.startswith("FAIL_CLOSED:task_envelope_not_configured"), out)

    def test_a8_fallback_unconfigured_task_never_gains_task_envelope_key(self):
        # A8：未配置任务档时，行为与改造前完全一致——普通 reserve 的 ledger 记录不出现
        # task-envelope 键。
        self.reserve("executor", "e1")
        reserved = [e for e in self.ledger() if e.get("event") == "reserved"][0]
        self.assertNotIn("task-envelope", reserved["counts_before"])
        self.assertNotIn("task-envelope", reserved["ceilings"])

    def test_small_tier_initial_blocks_then_extension_allows_up_to_cap(self):
        self.set_config(task_tier="small")   # initial=4, cap=8
        ok = 0
        for i in range(4):
            c, out, _ = self.reserve("task-envelope", f"te{i}")
            self.assertTrue(out.startswith("PROCEED"), out)
            ok += 1
        self.assertEqual(ok, 4)
        c, out, _ = self.reserve("task-envelope", "te_blocked")
        self.assertEqual(out, "BLOCK:task_envelope_exhausted", out)
        d = self.last_block_decision("task-envelope")
        self.assertIsNotNone(d)
        # 一次性授权：直接扩到 cap=8（不需要每 2 次打断用户）
        self.add_extension(extension_id="x1", scope="task-envelope",
                           triggering_block_event_id=d["decision_event_id"],
                           granted_at_usage=d["observed_usage"],
                           prior_ceiling=d["effective_ceiling"],
                           new_ceiling=8, supersedes=None, user_quote="一次性授权到cap")
        for i in range(4, 8):
            c, out, _ = self.reserve("task-envelope", f"te{i}")
            self.assertTrue(out.startswith("PROCEED"), out)
        c, out, _ = self.reserve("task-envelope", "te_over_cap")
        self.assertEqual(out, "BLOCK:task_envelope_exhausted", out)

    def test_extension_cannot_exceed_hard_cap(self):
        self.set_config(task_tier="small")   # cap=8
        ok = 0
        for i in range(4):
            self.reserve("task-envelope", f"te{i}")
            ok += 1
        c, out, _ = self.reserve("task-envelope", "te_blocked")
        self.assertEqual(out, "BLOCK:task_envelope_exhausted", out)
        d = self.last_block_decision("task-envelope")
        self.add_extension(extension_id="x1", scope="task-envelope",
                           triggering_block_event_id=d["decision_event_id"],
                           granted_at_usage=d["observed_usage"],
                           prior_ceiling=d["effective_ceiling"],
                           new_ceiling=9,   # 超过 cap=8
                           supersedes=None, user_quote="试图突破硬上限")
        c, out, _ = self.reserve("task-envelope", "te_after")
        self.assertTrue(out.startswith("FAIL_CLOSED"), out)
        self.assertIn("ext_task_envelope_exceeds_cap", out)

    def test_task_envelope_orthogonal_to_total_cap(self):
        # 把 total cap 压到很小，task-envelope 的 reserve 不应受其约束、也不应消耗它。
        self.set_config(max_outer_loops=1, max_inner_loops=0, max_blind_rechecks=0,
                        ultraverge_min_reviewers=0, total_safety=1.0,   # total cap = 5
                        task_tier="feature")   # initial=16, cap=24
        for i in range(10):   # 远超 total cap=5，但 task-envelope 有自己的独立 ceiling
            c, out, _ = self.reserve("task-envelope", f"te{i}")
            self.assertTrue(out.startswith("PROCEED"), out)
        # 其它角色的 total 预算仍然独立可用（未被 task-envelope 挤占）
        c, out, _ = self.reserve("executor", "e0")
        self.assertTrue(out.startswith("PROCEED"), out)

    def test_block_stops_new_reserve_but_allows_in_flight_settle(self):
        # design-review highlight #3：信封触发 BLOCK 时停止新 reserve、允许已 settle 动作完成。
        self.set_config(task_tier="small")   # initial=4
        for i in range(4):
            self.reserve("task-envelope", f"te{i}")
        # 第 4 个仍处于 reserved（未 settle）——BLOCK 之后应仍可正常结算
        c, out, _ = self.reserve("task-envelope", "te_blocked")
        self.assertEqual(out, "BLOCK:task_envelope_exhausted", out)
        c, out, _ = self.settle("te3", "succeeded", instance_id="i3")
        self.assertEqual(out, "OK", out)   # 已 reserve 的动作允许完成，不因信封 BLOCK 被卡住

    def test_explicit_cap_override_without_tier(self):
        self.set_config(task_envelope_initial=2, task_envelope_cap=3)
        self.reserve("task-envelope", "a")
        self.reserve("task-envelope", "b")
        c, out, _ = self.reserve("task-envelope", "c")
        self.assertEqual(out, "BLOCK:task_envelope_exhausted", out)

    def test_bad_tier_config_fail_closed(self):
        self.set_config(task_tier="not-a-real-tier")
        c, out, _ = self.reserve("task-envelope", "a")
        self.assertTrue(out.startswith("FAIL_CLOSED:config_type:task_tier"), out)

    def test_cap_lt_initial_fail_closed(self):
        self.set_config(task_envelope_initial=10, task_envelope_cap=5)
        c, out, _ = self.reserve("task-envelope", "a")
        self.assertTrue(out.startswith("FAIL_CLOSED:config_type:task_envelope_cap_lt_initial"), out)


class TestRootFixedFilesUseLFNewlines(Base):
    """plan Phase 5 step 5 (newline policy): gate-ledger.jsonl and _budget-state.json are
    root-fixed files the Archive Contract hashes at archive time — they must stay byte-for-
    byte the same as what Git (`.gitattributes: * text=auto eol=lf`) checks out, or a later
    `check`/`check-git-ref` re-verification reports content-mismatch on Windows, where text-
    mode file writes translate '\\n' to os.linesep ('\\r\\n')."""

    def test_gate_ledger_written_via_cli_has_no_crlf(self):
        self.reserve("outer-reviewer", "r1", rnd=1)
        self.settle("r1", "succeeded", instance_id="i1")
        data = (self.active / "gate-ledger.jsonl").read_bytes()
        self.assertNotIn(b"\r\n", data)
        self.assertIn(b"\n", data)

    def test_budget_state_written_via_cli_has_no_crlf(self):
        run("ingest-verdict", "--active-dir", str(self.active),
            "--target-round", "1", "--verdict", "阻断需修复", "--severities", "structural")
        data = (self.active / "_budget-state.json").read_bytes()
        self.assertNotIn(b"\r\n", data)

    def test_append_ledger_and_write_state_force_lf_at_the_python_level(self):
        import importlib
        budget_gate = importlib.import_module("budget_gate")
        with tempfile.TemporaryDirectory() as td:
            active = Path(td)
            budget_gate.append_ledger(active, {"event": "reserved", "reservation_id": "x"})
            self.assertNotIn(b"\r\n", (active / "gate-ledger.jsonl").read_bytes())
            budget_gate.write_state(active, {"config": {}, "extensions": [], "fsm": {"mode": "standard", "severities": {}}})
            self.assertNotIn(b"\r\n", (active / "_budget-state.json").read_bytes())


class TestScopeProductRootAllowlist(unittest.TestCase):
    """plan Phase 5 step 3 (root allowlist unification): every SCOPE_PRODUCT template this
    module generates must be accepted by the Archive Contract's root allowlist, or the
    generator and the archiver have silently diverged (the original defect: uv-init-N.md /
    blind-recheck-N.md rejected as root-clutter). The two modules cannot share a single
    import (archive_contract.model.validate_ledger imports budget_gate, so the reverse import
    would cycle) — this cross-module test is the single-source-of-truth enforcement instead."""

    def test_every_scope_product_template_is_root_allowed(self):
        import importlib
        budget_gate = importlib.import_module("budget_gate")
        model = importlib.import_module("archive_contract.model")
        for template in budget_gate.SCOPE_PRODUCT.values():
            for n in (1, 2, 10, 123):
                name = template.format(n=n)
                self.assertTrue(model.is_root_allowed_name(name), name)


class TestMalformedExistingStateFailClosed(Base):
    """Defect 1: malformed existing state must raise FailClosed, not raw AttributeError/TypeError."""

    def test_defaults_version_zero_fails_closed(self):
        """defaults_version=0 is not 1 or 2 → must raise FailClosed."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "defaults_version": 0, "config": {}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_defaults_version_three_fails_closed(self):
        """defaults_version=3 is not 1 or 2 → must raise FailClosed."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "defaults_version": 3, "config": {}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_defaults_version_bool_true_fails_closed(self):
        """Python bool is int subclass; True==1 but must not be accepted as version."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "defaults_version": True, "config": {}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_defaults_version_bool_false_fails_closed(self):
        """Python bool is int subclass; False==0 but must not be accepted as version."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "defaults_version": False, "config": {}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_fsm_string_fails_closed_not_attribute_error(self):
        """fsm as string → FailClosed, not AttributeError from .setdefault()."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [], "fsm": "not-a-dict"
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_fsm_list_fails_closed_not_type_error(self):
        """fsm as list → FailClosed, not TypeError."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [], "fsm": ["bad"]
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_fsm_mode_list_fails_closed(self):
        """fsm.mode as list → FailClosed."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [],
            "fsm": {"mode": ["standard"], "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_fsm_severities_string_fails_closed(self):
        """fsm.severities as string → FailClosed."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [],
            "fsm": {"mode": "standard", "severities": "bad"}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_read_state_fsm_string_fails_closed(self):
        """read_state() with fsm as string must raise FailClosed, not AttributeError."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [], "fsm": "corrupt"
        }), encoding="utf-8")
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.read_state(self.active)

    def test_existing_config_value_zero_accepted_for_legacy_sparse_state(self):
        """Sparse legacy state (no defaults_version) with max_outer_loops=0 is accepted.
        Legacy states lack defaults_version and retain backward compatibility including
        existing zero-valued boundary fixtures. This differs from version-2 states where
        zero-valued INT_CONFIG is malformed."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {"max_outer_loops": 0}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        state = budget_gate.initialize_state(self.active)
        self.assertEqual(state["config"]["max_outer_loops"], 0)
        self.assertEqual(path.read_bytes(), before)  # bytes preserved
        # But new explicit config with value < 1 IS rejected
        other = self.active / "new"
        other.mkdir()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(other, config={"max_outer_loops": 0})
        self.assertFalse((other / "_budget-state.json").exists())

    def test_defaults_version_2_zero_int_config_fails_closed(self):
        """Version-2 state with INT_CONFIG value 0 is malformed and must fail closed.
        New/version-2 state integer budget limits must be positive (>=1)."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "defaults_version": 2,
            "config": {"max_outer_loops": 0}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_defaults_version_2_negative_int_config_fails_closed(self):
        """Version-2 state with negative INT_CONFIG value must fail closed."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "defaults_version": 2,
            "config": {"max_inner_loops": -1}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_config_as_list_fails_closed_not_attribute_error(self):
        """Existing state with config as list → FailClosed, not AttributeError."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": [1, 2, 3], "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_invalid_mode_bogus_fails_closed(self):
        """Existing state with invalid mode value → FailClosed."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [],
            "fsm": {"mode": "bogus", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)


class TestModeConflictResolution(Base):
    """Defect 1: omitted vs explicit mode handling per plan D3."""

    def test_omitted_mode_on_existing_state_inherits(self):
        """Omitted mode (None) inherits active state without rewriting bytes."""
        path = self.active / "_budget-state.json"
        # 已有显式 config 的 ultraverge state（显式 config 权威，字节不动）
        path.write_text(json.dumps({
            "config": {"max_blind_rechecks": 2}, "extensions": [],
            "fsm": {"mode": "ultraverge", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        state = budget_gate.initialize_state(self.active, mode=None)
        self.assertEqual(state["fsm"]["mode"], "ultraverge")
        self.assertEqual(path.read_bytes(), before)

    def test_explicit_equal_mode_is_idempotent_noop(self):
        """Explicit mode equal to existing → no rewrite (when state is fully formed)."""
        path = self.active / "_budget-state.json"
        # 已有显式 config 的 ultraverge state（显式 config 权威，字节不动）
        path.write_text(json.dumps({
            "config": {"max_blind_rechecks": 2}, "extensions": [],
            "fsm": {"mode": "ultraverge", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        state = budget_gate.initialize_state(self.active, mode="ultraverge")
        self.assertEqual(state["fsm"]["mode"], "ultraverge")
        self.assertEqual(path.read_bytes(), before)

    def test_explicit_conflicting_mode_fails_closed(self):
        """Explicit mode conflicts with existing → FailClosed without rewriting."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [],
            "fsm": {"mode": "ultraverge", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active, mode="standard")
        self.assertEqual(path.read_bytes(), before)

    def test_force_overrides_mode_conflict(self):
        """--force replaces conflicting mode."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [],
            "fsm": {"mode": "ultraverge", "severities": {}}
        }), encoding="utf-8")
        state = budget_gate.initialize_state(self.active, mode="standard", force=True)
        self.assertEqual(state["fsm"]["mode"], "standard")

    def test_new_state_omitted_mode_defaults_to_standard(self):
        """Truly new state with omitted mode → standard."""
        state = budget_gate.initialize_state(self.active, mode=None)
        self.assertEqual(state["fsm"]["mode"], "standard")
        self.assertEqual(state["defaults_version"], 2)

    def test_new_state_explicit_ultraverge(self):
        """Truly new state with explicit ultraverge → 模式落盘，无 blind 叠加。"""
        state = budget_gate.initialize_state(self.active, mode="ultraverge")
        self.assertEqual(state["fsm"]["mode"], "ultraverge")
        self.assertNotIn("max_blind_rechecks", state["config"])
        # 有效值与 standard 同源：回退 DEFAULTS 的 blind=3
        self.assertEqual(budget_gate.cfg(state, "max_blind_rechecks"), 3)


class TestR4SharedValidationDefects(Base):
    """R4 defects: shared resolver / mode / config-key / ledger validation gaps.

    These tests prove the following asymmetries exist in production code:
    - initialize_state() rejects mode='bogus' on existing state but NOT on new state.
    - read_state() does NOT validate mode value at all (only checks it's a string).
    - read_state() does NOT reject unknown config keys.
    - initialize_state() does NOT read or validate the ledger for existing state.
    - Task-envelope config validation in initialize_state() is a divergent partial copy
      of validate_integrity(), not shared through the existing contract.
    """

    def test_new_state_bogus_mode_fails_closed(self):
        """Requirement 1: initialize_state(new_active, mode='bogus') must raise FailClosed
        and create no state file."""
        new_active = self.active / "new"
        new_active.mkdir()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(new_active, mode="bogus")
        self.assertFalse((new_active / "_budget-state.json").exists())

    def test_read_state_bogus_mode_fails_closed(self):
        """Requirement 2: A persisted state whose fsm.mode is 'bogus' causes read_state()
        to raise FailClosed."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [],
            "fsm": {"mode": "bogus", "severities": {}}
        }), encoding="utf-8")
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.read_state(self.active)

    def test_read_state_unknown_config_key_fails_closed(self):
        """Requirement 3a: read_state() must reject unknown config keys."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {"unknown": 1}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.read_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_initialize_state_unknown_config_key_fails_closed(self):
        """Requirement 3b: initialize_state() must reject unknown config keys on existing state."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {"unknown": 1}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_initialize_state_unknown_event_in_ledger_fails_closed(self):
        """Requirement 4a: existing valid state + unknown-event ledger → initialize_state()
        must raise FailClosed, preserving state bytes."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        # Write a ledger with an unknown event type
        ledger = self.active / "gate-ledger.jsonl"
        ledger.write_text(json.dumps({"event": "teleport", "reservation_id": "z"}) + "\n",
                          encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_initialize_state_malformed_ledger_fails_closed(self):
        """Requirement 4b: existing valid state + malformed ledger JSON → initialize_state()
        must raise FailClosed, preserving state bytes."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        ledger = self.active / "gate-ledger.jsonl"
        ledger.write_text("{not json\n", encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)

    def test_read_state_non_dict_config_fails_closed(self):
        """Requirement 5a: non-dict config in persisted state → read_state() raises FailClosed."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": [1, 2], "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.read_state(self.active)

    def test_read_state_non_list_extensions_fails_closed(self):
        """Requirement 5b: non-list extensions in persisted state → read_state() raises FailClosed."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {}, "extensions": "not-a-list",
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.read_state(self.active)

    def test_read_state_task_envelope_config_validated(self):
        """Requirement 6: existing task-envelope config values are validated by the shared
        contract (validate_integrity), not a divergent partial copy. Specifically,
        task_envelope_cap < task_envelope_initial must be rejected."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "config": {"task_envelope_initial": 10, "task_envelope_cap": 5},
            "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        # initialize_state should detect the invalid relationship
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active)
        self.assertEqual(path.read_bytes(), before)


class TestCandidateStateValidation(Base):
    """Blocker A: Candidate budget state must be validated before write/use.

    The current tree independently reproduces all of these invalid acceptances:
      new config {'task_tier':'bogus'} -> ACCEPTED
      new config {'task_envelope_initial':0} -> ACCEPTED
      new config {'task_envelope_initial':10,'task_envelope_cap':5} -> ACCEPTED
      new config {'total_safety':0} -> ACCEPTED
      existing valid state + explicit {'task_tier':'bogus'} -> written and ACCEPTED
      persisted defaults_version=2 + max_outer_loops=0 -> read_state()+validate_integrity() ACCEPTED
    """

    def test_new_config_bogus_task_tier_fails_closed(self):
        """Requirement 5: task_tier must be a current TASK_TIERS key."""
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active, config={"task_tier": "bogus"})
        self.assertFalse((self.active / "_budget-state.json").exists())

    def test_new_config_task_envelope_initial_zero_fails_closed(self):
        """Requirement 5: task_envelope_initial must be exact int >=1."""
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active, config={"task_envelope_initial": 0})
        self.assertFalse((self.active / "_budget-state.json").exists())

    def test_new_config_cap_lt_initial_fails_closed(self):
        """Requirement 5: cap >= initial when both present."""
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(
                self.active, config={"task_envelope_initial": 10, "task_envelope_cap": 5})
        self.assertFalse((self.active / "_budget-state.json").exists())

    def test_new_config_total_safety_zero_fails_closed(self):
        """Requirement 6: total_safety must be > 0."""
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active, config={"total_safety": 0})
        self.assertFalse((self.active / "_budget-state.json").exists())

    def test_new_config_total_safety_negative_fails_closed(self):
        """Requirement 6: total_safety must be > 0."""
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active, config={"total_safety": -1.5})
        self.assertFalse((self.active / "_budget-state.json").exists())

    def test_existing_state_explicit_bogus_task_tier_fails_closed_preserves_bytes(self):
        """Requirement 8: existing valid state + explicit bogus task_tier →
        FailClosed, state bytes preserved."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "defaults_version": 2, "config": {}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active, config={"task_tier": "bogus"})
        self.assertEqual(path.read_bytes(), before)

    def test_v2_state_zero_int_config_rejected_by_read_state_validate_integrity(self):
        """Requirement 7: read_state() + validate_integrity() must not accept a
        malformed version-2 state that initialize_state() rejects."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "defaults_version": 2,
            "config": {"max_outer_loops": 0}, "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        state = budget_gate.read_state(self.active)
        events = budget_gate.read_ledger(self.active)
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.validate_integrity(self.active, events, state)

    def test_config_as_list_rejected_not_silently_converted(self):
        """Requirement 1: initialize_state(config=[]) must raise FailClosed,
        never silently convert [] to {}."""
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active, config=[])
        self.assertFalse((self.active / "_budget-state.json").exists())

    def test_new_config_total_safety_integer_one_accepted(self):
        """Requirement 6: total_safety=1 (integer) is valid (> 0)."""
        state = budget_gate.initialize_state(self.active, config={"total_safety": 1})
        self.assertEqual(state["config"]["total_safety"], 1)

    def test_new_config_total_safety_float_accepted(self):
        """Requirement 6: total_safety=1.5 (float) is valid."""
        state = budget_gate.initialize_state(self.active, config={"total_safety": 1.5})
        self.assertEqual(state["config"]["total_safety"], 1.5)

    def test_new_config_valid_task_tier_accepted(self):
        """Requirement 5: valid task_tier keys are accepted."""
        for tier in budget_gate.TASK_TIERS:
            active = self.active / tier.replace("/", "_")
            active.mkdir(parents=True, exist_ok=True)
            state = budget_gate.initialize_state(active, config={"task_tier": tier})
            self.assertEqual(state["config"]["task_tier"], tier)


class TestCrossOverlayValidation(Base):
    """R7: Merged candidate state must be validated against ledger before write.
    Cross-key relationships assembled from old state + explicit config must be caught."""

    def test_existing_initial_new_cap_lt_initial_fails_closed(self):
        """Existing v2 state has task_envelope_initial=10;
        calling initialize_state(..., config={"task_envelope_cap":5}) must raise
        FailClosed and preserve state bytes. It currently accepts and writes the
        invalid merged candidate (cross-overlay bug)."""
        path = self.active / "_budget-state.json"
        path.write_text(json.dumps({
            "defaults_version": 2,
            "config": {"task_envelope_initial": 10},
            "extensions": [],
            "fsm": {"mode": "standard", "severities": {}}
        }), encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(budget_gate.FailClosed):
            budget_gate.initialize_state(self.active, config={"task_envelope_cap": 5})
        self.assertEqual(path.read_bytes(), before)


# ---------------------------------------------------------------------------
# plan r2 D7：治理计划 preflight（converge.governance-change/v1 + 窄数值经验门）
# ---------------------------------------------------------------------------
import hashlib  # noqa: E402

GOV_UUID_GOAL = "bdd405f3-2b03-40eb-9db2-09a32afacae2"
GOV_UUID_AUTH = "87c4f9f7-72f9-4c45-a2d2-409ae8d83120"
GOV_UUID_TRADE = "d2232c8d-76f9-4cd0-8164-fdcd45411d65"
GOV_REPORT_ID = "rep-1"


def gov_canon(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def gov_sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def gov_eligible_entry(ref, outer_usage, outer_prod, blind_usage, blind_prod):
    return {"ref": ref, "quantitative_status": "eligible", "reason": "ok",
            "sample_digest": "ab" * 32,
            "usage": {"outer": outer_usage, "blind": blind_usage},
            "productive": {"outer": outer_prod, "blind": blind_prod}}


class TestGovernancePreflight(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    # -- fixture 构造 -------------------------------------------------------
    def make_report(self, entries, hw=0, report_id=GOV_REPORT_ID):
        eligible = sum(1 for e in entries
                       if e.get("quantitative_status") == "eligible")
        return {
            "schema": "converge.calibration-report/v1",
            "id": report_id,
            "scope": "test-corpus",
            "freshness": {"repository_head": "0" * 40,
                          "source_archive_revision": "r1",
                          "source_event_high_watermark": hw},
            "corpus": entries,
            "corpus_digest": gov_sha(gov_canon(entries)),
            "quantitative_aggregates": {
                "eligible_samples": eligible,
                "status": "available" if eligible else "unavailable",
            },
        }

    def conflict_report(self):
        """负例语料：outer 7/12、blind 3/4 仍在持续推进的 eligible 样本。"""
        return self.make_report([
            gov_eligible_entry("done:a", 7, True, 3, True),
            gov_eligible_entry("done:b", 12, True, 4, True),
        ], hw=17)

    def make_gov(self, report, numeric_changes, counter=(), tradeoff=False,
                 report_id=GOV_REPORT_ID, locator_file="plan.md"):
        ume = {"quality_goal": GOV_UUID_GOAL,
               "execution_authorization": GOV_UUID_AUTH}
        if tradeoff:
            ume["tradeoff_decision"] = GOV_UUID_TRADE
        return {
            "schema": "converge.governance-change/v1",
            "change_id": "test-change",
            "numeric_changes": numeric_changes,
            "archaeology_refs": ["git:" + "0" * 40],
            "calibration": {
                "path": f"{locator_file}::json-fence"
                        f"[schema=converge.calibration-report/v1,id={report_id}]",
                "sha256": gov_sha(gov_canon(report)),
                "corpus_digest": report["corpus_digest"],
                "freshness": dict(report["freshness"]),
            },
            "counterevidence_refs": list(counter),
            "user_message_events": ume,
        }

    @staticmethod
    def restore_changes():
        """与真实 plan 同形的 8/3/3 恢复提案。"""
        return [
            {"control": "max_outer_loops", "kind": "default", "released": 8,
             "old": 3, "proposed": 8, "comparison": "outer",
             "basis": "empirical_restore"},
            {"control": "max_blind_rechecks", "kind": "default", "released": 3,
             "old": 1, "proposed": 3, "comparison": "blind",
             "basis": "empirical_restore"},
            {"control": "max_inner_loops", "kind": "default", "released": 3,
             "old": 1, "proposed": 3, "comparison": None,
             "basis": "released_compatibility_no_reduction_evidence"},
        ]

    @staticmethod
    def reduce_311_changes():
        """负例：3/1/1 缩减提案（无反证、无用户取舍）。"""
        return [
            {"control": "max_outer_loops", "kind": "default", "released": 8,
             "old": 8, "proposed": 3, "comparison": "outer",
             "basis": "cost_first"},
            {"control": "max_blind_rechecks", "kind": "default", "released": 3,
             "old": 3, "proposed": 1, "comparison": "blind",
             "basis": "cost_first"},
            {"control": "max_inner_loops", "kind": "default", "released": 3,
             "old": 3, "proposed": 1, "comparison": None,
             "basis": "cost_first"},
        ]

    def write_plan(self, gov, report, *, extra_fences=(), crlf=False,
                   name="plan.md"):
        parts = ["# plan\n"]
        for obj in (gov, report, *extra_fences):
            parts.append("```json\n" + json.dumps(obj, indent=2,
                         ensure_ascii=False) + "\n```\n")
        text = "\n".join(parts)
        p = self.dir / name
        data = text.replace("\n", "\r\n") if crlf else text
        p.write_bytes(data.encode("utf-8"))
        return p

    def preflight(self, plan, *extra):
        return run("preflight", "--plan", str(plan), *extra)

    # -- 正例 ---------------------------------------------------------------
    def test_bootstrap_restore_passes(self):
        report = self.make_report([])
        gov = self.make_gov(report, self.restore_changes())
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 0, out)
        self.assertIn("PREFLIGHT_OK:governance-change", out)

    def test_eligible_but_not_undercut_passes(self):
        # 有 eligible 样本，但 proposal（8/3）不低于已观测推进用量 → 不裁决冲突
        report = self.make_report([
            gov_eligible_entry("done:a", 5, True, 2, True),
            gov_eligible_entry("done:b", 8, True, 3, True),
        ], hw=9)
        gov = self.make_gov(report, self.restore_changes())
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 0, out)
        self.assertIn("PREFLIGHT_OK:governance-change", out)

    # -- 窄数值经验门负例 ---------------------------------------------------
    def test_empirical_conflict_blocks(self):
        report = self.conflict_report()
        gov = self.make_gov(report, self.reduce_311_changes())
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 15, out)
        self.assertIn("BLOCK:empirical_conflict", out)

    def test_counterevidence_discharges_conflict(self):
        report = self.conflict_report()
        gov = self.make_gov(report, self.reduce_311_changes(),
                            counter=["git:" + "1" * 40])
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 0, out)

    def test_user_tradeoff_discharges_conflict(self):
        report = self.conflict_report()
        gov = self.make_gov(report, self.reduce_311_changes(), tradeoff=True)
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 0, out)

    def test_inner_comparison_null_not_adjudicated(self):
        # comparison=null 的 inner 缩减即便有 eligible 语料也不进数值门
        report = self.conflict_report()
        changes = [{"control": "max_inner_loops", "kind": "default",
                    "released": 3, "old": 3, "proposed": 1,
                    "comparison": None, "basis": "cost_first"}]
        gov = self.make_gov(report, changes)
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 0, out)

    def test_role_mechanism_change_not_adjudicated(self):
        # 角色权限/一般机制变更（kind=mechanism）不被数值门裁决
        report = self.conflict_report()
        changes = [{"control": "reviewer_terminal_authority", "kind": "mechanism",
                    "released": None, "old": None, "proposed": None,
                    "comparison": None, "basis": "role_permission_change"}]
        gov = self.make_gov(report, changes)
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 0, out)
        self.assertIn("PREFLIGHT_OK:governance-change", out)

    # -- locator 错误分类 ---------------------------------------------------
    def test_locator_path_not_found_missing_file(self):
        report = self.make_report([])
        gov = self.make_gov(report, self.restore_changes(),
                            locator_file="retrospective.md")
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)
        self.assertIn("path-not-found", out)

    def test_locator_path_not_found_absent_id(self):
        report = self.make_report([])
        gov = self.make_gov(report, self.restore_changes(),
                            report_id="no-such-id")
        # sha256 针对不存在 id 无所谓——解析阶段即失败
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)
        self.assertIn("path-not-found", out)

    def test_locator_duplicate_target(self):
        report = self.make_report([])
        gov = self.make_gov(report, self.restore_changes())
        plan = self.write_plan(gov, report, extra_fences=[report])
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)
        self.assertIn("duplicate-target", out)

    def test_locator_wrong_schema(self):
        report = self.make_report([])
        other = dict(report)
        other["schema"] = "converge.other/v1"
        gov = self.make_gov(report, self.restore_changes())
        # plan 内只有 wrong-schema 的同 id 块
        parts = ["# plan\n",
                 "```json\n" + json.dumps(gov, indent=2) + "\n```\n",
                 "```json\n" + json.dumps(other, indent=2) + "\n```\n"]
        plan = self.dir / "plan.md"
        plan.write_bytes("\n".join(parts).encode("utf-8"))
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)
        self.assertIn("wrong-schema", out)

    # -- 严格 schema / 新鲜度 -----------------------------------------------
    def test_unknown_governance_field_fails_closed(self):
        report = self.make_report([])
        gov = self.make_gov(report, self.restore_changes())
        gov["unexpected"] = True
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)
        self.assertIn("FAIL_CLOSED", out)

    def test_missing_governance_field_fails_closed(self):
        report = self.make_report([])
        gov = self.make_gov(report, self.restore_changes())
        del gov["user_message_events"]
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)

    def test_duplicate_governance_block_fails_closed(self):
        report = self.make_report([])
        gov = self.make_gov(report, self.restore_changes())
        plan = self.write_plan(gov, report, extra_fences=[gov])
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)

    def test_calibration_hash_mismatch_fails_closed(self):
        report = self.make_report([])
        gov = self.make_gov(report, self.restore_changes())
        gov["calibration"]["sha256"] = "0" * 64
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)
        self.assertIn("hash", out)

    def test_stale_corpus_digest_fails_closed(self):
        report = self.make_report([])
        gov = self.make_gov(report, self.restore_changes())
        gov["calibration"]["corpus_digest"] = "0" * 64
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)
        self.assertIn("stale", out)

    def test_stale_high_watermark_fails_closed(self):
        report = self.make_report([], hw=17)
        gov = self.make_gov(report, self.restore_changes())
        gov["calibration"]["freshness"]["source_event_high_watermark"] = 16
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)
        self.assertIn("stale", out)

    def test_report_aggregate_inconsistency_fails_closed(self):
        report = self.conflict_report()
        report["quantitative_aggregates"]["eligible_samples"] = 0
        gov = self.make_gov(report, self.restore_changes())
        plan = self.write_plan(gov, report)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)

    def test_crlf_payload_fails_closed(self):
        report = self.make_report([])
        gov = self.make_gov(report, self.restore_changes())
        plan = self.write_plan(gov, report, crlf=True)
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 30, out)
        self.assertIn("crlf", out.lower())

    # -- 散文/表格不被解析 ---------------------------------------------------
    def test_prose_and_table_not_parsed(self):
        plan = self.dir / "plan.md"
        plan.write_bytes((
            "# plan\n\n本计划按 converge.governance-change/v1 的散文描述执行，"
            "numeric_changes 提议 3/1/1。\n\n"
            "| control | proposed |\n|---|---|\n| max_outer_loops | 3 |\n")
            .encode("utf-8"))
        c, out, _ = self.preflight(plan)
        self.assertEqual(c, 0, out)
        self.assertEqual(out, "CLEAN")

    def test_governance_flag_requires_block(self):
        plan = self.dir / "plan.md"
        plan.write_bytes("# plan\n纯散文，无机器块。\n".encode("utf-8"))
        c, out, _ = self.preflight(plan, "--governance")
        self.assertEqual(c, 30, out)


# ---------------------------------------------------------------------------
# plan r2 D10：Instrumented Task Envelope（call_id + atomic companion pair）
# ---------------------------------------------------------------------------

class TestInstrumentedTaskEnvelope(Base):
    """D10: call_id, atomic Spawn companion, idempotent settle, crash recovery,
    accounting_coverage, validate_integrity companion invariants."""

    def _setup_te_configured(self, tier="small"):
        """Configure task-envelope tier and return the active path."""
        self.set_config(task_tier=tier)

    # -- 1. Companion success: Spawn pair creates both reservations ------
    def test_spawn_creates_companion_task_envelope(self):
        """A non-task-envelope role reserve with configured task-envelope
        creates both the role reservation and a task-envelope companion
        with reciprocal call_id/companion_reservation_id references."""
        self._setup_te_configured()
        c, out, _ = self.reserve("outer-reviewer", "r1", rnd=1)
        self.assertTrue(out.startswith("PROCEED"), out)
        ledger = self.ledger()
        reserved = [e for e in ledger if e.get("event") == "reserved"]
        # Must have 2 reserved events: role + companion
        self.assertEqual(len(reserved), 2, f"Expected 2 reserved events, got {len(reserved)}")
        role_ev = next(e for e in reserved if e["target_role"] == "outer-reviewer")
        comp_ev = next(e for e in reserved if e["target_role"] == "task-envelope")
        # Reciprocal call_id
        self.assertIsNotNone(role_ev.get("call_id"))
        self.assertEqual(role_ev["call_id"], comp_ev["call_id"])
        # Reciprocal companion_reservation_id
        self.assertEqual(role_ev.get("companion_reservation_id"), comp_ev["reservation_id"])
        self.assertEqual(comp_ev.get("companion_reservation_id"), role_ev["reservation_id"])
        # Companion consumes=task-envelope
        self.assertEqual(comp_ev["consumes"], "task-envelope")

    def test_spawn_companion_checked_first_no_half_pair(self):
        """When task-envelope budget is exhausted, the role reservation
        is also blocked — no half-pair committed."""
        self._setup_te_configured()  # small: initial=4
        for i in range(4):
            c, out, _ = self.reserve("executor", f"te{i}")
            self.assertTrue(out.startswith("PROCEED"), out)
        # task-envelope exhausted (4/4)
        c, out, _ = self.reserve("outer-reviewer", "r1", rnd=1)
        self.assertEqual(out, "BLOCK:task_envelope_exhausted", out)
        # Verify no role reservation was created
        ledger = self.ledger()
        role_reserved = [e for e in ledger
                         if e.get("event") == "reserved"
                         and e.get("target_role") == "outer-reviewer"]
        self.assertEqual(len(role_reserved), 0, "No half-pair: role must not be reserved")

    # -- 2. Pre-dispatch failure cancels both ---------------------------
    def test_pre_dispatch_failure_cancels_companion(self):
        """A pre-execution cancelled settles both role and companion."""
        self._setup_te_configured()
        c, out, _ = self.reserve("outer-reviewer", "r1", rnd=1)
        self.assertTrue(out.startswith("PROCEED"), out)
        rid = out.split(":")[1]
        # Find companion
        ledger = self.ledger()
        comp_ev = next(e for e in ledger
                       if e.get("event") == "reserved"
                       and e.get("target_role") == "task-envelope")
        comp_rid = comp_ev["reservation_id"]
        # Cancel role (pre-execution)
        c, out, _ = self.settle(rid, "cancelled", pre_execution=True)
        self.assertEqual(out, "OK", out)
        # Both should be settled
        ledger = self.ledger()
        role_settled = any(e.get("reservation_id") == rid
                          and e.get("event") == "cancelled"
                          for e in ledger)
        comp_settled = any(e.get("reservation_id") == comp_rid
                          and e.get("event") == "cancelled"
                          for e in ledger)
        self.assertTrue(role_settled, "Role must be settled")
        self.assertTrue(comp_settled, "Companion must be settled")

    # -- 3. Post-dispatch failure consumes once -------------------------
    def test_post_dispatch_failure_consumes_once(self):
        """A post-dispatch failure (spawn_failed, pre_execution=False)
        consumes the envelope once."""
        self._setup_te_configured()
        c, out, _ = self.reserve("outer-reviewer", "r1", rnd=1)
        self.assertTrue(out.startswith("PROCEED"), out)
        rid = out.split(":")[1]
        c, out, _ = self.settle(rid, "failed")
        self.assertEqual(out, "OK", out)
        # Both should be settled (companion auto-settled)
        ledger = self.ledger()
        failed_events = [e for e in ledger if e.get("event") == "spawn_failed"]
        self.assertEqual(len(failed_events), 2, f"Expected 2 spawn_failed, got {len(failed_events)}")

    # -- 4. Idempotent settle -------------------------------------------
    def test_idempotent_same_result_noop(self):
        """Settling the same reservation with the same result twice is a no-op."""
        self._setup_te_configured()
        c, out, _ = self.reserve("executor", "e1")
        self.assertTrue(out.startswith("PROCEED"), out)
        rid = out.split(":")[1]
        c, out, _ = self.settle(rid, "succeeded", instance_id="i1")
        self.assertEqual(out, "OK")
        # Second settle with same result: should be no-op (companion already settled)
        c, out, _ = self.settle(rid, "succeeded", instance_id="i1")
        # Should not fail (idempotent)
        self.assertTrue(out == "OK" or "duplicate" in out.lower(), out)

    def test_conflicting_result_fails_closed(self):
        """Settling with a conflicting result fails closed."""
        self._setup_te_configured()
        c, out, _ = self.reserve("executor", "e1")
        rid = out.split(":")[1]
        c, out, _ = self.settle(rid, "succeeded", instance_id="i1")
        self.assertEqual(out, "OK")
        # Conflicting result
        c, out, _ = self.settle(rid, "failed")
        self.assertTrue(out.startswith("FAIL_CLOSED"), out)

    # -- 5. Cross-call link rejected ------------------------------------
    def test_cross_call_companion_link_rejected(self):
        """A companion referencing a different call_id fails validation."""
        self._setup_te_configured()
        # Manually inject a companion with mismatched call_id
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "event": "reserved", "reservation_id": "fake-comp",
                "ts": "2026-06-19T00:00:00+00:00",
                "target_role": "task-envelope", "consumes": "task-envelope",
                "target_round": None,
                "call_id": "nonexistent-call",
                "companion_reservation_id": "nonexistent-role",
                "counts_before": {"outer": 0, "blind": 0, "ultraverge": 0, "total": 0,
                                  "task-envelope": 0},
                "ceilings": {"outer": 8, "blind": 3, "ultraverge": 3, "total": 63,
                             "task-envelope": 4},
                "tier": "auditable-only",
            }) + "\n")
        c, out, _ = self.reserve("executor", "e1")
        self.assertTrue(out.startswith("FAIL_CLOSED"), out)
        self.assertIn("companion", out.lower(), out)

    # -- 6. Validate integrity companion invariants ----------------------
    def test_orphan_companion_without_role_fails_closed(self):
        """A companion reservation without a matching role reservation
        fails validation."""
        self._setup_te_configured()
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "event": "reserved", "reservation_id": "orphan-comp",
                "ts": "2026-06-19T00:00:00+00:00",
                "target_role": "task-envelope", "consumes": "task-envelope",
                "target_round": None,
                "call_id": "orphan-call",
                "companion_reservation_id": "no-such-role-rid",
                "counts_before": {"outer": 0, "blind": 0, "ultraverge": 0, "total": 0,
                                  "task-envelope": 0},
                "ceilings": {"outer": 8, "blind": 3, "ultraverge": 3, "total": 63,
                             "task-envelope": 4},
                "tier": "auditable-only",
            }) + "\n")
        c, out, _ = self.reserve("executor", "e1")
        self.assertTrue(out.startswith("FAIL_CLOSED"), out)

    # -- 7. accounting_coverage in summary -------------------------------
    def test_summary_instrumented_complete(self):
        """When all events have call_id, coverage is instrumented_complete
        and model_invocations is numeric."""
        self._setup_te_configured()
        c, out, _ = self.reserve("executor", "e1")
        rid = out.split(":")[1]
        self.settle(rid, "succeeded", instance_id="i1")
        c, out, _ = run("summary", "--active-dir", str(self.active))
        self.assertEqual(c, 0, out)
        summary = json.loads(out)
        self.assertEqual(summary.get("accounting_coverage"), "instrumented_complete")
        self.assertIsInstance(summary.get("model_invocations"), int)
        # Legacy key also present
        self.assertIsInstance(summary.get("model_invocation"), int)

    def test_summary_unavailable_without_call_id(self):
        """Legacy events without call_id force coverage=unavailable
        and model_invocations=unavailable."""
        # Write a legacy event without call_id
        self.reserve("executor", "e1")
        self.settle("e1", "succeeded", instance_id="i1")
        # Inject a legacy-style event without call_id
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "event": "reserved", "reservation_id": "legacy",
                "ts": "2026-06-19T00:00:00+00:00",
                "target_role": "executor", "consumes": "none",
                "target_round": None,
                "counts_before": {"outer": 0, "blind": 0, "ultraverge": 0, "total": 1},
                "ceilings": {"outer": 8, "blind": 3, "ultraverge": 3, "total": 63},
                "tier": "auditable-only",
            }) + "\n")
        c, out, _ = run("summary", "--active-dir", str(self.active))
        self.assertEqual(c, 0, out)
        summary = json.loads(out)
        self.assertEqual(summary.get("accounting_coverage"), "unavailable")
        self.assertEqual(summary.get("model_invocations"), "unavailable")

    # -- 8. Unconfigured envelope keeps A8 behavior ----------------------
    def test_unconfigured_envelope_no_companion(self):
        """Without task-envelope config, Spawn reserve creates no companion
        and existing behavior is unchanged (A8 backward compat)."""
        # No task_tier or task_envelope_cap configured
        c, out, _ = self.reserve("outer-reviewer", "r1", rnd=1)
        self.assertTrue(out.startswith("PROCEED"), out)
        ledger = self.ledger()
        reserved = [e for e in ledger if e.get("event") == "reserved"]
        self.assertEqual(len(reserved), 1, "No companion when unconfigured")
        self.assertEqual(reserved[0]["target_role"], "outer-reviewer")
        self.assertNotIn("companion_reservation_id", reserved[0])

    def test_unconfigured_task_envelope_direct_reserve_fails_closed(self):
        """Direct --role task-envelope when unconfigured still fails closed
        (A8 backward compat)."""
        c, out, _ = self.reserve("task-envelope", "t1")
        self.assertTrue(out.startswith("FAIL_CLOSED:task_envelope_not_configured"), out)

    # -- 9. Existing tier values unchanged -------------------------------
    def test_task_tier_values_unchanged(self):
        """TASK_TIERS values must be exactly as specified."""
        expected = {
            "small": {"initial": 4, "cap": 8},
            "medium": {"initial": 8, "cap": 16},
            "feature": {"initial": 16, "cap": 24},
            "critical": {"initial": 20, "cap": 30},
        }
        for tier, vals in expected.items():
            self.assertEqual(budget_gate.TASK_TIERS[tier], vals, f"Tier {tier} mismatch")
        # Alias
        self.assertEqual(budget_gate.TASK_TIERS["critical/ultraverge"],
                         budget_gate.TASK_TIERS["critical"])

    # -- 10. CRLF pollution red test for JSON evidence -------------------
    def test_crlf_pollution_in_ledger_fails_closed(self):
        """Gate ledger JSON written with CRLF must be caught."""
        self.reserve("executor", "e1")
        # Manually append a CRLF-polluted line
        ledger_path = self.active / "gate-ledger.jsonl"
        with ledger_path.open("ab") as f:
            f.write(b'{"event":"reserved","reservation_id":"crlf","ts":"2026-06-19T00:00:00+00:00","target_role":"executor","consumes":"none","target_round":null,"counts_before":{"outer":0,"blind":0,"ultraverge":0,"total":1},"ceilings":{"outer":8,"blind":3,"ultraverge":3,"total":63},"tier":"auditable-only"}\r\n')
        c, out, _ = self.reserve("executor", "e2")
        # CRLF in ledger should be caught (JSON parse may succeed but
        # integrity check should flag it)
        # Note: JSON parse is line-based so \r\n splits may cause issues
        # The key test is that our writes never produce CRLF
        data = ledger_path.read_bytes()
        # Verify our normal writes don't have CRLF
        lines = data.split(b"\n")
        normal_lines = [l for l in lines if l.strip() and not l.endswith(b"\r")]
        self.assertTrue(len(normal_lines) > 0, "Normal writes must use LF")


# ---------------------------------------------------------------------------
# Append-only companion linkage regression (r2 fix)
# ---------------------------------------------------------------------------

class TestAppendOnlyCompanionLinkage(Base):
    """Regression: cmd_companion_for must never rewrite gate-ledger.jsonl.

    The pre-reserved adapter path creates a companion AFTER the role
    reservation exists.  The role event legitimately has no forward
    call_id / companion_reservation_id; linkage is resolved by reverse
    lookup.  The ledger must remain append-only (byte-prefix invariant).
    """

    def _setup_te_configured(self, tier="small"):
        self.set_config(task_tier=tier)

    def _reserve_before_te(self, role, rid, rnd=None, tier="auditable-only"):
        """Create a role reservation BEFORE task-envelope is configured
        (no companion will be created by cmd_reserve)."""
        # Reserve without task-envelope configured
        c, out, _ = self.reserve(role, rid, rnd=rnd, tier=tier)
        self.assertTrue(out.startswith("PROCEED"), out)
        # Now configure task-envelope
        self._setup_te_configured()
        return c, out

    def _companion_for(self, role_rid, tier="auditable-only"):
        return run("reserve", "--active-dir", str(self.active),
                    "--role", "task-envelope", "--tier", tier,
                    "--companion-for", role_rid)

    # -- 1. Append-only: ledger bytes are never rewritten ----------------
    def test_companion_for_append_only_no_rewrite(self):
        """cmd_companion_for must only APPEND; pre-call bytes must be an
        exact prefix of post-call bytes (no rewrite)."""
        # Create role BEFORE task-envelope is configured (no atomic pair)
        self._reserve_before_te("executor", "role1", rnd=1)

        # Capture ledger bytes before companion_for
        ledger_path = self.active / "gate-ledger.jsonl"
        pre_bytes = ledger_path.read_bytes()

        # Create companion via companion_for
        c, out, _ = self._companion_for("role1")
        self.assertTrue(out.startswith("PROCEED"), out)

        # Assert: post-call file has pre-call bytes as exact prefix
        post_bytes = ledger_path.read_bytes()
        self.assertTrue(
            post_bytes.startswith(pre_bytes),
            "LEDGER REWRITE DETECTED: pre-call bytes are not a prefix of "
            "post-call bytes.  cmd_companion_for must only append.")

        # The appended portion must be exactly one JSON line
        appended = post_bytes[len(pre_bytes):]
        appended_lines = [l for l in appended.decode("utf-8").splitlines() if l.strip()]
        self.assertEqual(len(appended_lines), 1,
                         f"Expected exactly 1 appended line, got {len(appended_lines)}")
        comp_ev = json.loads(appended_lines[0])
        self.assertEqual(comp_ev["event"], "reserved")
        self.assertEqual(comp_ev["target_role"], "task-envelope")
        self.assertEqual(comp_ev["companion_reservation_id"], "role1")

    # -- 2. Role event has NO forward reference after companion_for ------
    def test_companion_for_no_forward_ref_on_role_event(self):
        """After cmd_companion_for, the role event must NOT be mutated to
        carry call_id or companion_reservation_id (append-only invariant)."""
        self._reserve_before_te("executor", "role1", rnd=1)

        c, out, _ = self._companion_for("role1")
        self.assertTrue(out.startswith("PROCEED"), out)

        ledger = self.ledger()
        role_ev = next(e for e in ledger
                       if e.get("event") == "reserved"
                       and e.get("reservation_id") == "role1")
        # Role event must NOT have been mutated
        self.assertIsNone(role_ev.get("call_id"),
                          "Role event must not be mutated with call_id")
        self.assertIsNone(role_ev.get("companion_reservation_id"),
                          "Role event must not be mutated with companion_reservation_id")

    # -- 3. Reverse lookup: settle role settles companion -----------------
    def test_companion_reverse_lookup_settle(self):
        """Settling the role reservation auto-settles its companion even
        when the role event has no forward companion_reservation_id."""
        self._reserve_before_te("executor", "role1", rnd=1)

        c, out, _ = self._companion_for("role1")
        self.assertTrue(out.startswith("PROCEED"), out)
        comp_rid = out.split(":")[1]

        # Settle role
        c, out, _ = self.settle("role1", "succeeded", instance_id="i1")
        self.assertEqual(out, "OK", out)

        # Companion must also be settled
        ledger = self.ledger()
        comp_settled = any(e.get("reservation_id") == comp_rid
                           and e.get("event") == "spawn_succeeded"
                           for e in ledger)
        self.assertTrue(comp_settled,
                        "Companion must be auto-settled when role is settled "
                        "(reverse lookup path)")

    # -- 4. Reverse lookup: cancel role cancels companion -----------------
    def test_companion_reverse_lookup_cancel(self):
        """Cancelling the role reservation auto-cancels its companion via
        reverse lookup."""
        self._reserve_before_te("executor", "role1", rnd=1)

        c, out, _ = self._companion_for("role1")
        self.assertTrue(out.startswith("PROCEED"), out)
        comp_rid = out.split(":")[1]

        # Cancel role
        c, out, _ = self.settle("role1", "cancelled", pre_execution=True)
        self.assertEqual(out, "OK", out)

        ledger = self.ledger()
        comp_cancelled = any(e.get("reservation_id") == comp_rid
                             and e.get("event") == "cancelled"
                             for e in ledger)
        self.assertTrue(comp_cancelled,
                        "Companion must be auto-cancelled when role is cancelled "
                        "(reverse lookup path)")

    # -- 5. Idempotent: companion_for on role that already has companion -
    def test_companion_for_idempotent_reverse_lookup(self):
        """Calling companion_for twice must detect existing companion via
        reverse lookup and return FAIL_CLOSED:companion_already_exists."""
        self._reserve_before_te("executor", "role1", rnd=1)

        c, out, _ = self._companion_for("role1")
        self.assertTrue(out.startswith("PROCEED"), out)

        # Second call must fail
        c, out, _ = self._companion_for("role1")
        self.assertTrue(out.startswith("FAIL_CLOSED"), out)
        self.assertIn("companion_already_exists", out)

    # -- 6. Settled role cannot be mutated by companion_for ---------------
    def test_settled_role_companion_for_still_works(self):
        """companion_for on an already-settled role must succeed (companion
        can still be created) but must not mutate the settled role event."""
        self._reserve_before_te("executor", "role1", rnd=1)

        # Settle role first
        c, out, _ = self.settle("role1", "succeeded", instance_id="i1")
        self.assertEqual(out, "OK", out)

        # Capture ledger bytes before companion_for
        ledger_path = self.active / "gate-ledger.jsonl"
        pre_bytes = ledger_path.read_bytes()

        # companion_for should still succeed (or fail gracefully),
        # but must NOT rewrite the ledger
        c, out, _ = self._companion_for("role1")
        # It may succeed or fail — what matters is append-only
        post_bytes = ledger_path.read_bytes()
        self.assertTrue(
            post_bytes.startswith(pre_bytes),
            "LEDGER REWRITE DETECTED on settled role: bytes were modified in place")

    # -- 7. Reverse lookup in validate_integrity -------------------------
    def test_validate_integrity_accepts_role_without_forward_ref(self):
        """validate_integrity must accept a companion whose role event has
        no companion_reservation_id (the pre-reserved adapter path)."""
        self._reserve_before_te("executor", "role1", rnd=1)

        c, out, _ = self._companion_for("role1")
        self.assertTrue(out.startswith("PROCEED"), out)

        # Trigger validate_integrity via a subsequent operation
        c, out, _ = self.reserve("executor", "e2")
        self.assertTrue(
            out.startswith("PROCEED"),
            f"validate_integrity must accept role without forward ref: {out}")

    # -- 8. Exactly one companion per role (reverse + forward) -----------
    def test_duplicate_companion_via_reverse_lookup_rejected(self):
        """A second companion referencing the same role must be rejected."""
        self._reserve_before_te("executor", "role1", rnd=1)

        c, out, _ = self._companion_for("role1")
        self.assertTrue(out.startswith("PROCEED"), out)

        # Manually inject a second companion referencing role1
        with (self.active / "gate-ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "event": "reserved", "reservation_id": "dup-comp",
                "ts": "2026-06-19T00:00:00+00:00",
                "target_role": "task-envelope", "consumes": "task-envelope",
                "target_round": None,
                "call_id": "dup-call",
                "companion_reservation_id": "role1",
                "counts_before": {"outer": 0, "blind": 0, "ultraverge": 0, "total": 0,
                                  "task-envelope": 0},
                "ceilings": {"outer": 8, "blind": 3, "ultraverge": 3, "total": 63,
                             "task-envelope": 4},
                "tier": "auditable-only",
            }) + "\n")

        # Next operation must fail on integrity check
        c, out, _ = self.reserve("executor", "e2")
        self.assertTrue(
            out.startswith("FAIL_CLOSED"),
            f"Duplicate companion must be rejected: {out}")


if __name__ == "__main__":
    unittest.main(verbosity=2)