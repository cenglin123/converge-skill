---
round: 2
reviewer_backend: opencode
reviewer_instance_id: 20260912_165156_c20fe2
generated_at: 2026-09-12T09:00:27.185739+00:00
verdict: 阻断需修复
---
verdict: 阻断需修复

# uv-init-2 · O6 material 增量复核机制（candidate-1）初审

> Reviewer：ultraverge 初审 #2（fresh、独立上下文；未读 uv-init-1.md、未读其他 reviewer 产出）。
> 审查对象：`.converge/active/20260912-o6-material-delta-recert/plan.md`（candidate-1，30961 bytes）。
> 实核方式：逐行实开 `plan.md`、`CONSTITUTION.md`、`SKILL.md`、`refs/*`、`scripts/orchest.py`、`scripts/archive_contract/model.py`、`scripts/budget_gate.py`、`tests/*`、B 归档证据；preflight 实跑；calibration hash 实算。

---

## 一、前置自检（5 问 + Q6）

| # | 问题 | 结论 | 依据 |
|---|---|---|---|
| Q1 | 产物身份自洽 | 通过 | 计划是"O6 material 修订分级 + 增量复核"的治理计划，名称/描述/实现同指一事；D1/D2 分工清晰 |
| Q2 | 产物边界诚实 | 通过 | §8 Non-Goals 明确不放宽 decisional 全量规则；§11 如实声明不声称机械闭环（R-1 残余） |
| Q3 | 产物数据纯度 | 基本通过 | 无项目业务数据硬编码；但 §4/§9 引用宿主环境路径 `~/.config/opencode/memories.md`（见 I-14） |
| Q4 | 职责边界自洽 | **触发关注** | "谁验证未触及 decisional"存在职责灰色地带：作者声明 + 单一 delta reviewer 语义判断，机械层只做声明交集（见 I-2/I-5） |
| Q5 | 命名一致性 | 基本通过 | `change_class`／`declared_class`／`changed_sections`／`decisional_anchors` 命名可辨识；但 `decisional_anchors` 语义歧义（见 I-2） |
| Q6 | 产物 vs 原始需求一致 | 通过（背景材料为 B 成本样本） | §2.1 成本论断可核（retro:75/:80）；O6 议题出处 `docs/plans/active/20260911-converge-operational-envelope.md:25` 实核 |

---

## 二、DR 7 维逐维结论

### DR1 一致性（Consistency）— concerns_found
- 实核为**真**：§2.2 全部 orchestr.py 锚点行号可核（`:1095`/`:1116-1117`/`:1133`/`:1171-1175`/`:1185-1186`/`:1207-1259`/`:1267-1272`/`:1273-1279`/`:1280-1293`/`:1303-1310`/`:1335-1337`/`:1340-1361`/`:1144-1149`/`:1204-1205`）；`REVIEWER_AUTHORITIES`(`model.py:91-94`)、`SKILL.md:462`、`state-schema.md:103-104`、`orchestrator-guide.md:23/:32` 逐字吻合。
- **不一致 1**：§3.4 要求 delta verdict "必须为 `可执行`"，但 §3.5 伪码（:161）与 A-9（:240）只做 `verdict != 阻断需修复` → `需重新设计` 会被放行（I-3）。
- **不一致 2**：A-13（:244）要求"旧句消失"，但 §12.3/§12.4 的替换文本是"原句保留 + 追加新段"（:326-327、:333-335），旧句**不会**消失（I-6）。
- **不一致 3**：§12.1 保留 `state-schema.md` "唯一 `converge.material-revision/v1` 块"措辞，而 §3.5 引入"全部 material 块（链）"语义（I-10）。
- **不一致 4**：§5 F5 只列 3 个 material 测试类（:351/:848/:1184），遗漏 `TestMaterialGateLegacySkip`（:989）（I-9）。

