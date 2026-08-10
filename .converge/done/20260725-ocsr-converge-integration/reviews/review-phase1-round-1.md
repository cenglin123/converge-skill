# Phase 1 Round 1 Review

> reviewer: deepseek-v4-pro | adapter: `ocsr_spawn_adapter.py` | 2026-07-25

```yaml
round: 1
verdict: 可执行
deterministic_check: pass
blocking_issues: []
suggestion_issues:
  - description: |
      `--reserved-reservation-id` bypass path (adapter lines 302-306) has zero test coverage.
      If a caller passes a reservation_id that was never reserved in the gate ledger, begin-invocation
      (capture.py line 214) accepts it as a non-empty string, complete-invocation succeeds, but settle
      (gate line 797) fails with `settle_without_reserve`. This produces a started+terminal event pair
      with no matching gate settlement — caught at archive time by `validate_ledger:ledger-binding-missing`,
      so it is fail-closed, but the adapter could prevent this class of error by checking the gate ledger
      itself (or at minimum validating the ID format) before proceeding to begin. The design does not
      mandate this check, but the test gap means the path is unverified against real gate ledger state.
      Test: a new `TestReservedReservationId` class with three cases — valid pre-reserved ID passes;
      nonexistent ID fails at settle (adapter rc non-zero); and the adapter does not leave an orphan
      started event when settle fails.
    attribution: executor_limit
    severity: implementation
    plan_amendment_required: false
    location: tests/test_ocsr_spawn_adapter.py (missing test class)
    rubric_gap: false
  - description: |
      `_extract_ocsr_instance_id` (adapter lines 184-223) is only exercised indirectly through the
      happy-path test via `fake_ocsr_dispatch.py`'s ledger output. Its edge cases — corrupted JSONL
      lines, OSError on read, no matching (label, model, prompt_file) tuple, empty ledger — have no
      dedicated unit tests. The fallback to `ocsr-unknown-<uuid8>` is honest but untested; if a
      regression breaks the matching logic, the instance_id silently becomes the synthetic fallback
      and the ledger cross-reference in the archive manifest weakens to "unknown." This is not a
      correctness bug (instance_id is non-constraining at `configured` level), but it degrades
      auditability. A focused test exercising at minimum: ledger with no matching entry, ledger with
      corrupt lines, and ledger file not found.
    attribution: executor_limit
    severity: implementation
    plan_amendment_required: false
    location: scripts/ocsr_spawn_adapter.py:184-223
    rubric_gap: false
  - description: |
      When `complete-invocation` fails after product landed (adapter lines 381-394), the error
      message does not include the `invocation_id`. The orchestrator needs this ID to retry
      `archive_convergence.py complete-invocation` directly. Currently the adapter prints
      `"complete-invocation failed (rc=N) but product landed..."` — the invocation_id must be
      extracted from the begin-invocation JSON stdout, which is not forwarded. Adding
      `invocation={invocation_id}` to the error line gives the orchestrator a direct remediation
      handle. This matches design §3.2's "caller decides whether to retry complete" intent.
    attribution: executor_limit
    severity: implementation
    plan_amendment_required: false
    location: scripts/ocsr_spawn_adapter.py:390-393
    rubric_gap: false
  - description: |
      The adapter's docstring at line 13 claims "fail-closed：begin 后任何异常都尝试 recover，绝不留孤儿 started event"
      but the complete-invocation failure path (happy path, product landed, lines 381-394) settles as
      "succeeded" and returns non-zero WITHOUT calling recover-invocation. This is correct behavior
      per design §3.2 (the product landed; calling recover would falsely mark it as failed), but the
      docstring claim is misleading. Correct the claim to: "begin 后 dispatch failure 的任何异常都尝试 recover"
      or update to: "complete-invocation 失败时由调用方重试，适配层记录 gate settle 但不调 recover."
    attribution: executor_limit
    severity: implementation
    plan_amendment_required: false
    location: scripts/ocsr_spawn_adapter.py:13
    rubric_gap: false
  - description: |
      `_map_ocsr_outcome` (lines 241-268) has a code branch for `ocsr_rc == 3` (path collision,
      EXIT_PATH_COLLISION in ocsr_dispatch.py line 52) mapped to `("failed", "backend-error", False)`.
      The test shim `_fake_ocsr_dispatch.py` defines a `fail-collision` mode (line 120-122) that
      returns rc=3, but no test exercises this code path. Additionally, the general fallthrough at
      line 268 (`return "failed", "backend-error", False`) for `ocsr_rc == 0` (success reported but
      product missing — e.g. product deleted between landing and adapter checking) is untested.
      Neither is likely to cause a correctness issue today, but untested branching invites future
      regressions.
    attribution: executor_limit
    severity: implementation
    plan_amendment_required: false
    location: scripts/ocsr_spawn_adapter.py:260-261
    rubric_gap: false
  - description: |
      The `_gate_settle` result mapping at line 437 maps all non-cancelled archive statuses to
      gate `"failed"`. The conditional `settle_result = "cancelled" if status == "cancelled" else "failed"`
      has a `"cancelled"` branch that is unreachable because `_map_ocsr_outcome` never returns
      `"cancelled"`. This is dead code, not a bug — the mapping is correct and will remain correct
      if the function later gains a cancelled return. Marking as suggestion for code clarity: either
      add a comment noting the branch is forward-looking, or simplify to `settle_result = "failed"`.
    attribution: executor_limit
    severity: implementation
    plan_amendment_required: false
    location: scripts/ocsr_spawn_adapter.py:437
    rubric_gap: false
antipattern_observations: []
contract_amendment_required: false
```

