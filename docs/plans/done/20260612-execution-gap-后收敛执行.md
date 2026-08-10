---
type: plan
status: active
created: 2026-06-12
scope: converge 后收敛执行阶段缺口（最小方案）
governance: true
note: 为 SKILL.md 主循环加落地执行路由锚点 + SKILL.md 责任清单加执行编排条目 + executor-prompt 模板变体 + orchestrator-guide 操作指引
related:
  - "SKILL.md"
  - "refs/executor-prompt.md"
  - "refs/orchestrator-guide.md"
---

# 后收敛执行约束（最小方案）

## 摘要

20260612-blind-recheck 落地时，Orchestrator 声称 spawn executor 但实际自己编辑文件——这是角色分离违反的实证。最小修复：在 SKILL.md 加一条落地时的硬约束（"必须 spawn executor，不得直接编辑"），配一个 executor-prompt 模板变体和 orchestrator-guide 操作指引。不引入 scope 拆分协议、确定性核对协议、补丁轮等机制。

## 问题陈述

converge 的流程止步于 verdict=可执行 + retrospective 归档。方案收敛后的文件落地没有任何流程定义，Orchestrator 进入无约束状态。

20260612-blind-recheck 落地时，Orchestrator 违反宪法硬约束 #7，自己直接编辑文件。这是已观测到的故障。

承认一点：这个故障也可以用另一个假说解释——"Orchestrator 只是违反了已有的 #7，加一条流程锚点提醒就够了，不需要新协议"。两个假说都成立，但**只对假说 1（角色违反）有实证**。假说 2（多文件编排失败）从未被观测到——没有案例表明 Orchestrator 在落地时遗漏文件、搞乱依赖、或因缺少确定性核对而出错。为未观测到的问题设计机制是过早的。

## 约简论证

原提案包含 scope 拆分协议、确定性核对协议、补丁轮（bounded 1 轮）、max_execution_rounds 参数、并行上限、角色边界强制机制。全部砍掉。

理由：

1. blind-recheck 复盘揭示的问题是"Orchestrator 没有被强制 spawn executor"，不是"编排失败"。从 block loop 的约简逻辑看：block loop 是一个无限循环机制，最终被约简为一个 bit（验证 / 拒绝）。落地执行的编排问题同样——如果从未观测到编排失败，就不需要编排协议。
2. scope 拆分、并行上限——没有证据表明 Orchestrator 在落地时处理不了多文件。等有了失败案例再设计。
3. 确定性核对——无编排失败实证，但清单项数核对是近零成本的一致性校验，与 converge 其他确定性核对义务对齐。仅保留清单项数 vs 实改文件数核对（executor 已在输出中列出修改文件），不引入 grep/diff/补丁轮。
4. 补丁轮——为"核对发现遗漏"设计的补救机制，但前提（核对步骤）本身就没有实证基础。
5. 角色边界强制机制——self-report `boundary_check: violated` 的价值存疑（违反者不会主动标注）。但 instance_id 留痕保留：executor 是否被 spawn 是客观事实（有/无 instance_id），非 self-report，可作为违规检测证据。

如果未来落地执行中出现编排问题，再针对性增加机制。现在加的是最小锚点。

## 最小方案

4 处改动：

1. **SKILL.md 主循环（锚点）** — 在主循环 step d 之后（`移 done/` 之后）增加路由指令：收敛后若用户要求落地执行，Orchestrator 按 `refs/orchestrator-guide.md` §落地执行编排 流程 spawn executor 执行文件改动（使用 `refs/executor-prompt.md` Plan-Execution 模式）。**这是从主循环体到落地流程的唯一路由锚点。**

