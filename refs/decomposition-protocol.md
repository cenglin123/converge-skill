# 分解协议 — 层级式并行收敛

> 当项目规模超出单次收敛的合理范围时，Planner 将任务分解为多个独立子收敛，并行执行，分阶段管控。

---

## 何时启用

Planner 在以下条件**同时满足**时启用层级模式：

1. 任务可分解为 ≥2 个互不干扰的独立 scope（文件范围 / 模块 / 文档）
2. 子任务间无实时数据依赖（如有依赖，按串联 phase 处理，见 §串联 phase）
3. 效率收益明确——并行节省的时间 > 分解 + 整合的开销

**不启用的情况：**

- 子任务边界模糊，强行拆分会增加边界冲突概率
- 任务总量小，单次收敛足够
- 子任务间有紧密依赖，拆开后协调成本超过收益

判断标准：**如果分解后子收敛间仍需频繁通信才能推进 → 不要拆。**

---

## 角色定义

| 角色 | 位置 | 职责 |
|------|------|------|
| **Planner** | 主控 agent | 分解任务、划定边界、分配预算、分阶段管控、整合结果 |
| **Orchestrator** | 子收敛 scope 的逻辑主控；可由 Planner 集中调度或 delegated subagent 承担 | 对单个 scope 跑完整 converge 循环（Reviewer ↔ Executor） |

Planner **不兼任**任何子收敛的语义判定者。这是硬约束——Planner 持有全局意图，不应被拉入局部修复细节。若平台不保证 subagent 可以继续 spawn 后代 agent，则采用集中调度：Planner 负责调度各 scope 的 Reviewer / Executor / Worker，但不替它们审查或修复。

---

## 执行模型：分阶段并行

### 为什么不能 fire-and-forget

子收敛运行期间通常**无法与 Planner 实时通信**，只能在阶段结束后返回结果。如果一次给满预算：

- 看不见：某个子收敛在第 4 轮挣扎，Planner 不知道
- 控不住：预算耗尽需要续费，但 subagent 无法中途请示
- 等不起：快的子收敛早完了，但被慢的阻塞

因此采用**分阶段（Phased）**模式：

```
Phase 1 → 同步点 → Phase 2 → 同步点 → ... → 整合
```

### 单阶段流程

```
1. Planner 读取 parent-state.md
2. 对每个 status = in_progress 的子收敛，构造阶段任务
3. 同时调度所有 in_progress 的子收敛：
   - centralized mode：Planner 直接 spawn 对应 scope 的 Reviewer / Executor / Worker
   - delegated mode：spawn 一个子收敛 subagent，由它在确认能力后内部运行 converge
4. 等待全部阶段任务返回
5. 读取每个子收敛的阶段汇报
6. 更新 parent-state.md
7. 在同步点做决策：
   - 全部 converged       → 整合 → 父级 verdict
   - 仍有 in_progress     → 检查预算 → 进入下一 phase 或 ask user
   - 有 boundary violation → 仲裁（见 §边界冲突仲裁）
```

### 阶段预算分配

每阶段给每个 `in_progress` 的子收敛分配固定轮数（默认 3 轮）。

Planner 在同步点可以：

- 对收敛趋势良好的子收敛继续分配预算
- 对收敛趋势停滞（阻断数不降）的子收敛调整 scope 或降级
- 将已完成子收敛的剩余预算重新分配给仍在进行的子收敛

预算分配记录在 `parent-state.md` 的阶段决策中。

---

## 文件格式

### 目录结构

```text
.converge/
├── active/
│   └── <parent-slug>/
│       ├── decomposition.md                 # 分解声明
│       ├── parent-state.md                  # 父级状态
│       ├── sub-report-<id>-phase-<N>.md     # 子收敛阶段汇报
│       └── <child-slug>/                    # 子收敛的工作目录
│           ├── contract.md
│           ├── round-N.md
│           ├── attempts.md
│           └── _orchestrator-state.md
└── done/
    └── <parent-slug>/
        ├── ... (上述所有文件)
        ├── <child-slug>/
        │   └── ... (子收敛完整产出)
        └── retrospective.md
```

### 分解声明（`decomposition.md`）

Planner 在 spawn 任何子收敛**之前**写入：

