# Round 1 独立评议 — review-glm

```yaml
round: 1
verdict: 阻断需修复
deterministic_check: pass
deterministic_check_skip_reason: ""
blocking_issues:
  - id: 1
    description: >
      ocsr SKILL.md 新增的"脚本化边界"清单把"产物契约校验（输出路径一致性、存在性、schema 字段）"列为可脚本化项，
      其中"schema 字段"是不实承诺——ocrs_dispatch.py 实际不做任何 schema 字段检查。
      grep scripts/ocsr_dispatch.py 显示产物校验只有：路径占位符检查（line 359 "首查 prompt 的输出路径是否含未解析占位符"）、
      _snapshot_dir 目录快照（line 304/346/444）、_collision_report 覆盖检测（line 528）。
      没有 schema 字段存在性/类型/语义校验的任何代码。这违反判据 ②"逃生舱真实可用"的反向版本——
      "承诺的防呆型机制真实存在"：把一项 ocsr 不具备的能力写入"可脚本化"侧，等于把概念上属于判断力侧的东西
      （字段语义校验需要判断力）误标为机械侧、且实现并未兑现。修复：删除"schema 字段"四字，
      或改为"输出路径一致性、存在性"（与脚本实际能力对齐）。
    attribution: executor_limit
    severity: implementation
    location: ocsr/SKILL.md 派发驱动器节（ocsr.diff line 10）
suggestion_issues:
  - description: >
      任务描述称"该仓库哲学段改动受测试守护——test_skill_guidance.py 会断言哲学段关键表述"，
      但实际 tests/test_skill_guidance.py 没有任何针对哲学第 8 条（Bitter Lesson 段）关键表述的断言
      （不检查"封顶型先验/防呆型机制/逃生舱/fail-closed/fail-open/三分判据"等任何新增术语）。
      pytest 62 passed 仅证明改动未破坏既有断言，不证明哲学段被守护。
      建议在 test_skill_guidance.py 追加针对第 8 条新增表述的断言，使本轮改动进入回归守护范围。
  - description: >
      ocsr 把"预算"列为"可脚本化项"在概念上略有错位——ocrs_dispatch.py 自身不做预算裁决
      （grep 显示仅有注释"scope enum（与 budget_gate ROLE_CONSUMES 对齐）"，无 budget_gate 实现），
      预算门控实际由 converge budget_gate.py 执行。建议改为"预算（通过引用 converge budget_gate）"
      或从清单中删除，避免读者误以为 ocsr 自身具备预算门控能力。
  - description: >
      init-agent-docs 新增段第三句"推理错误随模型变强减少，机械失误随任务量缩放"在因果上稍跳跃——
      读者需自行连接"推理错误随模型变强减少 → 故封顶型先验减值"和"机械失误不随模型强度变化 → 故防呆型机制不过时"。
      建议改写为显式因果："模型推理错误随模型变强而减少（故封顶型先验随模型变强减值），
      机械失误随任务量缩放、不随模型强度变化（故防呆型机制不过时）"。
```

---

## 审查要点逐条结论

### 1. 语义一致性（三层映射）

通过。三处是同一判据的三层表述，无相互矛盾：

- **init-agent-docs**（权威表述层）：抽象定义"封顶型 vs 防呆型"+ 三分判据，不绑定具体机制。
- **converge**（哲学锚点 + 兑现层）：在判据后紧跟"本 SKILL 的兑现：`需重新设计` / `contract_amendment_required`"，并把 budget_gate / archive contract / ledger 划入防呆型，verdict 裁决 / prompt 工程 / 重试 prompt 修订划入判断侧。
- **ocsr**（边界清单层）：把"脚本不做编排判断"扩为可/不可脚本化项清单。

三处用各自层读者的语言，无全文复制，无术语漂移（"封顶型先验/防呆型机制/逃生舱/fail-closed/fail-open"在三层含义一致）。

### 2. Bitter Lesson 解读的准确性

通过（含一处可改进措辞，见 suggestion 3）。Sutton 2019 原文核心反对的是"用领域知识代偿模型能力"（注入后系统上限被设计者水平封顶）。本判据把其反对的对象精确化为"封顶型先验"，把其不反对的对象（机械机制）命名为"防呆型机制"——这对术语在 Sutton 原文不直接出现，但作为操作化映射是忠实的：Sutton 反对的从来不是 lint、CI、契约校验这类防失误机制，而是"用人类专家启发式替代模型 search/learning"。三分判据把这层区分固化为可检验条款，无概念错误。

