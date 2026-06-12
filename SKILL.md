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
                可选前置阶段         单轮主观 verdict  仅 conceptual/arch   ultraverge:
                对齐"什么算完成"     一次写回           阻断时升级多轮收敛   全量（见执行流程）
                + 定义 Rubrics 维度
                                    ↖─────────────────────────────────────────────╳
                                      需重新设计 → 用户决定：重写/缩小范围/主观接受
```

- **前置条件**：有可审查的产物（plan 文件 / 代码项目 / 文档等），且产物已完成初稿
- **后继条件**：收敛达成后，产物可安全进入下一阶段（执行、提交、部署）
- **不适合**：单次快速审查、日常代码 review、lint 级别的检查——这些用更轻量的 review 技能
- **可组合**：如果存在完整的开发工作流型 SKILL（如 Dynamic Workflows 的 pipeline/parallel 编排），converge 可以作为其中的**质量门控**插入——在 phase 交接处插入独立的"方向性审视"，让指挥部的决策在行动前暴露盲点。门控分两级：L1 轻量信号检测（非 LLM 脚本，零 token 成本）和 L2 单轮对抗审查（按需启动）。详见 `refs/quality-gate.md`

---

> 设计原则、Orchestrator 行为边界、治理文档清单、修改程序详见 `CONSTITUTION.md`。
> 优先级与冲突裁决规则详见 `CONSTITUTION.md` 开头段落。

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

### 模型分层

Executor 可降档（模型档位下调）至该家族低档执行，**仅当同时满足以下三条件**：

- (a) 执行合同已通过确定性检查——指令含逐字文本或等价的零歧义规格；
- (b) 用户显式授权或计划明示——默认 inherit（继承主对话模型），**不静默降档**。本条**收紧并跨框架推广**附录 A.3 codex 约束 #4（模型继承优先）：Executor 模型档位选择场景中二者冲突时以本节为准，A.3 #4 继续管辖其余 model override 情形；
- (c) 降档时验收**必须**包含确定性核对（diff / grep / 测试 / 计数），不得仅语义验收。

**不降档角色**：Reviewer、Orchestrator、设计审查（判断力密集）。确定性核对类子任务（清点、diff/grep 核对、行数统计——判别准绳：任务存在客观判准、其结果可被机械复核）可用低档。未列出的角色（如层级模式的 Worker、仲裁 agent、L2 gate Reviewer）默认 inherit。

档位经由各框架 Spawn 的模型选择参数实现（如 Claude Code Agent 工具的 `model` 参数）；框架不支持模型选择时视同 inherit。降档（模型档位下调）与本 SKILL 既有的"降级"（能力/流程降级，见附录 A.4）语义无关，互不触发对方的义务。档位取值与三条件核对结果须记入 attempt log。

家族档位对照见 `refs/model-tiers.md`（数据层，随模型换代更新，无需修宪）。

---

## 终止状态与收敛判定

| 终止类型 | 判据 | 用户确认 | 产物要求 |
|----------|------|---------|---------|
| **终止-a 严格首轮通过** | fresh reviewer 首次审查 verdict = `可执行`，零阻断 | 无需 | 写 retrospective.md，移 done/ |
| **终止-b 渐近通过** | blocking_issues 单调下降 + 剩 ≤1 个无争议低级项 | 用户显式确认 | 写 retrospective.md，移 done/ |
| **终止-c 主观接受** | 未达 a/b，但用户明确说"够了，就这样" | 用户显式确认 | 写 retrospective.md，移 done/ |
| **预算软停**（无终止类型对应） | 达预算上限（默认 5 轮），用户决定不续费 | 用户确认不续费 | retrospective.md 注明"未收敛但用户接受" |
| **振荡硬停**（无终止类型对应） | 触 Type O（推翻≥3）或 R（重复≥5） | 无需 | retrospective.md 填病因 + 建议 |

终止-a 是默认目标。b/c 需用户显式确认。达预算上限后用户接受 → 预算软停；未达上限用户主动接受 → 终止-c。

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

**默认入口**：**从评议开始。** 绝大部分审查需求在第一轮评议中就能得到有效反馈。仅当评议发现 conceptual 或 architectural 级别的阻断、且单轮修复后需要 independent verification 时，才升级为完整收敛。完整收敛很少超过 3 轮。

评议的前置自检（5 个设计层问题，见 `refs/reviewer-prompt.md`）覆盖了产物身份、边界诚实、数据纯度、职责边界和命名一致性——这些是方向性问题，通常能在 1 分钟内判定。Q1-Q3 与设计审查的 DR1/DR4/DR6 为分层审查（前置自检做 binary check，设计审查做 dimensional assessment）。Q4/Q5 触发 blocking 时，Orchestrator 应评估是否触发设计审查——职责边界和命名一致性问题往往暗示更深层架构问题。更深层的架构维度（可维护性、可扩展性、残留冗余等）留给收敛后设计审查处理。

**判别原则：**

1. 先看时态——事前 = 评议，事后 = 审计，事中 = 收敛
2. 事中再看规模——单 scope = 单层收敛，多独立 scope = 层级收敛
3. 默认评议——仅在评议 verdict 含 conceptual/architectural 阻断时升级为完整收敛

> **Ultraverge**：评议的"全量变体"（扩域 + 多 Reviewer + 强制设计审查），详见执行流程专节。

> **收敛后设计审查**（`refs/design-review-prompt.md`）：事后、不写回、咨询式——时态属于审计，但判断维度不同（7 维 vs P0-P3对齐率），是审计的一个可选子模式。在产物收敛完成后触发，产出 advisory findings 供用户决策。

---

## 执行流程

### Ultraverge 路径（仅 `ultraverge` 关键词触发）

对安全性或稳定性有极端要求的产物（核心 SKILL 定义、宪法文档、基础架构 plan），用户可使用 `ultraverge` 关键词触发全量流程：

```
ultraverge → 评议（扩域至 DR 7 维 + 前置自检 5 问，≥ultraverge_min_reviewers 并行独立 Reviewer）
          → 评议 verdict = 可执行 → 跳过完整收敛 → 强制设计审查
          → 评议 verdict ≠ 可执行 → 完整收敛 → 强制设计审查
