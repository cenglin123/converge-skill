# converge — 双 Agent 迭代收敛器

双 Agent 迭代收敛，专为 AI 生成产物设计。不同于脚本化工作流，converge 使用独立 Agent 之间的**对抗式审查循环**，通过迭代驱动质量提升——直到 Reviewer 给出 `可执行` verdict 或触发停止条件。

> **框架无关**：Reviewer / Executor 的启动和续命通过抽象能力层（Spawn / Continue / Identify）实现，不绑定特定框架 API。核心预算裁决脚本（file-authoritative `budget_gate.py`）同样宿主无关——reserve/settle/ingest-verdict 的语义在所有框架下一致。
>
> **预算执行分 tier**：核心 gate 虽宿主无关，但"能否在 spawn 前硬阻断"取决于框架是否提供可阻断的 pre-spawn hook。Claude Code 已落地 `best-effort guarded`（PreToolUse 总量兜底）；opencode / Codex 当前为 `auditable-only`；真正的 `enforced` 仍是未来能力。详见下方「预算执行」。

## 设计哲学

**不要告诉模型该怎么走。告诉它"到达"意味着什么，给它验证工具，让它自己找到路径。**

Converge 遵循两条宪法级设计原则：

**Bitter Lesson**（苦涩教训）：手动注入的工作流结构（规范、脚本、硬编码角色）会随着模型能力的提升而逐渐失效。取而代之的是，它定义**验收标准**（contract）、**验证工具**（lint、测试）和**对抗式反馈**（独立 Reviewer）——然后让模型自主探索，直到通过。机制层硬编码（三角色、对抗循环、契约驱动），领域知识层做成 compiled 产物（反模式注册表由真实收敛日志驱动、随命中频率自动衰减）。

**Occam's Razor**（如无必要，勿增实体）：每个文件、每条规则、每个字段必须回答"它解决什么具体问题"。解决不了具体问题的抽象一律拒绝。三层分离（机制/宪法/反模式）本身就是 Occam 的应用——不让会变化的反模式知识腐化在不变的机制里；章程瘦身（引用表替代 ~400 行重复模板）同理。已失效的信息（如迁移考古）删除，git log 是它的归宿。

## 工作原理

```
Round 0：合同谈判（可选前置）
  Executor 提出验收标准 → Reviewer 挑战 → 形成最终 contract.md

Round 1+：对抗收敛
  Reviewer（fresh 全新上下文）审计产物 → Executor 修复 → 重复

振荡检测：
  Type O（推翻）、Type R（重复）、Type F（翻转）、Type S（摆动）
  → 达到阈值后硬停或上报用户
```

| 角色 | 担任者 | 关键约束 |
|------|--------|----------|
| **Orchestrator** | 主对话 Agent | 不兼任 Reviewer/Executor；只管理循环 + 语义判定 |
| **Reviewer** | 每轮 Spawn 的独立 Agent | **全新上下文**（看不到历史对话）；prompt 自足 |
| **Executor** | 每轮 Spawn 的独立 Agent | 全新上下文；prompt 自足 |

## 终止状态与收敛判定

产物通过以下五种方式之一终止收敛循环（详见 `SKILL.md`）：

| 终止类型 | 一句话概要 |
|----------|-----------|
| **终止-a 严格首轮通过** | fresh reviewer 首轮 verdict = `可执行`，零阻断 |
| **终止-b 渐近通过** | blocking 单调下降至 ≤1 低级项，用户确认 |
| **终止-c 主观接受** | 用户明确说"够了" |
| **预算 gate 阻断** | gate 返回 `BLOCK:*`，无有效 extension 不得续 spawn；用户选择扩容 / 接受 / 简化 / 终止 |
| **振荡硬停** | Type O/R 达阈值，自动硬停 |

## 预算执行

收敛的 spawn 预算由确定性脚本 `scripts/budget_gate.py` 在每次 spawn 前后裁决，不靠 Orchestrator 记忆计数。执行链路：

```
reserve → Agent spawn → settle → ingest-verdict
```

