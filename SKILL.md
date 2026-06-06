---
name: converge
description: Use when a plan, code artifact, or other structured output needs iterative convergence through independent review cycles. Trigger on "converge", "收敛", "迭代收敛", or when confidence in artifact quality is insufficient for execution. trigger "ultraverge" for the full pipeline (评议+收敛+收敛后设计审查) on mission-critical artifacts. NOT for single-pass code review — use a lighter review skill for that.
---

# Converge — 双 Agent 迭代收敛器

> Orchestrator（主对话）管理循环，每轮 Spawn 全新 Reviewer 审查产物，Executor 修复问题，直至 Reviewer 给出"可执行"verdict 或触发停止条件。
>
> **框架无关**：Reviewer / Executor 的启动和续命通过抽象能力层实现（附录 A），不绑定特定框架 API。

---

## Positioning

本 SKILL 在产物生命周期中的位置：

```
产物草稿完成 → [Round 0 合同谈判] → 评议（默认入口）→ Converge（按需升级）→ 产物进入执行/落地
                     ↑                  ↑               ↑                  ↑
               可选前置阶段         单轮主观 verdict  仅 conceptual/arch   ultraverge: 全量
               对齐"什么算完成"     一次写回           阻断时升级多轮收敛   强制评议→收敛→设计审查
               + 定义 Rubrics 维度
```

- **前置条件**：有可审查的产物（plan 文件 / 代码项目 / 文档等），且产物已完成初稿
- **后继条件**：收敛达成后，产物可安全进入下一阶段（执行、提交、部署）
- **不适合**：单次快速审查、日常代码 review、lint 级别的检查——这些用更轻量的 review 技能
- **可组合**：如果存在完整的开发工作流型 SKILL（如 Dynamic Workflows 的 pipeline/parallel 编排），converge 可以作为其中的**质量门控**插入——在 phase 交接处插入独立的"方向性审视"，让指挥部的决策在行动前暴露盲点。门控分两级：L1 轻量信号检测（非 LLM 脚本，零 token 成本）和 L2 单轮对抗审查（按需启动）。详见 `refs/quality-gate.md`

---

## ⚠️ 宪法级设计原则

> 以下两条是本 SKILL 的最高判据。任何对 SKILL.md 或 refs/ 的修改，必须先通过这两条的自检（详见 `refs/orchestrator-guide.md` §〇 宪法自检），否则不考虑执行。

本 SKILL 的自身演化受两条宪法级原则约束——它们不是运行时规则，而是**本 SKILL 该长什么样、该包含什么**的设计判据：

| 原则 | 判据 | 应用实例 |
|------|------|---------|
| **Bitter Lesson** | 这东西是通用机制还是针对当前模型的补丁？机制硬编码，补丁做成 compiled 产物 | 三角色/对抗循环硬编码；反模式清单挂在 retrospective 上、由 distill 脚本维护 status |
| **Occam** | 这东西解决什么具体问题？不解决具体问题的实体删除，git log 是考古层 | 三层物理分离（不让会变化的知识腐化在不变的机制里）；章程瘦身（引用表替代重复副本）；宪法级约束表不含"已迁出"说明 |

> 新增文件/规则/字段时，两条原则同时适用：先问 Bitter Lesson（硬编码还是 compiled？），再问 Occam（必要还是多余？）。

---

## 抽象能力层

三个原子能力。不同 agent 框架用不同方式实现，语义等价：

| 能力 | 语义 | 输入 | 输出 |
|------|------|------|------|
| **Spawn** | 启动**全新上下文**的 agent，给自足 prompt | prompt 文本 | instance_id |
| **Continue** | 向**已有** agent 发跟进消息，保有上下文 | instance_id + 消息 | agent 回复 |
| **Identify** | 返回当前 agent 实例标识 | — | instance_id |

> 附录 A：Claude Code / opencode / codex 的具体实现。

---

## 核心角色

| 角色 | 担任者 | 关键约束 |
|------|--------|---------|
| **Orchestrator** | 主对话 agent | 不兼任 reviewer/executor；只管理循环 + 语义判定 |
| **Reviewer** | 每轮 Spawn 的独立 agent | **全新上下文**（看不到历史对话）；prompt 自足 |
| **Executor** | 每轮 Spawn 的独立 agent | 全新上下文；prompt 自足 |

