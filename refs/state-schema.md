# State & Log 格式规范

> 本文件定义 `.converge/` 下所有持久化文件的格式。写文件时参考此处。

## Archive Contract v1（规范单源）

`schema_id="converge.archive"`，`schema_version="1.0"`。读取按 schema dispatch，不按日期：无 manifest 为 `missing/legacy-unverifiable`；严格 JSON 失败（含重复 key、BOM、NaN/Infinity）为 `malformed`；缺版本、外部 schema 或更新版本为 `unsupported`；可识别 v1 但闭包失败为 `invalid`；全部通过为 `valid`。未知版本 fail-safe，scan 只读且不迁移。

### 权威与依赖

可执行单源是 `scripts/archive_contract/model.py`；本节解释同一字段和枚举。模块依赖固定为 `capture -> model <- transaction`、`presentation -> model`，CLI 只装配。采集期 owner 是 append-only events；budget settlement 唯一 owner 是 `gate-ledger.jsonl`；旧 revision owner 是 `evidence/revisions/<revision-id>/manifest.json`。归档时 manifest 是 owners 的冻结投影，INDEX 只从 manifest 生成，不能产生事实。

### Event 与主外键

公共字段：`schema_id/schema_version/event_type/event_id/sequence`。event id 为 UUID；sequence 在所有 event 类型中从 1 连续且无缺口。`invocation-started` 拥有 invocation kind（spawn/continue）、role、phase、round、attempt、parent、reservation、started_at 与 requested provenance；`invocation-terminal` 只引用 started event，拥有 terminal status、completed_at、host receipt、settlement ref 与 resolved provenance。同一 started 恰有一个 terminal。Continue 必须引用同 instance 的 Spawn parent。

terminal status 为 `succeeded|failed|cancelled|timeout`；仅 succeeded 必须有 output evidence。失败 reason 为 `backend-error|cancelled-by-host|timeout|process-interrupted`。terminal decision 是闭合联合：`reviewer-verdict` 只引用成功 fresh/blank-slate Reviewer terminal；`user-decision` 只用于 terminal-b/c，必须含 `user_quote/source_ref/presented_degradations/accepted_state`。`design-review-completion` 是 advisory，禁止出现在 `final_verdict_ref`。最终 round 与 retrospective 必须反向引用同一 decision event id/value。

`reviewer-verdict` 的 owner 授权（`REVIEWER_AUTHORITIES`：`fresh={reviewer,outer-reviewer,ultraverge-initial}`、`blank-slate={blank-slate-reviewer,blind-reviewer}`）由 `model.validate_reviewer_verdict_authority()` 统一实现，且在**两处**调用同一函数：`capture.record_terminal_decision`（写入前，越权角色的事实**不会被持久化**）与 `model.validate_event_graph`（归档时的结构化复核）。一个角色不在任一列表内（例如 `l2-gate-reviewer`——`refs/quality-gate.md` 定义的 "L2 重量级" Reviewer，对应 `scripts/budget_gate.py` `ROLE_CONSUMES` 的字面角色名 `l2-gate-reviewer`；consumes=none，是设计选择而非遗漏：门控"不否决不阻断"，只产出 `gate_findings`，绝不能登记为终局 owner）永远不能通过 `record_terminal_decision` 落盘为 reviewer-verdict 的 `reviewer_event_id`。

Round 表示由 `model.canonical_round()` 单点归一化：`round` 字段只有 `null`（Round 0 / 无轮次）或正整数两种合法值；调用方传入字面 `0` 会被这个函数自动归一化为 `null`——`budget_gate.py` 的 `cmd_reserve`（ledger `target_round`）与 `capture.begin_invocation`（invocation `round`）都调用同一个 `canonical_round()`，不允许一处写 `0`、一处要求 `null`。

