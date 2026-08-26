# A.2 opencode — framework-adapters 分册

> 本文件是 `refs/framework-adapters.md` 的opencode分册。按需只加载本文件;公共层(A.4 通用降级 / A.5 适配新框架 / Archive Contract provenance 采集)在 `refs/framework-adapters.md`。

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

### OCSR 作为 opencode Spawn 实现（治理钩子接线）

OCSR（`scripts/ocsr_dispatch.py`，ocsr SKILL.md §三）是本机 `opencode run` 的驱动器，支持跨厂商异构模型、fresh-context 对抗评审、批量并行派发。当 OCSR 作为 converge 的 Spawn 后端时，每次 Spawn 都必须纳入 converge 的事件流（Archive Contract v1 的 `begin-invocation`/`complete-invocation`/`recover-invocation`）与预算门控（`budget_gate reserve/settle`），否则 `archive_convergence.py archive` fail-closed（`events-missing` —— OCSR 派发链路未调用该协议）。

converge 仓库侧提供 **`scripts/ocsr_spawn_adapter.py`**（薄适配层，~32KB stdlib-only）包装 `ocsr_dispatch.py dispatch`，把每次 Spawn 原子化为五步：

```
reserve → begin-invocation → ocsr_dispatch dispatch → complete/recover-invocation → settle
```

**CLI 表面**（详见 `design.md` §3.1）：

```bash
python scripts/ocsr_spawn_adapter.py dispatch \
  --converge-active <active-dir> --converge-scripts <scripts-dir> \
  --ocsr-dispatch <ocsr_dispatch.py path> \
  --role <outer-reviewer|blind-reviewer|ultraverge-initial|executor|...> \
  --phase <phase-name> --round <N|0> --attempt <N> \
  --prompt <abs-path> --model <provider/model> --label <ocsr-label> \
  --output-dir <dir> --output-name <filename> \
  [--watch] [--timeout <min>] [--reserved-reservation-id <rid>]
```

**关键属性**：

- **provenance 诚实降级**：OCSR 派发的 `opencode run` 当前不在产物中暴露 per-invocation 的 `provider/model` 字段，故 complete-invocation 使用 `evidence_level=configured + resolution_source=cli_argument + resolution_reason_code=backend-does-not-expose`（`archive_contract/model.py:PROVENANCE_MATRIX` 下 strictest legal honest choice）。`--instance-id`（ocsr `batch_id`）和 `--receipt`（`ocsr-dispatch-ledger.jsonl:<rid>`）作为非约束性关联句柄保留，但 **不** 升格 configured → host-reported；如果后续 opencode `--format json` 暴露绑定本次 invocation 的 tool_response `provider/model` 字段，可以升级。
- **角色映射直接对齐**：适配层用到的 6 个角色子集（outer-reviewer / blind-reviewer / ultraverge-initial / executor / arbiter / design-reviewer）在 `budget_gate.ROLE_CONSUMES` 与 `ocsr_dispatch.ROLE_VALUES` 中语义一致，无需翻译。
- **失败路径正确触发**：看门狗超时 → `recover-invocation(timeout)` + gate `settle(failed, pre_execution=false)`；launcher 错误 → `recover-invocation(failed)` + gate settle（`pre_execution=true`）；路径碰撞 → `failed`。
- **"edit X" 类任务的 sentinel 模式**：当 converge executor 的真实交付是"修改既有文件 + 写 attempts.md"而非产出单一新文件时，`--output-name` 需指向一个 sentinel 文件（如 `done.marker`），prompt 显式让 executor 在完成所有工作后写入该 sentinel。否则 ocsr watcher 等不到期望产物，适配层触发失败路径（recover-invocation + settle failed）——即使 executor 实际完成了修改。这是 faithful recording（archive Contract 捕获真实事件），调用方需知晓此约定。
- **config-init 辅助**：`ocsr_spawn_adapter.py config-init --mode ultraverge` 写入初始 `_budget-state.json`（自动覆盖 `max_blind_rechecks=2`），供 orchestrator 在第一个 reserve 前初始化。
- **ledger 双写无重复计费**：`gate-ledger.jsonl`（converge 预算决策）+ `ocsr-dispatch-ledger.jsonl`（ocsr 派发事实），两账本语义独立。budget_gate 的 `model_invocation` 计数只从 gate-ledger 派生。

**测试覆盖**（14 tests 全绿，`tests/test_ocsr_spawn_adapter.py`）：happy path / fail-launcher (pre_execution=true) / fail-timeout (pre_execution=false) / unknown-role DENY / outer-reviewer scope 消耗 / event-graph closure (model.validate_event_graph) / config-init 6 cases / per-scope BLOCK (5 outer 填满后第 6 次 BLOCK) / summary attempted vs model_invocation 区分。

**架构定位**：适配层是 **converge 仓库侧的客户代码**——ocsr 保持框架无关（`ocsr_dispatch.py` 不做预算/事件编排判断，呼应 ocsr SKILL.md §三 "脚本不做编排判断"），converge 是 ocsr 的客户之一。本适配层与 `archive_contract` 同仓库，可直接 import model 做 schema 校验。

详细对接设计见 `.converge/active/20260725-ocsr-converge-integration/design.md`（adapter-layer 决策、provenance 矩阵引用、失败注入测试、验收锚点）。端到端 dogfood 验证（`.converge/done/20260725-dogfood-adapter-usage/`，`archive` committed + `check` valid-v1 + sequence 1-7 连续 + 零孤儿 reservation）已通过。

