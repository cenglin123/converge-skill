# ocsr_spawn_adapter — Usage

A thin wrapper around `ocsr_dispatch.py` that wires OCSR dispatch into converge Archive Contract v1's event flow + budget_gate. Each Spawn runs the five-step atomic sequence: reserve → begin-invocation → ocsr_dispatch → complete/recover-invocation → settle.

## CLI surface

### `dispatch` — required

| Flag | Description |
|------|-------------|
| `--converge-active` | Converge active dir (gate-ledger.jsonl, `_budget-state.json`, evidence/) |
| `--converge-scripts` | Scripts dir (archive_convergence.py, budget_gate.py) |
| `--ocsr-dispatch` | Path to `ocsr_dispatch.py` |
| `--role` | budget_gate role: `outer-reviewer`, `blind-reviewer`, `executor`, `arbiter`, etc. |
| `--phase` | Phase name: `reviewer-round-1`, `executor-round-2`, etc. |
| `--attempt` | Attempt index (≥1) |
| `--prompt` | Absolute path to self-contained prompt file |
| `--model` | Model ID in `provider/model` form (e.g. `deepseek/deepseek-v4-flash`) |
| `--label` | OCSR worker label |
| `--output-dir` | Product output directory |
| `--output-name` | Product filename (no path) |

### `dispatch` — optional

| Flag | Default | Description |
|------|---------|-------------|
| `--round N` | None | Round number; 0 → null via canonical_round |
| `--reserved-reservation-id RID` | None | Skip reserve step (caller already reserved) |
| `--watch` | false | Blocking product wait via ocsr `--watch --progress` |
| `--timeout MIN` | 15 | Watchdog timeout in minutes |
| `--tier` | `auditable-only` | `auditable-only` or `enforced` |
| `--evidence-mode` | `metadata-only` | `metadata-only`, `redacted`, or `exact` |
| `--harness` | `ocsr-adapter` | OCSR harness tag |
| `--backend` | `opencode` | Archive backend name |
| `--backend-version` | auto-detect | Via `opencode --version` |
| `--scope` | `none` | OCSR meta scope (matches budget_gate ROLE_CONSUMES) |
| `--task-id` | None | OCSR meta task_id |

### Other subcommands

`selftest` — end-to-end self-check; writes a trivial prompt, dispatches, verifies event pair in evidence/events. Flags: `--converge-scripts` (req), `--ocsr-dispatch` (req), `--model`, `--work-dir`.

`config-init` — write initial `_budget-state.json` (idempotent). Flags: `--converge-active` (req), `--mode` (standard|ultraverge), `--max-outer-loops`, `--max-blind-rechecks`, `--ultraverge-min-reviewers`, `--max-inner-loops`, `--force`.

`summary` — pass-through to `budget_gate.py summary`. Flags: `--converge-active` (req), `--converge-scripts` (req).

### Examples

Minimal (watchdog timeout 10 min):
```bash
python scripts/ocsr_spawn_adapter.py dispatch \
  --converge-active .converge/active/my-session \
  --converge-scripts scripts \
  --ocsr-dispatch ../ocsr/scripts/ocsr_dispatch.py \
  --role executor --phase executor-round-1 --attempt 1 \
  --prompt /tmp/prompt.txt \
  --model deepseek/deepseek-v4-flash \
  --label my-task \
  --output-dir .converge/active/my-session/output \
  --output-name report.md \
  --watch --timeout 10
```

Full (explicit optional flags):
```bash
python scripts/ocsr_spawn_adapter.py dispatch \
  --converge-active .converge/active/my-session \
  --converge-scripts scripts \
  --ocsr-dispatch ../ocsr/scripts/ocsr_dispatch.py \
  --role outer-reviewer --phase reviewer-round-1 --round 1 --attempt 1 \
  --prompt /tmp/review.txt \
  --model anthropic/claude-sonnet-4-20250514 \
  --label round-1-review \
  --output-dir .converge/active/my-session/output \
  --output-name review-1.md \
  --evidence-mode metadata-only \
  --watch --timeout 30 \
  --tier auditable-only --harness ocsr-adapter \
  --backend opencode --backend-version "opencode 1.18.3" \
  --scope outer --task-id converge-main
```

## Call sequence (5 steps)

Each `dispatch` invocation (per design.md §3.2):

1. **reserve** — `budget_gate.py reserve --role <role> --target-round <round>`. Checks per-scope budget against `_budget-state.json`. Returns `PROCEED:<rid>` or blocks/denies (exit 10/11/20/21/22/30). Skipped if `--reserved-reservation-id` is set.

