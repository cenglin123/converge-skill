# State & Log 格式规范

> 本文件定义 `.converge/` 下所有持久化文件的格式。写文件时参考此处。

## 目录结构

```text
.converge/
├── tmp/                          # 中间产物（draft、临时脚本、调试输出等）。每轮结束后清理
├── active/<slug>/                # 进行中的收敛对象
│   ├── contract.md               # Round 0 合同终稿（可选）
│   ├── round-N.md                # 每轮 reviewer 输出 + orchestrator 处理记录
│   ├── attempts.md               # 跨轮 attempt log（含 overturn 链）
│   ├── gate-ledger.jsonl         # 预算 gate 仅追加事件流（reserved/settle/decision）
│   ├── _budget-state.json        # 预算 gate 结构化状态（config 覆盖 / extensions 链 / fsm mode+severities）
│   └── _orchestrator-state.md    # 抗 compact / 抗 session 切换
├── done/<slug>/                  # 已收敛/已停止
│   ├── ... (上述所有文件)
│   ├── retrospective.md          # 复盘（必填）
│   └── design-review.md          # 设计审查报告（可选，触发时生成）
└── gate/<slug>/                  # 门控产物（与 active/ 隔离）
    └── gate-findings.md          # L2 Reviewer gate_findings 汇总
```

> 格式规范见本文件以下各节。slug 命名：`<YYYYMMDD>-<对象简述>`。
>
> 收敛后修订时：done/ → active/（经 `scripts/archive_convergence.py reopen`） → 修订 → 重新归档 done/。
> retrospective 追加修订记录，不覆盖原有内容；修订必须经 reopen 保存旧 manifest revision 后再追加事实（见 Archive Contract v1）。

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

> **产出方**：round-N.md 骨架由 `orchest.py reserve-round` 创建（与 reservation 同命令落盘），frontmatter 契约字段由 `register-round` 回填、`record-verdict` 补 verdict——不再手写。下方格式定义为产物契约（字段与语义不变，产出方变更详见 `scripts/README.md`）。

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

预算执行由 file-authoritative gate 承担。每个 `active/<slug>/` 下两份机器可读文件，由脚本维护、仅追加、可机械重算（抗 compaction）。全量机器数据契约（`gate-ledger.jsonl` 精确 JSON 字段规格 / `_budget-state.json` 内部字段 / 计数模型内部结构 / `ROLE_CONSUMES`）单一权威源 = `scripts/budget_gate.py`（编译）；本节仅保留 agent 需读的角色摘要与判断/作者基准内容。

### 角色对照表（agent-relevant 摘要；完整 `ROLE_CONSUMES` 单一权威源 = `scripts/budget_gate.py`）

| `target_role` | consumes | 对应机制/文档 |
|---|---|---|
| `outer-reviewer` | outer | 主循环 Reviewer（`refs/reviewer-prompt.md`） |
| `blind-reviewer` | blind | 盲审复核 |
| `ultraverge-initial` | ultraverge | ultraverge 初审 |
| `executor` | none | Executor |
| `contract-proposer`/`contract-challenger`/`contract-finalizer` | none | Round 0 合同谈判（`refs/contract-negotiation.md`） |
| `arbiter` | none | 仲裁 |
| `l2-gate-reviewer` | none | `refs/quality-gate.md` "L2 重量级" Reviewer（同一机制） |
| `design-reviewer` | none | 设计审查（`refs/design-review-prompt.md`） |
| `task-envelope` | task-envelope | 任务级总信封（见下）——复用 reserve/settle 框架的粗粒度计量入口 |

终局 owner 授权（`REVIEWER_AUTHORITIES`：`fresh={reviewer,outer-reviewer,ultraverge-initial}`、`blank-slate={blank-slate-reviewer,blind-reviewer}`）由 `scripts/archive_contract/model.py` 与上文 §Archive Contract v1（`validate_reviewer_verdict_authority()`）统一实现。

### budget_extension 令牌校验（作者/校验基准）

`extensions` 链（`_budget-state.json`）仅追加，新记录写 `supersedes`，旧记录不可改。**extension 校验（违反 → FAIL_CLOSED）**：`triggering_block_event_id` 指向真实 BLOCK decision；`scope`/`granted_at_usage`/`prior_ceiling` 与该 decision 的 `scope`/`observed_usage`/`effective_ceiling` 一致；同 scope `supersedes` 为线性链（无分叉/环/多头）；`new_ceiling` 单调递增且 `> prior_ceiling`；取代旧记录时 `prior_ceiling == 被取代记录.new_ceiling`（链衔接）。`user_quote` 是人类可审计凭据，**不**机械证明来自用户。`scope="task-envelope"` 额外要求 `new_ceiling` 不得超过该任务档的一次性授权上限（`task_envelope_cap` 或 `TASK_TIERS[task_tier]["cap"]`）——这是 task-envelope 独有的约束，outer/blind/ultraverge/total 的 extension 无此上限（只要求单调递增）。