```

与默认路径的差异：
- **评议**：Reviewer prompt 额外注入设计审查的 7 维骨架（DR1-DR7），不做"仅查方向性问题"的裁切。**至少 Spawn `ultraverge_min_reviewers`（默认 3）个独立 Reviewer 并行审查**——这是 ultraverge 与普通评议的关键区分：普通评议允许单 Reviewer 快速对齐，ultraverge 要求多条独立视角以确保事实前提验证（如代码现状审计）和盲区覆盖（如 Bitter Lesson 冲突、跨治理域打包等问题往往只有少数 Reviewer 能捕获）。
- **并行裁决规则**：`ultraverge_min_reviewers` 条 verdict 全部一致 → 采纳。存在分歧时：
  - 多数方向 vs 少数方向 → Orchestrator 按多数方向推进，**但**：若少数派的阻断 issue severity 为 `conceptual` 或 `architectural`，Orchestrator **必须**升级为完整收敛（对应宪法约束 §1：不能以多数决跳过深层阻断）
  - 裁决规则仅管辖 ultraverge 的 spawn 约束 + 并行收敛语义，不约束宿主项目自有的评议汇总机制
- **降级路径**：若因 token 预算、API 不可用、并发限制等原因无法 spawn 满 `ultraverge_min_reviewers` 个 Reviewer：
  - 实际 spawn 数 ≥2 且 verdict 一致 → 降级为普通评议模式，Orchestrator 标注 `degraded_from: ultraverge` 并告知用户
  - 实际 spawn 数 <2 或 verdict 不一致 → 中止，告知用户原因，由用户决定是否降级为普通评议或稍后重试
- **完整收敛**：若评议 verdict = 可执行 → 跳过（评议已在扩域下审查完毕，完整收敛新增发现概率极低，只增成本）；若 verdict ≠ 可执行 → 标准流程（Round 0→多轮→收敛）
- **收敛后设计审查**：**强制触发**——跳过常规触发条件（模块数/新约定/系统边界）的判断，直接执行

仅在用户显式使用 `ultraverge` 关键词时触发。**触发边界（明线规则）**：

- **修改对象涉及宪法/治理文档 → 必须 ultraverge**（≥3 Reviewer + 收敛 + 设计审查）
- **修改对象不涉及宪法/治理文档 → 标准评议**（verdict 驱动，单轮写回）

> **"治理文档"判据**：对 Agent 行为有规范性约束力的文件。项目治理文档由项目入口文档（AGENTS.md / CLAUDE.md 等）定义；本 SKILL 自身的治理文档清单见 `CONSTITUTION.md` 第三部。边界情形按最高强度处理。

### 默认入口：评议

首次审查一律使用评议模式（单轮、主观 verdict、一次写回；ultraverge 关键词除外，见上方 Ultraverge 路径）。评议的 Reviewer prompt 与完整收敛的 Round 1 相同。评议完成后 Orchestrator 根据 verdict 决策：

- verdict = 可执行 → 收敛完成，归档 done/
- verdict = 阻断需修复 + 阻断为 implementation/structural → Executor 修复，评议模式再走一轮
- verdict = 阻断需修复 + 阻断为 conceptual/architectural → **升级为完整收敛**（下方主循环）
- verdict = 需重新设计 → 不进入修复循环。向用户报告产物存在方向性缺陷，由用户决定：重写产物后重新评议、缩小范围后重新评议、或走主观接受程序

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
   c+1. **角色边界自检**（详见责任清单 #3）：
        - 本轮动作是否仅限于循环管理 + 语义判定？
        - 若即将对产物做任何直接修改 → 停止，跳至步骤 f（Spawn Executor）
        - 将自检结果记录到 _orchestrator-state.md（boundary_check: pass | violated）
        - 若 violated 且已执行修改（guard step 被跳过时的补救路径）→ 在 attempts.md 以 [Orchestrator Detection] annotation 标注 source: orchestrator_self，告知用户降级影响
   c+2. **意图漂移条件注入**（详见责任清单 #19）：
        - 若存在 escalated_issues 或 contract_amendment_required 反复出现（≥2 次）→ 从 _orchestrator-state.md 提取 progress_summary 摘要，在下一轮 reviewer prompt 中注入 <drift_context> 块
        - 处理 reviewer 输出时检测 drift_detected: true 标记，若有 → 记录到 rule_frequency
   c+3. **规则触发记录**（详见责任清单 #19）：
        - 在步骤 c/c+1 更新 boundary_check 时顺带更新 rule_frequency 的 boundary_guard / reviewer_boundary_audit 触发状态
        - gate_l1 / design_review_trigger 在对应事件发生时更新
   d. 若 verdict = 可执行 →
        d1. 若本次收敛经历 ≥2 轮 outer loop → 进入盲审复核（见下方"盲审复核"小节）
        d2. 若本次收敛经历 = 1 轮 → 直接收敛
         收敛！执行完成前必检清单，写 retrospective.md，移 done/
         d3. 若用户后续要求落地执行（将方案改动清单写入目标文件）→ Orchestrator 按 `refs/orchestrator-guide.md` §落地执行编排 流程 spawn executor，使用 `refs/executor-prompt.md` Plan-Execution 模板
    e. 若有 contract_amendment_required → 先回写 contract.md 再继续
    f. Spawn 新 executor（prompt 模板见 refs/executor-prompt.md）
    g. Executor 修复后更新 attempts.md（格式见 refs/state-schema.md）
    h. plan_amendment_required 时先回写 plan 本体再改下游
    i. Continue 做 inner loop reviewer 验收（宪法第二部 #2：不可跳过；Continue 不可用时按附录 A.2/A.4 降级为 orchestrator 逐条验收并标注）
4. 超 max_outer_loops → 预算软停，询问用户
```

