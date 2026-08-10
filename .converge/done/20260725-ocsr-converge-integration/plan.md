# Plan：OCSR ↔ converge 治理钩子对接（事件流 + 预算门控）

> 指挥结构（本次实验性工作法）：kimi-k3 为高层指挥（写计划、裁决升级、最终验收、对接用户）；glm-5.2 为 orchestrator（驱动本 plan 从评议到收敛到落地全流程，经 OCSR 派 reviewer/executor）；宪法强制确认点（预算软停/需重新设计/终止-b/c）glm 必须暂停升级给 k3，k3 询问用户。
> 本 plan 本身走 ultraverge（converge 宪法第四部：治理文档修改先落 plan）。

## 背景与问题

2026-07-25 实证：以 OCSR（`ocsr_dispatch.py`）作为 converge 的 Spawn 后端跑完整 ultraverge 后，`archive_convergence.py archive` fail-closed（`events-missing`）——归档契约要求每次 Spawn/Continue 经 `begin-invocation`/`complete-invocation` CLI 记录连续序号事件（`evidence/events`，禁止回填），而 OCSR 派发链路从未调用该协议。同类缺口：OCSR 路径也未接 `budget_gate.py` 的 reserve/settle（本次人工控制 spawn 量代替机械门控）。结果：OCSR 驱动的 converge 无法形式化归档，治理钩子（事件流、预算闸）全部旁路，"嵌套派发失账"。

## 目标

当 OCSR 作为 converge 的 Spawn 后端时，事件流（begin/complete/recover-invocation）与预算门控（reserve/settle）端到端接线，使 OCSR 驱动的完整 converge 能通过 `archive`（valid）+ done/ 只读 `check`（valid-v1）。

## 非目标

- 不合并 ocsr 与 converge（用户明确：短时间内无合并可能，保持两仓库独立）
- 不做嵌套派生的成本归因汇总（ocsr `--meta` 遥测已有基础，超出本期）
- 不改 converge 的归档契约语义与 ocsr 的派发核心逻辑（只加对接面）

## 阶段

### Phase 0 · 调研 + 对接设计（含 smoke test）

1. 读透三处源码：converge `scripts/archive_convergence.py` 与 `archive_contract/`（事件 schema、begin/complete/recover CLI 的调用契约、provenance 字段、metadata-only/redacted/exact 分级）、`scripts/budget_gate.py`（reserve/settle/ingest-verdict CLI 与 `_budget-state.json` schema）、ocsr `scripts/ocsr_dispatch.py`（dispatch 生命周期钩子点）
2. **Smoke test（指挥结构可行性前置验证）**：glm orchestrator 在 opencode 内嵌套派发 1 个 `opencode run` worker 写一个测试文件——验证嵌套 spawn 可用、无 DB 锁。失败则上报 k3 调整指挥结构（改为我直接派发全部 spawn，glm 只做语义编排）
3. 产出对接设计文档（放 `.converge/active/<slug>/design.md`），关键决策：
   - **适配层 vs 内建 flag**：ocsr_dispatch 加 `--converge-dir` 原生感知，还是独立适配脚本（如 converge 仓库侧 `scripts/ocsr_spawn_adapter.py`）包装 dispatch？倾向适配层优先（保持 ocsr 框架无关，呼应知识库"运维须框架无关"教训），以源码证据定夺
   - 事件 provenance 映射：OCSR 派发的模型 = requested；resolved 只能从 opencode 回执证明，无法解析时按契约写 closed reason code，不声称"实际模型已证明"
   - 产物记录分级：默认 metadata-only（locator + hash + size）
   - budget_gate 接线点：dispatch 前 reserve、落盘后 settle（含失败路径 failed）

### Phase 1 · 事件流接线

实现 dispatch → begin-invocation → （落盘/看门狗终止/失败）→ complete-invocation / recover-invocation 全路径；遥测与事件双写不重复计费语义。含失败注入测试（超时 → recover-invocation）。

### Phase 2 · 预算门控接线

dispatch 前 `budget_gate.py reserve`（非 PROCEED 不派发）、落盘后 `settle`；ledger 写入 converge active 目录；`_budget-state.json` config 初始化（ultraverge 时 max_blind_rechecks=2 覆盖等既有规则）。

### Phase 3 · 端到端验证（dogfood）

用接好的链路跑一个真实小型 converge（对象：某个小文档改动，单 reviewer + 单 executor 即可），验收：
- `archive_convergence.py archive` 返回成功
- done/ 路径只读 `check` 返回 valid-v1
- 事件序号连续、provenance 标注诚实、预算 ledger 无孤儿 reservation

### Phase 4 · 文档同步与收口

ocsr SKILL.md（派发驱动器节：对接能力说明）、converge `refs/framework-adapters.md` §A.1（OCSR 作为 Spawn 实现的接线说明）；两仓库 CHANGELOG；retrospective。

## 验收标准

1. Phase 3 三项全部通过（这是核心验收，机械可判）
2. ocsr/converge 既有测试全绿（有的跑 pytest，无的跑 selftest：`ocsr_dispatch.py selftest`）
3. 文档与实现一致（Reviewer 独立核对，不接受执行者自检）
4. 最终落地 diff 由 k3 亲自验收签字

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| glm 长链编排中途 compact/停滞 | converge state 文件抗 compact 设计；k3 可按状态文件换派 glm 续接；看门狗阈值按阶段设（编排链预计 1-2h，单 dispatch 看门狗 120min 或按阶段拆派） |
| 嵌套 spawn DB 锁 | Phase 0 smoke test 前置验证；错峰 ≥5s |
| 适配层设计过度 | Occam：只做事件流+预算两个钩子，其余挂"非目标" |
| 两仓库治理文档改动 | 本 plan 走 ultraverge；落地 diff 由 k3 终验 |

## 指挥结构操作细则

1. k3 把本 plan + orchestrator 指令（角色、状态文件规范、升级协议）经 OCSR 派给 glm-5.2
2. glm 每完成一个 Phase 写 `_phase-report.md` 到 active 目录；遇到宪法强制确认点写 `_escalation.md` 并停等
3. k3 在 Phase 边界/升级点介入：读报告、问用户、回写决策
4. 落地前 k3 亲自审 diff（不接受 glm 自检代终验）
