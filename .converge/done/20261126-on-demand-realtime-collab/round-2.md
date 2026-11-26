---
round: 2
reviewer_backend: opencode
generated_at: 2026-11-25T17:18:39.827420+00:00
invocation_id: 9badb5b2-c700-4a2f-bb81-1ca0ced9fa74
reservation_id: 27f2a1a537d1
reviewer_instance_id: ses_dec4884e1ffe6M4JxmAh1sWYfm
verdict: 阻断需修复
---
# (skeleton)

## Reviewer 完整输出

# Round 2 独立复审报告（outer loop，fresh context）

## 0. 审查边界与方法

- 只读审查：本报告写入前未修改任何仓库文件，未运行任何改变仓库状态的命令。
- 输入按指定顺序读取：计划文件、attempts.md、CONSTITUTION.md、SKILL.md、refs/orchestrator-guide.md、refs/reviewer-discipline.md；另读取本文件骨架以保留 frontmatter。
- **边界声明（影响结论适用范围）**：按审查指令「其他位置禁读」，未读取 `round-1.md`、`uv-init-*.md`、`refs/state-schema.md`、`refs/framework-adapters.md`、`scripts/README.md` 等。因此：① Round 1 的 B1/S1–S8 原文以 `attempts.md` 第 17–24 行的摘要为唯一依据复述；② `refs/state-schema.md §relay-ledger` 等外部引用是否存在悬空，本轮**未核验**，不作为本轮阻断依据，仅在第 5 节末尾记为残余风险。

## 1. 结论摘要

`verdict: 阻断需修复`

- **B1（Round 1 唯一阻断，持续会话/宿主原生实时协同适用门收口到 `SKILL.md §传话编排` 单一权威 + 载体偏好统一）：已解决（resolved）。** 四处表述已全部改为「满足 §传话编排 统一适用门」的指针 + 一致的「强耦合多 Executor 优先宿主原生、否则回退 Spawn/手工传话」偏好。
- **S1 / S3 / S4 / S5 / S6 / S8：resolved。**
- **S2（统一 `retrospective.md` 为执行标识审计权威、frontmatter 为镜像）：未彻底解决（still_blocking）** — `refs/orchestrator-guide.md` §八的「脚本化映射」段（L396–L399）仍写着「`instance_id` 记 plan frontmatter implementation 条目」，且该段未纳入编辑点 5 的替换清单，与本轮新写入的「retrospective 为审计权威、frontmatter 仅镜像」直接冲突。此即本轮唯一阻断 **B2**。
- 本轮**未发现**宪法违规；Bitter Lesson 分层、Occam、宪法 #6/#7、层级模式不变量均与改动自洽（详见第 4 节）。

## 2. blocking_issues

### B2 — `refs/orchestrator-guide.md` §八 的「脚本化映射」段未纳入同步，执行标识出现第二个权威位置（S2 残留）

- **attribution**: `plan_defect`
- **severity**: `structural`（同一事实的双权威落点，与 B1 同类缺陷的缩小版）
- **plan_amendment_required**: `true`
- **location**: `docs/plans/active/20261126-on-demand-realtime-collab.md` §3 表第 5 行 / §4 编辑点 5；`refs/orchestrator-guide.md` L396–L399；`SKILL.md` C-21(c)（计划 §4 编辑点 3）

**证据（逐字引用）**

现行 `refs/orchestrator-guide.md` L399：

> **脚本化映射（落地执行 spawn 不进收敛预算门与 Archive Contract，设计裁决见 SKILL.md §执行阶段）**：落地 spawn 走宿主原生 Spawn；`instance_id` 记 plan frontmatter implementation 条目；N vs M 核对经 `scripts/orchest.py checkpoint-paths`（README 见 `scripts/README.md` ⑥；前置条件 = executor 落地改动先 commit，无 commit 则 M 侧无法机械生成，降级为 LLM 人工核对并标注）。

计划 §4 编辑点 3（新 C-21(c)）：

> 将客观执行标识（executor `instance_id`，或宿主实时协同的会话/成员标识与协作方式）记录至 `retrospective.md` 落地执行条目（审计权威；plan frontmatter `implementation` 条目可作镜像）

