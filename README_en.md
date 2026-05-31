# converge — Dual-Agent Iterative Convergence

Dual-agent iterative convergence for AI-generated artifacts. Instead of scripted workflows, converge uses **adversarial review cycles** between independent agents to drive quality through iteration — until Reviewer delivers a `executable` verdict or a stop condition is triggered.

> **Framework-agnostic**: Reviewer / Executor spawning and continuation are implemented via an abstract capability layer (Spawn / Continue / Identify), not tied to any specific framework API.

## Philosophy

**Don't tell the model how to walk. Tell it what "arrived" means, give it test tools, and let it find the path.**

Converge follows the Bitter Lesson: manually injected workflow structures (spec, scripts, hardcoded roles) decay as models improve. Instead, it defines **acceptance criteria** (contract), **verification tools** (lint, tests), and **adversarial feedback** (independent Reviewer) — then lets the model explore until it passes.

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

## Convergence Criteria

| Mode | Criteria |
|------|----------|
| **Strict first-pass** (default) | Fresh reviewer's first verdict = `executable`, zero blocking issues |
| **Asymptotic** | blocking_issues monotonically decreasing + ≤1 undisputed low-severity item remaining, user confirms |
| **Subjective acceptance** | Doesn't meet above, but user explicitly says "good enough" |

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
├── scripts/
│   └── l1_gate.py            # L1 signal detection (non-LLM, zero token cost)
└── refs/
    ├── contract-negotiation.md    # Round 0: contract negotiation flow + contract.md format
    ├── decomposition-protocol.md  # Hierarchical parallel convergence: decomposition & phased control
    ├── orchestrator-guide.md      # Loop management, oscillation detection, state tracking
    ├── reviewer-prompt.md         # Reviewer prompt template + hard rules
    ├── executor-prompt.md         # Executor prompt template + anti-pattern defenses
    ├── rubrics.md                 # Subjective quality scoring dimension library
    ├── state-schema.md            # Cross-round state persistence schema
    ├── testing-toolbox.md         # External verification tools (lint, tests, hooks)
    └── quality-gate.md            # Quality gate protocol for Dynamic Workflows integration
```
