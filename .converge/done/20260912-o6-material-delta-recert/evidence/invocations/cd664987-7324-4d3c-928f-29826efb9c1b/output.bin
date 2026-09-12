---
round: 1
reviewer_backend: ocsr-adapter
reviewer_instance_id: 20260912_164555_b88bdf
generated_at: 2026-09-12T16:58:00+08:00
verdict: 阻断需修复
---
阻断需修复

# uv-init-1 · ultraverge 初审（独立 Reviewer）

对象：`.converge/active/20260912-o6-material-delta-recert/plan.md`（candidate-1，30,961 B）
基线：HEAD `da81e70cee7931d49680866f9cd0b2cdb6fadc5a`（与计划 §2 声明一致）。本报告实开核对了计划全部 `文件:行` 断言、`scripts/orchest.py` 材料门现状、`scripts/budget_gate.py` 治理 preflight 现状、`tests/test_loop_a_coverage.py` 全部 `TestMaterial*` 类、B 对象归档证据；只读，未修改任何仓库文件（本报告除外）。

存在 7 条阻断（1 conceptual + 3 architectural + 3 structural，其中 B7 为事实性）。核心：**D1 的分级 + 单 delta reviewer 路径方向成立，但计划宣称的三重机械闭环在多处结构性失效**——交集 fail-safe 因词表互斥而恒为空（B1）、`decisional_anchors=["*"]` 哨兵不产生声明的保守回退（B2）、full-pair 泛化的比较目标未定死（B3）、delta 候选未锚定到本块（B4）；规范句与 File Matrix 遗漏标题/词汇表（B5）；D2 record-only 分支无验收与序列（B6）；"7 个 material 测试"计数失真（B7）。

---

## 零、事实核验（实开）

