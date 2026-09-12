---
round: 3
role: outer-reviewer
review_mode: ultraverge
reviewer_backend: opencode
reviewer_instance_id: fresh-r3-o6
generated_at: 2026-09-12
verdict: 可执行
---
可执行

# round-3 · O6 material 增量复核（candidate-4）· ultraverge 完整收敛 outer R3

> Reviewer：outer 权威（fresh、独立上下文；未读本轮 blind 产出，未与 plan 作者/前轮评审共享）。
> 受审对象：`.converge/active/20260912-o6-material-delta-recert/plan.md`（candidate-4，**46057 B**，sha256 `d6525f44…`）。
> 基线：HEAD `da81e70cee7931d49680866f9cd0b2cdb6fadc5a`（`git rev-parse HEAD` 实核）。
> 实核方式：逐行实开 `plan.md`、`round-1.md`、`round-2.md`、`attempts.md`、`repair-report-c4.md`、`uv-init-1/2/3.md`、`CONSTITUTION.md`、`SKILL.md`、`refs/state-schema.md`、`refs/orchestrator-guide.md`、`refs/design-review-prompt.md`、`scripts/orchest.py`、`scripts/archive_contract/model.py`、`scripts/budget_gate.py`、`tests/test_loop_a_coverage.py`、`tests/test_process_controller_contract.py`、真实归档块；preflight 独立复跑；calibration 独立复算；pytest 基线实跑。只读（本报告除外）。
> 输入命名勘误：任务书称"同目录 `round-3.md`（R2 全部 issue）"，实际磁盘上 R2 报告为 `round-2.md`（本轮生成本报告 `round-3.md`）；已按 `round-2.md` 复核，非产物缺陷。

**结论：R2 的 1 条阻断（R2-BLK-1）+ 3 条非阻断（R2-NB-1/2/3）全部按各自单选修法落地且可核。R2-BLK-1 的核心——链构造由 `_detect_revision_id` 过滤改为 `rev_cur = all_blocks[-1].get("revision_id")`（当前段 = 末块所属段）——经逐条推演，计划 A-19 列名的 10 条既有负例在 candidate-4 语义下**逐条仍 `rc != 0`**，且 7 条既有正例仍 `rc = 0`（A-12/A-16 可达）。未发现新的阻断级缺陷；余项为精度/可判定性级，可转实施约束清单。故 verdict = `可执行`。**

---

## 零、事实核验（实开/实跑）

