# Phase 2 Round 1 Review

> reviewer: xiaomi/mimo-v2.5-pro | adapter: `ocsr_spawn_adapter.py` (Phase 2 additions) | 2026-07-25

```yaml
round: 1
verdict: 可执行
deterministic_check: pass
blocking_issues: []
suggestion_issues: []
antipattern_observations: []
contract_amendment_required: false
```

## Deterministic checks

- **Adapter tests** (`test_ocsr_spawn_adapter.py`): exit code 0, 14 tests OK in 6.917s
- **Budget gate regression** (`test_budget_gate.py`): exit code 0, 69 tests OK in 16.155s
- **Archive convergence regression** (`test_archive_convergence.py`): exit code 0, 85 tests OK in 5.158s
- No regressions. All 160 pre-existing + 8 new = 168 tests pass. Exit codes all 0.

## Semantic review

### 1. config-init ultraverge override correctness: PASS

`cmd_config_init` (adapter:306-309): `config.setdefault("max_blind_rechecks", 2)` is called only after explicit args are set (lines 298-305). `setdefault` semantics guarantee that an explicit `--max-blind-rechecks 5` (line 301) wins over the ultraverge default. Cross-check:
- `budget_gate.DEFAULTS["max_blind_rechecks"]=1` (gate:62) — the gate's default is 1; adapter overrides to 2 for ultraverge.
- `ceiling(state, "blind")` (gate:422) calls `cfg(state, "max_blind_rechecks")` which returns `state.config.max_blind_rechecks` or falls back to `DEFAULTS["max_blind_rechecks"]=1`. So the adapter's written config value (2 or explicit override) is what the gate uses.
- `default_total_cap` (gate:432-436) uses `cfg(state, "max_blind_rechecks")` — picks up the overridden value. Correct.
- Test `test_explicit_overrides_win_over_ultraverge_default` directly validates `setdefault` override semantics with `--mode ultraverge --max-blind-rechecks 5`.

### 2. Idempotency / fail-closed on re-init: PASS

`cmd_config_init` returns `EXIT_FAIL_CLOSED` (30) when state exists and no `--force` (adapter:290-292). This matches `budget_gate.EXIT_FAIL_CLOSED=30` (gate:52). The bind/rebind pattern (gate:987-989) uses the same convention: `already_bound` → `EXIT_FAIL_CLOSED`. Consistent fail-closed semantics.

Test `test_idempotent_no_force_fails_closed` validates rc=30 and stderr contains "already exists".

### 3. LF line-ending pinning: PASS

`cmd_config_init` writes with `newline="\n"` (adapter:318-321), mirroring `budget_gate.write_state` (gate:204-206). `_budget-state.json` is in `ROOT_FIXED` (model.py:55) and gets manifest-hashed.

Test `test_state_file_uses_lf_line_endings` reads raw bytes (`read_bytes()`) and asserts `b"\r\n" not in raw`. This is the correct check — on Windows, `write_text(..., newline="\n")` bypasses the default CRLF translation, so the bytes on disk are LF. If CRLF were present, `b"\r\n"` would appear in the raw bytes. The test proves no CRLF exists at the byte level.

### 4. Per-scope blocking test validity: PASS

Trace through `test_outer_scope_reservation_blocks_at_ceiling`:
- Rounds 1-5: each dispatches `outer-reviewer` with unique round numbers 1-5, producing `round-1.md` through `round-5.md`.
- `realized(active, "outer")` (gate:320-321) counts files matching `round-*.md` pattern = 5.
- `pending(active, events, "outer")` (gate:324-337): all 5 previous reservations settled as `spawn_succeeded` (status in `("spawn_failed", "cancelled")` is False), and each `(active / "round-{n}.md").exists()` returns True → all skipped → pending=0.
- `effective_usage = 5 + 0 = 5`.
- `ceiling(state, "outer")` = `cfg(state, "max_outer_loops")` = `DEFAULTS["max_outer_loops"]` = 5 (no config-init, so state.config is empty → fallback to DEFAULTS).
- Gate check (gate:749-751): `5 >= 5` → True → BLOCK:budget_exhausted, EXIT_BLOCK_BUDGET=10.
- The BLOCK happens at `reserve` (gate:741-758), not at `begin`. The adapter never reaches `begin-invocation` for round 6. Test correctly asserts `rc=10` and `len(events)==10` (5 rounds × 2 events each).

