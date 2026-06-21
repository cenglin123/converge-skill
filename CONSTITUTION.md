# Converge SKILL 宪法

> 本文件是 converge SKILL 的最高设计治理文档——定义"SKILL 该长什么样、该包含什么"的宪法级判据；机制描述以 SKILL.md 为准，宪法约束以本文件为准。本文件的权威源于用户对 ultraverge 收敛结果的批准，而非内容的生成来源。
> 运行时机制冲突时以 SKILL.md 为准（运行时依赖优先于设计参考）；冲突本身即触发修宪程序，修正本文件与 SKILL.md 对齐。修改本文件需经 ultraverge 流程 + 人工审议确认。

---

## 第零部 · 本宪法的目的

本宪法不约束 converge 的用户（何时使用、对什么产物使用），只约束 converge SKILL 的**结构和演化方式**。具体而言：

- 定义 SKILL 自身演化的设计判据（第一部）
- 划定 Orchestrator 不可让渡的行为底线（第二部）
- 列明受宪法保护的文件范围（第三部）
- 规定修改宪法内容的程序（第四部）

---

## 一、宪法级设计原则

> 以下两条是本 SKILL 的最高判据。任何对 SKILL.md 或 refs/ 的修改，必须先通过这两条的自检（详见 `refs/orchestrator-guide.md` §〇 宪法自检），否则不考虑执行。

本 SKILL 的自身演化受两条宪法级原则约束——它们不是运行时规则，而是**本 SKILL 该长什么样、该包含什么**的设计判据：

| 原则 | 判据 | 应用实例 |
|------|------|---------|
| **Bitter Lesson** | 这东西是通用机制还是针对当前模型的补丁？机制硬编码，补丁做成 compiled 产物 | 三角色/对抗循环硬编码；反模式清单挂在 retrospective 上、由 distill 脚本维护 status |
| **Occam** | 这东西解决什么具体问题？不解决具体问题的实体删除，git log 是考古层 | 三层物理分离（不让会变化的知识腐化在不变的机制里）；章程瘦身（引用表替代重复副本） |

> 新增文件/规则/字段时，两条原则同时适用：先问 Bitter Lesson（硬编码还是 compiled？），再问 Occam（必要还是多余？）。

---

## 二、宪法级约束 — Orchestrator 不可让渡的行为边界

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
| 7 | "这次改动很简单，不用 spawn executor，我自己改就行" | Planner 亲自执行 = 破坏角色分离。简单任务也不是例外——边界一旦切开就会蔓延。**无论任务大小，Planner 不执行。**例外：若 Spawn 完全不可用，按 refs/framework-adapters.md §A.4 降级为 orchestrator_self，但**必须**标注降级模式并告知用户。 |

> 执行上述语义判定时，参考 `refs/orchestrator-guide.md` 中的操作步骤、偏见意识和边界场景处置。

> **授权粒度澄清**（呼应 #3/#5；记录见 `GOVERNANCE-DECISIONS.md` GD-1）：用户指令"走 converge 并执行"授权 (a) converge 推进至**默认**预算上限，(b) 收敛后进入落地执行。该指令**不**授权：预算扩展（budget_extension）、模式切换接受、终止-b/c。三者各需**新鲜、具体、可审计**的显式确认；超默认预算的续跑须写入关联真实 BLOCK decision 事件的 extension 令牌（含用户原话）。预算执行由 `scripts/budget_gate.py` 在 spawn 前裁决，但本条授权底线属宪法约束，不因执行机制变化而改变。

---

## 三、治理文档清单

以下文件对 Agent 行为有规范性约束力，修改须走 ultraverge：

- `CONSTITUTION.md` — 本文件（自指保护）
- `SKILL.md` — 机制定义
- `refs/reviewer-prompt.md` — Reviewer prompt 模板
- `refs/executor-prompt.md` — Executor prompt 模板
- `refs/state-schema.md` — State & log 格式规范
- `refs/orchestrator-guide.md` — Orchestrator 语义判定指南
- `refs/contract-negotiation.md` — Round 0 合同谈判协议（定义 Reviewer/Executor 行为边界）
- `refs/decomposition-protocol.md` — 层级收敛协议（定义系统架构级约束）
- `refs/design-review-prompt.md` — 设计审查 prompt 模板（Reviewer 行为定义）

以下文件不受宪法保护：

- `refs/antipatterns.md` — 反模式注册表（status 由 distill 脚本自动维护）
- `refs/rubrics.md` — Rubrics 维度库（新增维度由 contract 谈判驱动）
- `refs/testing-toolbox.md` — 测试工具速查（按需追加）
- `refs/quality-gate.md` — 门控协议（composability 扩展，非核心 converge 治理）

> 不在上述清单中的新增 refs/ 文件默认不受宪法保护。若需保护，通过修宪程序追加。

---

## 四、修改程序

1. 任何对治理文档清单中文件的修改，须先写入计划文件
2. 计划走 ultraverge 流程（≥3 Reviewer + 收敛 + 设计审查）
3. 收敛通过后，由人工确认提交
4. 若 SKILL 仓库有 pre-commit hook 要求 `AGENT_USER_APPROVED_COMMIT=1`，则遵循；否则由 Orchestrator 在收敛完成前必检中手动验证