| # | 断言 | 实核结果 |
|---|---|---|
| F1 | candidate-4 `plan.md` ≤ 45KB（A-1） | ✅ 实测 **46057 B** ≤ 46080（`wc -c`），与 `repair-report-c4.md:14`/`attempts.md:274` 一致 |
| F2 | plan.md sha256 | ✅ `d6525f441c321128e15f7d01bc7265cf46f403077ef694ae3e65018add8e6bee`（与 repair-report 一致） |
| F3 | frontmatter `status/review_mode/object_slug`（A-2） | ✅ 头 3 行 = `candidate-4`/`ultraverge`/`20260912-o6-material-delta-recert` |
| F4 | preflight 实跑（A-3） | ✅ 独立复跑 → `WARN:code_heavy:2,126` + `PREFLIGHT_OK:governance-change`，EXIT=0；与 `attempts.md:269-274`、`repair-report-c4.md:74-76` 逐字一致（真实） |
| F5 | 恰一个 governance fenced-json 块（A-4） | ✅ fenced-json 块总数 **1**、含该 schema 者 **1**；字符串 `converge.governance-change/v1` 出现 **5** 次（散文/§2/§14）——A-4 用解析器计数口径正确 |
| F6 | calibration（§2.4/§14/attempts） | ✅ fence `id=calibration`；canonical sha256 复算 `16ec2455…`；`corpus_digest=3627eb4d…`；`freshness` 三键吻合；与 `evidence/calibration-report.json` 同源 |
| F7 | `user_message_events` 跨对象 | ✅ B 对象 `evidence/events/00000049-989e5ebd…json`、`00000010-06754e6f…json` 实存；`budget_gate.py:1668-1679` 仅 UUID 格式校验；计划 §14:471 如实披露"本对象流内暂无"+ 后补路径——**接受，非伪造** |
| F8 | `orchest.py` 材料门锚点 | ✅ `:1095-1118`/`:1133-1361`/`:1144-1149`/`:1171-1175`/`:1185-1186`/`:1204-1205`/`:1207-1259`/`:1215-1218`/`:1235-1238`/`:1267-1272`/`:1273-1293`/`:1303-1310`/`:1335-1337`/`:1340-1361`/`:1579-1581` 全部命中；`:1121-1130` `_detect_revision_id` 默认 `r1` 属实 |
| F9 | 现有 material 测试计数（§2.5） | ✅ AST 计数：4 个 `TestMaterial*` 类、直接定义 **17** 个 test（ClosureGate 6 / LocatorResolution 4 / LegacySkip 3 / QualifyByCurrentBlock 4），行号与 §2.5:99-100 逐一吻合；**10** 条为 `assertNotEqual(rc,0)` 负例 |
| F10 | §12 全部"原文" | ✅ `state-schema.md:101/:103/:104`、`orchestrator-guide.md:17/:23/:32`、`SKILL.md:462`、`scripts/README.md:151/:17` 逐字吻合（含 `:17` 前导空格） |
| F11 | 12 项词表全篇一致 | ✅ 程序化提取：§3.2:125 与 §12.4:427 反引号 token 集合**恰为**同 12 项（无缺、无多） |
| F12 | 已删/未残留项 | ✅ `legacy-anchor-requires-full-pair` 出现 **0** 次；`declared_class` 仅出现在"废除 `declared_class`"；`["*"]` 仅出现在"无 `["*"]` 哨兵"；§3.5 无 `if not blocks: return`（仅 `if not all_blocks: return`，:156） |
| F13 | `REVIEWER_AUTHORITIES` | ✅ `model.py:91-94`：fresh 含 `outer-reviewer`，blank-slate 含 `blind-reviewer` |
| F14 | `_budget-state.json` | ✅ `fsm.mode=ultraverge`、`config.task_tier=critical`（§9 实核属实） |
| F15 | 基线 pytest 可行（A-12/A-16） | ✅ `python -m pytest tests/test_loop_a_coverage.py tests/test_process_controller_contract.py -q` = **60 passed**（105s） |
| F16 | F8 目标文件 git 状态 | ❗ `docs/plans/active/20260911-converge-operational-envelope.md` 存在（`:25` O6 行、`:36` 终态段实核属实），但 `docs/plans/active/` 在 HEAD 下 **untracked**（`git ls-files` 空、`git status` = `?? docs/plans/active/`）——见 issue-2 |

---

## 一、前置自检 5 问

| # | 问题 | 结论 | 依据 |
|---|---|---|---|
| Q1 | 产物身份自洽 | **通过** | "O6 重评 + 条件实现"贯穿 §1/§4/§6；§7 已按分支声明适用条件（implement A-1..A-19 / record-only A-R1..A-R3），不再身份冲突 |
| Q2 | 产物边界诚实 | **通过** | §1:42 明示"机械层只封'如实声明'下的违规、不声称机械闭环"；§3.4:142/§8.7/§10 R-2 对"prompt 内 base 文本无机械绑定"如实声明；A-11-14 承认 anchors 低报为语义残余 |
| Q3 | 产物数据纯度 | **通过** | 纯机制；calibration 真实生成物（已独立复算）；机器块 schema 通过 |
| Q4 | 职责边界自洽 | **基本通过** | 作者声明、复核者挑战、门禁只校验声明间一致性（§3.2:128/§3.5:190-224）；"归类争议=decisional"为流程 fallback 且残余 R-1/R-6 坦承（见 issue-6，非阻断） |
| Q5 | 命名一致性 | **通过** | `change_class` 全篇统一（`declared_class` 已除）；`candidate_plan or candidate_artifact` 统一为 `cur()`（§3.5:152）；12 项词表 §3.2/§12.4 逐字一致（F11） |

---

## 二、DR 7 维逐维结论

