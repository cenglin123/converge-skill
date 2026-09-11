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
import hashlib
import json
import math
import os
import re
import subprocess
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
EXIT_BLOCK_TASK_ENVELOPE = 14
EXIT_BLOCK_EMPIRICAL = 15
EXIT_MODE_SWITCH = 20
EXIT_DENY_UNKNOWN = 21
EXIT_DENY_ILLEGAL = 22
EXIT_FAIL_CLOSED = 30

# archive_contract.model 是 Round 表示的权威源（invocation-started 的 `round` 字段契约：
# null 或正整数）；ledger 的 `target_round` 由同一 canonical_round() 归一化产生，不允许
# 一处写字面 0、一处要求 null（plan Phase1 step2）。budget_gate.py 与 archive_contract 同在
# scripts/ 目录，脚本入口执行时该目录天然在 sys.path[0] 上，故本导入无需额外路径处理。
from archive_contract.model import canonical_round  # noqa: E402

DEFAULTS = {
    # 实证恢复的止损上限（非预期调用次数）：0137fce 两次复杂收敛 outer 7/12、blind 3/4
    # 仍在持续推进；d3c82cb 治理任务至 outer R8、blind #2 后方通过——outer=8/blind=3
    # 据此恢复为复杂任务止损上限。inner=3 为已发布兼容保留（无缩减证据，不声称同等
    # 强度的实证校准）。
    "max_outer_loops": 8,
    "max_blind_rechecks": 3,
    "ultraverge_min_reviewers": 3,
    "max_inner_loops": 3,
    "impl_severity_streak_threshold": 3,
    "preflight_code_block_threshold": 3,
    "preflight_code_loc_threshold": 40,
    "total_safety": 1.5,
}

# 旧版默认值：sparse legacy state（defaults_version=1）使用此表回退，
# 不随 DEFAULTS 变化而静默改变有效预算（DR1 权威性一致性）。
LEGACY_DEFAULTS = {
    "max_outer_loops": 8,
    "max_blind_rechecks": 3,
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
    # l2-gate-reviewer：Dynamic Workflows 门控专用角色，对应 refs/quality-gate.md 的
    # "L2 重量级" Reviewer（该文档只用 "L2 Reviewer" 这一散文名，二者是同一机制的两个
    # 名字——见 refs/state-schema.md §预算 gate 的角色对照表）。consumes=none：不占用
    # outer/blind/ultraverge 预算。它绝不能成为终局 owner——不在
    # archive_contract/model.py 的 REVIEWER_AUTHORITIES 任一列表内，且
    # capture.record_terminal_decision 在写入前就会拒绝把它登记为 reviewer-verdict
    # owner（plan Phase1 step1；这是设计选择，不是遗漏：门控"不否决不阻断"）。
    "l2-gate-reviewer": "none",
    "design-reviewer": "none",
    # task-envelope：跨 spawn/跨角色的任务级总信封（plan §6.1/§6.3），与本表其余角色
    # 计的 outer/blind/ultraverge/total 是不同维度、并行累加，不冲突、不替换。使用方式：
    # 每次真实 OCSR/模型调用，在其角色本身的 reserve 之外，另行调用一次
    # `reserve --role task-envelope`（同一 reservation 机制，scope 名与角色名相同）。
    # 未配置任务档（config 无 task_tier/task_envelope_cap）时不可用，见 _task_envelope_configured。
    "task-envelope": "task-envelope",
}

# 四档任务预算默认值（plan §6.1）：初始额度 = 预期消费区间（到达即 BLOCK，需走 extension）；
# cap = 一次性授权上限（同 scope 的 extension 不得超过该值，见 validate_extensions）。
_TASK_TIERS_BASE = {
    "small":    {"initial": 4,  "cap": 8},
    "medium":   {"initial": 8,  "cap": 16},
    "feature":  {"initial": 16, "cap": 24},
    "critical": {"initial": 20, "cap": 30},
}
TASK_TIERS = {**_TASK_TIERS_BASE, "critical/ultraverge": _TASK_TIERS_BASE["critical"]}   # plan §6.1 表头字面档名的别名

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


def _mint_call_id() -> str:
    """Mint one unique call_id per instrumented model call (D10)."""
    return uuid.uuid4().hex[:16]


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
    # newline="\n" pins the line terminator regardless of platform default (os.linesep is
    # "\r\n" on Windows) — gate-ledger.jsonl is a root-fixed file the Archive Contract hashes,
    # and must stay byte-identical to what Git (`.gitattributes: * text=auto eol=lf`) checks
    # out, or a later `check`/`check-git-ref` re-verification reports content-mismatch (plan
    # Phase 5 step 5's newline policy).
    with _ledger_path(active).open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _validate_state_shape(st: dict) -> None:
    """Shared state-shape/value validator for read_state() and initialize_state().

    Validates before calling .items(), .get(), or .setdefault() on any unproved
    nested type. Raises FailClosed on any violation.

    Does NOT enforce version-specific INT_CONFIG range (v >= 1) because read_state()
    must accept sparse legacy states with zero-valued INT_CONFIG.  That stricter check
    lives in initialize_state() where defaults_version is known.
    """
    if not isinstance(st.get("config", {}), dict):
        raise FailClosed("state_corrupt:config_not_object")
    if not isinstance(st.get("extensions", []), list):
        raise FailClosed("state_corrupt:extensions_not_list")
    fsm = st.get("fsm")
    if not isinstance(fsm, dict):
        raise FailClosed("state_corrupt:fsm_not_object")
    mode = fsm.get("mode", "standard")
    if not isinstance(mode, str) or mode not in ("standard", "ultraverge"):
        raise FailClosed(f"state_corrupt:fsm_mode_invalid:{mode}")
    if not isinstance(fsm.get("severities", {}), dict):
        raise FailClosed("state_corrupt:severities_not_object")
    # Config key validation: reject unknown keys (shared by read_state + initialize_state).
    # Type checks for known keys (bool-as-int, wrong type) applied here; range checks
    # (v < 1) deferred to caller with version context.
    cfgd = st.get("config", {})
    _INT_TASK_KEYS = {"task_envelope_initial", "task_envelope_cap"}
    for k, v in cfgd.items():
        if k not in DEFAULTS and k not in ("task_tier", "task_envelope_initial",
                                            "task_envelope_cap"):
            raise FailClosed(f"config_unknown:{k}")
        if k in INT_CONFIG or k in _INT_TASK_KEYS:
            if isinstance(v, bool) or not isinstance(v, int):
                raise FailClosed(f"config_type:{k}")
        if k == "total_safety":
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise FailClosed(f"config_type:{k}")


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
    _validate_state_shape(st)
    st["fsm"].setdefault("mode", "standard")
    st["fsm"].setdefault("severities", {})
    return st


def write_state(active: Path, state: dict) -> None:
    # newline="\n": same LF-pinning rationale as append_ledger above — _budget-state.json is
    # also a root-fixed, manifest-hashed file.
    _state_path(active).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )


