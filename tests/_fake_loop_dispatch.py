#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""converge_loop 测试用 fake ocsr_dispatch.py — 模拟 skill 版 dispatch CLI。

不调用任何模型。行为由环境变量控制：
  FAKE_STATE_FILE — JSON 文件路径，内容为 {"<label>": {"verdict": "...", "severities": [...]}}
                    fake 为每个 worker 按 label 查表写报告（含 ```yaml verdict 块）；
                    查不到 → 写一个无 verdict 块的报告（供解析失败路径测试）。
  FAKE_MODE       — "happy"（默认，写产物 exit 0）
                    "fail-no-artifact"（不写产物 exit 1）
                    "mismatch-exit"（写产物但 exit 1，模拟 watcher 虚报场景）
CLI 面与真实 ocsr_dispatch.py dispatch 对齐（worker/output-dir/output-pattern/
watch/timeout/harness/ledger-dir/meta/stagger/forbid-paths/work-dir）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("dispatch")
    d.add_argument("--worker", action="append")
    d.add_argument("--output-dir", required=True)
    d.add_argument("--output-pattern", required=True)
    d.add_argument("--watch", action="store_true")
    d.add_argument("--timeout", type=int, default=15)
    d.add_argument("--harness", default="fake")
    d.add_argument("--ledger-dir")
    d.add_argument("--meta", action="append", default=[])
    d.add_argument("--stagger", type=int, default=0)
    d.add_argument("--forbid-paths", action="append", default=[])
    d.add_argument("--work-dir")
    args = parser.parse_args()

    mode = os.environ.get("FAKE_MODE", "happy")
    state = {}
    sf = os.environ.get("FAKE_STATE_FILE")
    if sf and Path(sf).is_file():
        state = json.loads(Path(sf).read_text(encoding="utf-8"))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ledger_rows = []
    for w in (args.worker or []):
        prompt_file, model, label = w.split("|", 2)
        out_name = (args.output_pattern
                    .replace("{label}", label)
                    .replace("{model}", model.replace("/", "-")))
        out_path = output_dir / out_name
        entry = state.get(label, {})
        if mode != "fail-no-artifact":
            verdict = entry.get("verdict")
            sevs = entry.get("severities", [])
            body = entry.get("body", "")
            if verdict:
                sev_lines = "\n".join(
                    f"  - id: {i}\n    description: fake issue {i}\n"
                    f"    attribution: plan_defect\n    severity: {s}\n"
                    f"    plan_amendment_required: true\n    location: fake"
                    for i, s in enumerate(sevs, 1))
                content = (f"```yaml\nverdict: {verdict}\nblocking_issues:\n{sev_lines}\n```\n"
                           f"{body}\n")
            else:
                content = body or f"# fake report for {label}\n（无 yaml verdict 块）\n"
            out_path.write_text(content, encoding="utf-8")
        ledger_rows.append({"label": label, "model": model, "status": "launched"})

    if args.ledger_dir:
        led = Path(args.ledger_dir)
        led.mkdir(parents=True, exist_ok=True)
        with open(led / "ocsr-dispatch-ledger.jsonl", "a", encoding="utf-8") as f:
            for row in ledger_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    if mode == "fail-no-artifact":
        print("[fake] 模拟失败：无产物", file=sys.stderr)
        return 1
    if mode == "mismatch-exit":
        print("[fake] 模拟 watcher 虚报：产物已写但 exit 1", file=sys.stderr)
        return 1
    print("[fake] 全部 worker 完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
