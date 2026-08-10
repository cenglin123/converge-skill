---
reviewer_model: xiaomi/mimo-v2.5-pro
verdict: 可执行
deterministic_check:
  test_archive_convergence: "38/38 passed (2.242s)"
  test_budget_gate: "50/50 passed (10.597s)"
  encoding_scan: "all 9 source files: BOM=false, CRLF=false (except test_budget_gate.py CRLF=true)"
  git_diff_check: "clean (no whitespace errors)"
  destructive_probe_scan: "none found (os.kill, TerminateProcess absent)"
  static_dead_code: "model.py:1003-1010 unreachable after return"
blocking_issues: []
suggestion_issues:
  - id: S1
    severity: low
    location: scripts/archive_contract/model.py:1003-1010
    description: >
      Dead code: lines 1003-1010 are unreachable (after return on line 1002 in
      check_archive). Appears to be leftover validation logic from a prior
      version of validate_event that was copy-pasted into the except block.
      No runtime effect.
    fix: Delete lines 1003-1010.
  - id: S2
    severity: low
    location: tests/test_budget_gate.py
    description: >
      File has CRLF line endings despite .gitattributes specifying `* text=auto eol=lf`.
      Git will normalize on commit but working-tree bytes differ from other source files.
    fix: Convert to LF with `python -c "f='tests/test_budget_gate.py'; open(f,'wb').write(open(f,'rb').read().replace(b'\r\n',b'\n'))"`.

rubric_scores:
  spec_alignment: 5
  threat_model_honesty: 5
  closure_completeness: 5
  error_diagnostics: 5
  test_coverage: 5
  code_quality: 4
---

## Deterministic Evidence

### Test Results

| Suite | Tests | Result | Duration |
|---|---|---|---|
| test_archive_convergence.py | 38 | all pass | 2.242s |
| test_budget_gate.py | 50 | all pass | 10.597s |
| **Total** | **88** | **all pass** | **~12.8s** |

### Static Safety Checks

- **Destructive liveness probes**: `os.kill(pid, 0)`, `TerminateProcess`, `terminate()`, `taskkill` — **absent** from all `archive_contract/` modules and `archive_convergence.py`. The `owner_process_liveness` function in `model.py:58-86` uses `WaitForSingleObject(handle, 0)` on Windows (non-destructive) and `/proc/<pid>` existence check on Linux.
- **UTF-8 BOM**: none detected in any of the 9 source files.
- **CRLF**: `tests/test_budget_gate.py` has CRLF; all other files are LF-only. `.gitattributes` has `* text=auto eol=lf` which normalizes at commit time.
- **git diff --check**: clean (no whitespace errors in staged/modified files).

### Encoding & File Integrity

All implementation files (`archive_convergence.py`, `__init__.py`, `model.py`, `capture.py`, `transaction.py`, `presentation.py`, `stale-check.py`) are UTF-8 without BOM and LF. The `pre-push` hook uses `#!/bin/sh` with LF endings.

## Threat-Model Honesty

The implementation faithfully narrows its claims to match the plan's §1 threat boundary:

1. **INDEX.md** (model.py:934-945) states: "guarantee: archive-time internal consistency, structural integrity, and traceable declared provenance" and "does not guarantee: historical truth or resistance to a same-permission writer rewriting the whole archive and Git history."
2. **Manifest `risks` field** (model.py:664) always includes `"same-writer-rewrite-undetectable"`.
3. **`source_resolution` field** (model.py:665) is hardcoded to `"disabled"` — the system never claims to re-read external sources during check.
4. **Platform capability degradation**: On Windows (model.py:646-648), `"permissions:acl-confidentiality-not-verified"` is appended to degradations — honest acknowledgment that file ACLs cannot be verified with stdlib alone.
5. **Provenance degradation**: `configured`/`inherited` evidence levels are prohibited from claiming `resolved_model` (model.py:389-390). The `PROVENANCE_MATRIX` (model.py:49-55) enforces legal combinations.

No implementation code over-claims beyond what the spec allows.

## Audit-Journey Assessment

The 30-second audit journey contract (plan §9.1) is implementable and tested:

1. **`scan`** (presentation.py:26-46): Enumerates done/ directories, returns schema state + reason + next_action for each slug. Read-only, no mutations.
2. **`INDEX.md`** (model.py:889-975): Deterministic manifest projection containing Decision, Integrity & Threat Boundary, Degradations, Revision Timeline, Event Timeline, Model Provenance, Artifact Provenance, Residual Risks, and Next Reads — in the exact order specified by plan §9.1.
3. **`check`** (model.py:978-1002): Returns diagnostics with `{code, summary, path, next_action}`. Human-readable and JSON modes share stable diagnostic codes.

The INDEX contains all required first-screen information: final decision (value + type + event ref), archive/revision status, all capability/evidence degradations, residual risks, and next-read paths linking to final round, retrospective, terminal decision evidence, and design-review highlights.

## Spec ↔ Implementation Alignment (Detailed)

### Active/Evidence Path Containment