---

## 收敛方式

| 方式 | 触发条件 | 产物要求 |
|------|---------|---------|
| **收敛** | fresh reviewer 首次审查 verdict = `可执行`（零阻断） | 写 retrospective.md，移 done/ |
| **预算软停** | 达预算上限（默认 5 轮），用户决定不续费 | retrospective.md 注明"未收敛但用户接受" |
| **振荡硬停** | 触 Type O（推翻≥3）或 R（重复≥5） | retrospective.md 填病因 + 建议 |

---

## 收敛判定（D11 三选一）

| 类型 | 判据 |
|------|------|
| **a. 严格首轮通过** | fresh reviewer 首次审查 verdict = `可执行`，零阻断 |
| **b. 渐近** | blocking_issues 单调下降 + 剩 ≤1 个无争议低级项，用户确认后接受 |
| **c. 主观接受** | 未达 a/b，但用户明确说"够了，就这样" |

D11=a 是默认目标。b/c 需用户显式确认。

---

## 振荡检测

| 类型 | 定义 | 处置 |
|------|------|------|
| **Type O (Overturn)** | 同决策点被推翻 ≥3 次 | 硬停 |
| **Type R (Repeat)** | 本轮阻断与上轮同源（语义等价） | 标注，累计 ≥5 次硬停 |
| **Type F (Flip)** | 同一问题在 A↔B 之间来回翻转 | 标注 |
| **Type S (Swing)** | 同 reviewer 在 inner loop 中反转自己判断 | 标注 |

---

## 模式边界：评议 / 单层收敛 / 层级收敛 / 审计

| 维度 | 评议 (deliberate) | 单层收敛 (converge) | 层级收敛 (hierarchical) | 审计 (audit) |
|------|------------------|-------------------|----------------------|--------------|
| **对象** | 计划文件（事前草案） | 单个 plan / 代码 / 文档 | 大型项目（多模块） | 已落地产物（事后） |
| **时态** | 事前 | 事中 | 事中 | 事后 |
| **反馈路径** | 一次写回 | **多轮写回** | **多轮写回 × 并行子收敛** | 不写回（观察者） |
| **判断模式** | 主观 + 离散 verdict（5 问前置自检） | 严格首轮通过 / 渐近 / 主观接受 | 子收敛各自收敛 → Planner 整合 | P0-P3 + 对齐率% |
| **并行性** | 无 | 无（单线程迭代） | 有（多子收敛并行） | 无 |
| **启用条件** | 产物有初稿、需快速对齐 | 产物有初稿、需深度验证 | 产物可分解为 ≥2 独立 scope | 产物已落地 |

**默认入口**：**从评议开始。** 绝大部分审查需求在第一轮评议中就能得到有效反馈。仅当评议发现 conceptual 或 architectural 级别的阻断、且单轮修复后需要 independent verification 时，才升级为完整收敛。实证：6 次 converge 调用中 4 次是评议（单轮），完整收敛最多 3 轮从未超过。

评议的前置自检（5 个设计层问题，见 `refs/reviewer-prompt.md`）覆盖了产物身份、边界诚实、数据纯度、职责边界和命名一致性——这些是方向性问题，通常能在 1 分钟内判定。Q1-Q3 与设计审查的 DR1/DR4/DR6 为分层审查（前置自检做 binary check，设计审查做 dimensional assessment）。Q4/Q5 触发 blocking 时，Orchestrator 应评估是否触发设计审查——职责边界和命名一致性问题往往暗示更深层架构问题。更深层的架构维度（可维护性、可扩展性、残留冗余等）留给收敛后设计审查处理。

**判别原则：**

1. 先看时态——事前 = 评议，事后 = 审计，事中 = 收敛
2. 事中再看规模——单 scope = 单层收敛，多独立 scope = 层级收敛
3. 默认评议——仅在评议 verdict 含 conceptual/architectural 阻断时升级为完整收敛

> **Ultraverge**（表格外组合模式，仅 `ultraverge` 关键词触发）：评议（扩域至 DR 7 维 + 前置自检 5 问）→ 评议可执行则跳过收敛 → 强制设计审查。不是独立模式，是默认路径的"全量变体"。

