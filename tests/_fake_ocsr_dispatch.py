#!/usr/bin/env python3
"""Test shim that mimics ocsr_dispatch.py's CLI surface for unit-testing ocsr_spawn_adapter.

Does NOT call opencode or any model. Simulates one of three outcomes based on env var
FAKE_OCSR_MODE:
  - "happy" (default): writes a small product file to the expected --output-dir/pattern,
    writes a launched+landed row to --ledger-dir/ocsr-dispatch-ledger.jsonl, exits 0.
  - "fail-launcher": writes only a launched row + error.log to the work dir, no product,
    exits non-zero (simulates Start-Process failure → pre_execution).
  - "fail-timeout": writes only a launched row, no product, no error.log, exits 1
    (simulates watchdog timeout → model invoked but stalled, not pre_execution).

The shim deliberately accepts the same arg shape as the real ocsr_dispatch.py dispatch
subcommand so the adapter code path is identical to production.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import uuid
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("dispatch")
    d.add_argument("--worker", action="append")
    d.add_argument("--output-dir", required=True)
    d.add_argument("--output-pattern", required=True)
    d.add_argument("--ledger-dir")
    d.add_argument("--watch", action="store_true")
    d.add_argument("--timeout", type=int, default=15)
    d.add_argument("--progress", action="store_true")
    d.add_argument("--harness", default="fake")
    d.add_argument("--meta", action="append", default=[])
    d.add_argument("--stagger", type=int, default=0)
    d.add_argument("--work-dir")
    args = parser.parse_args()

    mode = os.environ.get("FAKE_OCSR_MODE", "happy")
    worker = (args.worker or ["prompt.txt|provider/model|label"])[0]
    prompt_file, model, label = worker.split("|", 2)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / args.output_pattern

    batch_id = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    work_root = Path(args.work_dir or os.environ.get("TEMP", "/tmp"))
    work_dir = work_root / f"ocsr_dispatch_{batch_id}" / label.replace("/", "-").replace(" ", "_")
    work_dir.mkdir(parents=True, exist_ok=True)

    # Always write launched row to ledger (mirrors real ocsr behavior)
    if args.ledger_dir:
        ledger = Path(args.ledger_dir) / "ocsr-dispatch-ledger.jsonl"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        launched_row = {
            "ts": datetime.datetime.now().astimezone().isoformat(),
            "event": "launched",
            "batch_id": batch_id,
            "label": label,
            "model": model,
            "harness": args.harness,
            "prompt_file": str(Path(prompt_file).resolve()),
            "expected_output": str(output_path),
            "work_dir": str(work_dir),
        }
        with ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(launched_row, ensure_ascii=False) + "\n")

    # start.marker (mirrors real ocsr)
    (work_dir / "start.marker").write_text(
        f"pwsh started {datetime.datetime.now().astimezone().isoformat()}\n",
        encoding="utf-8",
    )

    if mode == "happy":
        output_path.write_text("fake-product-content\n", encoding="utf-8")
        # Append "exit=0" to start.marker (mirrors real ocsr behavior)
        with (work_dir / "start.marker").open("a", encoding="utf-8") as f:
            f.write("exit=0\n")
        # Write landed row
        if args.ledger_dir:
            ledger = Path(args.ledger_dir) / "ocsr-dispatch-ledger.jsonl"
            landed_row = {
                "ts": datetime.datetime.now().astimezone().isoformat(),
                "event": "landed",
                "batch_id": batch_id,
                "label": label,
                "model": model,
                "output": str(output_path),
                "bytes": output_path.stat().st_size,
                "wall_min": 0.1,
            }
            with ledger.open("a", encoding="utf-8") as f:
                f.write(json.dumps(landed_row, ensure_ascii=False) + "\n")
        if args.progress:
            print(f"[fake] happy: wrote {output_path}")
        return 0

    if mode == "fail-launcher":
        # Simulate Start-Process / launcher error: write error.log, exit non-zero, no product
        (work_dir / "error.log").write_text(
            "simulated launcher failure (Start-Process returned non-zero)\n",
            encoding="utf-8",
        )
        if args.progress:
            print(f"[fake] fail-launcher: wrote error.log to {work_dir}")
        return 2

    if mode == "fail-timeout":
        # Simulate watchdog timeout: no product, no error.log, exit 1
        if args.progress:
            print(f"[fake] fail-timeout: no product, exit 1")
        return 1

    if mode == "fail-collision":
        # Simulate path collision (exit 3)
        return 3

    print(f"[fake] unknown FAKE_OCSR_MODE: {mode}", file=sys.stderr)
    return 99


if __name__ == "__main__":
    sys.exit(main())
