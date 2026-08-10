# Review · Design · Round 1

> Reviewer: xiaomi/mimo-v2.5-pro | Date: 2026-07-25 | Verdict: 阻断需修复

## Summary

The design's adapter-layer architecture (option B) is well-evidenced and correctly aligned with source code. The CLI surface, call sequences, and budget_gate/archive_contract wiring are sound. However, the provenance strategy in §3.3 proposes an **illegal combination** that would fail archive validation at `complete-invocation` time. This is the single blocking issue.

## Source-Code Verification Log

| # | Design Claim | Source File | Verdict |
|---|---|---|---|
| 1 | `begin_invocation` requires `reservation_id` for spawn (capture.py:214) | capture.py:214-215 | ✅ Exact match |
| 2 | `ROLE_CONSUMES` and `ROLE_VALUES` fully aligned | budget_gate.py:76-100, ocsr_dispatch.py:66-70 | ⚠️ Partial — shared subset matches; see suggestion #4 |
| 3 | `ROOT_FIXED` contains `ocsr-dispatch-ledger.jsonl` | model.py:52-60 (line 59) | ✅ Confirmed |
| 4 | `canonical_round` normalizes 0→None | model.py:103-116 | ✅ Confirmed |
| 5 | `PROVENANCE_MATRIX` values for host-reported | model.py:94-99 | ✅ Values match, but legal combination check fails — see blocking #1 |
| 6 | ocsr SKILL.md:66 "vault 适配层会自动补全该参数" | ocsr/SKILL.md:66 | ✅ Exact quote |
| 7 | ocsr SKILL.md:62 "脚本不做编排判断" | ocsr/SKILL.md:62 | ✅ Exact quote |
| 8 | `CONVERGE_LEDGER_NAME` in ocsr_dispatch.py:51 | ocsr_dispatch.py:51 | ✅ Confirmed |
| 9 | `capture.complete_invocation` auto-generates `settlement_ref` when None | capture.py:280-286 | ✅ Confirmed — `_canonical_settlement_ref(rid)` |
| 10 | `recover_invocation` forces `evidence_level=unavailable` | capture.py:324-335 | ✅ Confirmed |

## Provenance Honesty Check (Critical)

The design's §3.3 proposes:

```
evidence_level=host-reported
resolution_source=host_receipt
resolution_reason_code=receipt-missing
instance-id=<ocsr batch_id>
```

**Three violations found:**

1. **`receipt-missing` is not a valid reason for `host-reported`**: `PROVENANCE_MATRIX["host-reported"]["reasons"]` is `frozenset({None})`. `receipt-missing` only exists in `configured` and `unavailable` reasons (model.py:97-99). The combination would fail at model.py:501-502: `"Evidence level and resolution source are inconsistent."`

2. **`host-reported` requires concrete resolved fields AND bound host evidence** (model.py:503-508): The validation checks `host_bound = (resolution_source == "host_receipt" and receipt)`. While the receipt string is non-empty, the semantic claim is false — the ocsr ledger entry is not a per-invocation host receipt. More critically, the design omits `resolved_provider/resolved_model/resolved_family`, and line 506-508 requires them: `"Observed/host-reported provenance requires bound host evidence and concrete resolved fields."`

3. **The design acknowledges the degradation but selects the stronger level anyway**: §3.3 says "ocsr ledger 是宿主回执类，但不绑定本次 invocation 的 tool_response" — this is precisely the condition where `configured` should be used, not `host-reported`.

**Correct combination**: `configured` + `cli_argument` + `backend-does-not-expose`. This is the honest choice when the backend doesn't expose per-invocation model resolution.

## Blocking Issues

