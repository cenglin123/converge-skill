# converge — Dual-Agent Iterative Convergence

> Translated from README.md (authoritative source). 以中文版为准。

Dual-agent iterative convergence for AI-generated artifacts. Instead of scripted workflows, converge uses **adversarial review cycles** between independent agents to drive quality through iteration — until Reviewer delivers a `executable` verdict or a stop condition is triggered.

> **Framework-agnostic**: Reviewer / Executor spawning and continuation are implemented via an abstract capability layer (Spawn / Continue / Identify), not tied to any specific framework API. The core budget-adjudication script (file-authoritative `budget_gate.py`) is likewise host-independent — reserve/settle/ingest-verdict semantics are identical across all frameworks.
>
> **Budget enforcement is tiered**: the core gate is host-independent, but "can it hard-block before spawn?" depends on whether the framework exposes a blockable pre-spawn hook. Claude Code has a landed `best-effort guarded` (PreToolUse total-cap backstop); opencode / Codex are currently `auditable-only`; true `enforced` remains future work. See "Budget execution" below.

## Philosophy

**Don't tell the model how to walk. Tell it what "arrived" means, give it test tools, and let it find the path.**

Converge follows two constitutional design principles:

**Bitter Lesson**: Manually injected workflow structures (spec, scripts, hardcoded roles) decay as models improve. Instead, it defines **acceptance criteria** (contract), **verification tools** (lint, tests), and **adversarial feedback** (independent Reviewer) — then lets the model explore until it passes. Mechanisms are hardcoded (three roles, adversarial loop, contract-driven); domain knowledge is compiled from real convergence logs (antipattern registry driven by hit frequency, auto-decaying via distill).

**Occam's Razor**: Every file, rule, and field must answer "what specific problem does it solve." Abstractions that can't answer this are rejected. The three-layer separation (mechanism / constitution / antipatterns) is itself an application of Occam — volatile antipattern knowledge doesn't corrupt stable mechanism files. Defunct information (e.g., migration archaeology) is deleted; git log is its proper home.

## How it works

```
Round 0: Contract negotiation (optional preamble)
  Executor proposes acceptance criteria → Reviewer challenges → final contract.md

Round 1+: Adversarial convergence
  Reviewer (fresh context) audits artifact → Executor fixes → repeat

Oscillation detection:
  Type O (overturn), Type R (repeat), Type F (flip), Type S (swing)
  → hard stop or escalate to user after threshold
```

| Role | Actor | Key Constraint |
|------|-------|----------------|
| **Orchestrator** | Main dialog agent | Never doubles as Reviewer/Executor; only manages loop + semantic judgment |
| **Reviewer** | Fresh Spawn each round | **Brand-new context** (no access to prior dialog); self-contained prompt |
| **Executor** | Fresh Spawn each round | Brand-new context; self-contained prompt |

## Termination States

Artifacts exit the convergence loop through one of five states (see `SKILL.md`):

| State | Summary |
|-------|---------|
| **Terminate-a Strict first-pass** | Fresh reviewer's first verdict = `executable`, zero blocking issues |
| **Terminate-b Asymptotic** | blocking_issues monotonically decreasing to ≤1 low-severity item, user confirms |
| **Terminate-c Subjective acceptance** | User explicitly says "good enough" |
| **Budget gate block** | gate returns `BLOCK:*`; no valid extension → no further spawn; user chooses extend / accept / simplify / terminate |
| **Oscillation hard-stop** | Type O/R threshold reached, automatic stop |

## Budget execution

The spawn budget for a convergence is adjudicated by the deterministic script `scripts/budget_gate.py` before and after every spawn — it does not rely on the Orchestrator remembering counts. The pipeline:

```
reserve → Agent spawn → settle → ingest-verdict
```

- **reserve**: request quota before spawn; only `PROCEED:<rid>` permits spawn, otherwise act on the verdict
- **settle**: record the outcome after spawn (succeeded requires an instance_id)
- **ingest-verdict**: once the reviewer verdict is persisted, drives mode tracking and marginal-decrement judgment