> **收敛后设计审查**（`refs/design-review-prompt.md`）：事后、不写回、咨询式——时态属于审计，但判断维度不同（7 维 vs P0-P3对齐率），是审计的一个可选子模式。在产物收敛完成后触发，产出 advisory findings 供用户决策。

---

## 执行流程

### Ultraverge 路径（仅 `ultraverge` 关键词触发）

对安全性或稳定性有极端要求的产物（核心 SKILL 定义、宪法文档、基础架构 plan），用户可使用 `ultraverge` 关键词触发全量流程：

```
ultraverge → 评议（扩域至 DR 7 维 + 前置自检 5 问）
          → 评议 verdict = 可执行 → 跳过完整收敛 → 强制设计审查
          → 评议 verdict ≠ 可执行 → 完整收敛 → 强制设计审查
```

与默认路径的差异：
- **评议**：Reviewer prompt 额外注入设计审查的 7 维骨架（DR1-DR7），不做"仅查方向性问题"的裁切
- **完整收敛**：若评议 verdict = 可执行 → 跳过（评议已在扩域下审查完毕，完整收敛新增发现概率极低，只增成本）；若 verdict ≠ 可执行 → 标准流程（Round 0→多轮→收敛）
- **收敛后设计审查**：**强制触发**——跳过常规触发条件（模块数/新约定/系统边界）的判断，直接执行

仅在用户显式使用 `ultraverge` 关键词时触发。适用场景：converge 自身的自举审查（ultraverge 由用户显式触发，不存在 Orchestrator 自主跳过的风险）、init-agent-docs 等基础工具的审查、安全关键配置变更。

### 默认入口：评议。 首次审查一律使用评议模式（单轮、主观 verdict、一次写回）。评议的 Reviewer prompt 与完整收敛的 Round 1 相同。评议完成后 Orchestrator 根据 verdict 决策：

- verdict = 可执行 → 收敛完成，归档 done/
- verdict = 需修订 + 阻断为 implementation/structural → Executor 修复，评议模式再走一轮
- verdict = 需修订 + 阻断为 conceptual/architectural → **升级为完整收敛**（下方主循环）

完整收敛仅在有证据表明"评议的单轮深度不足以解决问题"时触发——不是默认路径。

### Round 0 · 合同谈判（可选前置）

> 详细流程和 contract.md 格式见 `refs/contract-negotiation.md`。Rubrics 维度选择见 `refs/rubrics.md`。

```
0a. Orchestrator 判断是否跳过（用户要求 / 对象极简 → 跳过并记录理由）
0b. Spawn Executor → 输出验收合同草案
0c. Spawn Reviewer（独立 context）→ 挑战合同草案
0d. 将挑战反馈交给 Executor → 修订合同 → 写入 contract.md
0e. 更新 _orchestrator-state.md → contract_status: completed
```

Round 0 **不计入** max_outer_loops 预算。若跳过，Round 1 的 Reviewer 不引用 contract。

### Orchestrator 主循环

```
1. 创建 .converge/active/<slug>/ 目录
2. 初始化 _orchestrator-state.md（格式见 refs/state-schema.md）
3. for round in 1..max_outer_loops:
   a. Spawn 新 reviewer（prompt 模板见 refs/reviewer-prompt.md，若存在 contract.md 则一并传入）
   b. 输出写入 round-N.md（格式见 refs/state-schema.md），记录 instance_id
   c. Orchestrator 处理：overturn 检测、等价标注、antipattern 关联
   d. 若 verdict = 可执行 → 收敛！执行完成前必检清单，写 retrospective.md，移 done/
   e. 若有 contract_amendment_required → 先回写 contract.md 再继续
   f. Spawn 新 executor（prompt 模板见 refs/executor-prompt.md）
   f. Executor 修复后更新 attempts.md（格式见 refs/state-schema.md）
   g. plan_amendment_required 时先回写 plan 本体再改下游
   h. （可选）Continue 做 inner loop reviewer 验收
4. 超 max_outer_loops → 预算软停，询问用户
```

### Inner Loop

