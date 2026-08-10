---
type: pilot-report
object_slug: 20260621-mode-differentiation-and-fork-executor
generated_at: 2026-06-21T00:00:00Z
gate: 不变量 #8（fork-vs-fresh 抗锚定 pilot）
result: INCONCLUSIVE（real fork 在本环境不可用）
---

# Pilot Report · 不变量 #8 fork-vs-fresh 抗锚定对照

## 结论：INCONCLUSIVE —— Part B 保持 BLOCKED

`subagent_type: fork` **在本 Claude Code 环境不可用**（顶层与嵌套 spawn 均报 `Agent type 'fork' not found`；可用类型仅 claude / claude-code-guide / Explore / general-purpose / Plan / statusline-setup）。因此：

1. **pilot 无法忠实执行**——两个场景的 fork 臂都退化为 **fork-proxy**（用 prose 叙述模拟"继承锚定"，而非真正继承 orchestrator 对话状态）。两个运行 agent 均明确标注 proxy 是"materially weaker test / cannot confirm or deny / 不能替代真 fork"。
2. **Part B 机制本身在本环境不存在**——即便落地，converge 也只会走计划自带的"探测→降级 fresh"路径（B-1），在本环境零收益。
3. 故 **不变量 #8 在本环境无法满足**，Part B 不落地（诚实阻断，非仅程序性）。

## 实测数据（fork-proxy，弱证据）

| 场景 | fresh 臂 | fork-proxy 臂 | delta |
|------|---------|--------------|-------|
| A 数值反转 0.2→0.35 | final=0.35，未折中（未取 0.25/补丁）anchored=no | final=0.35，未折中 anchored=no | SAME（均未锚定）|
| B 结构切换 synced-bool→chunk-based | 干净切到 Approach A，无 synced 残留 anchored=no | 干净切到 A，无 synced_to_chunks shim anchored=no | SAME（均未锚定）|

> 解读：在**显式重申 §1-§3** 的条件下，prose 级模拟锚定被中和——两臂都干净执行反转。但这**仅证明**"显式重申足以中和 prose 级锚定"，**不证明**"真 fork 继承的对话级锚定也能被中和"。真 fork 携带 orchestrator 全程推理轨迹作为对话记忆，锚定强度远高于 prose 叙述。

## 复跑要件（解除 Part B 阻断的前置）

需在 `subagent_type: fork` **真实可用**的环境复跑（或用 Codex `multi_agent_v1.spawn_agent(fork_context=true)`，实测可用）：
- N>1 试验；含"中间值易合理化"的更难反转；
- 增设 **no-reaffirmation 对照臂**，隔离"是 fork 本身还是 §1-§7 重申在起作用"；
- 测 composed 路径（forked executor → 自主落地 → blind=1）的反模式出现率 vs fresh 基线。

## 对计划的反馈
- 本发现**强化** B-1「fork 是探测能力，不支持则降级 fresh」——CC 部署间 fork 可用性不一致，必须运行时探测。
- framework-adapters §A.1 应记录：CC `subagent_type: fork` 由 harness 文档描述，但**本部署未暴露**（→ 探测后降级 fresh）。已随 B-8 落地。
- pilot 工件：`.converge/tmp/pilot/A|B/`（gitignored）。
