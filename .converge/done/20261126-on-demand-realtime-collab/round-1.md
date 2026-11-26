---
round: 1
reviewer_backend: opencode
generated_at: 2026-11-25T17:12:52.085296+00:00
invocation_id: 347a5995-ee54-4bb9-8168-4bf3574f090c
reservation_id: 7a5ae9fc0c98
reviewer_instance_id: ses_dec4dd23effeNLAxJx80LT2gnr
verdict: 阻断需修复
---
# Round 1 独立审查报告 — 20261126-on-demand-realtime-collab

审查者身份：fresh-context outer-loop Reviewer（deepseek-v4.1-flash-1017）。只读审查，未修改任何仓库文件。

## Reviewer 完整输出

### 0. 审查边界与输入

- 按任务给定的输入白名单读取 6 份材料（见文末 `reads`）。**未读取** `uv-init-1.md` / `uv-init-2.md` / `uv-init-3.md` 原文（白名单未含，且属"其他位置"）；因此初评 3 路的原始阻断项，本轮以 `attempts.md` 归并后的 **6 项修复** 为核验基准（与任务格式要求第 4 条一致）。
  - 推论性风险（供 Orchestrator 判断，非本轮阻断）：若初评原文存在未被 6 项修复覆盖的阻断，本轮无法发现。建议 Orchestrator 确认 `attempts.md` 的 6 项与 3 份初评的 blocking 集为满射。
- 为核对跨文件引用锚点与行号，做过一次跨仓定向 grep（模式：`执行阶段|子收敛之间不通信|子任务间无实时数据依赖|实时协同|消息板`），命中含 `refs/decomposition-protocol.md` 等文件的行级片段，未读其全文。
- 除输出文件外未创建/编辑/删除任何文件，未执行任何改变仓库状态的命令。

### 1. verdict

**阻断需修复**

6 项修复全部在计划本体中实质落地（无 `still_blocking`），宪法条款无违规；但新文本在**宿主原生实时协同的适用门（gate set）**上形成三处互相不可归约的表述，使计划自陈的硬前置之一（条件 2「验收判据机械可核」）是否约束该路径无法判定。该缺口落在初评阻断 #1 试图关闭的同一风险面（降级路径的补偿控制），属计划文本缺陷，须回写计划本体。

### 2. 对 attempts.md 6 项修复的逐项核验

| # | 修复项（attempts.md） | 计划本体落点 | 结论 | 核验说明 |
|---|---|---|---|---|
| 1 | Bitter Lesson 分层：条件 1、2 保留硬前置，仅条件 3 与载体选择交还裁量 | §2 三分判据；§4 编辑点 4 适用条件 1/2/3 | **resolved** | 条件 1、2 均标「硬前置」，条件 3 改为「规模参考（由 Orchestrator 按需裁量）」；§2 未修改任何数值阈值。附注：条件 1 的第二 disjunct（「或方案已定稿进入 C-21 落地」）机械性弱于声明，见 S1。 |
| 2 | 独立审计红线按功能判据覆盖全部 6 类独立评审角色，禁止 Reviewer↔被审者、Reviewer↔Reviewer 共享板 | §4 编辑点 1 第 1 条 | **resolved** | 功能判据（verdict / blocking 判定 / 收敛裁决 / 独立验收）+ 6 类角色枚举（outer loop、盲审、ultraverge 并行、Round 0 合同挑战、L2 gate、设计审查）齐备；「审计会话与落地协同板生命周期分离」补上了生命周期维度。枚举与 `refs/reviewer-discipline.md` 的 Mode 值集（main-loop / blind-recheck / gate-review）及设计审查、合同谈判协议无冲突。 |
| 3 | 明确不适用范围（仅 C-21，不适用主循环，不减损层级模式不变量） | §4 编辑点 1 第 2、3 条；§2 非变更声明 | **resolved** | 「不适用于收敛主循环内的角色派发（仍严格走主循环与 M-11 预算门）」+「不减损『子收敛之间不通信』（SKILL.md L519）与『子任务间无实时数据依赖』（L514）」逐字对应现存不变量，行号核对属实。 |
| 4 | 登记为可选宿主扩展，canonical 仍为 Spawn/Continue/Identify，不支持时回退 | §4 编辑点 1 第 2 条；§1 目标 2 | **resolved** | 「canonical 路径仍为 `Spawn` / `Continue` / `Identify`」「宿主不支持时自动回退至 `Spawn` / 传话编排，不触发能力缺失阻断」均在。附注：登记位置只在 SKILL.md 核心角色段，未触及抽象能力层表与 `refs/framework-adapters.md`，取舍可接受但建议补一句定位声明，见 S4。 |
| 5 | 跨文件同步纳入 target_files：`d3`、C-21(a)(c)、guide §八 全节；保留执行标识留痕与多 Executor 文件集汇总 | §3 表；§4 编辑点 2/3/5；frontmatter `target_files` | **resolved** | frontmatter 仅含 `SKILL.md`、`refs/orchestrator-guide.md`，与实际改动面一致；编辑点 2/3/5 的逐字终态均已给出，多 Executor 场景「汇总全部成员实改文件集」在 C-21(d) 与 guide 清单核对第 2 条双向对齐。附注：同一节内留痕位置仍有两说，见 S2；「§执行阶段」悬空锚点见 S7。 |
| 6 | 补齐新路径约束：载荷成本边界、宪法 #6 降级声明、宪法 #7 不直改产物、振荡检测归属 | §4 编辑点 4 载荷/独立性/角色边界/振荡检测；编辑点 5 硬约束 | **resolved** | 四项约束均有逐字文本：文件引用载荷 + 板面膨胀控制；#6 强制告知且「并行互查属独立性降级模式…不得产出 verdict、不入 gate ingest」；#7 在 C-21(b) 与新硬约束「无论采用单次 Spawn、传话编排还是宿主原生实时协同」全载体保留；振荡检测按手工/宿主两路径分流。附注：宿主路径的振荡检测只有归属、无可执行观察定义，见 S3。 |

