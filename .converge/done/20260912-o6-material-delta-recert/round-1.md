---
round: 1
reviewer_backend: opencode
reviewer_instance_id: 20260912_170634_87c9da
generated_at: 2026-09-12T09:11:06.059660+00:00
verdict: 阻断需修复
---
阻断需修复

---
round: 1
role: outer-reviewer
review_mode: ultraverge
reviewer_backend: opencode
generated_at: 2026-09-12
verdict: 阻断需修复
---

# round-1 · O6 material 增量复核（candidate-2）· ultraverge 完整收敛 outer R1

> Reviewer：outer 权威（fresh、独立上下文；未读同批 blind 报告）。
> 受审对象：`.converge/active/20260912-o6-material-delta-recert/plan.md`（candidate-2，**42114 B**）。
> 基线：HEAD `da81e70cee7931d49680866f9cd0b2cdb6fadc5a`。
> 实核方式：逐行实开 `plan.md`、`CONSTITUTION.md`、`SKILL.md`、`refs/state-schema.md`、`refs/orchestrator-guide.md`、`refs/design-review-prompt.md`、`scripts/orchest.py`、`scripts/archive_contract/model.py`、`scripts/budget_gate.py`、`tests/test_loop_a_coverage.py`、`tests/test_process_controller_contract.py`、`.converge/done/20260910-process-controller-consolidation/attempts.md`、B 归档证据；preflight 实跑；calibration 实算。只读（本报告除外）。

---

## 零、事实核验（实开/实跑）

| # | 断言 | 实核结果 |
|---|---|---|
| F1 | candidate-2 `plan.md` ≤ 45KB（A-1） | ✅ 实测 **42114 B** ≤ 46080 |
| F2 | frontmatter `status/review_mode/object_slug`（A-2） | ✅ 头 3 行逐字一致 |
| F3 | preflight 实跑（A-3） | ✅ 复跑 `python scripts/budget_gate.py preflight --plan …` → `WARN:code_heavy:2,91` + `PREFLIGHT_OK:governance-change`，EXIT=0，与 `attempts.md:90-92` 一致（真实） |
| F4 | 恰一个 governance fence（A-4） | ✅ fenced-json 块总数 1、含该 schema 者 1；字符串 `converge.governance-change/v1` 出现 **5** 次（散文/§2/§14），故必须用解析器计数——A-4 口径正确 |
| F5 | calibration（§2.4/§14） | ✅ fence `id=calibration`；canonical sha256 复算 `16ec2455…`；`corpus_digest=3627eb4d…`；`freshness` 三键吻合；fence canonical 字节与 `evidence/calibration-report.json` **逐字节相同** |
| F6 | `user_message_events` 跨对象接受性 | ✅ `budget_gate.py:1677-1679` 仅 UUID 格式校验；B 对象两事件文件实存——计划 §14 披露属实 |
| F7 | `REVIEWER_AUTHORITIES` | ✅ `model.py:91-94`：fresh 含 `outer-reviewer`，blank-slate 含 `blind-reviewer` |
| F8 | `orchest.py` 材料门全部锚点 | ✅ `:1095-1118`/`:1133-1361`/`:1144-1149`/`:1171-1175`/`:1185-1186`/`:1204-1205`/`:1207-1259`/`:1215-1218`/`:1235-1238`/`:1267-1272`/`:1273-1293`/`:1303-1310`/`:1335-1337`/`:1340-1361`/`:1579-1581` 全部命中；`:1344-1345` 现仅拒字面量 `阻断需修复`（计划陈述属实） |
| F9 | 现有 material 测试计数（§2.5） | ✅ 4 个 `TestMaterial*` 类、直接定义 **17** 个 test：ClosureGate(351)：443/452/464/483/531/572；LocatorResolution(848)：908/918/956/975；LegacySkip(989)：1075/1087/1117；QualifyByCurrentBlock(1184)：1292/1304/1372/1421。candidate-2 修正为 17 属实 |
| F10 | 现有/历史 material 块字段 | ❗**关键**：`tests` 的 `_make_material_block`（`test_loop_a_coverage.py:336-348`）与真实归档块（`.converge/done/20260910-process-controller-consolidation/attempts.md`）**均无** `change_class` / `changed_sections` / `decisional_anchors`；真实块用 `candidate_plan`（非 `candidate_artifact`），首块无 `id` |
| F11 | §12 五处"原文" | ✅ `state-schema.md:101/103/104`、`orchestrator-guide.md:17/23/32`、`SKILL.md:462`、`scripts/README.md:151` 逐字吻合 |
| F12 | B 成本证据 | ✅ `retrospective.md:42/53/62/75/80` 引文逐字存在（`:53` 标注为轮序表已正确） |
| F13 | `budget_gate.py` 机器块校验 | ✅ `:1467/1594` mechanism 未强制 `comparison=null`（计划 §14:428 更正属实）；`:1682-1699` calibration 校验；`:1710-1742` 窄门仅裁决 numeric kind |