def initialize_state(active: Path, *, mode: str | None = None,
                     config: dict | None = None, force: bool = False) -> dict:
    """Host-independent 状态初始化器/解析器（plan D3）。

    手动 orchestrator、ocsr_spawn_adapter config-init、converge_loop run
    三条入口共享同一初始化契约。行为：

    1. 无 active state → 创建 standard/ultraverge 模式 + 显式 config 写入。
    2. 已有 state → 校验完整状态/ledger；省略字段继承 active state；
       显式相等值为幂等 no-op；冲突值 fail-closed（不静默覆盖）。
    3. standard 与 ultraverge 共用同一组默认值上限，无模式叠加。
    4. 未知键、布尔伪装整数、负数、字符串数字、malformed shape → fail-closed。
    5. force=True 跳过冲突检查，直接覆盖。
    6. mode=None 表示省略：已有 state 继承其模式，新 state 默认 standard。
    """
    p = _state_path(active)
    if config is not None and not isinstance(config, dict):
        raise FailClosed(f"config_type:not_mapping")
    explicit = dict(config or {})

    # --- 校验显式 config 值（无论是否有已有 state） ---
    for k, v in explicit.items():
        if k not in DEFAULTS and k not in ("task_tier", "task_envelope_initial",
                                            "task_envelope_cap"):
            raise FailClosed(f"config_unknown:{k}")
        if k in INT_CONFIG:
            if isinstance(v, bool) or not isinstance(v, int):
                raise FailClosed(f"config_type:{k}")
            if v < 1:
                raise FailClosed(f"config_type:{k}")
        if k == "total_safety":
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise FailClosed(f"config_type:{k}")
            if v <= 0:
                raise FailClosed(f"config_type:total_safety")
        if k == "task_tier":
            if v not in TASK_TIERS:
                raise FailClosed(f"config_type:task_tier")
        if k in ("task_envelope_initial", "task_envelope_cap"):
            if isinstance(v, bool) or not isinstance(v, int) or v < 1:
                raise FailClosed(f"config_type:{k}")
    # cap >= initial when both present
    if "task_envelope_initial" in explicit and "task_envelope_cap" in explicit:
        if explicit["task_envelope_cap"] < explicit["task_envelope_initial"]:
            raise FailClosed("config_type:task_envelope_cap_lt_initial")

    # 校验显式 mode 参数（无论新旧 state）
    if mode is not None and mode not in ("standard", "ultraverge"):
        raise FailClosed(f"state_corrupt:fsm_mode_invalid:{mode}")

    if p.is_file():
        # --- 已有 state ---
        try:
            state = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise FailClosed(f"state_corrupt:{e}")
        if not isinstance(state, dict):
            raise FailClosed("state_corrupt:not_object")
        state.setdefault("config", {})
        state.setdefault("extensions", [])
        state.setdefault("fsm", {"mode": "standard", "severities": {}})
        # 校验 defaults_version：必须是 exactly int 1 或 2（bool 是 int 子类，拒绝）
        dv = state.get("defaults_version")
        if dv is not None:
            if isinstance(dv, bool) or not isinstance(dv, int) or dv not in (1, 2):
                raise FailClosed(f"state_corrupt:defaults_version:{dv}")
        # 共享 state shape/value 校验（config 类型/键、extensions 类型、fsm 类型/mode 值）
        _validate_state_shape(state)
        # 读取 ledger 并校验完整性（validate_integrity 包含 v2 INT_CONFIG 范围校验、
        # task_tier/task_envelope/total_safety 校验——单一事实源，不在此重复）。
        events = read_ledger(active)
        validate_integrity(active, events, state)

        # 标记旧版 sparse state（无 defaults_version 字段）。
        # 不重写旧版 state：defaults_version 缺失 → cfg() 内存中视为 version 1（LEGACY_DEFAULTS 回退）。
        # 旧版 state 字节不变，测试断言 defaults_version == 1、有效值、字节不变。

        if not force:
            # 冲突检查：显式值必须与已有值一致
            for k, v in explicit.items():
                if k in state["config"] and state["config"][k] != v:
                    raise FailClosed(f"config_conflict:{k}")
            # mode 冲突检查：显式 mode 与已有 fsm.mode 不一致 → fail-closed
            if mode is not None and state["fsm"].get("mode") != mode:
                raise FailClosed(f"mode_conflict:{state['fsm'].get('mode')}!={mode}")

        # 合并显式值到 state（不写磁盘）。
        # 目标：state["config"] 反映显式值的并集，cfg() 用它做回退。
        if force:
            state["config"].update(explicit)
        else:
            for k, v in explicit.items():
                state["config"].setdefault(k, v)

        # 应用 mode overlay（mode=None 时继承已有模式，不覆盖）
        if mode is not None:
            if force:
                state["fsm"]["mode"] = mode
            elif state["fsm"].get("mode") is None:
                state["fsm"]["mode"] = mode
        # mode=None: 继承已有 fsm.mode，不做任何修改

        # Re-validate merged candidate against ledger: catches cross-key relationships
        # assembled from old state + explicit config (R7 cross-overlay bug).
        validate_integrity(active, events, state)

        # 仅在实际内容变化时写入（避免 reformatted JSON 改变字节）。
        # 读取已有 state（不经过 setdefault），与 merged state 比较。
        try:
            raw_state = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw_state = None
        raw_state = raw_state if isinstance(raw_state, dict) else {}
        raw_state.setdefault("config", {})
        raw_state.setdefault("fsm", {"mode": "standard", "severities": {}})
        raw_state.setdefault("extensions", [])
        needs_write = (
            force
            or state["config"] != raw_state["config"]
            or state["fsm"] != raw_state["fsm"]
            or state["extensions"] != raw_state["extensions"]
        )
        if needs_write:
            write_state(active, state)
        return state

    # --- 新建 state ---
    # mode=None 时默认 standard
    effective_mode = mode if mode is not None else "standard"
    # 无模式叠加：standard 与 ultraverge 共用同一组默认值上限（plan r2 D9）
    merged_config = dict(explicit)

    state = {
        "defaults_version": 2,
        "config": merged_config,
        "extensions": [],
        "fsm": {"mode": effective_mode, "severities": {}},
    }
    # 校验候选状态（单一契约：与已有 state 路径的 validate_integrity 对称）
    validate_integrity(active, [], state)
    active.mkdir(parents=True, exist_ok=True)
    write_state(active, state)
    return state


def cfg(state: dict, key: str):
    if key in state.get("config", {}):
        return state["config"][key]
    # defaults_version 缺失 → version 1（LEGACY_DEFAULTS 回退），
    # 不随 DEFAULTS 变化而静默改变有效预算（plan D3 + DR1）。
    # 新建 state 写入 defaults_version=2，回退到 DEFAULTS。
    version = state.get("defaults_version", 1)
    if isinstance(version, bool) or not isinstance(version, int) or version not in (1, 2):
        raise FailClosed(f"state_corrupt:defaults_version:{version}")
    if version == 1 and key in LEGACY_DEFAULTS:
        return LEGACY_DEFAULTS[key]
    return DEFAULTS[key]


# In-memory 追踪哪些 active 目录是 legacy sparse state（无 defaults_version 字段）。
# _legacy_active_paths: set[str] = set()
# 注意：此全局集合已移除（plan D3 + 修复项 A）。
# 状态权威性改为 state 自带 defaults_version 字段：无此字段 → 内存中视为 version 1（LEGACY_DEFAULTS 回退）。
# 新建 state 写入 defaults_version=2。不因读/初始化而重写旧版 state。


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
            if et in ("cancelled", "spawn_failed"):
                res[rid]["pre_execution"] = bool(ev.get("pre_execution", False))
    return res


def total_reservations_issued(events: list[dict]) -> int:
    """`total` scope 的单调计数——不含 task-envelope。task-envelope 是独立于 total 的并行
    累加维度（plan §6.3：不消费也不受 total 硬上限约束），故显式排除，避免 task-envelope
    的 reserve 调用意外挤占其它角色的 total 预算空间（详见 cmd_reserve 中同一 rationale）。"""
    res = _reservation_status(events)
    return sum(1 for r in res.values()
               if r["consumes"] != "task-envelope"
               and not (r["status"] == "cancelled" and r["pre_execution"]))


def scope_reservations_issued(events: list[dict], scope: str) -> int:
    """按 consumes 过滤的单调计数，用法与 total_reservations_issued 一致——用于没有
    round-N.md 文件产物、因而不适用 realized()/pending() 模型的 scope（目前只有
    task-envelope：它是跨 spawn/跨角色的任务级累加，不对应任何具体文件产物）。"""
    res = _reservation_status(events)
    return sum(1 for r in res.values()
               if r["consumes"] == scope
               and not (r["status"] == "cancelled" and r["pre_execution"]))


