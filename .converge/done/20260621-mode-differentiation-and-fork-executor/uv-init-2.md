---
round: ultraverge-initial-2
reviewer_backend: claude-code
reviewer_instance_id: ac180905e1e5941df
verdict: 阻断需修复
---

# Ultraverge Initial Review 2

## Reviewer 完整输出（逐字）

verdict: 阻断需修复

### blocking_issues

**B1 — 「零代码改动 / 零测试 diff」主张被源码证伪**（plan_defect, structural, plan_amendment_required）
默认值定义在 `scripts/budget_gate.py:55` DEFAULTS（max_blind_rechecks=2），`cfg()`（172-173）回退 `state.config[key] else DEFAULTS[key]`——要让普通模式生效值=1 必须改第 55 行，否则未写 config 覆盖的普通收敛仍取 2，A1 完全不生效。`default_total_cap`（348-352）含 `+ cfg(...,"max_blind_rechecks")`，stock 从 2→1 使总量 44→42，而 `tests/test_budget_gate.py:604` 硬断言 `assertIn("cap=44", out)` 必红。修复：补 budget_gate.py:55 与 test:604 两处源码改动并撤销虚假不变量；或改"ultraverge 写 config=2、普通不动默认"的反向分层（但与用户"普通改 1"诉求相悖）。
location: plan §A1 + 改动清单脚注 + 不变量#6 ; budget_gate.py:55,348-352 ; tests:604

**B2 — 总量公式重算被留作 TODO，未在 plan 内给出确定结论**（plan_defect, implementation）
A-2「核对公式仍单调」、Q4 悬而未决。代核：普通 base=3+3+5×4+1+1=28 → cap=42；ultraverge override blind=2 → base=29 → cap=44。两者均正整数、单调、无下溢/误阻断（total_safety=1.5 已含 consumes:none 余量）。Q4「边界下溢风险」答案=无。但 plan 把可机械核验结论留空交 Reviewer 现算，违反"plan 自足"：执行 agent 不重算 test 期望(42)就撞红灯。修复：A-2 与不变量写死 42/44，test:604 期望按模式取值。
location: plan §A1 设计第三点 / A-2 / Q4 / 不变量#1 ; budget_gate.py:348-352

### suggestion_issues
- tier 命名裂缝：budget_gate.py `TIER_VALUES={"enforced","auditable-only"}`（356），"best-effort guarded" 纯文档别名；B-4 改 §A.1 时不可把它当 ledger tier 值传入，否则 `_validate_event`（433）FAIL_CLOSED。
- fork↔hook 交互（plan 未显式论证但成立）：`subagent_type: fork` 仍经 Agent 工具，PreToolUse `matcher:"Agent"` 按工具名匹配、不按 subagent_type，故 fork 照常被 hook 计数、照常走 reserve --role executor（consumes none，占 total 不占 per-scope）。不变量#5 成立。建议 B-4 一句话点明。
- 建议 retrospective 写明"本次收敛不构成 fork 收益实证、仅为设计批准"。

### design_review_7dim
- consistency: concerns（不变量#6/脚注与 budget_gate.py:55、test:604 冲突；Q4 结论与 A-1 未对账）
- completeness: concerns（公式 42/44 缺位；test 期望同步未进清单）
- maintainability: clean
- boundary_clarity: clean（fork 边界表与 ROLE_CONSUMES、#7 立法意图一致；A2 分类表逐字保留宪法强制点）
- residue_redundancy: clean（Occam：fork=Spawn 参数化变体非新原子）
- portability: clean（opencode/codex 无 fork 降级 fresh 并标注）
- scalability: clean

fidelity_to_user: faithful（含必要诚实纠偏）

## Orchestrator 处理记录
- **[Orchestrator Detection]** verdict=阻断需修复。B1 与 R1-B1 同源 → 合并。B2（公式 42/44 具体化）与 R1-B2（公式符号）、R3-S1 同域，合并为收敛 B2/B3 处理。fork↔hook 成立结论降低 R 间复核成本。
