# 框架适配 · 附录 A

从 `SKILL.md` 外提。保留原 A.x 小节编号，维持内部交叉引用完整性。

---

## A.1 Claude Code

| 能力 | 实现 |
|------|------|
| **Spawn** | `Agent` 工具（`subagent_type: general-purpose`），记录返回的 `agentID` |
| **Continue** | `SendMessage` 工具，`to` 参数为 `agentID` |
| **Identify** | 主对话即 orchestrator，无需自标识 |

**`fork` 子 agent 类型（框架能力；converge 不采纳 fork-executor——见 GD-2）**：harness 描述了 `subagent_type: fork`（继承父对话上下文的 spawn），但**并非所有部署都暴露**——已在至少一个当前 Claude Code 环境中实测**缺失**（顶层与嵌套 spawn 均返回 `Agent type 'fork' not found`）。因此 fork 必须按**运行时探测能力**对待：先探测可用性，**缺失即降级为 fresh Spawn**（converge 当前并不使用 fork）。

**`/goal` 加速（v2.1.139+）**：Claude Code 的 `/goal` 命令可让单 agent 跨 turn 持续工作，直到用户定义的条件满足。在 converge 场景下：

- **可用场景**：Executor 在 inner loop 中持续修复直到 Reviewer 验收通过。设 `/goal attempts.md 中本轮所有 issue verdict = Accepted` 即可让 Executor 自动循环修复，无需 Orchestrator 手动每轮 prompt。
- **不可用场景**：不能替代独立 Reviewer。`/goal` 的评估器是小模型自检，不是独立全新上下文的对抗式审查。converge 的核心价值（独立交叉验证）必须通过 Spawn 实现。
- **层级模式**：子收敛 subagent 可用 `/goal "收敛完成，verdict=可执行"` 自动跑完整个 converge 循环，加速分阶段执行。

**预算 gate hook 接线（`best-effort guarded`，已落地）**：

> **命名（治理边界）**：本机制**不是 "enforced" tier**——它不提供角色不可伪造/权限锁定保证。准确称谓为 **`best-effort guarded`**（即 `hook-blocked auditable-only`）：在 auditable-only 之上加一道宿主 hook 总量兜底。真正的 enforced（角色 FSM + 权限锁定）仍为未来工作。

`PreToolUse` hook 在**绑定的收敛会话**中对每次 `Agent` spawn 维护一个**独立于 ledger 的单调计数器**，达 `max_total_reserved_spawns` 即 `deny`。这是防 runaway 的兜底——即便 Orchestrator 完全遗忘 per-scope 预算，hook 也在 cap 处硬停（直击 31 轮失控的"漂移/遗忘"成因）。

| 阶段 | 命令 | 说明 |
|------|------|------|
| 会话开始绑定 | `budget_gate.py bind --session-id <SID> --active-dir <active>` | 写 host 域绑定（默认 `~/.claude/converge/bindings/<sha256(SID)>.json`，可经 `CONVERGE_BINDINGS_DIR` 覆盖）；**cap 派生自 validated `ceiling(state,total)`，不接受任意传入**；**已绑定则拒绝**（防 re-bind 清零） |
| 扩容刷新 | `budget_gate.py refresh-cap --session-id <SID>` | 加 `scope=total` extension 后调用：原子更新 cap = validated ceiling，**保留 count** |
| 每次 spawn 前 | `PreToolUse` hook 匹配 `Agent` → `budget_gate.py hook-pretooluse`（读 stdin）| 见下方 fail 边界 |
| 会话结束解绑 | `budget_gate.py unbind --session-id <SID>` | 删除绑定，恢复 passthrough |

`settings.json` 接线样例：

```json
{ "hooks": { "PreToolUse": [ { "matcher": "Agent",
  "hooks": [ { "type": "command",
    "command": "python /abs/path/scripts/budget_gate.py hook-pretooluse" } ] } ] } }
```

**生命周期 / fail 边界**：
- **一个会话同一时刻一个收敛**：`bind` 对已绑定会话**返回 `FAIL_CLOSED:already_bound`、不清零**；复用须先 `unbind`。并发收敛用不同 session_id（按完整 session_id 的 sha256 隔离，**无文件名碰撞**）。
- **cap 由 validated state 派生**：`ceiling(state,total)`，经 `validate_integrity`（含 `scope=total` extension 授权链校验）。bind 后扩容须先加 validated extension 再 `refresh-cap`——不存在任意 `--cap`。
- **fail 边界**（hook）：未绑定 / 非 `Agent` 工具 / stdin 不可解析（无法识别会话）→ **放行**；**绑定存在后任何损坏/字段缺失/session_id 不符/锁超时/写错误 → DENY（fail-closed）**，封堵"篡坏 binding 禁用上限"。绑定被删＝未绑定＝放行（已确认的残余）。

