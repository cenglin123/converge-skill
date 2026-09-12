---
round: 2
role: outer-reviewer
review_mode: ultraverge
reviewer_backend: opencode
reviewer_instance_id: fresh-r2-o6
generated_at: 2026-09-12
verdict: 阻断需修复
---
阻断需修复

# round-2 · O6 material 增量复核（candidate-3）· ultraverge 完整收敛 outer R2

> Reviewer：outer 权威（fresh、独立上下文；未读本轮 blind 产出，未与 plan 作者/前轮评审共享）。
> 受审对象：`.converge/active/20260912-o6-material-delta-recert/plan.md`（candidate-3，**46074 B**）。
> 基线：HEAD `da81e70cee7931d49680866f9cd0b2cdb6fadc5a`（`git log --format=%H -1` 实核）。
> 实核方式：逐行实开 `plan.md`、`round-1.md`、`attempts.md`、`uv-init-1/2/3.md`、`CONSTITUTION.md`、`SKILL.md`、`refs/state-schema.md`、`refs/orchestrator-guide.md`、`refs/design-review-prompt.md`、`scripts/orchest.py`、`scripts/archive_contract/model.py`、`scripts/budget_gate.py`、`tests/test_loop_a_coverage.py`、`tests/test_process_controller_contract.py`、真实归档块；preflight 独立复跑；`_detect_revision_id`/过滤语义实跑复现。只读（本报告除外）。

**结论：R1 的 BLK-1..4 与 NB-1/2/4/5/6 均已按单选修法落地且可核；唯 NB-3（reopen 分段）的落地写法引入一处新的 `architectural` 阻断——按 `_detect_revision_id` 过滤链，在既有测试夹具（块 `revision_id` 为 `r2/r3/r4`、无 `.reopen-state.json` → `_detect_revision_id()` 返回 `r1`）与真实归档块上会把整条链过滤为空并 `return`，导致 10 条既有负例断言失败（A-12/A-16 不可能成立），且构成材料门的整门 fail-open 绕过。故 verdict = `阻断需修复`。**

---

## 零、事实核验（实开/实跑）

| # | 断言 | 实核结果 |
|---|---|---|
| F1 | candidate-3 `plan.md` ≤ 45KB（A-1） | ✅ 实测 **46074 B** ≤ 46080（`wc -c`） |
| F2 | frontmatter `status/review_mode/object_slug`（A-2） | ✅ 头 3 行为 `candidate-3`/`ultraverge`/`20260912-o6-material-delta-recert` |
| F3 | preflight 实跑（A-3） | ✅ 独立复跑 `python scripts/budget_gate.py preflight --plan …` → `WARN:code_heavy:2,120` + `PREFLIGHT_OK:governance-change`，EXIT=0；与 `attempts.md:179-181` 一致（真实） |
| F4 | 恰一个 governance fenced-json 块（A-4） | ✅ 全文 fenced-json 块 **1** 个、含该 schema 者 **1**；字符串 `converge.governance-change/v1` 出现 **5** 次（散文/§2/§14）——A-4 用解析器计数口径正确 |
| F5 | `orchest.py` 材料门锚点 | ✅ `:1095-1118`/`:1133-1361`/`:1144-1149`/`:1171-1175`/`:1185-1186`/`:1204-1205`/`:1207-1259`/`:1215-1218`/`:1235-1238`/`:1267-1272`/`:1273-1293`/`:1303-1310`/`:1335-1337`/`:1340-1361`/`:1579-1581` 全部命中；`:1344-1345` 现仅拒字面量 `阻断需修复` |
| F6 | 现有 material 测试计数（§2.5） | ✅ AST 计数：4 个 `TestMaterial*` 类、直接定义 **17** 个 test（ClosureGate 6 / LocatorResolution 4 / LegacySkip 3 / QualifyByCurrentBlock 4）；其中 **10** 条为 `assertNotEqual(rc,0)` 负例 |
| F7 | §12 全部"原文" | ✅ `state-schema.md:101/:103/:104`、`orchestrator-guide.md:17/:23/:32`、`SKILL.md:462`、`scripts/README.md:151/:17` 逐字吻合（含 `:17` 前导空格） |
| F8 | `REVIEWER_AUTHORITIES` | ✅ `model.py:91-94`：fresh 含 `outer-reviewer`，blank-slate 含 `blind-reviewer` |
| F9 | budget_gate 校验 | ✅ `:1467/1594` mechanism 未强制 `comparison=null`；`:1710-1742` 窄门仅裁决数值 kind；`:1452-1459` `_ROOT_ALLOWLIST` 排除 `evidence/`；`:1668-1679` 仅 UUID 格式校验 |
| F10 | calibration | ✅ fence `id=calibration`；canonical sha256 `16ec2455…`；`corpus_digest=3627eb4d…`；`freshness` 三键吻合；`evidence/calibration-report.json` raw sha256 == canonical（逐字节一致） |
| F11 | **`_detect_revision_id` 语义（关键）** | ❗ 实跑：无 `.reopen-state.json` 时返回 **`r1`**；测试夹具 material 块 `revision_id` 分别为 `r2/r3/r4`（`tests/test_loop_a_coverage.py:360-373/412/868/870/882/926/960-966/1097/1127/1217/1254/1315/1328/1382`），真实归档块为 `r2`（`.converge/done/20260910-process-controller-consolidation/attempts.md:146/180/234`） |
| F12 | B 成本证据 | ✅ `retrospective.md:42/:53/:75/:80` 引文逐字存在 |
| F13 | `_budget-state.json` | ✅ `fsm.mode=ultraverge`、`config.task_tier=critical` |

