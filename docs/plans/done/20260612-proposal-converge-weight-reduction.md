# Proposal: Converge 减重 — 折叠监督 + 频次追踪 + 数据驱动蒸馏

> 提交给：converge SKILL 维护者 / 执行侧 agent
> 来源：主对话 agent（Orchestrator），compact 后上下文漂移 + 自重累积讨论
> 日期：2026-06-12（R2 修订版，响应 ultraverge R1/R2/R3 + Design Review 7 条阻断 + 3 条设计级发现）

---

## 背景

近期两次 converge 自举事件暴露了两个交织的问题：

1. **Orchestrator 边界违反**（已修复：guard step + 责任清单 #3 + Reviewer 审计 #7）——Orchestrator 直接修改产物而非 spawn Executor
2. **Converge 自重增长**（未修复）——每次防御一个漏洞，就在 converge 循环中增加一个检查项

这些机制的添加均有实证基础（guard step、boundary_check、边界审计 #7 来自两次 Orchestrator 边界违反事件；antipattern 巡查在 pilot #3 被独立确认有效）。问题是**没有机制让已有规则退出**——每个机制在添加时解决了真实问题，但随着 converge 运行数据积累，部分机制可能已不再需要，而它们仍在消耗每次 spawn 的 token。

当前 converge 的单轮开销中，"管理 converge 自身"的 token 占比在持续上升。guard step、boundary_check、门控 L1/L2 判断、设计审查触发判断、反模式注册表注入、compact 哨兵——累积起来让 converge 的 prompt 越来越长，审查越来越慢。

## 核心洞察

Converge 面临的结构性张力：

- **Bitter Lesson**：手工硬编码的约束（guard step、检查清单条目、审计规则）会随着时间累积，最终超过搜索和验证所能提供的价值
- **Occam**：每个新机制必须回答"它解决什么具体问题"，而"可能发生的问题"不是充分理由
- **防御纵深 vs 自重**：多层防护降低单点失败概率，但每层都有 token 成本——需要数据来判定价效比

最近两次 Orchestrator 违反证明 guard step 是需要的。问题不在于机制本身，而在于**没有数据驱动的退出机制**——只有人手动加进去，没有人（或机制）基于使用数据让它们退场。

## 方案：三阶段渐进

### 阶段 1：折叠（回收 Meta-Reviewer 提议，零新开销）

不建 Meta-Reviewer 新实体。将意图漂移检测折叠为 Orchestrator 注入 + Reviewer 产物验证的两步机制。

**改动**：两处联动修改——

**改动 A**：`refs/reviewer-prompt.md` 的审查维度中增加一段（放在现有"升级复查"段之后、"Output format"段之前）：

```markdown
### 意图漂移检查（条件激活，由 Orchestrator 注入触发）

若 Orchestrator 在 prompt 中传入了 `<drift_context>` 块（见下方说明），则在输出前检查：

1. 阅读 contract.md（若存在），对比当前产物的核心方向是否与 Round 0 合同一致
2. 结合 Orchestrator 注入的 drift_context（包含 progress_summary 摘要），检查当前产物是否存在超出合同定义的 scope creep
3. 若发现方向性漂移 → 列为 suggestion issue（severity: conceptual），标注 `drift_detected: true`

此检查仅在 Orchestrator 注入 drift_context 时激活——单轮快速评议不触发。
（注：`source: orchestrator_self` 的降级影响标注已由硬纪律 #7 覆盖，本段不重复。）
```

**改动 B**：`refs/reviewer-prompt.md` 的 YAML output format 中，在 `suggestion_issues` 条目结构增加可选字段：

```yaml
suggestion_issues:
  - description: ...
    drift_detected: <true | false>  # 可选，仅当意图漂移检查激活且发现漂移时标注
```

**Orchestrator 侧改动**：`SKILL.md` 主循环步骤 c 中增加条件注入逻辑——当 `escalated_issues` 存在或 `contract_amendment_required` 反复出现（≥2 次）时，Orchestrator 在拼装 reviewer prompt 时注入 `<drift_context>` 块，包含 `_orchestrator-state.md` 的 `progress_summary` 摘要。**Reviewer 不直接读取 `_orchestrator-state.md`**——由 Orchestrator 负责提取并注入。