```markdown
---
parent_slug: <YYYYMMDD>-<project-name>
strategy: parallel
total_budget: <跨所有子收敛的总轮数预算>
phase_budget: <每阶段每子收敛分配的轮数，默认 3>
generated_at: <ISO datetime>
---

# 分解声明 · <project-name>

## 子收敛列表

### #1: <子任务简述>
- **scope**: <文件 glob 或模块路径>
- **对象路径**: <被收敛的 plan/代码路径>
- **budget**: <分配的总轮数上限>
- **boundary_assertions**:
  - <具体断言，如"不修改 src/api/ 目录下的文件">
  - <具体断言，如"接口签名变更需记录在 spec-delta.md">

### #2: <子任务简述>
...

## 整合规则
<integration_rule: all_converged | majority | custom>

## 已知依赖
<无 | 列出子收敛间的依赖关系>
```

**boundary_assertions 硬纪律：**

- 必须具体到文件路径/glob，不允许"尽量不改"
- scope 之间**不允许有文件交集**——如果两个子收敛可能改同一个文件，要么合并为一个子收敛，要么该文件划给其中一个并在另一个的 boundary_assertions 中声明"不修改"
- boundary_assertions 会被注入子收敛的 Reviewer prompt，作为验收断言的一部分

### 父级状态（`parent-state.md`）

每阶段结束更新：

```markdown
---
current_phase: <N>
total_budget: <总轮数>
budget_consumed: <已消耗>
status: <active | converged | failed>
---

# 父级状态 · <project-name>

## 子收敛状态

| # | 状态 | 阶段 | 轮数 | 上轮阻断 | Rubric (C/Co/Cs) |
|---|------|------|------|---------|-------------------|
| 1 | converged | 1 | 2 | 0 | 5/4/4 |
| 2 | converged | 1 | 1 | 0 | 4/4/5 |
| 3 | in_progress | 1 | 3 | 2 | 3/3/4 |

## 阶段决策记录

### Phase 1
- 决策: 子#3 仍有 2 阻断但趋势下降（7→4→2），续费 Phase 2
- 预算分配: 子#3 分配 3 轮

## 下一步
- resume 子#3，Phase 2
```

### 子收敛阶段汇报（`sub-report-<id>-phase-<N>.md`）

每个子收敛每阶段结束时写入：

```markdown
---
sub_converge_id: <N>
phase: <M>
status: <converged | in_progress | budget_exhausted | error>
rounds_this_phase: <本阶段消耗>
rounds_total: <跨阶段累计>
---

# 子收敛 #<N> · Phase <M> 汇报

## 收敛状态
- blocking_trajectory: <n → m → ...>
- blocking_remaining: <当前阻断数>
- rubric_scores: {C: <n>, Co: <n>, Cs: <n>}

## 边界合规
- boundary_violations: []  <!-- 有则列出具体文件和原因 -->

## 关键决策
- <影响其他 scope 或全局的决策，如接口签名变更>

## 文件变更
- files_modified: [...]
- files_created: [...]

## 请求
- <向 Planner 请求的资源/帮助，converged 则写"无">
```

---

## 整合规则

### 基本规则

| 情况 | 处置 |
|------|------|
| 全部 converged，无边界冲突 | 父级 verdict = 可执行 |
| 部分 converged，其余趋势良好 | 进入下一 phase 继续 |
| 有 boundary_violation | 触发仲裁（见 §边界冲突仲裁） |
| 有子收敛 error | 评估影响范围 → 局部重试或降级 |
| 全部 budget_exhausted 且未收敛 | 汇总未解决问题 → ask user |

### 收敛趋势判断

Planner 在同步点看两个指标：

1. **阻断轨迹**：单调下降 → 良好；持平或反弹 → 停滞
2. **Rubric 分数**：最低维度 ≥ 3 且上升中 → 良好；≤ 2 → 可能需要调整

**停滞判定**：连续 2 个 phase 阻断数未下降 → 标记为停滞，Planner 决定是否：
- 调整 scope（拆更细）
- 降级处理（接受 D11=b 渐近收敛）
- ask user

### 边界冲突仲裁

当两个子收敛修改了冲突文件：

1. Planner 读取两个子收敛的汇报，定位冲突
2. Spawn 仲裁 agent（独立 subagent），输入：
   - 冲突文件的原始版本
   - 子收敛 #A 的修改 + 修改理由
   - 子收敛 #B 的修改 + 修改理由