---

## 一、前置自检 5 问

| # | 问题 | 结论 | 依据 |
|---|---|---|---|
| Q1 | 产物身份自洽 | **基本通过** | "O6 重评 + 条件实现"贯穿 §1/§4/§6；D1 分级 + delta 路径 + 链回溯自洽。仅 NB-3 落地与既有块 `revision_id` 现实冲突（R2-BLK-1） |
| Q2 | 产物边界诚实 | **基本通过** | §1 维持"机械绑定 + verdict 门控（判断）"定位；§3.4:142/§8.7/§10 R-2 对"prompt 内 base 文本无机械绑定"如实声明；A-11-14 承认 anchors 低报为语义残余——诚实 |
| Q3 | 产物数据纯度 | **通过** | 纯机制；calibration 实核；机器块 schema 通过 |
| Q4 | 职责边界自洽 | **基本通过** | 作者声明、reviewer 挑战、门禁只校验声明间一致性——candidate-3 已把"并集交集"从错误域约束中解放（BLK-1 修复），职责链自洽；唯一破口是 NB-3 过滤把整门短路 |
| Q5 | 命名一致性 | **通过** | `change_class` 全篇统一（`declared_class` 已除）；`candidate_plan or candidate_artifact` 统一为 `cur()`；12 项词表 §3.2/§12.4 逐字一致 |

---

## 二、DR 7 维逐维结论

