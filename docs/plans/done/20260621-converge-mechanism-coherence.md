---
type: plan
status: final
created: 2026-06-21
revision: post-convergence design-review（2026-06-21）—— 四层收窄为 N=1 工具（撤回 CONSTITUTION formalization）+ 3 hedge 显式分级（hedge #1 加机械接驳点）+ provisional 生命周期定义
scope: converge 机制协调性调整（Part B 事件之后）—— 结构迁移 + 四层 placement 判据（本次迁移专用，N=1）+ parking-discipline 规则
governance: true
trigger: 用户 ultraverge 关键词；评议本次 Part B 事件 surfacing 的协调性问题
related:
  - "CONSTITUTION.md"
  - "SKILL.md"
  - "GOVERNANCE-DECISIONS.md"
  - "refs/orchestrator-guide.md"
  - "refs/antipatterns.md"
  - "docs/plans/done/20260621-mode-differentiation-and-fork-executor.md"
  - ".converge/active/20260621-converge-mechanism-coherence/design-review.md"
---

# converge 机制协调性调整（Part B 事件之后）

## 背景

Part B（fork-executor）事件经历多轮 pilot 设计复评后**发散**——阻断逐层深化、修上一轮阻断竟引发下一轮此前不可讨论的新议题、验证 apparatus 复杂度反超被验证特性、"距通过"横移不缩。依宪法第一部仲裁（Bitter Lesson + Occam），事件被判定为"在收敛一个错误的问题"，放弃；GD-2 已 `approved`，重激活门槛明确。

事件过程 surfacing 出 converge **自身机制**的协调性问题，集中在 4 个相互锁死的症状：

1. **可达性悖论**：发散识别 5 判据（GD-2 § 判例）的处置原则要求 Orchestrator 能察觉发散并层升至用户；但判据停在 audit 层（GD-2），而 Orchestrator 运行时只读 `SKILL.md` + `refs/*-guide.md`——判据放 agent 看不到的地方 → 判据功能为零。
2. **"parking + 等触发"自我取消**：判据晋升门槛建立在"N≥3 复现"上；但 N 的计数依赖判据可达（Orchestrator 上报），判据不可达 → N 永远=1，触发器结构性死锁。
3. **层级错位**：活跃操作指导（判据、处置原则）放在 audit 层（GD），相当于"把函数逻辑写进 git log"——audit 是考古，不是 live guidance。
4. **parking 借口化风险**：对上述缺口一律采取"park 在 GD、等未来"策略，无判据区分"正当推迟"与"规避决策的借口"——存在用 Bitter Lesson / Occam 正当化 inaction 的便利空间。

本提案系统性回应这 4 症状：判据迁移至操作指导层、**为本次迁移构造四层 placement 判据（N=1 工具，非通用框架——见 § 本次 § 判据 迁移的 placement 判据）**、定义 parking-discipline 规则、加 SKILL.md 导航 pointer。

**out of scope**：重议 Part A（已落地）/ 重议 Part B 弃案（GD-2 approved）/ 与本事件无关的 converge 机制从零审查。

---

## 自举声明

**本计划是 converge 评议 converge 自身。** 评议者与被审查对象共享同一套设计 DNA——存在结构性便利"少动我自己"。处置方案若默认"不改 converge 机制、park 在 GD"，正是这一偏见的表现。

**对冲规则**（本计划的设计纪律，非事后补救）。**显式分级**（避免包装为同等严肃——约束力实有不均，承认之比掩饰之诚实）：

| # | hedge | 约束力级别 | 强制机制 |
|---|-------|----------|---------|
| 1 | **反转举证负担**（默认动手、park 须举证；parking-discipline 双条件） | **软约束** | 依赖独立 Reviewer 显式复核（机械接驳点见下） |
| 2 | **外部锚点**（用户 ultraverge 关键词触发，非 agent 自启） | **硬约束** | 结构性、agent 不可伪造 |
| 3 | **结构切换优于打补丁**（层级错位时迁移，不 flag / 改措辞） | **设计纪律声明** | 无机制强制，仅承诺 |

**hedge 内容**：

