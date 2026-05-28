# Rubrics 评分维度参考

> 为 Reviewer 提供显式评判维度，使"好"可量化、跨 Reviewer 可比。借鉴 GEP 的 Rubrics 机制。

---

## 维度库

| 维度 | 适用对象 | 定义 |
|------|---------|------|
| **正确性 (Correctness)** | 通用 | 交付物是否满足验收断言 |
| **完整性 (Completeness)** | 通用 | 是否覆盖所有断言，无遗漏 |
| **可维护性 (Maintainability)** | 代码 / 文档结构 | 后续修改是否容易，耦合度 |
| **简洁性 (Conciseness)** | 文档 / 代码 | 无冗余，无过度工程 |
| **一致性 (Consistency)** | 通用 | 与仓库现有风格/规范是否对齐 |
| **原创性 (Originality)** | UI / 设计 | 是否避免千篇一律的模板化输出 |

---

## 选用规则

Orchestrator 根据收敛对象类型从维度库中选取，写入 contract.md 的 `rubric_dimensions` 字段：

| 对象类型 | 默认维度 |
|---------|---------|
| **Plan 文本** | 正确性 + 完整性 + 一致性（3 维度） |
| **代码项目** | 正确性 + 完整性 + 可维护性 + 简洁性（4 维度） |
| **含 UI 的项目** | 在上述基础上 + 原创性（5 维度） |

Orchestrator 可在 contract.md 中为具体对象调整维度与权重，但**必须显式声明**。

---

## Reviewer 输出扩展

当 contract 中定义了评分维度时，Reviewer 在 YAML 输出中增加 `rubric_scores` 字段：

```yaml
rubric_scores:
  - dimension: Correctness
    score: 3          # 1-5 分制
    evidence: "<一句话引用具体证据>"
  - dimension: Completeness
    score: 2
    evidence: "..."
```

**评分标准**：

| 分数 | 含义 |
|------|------|
| 1 | 严重不足，多项断言未满足 |
| 2 | 有明显缺口，部分断言未满足 |
| 3 | 基本满足，有改进空间 |
| 4 | 充分满足，小问题可忽略 |
| 5 | 超出预期，无可挑剔 |

---

## 与 verdict 的关系

Rubric 分数是 verdict 的**辅助信号**，不替代 verdict：

- verdict 仍由 Reviewer 综合判断给出
- **若所有维度均 ≥ 4**，verdict **必须**为 `可执行`——除非 Reviewer 能明确指出 Rubric 未覆盖的问题
- 此时 Reviewer **必须**在 blocking_issues 中至少给出一个具体 issue 且标注 `rubric_gap: true`
- Orchestrator 统计 `rubric_gap` 触发次数，在 retrospective 中评估维度库是否需扩展

---

## Retrospective 评估

收敛完成后，retrospective 中增加 Rubrics 评估段：

| 维度 | 评估 |
|------|------|
| 使用的维度 | 哪些维度被使用 |
| 未使用的维度 | 是否有维度从未被引用或总被评高分（→ 考虑移除或替换） |
| rubric_gap 触发次数 | N 次（Reviewer 认为 Rubric 未覆盖的问题） |
| 跨轮分数趋势 | 各维度分数在轮次间的变化 |
