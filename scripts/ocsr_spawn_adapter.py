#!/usr/bin/env python3
"""ocsr_spawn_adapter —— 把 OCSR dispatch 包装为 converge Archive Contract v1 的 Spawn 实现。

本脚本是 design.md（.converge/active/20260725-ocsr-converge-integration/design.md）选项 B
的落地：在 converge 仓库侧新增一层薄适配，把"budget_gate reserve → archive_convergence
begin-invocation → ocsr_dispatch dispatch → archive_convergence complete/recover-invocation
→ budget_gate settle"五步原子化，使 OCSR 驱动的 converge 能通过 archive（valid）+
check（valid-v1）。

设计原则（与 ocsr SKILL.md §三 "脚本不做编排判断" 对齐）：
- 本脚本不做编排判断（选模型、prompt 残差注入、verdict 裁决仍由 orchestrator 负责）。
- 只做协议串联：每次 Spawn 把事件流 + 预算门控接好，按 outcome 落 complete/recover。
- fail-closed：begin 后 dispatch 阶段的异常都尝试 recover；complete 自身的失败不 recover（by design，避免重复终态）。
- provenance 严格诚实：configured + cli_argument + backend-does-not-expose
  （PROVENANCE_MATRIX 下 OCSR 无 per-invocation tool_response 绑定时的 strictest legal choice）。

退出码：
    0  = 全链路成功（spawn succeeded，complete-invocation 已记录）
    3  = Archive Contract 子 CLI 错误（begin/complete/recover/reserve/settle 返回非零）
    5  = ocsr dispatch 未落盘（看门狗超时 / exit≠0 / error.log）
    10 = budget_gate reserve BLOCK（透传 gate 的决策）
    11 = budget_gate reserve DENY
    30 = FAIL_CLOSED
    其他 = 异常

用法见 README / design.md。stdlib only。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path


EXIT_PROCEED = 0
EXIT_ARCHIVE_CLI = 3
EXIT_OCSR_NO_PRODUCT = 5
EXIT_BLOCK = 10
EXIT_DENY = 11
EXIT_FAIL_CLOSED = 30
EXIT_INTERNAL = 1


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _run_cli(script: Path, args: list[str]) -> tuple[int, str, str]:
    """Run a Python CLI script as subprocess, return (rc, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _parse_provider_model(model: str) -> tuple[str, str]:
    """Split 'provider/model' into (provider, model). Both required.

    OCSR `--worker` MODEL field uses opencode's full ID form (e.g.
    'deepseek/deepseek-v4-flash'). The archive Contract's requested provenance
    splits provider and model; we mirror that split here.
    """
    if "/" not in model:
        raise ValueError(f"model must be 'provider/model' form, got: {model}")
    provider, _, model_id = model.partition("/")
    if not provider or not model_id:
        raise ValueError(f"model must be 'provider/model' form, got: {model}")
    return provider, model_id


def _gate_reserve(gate_script: Path, active_dir: Path, role: str, target_round: int | None,
                  reservation_id: str | None, tier: str) -> tuple[int, str]:
    """Run budget_gate.py reserve. Returns (exit_code, rid_or_message)."""
    args = ["reserve", "--active-dir", str(active_dir), "--role", role, "--tier", tier]
    if target_round is not None:
        args += ["--target-round", str(target_round)]
    if reservation_id:
        args += ["--reservation-id", reservation_id]
    rc, out, err = _run_cli(gate_script, args)
    if rc == 0 and out.startswith("PROCEED:"):
        return 0, out[len("PROCEED:"):]
    return rc, out or err


def _gate_settle(gate_script: Path, active_dir: Path, reservation_id: str,
                 result: str, instance_id: str | None = None,
                 pre_execution: bool = False, reason: str | None = None) -> int:
    args = ["settle", "--active-dir", str(active_dir),
            "--reservation-id", reservation_id, "--result", result]
    if instance_id:
        args += ["--instance-id", instance_id]
    if pre_execution:
        args += ["--pre-execution"]
    if reason:
        args += ["--reason", reason]
    rc, out, err = _run_cli(gate_script, args)
    return rc


def _archive_begin(archive_script: Path, active_dir: Path, *, kind: str, role: str,
                   phase: str, round_number: int | None, attempt: int,
                   reservation_id: str, requested_provider: str, requested_model: str,
                   prompt_path: Path, evidence_mode: str) -> tuple[int, dict | None]:
    """Run archive_convergence.py begin-invocation. Returns (rc, parsed_json_or_None)."""
    args = ["begin-invocation", str(active_dir),
            "--kind", kind, "--role", role, "--phase", phase,
            "--attempt", str(attempt),
            "--reservation-id", reservation_id,
            "--requested-provider", requested_provider,
            "--requested-model", requested_model,
            "--prompt", str(prompt_path),
            "--evidence-mode", evidence_mode]
    if round_number is not None:
        args += ["--round", str(round_number)]
    rc, out, err = _run_cli(archive_script, args)
    if rc != 0:
        _err(f"begin-invocation failed (rc={rc}): {out or err}")
        return rc, None
    try:
        return 0, json.loads(out)
    except json.JSONDecodeError as e:
        _err(f"begin-invocation returned non-JSON: {e}; raw: {out[:200]}")
        return EXIT_ARCHIVE_CLI, None


def _archive_complete(archive_script: Path, active_dir: Path, invocation_id: str, *,
                      status: str, instance_id: str | None, receipt: str | None,
                      backend: str | None, backend_version: str | None,
                      output_path: Path, evidence_mode: str) -> int:
    """Run complete-invocation with the configured-level provenance combination.

    Per design.md §3.3 + model.py:PROVENANCE_MATRIX:
      evidence_level=configured, resolution_source=cli_argument,
      resolution_reason_code=backend-does-not-expose.
    OCSR dispatch has no per-invocation tool_response binding the resolved model,
    so we cannot elevate to host-reported/observed. The --instance-id and --receipt
    are kept as non-constraining correlation handles (audit/debug), not as
    evidence-binding facts.
    """
    args = ["complete-invocation", str(active_dir), invocation_id,
            "--status", status,
            "--evidence-level", "configured",
            "--resolution-source", "cli_argument",
            "--resolution-reason-code", "backend-does-not-expose",
            "--output", str(output_path),
            "--evidence-mode", evidence_mode]
    if instance_id:
        args += ["--instance-id", instance_id]
    if receipt:
        args += ["--receipt", receipt]
    if backend:
        args += ["--backend", backend]
    if backend_version:
        args += ["--backend-version", backend_version]
    rc, out, err = _run_cli(archive_script, args)
    if rc != 0:
        _err(f"complete-invocation failed (invocation_id={invocation_id}, rc={rc}): {out or err}")
    return rc


def _archive_recover(archive_script: Path, active_dir: Path, invocation_id: str, *,
                     status: str, failure_reason_code: str, failure_detail: str | None,
                     instance_id: str | None) -> int:
    """Run recover-invocation. Used on ocsr dispatch failure / watchdog timeout."""
    args = ["recover-invocation", str(active_dir), invocation_id,
            "--status", status,
            "--failure-reason-code", failure_reason_code]
    if failure_detail:
        args += ["--failure-detail", failure_detail]
    if instance_id:
        args += ["--instance-id", instance_id]
    rc, out, err = _run_cli(archive_script, args)
    if rc != 0:
        _err(f"recover-invocation failed (rc={rc}): {out or err}")
    return rc


def _extract_ocsr_instance_id(ledger_path: Path, label: str, model: str,
                              prompt_file: str) -> str:
    """Read ocsr-dispatch-ledger.jsonl and return the batch_id of the most recent
    `launched` event matching (label, model, prompt_file).

    Per design.md §3.3, this batch_id is used as the archive Contract
    `--instance-id` value — a non-constraining correlation handle (evidence_level
    is `configured`, so instance_id is not validated as host-evidence; it just
    lets an auditor trace back from an archive event to the ocsr dispatch batch).

    Returns the batch_id string, or a synthesized fallback
    `ocsr-unknown-<uuid8>` if the ledger can't be parsed or no match found.
    The fallback is honest (clearly labelled unknown) rather than empty.
    """
    fallback = f"ocsr-unknown-{uuid.uuid4().hex[:8]}"
    if not ledger_path.is_file():
        return fallback
    matches: list[tuple[str, str]] = []  # (ts, batch_id)
    try:
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("event") != "launched":
                continue
            if (row.get("label") == label and row.get("model") == model
                    and row.get("prompt_file") == prompt_file):
                ts = row.get("ts", "")
                bid = row.get("batch_id") or fallback
                matches.append((ts, bid))
    except OSError:
        return fallback
    if not matches:
        return fallback
    matches.sort()
    return matches[-1][1]


def _detect_opencode_version() -> str:
    """Best-effort detection of opencode CLI version, for archive backend_version."""
    try:
        proc = subprocess.run(
            ["opencode", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        text = (proc.stdout or proc.stderr).strip()
        # opencode --version output is typically a single line like "opencode 1.18.3"
        # or a JSON-ish blob; we take the first whitespace-trimmed line.
        return text.splitlines()[0][:80] if text else "unknown"
    except Exception:
        return "unknown"


def _map_ocsr_outcome(ocsr_rc: int, output_path: Path, error_log: Path | None) -> tuple[str, str, bool]:
    """Map ocsr dispatch outcome to (recover_status, failure_reason_code, pre_execution).

    pre_execution semantics (budget_gate.py + archive capture.py):
      true  = model was never actually called (Start-Process / launcher error before
              opencode run executed)
      false = model was invoked (default for any path where Start-Process succeeded)

    ocsr_dispatch exit codes:
      0            = success (all workers landed) — should not reach recover path
      1            = watchdog timeout / not-landed
      3            = EXIT_PATH_COLLISION (overwrote existing files)
      other        = various errors
    """
    # Watchdog timeout: model was invoked but stalled past deadline → not pre_execution
    if ocsr_rc == 1:
        return "timeout", "timeout", False
    # Path collision: model may have written somewhere unexpected; treat as backend error
    # post-execution (model was invoked).
    if ocsr_rc == 3:
        return "failed", "backend-error", False
    # Launcher-level errors (Start-Process failed) typically surface as ocsr rc=0 with
    # error.log present and no output — we treat as pre_execution since the launcher
    # never started opencode.
    if error_log is not None and error_log.is_file():
        return "failed", "backend-error", True
    # Generic backend error (post Start-Process): model was invoked.
    return "failed", "backend-error", False


def cmd_config_init(args) -> int:
    """Write an initial `_budget-state.json` to the converge active dir.

    budget_gate.py auto-creates a default state on first reserve if absent, but
    ultraverge mode requires `max_blind_rechecks=2` override *before* any reserve
    (per SKILL.md §Ultraverge: "纯 orchestrator 行为、零代码"). This subcommand
    encapsulates that init for reproducibility — orchestrator-side JSON writes are
    easy to get wrong (typo in key, wrong type) and budget_gate fail-closes on
    schema violations, so a typed CLI is safer than hand-editing.

    Idempotent: if the state file already exists, returns FAIL_CLOSED without
    modification (use --force to overwrite). Mirrors budget_gate bind's
    `already_bound` semantics: re-init in error smells like state loss.
    """
    active_dir = Path(args.converge_active).resolve()
    if not active_dir.is_dir():
        _err(f"active_dir not a directory: {active_dir}")
        return EXIT_INTERNAL
    state_path = active_dir / "_budget-state.json"
    if state_path.exists() and not args.force:
        _err(f"_budget-state.json already exists at {state_path}; use --force to overwrite")
        return EXIT_FAIL_CLOSED

    # Build config from defaults + overrides. We deliberately do NOT call
    # budget_gate.read_state() to avoid importing the gate module; we just write
    # the JSON the gate expects (its read_state will normalize missing keys).
    config: dict = {}
    if args.max_outer_loops is not None:
        config["max_outer_loops"] = args.max_outer_loops
    if args.max_blind_rechecks is not None:
        config["max_blind_rechecks"] = args.max_blind_rechecks
    if args.ultraverge_min_reviewers is not None:
        config["ultraverge_min_reviewers"] = args.ultraverge_min_reviewers
    if args.max_inner_loops is not None:
        config["max_inner_loops"] = args.max_inner_loops
    if args.mode == "ultraverge":
        # Ultraverge override per SKILL.md §Ultraverge (zero-code orchestrator
        # behavior, but typed here so it can't be typo'd):
        config.setdefault("max_blind_rechecks", 2)
    state = {
        "config": config,
        "extensions": [],
        "fsm": {"mode": args.mode, "severities": {}},
    }
    # LF-pinned write (mirrors budget_gate.write_state): _budget-state.json is
    # a root-fixed, manifest-hashed file that must stay byte-identical to what
    # Git checks out under `.gitattributes: * text=auto eol=lf`.
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n",
    )
    print(f"[config-init] wrote {state_path} (mode={args.mode}, config={config})")
    return EXIT_PROCEED


def cmd_summary(args) -> int:
    """Pass-through to budget_gate.py summary, for orchestrator convenience."""
    gate_script = Path(args.converge_scripts).resolve() / "budget_gate.py"
    if not gate_script.is_file():
        _err(f"budget_gate.py not found at {gate_script}")
        return EXIT_INTERNAL
    rc, out, err = _run_cli(gate_script, ["summary", "--active-dir", str(args.converge_active)])
    print(out)
    if rc != 0:
        _err(err)
    return rc


def cmd_dispatch(args) -> int:
    """The main five-step atomic Spawn: reserve → begin → dispatch → complete/recover → settle."""
    active_dir = Path(args.converge_active).resolve()
    scripts_dir = Path(args.converge_scripts).resolve()
    archive_script = scripts_dir / "archive_convergence.py"
    gate_script = scripts_dir / "budget_gate.py"
    ocsr_script = Path(args.ocsr_dispatch).resolve()
    prompt_path = Path(args.prompt).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_path = output_dir / args.output_name

    for required in (archive_script, gate_script, ocsr_script, prompt_path):
        if not required.is_file():
            _err(f"required file not found: {required}")
            return EXIT_INTERNAL

    if not active_dir.is_dir():
        _err(f"active_dir not a directory: {active_dir}")
        return EXIT_INTERNAL

    try:
        requested_provider, requested_model = _parse_provider_model(args.model)
    except ValueError as e:
        _err(str(e))
        return EXIT_INTERNAL

    backend = args.backend or "opencode"
    backend_version = args.backend_version or _detect_opencode_version()
    evidence_mode = args.evidence_mode

    # Step 1: reserve (or reuse an externally-provided reservation id)
    reservation_id = args.reserved_reservation_id
    if reservation_id:
        # Caller asserts they already reserved; we trust this (no re-reserve).
        # But we still record the budget gate's absence in our state by skipping.
        _err(f"[adapter] using externally-reserved id: {reservation_id}")
    else:
        rc, msg = _gate_reserve(gate_script, active_dir, args.role, args.round,
                                None, args.tier)
        if rc == 0 and msg:
            reservation_id = msg
        elif rc in (10, 11, 12, 13, 14):
            _err(f"[adapter] budget_gate reserve BLOCK: {msg}")
            return EXIT_BLOCK
        elif rc == 20:
            _err(f"[adapter] budget_gate reserve MODE_SWITCH_REQUIRED: {msg}")
            return EXIT_BLOCK
        elif rc in (21, 22):
            _err(f"[adapter] budget_gate reserve DENY: {msg}")
            return EXIT_DENY
        elif rc == 30:
            _err(f"[adapter] budget_gate reserve FAIL_CLOSED: {msg}")
            return EXIT_FAIL_CLOSED
        else:
            _err(f"[adapter] budget_gate reserve unexpected rc={rc}: {msg}")
            return EXIT_INTERNAL

    # Step 2: begin-invocation
    begin_rc, begin_json = _archive_begin(
        archive_script, active_dir,
        kind="spawn", role=args.role, phase=args.phase,
        round_number=args.round, attempt=args.attempt,
        reservation_id=reservation_id,
        requested_provider=requested_provider,
        requested_model=requested_model,
        prompt_path=prompt_path, evidence_mode=evidence_mode,
    )
    if begin_rc != 0 or begin_json is None:
        # Begin failed before invocation started → pre_execution cancel
        _gate_settle(gate_script, active_dir, reservation_id,
                     result="cancelled", pre_execution=True,
                     reason=f"begin-invocation failed rc={begin_rc}")
        return begin_rc if begin_rc else EXIT_ARCHIVE_CLI

    invocation_id = begin_json.get("invocation_id")
    if not invocation_id:
        _err(f"begin-invocation returned no invocation_id: {begin_json}")
        return EXIT_ARCHIVE_CLI

    # Step 3: ocsr_dispatch.py dispatch (blocking --watch)
    worker_arg = f"{prompt_path}|{args.model}|{args.label}"
    ocsr_args = [
        "dispatch",
        "--worker", worker_arg,
        "--output-dir", str(output_dir),
        "--output-pattern", args.output_name,
        "--ledger-dir", str(active_dir),  # auto-completes converge ledger per ocsr SKILL.md:66
        "--harness", args.harness,
        "--meta", f"task_id={args.task_id or 'ocsr-adapter'}",
        "--meta", f"role={args.role}",
        "--meta", f"scope={args.scope}",
        "--meta", f"converge-invocation-id={invocation_id}",
        "--meta", f"converge-reservation-id={reservation_id}",
    ]
    if args.watch:
        ocsr_args += ["--watch", "--timeout", str(args.timeout), "--progress"]
    ocsr_proc = subprocess.run(
        [sys.executable, str(ocsr_script), *ocsr_args],
        capture_output=False, text=True, encoding="utf-8",
    )
    ocsr_rc = ocsr_proc.returncode

    # Step 4: complete or recover based on whether product landed
    ledger_path = active_dir / "ocsr-dispatch-ledger.jsonl"
    instance_id = _extract_ocsr_instance_id(
        ledger_path, args.label, args.model, str(prompt_path))
    receipt = f"ocsr-dispatch-ledger.jsonl:{reservation_id}"

    if output_path.is_file() and output_path.stat().st_size > 0:
        # Happy path: product landed
        complete_rc = _archive_complete(
            archive_script, active_dir, invocation_id,
            status="succeeded", instance_id=instance_id, receipt=receipt,
            backend=backend, backend_version=backend_version,
            output_path=output_path, evidence_mode=evidence_mode,
        )
        settle_result = "succeeded"
        settle_rc = _gate_settle(gate_script, active_dir, reservation_id,
                                  result="succeeded", instance_id=instance_id)
        if complete_rc != 0:
            _err(f"[adapter] complete-invocation failed (invocation_id={invocation_id}, rc={complete_rc}) but product landed; "
                 "settle recorded as succeeded since model was actually called. "
                 "Archive will need reconciliation before archive-time check.")
            return complete_rc
        if settle_rc != 0:
            _err(f"[adapter] settle succeeded failed rc={settle_rc}")
            return settle_rc
        print(f"[adapter] OK invocation={invocation_id} reservation={reservation_id} "
              f"instance={instance_id} output={output_path}")
        return EXIT_PROCEED

    # Failure path: product did not land
    # Locate the work_dir's error.log (ocsr creates batch_dir/label/error.log)
    # Best-effort: walk ~/.ocsr or $TEMP for ocsr_dispatch_<batch>/error.log — but
    # this is fragile. Use _map_ocsr_outcome heuristics on exit code + work_dir probe.
    error_log = None
    try:
        work_root = Path(os.environ.get("TEMP", "/tmp"))
        candidates = sorted(work_root.glob(f"ocsr_dispatch_*/{args.label}/error.log"),
                            key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            error_log = candidates[0]
    except OSError:
        pass

    status, failure_reason, pre_exec = _map_ocsr_outcome(ocsr_rc, output_path, error_log)
    failure_detail = f"ocsr rc={ocsr_rc}; output={output_path} missing or empty"
    if error_log and error_log.is_file():
        try:
            failure_detail += f"; error.log: {error_log.read_text(encoding='utf-8', errors='replace')[:200]}"
        except OSError:
            pass

    recover_rc = _archive_recover(
        archive_script, active_dir, invocation_id,
        status=status, failure_reason_code=failure_reason,
        failure_detail=failure_detail, instance_id=instance_id,
    )
    # Gate settle has only 3 results (succeeded/failed/cancelled); archive has 4
    # terminal statuses. Mapping:
    #   archive succeeded  → gate succeeded
    #   archive failed     → gate failed
    #   archive timeout    → gate failed (closest; gate has no timeout, and timeout
    #                                  is a real post-invocation failure mode where
    #                                  the model was called — pre_execution=false)
    #   archive cancelled  → gate cancelled
    # forward-looking: cancelled not yet emitted by _map_ocsr_outcome, retained for completeness
    settle_result = "cancelled" if status == "cancelled" else "failed"
    settle_rc = _gate_settle(gate_script, active_dir, reservation_id,
                              result=settle_result, instance_id=instance_id,
                              pre_execution=pre_exec, reason=failure_reason)
    if recover_rc != 0:
        return recover_rc
    if settle_rc != 0:
        return settle_rc
    _err(f"[adapter] recover recorded: invocation={invocation_id} status={status} "
         f"reason={failure_reason} pre_execution={pre_exec}")
    return EXIT_OCSR_NO_PRODUCT


def cmd_selftest(args) -> int:
    """End-to-end self-check: write a trivial prompt, dispatch via the adapter,
    verify product landed AND that the converge active dir now has an
    invocation-started + invocation-terminal event pair."""
    work_dir = Path(args.work_dir or os.environ.get("TEMP", "/tmp")) / "ocsr_adapter_selftest"
    work_dir.mkdir(parents=True, exist_ok=True)
    active_dir = work_dir / "active"
    active_dir.mkdir(exist_ok=True)
    output_dir = work_dir / "output"
    output_dir.mkdir(exist_ok=True)

    scripts_dir = Path(args.converge_scripts).resolve()
    if not (scripts_dir / "archive_convergence.py").is_file():
        _err(f"converge-scripts dir invalid: {scripts_dir}")
        return EXIT_INTERNAL

    output_name = "selftest-marker.txt"
    output_path = output_dir / output_name
    output_path.unlink(missing_ok=True)

    prompt_path = work_dir / "prompt.txt"
    prompt_path.write_text(
        f"【任务】用 Write 工具写入：{output_path.as_posix()}\n"
        f"内容：adapter-selftest-ok\n"
        f"【输出】{output_path.as_posix()}\n"
        f"【边界与禁区】除上述输出外禁写；不依赖 stdout。\n"
        f"【执行证据】回复含路径 + 字节数。\n",
        encoding="utf-8",
    )

    adapter_args = [
        "dispatch",
        "--converge-active", str(active_dir),
        "--converge-scripts", str(scripts_dir),
        "--ocsr-dispatch", str(Path(args.ocsr_dispatch).resolve()),
        "--role", "executor",
        "--phase", "selftest",
        "--attempt", "1",
        "--prompt", str(prompt_path),
        "--model", args.model or "deepseek/deepseek-v4-flash",
        "--label", "adapter-selftest",
        "--output-dir", str(output_dir),
        "--output-name", output_name,
        "--watch", "--timeout", "5",
    ]
    rc = cmd_dispatch(argparse.Namespace(**{
        **{k: getattr(args, k) for k in vars(args)},
        **dict(reserved_reservation_id=None, round=None, attempt=1,
               harness="adapter-selftest", scope="none",
               task_id="adapter-selftest", evidence_mode="metadata-only",
               backend=None, backend_version=None,
               converge_active=str(active_dir),
               converge_scripts=str(scripts_dir),
               ocsr_dispatch=str(Path(args.ocsr_dispatch).resolve()),
               role="executor", phase="selftest",
               prompt=str(prompt_path),
               model=args.model or "deepseek/deepseek-v4-flash",
               label="adapter-selftest",
               output_dir=str(output_dir), output_name=output_name,
               watch=True, timeout=5, tier="auditable-only"),
    }))
    if rc != 0:
        print(f"[selftest] FAIL adapter dispatch rc={rc}")
        return rc

    # Verify event graph
    events_dir = active_dir / "evidence" / "events"
    if not events_dir.is_dir():
        print(f"[selftest] FAIL no evidence/events dir at {events_dir}")
        return EXIT_INTERNAL
    events = sorted(events_dir.glob("*.json"))
    if len(events) < 2:
        print(f"[selftest] FAIL expected ≥2 events, got {len(events)}")
        return EXIT_INTERNAL
    has_started = has_terminal = False
    for ev in events:
        try:
            data = json.loads(ev.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("event_type") == "invocation-started":
            has_started = True
        elif data.get("event_type") == "invocation-terminal":
            has_terminal = True
    if not (has_started and has_terminal):
        print(f"[selftest] FAIL event pair incomplete: started={has_started} terminal={has_terminal}")
        return EXIT_INTERNAL
    content = output_path.read_text(encoding="utf-8").strip()
    if content != "adapter-selftest-ok":
        print(f"[selftest] FAIL content mismatch: '{content[:50]}'")
        return EXIT_INTERNAL
    print(f"[selftest] OK events={len(events)} output={output_path} ({output_path.stat().st_size}B)")
    return EXIT_PROCEED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ocsr_spawn_adapter",
        description="Wrap ocsr_dispatch as a converge Archive Contract v1 Spawn implementation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    d = sub.add_parser("dispatch", help="Atomic reserve→begin→dispatch→complete/recover→settle.")
    d.add_argument("--converge-active", required=True,
                   help="converge active dir (contains gate-ledger.jsonl, _budget-state.json, evidence/).")
    d.add_argument("--converge-scripts", required=True,
                   help="converge scripts dir (contains archive_convergence.py, budget_gate.py).")
    d.add_argument("--ocsr-dispatch", required=True,
                   help="path to ocsr/scripts/ocsr_dispatch.py.")
    d.add_argument("--role", required=True,
                   help="budget_gate role (outer-reviewer | blind-reviewer | ultraverge-initial | executor | arbiter | design-reviewer | ...).")
    d.add_argument("--phase", required=True, help="converge phase name (e.g. reviewer-round-1).")
    d.add_argument("--round", type=int, default=None,
                   help="round number (null/0 = Round 0; canonical_round normalizes 0→null).")
    d.add_argument("--attempt", type=int, required=True, help="attempt index (≥1).")
    d.add_argument("--prompt", required=True, help="absolute path to self-contained prompt file.")
    d.add_argument("--model", required=True, help="opencode -m model id (provider/model).")
    d.add_argument("--label", required=True, help="ocsr --worker LABEL.")
    d.add_argument("--output-dir", required=True, help="product output dir.")
    d.add_argument("--output-name", required=True, help="product filename (no path).")
    d.add_argument("--reserved-reservation-id",
                   help="if set, skip reserve (caller asserts they already reserved).")
    d.add_argument("--watch", action="store_true", help="ocsr --watch (blocking product wait).")
    d.add_argument("--timeout", type=int, default=15, help="ocsr watchdog minutes (default 15).")
    d.add_argument("--tier", default="auditable-only", choices=["auditable-only", "enforced"])
    d.add_argument("--evidence-mode", default="metadata-only",
                   choices=["metadata-only", "redacted", "exact"])
    d.add_argument("--harness", default="ocsr-adapter", help="ocsr --harness tag.")
    d.add_argument("--backend", default=None, help="archive backend name (default: opencode).")
    d.add_argument("--backend-version", default=None,
                   help="archive backend version (default: auto-detect via opencode --version).")
    d.add_argument("--scope", default="none",
                   help="ocsr --meta scope value (matches budget_gate ROLE_CONSUMES).")
    d.add_argument("--task-id", default=None, help="ocsr --meta task_id value.")
    d.set_defaults(func=cmd_dispatch)

    st = sub.add_parser("selftest", help="End-to-end self-check with a trivial prompt.")
    st.add_argument("--converge-scripts", required=True)
    st.add_argument("--ocsr-dispatch", required=True)
    st.add_argument("--model", default=None)
    st.add_argument("--work-dir", default=None)
    st.set_defaults(func=cmd_selftest)

    ci = sub.add_parser("config-init",
                        help="Write initial _budget-state.json (idempotent; --force to overwrite).")
    ci.add_argument("--converge-active", required=True)
    ci.add_argument("--mode", default="standard", choices=["standard", "ultraverge"],
                    help="FSM mode; 'ultraverge' auto-applies max_blind_rechecks=2 override.")
    ci.add_argument("--max-outer-loops", type=int, default=None)
    ci.add_argument("--max-blind-rechecks", type=int, default=None)
    ci.add_argument("--ultraverge-min-reviewers", type=int, default=None)
    ci.add_argument("--max-inner-loops", type=int, default=None)
    ci.add_argument("--force", action="store_true",
                    help="Overwrite an existing _budget-state.json.")
    ci.set_defaults(func=cmd_config_init)

    sm = sub.add_parser("summary",
                        help="Pass-through to budget_gate.py summary for this active dir.")
    sm.add_argument("--converge-active", required=True)
    sm.add_argument("--converge-scripts", required=True)
    sm.set_defaults(func=cmd_summary)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
