# 框架适配 · 附录 A

从 `SKILL.md` 外提。保留原 A.x 小节编号，维持内部交叉引用完整性。

---

## A.1 Claude Code

| 能力 | 实现 |
|------|------|
| **Spawn** | `Agent` 工具（`subagent_type: general-purpose`），记录返回的 `agentID` |
| **Continue** | `SendMessage` 工具，`to` 参数为 `agentID` |
| **Identify** | 主对话即 orchestrator，无需自标识 |

**`/goal` 加速（v2.1.139+）**：Claude Code 的 `/goal` 命令可让单 agent 跨 turn 持续工作，直到用户定义的条件满足。在 converge 场景下：

- **可用场景**：Executor 在 inner loop 中持续修复直到 Reviewer 验收通过。设 `/goal attempts.md 中本轮所有 issue verdict = Accepted` 即可让 Executor 自动循环修复，无需 Orchestrator 手动每轮 prompt。
- **不可用场景**：不能替代独立 Reviewer。`/goal` 的评估器是小模型自检，不是独立全新上下文的对抗式审查。converge 的核心价值（独立交叉验证）必须通过 Spawn 实现。
- **层级模式**：子收敛 subagent 可用 `/goal "收敛完成，verdict=可执行"` 自动跑完整个 converge 循环，加速分阶段执行。

**预算 gate 接线（enforced tier）**：

| gate 能力 | Claude Code 实现 | 状态 |
|----------|-----------------|------|
| spawn 前 reserve + 拒绝 | `PreToolUse` hook 匹配 `Agent` 工具 → 运行 `budget_gate.py reserve` → 非 PROCEED 返回 deny（阻断该工具调用）| 落地待接线 |
| spawn 后 settle | `PostToolUse`（成功）/ `PostToolUseFailure`（失败）→ `budget_gate.py settle` | 落地待接线 |
| reservation 键 | hook 输入提供的 `session_id` + `tool_use_id` | 原生支持 |

**enforced 二要件（缺任一 → 整体 auditable-only，不得声称 enforced）**：
- **session→slug 绑定**须存于**运行中 Agent 工具无法写入**的宿主域（权限隔离路径 / harness 维护的注册表）——否则 Agent 可改绑定逃避 gate。
- **角色 FSM**（含 mode / round / in_flight / return_phase）同样须存于 Agent-不可写宿主域，由 settle/ingest-verdict 推进，hook 据其校验越权角色。

**关键待决设计点（落地阶段解决，见 plan §M1-tier/role）**：(1) 全局 `PreToolUse` 对**所有** `Agent` 调用触发，须识别哪些是 converge spawn 并定位正确 `active/<slug>/`（候选：active-converge 标记文件 / prompt sentinel + 失败时 fail-closed）；(2) Claude Code 的 subagent prompt 由调用方全权控制，宿主**不拥有** role→prompt 模板 → enforced 只声称"计费标签受控 + 总量硬上限"，**不**声称"角色不可伪造"（plan §M1-role 第二档）。

> **当前缺省 tier**：在宿主接线落地前，Claude Code 上运行于 **auditable-only**——Orchestrator 按责任清单 M-11 自行运行 `budget_gate.py`，违规由 gate ledger 缺口 + pre-push hook 兜底检测。

## A.2 opencode

| 能力 | 实现 |
|------|------|
| **Spawn** | 调用 `task` 工具，设置 `subagent_type: "general"`，prompt 参数传入自足的 reviewer/executor prompt |
| **Continue** | 通过 `task` 工具的 `task_id` 参数恢复同一个 subagent 会话 |
| **Identify** | 当前 agent 无标准 Identify，orchestrator 即主对话 |

**降级**：若版本不支持 Continue，inner loop 由 orchestrator 自身逐条验收（标注 `inner_loop: orchestrator_self`）。

**`/goal` 替代方案（截至当前版本）**：opencode 暂无内置 `/goal` 命令。若后续版本新增，用法与 A.1 中 Claude Code `/goal` 的说明一致。当前版本的替代路径：

1. **Orchestrator 手动驱动**（默认）：Orchestrator 在主循环中逐轮 Spawn Reviewer / Executor，这是 converge 的标准执行方式，无功能损失。
2. **Prompt 内嵌循环**：给 `task` subagent 的 prompt 中直接写入循环指令（如"重复以下步骤直到条件满足：先检查 X，若未满足则修改 Y，再检查 X"），让 subagent 在单次调用内自主迭代。适用于 inner loop 加速，但 subagent 内部无法 Spawn 独立 Reviewer（缺乏对抗式保证），retrospective 中需标注 `inner_loop: prompt_embedded`。

## A.3 codex (OpenAI Codex CLI)

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

## A.4 通用降级策略

框架**完全不支持** Spawn 时：

1. **Reviewer 降级**：Orchestrator 自身模拟 reviewer → 标注 `reviewer_backend: orchestrator_self`，retrospective 中分析自审偏差
2. **Executor 降级**：Orchestrator 自身执行修改，自觉遵守路径依赖防护
3. **Inner loop 降级**：Orchestrator 自身对照 reviewer 输出逐条验收

> ⚠️ 降级模式下结论可信度显著降低。Retrospective 必须讨论降级影响。

## A.5 适配新框架

三个问题完成适配：
1. 如何启动带全新上下文和自足 prompt 的 agent？（→ Spawn）
2. 能否向它发跟进消息且保有上下文？（→ Continue）
3. 如何引用该 agent 实例？（→ instance_id）
