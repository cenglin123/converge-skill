---
round: 3
reviewer_backend: opencode
reviewer_instance_id: 20260912_165518_d1087e
generated_at: 2026-09-12T09:00:27.474041+00:00
verdict: 阻断需修复
---
verdict: 阻断需修复

# uv-init-3 · O6 material 增量复核机制（candidate-1）初审

> Reviewer：ultraverge 初审 #3（fresh、独立上下文；未读取 uv-init-1.md / uv-init-2.md 正文）。
> 受审对象：`.converge/active/20260912-o6-material-delta-recert/plan.md`（candidate-1，30961 bytes）。
> 口径：只读实核 + 实跑 preflight；行号/符号全部实开核对。本报告是本对象唯一由我写入的文件。

## 0. 事实核验摘要（实开结果）

| 断言 | 核验 | 结论 |
|---|---|---|
| plan.md 30961B ≤ 46080 | 实算 | ✓ |
| A-3 preflight 实跑 | `python scripts/budget_gate.py preflight --plan <plan>` → `WARN:code_heavy:2,72` + `PREFLIGHT_OK:governance-change`，EXIT=0 | ✓ 复现，与 attempts.md:55-61 一致 |
| calibration 机器块 | fence 内 canonical 与 `evidence/calibration-report.json` 逐字节一致；sha256 `16ec2455…`；corpus 20 全 `no_sample`；eligible=0；freshness 三键 | ✓ |
| `user_message_events` 两个 UUID | B 对象 `evidence/events/00000049-…json`、`00000010-…json` 均存在且为 `user-message`；budget_gate 仅 UUID 格式校验（`scripts/budget_gate.py:1668-1679`） | ✓；跨对象引用当前被接受，计划 §14 fallback 披露属实 |
| 代码锚点 `:1095/:1133/:1171-1175/:1267-1272/:1273-1293/:1303-1310/:1335-1337/:1340-1361/:1579-1581` | 逐点实开 | ✓ 全部准确 |
| `budget_gate.py:1682-1699` / `:1710-1742` / `:1452-1459` / `:1668-1679` | 实开 | ✓ |
| B 成本证据 `retrospective.md:42/:53/:75/:80` | 实开 | ✓ 引文逐字正确 |
| §12 五处"原文" | 与 `state-schema.md:103/:104`、`orchestrator-guide.md:23/:32`、`SKILL.md:462` 逐字比对 | ✓ 原文准确 |
| `ultraverge_min_reviewers=3`、critical 20/30、`_budget-state.json` | 实开 | ✓ |
| **"现有 7 个 material 测试"** | 实开统计：4 个 `TestMaterial*` 类、17 个 test 方法（443/452/464/483/531/572/908/918/956/975/1075/1087/1117/1292/1304/1372/1421） | ✗ **事实错误**（见 UV3-08） |
| **§14 "comparison 对 mechanism 必须为 null"** | `budget_gate.py:1467/1594`：`_GOV_COMPARISONS={outer,blind,None}`，mechanism 未强制 null | ✗ **事实错误**（见 UV3-13） |
| **§2.2 "legacy 跳过 :1204-1205"** | `:1204-1205` 是 terminal-None 跳过；真正 legacy skip 在 `:1215-1218`（blob）与 `:1235-1238`（evidence_mode） | ⚠ 行号失准（见 UV3-12） |

## 1. 前置自检（Q1-Q5，`refs/reviewer-discipline.md:7-13`）

- **Q1 产物身份自洽**：基本自洽——"重评 + 条件实现"贯穿 Goal/§4/§6。但 §7 Acceptance（隐含"必实现"）与 §4 D2（允许 record-only）身份冲突：同一产物同时是"实现计划"和"条件性记录"。→ **否**，列 UV3-06。
- **Q2 产物边界诚实**：对残余（R-1 语义漏报）已如实声明"不声称机械闭环"，诚实。但 §1 成功判据"以 hash 链 + delta payload + verdict 三重机械校验替代第二权威"对"机械"的宣称超过实现（verdict 仅脆弱的字面量正则、diff 无数据供给）。→ **边界夸大**，列 UV3-03/UV3-04。
- **Q3 产物数据纯度**：纯机制，无业务数据硬编码。→ 通过。
- **Q4 职责边界自洽**：作者声明 `change_class`/`changed_sections`/`decisional_anchors`、reviewer 挑战"归类是否正确"、材料门做交集——但交集的两个操作数**都由作者声明**，"机械拦截"实为"自证"。谁来验证"未触及 decisional"没有闭环：delta reviewer 的语义 diff 无机械校验，且其 verdict 只被检查"≠阻断需修复"。→ **否**，列 UV3-04/UV3-16。
- **Q5 命名一致性**：`candidate_artifact`（§3.5:147/157/158）与代码同时接受 `candidate_plan`（`orchest.py:1171`）不一致；`decisional_anchors` 的 `["*"]` 哨兵在语义与算法间不一致（见 UV3-01/UV3-14）。→ **否**，列 UV3-01/UV3-14。

