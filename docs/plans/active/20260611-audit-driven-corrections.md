# Plan: converge SKILL 深度审计修正（20260611）

> **性质**：混合计划。A 组修改治理文档（SKILL.md、refs/reviewer-prompt.md、refs/state-schema.md、refs/decomposition-protocol.md）→ 按 CONSTITUTION 第四部走 **ultraverge**；B 组仅触碰非保护文件（refs/antipatterns.md、refs/testing-toolbox.md、refs/quality-gate.md、scripts/、README_en.md）→ 标准评议即可；C 组为运维动作 + 用户决策项，不产生评议需求但需人工裁断。
> **范式声明**：沿用 20260610 轻量计划范式（动机 + 改动清单 + 验收清单）。附逐字插入/替换块的项可由低档 agent 执行（满足模型分层条件 (a)）；标注「需裁决」的项不可降档，其措辞终稿以 ultraverge 收敛结果为准。
> **来源**：2026-06-11 对 converge SKILL 全量深度审计（SKILL.md、CONSTITUTION、双 README、12 个 refs、2 个脚本逐字阅读 + distill dry-run 实证交叉验证）。15 项发现全部映射至下方改动项或延后项，无遗漏。

## 动机

审计发现该 SKILL 架构成熟（三层分离真实落地、distill 生命周期有实证闭环），但文档间漂移已累积到机制自相矛盾的程度：verdict 枚举三处不一致、antipattern id「三处统一」硬约束已被打破、retrospective §11 编号冲突、SKILL.md 与宪法对 inner loop 验收的强制性表述相反。多数问题恰好是本 SKILL 自己定义的反模式（naming drift、archaeology_leftover、数据耦合），属于"医者自医"场景——按明线规则，治理文档修改必须走 ultraverge。

---

## A 组 · 治理域改动（须 ultraverge）

### A1 · verdict 枚举统一 + 「需重新设计」分支补全 〔审计 #1，阻断级〕

**问题**：`refs/reviewer-prompt.md` 定义的 verdict 枚举为 `可执行 | 阻断需修复 | 需重新设计`；`SKILL.md`「默认入口：评议」决策树使用枚举外的「需修订」，且对「需重新设计」无任何处置路径。

**修复合同**：以 reviewer-prompt.md 枚举为准（不动枚举，改 SKILL.md）。锚点：SKILL.md「默认入口：评议」节的三条 verdict 决策 bullet，整体替换为：

```markdown
- verdict = 可执行 → 收敛完成，归档 done/
- verdict = 阻断需修复 + 阻断为 implementation/structural → Executor 修复，评议模式再走一轮
- verdict = 阻断需修复 + 阻断为 conceptual/architectural → **升级为完整收敛**（下方主循环）
- verdict = 需重新设计 → 不进入修复循环。向用户报告产物存在方向性缺陷，由用户决定：重写产物后重新评议、缩小范围后重新评议、或走主观接受程序（终止状态 c）
```

**需裁决**：第四条 bullet 的处置语义（是否允许"缩小范围后重新评议"）由 ultraverge Reviewer 裁断；前三条为机械替换。

### A2 · antipattern type 枚举补全 〔审计 #2，阻断级〕

**问题**：注册表 12 个 id，`refs/reviewer-prompt.md` 输出 schema 的 `type` 枚举仅 10 个，缺 `report_hallucination`、`archaeology_leftover`，违反 state-schema.md §3 自身声明的「三处统一」硬约束。

**修复合同**：锚点：reviewer-prompt.md 完整模板内 `type: <minimum_patch | ...>` 行，逐字替换为：

```text
    type: <minimum_patch | solution_anchoring | over_compromise | past_commitment_anchoring | report_hallucination | false_generality | identity_crisis | data_tool_coupling | environment_lock-in | archaeology_leftover | orchestrator_self_review | silent_merge>
```