def attempted_dispatch(events: list[dict], scope: str | None = None) -> int:
    """dispatch 尝试总数——含启动前失败/CLI 错误，不含 pre_execution 取消（plan Phase1
    step4 双计数模型的第一项）。scope=None 时为全局汇总（跨全部 consumes，含 task-envelope）。"""
    res = _reservation_status(events)
    return sum(1 for r in res.values()
               if (scope is None or r["consumes"] == scope)
               and not (r["status"] == "cancelled" and r["pre_execution"]))


def model_invocation(events: list[dict], scope: str | None = None) -> int:
    """真实模型调用数——spawn_succeeded 全部计入；spawn_failed 仅当 pre_execution=false
    （即模型确实被调用过，只是调用后失败）才计入。不含任何 pre_execution=true 的失败/取消，
    也不含仍处于 reserved（尚未 settle）状态的预约（plan Phase1 step4 双计数模型第二项）。"""
    res = _reservation_status(events)
    count = 0
    for r in res.values():
        if scope is not None and r["consumes"] != scope:
            continue
        if r["status"] == "spawn_succeeded":
            count += 1
        elif r["status"] == "spawn_failed" and not r["pre_execution"]:
            count += 1
    return count


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
            # task-envelope 专属约束：cap（一次性授权上限）是真正的硬顶，extension 也不
            # 得突破它——outer/blind/ultraverge/total 的 extension 无此上限（只要求单调
            # 递增），task-envelope 的语义是"§6.2 硬上限是一次性授权边界"，与其它 scope
            # 不同，需要单独校验（plan Phase1 step5）。
            if scope == "task-envelope" and ext.get("new_ceiling", 0) > _task_envelope_hard_cap(state):
                raise FailClosed("ext_task_envelope_exceeds_cap")
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
    if scope == "task-envelope":
        return _task_envelope_initial(state)
    raise FailClosed(f"unknown_scope:{scope}")


def default_total_cap(state: dict) -> int:
    base = (3 + cfg(state, "ultraverge_min_reviewers")
            + cfg(state, "max_outer_loops") * (1 + cfg(state, "max_inner_loops"))
            + cfg(state, "max_blind_rechecks") + 1)
    return math.ceil(cfg(state, "total_safety") * base)


# ---- 任务档预算（task-envelope，plan §6.1/§6.3）------------------------------
def _task_envelope_configured(state: dict) -> bool:
    c = state.get("config", {})
    return "task_tier" in c or "task_envelope_cap" in c


def _task_envelope_initial(state: dict) -> int:
    """初始额度（预期消费区间，到达即 BLOCK；不是"必须用完"，只是 reserve() 的默认 ceiling，
    未配置任务档时不可调用——调用方须先检查 _task_envelope_configured()。"""
    c = state.get("config", {})
    if "task_envelope_initial" in c:
        return int(c["task_envelope_initial"])
    tier = c.get("task_tier")
    if tier not in TASK_TIERS:
        raise FailClosed("task_envelope_not_configured")
    return TASK_TIERS[tier]["initial"]


def _task_envelope_hard_cap(state: dict) -> int:
    """一次性授权上限（§6.2 硬上限）——ceiling() 的默认值不得超过它，extension 也不得
    超过它（validate_extensions 的 task-envelope 专属校验）。"""
    c = state.get("config", {})
    if "task_envelope_cap" in c:
        return int(c["task_envelope_cap"])
    tier = c.get("task_tier")
    if tier not in TASK_TIERS:
        raise FailClosed("task_envelope_not_configured")
    return TASK_TIERS[tier]["cap"]