| 断言 | 实核结果 |
|---|---|
| `plan.md` ≤ 45KB（A-1） | ✅ 30,961 B ≤ 46,080 |
| frontmatter `status/review_mode/object_slug`（A-2） | ✅ 头 5 行逐字一致 |
| preflight 实跑（A-3） | ✅ 复跑得 `WARN:code_heavy:2,72` + `PREFLIGHT_OK:governance-change`，EXIT=0，与 attempts.md:58-60 一致 |
| 恰一个 governance fence（A-4） | ✅ ```json fence 计数=1（`converge.governance-change/v1` 字符串出现 5 次于 prose/fence，fence 唯一） |
| calibration canonical sha/digest/freshness（§2.4） | ✅ 复算 `16ec2455…`、`3627eb4d…`、corpus 20 条全 `unavailable/no_sample`、`eligible_samples=0`，三者与 plan/attempts 一致 |
| `orchest.py` 行号 :1095/:1116-1117/:1133/:1171-1175/:1185-1186/:1207-1259/:1267-1272/:1273-1279/:1303-1310/:1335-1337/:1340-1361/:1579-1581 | ✅ 全部实开命中 |
| `budget_gate.py` :1452-1459/:1668-1679/:1682-1699/:1710-1742 | ✅ 全部实开命中 |
| `refs/state-schema.md:101-104/:76`、`refs/orchestrator-guide.md:17-32`、`SKILL.md:462`、`CONSTITUTION.md:71-72` | ✅ 全部实开命中 |
| B 成本 `retrospective.md:42/:53/:75/:80` | ✅ 引用原句存在 |
| 现有 material 测试数（§3.7） | ❌ 计划称"7 个"，实测 **17 个**（4 个 `TestMaterial*` 类；见 B7） |
| 基线测试（A-12/A-16 可行性） | ✅ `pytest tests/test_loop_a_coverage.py tests/test_process_controller_contract.py -q` = 60 passed |

---

## 一、前置自检 5 问

1. **产物身份自洽**：**部分通过**。产物自述"O6 重评 +（评议支持时）机制实现"，§1 Goal / §3 设计 / §14 机器块三者指向同一问题；但 §11 把 A-11-4 称为"**机械**拦截"，而实际拦截点是两份**作者自声明**集合的交集（且词表互斥使其恒空）——"声称机械、实为语义"，见 B1。
2. **产物边界诚实**：**不通过（blocking）**。§1 成功判据、§3.6、§11 声称"hash 链 + delta payload + verdict 三重机械校验""任何一环缺失一律 FAIL_CLOSED""§11 全部被拦"，但交集机制恒空（B1）、`["*"]` 保守回退不成立（B2）——边界被夸大。
3. **产物数据纯度**：**通过**。无业务数据；新增值为机制常量与受控词表；calibration 报告为真实生成物（已复算哈希）。
4. **职责边界自洽**：**不通过（issue）**。材料门机械检查的两侧输入（`changed_sections`、`decisional_anchors`）均由作者/agent 声明，"diff 是否真触及 decisional"的语义判断实际全部落在 delta reviewer；计划却把 A-11-4 的兜底归给机械交集（B1）。另 delta 与 full-pair 同用 `outer-reviewer` 角色，仅靠 payload 是否含 `delta` 区分，边界偏弱（B3/B4）。
5. **命名一致性**：**不通过（issue）**。同一"分级"概念在块内叫 `change_class`、在 payload 内叫 `declared_class`（N1）；规则改名（SKILL.md:462→"分级复核规则"）后，`state-schema.md:101` 标题"两次同字节审查"与 `orchestrator-guide.md:17` 标题"同字节两-authority 审查"未同步（B5）。

---

## 二、DR 7 维逐维结论

| 维度 | 结论 | 依据 |
|---|---|---|
| DR1 一致性 | **issue（阻断）** | 交集 fail-safe 与 §3.2 词表互斥自相矛盾（B1）；`["*"]` 缺省语义与 §3.5 集合运算矛盾（B2）；`change_class`/`declared_class` 命名漂移（N1）；两处标题未随规则改名同步（B5）。 |
| DR2 完整性 | **issue（阻断）** | full-pair 泛化比较目标未定（B3）；delta 候选未锚定 blocks[j]（B4）；guide 替换文本缺受控词表而 state-schema 指针指向它（B5）；D2 record-only 分支无验收/序列（B6）；伞形计划 O6 状态未入 File Matrix（N3）；reopen 跨 revision 链边界未定义（N4）。 |
| DR3 可维护性 | **issue** | `["*"]` 哨兵 + 词表互斥是"陷阱"：维护者按字面实现必得错误语义（B2）；伪代码含死分支（N2）；受控词表将散落 plan/state-schema/guide 三处，未单源（B5）。 |
| DR4 职责边界 | **issue** | 见前置自检 Q4：机械/语义边界倒置（B1）；delta 与 full 同角色靠 payload 区分（B3/B4）。 |
| DR5 残留与冗余 | **issue（轻）** | 旧语义标题残留（B5）；`scripts/README.md:151` "两份 authority prompt 与两份 Reviewer 输出"未在 §12 逐字覆盖（B5）；"7 个 material 测试"陈旧错误计数（B7）。 |
| DR6 可移植性 | **clean** | 未引入环境特定路径/用户名/OS 依赖；哈希链为平台无关机制。唯一约束（历史 exact blob 需长期保留）属运维/留存边界，非可移植性缺陷。 |
| DR7 可扩展性 | **concern** | 每次 finish 需回溯整链并重验"最近 decisional 全量对"，链长线性增长、且要求历史 exact 证据永久可寻址；"全 non-decisional 链"这一特例边界只在 §3.5 一行回退，未在设计中显式承认其不可达性（N4）。 |

---

## 三、逐条 issue

### 阻断

**B1｜交集 fail-safe 结构性恒空，A-10/A-11-4 的"机械拦截"不成立**
- severity: `architectural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:119-123`（§3.2 词表与归类权责）、`:162`（§3.5 伪代码 `changed_sections ∩ decisional_anchors == ∅`）、`:169`、`:241`（A-10）、`:291`（A-11-4）
- 事实：§3.2 规定 `non-decisional` 的 `changed_sections` **只允许后 4 项** `{doc-refs, wording, appendix, tests-non-assertive}`，而 `decisional_anchors` 承载"decision 内容所在章节"（前 8 项）。两集合词表**互斥** ⇒ 交集恒为 `∅` ⇒ A-11-4（"decisional 误标 non-decisional 且 changed_sections 含 decisional 章节"）**永远不可能**触发交集非空；它实际只会（如果实现）落入"non-decisional 声明了非法词表项"的 schema 违规，而计划并未定义该 schema 检查。此外两侧输入均为作者自声明，交集不依赖 diff 实证，无法构成所宣称的机械闭环。
- 单选修法：把 `changed_sections` 与 `decisional_anchors` 统一到**同一 12 项词表**，门禁改为硬检查 `non-decisional ⇒ changed_sections ∩ UNION(所有 prior decisional 块的 decisional_anchors) == ∅`（用并集，不用仅最近一块）；并同步改写 §3.2/§3.5/A-10/A-11-4 的"只允许后 4 项""最近 decisional 块"措辞。若坚持后 4 项限制，则必须把 A-11-4 的拦截改述为"schema 违规"并撤回"交集机械拦截"的声明。

**B2｜`decisional_anchors = ["*"]` 哨兵不产生声明的保守回退**
- severity: `architectural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:104-106`（§3.1）、`:148`/`:162`（§3.5）
- 事实：§3.1 声明旧 decisional 块缺省 `decisional_anchors = ["*"]`（"全锚定，任何 non-decisional 变更都会触发交集非空 → 保守 fail-closed 到全量对"）。但 §3.5 的交集是**集合交**：`{"wording"} ∩ {"*"} == ∅`。`"*"` 既不是合法章节标识（不在 §3.2 词表内），也无任意通配语义；计划未定义对哨兵的特判。故旧块后继的 non-decisional 块会**照常走 delta 并放行**，与"保守 fail-closed"声明相反。
- 单选修法：删除 `["*"]` 字面量，改为显式缺省语义并落进伪代码：`if blocks[i].decisional_anchors is missing/None: FAIL_CLOSED:material-gate:legacy-anchor-requires-full-pair`（旧 decisional 块的后继一律要求 full-pair，不允许 delta）；同步 §3.1/§12.1 的字段描述。

**B3｜full-pair 泛化的"比较目标"未定死，历史 decisional 块可能永远无法 qualify**
- severity: `architectural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:152`、`:167`（§3.5）；对照现状 `orchest.py:1267-1272`
- 事实：现行候选资格是"`payload.artifact.sha256` == **盘上** plan 且 `material_revision.sha256` == 当前块 hash"（`orchest.py:1267-1274`）。当链尾存在 non-decisional 块时，锚点块 `blocks[i].candidate_artifact` **不等于**盘上 plan。计划只说"泛化为对指定 target 块"，未规定 artifact 比较应从"盘上 plan"改为"target 块 `candidate_artifact`"。若执行者只泛化 `material_revision` 比较，历史 full-pair 会因 artifact≠盘上 plan 被永久 skip → 材料门误 FAIL_CLOSED（机制不可用）。另 §3.3 要求 decisional full-pair payload "不含 delta"，但 §3.5 未把"full-pair 候选不得含 delta"写成硬检查。
- 单选修法：在 §3.5 明确写出 helper 契约：候选对 target 块 `T` qualify 当且仅当 `payload.artifact == T.candidate_artifact` ∧ `payload.material_revision.sha256 == canon(T)` ∧ locator id == `T.id`；并要求 full-pair 候选 `"delta" not in payload`（违反即 FAIL_CLOSED）。补一条 A-6 子用例覆盖 artifact==历史 candidate。

**B4｜delta 候选未把 review-target payload 锚定到 `blocks[j]`，权威集非唯一确定**
- severity: `architectural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:153-161`（§3.5 delta require 列表）
- 事实：delta 列表只校验 `delta.declared_class/base_plan_sha256/current_plan_sha256` 三角与 echo。**未**校验 `payload.material_revision{locator,sha256}` == `blocks[j]` 的 canonical hash / id，也**未**校验 `payload.artifact == blocks[j].candidate_artifact`。因此一个 payload 可以让 `material_revision` 指向另一块、`artifact` 指向另一份字节，而仅让 `delta.*` 自洽——"块链 + base/current hash 链唯一确定权威集"不成立；同时 §11 无对应用例（A-11-2/5/6 都不覆盖）。
- 单选修法：delta require 列表补三条硬检查——`payload.artifact == blocks[j].candidate_artifact`、`payload.material_revision.sha256 == canon(blocks[j])`、locator id == `blocks[j].id`；并加对抗用例 A-11-9（delta payload 的 material_revision 指向他块 → FailClosed）。

**B5｜规范句/File Matrix 枚举不完整：标题与受控词表遗漏，`README:151` 未逐字覆盖**
- severity: `structural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:201-203`（F2 `:101-104`、F3 `:17-32`、F7 `:144-151`）、`:305-335`（§12 仅给 :103/:23/:32）
- 事实：(a) `refs/state-schema.md:101` 标题"material revision 后**两次**同字节审查的 payload"与 `refs/orchestrator-guide.md:17` 标题"Material revision 与**同字节两-authority** 审查"在引入单 delta 路径后失真，§12 未改写，A-13 也无法 grep 到；(b) §12.1 新增 bullet 指向 guide §Material revision 作为"判定标准与受控词表"单一来源，但 §12.3 的 guide 替换文本**没有出现 12 项受控词表**——指针悬空；(c) `scripts/README.md:151`（"两份 authority prompt 和两份 Reviewer 输出均须 exact"）在新语义下失真，F7 虽覆盖 `:144-151` 但 §12 无逐字对照，A-13 不校验它。
- 单选修法：§12 补三条逐字项——改写 state-schema:101 标题、改写 guide:17 标题、在 guide 替换文本中加入完整 12 项受控词表；把 `README:151` 的替换句纳入 §12（或明确 A-13 覆盖 F7）；相应把 A-13 的 grep 清单扩到这些句。

**B6｜D2 record-only 分支无验收、无 Bounded Sequence，§7 未声明适用条件**
- severity: `structural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:187-192`（§4）、`:212-249`（§6/§7）、`:266-268`（§9）
- 事实：§4.1 规定三名初审"一致否定→record-only，不修改 `orchest.py`/`state-schema`/`guide`"。但 §7 的 A-5…A-17（改代码、跑新测试、`git status` 覆盖 F1-F7）与 §6 的 P1-P6 都只在 implement 分支成立；record-only 时 A-14/A-16 等**逻辑上不可能通过**，而 §7 未声明"仅 implement 分支适用"。§4.1 也未给出 record-only 的机械判定（"conceptual/architectural 阻断指向 D1 方向"是语义判断）与产物收口序列。
- 单选修法：§7 抬头显式声明"本表仅适用于 §4.3 implement 分支"；新增 record-only 验收集（伞形计划 O6 状态 + retrospective 记录重评结论与理由）与 record-only 最小序列；§4.1 把"一致否定"的机械判据限定为"3/3 verdict ∈ {阻断需修复, 需重新设计} 且无任何 verdict=可执行"，把"指向 D1"降为 orchestrator 语义备注而非判定条件。

**B7｜`§3.7` 的"现有 7 个 material 测试"与实测不符（17 个）**
- severity: `implementation`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:181`
- 事实：`tests/test_loop_a_coverage.py` 中 `TestMaterialClosureGate`(6) + `TestMaterialLocatorResolution`(4) + `TestMaterialGateLegacySkip`(3) + `TestMaterialGateQualifyByCurrentBlock`(4) = **17 个唯一 material 测试方法**（AST 计数）。"7 个"为事实失真。
- 单选修法：改为"17 个（4 个 `TestMaterial*` 类；起于 :443）"，或直接以类名引用、删除数字；A-12 同步改为按类/断言内容判定，而非固定行号区间。

