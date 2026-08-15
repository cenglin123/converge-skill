"""T2 TDD:--continue-of 完整链路(方案甲,契约原生:continue 无 reservation)。

失败测试先行:本文件在实现前应 FAIL;实现后全绿。
规格(plan 20260815-converge-loop-wiring T2 + Archive Contract v1 原生 continue):
  - reserve-round --continue-of <父rid>:父须为 succeeded spawn;发射
    begin-invocation kind=continue(parent_event_id=父 started 事件 id,
    parent_instance_id=父 instance_id,reservation_id=None);**无 gate reserve**
    (契约:continue 不得携带 reservation;计数独立于 spawn cap 天然成立)
  - 上限:同一父链最多 3 次 continue(max_inner_loops,SKILL.md L273)
  - register-round --invocation-id <iid>:complete continue(succeeded),
    无 settle;settle 复用既有路径不适用;instance 必须等于父 instance(续命同实例)
  - finish 步骤 3:continue 孤儿(started 无 terminal)按无 reservation 分支恢复
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_loop_a_coverage import (  # noqa: E402
    LoopABase, FINAL_VERDICT, _read_events, _read_gate_ledger, run_orchest,
)


def _started_of(events, invocation_id):
    return next(e for e in events
                if e.get("event_type") == "invocation-started"
                and e.get("invocation_id") == invocation_id)


class TestContinueChain(LoopABase):

    def _spawned_parent(self) -> tuple[str, str, str]:
        rid, iid = self.reserve(round_no=1)
        rc, out, err = self.register(rid, "inst-r1")
        self.assertEqual(rc, 0, err)
        return rid, iid, "inst-r1"

    def _continue(self, parent_rid: str, prompt_extra: str = ""):
        return run_orchest(
            "reserve-round", "--active-dir", str(self.active),
            "--phase", "inner-review", "--attempt", "1",
            "--prompt-file", str(self.prompt),
            "--requested-provider", "testp", "--requested-model", "testm",
            "--continue-of", parent_rid)

    def test_continue_full_chain(self):
        rid, parent_iid, sid = self._spawned_parent()
        n_reserved_before = len([e for e in _read_gate_ledger(self.active)
                                 if e.get("event") == "reserved"])

        # 三次 Continue 全链
        cont_iids = []
        for k in range(3):
            rc, out, err = self._continue(rid)
            self.assertEqual(rc, 0, f"continue #{k+1} rc={rc} stdout={out} stderr={err}")
            cont_iid = next((l.split(":", 1)[1].strip()
                             for l in out.splitlines()
                             if l.startswith("invocation_id:")), None)
            self.assertTrue(cont_iid, f"continue #{k+1} 未返回 invocation_id: {out}")
            cont_iids.append(cont_iid)
            # 契约断言:kind=continue + parent 链 + 无 reservation
            ev = _started_of(_read_events(self.active), cont_iid)
            self.assertEqual(ev["invocation_kind"], "continue")
            self.assertEqual(ev["role"], "outer-reviewer")
            self.assertEqual(ev["round"], 1)
            self.assertIsNotNone(ev.get("parent_event_id"))
            self.assertEqual(ev.get("parent_instance_id"), sid)
            self.assertIsNone(ev.get("reservation_id"))
            # register:--invocation-id,同实例
            rc, out, err = run_orchest(
                "register-round", "--active-dir", str(self.active),
                "--invocation-id", cont_iid, "--instance-id", sid)
            self.assertEqual(rc, 0, f"register continue #{k+1}: {out} {err}")

        # 第四次 Continue 被上限拒绝(max_inner_loops=3)
        rc, out, err = self._continue(rid)
        self.assertNotEqual(rc, 0, "第 4 次 continue 应被拒绝")
        combined = out + err
        self.assertTrue("max_inner_loops" in combined or "continue" in combined.lower(),
                        f"拒绝原因应指明 continue 上限: {combined}")

        # gate 零新 reservation(continue 不占 spawn cap)
        n_reserved_after = len([e for e in _read_gate_ledger(self.active)
                                if e.get("event") == "reserved"])
        self.assertEqual(n_reserved_after, n_reserved_before)

        # continue 的 terminal:settlement_ref 为 None(无 ledger 记录可引用)
        events = _read_events(self.active)
        for cont_iid in cont_iids:
            st = _started_of(events, cont_iid)
            term = next(e for e in events
                        if e.get("event_type") == "invocation-terminal"
                        and e.get("started_event_id") == st["event_id"])
            self.assertEqual(term["terminal_status"], "succeeded")
            self.assertIsNone(term.get("settlement_ref"))

        # 全链仍可 verdict + finish
        rc, out, err = run_orchest("record-verdict", "--active-dir", str(self.active),
                                   "--round", "1", "--verdict", FINAL_VERDICT)
        self.assertEqual(rc, 0, err)
        self.write_retrospective()
        rc, out, err = self.finish()
        self.assertEqual(rc, 0, f"finish rc={rc} {out} {err}")
        self.assertTrue((self.done_root / self.SLUG).is_dir())

    def test_continue_parent_must_be_succeeded_spawn(self):
        # 父未 register(无 terminal)→ 拒绝
        rid, _ = self.reserve(round_no=1)
        rc, out, err = self._continue(rid)
        self.assertNotEqual(rc, 0, "父无 succeeded terminal 应拒绝")
        # 消费角色的父(consuming)也不行?不——executor(consumes=none)父同样合法,
        # 此处仅测「未完成」父。
        rc2, _, _ = self.register(rid, "inst-r1")
        self.assertEqual(rc2, 0)
        rc, out, err = self._continue(rid)
        self.assertEqual(rc, 0, f"父完成后 continue 应可用: {out} {err}")

    def test_register_continue_rejects_foreign_instance(self):
        rid, parent_iid, sid = self._spawned_parent()
        rc, out, err = self._continue(rid)
        self.assertEqual(rc, 0, err)
        cont_iid = next(l.split(":", 1)[1].strip() for l in out.splitlines()
                        if l.startswith("invocation_id:"))
        # 实例不一致(Continue 语义 = 续命同实例)→ 拒绝
        rc, out, err = run_orchest(
            "register-round", "--active-dir", str(self.active),
            "--invocation-id", cont_iid, "--instance-id", "other-instance")
        self.assertNotEqual(rc, 0, "异实例 register continue 应拒绝")

    def test_finish_recovers_orphan_continue(self):
        """continue started 后宿主崩溃(无 register)→ finish 步骤 3 恢复而非误报。"""
        rid, parent_iid, sid = self._spawned_parent()
        rc, out, err = self._continue(rid)
        self.assertEqual(rc, 0, err)
        # 不 register(模拟崩溃),直接 verdict + finish
        rc, out, err = run_orchest("record-verdict", "--active-dir", str(self.active),
                                   "--round", "1", "--verdict", FINAL_VERDICT)
        self.assertEqual(rc, 0, err)
        self.write_retrospective()
        rc, out, err = self.finish()
        self.assertEqual(rc, 0, f"含 continue 孤儿的 finish 应恢复而非失败: {out} {err}")
        self.assertTrue((self.done_root / self.SLUG).is_dir())


class TestNoRegressionWithoutContinue(LoopABase):
    """不带 --continue-of 时行为与既有完全一致(非目标 4:只加不改)。"""

    def test_spawn_flow_unchanged(self):
        rid, iid = self.reserve(round_no=1)
        rc, out, err = self.register(rid, "inst-r1")
        self.assertEqual(rc, 0, err)
        events = _read_events(self.active)
        ev = _started_of(events, iid)
        self.assertEqual(ev["invocation_kind"], "spawn")
        self.assertEqual(ev.get("parent_event_id"), None)
        self.assertEqual(ev.get("reservation_id"), rid)


if __name__ == "__main__":
    unittest.main()