requested provenance 字段为 `requested_provider/requested_model`；resolved 字段为 `resolved_provider/resolved_model/resolved_family/backend/backend_version`。`evidence_level=observed|host-reported|configured|inherited|unavailable`，`resolution_source=host_receipt|tool_response|cli_argument|agent_config|parent_instance|none`。configured/inherited 不得带 resolved model。partial/unavailable reason 仅允许 `backend-does-not-expose|receipt-missing|inherited-concrete-model-hidden|invocation-failed-before-resolution`。

`settlement_ref`（`invocation-terminal` 字段）由 `capture.complete_invocation` 自动生成规范值 `gate-ledger.jsonl:<reservation_id>`——仅当调用方**未显式传入** `settlement_ref` 且该 invocation 是持有 `reservation_id` 的 spawn 时触发；调用方仍可显式传入覆盖值（走基本格式校验：非空、有界字符串），但**不再需要**为常见路径手拼规范值。Continue（无 reservation）不受影响，`settlement_ref` 保持 `None`，语义不变。`gate-ledger.jsonl` 侧的 `ledger-settlement-ref` 交叉校验（archive 时）不变——若显式覆盖值与对应 reservation 不一致，仍会在 `validate_ledger` 处被拒绝。

### Evidence 与路径

`evidence_mode=metadata-only|redacted|exact` 分别映射 `identity-only|redacted-copy|snapshot`。hash 始终是原始输入字节 SHA-256（64 位小写 hex），size 是 byte；redacted 副本有自己的 hash/size，不能称 exact。workspace locator 仅含 `{kind,workspace_id,path}`；external 仅含 `{kind,display_locator,portable:false,authorization_ref}`，展示 locator 必须不可解引用，普通 drift 固定 `unavailable/external-read-disabled`。

根 allowlist：`INDEX.md/manifest.json/plan.md/contract.md/attempts.md/retrospective.md/design-review.md/_orchestrator-state.md/gate-ledger.jsonl/_budget-state.json/round-[1-9][0-9]*.md`。比较采用 NFC+casefold 唯一键。归档树拒绝 UNC、extended path、ADS、设备名、尾随点/空格、越界、symlink/junction/reparse、hardlink 与非普通文件。Markdown 导航必须是 archive-root 内 POSIX 相对链接；raw evidence 内容不改写也不当导航。

### Manifest 闭包与事务状态

manifest 承诺 canonical records、events、invocation/artifact blobs、revision manifests 的相对路径/hash/size，以及 invocation projection、artifact projection、final decision、advisory refs、degradations、parent revision。manifest 不自哈希；检查从 owners 重投影做语义比较，再逐字节重建 INDEX。archive 事务状态为 `preparing -> source-backed-up -> committed`，post-check 失败进入 `rolled-back`；reopen 使用 `reopen-prepared -> reopen-moved` journal。异常 journal 报 `recoverable`。重试从 journal 恢复，且任一时刻只接受 active、backup 或 done 中一个 authoritative 副本。只有 canonical done root 内且 check valid 才是 archived。reopen 将旧 manifest 原字节进入 revisions，新事件从历史最大 sequence 继续。

威胁边界：v1 只保证归档时点内部一致性、结构完整性和声明 provenance 可追溯性；hash 不认证来源，configured/inherited 不证明实际模型。本契约不抵抗同权限整体重写归档、ledger、manifest 和 Git 历史。

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
- Rejected alternatives: <executor 考虑过并排除的方案及排除理由；无则填「无」>
- Upstream scope check: <executor 对硬纪律「修复 scope 上溯」的自问结论；无则填「无」>
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

## relay-ledger（`relay-ledger.md`）

> 传话编排（relay orchestration）的**转发事件日志**。放在收敛对象目录下（`active/<slug>/`），与 `attempts.md`、`_orchestrator-state.md` 同级。

**硬约束**：

1. **append-only，不改写**——与 `attempts.md` 的「历史 entry 不改写，只追加 annotation」同源
2. 每条记录对应一次 orchestrator 转发事件

**字段**：

| 字段 | 说明 |
|------|------|
| 发送方 | `executor` / `reviewer` — 本轮产物的发出方 |
| 轮次 | 当前传话轮次（从 1 起） |
| 产物路径 | 转发产物的文件路径 |
| 内容 hash | 产物内容 SHA-256（64 位小写 hex） |
| 结论摘要 | 本轮结论的一句话摘要 |

