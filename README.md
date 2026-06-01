# converge — 双 Agent 迭代收敛器

双 Agent 迭代收敛，专为 AI 生成产物设计。不同于脚本化工作流，converge 使用独立 Agent 之间的**对抗式审查循环**，通过迭代驱动质量提升——直到 Reviewer 给出 `可执行` verdict 或触发停止条件。

> **框架无关**：Reviewer / Executor 的启动和续命通过抽象能力层实现，不绑定特定框架 API。

## 设计哲学

**不要告诉模型该怎么走。告诉它"到达"意味着什么，给它验证工具，让它自己找到路径。**

Converge 遵循"苦涩教训"（Bitter Lesson）：手动注入的工作流结构（规范、脚本、硬编码角色）会随着模型能力的提升而逐渐失效。取而代之的是，它定义**验收标准**（contract）、**验证工具**（lint、测试）和**对抗式反馈**（独立 Reviewer）——然后让模型自主探索，直到通过。

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

## 收敛判定

| 方式 | 判据 |
|------|------|
| **严格首轮通过**（默认） | fresh reviewer 首次审查 verdict = `可执行`，零阻断 |
| **渐近** | blocking_issues 单调下降 + 剩余 ≤1 个无争议低级项，用户确认后接受 |
| **主观接受** | 未达上述标准，但用户明确说"够了，就这样" |

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
│   └── l1_gate.py            # L1 信号检测（非 LLM，零 token 成本）
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
    └── antipatterns.md            # 反模式注册表（compiled 产物，status 由 distill 维护）
```

## 最近变更

### 2026-06-01 · 机制/宪法/反模式三层分离

**宪法依据**：Bitter Lesson（元原则 III）——将"命中频率会变化的领域知识"（反模式）从"能随模型变强的机制"（三角色、对抗、契约）和"不可让渡的构成性约束"（宪法级）中物理分离。

**改动摘要**：
- 新建 `refs/antipatterns.md`：10 个具名反模式（executor ×4、design ×4、orchestrator ×2），带 `status` / `layer` / `zero_streak` 字段，作为 compiled 产物
- `SKILL.md`：Red Flags 重组为"宪法级约束"小节（7 条不可让渡底线 + 修宪门槛声明）；原 #1/#6 迁入 antipatterns.md
- `refs/reviewer-prompt.md`：硬编码 antipattern 清单替换为 `{antipatterns_active}` 动态注入占位符
- `refs/state-schema.md`：retrospective §3 "类型"列加硬约束（必须用 antipatterns.md id 或 `new:` 前缀）
- `refs/orchestrator-guide.md`：Spawn 前自检清单加 `<antipatterns_path>`

**评议历史**：
- v1 提案 + 三方对抗评议（提案作者 / 知识库宪法 agent / 提案作者自评）
- v2 终版（本次执行的依据）
- `scripts/distill_antipatterns.py` 延后至 retrospective ≥ 10 时实现