| 维度 | 结论 | 依据 |
|---|---|---|
| DR1 一致性 | **concerns_found（阻断）** | §3.5:155-157 的 `_detect_revision_id` 过滤与既有块 `revision_id`（r2/r4）及 §3.7:233/A-5:307/A-12:313 直接冲突（R2-BLK-1）；§3.1:116/A-11-12:374 声明的错误码 `legacy-anchor-requires-full-pair` 在伪代码中无发出点（R2-NB-1） |
| DR2 完整性 | **concerns_found** | 主链逻辑（域门、legacy 含自身、T 三重锚定、并集交集、正向 verdict）完整；但 revision 分段规则的"当前段"定义误用 reopen-state 默认值，且无任何验收覆盖 `revision_id` 与当前段不等的场景 |
| DR3 可维护性 | **concerns_found（轻）** | `if not blocks: return` 作为"当前 revision 无块"的兼容分支，与过滤误用叠加即静默放行，属反直觉陷阱；R2-NB-2（"必填"字段缺省走 legacy）亦为软性口径 |
| DR4 职责边界 | **基本 clean** | 机械层职责限于"声明域合法 + 块链绑定 + 并集交集"，语义 diff 交 fresh reviewer——candidate-3 已修正 R1 的职责倒置 |
| DR5 残留与冗余 | **concerns_found（轻）** | `cur()` 辅助与常量命名清晰；唯 §3.1:112/§3.2:114 "decisional_anchors 必填" vs §3.5:176-177 缺省即 legacy 的口径未对齐 |
| DR6 可移植性 | **clean** | 无环境硬编码；宿主记忆路径已标注外部权威源 |
| DR7 可扩展性 | **concerns_found** | 链回溯 O(n) 可接受；分段规则若按 reopen-state 而非"末块所属段"识别，跨 revision 链的"当前段"随宿主状态漂移，扩展边界未被承认（R2-BLK-1） |

---

## 三、R1 处置清单（BLK-1..4 + NB-1..6，逐条 yes/no + plan 原文行号）

> 依据 `round-1.md` 第四节。以下"落地"= 按 R1 单选修法在 candidate-3 中可核。

| ID | R1 要求（摘要） | 落地 | plan 原文行号（实核） |
|---|---|---|---|
| BLK-1 | 消解"non-decisional 只允许后 4 项"域约束与并集交集矛盾（建议 A） | **yes** | §3.2:124-126（唯一域门 = 非空 ∧ ⊆12 项；误归类由并集交集拦截）；§3.5:172-173、215-216；A-10:311；A-11-4:366；§12.4:419 |
| BLK-2 | 完全旧块绕过 `changed_sections`/`decisional_anchors` 域门 | **yes** | §3.5:166-169（`if "change_class" not in b: … continue`）；§3.1:116；§3.7:233；A-5:307 |
| BLK-3 | legacy full-pair 含 legacy 块自身 | **yes** | §3.5:195-198（`for j in (legacy .. len(blocks)-1)`）；§3.1:116；§12.1:398；§12.4:419；§12.5:427 |
| BLK-4 | 伪代码统一 `candidate_plan or candidate_artifact` | **yes** | §3.5:152、161、186、207、210、211；§3.4:138-139；A-6:307；A-11-2:364；F1:256 |
| NB-1 | A-13 按 §12 逐项三态对齐 | **yes** | A-13:313-314（12.0/12.1-replace/12.2/12.3/12.6/12.7/12.8=replace；12.4/12.5=append；12.1 bullet=新增） |
| NB-2 | 删 `if not D` 死分支；修 §12.4/12.5 措辞 | **yes** | §3.5:200-201（`assert D`）；§12.4:419；§12.5:427（"链段首块非 decisional 直接 fail closed"） |
| NB-3 | reopen 跨 revision 边界按 `_detect_revision_id` 分段 | **no（引入新阻断）** | §3.5:147、155-158、181-182；F1:256。过滤写法与既有块 `revision_id` 现实冲突 → **R2-BLK-1** |
| NB-4 | 伪代码补 full-pair 正向 verdict + 禁含 delta | **yes** | §3.5:184-193（`require_full_pair`：`"delta" not in payload` + 双 verdict `== "可执行"`）；A-6:307；§3.3:132 |
| NB-5 | 分级常量单源命名并锚定 F6 | **yes** | §3.5:147、150-152（`MATERIAL_CHANGE_CLASSES`/`MATERIAL_SECTION_VOCAB`/`cur()`）；F6:261；A-5:307；F1:256 |
| NB-6 | `scripts/README.md:17` 随分级同步 | **yes** | §12.8:443-446；F7:262；A-13:313 |

**结论**：BLK-1..4 = 4/4 yes；NB-1/2/4/5/6 = 5/5 yes；**NB-3 = no**（其落地形式制造新阻断）。故 R1 处置完整性 = **9/10**，NB-3 未真正闭合。

