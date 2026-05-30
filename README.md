# converge — 双 Agent 迭代收敛器

Dual-agent iterative convergence for AI-generated artifacts. Instead of scripted workflows, converge uses **adversarial review cycles** between independent agents to drive quality through iteration — until zero blocking issues remain.

## Philosophy

**Don't tell the model how to walk. Tell it what "arrived" means, give it test tools, and let it find the path.**

Converge follows the Bitter Lesson: manually injected workflow structures (spec, scripts, hardcoded roles) decay as models improve. Instead, it defines **acceptance criteria** (contract), **verification tools** (lint, tests), and **adversarial feedback** (independent reviewer) — then lets the model explore until it passes.

## How it works

```
Round 0: Contract negotiation
  Executor proposes acceptance criteria → Reviewer challenges → final contract

Round 1+: Adversarial convergence
  Reviewer (fresh context) audits artifact → Executor fixes → repeat

Oscillation detection:
  Type O (overturn), Type R (repeat), Type F (flip), Type S (swing)
  → hard stop or escalate to user after threshold
```

| Role | Actor | Constraint |
|------|-------|------------|
| **Orchestrator** | Host agent | Manages loop, detects oscillation, tracks state |
| **Reviewer** | Fresh sub-agent each round | Independent context, adversarial stance |
| **Executor** | Sub-agent | Fixes issues, records attempts in cross-round log |

## When to use

- Plans, specs, or code artifacts that need independent cross-validation before execution
- Complex artifacts where a single review pass isn't sufficient
- Quality-critical deliverables where you want **zero blocking issues**

## Not for

- Single-pass quick reviews (use a lighter skill)
- Lint-level checks (use actual lint tools)
- Tasks simple enough to need no adversarial verification

## Structure

```
converge/
├── SKILL.md                  # Entry point: orchestrator workflow + abstract capability layer
├── scripts/
│   └── l1_gate.py            # L1 signal detection (non-LLM, ~50 lines)
└── refs/
    ├── contract-negotiation.md    # Round 0: acceptance criteria negotiation
    ├── decomposition-protocol.md  # Breaking complex artifacts into reviewable units
    ├── orchestrator-guide.md      # Loop management, oscillation detection, state tracking
    ├── reviewer-prompt.md         # Reviewer prompt template + hard rules
    ├── executor-prompt.md         # Executor prompt template + anti-pattern defenses
    ├── rubrics.md                 # Scoring dimensions for subjective quality
    ├── state-schema.md            # Cross-round state persistence schema
    ├── testing-toolbox.md         # External verification tools (lint, tests, hooks)
    └── quality-gate.md            # Quality gate protocol for Dynamic Workflows integration
