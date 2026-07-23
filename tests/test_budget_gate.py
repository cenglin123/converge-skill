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
        self.assertIn("cap=42", out)             # stock 默认公式（普通 converge, mbr=1）

    def test_default_cap_ultraverge_config_override(self):
        # ultraverge 路径：config 覆盖 max_blind_rechecks=2 → cap=44
        self.set_config(max_blind_rechecks=2)
        c, out, _ = run("bind", "--session-id", self.sid, "--active-dir", str(self.active),
                        env=self.env)
        self.assertIn("cap=44", out)             # ultraverge config 覆盖（mbr=2）


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