结论：candidate-2 对 UV 已确认的**事实性错误**（17 条计数、`:1204-1205` 语义、comparison 措辞、`:53` 引证）**全部修正属实**，机器块/preflight 真实。但**新增/保留的伪代码级缺陷**使若干机械声称不成立（见第三部分）。

---

## 一、前置自检 5 问

| # | 问题 | 结论 | 依据 |
|---|---|---|---|
| Q1 | 产物身份自洽 | **基本通过** | "O6 重评 + 条件实现"贯穿 §1/§4/§6；但 §3.2 与 §3.5 对"non-decisional 章节域"自相矛盾（BLK-1），身份内部一致性打折 |
| Q2 | 产物边界诚实 | **不通过（blocking）** | §1 已按 UV2-I-15 改为"hash 链（机械）+ payload 回显（机械）+ verdict 门控（判断）"，态度正确；但 §3.5 对 **legacy 链**的处理与 A-5/A-12/§3.7 冲突（BLK-2/3），且 §3.2 的"后 4 项"若落实会令 A-10/A-11-4 的"机械拦截"恒空（BLK-1）——边界的机械部分**实际不成立** |
| Q3 | 产物数据纯度 | **通过** | 无业务数据；calibration 为真实生成物（已复算）；机器块 schema 通过 |
| Q4 | 职责边界自洽 | **不通过（issue）** | "谁证明未触及 decisional"= 单一 delta reviewer 的语义 diff，计划已如实降级（R-2）；但 §3.2 又把该职责的一环归给"并集交集机械拦截"，而该交集在 §3.2 的域约束下达不到（BLK-1） |
| Q5 | 命名一致性 | **基本通过** | `change_class`/`declared_class` 已统一为 `change_class`（N1 修复）；12 项词表在 §3.2 与 §12.4 **逐字一致**；但 `candidate_artifact` vs 现实的 `candidate_plan` 在伪代码中未统一（BLK-4） |

---

## 二、DR 7 维逐维结论

| 维度 | 结论 | 依据 |
|---|---|---|
| DR1 一致性 | **concerns_found（阻断）** | §3.2 "non-decisional 只允许后 4 项" vs §3.5 `changed_sections ⊆ VOCAB`(12 项) + A-10 并集交集（BLK-1）；§3.5 对 legacy 块强制 `changed_sections` vs §3.1/§3.7/A-5（BLK-2）；A-13 把 §12.3 归为"新增型" vs §12.3 标题"(replace 型)"（NB-1）；`candidate_artifact` vs `candidate_plan`（BLK-4） |
| DR2 完整性 | **concerns_found（阻断）** | legacy 单块场景无任何 full-pair 要求（BLK-3）；reopen 跨 revision 边界仅靠全局 blocks[0] 检查，未按 revision 分段（NB-3）；§3.5 伪代码未含 full-pair 的"正向 verdict / 禁含 delta"两点（NB-4）；F6 静态断言无常量名（NB-5） |
| DR3 可维护性 | **concerns_found** | `if not D` 死分支（NB-2）；"全 non-decisional 链保守回退"不可达却写进 §12.4；`["*"]` 已废除（良好） |
| DR4 职责边界 | **concerns_found** | 机械层只校验"声明间一致性"，语义 diff 由单一 reviewer 承担——计划已诚实声明，但 §3.2 的域约束与交集职责倒置（BLK-1） |
| DR5 残留与冗余 | **concerns_found（轻）** | `scripts/README.md:17` "两-authority 审查时必传 exact" 未随分级机制同步（F7/§12.7 仅覆盖 `:151`）（NB-6）；A-13 与 §12 标题的"三态"分类不一致 |
| DR6 可移植性 | **clean** | 无环境硬编码；宿主记忆路径已标注"外部权威源，非本仓库可验证"（I-14 修复） |
| DR7 可扩展性 | **concerns_found** | 链回溯 O(n) 可接受；但"全 non-decisional 链"特例被 §3.5:170 显式处理却在 §3.5:163 下不可达，设计边界仍未自洽 |

