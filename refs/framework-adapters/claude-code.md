# A.1 Claude Code — framework-adapters 分册

> 本文件是 `refs/framework-adapters.md` 的Claude Code分册。按需只加载本文件;公共层(A.4 通用降级 / A.5 适配新框架 / Archive Contract provenance 采集)在 `refs/framework-adapters.md`。

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

`PreToolUse` hook 在**绑定的收敛会话**中对每次 `Agent` spawn 维护一个**独立于 ledger 的单调计数器**，达 `max_total_reserved_spawns` 即 `deny`。这是防 runaway 的兜底——即便 Orchestrator 完全遗忘 per-scope 预算，hook 也在 cap 处硬停（封堵漂移/遗忘导致的 runaway 路径）。

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
- **角色不可伪造 + 角色 FSM**（per-scope 在 hook 层强制 + 越权 deny）属**后续工作**：Claude Code 不拥有 subagent prompt 模板，且 FSM phase 机为 plan 明确推迟项。

**升级到真正 enforced 的二要件**：session→slug 绑定 + 角色 FSM 须存于 **Agent 不可写**宿主域（权限隔离路径 / harness 注册表）+ settings.json/hook 脚本/budget_gate.py 同样锁定，否则只能 `best-effort guarded`。

> **缺省 tier**：未 `bind` 的会话一律 **auditable-only**——Orchestrator 按责任清单 M-11 自行运行 `budget_gate.py reserve`，违规由 gate ledger 缺口 + pre-push hook 兜底检测。`hook-pretooluse` 对未绑定会话零干预。
