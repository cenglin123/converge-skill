#!/usr/bin/env python3
"""budget_gate —— converge 预算执行硬化的 file-authoritative 裁决脚本。

实现 docs/plans/active/20260618-budget-enforcement-hardening.md (v7) 的
**host-independent core**（auditable-only tier）：reserve / settle /
ingest_verdict / preflight + 仅追加 ledger + 按 scope 有效计数 + 单调总量上限 +
extension 链与 decision 交叉校验 + **统一 schema/lifecycle validator** + fail-closed。

本文件还含 **best-effort guarded**（= hook-blocked auditable-only）：bind / refresh-cap /
unbind + `hook-pretooluse`（PreToolUse 总量硬上限兜底）。**真正的 enforced**（角色不可
伪造、角色 FSM 越权校验、权限锁定）仍属未来工作——Claude Code 不拥有 subagent prompt
模板，FSM phase 机为 plan 推迟项。

计数语义（plan §计数模型）：
  realized(s) = 已落成产物文件数（outer: round-N.md / blind: blind-recheck-N.md
                / ultraverge: uv-init-N.md），outer/blind 须连续编号否则 fail-closed
  pending(s)  = consumes=s、未失败/取消、且产物尚未落成的 reservation 数
  effective_usage(s) = realized(s) + pending(s)
  total_reservations_issued = 单调累计的不同 reservation_id，failed 不释放，
                              仅宿主背书 pre_execution 的 cancelled 不计入

不变量（validator，违反 → FAIL_CLOSED(30)）：config 类型；已知事件类型；
reservation_id 不重复 reserved；settle 必有前序 reserve 且不重复；同一
(scope, target_round) 至多一个活跃 reservation；outer/blind 产物连续编号；
extension 链线性、单调、prior 与被取代记录的 new_ceiling 衔接、与 BLOCK decision 交叉一致。

退出码：PROCEED=0  BLOCK:*=10/11/12/13  MODE_SWITCH_REQUIRED=20
        DENY:*=21/22  FAIL_CLOSED:*=30
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

EXIT_PROCEED = 0
EXIT_BLOCK_BUDGET = 10
EXIT_BLOCK_BLIND = 11
EXIT_BLOCK_ULTRAVERGE = 12
EXIT_BLOCK_TOTAL = 13
EXIT_MODE_SWITCH = 20
EXIT_DENY_UNKNOWN = 21
EXIT_DENY_ILLEGAL = 22
EXIT_FAIL_CLOSED = 30

DEFAULTS = {
    "max_outer_loops": 5,
    "max_blind_rechecks": 1,
    "ultraverge_min_reviewers": 3,
    "max_inner_loops": 3,
    "impl_severity_streak_threshold": 3,
    "preflight_code_block_threshold": 3,
    "preflight_code_loc_threshold": 40,
    "total_safety": 1.5,
}
INT_CONFIG = {
    "max_outer_loops", "max_blind_rechecks", "ultraverge_min_reviewers",
    "max_inner_loops", "impl_severity_streak_threshold",
    "preflight_code_block_threshold", "preflight_code_loc_threshold",
}

ROLE_CONSUMES = {
    "outer-reviewer": "outer",
    "blind-reviewer": "blind",
    "ultraverge-initial": "ultraverge",
    "executor": "none",
    "contract-proposer": "none",
    "contract-challenger": "none",
    "contract-finalizer": "none",
    "arbiter": "none",
    "l2-gate-reviewer": "none",
    "design-reviewer": "none",
}

SCOPE_PRODUCT = {
    "outer": "round-{n}.md",
    "blind": "blind-recheck-{n}.md",
    "ultraverge": "uv-init-{n}.md",
}
# 连续编号检查仅对顺序 scope；ultraverge 是并行批次，部分失败可合法跳号。
CONTIGUOUS_SCOPES = ("outer", "blind")

KNOWN_EVENTS = {"reserved", "spawn_succeeded", "spawn_failed", "cancelled", "decision"}
SETTLE_EVENTS = {"spawn_succeeded", "spawn_failed", "cancelled"}
VERDICTS = ("可执行", "阻断需修复", "需重新设计")   # 与 refs/reviewer-prompt.md 一致

LEDGER_NAME = "gate-ledger.jsonl"
STATE_NAME = "_budget-state.json"
LOCK_NAME = ".gate.lock"
LOCK_STALE_SECONDS = 30


class FailClosed(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _ledger_path(active: Path) -> Path:
    return active / LEDGER_NAME


def _state_path(active: Path) -> Path:
    return active / STATE_NAME


def read_ledger(active: Path) -> list[dict]:
    p = _ledger_path(active)
    if not p.exists():
        return []
    events = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError as e:
            raise FailClosed(f"ledger_corrupt:line{i}:{e}")
        if not isinstance(ev, dict):
            raise FailClosed(f"ledger_corrupt:line{i}:not_object")
        events.append(ev)
    return events


def append_ledger(active: Path, event: dict) -> None:
    with _ledger_path(active).open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_state(active: Path) -> dict:
    p = _state_path(active)
    if not p.exists():
        return {"config": {}, "extensions": [], "fsm": {"mode": "standard", "severities": {}}}
    try:
        st = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise FailClosed(f"state_corrupt:{e}")
    if not isinstance(st, dict):
        raise FailClosed("state_corrupt:not_object")
    st.setdefault("config", {})
    st.setdefault("extensions", [])
    st.setdefault("fsm", {"mode": "standard", "severities": {}})
    if not isinstance(st["config"], dict) or not isinstance(st["extensions"], list):
        raise FailClosed("state_corrupt:bad_shape")
    st["fsm"].setdefault("mode", "standard")
    st["fsm"].setdefault("severities", {})
    return st


def write_state(active: Path, state: dict) -> None:
    _state_path(active).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def cfg(state: dict, key: str):
    return state.get("config", {}).get(key, DEFAULTS[key])


# ---- 锁 ---------------------------------------------------------------------
class Lock:
    def __init__(self, active: Path, timeout: float = 5.0):
        self.path = active / LOCK_NAME
        self.timeout = timeout
        self.fd = None

    def __enter__(self):
        deadline = time.time() + self.timeout
        while True:
            try:
                if self.path.exists() and (time.time() - self.path.stat().st_mtime) > LOCK_STALE_SECONDS:
                    self.path.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                if time.time() > deadline:
                    raise FailClosed("lock_timeout")
                time.sleep(0.02)

    def __exit__(self, *exc):
        if self.fd is not None:
            os.close(self.fd)
            self.path.unlink(missing_ok=True)


# ---- 状态聚合 ----------------------------------------------------------------
def _reservation_status(events: list[dict]) -> dict[str, dict]:
    """聚合每个 reservation_id 的最终状态。前提：validator 已保证无重复 reserved。"""
    res: dict[str, dict] = {}
    for ev in events:
        et = ev.get("event")
        rid = ev.get("reservation_id")
        if et == "reserved":
            res[rid] = {
                "status": "reserved", "consumes": ev.get("consumes"),
                "role": ev.get("target_role"), "target_round": ev.get("target_round"),
                "pre_execution": False,
            }
        elif et in SETTLE_EVENTS and rid in res:
            res[rid]["status"] = et
            if et == "cancelled":
                res[rid]["pre_execution"] = bool(ev.get("pre_execution", False))
    return res


def total_reservations_issued(events: list[dict]) -> int:
    res = _reservation_status(events)
    return sum(1 for r in res.values()
               if not (r["status"] == "cancelled" and r["pre_execution"]))


def realized_round_numbers(active: Path, scope: str) -> list[int]:
    tmpl = SCOPE_PRODUCT.get(scope)
    if tmpl is None:
        return []
    prefix, suffix = tmpl.split("{n}")
    nums = []
    for p in active.glob(f"{prefix}*{suffix}"):
        mid = p.name[len(prefix): len(p.name) - len(suffix)]
        if mid.isdigit():
            nums.append(int(mid))
    return nums


def realized(active: Path, scope: str) -> int:
    return len(realized_round_numbers(active, scope))


def pending(active: Path, events: list[dict], scope: str) -> int:
    res = _reservation_status(events)
    cnt = 0
    for r in res.values():
        if r["consumes"] != scope:
            continue
        if r["status"] in ("spawn_failed", "cancelled"):
            continue
        tmpl = SCOPE_PRODUCT.get(scope)
        n = r.get("target_round")
        if tmpl and n is not None and (active / tmpl.format(n=n)).exists():
            continue
        cnt += 1
    return cnt


def effective_usage(active: Path, events: list[dict], scope: str) -> int:
    return realized(active, scope) + pending(active, events, scope)


def active_targets(events: list[dict]) -> dict[tuple, str]:
    """(scope, target_round) → reservation_id，仅活跃（reserved/succeeded）的 consuming。"""
    res = _reservation_status(events)
    out: dict[tuple, str] = {}
    for rid, r in res.items():
        if r["consumes"] not in SCOPE_PRODUCT:
            continue
        if r["status"] in ("spawn_failed", "cancelled"):
            continue
        out[(r["consumes"], r["target_round"])] = rid
    return out


# ---- extension --------------------------------------------------------------
def _decisions_by_id(events: list[dict]) -> dict[str, dict]:
    return {ev["decision_event_id"]: ev for ev in events
            if ev.get("event") == "decision" and "decision_event_id" in ev}


def validate_extensions(state: dict, events: list[dict]) -> None:
    decisions = _decisions_by_id(events)
    by_scope: dict[str, list[dict]] = {}
    for ext in state.get("extensions", []):
        if not isinstance(ext, dict) or "extension_id" not in ext:
            raise FailClosed("ext_bad_record")
        by_scope.setdefault(ext.get("scope"), []).append(ext)

    for scope, exts in by_scope.items():
        by_id = {e["extension_id"]: e for e in exts}
        for ext in exts:
            d = decisions.get(ext.get("triggering_block_event_id"))
            if d is None or not str(d.get("verdict", "")).startswith("BLOCK"):
                raise FailClosed("ext_no_block_decision")
            if d.get("scope") != scope:
                raise FailClosed("ext_scope_mismatch")
            if d.get("observed_usage") != ext.get("granted_at_usage"):
                raise FailClosed("ext_usage_mismatch")
            if d.get("effective_ceiling") != ext.get("prior_ceiling"):
                raise FailClosed("ext_ceiling_mismatch")
            if not (ext.get("new_ceiling", 0) > ext.get("prior_ceiling", 0)):
                raise FailClosed("ext_not_increasing")
            # 链衔接：取代旧记录时，新记录 prior 必须 == 旧记录 new（强制沿链单调递增）
            sup = ext.get("supersedes")
            if sup is not None:
                if sup not in by_id:
                    raise FailClosed("ext_chain_dangling")
                if ext.get("prior_ceiling") != by_id[sup].get("new_ceiling"):
                    raise FailClosed("ext_chain_discontinuous")
        superseded = [e.get("supersedes") for e in exts if e.get("supersedes") is not None]
        if len(superseded) != len(set(superseded)):
            raise FailClosed("ext_chain_fork")
        heads = [e for e in exts if e["extension_id"] not in set(superseded)]
        if len(heads) != 1:
            raise FailClosed("ext_chain_multi_head")


def active_extension(state: dict, scope: str):
    exts = [e for e in state.get("extensions", []) if e.get("scope") == scope]
    if not exts:
        return None
    superseded_ids = {e.get("supersedes") for e in exts if e.get("supersedes")}
    heads = [e for e in exts if e["extension_id"] not in superseded_ids]
    return heads[0] if heads else None


def ceiling(state: dict, scope: str) -> int:
    ext = active_extension(state, scope)
    if ext is not None:
        return int(ext["new_ceiling"])
    if scope == "outer":
        return int(cfg(state, "max_outer_loops"))
    if scope == "blind":
        return int(cfg(state, "max_blind_rechecks"))
    if scope == "ultraverge":
        return int(cfg(state, "ultraverge_min_reviewers"))
    if scope == "total":
        return default_total_cap(state)
    raise FailClosed(f"unknown_scope:{scope}")


def default_total_cap(state: dict) -> int:
    base = (3 + cfg(state, "ultraverge_min_reviewers")
            + cfg(state, "max_outer_loops") * (1 + cfg(state, "max_inner_loops"))
            + cfg(state, "max_blind_rechecks") + 1)
    return math.ceil(cfg(state, "total_safety") * base)


# ---- 统一 validator（findings 共同根因）------------------------------------
TIER_VALUES = {"enforced", "auditable-only"}
CONSUMES_VALUES = {"outer", "blind", "ultraverge", "none"}
SCOPE_KEYS = ("outer", "blind", "ultraverge", "total")
DECISION_SCOPES = (None, "outer", "blind", "ultraverge", "total")
DECISION_EXACT = {"MODE_SWITCH_REQUIRED"}
BLOCK_SUFFIXES = {"budget_exhausted", "blind_exhausted", "ultraverge_exhausted", "total_spawn_cap"}
DENY_SUFFIXES = {"unknown_role", "illegal_role"}


def _nonempty_str(x) -> bool:
    return isinstance(x, str) and x != ""


def _int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _pos_int(x) -> bool:
    return _int(x) and x >= 1


def _iso(x) -> bool:
    if not isinstance(x, str) or not x:
        return False
    try:
        datetime.fromisoformat(x)
        return True
    except ValueError:
        return False


def _valid_decision_verdict(v) -> bool:
    if not isinstance(v, str):
        return False
    if v in DECISION_EXACT:
        return True
    if v.startswith("BLOCK:"):
        return v[len("BLOCK:"):] in BLOCK_SUFFIXES
    if v.startswith("DENY:"):
        return v[len("DENY:"):] in DENY_SUFFIXES
    if v.startswith("FAIL_CLOSED:"):
        return len(v) > len("FAIL_CLOSED:")
    return False


def _validate_event(ev: dict) -> None:
    """逐事件完整 schema：必填字段、类型、enum、嵌套结构、role↔consumes 一致。

    与 refs/state-schema.md §预算 gate 的事件契约一一对应。任何缺字段 / 错类型 /
    非法 enum / 嵌套结构不合 → FAIL_CLOSED（不让损坏事件污染计数）。
    """
    et = ev["event"]
    # 所有事件必带可解析 ISO 时间戳
    if not _iso(ev.get("ts")):
        raise FailClosed(f"event_field:{et}.ts")

    if et == "reserved":
        if not _nonempty_str(ev.get("reservation_id")):
            raise FailClosed("event_field:reserved.reservation_id")
        role = ev.get("target_role")
        if role not in ROLE_CONSUMES:
            raise FailClosed("event_field:reserved.target_role")
        consumes = ev.get("consumes")
        if consumes not in CONSUMES_VALUES or consumes != ROLE_CONSUMES[role]:
            raise FailClosed("event_field:reserved.consumes")
        if consumes in SCOPE_PRODUCT:
            if not _pos_int(ev.get("target_round")):
                raise FailClosed("event_field:reserved.target_round")
        elif ev.get("target_round") is not None and not _int(ev.get("target_round")):
            raise FailClosed("event_field:reserved.target_round")
        for fld in ("counts_before", "ceilings"):
            d = ev.get(fld)
            if not isinstance(d, dict) or any(not _int(d.get(k)) for k in SCOPE_KEYS):
                raise FailClosed(f"event_field:reserved.{fld}")
        eid = ev.get("extension_id")
        if eid is not None and not _nonempty_str(eid):
            raise FailClosed("event_field:reserved.extension_id")
        if ev.get("tier") not in TIER_VALUES:
            raise FailClosed("event_field:reserved.tier")

    elif et == "spawn_succeeded":
        if not _nonempty_str(ev.get("reservation_id")):
            raise FailClosed("event_field:spawn_succeeded.reservation_id")
        if not _nonempty_str(ev.get("instance_id")):
            raise FailClosed("event_field:spawn_succeeded.instance_id")

    elif et == "spawn_failed":
        if not _nonempty_str(ev.get("reservation_id")):
            raise FailClosed("event_field:spawn_failed.reservation_id")
        if "reason" in ev and not isinstance(ev["reason"], str):
            raise FailClosed("event_field:spawn_failed.reason")

    elif et == "cancelled":
        if not _nonempty_str(ev.get("reservation_id")):
            raise FailClosed("event_field:cancelled.reservation_id")
        if not isinstance(ev.get("pre_execution", False), bool):
            raise FailClosed("event_field:cancelled.pre_execution")
        if "reason" in ev and not isinstance(ev["reason"], str):
            raise FailClosed("event_field:cancelled.reason")

    elif et == "decision":
        if not _nonempty_str(ev.get("decision_event_id")):
            raise FailClosed("event_field:decision.decision_event_id")
        if not _valid_decision_verdict(ev.get("verdict")):
            raise FailClosed("event_field:decision.verdict")
        scope = ev.get("scope")
        if scope not in DECISION_SCOPES:
            raise FailClosed("event_field:decision.scope")
        if str(ev.get("verdict", "")).startswith("BLOCK"):
            if scope not in ("outer", "blind", "ultraverge", "total"):
                raise FailClosed("event_field:decision.block_scope")
            for f in ("observed_usage", "effective_ceiling"):
                if not _int(ev.get(f)):
                    raise FailClosed(f"event_field:decision.{f}")
        else:
            # 非 BLOCK（DENY/FAIL_CLOSED/MODE_SWITCH）：v7 规定 scope/usage/ceiling 必须显式存在且为 null
            if "scope" not in ev or ev["scope"] is not None:
                raise FailClosed("event_field:decision.nonblock_scope")
            for f in ("observed_usage", "effective_ceiling"):
                if f not in ev or ev[f] is not None:
                    raise FailClosed(f"event_field:decision.{f}_must_null")


def validate_integrity(active: Path, events: list[dict], state: dict) -> None:
    # config 类型
    cfgd = state.get("config", {})
    for k in INT_CONFIG:
        if k in cfgd and (isinstance(cfgd[k], bool) or not isinstance(cfgd[k], int)):
            raise FailClosed(f"config_type:{k}")
    if "total_safety" in cfgd and (isinstance(cfgd["total_safety"], bool)
                                   or not isinstance(cfgd["total_safety"], (int, float))):
        raise FailClosed("config_type:total_safety")

    # 事件类型 + reservation 生命周期
    seen_reserved: set = set()
    settled: set = set()
    for ev in events:
        et = ev.get("event")
        if et not in KNOWN_EVENTS:
            raise FailClosed(f"unknown_event:{et}")
        _validate_event(ev)
        rid = ev.get("reservation_id")
        if et == "reserved":
            if rid in seen_reserved:
                raise FailClosed("duplicate_reserved")
            seen_reserved.add(rid)
        elif et in SETTLE_EVENTS:
            if rid not in seen_reserved:
                raise FailClosed("settle_without_reserve")
            if rid in settled:
                raise FailClosed("duplicate_settlement")
            settled.add(rid)

    # 同一 (scope, target_round) 至多一个活跃 reservation
    res = _reservation_status(events)
    seen_targets: set = set()
    for r in res.values():
        if r["consumes"] not in SCOPE_PRODUCT:
            continue
        if r["status"] in ("spawn_failed", "cancelled"):
            continue
        key = (r["consumes"], r["target_round"])
        if key in seen_targets:
            raise FailClosed("double_target")
        seen_targets.add(key)

    # 顺序 scope 产物连续编号（无重复 FS 上不可能；缺号 → fail-closed）
    for scope in CONTIGUOUS_SCOPES:
        nums = realized_round_numbers(active, scope)
        if nums and sorted(nums) != list(range(1, max(nums) + 1)):
            raise FailClosed(f"round_gap:{scope}")

    # extension 链
    validate_extensions(state, events)


def mode_switch_required(state: dict, current_round: int) -> bool:
    k = cfg(state, "impl_severity_streak_threshold")
    sev = state.get("fsm", {}).get("severities", {})
    rounds = sorted((int(r) for r in sev.keys()), reverse=True)[:k]
    if len(rounds) < k:
        return False
    for r in rounds:
        items = sev.get(str(r)) or sev.get(r) or []
        if not items:
            return False
        impl = sum(1 for s in items if s == "implementation")
        if impl * 2 < len(items):
            return False
    return True


# ---- 命令 -------------------------------------------------------------------
def _emit_decision(active: Path, verdict: str, scope, observed, ceil) -> str:
    did = _new_id()
    append_ledger(active, {
        "event": "decision", "decision_event_id": did, "ts": _now(),
        "verdict": verdict, "scope": scope,
        "observed_usage": observed, "effective_ceiling": ceil,
    })
    return did


def cmd_reserve(args) -> int:
    active = Path(args.active_dir)
    if not active.is_dir():
        print("FAIL_CLOSED:no_active_dir"); return EXIT_FAIL_CLOSED
    with Lock(active):
        state = read_state(active)
        events = read_ledger(active)
        validate_integrity(active, events, state)

        # DENY：未知角色（优先于 BLOCK）
        role = args.role
        if role not in ROLE_CONSUMES:
            _emit_decision(active, "DENY:unknown_role", None, None, None)
            print("DENY:unknown_role"); return EXIT_DENY_UNKNOWN
        consumes = ROLE_CONSUMES[role]

        rid = args.reservation_id or _new_id()
        # 重复 reservation_id → fail-closed（finding 1）
        if any(e.get("event") == "reserved" and e.get("reservation_id") == rid for e in events):
            print("FAIL_CLOSED:duplicate_reservation_id"); return EXIT_FAIL_CLOSED
        # 同一 (scope, target_round) 重复活跃预约 → fail-closed（finding 2）
        if consumes in SCOPE_PRODUCT:
            if (consumes, args.target_round) in active_targets(events):
                print("FAIL_CLOSED:double_target"); return EXIT_FAIL_CLOSED

        # BLOCK：总量硬上限（单调）
        total_used = total_reservations_issued(events)
        total_ceil = ceiling(state, "total")
        if total_used >= total_ceil:
            _emit_decision(active, "BLOCK:total_spawn_cap", "total", total_used, total_ceil)
            print("BLOCK:total_spawn_cap"); return EXIT_BLOCK_TOTAL

        # BLOCK：按 scope 预算
        if consumes != "none":
            usage = effective_usage(active, events, consumes)
            ceil = ceiling(state, consumes)
            if usage >= ceil:
                verdict = {"outer": "BLOCK:budget_exhausted",
                           "blind": "BLOCK:blind_exhausted",
                           "ultraverge": "BLOCK:ultraverge_exhausted"}[consumes]
                _emit_decision(active, verdict, consumes, usage, ceil)
                print(verdict)
                return {"outer": EXIT_BLOCK_BUDGET, "blind": EXIT_BLOCK_BLIND,
                        "ultraverge": EXIT_BLOCK_ULTRAVERGE}[consumes]

        # MODE_SWITCH（低于 BLOCK 优先级）
        if consumes == "outer" and mode_switch_required(state, args.target_round or 0):
            # MODE_SWITCH 是非 scope 决策 → scope/usage/ceiling 一律 null（v7）
            _emit_decision(active, "MODE_SWITCH_REQUIRED", None, None, None)
            print("MODE_SWITCH_REQUIRED"); return EXIT_MODE_SWITCH

        # PROCEED
        append_ledger(active, {
            "event": "reserved", "reservation_id": rid, "ts": _now(),
            "target_round": args.target_round, "target_role": role, "consumes": consumes,
            "counts_before": {s: effective_usage(active, events, s)
                              for s in ("outer", "blind", "ultraverge")} | {"total": total_used},
            "ceilings": {s: ceiling(state, s) for s in ("outer", "blind", "ultraverge", "total")},
            "extension_id": (active_extension(state, consumes) or {}).get("extension_id")
                             if consumes != "none" else None,
            "tier": args.tier,
        })
        print(f"PROCEED:{rid}")
        return EXIT_PROCEED


def cmd_settle(args) -> int:
    active = Path(args.active_dir)
    if not active.is_dir():
        print("FAIL_CLOSED:no_active_dir"); return EXIT_FAIL_CLOSED
    with Lock(active):
        events = read_ledger(active)
        state = read_state(active)
        validate_integrity(active, events, state)
        res = _reservation_status(events)
        if args.reservation_id not in res:
            print("FAIL_CLOSED:settle_without_reserve"); return EXIT_FAIL_CLOSED
        if res[args.reservation_id]["status"] != "reserved":
            print("FAIL_CLOSED:duplicate_settlement"); return EXIT_FAIL_CLOSED
        if args.result == "succeeded" and not args.instance_id:
            print("FAIL_CLOSED:missing_instance_id"); return EXIT_FAIL_CLOSED
        ev = {"event": {"succeeded": "spawn_succeeded", "failed": "spawn_failed",
                        "cancelled": "cancelled"}[args.result],
              "reservation_id": args.reservation_id, "ts": _now()}
        if args.result == "succeeded":
            ev["instance_id"] = args.instance_id
        if args.result == "cancelled":
            ev["pre_execution"] = bool(args.pre_execution)
        if args.reason:
            ev["reason"] = args.reason
        append_ledger(active, ev)
        print("OK")
        return EXIT_PROCEED


def cmd_ingest_verdict(args) -> int:
    active = Path(args.active_dir)
    if not active.is_dir():
        print("FAIL_CLOSED:no_active_dir"); return EXIT_FAIL_CLOSED
    if args.verdict not in VERDICTS:
        print("FAIL_CLOSED:verdict_parse"); return EXIT_FAIL_CLOSED
    with Lock(active):
        state = read_state(active)
        events = read_ledger(active)
        validate_integrity(active, events, state)
        if args.mode:
            state["fsm"]["mode"] = args.mode
        sev = [s.strip() for s in (args.severities or "").split(",") if s.strip()]
        if args.verdict == "阻断需修复" and sev:
            state["fsm"]["severities"][str(args.target_round)] = sev
        write_state(active, state)
        print("ok")
        return EXIT_PROCEED


def cmd_preflight(args) -> int:
    plan = Path(args.plan)
    if not plan.is_file():
        print("FAIL_CLOSED:no_plan"); return EXIT_FAIL_CLOSED
    blocks = loc = 0
    in_block = False
    for line in plan.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            if in_block:
                in_block = False
            else:
                in_block = True
                blocks += 1
            continue
        if in_block:
            loc += 1
    if blocks >= DEFAULTS["preflight_code_block_threshold"] or loc >= DEFAULTS["preflight_code_loc_threshold"]:
        print(f"WARN:code_heavy:{blocks},{loc}")
    else:
        print("CLEAN")
    return EXIT_PROCEED


# ---- best-effort guarded：宿主绑定 + PreToolUse 总量硬上限 hook --------------
# 这**不是** "enforced" tier（不提供角色不可伪造/权限锁定保证）。命名为
# **best-effort guarded**（亦即 hook-blocked auditable-only）：hook 在**绑定的收敛
# 会话**中对每次 Agent spawn 维护一个**独立于 ledger 的单调计数器**，达总量硬上限
# 即 deny。它不替代 orchestrator 的 per-scope reserve（两者互不干扰），只作 runaway
# 的兜底——即便 orchestrator 完全遗忘 per-scope 预算，hook 也在 cap 处硬停。
# cap 派生自 validated state 的 ceiling(total)（含授权链校验过的 scope=total
# extension），不接受任意传入。绑定存于 host 域（默认 ~/.claude/converge/bindings/）；
# 不做权限锁定，绑定可被 Agent 改写——该残余边界已与用户确认（蓄意自篡改属另一威胁模型）。
BINDINGS_DIR = Path(os.environ.get(
    "CONVERGE_BINDINGS_DIR", str(Path.home() / ".claude" / "converge" / "bindings")))
SPAWN_TOOL_NAMES = {"Agent"}   # converge Spawn = Claude Code `Agent` 工具


def _binding_path(session_id: str) -> Path:
    # 无碰撞：以完整 session_id 的 sha256 命名（避免 a/b 与 a?b 撞同一文件）。
    import hashlib
    h = hashlib.sha256((session_id or "").encode("utf-8")).hexdigest()
    return BINDINGS_DIR / f"{h}.json"


class FileLock:
    def __init__(self, path: Path, timeout: float = 5.0):
        self.lock = Path(str(path) + ".lock")
        self.timeout = timeout
        self.fd = None

    def __enter__(self):
        deadline = time.time() + self.timeout
        while True:
            try:
                if self.lock.exists() and (time.time() - self.lock.stat().st_mtime) > LOCK_STALE_SECONDS:
                    self.lock.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                self.fd = os.open(str(self.lock), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                if time.time() > deadline:
                    raise FailClosed("binding_lock_timeout")
                time.sleep(0.02)

    def __exit__(self, *exc):
        if self.fd is not None:
            os.close(self.fd)
            self.lock.unlink(missing_ok=True)


def _validate_binding(binding, sid: str) -> None:
    """绑定文件严格 schema：防负数/错类型 counter 绕过 cap（finding 2）。任一异常 → FailClosed。"""
    if not isinstance(binding, dict):
        raise FailClosed("binding_not_object")
    if not _nonempty_str(binding.get("session_id")) or binding.get("session_id") != sid:
        raise FailClosed("binding_field:session_id")
    for f in ("hook_spawn_count", "hook_spawn_cap"):
        v = binding.get(f)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise FailClosed(f"binding_field:{f}")
    if not _nonempty_str(binding.get("active_dir")):
        raise FailClosed("binding_field:active_dir")
    if binding.get("mode") != "best-effort-guarded":
        raise FailClosed("binding_field:mode")


def _validated_total_cap(active: Path) -> int:
    """从**经完整校验**的 state 派生总量上限（含 validated scope=total extension）。

    cap 不接受任意传入——只能来自 validate_integrity 通过的 state 的 ceiling(total)，
    从而强制走 extension 授权链（封堵任意 --cap 绕过）。
    """
    state = read_state(active)
    events = read_ledger(active)
    validate_integrity(active, events, state)
    return ceiling(state, "total")


def cmd_bind(args) -> int:
    active = Path(args.active_dir).resolve()
    if not active.is_dir():
        print("FAIL_CLOSED:no_active_dir"); return EXIT_FAIL_CLOSED
    BINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    bp = _binding_path(args.session_id)
    try:
        with FileLock(bp):
            if bp.exists():
                # 已绑定 → 拒绝重置（防 re-bind 清零计数绕过 cap）。改用 refresh-cap。
                print("FAIL_CLOSED:already_bound"); return EXIT_FAIL_CLOSED
            cap = _validated_total_cap(active)
            bp.write_text(json.dumps({
                "session_id": args.session_id, "slug": active.name, "active_dir": str(active),
                "mode": "best-effort-guarded", "hook_spawn_count": 0, "hook_spawn_cap": int(cap),
                "governed_tools": sorted(SPAWN_TOOL_NAMES), "created_at": _now(),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"BOUND:{args.session_id}:cap={cap}")
        return EXIT_PROCEED
    except FailClosed as e:
        print(f"FAIL_CLOSED:{e.reason}"); return EXIT_FAIL_CLOSED


def cmd_refresh_cap(args) -> int:
    """扩容 cap，**保留 count**。新 cap **只能来自经验证的 `scope=total` extension**——
    普通 config 变化不得改变已绑定 cap（封堵改 config 绕授权链）。"""
    bp = _binding_path(args.session_id)
    try:
        with FileLock(bp):
            if not bp.exists():
                print("FAIL_CLOSED:not_bound"); return EXIT_FAIL_CLOSED
            binding = json.loads(bp.read_text(encoding="utf-8"))
            _validate_binding(binding, args.session_id)
            active = Path(binding["active_dir"])
            state = read_state(active)
            validate_integrity(active, read_ledger(active), state)   # 校验 extension 授权链
            ext = active_extension(state, "total")
            if ext is None:
                # 无 validated scope=total extension → 无授权可刷新（config 变化无效）。
                print("FAIL_CLOSED:no_total_extension"); return EXIT_FAIL_CLOSED
            new_cap = int(ext["new_ceiling"])
            if new_cap < int(binding["hook_spawn_cap"]):
                print("FAIL_CLOSED:cap_would_decrease"); return EXIT_FAIL_CLOSED
            binding["hook_spawn_cap"] = new_cap            # count 保持不变
            binding["refreshed_at"] = _now()
            bp.write_text(json.dumps(binding, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"REFRESHED:{args.session_id}:cap={new_cap}:count={binding['hook_spawn_count']}")
        return EXIT_PROCEED
    except FailClosed as e:
        print(f"FAIL_CLOSED:{e.reason}"); return EXIT_FAIL_CLOSED


def cmd_unbind(args) -> int:
    bp = _binding_path(args.session_id)
    try:
        with FileLock(bp):
            bp.unlink(missing_ok=True)
    except FailClosed as e:
        print(f"FAIL_CLOSED:{e.reason}"); return EXIT_FAIL_CLOSED
    print("UNBOUND")
    return EXIT_PROCEED


def _emit_deny(reason: str) -> None:
    # ensure_ascii=True：deny JSON 走 ASCII，规避 Windows hook stdout 编码不确定性。
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, ensure_ascii=True))


def cmd_hook_pretooluse(args) -> int:
    """Claude Code PreToolUse hook 入口：读 stdin JSON，绑定会话的 Agent spawn 计数+裁决。

    fail 边界（按审计指引）：
    - **未绑定会话 / 非 spawn 工具 / 无法识别会话**（stdin 不可解析）→ 放行（passthrough）。
      不误阻无关 Agent 调用；binding 被删＝未绑定＝放行，属已确认的 best-effort 残余
      （蓄意自篡改属另一威胁模型）。
    - **绑定存在 = 已知 enforced 会话**：此后**任何**歧义/损坏/锁/写错误 → **DENY**（fail-closed），
      封堵"篡坏 binding 以禁用上限"的逃避向量；达上限亦 DENY。
    """
    try:
        data = json.load(sys.stdin)
        tool = data.get("tool_name")
        sid = data.get("session_id")
    except (json.JSONDecodeError, OSError, ValueError):
        return EXIT_PROCEED   # 无法识别会话 → 放行（非 Agent 可控的逃避向量）
    if tool not in SPAWN_TOOL_NAMES:
        return EXIT_PROCEED
    bp = _binding_path(sid or "")
    if not bp.exists():
        return EXIT_PROCEED   # 未绑定 → 放行

    # —— 已知绑定会话：从此 fail-closed ——
    try:
        with FileLock(bp):
            binding = json.loads(bp.read_text(encoding="utf-8"))
            # 严格 schema（含文件内 session_id 一致、count/cap 为非负整数）。
            _validate_binding(binding, sid)
            count = binding["hook_spawn_count"]
            cap = binding["hook_spawn_cap"]
            if count >= cap:
                _emit_deny(
                    f"converge budget_gate: bound session Agent-spawn total hard cap {cap} reached "
                    f"(slug={binding.get('slug')}). best-effort guarded runaway backstop. To continue: "
                    f"user-authorized scope=total extension + refresh-cap, or accept/simplify/terminate.")
                return EXIT_PROCEED
            binding["hook_spawn_count"] = count + 1
            bp.write_text(json.dumps(binding, ensure_ascii=False, indent=2), encoding="utf-8")
        return EXIT_PROCEED
    except Exception as exc:  # noqa: BLE001 —— 绑定会话出错 → fail-closed DENY
        _emit_deny(
            f"converge budget_gate: bound session binding is ambiguous/corrupt "
            f"({type(exc).__name__}); failing closed (deny). Fix or unbind the binding and retry.")
        return EXIT_PROCEED


def _run(func, args) -> int:
    """统一异常边界：任何未预期异常 → FAIL_CLOSED(30)，绝不裸退出 1。"""
    try:
        return func(args)
    except FailClosed as e:
        print(f"FAIL_CLOSED:{e.reason}")
        return EXIT_FAIL_CLOSED
    except Exception as e:  # noqa: BLE001  —— fail-closed 安全网
        print(f"FAIL_CLOSED:internal:{type(e).__name__}:{e}")
        return EXIT_FAIL_CLOSED


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="budget_gate")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("reserve")
    r.add_argument("--active-dir", required=True)
    r.add_argument("--role", required=True)
    r.add_argument("--reservation-id")
    r.add_argument("--target-round", type=int)
    r.add_argument("--tier", default="auditable-only", choices=["auditable-only", "enforced"])
    r.set_defaults(func=cmd_reserve)

    s = sub.add_parser("settle")
    s.add_argument("--active-dir", required=True)
    s.add_argument("--reservation-id", required=True)
    s.add_argument("--result", required=True, choices=["succeeded", "failed", "cancelled"])
    s.add_argument("--instance-id")
    s.add_argument("--pre-execution", action="store_true")
    s.add_argument("--reason")
    s.set_defaults(func=cmd_settle)

    iv = sub.add_parser("ingest-verdict")
    iv.add_argument("--active-dir", required=True)
    iv.add_argument("--target-round", type=int, required=True)
    iv.add_argument("--verdict", required=True)
    iv.add_argument("--severities")
    iv.add_argument("--mode", choices=["standard", "ultraverge"])
    iv.set_defaults(func=cmd_ingest_verdict)

    pf = sub.add_parser("preflight")
    pf.add_argument("--plan", required=True)
    pf.set_defaults(func=cmd_preflight)

    bd = sub.add_parser("bind")        # 会话开始时绑定 session→active（cap 派生自 validated state）
    bd.add_argument("--session-id", required=True)
    bd.add_argument("--active-dir", required=True)
    bd.set_defaults(func=cmd_bind)

    rc = sub.add_parser("refresh-cap")  # scope=total 扩容后原子刷新 cap，保留 count
    rc.add_argument("--session-id", required=True)
    rc.set_defaults(func=cmd_refresh_cap)

    ub = sub.add_parser("unbind")      # 会话结束时解绑
    ub.add_argument("--session-id", required=True)
    ub.set_defaults(func=cmd_unbind)

    hk = sub.add_parser("hook-pretooluse")   # PreToolUse hook 入口（读 stdin）
    hk.set_defaults(func=cmd_hook_pretooluse)

    args = p.parse_args()
    return _run(args.func, args)


if __name__ == "__main__":
    sys.exit(main())