### 非阻断

**N1｜`change_class` 与 `declared_class` 同义异名（Q5/DR1）**
- severity: `implementation`；位置：`plan.md:102`（块字段）vs `:132/:135`（payload 字段）。
- 单选修法：payload 字段统一命名为 `change_class`，消除一词多义。

**N2｜伪代码死分支（DR3）**
- severity: `implementation`；位置：`plan.md:148/:154`。
- 事实：`i = max index with change_class == decisional` 之后，`for j in (i+1..): if blocks[j].change_class == decisional: continue` 恒不成立。
- 单选修法：删除该 `continue`，或用 `while` 明确定义"最近 decisional 之后的所有块必为 non-decisional"的前提断言。

**N3｜伞形计划 O6 状态未入 File Matrix（DR2/DR5）**
- severity: `structural`；位置：`plan.md:196-208`（§5）。
- 事实：`docs/plans/active/20260911-converge-operational-envelope.md:25/:36` 仍称"O6 … 候选后续（独立小对象）"。implement 或 record-only 任一收口都需更新其 O6 状态。
- 单选修法：新增 F8：改写伞形计划 O6 行与"终态"段，记录重评结论。

**N4｜reopen 跨 revision 的链边界未定义（DR2/DR7）**
- severity: `implementation`；位置：`plan.md:141`（"全部 material blocks（文档顺序）"）。
- 事实：`attempts.md` 在 reopen 后含上一 revision 的 material 块；"全部块"会让新 revision 首块的 `base_plan_sha256` 去比对上一 revision 的 candidate，语义未定义。现状 `_find_material_block(active)` 不按 revision 过滤，但新链逻辑应显式处理。
- 单选修法：链构造按 `_detect_revision_id` 过滤，或显式规定"首个块 base=null 且 `change_class` 必须为 decisional"。