> Q6（背景材料一致性）：无独立背景材料，不触发。

## 2. DR 7 维逐维结论

- **DR1 一致性（concerns_found）**：§12.3/§12.4 是"保留原句+追加"但 A-13 要求"旧句消失"（自相矛盾）；§12.1 新 bullet 把"受控词表"指向 `orchestrator-guide.md §Material revision`，而 §12.3/§12.4 未写入该表（悬空引用）；"7 个测试"与 "comparison 必须 null" 与事实不符。→ UV3-05/UV3-07/UV3-08/UV3-13。
- **DR2 完整性（concerns_found）**：受控章节词表只存在于 plan 散文，未进第三部也未进机器校验；delta reviewer 的 diff 输入无来源；D2 否定路径的 Acceptance 缺失；§11 对抗清单缺口（见 UV3-11）。→ UV3-01/02/04/05/06/11。
- **DR3 可维护性（concerns_found）**：`change_class`/`changed_sections`/`decisional_anchors` 由 orchestrator 手工写入 `attempts.md`，全仓无生成器、无 schema 校验器（`rg material-revision scripts/` 仅 `_find_material_block`）；新增字段的域约束会长期靠人记。→ UV3-02。
- **DR4 职责边界（concerns_found）**："归类争议=decisional"（§3.2/§3.6）只有流程语义、无机械检测点；分类权与验证权在闭环上重叠于作者声明。→ UV3-04/UV3-16。
- **DR5 残留与冗余（concerns_found）**：§3.5:154 的 `if blocks[j].change_class == decisional: continue` 在 `i=max decisional` 下是死代码，暴露旧"最后一块"语义与新"全链块"语义并存的认知残留。→ UV3-14。
- **DR6 可移植性（clean）**：无环境特定硬编码；仓库路径仅作为引用。无问题。
- **DR7 可扩展性（minor concerns）**：链回溯 O(n) 可接受；但 `changed_sections`/`decisional_anchors` 若词表不落机器契约、随对象增长将失去可比性，交集语义无法审计。→ UV3-05。

## 3. Issues（编号 · severity · 位置 · 单选修法）

### UV3-01 · conceptual · `plan.md:104,106,162`
**`decisional_anchors` 缺省 `["*"]` 与集合交集算法矛盾，所称"保守 fail-closed"实际是 fail-open。**
伪代码唯一判定是 `blocks[j].changed_sections ∩ blocks[i].decisional_anchors == ∅`。当旧 decisional 块缺省为 `["*"]` 时，与任意非空 `changed_sections` 的交集都是 **∅**（`"*"` 是字面串，不是通配符），于是旧块之后的 non-decisional delta **被放行**——与 §3.1"任何 non-decisional 变更都会触发交集非空 → 保守 fail-closed 到全量对"完全相反。这是本设计"链式不变量"的根基漏洞。
**单选修法**：在 §3.1/§3.5 明确定义哨兵语义并把判定改为 `if "*" in anchors or (changed_sections & anchors): FAIL_CLOSED`；或把旧块缺省改为受控词表**全量集合**（使交集恒非空）。二选一，且必须写进 §3.5 伪代码与 §12.1 规范句。

