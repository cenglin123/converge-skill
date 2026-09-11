#!/usr/bin/env python3
"""orchest —— converge 执行层编排：六条原子命令消除 orchestrator 的机械操作错误。

设计依据（converged plan，本脚本是其 §命令契约 1-6 的逐条落地）：
docs/plans/active/20260815-converge-exec-orchestration.md（KB vault）。
分层原则：评审/协商层（spawn 判断、prompt 设计、verdict 裁决）保持 LLM 自由；
本脚本只承接机械层——零转录、零顺序记忆、零"固定动作靠不遗忘"。

命令总览（均支持 --dry-run，只打印序列不落盘）：
  reserve-round    gate reserve → archive begin-invocation → SCOPE_PRODUCT 骨架
                   （全部在宿主 Spawn 之前；begin 失败不 settle，带内救济 =
                    --resume-reservation <rid> 同 rid 重试）
  register-round   宿主成功返回后：complete-invocation(succeeded) → settle(succeeded)
                   → 骨架 frontmatter 回填（幂等：terminal 已落盘时走早退分支）
  cancel-round     宿主失败/取消后：recover-invocation → settle → 骨架删除/标注
                   （幂等；open-无-started 的 reservation 拒绝闭合、零写入）
  record-verdict   产物 frontmatter 契约字段校验/补齐（数据源写死：该 round 的
                   invocation-terminal 读回）+ gate ingest-verdict + 复核
  finish           固定顺序 0→8：拒已归档 → verdict 交叉核对 → round 连续 →
                   全 settle → 孤儿显性化 → 异常恢复（只补 started-无-terminal）→
                   终局 decision → stamp → prompt 归位+根目录 allowlist → archive
                   → 归档后 check。任一步失败即停并输出已完成步骤清单（可安全重跑）
  checkpoint-paths git diff-tree 生成 implementation_paths YAML 块（零手抄）

历史错误 → 防呆机制映射（2026-08-14/15 三个会话的 8 类执行错误，全部发生在
执行层、零个发生在评审层——这是本脚本存在的理由）：
  #1 executor repair 轮 round-N.md 忘写（触发 round_gap FAIL_CLOSED）
       → reserve-round 骨架与 reservation 同命令落盘
  #2 backfill 时 round-N.md 未先写 → complete-invocation output_path=None
       → register-round --output 从 invocation-started 的 role+round 推导，
         产物存在且非空为前置校验
  #3 把从未 spawn 的 reservation 写成 succeeded（ledger-status-conflict）
       → begin 失败不 settle（无 started 的 settle 必产生 ledger 孤儿形态）；
         finish 步骤 3 只补"有 started 无 terminal"缺口，从不无中生有
  #4 重建 events 目录时误删 terminal-decision，被迫重 record+stamp
       → finish 固定顺序 + 步骤 4 幂等读回（decision 已 record 即复用 event id）
  #5 归档后手动把文件塞进 done/（post-archive mutation，破坏 tree-closure）
       → finish 步骤 0 拒绝已归档（done/<slug> 已存在）目录
  #6 plan checkpoint 手抄 UUID 漏字符（机械门拦截后逐字符对比才定位）
       → checkpoint-paths 从 git 输出生成路径清单；invocation_id 全程经
         evidence/events 读回，LLM 不经手
  #7 每次 archive 前手动删 prompt 文件（靠记忆，漏步）
       → finish 步骤 6 机械归位 *prompt*.md（移入 active 同级 tmp/）
  #8 验证脚本硬编码中文文件名导致误报（"未动"实为在）
       → finish 步骤 6 从文件系统枚举根目录实际条目与 archive_contract.model
         的根 allowlist（ROOT_FIXED + round 模式，import 不复制）求差；
         步骤 1 从目录枚举核对连续编号，不信任 LLM 计数

时间戳语义（Archive Contract v1 第一句对齐）：begin-invocation 在 reserve-round
内、宿主派发前执行——started_at 是宿主派发时刻的**上界**而非精确调用时刻
（两者间隔 LLM 编排延迟，宿主原生路径秒~分钟级；精度如实降档披露）。

provenance 默认（宿主原生 Spawn 无 per-invocation tool_response 绑定时的
strictest legal choice，同 ocsr_spawn_adapter）：evidence_level=configured /
resolution_source=cli_argument / resolution_reason_code=backend-does-not-expose。

退出码：0 成功（含幂等完成）；1 orchest 参数/状态校验错误；10-14/20/21-22/30
透传 budget_gate reserve 裁决；3/4 透传 archive_convergence CLI 错误。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import budget_gate  # noqa: E402
from archive_contract import capture, model  # noqa: E402
from archive_contract.model import canonical_round  # noqa: E402

GATE_SCRIPT = SCRIPTS_DIR / "budget_gate.py"
ARCHIVE_SCRIPT = SCRIPTS_DIR / "archive_convergence.py"

EXIT_OK = 0
EXIT_ERROR = 1

# terminal_status → gate settle result（§3 步骤 a 的单源定义；timeout 归并 failed
# 是 gate 三档的既定语义：timeout 是模型确曾被调用过的真实 post-invocation 失败）
TERMINAL_TO_GATE = {
    "succeeded": "succeeded",
    "failed": "failed",
    "cancelled": "cancelled",
    "timeout": "failed",
}
# cancel-round --reason-code → archive recover-invocation --status
REASON_TO_RECOVER = {
    "cancelled-by-host": "cancelled",
    "backend-error": "failed",
    "timeout": "timeout",
}
# gate settle 事件名 → recover (status, reason)（cancel-round §3c 反向；finish 步骤 3
# 的 orphan-recovery 按此显式元组解包。spawn_failed→failed 与 TERMINAL_TO_GATE 的
# timeout→failed 归并同向：两者都是模型侧失败，恢复终态记 failed/backend-error）
GATE_TO_RECOVER = {
    "spawn_failed": ("failed", "backend-error"),
    "cancelled": ("cancelled", "cancelled-by-host"),
}

# 骨架正文模板：单一常量。cancel-round 的机械占位判据②用它做逐字比较——不采用
# 创建时记录内容 hash 方案（那需要新增状态存储，违反非目标 3）。
SKELETON_BODY = (
    "# (skeleton)\n"
    "\n"
    "## Reviewer 完整输出\n"
    "\n"
    "(pending)\n"
    "\n"
    "## Orchestrator 处理记录\n"
    "\n"
    "(pending)\n"
)

TERMINAL_SETTLE_EVENTS = ("spawn_succeeded", "spawn_failed", "cancelled")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _run(script: Path, args: list[str]) -> tuple[int, str, str]:
    env = {**os.environ, "PYTHONUTF8": "1"}
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _gate(*args: str) -> tuple[int, str, str]:
    # D3/O7：orchest 编排路径的 reserve/settle 注入 --orchest-managed 来源声明。
    # ingest-verdict 不注入（其直调是 guide:248 既有规范指令，不设声明门）。
    cmd = list(args)
    if cmd and cmd[0] in ("reserve", "settle") and "--orchest-managed" not in cmd:
        cmd.append("--orchest-managed")
    return _run(GATE_SCRIPT, cmd)


def _archive_cli(*args: str) -> tuple[int, str, str]:
    return _run(ARCHIVE_SCRIPT, list(args))


# ---- 事件/ledger 读回（库调用，只读）------------------------------------------

def _started_for_rid(events: list[dict], rid: str) -> list[dict]:
    return [e for e in events
            if e.get("event_type") == "invocation-started"
            and e.get("invocation_kind") == "spawn"
            and e.get("reservation_id") == rid]


def _terminal_for_started(events: list[dict], started: dict) -> dict | None:
    return next((e for e in events
                 if e.get("event_type") == "invocation-terminal"
                 and e.get("started_event_id") == started.get("event_id")), None)


def _ledger_status(active: Path) -> dict[str, dict]:
    return budget_gate._reservation_status(budget_gate.read_ledger(active))


def _settle_row(active: Path, rid: str) -> dict | None:
    for ev in budget_gate.read_ledger(active):
        if ev.get("reservation_id") == rid and ev.get("event") in TERMINAL_SETTLE_EVENTS:
            return ev
    return None


def _consumes(role: str) -> str | None:
    return budget_gate.ROLE_CONSUMES.get(role)


def _settle_te_companion_for_continue(active: Path, invocation_id: str,
                                       result: str, instance_id: str = "") -> None:
    """D10: Settle task-envelope companion for a Continue invocation.

    The companion has call_id = invocation_id. Settles it if found and still
    reserved. Idempotent: if already settled, silently skips.
    """
    gate_events = budget_gate.read_ledger(active)
    res = budget_gate._reservation_status(gate_events)
    for ev in gate_events:
        if (ev.get("event") == "reserved"
                and ev.get("target_role") == "task-envelope"
                and ev.get("call_id") == invocation_id):
            comp_rid = ev["reservation_id"]
            if res.get(comp_rid, {}).get("status") == "reserved":
                settle_args = ["settle", "--active-dir", str(active),
                               "--reservation-id", comp_rid, "--result", result]
                if result == "succeeded" and instance_id:
                    settle_args += ["--instance-id", instance_id]
                rc, out, err_ = _gate(*settle_args)
                if rc != 0 and "duplicate_settlement" not in out:
                    _err(f"[te-companion] settle failed for {comp_rid}: {out or err_}")
            break


def _product_path(active: Path, role: str, round_no: int | None) -> Path | None:
    """按 role 的 consumes 经 budget_gate.SCOPE_PRODUCT 推导产物路径（运行时
    import 该常量，不复制枚举——单一事实源）。consumes=none / 无 round → None。"""
    c = _consumes(role)
    tmpl = budget_gate.SCOPE_PRODUCT.get(c) if c else None
    if tmpl is None or round_no is None:
        return None
    return active / tmpl.format(n=round_no)


# ---- frontmatter（极简 key: value 行；骨架与回填共用）--------------------------

def _fm_split(text: str) -> tuple[list[str], str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[4:end].split("\n"), text[end + 5:]
    return [], text


def _fm_join(fm_lines: list[str], body: str) -> str:
    return "---\n" + "\n".join(fm_lines) + "\n---\n" + body


def _fm_get(fm_lines: list[str], key: str) -> str | None:
    prefix = f"{key}:"
    for ln in fm_lines:
        if ln.startswith(prefix):
            return ln[len(prefix):].strip()
    return None


def _fm_set(fm_lines: list[str], key: str, value: str) -> None:
    prefix = f"{key}:"
    for i, ln in enumerate(fm_lines):
        if ln.startswith(prefix):
            fm_lines[i] = f"{key}: {value}"
            return
    fm_lines.append(f"{key}: {value}")


def _read_fm(path: Path) -> tuple[list[str], str]:
    return _fm_split(path.read_text(encoding="utf-8"))


def _write_fm(path: Path, fm_lines: list[str], body: str) -> None:
    path.write_text(_fm_join(fm_lines, body), encoding="utf-8", newline="\n")


def _skeleton_text(round_no: int, rid: str, invocation_id: str) -> str:
    fm = [
        f"round: {round_no}",
        "reviewer_backend: pending",
        f"generated_at: {_now()}",
        f"invocation_id: {invocation_id}",
        f"reservation_id: {rid}",
    ]
    return _fm_join(fm, SKELETON_BODY)


def _backfill_skeleton(active: Path, started: dict, terminal: dict,
                       backend_override: str | None) -> str | None:
    """成功 terminal → 骨架 frontmatter 回填（§2a/§2e 统一实现）。
    reviewer_backend = --backend > terminal.backend > unknown（不经推断合成）；
    reviewer_instance_id = terminal.instance_id。无骨架文件（consumes=none）→ 跳过。"""
    path = _product_path(active, started.get("role", ""), started.get("round"))
    if path is None or not path.is_file():
        return None
    fm, body = _read_fm(path)
    backend = backend_override or terminal.get("backend") or "unknown"
    _fm_set(fm, "reviewer_backend", backend)
    _fm_set(fm, "reviewer_instance_id", terminal.get("instance_id") or "unknown")
    _write_fm(path, fm, body)
    return path.name


def _cancel_skeleton(active: Path, started: dict, rid: str) -> str:
    """cancel-round 步骤 e：机械占位判据（三条件缺一不可，判定写死）。
    rid 匹配 + ① frontmatter 无 reviewer_instance_id + ② 正文与骨架模板逐字相等
    → 删除；否则（已有实质内容，或骨架属其他 reservation）→ 追加 status: cancelled
    标注，不删（幂等：已标注则不重复标注）。"""
    path = _product_path(active, started.get("role", ""), started.get("round"))
    if path is None or not path.is_file():
        return "无骨架（幂等，已删或从未创建）"
    fm, body = _read_fm(path)
    if (_fm_get(fm, "reservation_id") == rid
            and _fm_get(fm, "reviewer_instance_id") is None
            and body == SKELETON_BODY):
        path.unlink()
        return f"已删除机械占位骨架 {path.name}"
    if _fm_get(fm, "status") == "cancelled":
        return f"{path.name} 已标注 status: cancelled（幂等跳过）"
    _fm_set(fm, "status", "cancelled")
    _write_fm(path, fm, body)
    return f"{path.name} 已标注 status: cancelled（保留历史，不删实质内容）"


# ==============================================================================
# §1 reserve-round
# ==============================================================================

# max_inner_loops 由 active state 的有效配置决定（plan D3），
# 不再硬编码。orchest.py 在 _reserve_continue 中读取 validated state。


def _started_of(events: list[dict], invocation_id: str) -> dict | None:
    return next((e for e in events
                 if e.get("event_type") == "invocation-started"
                 and e.get("invocation_id") == invocation_id), None)


def _reserve_continue(args, active: Path, prompt: Path) -> int:
    """Inner Loop Continue（方案甲，Archive Contract v1 原生）：发射
    begin-invocation kind=continue。

    契约规定 continue 不携带 reservation（capture 侧自动派生 parent_instance_id
    并校验父链）——故本路径**无 gate reserve**：Continue 计数由 events 承载
    （同父链 kind=continue 的 started 事件数），上限由 active state 的有效
    max_inner_loops 配置决定；
    不占 spawn cap、不推进 outer 计数（gate ledger 零感知 = 计数天然独立）。
    """
    if args.resume_reservation:
        _err("--continue-of 与 --resume-reservation 互斥（continue 无 reservation）")
        return EXIT_ERROR
    if not prompt.exists():
        _err(f"--prompt-file 须已存在（begin-invocation 记录其 hash/metadata）: {prompt}")
        return EXIT_ERROR
    events = capture.read_events(active)
    started_list = _started_for_rid(events, args.continue_of)
    if not started_list:
        _err(f"--continue-of 失败: 无此 rid 的 spawn invocation-started: {args.continue_of}")
        return EXIT_ERROR
    if len(started_list) > 1:
        _err(f"--continue-of 失败: 该 rid 匹配到多个 invocation-started: {args.continue_of}")
        return EXIT_ERROR
    parent = started_list[0]
    terminal = _terminal_for_started(events, parent)
    if (terminal is None or terminal.get("terminal_status") != "succeeded"
            or not terminal.get("instance_id")):
        status_now = terminal.get("terminal_status") if terminal else "无 terminal"
        _err(f"--continue-of 失败: 父轮须为已 succeeded 的 spawn（terminal 记录 instance_id）；"
             f"当前: {status_now}")
        return EXIT_ERROR
    role = parent.get("role", "")
    if args.role and args.role != role:
        _err(f"--continue-of 失败: role-conflict（父轮 {role} ≠ --role {args.role}；"
             f"continue 复用父轮 role）")
        return EXIT_ERROR
    round_no = canonical_round(parent.get("round"))
    if args.round is not None and canonical_round(args.round) != round_no:
        _err(f"--continue-of 失败: round-conflict（父轮 {round_no} ≠ --round {args.round}；"
             f"continue 复用父轮 round）")
        return EXIT_ERROR
    prior = [e for e in events
             if e.get("event_type") == "invocation-started"
             and e.get("invocation_kind") == "continue"
             and e.get("parent_event_id") == parent.get("event_id")]
    # 从 validated active state 读取有效 max_inner_loops（plan D3），
    # 不使用硬编码默认值——stock=1、active override 可调。
    gate_events = budget_gate.read_ledger(active)
    state = budget_gate.read_state(active)
    budget_gate.validate_integrity(active, gate_events, state)
    effective_max = budget_gate.cfg(state, "max_inner_loops")
    if len(prior) >= effective_max:
        _err(f"--continue-of 失败: 已达 max_inner_loops={effective_max}"
             f"（同父链 continue 上限；超限 → 该轮失败 → 下一 outer loop）")
        return EXIT_ERROR
    attempt = (parent.get("attempt") or 1) + len(prior) + 1
    parent_instance = terminal.get("instance_id")

    if args.dry_run:
        print("[dry-run] reserve-round(continue) 序列:")
        print(f"  a. 无 gate reserve（契约: continue 不携带 reservation；计数入 "
              f"max_inner_loops={effective_max}，当前 {len(prior)}/{effective_max}）")
        print(f"  b. archive begin-invocation kind=continue role={role} phase={args.phase} "
              f"attempt={attempt} round={round_no} parent_event={parent.get('event_id')}")
        print("  c. 无产物骨架（round 产物随父轮已存在）")
        print(f"  d. 输出 invocation_id；宿主 Continue 同实例后 register-round "
              f"--invocation-id <iid> --instance-id {parent_instance}")
        return EXIT_OK

    begin_args = ["begin-invocation", str(active), "--kind", "continue",
                  "--role", role, "--phase", args.phase,
                  "--attempt", str(attempt),
                  "--parent-event-id", parent.get("event_id", ""),
                  "--prompt", str(prompt.resolve()),
                  "--evidence-mode", getattr(args, "evidence_mode", "metadata-only")]
    if args.requested_provider:
        begin_args += ["--requested-provider", args.requested_provider]
    if args.requested_model:
        begin_args += ["--requested-model", args.requested_model]
    if round_no is not None:
        begin_args += ["--round", str(round_no)]
    rc, out, err_ = _archive_cli(*begin_args)
    if rc != 0 or not out:
        _err(f"begin-invocation(continue) 失败（rc={rc}）: {out or err_}")
        return rc if rc != 0 else EXIT_ERROR
    try:
        invocation_id = json.loads(out)["invocation_id"]
    except (json.JSONDecodeError, KeyError):
        _err(f"begin-invocation(continue) 输出无法解析: {out[:300]}")
        return EXIT_ERROR

    # D10: Continue single-reservation exception — task-envelope companion
    # links directly to the existing invocation-started event via call_id.
    # No Spawn reservation is fabricated.
    gate_events = budget_gate.read_ledger(active)
    state = budget_gate.read_state(active)
    if budget_gate._task_envelope_configured(state):
        te_rid = budget_gate._new_id()
        te_counts = {s: budget_gate.effective_usage(active, gate_events, s)
                     for s in ("outer", "blind", "ultraverge")}
        te_counts["total"] = budget_gate.total_reservations_issued(gate_events)
        te_counts["task-envelope"] = budget_gate.scope_reservations_issued(
            gate_events, "task-envelope")
        te_ceilings = {s: budget_gate.ceiling(state, s)
                       for s in ("outer", "blind", "ultraverge", "total")}
        te_ceilings["task-envelope"] = budget_gate.ceiling(state, "task-envelope")
        budget_gate.append_ledger(active, {
            "event": "reserved", "reservation_id": te_rid, "ts": _now(),
            "target_round": None, "target_role": "task-envelope",
            "consumes": "task-envelope",
            "counts_before": te_counts, "ceilings": te_ceilings,
            "call_id": invocation_id,  # links to invocation-started event
            "extension_id": (budget_gate.active_extension(state, "task-envelope")
                             or {}).get("extension_id"),
            "tier": "auditable-only",
        })
        te_note = f"task-envelope companion: {te_rid} (call_id={invocation_id})"
    else:
        te_note = "task-envelope not configured, no companion"

    print(f"invocation_id: {invocation_id}")
    print(f"continue-of: {args.continue_of}（第 {len(prior) + 1}/{effective_max} 次，"
          f"role={role} round={round_no}，无 reservation）")
    print(f"task-envelope: {te_note}")
    print(f"next: 宿主 Continue 同实例（{parent_instance}）→ register-round "
          f"--invocation-id {invocation_id} --instance-id {parent_instance}")
    return EXIT_OK


def _register_continue(args, active: Path) -> int:
    """continue 轮登记：complete-invocation(succeeded)。无 settle、无骨架回填
    （无 reservation；round 产物随父轮，verdict 由 record-verdict 单独落盘）。"""
    events = capture.read_events(active)
    started = _started_of(events, args.invocation_id)
    if started is None:
        _err(f"无此 invocation-started: {args.invocation_id}")
        return EXIT_ERROR
    if started.get("invocation_kind") != "continue":
        _err(f"--invocation-id 仅用于 continue 轮（该 invocation 为 "
             f"{started.get('invocation_kind')}；spawn 轮用 --reservation-id）")
        return EXIT_ERROR
    parent_instance = started.get("parent_instance_id")
    if args.instance_id != parent_instance:
        _err(f"continue 登记失败: instance-conflict（Continue 续命同实例: 期望 "
             f"{parent_instance}, 传入 {args.instance_id}）")
        return EXIT_ERROR
    if _terminal_for_started(events, started) is not None:
        print(f"[register-round] 幂等完成: invocation {args.invocation_id} 已有 terminal")
        return EXIT_OK
    output = None
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = active / output
    else:
        output = _product_path(active, started.get("role", ""), started.get("round"))
    if output is None or not (output.is_file() and output.stat().st_size > 0):
        _err("continue 登记失败: 产物无法解析（--output 或 role+round 推导均未命中非空产物）")
        return EXIT_ERROR

    if args.dry_run:
        print("[dry-run] register-round(continue) 序列:")
        print(f"  a. 已读取 invocation-started（continue, invocation_id={args.invocation_id}）")
        print(f"  b. --output 解析: {output.name}")
        print(f"  c. complete-invocation status=succeeded instance-id={args.instance_id}（无 settle）")
        return EXIT_OK

    cargs = ["complete-invocation", str(active), args.invocation_id,
             "--status", "succeeded",
             "--instance-id", args.instance_id,
             "--evidence-level", args.evidence_level,
             "--resolution-source", args.resolution_source,
             "--resolution-reason-code", args.resolution_reason_code,
             "--output", str(output.resolve()),
             "--evidence-mode", getattr(args, "evidence_mode", "metadata-only")]
    if args.backend:
        cargs += ["--backend", args.backend]
    if args.backend_version:
        cargs += ["--backend-version", args.backend_version]
    rc, out, err_ = _archive_cli(*cargs)
    if rc != 0:
        _err(f"complete-invocation(continue) 失败: {out or err_}")
        return rc if rc != 0 else EXIT_ERROR

    # D10: Settle task-envelope companion for Continue (call_id = invocation_id)
    _settle_te_companion_for_continue(active, args.invocation_id, "succeeded",
                                       instance_id=args.instance_id)

    print(f"[register-round] OK invocation_id={args.invocation_id} "
          f"instance_id={args.instance_id} output={output.name}（continue: settle companion）")
    return EXIT_OK


def _cancel_continue(args, active: Path) -> int:
    """continue 轮取消：recover-invocation(cancelled)；无 settle（无 reservation）。"""
    events = capture.read_events(active)
    started = _started_of(events, args.invocation_id)
    if started is None:
        _err(f"无此 invocation-started: {args.invocation_id}")
        return EXIT_ERROR
    if started.get("invocation_kind") != "continue":
        _err(f"--invocation-id 仅用于 continue 轮（spawn 轮用 --reservation-id）")
        return EXIT_ERROR
    if _terminal_for_started(events, started) is not None:
        print(f"[cancel-round] 幂等完成: invocation {args.invocation_id} 已有 terminal")
        return EXIT_OK
    if args.dry_run:
        print("[dry-run] cancel-round(continue) 序列:")
        print(f"  a. recover-invocation status=cancelled reason={args.reason_code}"
             f" instance-id={started.get('parent_instance_id')}")
        return EXIT_OK
    rargs = ["recover-invocation", str(active), args.invocation_id,
             "--status", "cancelled", "--failure-reason-code", args.reason_code,
             "--instance-id", started.get("parent_instance_id") or ""]
    if args.detail:
        rargs += ["--failure-detail", args.detail]
    rc, out, err_ = _archive_cli(*rargs)
    if rc != 0:
        _err(f"recover-invocation(continue) 失败: {out or err_}")
        return rc if rc != 0 else EXIT_ERROR

    # D10: Settle task-envelope companion for Continue cancellation
    gate_result = "cancelled" if args.reason_code == "cancelled-by-host" else "failed"
    _settle_te_companion_for_continue(active, args.invocation_id, gate_result)

    print(f"[cancel-round] OK invocation_id={args.invocation_id} "
          f"status=cancelled（continue: settle companion {gate_result}）")
    return EXIT_OK


def cmd_reserve_round(args) -> int:
    active = Path(args.active_dir)
    prompt = Path(args.prompt_file)
    role = args.role
    if getattr(args, "continue_of", None):
        return _reserve_continue(args, active, prompt)
    if not role:
        _err("--role 必填（或改用 --continue-of <父rid>，由父轮派生）")
        return EXIT_ERROR
    consumes = _consumes(role)
    round_no = canonical_round(args.round)

    if consumes in budget_gate.SCOPE_PRODUCT and args.round is None:
        _err(f"consuming 角色({role})必填 --round")
        return EXIT_ERROR
    if not prompt.exists():
        _err(f"--prompt-file 必须已存在（begin-invocation 记录其 hash/metadata）: {prompt}")
        return EXIT_ERROR

    if args.dry_run:
        print("[dry-run] reserve-round 序列:")
        if not args.resume_reservation:
            print(f"  a. budget_gate reserve --role {role} --tier {args.tier}"
                  + (f" --target-round {args.round}" if args.round is not None else ""))
        else:
            print(f"  a. 跳过（--resume-reservation {args.resume_reservation}，rid 已 reserve）")
        print(f"  b. archive begin-invocation kind=spawn role={role} phase={args.phase} "
              f"attempt={args.attempt} round={round_no} prompt={prompt} "
              f"evidence-mode={getattr(args, 'evidence_mode', 'metadata-only')}")
        tmpl = budget_gate.SCOPE_PRODUCT.get(consumes) if consumes else None
        if tmpl and round_no is not None:
            print(f"  c. 骨架（不存在时创建）: {tmpl.format(n=round_no)}")
        else:
            print("  c. consumes=none → 不创建产物骨架（attempt 由 executor agent 自记 attempts.md）")
        print("  d. 输出 reservation_id + invocation_id；随后由 LLM 调宿主 Spawn")
        return EXIT_OK

    rid: str | None = None
    if args.resume_reservation:
        rid = args.resume_reservation
        # 前置校验（库调用只读，任一不满足 → 报错退出）
        status = _ledger_status(active)
        if rid not in status:
            _err(f"--resume-reservation 失败: gate ledger 无此 rid（rid 错误）: {rid}")
            return EXIT_ERROR
        st = status[rid]
        events = capture.read_events(active)
        if _started_for_rid(events, rid):
            _err(f"--resume-reservation 失败: 该 rid 已有 invocation-started——改走 "
                 f"register-round / cancel-round")
            return EXIT_ERROR
        if st["status"] != "reserved":
            _err(f"--resume-reservation 失败: 该 rid 已 settle（{st['status']}）且无 started——"
                 f"历史/手工 ledger 孤儿形态，走 finish 步骤 7 手工披露路径；orchest 命令面不产生此形态")
            return EXIT_ERROR
        if st["role"] != role:
            _err(f"--resume-reservation 失败: ledger-role-conflict（reserve 行 target_role="
                 f"{st['role']} ≠ 所传 --role {role}）")
            return EXIT_ERROR
        if round_no != st["target_round"]:
            _err(f"--resume-reservation 失败: ledger-round-conflict（reserve 行 target_round="
                 f"{st['target_round']} ≠ 所传 --round {round_no}）")
            return EXIT_ERROR
    else:
        gate_args = ["reserve", "--active-dir", str(active), "--role", role,
                     "--tier", args.tier]
        if args.round is not None:
            gate_args += ["--target-round", str(args.round)]
        rc, out, err_ = _gate(*gate_args)
        if rc != 0 or not out.startswith("PROCEED:"):
            print(out or err_)  # BLOCK/DENY/FAIL_CLOSED 原文透出（decision 已由 gate 落 ledger）
            return rc if rc != 0 else EXIT_ERROR
        rid = out[len("PROCEED:"):]

    # b. begin-invocation（宿主调用前——started_at 是派发时刻上界）
    begin_args = ["begin-invocation", str(active), "--kind", "spawn",
                  "--role", role, "--phase", args.phase,
                  "--attempt", str(args.attempt),
                  "--reservation-id", rid,
                  "--prompt", str(prompt.resolve()),
                  "--evidence-mode", getattr(args, "evidence_mode", "metadata-only")]
    if args.requested_provider:
        begin_args += ["--requested-provider", args.requested_provider]
    if args.requested_model:
        begin_args += ["--requested-model", args.requested_model]
    if round_no is not None:
        begin_args += ["--round", str(round_no)]
    rc, out, err_ = _archive_cli(*begin_args)
    if rc != 0 or not out:
        _err(f"begin-invocation 失败（rc={rc}）: {out or err_}")
        _err(f"reservation_id={rid} 保持 open（不 settle：无 started 的 settle 必被 "
             f"validate_ledger 以 ledger-invocation-orphan 拦截）；修复失败原因后以 "
             f"--resume-reservation {rid} 重跑本命令")
        return rc if rc != 0 else EXIT_ERROR
    try:
        invocation_id = json.loads(out)["invocation_id"]
    except (json.JSONDecodeError, KeyError):
        _err(f"begin-invocation 返回无法解析: {out[:300]}")
        return EXIT_ERROR

    # c. 骨架（与 reservation 同命令落盘；已存在 → 幂等跳过，不覆盖）
    tmpl = budget_gate.SCOPE_PRODUCT.get(consumes) if consumes else None
    skeleton_note = "(consumes=none，无产物骨架)"
    if tmpl is not None and round_no is not None:
        skel = active / tmpl.format(n=round_no)
        if skel.exists():
            skeleton_note = f"{skel.name}（已存在，幂等跳过）"
        else:
            skel.write_text(_skeleton_text(round_no, rid, invocation_id),
                            encoding="utf-8", newline="\n")
            skeleton_note = skel.name

    # d. 输出
    print(f"reservation_id: {rid}")
    print(f"invocation_id: {invocation_id}")
    print(f"skeleton: {skeleton_note}")
    print("next: 调用宿主 Spawn → 成功 register-round / 失败·取消 cancel-round")
    return EXIT_OK


# ==============================================================================
# §2 register-round
# ==============================================================================

def cmd_register_round(args) -> int:
    active = Path(args.active_dir)
    if bool(args.invocation_id) == bool(args.reservation_id):
        _err("--reservation-id 与 --invocation-id 恰好传一个（spawn 轮用前者，continue 轮用后者）")
        return EXIT_ERROR
    if args.invocation_id:
        return _register_continue(args, active)
    rid = args.reservation_id
    events = capture.read_events(active)
    started_list = _started_for_rid(events, rid)
    if not started_list:
        _err(f"无该 reservation 的 invocation-started: {rid}（应先跑 reserve-round，不代跑）")
        return EXIT_ERROR
    if len(started_list) > 1:
        _err(f"该 reservation 匹配到多个 invocation-started（invocation-reservation-duplicate）: {rid}")
        return EXIT_ERROR
    started = started_list[0]

    if args.dry_run:
        print("[dry-run] register-round 序列:")
        print(f"  a. 已读回 invocation-started（invocation_id={started['invocation_id']}）")
        path = _product_path(active, started.get("role", ""), started.get("round"))
        if args.output:
            out_note = args.output
        elif path is not None:
            out_note = str(path)
        else:
            out_note = "（consumes=none → 必须显式 --output）"
        print(f"  b. --output 解析: {out_note}（存在且非空为前置校验）")
        print(f"  c. complete-invocation status=succeeded instance-id={args.instance_id} "
              f"evidence-level={args.evidence_level} resolution-source={args.resolution_source} "
              f"resolution-reason-code={args.resolution_reason_code}")
        print("  d. budget_gate settle --result succeeded")
        print("  e. 骨架 frontmatter 回填（reviewer_backend / reviewer_instance_id）")
        return EXIT_OK

    terminal = _terminal_for_started(events, started)
    if terminal is not None:
        # 分支闭合：terminal 已落盘（重跑或崩溃窗口），契约写死
        status = _ledger_status(active)
        st = status.get(rid, {})
        settled = st.get("status") in TERMINAL_SETTLE_EVENTS
        if settled:
            settle_note = f"gate 已 settle（result={st['status']}）"
        else:
            # 崩溃窗口：terminal 落盘后、settle 前中断 → 补 settle（不重复写 terminal）
            result = TERMINAL_TO_GATE[terminal["terminal_status"]]
            sargs = ["settle", "--active-dir", str(active),
                     "--reservation-id", rid, "--result", result]
            if result == "succeeded":
                sargs += ["--instance-id", terminal.get("instance_id") or ""]
            rc, out, err_ = _gate(*sargs)
            if rc != 0 and "duplicate_settlement" not in out:
                _err(f"补 settle 失败: {out or err_}")
                return rc if rc != 0 else EXIT_ERROR
            settle_note = f"补 settle（result={result}，terminal 已存在不重复写）"
        if terminal["terminal_status"] == "succeeded":
            name = _backfill_skeleton(active, started, terminal, args.backend)
            backfill_note = f"骨架已回填: {name}" if name else "无骨架文件，跳过回填"
        else:
            backfill_note = "无成功产物回填（terminal status 非 succeeded）"
        print(f"[register-round] 幂等完成: terminal={terminal['terminal_status']}; "
              f"{settle_note}; {backfill_note}")
        return EXIT_OK

    # b. --output 解析（role/round 取自 invocation-started，命令签名不含 --role/--round）
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = active / output
    else:
        output = _product_path(active, started.get("role", ""), started.get("round"))
        if output is None:
            _err("consumes=none 角色必须显式传 --output（典型: attempts.md 或被修复产物路径）")
            return EXIT_ERROR
    if not (output.is_file() and output.stat().st_size > 0):
        _err(f"--output 文件须存在且非空: {output}")
        return EXIT_ERROR

    # c. complete-invocation（provenance 默认 configured/cli_argument/backend-does-not-expose）
    cargs = ["complete-invocation", str(active), started["invocation_id"],
             "--status", "succeeded",
             "--instance-id", args.instance_id,
             "--evidence-level", args.evidence_level,
             "--resolution-source", args.resolution_source,
             "--resolution-reason-code", args.resolution_reason_code,
             "--output", str(output.resolve()),
             "--evidence-mode", getattr(args, "evidence_mode", "metadata-only")]
    if args.backend:
        cargs += ["--backend", args.backend]
    if args.backend_version:
        cargs += ["--backend-version", args.backend_version]
    rc, out, err_ = _archive_cli(*cargs)
    if rc != 0:
        _err(f"complete-invocation 失败（invocation_id={started['invocation_id']}，不 settle）: "
             f"{out or err_}；重跑本命令（幂等）")
        return rc if rc != 0 else EXIT_ERROR

    # d. settle succeeded
    rc, out, err_ = _gate("settle", "--active-dir", str(active),
                          "--reservation-id", rid,
                          "--result", "succeeded",
                          "--instance-id", args.instance_id)
    if rc != 0 and "duplicate_settlement" not in out:
        _err(f"settle 失败: {out or err_}")
        return rc if rc != 0 else EXIT_ERROR

    # e. 骨架回填（数据源：刚落盘的 terminal）
    events2 = capture.read_events(active)
    terminal2 = _terminal_for_started(events2, started)
    if terminal2 is not None:
        name = _backfill_skeleton(active, started, terminal2, args.backend)
        if name:
            print(f"[register-round] 骨架回填: {name}")
    print(f"[register-round] OK invocation_id={started['invocation_id']} "
          f"reservation_id={rid} instance_id={args.instance_id} output={output.name}")
    return EXIT_OK


# ==============================================================================
# §3 cancel-round
# ==============================================================================

def cmd_cancel_round(args) -> int:
    active = Path(args.active_dir)
    if bool(args.invocation_id) == bool(args.reservation_id):
        _err("--reservation-id 与 --invocation-id 恰好传一个（spawn 轮用前者，continue 轮用后者）")
        return EXIT_ERROR
    if args.invocation_id:
        return _cancel_continue(args, active)
    rid = args.reservation_id
    recover_status = REASON_TO_RECOVER[args.reason_code]
    gate_result = "cancelled" if recover_status == "cancelled" else "failed"

    events = capture.read_events(active)
    started_list = _started_for_rid(events, rid)
    if not started_list:
        # 无 started → 报错退出、零写入；按 gate ledger 形态写死提示
        status = _ledger_status(active)
        st = status.get(rid)
        if st is None:
            _err(f"cancel-round 拒绝: gate ledger 无此 rid（rid 错误）: {rid}")
        elif st["status"] == "reserved":
            _err(f"cancel-round 拒绝（零写入）: rid={rid} 仍 open 且无 invocation-started"
                 f"（reserve-round 步骤 b 失败遗留）。带内闭合唯一路径 = "
                 f"reserve-round --resume-reservation {rid} 重试 begin；对无 started 的 "
                 f"reservation settle 即制造 ledger 孤儿形态（validate_ledger 必拦且无 "
                 f"pre_execution 豁免）")
        else:
            _err(f"cancel-round 拒绝: rid={rid} 已 settle（{st['status']}）而 events 无 "
                 f"invocation-started——历史/adapter 遗留孤儿形态，走 finish 步骤 7 手工"
                 f"披露路径（archive --declare-orphan-reservation）；orchest 命令面不产生此形态")
        return EXIT_ERROR
    started = started_list[0]

    if args.dry_run:
        print("[dry-run] cancel-round 序列:")
        print(f"  a. 已读回 invocation-started（invocation_id={started['invocation_id']}）")
        print(f"  b. recover-invocation status={recover_status} failure-reason-code={args.reason_code}"
              + (f" detail={args.detail}" if args.detail else ""))
        print(f"  c. budget_gate settle --result {gate_result} "
              f"pre_execution={'true' if args.pre_execution else 'false'}")
        print("  e. 骨架处理（机械占位判据：删除或标注 status: cancelled）")
        return EXIT_OK

    terminal = _terminal_for_started(events, started)
    if terminal is not None:
        # 分支闭合（与 register-round 步骤 a 对称）
        status = _ledger_status(active)
        st = status.get(rid, {})
        settled = st.get("status") in TERMINAL_SETTLE_EVENTS
        if not settled:
            result = TERMINAL_TO_GATE[terminal["terminal_status"]]
            sargs = ["settle", "--active-dir", str(active),
                     "--reservation-id", rid, "--result", result]
            if result == "succeeded":
                sargs += ["--instance-id", terminal.get("instance_id") or ""]
            rc, out, err_ = _gate(*sargs)
            if rc != 0 and "duplicate_settlement" not in out:
                _err(f"补 settle 失败: {out or err_}")
                return rc if rc != 0 else EXIT_ERROR
            settle_note = f"补 settle（result={result}，崩溃窗口闭合）"
        else:
            settle_note = f"gate 已 settle（result={st['status']}）"
        if terminal["terminal_status"] == "succeeded":
            # 成功轮产物不得被误判占位或误标 cancelled（收尾归 register-round 回填）
            print(f"[cancel-round] 幂等完成: terminal=succeeded; {settle_note}; "
                  f"成功产物不走骨架删除/标注")
            return EXIT_OK
        note = _cancel_skeleton(active, started, rid)
        print(f"[cancel-round] 幂等完成: terminal={terminal['terminal_status']}; "
              f"{settle_note}; 骨架: {note}")
        return EXIT_OK

    # b. recover-invocation（status 按 reason-code 映射）
    rargs = ["recover-invocation", str(active), started["invocation_id"],
             "--status", recover_status,
             "--failure-reason-code", args.reason_code]
    if args.detail:
        rargs += ["--failure-detail", args.detail]
    if args.instance_id:
        rargs += ["--instance-id", args.instance_id]
    rc, out, err_ = _archive_cli(*rargs)
    if rc != 0:
        _err(f"recover-invocation 失败: {out or err_}")
        return rc if rc != 0 else EXIT_ERROR

    # c. settle（映射照搬 ocsr_spawn_adapter：cancelled→cancelled / failed→failed /
    #    timeout→failed——gate 无 timeout 档；pre_execution 由 --pre-execution 显式传入）
    sargs = ["settle", "--active-dir", str(active),
             "--reservation-id", rid, "--result", gate_result,
             "--reason", args.reason_code]
    if args.instance_id and gate_result == "succeeded":
        sargs += ["--instance-id", args.instance_id]
    if args.pre_execution:
        sargs += ["--pre-execution"]
    rc, out, err_ = _gate(*sargs)
    if rc != 0 and "duplicate_settlement" not in out:
        _err(f"settle 失败: {out or err_}")
        return rc if rc != 0 else EXIT_ERROR

    # e. 骨架处理
    note = _cancel_skeleton(active, started, rid)
    print(f"[cancel-round] OK reservation_id={rid} recover={recover_status} "
          f"settle={gate_result}; 骨架: {note}")
    return EXIT_OK


# ==============================================================================
# §4 record-verdict
# ==============================================================================

_PRODUCT_SCOPE = (
    (model.ROUND_RE, "outer"),
    (model.BLIND_RECHECK_RE, "blind"),
    (model.UV_INIT_RE, "ultraverge"),
)


def cmd_record_verdict(args) -> int:
    active = Path(args.active_dir)
    product = args.product or f"round-{args.round}.md"
    n = args.round
    scope = next((s for rex, s in _PRODUCT_SCOPE if rex.fullmatch(product)), None)
    if scope is None:
        _err(f"无法识别产物类型: {product}（支持 round-N.md | blind-recheck-N.md | uv-init-N.md）")
        return EXIT_ERROR
    path = active / product
    if not path.is_file():
        _err(f"产物文件不存在: {path}")
        return EXIT_ERROR

    # 找该 (scope, round) 的 reservation（优先 settle=succeeded 行）
    status = _ledger_status(active)
    cands = [rid for rid, st in status.items()
             if st.get("consumes") == scope and st.get("target_round") == n]
    rid = next((r for r in cands if status[r]["status"] == "spawn_succeeded"),
               None)
    if rid is None:
        rid = next((r for r in cands if status[r]["status"] in TERMINAL_SETTLE_EVENTS), None)
    if rid is None:
        _err(f"gate ledger 无 ({scope}, round {n}) 的 reservation")
        return EXIT_ERROR
    events = capture.read_events(active)
    started_list = _started_for_rid(events, rid)
    if not started_list:
        _err(f"该 reservation 无 invocation-started: {rid}")
        return EXIT_ERROR
    terminal = _terminal_for_started(events, started_list[0])
    if terminal is None:
        _err(f"该 reservation（{rid}）无 invocation-terminal，无法回填契约字段（拒绝推断合成）")
        return EXIT_ERROR

    if args.dry_run:
        print("[dry-run] record-verdict 序列:")
        print(f"  a. 校验/补齐 {product} frontmatter（round/reviewer_backend/"
              f"reviewer_instance_id/generated_at ← terminal of {rid}；verdict={args.verdict}）")
        print(f"  b. budget_gate ingest-verdict --verdict {args.verdict} --target-round {n}"
              + (f" --severities {args.severities}" if args.severities else ""))
        print(f"  c. 复核产物 frontmatter 契约")
        return EXIT_OK

    # a. 校验/补齐（数据源写死：terminal 读回；字段缺失即报错，不做推断合成）
    fm, body = _read_fm(path)
    if _fm_get(fm, "round") is None:
        _fm_set(fm, "round", str(n))
    if _fm_get(fm, "reviewer_backend") in (None, "pending"):
        _fm_set(fm, "reviewer_backend", terminal.get("backend") or "unknown")
    if _fm_get(fm, "reviewer_instance_id") is None:
        inst = terminal.get("instance_id")
        if not inst:
            _err(f"terminal 缺 instance_id，拒绝推断合成（reservation {rid}）")
            return EXIT_ERROR
        _fm_set(fm, "reviewer_instance_id", inst)
    if _fm_get(fm, "generated_at") is None:
        _fm_set(fm, "generated_at", _now())
    _fm_set(fm, "verdict", args.verdict)  # 本仓实践扩展字段（schema §一未定义，如实标注）
    _write_fm(path, fm, body)

    # b. ingest-verdict（--target-round 取产物编号 N——盲审即盲审序号，不与主循环轮次混用）
    iargs = ["ingest-verdict", "--active-dir", str(active),
             "--target-round", str(n), "--verdict", args.verdict]
    if args.severities:
        iargs += ["--severities", args.severities]
    rc, out, err_ = _gate(*iargs)
    if rc != 0:
        _err(f"ingest-verdict 失败: {out or err_}")
        return rc if rc != 0 else EXIT_ERROR

    # c. 复核产物仍满足 frontmatter 契约
    fm2, _ = _read_fm(path)
    for field in ("round", "reviewer_backend", "reviewer_instance_id", "generated_at"):
        if _fm_get(fm2, field) is None:
            _err(f"复核失败: {product} frontmatter 缺契约字段 {field}")
            return EXIT_ERROR
    if _fm_get(fm2, "reviewer_backend") == "pending":
        _err(f"复核失败: {product} reviewer_backend 仍为 pending")
        return EXIT_ERROR
    print(f"[record-verdict] OK product={product} round={n} verdict={args.verdict} "
          f"reservation={rid}")
    return EXIT_OK


# ==============================================================================
# §5 finish
# ==============================================================================

def _finish_step1_missing(active: Path) -> list[str]:
    """顺序 scope 产物连续编号自检（读目录枚举，不信任 LLM 计数）。

    D2/O4 single-source：缺口集合复用 `budget_gate.contiguous_missing`（与
    `budget_gate.validate_integrity` 的 `round_gap:{scope}` 判定同源），此处只负责把
    缺失整数映射为产物文件名单。
    """
    missing: list[str] = []
    for scope in budget_gate.CONTIGUOUS_SCOPES:
        for n in budget_gate.contiguous_missing(active, scope):
            missing.append(budget_gate.SCOPE_PRODUCT[scope].format(n=n))
    return missing


def _finish_step6(active: Path) -> tuple[int, list[str]]:
    """归位 prompt 文件 + 根目录 allowlist 校验（从 FS 枚举，非硬编码文件名匹配）。
    返回 (moved_count, stray_entries)。"""
    moved = 0
    # Move prompt files to tmp (NOT .reopen-state.json — archive step 7 consumes it
    # to derive revision_id and parent linkage for reopened objects).
    patterns = ["*prompt*.md"]
    for pattern in patterns:
        for p in sorted(active.glob(pattern)):
            if not p.is_file():
                continue
            dest_dir = active.parent / "tmp"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / p.name
            i = 1
            while dest.exists():
                dest = dest_dir / f"{p.stem}-{i}{p.suffix}"
                i += 1
            p.replace(dest)
            moved += 1
    stray: list[str] = []
    for entry in sorted(active.iterdir()):
        if entry.is_dir():
            if entry.name == "evidence":
                continue  # 唯一合法根级目录（事件与 blob 的 owner）
            stray.append(entry.name + "/")
        elif entry.name == ".reopen-state.json":
            # Transient marker consumed by archive's _prepare() at step 7;
            # must survive step 6 so archive can read revision_id + parent.
            continue
        elif not model.is_root_allowed_name(entry.name):
            stray.append(entry.name)
    return moved, stray


# ---- Phase 4: material gate / calibration / reopened helpers ----------------

def _extract_fenced_json_blocks(text: str, schema: str, id_val: str | None = None) -> list[dict]:
    """Extract versioned fenced JSON blocks matching schema (and optional id).

    Scans ```` ```json ```` fences, parses each payload, selects by exact
    top-level ``schema`` and ``id``. Returns list of matching parsed dicts.
    """
    blocks: list[dict] = []
    i = 0
    while i < len(text):
        start = text.find("```json", i)
        if start == -1:
            break
        start += len("```json")
        if start < len(text) and text[start] == "\n":
            start += 1
        end = text.find("```", start)
        if end == -1:
            break
        payload_str = text[start:end].strip()
        i = end + 3
        try:
            obj = json.loads(payload_str)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(obj, dict):
            continue
        if obj.get("schema") != schema:
            continue
        if id_val is not None and obj.get("id") != id_val:
            continue
        blocks.append(obj)
    return blocks