```
1. Executor 完成后，orchestrator 通过 Continue 续命同 reviewer instance
2. Reviewer 验收修复 → 通过则 Accepted，打回则继续修
3. 最多 3 次 Continue，超过则该轮失败 → 下一 outer loop
```

### 收敛后修订（用户外部输入）

收敛完成（retrospective 已写入 done/）后，用户可能提供外部输入（新的分析视角、遗漏的关键信息、对结论的质疑），需要重新评估已收敛的产物。

**触发条件**：用户提供的输入对已收敛结论构成实质性挑战——不是微调措辞，而是动摇核心判断或引入新的分析维度。

**流程**：

```
1. 将 done/<slug>/ 移回 active/<slug>/
2. 在 attempts.md 追加新 entry（标注 source: user_external_input）
3. Executor 根据外部输入修订产物
4. Spawn fresh Reviewer 审查修订后的完整产物（含新增内容）
5. 若通过 → 更新 retrospective，重新归档 done/
6. 若有阻断 → 进入标准 converge 主循环
```

**不计入 max_outer_loops 预算**：收敛后修订是对已完成产物的补充，不是原收敛的延续。但 retrospective 中必须记录修订的触发来源、新增轮次和结论变化。

### 收敛后设计审查（可选）

收敛完成后，Orchestrator 可选择触发一次**设计审查**（`refs/design-review-prompt.md`）：单轮、咨询式、不给阻断权重，产出 `design-review.md` 写入 `.converge/done/<slug>/`。

**触发条件**（满足任一即触发）：产物涉及 ≥ 3 个独立模块；或引入新目录结构/命名约定/跨组件接口；或定义了新的**系统边界**（如 scheduler↔Orchestrator 的职责划分、SKILL.md↔refs 的层次关系、两个子系统之间的协议边界）；或用户显式请求。**预算**：设计审查 Spawn 不计入 `max_outer_loops`，视为与收敛后修订同级的可选扩展操作。建议在产品涉及系统级设计时启用——单模块修复可跳过。

---

## Orchestrator 责任清单

1. **Spawn 真实性** — 失败时如实记 `orchestrator_self`，不掩盖
2. **overturn 判定** — 比较本轮 issue 与 attempts.md 已 Accepted 修复
3. **Type O 计数** — 同决策点推翻 ≥3 次 → 硬停
4. **Type R/F 等价标注** — 同源标注（语义判断）
5. **plan_amendment_required** — 先回写 plan 本体，再让 executor 改下游
6. **plan 漂移检测** — 每 5 轮 / 触 Type O 时报告用户
7. **预算追踪** — 触上限时问用户，不直接收敛
8. **instance_id + Continue 调度** — Spawn 后记录 id；inner loop 用 Continue 续命，禁止 Spawn 新 agent
9. **_orchestrator-state.md 维护** — 每完成一个动作即更新
10. **字段名映射** — reviewer 输出 `attribution` ↔ attempt log `Issue 归因`
11. **合同谈判编排** — Round 0 中依次 spawn Executor（提议合同）→ Reviewer（挑战）→ Executor（定稿），将终稿写入 contract.md
12. **Rubrics 维度选择** — 根据收敛对象类型从维度库中选取，写入 contract.md
13. **contract_amendment_required** — 先回写 contract.md 本体，再让 executor 按新 contract 调整。contract 演进导致的矛盾不计入 Type O
14. **收敛后修订评估** — 用户在收敛后提供外部输入时，判断输入是否构成实质性挑战。判断标准：是否引入新的分析维度、是否动摇已收敛的核心判断、是否修正了被遗漏的关键事实。微调措辞不触发修订。触发后在 retrospective 中记录修订来源和结论变化
15. **门控 L1 执行** — 在 Dynamic Workflows pipeline 的 phase 收口时，调用 L1 信号检测（`python scripts/l1_gate.py`），记录 pass/warn 结果
16. **门控 L2 触发决策** — 根据 `gate_l2_mode` 和 L1 结果决定是否 spawn L2 gate Reviewer
17. **门控发现处置** — 读取 gate_findings，按 severity 决策（info → 记录；risk → 记录 + 报警；critical_gap → 触发完整 converge），所有决策记录到 state 文件
18. **设计审查触发与报告** — 收敛后判断是否满足设计审查触发条件：≥3 模块；或新约定/接口；或系统边界；或评议前置自检 Q4/Q5 触发过 blocking（职责边界和命名一致性问题往往暗示更深层架构问题）；或用户显式请求。满足则 Spawn reviewer 产出 design-review.md，提取 highlights 报告给用户

