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
    6  = 派发前路径一致性 preflight 拒绝（prompt 未声明 --output-name）
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

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import budget_gate  # noqa: E402


EXIT_PROCEED = 0
EXIT_ARCHIVE_CLI = 3
EXIT_OCSR_NO_PRODUCT = 5
EXIT_PROMPT_OUTPUT_MISMATCH = 6
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
    """Run budget_gate.py reserve. Returns (exit_code, rid_or_message).

    D3/O7：本适配器属编排路径 → 注入 `--orchest-managed` 来源声明（满足 budget_gate
    的来源声明门；非手工裸转移）。
    """
    args = ["reserve", "--active-dir", str(active_dir), "--role", role, "--tier", tier,
            "--orchest-managed"]
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
    # D3/O7：编排路径注入 --orchest-managed 来源声明。
    args = ["settle", "--active-dir", str(active_dir),
            "--reservation-id", reservation_id, "--result", result,
            "--orchest-managed"]
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
                              prompt_file: str,
                              converge_invocation_id: str | None = None) -> str:
    """Read ocsr-dispatch-ledger.jsonl and return the batch_id of the most recent
    `launched` event.

    Matching priority:
      1. If `converge_invocation_id` is non-empty, scan for launched events
         where `row.get("converge_invocation_id") == converge_invocation_id`
         and return the batch_id from the most recent match.
      2. Legacy fallback: match by (label, model, prompt_file) tuple.
      3. Final fallback: return `ocsr-unknown-<uuid8>`.

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
    corr_match: tuple[str, str] | None = None  # (ts, batch_id)
    tuple_match: tuple[str, str] | None = None  # (ts, batch_id)
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
            ts = row.get("ts", "")
            bid = row.get("batch_id") or fallback
            # Priority 1: correlation-key-first matching
            if converge_invocation_id:
                if row.get("converge_invocation_id") == converge_invocation_id:
                    if corr_match is None or ts > corr_match[0]:
                        corr_match = (ts, bid)
            # Priority 2: legacy tuple fallback (always tried)
            if (row.get("label") == label and row.get("model") == model
                    and row.get("prompt_file") == prompt_file):
                if tuple_match is None or ts > tuple_match[0]:
                    tuple_match = (ts, bid)
    except OSError:
        return fallback
    if corr_match:
        return corr_match[1]
    if tuple_match:
        return tuple_match[1]
    return fallback


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


def _ensure_te_companion(gate_script: Path, active_dir: Path,
                         role_reservation_id: str, tier: str) -> bool:
    """D10: Ensure a task-envelope companion exists for a pre-reserved role.

    When --reserved-reservation-id is provided, the adapter bypasses _gate_reserve
    (which handles atomic companion pairing). This function retroactively creates
    the companion via the gate's --companion-for mechanism.

    Returns True if companion was created or already exists, False on failure.
    """
    try:
        state = budget_gate.read_state(active_dir)
    except budget_gate.FailClosed:
        return True  # Can't read state → skip companion (A8: unconfigured = no-op)
    if not budget_gate._task_envelope_configured(state):
        return True  # No envelope configured → no companion needed (A8)

    # Check if companion already exists (forward or reverse lookup)
    events = budget_gate.read_ledger(active_dir)
    for ev in events:
        if (ev.get("event") == "reserved"
                and ev.get("reservation_id") == role_reservation_id
                and ev.get("companion_reservation_id") is not None):
            return True  # Already has companion (forward link on role)
    # Reverse lookup: companion may reference this role without the role
    # carrying a forward reference (append-only pre-reserved path)
    for ev in events:
        if (ev.get("event") == "reserved"
                and ev.get("companion_reservation_id") == role_reservation_id):
            return True  # Already has companion (reverse link from companion)

    # Create companion via gate CLI (D3/O7: orchestration path → --orchest-managed)
    args = ["reserve", "--active-dir", str(active_dir),
            "--role", "task-envelope", "--tier", tier,
            "--companion-for", role_reservation_id, "--orchest-managed"]
    rc, out, err = _run_cli(gate_script, args)
    if rc == 0 and out.startswith("PROCEED:"):
        return True
    if "companion_already_exists" in (out or ""):
        return True  # Idempotent
    _err(f"[adapter] companion creation failed (rc={rc}): {out or err}")
    return False


def _map_ocsr_outcome(ocsr_rc: int, output_path: Path, error_log: Path | None,
                      *, determinable: bool = True) -> tuple[str, str, bool]:
    """Map ocsr dispatch outcome to (recover_status, failure_reason_code, pre_execution).

    pre_execution semantics (budget_gate.py + archive capture.py):
      true  = model was never actually called (Start-Process / launcher error before
              opencode run executed)
      false = model was invoked (default for any path where Start-Process succeeded)

    `ocsr_dispatch.py dispatch --watch` exit-code contract — the single source of truth
    is the ocsr repo's `refs/dispatch-patterns.md` §退出码契约:

      0 = every worker landed (product exists, non-zero bytes)
      1 = watchdog timeout (a worker hit its deadline unsettled)
      2 = deterministic failure (launcher error / opencode non-zero /
          **opencode exited 0 but the expected product never landed**)
      3 = path collision (pre/post snapshot shows an existing file was overwritten)

      mixed-outcome priority: 3 > 1 > 2 > 0

    Exit code 2 is new in 2026-08. Before it existed, `--watch` returned **0** even when
    a worker failed, so callers could not distinguish success from failure by exit code —
    this adapter was written under that older contract. Two consequences were corrected
    when wiring the new one:

      1. Launcher errors no longer surface as `rc=0 + error.log`; they surface as
         `rc=2 + error.log`. `error.log` presence stays the pre_execution discriminator,
         because rc=2 covers *both* the pre-execution launcher error and the
         post-execution "opencode ran but produced nothing" case.
      2. The caller must not decide success from the product alone (see `cmd_dispatch`).

    `determinable` (2026-09 fix): the caller locates the batch's ocsr work_dir (from the
    dispatch ledger's `launched.work_dir`, or a best-effort TEMP glob). When the work_dir
    itself cannot be located, the presence/absence of `error.log` is unknowable and the
    classifier must fail conservatively toward `pre_execution=True` — the historical bug
    was an actual pre-execution failure (e.g. model-whitelist rejection) recorded as
    `false`. When the work_dir *is* located, a missing error.log is real evidence the model
    ran, so `false` is used.
    """
    # Watchdog timeout: model was invoked but stalled past deadline → not pre_execution
    if ocsr_rc == 1:
        return "timeout", "timeout", False
    # Path collision: the batch overwrote pre-existing files. The model *was* invoked;
    # whether or not this worker's own product landed, the batch is not a clean success.
    if ocsr_rc == 3:
        return "failed", "backend-error", False
    # rc=2 (deterministic failure) and any unexpected non-zero code: `error.log` is the
    # discriminator between "launcher never started opencode" (pre_execution) and
    # "opencode ran and failed / wrote nothing" (post-execution).
    if error_log is not None and error_log.is_file():
        return "failed", "backend-error", True
    if not determinable:
        # No locatable work_dir → cannot prove error.log absence → conservative pre_execution.
        return "failed", "backend-error", True
    return "failed", "backend-error", False


def _prompt_declares_output(prompt_path: Path, output_name: str) -> bool:
    """Path-consistency preflight predicate: does the prompt text name the product file?

    Two 2026-09 incidents (blind-recheck-3.md and design-review.md overwritten) had the
    same root cause: the prompt's 【输出】 path and the adapter's `--output-name` disagreed,
    so the worker wrote under the prompt's name while ocsr watched the other. A prompt that
    does not contain the expected filename cannot be dispatched safely.
    """
    try:
        text = prompt_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(output_name) and output_name in text


def _find_launched_row(ledger_path: Path, label: str, model: str, prompt_file: str,
                       invocation_id: str | None) -> dict | None:
    """Return the most recent `launched` ledger row for this batch, or None.

    Matching priority mirrors `_extract_ocsr_instance_id`:
      1. `converge_invocation_id` equality (correlation-key-first).
      2. Legacy (label, model, prompt_file) tuple fallback.
    """
    if not ledger_path.is_file():
        return None
    corr_match: tuple[str, dict] | None = None
    tuple_match: tuple[str, dict] | None = None
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
            ts = row.get("ts", "")
            if invocation_id and row.get("converge_invocation_id") == invocation_id:
                if corr_match is None or ts > corr_match[0]:
                    corr_match = (ts, row)
            if (row.get("label") == label and row.get("model") == model
                    and row.get("prompt_file") == prompt_file):
                if tuple_match is None or ts > tuple_match[0]:
                    tuple_match = (ts, row)
    except OSError:
        return None
    if corr_match:
        return corr_match[1]
    if tuple_match:
        return tuple_match[1]
    return None


def _locate_error_evidence(ledger_path: Path, label: str, model: str, prompt_file: str,
                           invocation_id: str | None) -> tuple[Path | None, bool]:
    """Locate the batch's ocsr work_dir error.log and report whether that was determinable.

    Returns `(error_log_or_None, determinable)`:
      - work_dir found in the launched ledger row → determinable=True; error.log is the
        file iff it actually exists (absence is then real post-execution evidence);
      - work_dir not found → best-effort TEMP glob fallback; a hit is determinable=True,
        a miss is determinable=False (pre_execution cannot be decided).
    """
    row = _find_launched_row(ledger_path, label, model, prompt_file, invocation_id)
    work_dir_value = row.get("work_dir") if row else None
    if isinstance(work_dir_value, str) and work_dir_value:
        error_log = Path(work_dir_value) / "error.log"
        return (error_log if error_log.is_file() else None), True
    # Legacy fallback: TEMP glob (the pre-2026-09 probe).
    try:
        work_root = Path(os.environ.get("TEMP", "/tmp"))
        candidates = sorted(work_root.glob(f"ocsr_dispatch_*/{label}/error.log"),
                            key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            return candidates[0], True
    except OSError:
        pass
    return None, False


def _path_anomaly_marked(ledger_path: Path, invocation_id: str | None, label: str,
                         model: str, prompt_file: str) -> list[str]:
    """Collect this batch's `path_anomaly` marks (overwritten ∪ unexpected_new).

    ocsr's `path_anomaly` row carries no batch_id, so rows are scoped by their position:
    every matching row appearing at or after this batch's `launched` row. Names are
    output-dir-relative basenames as written by `ocsr_dispatch._collision_report`.
    """
    if not ledger_path.is_file():
        return []
    try:
        rows: list[dict] = []
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    start_idx = None
    for i, row in enumerate(rows):
        if row.get("event") != "launched":
            continue
        if invocation_id and row.get("converge_invocation_id") == invocation_id:
            start_idx = i
        elif (row.get("label") == label and row.get("model") == model
                and row.get("prompt_file") == prompt_file):
            start_idx = i
    if start_idx is None:
        return []
    marked: list[str] = []
    for row in rows[start_idx:]:
        if row.get("event") != "path_anomaly":
            continue
        for key in ("overwritten", "unexpected_new"):
            values = row.get(key)
            if isinstance(values, list):
                marked.extend(v for v in values if isinstance(v, str) and v)
    return marked


def _canon_path(path: Path) -> str:
    try:
        return path.resolve().as_posix().casefold()
    except OSError:
        return str(path).replace("\\", "/").casefold()


def _in_place_edit_accepted(marked: list[str], declared: list[str], output_dir: Path) -> bool:
    """True iff every path ocsr flagged is explicitly declared via --in-place-edit.

    Marked names are output-dir-relative; declared values may be relative or absolute.
    Declared relative values are accepted against both the output dir and the cwd.
    """
    if not marked or not declared:
        return False
    marked_norm = {_canon_path(output_dir / name) for name in marked}
    declared_norm: set[str] = set()
    for value in declared:
        candidate = Path(value)
        if candidate.is_absolute():
            declared_norm.add(_canon_path(candidate))
        else:
            declared_norm.add(_canon_path(output_dir / candidate))
            declared_norm.add(_canon_path(Path.cwd() / candidate))
    return bool(marked_norm) and marked_norm <= declared_norm


def _finish_success(archive_script: Path, active_dir: Path, gate_script: Path, *,
                    invocation_id: str, reservation_id: str, instance_id: str | None,
                    receipt: str, backend: str | None, backend_version: str | None,
                    output_path: Path, evidence_mode: str) -> int:
    """Complete-invocation(succeeded) + settle(succeeded); shared by happy and accepted paths."""
    complete_rc = _archive_complete(
        archive_script, active_dir, invocation_id,
        status="succeeded", instance_id=instance_id, receipt=receipt,
        backend=backend, backend_version=backend_version,
        output_path=output_path, evidence_mode=evidence_mode,
    )
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


def cmd_config_init(args) -> int:
    """Write an initial `_budget-state.json` to the converge active dir.

    Delegates to the shared budget_gate.initialize_state() (plan D3):
    - Empty state → creates standard/ultraverge mode with explicit config.
    - Existing state → validates complete state; equal values are idempotent no-op;
      conflicting values fail closed (--force overrides).
    - Standard and ultraverge share the same default ceilings (no mode overlay).
    """
    import budget_gate

    active_dir = Path(args.converge_active).resolve()
    if not active_dir.is_dir():
        _err(f"active_dir not a directory: {active_dir}")
        return EXIT_INTERNAL

    config: dict = {}
    if args.max_outer_loops is not None:
        config["max_outer_loops"] = args.max_outer_loops
    if args.max_blind_rechecks is not None:
        config["max_blind_rechecks"] = args.max_blind_rechecks
    if args.ultraverge_min_reviewers is not None:
        config["ultraverge_min_reviewers"] = args.ultraverge_min_reviewers
    if args.max_inner_loops is not None:
        config["max_inner_loops"] = args.max_inner_loops
    for attr in ("task_tier", "task_envelope_initial", "task_envelope_cap"):
        val = getattr(args, attr, None)
        if val is not None:
            config[attr] = val

    try:
        state = budget_gate.initialize_state(
            active_dir, mode=args.mode, config=config, force=args.force)
    except budget_gate.FailClosed as e:
        _err(f"FAIL_CLOSED:{e.reason}")
        return EXIT_FAIL_CLOSED
    # Phase 5b: initialization disclosure
    if budget_gate._task_envelope_configured(state):
        ceilings = {s: budget_gate.ceiling(state, s)
                    for s in ("outer", "blind", "ultraverge", "total")}
        te_initial = budget_gate._task_envelope_initial(state)
        te_cap = budget_gate._task_envelope_hard_cap(state)
        print(f"[init] local ceilings: {ceilings}")
        print(f"[init] task-envelope: initial={te_initial}, cap={te_cap}")
        print("[init] quality_path_guaranteed: false")
        print("[init] envelope-may-block-before-local-ceiling: true")
    print(f"[config-init] OK (mode={args.mode}, config={config})")
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

    # Step 0: path-consistency preflight (before any ledger write / reservation).
    # The prompt's declared output path and --output-name must agree; when they diverged,
    # workers wrote under the prompt's name while ocsr watched --output-name, silently
    # overwriting a same-directory artifact (two 2026-09 incidents). Refuse to dispatch
    # unless the prompt text names the product file, with an explicit escape hatch.
    skip_name_check = bool(getattr(args, "skip_output_name_check", False))
    if not _prompt_declares_output(prompt_path, args.output_name):
        if skip_name_check:
            _err(f"[adapter] WARN: prompt does not declare --output-name={args.output_name}; "
                 "continuing because --skip-output-name-check was passed.")
        else:
            _err("[adapter] REFUSE: dispatch path-consistency preflight failed — "
                 "--output-name is not named anywhere in the prompt text.")
            _err(f"[adapter]   prompt:                {prompt_path}")
            _err(f"[adapter]   output-name:           {args.output_name}")
            _err(f"[adapter]   expected output path:  {output_path}")
            _err("[adapter]   fix: make the prompt's 【输出】 path exactly match --output-name "
                 "(same variable), or pass --skip-output-name-check to override (not recommended).")
            _err("[adapter]   no ledger row written, no reservation issued.")
            return EXIT_PROMPT_OUTPUT_MISMATCH

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
        # D10: Ensure task-envelope companion exists for the pre-reserved role
        _ensure_te_companion(gate_script, active_dir, reservation_id, args.tier)
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
        ledger_path, args.label, args.model, str(prompt_path),
        converge_invocation_id=invocation_id)
    receipt = f"ocsr-dispatch-ledger.jsonl:{reservation_id}"

    product_landed = output_path.is_file() and output_path.stat().st_size > 0
    if product_landed and ocsr_rc == 0:
        # Happy path: product landed AND the dispatch itself reported clean success.
        #
        # Both conditions are required. The product alone is not sufficient evidence:
        # under the exit-code contract, rc=3 means the batch overwrote pre-existing files
        # — this worker's product may well be on disk while something *else* was
        # clobbered. Recording that as `succeeded` would let a path collision enter the
        # archive as a clean Spawn. Conversely rc alone is not sufficient either: ocsr can
        # return 0 when `--watch` was not requested, in which case no product recovery ran.
        return _finish_success(
            archive_script, active_dir, gate_script,
            invocation_id=invocation_id, reservation_id=reservation_id,
            instance_id=instance_id, receipt=receipt,
            backend=backend, backend_version=backend_version,
            output_path=output_path, evidence_mode=evidence_mode)

    # In-place-edit acceptance (2026-09): ocsr returns a path-class non-zero code (rc=3)
    # because the worker rewrote existing files. An operator may have explicitly declared
    # those files as permitted in-place edits via `--in-place-edit`. When the worker's own
    # product landed, the ledger's path_anomaly marks are exactly the declared set, and no
    # other marked path exists, reconcile the batch as a success. Partial declaration or a
    # missing product keeps the failure classification (fail-closed).
    in_place_edit = list(getattr(args, "in_place_edit", None) or [])
    if product_landed and ocsr_rc == 3 and in_place_edit:
        marked = _path_anomaly_marked(ledger_path, invocation_id, args.label,
                                      args.model, str(prompt_path))
        if marked and _in_place_edit_accepted(marked, in_place_edit, output_dir):
            print(f"WARN:in-place-edit-accepted:{','.join(marked)}")
            return _finish_success(
                archive_script, active_dir, gate_script,
                invocation_id=invocation_id, reservation_id=reservation_id,
                instance_id=instance_id, receipt=receipt,
                backend=backend, backend_version=backend_version,
                output_path=output_path, evidence_mode=evidence_mode)

    # Failure path: the product did not land, or the dispatch reported a non-zero code.
    # Locate the batch's ocsr work_dir from the dispatch ledger (authoritative) with a
    # TEMP-glob fallback; `error.log` presence is the pre_execution discriminator. When the
    # work_dir cannot be located, classification defaults conservatively to pre_execution
    # (see _map_ocsr_outcome) instead of asserting the model ran.
    error_log, error_determinable = _locate_error_evidence(
        ledger_path, args.label, args.model, str(prompt_path), invocation_id)

    status, failure_reason, pre_exec = _map_ocsr_outcome(
        ocsr_rc, output_path, error_log, determinable=error_determinable)
    if pre_exec and not (error_log and error_log.is_file()):
        _err("[adapter] WARN: pre_execution defaulted to true (ocsr work_dir / error.log "
             "not determinable); conservative classification per the pre_execution contract.")
    # State the product's real status. When a dispatch fails with the product *present*
    # (rc=3 path collision is the live case), a detail line reading "missing or empty"
    # would be a false statement in the permanent archive record.
    product_state = ("present but dispatch failed" if product_landed else "missing or empty")
    failure_detail = f"ocsr rc={ocsr_rc}; output={output_path} {product_state}"
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
               watch=True, timeout=5, tier="auditable-only",
               skip_output_name_check=False, in_place_edit=None),
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
    d.add_argument("--skip-output-name-check", action="store_true",
                   help="Escape hatch: bypass the preflight that requires the prompt text "
                        "to name --output-name. Prints WARN and continues.")
    d.add_argument("--in-place-edit", action="append", metavar="PATH", default=None,
                   help="Declare a file the worker is allowed to rewrite in place (repeatable). "
                        "A path-class non-zero ocsr result is reconciled as success only when "
                        "the product landed and every path_anomaly mark is declared.")
    d.add_argument("--watch", action="store_true", help="ocsr --watch (blocking product wait).")
    d.add_argument("--timeout", type=int, default=15, help="ocsr watchdog minutes (default 15).")
    d.add_argument("--tier", default="auditable-only", choices=["auditable-only", "enforced"])
    d.add_argument("--evidence-mode", default="metadata-only",
                   choices=["metadata-only", "redacted", "exact"],
                   help="证据模式（D1/O2 默认策略）：缺省 metadata-only；material / 终局"
                        "同字节绑定相关的轮由调用方显式传 exact。透传至 begin/complete。")
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
    ci.add_argument("--mode", default=None, choices=["standard", "ultraverge"],
                    help="FSM mode; both modes share the same default ceilings; omit to inherit.")
    ci.add_argument("--max-outer-loops", type=int, default=None)
    ci.add_argument("--max-blind-rechecks", type=int, default=None)
    ci.add_argument("--ultraverge-min-reviewers", type=int, default=None)
    ci.add_argument("--max-inner-loops", type=int, default=None)
    ci.add_argument("--task-tier", choices=list(budget_gate.TASK_TIERS.keys()), default=None,
                    help="Task-envelope tier (small/medium/feature/critical); makes the "
                         "governance-plan envelope gate satisfiable.")
    ci.add_argument("--task-envelope-initial", type=int, default=None)
    ci.add_argument("--task-envelope-cap", type=int, default=None)
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