| 维度 | 结论 | 依据 |
|---|---|---|
| DR1 一致性 | **clean** | R2-BLK-1 的过滤致空已消除；§3.5 域门/legacy 含自身/T 三重锚定/并集交集/正向 verdict 与 §3.1/§3.3/§3.7/A-5..A-19/§12 互不矛盾；`legacy-anchor-requires-full-pair` 声明已按 R2-NB-1(b) 清除 |
| DR2 完整性 | **clean** | 链回溯（当前段=末块 `revision_id` 段）、历史段段首门、完全旧块绕过域门、anchors 缺失=legacy、T 块锚定、`require_full_pair` 禁 delta+正向 verdict、delta 三字段+base/current 链、并集交集、错误码集合均在 §3.5 落地；§11 对抗面 14 例穷举 |
| DR3 可维护性 | **concerns_found（轻）** | 若干验收文案偏软（A-5:313 "grep change_class 命中缺省" 无具体断言形态）；A-19 末条测试符号名不精确（见 issue-1） |
| DR4 职责边界 | **clean** | 机械层职责限于"声明域合法 + 块链绑定 + 并集交集"，语义 diff 交 fresh delta reviewer；§1 定位准确，无职责倒置 |
| DR5 残留与冗余 | **clean** | `["*"]` 哨兵、`declared_class`、死分支"全 non-decisional 保守回退"均已清除；§12.4/12.5 措辞与本实现一致 |
| DR6 可移植性 | **clean** | 宿主记忆路径标注为"外部权威源、非本仓库可验证"（§4.6:255/§9:349） |
| DR7 可扩展性 | **clean** | 链回溯 O(n) 可接受；当前段由末块 `revision_id` 确定性识别，不再随宿主 reopen 状态漂移（R2-BLK-1 修复的核心收益） |

---

## 三、R2 处置完整性（逐条 yes/no + plan 原文行号）

> 依据 `round-2.md` 第五节。R2 共 1 阻断 + 3 非阻断。

| ID | R2 要求（单选修法摘要） | 落地 | plan 原文行号（实核） |
|---|---|---|---|
| R2-BLK-1 | 删 `_detect_revision_id` 过滤；`rev_cur = all_blocks[-1].get("revision_id")`；`blocks = [b for b in all_blocks if b.get("revision_id", rev_cur) == rev_cur]`；`rev_cur is None` 全归当前段；当前段=末块所属段；历史段仅段首校验；补验收 | **yes** | §3.5:147（写死规则）、:155-164（伪代码）；§3.7:239-240；F1:263；A-5:313；**新增 A-19:327** |
| R2-NB-1 | 二选一；采 (b)：A-11-12 判 `rc≠0`、不硬断言专用错误码，同步 §3.1/§3.6 | **yes** | §3.1:116（"无专用码，R2-NB-1(b)"）；§3.6:234（fail 列表无该码）；A-11-12:382（"不硬断言专用错误码"） |
| R2-NB-2 | 语义改为"新 decisional 块缺失 anchors 即 legacy 兼容；空/域外才 `anchors-vocab`"，同步 §3.6 | **yes** | §3.1:114（"decisional 新块应填…缺失按 legacy 兼容…空/词表外才 `anchors-vocab`"）；§3.6:234（"缺失 `decisional_anchors` 不 fail"）；§3.5:181-185 |
| R2-NB-3 | 以 §3.2/§12.4 为单一权威，§12.1 仅指针 | **yes** | §12.1:405-406（新增 bullet 指向 guide §Material revision / §12.4，仅附一行 legacy 提醒） |

**R2 处置完整性 = 4/4 yes，无遗漏、无新引入矛盾。**

### 3.1 R2-BLK-1 特别推演：A-19 列名的 10 条既有负例在 candidate-4 语义下仍 `rc != 0`

> 按 §3.5 伪代码（:155-224）对 `tests/test_loop_a_coverage.py` 各夹具逐条推演。既有块均**无** `change_class`/`changed_sections`/`decisional_anchors`（`_make_material_block:336-348`），故各例 `legacy=0` → `require_full_pair`（对当前段全部块）；单块例 `blocks` 恒含末块（`rev_cur` 恒等于末块自身 `revision_id`），**不再出现 candidate-3 的过滤致空 `return`**。

