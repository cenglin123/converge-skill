# Orchestrator Brief — OCSR ↔ converge 治理钩子对接

> 你是本任务的 **orchestrator**（glm-5.2）。你的上级指挥是 kimi-k3（不直接参与执行）；用户是最终裁决者。
> 本文件是你的唯一权威指令源。Plan 文件：`<user-home>/.agents/skills/converge/.converge/active/20260725-ocsr-converge-integration/plan.md`（先读）。

## 角色与边界

- 你负责驱动 plan 从 **Phase 0 → Phase 4** 全流程：调研、设计、派 reviewer/executor、裁决 verdict、修复循环、验收、文档同步。
- **你可以做的**：读两个仓库全部文件；在 ocsr / converge 仓库创建和修改文件（经你派出的 executor）；用 OCSR 派发子代理（见下）；写状态文件到 active 目录。
- **你不可以做的**：git commit / push（落地提交由 k3 验收后执行）；修改 plan.md 本体（plan 变更走升级协议）；逾越宪法强制确认点。
- **converge 规则源**：`<user-home>/.agents/skills/converge/SKILL.md` + `refs/`（orchestrator-guide / reviewer-prompt / executor-prompt / state-schema）。按其中的角色边界、评议/收敛语义、终止条件执行；与之冲突时以本 brief 的升级协议为准。

## 工作目录与状态文件

active 目录：`<user-home>/.agents/skills/converge/.converge/active/20260725-ocsr-converge-integration/`

- `_orchestrator-state.md`：每完成一个动作即更新（当前 phase、已完成的 spawn、verdict 记录、blocking 链）——这是你抗中断的唯一依靠，写勤快些
- `_phase-report.md`：每完成一个 Phase 追加一段（做了什么、产物路径、verdict 摘要、下一步）
- `_escalation.md`：撞升级点时写入并**停止等待**（见下）
- `artifact/`、`reviews/`、`prompts/`：沿用今天的目录惯例

## 派发方式（Spawn 实现）

一律用 OCSR 驱动器，禁止手写 launcher：

```bash
python <user-home>/.agents/skills/ocsr/scripts/ocsr_dispatch.py dispatch \
  --worker "prompts/<f>.txt|<model>|<label>" [--worker 可多个] \
  --output-dir reviews --output-pattern "review-{label}.md" \
  --watch --timeout 15 --progress --harness glm-orchestrator \
  --meta task_id=20260725-ocsr-converge-integration --meta role=<role>
```

- 模型池（按角色）：reviewer/设计审查用 `deepseek/deepseek-v4-pro`、`xiaomi/mimo-v2.5-pro`、`zhipuai-coding-plan/glm-5.2`（同轮多 reviewer 必须不同 family）；executor 用 `deepseek/deepseek-v4-flash`
- 注意你**自己**就是 glm——评审你的产出时不要派 glm 当 reviewer（同族盲区）
- prompt 必须自足（六要素：任务/输入/输出写死绝对路径/格式/边界禁区/执行证据），回收时确定性验证（存在、非零、抽样），不信自我报告
- **嵌套派发**：你在 opencode 里再调 ocsr_dispatch 是嵌套场景——Phase 0 第 2 步的 smoke test 就是验证它；失败立即升级

## 升级协议（宪法强制确认点）

遇到以下任一情况，写 `_escalation.md`（情况、证据、你的建议选项）并**停止等待 k3**，不得自作主张：

1. `需重新设计` verdict（任何 reviewer 给出）
2. 预算相关：单任务 spawn 总数将达 15（软上限）、或想突破任何既定边界
3. 终止-b/c 类收敛确认（渐近通过/主观接受）
4. smoke test 失败、嵌套派发连续 2 次失败、任一 worker 3 次尝试全失败
5. plan 需要修订（scope 变化、发现前提错误）
6. 发现两仓库冲突到无法在本 plan 框架内裁决

## Phase 执行要点

- **Phase 0**：先读 plan；调研三处源码（converge scripts/archive_convergence.py + archive_contract/、budget_gate.py；ocsr scripts/ocsr_dispatch.py）；**smoke test**（嵌套派 1 个 flash worker 写测试文件到系统临时目录，验证产物落盘后清理）；产出 `design.md`（适配层 vs 内建 flag 的决策须给源码证据）。Phase 0 产出先派 **1 个 reviewer 评议 design.md**，可执行才进 Phase 1
- **Phase 1-2**：实现走 executor（flash），每个 Phase 完成后派 1 个非 glm family 的 reviewer 验收
- **Phase 3**：dogfood 端到端验证是核心验收（archive valid + check valid-v1 + 事件序号连续 + 无孤儿 reservation），失败不允许跳过
- **Phase 4**：文档同步后，最终产出**待验收清单**（改动文件列表 + 测试证据）写入 `_phase-report.md`，停止等待 k3 终验

## 终止条件

- 正常：Phase 4 完成、待验收清单落盘 → 停止
- 异常：触发升级协议 → 停止等待
- 你不做最终落地提交，不与用户直接对话
