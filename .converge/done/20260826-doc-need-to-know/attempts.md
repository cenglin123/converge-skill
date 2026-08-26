# Attempts Log — 20260826-doc-need-to-know

## ultraverge initial panel (rounds 1-3, parallel)

- Issue: 3-way panel returned 阻断需修复 with 8 consolidated fix directions. R1(判断/义务边界)2 blockers: acceptance#4 vs obligation-priority contradiction; M-11 mixed-backend pure-prose obligation. R2(冗余确认/哲学)5 blockers: budget-gate line-range wrong (L502, L506+ is output schema); dangling refs; sibling-plan conflict; M-11 3 pure-prose obligations; extension token authoring schema. R3(可执行/迁移完整性)5 blockers: silent_merge w/ sibling plan; unreachable line targets; protected migration; acceptance internal contradiction; formula deletion violates settled ruling.
- Approach: executor revised plan per consolidated adjudication: delta-on-landed-doc-layer-refactor (#16/6990314) with not-re-done table; keep max_total_reserved_spawns formula; DROP docs/budget-gate-contract.md (budget_gate.py = single authority; state-schema §预算 gate reduced to agent-relevant role summary, range L378-L502, L506+ carved out); no move-out -> no dangling refs; M-11 keeps 3 pure-prose obligations; checklist deletes only 2 truly-mechanical items, keeps 4 obligation reminders; extension token field schema kept as authoring basis; line targets -> reference-only.
- Diff: docs/plans/active/20260826-doc-need-to-know.md (rewritten, 136 lines)
- Status: Applied — pending outer Round 1 verification

## [manual-fallback] blind #2 ledger round-numbering correction (2026-08-26)

- 现象: 误将 blind #2 reserve 用 --round 3(应为 2),造成 blind 轮次 1/3 缺口,BLOCK:round_gap:blind,且 cancel/reserve/finish 全部被同校验拒。这是账户记账死锁,非内容问题。
- 处置: 手动移除 gate-ledger.jsonl 中 round-3 blind open reservation (f903decd21f7) 行;保留已有 blind #2 评审 verdict(可执行)并作为 round-2 产物 blind-recheck-2.md 落盘;重新 reserve round-2 + register。
- 原因: 工具 CLI 无绕过 round_gap 的下游修正路径;按宪法第二部兜底,以 manual-fallback + 显式告知用户处理。