def _canonical_json_bytes(obj: dict) -> bytes:
    """Canonical JSON: sorted keys, compact separators, UTF-8, one trailing LF."""
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def _find_material_block(active: Path, revision_id: str | None = None) -> tuple[dict, str] | None:
    """Find converge.material-revision/v1 block in attempts.md.

    If *revision_id* is given, looks for a block whose ``id`` equals
    ``{revision_id}-material`` (exact match, exactly one block expected).
    If *revision_id* is ``None``, returns the **last** material block found
    in document order — attempts.md is append-only so the last block is the
    most recent (latest-supersedes-all) revision.

    Returns ``(block_dict, canonical_sha256_hex)`` or ``None`` if no
    matching material block exists.
    """
    attempts = active / "attempts.md"
    if not attempts.is_file():
        return None
    text = attempts.read_text(encoding="utf-8")
    id_val = f"{revision_id}-material" if revision_id else None
    blocks = _extract_fenced_json_blocks(text, "converge.material-revision/v1", id_val)
    if not blocks:
        return None
    block = blocks[-1]
    block_bytes = _canonical_json_bytes(block)
    block_hash = hashlib.sha256(block_bytes).hexdigest()
    return block, block_hash


def _detect_revision_id(active: Path) -> str:
    """Detect current revision_id from .reopen-state.json (default r1)."""
    reopen = active / ".reopen-state.json"
    if reopen.is_file():
        try:
            data = json.loads(reopen.read_text(encoding="utf-8"))
            return data.get("revision_id", "r1")
        except (json.JSONDecodeError, OSError):
            pass
    return "r1"