---

## 四、UV 三票处置抽查表（≥8 条回 plan 原文；核 candidate-3 未破坏）

| # | 原 issue（票） | candidate-3 落点（实核行号） | 抽查结论 |
|---|---|---|---|
| 1 | uv1-B1 交集恒空 | §3.2:124-126 + §3.5:172-173/215-216 + A-10:311 + §11:366 | **已闭合**：域门放宽为 12 项，拦截改并集交集，错误括注已删 |
| 2 | uv1-B2 / uv2-I-1 / uv3-01 `["*"]` 哨兵 | §3.1:116（明示"无 `["*"]` 哨兵"）+ §3.5:166-169/195-198 | 哨兵已废、legacy 含自身；**受 R2-BLK-1 影响**（含自身逻辑本身正确） |
| 3 | uv1-B3 full-pair 比较目标 | §3.5:184-193 `require_full_pair(T)` 三重锚定 | **有效**（并补 NB-4 的禁 delta / 正向 verdict） |
| 4 | uv1-B4 / uv2-I-4 / uv3-09 delta 未锚定 | §3.5:206-211（artifact/material_revision/locator 三重 + delta.*）+ A-11-13:375 | **有效** |
| 5 | uv1-B5 / uv3-05 / uv3-07 标题+词表+README | §12.0:386-389、§12.3:407-410、§12.4:412-419（完整 12 项）、§12.7:436-441 | **有效**；指针目标真实存在 |
| 6 | uv1-B6 / uv3-06 record-only | §4.1:243 + §6:283-290 + A-R1..A-R3:320-322 | **有效**（3/3 `需重新设计` 为逐字机械判据） |
| 7 | uv1-B7 / uv2-I-7 / uv3-08 "7→17" | §2.5:99-100（4 类 17 条，AST） | **有效**（实核 17） |
| 8 | uv2-I-3 / uv3-03 verdict 正向 | §3.4:141 + §3.5:192/214 + A-9:310 | **有效**（含 `需重新设计`/缺失/变体） |
| 9 | uv2-I-5 非空/漏报 anchors | §3.5:172/179 + §10 R-1:350（changed_sections/anchors 双向） | **有效**（受 R2-BLK-1 短路影响） |
| 10 | uv3-12 legacy 行号 | §2.2:73（`:1215-1218`/`:1235-1238`；`:1204-1205` 标 terminal） | **有效**（逐行实核） |
| 11 | uv3-13 comparison 措辞 | §14:462 | **有效**（`:1594` 允许非 null） |
| 12 | uv3-16 规范性句子=decisional | §3.2:122 + §12.4:418 | **有效** |
| 13 | uv2-I-10 "唯一块"措辞 | §12.1:396（"locator 以 `id=` 唯一寻址 … 链判定读取全部块"） | **有效** |
| 14 | uv3-14 死代码 | §3.5:200-201（`assert D`） | **有效** |

**抽查结论**：candidate-3 未破坏任何已闭合的 UV 处置；合并去重与词表单源保持正确。

---

## 五、逐条 issue

### 阻断级