**N5｜§A-12 的行号区间锚定不稳（机械可判定性）**
- severity: `implementation`；位置：`plan.md:243`。
- 事实：`git diff 未改 :443-1421` 在 F5 于文件中部插入新类时会因行号漂移而不可机械判定。
- 单选修法：A-12 改为"现有 4 个 `TestMaterial*` 类的测试体无删除/修改"（按 diff hunks 判定），并要求 F5 新测试仅追加在文件末尾。

---

## 四、D1 方向是否成立

**成立（是）。** 理由：
1. `change_class` 对 material 修订做 decisional / non-decisional 二分，并对 decisional 保留现行"两 fresh 同字节全量对"不放宽（§3.3、§8.1）——这条底线正确，消除了"为省成本而普遍降级"的风险。
2. 对 non-decisional 引入"单 fresh delta reviewer + 上一有效字节 base hash + 本块 current hash + verdict 非阻断"的方向合理，且与既有 `_validate_material_gate` 的 exact 证据/角色授权基础设施（`REVIEWER_AUTHORITIES["fresh"]` 含 `outer-reviewer`）兼容，落地成本可控。
3. 计划如实声明了语义残余 R-1（作者漏报 `changed_sections` 时机械交集抓不到），没有伪造机械闭环的意图。

判为 **阻断需修复** 而非 **需重新设计**：问题集中在"机械不变量的实现规范"（B1-B4 的比较目标/锚定/词表/哨兵语义）与"文档枚举/条件分支完整性"（B5-B6），均可通过改写 §3.1/§3.2/§3.5/§12 与补验收条目修复，不需要推翻 delta 方向本身；B7 为事实性计数修正。