def _validate_material_gate(active: Path, events: list[dict]) -> None:
    """Validate material-revision same-hash gate (D8).

    Raises FailClosed on any violation. Returns silently when no material block
    exists (backward compatible).

    The gate resolves the CURRENT material block FIRST (the latest block in
    attempts.md), validates it against the on-disk plan.md, and then qualifies
    candidates against it.  Candidates whose payloads reference a superseded
    material block or a stale plan hash are SKIPPED (non-qualifying), not
    treated as contradictions.

    Non-qualifying legacy terminals (metadata-only evidence, missing blobs,
    no review-target block, wrong schema) are **skipped** — not failed — so
    that legacy ultraverge-initial or other metadata-only authority terminals
    do not block the gate when a qualifying exact-evidence pair exists.
    """
    revision_id = _detect_revision_id(active)
    # Quick existence check: any material block at all?
    result = _find_material_block(active)
    if result is None:
        return  # no material block → backward compatible

    # ── Read on-disk plan.md ────────────────────────────────────────────────
    plan_path = active / "plan.md"
    if not plan_path.is_file():
        raise budget_gate.FailClosed("material-gate: plan.md not found")
    plan_bytes = plan_path.read_bytes()
    plan_sha256 = hashlib.sha256(plan_bytes).hexdigest()
    plan_size = len(plan_bytes)

    # ── Resolve the CURRENT material block (step 1: locator resolution) ───
    # The current block is the last material block in attempts.md (append-only).
    # Its canonical hash is the reference against which all candidates qualify.
    current_block, current_block_hash = result
    # Also validate the current block's candidate artifact against on-disk plan.
    # The field name varies: "candidate_plan" in some blocks, "candidate_artifact"
    # in others.  Check both.
    ca = current_block.get("candidate_plan") or current_block.get("candidate_artifact") or {}
    if ca.get("sha256") != plan_sha256 or ca.get("size") != plan_size:
        raise budget_gate.FailClosed(
            "material-gate: current material block candidate_plan "
            "sha256/size mismatch with on-disk plan.md")

    # ── Build candidate list (step 2: qualify by current block + plan) ────
    # Collect all successful Spawn invocations whose role is in the fresh or
    # blank-slate authority sets.  For each, attempt to load exact prompt and
    # output evidence blobs.  Skip (do NOT fail) when: evidence_mode is not
    # "exact", blob file is missing, blob is empty, CRLF detected, no
    # single converge.review-target/v1 block can be extracted, payload
    # artifact doesn't match on-disk plan, or payload material_revision
    # doesn't match the resolved (current) material block.
    fresh_roles = model.REVIEWER_AUTHORITIES["fresh"]
    blank_roles = model.REVIEWER_AUTHORITIES["blank-slate"]
    fresh_candidates: list[dict] = []
    blank_candidates: list[dict] = []
    skipped: list[str] = []  # reason summaries for error message

    for e in events:
        if (e.get("event_type") != "invocation-started"
                or e.get("invocation_kind") != "spawn"):
            continue
        role = e.get("role", "")
        if role not in fresh_roles and role not in blank_roles:
            continue
        iid = e.get("invocation_id", "")
        # Find the matching succeeded terminal
        terminal = next((t for t in events
                         if t.get("event_type") == "invocation-terminal"
                         and t.get("started_event_id") == e.get("event_id")
                         and t.get("terminal_status") == "succeeded"), None)
        if terminal is None:
            continue

        # ── Check blob existence first (auxiliary path for backward compat) ─
        prompt_path = active / "evidence" / "invocations" / iid / "prompt.bin"
        output_path = active / "evidence" / "invocations" / iid / "output.bin"
        # Also check auxiliary prompt path for backward compatibility
        if not prompt_path.is_file():
            aux_prompt = active / "evidence" / "material" / iid / "prompt.bin"
            if aux_prompt.is_file():
                prompt_path = aux_prompt
        if not prompt_path.is_file() or not output_path.is_file():
            skipped.append(f"{iid[:8]} ({role}): blob missing "
                           f"(prompt={prompt_path.is_file()}, output={output_path.is_file()})")
            continue
        prompt_bytes = prompt_path.read_bytes()
        output_bytes = output_path.read_bytes()
        if not prompt_bytes or not output_bytes:
            skipped.append(f"{iid[:8]} ({role}): empty blob")
            continue

        # ── Check evidence mode (skip if not exact, after blob check) ───
        # Note: we check blob existence first because some tests store blobs
        # at auxiliary paths even when the event says metadata-only.
        # The evidence_mode check is a secondary indicator.
        prompt_evidence = e.get("prompt_evidence", {})
        output_evidence = terminal.get("output_evidence", {})
        prompt_mode = prompt_evidence.get("evidence_mode", "metadata-only")
        output_mode = output_evidence.get("evidence_mode", "metadata-only")
        # Only skip if BOTH modes are not exact (legacy metadata-only terminals)
        # If at least one mode is exact, the candidate may qualify
        if prompt_mode != "exact" and output_mode != "exact":
            skipped.append(f"{iid[:8]} ({role}): evidence_mode "
                           f"prompt={prompt_mode}, output={output_mode}")
            continue

        # ── CRLF check ───────────────────────────────────────────────────
        prompt_text = prompt_bytes.decode("utf-8")
        output_text = output_bytes.decode("utf-8")
        if "\r" in prompt_text or "\r" in output_text:
            skipped.append(f"{iid[:8]} ({role}): CRLF detected")
            continue

        # ── Extract review-target blocks ─────────────────────────────────
        prompt_blocks = _extract_fenced_json_blocks(prompt_text, "converge.review-target/v1")
        output_blocks = _extract_fenced_json_blocks(output_text, "converge.review-target/v1")
        if len(prompt_blocks) != 1 or len(output_blocks) != 1:
            skipped.append(
                f"{iid[:8]} ({role}): expected 1 review-target block; "
                f"got prompt={len(prompt_blocks)} output={len(output_blocks)}")
            continue
        prompt_payload = _canonical_json_bytes(prompt_blocks[0])
        output_payload = _canonical_json_bytes(output_blocks[0])
        if prompt_payload != output_payload:
            skipped.append(f"{iid[:8]} ({role}): prompt/output payload mismatch")
            continue

        # ── Qualify against current material block and on-disk plan ──────
        # Payload must match the RESOLVED (latest) material block and the
        # current on-disk plan.md.  Candidates referencing superseded blocks
        # or stale plan hashes are non-qualifying (skipped, not errors).
        payload_obj = prompt_blocks[0]
        artifact = payload_obj.get("artifact", {})
        if artifact.get("sha256") != plan_sha256 or artifact.get("size") != plan_size:
            skipped.append(
                f"{iid[:8]} ({role}): stale plan hash "
                f"(payload={str(artifact.get('sha256'))[:16]}, "
                f"disk={plan_sha256[:16]})")
            continue
        mr = payload_obj.get("material_revision", {})
        if mr.get("sha256") != current_block_hash:
            skipped.append(
                f"{iid[:8]} ({role}): stale material hash "
                f"(payload={str(mr.get('sha256'))[:16]}, "
                f"resolved={current_block_hash[:16]})")
            continue
        # Also verify the locator names the same material block id
        locator = mr.get("locator", "")
        _id_marker = "id="
        _id_start = locator.find(_id_marker)
        locator_id = None
        if _id_start != -1:
            _id_end = locator.find("]", _id_start)
            if _id_end != -1:
                locator_id = locator[_id_start + len(_id_marker):_id_end]
        if locator_id and locator_id != current_block.get("id"):
            skipped.append(
                f"{iid[:8]} ({role}): locator names {locator_id!r}, "
                f"expected {current_block.get('id')!r}")
            continue

        # ── Candidate qualifies ──────────────────────────────────────────
        entry = {"started": e, "terminal": terminal, "invocation_id": iid,
                 "payload": prompt_payload}
        if role in fresh_roles:
            fresh_candidates.append(entry)
        if role in blank_roles:
            blank_candidates.append(entry)

    # ── Require at least one qualifying pair (step 3) ──────────────────────
    if not fresh_candidates or not blank_candidates:
        skip_summary = "; ".join(skipped) if skipped else "(none)"
        raise budget_gate.FailClosed(
            "material-gate: no qualifying pair found (need at least one fresh "
            "and one blank-slate with exact evidence matching current material "
            "block and on-disk plan); "
            f"skipped candidates: {skip_summary}")

    # Select the first qualifying pair with different invocation_id and instance_id
    fresh_inv: dict | None = None
    blank_inv: dict | None = None
    for fc in fresh_candidates:
        for bc in blank_candidates:
            if fc["invocation_id"] == bc["invocation_id"]:
                continue
            fi = fc["terminal"].get("instance_id")
            bi = bc["terminal"].get("instance_id")
            if fi and bi and fi == bi:
                continue
            fresh_inv = fc
            blank_inv = bc
            break
        if fresh_inv is not None:
            break

    if fresh_inv is None or blank_inv is None:
        raise budget_gate.FailClosed(
            "material-gate: qualifying candidates exist but no valid pair "
            "(different invocation_id and instance_id required)")

    # ── Validate payloads are byte-identical ────────────────────────────────
    if fresh_inv["payload"] != blank_inv["payload"]:
        raise budget_gate.FailClosed(
            "material-gate: review-target payloads differ between the two invocations")

    # Verify verdicts: both products must be 可执行 with zero blocking issues
    for inv in (fresh_inv, blank_inv):
        iid = inv["invocation_id"]
        output_path = active / "evidence" / "invocations" / iid / "output.bin"
        output_text = output_path.read_bytes().decode("utf-8")
        vm = re.search(r"verdict:\s*(\S+)", output_text)
        if vm and vm.group(1) == "阻断需修复":
            raise budget_gate.FailClosed(
                f"material-gate: invocation {iid[:8]} has blocking verdict in output")
        started = inv["started"]
        role = started.get("role", "")
        round_no = started.get("round")
        if round_no is not None:
            consumes = budget_gate.ROLE_CONSUMES.get(role)
            product_tmpl = budget_gate.SCOPE_PRODUCT.get(consumes) if consumes else None
            if product_tmpl:
                product_path = active / product_tmpl.format(n=round_no)
                if product_path.is_file():
                    fm, _ = _fm_split(product_path.read_text(encoding="utf-8"))
                    pv = _fm_get(fm, "verdict")
                    if pv == "阻断需修复":
                        raise budget_gate.FailClosed(
                            f"material-gate: product {product_path.name} has blocking verdict")


