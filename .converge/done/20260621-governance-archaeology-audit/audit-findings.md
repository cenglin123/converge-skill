# Audit Findings — governance archaeology scan (2026-06-21)

2 independent reviewers (split scope: R1 core trio / R2 refs/), DR5 archaeology lens. Observation-only.

## 汇总：13 findings（2 P0 / 1 P1 / 6 P2 / 4 P3）

**关键信号**：2 个 P0 中**1 个是本次 landing 新引入的**（orchestrator-guide § 发散检测 的"placement 伴随说明"——我让 landing executor 写的迁移叙事，正是 DR5 禁的"原停于/迁移至"模式）。审计验证了你的直觉：考古是反复出现的、连我刚收敛完都重犯的模式。

## P0（必须修）

| # | 文件 | 位置 | 问题 | 来源 |
|---|------|------|------|------|
| 1 | framework-adapters.md | line 3（文件头） | "从 SKILL.md 外提。保留原 A.x 小节编号"——文件首行就是迁移叙事 | 旧（历史外提） |
| 2 | orchestrator-guide.md | line 131（§发散检测 placement 伴随说明） | "本节内容原停于 GD-2 §判例...迁移至操作指导层...保留作历史快照...本次迁移专用"——整段自我迁移叙事 | **新（本次 landing 引入）** |

## P1（应修）

| # | 文件 | 位置 | 问题 |
|---|------|------|------|
| 3 | SKILL.md | line 103 | "A2 不扩大授权"——"A2"在全文无定义，悬空指针 |

## P2（建议修）

| # | 文件 | 位置 | 问题 |
|---|------|------|------|
| 4 | CONSTITUTION.md | line 53 | "2026-06-19 经用户明确确认批准"——规则括注里的过去审批时戳（GD-1 指针已足够） |
| 5 | SKILL.md | line 397 | "20260618 plan §enforced 为 deferred 目标设计"——历史 plan 悬空指针（plan gitignore 不可达） |
| 6 | SKILL.md | line 397 | "从 prose 迁移到 file-authoritative gate"——迁移史叙事 |
| 7 | GOVERNANCE-DECISIONS.md | line 21（GD-1 关联产物） | active/ 路径（plan 已归档至 done/）——stale pointer |
| 8 | orchestrator-guide.md | line 127（§发散检测 案例摘要） | "经历 3 轮...仲裁裁决...→放弃"——嵌入的过去时案例叙事（GD-2 pointer 合法，但叙事段是考古） |
| 9 | orchestrator-guide.md | line 412（§九） | "如本次②"——悬空指向某次收敛的 #2 项 |
| 10 | state-schema.md | line 273 | "预算执行从 prose 计数迁移到 file-authoritative gate"——迁移叙事 |

## P3（可选清理）

| # | 文件 | 位置 | 问题 |
|---|------|------|------|
| 11 | GOVERNANCE-DECISIONS.md | line 38（GD-2 关联产物） | "handoff brief 已删"——关联产物列了不存在的产物 |
| 12 | framework-adapters.md | line 27 | "直击 31 轮失控的成因"——历史事件引用 |
| 13 | framework-adapters.md | line 52 | "审计已冻结其枚举转测试"——过去审计动作 |

## 合法历史（不算考古，不清理）

- GD-1/GD-2 的 dated 记录 + 用户确认交互（audit log 职能）
- GD-1 背景"31 轮失控复盘"（决策 context，合法）
- GD-2 注"早先 agent 误自标 approved 经回退"（audit 完整性证明）
- GD-2 §判例 主体（当前态指导，"本次"引用是合法判例来源）
- SKILL.md Pilot 经验速查（intentional 经验蒸馏节）
- antipatterns.md last_distilled_at（compiled registry metadata）
- 指向 GD 的 pointer（"见 GD-1/GD-2"——合法性溯源，非叙事）

## 对齐率

- R1（核心三件）：~99% 行级 clean，6 命中集中在 SKILL.md line 103/397 + GD 关联产物
- R2（refs/）：~88%，9 文件中 6 完全 clean（reviewer/executor-prompt, design-review-prompt, contract-negotiation, decomposition-protocol, antipatterns），考古集中在 3 文件（framework-adapters / orchestrator-guide / state-schema），且**集中在最近编辑的节**（验证"近期编辑=高风险"假设）

## 处置建议

- **P0（2）必修**：尤其 #2 是我本次 landing 自己引入的，讽刺但必须立即清
- **P1（1）应修**：SKILL.md "A2" 悬空
- **P2（6）建议修**：多数是删一行/改现在时的小修
- **P3（3）可选**：轻微，可批量或延后

修复方式：多数是 **删/改写为现在时**（不涉语义变更，仅清理考古）。可走轻量收敛（单 reviewer 验收）或直接 executor 修 + 你批准。
