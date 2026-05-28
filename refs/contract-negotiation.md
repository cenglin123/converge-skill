# 合同谈判（Round 0）参考

> 在正式收敛循环之前，Executor 和 Reviewer 先就"什么算完成"达成一致。借鉴 GEP 的合同谈判机制。

---

## 触发条件

所有收敛对象**默认进入**合同谈判。用户可显式跳过（紧急修复、对象过于简单），Orchestrator 在 `_orchestrator-state.md` 中记录跳过理由。

Round 0 **不计入** Round 计数预算（max_outer_loops），但 token 消耗照常计入。

---

## 流程

```
1. Executor 提议
   Orchestrator spawn Executor，给出收敛对象 + plan
   → Executor 输出「验收合同」：每个交付物对应的验收断言（具体、可测试）

2. Reviewer 挑战
   Orchestrator spawn Reviewer（独立 context），给出同一对象 + plan + Executor 的合同草案
   → Reviewer 逐条审查：断言是否充分？是否过弱？提出补充/加强建议

3. 合同定稿
   Orchestrator 将 Reviewer 挑战反馈交给 Executor
   → Executor 修订合同，输出终版
   → Orchestrator 写入 contract.md

4. 后续轮次
   Round 1+ 的 Reviewer 以 contract.md 为评判依据，不自行发明标准
   若 Reviewer 认为 contract 本身有缺口 → 标 `[contract_amendment_required]: true`
```

---

## contract_amendment_required 流程

与 `plan_amendment_required` 同构：

1. **谁修订**：Reviewer 标 `contract_amendment_required: true` 后，Orchestrator **先回写 contract.md 本体**（追加/修订断言），再让 Executor 按新 contract 调整下游产物。contract.md 始终是 single source of truth。

2. **已 Accepted entries 的处理**：contract 修订后，Orchestrator 逐条审查 attempts.md 中所有已 Accepted entry。若某 entry 的验收依据因 contract 修订而失效，在 entry 下追加 `**[Contract Amendment at R{M}]**` annotation（不修改历史原文），标注：(a) 失效原因；(b) 是否需要 Executor 返工。返工产生的新 attempt 记为 R{M} entry，不影响原 entry 的 R{N} verdict。

3. **Type O 计数影响**：若 contract 修订导致已 Accepted 的修复方向与新 contract 矛盾，Orchestrator **不将此计入 Type O**——这是 contract 演进而非 reviewer 反复。在 annotation 中显式标注 `[Not Type O: contract amendment]`。

4. **attempt log 记录**：contract amendment 本身不产生 attempt entry（它不是 executor 修复），但触发的返工修复按正常 attempt entry 格式记录，在 `Issue` 字段引用 contract amendment 的变更摘要。

---

## contract.md 格式

```markdown
---
type: convergence-contract
object_slug: <slug>
rubric_dimensions: <逗号分隔的维度名，如 Correctness,Completeness,Consistency>
generated_at: <ISO datetime>
---

## 验收断言

| # | 交付物 | 断言 | 验证方式 |
|---|--------|------|----------|
| 1 | <具体交付物> | <具体、可测试的完成条件> | <text_review \| rubric_score> |

## Reviewer 挑战记录

（Round 0 中 Reviewer 提出的挑战 + Executor 的回应，保留历史）
```

**硬约束**：
- 断言必须**具体且可测试**——"代码质量好"不是断言，"所有公共函数有对应的单元测试"才是
- 断言覆盖 contract 中列出的所有 Rubrics 维度（如有）
- contract.md 一旦定稿，Round 1+ 中只有通过 `contract_amendment_required` 流程才能修改