- **reserve**：spawn 前申请额度；`PROCEED:<rid>` 方可 spawn，否则按裁决处置
- **settle**：spawn 后落账（succeeded 须带 instance_id）
- **ingest-verdict**：reviewer verdict 落盘后驱动 mode 记录与边际递减判定

### 当前能力 tier

| 模式 | 能力 | 当前框架 |
|------|------|---------|
| `auditable-only` | 通用；Orchestrator 调用 reserve/settle；ledger、extension 链和 pre-push hook 提供审计与阻断 | opencode、Codex 及所有框架（缺省） |
| `best-effort guarded` | Claude Code；在 auditable-only 基础上增加独立、单调的 Agent spawn 总量 hook（= hook-blocked auditable-only） | Claude Code |
| true `enforced` | 尚未实现；需要角色 FSM、角色不可伪造及权限锁定 | （deferred） |

> `best-effort guarded` **不是** `enforced`——只强制**总 spawn cap**：不执行 per-scope reserve/settle（仍由 Orchestrator 驱动）、不防主动删除或篡改 hook/binding、hook 不写 ledger 也不与 ledger 双计。它解决的是漂移、遗忘和 compaction 后失控。

### 预算阻断处置

达预算上限时 gate 返回 `BLOCK:budget_exhausted` / `blind_exhausted` / `ultraverge_exhausted` / `total_spawn_cap`：**停止**，无有效 `budget_extension`（须关联真实 BLOCK decision 事件 + 用户原话）不得续 spawn。用户选择：扩容续跑 / 接受当前产物（终止-c）/ 简化 plan / 终止。

## 适用场景

- 计划、规范或代码产物，在执行前需要独立交叉验证
- 复杂产物，单次审查不足以保障质量
- 质量关键型交付物，要求**零阻断**
- 可组合为 Dynamic Workflows 中的**质量门控**（L1 信号检测 + L2 单轮对抗审查）

## 不适用场景

- 单次快速审查（使用更轻量的 skill）
- Lint 级别的检查（使用实际的 lint 工具）
- 足够简单、不需要对抗验证的任务

## 目录结构

```
converge/
├── SKILL.md                  # 入口：Orchestrator 工作流 + 抽象能力层
├── scripts/
│   ├── budget_gate.py             # 预算 gate（file-authoritative，reserve/settle/ingest-verdict/bind + PreToolUse hook）
│   ├── l1_gate.py                 # L1 信号检测（非 LLM，零 token 成本）
│   ├── distill_antipatterns.py    # 反模式蒸馏器（全量编译 retrospective → status）
│   └── hooks/
│       ├── pre-commit             # 提交前检查
│       ├── pre-push               # 推送前检查（含孤儿 reservation / stale 检测）
│       └── stale-check.py         # active/ stale 项检测
├── tests/
│   └── test_budget_gate.py        # 预算 gate 验收用例（49 tests，stdlib only）
└── refs/
    ├── contract-negotiation.md    # Round 0：合同谈判流程 + contract.md 格式
    ├── decomposition-protocol.md  # 层级式并行收敛：分解协议、分阶段管控
    ├── orchestrator-guide.md      # 循环管理、振荡检测、状态跟踪
    ├── reviewer-prompt.md         # Reviewer prompt 模板 + 硬性规则
    ├── executor-prompt.md         # Executor prompt 模板 + 反模式防御
    ├── rubrics.md                 # 主观质量评分维度库
    ├── state-schema.md            # 跨轮状态持久化 schema
    ├── testing-toolbox.md         # 外部验证工具（lint、测试、hooks）
    ├── quality-gate.md            # 质量门控协议，用于 Dynamic Workflows 集成
    ├── design-review-prompt.md    # 收敛后设计审查：7 维骨架，单轮咨询式
    └── antipatterns.md            # 反模式注册表（compiled 产物，status 由 distill 维护）
```

## 验证

```powershell
python -W always::ResourceWarning tests/test_budget_gate.py
python -m py_compile scripts/budget_gate.py tests/test_budget_gate.py
git diff --check
```

期望：49 tests OK，无 ResourceWarning。预算 gate 不依赖外部库（stdlib only）。

