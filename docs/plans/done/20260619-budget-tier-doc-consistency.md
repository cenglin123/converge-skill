---
type: plan
status: active
created: 2026-06-19
converged: 2026-06-19
scope: 治理文档预算 tier/hook 语义一致性修复（仅文档，不动运行代码）
governance: true
note: 动 SKILL.md / refs 治理文档，按明线规则走 ultraverge（≥3 Reviewer + 收敛 + 设计审查）+ 人工提交批准
trigger: README 同步方案第一阶段暴露的治理文档残留 tier/hook 语义矛盾
related:
  - "SKILL.md"
  - "refs/orchestrator-guide.md"
  - "refs/state-schema.md"
  - "refs/reviewer-prompt.md"
  - "refs/framework-adapters.md"
---

# 治理文档预算 tier/hook 语义一致性修复

## 摘要

`budget_gate.py` 已落地两层能力：**auditable-only**（host-independent core，reserve/settle/ingest-verdict 由 Orchestrator 驱动）和 **best-effort guarded**（= hook-blocked auditable-only，Claude Code PreToolUse 总量硬上限兜底）。真正的 **enforced**（角色 FSM + 角色不可伪造 + 权限锁定）仍是 deferred。

但 SKILL.md 主循环和 orchestrator-guide.md 仍残留**旧语义**，错误暗示：
1. 当前存在 "enforced 宿主"，其 PreToolUse hook 自动执行 per-scope reserve；
2. 存在 PostToolUse hook 自动 settle；
3. 信任边界仍是旧的二元（enforced / auditable-only），未反映已落地的三层。

这些与运行代码（`budget_gate.py`）和 `refs/framework-adapters.md §A.1`（已正确描述 best-effort guarded）矛盾。本 plan 修复治理文档使其与运行实现对齐。**仅改文档，不动 `scripts/budget_gate.py` 或测试行为。**

## 不可逾越的约束（硬边界）

- **不得修改** `scripts/budget_gate.py` 或 `tests/test_budget_gate.py`（运行代码零 diff）
- **不得实现** opencode/Codex hook 或 true enforced
- **不得新增** `--format` 等未验证接口
- **不得** 把 `best-effort guarded` 称为 `enforced`
- **不得** 声称 opencode/Codex 当前已有硬阻断 hook
- **不得** 顺带重构其他无关内容

## 现状矛盾清单（逐条 + 证据）

### SKILL.md（治理入口）

**矛盾 1 — line 193**：`enforced 宿主由 PreToolUse hook 自动执行并可拒绝；auditable-only 宿主由 Orchestrator 执行并记录（责任清单 M-11）。`
- 问题：暗示当前存在 "enforced 宿主" 且其 PreToolUse hook **自动执行 per-scope reserve**。实际：无 enforced tier；PreToolUse hook 是 best-effort guarded，只强制总量 cap，**不执行 per-scope reserve**。

**矛盾 2 — line 194**：`spawn 后 budget_gate.py settle（enforced 宿主经 PostToolUse 自动；succeeded 须带 instance_id）`
- 问题：暗示存在 PostToolUse 自动 settle hook。实际：**当前不存在 PostToolUse settle hook**；settle 一律由 Orchestrator 手动驱动（M-11 已正确描述）。

**矛盾 3 — line 375**：`信任边界按宿主能力分级（enforced / auditable-only）`
- 问题：仍用旧二元分级，未反映已落地的三层（auditable-only / best-effort guarded / true enforced deferred）。

> 注：line 296（M-11）**已经正确**——明确 best-effort guarded 非 enforced、per-scope 由 Orchestrator 经 reserve 驱动、hook 独立计数器不写 ledger。本次不动 M-11 正文，仅确认其一致性。

### refs/orchestrator-guide.md

**矛盾 4 — line 171**：`enforced 宿主：reserve/settle 由 PreToolUse/PostToolUse hook 自动执行，Orchestrator 不得绕过；auditable-only 宿主：Orchestrator 手动执行并确保结果落 ledger。`
- 问题：同矛盾 1+2。暗示 enforced 宿主存在、PreToolUse 自动 reserve、PostToolUse 自动 settle。实际三类均不成立。

### refs/state-schema.md

**矛盾 5 — line 283 / 289**：reserved 事件 schema 标注 `tier(∈{enforced,auditable-only})`。
- 现状：这与运行代码一致（`budget_gate.py` `TIER_VALUES = {"enforced","auditable-only"}`、CLI `choices=["auditable-only","enforced"]`）。tier 是 ledger 记录字段，gate **不按 tier 值改变裁决逻辑**。但文档未说明：guarded 模式的 ledger tier 仍是 `auditable-only`，guarded 状态独立存于 binding 的 `mode=best-effort-guarded`。

**矛盾 6 — line 334**：`enforced tier 的宿主 PreToolUse/PostToolUse 接线、session→slug 绑定、角色 FSM 越权校验依赖宿主能力，属落地阶段待决设计点`
- 问题：把 "enforced tier 的 PreToolUse/PostToolUse 接线" 描述为待决，混淆了：best-effort guarded 的 PreToolUse 总量 hook **已落地**；PostToolUse settle **不存在**；true enforced 仍 deferred。

### refs/reviewer-prompt.md

