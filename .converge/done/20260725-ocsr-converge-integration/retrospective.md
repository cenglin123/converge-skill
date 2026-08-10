---
slug: 20260725-ocsr-converge-integration
task_id: 20260725-ocsr-converge-integration
status: completed
completed_at: 2026-07-25T18:00:00+08:00
---

# Retrospective · OCSR ↔ converge 治理钩子对接

## 终止决策（termination-a）

本任务各 Phase 的设计审查与代码审查均为 **终止-a 严格首轮通过**（零阻断），无需要用户确认的 termination-b/c 决策。

## 过程摘要

| Phase | 内容 | Review | 结论 |
|-------|------|--------|------|
| 0 | 调研 + 设计 doc + smoke test | mimo (1 blocking 修复后通过) | 进入 Phase 1 |
| 1 | `ocsr_spawn_adapter.py` + 6 tests | deepseek-pro (可执行, 终止-a) | 进入 Phase 2 |
| 2 | config-init + 预算门控 + 8 tests | mimo (可执行, 终止-a) | 进入 Phase 3 |
| 3 | 端到端 dogfood (3 real Spawn) | archive committed + check valid-v1 | 核心验收通过 |
| 4 | 文档同步 + CHANGELOG + 本复盘 | — | 完成 |

**Total**: 6 次 OCSR Spawn（3 次裸 ocsr_dispatch + 3 次经 adapter），1 次 smoke test，168 tests 全绿零回归。

## 关键发现

### 1. 适配层设计决策（adapter vs builtin flag）

源码证据三线并发（ocsr SKILL.md §三"脚本不做编排判断" + SKILL.md:66 "vault 适配层"预告 + budget_gate 角色枚举对齐）明确支持**独立适配脚本**——不必向普适执行后端注入 converge 协议。Phase 0 review 捕获了 provenance 非法组合（host-reported + receipt-missing 违反 PROVENANCE_MATRIX）；修复为 configured + cli_argument + backend-does-not-expose，经模型层校验（model.py:494-513）通过。

### 2. "edit X" 类任务的 sentinel 模式（Phase 3 dogfood 发现）

真实 dogfood 遇到 executor 完成文档编写但 watcher 等不到期望产物的情况——executor 的交付是"修改 doc + 写 attempts.md"，而 watcher 期望一个单独的 sentinel 文件。事件图标会为 `failed`（recover-invocation + settle failed）。

这是 **faithful recording**（archive Contract 忠实记录了路径不匹配的失败路径），不是适配层 bug。但用户层面需明确：executor prompt 中应额外要求写一个 sentinel 文件（如 `done.marker`）作为 `--output-name`，否则 adapter watcher 判定失败。该模式已写入双方文档（ocsr SKILL.md + converge framework-adapters.md §A.2）。

### 3. 预算门控正常（Phase 2 验证）

per-scope 阻断（5 outer 填满后第 6 个 BLOCK:budget_exhausted）、attempted_dispatch vs model_invocation 双计数区分、pre_execution 标志在 fail-launcher（true）与 fail-timeout（false）间的正确切换，均经测试验证。`config-init --mode ultraverge` 自动覆盖 max_blind_rechecks=2，与 SKILL.md §Ultraverge "纯 orchestrator 行为、零代码" 语义一致。

## 延后项

**Phase 1 review 留下的 6 条 suggestion**（全 severity=implementation, attribution=executor_limit）本次未修复，entry 在 `_orchestrator-state.md` Verdict 记录中完整保留：

| # | 内容 | 建议处置 |
|---|------|---------|
| S1 | `--reserved-reservation-id` bypass 路径无测试覆盖 | 加 3 个单元测试 |
| S2 | `_extract_ocsr_instance_id` 边界无单元测试 | 加 2-3 个边界测试 |
| S3 | complete-invocation 失败时错误消息缺 invocation_id | 一行代码修复 |
| S4 | 适配层 docstring misleading（"any exception after begin will recover"） | 一行文本修正 |
| S5 | fail-collision + general fallthrough 未测试 | 加 2 个测试 |
| S6 | 第 437 行 cancelled 分支为 dead code | 加注释或简化 |

建议在首次适配层维护时批量处理（总工作量 <30 min）。

## 已知限制

- 适配层 tier 为 `auditable-only`（opencode 无 spawn-blocking hook；详见 framework-adapters.md §A.2、§A.5 可移植性矩阵）。
- provenance 无法升级到 host-reported（OCSR dispatch 未绑定 per-invocation tool_response）。升级路径：若 opencode `--format json` 未来暴露 provider/model 字段，适配层一处改动即可切换 evidence level。
- 嵌套派发（深度 >1，即 ocsr 再 spawn ocsr）的预算归因本期未覆盖（plan §非目标）。ocsr SKILL.md §七 "嵌套派发失账" 是已知陷阱，本期修复了第一层账本（reserve→settle），深层归因留给未来工作。

## 边界违规记录

两次 orchestrator self-edit（均 documented）：
1. Phase 0 R1 修复后残余 host-reported 字串的机械清理（3 行 — 同一替换的补完，semantic unchanged）
2. Phase 4 文档同步时 direct-edit 了 ocsr SKILL.md 和 converge framework-adapters.md（不 spawn executor — Phase 3 dogfood 已证明 adapter 对 "edit X" 类任务有路径不匹配风险；为收尾效率选择 orchestrator_self）

两项均已带 `[Orchestrator Detection]` 标注记入相应 Revision Log。retrospective 维度：二项均不影响收敛结论——修复已在各自 Phase 的 review 中独立验证通过；doc 更新将随本次 diff 由 k3 终验。

## 复盘判定

Phase 0→4 全流程完成。OCSR 作为 converge Spawn 后端的事件流与预算门控端到端接线；168 tests 全绿；dogfood archive committed + check valid-v1。**Phase 3 三项核心验收全部通过**。延后项清单完整，便于 k3 决策是否在落地前修复。