# ---- 统一 validator（findings 共同根因）------------------------------------
TIER_VALUES = {"enforced", "auditable-only"}
CONSUMES_VALUES = {"outer", "blind", "ultraverge", "none", "task-envelope"}
# SCOPE_KEYS：reserved 事件 counts_before/ceilings 的**必填**键集合，未配置任务档时保持不变
# （A8 向后兼容——旧 ledger/旧调用方完全不受影响）。task-envelope 仅在任务档已配置时作为
# **额外可选键**出现在这两个 dict 中（见 cmd_reserve），不加入本必填集合。
SCOPE_KEYS = ("outer", "blind", "ultraverge", "total")
DECISION_SCOPES = (None, "outer", "blind", "ultraverge", "total", "task-envelope")
DECISION_EXACT = {"MODE_SWITCH_REQUIRED"}
BLOCK_SUFFIXES = {"budget_exhausted", "blind_exhausted", "ultraverge_exhausted", "total_spawn_cap", "task_envelope_exhausted"}
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

    本脚本是 gate-ledger / `_budget-state.json` / 计数 / 事件契约等全量机器数据契约的
    单一权威源（编译）；refs/state-schema.md §预算 gate 仅保留 agent 需读的角色摘要。任何缺字段 /
    错类型 / 非法 enum / 嵌套结构不合 → FAIL_CLOSED（不让损坏事件污染计数）。
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
        elif ev.get("target_round") is not None and not _pos_int(ev.get("target_round")):
            # 与 archive_contract/model.py 的 invocation `round` 契约（null 或正整数）
            # 统一：Round 0 唯一合法表示是 null，literal 0 一律拒绝（plan Phase1 step2）。
            # cmd_reserve 通过 canonical_round() 在写入前把调用方传入的 0 归一化为 None，
            # 故此处只会在有人绕过 CLI 直接注入 ledger 时触发，属防御性 fail-closed。
            raise FailClosed("event_field:reserved.target_round")
        for fld in ("counts_before", "ceilings"):
            d = ev.get(fld)
            if not isinstance(d, dict) or any(not _int(d.get(k)) for k in SCOPE_KEYS):
                raise FailClosed(f"event_field:reserved.{fld}")
            # task-envelope 是可选附加键（仅任务档已配置时 cmd_reserve 才写入），若出现须为 int。
            if "task-envelope" in d and not _int(d["task-envelope"]):
                raise FailClosed(f"event_field:reserved.{fld}.task-envelope")
        eid = ev.get("extension_id")
        if eid is not None and not _nonempty_str(eid):
            raise FailClosed("event_field:reserved.extension_id")
        if ev.get("tier") not in TIER_VALUES:
            raise FailClosed("event_field:reserved.tier")
        # D10: call_id (optional, set by instrumented dispatch)
        cid = ev.get("call_id")
        if cid is not None and not _nonempty_str(cid):
            raise FailClosed("event_field:reserved.call_id")
        # D10: companion_reservation_id (optional, links Spawn pair)
        comp_rid = ev.get("companion_reservation_id")
        if comp_rid is not None and not _nonempty_str(comp_rid):
            raise FailClosed("event_field:reserved.companion_reservation_id")

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
        # pre_execution（可选，默认 false）：区分"启动前失败/CLI 参数错误"（true，从未真正
        # 调用模型）与"真实模型调用后失败"（false）——双计数模型（attempted_dispatch vs
        # model_invocation，plan Phase1 step4）依赖此字段，语义与 cancelled.pre_execution 对齐。
        if "pre_execution" in ev and not isinstance(ev["pre_execution"], bool):
            raise FailClosed("event_field:spawn_failed.pre_execution")

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
            if scope not in ("outer", "blind", "ultraverge", "total", "task-envelope"):
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
    if "total_safety" in cfgd and cfgd["total_safety"] <= 0:
        raise FailClosed("config_type:total_safety")
    if "task_tier" in cfgd and cfgd["task_tier"] not in TASK_TIERS:
        raise FailClosed("config_type:task_tier")
    for k in ("task_envelope_initial", "task_envelope_cap"):
        if k in cfgd and (isinstance(cfgd[k], bool) or not isinstance(cfgd[k], int) or cfgd[k] < 1):
            raise FailClosed(f"config_type:{k}")
    if ("task_envelope_initial" in cfgd and "task_envelope_cap" in cfgd
            and cfgd["task_envelope_cap"] < cfgd["task_envelope_initial"]):
        raise FailClosed("config_type:task_envelope_cap_lt_initial")
    # v2 INT_CONFIG 范围校验：v2 state 的 INT_CONFIG 值必须 >= 1；
    # sparse legacy state（无 defaults_version）保留零值边界兼容。
    dv = state.get("defaults_version")
    if dv == 2:
        for k in INT_CONFIG:
            if k in cfgd and cfgd[k] < 1:
                raise FailClosed(f"config_type:{k}")

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

    # D10: Companion reservation invariants (exactly-once pairing, no orphan,
    # no cross-link, no duplicate).  Supports two paths:
    #   - Atomic pair (cmd_reserve): both role and companion carry
    #     companion_reservation_id pointing at each other.
    #   - Pre-reserved adapter (cmd_companion_for): only the companion
    #     carries companion_reservation_id pointing at the role; the role
    #     has no forward reference.  This is the append-only path.
    reserved_by_rid = {ev.get("reservation_id"): ev for ev in events
                       if ev.get("event") == "reserved"}
    # Track which role→companion links have been validated (avoid double-
    # counting when both sides carry companion_reservation_id).
    validated_pairs: set[tuple[str, str]] = set()
    # Track which role rids have been claimed by a companion (duplicate check)
    claimed_roles: dict[str, str] = {}  # role_rid → companion_rid
    for ev in events:
        if ev.get("event") != "reserved":
            continue
        comp_rid = ev.get("companion_reservation_id")
        if comp_rid is None:
            continue
        # comp_rid points to the "other side" of the pair.
        # If ev is the companion (target_role == task-envelope), comp_rid is
        # the role rid.  If ev is the role, comp_rid is the companion rid.
        # We need to find the actual role event and companion event.
        if ev.get("target_role") == "task-envelope":
            # ev is the companion; comp_rid is the role
            role_rid = comp_rid
            comp_ev = ev
            role_ev = reserved_by_rid.get(role_rid)
        else:
            # ev is the role; comp_rid is the companion
            role_rid = ev["reservation_id"]
            comp_ev = reserved_by_rid.get(comp_rid)
            role_ev = ev
        # Deduplicate: in the atomic pair path, both events carry
        # companion_reservation_id and we'd validate the same pair twice.
        pair_key = (role_rid, comp_ev.get("reservation_id") if comp_ev else comp_rid)
        if pair_key in validated_pairs:
            continue
        validated_pairs.add(pair_key)
        # Companion must exist
        if comp_ev is None:
            raise FailClosed(f"companion_orphan:{ev['reservation_id']}->{comp_rid}")
        # Role must exist
        if role_ev is None:
            raise FailClosed(f"companion_orphan:{ev['reservation_id']}->{comp_rid}")
        # Exactly one companion per role (no duplicate)
        if role_rid in claimed_roles:
            existing_comp = claimed_roles[role_rid]
            if existing_comp != (comp_ev.get("reservation_id") if comp_ev else comp_rid):
                raise FailClosed(f"companion_duplicate:{role_rid}")
        else:
            claimed_roles[role_rid] = comp_ev.get("reservation_id") if comp_ev else comp_rid
        # Type check: exactly one must be task-envelope
        roles = {role_ev.get("target_role"), comp_ev.get("target_role")}
        if "task-envelope" not in roles:
            raise FailClosed("companion_missing_te_role")
        if roles == {"task-envelope"}:
            raise FailClosed("companion_both_te_role")
        # Cross-call link: when both sides carry call_id, they must match
        role_cid = role_ev.get("call_id")
        comp_cid = comp_ev.get("call_id")
        if role_cid is not None and comp_cid is not None and role_cid != comp_cid:
            raise FailClosed(
                f"companion_cross_call:{ev['reservation_id']}")

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

    # --companion-for: create a task-envelope companion for an existing role reservation
    if getattr(args, 'companion_for', None):
        return cmd_companion_for(args)

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

        # Round 0 单一规范表示：调用方传入的 0 在写入前归一化为 None，与
        # archive_contract 的 invocation `round` 契约（null 或正整数）保持一致
        # （plan Phase1 step2）。非法值（负数/非 int）→ fail-closed。
        try:
            target_round = canonical_round(args.target_round)
        except ValueError:
            print("FAIL_CLOSED:event_field:reserved.target_round"); return EXIT_FAIL_CLOSED

        rid = args.reservation_id or _new_id()
        # 重复 reservation_id → fail-closed（finding 1）
        if any(e.get("event") == "reserved" and e.get("reservation_id") == rid for e in events):
            print("FAIL_CLOSED:duplicate_reservation_id"); return EXIT_FAIL_CLOSED
        # 同一 (scope, target_round) 重复活跃预约 → fail-closed（finding 2）
        if consumes in SCOPE_PRODUCT:
            if (consumes, target_round) in active_targets(events):
                print("FAIL_CLOSED:double_target"); return EXIT_FAIL_CLOSED

        # BLOCK：总量硬上限（单调）——task-envelope 是与 total 正交的独立维度（plan §6.3），
        # 不消费也不受 total 硬上限约束，故跳过本检查（避免 task-envelope 的并行 reserve
        # 意外挤占其它角色的 total 预算空间）。
        if consumes != "task-envelope":
            total_used = total_reservations_issued(events)
            total_ceil = ceiling(state, "total")
            if total_used >= total_ceil:
                _emit_decision(active, "BLOCK:total_spawn_cap", "total", total_used, total_ceil)
                print("BLOCK:total_spawn_cap"); return EXIT_BLOCK_TOTAL
        else:
            total_used = total_reservations_issued(events)   # 仅用于下方 ledger 记录，不参与裁决

        # BLOCK：按 scope 预算
        if consumes == "task-envelope":
            usage = scope_reservations_issued(events, "task-envelope")
            ceil = ceiling(state, "task-envelope")   # 未配置任务档 → FailClosed("task_envelope_not_configured")
            if usage >= ceil:
                _emit_decision(active, "BLOCK:task_envelope_exhausted", "task-envelope", usage, ceil)
                print("BLOCK:task_envelope_exhausted"); return EXIT_BLOCK_TASK_ENVELOPE
        elif consumes != "none":
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
        if consumes == "outer" and mode_switch_required(state, target_round or 0):
            # MODE_SWITCH 是非 scope 决策 → scope/usage/ceiling 一律 null（v7）
            _emit_decision(active, "MODE_SWITCH_REQUIRED", None, None, None)
            print("MODE_SWITCH_REQUIRED"); return EXIT_MODE_SWITCH

        # PROCEED
        counts_before = {s: effective_usage(active, events, s)
                         for s in ("outer", "blind", "ultraverge")} | {"total": total_used}
        ceilings = {s: ceiling(state, s) for s in ("outer", "blind", "ultraverge", "total")}
        if _task_envelope_configured(state):
            # task-envelope 只在任务档已配置时才作为**额外可选键**出现（A8：未配置时
            # ledger 记录与改造前完全一致，见 SCOPE_KEYS 处注释）。
            counts_before["task-envelope"] = scope_reservations_issued(events, "task-envelope")
            ceilings["task-envelope"] = ceiling(state, "task-envelope")

        # D10: Atomic Spawn pair — for non-task-envelope roles with configured
        # task-envelope, create companion reservation atomically. Task companion
        # is checked first; no half-pair may be committed.
        call_id = None
        companion_rid = None
        te_blocked = False
        if consumes != "task-envelope" and _task_envelope_configured(state):
            call_id = _mint_call_id()
            companion_rid = _new_id()
            # Check task-envelope budget first
            te_usage = scope_reservations_issued(events, "task-envelope")
            te_ceil = ceiling(state, "task-envelope")
            if te_usage >= te_ceil:
                _emit_decision(active, "BLOCK:task_envelope_exhausted",
                               "task-envelope", te_usage, te_ceil)
                print("BLOCK:task_envelope_exhausted")
                return EXIT_BLOCK_TASK_ENVELOPE
            # Recompute counts_before with the companion's perspective
            te_counts = dict(counts_before)
            te_counts["task-envelope"] = te_usage
            te_ceilings = dict(ceilings)
            te_ceilings["task-envelope"] = te_ceil
            # Atomic: append companion first, then role (both or neither)
            append_ledger(active, {
                "event": "reserved", "reservation_id": companion_rid, "ts": _now(),
                "target_round": None, "target_role": "task-envelope",
                "consumes": "task-envelope",
                "counts_before": te_counts,
                "ceilings": te_ceilings,
                "call_id": call_id,
                "companion_reservation_id": rid,  # points to the role reservation
                "extension_id": (active_extension(state, "task-envelope")
                                 or {}).get("extension_id"),
                "tier": args.tier,
            })

        append_ledger(active, {
            "event": "reserved", "reservation_id": rid, "ts": _now(),
            "target_round": target_round, "target_role": role, "consumes": consumes,
            "counts_before": counts_before,
            "ceilings": ceilings,
            "extension_id": (active_extension(state, consumes) or {}).get("extension_id")
                             if consumes != "none" else None,
            "tier": args.tier,
            **({"call_id": call_id, "companion_reservation_id": companion_rid}
               if call_id else {}),
        })
        print(f"PROCEED:{rid}")
        return EXIT_PROCEED