### 5. summary pass-through correctness: PASS

`cmd_summary` (adapter:326-336) shells out to `budget_gate.py summary --active-dir <dir>` and prints stdout. The gate's `cmd_summary` (gate:863-899) outputs JSON with keys: `total_reservations_issued`, `total_ceiling`, `attempted_dispatch`, `model_invocation`, `scopes`. The adapter passes this through unchanged.

### 6. attempted vs model_invocation distinction: PASS

Test: 2 happy + 1 fail-launcher.

`budget_gate.attempted_dispatch(events, None)` (gate:282-288):
- Counts all reservations where `not (status=="cancelled" and pre_execution)`.
- 2 spawn_succeeded (pre_execution irrelevant) + 1 spawn_failed(pre_execution=True) → status!="cancelled" → counted.
- Total: **3**. Test asserts `attempted_dispatch==3`. ✓

`budget_gate.model_invocation(events, None)` (gate:291-304):
- spawn_succeeded → always counted (×2).
- spawn_failed with pre_execution=True → `not r["pre_execution"]` is False → NOT counted.
- Total: **2**. Test asserts `model_invocation==2`. ✓

The fail-launcher path in the adapter: `_map_ocsr_outcome` detects `error_log.is_file()` → returns `("failed", "backend-error", True)`. Gate settle gets `pre_execution=True`. Budget gate records `spawn_failed` with `pre_execution=True`. Correct.

### 7. Phase 1 regression: PASS

All Phase 1 test classes (`TestHappyPath`, `TestFailurePaths`, `TestReserveGate`, `TestArchiveCheckValid`) still pass — 6 tests. No modification to Phase 1 code paths. Phase 2 additions are purely additive (new subcommands, new test classes).

### 8. CLI surface completeness: PASS

`config-init` subparser (adapter:661-672): exposes `--converge-active` (required), `--mode` (standard/ultraverge), `--max-outer-loops`, `--max-blind-rechecks`, `--ultraverge-min-reviewers`, `--max-inner-loops`, `--force`. These cover all `budget_gate.DEFAULTS` int config keys (gate:70-74) plus `total_safety` (float, not exposed — not needed for Phase 3 dogfood). Defaults are sensible (mode=standard, all config=None → omitted from JSON → gate falls back to DEFAULTS on first read).

`summary` subparser (adapter:674-678): exposes `--converge-active` and `--converge-scripts`. Minimal and sufficient — summary is a read-only pass-through.

For Phase 3 dogfood: the orchestrator needs `config-init --mode ultraverge --converge-active <dir>` before first reserve, then `summary --converge-active <dir> --converge-scripts <dir>` for budget visibility. Both are present.

### 9. Antipattern scan: NONE DETECTED

Active antipatterns from `refs/antipatterns.md` checked:

- **environment_lock-in**: No hardcoded paths. Uses `Path` and `--converge-active`/`--converge-scripts` CLI args. Cross-platform compatible (`newline="\n"` is explicit, not relying on OS default). ✓
- **data_tool_coupling**: `cmd_config_init` writes the same JSON schema that `budget_gate.read_state` expects. No adapter-specific state format — pure pass-through of the gate's schema. ✓
- **solution_anchoring**: Phase 2 implements exactly what plan §Phase 2 specified (`config-init` for ultraverge override, `summary` pass-through). No evidence of patching over a structural mismatch. ✓

## Appendix: Source-code cross-references

| Claim | Source |
|---|---|
| `EXIT_FAIL_CLOSED=30` | budget_gate.py:52 |
| `DEFAULTS["max_blind_rechecks"]=1` | budget_gate.py:62 |
| `DEFAULTS["max_outer_loops"]=5` | budget_gate.py:61 |
| `write_state` uses `newline="\n"` | budget_gate.py:204-206 |
| `cmd_summary` JSON shape | budget_gate.py:891-899 |
| `attempted_dispatch` excludes only `cancelled+pre_execution` | budget_gate.py:282-288 |
| `model_invocation` excludes `spawn_failed+pre_execution=true` | budget_gate.py:291-304 |
| `_budget-state.json` in `ROOT_FIXED` | model.py:55 |
| `effective_usage = realized + pending` | budget_gate.py:340-341 |
| BLOCK at reserve, not begin | budget_gate.py:741-758 |
| bind `already_bound` → FAIL_CLOSED | budget_gate.py:987-989 |