| # | 测试（`tests/test_loop_a_coverage.py`） | 夹具链 | candidate-4 语义下的拦截点 | rc≠0 |
|---|---|---|---|---|
| 1 | `test_changed_plan_byte_after_review_invalidates:452` | [r2] | `current` 对盘校验 `cur(r2).sha256 != disk_plan.sha256`（§3.5:167-168）→ fail，消息含 plan.md | ✅ |
| 2 | `test_metadata_only_prompt_evidence_rejected_when_material:464` | [r2] | legacy=0 → `require_full_pair(r2)` 无 exact 候选 | ✅ |
| 3 | `test_post_hoc_hash_injection_rejected:483` | [r2] | blind prompt/output payload 不等 → 无 blank 合格候选 | ✅ |
| 4 | `test_crlf_pollution_fails_closed:531` | [r2] | blind CRLF → skip → 无 blank 合格候选 | ✅ |
| 5 | `test_duplicate_review_target_block_rejected:572` | [r2] | blind 2 个 review-target → skip → 无 blank 合格候选 | ✅ |
| 6 | `test_payload_referencing_missing_material_id_fails_closed:918` | [r2] | payload locator `r99`/hash `0…0` 不绑 r2 → 无合格对 | ✅ |
| 7 | `test_only_metadata_only_terminals_gate_fails_closed:1087` | [r2] | 全 metadata-only → 无 exact 候选 | ✅ |
| 8 | `test_qualifying_candidate_with_mismatched_payload_hash_fails:1117` | [r2] | blind material hash 不匹配 → skip → 无 blank | ✅ |
| 9 | `test_only_stale_pair_fails_closed:1304` | [r2(旧), r3(current)] | `rev_cur=r3`→`blocks=[r3]`、`hist=[r2]`；`require_full_pair(r3)`，pair 锚 r2 → 无合格对（"no qualifying pair"/"stale material"） | ✅ |
| 10 | `test_qualifying_pair_with_non_executable_verdict_fails:1372` | [r2] | outer verdict=`阻断需修复` + 正向 `verdict == 可执行` → fail | ✅ |

**正例不反转复核**（A-12/A-16 可达）：`test_two_distinct_same_hash_reviewers_pass:443`（[r2]→full-pair 通过）、`test_three_material_blocks_payloads_reference_last_passes:908`（[r2,r3,r4]→`rev_cur=r4`、`hist=[r2,r3]` 段首均缺省 decisional、`require_full_pair(r4)` 通过）、`test_superseded_block_plan_mismatch_ignored_when_payloads_name_current:975`、`test_legacy_metadata_only_terminals_skipped_gate_passes:1075`、`test_stale_pair_skipped_current_pair_qualifies:1292`（`rev_cur=r3`、当前对锚 r3）、`test_existing_material_tests_still_pass:1421`——均仍 `rc=0`。`test_find_material_block_no_id_returns_last_block:956` 直调 `_find_material_block`，其语义按 F1:263 不变。

**结论**：R2-BLK-1 的真正病灶（candidate-3:157-158 过滤空 → 静默 `return` 的整门 fail-open）已被消除；A-19 的 10 条 `rc≠0` 声明成立。

---

## 四、R1 处置抽查清单（BLK-1..4 + NB-1..6，回 plan 原文）

> 依据 `round-1.md` 第四节；核 candidate-4 未破坏各落点。

