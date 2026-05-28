# 文档一致性审计

> converge 的文档层验证模式。当项目的文档体系（如 AGENTS.md、STRUCTURE.md、docs/ 层级）随着时间漂移时，用 Reviewer→Executor 的对抗写回循环检测并**自动修复**文档偏差，而非仅报告。

## 定位

收敛体系目前覆盖了 **plan**（事前评议 + 事中 converge）和 **代码产物**（测试/lint 硬约束），但没有覆盖 **文档自身的准确性**。本模式补上这个盲区，走 converge 标准的多轮写回路径：
1. Reviewer 提取文档断言并对比代码/配置事实
2. 有 conflict → Executor 修正文档 → Reviewer 重新验证
3. 直到零 conflict 或触停止条件

本模式在时态上属于**事后验证**（文档已漂移 → 检测 → 修复），但反馈路径走 converge 的多轮写回而非 audit 的单次观察。

## 触发条件

- 周期性维护（每 5 次 converge 或每月执行一次）
- 当 agent 在执行任务时依赖文档信息，但发现实际行动与文档描述不符
- 用户显式触发："审计文档一致性""检查文档是否过期"

## 流程（converge 多轮模式）

### Round 0：合同谈判（可选）

可跳过（本模式的工作范围天然由文档体系定义）。若跳过，Reviewer 默认审计范围：AGENTS.md 硬约束段 + docs/overview.md + docs/deployment.md。若启用 Round 0，按 `contract-negotiation.md` 协商审计范围（覆盖哪些文档、排除哪些断言类型）。

### Round 1：Reviewer 提取断言并对比

Reviewer 读取目标项目的文档体系，提取**可验证的事实断言**，逐一对比可验证来源。

#### 断言提取规则

1. **初始深度**：首轮提取 15-30 条信息密度最高的断言（优先 AGENTS.md 硬约束段 → docs/overview.md → docs/deployment.md → docs/api.md → 其他）
2. **排除内容**：不可客观验证的陈述不纳入——设计原因（"为什么选 SQLite"）、环境陷阱（"Windows 上需先装 VS Build Tools"，这类经验性内容"适用性"而非"正确性"）、协作约定仅在可通过配置验证时才纳入（如 "所有 PR 需 review" 可通过 GitHub branch protection 设置验证）
3. **规格文档区分**：描述目标状态的设计文档（如 ARCHITECTURE.md 中的"计划迁移到 k8s"）不纳入一致性审计——其可验证来源是 plan 文件而非当前代码

#### 断言类型与可验证来源

| 断言类型 | 文档来源示例 | 可验证来源（优先级递降） |
|---------|------------|----------------------|
| 技术栈声明（"本项目使用 Python 3.12"） | docs/overview.md | pyproject.toml / .python-version / CI workflow |
| 构建产物路径（"构建产物在 dist/"） | AGENTS.md 硬约束段 | package.json scripts / CI config |
| 测试命令（"运行 pytest"） | docs/deployment.md | CI workflow / Makefile / task runner config |
| 目录结构（"模块在 src/ 下"） | STRUCTURE.md | 文件系统（Glob） |
| API 约定（"返回 JSON，字段 camelCase"） | docs/api.md | API schema 文件 / 实际响应 |
| 架构描述（"微服务，三个独立部署单元"） | docs/overview.md | workspace config / Dockerfile / CI |
| 部署环境（"生产环境用 k8s"） | docs/deployment.md | k8s manifest / helmfile / CI deploy step |

> 可验证来源的发现流程参照 `testing-toolbox.md` 的命令发现方法，避免 Reviewer 自行猜测。

#### 输出格式

Reviewer 的输出直接作为 round-N.md 的 Reviewer 完整输出：

```yaml
round: {N}
verdict: <可执行 | 阻断需修复>
blocking_issues:
  - id: 1
    document: docs/overview.md
    claim: "本项目使用 Python 3.12"
    verified_source: pyproject.toml#requires-python
    actual: ">=3.11"
    verdict: conflict  # match | stale | conflict
    description: |
      文档声称 Python 3.12，实际 requires-python=">=3.11"，文档限定了一个具体版本而实际接受范围版本。
    plan_amendment_required: false
    location: docs/overview.md §技术栈
```

#### 判定标准

| verdict | 含义 | 示例 |
|---------|------|------|
| `match` | 文档与事实一致 | 文档说 3.12，`python-version` 文件是 3.12 |
| `stale` | 文档信息过时但不直接误导 | 文档说 3.11，实际已升级到 3.12 |
| `conflict` | 文档与事实矛盾，agent 会基于错误信息决策 | 文档说用 SQLite，实际 `DATABASE_URL` 指向 PostgreSQL |

**部分真值处理**：当文档声明的范围与实际范围不一致时——文档声明是实际范围的子集 → `stale`（信息不完整），文档声明是实际范围的超集 → `conflict`（包含错误断言），文档声明与实际范围有交集但不重合 → `conflict`。