---

## 三、UV 三票处置抽查表（44 条抽样 15 条）

> 三票计数核对：uv1 = B1-B7(7)+N1-N5(5)=12；uv2 = I-1..I-16=16；uv3 = UV3-01..16=16；合计 **44**，与 `attempts.md:99` 一致。以下逐条回 `plan.md` 原文抽查：

| # | 原 issue | 处置落点（实核） | 抽查结论 |
|---|---|---|---|
| 1 | uv1-B1 交集恒空 | §3.2:124-128 统一词表 + §3.5:175/186 并集交集；A-10:282 | **部分有效**：并集方向正确，但 §3.2 "non-decisional 只允许后 4 项" 与并集语义仍冲突 → BLK-1，B1 未真正闭合 |
| 2 | uv1-B2/uv2-I-1/uv3-01 `["*"]` 哨兵 | §3.1:116 废除；§3.5:161-168 legacy→full-pair；A-11-12:345 | 哨兵已删、legacy 分支已建，但分支有 BLK-2/3 |
| 3 | uv1-B3 full-pair 比较目标 | §3.5:191 T 块三重锚定；禁含 delta；A-6:278 子用例 | **有效** |
| 4 | uv1-B4/uv2-I-4/uv3-09 delta 未锚定 | §3.5:177-184 三重锚定；A-11-13:346 | **有效** |
| 5 | uv1-B5/uv3-05/uv3-07 标题+词表+README | §12.0:359；§12.3:380；§12.4:390（含完整 12 项）；§12.7:410；A-13:285 | **基本有效**，但 A-13 对 §12.3 的分类错误（NB-1） |
| 6 | uv1-B6/uv3-06 record-only | §4.1:214；§6:254-263；§7 A-R1..A-R3:291-293 | **有效** |
| 7 | uv1-B7/uv2-I-7/uv3-08 "7→17" | §2.5:99-100 | **有效**（实核 17） |
| 8 | uv2-I-3/uv3-03 verdict 正向 | §3.4:141；§3.5:185；A-9:281 | **有效**（但伪代码未覆盖 full-pair verdict，NB-4） |
| 9 | uv2-I-5 非空校验/漏报 anchors | §3.5:158/162 域门；§10 R-1:321 双向漏报 | **有效**（受 BLK-1 影响） |
| 10 | uv2-I-6/uv3-07 A-13 三态 | A-13:285 | **部分有效**：三态引入正确，但与 §12 标题分类冲突（NB-1） |
| 11 | uv3-02 域校验 | §3.5:156-162；A-11-10/11:343-344 | **有效**，但域门顺序导致 legacy 块被误杀（BLK-2） |
| 12 | uv3-12 legacy 行号 | §2.2:73 改 `:1215-1218`/`:1235-1238`，`:1204-1205` 标 terminal | **有效**（实核） |
| 13 | uv3-13 comparison 措辞 | §14:428 | **有效**（`:1594` 允许非 null） |
| 14 | uv3-16 规范性句子=decisional | §3.2:122；§12.4:389 | **有效** |
| 15 | uv3-04 diff 无数据供给 | §3.4:142 诚实降级；§8.7:305；§10 R-2:322 | **有效**（如实声明，非机械闭环） |

**抽查结论**：处置表**逐条覆盖 44 条**，无遗漏、无编造；合并去重正确。但"已处置"≠"已修好"——BLK-1..4 是 **B1/B2/B3 修复面上的残余缺陷**，属实质性未闭合。

---

## 四、逐条 issue

### 阻断级