| ID | R1 单选修法摘要 | candidate-4 落点（实核） | 结论 |
|---|---|---|---|
| BLK-1 | 删"前 8/后 4"域约束与错误括注；唯一域门=非空∧⊆12 项；拦截改并集交集 | §3.2:124-126；§3.5:178-179、221-222；A-10:318；§11:374 | **未破坏** |
| BLK-2 | 完全旧块绕过 `changed_sections`/`decisional_anchors` 域门 | §3.5:171-175（`if "change_class" not in b: … continue`）；§3.1:116；§3.7:239 | **未破坏** |
| BLK-3 | legacy full-pair 含 legacy 块自身 | §3.5:201-204（`for j in (legacy .. len(blocks)-1)`）；§12.1:406；§12.4:427；§12.5:435 | **未破坏** |
| BLK-4 | 伪代码统一 `cur(b)=candidate_plan or candidate_artifact` | §3.5:152/167/192/213/216-217；§3.4:137-139；A-6:314；A-11-2:372 | **未破坏** |
| NB-1 | A-13 按 §12 逐项三态 | A-13:321（12.0/12.1-replace/12.2/12.3/12.6/12.7/12.8=replace；12.4/12.5=append；12.1-bullet=新增） | **未破坏** |
| NB-2 | 删 `if not D` 死分支；修 §12.4/12.5 措辞 | §3.5:207（`assert D`）；§12.4:427、§12.5:435 无"全 non-decisional 回退" | **未破坏** |
| NB-3 | reopen 跨 revision 分段 | R1 原写法（`_detect_revision_id` 过滤）被 R2-BLK-1 证伪并**整体替换**为 `rev_cur=末块所属段`（§3.5:147/155-164）；分段要求现由 R2 语义满足 | **已按 R2 重落地** |
| NB-4 | 伪代码补 full-pair 正向 verdict + 禁 delta | §3.5:190-199（`"delta" not in payload` + 两 verdict `== "可执行"`） | **未破坏** |
| NB-5 | 常量单源命名并锚定 F6 | §3.5:150-152（`MATERIAL_CHANGE_CLASSES`/`MATERIAL_SECTION_VOCAB`/`cur()`）；F6:268；A-5:313 | **未破坏** |
| NB-6 | `scripts/README.md:17` 随分级同步 | §12.8:451-454；F7:269；A-13:321 | **未破坏** |

---

## 五、UV 三票处置抽查表（≥8 条回 plan 原文；核 candidate-4 未破坏）

| # | 原 issue（票） | candidate-4 落点（实核行号） | 抽查结论 |
|---|---|---|---|
| 1 | uv1-B1 / uv3-01 交集恒空、哨兵反向 | §3.2:124-126；§3.1:116（"无 `["*"]` 哨兵"）；§3.5:171-175/221-222 | **已闭合**（域门 12 项 + 并集交集；哨兵已废） |
| 2 | uv1-B2 / uv2-I-1 (`["*"]`) | §3.1:116；§3.5:201-204 | **有效**（legacy 含自身 full-pair） |
| 3 | uv1-B3 full-pair 比较目标 | §3.5:190-199 `require_full_pair(T)` 三重锚定 + 禁 delta + 正向 verdict | **有效** |
| 4 | uv1-B4 / uv2-I-4 / uv3-09 delta 未锚定 | §3.5:212-218（artifact/material_revision/locator 三重 + `delta.*`）+ A-11-13:383 | **有效** |
| 5 | uv1-B5 / uv3-05 / uv3-07 标题+词表+README | §12.0:394-397；§12.3:415-418；§12.4:420-427（完整 12 项，F11 逐字核）；§12.7:444-449 | **有效**；指针目标真实存在 |
| 6 | uv1-B6 / uv3-06 record-only 无验收/序列 | §4.1:250；§6:290-297；A-R1..A-R3:328-330 | **有效**（3/3 `需重新设计` 为逐字机械判据） |
| 7 | uv1-B7 / uv2-I-7 / uv3-08 "7→17" | §2.5:99-100（4 类 17 条 + 行号） | **有效**（AST 实核 17） |
| 8 | uv2-I-3 / uv3-03 verdict 正向 | §3.4:141；§3.5:198/220；A-9:317；§11:379 | **有效**（含 `需重新设计`/缺失/变体） |
| 9 | uv2-I-5 / uv3-02 非空/域校验、漏报 anchors | §3.5:177-185；§10 R-1:358；A-11-10/11:380-381 | **有效** |
| 10 | uv3-04 diff 无数据供给 | §3.4:142（诚实声明"无 base 快照仓、不计入机械闭环"）；§8.7:342；§10 R-2:359 | **有效**（如实残余，非机械闭环） |
| 11 | uv3-05 词表未落第三部/指针悬空 | §12.1:405-406（指针）+ §12.4:427（完整 12 项全文） | **有效** |
| 12 | uv3-12 legacy 行号 | §2.2:73（`:1215-1218`/`:1235-1238`；`:1204-1205` 标 terminal 缺失） | **有效**（逐行实核 F8） |
| 13 | uv3-13 comparison 措辞 | §14:470（mechanism 置 null；schema 允许非 null 但不被数值门裁决） | **有效** |
| 14 | uv3-14 死代码 | §3.5:206-208（`D=[…]; assert D`） | **有效** |
| 15 | uv3-16 规范性句子=decisional | §3.2:122；§12.4:426 | **有效** |
| 16 | uv3-15 A-1/A-4 口径 | A-1:309（≤46080）；A-4:312（fenced-json 解析计数，非字符串 grep） | **有效** |
| 17 | uv2-I-10 "唯一块"措辞 | §12.1:404（"locator 以 `id=` 唯一寻址…可多枚，链读全部块"） | **有效** |