### 3. 逃生舱声明的事实性

**`需重新设计` 真实可用——通过**：
- `SKILL.md:185`："verdict = 需重新设计 → 不进入修复循环。向用户报告产物存在方向性缺陷，由用户决定：重写产物后重新评议、缩小范围后重新评议、或走主观接受程序"
- `SKILL.md:98` 在"宪法强制"确认点表中明确"必须报告用户决定重写/缩范围/主观接受"
- `budget_gate.py:122` `VERDICTS = ("可执行", "阻断需修复", "需重新设计")` 三元组包含
- `refs/orchestrator-guide.md:362` 自主推进底线列表中"需重新设计 verdict"被列入"永不因自主而跳过"
- 评估：逃生舱真实可用，未被任何规则架空。

**`contract_amendment_required` 真实可用——通过**：
- `refs/contract-negotiation.md:46-50` 完整"contract_amendment_required 流程"节，明确"Reviewer 标记 → Orchestrator 先回写 contract.md 本体 → 再让 Executor 按新 contract 调整"
- `refs/contract-negotiation.md:84` "contract.md 一旦定稿，Round 1+ 中只有通过 contract_amendment_required 流程才能修改"
- `refs/reviewer-prompt.md:80` 标记位 `contract_amendment_required: <true | false>`
- `SKILL.md:231` "若有 contract_amendment_required → 先回写 contract.md 再继续"
- `SKILL.md:321`（C-13）"contract 演进导致的矛盾不计入 Type O"——这是关键反架空条款，确保 contract 演进不会因被算成漂移而触发其他规则
- 评估：逃生舱真实可用，机制闭环。

### 4. 边界划分的正确性

**阻断**：ocsr 边界清单中"schema 字段"项无实现支撑（详见 blocking_issue #1）。其余项划分正确：
- 错峰（5s 间隔）、看门狗（硬阈值终止）、路径占位符检查、目录快照、覆盖检测、遥测——均为纯机械，正确划入可脚本化侧。✓
- 选模型、prompt 残注入、verdict 裁决、重试 prompt 修订——正确划入判断侧。✓
- 但"schema 字段"既无实现，且字段语义校验本身就需要判断力（区分必填/选填、类型语义），不应一概划入机械侧。
- "预算"项有概念错位但不阻断（详见 suggestion 2）。

### 5. 冗余度与读者匹配

通过。三处刻意不互相复制全文，每层用各层读者的语言：
- init-agent-docs 读者是"初始化执行者"——给原则和判别样例表，不绑定 converge/ocsr 机制 ✓
- converge 读者是"收敛编排者"——给宪法锚点 + 本 SKILL 的具体兑现 ✓
- ocsr 读者是"派发编排者"——给可/不可脚本化项清单 ✓
- 无层间越权（init-agent-docs 不引用 converge/ocsr 内部机制，converge 不展开 ocsr 细节，ocsr 仅引用"与 converge 宪法同构"）。

### 6. 与既有文本的冲突

通过：
- **init-agent-docs**：第 8 条原判别样例表（agent_links.py / changelog.py / 计划文件 / 完工清单）保留不变；新增段插在"判别原则"段落（line 153）之后、第 9 条之前，是对原判别原则（"先验如果能随项目演进自然扩展..."）的强化与精确化，不冲突。
- **converge**：宪法第一部 Bitter Lesson 原行（"这东西是通用机制还是针对当前模型的补丁？机制硬编码，补丁做成 compiled 产物"）保留；新增段是"精确边界"，是原行的细化，不冲突。
- **ocsr**："脚本不做编排判断——选模型、prompt 残注入、verdict 裁决仍由 orchestrator 负责"原句保留并被扩展（追加"重试时的 prompt 修订"），不冲突。

---

## 机械核对证据

### 1. pytest（确定性检查）

```
命令：python -m pytest tests/ -q   (在 <user-home>/.agents/skills/init-agent-docs)
结果：62 passed in 24.33s
exit code: 0
```

**但**：tests/test_skill_guidance.py 全文 173 行无任何断言涉及哲学第 8 条新增表述（"封顶型先验/防呆型机制/逃生舱/fail-closed/fail-open/三分判据"）。62 passed 仅证明既有断言未破坏，不证明哲学段被守护。详见 suggestion 1。

### 2. converge SKILL.md 逃生舱事实性核对

`grep -n "需重新设计\|contract_amendment_required"` 在 converge 仓库 24 处命中，关键命中：