**附加防漂移条款**（需裁决采纳与否）：在该行下方追加一句注释「枚举与 `refs/antipatterns.md` 的 id 全集逐字同步；新增/归档条目时本行同步更新（归档条目保留在枚举中——历史 retrospective 仍可能引用）」。

### A3 · retrospective §11 编号冲突 〔审计 #3，阻断级〕

**问题**：state-schema.md「收敛后修订记录」与 decomposition-protocol.md「层级收敛评估」均占用 §11；两情形叠加时产出两个 §11。

**修复合同**：「收敛后修订记录」保持 §11；「层级收敛评估」改为 **§12**。机械替换三处：

1. `refs/decomposition-protocol.md` §Retrospective 扩展模板首行：`## 11. 层级收敛评估` → `## 12. 层级收敛评估`
2. `refs/state-schema.md` 文末注释：「在 §10 之后追加 **§11. 层级收敛评估**」→「追加 **§12. 层级收敛评估**（§11 预留给收敛后修订记录；两节均可缺省，编号固定不顺延——保证 distill 类脚本按节标题定位的稳定性）」
3. 核对 `decomposition-protocol.md` 全文无其余 `§11` 自引用。

### A4 · inner loop 验收：宪法与机制层表述对齐 〔审计 #4，阻断级〕

**问题**：CONSTITUTION 第二部 #2 将"跳过 inner loop 验收"列为不可让渡违规；SKILL.md 主循环 3i 却标注「（可选）」。宪法开头段规定此类冲突本身即触发修宪程序。

**修复合同**（方向：机制层向宪法对齐，宪法不动）。锚点：SKILL.md「Orchestrator 主循环」代码块中 `i. （可选）Continue 做 inner loop reviewer 验收` 行，替换为：

```text
   i. Continue 做 inner loop reviewer 验收（宪法第二部 #2：不可跳过；Continue 不可用时按附录 A.2/A.4 降级为 orchestrator 逐条验收并标注）
```

**需裁决**：是否存在合法的"跳过 inner loop、由下一轮 fresh reviewer 充当验收"路径。若 ultraverge 裁定存在，则改为修订宪法 #2 措辞（人工审议 + 变更记录留痕），本项执行方案二选一。

### A5 · 删除项目特定路径引用 〔审计 #8〕

**问题**：SKILL.md「Ultraverge 路径」并行裁决规则中引用 `.meta/deliberations/README.md`——使用方项目的路径，SKILL 包外不可移植，命中自家 Q3 数据纯度 / DR6 可移植性。

**修复合同**：锚点：SKILL.md「并行裁决规则」第二个子 bullet（「裁决规则是 ultraverge 专属的并行评议收敛语义，与 `.meta/deliberations/README.md` 的 ≥3 评议摘要自动收敛互为补充…」），整条删除或改写为不含外部路径的通用表述（如「裁决规则仅管辖 ultraverge 的 spawn 约束 + 并行收敛语义，不约束宿主项目自有的评议汇总机制」）。**需裁决**：删除 vs 改写。

### A6 · deterministic_check skip 格式统一 〔审计 #10〕

**问题**：reviewer-prompt.md YAML schema 用独立字段 `deterministic_check_skip_reason`，正文两处（确定性检查前提段、第 4 条）又要求内联 `deterministic_check: skipped (reason: <具体原因>)`。

**修复合同**：以 schema 双字段为准。正文两处内联格式表述改为「标注 `deterministic_check: skipped` 并在 `deterministic_check_skip_reason` 填写具体原因」。语义审查节首行「在 blocking issue 中标注 `deterministic_check: skipped`」同步核对（该处指 YAML 顶层字段，非 issue 内字段——若有歧义一并澄清）。机械替换。

### A7 · 「D11」黑话消除 〔审计 #12b〕

**问题**：「D11」是历史计划的决策编号，SKILL.md 标题、表格及 orchestrator-guide / decomposition-protocol 的 `D11=b`、`D11=c` 引用对全新读者（含每轮被 Spawn、必读 SKILL.md 的 fresh Reviewer）不可解码。

