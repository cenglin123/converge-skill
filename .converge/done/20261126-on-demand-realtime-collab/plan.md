---
status: in_progress
created: 2026-11-26
owner: orchestrator
governance_level: ultraverge
target_files:
  - SKILL.md
  - refs/orchestrator-guide.md
  - refs/state-schema.md
  - scripts/README.md
---

# Plan: 为 converge-skill 增加「按需实时协同」可选宿主扩展与独立审计红线

## 1. 背景与目标

在具备原生多 Agent 实时协同能力（如共享消息板）的宿主上，主控 Orchestrator 在**收敛后的落地执行阶段（C-21）**常需并行修改多个相互依赖的文件。若强制每次交互都走一次性隔离派发或手工传话，会引入不必要的编排摩擦；反过来，若允许把实时协同带入独立审计环节，则会破坏反锚定机制。

本变更做两件事：
1. 在 `SKILL.md` 明示**独立审计上下文隔离红线**（按功能判据覆盖全部独立评审角色，同时禁止 Reviewer↔被审者 与 并行 Reviewer↔Reviewer 共享消息板/持续对话）。
2. 将**宿主原生实时协同能力**登记为收敛后落地执行（C-21）的**可选宿主扩展（optional host capability）**——canonical 路径仍是 `Spawn`（fresh-context Executor），宿主不支持时自动回退至 `Spawn` / 传话编排，保持框架无关；同步更新 `SKILL.md`（主循环 `d3`、C-21、传话编排）、`refs/orchestrator-guide.md`（§八）与 `scripts/README.md`（L97），消除跨文档矛盾。

**非变更声明**：不修改 `CONSTITUTION.md` 任何条款；不修改任何数值默认/阈值/停止条件（因此 `converge.governance-change/v1` 机器块不适用）；不改变收敛主循环内 M-11 预算门与 `orchest.py` 记账规则；不改变层级模式「子收敛之间不通信」（`SKILL.md` L519）与「子任务间无实时数据依赖」（L514）；不新增运行时脚本、新模式或 `refs/state-schema.md` 新字段。

## 2. 宪法级自检（CONSTITUTION §一）

- **Bitter Lesson 分层判别（三分判据）**：
  - **保留为硬前置（防呆/契约守卫，fail-closed）**：传话编排适用条件 1（**产物已收敛且方案已定稿**——唯一防止绕开主循环 `orchest.py` 与预算门的状态前提）与条件 2（**验收判据机械可核**——持续会话丧失反锚定后的补偿控制）均不随模型变强而减值，保持硬性不变。
  - **交还 Orchestrator 裁量（封顶型启发式参数，fail-open）**：仅将适用条件 3（**参与方 ≤ 2**）及落地阶段的**协作载体选择**（fresh-context `Spawn` / 传话编排 / 可选的宿主原生实时协同）交还 Orchestrator 判断侧。
- **Occam**：仅修改 3 个受保护文档（`SKILL.md`、`refs/orchestrator-guide.md`、`refs/state-schema.md`）并同步 1 个非受保护说明文档（`scripts/README.md`，不在 `CONSTITUTION.md` §三 保护清单内，本次同步以消除跨文档冲突）——共覆盖 4 个文件（7 个编辑点），不新增文件、不新增状态机或 schema 字段，复用**项目源计划文件**（如 `docs/plans/active/<slug>.md` 或对应已移入 `docs/plans/done/` 的源计划文件——与 `.converge/done/<slug>/` 完全隔离）末尾追加的「落地记录」小节与 `orchest.py checkpoint-paths` 产出的 `implementation_paths`（或降级汇总文件清单）；**`.converge/done/<slug>/` 下的全部已封存文件（含 `plan.md`、`retrospective.md`、`gate-ledger.jsonl` 等，均受 Archive Contract v1 `manifest.json` 哈希保护）均为只读，落地阶段绝不向其追加字节或重建 `active/<slug>/`**，不新增 `refs/state-schema.md` 字段。

## 3. 文件改动清单