**BLK-1｜§3.2 的 non-decisional 章节域约束使"并集交集"机械拦截恒空/自相矛盾（uv1-B1 残余）**
- severity: `architectural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:124-128`（§3.2 词表与域约束）、`:169/:175/:186`（§3.5 并集交集）、`:282`（A-10）、`:337`（A-11-4）
- 事实：§3.2 写"归类为 decisional 的 `changed_sections` 必须落在前 8 项，**non-decisional 只允许后 4 项**"；而 `decisional_anchors` = "判定承载章节快照"（前 8 项）。若该域约束在门禁落实，则 `changed_sections`(后 4) ∩ `union_anchors`(前 8) **恒为 ∅**，A-10/A-11-4 宣称的"交集 fail-safe 机械拦截"永不触发——正是 uv1-B1 的原始病灶。§3.2 的括注"（本约束不是交集恒空的理由——词表已统一，交集按判定承载集合计算）"在逻辑上不成立：统一词表不改变两个**互斥子集**求交为空。反向地，§3.5 伪代码只校验 `changed_sections ⊆ VOCAB`（12 项，**未**落实"后 4 项"），因此门禁实际依赖交集——两者不可能同时为真：落实 §3.2 则 A-10 死；按 §3.5 实现则 §3.2 被违反。A-11-11 只测空/词表外值，无测试锁定"前 8/后 4"域。
- 单选修法（二选一，必须同步 §3.2/§3.5/A-10/A-11-4/§12.4）：
  - **A**：删除 §3.2 "non-decisional 只允许后 4 项"（改为"正确归类者仅触及后 4 项；门禁接受全部 12 项，误归类由并集交集机械拦截"），并在 §3.5 明写 `changed_sections ⊆ VOCAB`（12 项）为唯一域门；或
  - **B**：保留域约束，则删除"并集交集"拦截，把 A-10/A-11-4 改述为"non-decisional 的 `changed_sections` 含前 8 项 → `FAIL_CLOSED:non-decisional-touches-decisional-section`"，并把 §3.2 括注改为直述该域门。
  （无论 A/B，均需把 §3.2 那句错误括注删除或改正。）

**BLK-2｜§3.5 对 legacy 块强制 `changed_sections` 非空，导致旧块（含全部既有测试块）`FAIL_CLOSED:sections-vocab`，A-5/A-12/A-16 不可能成立**
- severity: `architectural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:158`（§3.5 `if b.changed_sections empty or not ⊆ VOCAB`）、`:116`（§3.1 "无 change_class 的旧块视为 decisional"）、`:204-206`（§3.7）、`:277`（A-5）、`:284`（A-12）、`:288`（A-16）
- 事实：§3.5 对**每个**块无条件要求 `changed_sections` 非空；而 `tests/test_loop_a_coverage.py:336-348` 的 `_make_material_block` 与真实归档块（`.converge/done/20260910-process-controller-consolidation/attempts.md`）**均无**该字段（也无 `change_class`/`decisional_anchors`）。因此 17 条既有测试的块与任何 reopened 旧对象都会在 `sections-vocab` 失败——`test_two_distinct_same_hash_reviewers_pass` 等正例将失败，A-12"pytest 全绿"/A-16 无法达成。这与 §3.1"旧块视为 decisional（保守）"、§3.7"旧块无 change_class → decisional"、A-5"旧块（无字段）走 full-pair"直接矛盾。legacy 分支（`:164`）因该检查在前而永不可达。
- 单选修法：把"新块字段必填"写成**显式前置判定**——`if "change_class" not in b: legacy = min(legacy, index(b)); continue`（完全旧块不经 `changed_sections` 域门）；仅对带 `change_class` 的块校验 `changed_sections` 非空⊆VOCAB；再进入 anchors/legacy 判定。同步 A-5 措辞明确"旧块（缺全部三字段）→ full-pair"。

