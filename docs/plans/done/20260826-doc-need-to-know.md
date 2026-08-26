# 文档层 agent-need-to-know 削减：脚本兜底后勤，agent 专注判断（DELTA 版）

状态：进行中（同意后步入执行；本版为 ultraverge 3/3 评议 8 项 BLOCKING 处置 + outer Round 7 2 项 BLOCKING 处置 + outer Round 8 2 项 BLOCKING 处置后的修订版）

> **本计划是已合入的《docs/plans/active/20260826-doc-layer-refactor.md》（#16，squash 6990314；其计划与等价映射表现在归档于 docs/plans/done/）之上的 DELTA。** 本计划**不重做**该计划已完成单源化的条目：
>
> - M-11 的 hook wiring 命令级细节 -> `refs/framework-adapters/claude-code.md` §A.1 指针（**已落地**；目标是 claude-code，不是 codex）。
> - §六·预算追踪 + gate 编排 的 reserve-round/register-round/continue 命令序列收缩（**已落地**）。
> - §Archive/reopen 的不变量保留（journal 幂等、禁手工删除、绑定唯一性、bootstrap staging-only、legacy 只读）（**已落地**）。
> - 配置两分法 + `max_total_reserved_spawns` 为脚本派生的机械强制上限、其规范式保留在 SKILL.md（**已裁决**）。
>
> 因此本计划的 delta **仅限**：在「agent-need-to-know」视角下，对**剩余冗余散文**的进一步削减——减的是 agent 不需要重复读到的机械/复算内容，**不减**判断、义务或已单源的机制。与已归档等价映射表的交叉引用见 §「前序已单源、本 delta 不重做」。

## 设计哲学（裁决尺）

**脚本兜底后勤，agent 专注需要判断的事情。** 文档只告诉 agent：调什么命令、什么结果算成功、失败时如何判断/处置；**不**预先教「如何构造脚本会校验的东西」、**不**复述脚本算出的结果、**不**让 agent 确认脚本已机械检查的事实。

对应三条文档规则（本计划的删除判据）：

1. **脚本会拒绝的错误，文档不预先教「如何避免」**——只说「命令 X，失败按报错处置」。错误消息本身就是文档。
2. **脚本算出的数值/公式，文档不复述**——写「以脚本行为为准」。（复述正是上轮 42/44 vs 63/62 漂移的根因；本 delta 只针对**已单源化的数值复算**，规范式本体保留。）
3. **finish/gate/archive 已机械检查的项，必检清单不再让 agent 确认**——清单只留语义/义务项（用户告知了吗、降级声明了吗、retrospective 写了吗、授权判断了吗）。

## 前序已单源、本 delta 不重做

以下条目由《20260826-doc-layer-refactor.md》及其等价映射表（`docs/plans/active/20260826-doc-layer-refactor-equivalence.md`，已并入该计划归档）**已裁决并落地**，本计划**只确认、不重做**：

| 已单源条目 | 裁决/落地 | 本计划态度 |
|---|---|---|
| M-11 hook wiring（bind/unbind/refresh-cap/PreToolUse/独立计数器不双计） | -> `refs/framework-adapters/claude-code.md` §A.1（wiring 单源） | 只保留语义+指针，不覆盖接线细节 |
| §六·预算追踪 + gate 编排 命令序列（reserve-round/register-round/continue） | -> `scripts/README.md` Loop A（命令名+参数单源） | 不重复命令参数；只处理剩余冗余 + extension 作者 schema |
| §Archive/reopen 不变量 | 保留于 guide §Archive/reopen（journal 幂等、禁手工删、绑定唯一性、bootstrap staging-only、legacy 只读） | 不重做；本次不再改该节 |
| 配置两分法 + `max_total_reserved_spawns` 规范式 | 规范式**保留**在 SKILL.md；8 个脚本实收键指向 DEFAULTS（单源） | 保留规范式与 DEFAULTS 指针；只删**陈旧数字复算** |

## 语义零改动锚点（评审核心依据）

- 所有**判断性内容**一条不删不弱化：verdict 裁决、Overturn/Type R 语义等价判定、偏见意识、边界场景处置、非 PROCEED 处置表（BLOCK 呈现菜单/MODE_SWITCH 给用户选项）、终止状态确认点、升级/降级判定、用户告知义务、授权判断（extension 需用户原话）。
- 行为禁令不改：不得手跑裸 reserve/settle、不得记忆旧授权续费、不得手工移动/改写 manifest、禁用属性访问器（ctx.jobs/ctx.settings）。
- 每条删除必须能证明属于以下之一：(a) 目标事实由脚本 fail-closed 机械保证；(b) 纯实现描述（gate/orchest/archive 内部如何做）；(c) 脚本已在本轮之外计算的数值**复算**（非规范式本体）。
- **语义/义务保留始终优先于行数**（与已落地计划的「范围目标 + semantics-first」一致）。

## 可削减点（每项均给出「为什么 agent 不需要」）

> **范围界定**：本节「可削减点」均为**拟删除/收缩项**。其中 **M-11 三条纯 prose 义务** 为**保留确认（非删除项）**；**§六·预算追踪 + gate 编排 budget_extension 字段级作者 schema** 则属**执行项（补齐到 guide §六）**——两者**均不属于**本 delta 的删除/收缩清单，仅在本节作登记并与真正可削减项区分，避免范围混淆。

### SKILL.md（行数仅参考）

