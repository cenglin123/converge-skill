# 文档一致性审计

> converge 的文档层验证模式。当 init-agent-docs 创建的文档体系随着时间漂移时，用独立 Reviewer 视角检测"文档声称的事实"与"代码/配置中的真实事实"是否一致。

## 定位

收敛体系目前覆盖了 **plan**（事前评议 + 事中 converge）和 **代码产物**（测试/lint 硬约束），但没有覆盖 **文档自身的准确性**。本模式补上这个盲区。

init-agent-docs 构建的信息流是**单向推送**：写入文档 → agent 读取 → agent 行动。但文档会腐化——六个月后 STRUCTURE.md 说"本项目用 SQLite"，实际已被迁移到 PostgreSQL——agent 基于过时信息做决策，且没有机制检测偏差。

本模式把 converge 的对抗验证理念从执行层推广到文档层。

## 触发条件

- 周期性维护（建议每 5 次 converge 或每月执行一次）
- 当 agent 在执行任务时依赖文档信息，但发现实际行动与文档描述不符
- 用户显式触发："审计文档一致性""检查文档是否过期"

## 流程

### 1. 盘点文档中的断言

Reviewer 读取目标项目的文档体系（AGENTS.md、STRUCTURE.md、docs/*.md），提取所有**可验证的事实断言**：

| 断言类型 | 文档来源 | 可验证来源 |
|---------|---------|-----------|
| 技术栈声明（"本项目使用 Python 3.12"） | docs/overview.md | pyproject.toml / .python-version / CI |
| 构建产物路径（"构建产物在 dist/"） | AGENTS.md 硬约束段 | package.json build script / CI config |
| 测试命令（"运行 pytest"） | docs/deployment.md | CI workflow / Makefile |
| 目录结构（"模块在 src/ 下"） | STRUCTURE.md | 实际文件系统（Glob） |
| API 约定（"返回 JSON，字段 camelCase"） | docs/api.md | 实际 API 响应 / schema 文件 |
| 架构描述（"微服务，三个独立部署单元"） | docs/overview.md | workspace config / Dockerfile / CI |
| 部署环境（"生产环境用 k8s"） | docs/deployment.md | k8s manifest / helmfile / CI deploy step |

**不应验证的内容**（信息密度低，不值得审计）：设计原因（"为什么选 SQLite"）、协作约定（"前后端同步"）、环境陷阱。这些不是"对错"问题，是"是否仍然适用"问题——归入建议项，不做阻断。

### 2. 逐条对比验证

Reviewer 对每条断言，读取对应的可验证来源，给出判定：

```yaml
audit_results:
  - document: docs/overview.md
    claim: "本项目使用 Python 3.12"
    verified_source: pyproject.toml#requires-python
    actual: ">=3.11"
    verdict: <match | stale | conflict>
    severity: <P0 | P1 | P2>
```

| verdict | 含义 | severity 默认 |
|---------|------|--------------|
| `match` | 文档与事实一致 | — |
| `stale` | 文档信息过时（如"Python 3.11"实际已 3.12） | P2 |
| `conflict` | 文档与事实矛盾（如"使用 SQLite"实际是 PostgreSQL） | P0 |

### 3. 输出审计报告

```markdown
---
type: document-audit-report
project: <项目名>
generated_at: <ISO datetime>
model: <模型标识>
---

## 审计范围
（列出审计了哪些文档、哪些验证来源）

## 对比清单

| # | 文档 | 断言 | 可验证来源 | 实际 | 判定 | 严重度 |
|---|------|------|-----------|------|------|--------|

## 问题分级

| 级别 | 数量 | 说明 |
|------|------|------|
| 🔴 P0 (conflict) | N | 文档与事实矛盾，agent 会基于错误信息决策 |
| 🟡 P1 (stale) | M | 文档过时但不直接误导 |
| 🟢 P2 (suggestion) | K | 信息密度低，建议而非阻断 |

## 结论
（对齐率 = match 数 / 总断言数）
```

### 4. 处置

- `conflict` 断言：Orchestrator 标记对应文档段为"待更新"，或直接修正文档（仅在用户授权时）
- `stale` 断言：记录到 health-report
- 审计报告写入 `docs/plans/active/` 或 `.meta/audit/`
- CHANGELOG 留痕

## 与现有机制的关系

| 机制 | 对象 | 本模式 |
|------|------|--------|
| converge | plan / 代码产物（事前/事中） | 互补——converge 审产物，本模式审文档 |
| audit（知识库审计） | Agent 行为 / 宪法执行（事后） | 同构——都是观察者角色，不自动修正 |
| testing-toolbox | 代码测试/lint | 互补——测试审代码，本模式审"代码的说明书" |

## 实施建议

- 初始频率：每 10 次 converge 或每月一次
- 审计范围：先覆盖 AGENTS.md 硬约束段 + docs/overview.md + docs/deployment.md，这三个信息密度最高、腐化后果最严重
- Pilot 后根据误报率调整断言提取粒度