- **Symlink/junction/reparse rejection**: `ensure_safe_tree` (model.py:230-256) checks `stat.S_ISLNK`, `FILE_ATTRIBUTE_REPARSE_POINT`, and `FILE_ATTRIBUTE_SPARSE_FILE`. Test `test_symlink_or_reparse_tree_is_rejected_or_explicitly_skipped` validates this (skips on privilege limitation — honest).
- **Hardlink rejection**: `st.st_nlink != 1` check (model.py:251). Test `test_hardlink_artifact_is_rejected` validates.
- **UNC/extended path rejection**: `ensure_safe_root` (model.py:220-227) rejects `\\` and `\\?\` prefixes.
- **Windows reserved names**: `WINDOWS_RESERVED` set (model.py:44) + validation in `normalize_relative` (model.py:167) and `validate_identifier` (model.py:175).
- **Unicode/case collision**: NFC+casefold key dedup (model.py:240-242).
- **Workspace containment precedes source open**: Test `test_r3_b1_workspace_containment_precedes_source_open` uses mock to verify `capture_artifact` rejects out-of-workspace sources before reading them.
- **External authorization before read**: Test `test_b1_external_authorization_is_checked_before_source_read` verifies that missing `authorization_ref` prevents source access.

### Append-Only Invocation Lifecycle

- **Sequence allocation**: Global continuous integer starting at 1, allocated inside `EventLock` (capture.py:98). Test `test_concurrent_begin_never_corrupts_sequence` validates with 3-thread barrier.
- **Exclusive create**: `os.O_CREAT | os.O_EXCL` (capture.py:43, transaction.py:38).
- **Terminal event immutability**: `_find_started` (capture.py:232-239) rejects if terminal already exists. Test `test_b5_concurrent_complete_creates_exactly_one_terminal` validates.
- **Spawn requires reservation**: capture.py:193-194. Test `test_b2_spawn_requires_reservation_before_event_creation` validates.
- **Continue same-instance**: capture.py:273-277. Test `test_b2_continue_terminal_must_use_parent_instance` validates.
- **Reviewer authority**: `REVIEWER_AUTHORITIES` (model.py:45-48) restricts verdict to fresh/blank-slate reviewer roles. Test `test_b2_worker_cannot_own_reviewer_verdict` validates.
- **Terminal decision union**: Only `reviewer-verdict` and `user-decision` accepted (model.py:451-452). Test `test_terminal_decision_union_rejects_design_review` validates.
- **User-decision requires canonical message**: model.py:732-735. Tests `test_r3_b2_user_decision_requires_canonical_message_and_exact_degradations` and `test_r3_b2_user_decision_binds_prior_message_and_current_degradations` validate.

### Model Provenance

- **PROVENANCE_MATRIX** (model.py:49-55): Closed mapping of evidence_level → legal {sources, reasons}.
- **Configured/inherited cannot claim resolved model**: model.py:389-390. Test `test_provenance_matrix_rejects_configured_as_resolved` validates.
- **Observed requires host-bound evidence**: model.py:394-401. Test `test_b3_observed_without_bound_host_evidence_is_rejected` validates.
- **Failed-before-resolution reason forbidden on succeeded**: model.py:385-386. Test `test_r3_b3_failed_before_resolution_reason_rejected_on_success` validates.

### Archive/Reopen Durability

- **Journal state machine**: `preparing → source-backed-up → committed` (transaction.py:242-254); post-check failure → `rolled-back` (transaction.py:256-262).
- **Idempotent recovery**: `_recover_archive` (transaction.py:93-124) checks source/backup/target existence and validates the authoritative copy. Test `test_b5_archive_retry_recovers_after_source_backup_journal_failure` validates.
- **Reopen durability**: `_finish_reopen` (transaction.py:127-165) with journal states `reopen-prepared → reopen-moved → reopen-parent-stored → reopen-marker-stored`. Test `test_b5_reopen_retry_finishes_after_move_journal_failure` validates.
- **Lock owner liveness**: `owner_process_liveness` (model.py:58-86) uses `WaitForSingleObject` (Windows, non-signalling) or `/proc` (Linux). Test `test_event_lock_unknown_owner_fails_closed` validates fail-closed behavior.

### Ledger Bidirectional Binding

- **validate_ledger** (model.py:479-551): Every Spawn reservation must have exactly one invocation and one settlement; role/round must match bidirectionally; instance must not duplicate. Test `test_strict_ledger_bidirectional_binding` validates.

### Schema Dispatch

- **Five states**: `missing → malformed → unsupported → invalid → valid` (model.py:259-283). Test `test_schema_dispatch_five_states` validates.
- **Legacy read-only**: `check_archive` returns `legacy-unverifiable` diagnostic for missing manifest (model.py:980-982).

### Hooks

- **pre-push**: NUL-safe git diff parsing (`-z` flag, model.py in `_check_push_range`); uses `git archive` for path safety. Test `test_b6_pre_push_is_nul_safe_and_checks_any_done_change` validates.
- **stale-check**: Reads journal state via `transaction.journal_state` (stale-check.py:180-187); classifies `preparing/reopen-*` as CRITICAL. Does not mutate state.

### Documentation Claims vs Tests

- **Bugfix doc** (convergence-archive-auditability.md:62): States "Round 3 修复仍在验证中" and "旧绿测不代表问题已修复". This is honest — the current 88 tests pass and cover the specific adversarial scenarios mentioned.
- **SKILL.md Archive Contract section** (lines 447-457): Correctly describes invocation lifecycle, provenance, evidence modes, and threat boundary — all consistent with implementation.

## Files & Tools Used

| Category | Files |
|---|---|
| Spec | plan.md, SKILL.md, refs/state-schema.md, refs/orchestrator-guide.md, refs/framework-adapters.md |
| Implementation | archive_convergence.py, archive_contract/__init__.py, model.py, capture.py, transaction.py, presentation.py |
| Hooks | scripts/hooks/pre-push, scripts/hooks/stale-check.py |
| Tests | tests/test_archive_convergence.py (38 tests), tests/test_budget_gate.py (50 tests) |
| Documentation | docs/problems/bugfix/convergence-archive-auditability.md |
| Config | .gitattributes |

| Tool | Purpose |
|---|---|
| `python -B -m unittest discover` | Deterministic test execution (no __pycache__) |
| `grep` (rg pattern search) | Destructive probe scan |
| `read` | Full file examination |
| `bash` | Encoding scan, git status, git diff --check |