### 任务档预算 / task-envelope scope

四档任务预算是 converge 既有 spawn 预算（outer/blind/ultraverge/total）的**上层信封**——按任务级 OCSR 调用总量计量，维度更粗、跨度更大，不替换、不重复实现 per-scope reserve/settle。实现为 `consumes="task-envelope"` 的并行 scope，通过 `--role task-envelope` 触发，复用完全相同的 reserve/settle/extension 机制；机器强制（与 `total` 正交、BLOCK 语义、`summary` 命令等）单一权威源 = `scripts/budget_gate.py`。

- **四档默认值**（`budget_gate.py` 的 `TASK_TIERS`）：

  | 任务档 | 初始额度（ceiling 默认值） | 一次性授权上限（extension 硬顶） |
  |---|---:|---:|
  | small | 4 | 8 |
  | medium | 8 | 16 |
  | feature | 16 | 24 |
  | critical / critical/ultraverge | 20 | 30 |

  配置方式：`config.task_tier` 设为上表档名之一；或用 `config.task_envelope_initial`/`config.task_envelope_cap` 直接覆盖具体数值（`cap` 须 `>= initial`，否则 fail-closed）。
- **未配置行为**：`config` 中既无 `task_tier` 也无 `task_envelope_cap` 时，`reserve --role task-envelope` 直接 `FAIL_CLOSED:task_envelope_not_configured`；**其它任何角色的 reserve/settle 行为与改造前一致**（`counts_before`/`ceilings` 不出现 `task-envelope` 键）——A8 向后兼容。

> **tier 说明**：上述脚本是 host-independent core（auditable-only 完整可用）。`best-effort guarded`（= hook-blocked auditable-only）的 PreToolUse 总量硬上限 hook 已在 Claude Code 落地（PostToolUse settle 不存在）；其 ledger `tier` 仍为 `auditable-only`，guarded 状态独立存于 binding 的 `mode=best-effort-guarded`。true `enforced`（角色 FSM + 角色不可伪造 + 权限锁定）仍 deferred（升级要件见 `refs/framework-adapters.md` §A.1）。`budget_gate` 的 rule_frequency 触发检测方式：ledger 中出现 `decision` 事件即 triggered。

---

## §结构化协议字段扩展（executor / reviewer 输出 schema）

> 以下字段是 executor 输出 JSON 与 reviewer 输出 JSON 的**可选扩展**——不破坏既有 schema 的向后兼容性。基准 schema 见 converge SKILL.md §7.1（executor）/ §7.2（reviewer）。本节是 converge 官方 schema 的正式补充，与「角色对照表」同节。

### evidence_tier（executor `tests[]` 可选扩展）

executor 输出的 `tests[]` 数组中的每个元素可携带 `evidence_tier` 字段（字符串，可选）：

```
"evidence_tier": "static" | "isolated_runtime" | "target_like_integration" | "production_browser" | "human_authorization"
```

五级证据等级升序排列（`static` = 最低，`human_authorization` = 最高）。不标注时默认 `static`（rank 0）。

- 消费方（驱动器 / orchestrator）：按合同断言的 `required_evidence_tier` 逐条比对，`achieved_rank < req_rank` 即未满足前置证据要求。
- 适用范围：executor 提交 `ready_for_review` 时，驱动器检查是否满足 reviewer 的前置证据等级门禁（harness-first）；未满足即 fail-closed，不转发给 reviewer。

### dispute_topic_id（reviewer `blocking[]` 可选扩展）

reviewer 输出的 `blocking[]` 数组中的每个元素可携带 `dispute_topic_id` 字段（字符串，可选）：

```
"dispute_topic_id": "<非空字符串>"
```

用于跨轮追踪同一争议。reviewer 填写此字段表示本条 blocking 与之前某轮的 blocking 是同一议题的延续。

- 驱动器消费方式：按 `dispute_topic_id`（非空时优先）或 `id` 维护 `blocking_key`，对每个 key 追踪 `consecutive_open_rounds` 和 `recurrence_count`。
- 升级条件联动：同一 `dispute_topic_id` 连续 ≥2 轮未关闭（`consecutive_open_rounds >= 2`）→ 自动标记 `suspect_harness_or_contract`；同级缺陷（同 severity）连续 ≥2 轮复发 → 标记 `recurring_defect`。两者均触发升级 orchestrator。
- reviewer **不填**此字段时，驱动器按 `id` 做同轮唯一标识，不跨轮追踪（`consecutive_open_rounds` 恒为 1）。

> `dispute_topic_id` 与 `id` 的关系：`id` 是单轮内 blocking 的唯一标识（必填，同轮去重），`dispute_topic_id` 是跨轮的争议追踪 key（可选，填了才跨轮计数）。两者不互斥——reviewer 可同时填两者。
