---
type: design-review
object_slug: 20260621-mode-differentiation-and-fork-executor
reviewer_instance_id: ac22c551a7a7b6aa7
generated_at: 2026-06-21T00:00:00Z
mode: ultraverge (强制设计审查)
---

# Design Review · 模式分层 + Fork Executor

> 单轮咨询式、发散视角、**不阻断**收敛。findings 供用户决策，不自动转为 plan 改动。
> 收敛已完成（R1 可执行 + 盲审 pass）；以下为收敛后设计层观察。

## 7 维状态
全 7 维均 `concerns_found`（但 DR1/DR3/DR5/DR6/DR7 为"权衡型"，DR2/DR4 为承重型）。

## Highlights（报告用户，按重要性）

### H1 — fork 边界靠"封锁清单"而非生成式原则（DR4，承重）
**finding**：fork 边界由枚举例外维持（executor fork；R0/落地/所有 reviewer 不 fork），而非可推导的原则。计划采纳的理由"非独立角色可继承上下文"本身就是滑坡引擎——正是未来"落地 executor 只是机械套改动清单、也不需要独立性，为提速也 fork 它"会引用的论证。计划自己不得不把落地/R0 executor 作为显式例外**挖出来**，恰恰证明该原则不自我设限。
**why_it_matters**：独立性是 converge 存在的全部价值；靠封锁清单防御的边界会逐个"正当例外"地侵蚀。
**suggested_direction**：把边界改写为生成式——**仅当角色产出会被下游 fresh 独立 reviewer 机械复核时，才允许继承上下文**。收敛循环 executor 合格（inner-loop fresh reviewer 复核它）；落地/R0 executor 不合格（无下游 fresh 复核）。封锁清单即成为可推导的推论，未来任何"fork 角色 X"提案须先证明 X 受下游复核。

### H2 — 两 Part 的交互未被分析（DR1/DR2，承重）
**finding**：在 ≥2 轮的普通 converge 上，Part B fork executor（更易锚定）+ Part A 盲审 2→1（主要抗锚定兜底）+ A2 自主落地——**三个"独立性削弱器"在同一默认路径上叠加**，而各自安全裕度是孤立设定的。计划称两 Part"相互独立"，从未分析它们在同一次运行上的**交互**。
**why_it_matters**：盲审是"可能被 fork 锚定的收敛"与"自主写文件"之间唯一的 fresh-eyes 关口。三处同时减摩擦，恰好在计划新增自主性的地方集中了风险。
**suggested_direction**：把两 Part 的风险预算耦合——例如当某次运行**同时**用了 fork executor 且自主落地时，即便普通模式也保持盲审=2（或要求一轮 fresh 非 fork 验收）；并让不变量 #8 的 pilot 测**组合路径**，而非孤立的 fork-vs-fresh。

### H3 — fork 是治理层里的"模型经济学补丁"（DR7/DR5/DR6，Bitter Lesson）
**finding**：以 CONSTITUTION 第一部 Bitter Lesson+Occam 透镜看，fork 优化的是"重读开销"——而更长上下文/更便宜 token 的模型会抹平它（计划 张力3 自承 token 节省有条件且在收缩）；但其独立性侵蚀成本是结构性的、不随模型变便宜而缩小，且只有一个框架（Claude Code）真正使用它。新增的永久治理面（executor_context 字段、§1-§7 重申、探测/降级、pilot harness）由每框架每读者承担，收益只归一个框架。
**why_it_matters**：第一部正警告补丁"腐化在不变的机制里"。收益被长上下文模型抹平、成本却永久的特性，不该编码进受宪法保护层。
**suggested_direction**：把 fork 当作**可丢弃的优化层**而非治理级角色变更——用 pilot(#8) 把关 + 绑定一个随上下文经济学触发的 sunset/重评条件；SKILL/CONSTITUTION 用框架与经济学中立的措辞描述角色模型，把 fork 限制在 framework-adapters 内作为探测式优化。

## 处置建议（Orchestrator → 用户）
三条均为设计层、修复成本高于代码 bug，按 design-review 协议**不自动转 blocking**。建议用户在 Part B 落地前决策：H1（生成式边界）与 H2（耦合风险预算）值得在 plan 落地前折入；H3 是更长期的治理哲学取向。