3. 仲裁 agent 返回裁决（采用 A / 采用 B / 合并方案 + 理由）
4. Planner spawn 仲裁执行 agent，按裁决修改冲突文件（Planner 自身不改文件，遵守设计约束 #2）

**仲裁只限一次**。若仲裁仍无法解决 → 标记为未解决冲突 → ask user。

### 串联 phase（有依赖的子收敛）

当子收敛间存在依赖（如"子#1 的接口设计是子#2 的输入"）：

1. 先并行执行无依赖的子收敛
2. 依赖上游的子收敛在后续 phase 启动，上游结果作为其输入
3. 每个依赖关系在 `decomposition.md` 的"已知依赖"中**显式声明**

```
已知依赖:
- 子#2 依赖子#1 的 spec-delta.md（接口签名变更记录）
- 子#3 无依赖
```

Planner 在 Phase 1 只 spawn 子#1 和子#3；子#1 converged 后，Phase 2 spawn 子#2 并将子#1 的 spec-delta.md 路径注入其 prompt。

---

## 子收敛 Prompt 模板

Planner 在 delegated mode 下 spawn 子收敛 subagent 时，构造如下 prompt。若使用 centralized mode，则 Planner 将同样的 Global Intent、scope、boundary assertions 注入该 scope 的 Reviewer / Executor / Worker prompt，而不是要求一个子 agent 自己继续 spawn：

```text
You are an Orchestrator running a converge cycle for a sub-task.

Before spawning descendants, confirm your environment exposes Spawn / Continue. If not, report `delegated_spawn_unavailable` and stop after writing the phase report; the parent Planner will continue this scope in centralized mode.

## Global Intent (残差连接 — 直接来自顶层 Planner，不经过中间层)

<global-intent.md 全文注入>

## Identity

You are sub-converge #<N> of a larger project.
Your scope is strictly limited to: <scope definition from decomposition.md>

## Boundary Assertions (MUST obey)

<boundary_assertions from decomposition.md>
任何超出 scope 的修改都是 boundary violation，即使看起来"顺手就能修"。

## Required reading

1. <被收敛对象路径>
2. <converge SKILL.md 路径>
3. <converge 子文件路径>: reviewer-prompt.md, executor-prompt.md,
   state-schema.md, orchestrator-guide.md, contract-negotiation.md, rubrics.md,
   decomposition-protocol.md
4. <如有上游依赖> <上游产出路径>

**IF Phase > 1（续接已有子收敛）**，额外必读：
5. <child-slug>/_orchestrator-state.md — 当前收敛位置
6. <child-slug>/attempts.md — 跨轮修复记录
7. <child-slug>/contract.md — 已完成合同谈判的终稿（如存在）

## Your task

**IF Phase = 1（首次启动）**：
Run a complete converge cycle:
- Round 0: 合同谈判（如适用）
- Round 1..N: Reviewer ↔ Executor 循环

**IF Phase > 1（续接已有子收敛）**：
Continue converge from where Phase <M-1> left off:
- 读取 _orchestrator-state.md 获取 current_round
- 从 current_round + 1 继续 Spawn Reviewer
- 保留已有 attempts.md 和 contract.md，不重新初始化

Budget for this phase: <phase_budget> rounds.
Total budget remaining: <total_budget - rounds_used> rounds.

## State management

Write all converge state to: .converge/active/<child-slug>/

## Constraints

1. ONLY modify files within your scope
2. If you discover issues outside scope, record in report but do NOT fix
3. Do NOT reference or rely on files outside your scope unless explicitly provided
4. When done (converged or budget exhausted), write report
5. If your local scope decisions conflict with Global Intent, prefer Global Intent and report the conflict
6. If you changed files, list changed paths and include a diff summary. Do not assume other subagents can see your workspace automatically.

## Output

Write phase report to: .converge/active/<parent-slug>/sub-report-<N>-phase-<M>.md
Report format: see decomposition-protocol.md §子收敛阶段汇报
```

---

## Retrospective 扩展

层级收敛的 retrospective 在标准格式基础上增加：

```markdown
## 11. 层级收敛评估

| 维度 | 评估 |
|------|------|
| 子收敛数量 | N 个 |
| 实际 phases | M 个 |
| 总预算消耗 | X / Y 轮 |
| 最快子收敛 | #<N>: <R> rounds |
| 最慢子收敛 | #<N>: <R> rounds |
| boundary_violations | N 次 |
| 仲裁触发 | N 次 |
| 并行效率 | 总 wall time vs 各子收敛串行 time 之和 |
| 分解质量 | scope 划分是否合理、有无遗漏/重叠 |
```