**汇总：6/6 resolved，0 still_blocking。** 下述阻断项 B1 不是上述 6 项的未解决部分，而是修订文本**新引入**的跨段不一致。

### 3. blocking_issues

```yaml
blocking_issues:
  - id: 1
    description: |
      宿主原生实时协同的适用门（gate set）在计划中被写成三套互不归约的表述，导致「条件 2（验收判据机械可核）是否约束该路径」无法判定；同时载体偏好（强耦合场景选宿主协同还是传话编排）在两处结论相反。
      证据一（仅 C-21 定位，无附加门）：编辑点 1 第 2 条——「仅在收敛后落地执行阶段（C-21）且宿主提供原生实时协同（如共享消息板）时，Orchestrator 可按需选用该扩展替代单次 Spawn 或手工传话」。
      证据二（附加「多 Executor 强耦合」条件，仍未提条件 2）：C-21(a)——「默认为 fresh-context Spawn executor…，多 Executor 强耦合落地时可选用宿主原生实时协同能力或传话编排」。
      证据三（作为传话编排的替代实现，隐含继承条件 1、2，且偏好与证据二相反）：传话编排条件 3——「默认参与方 ≤ 2；多 Executor 强耦合且宿主具备原生实时协同能力时，可直接选用宿主能力替代手工传话」。
      证据四（只挂宪法 #6，不挂条件 2）：guide §八 新硬约束第 2 条——「选用宿主原生实时协同或传话编排时，须遵守 SKILL.md §核心角色 与 §传话编排 中的独立性降级声明（宪法 #6）」。
      影响：计划 §2 自陈「条件 2（验收判据机械可核——持续会话丧失反锚定后的补偿控制）…保持硬性不变」。若按证据一/二/四读法，实施者可在无机械验收判据的强耦合落地中启用降级协同——这正是初评阻断 #1 要关闭的「降级路径失去补偿控制」风险面。此外，条件 2 与该路径的激励场景存在张力：计划自述选用理由之一是「并行 Executor 间频繁对齐接口」（语义耦合），恰是机械验收判据最难给出的一类任务；不裁决「条件 2 如何适用于此路径」，实施时只能各自解读。
      修复要求：指定单一权威定义（建议落在编辑点 1 第 2 条或传话编排条件 3），写明二者之一并让其余两处改为指针——(i) 宿主路径是 C-21(a) 第三载体，且在参与方为持续会话/共享板时必须同时满足条件 1、2（并说明强耦合场景下「机械可核」的最低形态，如 diff/计数/接口契约测试）；或 (ii) 明文豁免条件 2，并给出替代补偿控制（如落地后由 fresh Reviewer 独立复验 + `checkpoint-paths` 机械核对 N/M）。同时统一载体偏好表述（强耦合场景的默认建议），消除证据二与证据三的相反指向。
    attribution: plan_defect
    severity: structural
    plan_amendment_required: true
    location: "§4 编辑点 1（第 2 条） / 编辑点 3（C-21(a)） / 编辑点 4（条件 3） / 编辑点 5（硬约束第 2 条）"
    rubric_gap: false
```

### 4. suggestion_issues