def _validate_calibration_sample(active: Path, events: list[dict]) -> None:
    """Validate converge.calibration-sample/v1 in current revision's retrospective.

    Lenient-bootstrap: if no sample exists yet, prints a warning but does not block.
    Once a sample exists, it must validate per the state-schema contract.
    """
    retro = active / "retrospective.md"
    if not retro.is_file():
        print("[finish] calibration: no retrospective.md; skipping sample validation")
        return

    revision_id = _detect_revision_id(active)
    retro_text = retro.read_text(encoding="utf-8")
    blocks = _extract_fenced_json_blocks(retro_text, "converge.calibration-sample/v1")
    current_blocks = [b for b in blocks if b.get("revision_id") == revision_id]

    if not current_blocks:
        # Lenient bootstrap: no sample for this revision → warn but don't block
        print(f"[finish] calibration: no calibration-sample for revision {revision_id} "
              f"(bootstrap period); not blocking")
        return

    if len(current_blocks) > 1:
        raise budget_gate.FailClosed(
            f"duplicate calibration-sample blocks for revision {revision_id}")

    sample = current_blocks[0]
    required = ("schema", "revision_id", "configured_limits", "usage",
                "productive_at_or_after_limit", "accounting_scope",
                "accounting_coverage", "model_invocations", "terminal")
    for field in required:
        if field not in sample:
            raise budget_gate.FailClosed(f"calibration-sample missing field: {field}")

    # Validate bindings: recompute SHA-256 where possible
    bindings = sample.get("bindings")
    if isinstance(bindings, dict):
        for key in ("budget_state", "gate_ledger", "attempts"):
            binding = bindings.get(key)
            if not isinstance(binding, dict):
                continue
            path_val = binding.get("path")
            expected_hash = binding.get("sha256")
            if not path_val or not expected_hash:
                continue
            file_path = active / path_val
            if file_path.is_file():
                actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                if actual_hash != expected_hash:
                    raise budget_gate.FailClosed(
                        f"calibration-sample binding '{key}' hash mismatch")
            else:
                print(f"[finish] calibration: binding '{key}' file {path_val} not found; "
                      "marked unavailable")
        rounds_bindings = bindings.get("rounds", [])
        if isinstance(rounds_bindings, list):
            for rb in rounds_bindings:
                if not isinstance(rb, dict):
                    continue
                rpath = rb.get("path")
                rhash = rb.get("sha256")
                if rpath and rhash:
                    rfile = active / rpath
                    if rfile.is_file():
                        actual = hashlib.sha256(rfile.read_bytes()).hexdigest()
                        if actual != rhash:
                            raise budget_gate.FailClosed(
                                f"calibration-sample round binding '{rpath}' hash mismatch")

    # Validate terminal event exists
    terminal_info = sample.get("terminal", {})
    terminal_eid = terminal_info.get("reviewer_terminal_event_id")
    if terminal_eid:
        event_exists = any(e.get("event_id") == terminal_eid for e in events)
        if not event_exists:
            raise budget_gate.FailClosed(
                f"calibration-sample references non-existent terminal {terminal_eid[:8]}")

    print(f"[finish] calibration: sample for revision {revision_id} validated")