**修复合同**（推荐方案，需裁决）：全仓库重命名 `D11-a/b/c` → `终止-a/终止-b/终止-c`，标题「终止状态与收敛判定（D11）」→「终止状态与收敛判定」。涉及文件：SKILL.md（标题 + 表格 + 表后说明）、README.md（D11 表）、refs/orchestrator-guide.md（`D11=c` 一处）、refs/decomposition-protocol.md（`D11=b` 一处）。执行前 grep `D11` 全量盘点，验收以 grep 零命中为准（done/ 历史归档与 git log 不改）。备选方案：保留编号、在首次出现处加一句定义。

---

## B 组 · 非保护域改动（标准评议）

### B1 · 删除悬空引用「Red Flag #1 / #6」 〔审计 #7〕

`refs/antipatterns.md` `orchestrator_self_review` 与 `silent_merge` 两条目 description 中各有一行「对应 Red Flag #N。」——Red Flag 清单已在历史减重中删除，全仓库无该清单。两行整行删除（命中自家 archaeology_leftover）。**时序约束**：先于 C1（distill --write 只改标量字段、不动 description，但先改先验证更干净）。

### B2 · README_en.md 同步 〔审计 #11〕

落后中文版：缺 CONSTITUTION.md、design-review-prompt.md、antipatterns.md、model-tiers.md、distill 脚本；终止状态仅 3 种（中文版 5 种）；无设计哲学双原则段。**修复合同**：以 README.md 为源重译全文，文首加一行「Translated from README.md (authoritative source). 以中文版为准。」防再漂移。

### B3 · quality-gate.md 阈值表补 `total_budget_high` 〔审计 #13b〕

`scripts/l1_gate.py` 实现了 `total_spent_pct > 0.85 → total_budget_high` 告警，但 quality-gate.md「阈值」表无此行。表中追加一行：

```markdown
| 总预算水位 | total_spent_pct > 0.85 → warn | 全局 token 预算消耗已达 85%，提示编排器进入收尾预算管理 |
```

### B4 · l1_gate.py 幻觉注释修正 〔审计 #13a〕

两条与代码行为无关的注释逐字替换：

- `# 1. Worker 一致性和 Token 预算偏差（使用远程代理自动构建签名）` → `# 1. Worker 一致性`
- `# 2. Token 预算偏差率自动调整：超出 30% 自动记录超限次数` → `# 2. Token 预算偏差（阶段超支 + 总水位）`

### B5 · distill 报告硬编码措辞 〔审计 #14〕

`scripts/distill_antipatterns.py` `print_report` 中 `"无（无 new: 达阈值，或四份样本中 new: 从未出现）"` 的「四份样本」改为动态：`f"无（无 new: 达阈值，或 {n_conv} 份样本中 new: 从未出现）"`。

### B6 · 脚本 stdout 显式 UTF-8 〔审计 #15〕

两脚本 `main()` 入口处加 `sys.stdout.reconfigure(encoding="utf-8")`（含 stderr），消除 Windows GBK 控制台乱码——Orchestrator 按协议解析 l1_gate stdout，输出编码属接口稳定性而非美观问题。

### B7 · testing-toolbox `cli_verify` 协议闭环 〔审计 #9〕

**问题**：toolbox §二 step 4 / §六 要求注入 `cli_verify: true` 标记，但 reviewer-prompt.md 无此占位符，Reviewer 收不到。reviewer-prompt 已有等价语义（「两命令均空 + 含可执行脚本 → 自行构造 happy-path」），标记冗余。

**修复合同**（Occam：改非保护侧，不动治理文档）：toolbox §二 step 4 与 §六「执行方式」删除 `cli_verify: true` / `cli_verify: skipped` 标记机制，改述为「两命令均留空；Reviewer 按 reviewer-prompt.md §代码项目审查第 3 条，检测到可执行入口后自行构造最小 happy-path。无法复现时按 `deterministic_check: skipped` + skip_reason 上报」。