---

## 宪法级约束 — Orchestrator 不可让渡的行为边界

> **本节约束需经人工审议后修改，不接受 Agent 自主变更。**
> 与 `refs/antipatterns.md`（可由 distill 脚本自动调整 status）不同，本节是 converge 的机制底线——违反这些条目意味着**明确规则被打破**（而非 plausible 认知偏误），检测方式是查表对照判据而非模式识别。即使将来 Orchestrator 不再违反它们，这些声明仍有解释性价值（"为什么零阻断是底线"）。任何修改都应有显式的人工决策记录。
>
> 以下检查清单主要面向**下一个 reviewer / 复盘者**，而非当前 orchestrator（它不会承认自己在违规）。

| # | 违规 | 底线 |
|---|------|------|
| 1 | "只剩 1 个低级阻断，不算阻断，直接收敛吧" | 严格首轮通过要求**零阻断**。b/c 类收敛需用户**显式确认** |
| 2 | "Executor 改了，看起来没问题了，不用 inner loop 验收" | 不验收 = 跳过验证环节，与收敛机制的设计意图冲突 |
| 3 | "budget 快到了，这轮就算通过了" | 预算软停**必须问用户**，不能自作主张 |
| 4 | "attempts.md 的历史 entry 我改一下让它更整洁" | **硬约束：历史 entry 不改写，只追加 annotation** |
| 5 | "用户没回复，我默认他同意继续" | b/c 类收敛和预算软停都需要**显式**用户确认 |
| 6 | "降级了但不用告诉用户吧，反正是内部细节" | 降级模式下结论可信度降低，**用户有权知道**。必须告知用户当前处于降级模式及影响 |
| 7 | "这次改动很简单，不用 spawn executor，我自己改就行" | Planner 亲自执行 = 破坏角色分离。简单任务也不是例外——边界一旦切开就会蔓延。**无论任务大小，Planner 不执行。**例外：若 Spawn 完全不可用，按附录 A.4 降级为 orchestrator_self，但**必须**标注降级模式并告知用户。 |

> 执行上述语义判定时，参考 `refs/orchestrator-guide.md` 中的操作步骤、偏见意识和边界场景处置。

---

## 收敛完成前必检

宣布收敛成立前，逐项确认：

- [ ] 最后一个 fresh reviewer verdict = `可执行`（或用户已显式接受 b/c）
- [ ] attempts.md 中所有 Accepted entry 无未解决的 Overturn 标注
- [ ] _orchestrator-state.md 的 current_phase 已标记为 completed
- [ ] **若收敛对象是代码**：所有测试通过（全绿）
- [ ] 所有 suggestion items 已处置（采纳/拒绝/延后，记录在 retrospective 中）
- [ ] retrospective.md 已写入 `.converge/done/<slug>/`
- [ ] `active/<slug>/` 目录已移至 `done/<slug>/`
- [ ] 用户已被告知收敛结果
- [ ] 若存在 contract.md：contract 中所有验收断言已被至少一轮 Reviewer 逐条验证
- [ ] 不存在未处理的 `contract_amendment_required: true` 标记
- [ ] 若触发了降级（orchestrator_self / inner_loop 降级）：用户已被告知降级模式及对结论可靠性的影响
- [ ] 若触发了设计审查：`design-review.md` 已写入，highlights 已报告用户，用户决策已记录