**与 `attempts.md` 的职责区分**（收敛后设计审查 DR5 明确结论）：
- `relay-ledger.md` 记**转发事件**——orchestrator 在 executor 与 reviewer 之间每完成一次转发，追加一条记录
- `attempts.md` 记**修复尝试**——executor 每完成一次修复，追加一条 entry
- 二者**不冗余**：relay-ledger 侧重编排层的时序与完整性，attempts.md 侧重修复层的因果与归因

**记录样例**：

```markdown
## Round 1 · executor → reviewer
- 发送方: executor
- 轮次: 1
- 产物路径: src/plan.md
- 内容 hash: a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890
- 结论摘要: executor 按 reviewer R1 阻断清单完成 3 项修复，产物已更新

## Round 2 · reviewer → executor
- 发送方: reviewer
- 轮次: 2
- 产物路径: src/plan.md
- 内容 hash: b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890ab
- 结论摘要: reviewer 发现 1 项遗留阻断，需 executor 修复
```

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
| budget_gate | <true/false> | <int> | active |

status 由 `distill_antipatterns.py` 的 `--rules` 模式按阈值计算（guard: 5/10, core: 20/40）。格式固定——脚本从表格解析。

> 若为层级收敛（启用 decomposition-protocol.md），在成本数据节之后追加 **§12. 层级收敛评估**（§11 预留给收敛后修订记录；两节均可缺省，编号固定不顺延——保证 distill 类脚本按节标题定位的稳定性），格式见 `decomposition-protocol.md` §Retrospective 扩展。

---

## §预算 gate（`scripts/budget_gate.py` 的数据契约）

预算执行由 file-authoritative gate 承担。每个 `active/<slug>/` 下两份机器可读文件，由脚本维护、仅追加、可机械重算（抗 compaction）。落地与残余边界见 `docs/plans/*/20260618-budget-enforcement-hardening.md`。

### gate-ledger.jsonl（仅追加事件流，每行一个 JSON）

`budget_gate.py` 启动每个命令前对全 ledger 跑 **严格 schema validator**（`validate_integrity` + `_validate_event`）：任一事件缺必填字段 / 错类型 / 非法 enum / 嵌套不合 → `FAIL_CLOSED`（不让损坏事件污染计数）。各事件类型的**完整契约**：