**`best-effort guarded` 的诚实边界**：
- hook 只强制**总量硬上限**；per-scope（outer/blind/ultraverge）预算、mode-switch、extension 菜单仍由 Orchestrator 经 `budget_gate.py reserve` 驱动（两条路互不干扰、不双计——hook 用独立计数器，不写 ledger）。
- **未做权限锁定**：绑定文件 Agent 可写/可删，蓄意自篡改可绕过——属"主动破坏自身治理"的不同威胁模型，已与用户确认排除（封堵的是漂移/遗忘，非恶意）。
- **角色不可伪造 + 角色 FSM**（per-scope 在 hook 层强制 + 越权 deny）属**后续工作**：Claude Code 不拥有 subagent prompt 模板，且 FSM phase 机为 plan 明确推迟项（审计已冻结其枚举转测试）。

**升级到真正 enforced 的二要件**：session→slug 绑定 + 角色 FSM 须存于 **Agent 不可写**宿主域（权限隔离路径 / harness 注册表）+ settings.json/hook 脚本/budget_gate.py 同样锁定，否则只能 `best-effort guarded`。

> **缺省 tier**：未 `bind` 的会话一律 **auditable-only**——Orchestrator 按责任清单 M-11 自行运行 `budget_gate.py reserve`，违规由 gate ledger 缺口 + pre-push hook 兜底检测。`hook-pretooluse` 对未绑定会话零干预。

## A.2 opencode

| 能力 | 实现 |
|------|------|
| **Spawn** | 调用 `task` 工具，传入 `subagent_type` 与自足的 reviewer/executor prompt；返回 session 式 `task_id` 句柄 |
| **Continue** | 用同一 `task_id` 重新调用 `task` 恢复该 subagent 会话（实测 1.17.8：上下文保留） |
| **Identify** | 当前 agent 无标准 Identify，orchestrator 即主对话 |

**实测校正（opencode 1.17.8）：**

- **`subagent_type` 可用性非普遍**：`"general"` **并非**在所有模式可用——在 restricted / plan-mode 主 agent 下 `task general` 被拒，此类会话只暴露 `explore`。正常 / 全权限配置下 `general` 存在且适用于多步工作。Spawn 前应探测当前主 agent 实际暴露的 subagent 类型，不要假定 `general` 始终可用。
- **无 per-spawn `model` 参**：`task` 调用本身不接受 `model` 参数；模型选择通过**已配置的 subagent 类型**实现（每个 agent 类型可 pin 一个 model；未配置则继承主 agent 模型）。
- **`opencode run --fork` 是 CLI-session fork，非 live 子 agent**：它 fork 出一个**可恢复的 CLI 会话**，不是对话内的 live in-conversation subagent，**不可**当作子 agent 上下文继承机制（converge 不采纳 fork-executor，见 GD-2）。

**降级**：若版本不支持 Continue，inner loop 由 orchestrator 自身逐条验收（标注 `inner_loop: orchestrator_self`）。

**`/goal` 替代方案（截至当前版本）**：opencode 暂无内置 `/goal` 命令。若后续版本新增，用法与 A.1 中 Claude Code `/goal` 的说明一致。当前版本的替代路径：

1. **Orchestrator 手动驱动**（默认）：Orchestrator 在主循环中逐轮 Spawn Reviewer / Executor，这是 converge 的标准执行方式，无功能损失。
2. **Prompt 内嵌循环**：给 `task` subagent 的 prompt 中直接写入循环指令（如"重复以下步骤直到条件满足：先检查 X，若未满足则修改 Y，再检查 X"），让 subagent 在单次调用内自主迭代。适用于 inner loop 加速，但 subagent 内部无法 Spawn 独立 Reviewer（缺乏对抗式保证），retrospective 中需标注 `inner_loop: prompt_embedded`。

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

> **第四问（fork-executor——converge 不采纳，见 GD-2）**：Spawn 能否继承当前父对话线程，受何限制？（→ inherited-context Spawn，框架能力）。Wait / Close 应作为生命周期能力探测，即便它们不属于上述三个概念原子。

### `best-effort guarded`（deny-before-spawn）可移植性 — 未来扩展数据，**非已实现**

记录跨框架可移植性，**不声称** opencode / Codex 已落地强制：

| 框架 | deny-before-spawn 现状 |
|------|------------------------|
| **Claude Code** | **已落地**（`PreToolUse` hook，见 §A.1）——目前唯一已落地 `best-effort guarded` 的框架 |
| **opencode** | **今日仅 auditable-only**：*可*经 `tool.execute.before` 插件或静态 `permission.task` deny 获得 deny-before-spawn，但默认无此类插件加载（实测 1.17.8：`opencode debug info` 无插件）→ 当前未 hook-guarded |
| **Codex 0.141.0** | **今日仅 auditable-only**：**无**可验证的 deny-before-spawn——`notify` 仅注入输出、不可拒绝调用；`token_budget` 特性禁用；hooks 是否能看见/拒绝 `multi_agent_v1.spawn_agent` 未经实测证实（不可凭 `hooks = stable` 推断）→ 维持 auditable-only |

> 切勿声称 opencode / Codex 的强制已实现。在真实 hook 测试证明配置的 pre-tool hook 能收到 spawn 事件并阻止 agent 创建之前，两者均维持 auditable-only。