- **`max_total_reserved_spawns`：只删数值复算，规范式与 DEFAULTS 指针保留**。这是脚本派生的机械强制上限，其**规范式语句保留在 SKILL.md**（sibling plan S2 裁决；脚本据此机械强制执行）。本 delta 删除目标仅为**重复/陈旧数字复算**：
  - 删除 [^totalcap] 脚注的**定义与推导式复算**（定义 + `ceil(1.5*42/41)`、`63/62` 的 stock 双档表、无边界下溢说明等——这些已由 #16 对齐到 DEFAULTS/公式单源，属重复复述）。**联动**：删除 [^totalcap] 脚注定义后，SKILL.md 配置表行（`max_total_reserved_spawns`）中的 [^totalcap] 内联引用标记一并删除，该行仅保留一行行为事实（普通=63 / ultraverge=62），不再承载脚注。
  - 删除 Ultraverge-path（原 L168）与配置区 NOTE（原 L454）中「total 上限按规范式重算——普通=63 -> ultraverge=62」这类数值复算。
  - **保留**：`max_total_reserved_spawns` 的确定性公式语句（`default = ceil(total_safety * [3 + ultraverge_min_reviewers + max_outer_loops*(1+max_inner_loops) + max_blind_rechecks + 1])`）；「与角色无关、单调、failed 不释放、扩容需 scope=total extension」语义；**8 个脚本实收键的 DEFAULTS 单源指针**（max_outer_loops / max_blind_rechecks / ultraverge_min_reviewers / max_inner_loops / impl_severity_streak_threshold / preflight_code_block_threshold / preflight_code_loc_threshold / total_safety）。
  - 「模式相关行为事实」作为**一行行为事实**保留：ultraverge 初始化 config 覆盖 `max_blind_rechecks=2`（纯 orchestrator 行为、零代码）；普通/ultraverge 两档总上限数值可作为行为事实一句带过，但**不再展开推导**。
- **预算执行哲学注**（原 L456 六行）：压缩为一句「预算由 `budget_gate.py` 在每次 spawn 前裁决；trust boundary 三级，逐级能力见 framework-adapters 分册（§A.1 claude-code / §A.6 kimi-code / §A.7 dsh）；[行为禁令「不得靠记忆计数」规范落在 refs/orchestrator-guide.md §六;SKILL 此处仅指针]」——删机制复述（「file-authoritative gate 的核心、不依赖 Orchestrator 记忆计数」属脚本保证）；**保留**「不得靠记忆计数」作为行为禁令（其完整保留位置 = `refs/orchestrator-guide.md` §六；SKILL.md 压缩注仅承载指针、不承载其规范式；等价映射表须记录该保留位置）。
- **SKILL.md 任务级总信封 note**（原 L458）：当前 note 说机制细节（BLOCK 语义 / 与 total 正交 / summary 命令）见 refs/state-schema.md §预算 gate「任务档预算/task-envelope scope」子锚点——这些机制细节恰是本 delta 从 state-schema 移除的维护者视角内容，缩减后该子锚点悬空。处置：改指 `scripts/budget_gate.py`（task-envelope 单一权威源）+ state-schema §预算 gate 角色摘要；**不保留机制复述**（BLOCK 语义 / 与 total 正交 / summary 命令）。
- **必检清单机械项（只删除 finish/archive 机械保证且无独立判断价值的 2 项）**：删除「`archive` 返回成功」（finish 的 landing 动作，不是 agent 义务）与「done 最终路径只读 `check` 返回 valid-v1」（finish 步骤 8）。**以下保留为一行提醒（语义/判断价值，脚本不可证明）**：
  - extension 须关联真实 BLOCK decision 事件 + round-stamped 用户原话（user_quote 是授权判断，非脚本可证明）；
  - 每个预算内 spawn 有 reservation 且已 settle / 无未结孤儿（混合后端下原生 spawn 可能逃逸 full-settle）；
  - extension **仅**抬高 ceiling、**不**替代 reservation；总量未突破 max_total_reserved_spawns；
  - 无不可阻断 hook 的 auditable-only 会话：属**纯 prose 无机械兜底**的自觉约束告知。
- **M-11 三条纯 prose 义务——保留确认（非删除项）**：M-11 的 hook-wiring 命令级细节（bind/unbind/refresh-cap/PreToolUse/独立计数器不双计）已由前序计划**单源**至 `refs/framework-adapters/claude-code.md` §A.1（#16 已落地），本 delta **不重做**、不再作为本表（等价映射表）的删除行登记。以下**三条纯 prose 义务**在本 delta 中**保留、不删**，作为「明确不删」清单的保留确认项：
  - (a) **混合后端检查点**：同一会话混用 gated 通道与未 gate 通道（宿主原生 spawn）时，每次 spawn 前显式确认本通道已过预算门——adapter 自动 gated 不构成原生通道已 gate 的证据；收敛循环内原生 spawn 须过门（reserve-round/register-round）；落地执行原生 spawn 豁免；若漏 gate，按 `orchestrator_self` 降级标注并继续，retrospective 中申报；不回填。
  - (b) **宿主能力矩阵**：Claude Code -> best-effort guarded（PreToolUse hook 已落地，§A.1）；kimi-code -> opt-in hook 可接线（§A.6，未接线即 auditable-only）；opencode -> auditable-only（无可阻断 hook）。
  - (c) **「auditable-only 宿主上本检查点无机械兜底，是纯 prose 自觉约束」**——一句显式声明。
  - M-11 的目标是「压缩」，但**绝不 drop 以上三条**（本条为保留确认，非删除行/非本 delta 收缩项）。
- **主循环内部实现描述**（原 L218/L299 等「gate reserve + begin-invocation + 骨架落盘」「settle 语义内嵌」「begin kind=continue 计数入 max_inner_loops」）：这类是 orchest.py 的内部步骤，agent 只需命令名+用途+指针（`scripts/README.md`）；**保留**语义判断点（★步骤）与盲审不变量（pass|fail|waived、共享 max_outer_loops、不自动扩），并**保留内环预算不变量「continue 不推进 max_outer_loops、不占新 spawn cap（仅计数入 max_inner_loops）」**——该不变量随 ★/盲审不变量**保留在 SKILL.md 主循环**，**不**仅靠 `scripts/README.md` L82 指针（L82 只写「计数入 max_inner_loops=3」，未写「不推进 max_outer_loops / 不占新 spawn cap」，指针不足单独承接）。来源：前序归档映射表 `docs/plans/done/20260826-doc-layer-refactor-equivalence.md` row 8。

