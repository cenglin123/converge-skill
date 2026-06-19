# Governance Decisions Log

> 治理文档（CONSTITUTION.md 第二部、SKILL.md 等）的人工审议批准记录。
> 宪法第二部约束"需经人工审议后修改，不接受 Agent 自主变更"——本日志为这类
> 修改提供可审计指针。**Agent 不得自行把条目标记为 `approved`**；状态从 `pending`
> 转为 `approved` 只能依据用户在对话中的明确确认，并由用户复核本记录无误。
> 不记录邮箱等无必要个人信息。

---

## GD-1 · CONSTITUTION 第二部「授权粒度澄清」追加

- **状态**：`approved`
- **日期**：2026-06-19
- **决策类型**：宪法第二部追加（澄清性，不改既有底线行）
- **内容**：在第二部表后追加"授权粒度澄清"段——明确"走 converge 并执行"只授权到**默认**预算上限，不授权预算扩展 / 模式切换接受 / 终止-b/c；超默认预算续跑须 round-stamped extension 令牌（关联真实 BLOCK decision + 用户原话）。
- **背景**：某执行侧 agent 31 轮失控（预算软停失效）复盘 → "budget-enforcement-hardening" 方案，经多轮人工编排审计收敛。
- **用户明确确认（2026-06-19，交互式确认）**：
  1. 第二部「授权粒度澄清」追加 → 用户选择 **"Yes, approve"**。
  2. 豁免**单独实现阶段 ultraverge**（以本次人工多轮审计 + 实现级对抗验收替代）→ 用户选择 **"Yes, waive it"**。
- **关联产物**：`CONSTITUTION.md` 第二部；`scripts/budget_gate.py` + `tests/test_budget_gate.py`；方案文件 `docs/plans/active/20260618-budget-enforcement-hardening.md`（`docs/` 被 .gitignore 忽略，为本地工作产物）。