**BLK-3｜legacy 分支从 `legacy+1` 起算，单 legacy 块（当前块）无需任何 fresh+blank 对 → fail-open 回归，既有负例测试反转**
- severity: `architectural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:164-168`（§3.5 `for j in (legacy+1 .. len-1)`）；对照现状 `orchest.py:1303-1310`（要求 fresh+blank 对）
- 事实：设链 = `[legacy]`（既有测试与多数旧对象的形态，单块）。`legacy=0`，循环区间 `(1..0)` 为空 → `return`，**不要求任何审查对**；而现状门禁对 current 块强制 fresh+blank 对。于是 `test_metadata_only_prompt_evidence_rejected_when_material`、`test_only_metadata_only_terminals_gate_fails_closed`、`test_post_hoc_hash_injection_rejected`、`test_crlf_pollution_fails_closed`、`test_duplicate_review_target_block_rejected` 等负例将 rc=0（本应 rc≠0），A-12/A-16 破。即使 BLK-2 修好，此洞仍在。
- 单选修法：循环改为**含 legacy 块**：`for j in (legacy .. len-1): require full pair against T=blocks[j]`（或至少显式要求"链上最后一个 decisional 块（含 legacy）必须有 full-pair"），保证单块 legacy 与现状同强度。

**BLK-4｜§3.5 伪代码硬编码 `candidate_artifact`，与真实旧块的 `candidate_plan` 不兼容，reopened 对象在 `:154` 即失败**
- severity: `structural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:154`（`current.candidate_artifact`）、`:178/:181/:182`（`candidate_artifact.sha256`）；对照 `orchest.py:1171`（现状 `candidate_plan or candidate_artifact`）、`plan.md:65`（§2.2 已承认二名并存）
- 事实：真实归档块使用 `candidate_plan`（实核 done 对象三块），仅测试 helper 使用 `candidate_artifact`。§3.5 的 `current.candidate_artifact == disk plan` 对 reopened 旧对象会在首个校验点失败，与"旧数据无需迁移"（§13.4:421）冲突；`blocks[j-1].candidate_artifact.sha256` 同理丢失兼容。§2.2 明确列出两种字段名，伪代码却只取一种——不一致。
- 单选修法：伪代码统一改用 `cur = b.get("candidate_plan") or b.get("candidate_artifact")`（与 `orchest.py:1171` 同源），并在 A-6 增设"legacy 块用 `candidate_plan` 的历史 candidate 子用例"。

### 非阻断

**NB-1｜A-13 把 §12.3 归为"新增型"，与 §12.3 标题"(replace 型)"冲突；§12.1 的 replace 部分亦未纳入三态**
- severity: `structural`；位置：`plan.md:285`（A-13）vs `:378`（§12.3 标题）、`:362`（§12.1 标题）；对照 `:357/:371`
- 事实：§12.3 是替换标题（旧标题须消失），A-13 却按"新增型（新子串存在）"判定，会放过"旧标题仍在"的漂移；§12.1 含 `:103` 的 replace 部分，A-13 只写"12.1 bullet"。A-13 的机械可判定性因此有缺口。
- 单选修法：A-13 改为逐项对齐 §12 标题：`12.0/12.1(replace 部分)/12.2/12.3/12.6/12.7 = replace`（旧子串消失 ∧ 新子串存在）；`12.4/12.5 = append`；`12.1 bullet = 新增`。

**NB-2｜§3.5 `if not D` 为不可达死分支；§12.4"全 non-decisional 链保守回退"措辞与实现不符**
- severity: `implementation`；位置：`plan.md:163`、`:169-172`、`:398`（§12.4）
- 事实：`:163` 已要求 `blocks[0].cc == decisional`，故 `D` 恒非空，`:170-172` 不可达；§12.4 却称"全 non-decisional 链……维持全量对（保守）"——该形态实际在首块门即 fail，不会进入回退。UV 曾专门批评死分支（N2/I-16/UV3-14），candidate-2 删除了 `continue` 却留下这一处。
- 单选修法：删除 `if not D` 分支，或改为 `assert D` 并补注释；同步修正 §12.4 措辞为"链首非 decisional → 直接 fail closed"。

**NB-3｜reopen 跨 revision 边界未被伪代码落实（仅检查全局 blocks[0]）**
- severity: `structural`；位置：`plan.md:147`（"覆盖 reopen 跨 revision：新 revision 首块必须 decisional"）、`:151`（`blocks = all material blocks`）
- 事实：链构造无 `_detect_revision_id` 过滤；`:163` 只要求**全局**首块 decisional。reopen 后全局首块是旧 revision 的块（通常 decisional），因此"新 revision 首块必须 decisional"**不被执行**。N4/I-11/UV3-06 的 reopen 缺口只被部分闭合。
- 单选修法：链构造按 `_detect_revision_id` 过滤（id 前缀/revision_id），或显式规定"每个 revision 段的首块必须 decisional 且 base=null"并落进伪代码。

