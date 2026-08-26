# 文档层重构：确定性归脚本单源，判断留入口（SKILL.md 去机械化 + guide 去重 + loop driver 接线）

状态：进行中（ultraverge 评审中；本版已并入 3 方 ultraverge 6 项 BLOCKING 处置与面板建议）

## 设计哲学（本计划的裁决尺）

仓库既定分工：**所有确定性的东西（顺序、记账、路由、验收、止损）交给脚本机械保证；所有需要判断的东西（verdict、副作用重派、prompt 内容、模型选择）强制留在 agent 手里。**

运行时已按此切分：SKILL.md 执行流程·Orchestrator 主循环总则 声明机械动作必须经 orchest.py、判断动作标注★。本计划不改任何机制，只让**文档结构与已声明的机制分工对齐**——消除文档层对脚本已机械保证内容的散文重述（同一事实多源，漂移风险）。

## 语义零改动锚点（评审核心依据）

1. SKILL.md 执行流程·Orchestrator 主循环总则 原文逐字保留。
2. 所有被移出/去重的内容，其语义不变量必须在单源处存在且等价（逐节 diff 核对，见验收）。
3. 判断类内容（★步骤、宪法强制确认点、终止状态语义、振荡语义判定、偏见意识、边界场景）一律不删不弱化，只做去重与指针化。
4. 配置参数单源化按两分法处理：脚本实收的预算参数（budget_gate.py DEFAULTS 中实际在 SKILL.md 配置表有行的 7 个键：max_outer_loops/max_blind_rechecks/ultraverge_min_reviewers/max_inner_loops/impl_severity_streak_threshold/preflight_code_block_threshold/total_safety）数值列写“见 budget_gate.py DEFAULTS（单源）”，数值以脚本为准；preflight_code_loc_threshold 虽属 DEFAULTS 8 键，但在 SKILL.md 配置表中无行，故不在重指向范围，也不新增行。判断侧阈值（type_o_threshold/type_r_threshold/plan_drift_check_interval/converge_dir/gate_l1_interval/gate_l2_mode/gate_l2_signal_threshold/gate_max_token_share/executor_model_tier/max_ultraverge_initial/relay_oscillation_interval/task_tier/task_envelope_* 等）是判断侧阈值，未经任何脚本强制，按宪法第一部由 Orchestrator 判断侧设定，故**保留其数值于 SKILL.md 表内**，仅做真实重复去重，不得指向脚本 DEFAULTS（脚本无此数据，指向即悬挂）。max_total_reserved_spawns 为脚本派生的机械强制上限（其规范公式保留在 SKILL.md），不属判断侧阈值，也不指向脚本 DEFAULTS。

## 三刀改动清单

### 第 1 刀：接线 converge_loop.py（纯新增指针）

