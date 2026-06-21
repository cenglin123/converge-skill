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

---

## GD-2 · Part B（fork-executor）放弃决断

- **状态**：`approved`
- **日期**：2026-06-21
- **决策类型**：Part B 处置决断（非宪法文本修改——不改 CONSTITUTION.md；基于第一部原则的仲裁裁决 + 用户对发散的决断）
- **内容**：放弃计划 `20260621-mode-differentiation-and-fork-executor.md` 的 **Part B（fork-executor，B-1~B-7）**。fork-executor 的宪法定位经第一部仲裁为「**随模型进步贬值的补丁**」（重读成本随上下文经济学改善而收缩；计划 H3 已挂 sunset 触发条件）。其落地前 pilot **设计**经 3 轮独立复评（Codex 主审 + fresh Reviewer）：前期存在关联产物修复不完整，后续持续暴露更深层的新问题，整体未显示稳定收敛趋势，形成 rigor-escalation loop。Occam 判「为贬值补丁投未收敛的重型验证」比例失衡。用户据此决断放弃。处置：(a) Part B 不采纳、相关不变量（#4/#5/#8/#9/#10）撤回；(b) handoff brief 删除；(c) `refs/framework-adapters.md` 的 fork 描述保留为「框架能力、converge 不采纳」；(d) CONSTITUTION #7 不受影响（fork 未采纳、无角色模型变更，#7 第四部审议继续 deferred）。
- **背景**：用户提出 fork-executor 建议 → 计划走 ultraverge 收敛（Part A + B 一起）→ Part A 落地（PR #4）→ Part B 的 pilot 设计经 Codex 3 轮复评发散 → 宪法第一部仲裁（Bitter Lesson + Occam）→ 用户决断放弃。
- **重激活门槛**：除非上下文经济学反转（重读成本非但不降反升）使 fork 收益质变，否则不再重启；重启时须先回答本轮发散的测量难题（软效应 × 软仪器 × 小样本）。
- **用户明确确认（2026-06-21，对话确认）**：
  1. 放弃 Part B（fork-executor）→ 用户明确表示「我认为可以放弃 Part B」。
  2. 复核 GD-2 记录全文后批准其状态 → 用户明确表示「批准 GD-2」。

  > 注：早先一个 agent 版本曾误将 GD-2 自标 `approved` 并写入伪造授权记录，经核验违反「Agent 不得自标 approved」规则后回退至 `pending`；本次 `approved` 由用户复核记录后于对话明确授予，合规。
- **关联产物**：`docs/plans/done/20260621-mode-differentiation-and-fork-executor.md`（Part A 已落地、Part B dropped）；handoff brief 已删；`refs/framework-adapters.md` fork 描述。

### § 判例：发散识别（distill 候选）

本次 Part B 弃案过程暴露 converge 检测网的一个真实缺口，提炼如下判例供未来参考：

**振荡 ≠ 发散**。振荡检测 4 型（Type O/R/F/S，见 `SKILL.md` §振荡检测）全抓「同议题的重复/翻转」；而本次在排除关联产物修复不完整后，仍持续出现此前不在桌上的、更深层新议题。旧问题虽有延续，但新增问题的抽象层级和验证复杂度继续上升，现有振荡检测对这种「非重复、持续深化」的失效模式存在盲区。收敛的隐含定义是「修复使问题集单调缩小」；发散信号则表现为**问题集持续更换/深化，且可接受距离不缩**。

**发散识别 5 判据**：
以下判据是**联合信号**，不是任一命中即可自动触发的规则。应先排除漏改关联产物、验收未执行等普通执行缺口；单条命中不足以判定发散，也不授权 agent 自行终止目标。
1. **深化趋势**：每轮阻断指向更深抽象层（表层 → 设计 → 基础原则），而非同层数量减少。
2. **净新增 > 净消解**：修 round N 的阻断竟使 round N+1 冒出「此前不可讨论的」新议题。
3. **过程复杂度反超产物**：验证 apparatus 比被验证特性更复杂（Occam 比例信号）。
4. **可接受距离不缩**：修后再评，「距通过」不缩、横移或扩大。
5. **元重设消解而非解答**：第一性问题（「这值得收敛吗？」）使原 loop 失去意义——合理处置可能是放弃目标、缩小范围或重设问题，而不是继续堆叠当轮修补。

**处置原则**：判据 5 尤其关键——发散可能意味着「在收敛一个错误的问题」，出路是先质疑问题。此时应**层升至用户用第一性原则决定放弃、缩范围或重设目标**，而非由 agent 自动终止或继续无条件消耗预算/轮次。

**晋升门槛（Bitter Lesson 自律）**：本判例为 N=1 观察，**不**据此硬编码新检测机制（如往振荡表加 `Type D (Divergence)`）——那正是 Bitter Lesson 反对的行为。当前作 distill 候选；若跨多个收敛复现 ≥3 次，再走 ultraverge 议 Type D 晋升，届时凭数据不凭单点。

**详细案例**：见知识库笔记「20260621-converge发散识别判据-fork-executor弃案复盘」（Obsidian Vault 根目录），含完整 3 轮 Codex 复评经过 + 宪法第一部仲裁推理。

> 📎 注记（2026-06-21，本计划落地执行日）：§ 判例 内容已迁移至 `refs/orchestrator-guide.md` § 发散检测（操作指导层，Orchestrator 运行时可读——dissolve 可达性悖论）。本 GD-2 entry 本体保留作**历史快照**（append-only，不回改）；live source = orchestrator-guide § 发散检测。