def cmd_finish(args) -> int:
    active = Path(args.active_dir)
    slug = args.slug or active.name
    done_root = Path(args.done_root) if args.done_root else active.parent.parent / "done"
    completed: list[str] = []

    def fail(msg: str) -> int:
        _err(f"[finish] 已完成步骤: {', '.join(completed) if completed else '（无）'}")
        _err(f"[finish] 失败: {msg}")
        return EXIT_ERROR

    # 0. 拒绝已归档（消除错误 #5 的二次操作）
    if (done_root / slug).exists():
        return fail(f"步骤 0: {done_root / slug} 已存在——已归档目录拒绝二次操作"
                    f"（post-archive mutation 破坏 tree-closure）")
    completed.append("0")

    # 0.5 只读交叉核对（--verdict 转录点）
    if args.verdict == "阻断需修复":
        state = budget_gate.read_state(active)
        if not state.get("fsm", {}).get("severities"):
            return fail("步骤 0.5: 终局 verdict=阻断需修复 而 gate 侧 fsm.severities 为空"
                        "（record-verdict 未 ingest 过阻断 verdict，矛盾）——先跑 record-verdict")
    completed.append("0.5")

    # 1. 顺序 scope 产物连续编号
    missing = _finish_step1_missing(active)
    if missing:
        return fail(f"步骤 1: 产物编号有缺口，缺失: {', '.join(missing)}（前置拦截，"
                    f"而非 archive 中途 round_gap FAIL_CLOSED）")
    completed.append("1")

    # 2. gate-ledger 全部 reservation 已 settle
    status = _ledger_status(active)
    unsettled = sorted(rid for rid, st in status.items() if st["status"] == "reserved")
    if unsettled:
        return fail(f"步骤 2: 未 settle 的 reservation: {', '.join(unsettled)}（处置 = 逐个 "
                    f"register-round 或 cancel-round，finish 不自动代跑；open-无-started "
                    f"两命令均拒绝——带内路径 = reserve-round --resume-reservation 重试）")
    completed.append("2")

    # 2.5 只读预检：settle-无-started（历史/手工 ledger 孤儿）显性化前置，零写入
    events = capture.read_events(active)
    started_rids = {e["reservation_id"] for e in events
                    if e.get("event_type") == "invocation-started"
                    and e.get("invocation_kind") == "spawn"
                    and e.get("reservation_id")}
    orphans = sorted(rid for rid, st in status.items()
                     if st["status"] in TERMINAL_SETTLE_EVENTS
                     and st.get("consumes") != "task-envelope"
                     and rid not in started_rids)
    if orphans:
        print(f"[finish] 步骤 2.5 警告: 有 settle 无 started（历史/手工 ledger 孤儿，步骤 7 "
              f"硬校验必拦，无带内修复）: {', '.join(orphans)}")
    completed.append("2.5")

    # 3. 异常恢复（只补"有 started 无 terminal"缺口，从不无中生有）
    by_started = {e["event_id"]: e for e in events if e.get("event_type") == "invocation-started"}
    terminal_sids = {e["started_event_id"] for e in events
                     if e.get("event_type") == "invocation-terminal"}
    recover_notes: list[str] = []
    for ev in sorted(events, key=lambda e: e["sequence"]):
        if ev.get("event_type") != "invocation-started" or ev["event_id"] in terminal_sids:
            continue
        if ev.get("invocation_kind") == "continue":
            # continue 无 reservation（契约）：无 gate 状态可查，恢复 = recover(failed/process-interrupted)
            recover_notes.append(
                f"continue:{ev.get('invocation_id', '')[:8]}:补 recover(failed/process-interrupted)")
            if not args.dry_run:
                rargs = ["recover-invocation", str(active), ev["invocation_id"],
                         "--status", "failed", "--failure-reason-code", "process-interrupted",
                         "--instance-id", ev.get("parent_instance_id") or ""]
                rc, out, err_ = _archive_cli(*rargs)
                if rc != 0:
                    return fail(f"步骤 3: recover-invocation(continue) 失败: {out or err_}")
            continue
        rid = ev.get("reservation_id")
        st = status.get(rid, {})
        if st.get("status") not in TERMINAL_SETTLE_EVENTS:
            return fail(f"步骤 3: started 无 terminal 且 gate 无 settle 记录（步骤 2 不应放行）: {rid}")
        if st["status"] == "spawn_succeeded":
            row = _settle_row(active, rid) or {}
            output = _product_path(active, ev.get("role", ""), ev.get("round"))
            if output is None or not (output.is_file() and output.stat().st_size > 0):
                return fail(f"步骤 3: reservation {rid} 的产物无法解析（consumes=none 无推导、"
                            f"settle 行不含产物路径）——历史/手工 ledger 形态，停止")
            recover_notes.append(f"{rid}:补 complete(succeeded)")
            if not args.dry_run:
                # D1/O2：崩溃恢复缺省继承该 invocation-started 的 prompt_evidence.evidence_mode
                # （与 material gate 判定同源）；--evidence-mode 仅作显式覆盖（default=None 哨兵）。
                started_evidence = (ev.get("prompt_evidence") or {}).get(
                    "evidence_mode", "metadata-only")
                override = getattr(args, "evidence_mode", None)
                recovery_mode = override or started_evidence
                cargs = ["complete-invocation", str(active), ev["invocation_id"],
                         "--status", "succeeded",
                         "--instance-id", row.get("instance_id") or "",
                         "--evidence-level", "configured",
                         "--resolution-source", "cli_argument",
                         "--resolution-reason-code", "backend-does-not-expose",
                         "--output", str(output.resolve()),
                         "--evidence-mode", recovery_mode]
                rc, out, err_ = _archive_cli(*cargs)
                if rc != 0:
                    return fail(f"步骤 3: 补 complete-invocation 失败（{rid}）: {out or err_}")
        else:
            rstatus, rreason = GATE_TO_RECOVER.get(st["status"], ("failed", "backend-error"))
            recover_notes.append(f"{rid}:补 recover({rstatus})")
            if not args.dry_run:
                rargs = ["recover-invocation", str(active), ev["invocation_id"],
                         "--status", rstatus, "--failure-reason-code", rreason]
                rc, out, err_ = _archive_cli(*rargs)
                if rc != 0:
                    return fail(f"步骤 3: 补 recover-invocation 失败（{rid}）: {out or err_}")

    # 3.4 D3/O7 手工状态转移显式降级：扫描 attempts.md 的 [manual-fallback] 条目。
    # 位置写死：step 3（异常恢复循环，含其"产物无法解析"早退）之后、step 3.5 之前、
    # 归档（step 7）之前。扫描只读；--dry-run 下同样生效（插入点先于 dry-run 早退）。
    attempts_path = active / "attempts.md"
    manual_fallback_count = 0
    if attempts_path.is_file():
        # N1：按行首 bullet 锚定计数，正文对字面量的引用不计入（见审计 N1）。
        manual_fallback_count = len(re.findall(
            r"^[ \t]*- \[manual-fallback\]",
            attempts_path.read_text(encoding="utf-8"), re.MULTILINE))
    if manual_fallback_count:
        print(f"[finish] DEGRADED:manual-fallback={manual_fallback_count}")
        if not getattr(args, "acknowledge_manual_fallback", False):
            return fail(
                f"步骤 3.4: 检测到 {manual_fallback_count} 条 [manual-fallback] 手工状态转移"
                f"（DEGRADED:manual-fallback={manual_fallback_count}）——须显式 "
                f"--acknowledge-manual-fallback 才能继续归档")
    completed.append("3.4")

    # 3.5 Material gate + calibration sample validation (non-dry-run only)
    if not args.dry_run:
        _validate_material_gate(active, events)
        _validate_calibration_sample(active, events)

    # 4. 终局 decision（读 evidence/events 实际文件，零转录）
    completed.append("3")
    events = capture.read_events(active) if not args.dry_run else events
    fresh = model.REVIEWER_AUTHORITIES["fresh"]
    blank = model.REVIEWER_AUTHORITIES["blank-slate"]
    last_terminal = None
    review_kind = None
    for e in sorted(events, key=lambda x: x["sequence"]):
        if e.get("event_type") != "invocation-terminal" or e.get("terminal_status") != "succeeded":
            continue
        st_event = by_started.get(e.get("started_event_id"))
        role = st_event.get("role") if st_event else None
        if st_event is not None and st_event.get("invocation_kind") != "spawn":
            continue
        if role in fresh:
            last_terminal, review_kind = e, "fresh"
        elif role in blank:
            last_terminal, review_kind = e, "blank-slate"
    if last_terminal is None:
        return fail("步骤 4: 无 reviewer-authority（fresh/blank-slate）成功 terminal，"
                    "无法 record 终局 reviewer-verdict")
    final = model.final_decision_summary(events)
    if final is not None:
        if final["type"] != "reviewer-verdict":
            return fail("步骤 4: 已存在 user-decision 终局——finish 不覆盖 user-decision 类终止"
                        "（走手工分步，见 plan 非目标）")
        if final["value"] != args.verdict:
            return fail(f"步骤 4: 已 record 的终局 decision verdict={final['value']!r} 与 "
                        f"--verdict {args.verdict!r} 冲突（复用前提是判定一致）")
        final_event = next(e for e in events
                           if e.get("event_type") == "terminal-decision"
                           and e["event_id"] == final["event_id"])
        if final_event.get("reviewer_event_id") != last_terminal["event_id"]:
            # Reopened superseding decision path (D8 / Phase 4):
            # When .reopen-state.json indicates a reopened object and the existing
            # decision verdict matches --verdict, append a NEW reviewer-verdict
            # decision bound to the latest authority terminal. The graph derives
            # supersedes automatically. Never rewrite the old decision.
            reopen_path = active / ".reopen-state.json"
            if reopen_path.is_file() and final["value"] == args.verdict:
                if not args.dry_run:
                    dargs = ["record-terminal-decision", str(active),
                             "--decision-type", "reviewer-verdict",
                             "--reviewer-event-id", last_terminal["event_id"],
                             "--review-kind", review_kind,
                             "--verdict", args.verdict,
                             "--verdict-output-ref", last_terminal["event_id"]]
                    rc, out, err_ = _archive_cli(*dargs)
                    if rc != 0:
                        return fail(f"步骤 4: record-terminal-decision (reopened supersedes) "
                                    f"失败: {out or err_}")
                    decision_note = (f"superseded old={final['event_id'][:8]}, "
                                     f"new={json.loads(out)['event_id'][:8]}")
                else:
                    decision_note = (f"supersede (dry-run: old={final['event_id'][:8]})")
            else:
                return fail("步骤 4: 已 record decision 的 reviewer_event_id 与最后一个 "
                            "reviewer-authority 成功 terminal 不一致")
        else:
            decision_note = f"reused（event_id={final['event_id']}）"
    elif args.dry_run:
        decision_note = "record（dry-run 占位）"
    else:
        dargs = ["record-terminal-decision", str(active),
                 "--decision-type", "reviewer-verdict",
                 "--reviewer-event-id", last_terminal["event_id"],
                 "--review-kind", review_kind,
                 "--verdict", args.verdict,
                 "--verdict-output-ref", last_terminal["event_id"]]
        rc, out, err_ = _archive_cli(*dargs)
        if rc != 0:
            return fail(f"步骤 4: record-terminal-decision 失败: {out or err_}")
        decision_note = f"recorded（event_id={json.loads(out)['event_id']}）"

    if args.dry_run:
        print("[dry-run] finish 只读自检通过（步骤 0-2.5）+ 步骤 3-4 判定如下，"
              "后续写操作未执行:")
        print(f"  3. {'; '.join(recover_notes) if recover_notes else '无 started-无-terminal 缺口'}")
        print(f"  3.5 material-gate + calibration-sample validated (non-dry-run)")
        print(f"  4. 终局 decision: {decision_note}; reviewer terminal="
              f"{last_terminal['event_id']} kind={review_kind}")
        print("  5. stamp-decision-markers（retrospective.md + 最高 round-N.md）")
        print("  6. prompt 归位 + 根目录 allowlist 校验")
        print(f"  7. archive {active.parent} {done_root} {slug} --local-staging auto")
        print(f"  8. 归档后 check {done_root / slug}")
        return EXIT_OK

    completed.append("4")

    # 5. stamp-decision-markers
    rc, out, err_ = _archive_cli("stamp-decision-markers", str(active), "--format", "json")
    if rc != 0:
        return fail(f"步骤 5: stamp-decision-markers 失败: {out or err_}")
    completed.append("5")

    # 6. prompt 归位 + 根目录 allowlist 校验（FS 枚举 ∩ ROOT_FIXED allowlist 求差）
    moved, stray = _finish_step6(active)
    if stray:
        return fail(f"步骤 6: 根目录存在 allowlist 外条目: {', '.join(stray)}（archive "
                    f"root-clutter 必拦，前置显性化）")
    completed.append("6")

    # 7. archive（--declare-orphan-reservation 不是本命令参数：常态与异常均不暴露；
    #    历史孤儿走人工归档披露，orchest 不自动化、不绕过）
    rc, out, err_ = _archive_cli("archive", str(active.parent), str(done_root), slug,
                                 "--local-staging", "auto")
    if rc != 0:
        return fail(f"步骤 7: archive 失败（含事务回滚）: {out or err_}")
    completed.append("7")

    # 8. 归档后 check
    rc, out, err_ = _archive_cli("check", str(done_root / slug), "--format", "json")
    if rc != 0:
        return fail(f"步骤 8: 归档后 check 失败: {out or err_}")
    completed.append("8")

    print(f"[finish] 完成: {done_root / slug} verdict={args.verdict} "
          f"decision={decision_note}; 步骤: {', '.join(completed)}")
    return EXIT_OK


