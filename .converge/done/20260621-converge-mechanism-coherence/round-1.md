# Round 1 — ultraverge 评议（3 并行独立 reviewer）

## Reviewer 配置

3 个独立 fresh-context reviewer，差异化 lens（破自举评议的同模型盲区）：
- **R1**：Bitter Lesson / Occam 第一性原理 lens
- **R2**：数据架构 / audit-registry 区分 lens
- **R3**：对抗性盲区 / 反自利 lens

reservation：5fd307744c83 (R1) / f4ea74f4096b (R2) / 80b867f1b9b6 (R3)，均 settled succeeded。

## Verdicts

| Reviewer | Verdict | Lens |
|----------|---------|------|
| R1 | **阻断需修复** | bitter-lesson-occam |
| R2 | **阻断需修复** | data-architecture-audit-registry |
| R3 | **阻断需修复** | adversarial-blindspot |

**3/3 阻断** → 进入完整收敛（executor 修订 plan → round 2 re-review）。

---

## Orchestrator 处理

### 振荡检测
Round 1（首轮）→ Type O/R/F/S 均不适用。

### 收敛分析（关键：独立视角的一致结论）

3 个独立 reviewer、不同 lens、**达成一致核心结论**——这是强信号（非发散，是真正的盲区被独立确认）。逐条收敛主题：

1. **可达性悖论（3/3 命中）**：5 判据的处置原则（"层升至用户用第一性原则"）内含前提——agent 能察觉发散。但 plan 同时让判据对 agent 不可达（不读 GD + 不加 SKILL pointer）。结果：判据结构性 inert，"层升"路径无法触发。判据**功能为零**。R3 判 severity=conceptual；R1/R2 同义表述。
2. **"parking + 等触发"是借口而非纪律（3/3）**：触发条件自我取消——N≥3 需判据可达才能计数命中；判据不可达 → N 永远=1。parking 无 deadline / owner / 强制 review → 永久化。R1 提议二元判据：parking 合规 ⟺ (a) 触发器可验证且可触发 + (b) parking 期间核心功能仍可运作。
3. **§ 判例 层级错位（R2 最强，R1/R3 支持）**：活跃操作指导放在 audit 层 = "把函数逻辑写进 git log"（R2 原话）。应迁至 operational guide（`refs/orchestrator-guide.md` 新增 § 发散检测）。GD-2 留指针。**这同时解可达性悖论**（agent 读 orchestrator-guide → 察觉 → 层升可触发）。
4. **结构缺口：缺 operational-guidance 中间层（R2 id3, R3 DR7）**：converge 数据架构四层（机制 / 操作指导 / audit / registry）中"操作指导层"无显式身份。§ 判例 是首例，未来 process-level 信号（合同谈判启发式、边界仲裁经验等）会重复此纠结。R2 给出 artifact 归属层的通用判据（指导运行时行为？是→不在 audit；频率驱动 compiled？否→不在 registry；通用机制？N=1 否→不在机制层；elimination → 操作指导层）。
5. **Bitter Lesson 误用（R1 id1/id3, R3 id3/id4）**：Bitter Lesson 反对"硬编码模型补丁"，**不**反对"搭最小结构收集证据"。plan 混为一谈，用前者正当化 inaction。pointer ≠ mechanism，Bitter Lesson 不覆盖 pointer。同时 plan 对 pointer 从严、对 status convention 从宽——原则施加方向随结论便利翻转（R1 DR1）。
6. **自举结构性偏见无对冲（R3 id5）**：converge 评议自身 → 结构性便利"少动我自己"。4 项调整全部默认"不改 converge"。无外部锚点、无反转举证负担、无利益冲突声明。R3 判 severity=conceptual；"自评议产物若全结论都是'不必改我'，无对冲规则时 verdict 不可信"。
7. **plan 内部矛盾（R2 id2, R3 id2）**：调整 2 说"活跃指导应迁出 GD"，调整 1/3/4 却 park 在 GD。直接冲突未解，只是抛回给 reviewer。
8. **resolution density 过低（R1 DR2）**：3/4 调整是显式不行动。本次 ultraverge 的"可执行产物"≈ status 字段 + TODO。"deferral log"非 plan。

### Antipattern 观察（供 retrospective）
- 自举便利倾向（R1/R3 隐示）：plan 利用"审查者=被审查者"降低标准。近似 `silent_merge` / `orchestrator_self_review` 的结构性变体——非正式标注，供 retrospective distill 评估。

---

## Executor 修复方向（consolidated fix-list，供 round-2 executor）

executor 应将 plan 修订为（**实质性重构，非措辞调整**）：

1. **迁移 § 判例**：GD-2 § 判例 → `refs/orchestrator-guide.md` 新增 § 发散检测（或新文件 `refs/divergence-signals.md`）。GD-2 留指针。**解可达性悖论**（agent 读 orchestrator-guide → 察觉 → 层升可触发）+ 解层级错位。
2. **加 SKILL.md §振荡检测 pointer**（一行）：pointer 是导航非机制，不违 Bitter Lesson。指向 `refs/orchestrator-guide.md` § 发散检测。
3. **命名 operational-guidance 中间层**：plan 显式确立 converge 四层数据架构（机制 / 操作指导 / audit / registry），给"未来 process-level artifact 归哪层"的通用判据（采用 R2 的 elimination 推理）。
4. **parking-discipline 规则**：parking 可接受 ⟺ (a) 迁移触发器可验证且可触发 + (b) parking 期间核心功能仍可运作。任一否 → 必须立即处置。按此规则，原 plan 调整 1/3/4 的 parking **不合格**（触发器不可达、核心功能死锁）。
5. **解内部矛盾**：调整 2 的"迁出"与 1/3/4 的 parking 冲突 → 修订后统一为"迁出"（执行 #1），消除矛盾。
6. **自举对冲声明**：plan 增"自举声明"节——承认 converge 评议自身的结构性偏见 + 反转举证负担（自举场景下"默认动手、park 须举证"）+ 本次触发由用户 `ultraverge` 关键词打破闭环（外部锚点）。
7. **status convention 推迟**（R1/R2 一致）：2 条目时 4 态 status 过早；只保留 pending/approved（既有事实），superseded/archived 留 N≥5 再加。
8. **KB 依赖澄清**：§ 判例 的完整案例**进仓库**（迁移后的 operational guide 内联或 refs 附录），Obsidian KB 仅扩展阅读——self-containedness。

---

## 下一步

spawn executor（fresh context）按 fix-list 修订 `docs/plans/active/20260621-converge-mechanism-coherence.md` → round 2 re-review。