| # | 文件 | 编辑点 | 改动摘要 |
|---|---|---|---|
| 1 | `SKILL.md` | `## 核心角色` 表之后、`### 模型分层` 之前 | 新增「实时协同与独立审计红线」单源段（功能判据与角色示例、禁止 Reviewer↔被审者 及 Reviewer↔Reviewer 共享板；独立审计红线全局适用于所有独立评审角色；宿主实时协同裁量权仅限收敛后 C-21，不适用于主循环与层级子收敛；明确可选宿主扩展与回退） |
| 2 | `SKILL.md` | `### Orchestrator 主循环` 步骤 `d3`（L252） | 补充引用 C-21(a) 与 `refs/orchestrator-guide.md` §落地执行编排，使 `d3` 与 C-21 一致 |
| 3 | `SKILL.md` | 责任清单 `C-21`（L379） | 给出 `C-21(a)/(b)/(c)/(d)` 逐字终态：明确落地载体三选一（默认 `Spawn`、可选宿主原生实时协同或传话编排）；明确 `C-21(b)` 宪法 #7 连同 `refs/framework-adapters.md` §A.4 不可用降级例外全载体适用；统一 `C-21(c)` 全三载体客观执行标识留痕与诚实证据边界（单次 `Spawn` 记 `instance_id` 佐证独立启动，手工传话记 `instance_id` 列表、宿主协同记会话/成员标识及协作方式；标识为启动/在场参与的客观留痕，不单独证明逐文件写入归属或 fresh 启动；统一记入**项目源计划文件**（如 `docs/plans/active/<slug>.md` 或对应已移入 `docs/plans/done/` 的源计划文件——与 `.converge/done/<slug>/` 完全隔离）末尾「落地记录」小节并配合 `orchest.py checkpoint-paths` 产出的 `implementation_paths`（或降级汇总文件清单）；**`.converge/done/<slug>/` 下的全部已封存文件（含 `plan.md`、`retrospective.md`、`gate-ledger.jsonl` 等，均受 Archive Contract v1 `manifest.json` 哈希保护）均为只读，落地阶段绝不向其追加字节或重建 `active/<slug>/`**）；并将 `C-21(d)` 核对改为指向 `refs/orchestrator-guide.md` §八「脚本化映射」单源指针 |
| 4 | `SKILL.md` | `### 传话编排（relay orchestration）`（L385–L398） | 保留条件 1、2 为硬前置（条件 1 统一为单一无歧义入口：该 slug 已完成终局 decision 并经 `finish` 归档至 `.converge/done/<slug>/`，与 `d2→finish→d3` 及 `guide` L390 一致），将条件 3 改为载体与规模裁量；明确可选用宿主原生实时协同替代手工传话，同时写明新路径上的宪法 #6 降级告知（含对结论可靠性的影响）、宪法 #7 不直改产物、以及振荡检测与归档后落盘边界（手工传话路径下因 C-21 落地发生在 `finish` 归档之后、`.converge/done/<slug>/` 全部文件含 `gate-ledger.jsonl` 已封存只读且不得重建 `active/<slug>/`，每次转发记录沿用 `refs/state-schema.md` §relay-ledger 格式单源追加于项目源计划文件「落地记录」节；振荡裁判输入仅为该「落地记录」节中的转发记录、输出仅为 Type O/R/F/S 的枚举判定、orchestrator 保持沉默不自行做语义判定，裁判 spawn 与判定结论同样记入源计划「落地记录」节并与落地执行方同享不回写已封存 `gate-ledger.jsonl` 的豁免；宿主实时协同路径无手工转发且不新增停止条件或计数阈值，由 Orchestrator 自主识别无效循环并中止/回退单次 `Spawn`） |
| 5 | `refs/orchestrator-guide.md` | `## 八、落地执行编排`（L388–L469） | 精确同步 9 个子项：流程（L394–L397，留痕改按 `§执行标识留痕（instance_id）`）、脚本化映射（L399，统一三载体执行标识、诚实证据边界、项目源计划文件末尾「落地记录」节配合 `implementation_paths`（或降级汇总文件清单）、`.converge/done/<slug>/` 全部已封存文件均只读且绝不重建 `active/<slug>/`，与 M 侧生成及降级单源规则）、显式不适用（L401，涵盖收敛后 C-21 落地阶段的执行方与手工传话振荡裁判——均不进收敛预算门且不回写已封存 `.converge/done/<slug>/gate-ledger.jsonl`，三命令仅适用于收敛循环内全部受门控角色派发（见 `scripts/budget_gate.py` `ROLE_CONSUMES` 及 Inner Loop Continue））、自主推进明线（L407）、硬约束（L413–L416，补齐宪法 #7 的 A.4 不可用降级例外指针，并将持续会话纪律改写为诚实的范围约束表述）、执行标识留痕（L418–L420，原标题 `### instance_id 留痕` → 新标题 `### 执行标识留痕（instance_id）`，统一全三载体标识、诚实证据边界、项目源计划文件「落地记录」节与 `.converge/done/<slug>/` 全部已封存文件只读边界）、清单项数核对（L422–L429，首句与第 2 条对齐 `§八`「脚本化映射」单源取数并用于交叉核验）、传话首句（L433）、边界自检记录首条（L467，对应改记源计划「落地记录」节转发记录，绝不回写已封存 `.converge/done/<slug>/`），消除与 `SKILL.md` 的跨文件矛盾（`SKILL.md` L356 既有「§执行阶段」旧锚点不在本次编辑范围内，本次新增与改写文本无悬空引用） |
| 6 | `scripts/README.md` | L97 | 同步落地执行说明为按 `SKILL.md` C-21 与 `refs/orchestrator-guide.md` §落地执行编排 选定载体，执行标识与 M 侧改动清单（优先由 `checkpoint-paths` 产出 `implementation_paths`，无统一 commit 边界时降级汇总并标注，详见 §落地执行编排「脚本化映射」）记入项目源计划文件「落地记录」节（绝不回写已封存 `.converge/done/` 文件），消除跨文档冲突（注：`scripts/README.md` 不在 `CONSTITUTION.md` §三 保护清单内） |
| 7 | `refs/state-schema.md` | `## relay-ledger` 导语（L173） | 同步转发记录落盘位置：因 C-21 落地发生在 `finish` 归档之后、`.converge/done/<slug>/` 全部文件已封存只读且不得重建 `active/<slug>/`，转发记录追加于项目源计划文件（`docs/plans/...`）的「落地记录」节（沿用下方字段集，append-only，不改写） |

