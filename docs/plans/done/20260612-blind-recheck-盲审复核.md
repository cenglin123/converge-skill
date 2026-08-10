---
type: plan
status: active
created: 2026-06-12
scope: converge SKILL 终止判定 — 盲审复核（blank-slate recertification）
governance: true
note: 动终止判定属治理域，落地修改本身按明线规则走 ultraverge
related:
  - "SKILL.md"
  - "refs/reviewer-prompt.md"
  - "refs/state-schema.md"
---

# 盲审复核（Blank-Slate Recertification）

## 摘要

为 converge 增加一个终止前的**盲审复核**步骤：当收敛经历 ≥2 轮后签发"可执行"，spawn 一个**不读 attempts.md** 的 fresh Reviewer 做最终复核。它修补一个现有结构盲点——越难收敛的产物，最终签发者读的 attempts 越厚，验收越不"干净"。本方案是对"收敛完成前必检"的一处修正 + 对既有 escalated_issues / Executor 修复管道的复用，**不引入嵌套循环层级**。

## 溯源（设计演化本身是论证的一部分）

| 阶段 | 形态 | 结论 |
|------|------|------|
| 起点 | block loop（三层循环 + Block/Stacking/Skip/Residual 四概念） | 用 ResNet 类比堆叠完整 converge 块 |
| 约简 | 独立 Reviewer 审查发现：block loop 全部增量 = 一个比特（终审者读不读 attempts） | 三层包装是 Inception 式复杂化，放弃 |
| 压测 | 对约简方案压四个交互面（产物泄漏 / 归因 / contract 版本 / 信息量） | 四面全部闭合 |
| 收敛 | 原方案作者攻不破，verdict=可执行 + 2 suggestion | 进入本提案 |

**关键教训（写入 rationale，不进规范文本）**：ResNet 的精神是"不把深做成新楼层"。真正的约简是修一个终止判定，而非新增一层循环。block loop 虽运行时简单，但文档重量是 Inception 式的——与近期减重方向（2c5a1d7）冲突。

## 问题陈述

现有体系中，签发"可执行"的最后一个 Reviewer：

- **若 D11=a（首轮通过）**：Round 1 Reviewer 因"skip if Round 1"本就不读 attempts，签发者已 fresh，无需干预。
- **若 D11=b（渐近，≥2 轮）**：终审 Reviewer 读了完整 attempts.md，带着"清单上的问题都修了"的确认偏误签发——它在确认"已知问题已解决"，而非空白视角问"这产物本身好不好"。

**结构盲点：最需要干净验收的难产物，恰恰拿到最不干净的验收。** 这不是 max_outer_loops 能解决的——每多一轮，attempts 只会更厚，永远给不出无历史的终审者。

这也是 converge 已有原则"Reviewer fresh context 防偏见"的逻辑闭合：若信这条，则最该 fresh 的就是终审那一刻，而现状恰在此刻最不 fresh。盲审复核不是新原则，是把旧原则贯彻到底。

## 核心机制

```
收敛主循环 → verdict=可执行
  ├ 若本次收敛 = 1 轮（D11=a）→ 直接收敛，无盲审（终审者已 fresh）
  └ 若本次收敛 ≥2 轮 →
       spawn 盲审 Reviewer（不读 attempts.md）
       ├ 零阻断 → 真正收敛，retrospective 记 blind_recheck: pass
        └ 有阻断 → findings 作为 escalated_issues 注入主循环
                   → Executor 修复 → 下一 outer loop Spawn fresh Reviewer 验收 → 再次可执行 → 再次盲审
                  → 超 max_blind_rechecks → 预算软停，问用户
```

任一次盲审首轮通过即止（等价于"残差→0"）。盲审失败→重新收敛→再盲审（等价于"块堆叠"）。contract 持续在场（等价于"skip connection"）。——三个 block loop 概念在行为上被复现，但实现是修终止判定，零新嵌套循环层级。

**目录状态**：盲审在 `active/` 内进行——verdict=可执行后、retrospective 写入前。盲审失败后，findings 注入主循环的 escalated_issues，Executor 在 `active/` 内修复，下一 outer loop Spawn fresh Reviewer 验收，再次可执行后再次盲审。不触发 done/→active/ 回流（那是收敛后修订的流程，不是盲审的）。