```jsonc
// reserved —— 必填：event, reservation_id(非空串), ts(ISO), target_role(∈ROLE_CONSUMES),
//   consumes(== ROLE_CONSUMES[target_role], ∈{outer,blind,ultraverge,none,task-envelope}),
//   counts_before 与 ceilings(均为**至少**含 outer/blind/ultraverge/total 四键的 int dict；
//   仅当任务档已配置——见下方"任务档预算"——时，两个 dict 才额外携带 task-envelope 键，
//   若出现须为 int；未配置任务档时两个 dict 恰好四键，与改造前完全一致，A8 向后兼容),
//   tier(∈{enforced,auditable-only})——ledger 记录字段，gate 不按此值改变裁决逻辑；
//   guarded 模式的 ledger tier 仍为 auditable-only，guarded 状态存于独立 binding 的 mode=best-effort-guarded；
//   tier=enforced 保留给未来真正 enforced。consuming(outer/blind/ultraverge)时 target_round 须为正整数；
//   consumes=none/task-envelope 时 target_round 须为 null 或正整数（不接受字面 0，见上文
//   canonical_round——cmd_reserve 已在写入前把调用方传入的 0 归一化为 null，本处校验属防御性
//   fail-closed，只在有人绕过 CLI 直接注入 ledger 时才会触发）；extension_id 为 非空串或 null。
{"event":"reserved","reservation_id":"<session>:<tool_use>","ts":"<ISO>",
 "target_round":N,"target_role":"...","consumes":"outer|blind|ultraverge|none|task-envelope",
 "counts_before":{"outer":..,"blind":..,"ultraverge":..,"total":..},
 "ceilings":{"outer":..,"blind":..,"ultraverge":..,"total":..},
 "extension_id":"<或 null>","tier":"enforced|auditable-only"}
// spawn_succeeded —— 必填：reservation_id, ts(ISO), instance_id(非空串)。
{"event":"spawn_succeeded","reservation_id":"..","ts":"..","instance_id":".."}
// spawn_failed —— 必填：reservation_id, ts；reason 可选(若有须为串)；pre_execution 可选
//   (若有须为 bool，默认视为 false)——true 表示启动前失败/CLI 参数错误（模型从未被真正
//   调用），false（默认）表示模型确已被调用、只是调用后失败。用于双计数模型（见下）区分
//   attempted_dispatch 与 model_invocation。
{"event":"spawn_failed","reservation_id":"..","ts":"..","reason":"..","pre_execution":true|false}
// cancelled —— 必填：reservation_id, ts；pre_execution 须为 bool(默认 false)；reason 可选。
{"event":"cancelled","reservation_id":"..","ts":"..","pre_execution":true|false,"reason":".."}
// decision —— 必填：decision_event_id(非空串), ts(ISO),
//   verdict ∈ {MODE_SWITCH_REQUIRED, BLOCK:{budget|blind|ultraverge}_exhausted, BLOCK:total_spawn_cap,
//              BLOCK:task_envelope_exhausted, DENY:{unknown|illegal}_role, FAIL_CLOSED:<reason>}
//              （闭合枚举，非法值如 "BANANA" → fail-closed）；
//   scope ∈ {outer,blind,ultraverge,total,task-envelope,null}；BLOCK 系决策 scope 非 null 且 observed_usage/effective_ceiling 为 int；
//   **非 BLOCK 决策（DENY/FAIL_CLOSED/MODE_SWITCH）须 scope=null 且 observed_usage=null 且 effective_ceiling=null（三字段均须显式存在为 null）**。
{"event":"decision","decision_event_id":"<id>","ts":"..","verdict":"...",
 "scope":"outer|blind|ultraverge|total|task-envelope|null","observed_usage":<int|null>,"effective_ceiling":<int|null>}
```

- **仅追加，永不改写**（同 attempts.md 硬约束）。spawn 结果不回填 reserved 事件，而是追加新事件引用 `reservation_id`。
- **生命周期不变量**：reservation_id 不重复 reserved；settle（succeeded/failed/cancelled）必有前序 reserve 且不重复；同一 (scope, target_round) 至多一个活跃 reservation；outer/blind 产物文件须连续编号。违反 → `FAIL_CLOSED`。

### _budget-state.json（结构化状态）

```jsonc
{"config": {"max_outer_loops":5, ...},          // 仅放需覆盖默认的项；int 参数须为 int 否则 fail-closed
 "extensions": [                                  // 仅追加链；新记录写 supersedes，旧记录不可改
   {"extension_id":"<id>","ts":"..","scope":"outer|blind|ultraverge|total|task-envelope",
    "triggering_block_event_id":"<对应 decision 事件 id>",
    "granted_at_usage":<int>,"prior_ceiling":<int>,"new_ceiling":<int>,
    "supersedes":"<旧 id 或 null>","user_quote":"<用户原话>"}],
 "fsm": {"mode":"standard|ultraverge","severities":{"<round>":["implementation",...]}}}
```

**extension 校验（违反 → FAIL_CLOSED）**：`triggering_block_event_id` 指向真实 BLOCK decision；`scope`/`granted_at_usage`/`prior_ceiling` 与该 decision 的 `scope`/`observed_usage`/`effective_ceiling` 一致；同 scope `supersedes` 为线性链（无分叉/环/多头）；`new_ceiling` 单调递增且 `> prior_ceiling`；取代旧记录时 `prior_ceiling == 被取代记录.new_ceiling`（链衔接）。`user_quote` 是人类可审计凭据，**不**机械证明来自用户。`scope="task-envelope"` 额外要求 `new_ceiling` 不得超过该任务档的一次性授权上限（`task_envelope_cap` 或 `TASK_TIERS[task_tier]["cap"]`）——这是 task-envelope 独有的约束，outer/blind/ultraverge/total 的 extension 无此上限（只要求单调递增）。