计划 §4 编辑点 5（guide §八 L418–L420 新文本）：

> 记录到 `retrospective.md` 的落地执行条目中（审计权威；plan frontmatter `implementation` 条目可作镜像）

**问题**

1. 编辑点 5 的条目清单仅覆盖 L394–L397（流程）、L413–L416（硬约束）、L418–L420（留痕）、L427（M 定义）、L433（传话首句）；**L396–L399 的「脚本化映射」段未被替换**，该段仍单独指示「`instance_id` 记 plan frontmatter implementation 条目」。同一 `instance_id` 在同一节内因此有两个落点陈述，其中一处未标注「镜像」，与 S2 宣称的「单一审计权威」未闭合。这与 B1 属同一缺陷族：**同一规范事实的多处非指针化表述**。执行者按 L399 只写 frontmatter 即满足字面要求，`retrospective` 审计链可被合法绕过。
2. 同段「N vs M 核对经 `checkpoint-paths`」与计划新写入的「并**优先**经 `checkpoint-paths` 机械生成」（guide L427 新文本）、以及新 C-21(d)「M 侧经 `orchest.py checkpoint-paths` 机械生成」（无条件语气）三种措辞不一致；在多 Executor 协同（本计划新启用场景）下「落地改动先 commit」未必成立，无条件语气会让「核对」这一步在字面上不可执行。
3. 计划 §5.2 声称编辑点 5 为「§八 全节同步（L388–L469）」且「无悬空引用与规范冲突」——该断言与实际条目清单不符，属于计划自述与改动范围不符，需一并修正（否则下次复核仍会以错误的自述为基线）。

**建议修复（逐字终态，新增为编辑点 5 的第 6 项）**

```markdown
**脚本化映射（落地执行 spawn 不进收敛预算门与 Archive Contract，设计裁决见 `SKILL.md` C-21 与 M-11）**：落地执行走宿主原生（未过 gate 的）通道，载体按 C-21(a) 与 `SKILL.md` §传话编排 适用门选定；客观执行标识记 `retrospective.md` 落地执行条目（审计权威），plan frontmatter `implementation` 条目仅作镜像；N vs M 核对优先经 `scripts/orchest.py checkpoint-paths` 机械生成（前置条件 = 落地改动已 commit），无法机械生成时（含多 Executor 无统一 commit 边界）降级为 LLM 汇总各成员实改文件集并显式标注。
```

并同步：① C-21(d) 与 `d3` 的「M 侧经 `checkpoint-paths` 机械生成」改为「优先经 … 机械生成；无统一 commit 边界时降级 LLM 汇总并标注」；② 计划 §5.2 的「§八 全节同步」表述改为覆盖 L388–L469 的逐点清单（含本段）。

## 3. 逐项核验结论

