# A.6 kimi-code — framework-adapters 分册

> 本文件是 `refs/framework-adapters.md` 的kimi-code分册。按需只加载本文件;公共层(A.4 通用降级 / A.5 适配新框架 / Archive Contract provenance 采集)在 `refs/framework-adapters.md`。

## A.6 kimi-code

| 能力 | 实现 |
|------|------|
| **Spawn** | `Agent` 工具（`subagent_type: coder / explore / plan`），记录返回的 `agent_id` |
| **Continue** | `Agent(resume=<agent_id>, prompt=...)` 续命同一实例，上下文保留 |
| **Identify** | 主对话即 orchestrator，无需自标识 |
| **fork** | 无（`resume` 是续命既有实例，不是上下文 fork；converge 不采纳 fork-executor 的立场不变，见 GD-2） |

**模型分层**：`Agent` 工具无 per-spawn model 参数，子代理继承主对话模型（inherit）；降档不可经原生通道实现，跨族/降档走 OCSR（§A.2 OCSR 适配层）。

**`best-effort guarded` 可接线（机制已验证、端到端待实测）**：kimi-code 的 `PreToolUse` hook 支持阻断（exit 2 或 stdout `hookSpecificOutput.permissionDecision="deny"`——deny JSON 格式与 Claude Code 一致，`budget_gate.py hook-pretooluse` 的 `_emit_deny` 输出可被直接消费）；matcher 按工具名匹配，原生 Spawn 工具名为 `Agent`（与 `SPAWN_TOOL_NAMES` 兼容）；hook payload 含 `session_id`。接线三件：

1. `scripts/hooks/kimi_pretooluse_shim.py`（本仓库）：payload 归一化（工具名键变体容忍）→ 子进程调用 `budget_gate.py hook-pretooluse` → 逐字转发 stdout。
2. `config.toml`（用户级，opt-in）：`[[hooks]] event="PreToolUse" matcher="Agent" command="python <converge>/scripts/hooks/kimi_pretooluse_shim.py"`；同文件另挂一行 `[[hooks]] event="SessionStart" command="python <converge>/scripts/hooks/kimi_pretooluse_shim.py --record-session <状态文件路径>"`（落盘 session_id，供第 3 件 bind 前读取）。
3. session_id 获取：orchestrator `bind --session-id` 需要当前会话 id——用 shim 的 `--record-session <文件>` 模式挂 `SessionStart` hook 落盘，orchestrator bind 前读取。

**诚实边界（kimi 特有）**：kimi CLI 对 hook 脚本错误/超时 **fail-open**（默认放行）——绑定损坏时的 fail-closed 仅由 budget_gate 脚本内部保证（deny JSON），shim 自身崩溃则本层防护失效；此为相对 Claude Code 的额外 best-effort 残余，接入时必须告知用户。payload 工具名键名以实测为准（shim 容忍 `tool_name`/`toolName`/`tool` 变体）。当前 tier：**auditable-only**（hook 未接线前）；接线并端到端验证后方可声明 best-effort guarded。退化矩阵：shim 正常运行 → best-effort guarded（budget_gate fail-closed 生效）；shim 崩溃/超时/budget_gate 缺失 → auditable-only（kimi CLI fail-open 静默放行，shim 仅在 stderr 留一行说明）。
