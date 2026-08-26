# A.3 codex — framework-adapters 分册

> 本文件是 `refs/framework-adapters.md` 的codex分册。按需只加载本文件;公共层(A.4 通用降级 / A.5 适配新框架 / Archive Contract provenance 采集)在 `refs/framework-adapters.md`。

## A.3 codex (OpenAI Codex CLI)

优先按能力探测适配。若当前 Codex 环境暴露 `multi_agent_v1`，使用原生多 agent adapter：

| 能力 | 实现 |
|------|------|
| **Spawn** | `multi_agent_v1.spawn_agent`，**同时支持** fresh（`fork_context=false`/省略）与 **inherited**（`fork_context=true`）上下文。Reviewer 必须用 fresh self-contained prompt；inherited 变体是 CC `fork` 的原生等价物（框架能力；converge 不采纳，见 GD-2）。Executor/Worker 必须明确 write scope |
| **Continue（两步）** | ① `multi_agent_v1.send_input(target=<agent_id>)` 返回 `submission_id`（**不是** agent 的回复）；② `multi_agent_v1.wait_agent(targets=[...])` 返回状态 + 最终 response。Continue 不是单次返回回复的调用 |
| **Resume** | `multi_agent_v1.resume_agent(id=<agent_id>)`：重开已关闭/空闲的 agent，上下文保留 |
| **Close** | `multi_agent_v1.close_agent(target=<agent_id>)`；角色完成后关闭，避免悬挂 agent |
| **Identify** | 主会话即 Orchestrator；子 agent id 来自 Spawn 返回值（`agent_id`） |

**Codex adapter 约束：**

1. **显式授权**：只有用户明确请求 converge / subagent / delegation，或当前 skill invocation 本身就是显式收敛工作流时，才 spawn agent。
2. **不默认嵌套 spawn**：不要假设 subagent 内部也能继续 spawn 后代 agent。层级模式优先采用主 Orchestrator 集中调度；只有确认子 agent 能力后才启用 delegated hierarchical mode。
3. **文件可见性保守处理**：不要假设一个 subagent 的文件修改会自动对另一个 subagent 可见。Executor/Worker 返回时必须列出 changed paths、diff 或摘要；Orchestrator 先审查并集成，再把必要 diff/产物路径传给 Reviewer 验收。
4. **模型继承优先**：per-agent model override（`model` / `reasoning_effort` / `service_tier`）**仅对 fresh spawn 可用**——不要设置 override，除非用户明确指定模型或 scope 有清晰的任务级理由。**full-history fork 必须继承**父 agent type、model、reasoning effort（**无 per-fork model override**：实测中 `fork_context=true` 叠加异种 agent_type 被拒）。
5. **关闭已完成 agent**：Reviewer/Executor/Worker 完成角色后调用 Close；若关闭失败，在 state 中记录原因。

**能力探测（Codex 0.141.0 实测）**：探测 = 检视 `spawn_agent` 工具的输入 schema 是否含 `fork_context` 参数（**不要**仅凭 CLI 版本 / feature flag 推断——`codex features list` 中 `multi_agent` enabled 只是支撑证据，不证明当前 agent 被暴露了对应工具）。fresh Spawn 省略或设 `fork_context=false`；inherited Executor 设 `true`。独立探测 `send_input` / `wait_agent` / `close_agent` / `resume_agent`。

> **CLI `codex fork` / `codex resume` 注意**：它们作用于**已保存的 SESSION**，**不是** live 子 agent 机制——不返回 `multi_agent_v1` 子 agent 句柄，也不提供 `send_input` / `wait_agent` 编排。子 agent adapter 用的是 `multi_agent_v1.spawn_agent`，非 CLI `fork`。

若未暴露 `multi_agent_v1` 但存在其他 Codex task/sub-agent 机制，则按该机制映射 Spawn / Continue / Wait；若 Continue 不可用，inner loop 降级同 A.2。若完全不支持 Spawn，按 A.4 降级。

**`/goal` 加速（可选）`[UNCERTAIN]`**：Codex 0.141.0 中**无可验证的 `/goal` 收敛循环设施**——该运行时暴露 thread goal-management 工具，但未证实存在能自动跑 Executor/Reviewer 收敛循环的 `/goal`。**不要声称 Codex 当前支持** `/goal` 驱动收敛（待单独的 TUI 探测确认）。若后续版本确证支持：`/goal` 可作为 Executor inner loop 或子收敛执行的加速器，但不是基础依赖，且不能替代独立 Reviewer——仍需通过 Spawn 获得 fresh reviewer 做对抗式审查，并在 retrospective 中记录 goal-assisted execution。