### 角色对照表（`ROLE_CONSUMES`，`scripts/budget_gate.py` 单一权威源）

| `target_role` | consumes | 对应机制/文档 | 终局 owner 资格（`REVIEWER_AUTHORITIES`） |
|---|---|---|---|
| `outer-reviewer` | outer | 主循环 Reviewer（`refs/reviewer-prompt.md`） | fresh |
| `blind-reviewer` | blind | 盲审复核 | blank-slate |
| `ultraverge-initial` | ultraverge | ultraverge 初审 | fresh |
| `executor` | none | Executor | 不适用（非 reviewer） |
| `contract-proposer`/`contract-challenger`/`contract-finalizer` | none | Round 0 合同谈判（`refs/contract-negotiation.md`） | 不适用 |
| `arbiter` | none | 仲裁 | 不适用 |
| `l2-gate-reviewer` | none | **`refs/quality-gate.md` "L2 重量级" Reviewer**（该文档只用 "L2 Reviewer" 散文名，二者是同一机制） | **无**——不在 `REVIEWER_AUTHORITIES` 任一列表内；`capture.record_terminal_decision` 在**写入前**拒绝将其登记为 reviewer-verdict owner（见上文）。设计选择：门控"不否决不阻断"，只产出 `gate_findings`（advisory） |
| `design-reviewer` | none | 设计审查（`refs/design-review-prompt.md`） | 不适用（advisory，独立的 `design-review-completion` 事件类型，非 terminal-decision） |
| `task-envelope` | task-envelope | 任务级总信封（见下）——不是真正的 "Spawn 角色"，是复用 reserve/settle 框架的粗粒度计量入口 | 不适用 |

`reviewer`（`REVIEWER_AUTHORITIES.fresh` 的字面角色名之一，供未纳入 outer/ultraverge 计数的通用 fresh reviewer 使用）与 `outer-reviewer` 均可作终局 owner；两者不是同一角色，只是都落在 `fresh` 授权集合内。

### 任务档预算 / task-envelope scope（plan `20260724-OCSR-converge薄编排与成本控制修复.md` §6.1/§6.2/§6.3）

四档任务预算是 converge 既有 spawn 预算（本节其余部分描述的 outer/blind/ultraverge/total）的**上层信封**——按任务级 OCSR 调用总量计量，维度更粗、跨度更大，不替换、不重复实现 per-scope reserve/settle。实现为**新增一个并行 scope**：`consumes="task-envelope"`，通过 `--role task-envelope` 触发，复用完全相同的 reserve/settle/extension 机制。

- **四档默认值**（`budget_gate.py` 的 `TASK_TIERS`）：

  | 任务档 | 初始额度（ceiling 默认值） | 一次性授权上限（extension 硬顶） |
  |---|---:|---:|
  | small | 4 | 8 |
  | medium | 8 | 16 |
  | feature | 16 | 24 |
  | critical / critical/ultraverge | 20 | 30 |

  配置方式：`config.task_tier` 设为上表档名之一；或用 `config.task_envelope_initial`/`config.task_envelope_cap` 直接覆盖具体数值（`cap` 须 `>= initial`，否则 fail-closed）。
