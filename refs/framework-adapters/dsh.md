# A.7 dsh — framework-adapters 分册

> 本文件是 `refs/framework-adapters.md` 的dsh分册。按需只加载本文件;公共层(A.4 通用降级 / A.5 适配新框架 / Archive Contract provenance 采集)在 `refs/framework-adapters.md`。

## A.7 dsh (DeepSeek Harness)

dsh (DeepSeek Harness) 经其 Cordis 合成提供第一方 subagent 工具。converge 可经 `subagent`(spawn 提供方、continuable)+ `send_message` 实现 Spawn/Continue;`subagent_fork`(fork 提供方)为一次性。框架无关的 Spawn / Continue / Identify 三个原子能力在 dsh 里均可用,inner loop 并非不适用于 dsh——关键是用对工具。

| 能力 | 实现 |
|------|------|
| **Spawn** | `subagent` 工具(spawn 提供方)。默认后台模式,立即返回 durable `subagent_id`;fresh 自足 prompt。也支持前台(run_in_background:false),但前台拿不到 durable id,不利于 Continue。 |
| **Continue** | `send_message <subagent_id> ...`。仅对 continuable/后台 `subagent` 生效;可续跑同一条子会话、保有上下文。 |
| **Identify** | `subagent_id`(Spawn 返回的 durable id)。 |

**一次性 vs 可续(易混淆)**:
- `subagent`(spawn 提供方)配置为 `backgroundMode: continuable` → **可**用 `send_message` 续跑。
- `subagent_fork`(fork 提供方)配置为 `backgroundMode: one-shot` → **一次性,不支持后续消息**;dsh 的注释明确「one-shot fork children install neither report tool nor prompt section」。converge 不采纳 fork-executor(见 GD-2)。
- 因此「一次性子代理不支持后续消息」仅指 `subagent_fork`;若要用 dsh 做 inner loop,请用 `subagent` 而非 `subagent_fork`,并保留其 id 供 `send_message`。

**账本/事件接线(与 orchest.py 配对,非自动)**:

dsh 原生 `subagent` **不发射** archive Contract 的 `begin-invocation`/`complete-invocation` 事件。要完整入账需与 orchest.py 手工配对(或写一个薄 dsh adapter 原子化,类似 `ocsr_spawn_adapter.py`):

- **Spawn**: `orchest.py reserve-round --role <r> --round <N> --phase <p> --attempt 1 --prompt-file <abs>` → `subagent(...)` → `orchest.py register-round --reservation-id <rid> --instance-id <subagent_id>`;失败/取消走 `cancel-round`。
- **Continue(inner loop)**: `orchest.py reserve-round --continue-of <父rid> --role <r> --phase review --attempt <n> --prompt-file <abs>`(begin kind=continue,不占 gate reserve,计数入 max_inner_loops)→ `send_message <subagent_id>` → `register-round --invocation-id <invocation_id>`(continue 轮用 invocation-id,不是 reservation-id)。
- **完备性**: executor 轮(consumes=none)注册必须带 `--output attempts.md`;评审/blind 轮按 role+round 推导 output;未入账(=直接 `subagent` 不配 orchest.py)会留下泄漏/孤儿 reservation 或 events-missing。

**provenance 诚实降级(按 PROVENANCE_MATRIX)**:
dsh `subagent` 不返回 per-invocation 的 provider/model,且为 in-process、继承宿主会话模型 →
- Spawn fresh subagent:`configured + resolution_source=agent_config + resolution_reason_code=backend-does-not-expose`。
- Continue 只继承同实例:`inherited + parent_instance + inherited-concrete-model-hidden`。

**预算 / tier**:
dsh 原生 `subagent` 无 deny-before-spawn hook 接线(harness 的 in-process subagent 不经 PreToolUse 类 hook 拒绝)→ 当前 tier **auditable-only**。若 dsh 暴露可拦截并拒绝 subagent spawn 的 tool-use 钩子,可升级到 best-effort guarded——需实测,勿凭推断。

**模型分层 / 降档**:
`subagent` 工具无 per-spawn `model` 参数,子代理继承宿主会话模型(inherit);降档/跨族经 OCSR(opencode)通道(§A.2)。

**降级**:
若 Continue 不可用(用错 `subagent_fork`、或前台且无 `send_message`),inner loop 降级为 orchestrator 自身逐条验收(标注 `inner_loop: orchestrator_self`);若 Spawn 不可用,按 §A.4。

**与 OCSR 的关系**:
dsh 原生 subagent 是同一会话内、继承宿主模型的第一方通道;OCSR 是跨厂商/低成本/一次性 fresh 的第二通道。二者可并存:dsh 用于常规评审循环,OCSR 用于异构/降档/批量。

**选型建议**:
- 同模型、账本完整、无需 opencode → dsh 原生 `subagent` + orchest.py 接线(建议先补薄 dsh adapter 原子化 reserve→subagent→register)。
- 跨厂商、低预算、一次性 fresh → OCSR(§A.2 OCSR 适配层)。