**与责任清单 #6 的关系**：责任清单 #6（plan 漂移检测）是 Orchestrator 第一方的**循环内检测**（每 5 轮或触 Type O 时），检测的是 plan 内容在收敛过程中的偏移。本方案的意图漂移检查是 Reviewer 独立第三方的**产物-合同对齐检测**（条件激活），检测的是当前产物是否偏离了 Round 0 合同定义的方向。两者视角不同（第一方 vs 第三方）、触发条件不同（间隔+事件 vs 条件注入）、检测对象不同（plan 内容偏移 vs 产物-合同方向偏差），互补而非重叠。

**新增 token 成本**：reviewer-prompt.md 增加约 7 行条件激活段 + YAML 格式增加 1 行可选字段。Orchestrator 注入 drift_context 时增加约 2-3 行文本。仅在条件激活时生效（大多数轮次不触发）。零新实体、零新 spawn、零新 Required Reading。

**理由**：这个折叠保持了角色边界——Orchestrator 负责循环状态管理（提取 progress_summary、判断是否注入），Reviewer 负责产物验证（对比 contract 与产物）。意图漂移的检测需要对比"当前产物 vs 原始意图"，而 contract.md 恰好是原始意图的锚点。Reviewer 在已有读取路径上增加检查维度，不读取额外文件。

### 阶段 2：追踪（建立频次驱动的规则活性追踪）

建立 converge 自身规则的"使用频次 → 活性状态"追踪机制。**阶段 2 只记录和报告，不执行运行时衰减。** 规则的实际移除走阶段 3 的人确认流程。

**核心逻辑**：如果一个检查项在过去 N 次 converge **任务**中被触发过，它是活跃的。如果连续多次任务未触发，标记为待评估。阶段 2 不干预 prompt——只产出数据供阶段 3 蒸馏。

**计数单位**：任务级，字段名 `zero_streak`（与 `distill_antipatterns.py` 统一命名）——一个 converge 任务（从 Round 0/1 到收敛完成计为 1 次），而非单个轮次。10 次收敛任务即可积累足够数据（按当前频率约 1-2 个月）。

**实现**：

1. **规则 key 注册表**。在 `_orchestrator-state.md` 增加 `rule_frequency` 段，使用统一的规则 key：

```yaml
rule_frequency:
  boundary_guard: {triggered: true, zero_streak: 0}
  reviewer_boundary_audit: {triggered: true, zero_streak: 0}
  intent_drift_check: {triggered: false, zero_streak: 5}
  gate_l1: {triggered: false, zero_streak: 7}
  design_review_trigger: {triggered: true, zero_streak: 2}
```

**规则 key 注册表**（权威来源，与 `refs/antipatterns.md` 的 id 机制同构）：

| 规则 key | 对应机制 | 触发检测方式 | 分类 |
|----------|----------|-------------|------|
| `boundary_guard` | 主循环 c+1 guard step | `boundary_check: violated` in `_orchestrator-state.md` | guard |
| `reviewer_boundary_audit` | Reviewer 硬纪律 #7 | `source: orchestrator_self` in `attempts.md` | guard |
| `intent_drift_check` | 本方案阶段 1 意图漂移检查 | `drift_detected: true` in reviewer YAML output | guard |
| `gate_l1` | 门控 L1 信号检测 | L1 gate 脚本执行记录 in `_orchestrator-state.md` | guard |
| `design_review_trigger` | 设计审查触发判断 | 设计审查 spawn 事件 in `_orchestrator-state.md` | guard |

新增 guard mechanism 时，在此注册表追加条目并指定触发检测方式。未在注册表中的规则不被追踪。

2. **实时触发记录**。Orchestrator 在每轮执行时**即时记录**规则触发（而非在 retrospective 写入时回溯重建），避免 context compaction 导致的触发遗忘：

- `boundary_guard`：主循环 c+1 步骤执行时，将结果写入 `_orchestrator-state.md`（已有 `boundary_check` 字段）
- `reviewer_boundary_audit`：Orchestrator 处理 reviewer 输出时，检测 attempts.md 是否有 `source: orchestrator_self` 条目
- `intent_drift_check`：Orchestrator 处理 reviewer 输出时，检测 `drift_detected: true` 标记
- `gate_l1`：Orchestrator 执行 L1 gate 脚本时记录
- `design_review_trigger`：Orchestrator 决定 spawn 设计审查时记录

