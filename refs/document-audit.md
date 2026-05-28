# 文档一致性审计

> 项目文档会漂移。六个月前写的"本项目使用 SQLite"，现在后端跑的是 PostgreSQL。文档审计做一件事：取文档中的事实断言，去代码和配置里逐条对账，不一致就标出来。**只观察，不修改。** 如有 conflict，输出报告交给标准 converge 流程接管修复。

## 定位

本模式是**审计**（事后、不写回），不是 converge。按 SKILL.md 的语义边界——审计只记录不裁决，converge 做多轮写回。文档审计负责前半段（找出问题），converge 负责后半段（修对问题）。

## 触发条件

- 用户显式触发："审计文档一致性""检查文档是否过期"
- 当 agent 在执行任务时依赖文档信息，但发现实际行动与文档描述不符
- 周期性维护（建议每 5 次 converge 或每月一次，由项目维护计划决定，本模式不内置调度）

## 流程

### 1. Spawn Reviewer 做审计

Orchestrator 按下方 Reviewer Prompt 模板 spawn 独立 Reviewer，产出审计报告。

### 2. 判定并分流

Orchestrator 读 Reviewer 输出：

- **零 conflict**：审计通过，报告归档。
- **有 conflict**：以审计报告为输入，触发标准 converge 运行。此次 converge 的**产物是修正后的文档**，走完整 converge 流程——合同谈判（协商修复范围）、每轮新 Reviewer、D11 裁决、振荡检测、retrospective。

Stale 断言不触发 converge，记录到 health-report 即可。

### 3. 报告放置

审计报告写入 `docs/plans/active/`（作为后续 converge 的 plan 输入）。converge 产物走标准 `.converge/active/<slug>/` 目录。

## Reviewer Prompt 模板

```text
You are a document consistency auditor. This is a single-pass audit, NOT a convergence loop.

## Required reading
1. Project entry files: AGENTS.md, CLAUDE.md, GEMINI.md (note: these should be identical; if not, flag as a finding)
2. Project STRUCTURE.md (if exists)
3. Project docs/*.md (overview, deployment, api, pitfalls — as applicable)
4. This charter: <document-audit.md path>

## Your task

Extract 15-30 **verifiable factual claims** from the project documentation.
For each claim, locate the actual truth source (code, config, CI, file system)
and compare.

Claim extraction priority:
1. Entry files hard constraints section — also check if AGENTS.md / CLAUDE.md / GEMINI.md are in sync
2. docs/overview.md (tech stack, architecture claims)
3. docs/deployment.md (deploy environment, startup commands)
4. docs/api.md (if exists)
5. STRUCTURE.md (directory claims only — verify with Glob)

Do NOT extract:
- Design rationale ("why SQLite")
- Environment traps ("first build needs setup.sh") 
- Collaboration conventions (unless config-verifiable, e.g. GitHub branch protection)
- Target-state descriptions in design docs (not yet implemented)

## Verdict rules

| verdict | meaning | example |
|---------|---------|---------|
| match | doc matches reality | doc says 3.12, .python-version is 3.12 |
| stale | doc outdated but not directly misleading | doc says 3.11, actual is 3.12 |
| conflict | doc contradicts reality, agent would make wrong decisions | doc says SQLite, DATABASE_URL points to PostgreSQL |

Partial truth: doc claims subset of reality → stale (incomplete). Doc claims superset of reality → conflict (wrong). Partial overlap → conflict.

Important: when doc and code/config conflict, do NOT assume doc is wrong. The doc may reflect correct design intent and the code may have drifted. Flag the contradiction without assigning blame — the subsequent converge run will determine which side to fix.

## Output format

```yaml
audit_result:
  total_claims: N
  match_count: N
  stale_count: N
  conflict_count: N
  conflict_density: "<conflict_count / total_claims>"
  stale_density: "<stale_count / total_claims>"

matched_claims:
  - document: <path>
    claim: "<exact quote>"
    verified_source: <file#section>
    actual: "<what source says>"

stale_claims:
  - document: <path>
    claim: "<exact quote>"
    verified_source: <file#section>
    actual: "<what source says>"
    note: "<why stale not conflict>"

conflict_claims:
  - id: N
    document: <path>
    claim: "<exact quote>"
    verified_source: <file#section>
    actual: "<what source says>"
    description: |
      <nature of contradiction — does NOT prescribe which side to fix>
    location: <doc section>
    possible_interpretations:
      - "doc is correct, code/config drifted"
      - "code/config is correct, doc is stale"
```

If conflict_count > 0, the audit report becomes the input to a standard converge run.
The converge run's deliverable is the fixed documentation.
```

## 与 converge 的衔接

审计报告产出 conflict 后，Orchestrator 启动一次标准 converge，收敛对象为**被标记的文档**：

1. Round 0 合同谈判：Executor 提议修复范围（只修 conflict 还是连 stale 一起修）、Rubrics 维度、完成标准
2. Round 1+：标准 converge 流程——每轮新 Reviewer、D11 裁决、振荡检测
3. 修复不限于文档——如果 conflict 的根因是代码错误（如文档正确但实现偏差），则修复代码而非文档
4. 产物写入 `.converge/active/<YYYYMMDD-doc-fix>/`

## Reviewer 自检清单

- [ ] 是否已读入口文件（AGENTS.md / CLAUDE.md / GEMINI.md），三者是否内容一致
- [ ] 是否已读 docs/overview.md 技术栈/架构声明
- [ ] 是否已读 docs/deployment.md 部署/环境声明
- [ ] 是否参照 `testing-toolbox.md` 的命令发现流程定位可验证来源
- [ ] 是否区分了规格文档（目标状态）和参考文档（当前状态）
- [ ] 断言数量是否在 15-30 条范围内
- [ ] 每条 conflict 是否标注了双向可能的解释（doc 错 vs code 错）
- [ ] 是否仅做观察，未尝试修改任何文件

## 与现有机制的关系

| 机制 | 本模式 |
|------|--------|
| converge | 审计报告产出 conflict → 触发标准 converge 修复文档（或代码） |
| audit | 同构——事后观察，不写回 |
| testing-toolbox | 互补——测试审代码，本模式审"代码的说明书" |
