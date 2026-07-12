# State & Log 格式规范

> 本文件定义 `.converge/` 下所有持久化文件的格式。写文件时参考此处。

## Archive Contract v1（规范单源）

`schema_id="converge.archive"`，`schema_version="1.0"`。读取按 schema dispatch，不按日期：无 manifest 为 `missing/legacy-unverifiable`；严格 JSON 失败（含重复 key、BOM、NaN/Infinity）为 `malformed`；缺版本、外部 schema 或更新版本为 `unsupported`；可识别 v1 但闭包失败为 `invalid`；全部通过为 `valid`。未知版本 fail-safe，scan 只读且不迁移。

### 权威与依赖

可执行单源是 `scripts/archive_contract/model.py`；本节解释同一字段和枚举。模块依赖固定为 `capture -> model <- transaction`、`presentation -> model`，CLI 只装配。采集期 owner 是 append-only events；budget settlement 唯一 owner 是 `gate-ledger.jsonl`；旧 revision owner 是 `evidence/revisions/<revision-id>/manifest.json`。归档时 manifest 是 owners 的冻结投影，INDEX 只从 manifest 生成，不能产生事实。

### Event 与主外键

公共字段：`schema_id/schema_version/event_type/event_id/sequence`。event id 为 UUID；sequence 在所有 event 类型中从 1 连续且无缺口。`invocation-started` 拥有 invocation kind（spawn/continue）、role、phase、round、attempt、parent、reservation、started_at 与 requested provenance；`invocation-terminal` 只引用 started event，拥有 terminal status、completed_at、host receipt、settlement ref 与 resolved provenance。同一 started 恰有一个 terminal。Continue 必须引用同 instance 的 Spawn parent。

terminal status 为 `succeeded|failed|cancelled|timeout`；仅 succeeded 必须有 output evidence。失败 reason 为 `backend-error|cancelled-by-host|timeout|process-interrupted`。terminal decision 是闭合联合：`reviewer-verdict` 只引用成功 fresh/blank-slate Reviewer terminal；`user-decision` 只用于 terminal-b/c，必须含 `user_quote/source_ref/presented_degradations/accepted_state`。`design-review-completion` 是 advisory，禁止出现在 `final_verdict_ref`。最终 round 与 retrospective 必须反向引用同一 decision event id/value。

requested provenance 字段为 `requested_provider/requested_model`；resolved 字段为 `resolved_provider/resolved_model/resolved_family/backend/backend_version`。`evidence_level=observed|host-reported|configured|inherited|unavailable`，`resolution_source=host_receipt|tool_response|cli_argument|agent_config|parent_instance|none`。configured/inherited 不得带 resolved model。partial/unavailable reason 仅允许 `backend-does-not-expose|receipt-missing|inherited-concrete-model-hidden|invocation-failed-before-resolution`。

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
//   consumes(== ROLE_CONSUMES[target_role], ∈{outer,blind,ultraverge,none}),
//   counts_before 与 ceilings(均为含 outer/blind/ultraverge/total 四键的 int dict),
//   tier(∈{enforced,auditable-only})——ledger 记录字段，gate 不按此值改变裁决逻辑；
//   guarded 模式的 ledger tier 仍为 auditable-only，guarded 状态存于独立 binding 的 mode=best-effort-guarded；
//   tier=enforced 保留给未来真正 enforced。consuming(outer/blind/ultraverge)时 target_round 须为正整数；
//   extension_id 为 非空串或 null。
{"event":"reserved","reservation_id":"<session>:<tool_use>","ts":"<ISO>",
 "target_round":N,"target_role":"...","consumes":"outer|blind|ultraverge|none",
 "counts_before":{"outer":..,"blind":..,"ultraverge":..,"total":..},
 "ceilings":{"outer":..,"blind":..,"ultraverge":..,"total":..},
 "extension_id":"<或 null>","tier":"enforced|auditable-only"}