2. **begin-invocation** — `archive_convergence.py begin-invocation`. Records `invocation-started` event under `evidence/events/`. Returns JSON with `invocation_id`. On failure, settles `--result cancelled --pre-execution`.

3. **dispatch** — `ocsr_dispatch.py dispatch --worker <prompt|model|label> --output-dir <dir> --output-pattern <name> --watch --timeout <min> --progress --ledger-dir <active-dir> --meta task_id=... --meta role=... --meta scope=... --meta converge-invocation-id=... --meta converge-reservation-id=...`. The adapter auto-appends `--ledger-dir` (ocsr SKILL.md:66).

4. **complete or recover** — If output file exists and >0 bytes: `archive_convergence.py complete-invocation --status succeeded` with provenance flags. Otherwise: `archive_convergence.py recover-invocation` with mapped status and failure-reason-code.

5. **settle** — `budget_gate.py settle --reservation-id <rid> --result succeeded|failed|cancelled`. Frees the reservation and records budget outcome.

Happy path exits 0. Failure exits: 3 (archive CLI error), 5 (OCSR no product), 10/11 (gate block/deny), 30 (fail-closed).

## Provenance choice

Per `archive_contract/model.py:94-100` (PROVENANCE_MATRIX) and design.md §3.3, the adapter uses the strictest legal honest combination:

| Field | Value |
|-------|-------|
| `evidence_level` | `configured` |
| `resolution_source` | `cli_argument` |
| `resolution_reason_code` | `backend-does-not-expose` |

OCSR dispatch does not expose a per-invocation tool_response binding the resolved model — its dispatch ledger is batch-level, not bound to this specific invocation. `host-reported` is forbidden because it requires both a bound host receipt and concrete resolved fields (`host_bound && (resolved_provider && (resolved_model || resolved_family))`, model.py:503-508), and its `reason` must be `None` (model.py:96). OCSR satisfies none of these.

`--instance-id` (ocsr `batch_id`) and `--receipt` (`ocsr-dispatch-ledger.jsonl:<rid>`) are passed as non-constraining correlation handles. At `configured` level they do not participate in host-evidence binding validation (model.py:512-513 forbids degraded provenance from claiming `resolved_provider`/`resolved_model`/`host_evidence_ref`). If a future opencode version exposes per-invocation model fields in tool responses, the combination can be upgraded to `host-reported` + `host_receipt` with `None` reason.

## Failure paths

Outcomes mapped by `_map_ocsr_outcome` in the adapter (`ocsr_spawn_adapter.py:241-268`):

| Scenario | recover `--status` | settle `--result` | `pre_execution` |
|----------|--------------------|--------------------|-----------------|
| Watchdog timeout (ocsr rc=1) | `timeout` | `failed` | `false` |
| Launcher error (Start-Process failed) | `failed` | `failed` | `true` |
| Path collision (ocsr rc=3) | `failed` | `failed` | `false` |
| Generic backend error (post-Start-Process) | `failed` | `failed` | `false` |
| Begin-invocation failure (before dispatch) | — | `cancelled` | `true` |

`pre_execution=true` means the model was never invoked (budget counts it differently). Recover `--failure-reason-code` is `timeout` or `backend-error`; `failure_detail` includes the ocsr exit code and error.log excerpts.

## Honest limitations

1. **No per-invocation resolved model** — OCSR dispatch does not expose which model actually ran in this invocation. Evidence is capped at `configured`. Future upgrade path: if opencode `--format json` exposes per-invocation provider/model in tool responses, switch to `host-reported` + `host_receipt` (see design.md §3.3 "future upgrade path").

2. **Tier is `auditable-only`** — opencode lacks a spawn-blocking hook (per `refs/framework-adapters.md §A.2, table row: opencode → "今日仅 auditable-only"`). The `--tier` flag defaults to `auditable-only`; `best-effort guarded` is not applicable. The budget gate still runs per-spawn reserve/settle for ledger auditability but cannot deny at the framework level before spawn.

3. **Instance_id is OCSR batch_id, not opencode task_id** — The batch_id extracted from `ocsr-dispatch-ledger.jsonl` is a correlation handle (`ocsr_spawn_adapter.py:184-223`). It lets an auditor trace from an archive event back to the OCSR dispatch batch but is not a framework-level invocation identity.

## See also

- [design.md](.converge/active/20260725-ocsr-converge-integration/design.md) — full design decisions, PROVENANCE_MATRIX analysis, ledger semantics
- `python scripts/archive_convergence.py --help` — begin-invocation, complete-invocation, recover-invocation
- `python scripts/budget_gate.py --help` — reserve, settle, summary, config-init
- [refs/framework-adapters.md §A.2](refs/framework-adapters.md) — opencode capabilities and auditable-only tier justification