### DR2 完整性（Completeness）— concerns_found
- `decisional_anchors=["*"]` 缺省与机械交集语义缺失（I-1）。
- `changed_sections`／`decisional_anchors` 的**非空**校验未进入 §3.5 伪码；空列表可平凡绕过交集（I-5）。
- 链回溯未定义 reopen/多 revision 边界（§3.5:144 "all material blocks" 无 revision 过滤）（I-11）。
- D2 未覆盖"一致 `阻断需修复` 但仅 implementation/structural"分支（I-12）。
- 对抗面 §11 对"谎报分级"的机械拦截依赖作者如实声明 `changed_sections`；漏报方向已承认（R-1），但**漏报 decisional_anchors**（对称攻击）未列入风险（I-5）。

### DR3 可维护性（Maintainability）— concerns_found
- 受控章节词表、判定标准同时存在于 plan §3.2 与 §12.3 新句（guide），单一权威源未声明；后续漂移风险。
- `["*"]` 缺省是一个"反直觉陷阱"：文档意图保守，机械实现可能反向（I-1）。
- 归类的正确性完全落在单一 fresh delta reviewer 的语义判断上，无第二视角；DR3 层面的独立复核强度低于现行双权威（计划已承认 R-2，但属机制固有代价，非缺陷）。

### DR4 职责边界（Boundary Clarity）— concerns_found
- 边界链：作者**声明** `change_class`/`changed_sections`/`decisional_anchors` → 机械门做**声明交集** → 单一 reviewer 做**语义实核** → 争议 fail-safe。机械层只校验声明之间的一致性，**不校验声明与真实 diff 的一致性**。
- 因此"谁验证未触及 decisional"= 单一 delta reviewer；该判断无法被机械复核。计划 §11 如实声明，但 §1 的"三重机械校验替代第二权威"措辞与此不符（I-15，suggestion）。

### DR5 残留与冗余（Residue & Redundancy）— clean（有 1 项待确认）
- 未见迁移考古式措辞；§12.3/§12.4 保留原句属刻意增补，非残留。
- 待确认：§3.5 伪码 `if blocks[j].change_class == decisional: continue`（:154）为死代码（`i` 已取 max decisional，j>i 必非 decisional），保留易误导（I-16，suggestion）。

### DR6 可移植性（Portability）— concerns_found（低）
- §4/§9 以宿主绝对语义路径 `~/.config/opencode/memories.md` 作为用户裁决权威源；治理计划跨环境不可自足复现（I-14，suggestion）。

### DR7 可扩展性（Scalability）— concerns_found
- 链式回溯为 O(n) 全链重验；块数增长时每次 finish 重算全部 hash（可接受，但未声明上限/复杂度）。
- `decisional_anchors` 按"最近一个 decisional 块"取，链一长即出现"更早 decisional 章节失去保护"的覆盖衰减（I-2）。

---

## 三、逐条 issue

### 阻断级

**I-1（structural）`["*"]` 缺省在机械交集下反向失效**
- 位置：`plan.md:106`（§3.1）、`:162`（§3.5）
- 事实：§3.1 声明旧 decisional 块缺省 `decisional_anchors=["*"]`，"任何 non-decisional 变更都会触发交集非空 → 保守 fail-closed"。但 §3.5:162 写作 `blocks[j].changed_sections ∩ blocks[i].decisional_anchors == ∅`。`"*"` 不在 12 项受控词表内，朴素集合交集 `{任意词} ∩ {"*"} = ∅`，条件**成立** → 放行到 delta 路径，与文档声明的保守意图完全相反。伪码/实现要点未定义 `"*"` 的通配语义。
- 单选修法：A) 在 §3.5 增一句"若 `decisional_anchors` 含 `"*"`，交集判定直接视为非空 → `FAIL_CLOSED`，不得作集合交集"；B) 旧块缺省不用 `["*"]`，改为在链回溯见到旧 decisional 块时**直接要求其后全部块 full-pair**（显式分支，不引通配符）。二选一。