- **未配置行为**：`config` 中既无 `task_tier` 也无 `task_envelope_cap` 时，`reserve --role task-envelope` 直接 `FAIL_CLOSED:task_envelope_not_configured`；**其它任何角色的 reserve/settle 行为与改造前逐字节一致**（counts_before/ceilings 不出现 `task-envelope` 键）——这是 A8 向后兼容的机制保证，不依赖调用方记得"不要用这个新功能"。
- **与 total 的正交性**：task-envelope 的 reserve **不**计入、也**不**受 `total_reservations_issued`/`ceiling(state,"total")` 约束（`total_reservations_issued()` 显式排除 `consumes=="task-envelope"` 的 reservation）——两者是完全独立的计量维度，双方互不挤占对方的预算空间。
- **计量方式**：task-envelope 没有对应的文件产物（不像 outer/blind/ultraverge 有 `round-N.md` 等），因此不用 `realized()+pending()` 模型，而是用 `scope_reservations_issued(events, "task-envelope")`——与 `total_reservations_issued` 同构的单调计数（settled 的 succeeded/failed 都计入，仅 `pre_execution=true` 的 cancelled 不计）。
- **BLOCK 语义（design-review highlight #3 已定案）**：信封触发 `BLOCK:task_envelope_exhausted` 时，只阻止**新的** `reserve` 调用；已经 `reserve` 成功、处于 in-flight（pending，尚未 settle）状态的动作允许正常 `settle` 完成——`settle()` 本身从不检查预算（reserve/settle 分离是既有设计，BLOCK 只发生在 reserve 侧），故该语义无需额外代码即天然成立，本节只是显式记录这一点供后续实现/审查引用。

### 计数模型（确定性，脚本实现）

```text
realized(s) = 产物文件数  (outer: round-N.md / blind: blind-recheck-N.md / ultraverge: uv-init-N.md)
pending(s)  = consumes=s、未 failed/cancelled、且产物未落成的 reservation 数
effective_usage(s) = realized(s) + pending(s)                          # 可释放，仅 outer/blind/ultraverge 使用
total_reservations_issued = 单调累计的不同 reservation_id，**不含 task-envelope**
                            （failed 不释放；仅 pre_execution cancelled 不计）
scope_reservations_issued(s) = 单调累计的、consumes=s 的 reservation_id（口径同 total_reservations_issued，
                                但按 scope 过滤）——task-envelope 用此口径而非 effective_usage
reserve PROCEED iff total_reservations_issued < max_total_reserved_spawns AND effective_usage(s) < ceiling(s)
                    （task-envelope 的判据是 scope_reservations_issued("task-envelope") < ceiling(state,"task-envelope")，
                     且完全不参与 total_reservations_issued 的判据）
```

**双计数模型（`attempted_dispatch` vs `model_invocation`，plan Phase1 step4）**：

```text
attempted_dispatch(s)  = 已 settle 且非(pre_execution cancelled) 的 reservation 数
                          ——含启动前失败/CLI 错误（spawn_failed 且 pre_execution=true）
model_invocation(s)    = spawn_succeeded 数 + (spawn_failed 且 pre_execution=false) 数
                          ——只计真正发生过的模型调用，不含从未真正调用模型的失败/取消
```

两者由 `budget_gate.py summary --active-dir <active>` 命令输出（全局汇总 + 按 scope 拆分的 JSON），每次调用从 ledger 全量重算，不依赖缓存（幂等，同条款2）。

裁决优先级：`FAIL_CLOSED`(30) > `DENY`(21/22) > `BLOCK`(10/11/12/13/14) > `MODE_SWITCH_REQUIRED`(20) > `PROCEED`(0)。`max_total_reserved_spawns` 默认 = `ceil(total_safety×[3+max_ultraverge_initial+max_outer_loops×(1+max_inner_loops)+max_blind_rechecks+1])`。exit code 14 = `BLOCK:task_envelope_exhausted`。

> **tier 说明**：上述脚本是 host-independent core（auditable-only 完整可用）。`best-effort guarded`（= hook-blocked auditable-only）的 PreToolUse 总量硬上限 hook 已在 Claude Code 落地（PostToolUse settle 不存在）；其 ledger `tier` 仍为 `auditable-only`，guarded 状态独立存于 binding 的 `mode=best-effort-guarded`。true `enforced`（角色 FSM + 角色不可伪造 + 权限锁定）仍 deferred（升级要件见 `refs/framework-adapters.md` §A.1）。`budget_gate` 的 rule_frequency 触发检测方式：ledger 中出现 `decision` 事件即 triggered。