**抽查结论**：candidate-4 未破坏任何已闭合的 R1/UV 处置；词表单源、命名统一、残余坦承均保持。

---

## 六、逐条 issue

> 未发现阻断级。以下为精度/可判定性级（非阻断），可作实施约束。

**R3-1｜A-19 第 10 条测试符号名不精确（缺 `_fails`）**
- severity: `implementation`（精度）
- 位置：`plan.md:327`（`test_qualifying_pair_with_non_executable_verdict:1372`）
- 事实：实际测试方法为 `tests/test_loop_a_coverage.py:1372` 的 `test_qualifying_pair_with_non_executable_verdict_fails`；A-19 所写符号在仓库中不存在（行号 1372 可唯一消歧，行为断言不受影响）。
- 单选修法：把 A-19 该条符号改为 `test_qualifying_pair_with_non_executable_verdict_fails:1372`（其余 9 条符号/行号已逐条实核精确）。

**R3-2｜F8 目标文件在 HEAD 下 untracked，致 §13.3 回滚命令失效、A-14 对 F8 不可判定**
- severity: `structural`（非阻断；不影响机制正确性）
- 位置：`plan.md:270`（F8）、`:322`（A-14）、`:462`（§13.3）
- 事实：`docs/plans/active/` 未被 git 跟踪（`git ls-files docs/plans/active/` 空；`git status --porcelain` = `?? docs/plans/active/`）。故 §13.3 `git checkout -- docs/plans/active/20260911-converge-operational-envelope.md` 必失败；A-14 的 `git status --porcelain` 在编辑前后都显示同一 `??`，无法证明 F8 被触达。A-18 已显式限定 F1-F4，故不受影响。
- 单选修法：F8 落地前先将伞形计划纳入跟踪（`git add`）或先备份原文件；A-14 的 F8 判定改为内容型（复用 P5 的"O6 行含重评结论+机制实现"grep），不依赖 `git status`。

**R3-3｜§3.4 与 §3.5 对 delta reviewer 角色口径宽窄不一**
- severity: `implementation`（精度）
- 位置：`plan.md:136`（"复用 `outer-reviewer` 角色"）vs `:219`（`role ∈ REVIEWER_AUTHORITIES["fresh"]`）
- 事实：`REVIEWER_AUTHORITIES["fresh"]`（`model.py:92`）含 `reviewer`/`outer-reviewer`/`ultraverge-initial`，比 §3.4 的"outer-reviewer"更宽；两者均为 fresh 权威，无安全差异，但实现者会面对两种口径。
- 单选修法：统一为 `outer-reviewer`（与 §3.4 一致、更可审计），或把 §3.4 改为"复用 fresh 角色集合（推荐 outer-reviewer）"。

**R3-4｜A-5"`grep change_class` 命中缺省"判定形态偏软**
- severity: `implementation`（可判定性）
- 位置：`plan.md:313`（A-5）
- 事实："grep change_class 命中缺省"未给出具体断言对象（命中哪个默认分支/常量），机械可判定性弱于同表其余条目。
- 单选修法：写死为静态断言——`orchest.py` 中 `_validate_material_gate` 含 `b.get("change_class", "decisional")` 形态的缺省处理（或 `MATERIAL_CHANGE_CLASSES` 常量 + 缺省分支），与 F6 新增静态断言同源。

**R3-5｜§3.1 anchors 类型列"非空"与缺失=legacy 语义存在字面张力**
- severity: `wording`
- 位置：`plan.md:114`
- 事实：类型列写"string 列表（非空、⊆ 12 项词表）"，语义列写"缺失按 legacy 兼容"——"非空"未覆盖"缺失"这一第三种状态。R2-NB-2 已选定缺失=legacy，语义正确，仅字面需收口。
- 单选修法：类型列改为"string 列表（⊆12 项词表；出现时非空）"，或注明"缺失≠空：缺失走 legacy，空才 `anchors-vocab`"。