## 4. 精确改动规格（逐字终态）

### 编辑点 1：`SKILL.md` — `## 核心角色` 表格后、`### 模型分层` 前新增

```markdown
> **独立审计红线与宿主原生实时协同能力（可选扩展）**：
> - **独立审计上下文隔离（硬红线）**：凡输出进入 verdict、blocking 判定、收敛裁决或独立验收的角色——功能判据为穷尽标准，例如 outer loop Reviewer、Inner Loop Reviewer、盲审复核 Reviewer、ultraverge 并行 Reviewer、Round 0 合同挑战 Reviewer、L2 gate Reviewer、收敛后设计审查 Reviewer、仲裁/振荡裁判——**必须**保持上下文隔离，既不得与被审者共享公开消息板或持续对话，并行 Reviewer 之间亦不得共享；审计会话与落地协同板生命周期分离。
> - **宿主原生实时协同能力（可选宿主扩展）**：核心角色表的『Executor = 全新上下文』约束作用于收敛主循环；落地执行阶段的持续会话/共享板参与方按 `§传话编排` 适用门与独立性降级声明执行。抽象能力层的 canonical 路径仍为 `Spawn` / `Continue` / `Identify`；本扩展**不是**第四个抽象能力，不入 `refs/framework-adapters.md` 适配层矩阵，宿主协作协议由宿主文档定义。仅在**收敛后落地执行阶段（C-21）**且满足 `§传话编排（relay orchestration）` 统一适用门时，Orchestrator 可按该节载体裁量规则选用该扩展；宿主不支持时自动回退至 `Spawn` / 手工传话，不触发能力缺失阻断。
> - **不适用范围**：本裁量权**不适用于收敛主循环内的角色派发**（仍严格走主循环与 M-11 预算门），亦**不减损层级模式「子收敛之间不通信」与「子任务间无实时数据依赖」的不变量**。实时协同中的并行互查属**独立性降级模式**下的协作建议，必须按宪法 #6 告知用户当前处于独立性降级模式**及其对结论可靠性的影响**，不得产出 verdict、不入 gate ingest、不可替代任何独立审计角色。
```

