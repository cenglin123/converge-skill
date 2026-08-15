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
import json
import os
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
# gate settle result → recover result（cancel-round §3c 反向；timeout→failed 同上）
GATE_TO_RECOVER = {"failed": "failed", "cancelled": "cancelled"}

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
    return _run(GATE_SCRIPT, list(args))


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

def cmd_reserve_round(args) -> int:
    active = Path(args.active_dir)
    prompt = Path(args.prompt_file)
    role = args.role
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
              f"evidence-mode=metadata-only")
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
                  "--evidence-mode", "metadata-only"]
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
             "--evidence-mode", "metadata-only"]
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
    """顺序 scope 产物连续编号自检（读目录枚举，不信任 LLM 计数）。"""
    missing: list[str] = []
    for scope in budget_gate.CONTIGUOUS_SCOPES:
        nums = budget_gate.realized_round_numbers(active, scope)
        if not nums:
            continue
        have = set(nums)
        for n in range(1, max(nums) + 1):
            if n not in have:
                missing.append(budget_gate.SCOPE_PRODUCT[scope].format(n=n))
    return missing


def _finish_step6(active: Path) -> tuple[int, list[str]]:
    """归位 prompt 文件 + 根目录 allowlist 校验（从 FS 枚举，非硬编码文件名匹配）。
    返回 (moved_count, stray_entries)。"""
    moved = 0
    for p in sorted(active.glob("*prompt*.md")):
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
        elif not model.is_root_allowed_name(entry.name):
            stray.append(entry.name)
    return moved, stray


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
                cargs = ["complete-invocation", str(active), ev["invocation_id"],
                         "--status", "succeeded",
                         "--instance-id", row.get("instance_id") or "",
                         "--evidence-level", "configured",
                         "--resolution-source", "cli_argument",
                         "--resolution-reason-code", "backend-does-not-expose",
                         "--output", str(output.resolve()),
                         "--evidence-mode", "metadata-only"]
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
            return fail("步骤 4: 已 record decision 的 reviewer_event_id 与最后一个 "
                        "reviewer-authority 成功 terminal 不一致")
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
    r.add_argument("--role", required=True)
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
    r.add_argument("--dry-run", action="store_true")
    r.set_defaults(func=cmd_reserve_round)

    g = sub.add_parser("register-round", help="宿主成功返回后：complete → settle → 回填")
    g.add_argument("--active-dir", required=True)
    g.add_argument("--reservation-id", required=True)
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
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_register_round)

    c = sub.add_parser("cancel-round", help="宿主失败/取消后：recover → settle → 骨架处理")
    c.add_argument("--active-dir", required=True)
    c.add_argument("--reservation-id", required=True)
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
