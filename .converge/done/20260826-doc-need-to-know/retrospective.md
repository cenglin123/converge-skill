---
type: retrospective
object_slug: 20260826-doc-need-to-know
generated_at: 2026-08-26T06:25:00+00:00
---

# Retrospective · 20260826-doc-need-to-know

## 1. 结束模式

收敛完成（ultraverge 路径：3 并行扩域评议一次性"阻断需修复" → 完整主循环收敛（outer R1-R8）→ 全新上下文盲审 #2 verdict = `可执行` 零阻断 → 收敛后设计审查完成（单轮咨询式，advisory，不阻断））。
流程定位：本次收敛对象为 SKILL.md / refs/ / scripts/ 的"agent-need-to-know 削减"方案，属受保护文档（SKILL.md/CONSTITUTION 第三部）变更，故按 CONSTITUTION 修宪/受保护文档程序走 ultraverge。

## 2. 阻断轨迹

| 阶段 | 轮次 | verdict |
|------|------|---------|
| ultraverge 3 并行评议 | uv-init-1 / 2 / 3 | 3 × 阻断需修复 |
| 主循环 outer | R1-R3 | 阻断需修复 |
| | R4 | 可执行 |
| | R5-R8 | 阻断需修复（渐进式新发现） |
| 盲审 | blind-recheck-1 | 阻断需修复 |
| | blind-recheck-2 | 可执行（0 阻断，3 建议） |

整体非单调：R4 一度可达执行，R5-R8 又爆出精度/语义新问题；最终由 blind-recheck-2（全新上下文、blank-slate authority）收敛到可执行。

## 3. Antipattern 巡查

executor 对 8 条合并阻断（+R5-R8 渐进新问题）的修复真实落地。盲审 #2 以全新上下文独立复核，确认"已落地/前序已单源"delta 边界诚实、8 行等价表与正文一致、作者基准（granted_at_usage==observed_usage / user_quote 不校验）与机器校验跨引用闭合；未出现 history 依赖、report_hallucination、solution_anchoring、over_compromise。

## 4. Executor 路径依赖评估

Executor 修复路径正确：保留具名锚点（角色对照表/任务档预算）、单源化指针、丢弃纯机器 JSON schema 重复、行号降级为 reference-only。盲审 #2 确认唯一未闭合点（首次等价表 7 行 vs 实际 8 行）在修正后闭合。

## 5. Reviewer 间 Verdict 分歧分布

| 阶段 | Verdict | 合并后阻断数 |
|------|---------|-------------|
| uv-init 3 并行 | 3 × 阻断需修复 | 8 |
| 主循环 R1-R8 | 可执行(R4) / 阻断需修复(其余) | 渐进 |
| 盲审 #1 | 阻断需修复 | 1 |
| 盲审 #2 | 可执行 | 0 |

## 6. 降级影响评估

无降级。全部 Reviewer/Executor 通过 dsh-subagent Spawn（deepseek-official / deepseek-v4-flash）；Continue/SendMessage 本轮未使用（环境限制，与前序一致）。

## 7. 经验教训

1. **need-to-know 判定三角可行**：删除判据 = (a) 脚本 fail-closed 保证 / (b) 纯实现描述 / (c) 脚本计算值复述。凡涉及 agent 仍需判断或义务的纯叙述一律保留（M-11 三义务、锚点 角色对照表/任务档预算、authority 校验）。
2. **保留具名锚点、删纯机器 schema** 是安全边界：state-schema §预算 gate 只删 PURE MACHINE JSON schema，保留两个具名锚点，避免"删内容"退化为"删契约"。
3. **行号/数字引用易漂移**：计划多处行号与"8 行"计数被历轮点名；最终统一为 reference-only（行号仅供参考，不作为硬契约），契合"脚本兜底、agent 判断"哲学。

## 8. 后续建议

1. 用户决策设计审查 highlights 的处置（采纳/延后/忽略），录入 §11。
2. 用户确认后按计划落地（SKILL.md / orchestrator-guide.md / state-schema.md / budget_gate.py docstring / quality-gate.md 指针 + 新增等价映射文件）。
3. 本 retrospective 与前序收敛构成新语料，可运行 `scripts/distill_antipatterns.py`。

## 9. Round 0 合同谈判评估

| 维度 | 评估 |
|------|------|
| 是否启用 | 否（计划自带验收标准，与前序 ultraverge 一致） |
| contract_amendment 触发次数 | 0 |

## 10. Rubrics 评估

| 维度 | 评估 |
|------|------|
| 使用维度 | 7 维骨架（DR1-DR7）注入 ultraverge 评议；主循环以 plan 验收标准 + 判定三角为主 |
| portability | clean（plan 类对象区分度低，与前序一致） |

## 11. 设计审查发现与用户决策（待录）

设计审查为单轮咨询式（advisory，不阻断），产出见 design-review.md。最核心 highlight：

> 单一权威源未落实到预算扩展令牌（budget_extension）这一最需要单源的路径——同一记录在脚本(validate_extensions)、guide §六(作者基准)、state-schema L437(校验细节)三处描述，且 user_quote 被明确排除在脚本单源之外，authoritative 归属悬空。建议为 budget_extension 指定唯一"作者字段清单权威"（guide §六），state-schema 与脚本仅保留"校验视角"并明确"字段清单以 guide 为准"；同类建议把 SKILL.md 硬编码 63/62 与 [^mbr] 调优历史改为"以脚本 DEFAULTS/公式为准"或标注 as-of 日期。

用户决策：**已采纳（部分，2026-08-26）** —— 1) budget_extension 单一权威源由 guide §六 作为作者字段清单权威落地（计划本身已覆盖）；2) 用户指示将 SKILL.md 的 `普通=63 / ultraverge=62` 一行标注为「以 `scripts/budget_gate.py` DEFAULTS/公式为准」（以脚本为数值单源，避免再漂移）。
详见 `.converge/done/20260826-doc-need-to-know/design-review.md`。
terminal_decision_event_id: c4d42f8c-0c7b-406a-a3b2-d86efecaa2b3
terminal_decision_value: 可执行