**I-2（architectural）`decisional_anchors` 语义与作用域未定，覆盖会随链衰减**
- 位置：`plan.md:104`（§3.1）、`:121`（§3.2）、`:162`（§3.5）
- 事实：字段定义为"该 decision 内容所在的章节标识集合"。若按"该块本次触及的 decisional 章节"理解，则 §3.5:162 只对**最近一个** decisional 块 `blocks[i]` 求交，更早 decisional 块覆盖过的章节不再受保护。例：b1(decisional, anchors=[acceptance]) → b2(decisional, anchors=[numeric-defaults]) → b3(non-decisional, changed_sections=[acceptance])：与 b2 交集为 ∅ → 机械放行，但 acceptance 是判定章节。
- 单选修法：A) 明确 `decisional_anchors` = "该 revision 全量判定承载章节集合"，并接受只要最近块即为全局快照；B) 保留 per-block 语义，但交集对象改为**所有** decisional 块 anchors 的并集（或维护一个累积 decisive-set）。二选一，并同步写入 §12.1 新增 bullet 的字段定义。

**I-3（structural）delta verdict 判定与规范句不一致**
- 位置：`plan.md:136`（§3.4 "verdict 必须为 `可执行`"）vs `:161`（§3.5 `verdict != 阻断需修复`）、`:240`（A-9）
- 事实：复用现行负向检查（`:1340-1361` 仅拒 `阻断需修复`）时，`verdict: 需重新设计` 的 delta reviewer 会被放行；A-9 也只测"阻断"用例，未覆盖"需重新设计"。
- 单选修法：A) 把 §3.5 实现要点与 A-9 改为正向校验 `verdict == 可执行`，并补 `需重新设计` 对抗用例；B) 把 §3.4 规范句降级为 `!= 阻断需修复` 并说明接受 `需重新设计` 的理由（与全量对语义一致）。二选一；推荐 A。

**I-4（structural）delta 候选缺少 `artifact`/`material_revision` 的块绑定校验**
- 位置：`plan.md:155-161`（§3.5 delta 校验）
- 事实：现行三处锚点中，full-pair 会校验 `payload.artifact.sha256/size` 与 `payload.material_revision.sha256`（对应代码 `:1267-1272`、`:1273-1279`）。delta 分支只校验 `delta.base_plan_sha256`/`delta.current_plan_sha256`/`declared_class`，**未**要求 `payload.artifact == blocks[j].candidate_artifact`、`payload.material_revision.sha256 == blocks[j] canonical hash`、locator id 一致。攻击者可使 `artifact` 指向别的字节而 `delta.current_plan_sha256` 正确，payload 仍 byte-equal（prompt=output），机械通过。
- 单选修法：A) 在 delta 校验复用现有锚点（artifact == blocks[j].candidate_artifact；material_revision.sha256 == blocks[j] hash；locator id 一致）；B) 显式声明 delta 路径下 `artifact` 字段被 `delta.current_plan_sha256` 取代并从 review-target 移除，避免双重真相。二选一。

**I-5（structural）声明字段缺非空校验 + 风险穷举缺"漏报 anchors"方向**
- 位置：`plan.md:103-104`（§3.1 non-empty 要求）、`:162`（§3.5 无校验）、`:276`（R-1）
- 事实：①§3.5 伪码未校验 `changed_sections` 非空；`changed_sections=[]` 时交集恒 ∅，A-11-4 的"机械拦截"平凡失效。②R-1 只覆盖"谎报 `changed_sections`（漏报 decisional 章节）"；对称的"漏报 `decisional_anchors`"（new decisional 块少声明锚点）未列入风险，而 I-2 表明该方向同样能弱化机械层。
- 单选修法：A) §3.5 增补"`changed_sections` 为空或含词表外值 → `FAIL_CLOSED`"，并把 R-1 改写为覆盖 changed_sections / decisional_anchors 两个漏报方向；B) 引入一个不可由作者缩写的全局 decisive-set（见 I-2 B），使标注成为冗余。二选一。