### orchestrator-guide.md（行数仅参考）

- **§六·预算追踪 + gate 编排 budget_extension 令牌字段级 schema——执行项：补齐到 guide §六（作者基准，不是纯 gate 校验）**。orchestrator 在 manual-fallback 时**手写**该令牌，字段级 schema 是它的**作者基准**。因此本 delta 对该字段 schema 的处置是**补齐**（而非仅保留确认）：在 guide §六 的 budget_extension 作者字段描述中**确保写入** `extension_id`、`ts`、`granted_at_usage`，连同既有 `triggering_block_event_id`、`new_ceiling` 单调递增且 `prior_ceiling` 接上链、`supersedes`、`scope`/`observed_usage`/`effective_ceiling` 逐项一致、`user_quote`。其中 `extension_id`/`ts` 为纯作者字段（orchestrator 手写、脚本不生成）；`granted_at_usage` 由 `budget_gate.py` **`validate_extensions` L383** 机械校验为 `== decision.observed_usage`（orchestrator 必须照实填写）；**`user_quote` 是作者基准**（`budget_gate.py` 的 `validate_extensions` 并不包含/校验它），故**不**把 `user_quote` 指向 `scripts/budget_gate.py` 作为作者单源——保留 guide 作者字段描述。**必留**：必须关联真实 BLOCK decision 事件 + `user_quote` + 单调 ceiling 链；校验不过 -> `FAIL_CLOSED`；不得用记忆中的旧授权续费。
- **§六·预算追踪 + gate 编排 中对「全量数据契约」的引用改指 `scripts/budget_gate.py`**：原「数据契约见 refs/state-schema.md §预算 gate」改为「状态机/计数/角色表等全量机器数据契约以 `scripts/budget_gate.py` 为单一权威源（编译）；state-schema §预算 gate 仅保留 agent 需读的角色摘要」。§六 命令序列收缩属**前序已单源（#16）**，本 delta 不重做（等价映射见归档映射表 rows 21）。本条「全量数据契约引用改指」与 state-schema §预算 gate 缩减（等价映射表 row 5）为一组单源重定向，**折叠进 row 5 登记，不新增行**（保持 8 行计数）。
- **§一 spawn 前自检**：保留语义项（prompt 自足、路径有效性、未暗示结果、升级复查、instance_id 记录）；机械探测项（若代码项目查 testing-toolbox 定 test/lint 命令）保留为一句，不展开。
- **§Archive/reopen 内部实现**：前序计划已保留不变量，本 delta **不再改**该节。

### refs/state-schema.md（行数仅参考）

- **§预算 gate（原 §「预算 gate」约 L378-L502）：need-to-know 保留 ANCHOR、只删 PURE MACHINE JSON schema 重复，不迁移、不新增合约文件；锚点命名保持稳定（**不**重命名为「角色契约摘要」）。** 被删的 **PURE MACHINE JSON schema 重复**（`gate-ledger.jsonl` 精确 JSON 字段规格、`_budget-state.json` 内部字段、计数模型内部结构——L79 三类）由 **`scripts/budget_gate.py` 作为单一权威源（编译）**。**节标题 `§预算 gate` 保留（锚点稳定，不因缩减改名/不降级）**；该节内缩减落点即「以一句『全量数据契约单一权威源 = `scripts/budget_gate.py`』替代被删的 PURE MACHINE JSON schema 重复」。因此：
  - **保留命名锚点 `角色对照表`（不重命名）**：缩减为 **agent-relevant 「角色 → consumes」摘要**——按 `ROLE_CONSUMES` 简化为「哪些角色 consumes `outer`/`blind`/`ultraverge`/`none`」（`executor` consumes `none`、`l2-gate-reviewer` consumes `none`、`design-reviewer` consumes `none`、`arbiter`/contract 三角色 consumes `none`），**仅删除 `终局-owner-资格` 列**（gate-enforcement 细节）。该列删除后仍由 agent 可访问的**作者权威源**覆盖：`scripts/archive_contract/model.py`（`REVIEWER_AUTHORITIES` 枚举：`fresh`/`blank-slate` 授权集合）+ `refs/state-schema.md` L44（`validate_reviewer_verdict_authority()` 的 owner 授权说明）——**不**引用 reviewer-discipline（无该枚举）或 quality-gate L82（已不再指向完整 owner 列），故不造成作者信息丢失。这使得 `budget_gate.py` L91 注释（to 角色对照表）、state-schema L508（与角色对照表同节）、quality-gate L82（经修复的 consumes-summary + 完整 `ROLE_CONSUMES` 单源指针）全部指向保留锚点、**RESOLVABLE**。
  - **保留命名锚点 `任务档预算` / task-envelope scope（语义指针）与档位表**：作为与 total 正交的独立维度保留「存在性说明」（BLOCK 语义 / 与 total 正交 / summary 命令的机制不再展开）与 **task-envelope 四档档位表（L461-466：`small`/`medium`/`feature`/`critical` 的初额度默认值与一次性授权上限；agent-relevant/判断，保留）**，并指向 `scripts/budget_gate.py` 作为机器强制。SKILL.md L458（任务级总信封 note）引用仍解析。
  - **保留（NARROW 范围，agent-relevant/judgment，非删除）**：`_budget-state.json` 节的 **extension 校验细节（L437）**——`triggering_block_event_id` 指向真实 BLOCK decision；`scope`/`granted_at_usage`/`prior_ceiling` 与该 decision 的 `scope`/`observed_usage`/`effective_ceiling` 一致；`supersedes` 线性链；`new_ceiling` 单调递增且 `> prior_ceiling`；`prior_ceiling == 被取代记录.new_ceiling`；**`user_quote` 是人类可审计凭据，不机械证明来自用户**；`scope="task-envelope"` 的额外一次性授权上限——这些是判断/作者基准内容，**保留**，不属 L79 的「PURE MACHINE JSON schema 重复」三类删除，也**不**将 `user_quote` 指向 `budget_gate.py` 作为作者单源。
  - **删除**：仅删除 §预算 gate 内 **PURE MACHINE JSON schema 重复**——`gate-ledger.jsonl` 精确 JSON 字段规格、`_budget-state.json` 内部字段、计数模型内部结构（均是从 `budget_gate.py` 复述的内容）。以一句「machine schema / `ROLE_CONSUMES` / 计数模型单一权威源 = `scripts/budget_gate.py`」替代。
  - **范围边界（重要）**：§预算 gate **实际止于 L502**（含 tier 说明与分隔线）。**L506 起是 §结构化协议字段扩展（`evidence_tier`/`dispute_topic_id`，executor/reviewer 输出 schema）——必须保留，agent 会读，不得纳入任何缩减。** state-schema L508（与角色对照表同节）因 `角色对照表` 锚点保留而**自然解析**。
  - 本 delta **不创建 `docs/budget-gate-contract.md`**，避免受保护文件迁移与悬空引用。
  - **refs/quality-gate.md L82 引用修复**：「完整角色对照表见 refs/state-schema.md §预算 gate『角色对照表』」改为「consumes-summary 在 state-schema §预算 gate『角色对照表』；完整 `ROLE_CONSUMES` 单一权威源 = `scripts/budget_gate.py`」（角色表只减 `终局-owner-资格` 列，`角色对照表` 锚点保留）。