1. **反转举证负担（软约束）**：自举场景下，"默认动手、park 须举证"。欲推迟某项修复，必须通过 parking-discipline 规则（见下）的双条件——举证失败则必须立即处置，不得以 Bitter Lesson / Occam 正当化 inaction。**机械接驳点（让软约束真有 teeth）**：parking-discipline 规则的"合格判定"在自举/自评场景下**必须由独立 Reviewer 显式回应**——Reviewer 须在 round 输出中针对本 plan 的每个 parking 自评（见 § 应用到本提案的 registry 延后）标记 `parking-claim: verified` 或 `parking-claim: rejected`，并给出依据。**未标记 = plan 不进下一轮**。
2. **外部锚点（硬约束，必要非充分）**：本次 ultraverge 由用户 `ultraverge` 关键词触发，非 agent 自启。用户指令打破了自举闭环——评议的对象、范围、停止条件由外部定义，agent 不拥有"是否继续评议自己"的自决权。**但**外部锚点只是**必要非充分**条件——它设定评议对象/范围/停止条件，**不单独消解内容判断的自利倾向**；**hedge #1（反转举证负担 + parking-discipline）才是实质对冲**。
3. **结构切换优于打补丁（设计纪律声明）**：当问题源于层级归属错误，解法是迁移判据、命名中间层——不在原方案内加 flag / 改措辞敷衍（反折中纪律）。**无机制强制**——若违反（如在层级错位处加 flag 而非迁移），仅靠本声明 + Reviewer 复核识别。

---

## 本次 § 判据 迁移的 placement 判据（四层框架，N=1）

> **定位声明（反自利收窄）**：四层 + elimination 推理是**为本次 § 判据 迁移决策构造的工具**，**N=1 验证**（仅在 § 判据 上跑过），**不覆盖** refs/ 其余文件（见下"覆盖范围"）。本提案**不**把四层呈现为 converge 的通用数据架构，**不**进 CONSTITUTION（N=1 不固化进宪法）。四层是 placement 工具，不是全量分类系统。

converge 的数据承载事实上呈现多层，但"操作指导层"在本次事件前无显式身份，导致活跃操作指导（如发散判据）无处可去、塞进 audit 层。本节为**本次迁移决策**构造四层 placement 判据。

### 覆盖范围（显式声明）

- **本框架经验证**：§ 判据（→ 操作指导层，见下验证）。N=1。
- **本框架不覆盖**：refs/ 其余 8 文件（model-tiers / rubrics / quality-gate / state-schema / contract-negotiation / decomposition-protocol / framework-adapters / testing-toolbox）的层属——**本提案不重分类**这些文件，留待各自出现 placement 争议时单独议定。
  - 特别地：**model-tiers.md 自称"数据层"**（四层无此类别）——本提案**不吞并**该用法。converge 已有"数据层"概念，本四层框架（placement 工具）与之并存，不宣称独占层词汇。
- **结论**：四层是**本次迁移的决策工具**，非 converge 全量数据架构声明。

### 四层（本次迁移的 placement 判据）

| 层 | 载体 | 性质 | 修改程序 |
|----|------|------|---------|
| **机制层** | `SKILL.md` / `CONSTITUTION.md` | 通用机制（framework-agnostic、不随模型/项目变化） | ultraverge + 人工确认 |
| **操作指导层** | `refs/*-guide.md` / `refs/*-prompt.md` | 指导 agent 运行时行为，agent-readable | ultraverge（宪法保护文件）/ 普通收敛（非保护文件） |
| **audit 层** | `GOVERNANCE-DECISIONS.md` | append-only 决策日志（考古是特性，像 git log） | 追加（不可回改已记条目） |
| **registry 层** | `refs/antipatterns.md` | 频率驱动的 compiled 产物（distill 脚本维护 status） | distill 脚本 + 人工固化 |