def _find_companion(events: list[dict], rid: str) -> str | None:
    """D10: Find the companion reservation_id for a given reservation.

    Forward lookup: reads companion_reservation_id from the event itself
    (used by the atomic-pair path in cmd_reserve where both sides carry it).
    Reverse lookup: scans reserved events for one whose
    companion_reservation_id == rid (used by the pre-reserved adapter path
    where the role event has no forward reference).

    Returns the companion's reservation_id or None if no companion exists.
    """
    # Forward lookup (atomic pair path)
    for ev in events:
        if ev.get("event") == "reserved" and ev.get("reservation_id") == rid:
            fwd = ev.get("companion_reservation_id")
            if fwd is not None:
                return fwd
    # Reverse lookup (pre-reserved adapter path)
    for ev in events:
        if (ev.get("event") == "reserved"
                and ev.get("companion_reservation_id") == rid):
            return ev.get("reservation_id")
    return None


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
        if args.result in ("cancelled", "failed"):
            # failed 也记 pre_execution（默认 false）：区分"启动前失败/CLI 参数错误"
            # （从未真正调用模型）与"真实模型调用后失败"，供 attempted_dispatch/
            # model_invocation 双计数使用（plan Phase1 step4）。
            ev["pre_execution"] = bool(args.pre_execution)
        if args.reason:
            ev["reason"] = args.reason
        append_ledger(active, ev)

        # D10: Idempotent companion settle — settling a role reservation
        # also settles its task-envelope companion with the same result.
        comp_rid = _find_companion(events, args.reservation_id)
        if comp_rid and res.get(comp_rid, {}).get("status") == "reserved":
            comp_ev = {"event": ev["event"],
                       "reservation_id": comp_rid, "ts": _now()}
            if args.result == "succeeded":
                comp_ev["instance_id"] = args.instance_id
            if args.result in ("cancelled", "failed"):
                comp_ev["pre_execution"] = bool(args.pre_execution)
            if args.reason:
                comp_ev["reason"] = args.reason
            append_ledger(active, comp_ev)

        print("OK")
        return EXIT_PROCEED


def cmd_companion_for(args) -> int:
    """Create or update a task-envelope companion for an existing role reservation.

    Used by the adapter when --reserved-reservation-id is provided (pre-reserved):
    the gate's atomic pair in cmd_reserve was skipped, so this command retroactively
    creates the companion and links it to the role reservation.
    """
    active = Path(args.active_dir)
    if not active.is_dir():
        print("FAIL_CLOSED:no_active_dir"); return EXIT_FAIL_CLOSED
    with Lock(active):
        events = read_ledger(active)
        state = read_state(active)
        validate_integrity(active, events, state)

        if not _task_envelope_configured(state):
            print("FAIL_CLOSED:task_envelope_not_configured"); return EXIT_FAIL_CLOSED

        role_rid = args.companion_for
        # Role reservation must exist
        role_ev = None
        for ev in events:
            if ev.get("event") == "reserved" and ev.get("reservation_id") == role_rid:
                role_ev = ev
                break
        if role_ev is None:
            print("FAIL_CLOSED:role_reservation_not_found"); return EXIT_FAIL_CLOSED

        # Role must not already have a companion (check both forward and reverse)
        if role_ev.get("companion_reservation_id") is not None:
            print("FAIL_CLOSED:companion_already_exists"); return EXIT_FAIL_CLOSED
        # Reverse lookup: check if any reserved event already references this role
        for ev in events:
            if (ev.get("event") == "reserved"
                    and ev.get("companion_reservation_id") == role_rid):
                print("FAIL_CLOSED:companion_already_exists"); return EXIT_FAIL_CLOSED

        # Check task-envelope budget
        te_usage = scope_reservations_issued(events, "task-envelope")
        te_ceil = ceiling(state, "task-envelope")
        if te_usage >= te_ceil:
            _emit_decision(active, "BLOCK:task_envelope_exhausted",
                           "task-envelope", te_usage, te_ceil)
            print("BLOCK:task_envelope_exhausted"); return EXIT_BLOCK_TASK_ENVELOPE

        call_id = _mint_call_id()
        companion_rid = _new_id()
        total_used = total_reservations_issued(events)
        te_counts = {s: effective_usage(active, events, s)
                     for s in ("outer", "blind", "ultraverge")}
        te_counts["total"] = total_used
        te_counts["task-envelope"] = te_usage
        te_ceilings = {s: ceiling(state, s)
                       for s in ("outer", "blind", "ultraverge", "total")}
        te_ceilings["task-envelope"] = te_ceil

        # Append companion reservation (append-only: never mutate existing events)
        append_ledger(active, {
            "event": "reserved", "reservation_id": companion_rid, "ts": _now(),
            "target_round": None, "target_role": "task-envelope",
            "consumes": "task-envelope",
            "counts_before": te_counts, "ceilings": te_ceilings,
            "call_id": call_id,
            "companion_reservation_id": role_rid,
            "extension_id": (active_extension(state, "task-envelope")
                             or {}).get("extension_id"),
            "tier": args.tier,
        })

        print(f"PROCEED:{companion_rid}")
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


# ---- 治理计划 preflight（plan r2 D7：机器输入 + 窄数值经验门）------------------
#
# preflight 在既有 code-heaviness 启发式之上扩展治理计划模式：plan 内出现
# `converge.governance-change/v1` fenced JSON 块（或显式 --governance）时，读取
# **唯一**该 schema 块（重复块/畸形 JSON/未知字段/缺字段一律 fail closed），经
# calibration locator 解析唯一 `converge.calibration-report/v1` 报告，复算其
# canonical hash、比对 corpus_digest 与事件 high-water 新鲜度，然后仅对
# numeric_changes 中 comparison ∈ {outer, blind} 的数值默认/阈值/停止条件做窄比较：
# proposal 低于"仍有推进证据的已观测用量"且无 counterevidence_refs、无绑定用户
# 取舍事件 → BLOCK:empirical_conflict（退出码 15）。角色权限/一般机制
# （kind=mechanism 或 comparison=null）不被数值门裁决，交给 Reviewer 语义审查。
#
# **一次性 bootstrap 例外**：本实现落地前编译器尚不存在，唯一合法的自举形态是
# 计划文件内嵌的 calibration-report 块（locator 指向 plan 自身，如
# `plan.md::json-fence[schema=converge.calibration-report/v1,id=...]`）。此后的
# 治理变更必须提供由 `distill_antipatterns.py --calibration` 生成的报告，不再
# 接受内嵌自举。此注释即该例外在代码侧的说明（plan §Machine Preflight Input）。
#
# canonical 字节规则与 locator 语法的规范定义见 refs/state-schema.md §版本化
# fenced JSON 机器块契约（与 distill_antipatterns.py 的实现保持字面一致）。