- `SKILL.md:25` workflow 图：`需重新设计 → 用户决定：重写/缩小范围/主观接受`
- `SKILL.md:98` 宪法强制表：`需重新设计 verdict | 宪法强制 | 保留——必须报告用户决定重写/缩范围/主观接受`
- `SKILL.md:185` 评议处置：`需重新设计 → 不进入修复循环...由用户决定`
- `SKILL.md:213` round-N.md 格式：`reviewer verdict（可执行/阻断需修复/需重新设计）`
- `SKILL.md:231` `若有 contract_amendment_required → 先回写 contract.md 再继续`
- `SKILL.md:321` C-13：`contract_amendment_required — 先回写 contract.md 本体...contract 演进导致的矛盾不计入 Type O`
- `SKILL.md:335` C-19 意图漂移检测引用 `contract_amendment_required 反复出现（≥2 次）`
- `budget_gate.py:122` `VERDICTS = ("可执行", "阻断需修复", "需重新设计")`
- `refs/contract-negotiation.md:46` `## contract_amendment_required 流程` 专节
- `refs/reviewer-prompt.md:56` verdict schema、`:80` 标记位、`:89` 触发条件
- `refs/orchestrator-guide.md:164` 处置表、`:209` ingest-verdict、`:362` 自主底线列表

**结论**：宪法新增段对两个逃生舱的描述（"`需重新设计` verdict 退出修复循环、`contract_amendment_required` 允许模型修合同本身"）与机制定义完全一致——逃生舱真实可用。

### 3. ocsr schema 字段检查的事实性核对

`grep -n "schema\|字段\|输出路径\|存在性"` 在 ocsr/scripts 命中：
- `ocsr_dispatch.py:359` `"首查 prompt 的输出路径是否含未解析占位符。"`
- `ocsr_dispatch.py:973` `help="聚合字段（默认 role）"`（遥测聚合参数，非产物 schema）

`grep -n "产物契约\|output.*check\|validate\|verify\|存在性\|覆盖检测\|snapshot"` 命中：
- `ocsr_dispatch.py:304` `def _snapshot_dir(path)` 目录快照
- `:346 / :444` 调用 `_snapshot_dir`
- `:528` `_collision_report(output_dir, snapshot_before, expected_names, ledger)`

`grep -n "budget\|gate\|预算"` 命中：
- `ocsr_dispatch.py:72` 注释 `# scope enum（与 budget_gate ROLE_CONSUMES 对齐）`
- 无任何 budget_gate 实现代码

**结论**：ocsr 产物契约校验实际能力 = 路径占位符检查 + 目录快照 + 覆盖检测（三项均为路径/存在性层面）。无 schema 字段检查。新增段措辞与实现不符，构成阻断。

### 4. init-agent-docs 测试断言核对

`read tests/test_skill_guidance.py`（173 行）共 7 个测试方法，断言关键词均为：
- 源优先级、instruction 文件、AGENTS 模板机制、eval-baseline、maintain.py / memory 索引、worktree 四动作 / reference-transaction hook
- **无任何**针对哲学第 8 条 Bitter Lesson 段（含新增"封顶型 vs 防呆型"表述）的断言

---

## 执行证据

- **产出文件**：`<user-home>/.agents/skills/converge/.converge/active/20260725-flow-prior-legitimacy/reviews/review-glm.md`
- **字节大小**：（见下条命令验证）
- **关键工具调用清单**：
  - Read：plan.md、artifact/init-agent-docs.diff、artifact/converge.diff、artifact/ocsr.diff、init-agent-docs/SKILL.md（哲学第 8 条上下文）、converge/CONSTITUTION.md（全文）、converge/SKILL.md（第 90-104、180-219 行）、ocsr/SKILL.md（第 40-79 行）、init-agent-docs/tests/test_skill_guidance.py（全文）
  - Grep：converge 全仓库 `需重新设计|contract_amendment_required`（24 命中）；ocsr/scripts `schema|字段|输出路径|存在性`（2 命中）；ocsr/scripts `产物契约|validate|verify|snapshot`（5 命中）；ocsr/scripts `budget|gate|预算`（12 命中，关键命中 ocsr_dispatch.py:72 仅注释）；ocsr/scripts/ocsr_dispatch.py `budget|gate|预算`（确认 ocsr 自身无预算裁决实现）
  - Bash：`python -m pytest tests/ -q`（init-agent-docs，62 passed，exit 0）；`ls -la reviews/`（确认目录为空，避免覆盖）