- 保留 state-schema 中 agent 实际会读的：round-N.md 格式、attempts.md 格式、_orchestrator-state.md 格式、retrospective 格式、relay-ledger 格式、目录结构节。

## 明确不删（语义/禁令清单）

- 非 PROCEED 处置表（BLOCK 菜单、MODE_SWITCH 选项、DENY、FAIL_CLOSED）。
- 授权判断：extension 需用户原话；终止-b/c 需用户显式确认；预算软停/预算扩展需用户裁决。
- 行为禁令：不得手跑裸 reserve/settle、不得记忆旧授权续费、不得手工移动/改写 manifest、禁止 ctx.jobs/ctx.settings 属性访问器、不得静默漏 gate（混合后端检查点）。
- 判断语义：Overturn/Type R/发散检测、偏见意识、边界场景、内环验收、升级/降级判定、检索申诉仲裁、传话编排三条件等。
- 用户告知/证据义务：用户已被告知降级模式、设计审查 highlights 报告用户、裸 auditable-only 告知、降档三条件核对记录。
- **纯 prose 无机械兜底的三条 M-11 义务**（混合后端检查点 / 宿主能力矩阵 / auditable-only 纯 prose 声明）。
- **§六·预算追踪 + gate 编排 budget_extension 令牌字段级作者 schema**（执行项：补齐到 guide §六，作者基准，非删除项；字段集含 `extension_id`/`ts`/`granted_at_usage`/`triggering_block_event_id`/`new_ceiling`/`prior_ceiling`/`supersedes`/`scope`/`observed_usage`/`effective_ceiling`/`user_quote`；`granted_at_usage` 由 `budget_gate.py` `validate_extensions` L383 机械校验 `== decision.observed_usage`；`user_quote` 为作者基准，`validate_extensions` 不含它，故不指向其为 `user_quote` 作者单源）。
- **state-schema §结构化协议字段扩展（evidence_tier / dispute_topic_id）**。
- **state-schema §预算 gate 的 NARROW 保留项**：extension 校验细节（L437，含 `user_quote` 人类可审计凭据、非机械可证明）+ task-envelope 四档档位表（L461-466）——agent-relevant/判断，**保留**，不属 L79 的 PURE MACHINE JSON schema 重复删除。

## 改动范围

- 只改：SKILL.md、refs/orchestrator-guide.md、refs/state-schema.md、refs/quality-gate.md（L82 引用修复），外加 `scripts/budget_gate.py` 的一处**注释/docstring 行**修正（零运行时行为变化）与 L91 注释核对（仅确认，零改动）。
- **两处暴露的悬空子锚点引用修复（新增入范围）**：
  - SKILL.md 任务级总信封 note（原 L458）：保留指向 `任务档预算`/task-envelope scope 锚点（语义指针）；BLOCK 语义 / 与 total 正交 / summary 命令等机制细节改指 `scripts/budget_gate.py`（task-envelope 单一权威源），不保留机制复述。
  - refs/quality-gate.md L82：改为「consumes-summary 在 state-schema §预算 gate；完整 `ROLE_CONSUMES` 单一权威源 = `scripts/budget_gate.py`」。
