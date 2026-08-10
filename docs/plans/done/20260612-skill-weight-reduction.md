---
type: plan
status: active
created: 2026-06-12
scope: SKILL.md 减重（附录 A + 层级模式外提）
governance: true
note: 将附录 A（框架适配）外提为 refs/framework-adapters.md，层级模式精简为引用
related:
  - "SKILL.md"
  - "refs/framework-adapters.md"
  - "refs/decomposition-protocol.md"
---

# SKILL.md 减重方案

## 摘要

SKILL.md 当前 545 行 / 40KB / ~3,700 tokens。token 成本和模型性能不是问题，但信噪比影响 Orchestrator 导航效率。将两个"一次只用一个"的大段外提为独立 refs 文件，SKILL.md 只留引用和启用条件。

## 问题陈述

SKILL.md 的直接消费方是 Orchestrator——每轮操作需要找到正确段落拼装 prompt、做语义判定、检查清单。文件越长，两个相关段落距离越远，漏读或误关联概率越高。

当前内容分布：
- **附录 A（框架适配）**：5 个小节（A.1–A.5：4 个框架 + 通用降级 + 适配新框架），~71 行。一次只用一个框架，其余全是噪声。
- **层级模式**：完整架构段落 + 启用条件 + 执行模型 + 关键约束，~50 行。启用条件严格（三个同时满足），绝大多数收敛不触发。
- **核心流程**（主循环、责任清单、必检、参数表）：~200 行。必须在 SKILL.md 正文。
- **其余**（Positioning、Pilot 经验、目录结构、拆分文件索引）：~100 行。辅助定位，保留。

## 减重方案

### 改动 1a：附录 A → `refs/framework-adapters.md`

将 SKILL.md 附录 A 全部 5 个小节（A.1–A.5）移至新文件 `refs/framework-adapters.md`。新文件保留原 A.x 小节编号（A.1–A.5），不重编号，以维持内部交叉引用完整性。

SKILL.md 原位置（附录 A 整段，第 474–544 行）替换为：

```
> 框架适配实现见 `refs/framework-adapters.md`（Claude Code / opencode / codex / 通用降级 / 适配新框架）。
```

SKILL.md 第 50 行（`附录 A：Claude Code / opencode / codex 的具体实现。`）同步更新为指向新文件，与上方替换文本职责合并：附录 A 原位的替换文本保持极简（仅一行引用），第 50 行提供结构化入口。

### 改动 1b：更新 SKILL.md 内 5 处"附录 A"引用

| 行号 | 当前文本 | 替换为 |
|------|---------|--------|
| 10 | `（附录 A）` | `（见 refs/framework-adapters.md）` |
| 50 | `附录 A：Claude Code / opencode / codex 的具体实现。` | 见改动 1a 说明 |
| 67 | `附录 A.3 codex 约束 #4` | `refs/framework-adapters.md §A.3 codex 约束 #4` |
| 72 | `见附录 A.4` | `见 refs/framework-adapters.md §A.4` |
| 214 | `按附录 A.2/A.4 降级` | `按 refs/framework-adapters.md §A.2/A.4 降级` |

### 改动 2：层级模式精简为引用

`refs/decomposition-protocol.md` 已存在。SKILL.md 的"层级模式"小节精简为：

```
## 层级模式（Planner → 多个 Orchestrator）

> 当项目规模超出单次收敛的合理范围时，可启用层级式并行收敛。详细协议见 `refs/decomposition-protocol.md`。

**启用条件**（三个同时满足）：

1. 任务可分解为 ≥2 个互不干扰的独立 scope
2. 子任务间无实时数据依赖
3. 并行效率收益 > 分解 + 整合的开销

**关键约束**：
- **Planner 不改被收敛对象**
- **子收敛之间不通信**
- **子收敛内部运行标准 converge 语义**
```

删除：架构图、执行模型（分阶段并行）、Planner 详细职责。这些已在 `refs/decomposition-protocol.md` 中。

### 改动 3：拆分文件索引更新

在拆分文件索引表中增加一行：

```
| 框架适配：Spawn/Continue/Identify 的具体实现 | `refs/framework-adapters.md` |
```

## 文件改动清单

| 文件 | 改动 |
|------|------|
| `SKILL.md` | 附录 A 替换为 1 行引用；5 处内部"附录 A"引用更新为新文件路径；层级模式精简为启用条件 + 关键约束；拆分文件索引 +1 行 |
| `refs/framework-adapters.md` | 新建，内容为原附录 A 全文（保留 A.1–A.5 编号） |
| `CONSTITUTION.md` | 更新 1 处"附录 A.4"引用（第 49 行） |
| `refs/orchestrator-guide.md` | 更新 1 处"附录 A.4"引用（第 143 行） |

## 不做的事

| 砍掉的操作 | 理由 |
|-----------|------|
| 核心流程外提 | Orchestrator 每轮必读，外提增加导航成本 |
| 责任清单外提 | 同上 |
| 配置参数表外提 | 同上 |
| Pilot 经验速查外提 | 4KB，且对 Orchestrator 决策有参考价值 |
| 目录结构外提 | 导航锚点，保留在正文 |
| 合并 refs/ 文件 | 反方向——refs/ 的存在就是为了降低 SKILL.md 体积 |

## 风险评估

| 风险 | 等级 | 缓解 |
|------|------|------|
| Orchestrator 无法找到框架适配细节 | 低 | 替换文本明确指向 `refs/framework-adapters.md`；拆分文件索引有入口 |
| 层级模式启用时 Orchestrator 误读精简版 | 低 | 关键约束保留在 SKILL.md；详细协议在 decomposition-protocol.md |
| 外提后 SKILL.md 仍 >30KB | 低 | 改动 1a 减 ~71 行，改动 1b 净增 0 行（原地替换），改动 2 减 ~35 行，合计减 ~106 行 / ~19% |

## 自举声明

本方案首次落地发生在协议生效前（自举窗口）。首次落地时应遵循本方案定义的 plan-execution 流程。