| 项 | 内容（依 `attempts.md` L22–L23 摘要） | 结论 | 核验依据 |
|---|---|---|---|
| **B1** | 适用门与载体偏好收口到 `SKILL.md §传话编排` 单一权威 | **resolved** | 计划 §4 编辑点 1 写「仅在 C-21 且满足 `§传话编排（relay orchestration）` 统一适用门时」；编辑点 3 C-21(a) 写「满足 `§传话编排` 适用门时」；编辑点 5 硬约束写「须满足 `SKILL.md` §传话编排 统一适用门」。四处载体偏好一致：强耦合多 Executor → 优先宿主原生，不支持 → 回退 Spawn/手工传话。未再出现第二个「适用条件」定义（现行 L385–L388 的「三条同时满足」被编辑点 4 整段替换）。残余仅措辞级（见 S-3）。 |
| **S1** | 删除条件 1 冗余 disjunct，仅留归档 `done/` 机械判据 | **resolved** | 编辑点 4 条件 1 为「产物已收敛且方案已定稿（该 slug 已完成终局 decision 并归档 `done/`）」，单一机械判据。与主循环 `d2`→`finish` 先行、`d3` 在后的顺序自洽（`SKILL.md` L251–L252）。 |
| **S2** | 统一 `retrospective.md` 为执行标识审计权威，frontmatter 为镜像 | **still_blocking** | `SKILL.md` 侧（C-21(c)、guide L418–L420 新文本）已统一；但 guide L399 未同步且未纳入编辑点清单 → B2。 |
| **S3** | 补齐宿主实时协同的振荡守卫（Type O 等价） | **resolved**（残余枚举，见 S-2） | 编辑点 4 新增「同一接口或文件被反复推翻 ≥ `type_o_threshold`（默认 3）次 → 立即停止协同并上报用户」；复用既有阈值，未新增数值默认，符合 §1 非变更声明。 |
| **S4** | 明示扩展不入抽象能力层/适配层矩阵 | **resolved** | 编辑点 1 bullet 2：「canonical 路径仍为 `Spawn`/`Continue`/`Identify`；本扩展不是第四个抽象能力，不入 `refs/framework-adapters.md` 适配层矩阵」。与 `SKILL.md` L48–L58 抽象能力层表一致；CONSTITUTION §三 framework-adapters 条款未被触动。 |
| **S5** | 非默认载体沿用 Plan-Execution 等价纪律 | **resolved** | 编辑点 5 硬约束第 2 条：「选用宿主原生实时协同或传话编排时，须满足 … 统一适用门、遵守独立性降级声明（宪法 #6），并沿用 Plan-Execution 的等价纪律（自足 prompt、仅读方案文件、不读审计历史）」。 |
| **S6** | 校正 §八 范围（L388–L469） | **resolved** | 实测 guide：`## 八、落地执行编排` 在 L388，`## 九、信息源核对与申诉仲裁` 在 L472 → 本节实为 L388–L470，计划标注 L388–L469 与各子项行号（L394–L397 / L413–L416 / L418–L420 / L422–L429 / L433）逐条核对均准确。 |
| **S8** | 补 preflight 自检记录 | **resolved** | 计划 §5.5：「本次无数值默认/阈值/停止条件变更，`converge.governance-change/v1` 机器块与 `task-envelope` 要求不触发（理由引 §1）」；与 §1 非变更声明、§2 Bitter Lesson 分层一致。程序性缺项见 S-5（change_class 声明）。 |

**附加核对（计划自述事实）**：`SKILL.md` 中「子收敛之间不通信」在 L519、「子任务间无实时数据依赖」在 L514，与 §1 引用行号一致；编辑点 1 插入位置（核心角色表 L68 之后、`### 模型分层` L70 之前）、编辑点 2 的 `d3`（L252）、编辑点 3 的 C-21（L379）均与现行文件行号一致。行号引用层面无误。

## 4. 宪法与跨文档自检

- **Bitter Lesson（§一三分判据）**：条件 1（产物已收敛定稿 → 防绕开主循环/预算门的状态守卫）与条件 2（验收判据机械可核 → 持续会话丧失反锚定后的补偿控制）保留为硬前置，属「防呆型机制」，不随模型变强减值；条件 3（参与方 ≤ 2）与载体选择交还判断侧，与宪法「机制阈值与参数的设定永远留在 Orchestrator 判断侧」一致。**通过**。
- **Occam**：仅改 2 个受保护文档，不新增文件、状态机、schema 字段；复用 `relay-ledger`、`type_o_threshold`、`retrospective` 落地条目。**通过**。
- **宪法 #6（降级告知）**：手工传话与宿主原生实时协同两条路径均强制告知；并行互查明确「不得产出 verdict、不入 gate ingest」。**通过**。
- **宪法 #7（Orchestrator 不直改产物）**：C-21(b)、编辑点 4「角色边界」、编辑点 5 硬约束三重覆盖，且写入「若偏差需要改产物，仍须 spawn executor」。**通过**。
- **宪法 #1–#5**：无触及；编辑点 2 逐字保留全部宪法强制 gate（终止-b/c、预算软停/`*_exhausted`、`MODE_SWITCH_REQUIRED`、`FAIL_CLOSED`、`需重新设计`）。**通过**。
- **层级模式不变量**：实时协同限定于 C-21；「子收敛之间不通信」「子任务间无实时数据依赖」未被减损。**通过**。
- **独立审计红线**：按功能判据（输出进入 verdict/blocking/收敛裁决/独立验收）+ 六类角色枚举覆盖 outer loop、盲审、ultraverge 并行、Round 0、L2 gate、设计审查；同时禁止 Reviewer↔被审者 与 并行 Reviewer↔Reviewer 共享板，并要求「审计会话与落地协同板生命周期分离」。仲裁 agent（guide L199）与振荡裁判（编辑点 4）虽未点名枚举，但功能性判据已覆盖（二者输出均进入裁决），不构成缺口。**通过**。
- **数值默认/阈值**：无新增或修改，宿主协同守卫复用 `type_o_threshold`；`relay_oscillation_interval` 语义未变。**通过**。