- SKILL.md：删数值复算（`63/62` 推导、[^totalcap] 重复表与导出）；保留 `max_total_reserved_spawns` 规范式与 DEFAULTS 单源指针；必检清单**只删 2 项机械项**、其余提醒保留；M-11 的 hook-wiring 收缩为**前序已单源（#16）**，本 delta 不重做——仅保留**三条纯 prose 义务**作为保留确认（非删除项）。
- refs/orchestrator-guide.md：§六·预算追踪 + gate 编排 **补齐** budget_extension 字段级作者 schema（执行项：补入 `extension_id`/`ts`/`granted_at_usage`；`granted_at_usage` 标注 `validate_extensions` L383 `== decision.observed_usage`）、引全量数据契约改指 `budget_gate.py`；§六 命令序列重复收缩为**前序已单源（#16）**，本 delta 不重做；§一 收缩机械探测、保留语义项。
- refs/state-schema.md：§预算 gate 仅删除 **PURE MACHINE JSON schema 重复**（L79 三类：`gate-ledger.jsonl` 精确 JSON 字段规格、`_budget-state.json` 内部字段、计数模型内部结构）；保留命名锚点 `角色对照表`（缩减为 agent-relevant「角色→consumes」摘要，仅删 `终局-owner-资格` 列）、`任务档预算` / task-envelope scope 语义指针与**档位表（L461-466）**、**extension 校验细节（L437，含 `user_quote` 人类可审计凭据，非机械可证明）**——均指向 `scripts/budget_gate.py`；§结构化协议字段扩展不动。L508（与角色对照表同节）因锚点保留自然解析。
- **scripts/budget_gate.py（仅注释/docstring 行，零运行时行为变化）**：`_validate_event` docstring（L525-526）中「与 refs/state-schema.md §预算 gate 的事件契约一一对应」的反向引用，改写为「本脚本是 gate-ledger / `_budget-state.json` / 计数 / 事件契约等全量机器数据契约的单一权威源（编译）；refs/state-schema.md §预算 gate 仅保留 agent 需读的角色摘要」。仅改注释/docstring，**不触碰任何运行时逻辑**。
- **scripts/budget_gate.py L91 注释核对（纳入本 delta 确认项）**：L91 注释行（to 角色对照表）必须仍指向保留的 `角色对照表` 锚点——由于本版**不再重命名该锚点**，该注释现已满足、无需改动；仅作确认（零运行时行为变化）。
- **不新增 `docs/budget-gate-contract.md`**；运行时不改动脚本行为（仅 `budget_gate.py` 注释/docstring 一行反向引用修正）；framework-adapters 分册不动（M-11 §A.1 指针已单源）。
- **本 delta 等价映射表**：`docs/plans/active/20260826-doc-need-to-know-equivalence.md`（验收 #2 引用；登记本 delta 删除行 -> 单源/保留位置/指针；前序已单源条目（M-11 hook-wiring / §六 命令序列，rows 16/21）沿用已归档映射表 `docs/plans/done/20260826-doc-layer-refactor-equivalence.md`，本 delta 不重做）。**「不得靠记忆计数」行为禁令的保留位置 = `refs/orchestrator-guide.md` §六**（非 SKILL.md 压缩哲学注）；该保留位置须记入等价映射表。

## 验收标准

1. **范围目标（替代硬行数）**：改动范围 = 本计划所列各压缩/保留项（delta 视角，不含前序已落地条目）。行数（SKILL.md <=450 / guide <=440 / state-schema <=420）**仅为参考**，非硬性验收限制；**语义/义务保留始终优先**。本计划与风险节之间**无行数硬指标矛盾**。
2. **单源存在且完整**：对每条删除/保留确认，本 delta 的**自有等价映射表**（`docs/plans/active/20260826-doc-need-to-know-equivalence.md`；**已登记本 delta 全部 8 条映射行**（7 条删除/收缩 + 1 条非删除项——extension 作者 schema 执行项「补齐到 guide §六」，非删除行）：行 1 数值复算移除、行 2 预算哲学注压缩、行 3 必检清单 2 项、行 4 主循环内部实现、行 5 state-schema §预算 gate（含 guide §六 全量数据契约引用改指 + quality-gate L82 指针重定向，折叠）、行 6 extension 作者 schema（执行项：补齐到 guide §六，非删除行）、行 7 §一 机械探测、行 8 SKILL.md 任务级总信封）记录「删除段 -> 单源/脚本文档/迁移目标」且确证存在（前序已单源条目沿用已归档映射表 `docs/plans/done/20260826-doc-layer-refactor-equivalence.md`，本 delta 不重做）；`budget_gate.py` 的 `ROLE_CONSUMES`、公式与 schema 仍能覆盖被删的维护者视角内容（grep 验证）。
3. **语义零弱化**：「明确不删」清单逐项在 SKILL.md/guide 中仍存在（grep 触发词）；非 PROCEED 处置表完整；M-11 三条纯 prose 义务（混合后端检查点 / 宿主能力矩阵 / auditable-only 纯 prose 声明）以**保留检查**验证仍在——它们保留，但**不再**作为本 delta 的「删除行」。
4. **机械核对与义务保留**：
   - `git diff --check` 通过。
   - 必检清单中**只删**「archive 返回成功」「check 返回 valid-v1」两项；**保留**的提醒（extension 关联 decision + round-stamped 用户原话 / 每 spawn 有 reservation 且 settle / 无孤儿 / extension 仅抬 ceiling / auditable-only 无机械兜底）经 grep 验证为 **>=1 命中（NOT 0-hit）**。
   - 内环预算不变量**保留在 SKILL.md 主循环**（随 ★/盲审不变量，非删除）：grep 验证 **`不推进 max_outer_loops` 与 `不占新 spawn cap` 均 >=1 命中（NOT 0-hit）**（对应 SKILL.md L300 保留句「不推进 max_outer_loops、不占新 spawn cap」，即 continue 不推进 max_outer_loops、不占新 spawn cap 的内环预算不变量）——该不变量**不**仅靠 `scripts/README.md` L82 指针（L82 未写「不推进 max_outer_loops / 不占新 spawn cap」，指针不足单独承接）。
   - §六·预算追踪 + gate 编排 budget_extension 字段级 authoring schema **已补齐**：guide §六 extension authoring 描述经 grep 验证 **`extension_id`、`ts`、`granted_at_usage` 三者均存在（NOT 0-hit）**，且 `granted_at_usage` 标注由 `budget_gate.py` `validate_extensions` L383 校验为 `== decision.observed_usage`；保留 `user_quote` 作者基准（**不**指向 `budget_gate.py` 作为 `user_quote` 作者单源）。
   - M-11 三条纯 prose 义务（混合后端检查点 / 宿主能力矩阵 / auditable-only 纯 prose 声明）逐条仍在。
   - `max_total_reserved_spawns` 规范式语句保留；`63/62` **推导/复算措辞**已删——grep 目标为推导式复算与 `[^totalcap]` 复算表/导出（对 `ceil(1.5*42/41)`、`63/62` stock 双档表、无边界下溢说明等），**非**原始数字本身；一行行为事实「普通=63 / ultraverge=62」**允许保留**，不视为残留。
