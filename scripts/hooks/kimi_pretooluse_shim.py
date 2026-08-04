#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kimi_pretooluse_shim.py — 把 kimi-code 宿主的 hook 事件桥接到 converge budget_gate。

用途
----
kimi-code 的 PreToolUse hook 从 stdin 收到 JSON（含 session_id、tool_input 等字段，
工具名字段存在 tool_name / toolName / tool 变体；kimi 的 spawn 工具名为 `Agent`）。
converge 的 budget_gate.py hook-pretooluse 按 Claude Code 格式实现（读 stdin 的
tool_name/session_id，deny 时打印 {"hookSpecificOutput": {...}} JSON，始终 exit 0）。
本 shim 做字段归一化后以子进程调用 budget_gate，并逐字转发其裁决 stdout。

两种模式
--------
1. 默认（PreToolUse）：读 stdin JSON → 归一化为 {"tool_name": ..., "session_id": ...}
   → 调用 <converge>/scripts/budget_gate.py hook-pretooluse（相对本文件位置解析：
   本文件位于 scripts/hooks/，budget_gate.py 在上一级 scripts/）→ 逐字转发其
   stdout（字节级），exit 0。
2. --record-session <文件>（SessionStart/PreToolUse 用）：从 stdin JSON 取
   session_id，原子写入 {"session_id": ..., "updated_at": <ISO>} 到指定文件，
   供 orchestrator 执行 `budget_gate.py bind --session-id` 前读取。

kimi config.toml 接线样例（示意，按实际 hook 配置语法调整）：

    [[hooks]]
    event = "PreToolUse"
    command = "python <converge>/scripts/hooks/kimi_pretooluse_shim.py"

    [[hooks]]
    event = "SessionStart"
    command = "python <converge>/scripts/hooks/kimi_pretooluse_shim.py --record-session <converge-tmp>/session.json"

best-effort 边界
----------------
本 shim 是 best-effort 残余：自身解析失败、budget_gate.py 缺失、子进程异常/超时
时一律 fail-open（exit 0、无 stdout，stderr 留一行说明）——**不得视为 fail-closed**。
真正的阻断裁决只来自 budget_gate 自身（其绑定会话内的 fail-closed 逻辑不受本
shim 影响）；shim 这一层只做透明桥接，不新增任何阻断语义。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BUDGET_GATE = Path(__file__).resolve().parent.parent / "budget_gate.py"
TOOL_NAME_KEYS = ("tool_name", "toolName", "tool")
GATE_TIMEOUT_SEC = 15


def _fail_open(reason: str) -> int:
    """best-effort 边界：任何 shim 自身故障都不阻断工具调用。"""
    try:
        print(f"[kimi-pretooluse-shim] fail-open: {reason}", file=sys.stderr)
    except Exception:
        pass
    return 0


def _read_stdin_json() -> dict:
    data = json.loads(sys.stdin.read())
    if not isinstance(data, dict):
        raise ValueError("stdin JSON 不是对象")
    return data


def _normalize_tool_name(data: dict) -> str | None:
    """工具名字段容忍 tool_name / toolName / tool 三种键。"""
    for key in TOOL_NAME_KEYS:
        val = data.get(key)
        if isinstance(val, str) and val:
            return val
    return None


def _forward_stdout(raw: bytes) -> None:
    """逐字（字节级）转发 budget_gate 的 stdout。"""
    out = getattr(sys.stdout, "buffer", None)
    if out is not None:
        out.write(raw)
        out.flush()
    else:
        sys.stdout.write(raw.decode("utf-8", errors="replace"))
        sys.stdout.flush()


def _mode_pretooluse() -> int:
    try:
        data = _read_stdin_json()
        normalized = {
            "tool_name": _normalize_tool_name(data),
            "session_id": data.get("session_id"),
        }
        if not BUDGET_GATE.is_file():
            return _fail_open(f"budget_gate.py 不存在: {BUDGET_GATE}")
        proc = subprocess.run(
            [sys.executable, str(BUDGET_GATE), "hook-pretooluse"],
            input=json.dumps(normalized, ensure_ascii=False).encode("utf-8"),
            capture_output=True,
            timeout=GATE_TIMEOUT_SEC,
        )
        if proc.stdout:
            _forward_stdout(proc.stdout)
        return 0
    except Exception as e:  # noqa: BLE001 —— shim 层 fail-open
        return _fail_open(f"{type(e).__name__}: {e}")


def _mode_record_session(target: str) -> int:
    try:
        data = _read_stdin_json()
        sid = data.get("session_id")
        if not isinstance(sid, str) or not sid:
            return _fail_open("stdin JSON 缺少 session_id")
        dest = Path(target)
        dest.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {"session_id": sid, "updated_at": datetime.now(timezone.utc).isoformat()},
            ensure_ascii=False,
        )
        # 原子写入：同目录临时文件 + os.replace，避免 orchestrator 读到半写文件
        fd, tmp_name = tempfile.mkstemp(dir=str(dest.parent), prefix=dest.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(payload + "\n")
            os.replace(tmp_name, dest)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        return 0
    except Exception as e:  # noqa: BLE001 —— 写失败 fail-open
        return _fail_open(f"{type(e).__name__}: {e}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="kimi-code hook → converge budget_gate 桥接 shim（best-effort，fail-open）")
    parser.add_argument("--record-session", metavar="FILE",
                        help="SessionStart 模式：从 stdin JSON 取 session_id 原子写入指定文件")
    args = parser.parse_args()
    if args.record_session:
        return _mode_record_session(args.record_session)
    return _mode_pretooluse()


if __name__ == "__main__":
    sys.exit(main())