## 5. suggestion_issues

**S-1（中，B2 修复后应一并处理）· `SKILL.md` M-11 与 guide L399 的「§执行阶段」悬空引用**
`SKILL.md` L356 写「落地执行 spawn 豁免（设计裁决，见 §执行阶段/§落地执行编排）」，`refs/orchestrator-guide.md` L399 写「设计裁决见 SKILL.md §执行阶段」，但 `SKILL.md` 无名为「执行阶段」的节（实为「### 执行流程」与 C-21/§落地执行编排）。本计划恰好重写这两处邻近文本，建议顺手改为 `SKILL.md` C-21 / `refs/orchestrator-guide.md` §八，避免「无悬空引用」验收项失真。

**S-2（中）· 宿主原生协同路径的振荡类型枚举不完整（Type F / Type R 处置缺失）**
编辑点 4 写「宿主原生实时协同路径下无手工转发与 outer round 结构，Type R/S 不适用，保留 Type O 等价守卫」。`SKILL.md` L117–L122 的振荡表含 O/R/F/S 四型，其中 **Type F（同一问题在 A↔B 间来回翻转）**在协作板上恰是最可能的形态，文本既未声明其不适用，也未说明由 Type O 计数覆盖。建议补一句：「Type F 由同一 Type O 计数覆盖（同一决策点 A↔B 往返计为推翻），Type R/S 不适用」——不新增阈值，仅补枚举闭合，避免读者认为 Type F 被静默丢弃。

**S-3（低）· 四处载体偏好表述的限定语不一致**
权威定义（编辑点 4 条件 3）的判据是「多 Executor **强耦合** 且宿主具备原生能力 → 优先原生」。编辑点 1 追加了「且需共享中间状态或频繁对齐接口」的限定；编辑点 3 与 guide 流程段（「强耦合落地可选宿主原生实时协同或传话编排」）则省略了「满足适用门」与「优先」二字。语义均不相反，但存在「非权威处自带判据」的复发风险（B1 的病根）。建议非权威处要么只写指针（「载体按 C-21(a) 与 §传话编排 适用门选定」），要么逐字复述条件 3 的判据。

**S-4（中）· 手工传话路径「振荡裁判」spawn 的记账路径与「落地 spawn 不进预算门」冲突**
编辑点 4 保留「该 spawn 记入现有 gate ledger，落在 `total_safety` 余量内」，而 guide §八 L401 明确「落地执行 spawn 不进收敛预算门；reserve-round/register-round/cancel-round 仅限收敛循环内 executor 修复轮」。于是裁判 spawn 既被要求进 ledger，又被排除在唯一合法的 gate 生命周期命令之外；`SKILL.md` L215 又禁止手跑裸 `budget_gate.py`。建议在编辑点 4 明示记账方式（例如：裁判 spawn 作为 `consumes:none` 事件经 `orchest.py` 记录、不占 reservation；或明确其属于落地豁免、仅记 attempts.md），否则执行时会落入「记账则违规、不记账则漏记」的二难。