**R2-BLK-1｜§3.5 按 `_detect_revision_id` 过滤 revision 段，在既有夹具/真实归档块上把链过滤为空 → 10 条既有负例反转 + 整门 fail-open**
- severity: `architectural`；attribution: `plan_defect`；plan_amendment_required: true
- 位置：`plan.md:147`（"按 `_detect_revision_id` 过滤 `revision_id`"）、`:155-157`（`rev = _detect_revision_id(active); blocks = [b … if b.get("revision_id", rev) == rev]`）、`:158`（`if not blocks: return`）、`:181-182`；F1:256
- 事实（可复跑）：
  1. `orchest.py:1121-1130` 的 `_detect_revision_id` 在无 `.reopen-state.json` 时返回 `"r1"`；本对象/测试夹具均无该文件。
  2. `tests/test_loop_a_coverage.py` 的全部 material 夹具用 `_make_material_block`（`:336-348`）写入 `revision_id` = `r2`/`r3`/`r4`（实核行 `:412/868/870/882/926/960-966/1097/1127/1217/1254/1315/1328/1382`）。真实归档块 `revision_id` = `r2`（`.converge/done/20260910-process-controller-consolidation/attempts.md:146/180/234`）。
  3. 实跑复现：`_detect_revision_id(空目录)` → `r1`；对块 `{"revision_id":"r2"}` 施加候选过滤 → `[]` → `not blocks` 为真 → §3.5:158 `return`（本 Reviewer 已独立复现）。
  4. 后果一（验收不可能）：17 条既有 material 测试中 **10 条负例**（`test_changed_plan_byte_after_review_invalidates:452`、`test_metadata_only_prompt_evidence_rejected_when_material:464`、`test_post_hoc_hash_injection_rejected:483`、`test_crlf_pollution_fails_closed:531`、`test_duplicate_review_target_block_rejected:572`、`test_payload_referencing_missing_material_id_fails_closed:918`、`test_only_metadata_only_terminals_gate_fails_closed:1087`、`test_qualifying_candidate_with_mismatched_payload_hash_fails:1117`、`test_only_stale_pair_fails_closed:1304`、`test_qualifying_pair_with_non_executable_verdict_fails:1372`）断言 `rc != 0`；链被过滤为空后门静默 `return` → `rc=0` → 全部失败。A-12（"17 条行为不变"）、A-16（全量 pytest 绿）**不可能达成**。
  5. 后果二（fail-open）：任何**非 reopen** 对象只要当前 material 块的 `revision_id` 不等于 `_detect_revision_id()`（默认 `r1`）——真实块即 `r2`——材料门整门被 `if not blocks: return` 短路，不做 current-block-vs-disk-plan 校验、不做任何 full-pair/delta 校验。这与 §3.6:228-229"不降级/任何一环缺失 FAIL_CLOSED"及 §1 成功判据直接冲突，也比现行实现（`orchest.py:1152-1175` 不按 revision 过滤、对 current 块强制校验）更弱。
- 单选修法（单条、须同步 §3.5/§3.7/F1/A-5 并补验收）：
  - **删除对 `_detect_revision_id` 的过滤依赖**。链构造改为：取**全部** `converge.material-revision/v1` 块（文档顺序），**当前段 = 末块所属 revision 段**（自末块向前，凡 `revision_id` 与末块相同或缺失者归入当前段；`revision_id` 与末块不同的更早块属历史段，仅对其段首做 decisional 校验、不参与 delta 链）；`current = blocks[-1]` 与盘上 `plan.md` 的校验保持不变。
  - 即：`rev_cur = all_blocks[-1].get("revision_id")`，`blocks = [b for b in all_blocks if b.get("revision_id", rev_cur) == rev_cur]`，且当 `rev_cur is None` 时全部块归当前段（不再以 `"r1"` 默认值判定）。这样既保留 reopen 分段（新 revision 追加于末尾 → 末块属新段），又不误伤 `r2/r4` 夹具与真实对象。
  - 同步：§3.7:233/A-5:307 明写"`revision_id` 与当前段不一致的块按历史段处理、不影响 current 校验；`revision_id` 缺省或等于末块 `revision_id` 的块参与链"；新增一条验收（如 A-5 子断言或 A-11 新例）覆盖"无 `.reopen-state.json` + 块 `revision_id=r2` → 门仍生效（负例 rc≠0、正例 rc=0）"。

### 非阻断级