### 编辑点 2：`SKILL.md` — 主循环步骤 `d3`（替换原 L252）

```markdown
         d3. 落地执行（将方案改动清单写入目标文件）：**当原始指令含执行意图时**（机械明线：指令含执行动词「并执行 / 落地 / apply」等，见 §确认点分类）→ Orchestrator **默认自主推进**，不追加"现在要执行吗"check-in，按 `refs/orchestrator-guide.md` §落地执行编排 与 C-21 执行落地（默认使用 `refs/executor-prompt.md` Plan-Execution 模板 spawn executor，必要时按 C-21(a) 选用宿主原生实时协同或传话编排；落地执行不进收敛预算门与 Archive Contract，M 侧清单生成与降级规则以 `refs/orchestrator-guide.md` §八「脚本化映射」为单源，N vs M 比较由 Orchestrator 完成）。**指令不含执行意图时**：落地前仍需用户确认。全部宪法强制 gate（终止-b/c、预算软停/`*_exhausted`、`MODE_SWITCH_REQUIRED`、`FAIL_CLOSED`、`需重新设计`）不受此影响、逐字保留。
```

### 编辑点 3：`SKILL.md` — 责任清单 `C-21`（替换原 L379）

```markdown
  C-21. **后收敛执行编排** — 方案收敛后用户要求落地执行时：(a) 选用落地载体——默认为 fresh-context Spawn executor（`refs/executor-prompt.md` Plan-Execution 模板）；满足 `§传话编排` 统一适用门时按该节载体裁量规则选用宿主原生实时协同或手工传话；(b) **不得直接编辑文件**（无论采用何种载体，宪法 #7 在落地阶段均适用；仅当 Spawn 完全不可用时，按 `refs/framework-adapters.md` §A.4 优先触发降级为 `orchestrator_self` 执行，须在项目源计划文件末尾「落地记录」节如实标注 `source: orchestrator_self` 并向用户说明降级及对结论可靠性的影响，不得伪造独立执行标识）；(c) 将客观执行标识（单次 Spawn 记 executor `instance_id`，佐证独立执行方启动；手工传话记参与执行方 `instance_id` 列表；宿主原生实时协同记宿主协作会话标识、实际执行成员标识及所选协作方式；**诚实边界**：上述标识为启动/在场参与的客观留痕、非纯 self-report，但对复用/持续会话或宿主协同**不单独证明逐文件写入归属或 fresh 启动**；若触发 §A.4 `orchestrator_self` 降级，仅如实标注降级记录，不要求也不得伪造不存在的独立执行标识）统一记录于**项目源计划文件（如 `docs/plans/active/<slug>.md` 或对应已移入 `docs/plans/done/` 的源计划文件——与 `.converge/done/<slug>/` 完全隔离）末尾追加的「落地记录」小节（含协作载体、执行标识、以及 `scripts/orchest.py checkpoint-paths` 产出的 `implementation_paths` 或降级汇总文件清单）**，完全处于 Archive Contract 封存域之外；**`.converge/done/<slug>/` 下的全部已封存文件（含 `plan.md`、`retrospective.md`、`gate-ledger.jsonl` 等，均受 Archive Contract v1 `manifest.json` 哈希保护）均为只读，落地阶段绝不向其追加字节或重建 `active/<slug>/`**（亦不触发 reopen）；(d) 核对改动清单项数与实改文件数一致（M 侧清单生成与降级规则以 `refs/orchestrator-guide.md` §八「脚本化映射」为单源，N vs M 比较由 Orchestrator 完成）；(e) 落地后建议（非强制）`.meta/audit` plan-landing 子模式（条件触发、小落地豁免、ultraverge 不豁免——阈值与细节单源 `.meta/audit/README.md`）。职责要点；编排指引单源见 `refs/orchestrator-guide.md` §落地执行编排
```