**S-5（中）· 未声明 `change_class`，material revision 程序链未闭合**
`refs/orchestrator-guide.md` §Material revision 规定：post-review 修订须在 `attempts.md` 写 `converge.material-revision/v1` 块并声明 `change_class`；`decisional`（含 roles-permissions / fail-closed 锚点）须两个不同 fresh Spawn 审查同一最终字节。本轮修订涉及「落地载体授权门」（角色/权限语义）与「适用门从三硬条件降为两硬+一软」（Round 1 引入），`attempts.md` 仅有人读摘要，无 `change_class` 声明与机器块。建议：① 在 `attempts.md` 追加 `change_class` 声明（若判定 `non-decisional`，写明不触及 roles-permissions/fail-closed 的理由；若 `decisional`，按 §Material revision 的同字节双权威复核执行）；② 计划 §5.4 的治理程序清单同步补上该链路。**注**：因未读 `round-1.md` / `uv-init-*.md`（审查边界），severity 归类请以 Orchestrator 对原阻断严重度的认定为准；本项按「程序完备性未闭合」提出，不单独作为阻断。

**S-6（低）· 核心角色表的「Executor = 全新上下文」与落地持续会话参与方的口径未标明作用域**
`SKILL.md` L68 的核心角色表规定 Executor「**全新上下文**」，而本计划允许落地阶段以持续会话/共享板参与方承担 executor 角色（经宪法 #6 告知）。编辑点 1 紧邻该表插入，却未声明「角色表的新鲜上下文约束作用于收敛主循环角色，落地阶段参与方按 §传话编排 载体现状适用并做降级告知」。建议补一句作用域限定，避免前置自检 Q1/Q4 或后续 reviewer 将其读成身份矛盾。

**S-7（低）· 落地标识写入已归档 `retrospective.md` 的写路径未规定**
`SKILL.md` L334 规定收敛后修订须先 `reopen`、禁止手改历史 manifest，而 guide L401 自述「落地发生在归档之后」。新文本要求把执行标识写入 `retrospective.md`（审计权威），但未说明该写入发生在归档前的占位条目、还是归档后的 append（是否需要 reopen）、还是以 frontmatter 为主。建议在编辑点 5 留痕段补半句：「若 retrospective 已归档，落地条目为 append-only 追加（不覆盖），并在 plan frontmatter 镜像；不触发 reopen」。

**残余风险（非建议项，供 Orchestrator 决策）**：本轮按指令未读 `refs/state-schema.md`、`refs/framework-adapters.md`、`scripts/README.md`、`refs/executor-prompt.md`。若 `state-schema.md §relay-ledger` 或 README 中另有「适用条件/参与方 ≤ 2/instance_id 记录位置」的规范性表述，仍可能存在未被本轮覆盖的第三方表述冲突（即 B1 的第三处）。建议执行前做一次全域字面检索：`grep -n "≤ 2\|三条同时满足\|frontmatter implementation\|relay orchestration" SKILL.md refs/ scripts/README.md`，命中处一律降级为指针。

## 6. 结论

B1 已解决，S1/S3/S4/S5/S6/S8 已解决；S2 未彻底闭合，构成阻断 **B2**（`refs/orchestrator-guide.md` §八 L396–L399 未同步，执行标识出现第二落点且 M 侧措辞三处不一致）。修复成本约一段落 + 两处措辞对齐，同时建议吸收 S-1/S-2/S-4/S-5 以避免下一轮因同类「非指针化残留」再次阻断。

`verdict: 阻断需修复`

### reads

- `<user-home>\Documents\GitHub\converge-skill\docs\plans\active\20261126-on-demand-realtime-collab.md`
- `<user-home>\Documents\GitHub\converge-skill\.converge\active\20261126-on-demand-realtime-collab\attempts.md`
- `<user-home>\Documents\GitHub\converge-skill\CONSTITUTION.md`
- `<user-home>\Documents\GitHub\converge-skill\SKILL.md`
- `<user-home>\Documents\GitHub\converge-skill\refs\orchestrator-guide.md`
- `<user-home>\Documents\GitHub\converge-skill\refs\reviewer-discipline.md`
- `<user-home>\Documents\GitHub\converge-skill\.converge\active\20261126-on-demand-realtime-collab\round-2.md`（骨架，输出目标）
- `<user-home>\Documents\GitHub\converge-skill\.converge\active\20261126-on-demand-realtime-collab\`（目录列举）

## Orchestrator 处理记录

(pending)