---

## C 组 · 运维动作与用户决策项

### C1 · 重跑 distill 回写注册表 〔审计 #5〕

注册表过期实证（2026-06-11 dry-run）：`false_generality` 实际 `count=1, last_confirmed=20260610-model-tiering-amendment, zero_streak=2`，文件中为 `0 / "" / 3`；其余条目 zero_streak 应为 4。动作：B1 落地后执行 `python scripts/distill_antipatterns.py --write`，人工核对报告快照与本节预期一致。

### C2 · `.converge/` 入库策略 〔审计 #6，**需用户裁决**〕

事实：`.gitignore` 整体忽略 `.converge/`（`git ls-files` 确认零跟踪），而 antipatterns.md 声称「删除本文件后运行 distill 可完全重建」——raw source 不入库，新 clone 无法重建 compiled 产物，衰减状态机依赖单机本地状态。

| 选项 | 动作 | 代价 |
|------|------|------|
| **(a) raw source 入库（推荐）** | `.gitignore` 改为忽略 `.converge/tmp/`、`.converge/active/`、`.converge/gate/`，提交 `done/` | 仓库携带运行日志（done/ 当前约 100KB）；done/ 本就是注册表生命周期的唯一数据源，与「compiled 产物可重建」声明自洽 |
| (b) 维持忽略 | antipatterns.md 删除「可完全重建」声明，改为「raw source 为本地数据，注册表统计值以最后一次 distill 为准」 | 重建承诺降级；多机/协作场景统计断裂 |

### C3 · 延后项（显式不在本计划范围）〔审计 #12a〕

SKILL.md 33KB 的入口减重与责任清单 18 条跳号编号重排：牵连全部跨文档引用（「对应职责 #N」），属独立减重计划范畴（已有 20260610 先例），本计划不做，避免与 A 组改动叠加放大 diff 审查面。

---

## 范围声明

- **须 ultraverge（A 组）**：SKILL.md（A1/A4/A5/A7）、refs/reviewer-prompt.md（A2/A6）、refs/state-schema.md（A3/A7 核对）、refs/decomposition-protocol.md（A3/A7）、refs/orchestrator-guide.md（A7）
- **标准评议（B 组）**：refs/antipatterns.md、refs/testing-toolbox.md、refs/quality-gate.md、scripts/l1_gate.py、scripts/distill_antipatterns.py、README.md（仅 A7 重命名波及）、README_en.md
- **明确不动**：CONSTITUTION.md（A4 默认方案下零修改；若裁决转向方案二则按修宪程序另行处理）、refs/rubrics.md、refs/contract-negotiation.md、refs/design-review-prompt.md、refs/executor-prompt.md、refs/model-tiers.md、`.converge/done/` 历史归档（A7 不改历史文件）
- **原子性**：A 组一次提交（ultraverge 验收通过后）；B 组 + C1 一次提交；C2 按用户裁决单独提交。任一组内验收失败则该组整体退回，不跨组阻塞。

## 验收清单