**I-6（structural）A-13 "旧句消失"与 §12.3/§12.4 增补式改写自相矛盾**
- 位置：`plan.md:244`（A-13）、`:321-327`（§12.3）、`:329-335`（§12.4）
- 事实：§12.3/:23 与 §12.4/:32 的替换文本 = 原句逐字保留 + 追加新段。A-13 统一要求"逐条 grep 新句存在、旧句消失"，对这两条永远无法满足（旧句仍在），使 A-13 非机械可判定。
- 单选修法：A) A-13 改为按 §12 每条标注动作类型（replace → 旧句消失；append → 原句保留 + 新段存在），逐条判定；B) 把 §12.3/§12.4 改成替换整行/整段（原句不再逐字保留）。二选一。

**I-7（implementation，事实失真）"现有 7 个 material 测试"数量错误**
- 位置：`plan.md:181`（§3.7）、呼应 `:243`（A-12）
- 事实：`tests/test_loop_a_coverage.py:443-1421` 区间内直接定义的 material 相关测试实核约 17 个（ClosureGate 6 + LocatorResolution 4 + LegacySkip 3 + QualifyByCurrentBlock 3 + `test_existing_material_tests_still_pass` 1；pytest 因继承收集更多）。"7 个"与文件实况不符。
- 单选修法：A) 改为实测数量；B) 删去计数，仅保留"`tests/test_loop_a_coverage.py:443-1421` 区间既有断言行为不变"。二选一；推荐 B（避免数字漂移）。

### 建议级

**I-8（structural）A-12 非机械可判定且范围会因新增测试漂移**
- 位置：`plan.md:243`（A-12）、`:204`（F5 在同一文件新增测试）
- 事实：F5 在 `tests/test_loop_a_coverage.py` 新增测试会改变文件行号与 `git diff`，A-12 的判定方式"git diff 未改 443-1421 既有断言"需人工解释。
- 单选修法：A) 改为对 `git diff` 的机械断言（新增 hunk 不修改既有 test def 的断言行）；B) 显式声明既有断言以 test 名为锚而非行号。二选一。

**I-9（implementation）F5 遗漏 `TestMaterialGateLegacySkip`**
- 位置：`plan.md:204`（§5 F5）
- 事实：legacy skip 语义（`:1144-1149`）正是 F1 要保留的关键路径，但 F5 只列 3 个类，漏 `TestMaterialGateLegacySkip :989`。
- 单选修法：A) 在 F5 补 `TestMaterialGateLegacySkip :989`；B) 明示该文件全部 `TestMaterial*` 类均纳入回归（不逐类列举）。二选一。

**I-10（implementation）`state-schema` 的"唯一 material 块"措辞与链语义张力**
- 位置：`plan.md:310`（§12.1 替换后仍保留）、`:143-144`（§3.5 "all material blocks"）
- 事实：`state-schema.md:103` 描述 locator 指向"唯一"material 块；链式机制要求 attempts.md 中存在多块并全部参与判定。虽可按"locator 以 id 唯一寻址"解释，但字面易误读。
- 单选修法：A) 在 §12.1 新 bullet 补一句"material 块可多枚；locator 以 `id=` 唯一定位，链判定读取全部块"；B) 修改 :103 措辞为"指向 attempts.md 内由 locator 唯一寻址的 material 块"。二选一。

**I-11（implementation）链回溯未定义 reopen/多 revision 边界**
- 位置：`plan.md:144`（§3.5 `blocks = all material blocks`）
- 事实：reopen 后 attempts.md 追加新 revision 的块；全量解析会把旧 revision 的块并入链，`i`（最近 decisional）可能落在旧 revision。
- 单选修法：A) 规定仅取当前 `_detect_revision_id` 对应的 material 块（按其 `id` 前缀或 `revision_id` 过滤）；B) 显式声明跨 revision 全链为预期并给出理由。二选一。

