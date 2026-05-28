# State & Log 格式规范

> 本文件定义 `.converge/` 下所有持久化文件的格式。写文件时参考此处。

---

## 一、Round Log（`round-N.md`）

```markdown
---
round: N
reviewer_backend: <实际 Spawn 后端，如 claude-code | opencode | codex | orchestrator_self>
reviewer_instance_id: <Spawn 返回的 instance_id>
generated_at: <ISO datetime>
---

# Round N · <对象 slug>

## Reviewer 完整输出

[reviewer agent 返回的原始内容，逐字记录，不做摘要]

## Orchestrator 处理记录

[orchestrator 在本轮做的判定，每条以 **[Orchestrator Detection]** 前缀]

- **[Orchestrator Detection]** Type O 检测：本轮 issue {n} 与 Round {m} 接受的修复方向相反 → 在 attempts.md 追加 overturn annotation
- **[Orchestrator Detection]** Type R 等价标注：本轮 issue {x} 与 Round {y} issue {z} 标记为同源（理由：xxx）
- ...
```

---

## 二、Attempt Log（`attempts.md`，跨轮累加）

每个修复尝试一段，按时间顺序排列。

```markdown
## Round N attempt · issue {issue_id}
- source: <converge_loop | user_external_input>   # 收敛后修订时填 user_external_input
- reviewer_backend: <实际 Spawn 后端>
- Issue: <reviewer 原话引用，保留措辞强度>
- Issue 归因（reviewer 判定）: plan_defect | executor_limit
- plan_amendment_required: true | false
- Approach: <executor 一句话修复思路>
- Diff: <commit hash | inline 段落变更>
- R{N} verdict: Accepted | Rejected
- **[Orchestrator Detection at R{M}]** Status changed to: Overturned   # 仅当后续轮次推翻时追加
  - Overturned by: R{M}
  - R{M} 原话（引用）: "..."
  - Orchestrator 判定理由: <一句话>
  - Net effect: <reverted / partially undone / 等>
```

**硬约束**：

1. 历史 entry **不改写**，只**追加 annotation**（保留诚实历史）
2. `reviewer_backend` 字段**必填**，如实记录实际后端（Spawn 失败降级时填 `orchestrator_self`）
3. `Issue 归因` 字段**必填**，二元归因（plan_defect / executor_limit），不允许"warning / 不重要"
4. 所有语义判定以 `**[Orchestrator Detection]**` 前缀标记
5. Reviewer comment 必须**原话引用**，不允许摘要转述

---

## 三、Orchestrator State（`_orchestrator-state.md`）

> 抗 compact / 抗 session 切换的根本机制。每个收敛对象目录下一份。

```markdown
---
type: orchestrator-state
object_slug: <对象 slug>
generated_at: <ISO datetime>
last_updated_at: <ISO datetime>
---

# Orchestrator State · <对象 slug>

## Current Position

- current_round: N
- current_phase: <round-0-propose | round-0-challenge | round-0-finalize | round-N-review | round-N-execute | completed>
- last_completed_action: <一句话描述>
- next_pending_action: <一句话描述>
- progress_summary: <人类可读进度摘要，如 "R2: 1/3 blocking fixed, 2 remaining (B2=反面论证, B3=偏差分析)">

## Round 0 State

- contract_status: <pending | completed | skipped>
- skip_reason: <跳过理由（仅 skipped 时填写）>
- contract_path: <contract.md 路径（仅 completed 时填写）>
- rubric_dimensions: <逗号分隔的维度名（仅 completed 时填写）>

## Unapplied Amendments

| Source | Target | Status |
|--------|--------|--------|
| R{X} blocking #{Y} | <plan 段或文件路径> | pending / applied |
| R{X} contract_amendment | contract.md | pending / applied |

## Active Instance Registry

| Round | Instance ID | Role | Status |
|-------|-------------|------|--------|
| 0 | <instance-id> | contract-proposer | completed |
| 0 | <instance-id> | contract-challenger | completed |
| 0 | <instance-id> | contract-finalizer | completed |
| 1 | <instance-id> | reviewer | completed |

## Compact Recovery Notes

- <ISO datetime> · <动作摘要 + 与 plan/charter 的对应关系>
```

**维护规则**：
1. 每次完成 Spawn / amend / log 等独立动作后**立即更新**
2. `current_round` 始终是"已写完 round-N.md 的最大 N"
3. `next_pending_action` 必须具体到可直接执行，不允许"继续推进"

---

## 四、Retrospective（`retrospective.md`）

收敛完成后写入 `done/<slug>/`。

```markdown
---
type: retrospective
object_slug: <对象 slug>
generated_at: <ISO datetime>
---

# Retrospective · <对象 slug>

## 1. 结束模式
（收敛 / 预算软停 / 振荡硬停，说明具体条件）

## 2. 阻断轨迹
R1={n} → R2={m} → ... → R{k}=0，单调/非单调

## 3. Antipattern 巡查
| Round | 类型 | 对象 | 触发结果 |
|-------|------|------|---------|

## 4. Executor 路径依赖评估
（反折中 / 方案锚定 / 最小补丁 实际触发情况）

## 5. Reviewer 间 Verdict 分歧分布
| 轮次 | Verdict | 阻断数 | 归因分布 |

## 6. 降级影响评估（如有降级）
（若使用了 orchestrator_self 或 inner_loop 降级，讨论对结论可靠性的影响）

## 7. 经验教训
（机制层面 + 对象层面的发现）

## 8. 后续建议

## 9. Round 0 合同谈判评估

| 维度 | 评估 |
|------|------|
| 是否启用 | 是 / 否（跳过理由：___） |
| contract 是否减少预期错位 | （对比有/无 contract 时"Executor 误解需求"类 issue 占比） |
| contract_amendment 触发次数 | N 次 |
| contract 与 plan 的同步性 | （是否出现 plan 修订但 contract 未跟进） |

## 10. Rubrics 评估

| 维度 | 评估 |
|------|------|
| 使用的维度 | 哪些维度被实际引用 |
| 未使用/总高分的维度 | 是否有维度从未触发低分（→ 考虑移除） |
| rubric_gap 触发次数 | N 次（Reviewer 认为 Rubric 未覆盖的问题） |
| 跨轮分数趋势 | 各维度分数在轮次间的变化 |
```

## 11. 收敛后修订记录（如有）

若收敛后因用户外部输入触发修订，追加本节：

```markdown
## 11. 收敛后修订记录

### 修订 {N}
- **触发来源**：用户外部输入
- **触发时间**：<ISO datetime>（原收敛完成后 X 天/小时）
- **输入摘要**：<一句话描述用户提供的新视角/信息>
- **影响范围**：<哪些章节/结论受影响>
- **新增轮次**：R{k+1} → R{k+m}
- **结论变化**：<原结论> → <修订后结论>
- **Reviewer 验证**：<fresh reviewer verdict>
```

> 若为层级收敛（启用 decomposition-protocol.md），在 §10 之后追加 **§11. 层级收敛评估**，格式见 `decomposition-protocol.md` §Retrospective 扩展。