## 七要素规范

### 1. 触发条件

`verdict = 可执行` 且本次收敛经历 ≥2 轮 outer loop。

> **记号约定**：D11=a/b/c 是本方案的内部分析缩写，对应 SKILL.md 终止-a（严格首轮通过）/ 终止-b（渐近通过）/ 终止-c（主观接受）。不进入 SKILL.md 规范文本——规范文本用"终止-a/b/c"全称。

- D11=a（1 轮）天然排除——签发者已 fresh。
- D11=c（主观接受）且 ≥2 轮：触发盲审，但因用户已主观接受，盲审失败时**提示而不强制**重新收敛（用户可一键确认"仍然够了"）。用户确认跳过时标注口径见 §5。

### 2. 盲审输入

`产物本体 + amended contract.md + reference_materials`（required reading #5），**不含 attempts.md / round-N.md / retrospective**。

- 传 amended contract 而非原始版：系统只有一份就地回写的 contract.md（责任清单 #13），传原始版需考古 + 新增版本机制，撞反考古治理立场。
- amendment 是经对抗程序认证的**意图修正**，性质与 attempts（修复痕迹）根本不同——意图可演进，历史不可继承。
- 原始意图锚由 reference_materials 承载，模板已要求跨轮一致传递。skip connection 两端各有着落：amended contract = 最新标准，reference_materials = 原始意图。

### 3. 盲审指令（按产物痕迹类型分流）

盲审 Reviewer 的 prompt 是标准 Reviewer prompt 的一个**变体**，不是独立模板。以下逐节定义变体差异（保留 = 与标准模板一致；删除 = 整节移除；替换 = 覆盖内容）：

| 标准模板节 | 盲审变体操作 | 说明 |
|-----------|------------|------|
| Required reading | **替换** | 移除 attempts.md（#2）；保留 plan_path（#1）、this_skill_path（#3）、contract_path（#4）、reference_materials_path（#5） |
| 前置自检 Q1-Q6 | **保留** | 盲审仍需检查产物身份/边界/纯度等 |
| Your task | **保留** | 审查任务不变 |
| 升级复查（escalated_issues） | **保留** | 盲审可能接收主循环注入的 escalated_issues（来自上一轮盲审失败的 findings） |
| 意图漂移检查 | **删除** | drift_context 依赖 attempts.md 历史，盲审无此输入 |
| Output format · attribution | **替换** | 移除 `attribution: <plan_defect \| executor_limit>` 字段要求，替换为 `attribution: pending`（固定值）。见下方"归因处理" |
| 硬纪律 #2 | **替换** | 原文要求 attribution MANDATORY 二元归因。盲审变体改为：`attribution: pending`（固定，不要求归因判断）。理由：盲审无历史，结构上无法做归因 |
| 硬纪律 #6 | **删除** | 依赖 attempts.md 中 `[Orchestrator Detection]` 标记，盲审不读 attempts.md |
| 硬纪律 #7 | **删除** | 依赖 attempts.md 中 `source: orchestrator_self` 条目，盲审不读 attempts.md |
| Antipattern 巡查（Round ≥ 2，executor 层） | **删除** | executor 层反模式依赖 attempts.md 修复历史，盲审无此输入 |
| 设计层 Antipattern | **保留** | 产物本身的设计缺陷仍需检测 |
| 代码项目审查 | **保留**（条件激活） | 若收敛对象是代码项目，确定性检查和语义审查仍适用 |
| Contract / Rubrics | **保留** | 传 amended contract 和 rubrics |

**归因处理**：盲审 prompt 的 output format 中 `attribution` 字段固定为 `pending`，不要求 Reviewer 做二元选择。标准模板硬纪律 #2（attribution MANDATORY）在盲审变体中被替换为上述规则。这不矛盾——归因义务转移到下一轮主循环 Reviewer（见 §4）。

盲审 Reviewer 在标准 Reviewer 基础上增加两条替换指令：