**I-12（implementation）D2 未覆盖"一致 `阻断需修复` 且仅 implementation/structural"分支**
- 位置：`plan.md:187-192`（§4）
- 事实：规则 1（一致否定）、规则 2（多数支持+少数 conceptual/architectural）、规则 3（可执行）。三者之间的"一致阻断但无 conceptual/architectural"落入规则空档。
- 单选修法：A) 补第 5 条"一致 implementation/structural 阻断 → 标准修复循环 + 修订后按 §4 重新分流"；B) 声明该情形按标准 converge 默认流程处理，不在本协议额外规定。二选一。

**I-13（implementation）§2.1 的 :53 引证支撑不足**
- 位置：`plan.md:52`（§2.1 重认证轮序行）
- 事实：`retrospective.md:53` 实为 "outer R1-R5 verdict/阻断数" 表，仅备注"R2 起进入材料重认证循环"；未见"blind 1-4 中多次同字节复核（材料对 #1/#2）"。材料对相关表述在 `:62`（"终局材料对为 R5+blind 终局"）与 `:80`（"7 次重认证"）。
- 单选修法：A) 改引 `:62`/`:80` 或删除"材料对 #1/#2"细节；B) 保留并补可核出处。二选一。

**I-14（suggestion，DR6）宿主环境路径写入治理计划**
- 位置：`plan.md:192`（§4 引 `~/.config/opencode/memories.md`）、`:267`（§9）
- 事实：以本机 OpenCode 记忆文件作为用户裁决权威源，跨环境不可复现。
- 单选修法：A) 改为引用仓库内留痕（如 `GOVERNANCE-DECISIONS.md` 的等价条目）；B) 保留但标注为"宿主环境外部权威源，非本仓库可验证"。二选一。

**I-15（suggestion）§1 "三重机械校验"措辞过强**
- 位置：`plan.md:40`（§1 成功判据）
- 事实：hash 链与块绑定是机械的；`delta.declared_class` 是声明回显、verdict 是判断，二者非机械校验。§11:297 已诚实声明残余，两处措辞不一致。
- 单选修法：A) 改为"hash 链 + 声明回显 + verdict 门控"；B) 明确列出哪一环是机械、哪一环是语义，与 §11 对齐。二选一。

**I-16（suggestion）§3.5 伪码死分支**
- 位置：`plan.md:154`（`if blocks[j].change_class == decisional: continue`）
- 事实：`i` 取 max decisional 索引后，所有 `j>i` 必非 decisional，该 `continue` 不可达。
- 单选修法：A) 删除该行；B) 若意图保留"未来多 decisional 段"扩展，补注释说明其当前不可达。二选一。

---

## 四、对抗面复核（§11 清单封死性）

| 攻击 | 是否封死 | 结论 |
|---|---|---|
| 谎报 `non-decisional` + 如实声明触达 decisional 章节（A-11-1/A-11-4） | 是（条件成立时） | reviewer verdict 门 + 交集 fail-safe；但**依赖作者如实声明 `changed_sections`**（R-1 已承认） |
| 谎报 `non-decisional` + **漏报** `changed_sections` | **否（残余）** | 机械层失效，仅剩单 delta reviewer 语义判断；计划如实声明不声称闭环 |
| 伪造 `base_plan_sha256`（A-11-2） | 是 | 与 `blocks[j-1].candidate_artifact.sha256` 比对，攻击者无法伪造前块 |
| 链中删块（A-11-3） | 是 | 环断裂（base 无对应前块）→ fail |
| payload/output 回显不一致（A-11-6） | 是 | byte-equal |
| verdict 造假（进阶：`需重新设计`） | **否** | I-3：现行负向检查只拒 `阻断需修复`，`需重新设计` 会放行 |
| 空 `changed_sections` | **否** | I-5：无非空校验，交集恒 ∅ 放行 |
| 伪造 delta `artifact` 字段 | **否** | I-4：delta 分支未做 artifact/material_revision 块绑定 |

结论：§11 未封死——"漏报声明"（已承认残余）、"verdict=需重新设计"（I-3）、"空 changed_sections"（I-5）、"artifact 伪造"（I-4）。其中 I-3/I-4/I-5 是可机械封死却未封的，属计划缺陷而非固有残余。