#### 退出码契约（2026-08 接口变更）

`ocsr_dispatch.py dispatch --watch` 的退出码语义由 **ocsr 仓库的 `refs/dispatch-patterns.md` §退出码契约**单一定义：

```
0 全部落盘 ｜ 1 看门狗超时 ｜ 2 确定性失败 ｜ 3 路径碰撞
混合结局优先级：3 > 1 > 2 > 0
```

退出码 `2` 是新增。在此之前 `--watch` 在 worker 失败时也返回 **0**，调用方无法用退出码判断成败——适配层最初就是在那个前提下写的。接线后有一条行为变化值得单列：

> **产物存在不等于成功。** 适配层现在要求 **产物落盘 且 `rc == 0`** 才记 `complete-invocation(succeeded)`。
> `rc=3` 意味着这一批**覆盖了既有文件**——本 worker 自己的产物在不在盘上，与「别的东西有没有被覆写」无关。
> 只看产物就会把一次路径碰撞记成一次干净的 Spawn。

### 终局链路交给 OCSR 运行器（`run --spec`）

ocsr 的确定性步骤运行器（`ocsr_dispatch.py run --spec`，schema 见 ocsr `refs/run-spec.md`）用来执行**终局这一段**：

```
record-user-message → record-terminal-decision → stamp-decision-markers → archive → check
```

模板：**`refs/run-specs/terminal-chain.yaml`**（本仓库）。填 `vars` 即可用，先 `--validate` 再执行。

**为什么只接这一段**：它失败率最高，而且**完全不含判断**。多轮主循环（spawn reviewer/executor、裁 verdict、盲审）每一步都要 agent 判断，正是运行器不该接管的——`run --spec` 的 `pause` 步骤保证编排空间不被收窄，但这里根本用不上。

**分工边界不变**：spec 由 converge 撰写并保存在 converge 仓库；ocsr 的运行器不认识 reserve/settle/archive/verdict 的含义，只按 spec 执行 argv 并按契约 fail-closed。

**配套的机械化**（2026-08-10，S9b）：链路里凡是能从事件图导出的值，一律不再手填——

| 值 | 由谁导出 |
|---|---|
| `supersedes_decision_event_id` | `record-terminal-decision`（缺省填充；给定则比对，不符拒写） |
| `presented_degradations` | 同上 |
| `accepted_state` | 由 `--decision-kind` 蕴含 |
| `terminal_decision_event_id` / `_value` 两个 marker | `stamp-decision-markers` |
| 决策的 `--source-ref` | 上一步 `record-user-message` 的输出捕获（`{{steps.<id>.capture.<name>}}`） |

只剩**用户原话**需要人写——它本来就不是能导出的东西。诊断用 `derive-decision-fields`（只读，派发前肉眼复核）。

> **重放旧事件时省略 derived 字段。** 把旧版本写下的事件重新灌入
> `record-terminal-decision` 时，不要把原事件里的 `supersedes_decision_event_id` /
> `presented_degradations` 一起传——重放时的事件图与当初不同，导出值也不同，
> 原样传入会撞上 `decision-derived-field-conflict`。让它自动填充即可。
> （直接写事件文件的 bootstrap 导入路径不走这条 CLI，不受影响。）

**这不是新功能，是止血。** ocsr 的两次收敛在归档这一步连续失败（`20260809` → `decision-chain`，`20260810` → `user-decision-degradations`），两次都是把机器能算的值交给人手填，两次都**不可追加修复**。`record-terminal-decision` 现在在写入前就拒绝这两类事件（连同 `user-decision-source` 的 quote 绑定），理由与既有的 `reviewer-verdict` 授权前置检查逐字相同：一条注定在归档时 fail-closed 的事件，不该先落盘再被发现。

**诚实边界**：运行器**不是安全沙箱**——`hook` 步骤执行 spec 声明的任意 argv。spec 及其调用的命令必须当作可信输入（ocsr `refs/run-spec.md` 已就此订正过一次虚假声称）。

**一处仍然存在的缺口（2026-08-10 登记，非待办）**：`validate_event_graph` 对
`reviewer-verdict` 有「已被超越者降级为可审计条目」的宽免，对 `user-decision` **没有**。
因此若一条 `presented_degradations` 或 `source_ref` 有误的 `user-decision` 真的进了事件图，
归档将永久 fail-closed，**且「追加一条正确的决策去超越它」这条合规修复路径不通**
（已实测）。上述写入前拒绝把这种情形从常态降为异常（只剩 `append_event` 直写、
bootstrap 导入、本次变更之前的旧归档三条路径），但没有消除它。
对应的放宽提案经两位跨族独立评审后**未获通过**：先例放掉的恰恰是
`reviewer_event_id` 这个**身份**字段，因此「放元数据、保身份」这条界线未被论证。
要放就得连 `source_ref` 一起放以对齐先例，要保就得给出区分判据——两者都还没做。

端到端验证：`tests/test_terminal_chain_spec.py`（5 条）用**真实 ocsr 运行器**跑通模板，产出真实归档并独立 `check` 为 `valid-v1`；全程零模型调用。ocsr 检出位置由 `OCSR_SKILL_DIR` 指定，缺失即 skip——converge 不硬依赖它的路径。