# ==============================================================================
# §6 checkpoint-paths
# ==============================================================================

# clean_env 剥离的 git 仓库定位变量（hook 上下文中它们优先于 -C，使跨仓查询静默落回
# 当前仓库——实证见源仓 check_plan_review.git 的 docstring）
_GIT_ENV_STRIP = (
    "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX", "GIT_COMMON_DIR",
)


def changed_paths(commit: str, repo: str | None = None) -> set[str]:
    """核验 commit 的实际改动路径。

    本函数是 KB 仓 check_plan_review.changed_paths 的**逐字复刻**（非"同算法"口号）。
    源锚点: C:/OneDrive/Cr/Obsidian_Vault/.meta/scripts/check_plan_review.py:79
    （changed_paths，2026-08-15 时点行号）。跨仓断言见 tests/test_orchest.py
    验收 7（fixture 固化 + KB_VAULT_ROOT 现算对比 skip-if-absent）；源算法变更导致
    锚点失准时，由验收 7(b) 现算对比捕获。
    """
    cargs = ["diff-tree", "--root", "--no-commit-id", "--name-status", "-r", "-M", commit]
    if repo:
        cargs = ["-C", repo, *cargs]
    env = None
    if repo:
        env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_STRIP}
    result = subprocess.run(
        ["git", *cargs], text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    paths: set[str] = set()
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        if parts[0].startswith(("R", "C")) and len(parts) >= 3:
            paths.update((parts[1], parts[2]))
        elif len(parts) >= 2:
            paths.add(parts[1])
    return paths


def cmd_checkpoint_paths(args) -> int:
    try:
        paths = changed_paths(args.commit, args.repo)
    except RuntimeError as exc:
        _err(f"checkpoint-paths 失败: {exc}")
        return EXIT_ERROR
    lines = ["implementation_paths:"]
    if paths:
        for p in sorted(paths):
            lines.append(f"  - {p}")
    else:
        lines[0] = "implementation_paths: []"
    print("\n".join(lines))
    return EXIT_OK


# ==============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchest",
        description="converge 执行层编排：六条原子命令（reserve-round / register-round / "
                    "cancel-round / record-verdict / finish / checkpoint-paths），"
                    "消除 orchestrator 机械操作中的转录错误/漏步/顺序错；评审层保持 LLM 自由。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    r = sub.add_parser("reserve-round",
                       help="gate reserve → begin-invocation → 骨架（宿主 Spawn 之前）")
    r.add_argument("--active-dir", required=True)
    r.add_argument("--role", default=None,
                   help="spawn 轮必填；--continue-of 轮由父轮派生（传入则须与父轮一致）")
    r.add_argument("--continue-of", metavar="RID", default=None,
                   help="Inner Loop Continue：父轮（已 succeeded 的 spawn）rid；发射 "
                        "begin-invocation kind=continue——契约规定 continue 不携带 "
                        "reservation，计数入 max_inner_loops（无 gate reserve）")
    r.add_argument("--prompt-file", required=True)
    r.add_argument("--phase", required=True)
    r.add_argument("--requested-provider")
    r.add_argument("--requested-model")
    r.add_argument("--round", type=int, default=None,
                   help="round number（consuming 角色必填；0 归一化为 null）")
    r.add_argument("--attempt", type=int, default=1)
    r.add_argument("--tier", default="auditable-only", choices=["auditable-only", "enforced"])
    r.add_argument("--resume-reservation", metavar="RID",
                   help="begin 失败后的同 rid 重试入口（跳过 reserve，前置校验 role/round）")
    r.add_argument("--evidence-mode", default="metadata-only",
                   choices=["metadata-only", "redacted", "exact"],
                   help="证据模式（material revision 需要 exact 以链接 prompt blob）")
    r.add_argument("--dry-run", action="store_true")
    r.set_defaults(func=cmd_reserve_round)

    g = sub.add_parser("register-round", help="宿主成功返回后：complete → settle → 回填")
    g.add_argument("--active-dir", required=True)
    g.add_argument("--reservation-id", default=None,
                   help="spawn 轮入口（与 --invocation-id 二选一）")
    g.add_argument("--invocation-id", default=None,
                   help="continue 轮入口（与 --reservation-id 二选一；complete 而无 settle）")
    g.add_argument("--instance-id", required=True)
    g.add_argument("--output", default=None,
                   help="产物路径（consumes=none 角色必填；consuming 角色缺省按 role+round 推导）")
    g.add_argument("--backend")
    g.add_argument("--backend-version")
    g.add_argument("--evidence-level", default="configured",
                   choices=["configured", "observed", "host-reported"])
    g.add_argument("--resolution-source", default="cli_argument",
                   choices=["cli_argument", "host_receipt", "tool_response", "agent_config"])
    g.add_argument("--resolution-reason-code", default="backend-does-not-expose",
                   choices=["backend-does-not-expose", "receipt-missing"])
    g.add_argument("--evidence-mode", default="metadata-only",
                   choices=["metadata-only", "redacted", "exact"],
                   help="证据模式（material revision 需要 exact 以链接 blob）")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_register_round)

    c = sub.add_parser("cancel-round", help="宿主失败/取消后：recover → settle → 骨架处理")
    c.add_argument("--active-dir", required=True)
    c.add_argument("--reservation-id", default=None,
                   help="spawn 轮入口（与 --invocation-id 二选一）")
    c.add_argument("--invocation-id", default=None,
                   help="continue 轮入口（recover-cancelled，无 settle）")
    c.add_argument("--reason-code", required=True,
                   choices=["cancelled-by-host", "backend-error", "timeout"])
    c.add_argument("--pre-execution", action="store_true",
                   help="true = 模型从未被调用（宿主 spawn 直接报错）；默认 false（诚实默认）")
    c.add_argument("--detail")
    c.add_argument("--instance-id")
    c.add_argument("--dry-run", action="store_true")
    c.set_defaults(func=cmd_cancel_round)

    v = sub.add_parser("record-verdict", help="产物 frontmatter 契约字段 + gate ingest-verdict")
    v.add_argument("--active-dir", required=True)
    v.add_argument("--round", type=int, required=True)
    v.add_argument("--verdict", required=True)
    v.add_argument("--severities", default=None, help="逗号分隔（阻断需修复时）")
    v.add_argument("--product", default=None,
                   help="产物文件名（默认 round-N.md；盲审轮传 blind-recheck-N.md）")
    v.add_argument("--dry-run", action="store_true")
    v.set_defaults(func=cmd_record_verdict)

    f = sub.add_parser("finish", help="异常恢复 + 终局 decision + 归档（固定顺序一条命令）")
    f.add_argument("--active-dir", required=True)
    f.add_argument("--verdict", required=True,
                   help="终局 verdict（必填：缺省会诱导'先跑起来再说'的半途失败）")
    f.add_argument("--done-root", default=None,
                   help='缺省 = active 上级目录的同级 done/（如 .converge/active/<slug> → .converge/done）')
    f.add_argument("--slug", default=None, help="缺省 = <active-dir> 目录名")
    f.add_argument("--evidence-mode", default=None,
                   choices=["metadata-only", "redacted", "exact"],
                   help="D1/O2：崩溃恢复 complete 的显式覆盖；缺省（None）继承对应 "
                        "invocation-started 的 prompt_evidence.evidence_mode")
    f.add_argument("--acknowledge-manual-fallback", action="store_true",
                   help="D3/O7：显式确认 attempts.md 中的 [manual-fallback] 手工状态转移"
                        "（否则 finish 输出 DEGRADED 并停止）")
    f.add_argument("--dry-run", action="store_true")
    f.set_defaults(func=cmd_finish)

    k = sub.add_parser("checkpoint-paths", help="git diff-tree → implementation_paths YAML 块")
    k.add_argument("--commit", required=True)
    k.add_argument("--repo", default=None,
                   help="外部仓库路径（跨仓核验；给定时剥离开 GIT_* 定位变量）")
    k.add_argument("--dry-run", action="store_true", help="本命令只读，dry-run 行为等同")
    k.set_defaults(func=cmd_checkpoint_paths)

    return parser


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except budget_gate.FailClosed as e:
        _err(f"FAIL_CLOSED:{e.reason}")
        return 30
    except model.ArchiveError as e:
        _err(f"archive-error:{e.code}: {e.summary}")
        return 3
    except Exception as e:  # noqa: BLE001 —— fail-closed 安全网
        _err(f"orchest-internal:{type(e).__name__}: {e}")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