5. **无悬空引用 / 单源指正（reference-sweep，EXHAUSTIVE grep）**：
   - 以 `state-schema.md §预算 gate`、`角色对照表`、`任务档预算` 为触发词，**跨 `SKILL.md`、`refs/*.md`、`scripts/budget_gate.py` 注释**，**逐处**核对全部出现**必须仍解析到保留的命名锚点**（`角色对照表` / `任务档预算`）。`docs/plans/done/**` 等历史文档标记为 historical，不要求改动。
   - `refs/state-schema.md` §预算 gate **存在**且 `角色对照表` 锚点保留（不重命名）；state-schema L508（与角色对照表同节）、`budget_gate.py` L91 注释（to 角色对照表）、quality-gate L82（经修复的 consumes-summary + 完整 `ROLE_CONSUMES` 单源指针）均解析；`终局-owner-资格` 列由 `scripts/archive_contract/model.py`（`REVIEWER_AUTHORITIES`）+ state-schema L44 覆盖（已修正，不再引用 reviewer-discipline / quality-gate L82 完整 owner 列）。
   - SKILL.md / guide 中指向**全量机器数据契约**的引用改为指向 `scripts/budget_gate.py`（单一权威源）。
   - 仓库中**无** `docs/budget-gate-contract.md` 创建动作。
6. **判断内容零弱化**：宪法强制确认点、终止状态语义、★步骤清单、偏见/边界场景段落逐项仍在（位置可变）。

## 风险与裁决点

- **过度削减**：删除判据必须满足「脚本 fail-closed 保证」或「纯实现描述」或「脚本已计算的复算」。若评审认为某项删除会弱化判断指导（如必检清单的「extension 关联 decision 事件」、M-11 的混合后端检查点/宿主能力矩阵、§六·预算追踪 + gate 编排 字段级作者 schema），裁决原则=判断/义务/作者基准优先于行数；可保留为一句提醒而非删除。
- **行数为参考非门槛**：行数下降不得以牺牲上述语义/义务为代价；若压缩后行数未达标，应以范围目标达成与语义完整性为准，不追加删除。
- **SPOT 基准**：本计划基于已合入 #16（squash 6990314）与 #15 之后的 master；库内文件行号仅作参考，改动以**具名节/锚点**定位。

## 评审处置记录

- （ultraverge 各轮由 .converge/ 归档承载，此处记最终结论）

- **ultraverge 3/3 评审 -> 8 项 BLOCKING 处置后修订（本版已并入）**：
  1. **与已落地 doc-layer-refactor 的冲突**：本版改为 DELTA，增加「前序已单源、本 delta 不重做」节与头部声明；明确本计划不再重做 M-11 hook wiring（-> claude-code §A.1）、§六·预算追踪 + gate 编排 命令序列、§Archive/reopen 不变量、配置两分法与 `max_total_reserved_spawns` 规范式；并交叉引用已归档等价映射表。
  2. **规范式删除违规**：`max_total_reserved_spawns` 规范式保留于 SKILL.md（脚本派生的机械强制上限）；仅删陈旧数值复算（63/62 推导、[^totalcap] 重复表与导出），保留公式语句与 8 个脚本实收键的 DEFAULTS 指针。
  3. **budget-gate 契约迁移重设计（按 R2）**：删除创建 `docs/budget-gate-contract.md` 的方案；state-schema §预算 gate 不迁移、缩减为 agent-relevant 角色摘要；全量机器数据契约与 `ROLE_CONSUMES` 单一权威源 = `scripts/budget_gate.py`。范围修正：§预算 gate 止于 L502，L506+ 的 §结构化协议字段扩展（evidence_tier/dispute_topic_id）必须保留。
  4. **跨引用扫尾**：不迁移内容 -> 无悬空引用；对指向《state-schema §预算 gate》的引用，验收加入「该锚点仍存在且解析」；对指向全量数据契约的引用改指 `budget_gate.py`。
  5. **M-11 纯 prose 义务保留**：M-11 缩减仅限 hook-wiring 命令级 -> §A.1 指针；混合后端检查点、宿主能力矩阵、「auditable-only 无机械兜底」三条完整保留。
  6. **必检清单只删真机械项**：只删「archive 返回成功」「done check 返回 valid-v1」；保留 extension 关联 decision + 用户原话、每 spawn reservation + settle / 无孤儿、extension 仅抬 ceiling、「无不可阻断 hook 的 auditable-only 提醒」为一行提醒。验收 #4 改为验证这些提醒仍存在（NOT 0-hit）。
  7. **§六·预算追踪 + gate 编排 extension 字段 schema = 作者基准（outer R7 B1 厘清为执行项「补齐到 guide §六」）**：不把字段级 schema 当纯 gate 校验删除；**补齐**字段描述（`extension_id`/`ts`/`granted_at_usage` 一并补入 guide §六；`granted_at_usage` 由 `validate_extensions` L383 机械校验 `== decision.observed_usage`；`user_quote` 为作者基准，`budget_gate.py` 的 `validate_extensions` 不含它，故**不**指向其为 `user_quote` 作者单源）；保留「关联真实 BLOCK decision + user_quote + 单调 ceiling 链；FAIL_CLOSED；不得记忆续费」。
  8. **行数硬指标改参考**：验收 #1 改为范围目标 + 行数仅参考，语义/义务优先；消除验收与风险节间的内部矛盾。