1. **A1**：SKILL.md 评议决策树四条 bullet 与 A1 插入块一致（第四条以收敛终稿为准）；全仓库 grep「需修订」零命中（done/ 归档与 git log 除外）。
2. **A2**：reviewer-prompt.md type 枚举 12 个 id 与 antipatterns.md id 全集逐字一致（脚本核对：两侧提取排序后 diff 为空）。
3. **A3**：grep `## 11. 层级收敛评估` 零命中；decomposition-protocol.md 与 state-schema.md 对层级收敛评估的编号表述均为 §12。
4. **A4**：SKILL.md 主循环 3i 无「（可选）」字样，且含宪法 #2 指针；与 CONSTITUTION 第二部 #2 无语义冲突（双向阅读核对）。
5. **A5**：SKILL.md grep `.meta/` 零命中。
6. **A6**：reviewer-prompt.md grep `skipped (reason` 零命中；skip 路径表述统一指向 `deterministic_check_skip_reason` 字段。
7. **A7**（若采推荐方案）：全仓库 grep `D11` 仅命中 `.converge/done/`、`docs/plans/done/` 与 git 历史；SKILL.md / README.md / orchestrator-guide / decomposition-protocol 零命中。
8. **B1**：antipatterns.md grep `Red Flag` 零命中。
9. **B2**：README_en.md 含 5 行终止状态表、目录树含 CONSTITUTION.md / design-review-prompt.md / antipatterns.md / model-tiers.md / distill_antipatterns.py、文首含权威源声明。
10. **B3**：quality-gate.md 阈值表行数 = l1_gate.py 告警信号种类数（timestamp_clustered 作为附带证据除外，表下注明）。
11. **B4/B5/B6**：l1_gate.py 与 distill_antipatterns.py 的 diff 仅含注释修正、动态措辞、encoding reconfigure 三类；`python scripts/l1_gate.py < 任意合法 JSON` 与 distill dry-run 在 Windows 默认控制台输出无乱码。
12. **B7**：testing-toolbox.md grep `cli_verify` 零命中；§六语义与 reviewer-prompt.md 代码项目审查第 3 条互相引用、无独立标记协议。
13. **C1**：antipatterns.md 中 `false_generality` 为 `confirmed_count: 1`、`last_confirmed: "20260610-model-tiering-amendment"`；`last_distilled_at` 晚于本计划执行日。
14. **C2**：按用户裁决执行后，antipatterns.md「可完全重建」声明与 `.gitignore` 实际策略自洽（二者必居其一）。
15. **双原则自检**：Bitter Lesson——本计划零新增机制，全部为既有机制的一致性修复；Occam——每项改动对应一个编号审计发现，无"顺手优化"。

## 状态

- [x] 计划写入（本文件）— 2026-06-11
- [x] 用户裁决：A1=允许缩小范围、A2=纳入合同、A4=方案一、A5=删除、A7=重命名、C2=(a) 入库（裁决记录见 .converge/done/20260611-audit-driven-corrections/retrospective.md §裁决结果）
- [x] ultraverge：3 并行 Reviewer 评议（R1/R3=可执行，R2=2 个 implementation/structural 阻断转 plan amendment，2:1 按多数推进）
- [x] 完整收敛：未触发（无 conceptual/architectural 阻断）
- [x] 强制设计审查（3 advisory findings，#1 已修复，#2/#3 见 retrospective §8）
- [x] B 组标准评议 + 执行
- [x] C1 distill --write + 核对（false_generality 1/20260610-model-tiering-amendment，last_distilled_at=2026-06-11T09:48:59Z）
- [x] 验收（2026-06-11 Orchestrator 逐项核验 15 项验收清单，结果见验收记录）
- [ ] 人工确认提交（A 组 / B 组+C1 / C2 三次原子提交）

## 验收记录（2026-06-11）

15 项验收清单：14 项通过；#10 字面偏差（`worker_variance` 信号在阈值表中无独立行——该缺口先于本计划存在，本计划仅承诺补 `total_budget_high`，已补）。A5 验收判据按 R2 plan amendment 收窄为 grep `.meta/deliberations` 零命中（SKILL.md 配置参数表中 `.meta/.converge/` 为合法自定义路径示例，非悬空引用）。功能实跑：l1_gate（`total_budget_high` 触发正常、UTF-8 无乱码）、distill dry-run（动态样本数措辞正常）均通过。

**验收时已知遗留**：(1) 本次收敛的 retrospective 归档后，11/12 反模式条目 zero_streak 已达 5——下次 `distill --write` 将批量降为 dormant 并退出 reviewer prompt 注入，属设计内衰减但需人工确认后执行；(2) `docs/plans/done/20260610-model-tiering-amendment.md` 的状态勾选为本计划执行前已存在的未提交改动，提交时勿混入三次原子提交。
