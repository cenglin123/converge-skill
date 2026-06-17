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
- source: <converge_loop | user_external_input | blind_recheck | factual_self_adjudication | user_arbitration>   # 收敛后修订 user_external_input；盲审 blind_recheck；agent 事实自裁剔除填 factual_self_adjudication；用户仲裁被驳回填 user_arbitration
- reviewer_backend: <实际 Spawn 后端>
- Issue: <reviewer 原话引用，保留措辞强度>
- Issue 归因（reviewer 判定）: plan_defect | executor_limit | pending | reviewer_factual_error   # pending 仅限 source: blind_recheck；reviewer_factual_error 仅限 source ∈ {factual_self_adjudication, user_arbitration}（reviewer 事实误读导致的剔除）
- plan_amendment_required: true | false
- Approach: <executor 一句话修复思路>
- Diff: <commit hash | inline 段落变更>
- R{N} verdict: Accepted | Rejected   # source ∈ {factual_self_adjudication, user_arbitration} 且为事实矛盾剔除时，verdict 取 Rejected，并在下一行追加 `- Rejection reason: factual_error`
- **[Orchestrator Detection at R{M}]** Status changed to: Overturned   # 仅当后续轮次推翻时追加
  - Overturned by: R{M}
  - R{M} 原话（引用）: "..."
  - Orchestrator 判定理由: <一句话>
  - Net effect: <reverted / partially undone / 等>
```

**硬约束**：

1. 历史 entry **不改写**，只**追加 annotation**（保留诚实历史）
2. `reviewer_backend` 字段**必填**，如实记录实际后端（Spawn 失败降级时填 `orchestrator_self`）
3. `Issue 归因` 字段**必填**，归因为 plan_defect / executor_limit / pending（仅限 source: blind_recheck）/ reviewer_factual_error（仅限 source ∈ {factual_self_adjudication, user_arbitration}），不允许"warning / 不重要"。pending 适用条件：仅当 issue 来源为盲审复核（source: blind_recheck）时可用，且不得跨过下一主循环轮存活。reviewer_factual_error 适用条件：仅当 blocking 因 reviewer 事实误读被自裁或用户仲裁剔除时。**Consumer 契约**：pending 值仅对 source: blind_recheck 条目合法，且在该条目对应的下一主循环轮结束时必须已落定为 plan_defect 或 executor_limit；reviewer_factual_error 值在归因统计时归入"reviewer 过失"类，不计入 plan/executor 归因分布。Consumer 在做归因统计时应排除 pending 值或将其标记为 attribution_incomplete
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
- boundary_check: <pass | violated>（每轮角色边界自检结果，Orchestrator 是否仅执行循环管理+语义判定而未直接修改产物）
- boundary_violation_detail: <可选，描述违反情况>
- rule_frequency:
    boundary_guard: {triggered: <true|false>, zero_streak: <int>}
    reviewer_boundary_audit: {triggered: <true|false>, zero_streak: <int>}
    intent_drift_check: {triggered: <true|false>, zero_streak: <int>}
    gate_l1: {triggered: <true|false>, zero_streak: <int>}
    design_review_trigger: {triggered: <true|false>, zero_streak: <int>}
    blind_recheck: {triggered: <true|false>, zero_streak: <int>}

**规则 key 注册表**（权威来源，与 `refs/antipatterns.md` 的 id 机制同构）：

| 规则 key | 对应机制 | 触发检测方式 | 分类 |
|----------|----------|-------------|------|
| `boundary_guard` | 主循环 c+1 guard step | `boundary_check: violated` in state | guard |
| `reviewer_boundary_audit` | Reviewer 硬纪律 #7 | `source: orchestrator_self` in attempts.md | guard |
| `intent_drift_check` | 意图漂移检查 | `drift_detected: true` in reviewer output | guard |
| `gate_l1` | 门控 L1 信号检测 | L1 gate 脚本执行记录 in state | guard |
| `design_review_trigger` | 设计审查触发判断 | 设计审查 spawn 事件 in state | guard |
| `blind_recheck` | 盲审复核 | `blind_recheck` 字段出现在 retrospective 中即 triggered（`waived` 不计入命中率，算 zero_streak 递增） | guard |

新增 guard mechanism 时，在注册表追加条目并指定触发检测方式。未在注册表中的规则不被追踪。触发检测在各轮执行时实时记录（非 retrospective 时回溯），避免 context compaction 导致的触发遗忘。`zero_streak` 由 `distill_antipatterns.py` 跨收敛对象计算。

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

> **硬约束**：`类型` 列必须填 `refs/antipatterns.md` 中的 `id`（逐字一致）。
> 若发现清单外的新反模式，填 `new:<一句话描述>`，提示人工评估是否新增条目。
> 此约束确保 retrospective 可被 `distill_antipatterns.py` 可靠解析——
> id 与 reviewer-prompt.md `antipattern_observations.type` 枚举、
> antipatterns.md `id` 三处统一。

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

## 成本数据（可缺省）

| 阶段 | tokens | 时间 | agent 数 | 关键产出 |
|------|--------|------|----------|---------|
| R0 合同谈判 | — / ~K | — / ~min | — | — |
| R{N} Reviewer | ~K | ~min | 1 | — |
| R{N} Executor | ~K | ~min | 1 | — |
| 设计审查 | ~K | ~min | 1 | — |
| **总计** | **~K** | **~min** | **N** | — |

> token 和时间供后续收敛校准预算参数（max_outer_loops、gate_max_token_share 等）。
> 框架无法提供精确 token 计数时填估算值并标注 ≈。
> 阶段行按实际收敛流程增减（R0 无则删、inner loop 可合并到对应 outer round、设计审查未触发则删）。
> 跨 ≥3 次收敛积累后，按 totals 行估算单轮/单 agent 平均消耗，据此调整预算参数。
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

## 盲审复核（条件，仅当收敛经历 ≥2 轮时）

```yaml
blind_recheck:
  status: <pass | fail | waived>
  traces_reported: <int>      # A1 类修复痕迹举报数
  rounds_used: <int>          # 盲审轮次消耗（含重试）
  findings_count: <int>       # 盲审发现的阻断 issue 数
  escalated_to_main_loop: <bool>  # findings 是否注入主循环
```

- `waived`：仅终止-c（主观接受）+ 用户确认跳过盲审修复时使用。声称口径为"用户在已知盲审发现后主动接受"
- `waived` 不计入 rule_frequency 命中率（算 zero_streak 递增）
- 永不升格终止类型：终止-b + blind_recheck: pass 不重标为终止-a

## Rule Activity

| rule | triggered | zero_streak | status |
|------|-----------|-------------|--------|
| boundary_guard | <true/false> | <int> | active |
| reviewer_boundary_audit | <true/false> | <int> | active |
| intent_drift_check | <true/false> | <int> | active |
| gate_l1 | <true/false> | <int> | active |
| design_review_trigger | <true/false> | <int> | active |
| blind_recheck | <true/false> | <int> | active |

status 由 `distill_antipatterns.py` 的 `--rules` 模式按阈值计算（guard: 5/10, core: 20/40）。格式固定——脚本从表格解析。

> 若为层级收敛（启用 decomposition-protocol.md），在成本数据节之后追加 **§12. 层级收敛评估**（§11 预留给收敛后修订记录；两节均可缺省，编号固定不顺延——保证 distill 类脚本按节标题定位的稳定性），格式见 `decomposition-protocol.md` §Retrospective 扩展。