- **outer Round 1 -> 2 项 BLOCKING 处置（本轮已并入）**：
  1. **B1 单权威反向引用**：选择 (a)——在「改动范围」追加 `scripts/budget_gate.py` 的 docstring-only 编辑（注释行、零运行时行为变化）；将其 `_validate_event` docstring 中对 `refs/state-schema.md §预算 gate` 的反向引用改为「本脚本为 gate-ledger / `_budget-state.json` / 计数 / 事件契约等全量机器数据契约的单一权威源（编译）；state-schema §预算 gate 仅保留 agent 需读的角色摘要」。不改运行时逻辑。
  2. **B2 结构等价映射**：为本 delta 创建**自有等价映射表** `docs/plans/active/20260826-doc-need-to-know-equivalence.md`，登记本 delta 删除行（数值复算移除、必检清单 2 机械项移除、state-schema §预算 gate 缩减、extension 作者 schema 保留；~~M-11 hook-wiring 收缩~~——**历史快照**：当前表**不含 M-11**，前序已单源、本表不重复登记）的「删除段 -> 单源/保留位置/指针」；验收 #2 改为引用该自有映射表（前序已单源条目沿用已归档映射表）。
  3. **fold 项**：(a) 锚点标签统一改为「§六·预算追踪 + gate 编排」（对应 guide 「六、职责操作指引」下的「预算追踪 + gate 编排」小节）；(b) 验收 #4 的 grep 目标明确为推导/复算措辞而非原始数值，一行行为事实（普通=63 / ultraverge=62）允许保留；(c) budget_extension 的 `user_quote` 保留 guide 作者字段描述（作者基准；`validate_extensions` 不含它），**不**指向 `budget_gate.py` 作为 `user_quote` 作者单源。

- **outer Round 2 -> 1 项 BLOCKING 处置（本轮已并入）**：
  1. **B1 悬空子锚点引用（SKILL.md 任务级总信封 note / refs/quality-gate.md L82）**：state-schema §预算 gate 缩减为 agent-relevant 角色摘要 + 指向 `budget_gate.py` 后，两处仍引用其子锚点（「任务档预算/task-envelope scope」「角色对照表」）会悬空，且此前不在「改动范围」。处置：将两处**均纳入「改动范围」**（SKILL.md 任务级总信封 note 机制细节（BLOCK 语义 / 与 total 正交 / summary 命令）改指 `scripts/budget_gate.py`（task-envelope 单一权威源）+ state-schema §预算 gate 角色摘要；新增 refs/quality-gate.md L82 引用修复：完整 `ROLE_CONSUMES` 单一权威源 = `scripts/budget_gate.py`），并**加入验收 #5 reference-sweep**。
  2. **fold 建议**：(a) ~~state-schema §预算 gate 标题改为「角色契约摘要(agent-relevant)」~~ ——**已被 outer R3 B1 否决**：保留 `角色对照表` 命名锚点，不重命名，仅删 PURE MACHINE JSON schema 重复；(b) 「不得靠记忆计数」行为禁令的保留位置 = `refs/orchestrator-guide.md` §六（非 SKILL.md 压缩哲学注），记入等价映射表——**保留（R3 B3 确认）**。

- **outer Round 3 -> 3 项 BLOCKING 处置（本轮已并入，结构性修复）**：
  1. **B1 命名锚点稳定性（根治 whack-a-mole）**：放弃「标题重命名为 `角色契约摘要`」——保留 state-schema §预算 gate 的命名锚点 `角色对照表`（不重命名；缩减为 agent-relevant「角色→consumes」摘要，仅删 `终局-owner-资格` 列）与 `任务档预算` / task-envelope scope 语义指针；仅移除 §预算 gate 内 **PURE MACHINE JSON schema 重复**（gate-ledger.jsonl 精确字段规格、_budget-state.json 内部字段、计数模型内部结构），以「machine schema / `ROLE_CONSUMES` / 计数模型单一权威源 = `scripts/budget_gate.py`」替代。这使 `budget_gate.py` L91、state-schema L508、quality-gate L82、SKILL.md L458 全部指向保留锚点，停止逐处打补丁。
  2. **B2 验收 #5 全面扫**：reference-sweep 改为 **EXHAUSTIVE grep**——凡 `SKILL.md` / `refs/*.md` / `scripts/budget_gate.py` 注释中出现 `state-schema.md §预算 gate`、`角色对照表`、`任务档预算` 的**每一处**都必须解析到保留锚点；`docs/plans/done/**` 标记 historical，不改。
  3. **B3 等价映射 row#2 保留位置修正**：「不得靠记忆计数」行为禁令规范式保留于 `refs/orchestrator-guide.md` §六（不靠 Orchestrator 记忆比较计数）；SKILL.md 压缩注仅指针；等价映射表已更新。
  4. **改动范围补充**：加入 `budget_gate.py` L91 注释核对（必须仍指向保留的 `角色对照表` 锚点——现已满足，仅确认）。

- **等价映射表 盲审 recheck（B1）处置（已并入）**：补齐计划正文已列、但等价映射表缺失的 3 条删除行——(a) orchestrator-guide §六 命令序列重复（单源 = `scripts/README.md` Loop A；语义规则保留）；(b) orchestrator-guide §一 机械探测项「展开」收缩（单源 = `refs/testing-toolbox.md`；语义自足项保留）；(c) SKILL.md 任务级总信封 note（移除机制复述，重定向 = `scripts/budget_gate.py`；保留正交性语义指针）。映射表现为 10 行（**该轮视角的历史记录**；当前表为 8 行——其中 guide §六 全量数据契约引用改指已折叠进 row 5、不新增行，见验收 #2），验收 #2 引用完整表。**fold 两项建议**：(1) 删除 [^totalcap] 脚注定义与推导时，同步删除 SKILL.md 配置表行（`max_total_reserved_spawns`）中的 [^totalcap] 内联引用标记，该行仅保留一行行为事实；(2) state-schema §预算 gate 保留节标题（锚点稳定），并在该节内以一句「全量数据契约单一权威源 = `scripts/budget_gate.py`」替代被删的 PURE MACHINE JSON schema 重复。