2. **refs/executor-prompt.md** — 增加"Plan-Execution 模式"小节，与现有 issue-fix 模式并列。模板必须覆盖以下部分：
   - IF 条件：Orchestrator 要求执行改动清单。**显式声明：这是一个 fresh-context spawn，不是继续 converge 循环**
   - Required reading：仅方案文件路径（executor 直接读取 plan 文件中的改动清单表）。**不读 attempts.md、round 文件或 contract.md——此模式独立于 converge 循环**
   - Task：按改动清单逐项执行目标文件的修改
   - Output format：列出已修改文件 + 每文件变更摘要
   - Hard disciplines：不跳过清单项；失败即停止并报告；不修改改动清单范围外的文件
   - 注：此模式独立于 converge 循环，不要读取 attempts.md、round 文件或 contract.md

3. **refs/orchestrator-guide.md** — 增加"落地执行编排"小节，与"收敛后修订"、"盲审复核编排"同级。内容：触发条件（用户要求落地）→ 读取方案改动清单 → spawn executor（使用 plan-execution 模板）→ **硬约束：落地执行涉及文件改动时必须 spawn executor，不得直接编辑（宪法硬约束 #7 在落地阶段同样适用）** → 等待 executor 完成后报告用户 → **记录 executor 的 instance_id 到 retrospective.md 或落地日志条目（客观证据，非 self-report）** → **清单项数 vs 实改文件数核对：executor 输出列出已修改文件，Orchestrator 交叉核对数量与改动清单一致**。

4. **SKILL.md Orchestrator 责任清单（条件触发类）** — 增加 1 条"后收敛执行编排"：落地时 spawn executor + 使用 plan-execution 模板。

## 文件改动清单

| 文件 | 改动 |
|------|------|
| `SKILL.md` | 主循环 step d 后 +1 条路由锚点（落地执行→orchestrator-guide §落地执行编排） |
| `refs/executor-prompt.md` | +1 小节（plan-execution prompt 模板，含 fresh-context 声明 + 5 部分骨架 + 不读 attempts 注） |
| `refs/orchestrator-guide.md` | +1 小节（落地执行编排，含硬约束 + instance_id 留痕 + 清单项数核对，约 15 行） |
| `SKILL.md` | Orchestrator 责任清单 +1 条（后收敛执行编排） |

## 不做的事

| 砍掉的机制 | 理由 |
|-----------|------|
| Scope 拆分协议（按文件拆分、合并条件、依赖排序） | 无实证：从未观测到编排失败 |
| 确定性核对（grep/diff/计数验证） | 无实证：从未观测到 executor 遗漏改动 |
| 补丁轮（bounded 1 轮修正） | 依赖确定性核对，核对无实证则补丁轮无必要 |
| max_execution_rounds 参数 | 去掉补丁轮后不再需要 |
| 并行上限（≤3 executor） | 无实证：未观测到并行问题 |
| 角色边界强制机制（boundary_check 标注） | self-report 价值存疑，违反者不会主动标注；instance_id 留痕保留（客观证据） |
| 独立预算估算 | 去掉上述机制后不需要 |
| 执行阶段独立小节（15 行流程描述） | 用必检项 + 责任清单条目替代，无需独立小节 |
| 执行失败恢复协议 | 无实证：未观测到 executor 执行失败；出现后可针对性增加 |
| 后收敛 retrospective 要求 | 收敛 retrospective 已覆盖方案质量；执行阶段无额外复盘需求 |

## 风险评估

| 风险 | 等级 | 缓解 |
|------|------|------|
| Orchestrator 仍然违反约束（无视必检项） | 低 | 与违反 #7 的概率相同；prompt 锚点比零约束好 |
| 多文件落地时编排不当 | 低 | 未观测到；出现后可针对性增加 |
| executor 执行偏差 | 低 | 改动清单已经过收敛循环验证 |

## 自举声明

本方案首次落地发生在协议生效前（自举窗口）。首次落地时应遵循本方案定义的流程，但 retrospective 中无需记录执行阶段的独立复盘。

## 与盲审复核方案的交叉

盲审复核方案（20260612-blind-recheck）已落地。它在没有落地执行约束的情况下完成了文件改动——这是已知的流程债务。本方案批准后，后续方案的落地将受新约束覆盖。