**NB-4｜§3.5 伪代码未含 full-pair 的"正向 verdict"与"禁含 delta"两项硬检查**
- severity: `implementation`；位置：`plan.md:132`（§3.3 禁 delta）、`:141`（分级 verdict 语义）、`:174`（full-pair require）、`:191`（文字描述）
- 事实：`"delta" not in payload` 与 full-pair 的正向 `verdict == 可执行` 仅出现在 §3.5 的散文（`:191`、§2.2:72），未进入"写死"伪代码的 full-pair 分支；若实现者只按伪代码落地，full-pair 仍可能沿用旧的负向 verdict 检查，且带 `delta` 的 payload 可能被 full-pair 接受。
- 单选修法：把两条检查写进 §3.5 的 full-pair require 列表，并对应加 A-6 子断言。

**NB-5｜F6"分级常量单源在 orchest.py"静态断言无常量名/位置**
- severity: `implementation`；位置：`plan.md:232`（F6）
- 事实：UV3-02 已指出该断言不可预判可写性；candidate-2 未在 §3.5/§5 定义常量名（如 `MATERIAL_CHANGE_CLASSES`/`MATERIAL_SECTIONS_VOCAB`）。断言无法机械落地。
- 单选修法：在 §3.5 命名单一权威常量（如 `MATERIAL_CHANGE_CLASSES`、`MATERIAL_SECTION_VOCAB`）并声明唯一来源，F6 断言锚定该符号。

**NB-6｜`scripts/README.md:17` 的"两-authority 审查时必传 exact"未随分级机制同步**
- severity: `implementation`；位置：`scripts/README.md:17`；对照 F7/§12.7 仅覆盖 `:151`
- 事实：新机制下 non-decisional 单 delta 路径**亦**须 exact。`:17` 的从句会让读者以为仅双权威需 exact。F7 描述 `:144-151` 未含 `:17`。
- 单选修法：把 F7 锚点扩为 `:17` 与 `:144-151`，或将该注释改为"material-revision（任一级别）审查时必传 exact"。

---

## 五、对抗面复核（§11 封死性）

| 攻击 | 是否封死 | 依据 |
|---|---|---|
| 谎报 non-decisional 且 `changed_sections` 含 decisional 章节（A-11-4） | **存疑（依赖 BLK-1 消解）** | 若按 §3.2 域约束实现 → 交集恒空、A-10 死；若按 §3.5 实现 → 可拦截。二者需先一致 |
| 漏报 `changed_sections`（如实声明下的语义漏报） | 否（**固有残余**，R-1 已承认） | 机械层不可判，交 delta reviewer |
| 伪造 `base_plan_sha256`（A-11-2） | 是 | 与 `blocks[j-1].candidate_artifact.sha256` 比对；但 BLK-4 下旧块用 candidate_plan 会误伤 |
| 链中删块（A-11-3） | 是 | 后继 payload 的 base 与新前块不符 → fail |
| payload/output 回显不一致（A-11-6） | 是 | byte-equal |
| `verdict = 需重新设计`（A-11-9） | 是 | 正向 `== 可执行`（candidate-2 已修） |
| `change_class` 非法枚举/变体（A-11-10） | 是 | 域门 |
| `changed_sections` 空/词表外（A-11-11） | 是 | 域门（但 BLK-2 对 legacy 误杀） |
| 旧 decisional 缺 anchors 后继走 delta（A-11-12） | 是 | legacy→随后全 full-pair（但 BLK-3 漏当前块） |
| decisional 低报 anchors（A-11-14） | 否（**固有残余**，如实声明） | 语义兜底 |

结论：§11 在**语义层坦承残余**（A-11-14/R-1/R-2）的态度正确；但 BLK-1 令 A-11-4/A-10 的"机械"性质悬空，BLK-2/3 令 A-11-12 与既有负例冲突。

---

## 六、机器块与治理要件复核