### 编辑点 4：`SKILL.md` — `### 传话编排（relay orchestration）`（替换原 L385–L398）

```markdown
**适用门（持续会话 / 共享消息板落地的单一权威定义；本节不进入收敛主循环，进入主循环须按步骤 a0+a 过 gate）**：
1. **硬前置**：产物已收敛且方案已定稿（该 slug 已完成终局 decision 并经 finish 归档至 .converge/done/<slug>/）
2. **硬前置**：验收判据机械可核（测试退出码 / hook 返回码 / diff / 计数；强耦合落地场景最低形态为接口契约测试或 diff/计数校验）
3. **载体与规模裁量**（由 Orchestrator 按需决定）：手工传话默认参与方 ≤ 2；多 Executor 强耦合且宿主具备原生实时协同能力时，优先选用宿主原生能力替代手工传话，不支持则回退 `Spawn` 或手工传话。

**载荷与成本边界**：手工传话载荷必须为**文件引用**，**不得为消息全文**——消息载荷下两侧 agent 各自累积对方全部历史，输入 token 随轮次二次增长。改用宿主原生实时协同能力时，亦须以文件/提交引用为主、控制板面上下文膨胀。

**独立性降级声明**：无论经手工传话还是宿主原生实时协同，只要参与方为持续会话或共享消息板，converge 的反锚定机制（executor 纪律「打破过往同意惯性」/「打破上轮 reviewer 偏好锚定」、盲审复核、`past_commitment_anchoring` 巡查）即**不生效**。使用前 orchestrator **必须**按宪法 #6 告知用户当前处于独立性降级模式**及其对结论可靠性的影响**。

**角色边界**：传话编排与宿主原生实时协同中，orchestrator 的「纠偏」均限定为**指出偏差并要求执行方修正**，**不含直接修改产物**（宪法 #7 连同其 `refs/framework-adapters.md` §A.4 不可用降级例外在落地阶段同样适用，C-21(b) 已有明文）。除 Spawn 完全不可用按 `refs/framework-adapters.md` §A.4 降级为 `orchestrator_self` 并如实标注告知外，Orchestrator **不得直接修改**产物文件。

**振荡检测**：手工传话路径下，因 C-21 落地发生在 `finish` 归档之后、`.converge/done/<slug>/` 全部文件（含 `gate-ledger.jsonl`）均已封存只读且不得重建 `active/<slug>/`，orchestrator 对每次转发在项目源计划文件（`docs/plans/...`）的「落地记录」节追加一条转发记录（字段格式仍沿用 `refs/state-schema.md` §relay-ledger 单源）。每 `relay_oscillation_interval` 轮（默认 3），spawn 一个一次性「振荡裁判」agent——**输入仅为该「落地记录」节中的转发记录**，**输出仅为 Type O/R/F/S 的枚举判定**。orchestrator 只负责 spawn 与转发判定结果，**保持沉默**——不自行做语义判定；裁判 spawn 与判定结论同样记入源计划「落地记录」节，与落地执行方同享不回写已封存 `gate-ledger.jsonl` 的豁免（不再尝试经 `orchest.py` 写入已封存账本）。宿主原生实时协同路径下无手工转发，**不新增停止条件或计数阈值**；由 Orchestrator 依据宿主板面与执行日志自主识别反复推翻或往返翻转等无效循环，及时中止协同或回退单次 `Spawn`。

> 操作细节（默认不发言、仅偏差介入的转发纪律与包裹格式）见 `refs/orchestrator-guide.md` §八；relay-ledger 记录格式以 `refs/state-schema.md` §relay-ledger 为**唯一单源**。
```

### 编辑点 5：`refs/orchestrator-guide.md` — `## 八、落地执行编排`（L388–L469）