---

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_outer_loops` | 5 | 最大 outer loop 轮数（实证：收敛均在 2-3 轮完成；达到上限通常为振荡或 Reviewer 分歧，触发预算软停） |
| `max_inner_loops` | 3 | 同轮 inner loop 最大 Continue 次数 |
| `type_o_threshold` | 3 | Type O 触发硬停的推翻次数 |
| `type_r_threshold` | 5 | Type R 触发硬停的累计次数 |
| `plan_drift_check_interval` | 5 | plan 漂移检测间隔（轮） |
| `converge_dir` | `.converge/` | 收敛目录路径。可改为 `.meta/.converge/` 等自定义路径 |
| `gate_l1_interval` | 1 | 门控 L1 每 N 个 phase 触发 |
| `gate_l2_mode` | `signal` | 门控 L2 启动方式：`always` / `signal` / `adaptive` |
| `gate_l2_signal_threshold` | `warn` | 信号触发条件（当前仅支持 `warn`；`info`/`critical` 级别预留给后续 L1 信号扩展） |
| `gate_max_token_share` | 0.15 | 门控 token 预算占总预算比例上限 |

---

## Pilot 经验速查

1. **自举收敛可行**：convergence 自身 plan 可自举收敛（3 轮，4→1→0），但无法验证独立 executor 路径依赖
2. **Continue > Spawn 新 agent**：同 context 往返实现真正 inner loop
3. **antipattern 巡查有效**：over_compromise / minimum_patch 在 pilot 中被独立 reviewer 确认
4. **结构对标 > 内容对标**：reviewer 对"缺专节"的阻断力度大于"内容不完善"
5. **可用性是关键维度**："可直接使用"比"分析透彻"更影响 reviewer 的 verdict
6. **R0 Reviewer 挑战不可省**：自举收敛中 Executor 自选的概念列表漏了最关键的项。跳过 R0 挑战是自举偏差的主要来源
7. **用户外部输入可触发实质性修正**：收敛后用户提供的新分析视角（Bitter Lesson、做不到/做不好分类）产出了 R1/R2 Reviewer 均未能提供的洞察。用户角色不仅是最终确认者，还是关键的外部纠偏来源
8. **反面论证需限定范围**：合同中的反面论证断言必须限定"在 converge 目标场景内"，否则 Executor 会选择自己不参加的比赛来"承认"对手强（稻草人）

---

## 目录结构

```text
.converge/
├── tmp/                          # 中间产物（draft、临时脚本、调试输出等）。每轮结束后清理
├── active/<slug>/              # 进行中的收敛对象
│   ├── contract.md             # Round 0 合同终稿（可选）
│   ├── round-N.md              # 每轮 reviewer 输出 + orchestrator 处理记录
│   ├── attempts.md             # 跨轮 attempt log（含 overturn 链）
│   └── _orchestrator-state.md  # 抗 compact / 抗 session 切换
├── done/<slug>/                # 已收敛/已停止
│   ├── ... (上述所有文件)
│   ├── retrospective.md        # 复盘（必填）
│   └── design-review.md         # 设计审查报告（可选，触发时生成）
└── gate/<slug>/                # 门控产物（与 active/ 隔离）
    └── gate-findings.md         # L2 Reviewer gate_findings 汇总
```

> 格式规范见 `refs/state-schema.md`。slug 命名：`<YYYYMMDD>-<对象简述>`。
>
> 收敛后修订时：done/ → active/ → 修订 → 重新归档 done/。retrospective 追加修订记录，不覆盖原有内容。

---

## 层级模式（Planner → 多个 Orchestrator）

> 当项目规模超出单次收敛的合理范围时，可启用层级式并行收敛。详细协议见 `refs/decomposition-protocol.md`。

### 架构

```
Planner（主控）
  ├── 写 global-intent.md（全局意图摘要，30-50 行）
  ├── 分解任务为 N 个独立 scope
  ├── 划定边界（boundary assertions）
  ├── 分配预算
  ├── 并行调度子收敛 scope（集中调度优先）
  └── 分阶段管控 + 整合结果

子收敛 scope（逻辑上各自有 Orchestrator）
  ├── 读取 global-intent.md（残差连接，直接拿到顶层意图）
  ├── 独立运行完整 converge 循环（Reviewer ↔ Executor）
  ├── 受 boundary assertions 约束
  └── 每阶段汇报收敛状态