```yaml
round: 1
verdict: 阻断需修复
deterministic_check: skipped
deterministic_check_skip_reason: design doc, no code to run; claims verified by source-code reading
blocking_issues:
  - id: 1
    description: |
      §3.3 provenance selection uses evidence_level=host-reported with
      resolution_reason_code=receipt-missing. This combination is illegal per
      PROVENANCE_MATRIX (model.py:94-99): host-reported only allows reason=None.
      Additionally, host-reported requires concrete resolved fields AND a bound
      host receipt (model.py:503-508), neither of which OCSR dispatch can provide.
      The design acknowledges the degradation ("ocsr ledger 不绑定本次 invocation
      的 tool_response") but still selects the stronger evidence level. Correct
      choice: configured + cli_argument + backend-does-not-expose.
    attribution: plan_defect
    severity: implementation
    plan_amendment_required: false
    location: §3.3 provenance 诚实降级
    rubric_gap: false
suggestion_issues:
  - description: |
      §3.1 CLI surface is missing --backend and --backend-version parameters,
      but §3.2 happy-path complete-invocation call requires them
      (--backend opencode --backend-version <ver>). Add them to the CLI spec.
  - description: |
      §3.2 does not mention the record-terminal-decision step. The archive
      requires a terminal-decision event (model.py:76-77: "final-decision-missing")
      for final_verdict_ref. The adapter should document that the orchestrator
      must call archive_convergence.py record-terminal-decision after the final
      reviewer invocation completes.
  - description: |
      §3.2 happy path does not explicitly show --pre-execution defaulting to
      false on settle. While the default is correct (model was called), making
      it explicit would improve clarity.
  - description: |
      §2.2 claims "ROLE_CONSUMES and ROLE_VALUES are fully aligned". The shared
      subset used by the adapter (6 roles) matches exactly, but the full sets
      differ: ROLE_CONSUMES has contract-proposer/challenger/finalizer and
      l2-gate-reviewer; ROLE_VALUES has reviewer and release-executor. The claim
      is slightly misleading — qualify as "the adapter's role subset is fully
      aligned" instead.
antipattern_observations:
  - round_referenced: 1
    type: false_generality
    evidence: |
      §3.3: "evidence_level=host-reported：因 ocsr ledger 是宿主回执（记录了
      模型 + wall + 字节数），属'信任宿主回执但无外部签名'"。
      The design treats ocsr's dispatch ledger (a batch-level telemetry record)
      as equivalent to opencode's per-invocation host receipt (task_id). While
      the design acknowledges the downgrade, the evidence level selection still
      over-claims: the ocsr ledger is a dispatch-level record, not a
      per-invocation receipt that binds to this specific tool response.
      Using "configured" would be the honest characterization.
contract_amendment_required: false
```

## Decision Rationale Check (§2.2)

The adapter vs builtin flag decision chain is well-evidenced:

- **Option A rejection**: Cites ocsr SKILL.md §三 "脚本不做编排判断" — verified at ocsr/SKILL.md:62. The reasoning that budget/event recording = orchestration judgment is sound.
- **Option B adoption**: Correctly argues converge is a customer of ocsr, not the other way around. The ROOT_FIXED evidence (model.py:59) and SKILL.md:66 "vault 适配层" evidence are both verified.
- **Option C rejection**: "易遗漏 begin/complete（这恰是当前 bug 根因）" — correct, the current failure mode is exactly this.

No rejected alternative was dismissed too quickly.

## Failure-Path Completeness (§3.2)

The §3.2 happy/failed/timeout paths cover the outcomes `_watch_loop` can produce:

| `_watch_loop` outcome | Design §3.2 path | `pre_execution` | Status |
|---|---|---|---|
| Product landed (file exists, >0 bytes) | Happy path → complete-invocation succeeded | false (default) | ✅ |
| error_file exists (launcher error) | Not-landed → recover-invocation failed | design says "仅当 ocsr Start-Process 失败时加" | ✅ |
| exit_code non-zero (opencode error) | Not-landed → recover-invocation failed | false (model was called) | ✅ |
| DB-lock auto-retry (retry once, then exit) | Implicitly covered by exit_code path | false | ✅ (implicit) |
| Watchdog timeout (deadline exceeded) | Not-landed → recover-invocation timeout | false (model was called but stalled) | ✅ |
| PATH_COLLISION (exit code 3) | Not covered explicitly | — | ⚠️ Minor gap |

The PATH_COLLISION case (ocsr_dispatch.py returns exit code 3 when existing files are overwritten) is not explicitly covered, but the general "未落盘" path handles it implicitly via exit code detection.

## Archive Contract Compliance Trace

Tracing through `validate_event_graph` (model.py:885-971) and `validate_ledger` (model.py:588-682):

1. **Spawn started+terminal pair**: Design produces both via begin-invocation + complete/recover-invocation. ✅
2. **settlement_ref cross-check**: Design omits `--settlement-ref` on complete-invocation → capture.py:280-286 auto-generates canonical `gate-ledger.jsonl:<rid>`. validate_ledger checks `terminal["settlement_ref"] != f"gate-ledger.jsonl:{rid}"` (model.py:673-674). Auto-generated value matches. ✅
3. **final_verdict_ref mechanism**: Requires a terminal-decision event (model.py:76-77). Design does not mention this step — see suggestion #2. The mechanism is intact but needs explicit documentation in the adapter's workflow.
4. **Sequence continuity**: Events are committed via `_commit_event` which auto-assigns sequential numbers (capture.py:115). ✅
5. **Orphan reservation check**: Design's §7 验收锚点 mentions `list-orphan-reservations` — correctly anticipated. ✅

## Non-Goals & Scope Creep

Design §5 non-goals match plan §非目标 verbatim:
- No ocsr/converge merge ✅
- No nested-cost attribution ✅
- No archive-contract semantic changes ✅

No scope creep detected.