1. 替换 `### 流程`（L394–L397）：
````markdown
```
用户要求落地 → 读取方案中的"文件改动清单"表 → 按 C-21(a) 与 `SKILL.md` §传话编排 统一适用门启动执行方（默认 Spawn executor）
→ 等待执行完成 → 记录客观执行标识（按 §执行标识留痕（instance_id））→ 核对清单项数 vs 实改文件数 → 报告用户
```
````
2. 替换 `### 硬约束`（L413–L416）：
```markdown
### 硬约束

- **除 Spawn 完全不可用触发 `refs/framework-adapters.md` §A.4 降级（在项目源计划文件「落地记录」节标注 `source: orchestrator_self` 并向用户说明降级及影响）外，必须由独立执行方落地，Orchestrator 不得兼任 executor 或直接编辑产物**（宪法 #7 在单次 Spawn、传话编排与宿主原生实时协同下均适用）
- 默认路径下 executor 使用 `refs/executor-prompt.md` Plan-Execution 模式（fresh-context spawn，仅读方案文件）；选用宿主原生实时协同或传话编排时，须满足 `SKILL.md` §传话编排 统一适用门、遵守独立性降级声明（宪法 #6），并遵守范围约束（任务消息自足、以方案文件为唯一需求输入、禁止读取或转述审计历史；持续会话不主张 fresh 上下文）。
```
3. 替换原标题 `### instance_id 留痕` 为 `### 执行标识留痕（instance_id）`（L418–L420）：
```markdown
### 执行标识留痕（instance_id）

启动落地执行后，将客观执行标识（单次 Spawn 记 executor `instance_id`，佐证独立执行方启动；手工传话记参与执行方 `instance_id` 列表；宿主原生实时协同记宿主协作会话标识、实际执行成员标识及所选协作方式）统一记录于**项目源计划文件（如 `docs/plans/active/<slug>.md` 或对应已移入 `docs/plans/done/` 的源计划文件——与 `.converge/done/<slug>/` 完全隔离）末尾追加的「落地记录」小节（含协作载体、执行标识、以及 `scripts/orchest.py checkpoint-paths` 产出的 `implementation_paths` 或降级汇总文件清单）**，完全处于 Archive Contract 封存域之外；**`.converge/done/<slug>/` 下的全部已封存文件（含 `plan.md`、`retrospective.md`、`gate-ledger.jsonl` 等，均受 Archive Contract v1 `manifest.json` 哈希保护）均为只读，落地阶段绝不向其追加字节或重建 `active/<slug>/`**（亦不触发 reopen）。**诚实边界**：上述标识为启动/在场参与的客观留痕（非纯 self-report），但对复用/持续会话或宿主协同**不单独证明逐文件写入归属或 fresh 启动**；若触发 §A.4 `orchestrator_self` 降级，仅如实标注降级记录，不要求也不得伪造不存在的独立执行标识。
```
4. 替换 `### 清单项数核对`（L422–L429）首句与第 2 条：
   - 首句：``执行方完成后，Orchestrator 交叉核对改动清单与实际修改文件数：``
   - 第 2 条：``2. 按 `§八`「脚本化映射」单源规则获取 M 侧已修改文件数（优先由 `scripts/orchest.py checkpoint-paths` 机械生成，降级时汇总全部执行方报告的实改文件集并显式标注；执行方报告同时用于交叉核验）``