每轮结束时更新 `rule_frequency` 的 `triggered` 字段。`zero_streak` 由阶段 3 distill 脚本跨收敛对象计算（不在单个收敛对象的 state 中维护跨对象累计值）。

3. **衰减阈值**（pilot 参数，仅用于阶段 3 蒸馏时的 advisory report 分级，不驱动运行时行为）：

**统一状态机**（复用 `distill_antipatterns.py` 的 active/dormant/archived 三级，不引入新状态）：

| 分类 | 连续未触发任务数 (zero_streak) | 状态 | 阶段 3 蒸馏建议 |
|------|------|------|------|
| guard mechanism | 0-4 | active | 保留 |
| guard mechanism | 5-9 | dormant | 降级为条件激活 |
| guard mechanism | ≥10 | archived | 建议移除，retrospective 中记录 |
| 核心机制 | 0-19 | active | 保留 |
| 核心机制 | 20-39 | dormant | 建议降级（需人确认） |
| 核心机制 | ≥40 | archived | 建议移除（需人确认 + ultraverge） |

核心机制的阈值远高于 guard mechanism——这是"差异化的保护强度"而非"永久豁免"。核心机制包括：前置自检 Q1-Q5、确定性检查、升级复查三态标记、振荡硬停、预算软停、Reviewer fresh context 约束。当前注册表仅追踪 guard mechanism。核心机制已预留差异化阈值架构（20/40），其规则 key 注册和触发检测方式定义在后续迭代中完成——当 guard mechanism 的追踪流程经过足够验证（≥10 次收敛任务）后，再扩展到核心机制。

**自指处理**：本方案新增的追踪机制本身不进入 `rule_frequency`——它是数据采集层，不是被采集的 guard mechanism。其成本（每轮 ~1 行 YAML 更新）远低于被追踪的 guard mechanism 的 token 成本，不构成同等级的自重问题。追踪机制自身属于硬编码行为约束（与 guard step 同类型），但其生命周期管理通过以下机制保证：(1) 每次收敛的 retrospective 中必须包含一段对"追踪机制本次执行成本"的评估（约 1 句话：是否正常工作、是否有异常）；(2) 当被追踪规则总数降至 2 条以下时，retrospective 中必须显式评估追踪机制是否仍有必要；(3) 任何对追踪机制本身的修改（新增/移除追踪规则、调整阈值）需经人确认。

**层级收敛交互**：层级模式下，每个子收敛有独立的 `_orchestrator-state.md` 和 `rule_frequency`。子收敛的触发数据归子收敛所有——Planner 级 guard mechanism（如 gate_l1）在 Planner 的 state 中追踪，子收敛级 guard mechanism 在子收敛 state 中追踪。阶段 3 distill 脚本按收敛对象独立扫描，不假设层级关系。

**变动文件**：
- `refs/state-schema.md`：`_orchestrator-state.md` 增加 `rule_frequency` 段 + 规则 key 注册表
- `SKILL.md` Orchestrator 责任清单（条件触发类）：增加一条 "规则触发记录 — 在现有 boundary_check 更新（步骤 c/c+1）时顺带更新 rule_frequency；gate_l1 和 design_review_trigger 在对应事件发生时更新。不新增独立循环步骤"

**不变动**：
- `SKILL.md` 配置参数段不增加（无运行时衰减逻辑，阈值仅在 distill 脚本中使用）
- `SKILL.md` 主循环不增加结构性步骤
- Reviewer prompt 不增加（追踪不干预 prompt 拼装）

### 阶段 3：蒸馏（扩展 `distill_antipatterns.py` 到规则活性）

`distill_antipatterns.py` 当前只蒸馏反模式。扩展到同时蒸馏 guard mechanism 的活性。

**改动**：

1. **retrospective 模板增加格式化节**（`refs/state-schema.md`）。在 retrospective 模板的 `## 成本数据（可缺省）` 节之后增加 `## Rule Activity` 节（固定位置，编号紧跟上节），格式固定：