### 盲审复核（Blank-Slate Recertification）

当收敛经历 ≥2 轮 outer loop 后签发"可执行"，在 retrospective 写入前增加盲审复核 gate：

```
verdict=可执行 且 ≥2 轮 →
  spawn 盲审 Reviewer（不读 attempts.md，prompt 变体见 refs/reviewer-prompt.md §盲审复核变体）
  ├ 零阻断 → 真正收敛，retrospective 记 blind_recheck: pass
  └ 有阻断 → findings 作为 escalated_issues（BR- 前缀独立注入块）注入主循环
             → Executor 修复 → 下一 outer loop Spawn fresh Reviewer 验收 → 再次可执行 → 再次盲审
             → 超 max_blind_rechecks → 预算软停，问用户
  若终止-c（主观接受）+ 盲审失败 → 提示用户，用户可确认跳过（retrospective 记 blind_recheck: waived）
```

**关键约束**：
- 盲审在 `active/` 内进行，不触发 done/→active/ 回流
- 盲审 Reviewer prompt 变体定义见 `refs/reviewer-prompt.md`
- 盲审 findings → attempts.md 字段映射和 → escalated_issues 传递格式见 `refs/state-schema.md`
- 归因协议：盲审只发现（attribution: pending），主循环 Reviewer 补归因（plan_defect / executor_limit）
- pending 归因不得跨过下一主循环轮存活
- 标注口径：`blind_recheck: pass | fail | waived`，永不升格终止类型
- 盲审失败后的修复轮次**共享原 max_outer_loops**，不自动扩

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