5. 替换 `### 传话编排（relay orchestration）` 首句（L433）：将「适用条件见 SKILL.md Orchestrator 责任清单」改写为「适用条件、宿主原生实时协同替代边界与降级要求见 `SKILL.md` §传话编排（relay orchestration）」。
6. 替换原 L399 `**脚本化映射...**` 段，逐字终态为：
```markdown
**脚本化映射（落地执行方不进收敛预算门与 Archive Contract，设计裁决见 `SKILL.md` C-21 与 M-11）**：落地执行走宿主原生（未过 gate 的）通道，载体按 C-21(a) 与 `SKILL.md` §传话编排 统一适用门选定；客观执行标识（单次 Spawn 记 executor `instance_id`，佐证独立执行方启动；手工传话记参与执行方 `instance_id` 列表；宿主原生实时协同记宿主协作会话标识、实际执行成员标识及所选协作方式；**诚实边界**：上述标识为启动/在场参与的客观留痕、非纯 self-report，但对复用/持续会话或宿主协同**不单独证明逐文件写入归属或 fresh 启动**；若触发 §A.4 `orchestrator_self` 降级，仅如实标注降级记录，不要求也不得伪造不存在的独立执行标识）统一记录于**项目源计划文件（如 `docs/plans/active/<slug>.md` 或对应已移入 `docs/plans/done/` 的源计划文件——与 `.converge/done/<slug>/` 完全隔离）末尾追加的「落地记录」小节（含协作载体、执行标识、以及 `scripts/orchest.py checkpoint-paths` 产出的 `implementation_paths` 或降级汇总文件清单）**，完全处于 Archive Contract 封存域之外；**`.converge/done/<slug>/` 下的全部已封存文件（含 `plan.md`、`retrospective.md`、`gate-ledger.jsonl` 等，均受 Archive Contract v1 `manifest.json` 哈希保护）均为只读，落地阶段绝不向其追加字节或重建 `active/<slug>/`**（亦不触发 reopen）；`scripts/orchest.py checkpoint-paths` 仅负责机械生成 M 侧已改文件清单（同时产出 `implementation_paths`；前置条件 = 落地改动已 commit，无论是单 Executor 还是多 Executor），凡尚未 commit 或无统一 commit 边界导致无法机械生成时，一律降级为 LLM 汇总全部执行方实改文件集并显式标注；N vs M 比较始终由 Orchestrator 完成。
```
7. 替换原 L401 `**显式不适用**` 段，逐字终态为：
```markdown
**显式不适用（收敛后的 C-21 落地阶段）**：reserve-round / register-round / cancel-round（收敛后落地阶段的执行方与手工传话振荡裁判均不进收敛预算门，亦不回写已封存的 `.converge/done/<slug>/gate-ledger.jsonl`；spawn 生命周期三命令仅适用于**收敛循环内**全部受门控角色派发（见 `scripts/budget_gate.py` `ROLE_CONSUMES` 及 Inner Loop Continue））、record-verdict（落地阶段无 verdict，产物亦非 round-N.md/blind-recheck-N.md）、finish（落地发生在归档之后，无归档动作）。
```
8. 替换原 L407 执行意图机械明线首条，逐字终态为：
```markdown
- **执行意图机械明线**：原始指令含执行动词（如「并执行 / 落地 / apply」等）→ 收敛后按 C-21(a) **自主推进落地**，**不**追加"现在要执行吗"check-in。
```
9. 替换原 L467 边界自检记录首条，逐字终态为：
```markdown
- 在项目源计划文件「落地记录」节的转发记录中（如已记录转发条目）标注 `boundary_violation_pending`（绝不回写已封存的 `.converge/done/<slug>/`）
```

### 编辑点 6：`scripts/README.md` — L97（替换原 L97）

```markdown
落地执行（收敛完成后）**不进**上述循环：执行方按 `SKILL.md` C-21 与 `refs/orchestrator-guide.md` §落地执行编排 选定载体，执行标识与 M 侧改动清单（优先由 `checkpoint-paths` 产出 `implementation_paths`，无统一 commit 边界时降级汇总并标注，详见 §落地执行编排「脚本化映射」）记入项目源计划文件的「落地记录」节（绝不回写已封存的 `.converge/done/` 文件）——操作权威与映射表见 `refs/orchestrator-guide.md` §落地执行编排。
```

### 编辑点 7：`refs/state-schema.md` — `## relay-ledger` 导语（替换原 L173）

```markdown
> 传话编排（relay orchestration）的**转发事件日志**。因 C-21 落地发生在 `finish` 归档之后、`.converge/done/<slug>/` 全部文件已封存只读且不得重建 `active/<slug>/`，转发记录追加于项目源计划文件（`docs/plans/...`）的「落地记录」节（沿用下方字段集，append-only，不改写）。
```

## 5. 验收与验证标准

1. **宪法条款逐项核对**：
   - `CONSTITUTION.md` §一（Bitter Lesson 分层）：条件 1、2 保留硬前置，仅条件 3 与落地载体选择交还判断侧；
   - `CONSTITUTION.md` §二 #6（降级告知）在实时协同路径上显式收紧/补全，#7（Orchestrator 不直改产物）全载体保留；其余 #1–#5 不受影响。