- **preflight 真实**：独立复跑，输出与 `attempts.md:90-92` 一致，EXIT=0（真实，非编造）。
- **calibration**：locator `attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration]` 解析成功；canonical hash/digest/freshness 与报告一致；独立文件逐字节等于 canonical（仅证据留痕，preflight 不校验 `evidence/`——`_ROOT_ALLOWLIST` 确排除，`refs/state-schema.md:76` 属实）。
- **user_message_events 跨对象**：`budget_gate.py:1677-1679` 仅 UUID 格式校验，B 对象事件实存，计划 §14:429 披露充分且给出"编排层后补清单"路径——**接受，非伪造**。惟该两 UUID 并非本对象授权事件，属语义降级，建议 retrospective 显式落账。
- **A-4 口径**：正确采用 fenced-json 解析计数（字符串出现 5 次），避免误判。
- **A-1/A-17**：42114 B ≤ 46080；`budget_gate.py` 无改动、`numeric_changes` 全 mechanism。

---

## 七、D1 方向是否成立

**成立（是）。**

1. O6 的成本问题有活体证据（B 对象 `retrospective.md:75/:80`：41KB→133KB、7 次重认证≈半数评议成本），议题出处 `docs/plans/active/20260911-converge-operational-envelope.md:25` 实核。
2. `decisional` 保留全量双权威、`non-decisional` 降为单 fresh delta + 块链 hash + 并集交集的**三段式认证语义自洽**：最后一个 decisional 块的全量对直接认证其字节，其后每块 delta 绑定前块→本块，最终可归纳认证；更早块无需复验也不破安全。
3. candidate-2 已把 §1 的"三重机械校验"改为诚实的"机械 + 判断"分工，并对 R-1/R-2 如实声明，不伪造闭环——符合"契约违反 fail-closed、判断分歧交语义"的宪法边界。

**判为 `阻断需修复` 而非 `需重新设计`**：缺陷集中在 §3.2/§3.5 的**机械不变量规范**（章节域、legacy 分支、字段兼容）与验收分类精度，均可通过改写 §3.2/§3.5 伪代码与 A-5/A-12/A-13 修复，不动摇 delta 方向本身。

---

## 八、实施前必须满足的前置条件清单（本 verdict 为 `阻断需修复`，仅列修复面）

1. 消解 BLK-1：统一 §3.2/§3.5/A-10/A-11-4 的章节域语义（建议选 A：门禁接受 12 项、并集交集机械拦截；删除错误括注）。
2. 消解 BLK-2：完全旧块（缺 `change_class`）绕过 `changed_sections` 域门，按 legacy→full-pair 处理，保证既有 17 条测试与 reopened 对象通过。
3. 消解 BLK-3：legacy full-pair 范围含 legacy 当前块（或显式要求最后 decisional 块有对），保证单块旧对象不被 fail-open。
4. 消解 BLK-4：伪代码统一 `candidate_plan or candidate_artifact`。
5. 修正 NB-1（A-13 三态）、NB-2（死分支/§12.4 措辞）、NB-3（reopen 分段）、NB-4（伪代码补 full-pair verdict/delta 检查）、NB-5（常量命名）、NB-6（README:17）。
6. 上述修订后重跑：`preflight` + 全套 `pytest`；并在 attempts.md 追加 candidate-3 处置记录。

---

## 九、无法核实的断言清单

1. **§3.5 全部新门禁行为**（链回溯、T 块 full-pair、delta 候选、并集交集、错误码）与 A-5..A-13、A-15 均**待实现**，当前只能静态推演；本报告已指出其中 4 处会导致 A-12/A-16 无法达成。
2. **B 对象"7 次重认证≈半数评议成本"**（`retrospective.md:80`）为该对象自报估算，仅核对引文存在，未复核底层派发记账。
3. **D2 三种分流结果的实际触发分布**属未来事实，不可核实。
4. **`ultraverge_min_reviewers=3`、critical 20/30** 由 `_budget-state.json`/`gate-ledger` 佐证；本批实际 spawn 数待本批完成后核实。
5. **OCSR 派发层能否在 `--evidence-mode exact` 下为 delta reviewer 正确采集 prompt/output blob**，需实现后验证（与 R-2 残余相关）。
6. `archive:done/20260911-op-envelope-b-contract-correction` 仅过格式校验（`budget_gate.py:1450`），preflight 不做存在性核验；其归档现状依赖 B 对象（已实存）。