### UV3-02 · architectural · `plan.md:100-104,148-162`（`scripts/orchest.py` 无对应校验）
**新字段无域校验，非法枚举被静默当成 non-decisional 放行。**
`i = max index with change_class(default=decisional) == decisional`；循环用 `== "decisional"` 判定。`change_class="Decisional"`、`"decisional "`、`"foo"` 一律不匹配 → 按 non-decisional 处理。同理 `changed_sections=[]`（空集）与非法 `decisional_anchors` 都会让交集短路通过。计划声称"必填/非空/受控词表"，但 §3.5 无任何一项机械校验。
**单选修法**：在任何分支前加字段域门——`change_class ∈ {decisional,non-decisional}` 否则 FAIL_CLOSED；`changed_sections` 非空且 ⊆ 受控词表；decisional 块 `decisional_anchors` 非空且 ⊆ 词表；任一不满足 → FAIL_CLOSED。

### UV3-03 · architectural · `plan.md:136` vs `:161`
**delta 路径 verdict 判定自相矛盾，`需重新设计` 等非"阻断需修复"verdict 会被放行。**
§3.4 要求 delta reviewer `verdict 必须为 可执行`；§3.5 却只检查 `verdict != 阻断需修复`。沿用 `orchest.py:1344-1345` 的正则，`需重新设计`、缺失 verdict、拼写变体都通过 → 相对"单权威替代双权威"的放宽，这是新增的 fail-open；§11 也未列该攻击用例。
**单选修法**：delta（以及为一致性计，full-pair）verdict 改为闭集判定，必须解析出恰好 `可执行`，否则（含缺失/其他字面量）FAIL_CLOSED；A-9 与 §11 增补"delta 返回 需重新设计"用例。

### UV3-04 · architectural · `plan.md:132-137,157-158`
**delta reviewer 的"实核 diff"无数据供给、无机械校验，职责不闭环。**
payload 只带 `base_plan_sha256`/`current_plan_sha256`；旧 plan 字节不落归档（块只存 sha256/size），材料门也无法证明 reviewer 见过 base 字节。若只把 current plan 发给 reviewer，它做的是重新全审而非 diff；若把 base 文本塞进 prompt，gate 又不校验该文本与 base hash 绑定。"实核 diff 确认未触及 decisional"是本路径唯一的语义防线，却悬空。
**单选修法**：给 delta 证据增加机器可校验的 base 绑定（如块内新增 `base_snapshot{path,sha256}` 或 `diff_artifact{sha256,size}`，以 exact 证据采集并在 gate 中比对），并规定 prompt 必含 base 内容；或明确降级宣称：delta = "单 fresh 对 current 字节的轻量复核"，不再声称 diff 实核，并如实写入残余。

### UV3-05 · structural · `plan.md:121,312,321-335`
**受控章节词表未落入任何第三部文件，且 §12.1 的引用悬空。**
§12.1 新 bullet 写"判定标准与受控词表见 `refs/orchestrator-guide.md` §Material revision"，但 §12.3（orchestrator-guide:23）只给 decisional/non-decisional 定义，§12.4（:32 后 item 7）只给流程，**均不含** §3.2 的 12 项词表与 `decisional_anchors` 语义；机器也不校验取值。第三部因此缺少交集判定的可审计基础。
**单选修法**：将 §3.2 词表与 anchors 语义逐字加入 §12.3 的新增段（或落为 `state-schema.md` 的规范表），确保 §12.1 的引用目标真实存在且同源。

### UV3-06 · architectural · `plan.md:§4` vs `§6/§7`
**D2 的 record-only 分支与 Acceptance/Bounded Sequence 未分流，否定路径不可判定。**
§4.1 允许"一致否定 → record-only，不修改 F1-F4"，但 A-6..A-18、§6 P1-P6 全以"已实现"为前提；record-only 时 A-14（`git status` 覆盖 F1-F7）必然失败。任务点 7 的"否定路径是否同样可判定"答案在此是否定的。
**单选修法**：把 §7 明确为两套（或加列"适用分支"）：实现分支用 A-5..A-18；record-only 分支用"F1-F7 零触达 + record-only 产物（修订计划 + 不实现理由）存在 + 现有 material 测试全绿"。

### UV3-07 · structural · `plan.md:244,326-327,334-335`
**A-13 "旧句消失"与 §12.3/§12.4 的"保留原句+追加"自相矛盾，非机械可判定。**
§12.3/§12.4 的新文本以原句为前缀，故"旧句"必然仍存在；A-13 无法同时成立。
**单选修法**：A-13 改为逐节三态判定——§12.2/§12.5 的**被替换子串消失**、§12.3/§12.4 的**原句子串仍在**且新增子串存在、§12.1 的 `delta` 新句存在。

