---
round: 2
reviewer_backend: ocsr-via-adapter
generated_at: 2026-07-25T17:00:00+08:00
terminal_decision_event_id: 40808243-c717-4682-a2d8-1036395ba26d
terminal_decision_value: 可执行
---

# Round 2 · dogfood-adapter-usage

## Reviewer output

```yaml
round: 2
verdict: 可执行
deterministic_check: skipped
deterministic_check_skip_reason: doc review
blocking_issues: []
suggestion_issues: []
antipattern_observations: []
contract_amendment_required: false
```

## Round 1 blocking issue triage

| R1 ID | Issue | Verdict | Evidence |
|-------|-------|---------|----------|
| 1 | Doc was empty stub (3 lines) | resolved | Doc now 140 lines, full content covering all 5 plan criteria |
| 2 | CLI parameter coverage missing (22 dispatch + 4 selftest + 7 config-init + 2 summary) | resolved | `## CLI surface` tables cover all 22 dispatch args (11 required + 11 optional); `## Other subcommands` covers selftest/config-init/summary flags; examples included |
| 3 | 5-step call sequence missing | resolved | `## Call sequence (5 steps)` enumerates reserve→begin→dispatch→complete/recover→settle matching design.md §3.2 |
| 4 | Provenance choice missing | resolved | `## Provenance choice` documents `configured + cli_argument + backend-does-not-expose`, explains host-reported forbidden per PROVENANCE_MATRIX |
| 5 | Failure paths missing | resolved | `## Failure paths` table maps 5 scenarios with recover status + settle result + pre_execution |
| 6 | Honest limitations missing | resolved | `## Honest limitations` covers no resolved model, auditable-only tier, batch_id correlation handle |

Triage counts: resolved=6, still_blocking=0, deferred=0.

## Round-2-specific verification

### 1. Doc-source CLI flag consistency

Every dispatch flag in `build_parser()` (`ocsr_spawn_adapter.py:620-652`) appears in doc tables:

- Required (11): `--converge-active`, `--converge-scripts`, `--ocsr-dispatch`, `--role`, `--phase`, `--attempt`, `--prompt`, `--model`, `--label`, `--output-dir`, `--output-name` — all present.
- Optional (11): `--round`, `--reserved-reservation-id`, `--watch`, `--timeout` (default 15), `--tier` (default `auditable-only`), `--evidence-mode` (default `metadata-only`), `--harness` (default `ocsr-adapter`), `--backend` (effective default `opencode` via null-coalesce at line 365), `--backend-version` (effective default auto-detect via `_detect_opencode_version()` at line 366), `--scope` (default `none`), `--task-id` (default None) — all present.
- Selftest flags (4): `--converge-scripts`, `--ocsr-dispatch`, `--model`, `--work-dir` — all present.
- Config-init flags (7): `--converge-active`, `--mode`, `--max-outer-loops`, `--max-blind-rechecks`, `--ultraverge-min-reviewers`, `--max-inner-loops`, `--force` — all present.
- Summary flags (2): `--converge-active`, `--converge-scripts` — both present.

No invented flags. No missing essential flags. **Pass.**

### 2. Provenance claim accuracy

Doc provenance table (line 103-107):
```
evidence_level: configured
resolution_source: cli_argument
resolution_reason_code: backend-does-not-expose
```

Cross-check `PROVENANCE_MATRIX` (`model.py:94-100`):
- `configured` → sources: `{cli_argument, agent_config}` → `cli_argument` ∈ sources ✓
- `configured` → reasons: `{backend-does-not-expose, receipt-missing}` → `backend-does-not-expose` ∈ reasons ✓

Doc correctly avoids `host-reported` (line 109) which requires `host_receipt`/`tool_response` source + `None` reason (`model.py:96,503-510`). Doc correctly notes `--instance-id`/`--receipt` are non-constraining correlation handles at `configured` level (`model.py:512-513` forbids degraded provenance from claiming `resolved_*` fields). **Pass.**

### 3. Failure path correctness

Cross-check `_map_ocsr_outcome` (`ocsr_spawn_adapter.py:241-268`) vs doc table:

| Scenario | Code return | Doc recover status | Doc settle result | Doc pre_execution | Match |
|----------|------------|-------------------|-------------------|-------------------|-------|
| Watchdog timeout (rc=1) | `("timeout", "timeout", False)` | `timeout` | `failed` | `false` | ✓ |
| Launcher error (error.log exists) | `("failed", "backend-error", True)` | `failed` | `failed` | `true` | ✓ |
| Path collision (rc=3) | `("failed", "backend-error", False)` | `failed` | `failed` | `false` | ✓ |
| Generic backend error | `("failed", "backend-error", False)` | `failed` | `failed` | `false` | ✓ |
| Begin-invocation failure | not via `_map_ocsr_outcome` (handled at line 408-410) | — | `cancelled` | `true` | ✓ |

Settle result mapping at lines 497-515: `"cancelled"` if status==cancelled else `"failed"` → all doc settle results match. **Pass.**

### 4. Honest limitations

Doc §Honest limitations explicitly states:
1. "No per-invocation resolved model" — does NOT claim resolved model exposure. ✓
2. "Tier is `auditable-only`" — does NOT claim enforced tier. ✓

**Pass.**

### 5. Length and non-duplication

- Line count: 140 lines (≤200 target). ✓
- §See also links to design.md, archive_convergence.py, budget_gate.py, framework-adapters.md — does not duplicate design.md content. ✓

## Pre-check (reviewer-discipline Q1–Q5)

- **Q1 产物身份自洽**: Title "ocsr_spawn_adapter — Usage", first sentence describes a thin wrapper wiring OCSR dispatch into converge Archive Contract v1. Internally consistent. ✓
- **Q2 产物边界诚实**: Describes CLI usage, call sequence, provenance, failure paths, limitations. Does not overstate capabilities. ✓
- **Q3 产物数据纯度**: Pure tool documentation; no embedded business data or hardcoded environment. Example paths are placeholders. ✓
- **Q4 职责边界自洽**: Single-purpose doc; external references go to their source files. No ambiguous "grey zone" responsibilities claimed. ✓
- **Q5 命名一致性**: CLI flag names consistent between tables and examples. Consistent use of `adapter`, `dispatch`, `invocation`, `settle` throughout. ✓

No pre-check failures.

## Verdict summary

All 6 Round 1 blocking issues resolved. All 5 Round-2-specific checks pass. Doc meets all 5 plan acceptance criteria. Verdict: **可执行** — ready for record-terminal-decision + archive + check (Phase 3 core acceptance).