**A1 — 散落正文的修复痕迹 → 举报，不忽略。** "本条应 R2 Reviewer 要求调整"类行内注释、产物内对轮次/retrospective 的引用，本身是 `archaeology_leftover` 反模式（已在 antipatterns 枚举），收敛完成的产物不该残留。盲审作为"产物无考古层"纪律的最后执法者，看到即列为 finding。空白视角恰是检测考古层的最佳视角——主循环 Reviewer 读 attempts 读到对这些痕迹脱敏。

**A2 — 合法结构化历史段（如 plan 的 `## Agent 评议` 段）→ 审一致性，但禁推理偏移。** 指令原文：

> 产物中若存在评议/执行记录类章节，将其作为产物内容审查（一致性、与正文的矛盾）；但"产物已经过 N 轮审查/修复"这一事实**不得作为降低审查强度或提高通过倾向的依据**。

禁的是"已审过→倾向通过"这一步推理，不是那段文本的可见性。

**否决数据层剥离**：剥离后认证的是幻影副本而非交付物；且自动隐藏 `## Agent 评议` 段等于在认证前替产物掩盖 A1 类应被举报的缺陷。剥离与盲审目的直接对抗。

### 4. 归因协议（证人发现 / 法官归因）

盲审无历史 → 结构上无法做二元归因（归因需要"这是 executor 改出来的还是 plan 本有的"历史）。切分：盲审（证人）只发现，主循环 Reviewer（法官）补归因。

```
盲审 finding → attempts.md（attribution: pending，annotation 标 source: blind_recheck）
            → 注入下一主循环 Reviewer 的 <escalated_issues>
            → Reviewer 复查时必须落定 attribution（plan_defect / executor_limit）
```

**findings → attempts.md 字段映射**：

| 盲审 finding YAML 字段 | attempts.md entry 字段 | 映射规则 |
|----------------------|---------------------|---------|
| `id` | `issue` 标题后缀 | `## Round N blind-recheck attempt · finding {id}` |
| `description` | `Issue:` | 原话引用 |
| `severity` | `severity:`（新增字段） | 直接映射 |
| `plan_amendment_required` | `plan_amendment_required:` | 直接映射 |
| `location` | `location:`（新增字段） | 直接映射 |
| （固定值） | `Issue 归因（reviewer 判定）:` | 填 `pending` |
| （固定值） | `source:` | 填 `blind_recheck` |
| `attribution` | — | 忽略（固定为 pending，不写入 attempts.md 的归因字段——归因字段记录落定后的值） |
| `antipattern_observations` | — | 保留在 round-N.md 原始输出中，不映射到 attempts.md entry |

**findings → escalated_issues 传递格式**：

盲审 findings 以**独立注入块**方式传入下一主循环 Reviewer 的 `<escalated_issues>`——不做语义嫁接（不把 findings 伪装成上轮 Reviewer 的 blocking_issues）。格式：

```yaml
# Orchestrator 注入的 escalated_issues 中，盲审来源条目标注如下：
- id: BR-{finding_id}
  source: blind_recheck
  description: |
    <finding description 原文>
  severity: <finding severity>
  attribution: pending
  plan_amendment_required: <finding 的 plan_amendment_required>
```

前缀 `BR-` 与主循环 issue 的数字 id 区分。主循环 Reviewer 复查时必须：
- 对 `attribution: pending` 的 escalated issue，三态标记（resolved / still_blocking / deferred）之外**同时落定二元归因**（plan_defect / executor_limit）
- "回应"不等于"补归因"——需在 protocol 中显式要求，否则 pending 可能在"已回应但未归因"状态下过期

- 复用 escalated_issues 既有强制机制（逐条回应、三态标记、禁止沉默）。**额外强制项**：回应一条 `attribution: pending` 的 escalated issue 时，三态标记之外必须**同时落定二元归因**——"回应"不等于"补归因"，需在协议中显式要求，否则 pending 可能在"已回应但未归因"状态下过期。
- `pending` 枚举值仅 blind_recheck 来源可用；**硬过期规则**：不得跨过下一主循环轮存活。
- **否决 Orchestrator 补归因**：归因是宪法分配给 Reviewer 的判断（硬纪律 #2/#3）；且 Orchestrator 跑 Type O/R 检测、归因是其输入——让它补归因 = 裁判生产自己要裁的证据。
- **时序无害**：Executor 修复只需 finding 描述、不需归因；归因在下一轮落定，早于任何振荡分析对该 entry 归因的依赖。硬纪律 #3（归因不得跨轮切换）对 pending→落定不构成切换（首次落定非 flip）。