### Current capability tiers

| Mode | Capability | Current frameworks |
|------|-------------|-------------------|
| `auditable-only` | Universal; Orchestrator calls reserve/settle; ledger, extension chain and pre-push hook provide audit and blocking | opencode, Codex, and all frameworks (default) |
| `best-effort guarded` | Claude Code; adds an independent, monotonic Agent-spawn total-cap hook on top of auditable-only (= hook-blocked auditable-only) | Claude Code |
| true `enforced` | Not yet implemented; requires role FSM, role non-forgeability and permission lock-down | (deferred) |

> `best-effort guarded` is **not** `enforced` — it only enforces a **total spawn cap**: it does not perform per-scope reserve/settle (still Orchestrator-driven), does not defend against active deletion or tampering of the hook/binding, and the hook writes no ledger (no double-counting with the ledger). It addresses drift, forgetting, and post-compaction loss of control.

### Budget-block handling

When a budget limit is hit the gate returns `BLOCK:budget_exhausted` / `blind_exhausted` / `ultraverge_exhausted` / `total_spawn_cap`: **stop**. No further spawn is allowed without a valid `budget_extension` (must reference a real BLOCK decision event + the user's verbatim quote). The user chooses: extend and continue / accept the current artifact (terminate-c) / simplify the plan / terminate.

## When to use

- Plans, specs, or code artifacts that need independent cross-validation before execution
- Complex artifacts where a single review pass isn't sufficient
- Quality-critical deliverables where you want **zero blocking issues**
- Composable as a **quality gate** in Dynamic Workflows (L1 signal detection + L2 single-round adversarial review)

## Not for

- Single-pass quick reviews (use a lighter skill)
- Lint-level checks (use actual lint tools)
- Tasks simple enough to need no adversarial verification

## Structure

```
converge/
├── SKILL.md                  # Entry point: Orchestrator workflow + abstract capability layer
├── CONSTITUTION.md           # Constitutional design principles + governance file list
├── scripts/
│   ├── budget_gate.py        # Budget gate (file-authoritative, reserve/settle/ingest-verdict/bind + PreToolUse hook)
│   ├── l1_gate.py            # L1 signal detection (non-LLM, zero token cost)
│   ├── distill_antipatterns.py  # Antipattern distiller (compiles retrospective → status)
│   └── hooks/
│       ├── pre-commit        # Pre-commit check
│       ├── pre-push          # Pre-push check (orphan reservation / stale detection)
│       └── stale-check.py    # active/ stale-item detection
├── tests/
│   └── test_budget_gate.py   # Budget gate acceptance tests (49 tests, stdlib only)
└── refs/
    ├── contract-negotiation.md    # Round 0: contract negotiation flow + contract.md format
    ├── decomposition-protocol.md  # Hierarchical parallel convergence: decomposition & phased control
    ├── orchestrator-guide.md      # Loop management, oscillation detection, state tracking
    ├── reviewer-prompt.md         # Reviewer prompt template + hard rules
    ├── executor-prompt.md         # Executor prompt template + anti-pattern defenses
    ├── rubrics.md                 # Subjective quality scoring dimension library
    ├── state-schema.md            # Cross-round state persistence schema
    ├── testing-toolbox.md         # External verification tools (lint, tests, hooks)
    ├── quality-gate.md            # Quality gate protocol for Dynamic Workflows integration
    ├── design-review-prompt.md    # Post-convergence design review: 7-dimension advisory
    ├── antipatterns.md            # Antipattern registry (compiled product, distill-maintained)
    └── model-tiers.md             # Executor model tier reference table
```

## Verification

```powershell
python -W always::ResourceWarning tests/test_budget_gate.py
python -m py_compile scripts/budget_gate.py tests/test_budget_gate.py
git diff --check
```

Expected: 49 tests OK, no ResourceWarning. The budget gate has no external dependencies (stdlib only).