```yaml
suggestion_issues:
  - id: S1
    description: |
      条件 1 的第二 disjunct「或方案已定稿进入 C-21 落地」缺机械判据，与计划 §3 表第 4 行自述的「含机械核验指向」及「硬前置」定性不符，也与 guide §八 首句「当方案已收敛（retrospective 已写入 done/）」的单一定义并存。
      **不构成实际绕过**：C-21 在 SKILL.md 中的定义本身以「方案收敛后」为前提，因此该 disjunct 语义上被 C-21 蕴含，属冗余表述而非独立门。但「已定稿」由 LLM 判定，会给后续争辩留空间。
      建议：删除第二 disjunct，或绑定客观标记（terminal decision id / plan frontmatter status + 当轮 C-21 执行授权记录）。
    severity: implementation
  - id: S2
    description: |
      guide §八 内执行标识留痕位置自相矛盾，且计划未消解：未改动的 L399 写「`instance_id` 记 plan frontmatter implementation 条目」，而计划编辑点 5 第 3 项改写后的 §执行标识留痕写「记录到 `retrospective.md` 的落地执行条目中」；C-21(c) 又写「记录至 retrospective/落地日志」。计划 §5 验收第 2 条声称「5 个编辑点全部一致，无悬空引用与规范冲突」，此条使该声称不成立。
      建议：本次编辑中择一为权威（或明文「两处均记，以 retrospective 为审计权威、frontmatter 为便捷镜像」），否则实施者按不同段落会写到不同位置，后续审计核对口径不一。
    severity: implementation
  - id: S3
    description: |
      宿主实时协同路径的振荡检测只有归属声明：「振荡/循环检测回归全局 Type O/R/F/S 职责（以宿主板面/执行日志为观察依据）」，缺少观察者、轮次/触发计数口径与触发后动作。落地阶段没有 round 结构，Type R（与上轮阻断同源）、Type S（同一 reviewer 反转自身判断）缺乏轮次参照，按现有定义不可执行。
      建议：给出最小可执行定义（谁观察、以 relay 之外的什么为本、阈值、触发后动作），或明确落地阶段只保留 Type O 的等价形式（同一接口/文件被反复推翻 ≥N 次即停），其余类型标注「不适用于落地阶段」。
    severity: implementation
  - id: S4
    description: |
      新路径未在抽象能力层表与适配层登记：SKILL.md §抽象能力层 仍声明「三个原子能力」，`refs/framework-adapters.md` 无该扩展的适配/降级（§A.4）挂接点。计划以免触碰治理文件换取 Occam 合规，属可接受取舍。
      建议：在编辑点 1 第 2 条补一句定位声明——「该扩展不是第四个抽象能力，不入适配层矩阵；宿主协作协议由宿主文档定义，落地回退路径见 guide §八」，避免后续实现按「能力层」解读并倒推修改 framework-adapters。
    severity: structural
  - id: S5
    description: |
      非默认载体的执行方 prompt/纪律未定义：编辑点 5 硬约束只规定「默认路径下 executor 使用 `refs/executor-prompt.md` Plan-Execution 模式（fresh-context spawn，仅读方案文件）」，而 Plan-Execution 模板是单发 fresh-context 模板；多 Executor 实时协同场景下 prompt 应遵守什么纪律（自足 prompt、仅读方案文件、不读审计历史）未指定。
      建议：加一句「非默认载体沿用 Plan-Execution 的等价纪律（自足 prompt、仅读方案文件），宿主协作协议由宿主文档定义」，不新增模板文件。
    severity: structural
  - id: S6
    description: |
      行号与范围精度：计划 §3 表第 5 行与 §4 编辑点 5 写 `## 八、落地执行编排`（L392–L434），实际标题在 L388、该节延伸至 L469（下一个二级标题「九」在 L472）；§8 的开头段（L390–L401）与「自主推进判据」段不在声明范围内。各子节替换范围（394–397 / 413–416 / 418–420 / 422–429 / 433）经核对准确。
      建议：把节范围校正为 L388–L469，避免实施时按「434」为界漏改 relay 小节尾部（L431–L469）。
    severity: implementation
  - id: S7
    description: |
      「§执行阶段」为悬空引用，非本计划引入但会被 §5 验收第 2 条「无悬空引用」核到：SKILL.md M-11（L356）写「落地执行 spawn 豁免（设计裁决，见 §执行阶段/§落地执行编排）」，guide L399 写「设计裁决见 SKILL.md §执行阶段」，而 SKILL.md 无 `§执行阶段` 标题（相关定义实际在 C-21 与 guide §八）。
      建议：既然本次已改 C-21 与 guide §八，顺带把两处锚点改为 `C-21` 或 `refs/orchestrator-guide.md §八`；或把此项显式排除在验收声称之外。
    severity: implementation
  - id: S8
    description: |
      治理 preflight 判定未留痕：计划属治理文档变更，§1 非变更声明给出「不含 `converge.governance-change/v1` 机器块」的理由（不改数值默认/阈值/停止条件），推理成立；但 §5 验收未记录该判定与 preflight 结果（含 `task_tier`/task-envelope 是否受治理计划默认要求约束的解释）。
      建议：在 §5 增加一条「preflight 自检：governance 机器块不适用（理由引 §1），task-envelope 要求随之不触发」，使后续审计不必重新推导。
    severity: implementation