### 5. 标注口径（诚实闭合）

- `blind_recheck` 是 retrospective 独立字段，**永不升格终止类型**——D11=b + 盲审通过记为"D11=b + blind_recheck: pass"，不重标为 D11=a。"D11=b 误升 D11=a"无发生通道，因为这个升格操作不存在。
- 声称口径固定为：**"一个未读修复历史的独立 Reviewer 未发现阻断"**——不声称"等价于首轮通过"。
- 若盲审举报了 A1 类痕迹：记 `blind_recheck: pass (traces_reported: N)`，pass 的证据强度如实打折。
- "假盲审比无盲审糟"只在假盲审**冒充**真盲审发认证时成立——本协议移除的是声称（降口径），不是机制。
- **D11=c 交叉状态**：若终止-c（主观接受）触发盲审后，用户确认跳过盲审修复：
  - retrospective 记 `blind_recheck: waived (user_accepted_with_known_gaps: true)`——不记 pass（未通过），不记 fail（产物仍进入 done/）。
  - `waived` 不计入 rule_frequency 的命中率统计（避免拉低盲审的实证基线）。
  - "诚实闭合"原则要求：声称口径为"用户在已知盲审发现后主动接受"——这不是盲审通过，是用户行使终止-c 的显式确认权。

### 6. 预算

- `max_blind_rechecks`：默认 2。独立于 max_outer_loops。
- 盲审失败后的修复轮次**共享原 max_outer_loops**。若收敛时 max_outer_loops 已近耗尽、盲审失败后修复触顶 → 走预算软停问用户，**不自动扩**（防止盲审变绕过预算上限的后门）。

### 7. 采纳节奏

先在 ultraverge / mission-critical 试运行 → 以 A5 对照实验 + 若干次实战 retrospective 为门槛 → 放开默认开启。**这是推广策略（攒实证），不是正确性 fallback**——A/C 已闭合，不存在"无法闭合所以退守"的情形。

## 文件改动清单

| 文件 | 改动 |
|------|------|
| `SKILL.md` 收敛完成前必检 | 增加盲审复核 gate 项：≥2 轮收敛时，终审通过后须先过盲审（或 blind_recheck: waived） |
| `SKILL.md` 执行流程 | 在 Orchestrator 主循环步骤 d（verdict=可执行）后、收敛完成前必检前，插入盲审复核小节：≥2 轮收敛时 spawn 盲审 Reviewer，findings 作为 escalated_issues 注入主循环（仍在 active/ 内，不触发 done/→active/ 回流） |
| `SKILL.md` 配置参数 | 增加 `max_blind_rechecks`（默认 2） |
| `SKILL.md` Orchestrator 责任清单（条件触发类） | 增加一条"盲审复核编排"——≥2 轮收敛后 spawn 盲审、处置 findings、维护 blind_recheck 标注 |
| `refs/reviewer-prompt.md` | (1) 增加盲审复核 prompt 变体定义（见 §3 节级差异表 + A1 举报义务 + A2 推理禁令 + 去 attempts required reading + attribution 固定为 pending）；(2) 标准模板 escalated_issues 节增加规则：回应 `attribution: pending` 的 escalated issue 时，三态标记之外必须同时落定二元归因 |
| `refs/orchestrator-guide.md` | 增加盲审复核编排操作指引：盲审 spawn 条件、findings 处置（注入 escalated_issues，用 BR- 前缀独立注入块）、pending 归因过期检查、blind_recheck 标注维护 |
| `refs/state-schema.md` | attempts attribution 增加 `pending` 值 + `blind_recheck` source；retrospective 增加 `blind_recheck` 字段（含 traces_reported）。**Consumer 契约**：pending 值仅对 source: blind_recheck 条目合法，且在该条目对应的下一主循环轮结束时必须已落定为 plan_defect 或 executor_limit。Consumer 在做归因统计时应排除 pending 值或将其标记为 attribution_incomplete |
| `refs/state-schema.md` 硬约束 #3 | **修改硬约束文本**：将"二元归因（plan_defect / executor_limit），不允许 warning / 不重要"改为"归因为 plan_defect / executor_limit / pending（仅限 source: blind_recheck），不允许 warning / 不重要"。pending 是第三种合法值，适用条件：仅当 issue 来源为盲审复核（source: blind_recheck）时可用，且不得跨过下一主循环轮存活 |
| `refs/state-schema.md` rule_frequency 注册表 | 增加 `blind_recheck` key——命中率长期为 0 时按减重方案自动进入衰减评估。触发检测方式：`blind_recheck` 字段出现在 retrospective 中即 triggered。`waived` 状态不计入命中率（算 zero_streak 递增） |
| `refs/state-schema.md` retrospective 模板 | 增加 `## 盲审复核` 结构化字段定义：`blind_recheck: <pass \| fail \| waived>`, `traces_reported: <int>`, `rounds_used: <int>`, `findings_count: <int>`, `escalated_to_main_loop: <bool>` |

