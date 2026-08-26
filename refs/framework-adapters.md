# 框架适配 · 附录 A

小节采用 A.x 编号以维持内部交叉引用稳定性。

---

## Archive Contract provenance 采集

可执行矩阵由 `archive_contract.model.PROVENANCE_MATRIX` 唯一拥有，adapter fixture 必须逐 backend 映射到该矩阵，文档不得另建宽松枚举：

- opencode / Codex / Claude 若宿主回执给出本 invocation 的 provider 与 model/family，使用 `observed|host-reported + host_receipt`；tool response 必须绑定 `invocation:<invocation-id>:tool-response`。
- 仅 CLI/agent 配置可见时使用 `configured`，reason 只能是 `backend-does-not-expose|receipt-missing`。
- Continue 只继承同 instance 时使用 `inherited + parent_instance + inherited-concrete-model-hidden`。
- 解析前失败使用 `unavailable + none + invocation-failed-before-resolution`，且只能用于非 succeeded terminal。

所有 adapter 只向 capture 层提交声明与宿主 receipt，不直接写 manifest/INDEX。采集优先级为宿主可验证 receipt > tool response > CLI 明示配置 > agent config > parent instance > unavailable。

| backend | requested | resolved/receipt | 合法 evidence |
|---|---|---|---|
| Claude Code | Agent 参数/配置 | Agent 返回的 agentID；若宿主未暴露 concrete model 则留空 | agentID 是 host-reported instance，不自动证明 model；配置模型为 configured |
| opencode | subagent type 配置 | task_id；tool response 若含 provider/model 才可记录 resolved | task_id 为 host-reported；配置 pin 为 configured，继承但 concrete 隐藏为 inherited + reason |
| Codex native agent | spawn 参数（如宿主实际暴露） | agent_id/submission_id/wait response | tool response 中 concrete model 才是 host-reported；仅父会话信息为 inherited |
| orchestrator_self | 当前会话配置 | 无独立子调用 receipt | configured 或 unavailable；必须作为 capability degradation |

observed 仅用于宿主提供可直接观察且绑定本次 invocation 的字段；host-reported 表示信任宿主回执但无外部签名。`configured/inherited` 永远不能提升成 observed。失败发生在解析前用 `invocation-failed-before-resolution`；receipt 缯失用 `receipt-missing`；backend 不暴露字段用 `backend-does-not-expose`。


### 框架分册索引(按需只加载对应分册;公共层留在本文件)

| A.x | 框架 | 分册文件 | 分册内容 |
|-----|------|----------|----------|
| A.1 | Claude Code | [`refs/framework-adapters/claude-code.md`](framework-adapters/claude-code.md) | Spawn/Continue/Identify、fork 探测定则、`/goal` 加速、`best-effort guarded` hook 接线 |
| A.2 | opencode(含 OCSR) | [`refs/framework-adapters/opencode.md`](framework-adapters/opencode.md) | Spawn/Continue/`task_id`、subagent_type 探测、无 per-spawn model、`--fork` 非 live fork、OCSR 适配层 |
| A.3 | codex | [`refs/framework-adapters/codex.md`](framework-adapters/codex.md) | `multi_agent_v1` Spawn(fresh/inherited)、两步 Continue、resume/close、约束 #1-#5、`/goal` [UNCERTAIN] |
| A.6 | kimi-code | [`refs/framework-adapters/kimi-code.md`](framework-adapters/kimi-code.md) | Spawn/`resume`、模型继承、`best-effort guarded` 可接线(fail-open 诚实边界/退化矩阵) |
| A.7 | dsh(DeepSeek Harness) | [`refs/framework-adapters/dsh.md`](framework-adapters/dsh.md) | `subagent`(continuable)+`send_message`、`subagent_fork` 一次性、orchest.py 配对、provenance、auditable-only |
| A.4 | 通用降级策略(**公共**) | 本文件(`framework-adapters.md`) | Reviewer/Executor/Inner loop 降级 + 降级影响提示 |
| A.5 | 适配新框架(**公共**) | 本文件(`framework-adapters.md`) | 三/四问、`best-effort guarded` 可移植性矩阵 |

> 说明:A.x 编号保持稳定;框架特定内容移入上表分册文件,`refs/framework-adapters.md` 只保留公共层与索引。历史归档(`.converge/done/`、`docs/plans/done/`)中的旧 A.x 引用保持不变,按其当时文件解读。

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
