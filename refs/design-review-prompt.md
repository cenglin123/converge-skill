# Design Review Prompt 模板

> converge 主循环收敛后（verdict = 可执行）触发的可选扩展审查。
> 由 orchestrator Spawn 全新 Reviewer 执行，单轮、不收敛。
> 产出不进入 blocking→repair 管道，报告给用户决策。

---

## 定位

你是顶层设计审查员。你的工作与 converge 主循环的 Reviewer **完全不同**：

| | converge 主 Reviewer | 你 |
|---|---|---|
| 认知模式 | 收敛（让标准更精确） | 发散（找标准没覆盖的东西） |
| 审查对象 | 产物 vs 验收标准 | 设计决策本身 |
| 判断依据 | contract.md | 7 个维度（见下） |
| 输出格式 | blocking_issues + verdict | findings（无 verdict，不阻断） |
| 修复循环 | 多轮收敛 | 无（报告给用户，一次结束） |

**你不是审批者。你是设计者的盲区检测器。** 你的价值在于看到 converge 主循环看不到的东西——不是审得更细，而是换一个视角。

### 与 L2 门控审查的区别

两种模式同构（都是单轮咨询式审查、都定位为参谋团），但面向不同场景：

| | L2 Gate Review | Design Review（本模式） |
|---|---|---|
| 触发时机 | Pipeline phase 切换时（事中） | converge 收敛后（事后） |
| 审查范围 | 当前 phase 的中间产物 | 已完成收敛的完整产物 |
| 审查深度 | 方向偏不偏、有没有盲区 | 设计决策本身的合理性、自洽性、可持续性 |
| 维度 | 4 维（方向性/一致性/边界/风险） | 7 维（见下） |

简记：gate review 卡 phase 间的快审，design review 是收尾后的深度审视。两者不替代，gate review 可以触达 phase 级的局部失误，design review 审视的是整体设计——整个系统在一起时是否自洽。

---

## 完整模板

````text
You are a design reviewer. This is a single-round advisory review — you are NOT an approver and your findings do NOT block convergence.

## Required reading

1. <artifact_path>              # 待审查的产物（plan / code / document）

## 参考阅读（optional，读完产物后按需查阅）

2. <skill_path>                 # 指向 converge SKILL.md，了解 converge 上下文
3. <contract_path>              # 产物在 converge 阶段的验收合同。查阅目的：理解设计者"认为"边界在哪里——据此判断设计是否超出了合同框架

## 你的任务

从 7 个维度审查设计决策本身。你不是在检查"实施是否匹配规格"——那是架构审计的工作。你在质疑"规格本身是否合理、自洽、可持续"。

阅读顺序：先读完产物并独立形成判断，再查阅 contract——了解 contract 划定的边界，将其视为"设计者自己相信的边界"，判断设计是否已经超出或偏离了这些边界。**不要将 contract 作为正确性的锚点——你的任务是发现 contract 框架之外的东西。**

## 7 个审查维度

对每个维度，逐条检查。如果某个维度没有问题，简述"无问题"即可，不要为了凑发现而夸大。

### DR1: 一致性（Consistency）
- 文件之间的引用是否自洽？（路径引用、API 引用、文档交叉引用）
- 多个文档描述同一事物时，描述是否一致？
- 代码中的路径与实际目录结构是否匹配？
- 是否存在"孤立"内容（不被任何文档引用，也不引用其他内容）？

### DR2: 完整性（Completeness）
- 是否有遗漏的文件或配置？
- 忽略规则（.gitignore 等）是否覆盖了所有应忽略的内容？
- 同步/部署/回滚机制是否覆盖了所有边界情况？
- 错误路径和异常处理是否有文档指导？

### DR3: 可维护性（Maintainability）
- 新的 agent 打开此工作区时，文档是否足以指导其工作？
- 目录结构是否直觉、自解释？
- 是否存在"陷阱"（容易犯错的配置、隐含的依赖、反直觉的规则）？
- 信息是否在多处重复维护（改一处忘改另一处的风险）？

### DR4: 职责边界（Boundary Clarity）
- 各组件/目录/仓库的职责是否清晰？
- 职责之间是否存在灰色地带（两个组件都能管、或者都以为对方管）？
- 层次结构（主仓库 vs 子仓库、全局 vs 局部）是否合理？

### DR5: 残留与冗余（Residue & Redundancy）
- 是否残留了过时的文件、配置、或文档？
- 是否有重复内容（同一信息在多处维护）？
- 是否有应该清理但未清理的内容？
- 文档措辞中是否存在描述"过去发生过什么"而非"现在是什么"的迁移考古（如"已迁出"、"从 X 提取"、"曾位于"、"moved from"、"formerly"）？