### UV3-08 · structural · `plan.md:181`
**"现有 7 个 material 测试"事实错误（实际 4 类 17 个 test 方法）。**
**单选修法**：改为准确计数（`tests/test_loop_a_coverage.py:443-1430` 区间 4 个 `TestMaterial*` 类共 17 个 test 方法），或删除数字直接列类名。

### UV3-09 · structural · `plan.md:155-161`
**delta 分支未绑定 `material_revision.sha256`/locator id/`payload.artifact`，弱于既有锚点(b)(c)。**
现行 full-pair 在 `orchest.py:1267-1272`（artifact vs plan）与 `:1273-1293`（material_revision sha256 + locator id）双重绑定；§3.5 的 delta 检查只比对 `delta.declared_class/base/current`，未要求 `payload.artifact.sha256/size == blocks[j].candidate_artifact`、`payload.material_revision.sha256 == hash(blocks[j])` 与 locator id 一致。跨块重放/错位 payload 因此有空间。
**单选修法**：delta 候选校验补齐上述三项，与 full-pair 同强度。

### UV3-10 · structural · `plan.md:189-192`（`SKILL.md:169-171`）
**D2 未处理"2:1 多数否定但不是一致否定、且少数派非 conceptual/architectural"的情形。**
规则 1 要求三名一致否定；规则 2 仅覆盖"多数支持"；规则 3 仅"可执行"。2 否定 + 1 可执行落在规则空档，裁决不可判定，且与 SKILL.md 的"多数方向推进"规则不对齐。
**单选修法**：补一条——非一致时按 `SKILL.md:169-171` 多数方向推进；若少数派阻断 severity ∈ {conceptual,architectural} 则升级完整收敛；并明确 `需重新设计` 是否算方向性阻断等级。

### UV3-11 · structural · `plan.md:284-297`
**§11 对抗清单穷举缺口。**缺：① delta verdict=`需重新设计`（UV3-03）；② `change_class` 非法枚举/大小写变体（UV3-02）；③ `changed_sections` 为空（UV3-02）；④ 旧 decisional 块缺省 `["*"]` 后被 delta 放行（UV3-01）；⑤ decisional 块自身低报 `decisional_anchors` 以使交集为空（攻击点在 anchor 声明而非 changed_sections，R-1 未覆盖）；⑥ delta payload 的 `artifact`/`material_revision` 不绑定 target 块（UV3-09）。
**单选修法**：§11 追加 A-11-9..A-11-14 覆盖以上六类，并在 §7 建立一一对应断言。

### UV3-12 · implementation · `plan.md:71`
**legacy 跳过行号失准。**`orchest.py:1204-1205` 是 terminal 缺失跳过，不是 legacy 语义；后者在 `:1215-1218` 与 `:1235-1238`。
**单选修法**：改为 `:1144-1149`（docstring 语义）+ `:1215-1218`/`:1235-1238`（实际跳过点）。

### UV3-13 · implementation · `plan.md:357`
**"`comparison` 对 mechanism 必须为 `null`"与 validator 不符。**`budget_gate.py:1594` 允许 mechanism 配 `outer|blind|None`，未强制 null；窄门 `:1720-1724` 只按 kind 过滤，不裁决 mechanism。
**单选修法**：改为"本计划 mechanism 条目一律置 `comparison=null`（schema 允许非 null，但机制条目不被数值门裁决）"。

### UV3-14 · implementation · `plan.md:148,154`
**`i = max decisional` 与循环内 `if blocks[j].change_class == decisional: continue` 逻辑不一致（死代码）。**
在"i 是最后一个 decisional"定义下，j∈(i+1..) 内不可能再出现 decisional，该分支不可达；它暗示作者对"多 decisional 段"语义未定。附带后果：更早的 non-decisional 链段不被要求 delta，这与 §12.2 "链上任何一环缺失即 fail closed"的规范句不符。
**单选修法**：删除死分支，并显式写明"只回溯至最后 decisional 块，其后每块一 delta；更早块由该 decisional 全量对覆盖"，同时修正 §12.2 措辞与之一致。