- scripts/README.md：新增一节 converge_loop.py（run/resume/validate/status；loop-spec 驱动派发阶段机械调度；其描述须注明依赖**经 spec 提供的外部 ocsr_dispatch 可执行文件**，即 converge_loop 按 spec 调用 ocsr_dispatch，非本仓库内置执行体；何时用：整个收敛循环的机械阶段需 spec 推进时；边界：语义判定/verdict/prompt 组装仍 LLM）。
 - 同步把 converge_loop.py 补进该文件“其他脚本”清单。
 - 一并把 l1_gate.py、distill_antipatterns.py、hooks/* 补进该文件“其他脚本”清单（与 converge_loop.py 同列）。
 - 在 scripts/README.md 标注其作为脚本命令/用法清单的单源状态；并注明 scripts/README.md 不在 CONSTITUTION 保护文件清单内——加维护说明：任何脚本或文档改写涉及该清单时须同步维护，并走常规评审而非保护文件豁免路径。
 - **修订 scripts/README.md 过时的过渡性头注**：该文件目前宣称“SKILL.md 接线留给未来计划”，但 SKILL.md 现已接线；落地须将其改写为“本文件为脚本命令/用法清单的单源”，消除该过期声明。验收 #2 增加对过渡性措辞的 grep（见验收）。
 - 记录（仅记录，不实现）一条治理建议：脚本命令契约保护应纳入未来宪法修正案裁决（脚本/文档改动触发契约变更时走保护路径）；本计划不实现该机制。
 - **单活约束（cut 1/3d）**：converge_loop 的 spec 驱动路径与人工主循环不得**并发驱动同一 active 目录**——二者同时写会造成 ledger/budget 双计数风险；落地须在 converge_loop 说明与 SKILL.md/guide 边界声明中明确“同一 active 目录同一时刻只允许一条驱动路径（spec 驱动或人工主循环）”。
- SKILL.md 执行流程总则（执行流程·Orchestrator 主循环总则 后）追加一句：机械阶段可由 converge_loop spec 驱动（run --spec），LLM 只承担★步骤；命令细节见 scripts/README.md。再追加一句：converge_loop 为**可选调度器**（OPTIONAL scheduler），语义判定始终按 SKILL.md 主循环执行。
- SKILL.md 拆分文件索引表追加一行：循环级机械调度 | scripts/converge_loop.py（用法见 scripts/README.md）。

### 第 2 刀：SKILL.md 去机械化（执行流程段移出/去重）

2a. **执行流程命令块单源化**：主循环 a0/a0+a/b/d2/f、盲审 reserve/register、inner-loop continue 的完整 CLI 命令块（执行流程·命令块内嵌命令）收缩为“命令名 + 一句用途”，细节单源指向 scripts/README.md（Loop A 接线示例已在）。
   - **明确边界（仅收缩命令调用/序列）**：只允许把 CLI 命令调用/命令序列收缩为“命令名 + 指针”；**所有循环结构语义必须保留在 SKILL.md**，至少枚举保留：c+1（角色边界自检：即将编辑产品前若越界则跳到 f）、c+2（drift 上下文注入下一轮 prompt）、c+3（规则触发记录）、d2（pre-checks → retrospective → finish）、d3（落地意图裁决）、e/g/h（契约/计划修订顺序）、i（inner-loop 接受）。这些不随命令块收缩。
   - 保留：★语义步骤（verdict 处置、升级判定、盲审触发条件、BR- 注入、overturn/Type R 标注）、gate 裁决处置表语义（BLOCK/MODE_SWITCH/DENY/FAIL_CLOSED 各自的停止语义，非命令）。
   - **盲审不变量保留在 SKILL.md（无其他单源）**：pass|fail|waived 标注语义（verdict 与 annotation 是两个概念；annotation 从不被摄入；waived 无 gate action）以及盲审修复轮共享原 max_outer_loops、不自动扩展。此处在 2a/2d 联合保证不收缩、不删除。
2b. **配置参数表数值单源化（按预算参数/判断侧阈值两分）**：表格保留参数名+语义+调优脚注引用。
   - 脚本实收预算参数（budget_gate.py DEFAULTS 中实际在 SKILL.md 配置表有行的 7 键：max_outer_loops、max_blind_rechecks、ultraverge_min_reviewers、max_inner_loops、impl_severity_streak_threshold、preflight_code_block_threshold、total_safety）：其数值列改为“见 budget_gate.py DEFAULTS（单源）”，数值只由脚本决定。preflight_code_loc_threshold 虽属 DEFAULTS 8 键，但在 SKILL.md 配置表中无行，故不在重指向范围，也不新增行。
   - 判断侧阈值（type_o_threshold、type_r_threshold、plan_drift_check_interval、converge_dir、gate_l1_interval、gate_l2_mode、gate_l2_signal_threshold、gate_max_token_share、executor_model_tier、max_ultraverge_initial、relay_oscillation_interval、task_tier、task_envelope_*）：不被任何脚本强制；按宪法第一部阈值/参数设定留在 Orchestrator 判断侧。**在 SKILL.md 表中保留其数值**，仅对真实重复去重；不得改为指向脚本 DEFAULTS（会造成悬挂源）。
   - max_total_reserved_spawns 不属判断侧阈值，而是**脚本派生的机械强制上限**（derived cap）：其规范公式保留在 SKILL.md，脚本据此机械强制执行；不作为 judgment-side 阈值处理，也不指向脚本 DEFAULTS。
   - **DEFAULTS 单源与模式相关行为事实分离**：2b 的“数值列见 DEFAULTS”只对应**默认值单源化**；**模式相关的行为事实**（如 ultraverge 初始化配置覆写 max_blind_rechecks=2、total 上限按规范式重算为 62）属于 SKILL.md 的行为说明，**保留在 SKILL.md 正文（行为注）**，不得并入 2b 的调优史脚注（脚注仅承载调优历史，不承载模式行为覆写）。验收 #2 增加 `max_blind_rechecks` / `42` / `44` grep 模式。
   - 调优史脚注：改为指向 budget_gate.py DEFAULTS 注释 + git 历史（提交 0137fce），或在表中保留一行调优理由；不再指向 docs/CHANGELOG.md（该文件无对应 2026-08-16 调优条目）。
2c. **目录结构段（SKILL.md 目录结构节）迁移为 state-schema 新规范节**：state-schema 目前只定义文件格式小节，并不含目录树；目录树 + slug 命名 + post-convergence 修订注（done→active→re-archive）仅存在于 SKILL.md 目录结构节。因此本刀为**从 SKILL.md 迁入 refs/state-schema.md 并新增一个规范章节**（非“既有单源”声明）；SKILL.md 留 3 行摘要+指针。新增节自带等价检查：覆盖 slug 命名 与 done→active→re-archive 修订注。
2d. **Archive Contract v1 段收缩**：state-schema §Archive Contract v1 标注自身为“规范单源”；SKILL.md 收缩为 3 行声明（不变量要点）+指针。盲审不变量由 2a 边界保留在 SKILL.md（2a/2d 联合保证）。
2e. **责任清单去重**：M-11 内嵌的 best-effort guarded hook 接线细节（bind/unbind/refresh-cap 命令级描述）收缩为语义+指针（framework-adapters/claude-code.md §A.1 为接线单源）；C-20/C-21 中与 orchestrator-guide §六/§八 逐字重复的操作细节收缩为职责要点+指针。
2f. **传话编排收缩**：SKILL.md 内该小节保留政策（适用三条件、载荷强制文件引用、独立性降级声明、角色边界），操作细节按下述单源映射收缩：
   - 振荡裁判（oscillation-referee）spawn 语义保留在 SKILL.md；**不指向 orchestrator-guide §八**（guide §八只有 landing+relay，无 oscillation-referee spawn 细节，原指针断裂）。
   - relay-ledger 记录格式以 state-schema §relay-ledger 为**唯一单源**；guide §八 的 relay 记录字段集描述（与 state-schema 双源）删除，收缩为只管操作（见第 3 刀 3c）。**字段级等价核对**：guide §八 的 field set 含 timestamp 字段，而 state-schema §relay-ledger 的五字段集不含 timestamp——二者存在真实差异；落地时须产出字段级等价映射（field-by-field equivalence map），明确裁决 timestamp 是被有意丢弃还是补入 state-schema 作为单源，并将裁决记入等价映射附录。等价映射须覆盖五组中英字段名：发送方/sender_role、轮次/round_id、产物路径/artifact_path、内容hash/content_hash、结论摘要/verdict_or_response——不仅 timestamp。

### 第 3 刀：orchestrator-guide.md 去机械重复（515 → 参考 ~300-350 行）

3a. **§Archive/reopen 操作**：完整命令序列被 orchest.py finish 单命令取代部分删除。**明确边界**：只有 archive 序列被 finish 取代；以下内容必须保留在 guide（无其他单源）：per-spawn begin/complete/recover 生命周期、reopen old-manifest 修订、journal 幂等恢复（重试同一命令，绝不手工删除 source/backup/staging/journal）、绑定唯一性（不可唯一绑定时停止，绝不按文件名猜 role/model）、bootstrap staging-only、legacy read-only。收缩为“何时 reopen + 上述不变量 + 指针 archive_convergence.py --help 与 scripts/README.md”。
3b. **§六.5 预算追踪+gate 编排**：reserve-round/register-round/continue 命令序列删除（三处重复：SKILL.md/scripts README/guide），保留语义规则（非 PROCEED 处置、budget_extension 令牌约束、孤儿 reservation、禁止手跑裸序列）+ 指针。
3c. **§八 落地执行编排**：流程箭头图保留，“清单项数核对”的数数步骤保留（判断性核对），checkpoint-paths 用法细节指针化。**新增（第 3 刀范围）**：guide §八 收缩为操作层，删除与 state-schema §relay-ledger 重复的 relay record 字段集描述（relay 记录格式以 state-schema §relay-ledger 为单源）；保留 landing+relay 操作与落地执行编排；oscillation-referee spawn 语义不在 guide §八（留在 SKILL.md）。**字段级等价核对（relay dedup）**：guide §八 的 relay 字段集含 timestamp，state-schema §relay-ledger 五字段集不含 timestamp；落地时须按字段逐一对齐并记录裁决——要么确认 timestamp 有意丢弃，要么将 timestamp 补入 state-schema 作为单源。等价核对须覆盖五组中英字段名：发送方/sender_role、轮次/round_id、产物路径/artifact_path、内容hash/content_hash、结论摘要/verdict_or_response，并记录 timestamp 归属裁决。
3d. **§十 自主循环驱动器**：保留（交叉引用+边界声明）。**明确裁决**：converge_loop.py 是 converge 侧机械合并器（以 subprocess 调用 orchest.py + ocsr_dispatch.py），与 vault 侧 adapter driver（ocsr_driver_core.py）属**不同域**；§十 保留其 adapter-layer 边界措辞，并增加一句区别句，区分本仓库内 converge_loop.py 与 vault 侧 ocsr_driver_core.py。追加 converge_loop.py 为本仓库内参考实现的指针；同时说明其为可选调度器，语义判定仍按 SKILL.md 主循环。**单活约束（cut 1/3d）**：spec 驱动路径与人工主循环不得并发驱动同一 active 目录（ledger/budget 双计数风险）。

## 不改动清单（明确排除）

- CONSTITUTION.md、refs/reviewer-prompt.md、refs/executor-prompt.md、refs/state-schema.md 的既有规范内容（state-schema 仅新增目录结构一节——由 SKILL.md 迁入的**新规范章节**，不改动既有小节（文件格式、Archive Contract v1 规范单源声明））。
- framework-adapters 拆分结果与治理豁免（PR #15 范围；baseline 见风险与裁决点“与 PR #15 交叠”）。
- 任何运行时脚本（scripts/*.py）零改动；scripts/README.md 仅为清单/单源状态维护（第 1 刀），不属保护文件。

## 验收标准

1. 语义零改动核对：对每个被收缩/移出的段落，产出“原句 → 单源处等价句”对照表，逐条确认不变量等价；执行流程·Orchestrator 主循环总则 逐字未变。等价映射对照表持久化于本计划文件的《等价映射对照表》附录章节或 .converge/attempts/ 记录，落地提交须注明其路径。
2. 单源化核对（含存在性）：grep 验证每个被收缩段落/参数在 SKILL.md 内不再有完整副本（指针除外），**并在其声明的单源处存在等价内容**——即做逐参数/逐节的“单源存在性检查”，而不仅是“无双副本”检查。grep 准则以触发词/命令名为正则，例如：`converge_loop`、`reserve-round`、`register-round`、`--continue-of`、`archive_convergence`、`finish`、`BLOCK|MODE_SWITCH|DENY|FAIL_CLOSED`、`max_outer_loops`、`max_blind_rechecks`、`42`、`44`、`pass|fail|waived`、`振荡裁判|oscillation-referee`、`relay-ledger`、`slug`、`bootstrap`、`legacy`，以及 scripts/README.md 过渡性头注的“留给未来计划 / 未来计划”类措辞。
3. 行为等价：SKILL.md 拆分文件索引仍能导航到全部被移出内容；盲审/inner-loop/落地执行的语义步骤在 SKILL.md 或 guide 至少一处完整存在。
4. 范围目标（替代硬行数）：改动范围 = 本计划所列各刀；SKILL.md ≤400 / guide ≤380 仅为参考目标，非验收硬性限制；**语义保留始终优先于行数**。
5. 机械验证：git diff --check 通过；若仓库有 pre-commit/pre-push hook，通过或按其要求操作。
6. 判断内容零弱化：宪法强制确认点、终止状态语义、★步骤清单、偏见/边界场景段落逐项仍在（位置可变）。
7. 全 SKILL.md 陈旧数字一致性核对：SKILL.md 的 Ultraverge-path 一节目前声明 max_blind_rechecks 真默认 1、以及 42→44 的重算，与配置表及 budget_gate.py DEFAULTS（3/62）矛盾；落地须将这些陈旧数字对齐到 DEFAULTS/公式单源（属本计划消除之同事实多源漂移，故纳入范围）；核对确认后不再存在该等冲突数字（配合 #2 的 `max_blind_rechecks`/`42`/`44` grep）。

## 风险与裁决点

- **指针失效**：移出内容改指针后，链接目标必须存在（scripts/README、state-schema、guide 章节锚点）；落地后跑链接核对。framework-adapters/claude-code.md 指针目标（M-11 接线单源）一并纳入核对。
- **过度收缩**：若评审认为某段收缩会弱化判断指导（如 M-11 的混合后端检查点、2a/2d/3a 的保留边界），裁决原则=语义保留优先于行数目标。保留清单以 2a（循环结构与盲审不变量）、2d（盲审/Archive）、3a（Archive/reopen 不变量）为准。
- **与 PR #15 交叠**：本计划基于分支 `agent/doc-layer-refactor`；该分支已含 PR #15 framework split（按框架拆分提交 f98f910、治理豁免授予 e00fdbb）。**基线提交钉扎 e00fdbb8d69c714555eb0fe2aaa145cdb14a8e1f**；落地不得丢失 framework-adapters/claude-code.md 指针目标（读取由 index 指向分文件的 0.1 断点，保持 adapter 接线单源可导航）。
- **治理路径**：SKILL.md 与 orchestrator-guide.md 均为宪法第三部保护文件，且本次为机制定义文件改写（不符合 framework-adapters 式豁免前提）；**refs/state-schema.md 亦为宪法第三部保护文件**，且本次将新增目录结构一节规范内容（机制定义改写），同样纳入受保护文件范围。故走 ultraverge：≥3 独立 Reviewer 并行评议 + 收敛 + 强制设计审查；通过后人工确认提交。

## 评审处置记录

- （ultraverge 各轮结果由 .converge/ 归档承载，此处记最终结论）

- **UV-B1（architectural，3/3）— 已裁决**：2b 改两分法。脚本实收预算参数 = budget_gate.py DEFAULTS 的 8 键取“见 DEFAULTS（单源）”；原表其余参数为判断侧阈值，保留数值于 SKILL.md 表（仅去重真实重复），不得指向脚本。锚点 #4 同步改为两分法表述。
- **UV-B2（conceptual）— 已裁决**：3d 明确 converge_loop.py 为 converge 侧机械合并器（subprocess 调 orchest.py + ocsr_dispatch.py），与 vault 侧 adapter driver（ocsr_driver_core.py）不同域；§十 保留 adapter-layer 边界措辞并加区别句；第 1 刀追加“converge_loop 为可选调度器，语义判定按主循环”。
- **UV-B3（structural）— 已裁决**：oscillation-referee spawn 语义保留在 SKILL.md，不指向 guide §八（原指针断裂）；relay 记录格式以 state-schema §relay-ledger 为唯一单源，guide §八 收缩为操作层（并入第 3 刀 3c）。
- **UV-B4（structural）— 已裁决**：2a 增加“仅收缩 CLI 调用/序列、循环结构语义保留”边界并枚举 c+1/c+2/c+3/d2/d3/e/g/h/i；2a/2d 联合保留盲审 pass|fail|waived 与共享 max_outer_loops 不变量在 SKILL.md；3a 枚举 Archive/reopen 保留内容（per-spawn 生命周期、reopen 修订、journal 幂等、绑定唯一性、bootstrap staging-only、legacy read-only）。
- **UV-B5（structural）— 已裁决**：2b 调优史脚注改指 budget_gate.py DEFAULTS 注释 + git 历史（提交 0137fce），或在表中保留一行调优理由；不再指向无对应条目的 CHANGELOG。
- **UV-B6（structural）— 已裁决**：2c 改为“迁移并新增 state-schema 规范章节”（非既有单源声明），附 slug 命名与 done→active→re-archive 修订注的等价检查。

- **面板建议（并入）**：
  - 硬行数改为范围目标：改动范围 = 所列刀；SKILL ≤400 / guide ≤380 为参考，语义保留优先。
  - scripts/README “其他脚本”清单补 l1_gate.py、distill_antipatterns.py、hooks/*；标注 scripts/README 单源状态与其不在 CONSTITUTION 保护清单内（加维护说明）。
  - 验收 #2 增加逐参数/逐节“单源存在性检查”；#2/#3 明确 grep 正则与等价映射表持久化位置。
  - 基线提交钉扎 e00fdbb8d69c714555eb0fe2aaa145cdb14a8e1f（含 PR #15 framework split），落地不得丢失 claude-code.md 指针目标。

- **R1 非阻塞建议（并入）**：S1 2b DEFAULTS 重指向仅限 SKILL.md 配置表实际有行的 7 键（preflight_code_loc_threshold 无行，不新增，锚点 #4 同步）；S2 2b max_total_reserved_spawns 重新标注为脚本派生、机械强制的上限，规范公式保留在 SKILL.md，不列判断侧阈值，也不指向脚本 DEFAULTS；S3 2f/3c relay 去重须按字段级等价映射核对 timestamp 字段差异（guide §八 含 timestamp，state-schema 五字段集不含），落地裁决 timestamp 有意丢弃或补入 state-schema 单源并记录；S4 验收 grep 准则改用 `振荡裁判|oscillation-referee`；S5 治理路径补名 refs/state-schema.md 为受保护文件并新增目录结构规范节；S6 行号锚点改具名节锚（执行流程·Orchestrator 主循环总则 / 配置参数 / 目录结构 / Archive Contract v1 / M-11 / C-20 / C-21 / §六.5 / §八 / §十）。

- **设计评审亮点（并入本版）**：
  - **H1（陈旧数字一致性）— 并入验收 #7**：SKILL.md Ultraverge-path 的 max_blind_rechecks 真默认 1、42→44 重算，与配置表 + budget_gate.py DEFAULTS（3/62）矛盾；落地对齐到 DEFAULTS/公式单源，纳入同事实多源漂移消除范围。
  - **H2（DEFAULTS 单源与模式行为事实分离）— 并入 2b**：2b“见 DEFAULTS”仅指默认值单源化；ultraverge 初始化配置覆写（max_blind_rechecks=2、total 上限重算 62）作为行为注保留在 SKILL.md，不并入调优史脚注；验收 #2 增 `max_blind_rechecks`/`42`/`44` grep。
  - **H3（scripts/README 过渡性头注）— 并入第 1 刀**：改写宣称“SKILL.md 接线留给未来计划”的过期头注为“本文件为脚本命令/用法清单单源”；验收 grep 该过渡性措辞；另记录（不实现）治理建议：脚本命令契约保护纳入未来宪法修正案裁决。
- **边界注（并入本版）**：
  - **BN1（外部 ocsr_dispatch）— 并入第 1 刀**：converge_loop 描述须注明依赖经 spec 提供的外部 ocsr_dispatch 可执行文件。
  - **BN2（relay 字段等价映射五组中英字段名）— 并入 2f/3c**：字段级等价核对须覆盖 发送方/sender_role、轮次/round_id、产物路径/artifact_path、内容hash/content_hash、结论摘要/verdict_or_response，不仅 timestamp。
  - **BN3（单活约束）— 并入第 1 刀/3d**：spec 驱动路径与人工主循环不得并发驱动同一 active 目录（ledger/budget 双计数风险）。