**R2-NB-1｜§3.1/§3.6/A-11-12 声明的错误码 `legacy-anchor-requires-full-pair` 在 §3.5 伪代码中无发出点**
- severity: `implementation`；位置：`plan.md:116`（§3.1 声明错误码）、`:228`（§3.6）、`:374`（A-11-12）vs `:195-198`（§3.5 legacy 分支仅逐个 `require_full_pair`）
- 事实：伪代码 legacy 分支对所有后续块调用 `require_full_pair`，失败时只会产生既有"no qualifying pair"类错误，不会产生 `FAIL_CLOSED:material-gate:legacy-anchor-requires-full-pair`；而 A-11:312 要求"指定错误码"，A-11-12:374 明确写该码。规范与伪代码不一致。
- 单选修法：二选一——(a) 在 §3.5 legacy 分支进入前显式 `raise FAIL_CLOSED:material-gate:legacy-anchor-requires-full-pair`（对"缺 anchors 的旧 decisional 块"与"完全旧块"分别发码），或 (b) 把 A-11-12 的判定改为"rc≠0 即可，错误码不作硬断言"，并同步 §3.1:116/§3.6:228 措辞。

**R2-NB-2｜`decisional_anchors` 声明为"必填"，伪代码却把缺省当 legacy 而非 schema 违规**
- severity: `implementation`；位置：`plan.md:112`（§3.1 表"必填"）、`:114`（§3.2 "decisional 块必填"）vs `:176-177`（§3.5 `if a is None: if legacy is None: legacy = i`）
- 事实：带 `change_class` 的新 decisional 块若缺 `decisional_anchors`，伪代码不 `FAIL_CLOSED`，而走 legacy→full-pair。行为上保守（不 fail-open），但与"必填"口径不符，且 §3.6:228 的 fail 条件列举里"`decisional_anchors` 空或含词表外值"未含"缺失"。
- 单选修法：在 §3.1/§3.2 将该字段语义写成"新 decisional 块缺失即 legacy 兼容（自其起全量对）；空列表或词表外值才 `FAIL_CLOSED:anchors-vocab`"，或反之把缺失也纳入 `anchors-vocab` fail；二者取一，并同步 §3.6:228。

**R2-NB-3｜§12.4 新增段落的 `decisional_anchors` 语义与 §3.1 表定义存在措辞冗余（非缺陷，供实施对齐）**
- severity: `implementation`（提示，不阻断）；位置：`plan.md:114`（§3.1 表"全量判定承载章节快照"）vs `:419`（§12.4 同义句）
- 事实：两处语义一致，无实质冲突；但 §12.4 为准规范落地文本，建议实施时保持与 `refs/state-schema.md` 新 bullet（§12.1:398）三处同字，避免后续 drift。
- 单选修法：实施时以 §3.2/§12.4 为单一权威，§12.1 仅指针，不再展开语义分支。

> 说明：§3.5 伪代码的域门/legacy 含自身/T 三重锚定/并集交集/正向 verdict 经逐行推演**未发现 fail-open**；R2-NB-1/NB-2 为规范-伪代码一致性问题，R2-NB-3 为对齐提示。A-1 仅有 6 B 余量（46074/46080），属 R-5 已声明风险，不单列。

---

## 六、对抗面复核（§11 封死性，含 candidate-3 新面）

| 攻击 | 是否封死 | 依据 |
|---|---|---|
| 谎报 non-decisional + `changed_sections` 含 decisional 章节（A-11-4） | **是**（条件成立时） | §3.5:215-216 并集交集；本文档论证：若按 §3.2 旧"后 4 项"域则为死；candidate-3 已删该域约束，改 12 项域门，交集可触发 |
| 漏报 `changed_sections` / 低报 `decisional_anchors` | **否（固有残余，如实声明）** | §10 R-1:350、A-11-14:376，机械层不可判，交 delta reviewer |
| 伪造 `base_plan_sha256`（A-11-2） | **是** | §3.5:210 比对 `cur(blocks[j-1]).sha256` |
| 链中删块（A-11-3） | **是** | 后继块 `base` 与新前块不符 → fail（前提：链未被 R2-BLK-1 过滤空） |
| `change_class` 非法枚举/变体（A-11-10） | **是** | §3.5:171 域门 |
| `changed_sections` 空/词表外（A-11-11） | **是** | §3.5:172-173 域门 |
| verdict 造假含 `需重新设计`/缺失/变体（A-11-9） | **是** | §3.5:192/214 正向 `== "可执行"`（full 与 delta 皆然） |
| payload/输出回显不一致（A-11-6） | **是** | byte-equal |
| 旧 decisional 缺 anchors 后继走 delta（A-11-12） | **是**（保守） | §3.5:195-198 全量对；惟错误码未按声明发出（R2-NB-1） |
| **`revision_id` ≠ `_detect_revision_id()`（新面）** | **否（R2-BLK-1）** | §3.5:157-158 过滤空 → `return`，全门绕过 |
| decisional 低报 anchors（A-11-14） | **否（固有残余，如实声明）** | 语义兜底 |