## Deterministic checks

- **Adapter tests** (`test_ocsr_spawn_adapter.py`): exit code 0, 6 tests OK in 2.555s
- **Budget gate regression** (`test_budget_gate.py`): exit code 0, 69 tests OK in 16.561s
- **Archive convergence regression** (`test_archive_convergence.py`): exit code 0, 85 tests OK in 5.214s
- No regressions. All 160 pre-existing + 6 new = 166 tests pass.

## Semantic review summary

### 1. Spec-conformance (design §3.2 call sequence): PASS

The adapter implements the exact 5-step sequence: reserve (lines 302-326) → begin-invocation (328-348) → dispatch (350-371) → complete/recover (373-447) → settle (embedded in step 4). Happy path and failure path both match the design.

### 2. Provenance correctness: PASS

`_archive_complete` (lines 148-152) passes:
- `--evidence-level configured`
- `--resolution-source cli_argument`
- `--resolution-reason-code backend-does-not-expose`

Does NOT pass `--resolved-provider`, `--resolved-model`, or `--resolved-family`. This is the only legal combination under `PROVENANCE_MATRIX` (model.py:497-498, 512-513). `--instance-id` and `--receipt` are passed as non-constraining correlation handles, as permitted by design §3.3.

### 3. pre_execution mapping: PASS

| condition | ocsr rc | error.log | pre_execution | rationale |
|---|---|---|---|---|
| Watchdog timeout | 1 | - | false | Model was called |
| Path collision | 3 | - | false | Model was called |
| Start-Process fail | any | present | true | Launcher never started opencode |
| Generic backend err | other | absent | false | Model was called |

All match budget_gate.py semantics (lines 571-574).

### 4. Settle mapping (archive timeout → gate failed): PASS

SETTLE_EVENTS is `{spawn_succeeded, spawn_failed, cancelled}`. `validate_ledger` (model.py:670) maps `spawn_failed` → `{failed, timeout}`. So mapping archive `timeout` → gate `failed` is the correct cross-reference — both validate_ledger and the adapter agree.

### 5. Orphan-event prevention: PASS (design-acknowledged gap)

When complete-invocation fails after product landed (lines 381-394): settle is recorded as "succeeded" but there is no terminal event. Design §3.2 explicitly states: "Complete 失败 — 不撤销产物，但向 stderr 报错并以非零退出；调用方决定是否 retry complete." This is a caller-visible failure, not a silent orphan. The adapter correctly signals the error. Suggestion: include invocation_id in the error message for retry (see suggestion #3).

### 6. Test coverage: ADEQUATE+

- Happy path: covered (TestHappyPath)
- fail-launcher: covered (TestFailurePaths)
- fail-timeout: covered (TestFailurePaths)
- Unknown role DENY: covered (TestReserveGate)
- Outer-reviewer scope: covered (TestHappyPath)
- Event-graph validity: covered (TestArchiveCheckValid)
- `--reserved-reservation-id` bypass: NOT covered (suggestion #1)
- `_extract_ocsr_instance_id` edge cases: NOT directly covered (suggestion #2)
- fail-collision (rc=3): NOT covered (suggestion #5)

### 7. CLI parameter completeness: PASS

All design §3.1 params present. Implementation adds `--harness`, `--scope`, `--task-id`, `--tier` with sensible defaults — all referenced in §3.2 step 3 or are necessary for ocsr dispatch passthrough.

### 8. Source-code citation re-verification: PASS

- model.py:498 (configured forbids resolved_model): adapter omits all resolved fields ✓
- model.py:512-513 (degraded provenance forbids resolved): adapter omits all resolved fields ✓
- capture.py:214 (spawn requires reservation_id): adapter always passes reservation_id ✓
- capture.py:280-286 (auto-generated settlement_ref): adapter relies on auto-generation ✓

### 9. Antipattern scan: NONE DETECTED

No active antipatterns from `refs/antipatterns.md` apply to this implementation. The adapter is a focused, single-purpose bridge with clear boundaries.