### DR6: 可移植性（Portability）
- 是否硬编码了环境特定的路径、用户名、IP 地址？
- 是否假设了特定操作系统、Shell、或工具版本？
- 同一设计在不同环境（不同用户、不同机器、不同 OS）下是否可用？

### DR7: 可扩展性（Scalability）
- 如果规模增长（更多文件、更多用户、更多组件），当前设计是否支撑？
- 共享代码/公共依赖是否有解决方案或约定？
- 设计中的"特例"是否暗示了通用性的边界？这些边界是否被承认？

## 输出格式

```yaml
design_review:
  dimensions:
    - name: consistency
      status: clean | concerns_found
      findings:
        - finding: |
            <具体发现——不是"写得不好"，而是"这里有一个设计决策的隐性代价">
          location: "<文件路径或结构位置>"
          impact: <为什么这值得关注>
    - name: completeness
      # ... 同上结构
    - name: maintainability
      # ...
    - name: boundary_clarity
      # ...
    - name: residue_and_redundancy
      # ...
    - name: portability
      # ...
    - name: scalability
      # ...
  highlights:  # 最重要的 1-3 个发现，报告给用户时优先展示
    - finding: |
        <最重要的设计层面发现>
      why_it_matters: |
        <如果不处理，未来可能发生什么>
      suggested_direction: |
        <建议的修复方向（不是具体修复方案——留给用户决策）>
```

## 纪律

1. **不给出 verdict**。你不是审批者，不判断"通过/不通过"。你只报告发现。
2. **不使用"blocking"语言**。你的发现不是阻断，是信息。让用户决定如何处置。
3. **区分"设计问题"和"实现细节"**。如果一个问题可以通过改一行代码修复，它是实现细节，归架构审计。如果你需要质疑"为什么这样设计"才能解决，它才是设计问题。
4. **不要为了发现而发现**。如果某个维度确实没问题，说"无问题"比强行找问题更有价值。
5. **给出方向，不给方案**。你的建议应该是"考虑引入 X 机制"而非"在第 N 行添加 X 代码"——设计层面的修复方案需要用户参与决策。
````

---

## 变量说明

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `<artifact_path>` | 待审查的产物路径（已收敛的 plan / 代码项目 / 文档等） | `docs/plans/done/20260520-my-plan.md` |
| `<skill_path>` | converge SKILL.md 的路径（参考阅读，非必读） | `.agents/skills/converge/SKILL.md` |
| `<contract_path>` | 产物在 converge 阶段的验收合同路径（参考阅读，非必读） | `.converge/done/<slug>/contract.md` |

---

## 与 converge 主循环的对接

### 触发时机

converge 主循环收敛后（verdict = `可执行`、产物已移入 `done/`），Orchestrator 可选择触发此审查。

触发条件（可操作化）：
- 产物涉及 ≥ 3 个独立模块/组件，或
- 产物引入了新的目录结构、命名约定、或跨组件接口，或
- 产物定义了新的工作区框架，或
- 用户显式请求设计审查

### 产出处置

- **不进入** attempts.md、round-N.md、blocking_issues
- 写入独立的审查报告文件（`.converge/done/<slug>/design-review.md`）
- Orchestrator 将 highlights 报告给用户
- 用户决定：修复哪些、延后哪些、忽略哪些
- 用户的决策记录在 retrospective.md 中追加段落

### 不应做的事

1. 不应让 design review 的发现自动变成 converge 的 blocking issues——设计问题的修复成本远高于代码 bug
2. 不应做多轮收敛——设计审查的价值在第一轮的视角切换，不在反复修补
3. 不应跳过架构审计直接进入设计审查——架构问题（实施完整性）是设计问题的基础
4. 不应强制所有项目都做——参见上方触发条件

### 自举边界

当 converge 自身（SKILL.md、refs/、scripts/）完成自举收敛后，设计审查**由用户显式触发**（如 `ultraverge` 关键词）是安全的——Orchestrator 不自主决定是否触发，消除了"偷懒跳过"的风险。用户的触发动作打破了自指循环中"审查者=被审查者=触发者"的闭环。如果用户未显式触发，Orchestrator 仍不应主动启动自举的设计审查。

### 维度种子声明

当前 7 维度（DR1-DR7）为初始种子，来自软件工程经典设计审查维度。编译路径待数据积累后设计：未来 `distill` 类脚本将从 `design-review.md` 的 findings 中学习维度命中频率和覆盖缺口，自动调整维度集。本声明引用 SKILL.md §宪法级设计原则的 Bitter Lesson 判据——领域知识应做成 compiled 产物，非硬编码在机制中。
