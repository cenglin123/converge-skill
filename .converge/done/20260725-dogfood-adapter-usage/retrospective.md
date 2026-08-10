---
slug: 20260725-dogfood-adapter-usage
terminal_decision_event_id: 40808243-c717-4682-a2d8-1036395ba26d
terminal_decision_value: 可执行
terminal_type: 终止-a
blind_recheck: waived
generated_at: 2026-07-25T17:45:00+08:00
---

# Retrospective · dogfood-adapter-usage

## 终止决策
- **类型**：终止-a 严格首轮通过（R1 阻断 → executor 修复 → R2 可执行，零阻断）
- **terminal decision event**：通过 `archive_convergence.py record-terminal-decision` 登记引用 R2 reviewer terminal（event_id `8ddc663b-...`）。
- **用户确认**：无需（终止-a 默认自主）。

## 过程摘要
- **R1 reviewer**（mimo-v2.5-pro，outer-reviewer round 1）：发现 5 个 structural blocking issues（stub 空）。
- **R1 executor**（deepseek-v4-flash）：填写完整文档（3 行 → 140 行），写 attempts.md（4394B）。
  - **降级记录**：executor 的 invocation 在事件图中标为 `failed`，原因 = 路径不匹配（adapter watcher 期望 `executor-r1-reply.md`，但 executor 的实际交付是 "edit doc + write attempts.md"）。这是 faithful recording——archive Contract 捕获真实事件，包括失败路径。doc 内容本身已正确更新，R2 reviewer 独立验证通过。
- **R2 reviewer**（deepseek-v4-pro，outer-reviewer round 2）：verdict = 可执行，零阻断、零建议。

## 关键发现（dogfood 价值）

1. **适配层链路端到端工作**：reserve → begin-invocation → ocsr_dispatch → complete-invocation → settle 五步流水线在真实 opencode 调用下全部正确执行；事件图闭包（started+terminal 1:1）、sequence 连续、ledger 双写（gate-ledger + ocsr-dispatch-ledger）一致。

2. **provenance 诚实降级验证**：configured + cli_argument + backend-does-not-expose 组合通过 archive Contract 的 PROVENANCE_MATRIX 校验。`--instance-id`（ocsr batch_id）和 `--receipt`（ocsr-dispatch-ledger.jsonl:<rid>）作为非约束性关联句柄，不升格 evidence level。

3. **失败路径正确触发**：当 ocsr 退出 exit=0 但期望产物未落盘时（路径不匹配），适配层正确：
   - 检测"未落盘" → recover-invocation（status=failed, reason=backend-error, pre_execution=false）
   - settle failed（不是 cancelled，不是 succeeded）
   - 事件图正确记录失败 terminal

4. **预算 ledger 无孤儿**：每次 reserve 都有对应 settle；spawn invocation 都有 started+terminal 对。`budget_gate.summary` 显示 attempted_dispatch=3, model_invocation=3（含一次失败模型调用）。

## 已知限制 / 后续工作

- **适配层对 "edit X" 类任务的产物判定过严**：watcher 期望单一产物文件，但 executor 的真实交付可能是 "edit doc + write log"。**缓解**：调用方应让 executor 同时写一个 sentinel 文件（如 `done.marker`）作为 `--output-name`；或未来给适配层加 `--sentinel-only` 模式（用 exit_code=0 + 任意文件 landed 作 success 判据）。Phase 4 文档会写明此模式。
- **Phase 1 reviewer 留下的 6 条 suggestion 仍 deferred**：见 `_orchestrator-state.md` Verdict 记录。Phase 4 收口时 triage。

## 复盘判定
dogfood 目标全部达成：archive 链路打通，provenance 诚实，失败路径可观测，预算账本一致。**Phase 3 验收通过**。