```

### 5. 宪法与跨文件核对摘要

| 核对项 | 结论 |
|---|---|
| 宪法 §一 Bitter Lesson 三分判据 | 通过。①机制不执行任务（只选载体）；②不收窄解空间（逃生舱 = Spawn / 传话 / 回退，均真实可用）；③条件 1、2 对违约 fail-closed，条件 3 与载体选择 fail-open。 |
| 宪法 §一 Occam | 通过。2 个文件、5 个编辑点、0 新增文件 / 模式 / schema 字段；复用现有 retrospective 落地条目与 `checkpoint-paths`。 |
| 宪法 §二 #6（降级告知） | 通过且收紧：两条降级路径（手工传话 / 宿主共享板）均强制告知，并声明「不含反锚定机制」。 |
| 宪法 §二 #7（不直改产物） | 通过：C-21(b)、编辑点 4 角色边界、编辑点 5 硬约束第 1 条三处覆盖全部载体，无「简单任务例外」。 |
| 宪法 §二 #1–#5 | 不受影响：未触碰终止-b/c、预算软停、`budget_extension`、历史 entry 只追加规则。 |
| 宪法 §三 治理清单 / §四 程序 | 通过：改动面全部落在清单内文件（SKILL.md、orchestrator-guide.md），走 ultraverge 符合程序；未触碰宪法本体。 |
| 数值默认与停止条件 | 未改动：`relay_oscillation_interval` 默认 3 保留，`total_safety` 记账语义保留，故机器块不适用的判定成立（S8 仅要求留痕）。 |
| 层级模式不变量 | 未减损：L514 / L519 引用属实，新段明文排除层级子收敛。 |
| 主循环 / M-11 | 未被放宽：新裁量权明文不适用于主循环角色派发；落地 spawn 豁免为既有设计。 |
| 跨文件一致性（5 个编辑点） | 4/5 完全一致（`d3` ↔ C-21(a) ↔ guide 流程；C-21(b) ↔ guide 硬约束；C-21(c) ↔ guide 留痕；C-21(d) ↔ guide 清单核对），载体选择与适用门一处不一致 → B1。另有同节内留痕位置两说（S2）。 |

### 6. 结论

- 初评 3 路的核心关切（Bitter Lesson 分层、审计红线覆盖面、适用范围、框架无关回退、跨文件同步、新路径约束）均已在计划本体中实质落地，无 `still_blocking`。
- 计划整体方向可执行，宪法自检成立；**唯一阻断**是新引入的「宿主实时协同适用门」不一致（B1），属一处可定点修复的文本缺陷，修复面很小（选定单一权威表述 + 两处改指针 + 统一载体偏好）。
- 建议下一轮以 fresh Reviewer 对**修复后的最终字节**复核 B1 与 S1/S2（其余 suggestion 可在落地实施时处置，不阻断收敛）。

### reads

- `<user-home>\Documents\GitHub\converge-skill\docs\plans\active\20261126-on-demand-realtime-collab.md`（全文，1–114）
- `<user-home>\Documents\GitHub\converge-skill\.converge\active\20261126-on-demand-realtime-collab\attempts.md`（全文）
- `<user-home>\Documents\GitHub\converge-skill\CONSTITUTION.md`（全文，1–96）
- `<user-home>\Documents\GitHub\converge-skill\SKILL.md`（全文，1–547）
- `<user-home>\Documents\GitHub\converge-skill\refs\orchestrator-guide.md`（§七末–§九初，L340–519，覆盖 §八 全文）
- `<user-home>\Documents\GitHub\converge-skill\refs\reviewer-discipline.md`（全文，1–300）
- 辅助（非白名单内容读取）：一次跨仓定向 grep（命中 `refs/decomposition-protocol.md`、`docs/plans/done/20260612-*` 等的行级片段，未读全文）
- 未读取：`.converge/active/20261126-on-demand-realtime-collab/uv-init-1.md`、`uv-init-2.md`、`uv-init-3.md`

## Orchestrator 处理记录

(pending)