---

## 五、无法核实的断言清单

1. §3.5 全部门禁新行为（链回溯、`blocks[i]` full-pair、delta 候选、交集、错误码）与 A-5…A-11、A-15 均为**待实现**设计，当前无法运行验证；其正确性只能由本报告的静态推理判断。
2. B 对象"7 次重认证 ≈ 全部评议成本的一半"（`retrospective.md:80`）为该对象自报估算；我只核对了引用行文本存在，未核对其底层派发记账。
3. "calibration 独立文件不被 preflight 机械校验"仅由 allowlist 结构（`refs/state-schema.md:76`、`budget_gate.py:1452-1459` 排除 `evidence/`）与实跑通过佐证；未独立复算 B 对象"同构"做法的 fence 字节。
4. D2 的未来三名初审 verdict 分布、"conceptual/architectural 阻断是否指向 D1"属未来且语义，无法机械核实。
5. `ultraverge_min_reviewers=3`、本对象 `task_tier=critical(20/30)` 由 `_budget-state.json` 与 `gate-ledger.jsonl`（reserved ultraverge-initial + ceilings ultraverge=3）佐证；实际 spawn 数待本批完成后才能核实。
6. preflight 的 `WARN:code_heavy:2,72` 判定阈值（block≥3 或 loc≥40）来自 attempts.md 说明，未逐一实开该启发式源码复核。