2. **跨文件逐条核对**：4 个目标文件共 7 个编辑点——`SKILL.md`（核心角色、`d3`、C-21、传话编排）、`refs/orchestrator-guide.md` §八 9 个子项（流程 L394–L397、脚本化映射 L399、显式不适用 L401、自主推进明线 L407、硬约束 L413–L416、执行标识留痕 L418–L420、清单项数核对 L422–L429、传话首句 L433、边界自检 L467）、`scripts/README.md` L97 与 `refs/state-schema.md` L173（`## relay-ledger` 导语）——全部一致：全三载体客观执行标识口径、诚实证据边界（启动/在场参与的客观留痕，对复用/持续会话或宿主协同不单独证明逐文件写入归属或 fresh 启动）、唯一落盘位置（项目源计划文件末尾「落地记录」节配合 `scripts/orchest.py checkpoint-paths` 产出的 `implementation_paths` 或降级汇总文件清单，处于 Archive Contract 封存域之外，`.converge/done/<slug>/` 全部已封存文件含 `plan.md`、`retrospective.md`、`gate-ledger.jsonl` 均只读且绝不追加字节或重建 `active/<slug>/`）在 C-21(c)/L399/L418–L420/scripts/README.md L97 四处完全一致（其中 `scripts/README.md` L97 同步补入 `checkpoint-paths` 优先 + 无统一 commit 边界时降级汇总并标注的单源指针）；C-21 落地统一在 `finish` 归档至 `.converge/done/<slug>/` 之后执行（与 `SKILL.md` `d2→finish→d3`、`§传话编排` 条件 1 及 `guide` L390 一致）；手工传话转发记录（沿用 `refs/state-schema.md` §relay-ledger 格式单源）、振荡裁判输入（仅取该节转发记录）、裁判 spawn 记录与结论、以及 `boundary_violation_pending` 边界自检记录（`guide` L467）统一记入项目源计划文件「落地记录」节，与落地执行方同享不进收敛预算门、不回写已封存 `.converge/done/<slug>/gate-ledger.jsonl` 且不重建 `active/<slug>/` 的豁免（`SKILL.md` `§传话编排`、`guide` L401 与 `guide` L467 完全一致），且 `refs/state-schema.md` L173 `## relay-ledger` 导语已同步改为追加至项目源计划文件「落地记录」节（不再引用 `active/<slug>/`）；宪法 #7 连同其 `refs/framework-adapters.md` §A.4 不可用降级例外在 C-21(b) 与硬约束 L415 一致；硬约束 L416 持续会话纪律表述为诚实的范围约束（不主张 fresh 上下文）；显式不适用 L401 界定为涵盖收敛后 C-21 落地阶段的执行方与手工传话振荡裁判、三命令仅适用于收敛循环内全部受门控角色派发（见 `scripts/budget_gate.py` `ROLE_CONSUMES` 及 Inner Loop Continue）；执行标识留痕 L418–L420 明确由原标题 `### instance_id 留痕` 替换为 `### 执行标识留痕（instance_id）`；手工传话振荡裁判核心纪律（输入仅为该「落地记录」节中的转发记录、输出仅为 Type O/R/F/S 的枚举判定、orchestrator 保持沉默不自行做语义判定）完整保留；清单项数核对 L424/L427 与 L399 单源取数一致；本次新增与改写文本无悬空引用与规范冲突（注：`SKILL.md` L356 既有「§执行阶段」旧锚点不在本次编辑范围内）。
3. **确定性测试**：本仓既有测试套件全绿：`python -X utf8 -m pytest tests/ -q`、`git diff --check`。
4. **治理程序完备**：完成 `ultraverge`（≥3 独立 Reviewer 初评 → 修复 → fresh Reviewer 重审可执行 → 强制收敛后设计审查 → `orchest.py finish` 归档），提交时遵循仓内 pre-commit 约定并由人工确认。
5. **preflight 自检**：本次无数值默认/阈值/停止条件变更，`converge.governance-change/v1` 机器块与 `task-envelope` 要求不触发（理由引 §1）。