**触发条件**（满足任一即触发）：产物涉及 ≥ 3 个独立模块；或引入新目录结构/命名约定/跨组件接口；或定义了新的**系统边界**（如 scheduler↔Orchestrator 的职责划分、SKILL.md↔refs 的层次关系、两个子系统之间的协议边界）；或用户显式请求。**预算**：设计审查 Spawn 不计入 `max_outer_loops`，视为与收敛后修订同级的可选扩展操作。建议在产物涉及系统级设计时启用——单模块修复可跳过。

---

## Orchestrator 责任清单

**每轮必做** ——
1. **Spawn 真实性** — 失败时如实记 `orchestrator_self`，不掩盖
2. **overturn 判定** — 比较本轮 issue 与 attempts.md 已 Accepted 修复
3. **角色边界自检** — 每轮处理完 reviewer 输出后、执行任何修复动作前，确认：本次动作范围是否为"循环管理 + 语义判定"？若涉及产物修改且尚未 spawn Executor → 必须先 spawn Executor。违反时必须在 _orchestrator-state.md 记录 boundary_check: violated，在 attempts.md 以 [Orchestrator Detection] annotation 标注 source: orchestrator_self，告知用户降级模式及对结论可靠性的影响。Round 0 和 inner loop 中存在同构的边界违反窗口，当前 guard step 覆盖主循环（最频发场景），其余窗口依靠本责任清单条目提醒
4. **Type O 计数** — 同决策点推翻 ≥3 次 → 硬停
5. **Type R/F 等价标注** — 同源标注（语义判断）
9. **instance_id + Continue 调度** — Spawn 后记录 id；inner loop 用 Continue 续命，禁止 Spawn 新 agent
10. **_orchestrator-state.md 维护** — 每完成一个动作即更新

**条件触发** ——
5. **plan_amendment_required** — 先回写 plan 本体，再让 executor 改下游
6. **plan 漂移检测** — 每 5 轮 / 触 Type O 时报告用户
7. **预算追踪** — 逐轮递增计数由主循环结构保证；本条规范触上限时必须问用户的行为（呼应宪法第二部 #3）
10. **字段名映射** — 写入 attempt log entry 时执行：reviewer 输出 `attribution` ↔ attempt log `Issue 归因`
13. **contract_amendment_required** — 先回写 contract.md 本体，再让 executor 按新 contract 调整。contract 演进导致的矛盾不计入 Type O
14. **收敛后修订评估** — 用户在收敛后提供外部输入时，判断输入是否构成实质性挑战。判断标准：是否引入新的分析维度、是否动摇已收敛的核心判断、是否修正了被遗漏的关键事实。微调措辞不触发修订。触发后在 retrospective 中记录修订来源和结论变化
15. **门控 L1 执行** — 在 Dynamic Workflows pipeline 的 phase 收口时，调用 L1 信号检测（`python scripts/l1_gate.py`），记录 pass/warn 结果
16. **门控 L2 触发决策** — 根据 `gate_l2_mode` 和 L1 结果决定是否 spawn L2 gate Reviewer
17. **门控发现处置** — 读取 gate_findings，按 severity 决策（info → 记录；risk → 记录 + 报警；critical_gap → 触发完整 converge），所有决策记录到 state 文件

**Round 0 前置** ——
11. **合同谈判编排** — Round 0 中依次 spawn Executor（提议合同）→ Reviewer（挑战）→ Executor（定稿），将终稿写入 contract.md
12. **Rubrics 维度选择** — 根据收敛对象类型从维度库中选取，写入 contract.md

**收口必做**（含逐项执行"收敛完成前必检"）——
18. **设计审查触发与报告** — 收敛后判断是否满足设计审查触发条件：≥3 模块；或新约定/接口；或系统边界；或评议前置自检 Q4/Q5 触发过 blocking（职责边界和命名一致性问题往往暗示更深层架构问题）；或用户显式请求。满足则 Spawn reviewer 产出 design-review.md，提取 highlights 报告给用户