---

## 五、规范句修改复核（§12）

- §12.1/:103、§12.2/:104、§12.3/:23、§12.4/:32、§12.5/:462 的"原文"逐字与实开文件一致（已核对）。
- §12.2 替换**未削弱**原 fail-closed 强度：decisional 规则原样保留，non-decisional 明确"任何一环缺失即 fail closed，不得降级"。
- §12.5 替换把指针句从"两-authority 同字节规则"改为"分级复核规则"，方向正确且保强度。
- 问题：§12.3/§12.4 为追加式（原句保留），与 A-13 统一"旧句消失"矛盾（I-6）。§12.1 保留"唯一 material 块"措辞（I-10）。

---

## 六、机器块与治理要件

- **preflight 实跑真实**：本 reviewer 独立复跑
  `python scripts/budget_gate.py preflight --plan .converge/active/20260912-o6-material-delta-recert/plan.md`
  输出与 `attempts.md:58-60` 一致：`WARN:code_heavy:2,72` + `PREFLIGHT_OK:governance-change`，EXIT=0。真实。
- **calibration 一致**：attempts.md 内 fence `id=calibration`；canonical sha256 `16ec2455…` 实算吻合；`evidence/calibration-report.json` 与 canonical fence **逐字节相同**（raw==canonical True）；`corpus_digest=3627eb4d…`、`freshness` 三键吻合。
- **user_message_events 跨对象引用**：现行校验（`budget_gate.py:1668-1679`）仅做 UUID 格式检查，不检查"本对象事件流内存在"。B 对象两个事件文件实存（`00000049-989e5ebd…json`、`00000010-06754e6f…json`）。计划 §14/attempts.md 已如实披露"本对象事件流内暂无对应事件"及后补路径，**披露充分、不伪造**。
- **governance schema / archaeology_refs**：`git:da81e70…`=当前 HEAD，`git cat-file -e` 由 preflight 校验通过；`archive:done/20260911-op-envelope-b-contract-correction` 实存。

---

## 七、D1 方向是否成立

**成立：是。**

理由：以 B 对象实测成本（`retrospective.md:75/:80`：41KB→133KB、每轮字节变更全量双认证、7 次重认证≈半数评议成本）为动机，把 material 修订二分并只对 `non-decisional` 段降为单 fresh delta reviewer，同时用块链 hash 回溯 + 交集 fail-safe + verdict 门控约束，方向对症、成本收益明确；该改动属防呆型机制（`CONSTITUTION.md:32` Bitter Lesson 精确边界），非补丁。缺陷集中在**规范精度**（通配符语义、anchor 作用域、verdict 判定、payload 绑定、非空校验、验收判据），均可通过修订计划消解，不动摇 D1 方向，故**不需要重新设计**。

但须强调：§1 "三重机械校验替代第二权威"的表述与 §11 的诚实声明存在张力（I-15）。D1 的真实强度是"机械层封死**如实声明**下的违规 + 语义层由单一 reviewer 兜底"，不是"机械封死语义分类正确性"。计划应把这一定位写准，避免下游对机制安全性产生过度信任。

---

## 八、无法核实的断言清单

1. `plan.md:52` "R1-R5 + blind 1-4 中多次同字节复核（材料对 #1/#2）"——`:53` 无此内容；"材料对 #1/#2"的具体枚举无法从 B 归档核实（仅能核到终局材料对与 7 次重认证总量）。
2. `plan.md:181` "现有 7 个 material 测试"——与实核（≈17 个直接定义）不符（见 I-7）。
3. §3.5 改造后 `_validate_material_gate` 的实际行为（链回溯、full-pair 泛化、error code 集合）——代码未落地，无法运行核实；本审仅核规范可判定性与代码事实边界。
4. OCSR 派发层是否会在 `--evidence-mode exact` 下正确采集 delta reviewer 的 prompt/output blob——需实现后验证。
5. D2 三种分流结果的实际触发概率——属评议后事实，当前不可核实。