阈值：所有 verdict 为 `conflict` 的断言自动成为 blocking_issues。

#### 对齐率口径

不计算单一对齐率——按 `conflict` 密度和 `stale` 密度两个指标分别报告：

```
conflict 密度 = conflict 数 / 总断言数
stale 密度 = stale 数 / 总断言数
```

一个 conflict 密度 10% 的审计比 stale 密度 40% 的审计更紧急，合并计算会掩盖这个差异。

### Round 1+：Executor 修复 + Reviewer 重审

1. Executor 只修复 `conflict` 断言（`stale` 不触发修复——信息过时不值得立即修正，记录到 health-report 即可，由用户择机决策）
2. 修复后 Executor 在 attempts.md 追加 entry（格式同 converge 标准 attempt log）
3. 同一 Reviewer 重审修复结果（同 context 内验收，通过 `SendMessage` 续命）
4. 重审仅检查：(a) conflict 是否已修正；(b) 修正是否引入了新 conflict
5. 零 conflict → 收敛成立

## 产物目录

走 converge 标准目录结构：

```
.converge/active/<YYYYMMDD-doc-audit-<项目>>/
├── contract.md            # Round 0 产物（可选，跳过则不生成）
├── round-1.md             # Reviewer 审计报告
├── round-2.md             # 重审报告（如有）
├── attempts.md            # Executor 修复记录
├── _orchestrator-state.md
└── retrospective.md       # 收敛完成后
```

## Reviewer Prompt 模板

Orchestrator 在 spawn Reviewer 时拼装以下 prompt：

```text
You are a document consistency auditor. This is Round {N}.

## Required reading
1. Project AGENTS.md (behavior rules + hard constraints)
2. Project STRUCTURE.md (if exists, doc index)
3. Project docs/*.md (overview, deployment, api, pitfalls — as applicable)
4. This charter: <document-audit.md path>

## Your task

Extract 15-30 **verifiable factual claims** from the project documentation.
For each claim, locate the actual truth source (code, config, CI, file system)
and compare.

Claim extraction priority:
1. AGENTS.md hard constraints section (highest information density)
2. docs/overview.md (tech stack, architecture)
3. docs/deployment.md (deploy environment, startup commands)
4. docs/api.md (if exists)
5. STRUCTURE.md (directory claims only — verify with Glob)

Do NOT extract:
- Design rationale ("why SQLite")
- Environment traps ("first build needs setup.sh")
- Collaboration conventions (unless GitHub branch protection settings can verify them)
- Target-state descriptions in design docs (not yet implemented)

For partial truth: doc subset of reality → stale; doc superset of reality → conflict;
doc and reality overlap partially → conflict.

## Output format

```yaml
round: {N}
verdict: <可执行 | 阻断需修复>
blocking_issues:
  - id: N
    document: <path>
    claim: "<exact quote from doc>"
    verified_source: <file#section>
    actual: "<what the source actually says>"
    verdict: <match | stale | conflict>
    description: |
      <one paragraph explaining the discrepancy>
    plan_amendment_required: false
    location: <doc section>
```

All `conflict` items become blocking_issues. All `stale` items go into suggestion_issues.
`match` items are listed in a separate `matched_claims` array for the report.
```

## Reviewer 自检清单（Pilot 后追加模板化）

Orchestrator 在 spawn 时不额外注入——以下由 Reviewer 在开始工作前自检：

- [ ] 是否已读 AGENTS.md 硬约束段
- [ ] 是否已读 docs/overview.md 技术栈/架构声明
- [ ] 是否已读 docs/deployment.md 部署/环境声明
- [ ] 是否参照 `testing-toolbox.md` 的命令发现流程定位可验证来源
- [ ] 是否区分了规格文档（目标状态）和参考文档（当前状态）
- [ ] 断言数量是否在 15-30 条范围内
- [ ] 每条 conflict/stale 是否引用了具体文件行或配置键

## 与现有机制的关系

| 机制 | 对象 | 时态 | 反馈路径 | 本模式 |
|------|------|------|---------|--------|
| converge（plan/code） | plan / 代码产物 | 事中 | 多轮写回 | 机制同构，对象不同 |
| audit | Agent 行为 / 宪法执行 | 事后 | 不写回 | 与本模式不同——本模式走 converge 写回，**主动修正** |
| testing-toolbox | 代码测试/lint | 事中 | 测试结果 | 互补——测试审代码，本模式审代码的说明书 |

## 实施建议

- 初始频率：每 5 次 converge 或每月一次
- 审计范围：先覆盖 AGENTS.md 硬约束段 + docs/overview.md + docs/deployment.md
- 断言提取粒度：首轮 15-30 条，pilot 后根据 conflict 密度调整——密度太低（< 5%）说明提取太保守，密度太高（> 30%）缩小范围
- Pilot 收敛后视复盘决定是否将 Reviewer 自检清单模板化到独立文件