**R3-6｜§3.6"归类争议 → FAIL_CLOSED"为流程级、无机械检测点**
- severity: `implementation`（残余，非本轮新增）
- 位置：`plan.md:234`（§3.6 fail 条件列表含"归类争议"）
- 事实：§3.5 无"争议"的机械输入（争议由 reviewer 提出），该条依赖 agent 判断执行；与 §1:42/§10 R-1/R-6 的诚实定位一致，非虚假机械闭环。
- 单选修法：将该条文字标注为"流程 fallback（复核者挑战触发；机械层不检测）"，与 §3.2:128 表述同源，避免被误读为机械门。

---

## 七、对抗面复核（§11 封死性，含 R2 修复后的新面）

| 攻击 | 是否封死 | 依据 |
|---|---|---|
| 谎报 non-decisional + diff 触及 decisional（A-11-1） | **是（条件成立时）** | delta reviewer 正向 `verdict == 可执行`（§3.5:220）；语义 diff 由 reviewer 承担（R-2 残余） |
| 伪造 `base_plan_sha256`（A-11-2） | **是** | 比对 `cur(blocks[j-1]).sha256`（§3.5:216） |
| 链中删块（A-11-3） | **是（朴素删块）** | 后继块 base 与新前块不符 → fail；若攻击者同时重签 reviewer 则落入 R-2 语义残余 |
| decisional 误标 + `changed_sections` 含 decisional 章节（A-11-4） | **是** | 并集交集 fail-safe（§3.5:221-222/A-10），且域门已放宽为 12 项，交集可触发 |
| `change_class` 非法枚举/变体（A-11-10） | **是** | 域门 `∈ MATERIAL_CHANGE_CLASSES`（§3.5:177） |
| `changed_sections` 空/词表外（A-11-11） | **是** | 非空 + ⊆VOCAB 门（§3.5:178-179） |
| verdict 造假含 `需重新设计`/缺失/变体（A-11-9） | **是** | full + delta 均正向 `== 可执行`（§3.5:198/220） |
| payload/输出回显不一致（A-11-6） | **是** | byte-equal（§3.5:196/219） |
| 旧 decisional 缺 anchors 后继走 delta（A-11-12） | **是（保守）** | legacy 自其起 full-pair（§3.5:181-185/201-204）；不硬断言专用码（R2-NB-1(b)） |
| delta payload artifact/material_revision/locator 不绑 target（A-11-13） | **是** | 三重块锚定（§3.5:213-214） |
| **`revision_id` ≠ 末块段（R2-BLK-1 新面）** | **已封死** | 段由末块 `revision_id` 界定，不存在过滤致空 `return`；历史段仅段首校验（§3.5:155-164） |
| decisional 低报 `decisional_anchors`（A-11-14） | **否（固有残余，如实声明）** | §10 R-1/R-6；机械层只封"如实声明下的违规" |

结论：R2-BLK-1 引入的整门 fail-open 已消除；除如实声明的语义残余（A-11-14 / R-1 / R-2 / R-6）外，§11 机械对抗面成立。

---

## 八、机器块与治理要件复核

- **preflight 真实**：独立复跑与 `attempts.md:269-274`、`repair-report-c4.md:74-76` 一致（`WARN:code_heavy:2,126` + `PREFLIGHT_OK:governance-change`，EXIT=0）。
- **calibration**：locator `attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration]` 解析成功；canonical sha256 `16ec2455…`、`corpus_digest=3627eb4d…`、`freshness` 三键独立复算吻合；`evidence/` 不被 preflight 校验（`_ROOT_ALLOWLIST` 实核）。
- **user_message_events 跨对象**：`budget_gate.py:1668-1679` 仅 UUID 格式校验；两个 B 对象事件 UUID 计划已如实披露并给后补路径——**接受，非伪造**；建议 retrospective 显式落账。
- **A-4 口径**：解析器计数 == 1，字符串出现 5 次，口径正确。
- **A-17**：§14 `numeric_changes` 3 条全 `kind: mechanism`、`comparison: null`；`budget_gate.py` 无改动。
- **D2 分流可判定性**：§4.1 以三名初审 `3/3 需重新设计` 逐字为 record-only 机械判据；实际三票均为 `阻断需修复` → 落 §4.3 标准修复循环（本 candidate-4 即此）；§4.2/§4.5 引 `SKILL.md:169-171` 多数/升级规则属实。可判定。