```

**两层是默认值**。默认采用 Planner 集中调度：主控直接 spawn 各 scope 的 Reviewer / Executor / Worker，并把子收敛视为逻辑 scope，而不是假设子 agent 一定能继续 spawn 后代 agent。只有确认子 agent 环境也暴露 Spawn / Continue 能力时，才启用 delegated hierarchical mode（子收敛 subagent 自己充当 Orchestrator）。深层（3+）需要 Planner justify（scope 粒度分析 + 并行收益估算）。详见 `refs/decomposition-protocol.md`。

### 启用条件

三个条件同时满足时启用：

1. 任务可分解为 ≥2 个互不干扰的独立 scope
2. 子任务间无实时数据依赖
3. 并行效率收益 > 分解 + 整合的开销

### 执行模型

分阶段（Phased）并行——不 fire-and-forget，每阶段结束有同步点：

```
Phase 1（3 轮/子收敛）→ 同步点 → Phase 2 → 同步点 → ... → 整合
```

同步点 Planner 做：看全局状态、调整预算、处理边界冲突、决定继续/ask user。

### 关键约束

- **Planner 不改被收敛对象**——Planner 可以写 `.converge/` 元数据、分解文件和状态文件；代码/文档主体改动由 Executor/Worker 完成，或在集成阶段明确委派执行
- **子收敛之间不通信**——通过 boundary assertions 和阶段汇报间接协调
- **子收敛内部运行标准 converge 语义**——无论集中调度还是 delegated mode，都使用同样的 Reviewer prompt、Executor prompt、state 管理和合同谈判

---

## 拆分文件索引

拼装 Reviewer/Executor prompt 或写 state 文件时，参考对应文件：

| 需求 | 文件 |
|------|------|
| Spawn reviewer 时拼装 prompt | `refs/reviewer-prompt.md` |
| Spawn executor 时拼装 prompt | `refs/executor-prompt.md` |
| 写 round-N.md / attempts.md / state / retrospective | `refs/state-schema.md` |
| 执行 overturn/Type R 判定、inner loop 验收等语义判断 | `refs/orchestrator-guide.md` |
| Round 0 合同谈判流程、contract.md 格式 | `refs/contract-negotiation.md` |
| Rubrics 维度库、评分标准、与 verdict 的关系 | `refs/rubrics.md` |
| 层级式并行收敛：分解协议、分阶段管控、边界仲裁 | `refs/decomposition-protocol.md` |
| 代码项目测试/lint 命令速查、发现流程、CI 信号源 | `refs/testing-toolbox.md` |
| 在 Dynamic Workflows 中插入质量门控：两级门检协议 + 触发决策 + 预算统筹 | `refs/quality-gate.md` |
| 收敛后设计审查：7 维骨架、单轮咨询式、不给阻断权重 | `refs/design-review-prompt.md` |
| Reviewer/Executor/Orchestrator 反模式巡查清单（动态注入，status 由 distill 维护） | `refs/antipatterns.md` |

---

## 附录 A · 框架适配

### A.1 Claude Code

| 能力 | 实现 |
|------|------|
| **Spawn** | `Agent` 工具（`subagent_type: general-purpose`），记录返回的 `agentID` |
| **Continue** | `SendMessage` 工具，`to` 参数为 `agentID` |
| **Identify** | 主对话即 orchestrator，无需自标识 |

**`/goal` 加速（v2.1.139+）**：Claude Code 的 `/goal` 命令可让单 agent 跨 turn 持续工作，直到用户定义的条件满足。在 converge 场景下：

- **可用场景**：Executor 在 inner loop 中持续修复直到 Reviewer 验收通过。设 `/goal attempts.md 中本轮所有 issue verdict = Accepted` 即可让 Executor 自动循环修复，无需 Orchestrator 手动每轮 prompt。
- **不可用场景**：不能替代独立 Reviewer。`/goal` 的评估器是小模型自检，不是独立全新上下文的对抗式审查。converge 的核心价值（独立交叉验证）必须通过 Spawn 实现。
- **层级模式**：子收敛 subagent 可用 `/goal "收敛完成，verdict=可执行"` 自动跑完整个 converge 循环，加速分阶段执行。

### A.2 opencode

| 能力 | 实现 |
|------|------|
| **Spawn** | 调用 `task` 工具，设置 `subagent_type: "general"`，prompt 参数传入自足的 reviewer/executor prompt |
| **Continue** | 通过 `task` 工具的 `task_id` 参数恢复同一个 subagent 会话 |
| **Identify** | 当前 agent 无标准 Identify，orchestrator 即主对话 |

**降级**：若版本不支持 Continue，inner loop 由 orchestrator 自身逐条验收（标注 `inner_loop: orchestrator_self`）。

**`/goal` 替代方案（截至当前版本）**：opencode 暂无内置 `/goal` 命令。若后续版本新增，用法与 A.1 中 Claude Code `/goal` 的说明一致。当前版本的替代路径：

1. **Orchestrator 手动驱动**（默认）：Orchestrator 在主循环中逐轮 Spawn Reviewer / Executor，这是 converge 的标准执行方式，无功能损失。
2. **Prompt 内嵌循环**：给 `task` subagent 的 prompt 中直接写入循环指令（如"重复以下步骤直到条件满足：先检查 X，若未满足则修改 Y，再检查 X"），让 subagent 在单次调用内自主迭代。适用于 inner loop 加速，但 subagent 内部无法 Spawn 独立 Reviewer（缺乏对抗式保证），retrospective 中需标注 `inner_loop: prompt_embedded`。

### A.3 codex (OpenAI Codex CLI)

优先按能力探测适配。若当前 Codex 环境暴露 `multi_agent_v1`，使用原生多 agent adapter：

| 能力 | 实现 |
|------|------|
| **Spawn** | `multi_agent_v1.spawn_agent`；Reviewer 使用 fresh self-contained prompt，Executor/Worker 必须明确 write scope |
| **Continue** | `multi_agent_v1.send_input(target=<agent_id>)` |
| **Wait** | `multi_agent_v1.wait_agent(targets=[...])` |
| **Close** | `multi_agent_v1.close_agent(target=<agent_id>)`；角色完成后关闭，避免悬挂 agent |
| **Identify** | 主会话即 Orchestrator；子 agent id 来自 Spawn 返回值 |

**Codex adapter 约束：**

1. **显式授权**：只有用户明确请求 converge / subagent / delegation，或当前 skill invocation 本身就是显式收敛工作流时，才 spawn agent。
2. **不默认嵌套 spawn**：不要假设 subagent 内部也能继续 spawn 后代 agent。层级模式优先采用主 Orchestrator 集中调度；只有确认子 agent 能力后才启用 delegated hierarchical mode。
3. **文件可见性保守处理**：不要假设一个 subagent 的文件修改会自动对另一个 subagent 可见。Executor/Worker 返回时必须列出 changed paths、diff 或摘要；Orchestrator 先审查并集成，再把必要 diff/产物路径传给 Reviewer 验收。
4. **模型继承优先**：不要设置 model override，除非用户明确指定模型，或 scope 有清晰的任务级理由。
5. **关闭已完成 agent**：Reviewer/Executor/Worker 完成角色后调用 Close；若关闭失败，在 state 中记录原因。

若未暴露 `multi_agent_v1` 但存在其他 Codex task/sub-agent 机制，则按该机制映射 Spawn / Continue / Wait；若 Continue 不可用，inner loop 降级同 A.2。若完全不支持 Spawn，按 A.4 降级。

**`/goal` 加速（可选）**：Codex 的 `/goal` 可作为 Executor inner loop 或子收敛执行的加速器，但不是基础依赖，且不能替代独立 Reviewer。使用 `/goal` 时仍需通过 Spawn 获得 fresh reviewer 做对抗式审查，并在 retrospective 中记录 goal-assisted execution。

### A.4 通用降级策略

框架**完全不支持** Spawn 时：

1. **Reviewer 降级**：Orchestrator 自身模拟 reviewer → 标注 `reviewer_backend: orchestrator_self`，retrospective 中分析自审偏差
2. **Executor 降级**：Orchestrator 自身执行修改，自觉遵守路径依赖防护
3. **Inner loop 降级**：Orchestrator 自身对照 reviewer 输出逐条验收

> ⚠️ 降级模式下结论可信度显著降低。Retrospective 必须讨论降级影响。

### A.5 适配新框架

三个问题完成适配：
1. 如何启动带全新上下文和自足 prompt 的 agent？（→ Spawn）
2. 能否向它发跟进消息且保有上下文？（→ Continue）
3. 如何引用该 agent 实例？（→ instance_id）