```markdown
## Rule Activity

| rule | triggered | zero_streak | status |
|------|-----------|-------------|--------|
| boundary_guard | true | 0 | active |
| reviewer_boundary_audit | false | 3 | dormant |
| intent_drift_check | false | 5 | dormant |
```

status 由阈值表自动计算。格式固定——脚本从 Markdown 表格解析，不依赖自由文本。

2. **扩展 `distill_antipatterns.py`**：

- 新增 `--rules` 模式（与现有 `--antipatterns` 模式并行，不干扰已有功能）
- 输入源：`retrospective.md` 的 Rule Activity 表
- 跨收敛对象聚合：按收敛对象独立扫描，对同一规则取 `zero_streak` 最大值。报告按收敛对象分列，同时提供跨对象汇总（汇总标注数据来源数量和置信度）
- 状态机：复用 active/dormant/archived 三级（与反模式一致），按分类使用不同阈值
- 输出：全规则活性报告，标记 active/dormant/archived 状态，对 dormant/archived 给出移除建议
- 不自动修改 SKILL.md——产出 advisory report，人确认后手动移除或降级

3. **pilot 参数治理**：衰减阈值（5/10 guard, 20/40 core）作为 `distill_antipatterns.py` 的 `--rules` 模式专有 CLI 参数实现（如 `--guard-dormant-threshold 5 --guard-archive-threshold 10 --core-dormant-threshold 20 --core-archive-threshold 40`），不存储在 `antipatterns.md` frontmatter 中——规则活性和反模式活性是两个独立领域，阈值分开管理。参数调整不涉及宪法级文件修改，仅在 distill 脚本层面。

**目标**：让 converge 的规则集从"手工设计 + 永远不删"变成"日志驱动 + 数据说话 + 人确认删除"。符合 Bitter Lesson——通用搜索机制优于硬编码规则集。

### 阶段优先级和依赖

```
阶段 1（折叠）          独立可执行，零依赖
阶段 2（追踪）          独立于阶段 1（不修改 reviewer-prompt.md）
     ↕（无依赖，可并行实施）
阶段 3（蒸馏）          依赖阶段 2 积累的频次数据（≥10 次收敛任务）
```

阶段 1 和阶段 2 相互独立，可并行实施。阶段 1 只改 `refs/reviewer-prompt.md`；阶段 2 只改 `refs/state-schema.md` + `SKILL.md` 责任清单。阶段 3 依赖阶段 2 积累至少 10 次收敛任务数据。

**迁移**：已有 `.converge/active/` 目录下的 `_orchestrator-state.md` 没有 `rule_frequency` 段。首次遇到缺失字段时，Orchestrator 初始化为全 active（所有规则的 triggered=true, zero_streak=0）。不需要版本标记或迁移脚本——缺失即初始化。

## 改动范围

### 阶段 1

| 文件 | 改动 |
|------|------|
| `refs/reviewer-prompt.md` | 增加"意图漂移检查"段（条件激活，~7 行）+ YAML output format 增加 `drift_detected` 可选字段 |
| `SKILL.md` 主循环步骤 c | 增加条件注入 drift_context 逻辑（~2 行） |

### 阶段 2

| 文件 | 改动 |
|------|------|
| `refs/state-schema.md` | `_orchestrator-state.md` 增加 `rule_frequency` 段 + 规则 key 注册表 |
| `SKILL.md` Orchestrator 责任清单（每轮必做类） | 增加一条"规则触发记录 — 每轮结束时更新 rule_frequency" |

**零运行时逻辑变更**。频次更新在现有 boundary_check 更新步骤中顺带完成，不新增独立循环步骤。

### 阶段 3

| 文件 | 改动 |
|------|------|
| `refs/state-schema.md` | retrospective 模板增加 `## Rule Activity` 格式化表格节 |
| `scripts/distill_antipatterns.py` | 新增 `--rules` 模式，输入源增加 retrospective Rule Activity 表；跨收敛对象聚合；输出全规则活性报告 |

## 不做的事