---

## 九、实施前必须满足的前置条件清单（verdict = 可执行）

均为**实施约束**（非阻断），建议并入 executor 约束清单：

1. **R3-1**：落地 A-19 时把第 10 条符号补正为 `test_qualifying_pair_with_non_executable_verdict_fails:1372`（其余 9 条已精确）。
2. **R3-2**：F8 落地前将 `docs/plans/active/20260911-converge-operational-envelope.md` 纳入跟踪或备份；A-14 对 F8 改用内容型判据（P5 grep），勿依赖 `git status`。
3. **R3-3**：统一 delta reviewer 角色口径为 `outer-reviewer`（或明确 fresh 集合）。
4. **R3-4**：把 A-5 的"grep change_class 命中缺省"写死为具体静态断言（与 F6 同源）。
5. **R3-6**：§3.6"归类争议 → FAIL_CLOSED"标注为流程 fallback，避免误读为机械门。

---

## 十、D1 方向是否成立

**成立（是）。** 理由：

1. 成本问题有活体证据（B `retrospective.md:75/:80`：41KB→133KB、7 次重认证 ≈ 半数评议成本），议题出处 `docs/plans/active/20260911-converge-operational-envelope.md:25` 实核（F16）。
2. 三段式认证语义自洽：`decisional` 保留全量双权威不放宽（§3.3:132）；`non-decisional` 降为单 fresh delta，以"最近 decisional 全量对（锚定其候选字节）+ 其后逐块 delta（前块→本块 hash 链）+ 并集交集 fail-safe + 正向 verdict"归纳认证最终字节；被更晚 decisional 块覆盖的中间 non-decisional 块无需单独 delta，不破安全。
3. candidate-4 对 R2 的 1+3 条 issue 全部按单选修法落地，且对 R-1/R-2/R-6 语义残余如实声明，不伪造机械闭环——符合"契约违反 fail-closed、判断分歧交语义"的边界。

**判为 `可执行` 而非其他**：R2 的唯一阻断（`_detect_revision_id` 过滤致整门 fail-open + 10 条既有负例反转）已由 `rev_cur = 末块所属段` 消解并经 10 条逐案推演验证；余项（R3-1..R3-6）均为精度/可判定性级，不动摇 D1 方向与 §3.5 的机械不变量，可转入实施约束清单由实施后独立 fresh 审计兜底。

---

## 十一、无法核实的断言清单

1. **§3.5 全部门禁新行为**（链回溯、`require_full_pair(T)`、delta 候选、并集交集、错误码）与 A-5..A-19、A-15 均**待实现**；本报告以逐条静态推演证明 R2-BLK-1 已消解、10 条既有负例仍 `rc≠0`、7 条正例仍 `rc=0`，但未运行改造后代码。
2. **A-19/A-12/A-16 的最终通过**须在 implement P3/P4 由实跑 pytest 确认（当前基线 60 passed 仅为未改造态）。
3. **OCSR 派发层能否在 `--evidence-mode exact` 下为 delta reviewer 正确采集 prompt/output blob**，需实现后验证（与 R-2 残余相关）。
4. **B 对象"7 次重认证≈半数评议成本"**（`retrospective.md:80`）为该对象自报估算，仅核对引文存在，未复核底层派发记账。
5. **D2 三种分流结果的实际触发分布**属未来事实；本对象三票 verdict 已实核为 `阻断需修复`，故落 §4.3，但后续轮次走向不可提前核实。
6. **§14 `user_message_events` 两 UUID 的后续后补**（升级为"本对象事件流内存在"时）依赖编排层路径，当前不可核实。
7. `archive:done/20260911-op-envelope-b-contract-correction` 仅过格式校验（`budget_gate.py:1450`），preflight 不做存在性核验；其实存已实核。
8. **F8 目标文件纳入跟踪的时点**（R3-2）依赖落地 executor 的 git 操作，当前不可核实。
terminal_decision_event_id: 6b3e306a-39e8-4ebd-9b1a-18f35c534f1d
terminal_decision_value: 可执行