**条件触发** ——
19. **意图漂移检测 + 规则触发记录** — (a) 意图漂移：当 escalated_issues 存在或 contract_amendment_required 反复出现（≥2 次）时，从 _orchestrator-state.md 提取 progress_summary 摘要注入下一轮 reviewer prompt 的 `<drift_context>` 块；reviewer 通过 drift_detected: true 标记反馈漂移。与 #6 的关系：#6 是 Orchestrator 第一方循环内检测（plan 内容偏移，每 5 轮/触 Type O），本条是 Reviewer 独立第三方产物-合同对齐检测（条件注入），互补而非重叠。(b) 规则触发记录：在步骤 c/c+1 更新 boundary_check 时顺带更新 rule_frequency 的 boundary_guard / reviewer_boundary_audit 触发状态；gate_l1 / design_review_trigger 在对应事件发生时更新。rule_frequency 字段格式和规则 key 注册表见 `refs/state-schema.md`。不新增独立循环步骤。retrospective 中必须包含对追踪机制执行成本的评估（约 1 句话）；当被追踪规则总数降至 2 条以下时，必须显式评估追踪机制是否仍有必要
  20. **盲审复核编排** — 当收敛经历 ≥2 轮 outer loop 且 verdict=可执行时：(a) 判断是否满足盲审触发条件（≥2 轮）；(b) Spawn 盲审 Reviewer（使用 refs/reviewer-prompt.md 盲审变体 prompt）；(c) 若盲审有阻断，将 findings 以 BR- 前缀独立注入块格式转为 escalated_issues，注入下一主循环轮；(d) 在 attempts.md 中为盲审 findings 创建 entry（source: blind_recheck, attribution: pending）；(e) 检查 pending 归因是否在下一主循环轮落定（硬过期）；(f) 维护 retrospective 的 blind_recheck 标注（pass / fail / waived）。操作指引见 `refs/orchestrator-guide.md`
  21. **后收敛执行编排** — 方案收敛后用户要求落地执行时：(a) Spawn executor（使用 refs/executor-prompt.md Plan-Execution 模板，fresh-context spawn）；(b) **不得直接编辑文件**（宪法硬约束 #7 在落地阶段同样适用）；(c) 记录 executor instance_id 到 retrospective 或落地日志条目（客观证据）；(d) 核对改动清单项数与 executor 报告的已修改文件数一致。操作指引见 `refs/orchestrator-guide.md` §落地执行编排

---

> Orchestrator 不可让渡的行为边界详见 `CONSTITUTION.md` 第二部。

---

## 收敛完成前必检

宣布收敛成立前，逐项确认：

- [ ] 最后一个 fresh reviewer verdict = `可执行`（或用户已显式接受 b/c）
- [ ] attempts.md 中所有 Accepted entry 无未解决的 Overturn 标注
- [ ] _orchestrator-state.md 的 current_phase 已标记为 completed
- [ ] 每轮 boundary_check 均为 pass，或违反已记录并告知用户
- [ ] **若收敛对象是代码**：所有测试通过（全绿）
- [ ] 所有 suggestion items 已处置（采纳/拒绝/延后，记录在 retrospective 中）
- [ ] retrospective.md 已写入 `.converge/done/<slug>/`
- [ ] `active/<slug>/` 目录已移至 `done/<slug>/`
- [ ] 用户已被告知收敛结果
- [ ] 若存在 contract.md：contract 中所有验收断言已被至少一轮 Reviewer 逐条验证
- [ ] 不存在未处理的 `contract_amendment_required: true` 标记
- [ ] 若触发了降级（orchestrator_self / inner_loop 降级）：用户已被告知降级模式及对结论可靠性的影响
- [ ] 若触发了设计审查：`design-review.md` 已写入，highlights 已报告用户，用户决策已记录
- [ ] 若本次收敛中 Executor 使用了降档（low）：验收已包含确定性核对，档位取值与三条件核对结果已记入 attempt log
- [ ] 若本次收敛经历 ≥2 轮：盲审复核已完成（verdict=可执行 或 blind_recheck: waived），retrospective 中已记录 blind_recheck 字段

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
| `ultraverge_min_reviewers` | 3 | ultraverge 评议阶段最少并行 Reviewer 数（默认 3，来自 ≥3 自动收敛阈值。可随实证数据调整） |
| `executor_model_tier` | `inherit` | Executor 模型档位。`inherit` = 继承主对话模型；`low` = 该家族低档（对照表见 `refs/model-tiers.md`）。仅当「模型分层」小节三条件满足时可设 `low`。初始策略，随实证数据调整 |
| `max_blind_rechecks` | 2 | 盲审复核最大次数（独立于 max_outer_loops）。盲审失败后修复轮次共享 max_outer_loops |

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
| Executor 降档时选择各家族低档 | `refs/model-tiers.md` |

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