**潜在误读 — line 300**：`前者驱动角色 FSM 转换（enforced tier）`
- 评估：括注可能被误读为 "角色 FSM 当前在 enforced tier 活跃"。实际：角色 FSM 是未来 true enforced 的输入；当前 guarded hook 不消费角色 FSM。仅在 ultraverge 判定确需消除误读时微调，不重写 prompt。

## 修复方案（逐文件）

### SKILL.md

**修复矛盾 1（line 193）** → 改为：所有当前模式的 per-scope reserve 由 Orchestrator 驱动；best-effort guarded 仅额外提供独立 PreToolUse 总量 cap，不执行 per-scope reserve。

**修复矛盾 2（line 194）** → 删除 "enforced 宿主经 PostToolUse 自动"；settle 一律由 Orchestrator 手动驱动（succeeded 须带 instance_id）。

**修复矛盾 3（line 375）** → 信任边界分级改为三层：`auditable-only` / `best-effort guarded (= hook-blocked auditable-only)` / `true enforced (deferred)`。

### refs/orchestrator-guide.md

**修复矛盾 4（line 171）** → 删除 "enforced 宿主 PreToolUse/PostToolUse 自动" 现状描述。明确：
- guarded 模式仍要手动执行 per-scope gate（reserve/settle 由 Orchestrator）；
- hook 不写 ledger；hook counter 与 ledger 不双计；
- bind/refresh-cap/unbind 只管理总量 backstop。

### refs/state-schema.md

**修复矛盾 5（line 283/289 附近）** → 加 tier 说明：ledger 的 `tier=auditable-only` 仍适用于 guarded 模式；guarded 状态记录在独立 binding 的 `mode=best-effort-guarded`；`tier=enforced` 保留给未来真正 enforced。不改 schema 枚举本身（与运行代码一致）。

**修复矛盾 6（line 334）** → 区分三层：auditable-only 完整可用；best-effort guarded 的 PreToolUse 总量 hook 已落地（PostToolUse settle 不存在）；true enforced deferred。

### refs/reviewer-prompt.md

**line 300** → 仅在 ultraverge 判定确需消除现状误读时微调括注（角色 FSM = 未来 true enforced 输入，当前 guarded hook 不消费）。不重写 prompt。

## 不变量（验收硬条件）

1. per-scope gate 始终由 Orchestrator 执行（两个已落地 tier 都如此）
2. guarded hook 只执行总量 cap（不执行 per-scope reserve/settle）
3. 当前不存在 PostToolUse 自动 settle
4. guarded 不被称为 enforced
5. true enforced 的 deferred 边界保持不变
6. 没有运行代码 diff（`scripts/budget_gate.py` / `tests/` 零变化）

## 验收命令

```powershell
rg -n "enforced 宿主|PostToolUse|best-effort guarded|auditable-only|true enforced" SKILL.md refs
python -W always::ResourceWarning tests/test_budget_gate.py
python -m py_compile scripts/budget_gate.py tests/test_budget_gate.py
git diff --check
```

期望：49 tests OK；治理文档中无 "enforced 宿主...自动执行" 或 "PostToolUse 自动 settle" 的现状描述；运行代码零 diff。

## 流程

本 plan 走完整 ultraverge：≥3 独立 Reviewer → 必要修复收敛 → 收敛后设计审查 → **人工提交批准**（执行 agent 不得自行 commit）。

## ultraverge 收敛记录

**评议**（≥3 并行独立 Reviewer，fresh context）：
- R1 verdict = `可执行`（无阻断；flag SKILL.md:348 为低优先级遗漏）
- R2 verdict = `阻断需修复`（B1: SKILL.md:348 误导；B2: M-11 "两个 tier" 与新 3-tier 冲突；N1: reviewer-prompt:300 事实错误；N2: 375 指向陈旧 plan）
- R3 verdict = `可执行`（无阻断；P1: 193 显式枚举；P2: 348；P3: 334 交叉引用；P4: 300 主动修复）

**收敛决策**（采纳阻断 + 精度项）：
- **B2/P1 采纳**：SKILL.md:193 改用显式枚举"两个已落地 tier"；SKILL.md:296（M-11）"两个 tier"补全为"两个已落地 tier（auditable-only / best-effort guarded），true enforced 仍 deferred"。
- **B1/P2 采纳**：SKILL.md:348 括注改为"无可阻断的 pre-spawn hook（未 bind 的 auditable-only 会话）"，区分 guarded（有 hook）。
- **N1/P4 采纳**：reviewer-prompt.md:300 删除"（enforced tier）"，改为"角色 FSM 是未来 true enforced 的输入，当前 guarded hook 不消费"（ingest-verdict 无 tier gate，FSM mode 在 auditable-only 即生效）。
- **P3 采纳**：state-schema.md:334 加交叉引用"升级要件见 refs/framework-adapters.md §A.1"。
- **N2 采纳**：SKILL.md:375 指针加陈旧标注。
- **原方案保留**：SKILL.md:194（删 PostToolUse）、orchestrator-guide.md:171、state-schema.md:283/289 + 334。

**新增矛盾（收敛追加，原清单未列）**：
- SKILL.md:296（M-11）"两个 tier"措辞与新 3-tier 冲突
- SKILL.md:348 括注 "auditable-only（无 pre-spawn hook）"对 guarded 误导