---

## 全局意图摘要（残差连接）

> 灵感来源：ResNet 的残差连接让深层网络也能接收到原始输入信号。同理，层级架构中所有层级的 agent 都应直接接收到顶层的全局意图，而非仅依赖中间层转述。

### 问题

层级越深，原始意图经过越多层压缩转述后衰减。即使中间层忠实传递，隐含假设和决策语境仍然会丢失。

### 解法：`global-intent.md`

Planner 在分解任务时写一份 **30-50 行**的全局意图摘要。这份文件作为"残差连接"，**直接注入所有层级 agent 的 prompt**，不经过中间层转述。

```markdown
# 全局意图 · <project-name>

## 一句话目标
<项目要达成的最终效果，一句话>

## 核心约束
- <不可违反的硬约束，3-5 条>
- <如：接口必须是 RESTful，认证走 OAuth2>

## 架构地图
<一张简单的结构图，让每个 agent 知道整体结构>
<如：前端(React) → API Gateway → Auth 服务 → 业务服务 → DB>

## 你的位置
（Planner 在注入每个 agent 的 prompt 时动态填充）
你是子收敛 #<N>，负责 <scope>。
你的产出将被 <下游消费者> 使用。
你的上游依赖是 <上游产出>。
```

### 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 谁写 | Planner | 只有 Planner 持有全局意图 |
| 谁能改 | 只有 Planner | 防止底层 agent 篡改全局意图；仲裁结果如涉及全局意图变更，Planner 在同步点统一更新 |
| 多长 | 30-50 行（~500 token） | 在 200K+ context 窗口中占比 <0.25%，可忽略 |
| 何时更新 | 每个同步点 | 解决陈旧信号问题 |
| 注入位置 | subagent prompt 最前 | 确保被优先阅读 |
| 注入范围 | **所有层级**的 agent | 不限于直接下级——这就是"残差"的含义 |

### 陈旧信号的处理

每个同步点，Planner 刷新 `global-intent.md`：

```
Phase 1:
  Planner 写 global-intent.md v1
  注入所有层级 agent → spawn

Phase 1 同步点:
  Planner 根据阶段结果更新 global-intent.md → v2
  （如："Auth 服务接口已确定为 RESTful，不再需要 GraphQL 方案"）

Phase 2:
  注入 v2 → spawn
  所有层级 agent 拿到最新全局意图
```

### 目录结构更新

```text
.converge/
├── active/
│   └── <parent-slug>/
│       ├── decomposition.md
│       ├── global-intent.md              # 全局意图摘要
│       ├── parent-state.md
│       ├── sub-report-<id>-phase-<N>.md
│       └── <child-slug>/
│           └── ...
```

### decomposition.md 格式更新

分解声明中增加 `global_intent_path` 字段：

```yaml
---
parent_slug: <YYYYMMDD>-<project-name>
strategy: parallel
total_budget: <总轮数预算>
phase_budget: <每阶段轮数>
global_intent_path: .converge/active/<parent-slug>/global-intent.md
generated_at: <ISO datetime>
---
```

---

## 设计约束

1. **两层是默认值，不是上限**。Planner → child scope 两层适用于绝大多数项目。深层（3+）需要 Planner 在分解声明中 justify：
   - scope 粒度分析：为什么当前项目天然需要更细粒度的分解
   - 并行收益估算：深层并行节省的墙钟时间 > 额外协调开销
   - 无 justify 则默认两层
2. **Planner 不改被收敛对象**。Planner 可以写 `.converge/` 元数据、分解文件和状态文件；代码/文档主体改动由 Executor/Worker 完成，或在集成阶段明确委派执行。
3. **子收敛之间不通信**。子收敛只与 Planner 通信（通过阶段汇报）。子收敛之间通过 boundary_assertions 和 decomposition.md 的"已知依赖"间接协调。
4. **子收敛内部保持标准 converge 语义**。不引入任何新的收敛机制——同样的 Reviewer prompt、Executor prompt、state 管理、合同谈判；实现上可由 Planner 集中调度，也可在确认能力后由 delegated subagent 执行。
5. **全局意图摘要必须注入所有层级**。这是残差连接的核心——每个 agent 都直接拿到顶层意图，不依赖中间层转述。