- **不建新文件**。所有改动在现有文件中
- **不建新实体**。不建 Meta-Reviewer、不建 Supervisor、不建新的 spawn 目标——全部折叠进现有 Reviewer 和 Orchestrator 职责
- **不在阶段 1 引入追踪机制**。阶段 1 只做折叠，零新基础设施。追踪属于阶段 2
- **不自动删除规则**。蒸馏产出 advisory report，删除需人确认——这保留了 converge 的"人类最终决策权"原则。核心机制的移除需额外经 ultraverge 流程
- **不改 converge 核心收敛语义**。Verdict、convergence modes、oscillation detection 不变
- **不引入新状态枚举**。复用 distill_antipatterns.py 的 active/dormant/archived 三级状态机

## 风险评估

| 风险 | 等级 | 缓解 |
|------|------|------|
| 意图漂移检查增加 Reviewer prompt 长度 | 低 | 条件激活 + Orchestrator 注入（非 Reviewer 自行读取），大多数轮次不触发 |
| 频次数据积累需要时间 | 低 | 阶段 2 不驱动运行时行为——只记录和报告，无破坏性；数据不足时蒸馏产出低置信度标记 |
| 衰减阈值未经实证 | 中 | 存储在 distill 脚本 CLI 参数中，可调整；蒸馏产出 advisory report 不自动删除 |
| 实时触发记录增加 Orchestrator 认知负担 | 低 | 每轮 ~1 行 YAML 更新，在现有 boundary_check 更新步骤中顺带完成；不新增独立步骤 |
| 规则 key 注册表需手动维护 | 低 | 新增 guard mechanism 时追加条目——与 antipatterns.md 的 id 注册表维护模式一致，已有先例 |
| 追踪机制本身增加自重 | 低 | 成本约每轮 1 行 YAML 更新，远低于被追踪的 guard mechanism 的 token 成本；不追踪自身 |

## 验证

- [ ] 阶段 1：Reviewer prompt 新增段落在非触发轮次不出现（条件注入机制有效）
- [ ] 阶段 1：触发轮次中，Reviewer 正确检测到 contract 与当前产物方向偏差并标注 drift_detected
- [ ] 阶段 1：drift_detected 字段在 reviewer YAML output format 中有定义，Orchestrator 可解析
- [ ] 阶段 1：Reviewer 不直接读取 _orchestrator-state.md（角色边界保持）
- [ ] 阶段 1：与责任清单 #6 的关系在 reviewer-prompt.md 或 SKILL.md 中有显式说明
- [ ] 阶段 2：rule_frequency 在每轮结束时实时更新（非 retrospective 时回溯）
- [ ] 阶段 2：规则 key 注册表完整且跨阶段一致
- [ ] 阶段 2：缺失 rule_frequency 段时正确初始化（全 active）
- [ ] 阶段 2：层级收敛中子收敛有独立的 rule_frequency
- [ ] 阶段 3：distill_antipatterns.py --rules 模式产出全规则活性报告
- [ ] 阶段 3：报告按收敛对象分列 + 跨对象汇总（标注置信度）
- [ ] 阶段 3：状态机与反模式共享 active/dormant/archived 三级
- [ ] 阶段 3：衰减阈值通过 CLI 参数可调
- [ ] 阶段 3：不自动修改 SKILL.md（advisory report only）

## 附录：与已有机制的对比

| 机制 | 解决的问题 | 实体数 | 每轮 token 成本 | 是否有衰减路径 |
|------|-----------|--------|----------------|--------------|
| Guard step (c+1) | Orchestrator 单轮内直接修改产物 | 0 新（在现有主循环中） | 低（~5 行自检） | 有（本方案阶段 2/3） |
| Reviewer 边界审计 (#7) | Reviewer 交叉验证 Orchestrator 修改 | 0 新（在现有 Reviewer prompt 中） | 低（~3 行检查） | 有（本方案阶段 2/3） |
| 意图漂移检查（本方案阶段 1） | 跨轮意图漂移 | 0 新（折叠进现有 Reviewer） | 低（条件注入，~7 行） | 有（本方案阶段 2/3） |
| Meta-Reviewer（被替代的方案） | 跨轮意图漂移 | 1 新实体 + 1 新 spawn | 高（每次 spawn ~5K+ token） | 无 |

本方案用折叠替代新增——Orchestrator 注入上下文、Reviewer 在已有读取路径上增加检查维度，零新实体、零新 spawn、零新 Required Reading。