- **outer Round 6 -> 2 项 BLOCKING 处置（本轮已并入）**：
  1. **B1 结构（budget_extension 作者字段清单留全）**：guide §六·预算追踪 + gate 编排的 budget_extension 作者 schema 字段清单补入 `extension_id`、`ts`、`granted_at_usage`，并标注 `granted_at_usage` 由 `budget_gate.py` `validate_extensions` L383 机械校验 `== decision.observed_usage`（`extension_id`/`ts` 为纯作者字段）；等价映射表 extension 作者 schema 行同步补入。
  2. **B2 实现（SKILL 压缩注仅指针、指针不丢失）**：SKILL.md 预算执行哲学注压缩句补入指针 `[行为禁令「不得靠记忆计数」规范落在 refs/orchestrator-guide.md §六;SKILL 此处仅指针]`，满足「压缩注仅指针」承诺；等价映射表 row 2 同步。
  3. **fold**：(a) 可削减点节内将「保留确认（非删除项）」与可削减项区分（加范围界定 note）；(b) `终局-owner-资格` 列删除的覆盖性补一句——作者源应为 `scripts/archive_contract/model.py`（`REVIEWER_AUTHORITIES`）+ `refs/state-schema.md` L44；**修正**：非 quality-gate L82（已不再指向完整 owner 列）或 reviewer-discipline（无该枚举），见 outer R7 fold(c)；(c) 等价映射 rows 6/21 中 `§六.5` 改指命名锚点 `§六·预算追踪 + gate 编排`。

- **outer Round 7 -> 2 项 BLOCKING 处置（本轮已并入）**：
  1. **B1 结构（guide §六 extension 字段改动从「保留/确认」改为「补齐到 guide」）**：guide §六·预算追踪 + gate 编排的 budget_extension 字段级作者 schema 从「保留/确认（非删除项）」改为**实际执行项「补齐到 guide §六」**——在 guide 的 authoring field description **补入** `extension_id`、`ts`、`granted_at_usage`，并标注 `granted_at_usage` 由 `budget_gate.py` `validate_extensions` L383 机械校验 `== decision.observed_usage`（`extension_id`/`ts` 为纯作者字段，脚本不生成）；该执行项与「保留 `user_quote` 作者基准、不指向 `budget_gate.py`」的既有裁决并存。等价映射表 row 6 同步改为「执行项：补齐到 guide §六（非删除行）」。验收 #4 增加 grep 核验：guide §六 extension authoring description 中 `extension_id`、`ts`、`granted_at_usage` 三者均存在（NOT 0-hit）。
  2. **B2 结构（主循环保留清单补齐内环预算不变量）**：主循环内部实现收缩的保留清单**新增**内环预算不变量「continue 不推进 max_outer_loops、不占新 spawn cap（仅计数入 max_inner_loops）」——该不变量来自前序归档映射表 `docs/plans/done/20260826-doc-layer-refactor-equivalence.md` row 8；它**保留在 SKILL.md 主循环**（随保留的 ★/盲审不变量），**不**仅靠 `scripts/README.md` L82 指针（L82 只写「计数入 max_inner_loops=3」、未写「不推进 max_outer_loops / 不占新 spawn cap」，指针不足单独承接）。等价映射表 row 4（主循环内部实现）同步记录该保留不变量。
  3. **fold 项**：(a) 评审处置记录「映射表现为 10 行」标注为**历史记录**（该轮视角；当前表为 8 行，见验收 #2）；(b) guide §六 引全量数据契约改指 `budget_gate.py` 折叠进等价映射表 row 5（不新增行，保持 8 行计数不变）；(c) `终局-owner-资格` 列删除的覆盖作者源改为 `scripts/archive_contract/model.py`（`REVIEWER_AUTHORITIES` 枚举）+ `refs/state-schema.md` L44（owner 授权说明），**不**引用 reviewer-discipline（无该枚举）与 quality-gate L82（已不再指向完整 owner 列）。

- **outer Round 8 -> 2 项 BLOCKING 处置（本轮已并入）**：
  1. **B1 内环预算不变量 grep 存在性核验**：验收 #4 新增——内环预算不变量（continue 不推进 max_outer_loops、不占新 spawn cap，仅计数入 max_inner_loops）须在 SKILL.md **NOT 0-hit**：grep 目标为 SKILL.md L300 保留句中的 **`不推进 max_outer_loops` 与 `不占新 spawn cap`**（保留约束，非删除；避免使用 SKILL.md 中不存在的「continue 不推进 max_outer_loops」连续词导致 0-hit 假阳性）；该不变量**不**仅靠 `scripts/README.md` L82 指针（L82 未写「不推进 max_outer_loops / 不占新 spawn cap」，指针不足单独承接）。
  2. **B2 state-schema §预算 gate 删除范围定为 NARROW（L79 三类）**：正文 L76 措辞由「全量机器数据契约」对齐为「PURE MACHINE JSON schema 重复（L79 三类）」；明确**保留** extension 校验细节（L437，含 `user_quote` 人类可审计凭据、非机械可证明）与 task-envelope 四档档位表（L461-466）——agent-relevant/判断，非删除；等价映射表 row 5 源/目标同步为 NARROW。
  3. **fold 项**：(a) quality-gate.md L82 指针重定向折叠进等价映射表 row 5（不新增行，保持 8 行计数）；(b) 评审处置记录「应移至 docs/plans/done/」陈旧说明改写为已归档；(c) SKILL 预算注指针具名 framework-adapters 分册（§A.1 claude-code / §A.6 kimi-code / §A.7 dsh）；(d) outer R1 历史行中 M-11 hook-wiring 标注为「历史快照，当前表不含 M-11（前序已单源）」。

> 归档说明：`docs/plans/active/20260826-doc-layer-refactor.md` 与其等价映射表 `docs/plans/active/20260826-doc-layer-refactor-equivalence.md` **已**归档至 `docs/plans/done/`（历史记录；无需再移动）。