## pilot 实验（A5，放开默认的门槛）

拿一个已收敛产物：带痕迹原件 vs 手工剥痕迹副本，各 spawn 盲审，比较 verdict 与理由中是否出现历史引用。成本 2-4 个 spawn。验证"指令层禁推理偏移"对同模型的实际有效性。

## 不做的事（收敛过程中明确排除，防止执行侧重新引入）

- 不引入 block loop 三层循环、不把 Block/Stacking/Skip Connection/Residual 写进 SKILL.md 规范文本（ResNet 故事只进本提案 rationale）
- 不对产物做数据层剥离（认证幻影副本 + 主动隐藏缺陷）
- 不让 Orchestrator 补归因（裁判自我交易）
- 不传原始 contract（传 amended + reference_materials）
- 不让 blind_recheck 升格终止类型
- 不新增独立循环层级（修终止判定 + 复用主循环的 escalated_issues 和 Executor 修复管道）
- 不处理层级模式（hierarchical converge）与盲审的交互——待 `refs/decomposition-protocol.md` 后续版本处理
- 不在收敛后修订流程中集成盲审——收敛后修订是对已完成产物的补充（已有独立 Reviewer 验证），与盲审的"终审前干净复核"场景不同。若用户在收敛后修订中再次触发 ≥2 轮收敛，盲审自然适用，无需特殊处理

**溯源表定位**：上方"溯源"节中的表格是本提案 rationale 的论证记录（设计演化过程），不进入 SKILL.md 规范文本——它记录的是"方案怎么来的"而非"方案是什么"。

## 风险评估

| 风险 | 等级 | 缓解 |
|------|------|------|
| 指令层禁推理偏移对**隐性先验偏移**效果弱 | 中 | 泄漏单向偏置"更易通过"（不造假阻断）；现状基线是终审者读完整 attempts，任何残留锚定**严格轻于现状**；标注诚实兜底；A5 对照实验量化 |
| 盲审同模型同 prompt，盲点高度相关，可能频繁 no-op | 中 | no-op 下界 1 spawn；"独立空白复核未发现阻断"本身有信息量；rule_frequency 追踪命中率，长期为 0 则自动衰减（自带证伪路径） |
| `pending` 归因悬空 | 低 | 硬过期规则（不跨下一主循环轮）+ escalated 强制回应 + 额外强制落定归因 |
| 又加机制，与减重方向冲突 | 低 | 修终止判定非加楼层；接入 rule_frequency 衰减管道，与减重同向 |
| 盲审成为绕过预算的后门 | 低 | max_blind_rechecks 独立上限；修复轮次共享 max_outer_loops，触顶走软停不自动扩 |

## 元层观察

这轮"block loop → 约简 → 压测 → 闭合"本身是一次活的 converge，对象是本方案。原方案作者在"挑战者"身份下主动撤回了"二次锚定"伪问题——**角色切换提供的去锚定，与盲审提供的去锚定，是同一种力**。这是价值假设的一个现场证据点（但独立性强于盲审的"同模型不同 spawn"，不能完全外推）。

## 落地约束

本方案动 SKILL.md 终止判定，属治理域。**落地修改本身按明线规则走 ultraverge**（≥3 并行 Reviewer + 收敛 + 强制设计审查）。