GOVERNANCE_SCHEMA = "converge.governance-change/v1"
CAL_REPORT_SCHEMA = "converge.calibration-report/v1"

_LOCATOR_RE = re.compile(
    r"^(?P<file>[^/\\:\s]+)::json-fence\[schema=(?P<schema>[^,\]\s]+),"
    r"id=(?P<id>[^\]\s]+)\]$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_GIT_REF_RE = re.compile(r"^git:[0-9a-f]{40}$")
_ARCHIVE_REF_RE = re.compile(r"^archive:\S+$")

# Archive Contract 根 allowlist（refs/state-schema.md §Evidence 与路径）：locator 的
# root-file 必须是其中允许的普通文件名。
_ROOT_ALLOWLIST = {
    "INDEX.md", "manifest.json", "plan.md", "contract.md", "attempts.md",
    "retrospective.md", "design-review.md", "_orchestrator-state.md",
    "gate-ledger.jsonl", "_budget-state.json",
}
_ROOT_ALLOWLIST_RE = re.compile(r"^round-[1-9][0-9]*\.md$")

_GOV_KEYS = {"schema", "change_id", "numeric_changes", "archaeology_refs",
             "calibration", "counterevidence_refs", "user_message_events"}
_GOV_CHANGE_KEYS = {"control", "kind", "released", "old", "proposed",
                    "comparison", "basis"}
_GOV_NUMERIC_KINDS = {"default", "threshold", "stopping_condition"}
_GOV_KINDS = _GOV_NUMERIC_KINDS | {"mechanism"}
_GOV_COMPARISONS = {"outer", "blind", None}
_GOV_CAL_KEYS = {"path", "sha256", "corpus_digest", "freshness"}
_GOV_FRESHNESS_KEYS = {"repository_head", "source_archive_revision",
                       "source_event_high_watermark"}
_GOV_UME_REQUIRED = {"quality_goal", "execution_authorization"}
_GOV_UME_ALLOWED = _GOV_UME_REQUIRED | {"tradeoff_decision"}


def _canonical_json_bytes(obj) -> bytes:
    """canonical JSON 字节：UTF-8、sorted keys、compact separators、恰好一个 LF。"""
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _strict_json_object(raw: bytes) -> dict:
    """严格 JSON：拒绝重复 key、NaN/Infinity、非 dict 顶层。失败抛 ValueError。"""
    def _no_dupes(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError(f"duplicate_key:{k}")
            out[k] = v
        return out

    def _bad_const(x):
        raise ValueError(f"invalid_constant:{x}")

    obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_dupes,
                     parse_constant=_bad_const)
    if not isinstance(obj, dict):
        raise ValueError("top_level_not_object")
    return obj


def _extract_json_fences(data: bytes) -> tuple[list[bytes], list[bytes]]:
    """扫描 ```json fenced 块。返回 (payloads, crlf_payloads)。

    只识别 opening line 为三个反引号紧接 json 的 fence；payload 含 CR（CRLF 污染）
    的块单独列出——字节级一致校验必须 fail closed，不得静默归一化换行。
    未闭合 fence 的残余行不计入（与历史 code-heaviness 计数行为一致）。
    """
    payloads: list[bytes] = []
    crlf: list[bytes] = []
    in_fence = False
    buf: list[bytes] = []
    for line in data.split(b"\n"):
        stripped = line.rstrip(b"\r").rstrip()
        if not in_fence:
            if stripped == b"```json":
                in_fence = True
                buf = []
            continue
        if stripped == b"```":
            payload = b"\n".join(buf)
            (crlf if b"\r" in payload else payloads).append(payload)
            in_fence = False
            buf = []
            continue
        buf.append(line)
    return payloads, crlf


def _resolve_report_locator(plan: Path, locator: str) -> dict:
    """解析 `<root-file>::json-fence[schema=<schema>,id=<id>]`，返回报告 payload。

    恰好一个精确匹配是硬性要求：文件缺失或 id 缺席 → path-not-found；多于一个
    精确匹配 → duplicate-target；请求的 id 只在别的 schema 下出现 → wrong-schema。
    """
    m = _LOCATOR_RE.match(locator)
    if not m:
        raise FailClosed(f"locator_syntax:{locator}")
    fname = m.group("file")
    if fname not in _ROOT_ALLOWLIST and not _ROOT_ALLOWLIST_RE.match(fname):
        raise FailClosed(f"locator_file_not_allowed:{fname}")
    target = plan.parent / fname
    if not target.is_file():
        raise FailClosed(f"path-not-found:{fname}")
    payloads, crlf = _extract_json_fences(target.read_bytes())
    if crlf:
        raise FailClosed(f"crlf_payload:{fname}")
    exact: list[dict] = []
    id_elsewhere = False
    for raw in payloads:
        try:
            obj = _strict_json_object(raw)
        except (ValueError, UnicodeDecodeError):
            raise FailClosed(f"malformed_json_fence:{fname}")
        if obj.get("schema") == m.group("schema") and obj.get("id") == m.group("id"):
            exact.append(obj)
        elif obj.get("id") == m.group("id"):
            id_elsewhere = True
    if len(exact) > 1:
        raise FailClosed(f"duplicate-target:{m.group('id')}")
    if not exact:
        if id_elsewhere:
            raise FailClosed(f"wrong-schema:{m.group('id')}")
        raise FailClosed(f"path-not-found:{m.group('id')}")
    return exact[0]


def _validate_governance_change(gov: dict, plan: Path) -> None:
    """converge.governance-change/v1 严格 schema：未知字段/缺字段/错类型 fail closed。"""
    unknown = sorted(set(gov) - _GOV_KEYS)
    if unknown:
        raise FailClosed(f"gov_unknown_field:{unknown[0]}")
    missing = sorted(_GOV_KEYS - set(gov))
    if missing:
        raise FailClosed(f"gov_missing_field:{missing[0]}")
    if not _nonempty_str(gov["change_id"]):
        raise FailClosed("gov_field:change_id")

    changes = gov["numeric_changes"]
    if not isinstance(changes, list):
        raise FailClosed("gov_field:numeric_changes")
    for ch in changes:
        if not isinstance(ch, dict):
            raise FailClosed("gov_field:numeric_changes.entry")
        extra = sorted(set(ch) - _GOV_CHANGE_KEYS)
        if extra:
            raise FailClosed(f"gov_unknown_field:numeric_changes.{extra[0]}")
        miss = sorted(_GOV_CHANGE_KEYS - set(ch))
        if miss:
            raise FailClosed(f"gov_missing_field:numeric_changes.{miss[0]}")
        if not _nonempty_str(ch["control"]):
            raise FailClosed("gov_field:numeric_changes.control")
        if ch["kind"] not in _GOV_KINDS:
            raise FailClosed(f"gov_field:numeric_changes.kind:{ch['kind']}")
        if ch["comparison"] not in _GOV_COMPARISONS:
            raise FailClosed("gov_field:numeric_changes.comparison")
        if not _nonempty_str(ch["basis"]):
            raise FailClosed("gov_field:numeric_changes.basis")
        for f in ("released", "old", "proposed"):
            v = ch[f]
            if ch["kind"] == "mechanism":
                if v is not None and not _int(v):
                    raise FailClosed(f"gov_field:numeric_changes.{f}")
            elif not _int(v):
                raise FailClosed(f"gov_field:numeric_changes.{f}")

    refs = gov["archaeology_refs"]
    if not isinstance(refs, list) or not refs:
        raise FailClosed("gov_field:archaeology_refs")
    for r in refs:
        if not isinstance(r, str) or not (_GIT_REF_RE.match(r)
                                          or _ARCHIVE_REF_RE.match(r)):
            raise FailClosed(f"gov_field:archaeology_refs:{r}")
    # git 对象存在性：plan 位于 git 工作树内时用 cat-file 核验；不在工作树内
    # （单元测试临时目录）退化为格式校验——存在性断言只在可核验环境中生效。
    root = plan.parent
    while root != root.parent and not (root / ".git").exists():
        root = root.parent
    if (root / ".git").exists():
        for r in refs:
            if _GIT_REF_RE.match(r):
                sha = r[len("git:"):]
                try:
                    p = subprocess.run(
                        ["git", "-C", str(root), "cat-file", "-e", sha],
                        capture_output=True, timeout=10)
                except (OSError, subprocess.SubprocessError):
                    raise FailClosed(f"archaeology_ref_unverifiable:{r}")
                if p.returncode != 0:
                    raise FailClosed(f"archaeology_ref_missing:{r}")

    if not isinstance(gov["counterevidence_refs"], list) or any(
            not isinstance(r, str) for r in gov["counterevidence_refs"]):
        raise FailClosed("gov_field:counterevidence_refs")

    cal = gov["calibration"]
    if not isinstance(cal, dict):
        raise FailClosed("gov_field:calibration")
    unknown = sorted(set(cal) - _GOV_CAL_KEYS)
    if unknown:
        raise FailClosed(f"gov_unknown_field:calibration.{unknown[0]}")
    missing = sorted(_GOV_CAL_KEYS - set(cal))
    if missing:
        raise FailClosed(f"gov_missing_field:calibration.{missing[0]}")
    if not _nonempty_str(cal["path"]):
        raise FailClosed("gov_field:calibration.path")
    for f in ("sha256", "corpus_digest"):
        if not (isinstance(cal[f], str) and _HEX64_RE.match(cal[f])):
            raise FailClosed(f"gov_field:calibration.{f}")
    fresh = cal["freshness"]
    if not isinstance(fresh, dict):
        raise FailClosed("gov_field:calibration.freshness")
    unknown = sorted(set(fresh) - _GOV_FRESHNESS_KEYS)
    if unknown:
        raise FailClosed(f"gov_unknown_field:freshness.{unknown[0]}")
    missing = sorted(_GOV_FRESHNESS_KEYS - set(fresh))
    if missing:
        raise FailClosed(f"gov_missing_field:freshness.{missing[0]}")
    head = fresh["repository_head"]
    if not (isinstance(head, str)
            and (re.fullmatch(r"[0-9a-f]{40}", head) or head == "unavailable")):
        raise FailClosed("gov_field:freshness.repository_head")
    if not _nonempty_str(fresh["source_archive_revision"]):
        raise FailClosed("gov_field:freshness.source_archive_revision")
    hw = fresh["source_event_high_watermark"]
    if isinstance(hw, bool) or not isinstance(hw, int) or hw < 0:
        raise FailClosed("gov_field:freshness.source_event_high_watermark")

    ume = gov["user_message_events"]
    if not isinstance(ume, dict):
        raise FailClosed("gov_field:user_message_events")
    unknown = sorted(set(ume) - _GOV_UME_ALLOWED)
    if unknown:
        raise FailClosed(f"gov_unknown_field:user_message_events.{unknown[0]}")
    missing = sorted(_GOV_UME_REQUIRED - set(ume))
    if missing:
        raise FailClosed(f"gov_missing_field:user_message_events.{missing[0]}")
    for k, v in ume.items():
        if not (isinstance(v, str) and _UUID_RE.match(v)):
            raise FailClosed(f"gov_field:user_message_events.{k}")


def _resolve_and_check_report(gov: dict, plan: Path) -> dict:
    """locator 解析 + canonical hash 复算 + 新鲜度（corpus digest / high-water）。"""
    cal = gov["calibration"]
    report = _resolve_report_locator(plan, cal["path"])
    if report.get("schema") != CAL_REPORT_SCHEMA:
        raise FailClosed("calibration_report_schema")
    actual = hashlib.sha256(_canonical_json_bytes(report)).hexdigest()
    if actual != cal["sha256"]:
        raise FailClosed("calibration_hash_mismatch")
    if not isinstance(report.get("corpus"), list) or any(
            not isinstance(e, dict) or not _nonempty_str(e.get("ref"))
            or not _nonempty_str(e.get("quantitative_status"))
            for e in report["corpus"]):
        raise FailClosed("calibration_report_corpus")
    if report.get("corpus_digest") != cal["corpus_digest"]:
        raise FailClosed("stale_calibration:corpus_digest")
    if report.get("freshness") != cal["freshness"]:
        raise FailClosed("stale_calibration:freshness")
    agg = report.get("quantitative_aggregates")
    if not isinstance(agg, dict):
        raise FailClosed("calibration_report_aggregates")
    eligible = sum(1 for e in report["corpus"]
                   if e.get("quantitative_status") == "eligible")
    if agg.get("eligible_samples") != eligible:
        raise FailClosed("calibration_report_inconsistent:eligible_samples")
    return report


def _numeric_empirical_conflicts(gov: dict, report: dict) -> list[str]:
    """窄数值经验门：仅 comparison ∈ {outer, blind} 的数值默认/阈值/停止条件。

    proposal 低于"仍有推进证据的已观测用量"（eligible 样本中该 axis
    productive=true 的最大 usage）且无 counterevidence_refs、无绑定用户取舍事件
    → 冲突。角色权限/一般机制（mechanism / comparison=null）不进本门。
    """
    dischargers = bool(gov["counterevidence_refs"]) or \
        "tradeoff_decision" in gov["user_message_events"]
    conflicts: list[str] = []
    for ch in gov["numeric_changes"]:
        if ch["kind"] not in _GOV_NUMERIC_KINDS:
            continue
        axis = ch["comparison"]
        if axis not in ("outer", "blind"):
            continue
        usages = []
        for e in report["corpus"]:
            if e.get("quantitative_status") != "eligible":
                continue
            prod = e.get("productive", {})
            usage = e.get("usage", {})
            if isinstance(prod, dict) and prod.get(axis) is True:
                u = usage.get(axis) if isinstance(usage, dict) else None
                if _int(u):
                    usages.append(u)
        if not usages:
            continue   # 无 eligible 可比样本 → 不做数值裁决
        observed = max(usages)
        if ch["proposed"] < observed and not dischargers:
            conflicts.append(f"{ch['control']}:proposed={ch['proposed']}"
                             f"<observed_productive_usage={observed}")
    return conflicts


def cmd_preflight_governance(args, plan: Path, gov: dict) -> int:
    _validate_governance_change(gov, plan)
    report = _resolve_and_check_report(gov, plan)
    conflicts = _numeric_empirical_conflicts(gov, report)
    if conflicts:
        for c in conflicts:
            print(f"BLOCK:empirical_conflict:{c}")
        return EXIT_BLOCK_EMPIRICAL
    print("PREFLIGHT_OK:governance-change")
    return EXIT_PROCEED


def cmd_preflight(args) -> int:
    plan = Path(args.plan)
    if not plan.is_file():
        print("FAIL_CLOSED:no_plan"); return EXIT_FAIL_CLOSED
    raw = plan.read_bytes()
    blocks = loc = 0
    in_block = False
    for line in raw.decode("utf-8", "replace").splitlines():
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

    # 治理计划模式（plan r2 D7）：plan 内出现唯一 governance-change 机器块，
    # 或显式 --governance 时启用。散文/表格永不进入机器裁决。
    payloads, crlf = _extract_json_fences(raw)
    parsed: list[dict] = []
    malformed = 0
    for p in payloads:
        try:
            parsed.append(_strict_json_object(p))
        except (ValueError, UnicodeDecodeError):
            malformed += 1
    gov_blocks = [o for o in parsed if o.get("schema") == GOVERNANCE_SCHEMA]
    if not args.governance and not gov_blocks:
        # 纯 legacy 模式：行为与改造前一致。唯一例外：CRLF 污染的 fence 里带有
        # converge 机器块标记——无法安全解析其 schema，按 fail-closed 处理而非
        # 静默放过（字节级一致契约，plan r2 设计审查 highlight）。
        if any(b"converge." in p for p in crlf):
            print("FAIL_CLOSED:crlf_payload"); return EXIT_FAIL_CLOSED
        return EXIT_PROCEED
    if crlf:
        print("FAIL_CLOSED:crlf_payload"); return EXIT_FAIL_CLOSED
    if malformed:
        print("FAIL_CLOSED:malformed_json_fence"); return EXIT_FAIL_CLOSED
    if not gov_blocks:
        print("FAIL_CLOSED:no_governance_block"); return EXIT_FAIL_CLOSED
    if len(gov_blocks) > 1:
        print("FAIL_CLOSED:duplicate_governance_block"); return EXIT_FAIL_CLOSED
    return cmd_preflight_governance(args, plan, gov_blocks[0])


def cmd_summary(args) -> int:
    """可验证汇总（plan Phase1 step4）：从 ledger + state 重新计算，不依赖任何缓存——
    与本文件其它命令一样每次调用都是幂等的全量重算（条款2）。区分 attempted_dispatch
    （含启动前失败/CLI 错误）与 model_invocation（真实模型调用），避免"预算数字"语义漂移。"""
    active = Path(args.active_dir)
    if not active.is_dir():
        print("FAIL_CLOSED:no_active_dir"); return EXIT_FAIL_CLOSED
    state = read_state(active)
    events = read_ledger(active)
    validate_integrity(active, events, state)
    scopes: dict[str, dict] = {}
    for s in ("outer", "blind", "ultraverge"):
        scopes[s] = {
            "realized": realized(active, s),
            "pending": pending(active, events, s),
            "effective_usage": effective_usage(active, events, s),
            "ceiling": ceiling(state, s),
            "attempted_dispatch": attempted_dispatch(events, s),
            "model_invocation": model_invocation(events, s),
        }
    if _task_envelope_configured(state):
        scopes["task-envelope"] = {
            "usage": scope_reservations_issued(events, "task-envelope"),
            "ceiling": ceiling(state, "task-envelope"),
            "hard_cap": _task_envelope_hard_cap(state),
            "attempted_dispatch": attempted_dispatch(events, "task-envelope"),
            "model_invocation": model_invocation(events, "task-envelope"),
        }
    out = {
        "total_reservations_issued": total_reservations_issued(events),
        "total_ceiling": ceiling(state, "total"),
        "attempted_dispatch": attempted_dispatch(events, None),
        "model_invocation": model_invocation(events, None),  # legacy key preserved
        "scopes": scopes,
    }
    # D10: accounting_coverage — instrumented_complete / partial / unavailable.
    # Legacy ledger events without call_id force coverage=unavailable.
    reserved_events = [e for e in events if e.get("event") == "reserved"]
    if not reserved_events:
        coverage = "unavailable"
    else:
        with_call_id = sum(1 for e in reserved_events if e.get("call_id"))
        if with_call_id == len(reserved_events):
            coverage = "instrumented_complete"
        elif with_call_id > 0:
            coverage = "partial"
        else:
            coverage = "unavailable"
    out["accounting_coverage"] = coverage
    out["accounting_scope"] = "instrumented_dispatch_only"
    # Numeric model_invocations only allowed for instrumented_complete
    if coverage == "instrumented_complete":
        out["model_invocations"] = model_invocation(events, None)
    else:
        out["model_invocations"] = "unavailable"
    print(json.dumps(out, ensure_ascii=False, sort_keys=True))
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
    # 确保 state 存在且使用 version 2 默认值（plan D3）。
    # 若无 state → 创建 stock standard state；已有 state → 校验（幂等）。
    initialize_state(active)
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


def cmd_init(args) -> int:
    """CLI 入口：host-independent 状态初始化器（plan D3）。

    三条入口（手动 orchestrator / ocsr_spawn_adapter config-init / converge_loop run）
    共享同一初始化契约。
    """
    active = Path(args.active_dir)
    config = {}
    for attr in ("max_outer_loops", "max_blind_rechecks", "max_inner_loops",
                 "ultraverge_min_reviewers"):
        val = getattr(args, attr.replace("-", "_"), None)
        if val is not None:
            config[attr] = val
    # task_tier / task_envelope_initial / task_envelope_cap passthrough
    for attr in ("task_tier", "task_envelope_initial", "task_envelope_cap"):
        val = getattr(args, attr, None)
        if val is not None:
            config[attr] = val
    # mode=None 表示省略（继承已有 state 的模式）；CLI 未指定时 default=None
    mode = getattr(args, "mode", None)
    force = getattr(args, "force", False)
    try:
        state = initialize_state(active, mode=mode, config=config, force=force)
        # Phase 5b: initialization disclosure
        if _task_envelope_configured(state):
            ceilings = {s: ceiling(state, s)
                        for s in ("outer", "blind", "ultraverge", "total")}
            te_initial = _task_envelope_initial(state)
            te_cap = _task_envelope_hard_cap(state)
            print(f"[init] local ceilings: {ceilings}")
            print(f"[init] task-envelope: initial={te_initial}, cap={te_cap}")
            print("[init] quality_path_guaranteed: false")
        print("OK")
        return EXIT_PROCEED
    except FailClosed as e:
        print(f"FAIL_CLOSED:{e.reason}")
        return EXIT_FAIL_CLOSED


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
    r.add_argument("--companion-for",
                   help="Create a task-envelope companion for an existing role reservation.")
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
    pf.add_argument("--governance", action="store_true",
                    help="强制治理计划模式：要求唯一 converge.governance-change/v1 "
                         "机器块（缺块 fail closed）；省略时检测到该块亦自动启用")
    pf.set_defaults(func=cmd_preflight)

    sm = sub.add_parser("summary")     # 可验证预算汇总（attempted_dispatch/model_invocation 双计数）
    sm.add_argument("--active-dir", required=True)
    sm.set_defaults(func=cmd_summary)

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

    ini = sub.add_parser("init")        # host-independent 状态初始化器（plan D3）
    ini.add_argument("--active-dir", required=True)
    ini.add_argument("--mode", choices=["standard", "ultraverge"], default=None)
    ini.add_argument("--max-outer-loops", type=int)
    ini.add_argument("--max-blind-rechecks", type=int)
    ini.add_argument("--max-inner-loops", type=int)
    ini.add_argument("--ultraverge-min-reviewers", type=int)
    ini.add_argument("--task-tier", choices=list(TASK_TIERS.keys()))
    ini.add_argument("--task-envelope-initial", type=int)
    ini.add_argument("--task-envelope-cap", type=int)
    ini.add_argument("--force", action="store_true")
    ini.set_defaults(func=cmd_init)

    hk = sub.add_parser("hook-pretooluse")   # PreToolUse hook 入口（读 stdin）
    hk.set_defaults(func=cmd_hook_pretooluse)

    args = p.parse_args()
    return _run(args.func, args)


if __name__ == "__main__":
    sys.exit(main())