### UV3-15 · implementation · `plan.md:232,235`
**A-1/A-4 计数口径未定义。**A-1 的 45KB 未定 45000/46080（plan 现 30961B 两者皆过，但判定须唯一）；A-4 的 `converge.governance-change/v1` 在 plan 文本出现 5 次（散文+代码），"计数==1"若用字符串 grep 会误判。
**单选修法**：A-1 写死 `≤46080`；A-4 写死"以 fenced-json 解析器计含该 schema 的块数 == 1（非字符串 grep）"。

### UV3-16 · conceptual（残余边界） · `plan.md:119,121,335`
**把第三部规范句的"措辞"改造归入 non-decisional，可能让治理句改写绕过双权威。**
§3.2 的 non-decisional 含"措辞"，而 §12 本次改造的对象正是 `state-schema`/`orchestrator-guide`/`SKILL.md` 的规范句。若后续对象把这类语义改动声明为 `wording`，delta 单权威即可通行。尽管可援引"归类争议=decisional"，但该 fail-safe 无机械检测（见 UV3-04）。
**单选修法**：在 §3.2 加硬约束——凡触及 `CONSTITUTION.md` 第三部清单文件的**规范性句子**一律 `decisional`；`wording/appendix/doc-refs` 仅限非规范散文。并同步 §12.3。

> 注：现有 full-pair 路径同样只拦截字面量 `阻断需修复`（`orchest.py:1344-1345`），`需重新设计` 在双权威下也会放行。本计划未引入该缺陷，但既然 §1 宣称"不放宽"，建议一并按 UV3-03 收口（可作为次优先，不单列阻断）。

## 4. D1 方向是否成立

**成立（direction：是）。** 理由：

1. 成本问题真实且有活体证据（B 对象 `retrospective.md:75/:80`：41KB→133KB、7 次重认证≈半数评议成本），O6 议题（`docs/plans/active/20260911-converge-operational-envelope.md:25`）来源准确。
2. "decisional 全量双权威不放宽 + non-decisional 单 fresh delta + 回溯至最近 decisional 块"的三段式在**认证语义上自洽**：最后一个 decisional 块的全量对直接认证其字节 P_i，其后每个 delta 绑定 P_{j-1}→P_j，故最终 plan 可归纳认证；更早 decisional 块无需复验也不破坏安全性。方向不需要推翻重来。
3. 单权威替代双权威对 non-decisional 是**有意的成本/鲁棒性取舍**，且计划对 R-1 语义残余如实声明，符合"契约违反 fail-closed、判断分歧 fail-open"的宪法边界（`CONSTITUTION.md:34`）。

但当前 candidate-1 的**机械落地不足以兑现其 fail-closed 宣称**：UV3-01/02/03 三条均为可被绕过的新增放行口，UV3-04/05/06 使"机械闭环/条件实现"不可判定。故 **verdict = 阻断需修复**，而非"需重新设计"。修复面上均为本架构内的局部补强，无方向性重写需求。

## 5. 无法核实的断言清单

1. **A-6..A-11 的行为**：新测试尚不存在，无法验证；仅能验证其描述与 §3.5 伪代码的一致性（已发现 §3.5 自身缺口，见 UV3-01/02/03/09）。
2. **F6 的"分级常量单源在 `orchest.py`"静态断言**：plan 未定义该常量名/位置，无法预判断言可写性。
3. **"17 个既有 material 测试改造后仍全绿"**：需实际实现并运行 pytest；本报告仅做逐案静态推演（现有块均缺 `change_class`→défault decisional、i=末块，推测可绿，但未运行）。
4. **delta reviewer 能否在运行时拿到前一版 plan 字节**：取决于 orchestrator 拼装 prompt 的未定行为，plan 未规定。
5. **"任一 reviewer 指出归类错误 → 按 decisional 重做全量对"（§3.2）**：纯流程约束，无签名/事件结构可机械核验。
6. `archive:done/20260911-op-envelope-b-contract-correction` 仅过格式校验（`budget_gate.py:1450`），preflight 不做存在性核验；其路径正确性依赖 B 对象归档现状（已实存 `docs/plans` 与 `.converge/done` 两处，preflight 通过）。
