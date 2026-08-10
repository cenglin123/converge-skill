# Deferred Fix Execution Report

**Executor**: deepseek-v4-flash (fresh context)  
**Date**: 2026-07-25  
**Task**: Fix 6 implementation-level suggestions (S1–S6) from converge review cycle

---

## Changes Made

### S3 — invocation_id 加入 complete 失败错误消息

**File**: `scripts/ocsr_spawn_adapter.py`

Two locations updated:

1. `_archive_complete()` (line 163):
   - Before: `_err(f"complete-invocation failed (rc={rc}): {out or err}")`
   - After: `_err(f"complete-invocation failed (invocation_id={invocation_id}, rc={rc}): {out or err}")`

2. `cmd_dispatch()` happy-path error (line ~462):
   - Before: `_err(f"[adapter] complete-invocation failed (rc={complete_rc}) but product landed; ...")`
   - After: `_err(f"[adapter] complete-invocation failed (invocation_id={invocation_id}, rc={complete_rc}) but product landed; ...")`

### S4 — docstring 措辞纠正

**File**: `scripts/ocsr_spawn_adapter.py`

Line 13:
- Before: `- fail-closed：begin 后任何异常都尝试 recover，绝不留孤儿 started event。`
- After: `- fail-closed：begin 后 dispatch 阶段的异常都尝试 recover；complete 自身的失败不 recover（by design，避免重复终态）。`

Now accurately describes that only dispatch-phase exceptions trigger recover; complete failures do not.

### S6 — cancelled 分支添加 forward-looking 注释

**File**: `scripts/ocsr_spawn_adapter.py`

Line 504–505 (settle mapping), added comment before the dead-code line:
```python
    # forward-looking: cancelled not yet emitted by _map_ocsr_outcome, retained for completeness
    settle_result = "cancelled" if status == "cancelled" else "failed"
```

The `status == "cancelled"` branch is currently unreachable because `_map_ocsr_outcome` only returns `"timeout"` or `"failed"`. Kept as a forward-looking placeholder.

### S1 — 3 tests for `--reserved-reservation-id` bypass

**File**: `tests/test_ocsr_spawn_adapter.py`

New class `TestReservedReservationId(AdapterBase)` with 3 tests:

| Test | Description |
|------|-------------|
| `test_reserved_id_happy_bypasses_reserve` | Pre-reserve via gate CLI with known ID; run adapter with `--reserved-reservation-id`; verify no duplicate reserve event in gate ledger, events reference external ID, stderr logs bypass message |
| `test_reserved_id_fail_launcher_still_recovers` | Same pre-reserve + fail-launcher; verify adapter still exits 5, recovery path works, spawn_failed uses external ID |
| `test_reserved_id_fail_timeout_recovers` | Same pre-reserve + fail-timeout; verify timeout terminal status, reservation_id preserved |

Each test first calls `budget_gate.py reserve --reservation-id X` (via `run_gate()` helper) then invokes `run_adapter()` with `reserved_reservation_id=X`. Asserts exactly 1 reserved event (from pre-reserve, not re-issued by adapter).

### S2 — 3 boundary tests for `_extract_ocsr_instance_id`

**File**: `tests/test_ocsr_spawn_adapter.py`

New class `TestExtractInstanceId(unittest.TestCase)` with 3 tests (direct unit tests, no subprocess):

| Test | Description |
|------|-------------|
| `test_no_ledger_file_returns_fallback` | Ledger file does not exist → `ocsr-unknown-*` fallback |
| `test_empty_ledger_returns_fallback` | Ledger file is empty string → `ocsr-unknown-*` fallback |
| `test_no_match_returns_fallback` | Ledger has a launched event for a different label/model → `ocsr-unknown-*` fallback |

All call `_extract_ocsr_instance_id()` directly via the imported private function.

### S5 — 2 tests for fail-collision and generic fallthrough

**File**: `tests/test_ocsr_spawn_adapter.py`

New class `TestFailCollisionAndFallthrough(AdapterBase)` with 2 tests:

| Test | Description |
|------|-------------|
| `test_fail_collision_uses_recover` | `FAKE_OCSR_MODE=fail-collision` (ocsr rc=3) → adapter exits 5, terminal `failed`/`backend-error`, `pre_execution=false` |
| `test_unknown_ocsr_rc_falls_through_to_generic` | `FAKE_OCSR_MODE=unknown-mode-99` (fake returns rc=99) → adapter exits 5, terminal `failed`/`backend-error`, generic fallthrough |

---

## Test Results

```
$ python -m pytest tests/ -q
...................................                                      [100%]
176 passed in 30.66s
```

- **Before**: 168 tests all green
- **After**: 176 tests all green (8 new)
- **Delta**: +8 passed, 0 failed, 0 skipped

---

## File Modification Summary

| File | Changes |
|------|---------|
| `scripts/ocsr_spawn_adapter.py` | 4 edits: S3 (2 error messages), S4 (1 docstring), S6 (1 comment) |
| `tests/test_ocsr_spawn_adapter.py` | 1 import + 3 new test classes with 8 test methods |
| `tests/_fake_ocsr_dispatch.py` | Not modified (already had `fail-collision` mode; fallthrough for unknown modes handled by existing code) |
| Other files | Not touched |
| `.converge/` | Not touched (review report excepted) |

## Unresolved Items

None. All 6 suggestions (S1–S6) are fully implemented and verified.
