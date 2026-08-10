## Round 1 attempt · issue 1
- reviewer_backend: ocsr-via-adapter
- Issue: Document is a near-empty stub (3 lines). None of the 5 acceptance criteria from plan.md are addressed.
- Issue 归因（reviewer 判定）: executor_limit
- plan_amendment_required: false
- Approach: Stub→full doc (~150 lines) covering all 5 criteria: what-it-is, CLI surface, call sequence, provenance, failure paths, limitations, see-also.
- Rejected alternatives: 无
- Upstream scope check: 无
- Diff: Wrote full doc (see attempts.md entry per criterion for per-criterion diff)
- R1 verdict:

## Round 1 attempt · issue 2
- reviewer_backend: ocsr-via-adapter
- Issue: CLI parameter coverage missing — 18 dispatch args, 4 selftest args, 6 config-init args, 2 summary args all undocumented.
- Issue 归因（reviewer 判定）: executor_limit
- plan_amendment_required: false
- Approach: Added required/optional flag tables for `dispatch` (11 required + 11 optional), brief coverage of `selftest`/`config-init`/`summary`, plus minimal + full command examples.
- Rejected alternatives: Single flat list without grouping (worse readability)
- Upstream scope check: argparse definition in ocsr_spawn_adapter.py:613-680 — tables verified against build_parser()
- Diff: Added `## CLI surface` section with two tables and `## Other subcommands` + `## Examples` subsection
- R1 verdict:

## Round 1 attempt · issue 3
- reviewer_backend: ocsr-via-adapter
- Issue: Call sequence coverage missing — plan criterion 2 requires 5-step sequence (reserve→begin→dispatch→complete→settle) matching design.md §3.2.
- Issue 归因（reviewer 判定）: executor_limit
- plan_amendment_required: false
- Approach: Added `## Call sequence (5 steps)` section enumerating each step with responsible script, flags, and outcome descriptions. Matches design.md §3.2 verbatim.
- Rejected alternatives: 无
- Upstream scope check: design.md §3.2 happy/failure paths — confirmed step order and script boundaries
- Diff: Added `## Call sequence (5 steps)` section
- R1 verdict:

## Round 1 attempt · issue 4
- reviewer_backend: ocsr-via-adapter
- Issue: Provenance choice missing — plan criterion 3 requires documenting `configured + cli_argument + backend-does-not-expose` and why `host-reported` is forbidden.
- Issue 归因（reviewer 判定）: executor_limit
- plan_amendment_required: false
- Approach: Added `## Provenance choice` section with table, PROVENANCE_MATRIX reference (model.py:94-100), evidence that host-reported requires bound receipt + concrete resolved (model.py:503-508) + None reason (model.py:96), and explanation of --instance-id/--receipt as non-constraining correlation handles.
- Rejected alternatives: 无
- Upstream scope check: design.md §3.3 provenance analysis — confirmed configured is strictest legal honest choice
- Diff: Added `## Provenance choice` section
- R1 verdict:

## Round 1 attempt · issue 5
- reviewer_backend: ocsr-via-adapter
- Issue: Failure paths missing — plan criterion 4 requires covering watchdog timeout, launcher error, generic backend error with recover-invocation status + settle result + pre_execution flag.
- Issue 归因（reviewer 判定）: executor_limit
- plan_amendment_required: false
- Approach: Added `## Failure paths` section with 5-row table mapping ocsr outcomes → recover status → settle result → pre_execution. References _map_ocsr_outcome (ocsr_spawn_adapter.py:241-268).
- Rejected alternatives: 无
- Upstream scope check: _map_ocsr_outcome in adapter — confirmed pre_execution semantics (true only for launcher error pre-Start-Process)
- Diff: Added `## Failure paths` section
- R1 verdict:

## Round 1 attempt · issue 6
- reviewer_backend: ocsr-via-adapter
- Issue: Honest limitations missing — plan criterion 5 requires stating OCSR does NOT expose resolved model and does NOT enforce tier.
- Issue 归因（reviewer 判定）: executor_limit
- plan_amendment_required: false
- Approach: Added `## Honest limitations` section with 3 items: (1) no per-invocation resolved model → capped at configured; (2) auditable-only tier per framework-adapters.md §A.2; (3) instance_id is batch_id correlation handle, not task_id.
- Rejected alternatives: 无
- Upstream scope check: framework-adapters.md §A.2 table row confirms opencode "今日仅 auditable-only"
- Diff: Added `## Honest limitations` section
- R1 verdict:
