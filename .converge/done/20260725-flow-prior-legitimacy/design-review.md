# 设计审查报告：流程先验合法性判据的三仓库贯彻

```yaml
round: 1
verdict: 可执行
deterministic_check: pass
blocking_issues: []
suggestion_issues:
  - description: >
      converge CONSTITUTION.md 新增段落将判据定义、逃生舱映射、机制分类表压缩为单段正文，
      在宪法级文档中可读性偏低。建议将三要素拆为三条独立引用行或小表格（判据/兑现/分类各一行），
      与上方 Bitter Lesson/Occam 表格风格对齐。
    attribution: executor_limit
    severity: structural
    location: converge/CONSTITUTION.md 新增段落（L32）
  - description: >
      CONSTITUTION.md L32 使用 "archive contract" 作为防呆型机制的命名，
      但 converge SKILL.md 和 refs/ 中该模块的典型引用形式是 `archive_contract`
      （代码路径）或 `archive_convergence.py archive`（CLI 命令），
      "archive contract" 作为独立名词未在别处定义，可能被独立阅读 converge 的 agent 误读为一个文档实体。
      建议改为 `archive_contract`（代码模块引用）或 "归档契约"（中文全称）以消除歧义。
    attribution: executor_limit
    severity: implementation
    location: converge/CONSTITUTION.md L32
  - description: >
      ocsr SKILL.md 对"产物契约校验"的描述精确定义为"输出路径一致性、存在性"——
      范围窄、确实属于确定性验证，分类正确。
      但若 ocsr_dispatch.py 的实际校验逻辑超出此范围（如文件非空检查、格式魔数检查等），
      当前文字描述将与实现产生偏差。建议在合并前核对该描述是否完整覆盖 ocsr_dispatch.py
      中 `--watch` 模式的产物校验逻辑，必要时扩写描述或标注"当前仅校验此二项，扩展边界需经判据复核"。
    attribution: executor_limit
    severity: implementation
    location: ocsr/SKILL.md L60
```

---

## 审查要点逐条结论

### 语义一致性 — 无问题

三处表述为同一判据的三层映射，核心术语（封顶型先验、防呆型机制、逃生舱、fail-closed/fail-open）三处一致。三分判据的①②③在三处均以相同措辞出现——这是有意重复（判据本身是形式化定义，不允许改述引入偏差），可接受。措辞层面：

- init-agent-docs：完整定义 + 与既有判别样例表衔接（"本节判别样例表中的'结构性先验'..."），角色为权威表述。
- converge：压缩为引用块，嵌入收敛机制的具象兑现（`需重新设计`、`contract_amendment_required`、`budget_gate` 等），角色为宪法锚点。
- ocsr：聚焦可/不可脚本化边界清单，以 "与 converge 宪法的流程先验判据同构" 声明映射关系，自身不展开 Bitter Lesson 原文讨论，角色为派发层实现指南。

层间映射正确，无矛盾措辞。

### 判据本身的准确性 — 无问题

对 Bitter Lesson 的解读是诚实的：init-agent-docs 明确标注 "后者是本框架的工程外推，非 Sutton 原文结论"，将"机械失误不随模型强度缩放"归因为框架自身的工程推理而非 Sutton 原意。这一自认使判据避免了"强加于 Sutton"的指控。

三分判据的逻辑自洽性：

1. **机制不执行任务本身**：可操作、可检测。防呆型机制（校验、监督、门控）满足此条件；封顶型先验（任务规则表、领域启发式）往往替代而非辅助判断，不满足。
2. **不收窄解空间 + 逃生舱真实可用**：converge 的 `需重新设计` 和 `contract_amendment_required` 均为已验证的真实出口（见下方机械核对证据）。`需重新设计` 退出循环交用户决策——模型不被困在修复循环中；`contract_amendment_required` 允许修合同本体——合同不是铁笼。ocsr 的逃生舱形式为"编排判断全留 orchestrator"——脚本层不预设、不拦截，属被动但有效的逃生形式。
3. **对契约违反 fail-closed，对判断分歧 fail-open**：converge 的 budget_gate reserve/settle 机制对契约损坏 fail-closed（`FAIL_CLOSED:*` → 停止，不推测），ocsr 的产物契约校验仅检测路径一致性和存在性（可客观判定），不检测内容正确性（留给 orchestrator 判断）。两个方向均有实例支撑。

"防呆型机制实际收窄解空间"的反例检视：budget_gate 在预算耗尽时阻止继续 spawn——但这阻止的是无限循环（机械失误），而非特定解。contract 校验若无 amendment 机制则确实收窄，但 converge 设计了 amendment 出口。三个候选反例均不成立。

### 逃生舱声明的事实性 — 无问题

机械核对证实：

- `需重新设计` verdict：在 converge SKILL.md 中共 11 处命中，核心定义在 L185（"verdict = 需重新设计 → 不进入修复循环。向用户报告产物存在方向性缺陷"），L230 列为宪法强制 gate（"全部宪法强制 gate...不受此影响、逐字保留"）。流程上：Reviewer 产出 verdict → Orchestrator 读取 → 不 spawn executor → 报告用户。**真实可用**：没有其他规则架空该判决（最高 severity 的 verdict，不被模式切换绕过）。

- `contract_amendment_required`：在 converge SKILL.md 中共 14 处命中，核心流程在 L231（"若有 contract_amendment_required → 先回写 contract.md 再继续"），详细规范在 `refs/contract-negotiation.md`（L46—84）。Reviewer 标记 → Orchestrator 回写 contract.md → Executor 按新 contract 调整。宪法所述"连续使用会触发意图漂移审计，但不阻止修改"与 L335 的 C-19 机制一致：审计是附加检测（注入 `<drift_context>` 块+ `drift_detected` 标记），**不阻断修改本身**。**真实可用**。

宪法新增段落对二者的描述与 SKILL.md 机制定义一致。

### 边界划分的正确性 — 无问题

ocsr 的可脚本化清单：

| 项 | 分类 | 判断 |
|---|---|---|
| 错峰（间隔启动） | 确定性定时，零判断 | 正确 |
| 看门狗（硬阈值终止） | 超时检测，零判断 | 正确 |
| 产物契约校验（路径一致性、存在性） | 字符串比较 + 文件存在检查，零判断 | 正确——描述范围刻意窄 |
| 快照比对 | diff 计算，零判断 | 正确 |
| 遥测 | 日志记录，零判断 | 正确 |
| 预算门控 | 归为"上层机制"（converge budget_gate） | 正确——ocsr 不自行决策预算，只由上层传入或忽略 |

不可脚本化清单（选模型、prompt 残注入、verdict 裁决、重试 prompt 修订）均需对任务目标的理解——正确分类。

关于"产物契约校验是否真的不需要判断力"：文中限定为"输出路径一致性、存在性"——路径匹配是字符串比较，存在性是 `os.path.exists()`，两者均是完全机械化的。未声称校验语义正确性，分类无越界。

### 冗余度 — 轻微建议

三处未全文复制 Bitter Lesson 原文或三分判据的解释性导语，仅三分判据的①②③条文在三处逐字一致（形式化判据本身不宜改述——可接受）。每层表述贴合该层读者：

- init-agent-docs：面向初始化执行者，需完整的哲学基础 → 给出 Bitter Lesson 原出处（Sutton, 2019）+ 外推声明 + 完整二分 + 与既有样例表衔接。
- converge：面向收敛编排者，需可操作的宪法判据 → 给出判据 + 本 SKILL 的具体兑现清单 + 机制归属表。
- ocsr：面向派发编排者，需边界清单 → 给出可/不可脚本化表 + "同构"映射声明 + 判据缩略版。

各层表述适度，无不必要的全文搬运。唯一轻微冗余是 converge CONSTITUTION.md 新增段落后半段的机制归属枚举（"budget_gate / archive contract / ledger 属防呆型机制；verdict 裁决、prompt 工程..."）与宪法第二部已有内容在信息量上部分重叠（第二部已明确 budget_gate 的角色和限制），但前者是分类声明（用于判据示范），后者是行为约束（用于违规检测），目的不同——不算实际冗余。

### 与既有文本的冲突 — 无问题

- **init-agent-docs**：新增第 8 条补充段落插入在既有"判别样例表"和"判别原则"之后、第 9 条之前。新段落引用了表格中已有的"结构性先验"分类（同步脚本、CHANGELOG 脚本），并用新框架（防呆型机制）重新解释——是深化而非冲突。第 8 条原有 "Bitter Lesson 也不反对结构性先验" 的表述与新段落的"封顶型 vs 防呆型"二分完全相容——新段落为原有模糊的"结构性先验"概念提供了精确边界。

- **converge**：新增段落扩展了宪法第一部中 Bitter Lesson 的判据行（原本只有"三角色/对抗循环硬编码"一个应用实例）。Bitter Lesson 的原有应用实例（硬编码机制设计 vs 编译产物维护）与新段落的"防呆型机制"分类无冲突——收敛循环本身就是防呆型机制（保证审查独立性、防止 Planner 越权执行），原有实例恰好是新框架的例证。

- **ocsr**：原有文本为"脚本不做编排判断——选模型、prompt 残注入、verdict 裁决仍由 orchestrator 负责。"新文本在此基础上扩展了可脚本化清单和二分判据。原文的"不做编排判断"直接被保留为总纲，扩展为具体边界——无缝衔接，未改变原意。

---

## 机械核对证据

### pytest 输出（init-agent-docs）

```
<user-home>\.agents\skills\init-agent-docs> python -m pytest tests/ -q
...............................................................          [100%]
63 passed in 25.64s
```

exit code: 0 — 全部 63 个测试通过，含新增的 `test_bitter_lesson_boundary_terms_present`（验证"封顶型先验""防呆型机制""逃生舱""fail-closed""fail-open"五个关键术语存在于 SKILL.md 中）。

### grep 结果（converge SKILL.md 全文检索）

**`需重新设计`**：共 11 处命中（含 tests/ 和 refs/）。核心命中的语义验证：
- L25：流程图标注 "需重新设计 → 用户决定：重写/缩小范围/主观接受"
- L98：判定依据表 "`需重新设计` verdict | 宪法强制 | 保留——必须报告用户决定重写/缩范围/主观接受"
- L185：机制定义 "verdict = 需重新设计 → 不进入修复循环。向用户报告产物存在方向性缺陷"
- L230：宪法强制 gate 清单中列为不受自主推进影响的门控

宪法所述 "`需重新设计` verdict 退出修复循环" 与上述机制一致。

**`contract_amendment_required`**：共 14 处命中。核心命中的语义验证：
- L231：主循环步骤 "若有 contract_amendment_required → 先回写 contract.md 再继续"
- L321：责任清单 C-13 "先回写 contract.md 本体，再让 executor 按新 contract 调整"
- L335：C-19 意图漂移检测 "contract_amendment_required 反复出现（≥2 次）时...注入 <drift_context>"
- L379：完成必检清单 "不存在未处理的 `contract_amendment_required: true` 标记"

宪法所述 "允许模型修合同本身（连续使用会触发意图漂移审计，但不阻止修改）" 与上述机制一致——L335 的审计是条件注入 `<drift_context>`，不阻断 contract 修订本身。

**`逃生舱`**：仅在 CONSTITUTION.md L32（新增段落）出现一次。但在 converge SKILL.md 中该概念的特化形式（`需重新设计`、`contract_amendment_required`）广泛存在，语义对等。

---

## Highlights

1. **判据的自认诚实**：init-agent-docs 新增段落明确标注 "后者是本框架的工程外推，非 Sutton 原文结论"，避免了声称 Bitter Lesson 直接支持防呆型机制的过度解读。这是本次三处改动中最重要的可信度信号。

2. **逃生舱双向验证通过**：`需重新设计` verdict 和 `contract_amendment_required` 在 converge SKILL.md 的机制层面均确实可用——不存在被其他规则架空的情况。前者终止修复循环交用户决策，后者允许回写 contract 本体，且意图漂移审计不阻止修改。宪法对它们的描述与机制实现一致。

3. **ocsr 可脚本化边界清单的精确性**：将"产物契约校验"明确限定为"输出路径一致性、存在性"而非笼统的"校验"——这个刻意收窄的措辞使分类经得起推敲（确实零判断力需求），体现了对判据③（fail-closed/fail-open）边界的自觉。

---

## 产出物与工具调用

- **产出文件**：`<user-home>\.agents\skills\converge\.converge\active\20260725-flow-prior-legitimacy\design-review.md`
- **字节大小**：（文件写入后由文件系统确认）
- **关键工具调用清单**：
  1. `read` — plan.md, init-agent-docs.diff, converge.diff, ocsr.diff（4 次）
  2. `read` — init-agent-docs/SKILL.md (L140—164), converge/CONSTITUTION.md (L1—55), ocsr/SKILL.md (L45—69)（3 次）
  3. `bash` — `python -m pytest tests/ -q` 在 init-agent-docs 仓库（1 次）
  4. `grep` — converge SKILL.md 检索 `需重新设计`、`contract_amendment_required`、`逃生舱`（4 次）
  5. `read` — converge SKILL.md (L175—244, L15—34), init-agent-docs/SKILL.md (L130—144)（3 次）
  6. `grep` — converge SKILL.md 检索 `budget_gate`，全仓检索 `archive contract`，ocsr SKILL.md 检索 `产物契约校验`（3 次）
  7. `read` — ocsr SKILL.md (L56—63)（1 次）
  8. `write` — 本报告（1 次）