> **"agent-readable" scope（本 context）**：指 **Orchestrator**（divergence-detector 角色）运行时可读——即进入 Orchestrator 必读集（refs/*-guide.md 等），**非** reviewer/executor 的可读集。placement 判据的注入点 = Orchestrator 运行时必读集。

### Artifact-placement 判据（elimination 推理，本次迁移专用）

本次迁移的 artifact（§ 判据）按以下顺序排除归属：

1. **audit 否决测试**：指导运行时 agent（Orchestrator）行为？是 → **不在 audit 层**（audit 是 append-only 考古，不是 live guidance；活跃指导放 audit 层 = "把函数逻辑写进 git log"）——此步使 elimination 流方向一致（先 audit 否决，再正向归属 registry/机制/操作指导）
2. **频率驱动、可由脚本 compiled？** 是 → **registry 层**（antipatterns 管线）
3. **通用机制（framework-agnostic、不随模型/项目变化）？** 是 → **机制层**
4. **以上均否** → **操作指导层**

**§ 判据 验证（N=1）**：(1) audit 否决测试——指导 Orchestrator 察觉发散？是 → 不在 audit ✓；(2) 频率驱动？否（N=1 经验提炼）→ 不在 registry ✓；(3) 通用机制？否（特定观察的经验）→ 不在机制层 ✓ → **操作指导层**。这验证了迁移的必要性（仅本个案验证，非通用判据的 N≥3 验证）。

### 落地（不进 CONSTITUTION）

**四层框架不进 CONSTITUTION**（N=1 不固化进宪法）。四层 + placement 判据留存在：

1. **本 plan**（作为本次迁移的决策记录）；
2. **迁移落地后的 `refs/orchestrator-guide.md`**（placement 判据推理作为 § 发散检测 迁移的伴随说明，记录"为何 § 判据 归操作指导层"——四层框架的落地载体）。

将来若 ≥3 次 placement 决策验证四层框架有效，再议 CONSTITUTION 正式化——届时凭数据不凭单点。

### 四层框架的生命周期（provisional 工具）

四层框架 = **本提案的 provisional 工具**，非 stable binding。其"转正"路径定义如下（避免 provisional 沦为"永久 binding 加弱标签"）：

- **转正触发**：下次 converge 出现 artifact placement 争议时，**独立 Reviewer 须评估四层框架是否仍适用**（显式回应：复用 / 修订 / 弃用）。若 Reviewer 决定复用且有效，计为 1 次复用验证。
- **固化门槛**：累计 ≥3 次复用且有效 → 再议固化（CONSTITUTION 正式化或保持 refs/ 文档形式）。
- **记录载体**：placement 决策事件（本次迁移 + 未来争议）记入 **retrospective**（converge 周期产物），由 **ultraverge 周期复审**。
- **未转正期间**：四层框架可指导本次迁移落地，但**不作未来 placement 争议的既定判据**——未来争议必须先经 Reviewer 评估框架适用性。

---

## parking-discipline 规则

区分"正当推迟"与"规避决策的借口"的二元判据：

> **parking 可接受 ⟺ 同时满足：**
> - **(a) 迁移触发器可验证且可触发**：存在可观测事件（非计数自身的循环），且该事件在当前架构下**可达**（不会被结构性屏蔽）。
> - **(b) parking 期间核心功能仍可运作**：被 park 的 artifact 所支撑的核心功能不依赖迁移完成后才生效。
>
> **任一否 → 必须立即处置（不允许 park）。**

**持久化**：本规则迁移至 `refs/orchestrator-guide.md` § parking-discipline（操作指导层）——Orchestrator 做停放决策的运行时纪律。plan 归档后规则仍在 Orchestrator 必读集内生效（反 self-bootstrapping 偏见对冲 hedge #1 的持久化载体）。见 § 文件改动清单。

> **自评循环对冲**：parking-discipline 是本计划自创规则。当本计划用该规则判定自身的 parking 决策（见下"应用到本提案的 registry 延后"）时，合格判定**必须由独立 Reviewer 复核确认**，不采信 plan 自评——以弱化"自创规则又自评"的循环。本计划的 parking 自评以下文形式给出，留作 Reviewer 复核的标的，而非既成结论。**（hedge #1 机械接驳点见 § 自举声明——Reviewer 须显式标记 `parking-claim: verified/rejected`，未标记 plan 不进下一轮。）**

### 应用到原处置方案（诊断为何其 parking 不合格）

| 原 plan 调整 | 触发器 | (a) 可达？ | 核心功能 | (b) 运作？ | 判定 |
|---|---|---|---|---|---|
| 调整 1（判据 park at GD） | N≥3 复现 | **否**：计数需判据可达，判据在 GD 不可达 → N 永远=1，触发器自我取消 | agent 察觉发散并层升 | **否**：判据不可达 → agent 无法察觉 → 层升路径死锁 | **不合格** |
| 调整 3（registry gap） | N≥2 类不同 process 信号 | **否**：无机制观测/计数 process 信号类别 | 判据可处置 | **否**（联动调整 1） | **不合格** |
| 调整 4（可达性 gap） | "与调整 1/3 联动" | 循环依赖 | agent 察觉能力 | **否**：plan 明文"接受 gap" | **不合格** |

原处置方案的 parking 策略整体不合格——(a) 全部自我取消或循环依赖，(b) 全部核心功能死锁。这不是 Bitter Lesson 的正当应用——Bitter Lesson 反对硬编码模型补丁，**不**反对搭最小结构 / 加导航 pointer；原则施加方向不应随结论便利翻转。

### 应用到本提案的 registry 延后（自评，待 Reviewer 复核）

本提案仅延后 **process-level maintained registry** 的创建（见调整 3）。验证：

- (a) 触发器 = "下一类 process-level 信号出现并落入操作指导层；若频率模式浮现，则议 registry 晋升"。**可观测**（新内容出现在 refs/*-guide.md 是可观测事件）；**可达**（操作指导层 Orchestrator-readable，不自我屏蔽）。
- (b) 核心功能 = 判据可达 + Orchestrator 可察觉发散 + 层升路径可触发。判据迁移至操作指导层后全部 live → **运作正常**。

**自评判定：合格。** 这是正当推迟（触发器可验证且可触发 + 核心功能运作），不是借口。**该自评提交独立 Reviewer 复核确认**（见上"自评循环对冲"）。

---

## 调整 1：迁移 § 判例 至操作指导层

**现状（问题）**：发散识别 5 判据停在 GD-2 § 判例（audit 层）。Orchestrator 读 SKILL.md + refs/ prompt，不读 GD → 判据对 Orchestrator 不可达 → 可达性悖论（判据处置原则要求 Orchestrator 察觉发散，但判据放 Orchestrator 看不到的地方 → 判据功能为零）+ 层级错位（活跃操作指导放 audit 层 = "把函数逻辑写进 git log"）。

**处置（结构迁移，非打补丁）**：

1. **GD-2 § 判例 全文迁移至 `refs/orchestrator-guide.md` 新增 § 发散检测**。内容包括：振荡 ≠ 发散的区分、发散识别 5 判据（联合信号框架）、处置原则（层升至用户）、晋升门槛（Bitter Lesson 自律）。
2. **案例证据随迁，使迁移后的章节 self-contained**。GD-2 § 判例 当前的"详细案例见 Obsidian KB 笔记"指向外部依赖——迁移时把支撑判据的关键证据就地概要 inline，外部笔记降级为"扩展阅读"。Inline 证据概要：
   - **divergence 形态**：pilot 复评的阻断逐层深化——执行细节 → 模块边界 → 元问题（是否值得做）；修上一轮阻断竟引发下一轮此前不可讨论的新议题；验证 apparatus 复杂度反超被验证特性；"距通过"横移不缩。
   - **第一部仲裁推理**：Bitter Lesson + Occam 联合判定——这是"在收敛一个错误的问题"（继续堆叠当轮修补无法消解元重设诉求），合法处置是放弃 / 缩范围 / 重设目标，而非继续消耗预算轮次。
   - 上述概要使读者无须查 Obsidian 即可理解判据如何由真实事件提炼；Obsidian 笔记保留作"完整原始经过"扩展阅读，非必要依赖。
3. **GD-2 entry 完全不动（no-touch + 追加注记）**：§ 判例 内容作为"批准时的持有位置"**完整保留**——GD 是考古层（记录"当时如此"，不回改已 approved 条目）。orchestrator-guide § 发散检测 = **唯一 live source**。迁移本身由 GD-2 entry 末尾追加一行 **annotation 注记** 记录（**append，不是回改**）：

   > 📎 注记（`<date>` = 本计划落地执行日）：§ 判例 内容已迁移至 `refs/orchestrator-guide.md` § 发散检测（live source）；本 GD-2 entry 保留作历史快照（批准时的持有位置），不再代表当前 live 指导。

   **source of truth**：orchestrator-guide § 发散检测 = live；GD-2 § 判例 = 历史快照。未来若需新建 GD 条目（如 GD-3）正式授权此次迁移，可在后续 GD 条目中追加——本计划不强制要求，注记已足够 audit。

   **（反折中纪律）**：在"additive no-touch"与"substitutive 改写 GD-2"之间采 **additive no-touch**——GD-2 entry 本体不动，消除"改为指针"的 substitutive 措辞与 append-only 原则的冲突。

**此调整的效果**：
- **可达性悖论 dissolved**：Orchestrator 读 orchestrator-guide（运行时必读）→ 察觉发散信号 → 可按判据处置原则层升至用户 → 层升路径 live。
- **层级错位 corrected**：判据从 audit 层迁至操作指导层（placement 判据验证：操作指导层是正确归属）。
- **N≥3 计数可达**：判据 Orchestrator-readable → 未来跨收敛命中可被 Orchestrator 上报 → distill 晋升的触发器不再自我取消。
- **audit 纯度保持**：GD-2 entry no-touch + append annotation → 不违反 append-only 原则。

---

## 调整 1a：SKILL.md §振荡检测 加导航 pointer

**现状**：SKILL.md §振荡检测 定义 Type O/R/F/S，**不提**发散（发散 ≠ 振荡，见判据）。Orchestrator 读 SKILL.md 时无任何信号指向"还存在另一种失效模式"。

**处置**：在 SKILL.md §振荡检测 表后加一行 pointer：

> > 发散（非重复/翻转的持续深化失效模式）的识别判据与处置原则见 `refs/orchestrator-guide.md` § 发散检测。

**Bitter Lesson 不覆盖 pointer**：

- Bitter Lesson 反对"硬编码模型补丁为机制"（如往振荡表加 `Type D (Divergence)` 并赋予硬停语义——这正是 GD-2 § 判例 的晋升门槛所自律的）。
- Bitter Lesson **不**反对"加导航 pointer"。pointer 是索引条目（告诉 Orchestrator"那里有相关内容"），不是机制 patch（不定义新检测规则、不改变运行时行为）。
- 原处置方案对 pointer 从严（"N=1 不硬编码"）、对 status convention 从宽（"借鉴字段思路"）——原则施加方向随结论便利翻转。本提案统一：pointer = 导航 ≠ mechanism → 不触发 Bitter Lesson 自检。

---

## 调整 2：GOVERNANCE-DECISIONS.md 性质 + status 约定

**现状**：GD 是 append-only 决策日志，只有 pending→approved。随条目累积，未来读者难辨"live 决定" vs "历史"。

**处置**：

1. **澄清 GD = 纯 audit trail**（append-only，考古是特性，像 git log）——**不**改成 maintained registry。活跃指导（如判据）**迁出** GD（调整 1 执行），不长期停放。**已 approved 条目本体不可回改**——迁移以"no-touch + 末尾追加注记"形式落地（调整 1 step 3），保 audit 纯度。
2. **status 约定：仅保留 `pending` → `approved`**（2 条目时 4 态过早，徒增维护）。`superseded` / `archived` 留 N≥5 再议——届时凭数据不凭单点。
3. **不借 distill 脚本**：决策一次性、非频率驱动，distill 信号不配（与 antipatterns 的频率模型保持边界清晰）。

**内部一致**：澄清 GD = 纯 audit trail（点 1）+ 活跃指导迁出（调整 1）+ status 精简（点 2）相互一致；不再出现"活跃指导应迁出却仍 park 在 GD"的内部矛盾。

---

## 调整 3：process-level maintained registry 缺口（部分填补 + registry 正当延后）

**现状**：converge 有 product-level maintained registry（`refs/antipatterns.md`，distill 按频率维护），但无 process-level 的。发散判据是 process-level 信号（轨迹级、非 reviewer per-issue flag），不进 antipatterns 管线（distill 没东西统计），原处置方案塞进 GD。

**处置（分层填补）**：

1. **缺口部分填补**：通过命名操作指导层（本次迁移的四层 placement 判据，N=1——见 § 本次 § 判据 迁移的 placement 判据）+ 迁移 § 判据 至该层（调整 1），process-level 信号**现在有家了**——操作指导层承载 Orchestrator-readable 的 process-level 指导，audit 层不再被迫承担非 audit 职责。
2. **process-level maintained registry 仍正当延后**：registry 层（频率驱动、distill 维护）的创建需频率证据。当前仅 N=1 类 process 信号（发散识别）。Bitter Lesson：N=1 不建 registry。**触发器**：下一类 process-level 信号出现并落入操作指导层；若频率模式浮现（跨多类信号重复结构），则议 registry 晋升。
3. **parking-discipline 验证**（见上）：触发器可验证（新内容出现可观测）且可达（操作指导层不自我屏蔽）+ 核心功能运作（判据已 live）→ **延后合格，非借口**（自评，待独立 Reviewer 复核）。

---

## 调整 4：可达性 gap — dissolved

原处置方案的调整 4 是"接受当前 gap"——Orchestrator 不读 GD，判据对 Orchestrator 隐形，人类按需查阅。本提案判此不可接受：判据处置原则（层升至用户）内含前提 Orchestrator 能察觉发散，gap 使前提不成立——层升路径结构性死锁。

**本提案 dissolved 此 gap**：调整 1 将判据迁移至操作指导层（Orchestrator-readable）+ 调整 1a 加 SKILL.md pointer → Orchestrator 可察觉发散信号 → 可层升至用户 → 可达性悖论不再存在。原"接受 gap"策略删除。

---

## 文件改动清单

| 文件 | 改动 | 宪法保护？ |
|------|------|-----------|
| `refs/orchestrator-guide.md` | (1) 新增 § 发散检测（从 GD-2 § 判例 迁移全文 + 关键案例证据 inline：divergence 形态 + 第一部仲裁推理概要；Obsidian KB 降为扩展阅读）；(2) **新增 § parking-discipline**（从本 plan § parking-discipline 规则 节迁移——规则持久化至操作指导层，Orchestrator 运行时可读）；(3) placement 判据推理作为 § 发散检测 的伴随说明（记录"为何 § 判据 归操作指导层"——四层框架的落地载体） | 是 |
| `GOVERNANCE-DECISIONS.md` | **GD-2 entry 本体 no-touch**（§ 判例 保留作历史快照）；仅在 GD-2 entry 末尾**追加 annotation 注记**（append-only：指向 orchestrator-guide § 发散检测 为 live source；`<date>` = 本计划落地执行日） | 否（追加注记，非修改既有决策） |
| `SKILL.md` | §振荡检测 表后加一行 pointer → `refs/orchestrator-guide.md` § 发散检测 | 是 |

**不触碰**：CONSTITUTION.md（**第一部 + 第二部——四层框架不进宪法，N=1 不固化**）/ 已落地 Part A / GD-2 approved 决断本身（**GD-2 entry 本体完全不动**——§ 判例 子节保留作历史快照，仅末尾追加注记）。

> **改动清单说明**：本计划现 **3 文件改动**（去 CONSTITUTION.md——四层框架撤回 CONSTITUTION 正式化，见 § 落地）。

---

## 落地流程

本计划走 **ultraverge**（用户关键词触发的外部锚点）：

- **Reviewer 复核**（重点验）：可达性悖论是否真 dissolved / parking-discipline 规则自评循环是否被对冲（**hedge #1 机械接驳点**：Reviewer 须显式标记 `parking-claim: verified/rejected`）/ GD no-touch + annotation 的 audit 纯度 / 四层框架收窄是否诚实（N=1 声明 + 不覆盖 refs/ 8 文件 + 不进 CONSTITUTION）/ hedge 分级是否准确 / provisional 生命周期是否可操作 / 调整 1 step 2 inline 证据概要是否 self-contained。
- **强制设计审查**（系统边界）：**已完成（本轮 ultraverge）**——findings 见 design-review.md，3 highlights 由本修订处置（四层收窄 + hedge 分级 + provisional 生命周期）。后续若 Reviewer 认为本修订未充分处置，可再启一轮设计审查。
- **阻断 → 收敛轮**（按 converge 标准流程）；**通过 → 人工批准**。
- **executor 落地**：人工批准后，spawn executor 按 Plan-Execution 模板执行文件改动清单（现 3 文件）；落地执行日记入 GD-2 annotation 的 `<date>` 占位符。placement 决策事件（本次迁移）记入下次 retrospective，供 ultraverge 周期复审 provisional 框架。