结论：§11 的语义残余坦承正确；除新面 R2-BLK-1 外，机械对抗面在链未被短路的假设下成立。

---

## 七、机器块与治理要件复核

- **preflight 真实**：独立复跑与 `attempts.md:179-181` 一致，EXIT=0。
- **calibration**：locator `attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration]` 解析成功；canonical hash/digest/freshness 与独立文件逐字节一致（raw==canonical True）；`evidence/` 不被 preflight 校验（`_ROOT_ALLOWLIST` 实核）。
- **user_message_events 跨对象**：`budget_gate.py:1677-1679` 仅 UUID 格式校验；两个 B 对象事件 UUID 计划已如实披露并给后补路径——**接受，非伪造**；建议 retrospective 显式落账。
- **A-4 口径**：解析器计数 == 1，字符串出现 5 次，口径正确。
- **A-17**：§14 `numeric_changes` 3 条全 `kind: mechanism`、`comparison: null`；`budget_gate.py` 无改动。

---

## 八、D1 方向是否成立

**成立（是）。** 理由：

1. 成本问题有活体证据（B `retrospective.md:75/:80`：41KB→133KB、7 次重认证≈半数评议成本），议题出处 `docs/plans/active/20260911-converge-operational-envelope.md:25` 实核。
2. 三段式认证语义自洽：`decisional` 保留全量双权威不放宽（§3.3/§8.1）；`non-decisional` 降为单 fresh delta，以"最近 decisional 全量对 + 其后逐块 delta（前块→本块）+ 并集交集 fail-safe + 正向 verdict"归纳认证最终字节；更早块被新 decisional 全量对覆盖，无需复验。
3. candidate-3 对 R1 的 BLK-1..4/NB-1/2/4/5/6 均按单选修法落地，并诚实保留 R-1/R-2/R-6 语义残余，不伪造机械闭环。

**判为 `阻断需修复` 而非 `需重新设计`**：缺陷集中在 NB-3 的落地选择（用 `_detect_revision_id` 过滤当前段）与两处规范-伪代码口径；可由 R2-BLK-1 单条改写（当前段 = 末块所属段）+ 补一条验收消解，不动摇 delta/分级方向本身。

---

## 九、无法核实的断言清单

1. **§3.5 全部门禁新行为**（链回溯、`require_full_pair(T)`、delta 候选、并集交集、错误码）与 A-5..A-13、A-15 均**待实现**；本报告已静态推演出 R2-BLK-1 会令 10 条既有负例失败。
2. **OCSR 派发层能否在 `--evidence-mode exact` 下为 delta reviewer 正确采集 prompt/output blob**，需实现后验证（与 R-2 残余相关）。
3. **B 对象"7 次重认证≈半数评议成本"**（`retrospective.md:80`）为该对象自报估算，仅核对引文存在，未复核底层派发记账。
4. **D2 三种分流结果的实际触发分布**属未来事实，不可核实。
5. **`ultraverge_min_reviewers=3`、critical(20/30)** 由 `_budget-state.json`（`fsm.mode=ultraverge`、`config.task_tier=critical`）与 defaults_version=2 佐证；本批实际 spawn 数待本批完成后核实。
6. `archive:done/20260911-op-envelope-b-contract-correction` 仅过格式校验（`budget_gate.py:1450`），preflight 不做存在性核验；其归档现状依赖 B 对象（已实存）。