// spawn_succeeded —— 必填：reservation_id, ts(ISO), instance_id(非空串)。
{"event":"spawn_succeeded","reservation_id":"..","ts":"..","instance_id":".."}
// spawn_failed —— 必填：reservation_id, ts；reason 可选(若有须为串)。
{"event":"spawn_failed","reservation_id":"..","ts":"..","reason":".."}
// cancelled —— 必填：reservation_id, ts；pre_execution 须为 bool(默认 false)；reason 可选。
{"event":"cancelled","reservation_id":"..","ts":"..","pre_execution":true|false,"reason":".."}
// decision —— 必填：decision_event_id(非空串), ts(ISO),
//   verdict ∈ {MODE_SWITCH_REQUIRED, BLOCK:{budget|blind|ultraverge}_exhausted, BLOCK:total_spawn_cap,
//              DENY:{unknown|illegal}_role, FAIL_CLOSED:<reason>}（闭合枚举，非法值如 "BANANA" → fail-closed）；
//   scope ∈ {outer,blind,ultraverge,total,null}；BLOCK 系决策 scope 非 null 且 observed_usage/effective_ceiling 为 int；
//   **非 BLOCK 决策（DENY/FAIL_CLOSED/MODE_SWITCH）须 scope=null 且 observed_usage=null 且 effective_ceiling=null（三字段均须显式存在为 null）**。
{"event":"decision","decision_event_id":"<id>","ts":"..","verdict":"...",
 "scope":"outer|blind|ultraverge|total|null","observed_usage":<int|null>,"effective_ceiling":<int|null>}
```

- **仅追加，永不改写**（同 attempts.md 硬约束）。spawn 结果不回填 reserved 事件，而是追加新事件引用 `reservation_id`。
- **生命周期不变量**：reservation_id 不重复 reserved；settle（succeeded/failed/cancelled）必有前序 reserve 且不重复；同一 (scope, target_round) 至多一个活跃 reservation；outer/blind 产物文件须连续编号。违反 → `FAIL_CLOSED`。

### _budget-state.json（结构化状态）

```jsonc
{"config": {"max_outer_loops":5, ...},          // 仅放需覆盖默认的项；int 参数须为 int 否则 fail-closed
 "extensions": [                                  // 仅追加链；新记录写 supersedes，旧记录不可改
   {"extension_id":"<id>","ts":"..","scope":"outer|blind|ultraverge|total",
    "triggering_block_event_id":"<对应 decision 事件 id>",
    "granted_at_usage":<int>,"prior_ceiling":<int>,"new_ceiling":<int>,
    "supersedes":"<旧 id 或 null>","user_quote":"<用户原话>"}],
 "fsm": {"mode":"standard|ultraverge","severities":{"<round>":["implementation",...]}}}
```

**extension 校验（违反 → FAIL_CLOSED）**：`triggering_block_event_id` 指向真实 BLOCK decision；`scope`/`granted_at_usage`/`prior_ceiling` 与该 decision 的 `scope`/`observed_usage`/`effective_ceiling` 一致；同 scope `supersedes` 为线性链（无分叉/环/多头）；`new_ceiling` 单调递增且 `> prior_ceiling`；取代旧记录时 `prior_ceiling == 被取代记录.new_ceiling`（链衔接）。`user_quote` 是人类可审计凭据，**不**机械证明来自用户。

### 计数模型（确定性，脚本实现）

```text
realized(s) = 产物文件数  (outer: round-N.md / blind: blind-recheck-N.md / ultraverge: uv-init-N.md)
pending(s)  = consumes=s、未 failed/cancelled、且产物未落成的 reservation 数
effective_usage(s) = realized(s) + pending(s)                          # 可释放
total_reservations_issued = 单调累计的不同 reservation_id（failed 不释放；仅 pre_execution cancelled 不计）
reserve PROCEED iff total_reservations_issued < max_total_reserved_spawns AND effective_usage(s) < ceiling(s)
```

裁决优先级：`FAIL_CLOSED`(30) > `DENY`(21/22) > `BLOCK`(10/11/12/13) > `MODE_SWITCH_REQUIRED`(20) > `PROCEED`(0)。`max_total_reserved_spawns` 默认 = `ceil(total_safety×[3+max_ultraverge_initial+max_outer_loops×(1+max_inner_loops)+max_blind_rechecks+1])`。

> **tier 说明**：上述脚本是 host-independent core（auditable-only 完整可用）。`best-effort guarded`（= hook-blocked auditable-only）的 PreToolUse 总量硬上限 hook 已在 Claude Code 落地（PostToolUse settle 不存在）；其 ledger `tier` 仍为 `auditable-only`，guarded 状态独立存于 binding 的 `mode=best-effort-guarded`。true `enforced`（角色 FSM + 角色不可伪造 + 权限锁定）仍 deferred（升级要件见 `refs/framework-adapters.md` §A.1）。`budget_gate` 的 rule_frequency 触发检测方式：ledger 中出现 `decision` 事件即 triggered。
