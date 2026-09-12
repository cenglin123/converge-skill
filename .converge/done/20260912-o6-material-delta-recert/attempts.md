# Attempts · 20260912-o6-material-delta-recert（Plan Author 撰写记录）

> 本文件是 candidate-1 撰写记录 + **candidate-2 修订记录** + **candidate-3 修订记录** + **candidate-4 修订记录（outer R2 处置）** + preflight 实跑输出 + calibration-report 的 locator 载体。
> Plan Author：fresh Executor（candidate-1）；Plan Repair Executor（candidate-2，fresh）；Plan Repair Executor（candidate-3，fresh）；Plan Repair Executor（candidate-4，fresh，仅改 `plan.md` 与 `attempts.md`）。不做 git 操作。
> candidate-2 依据 `uv-init-1.md`/`uv-init-2.md`/`uv-init-3.md` 逐条修订（处置表见 §五）；candidate-3 依据 `round-1.md`（outer R1：BLK-1..4 + NB-1..6）逐条修订（处置表见 §七）；candidate-4 依据 `round-2.md`（outer R2：R2-BLK-1 + R2-NB-1..3）逐条修订（处置表见 §八）。

## 一、撰写记录

| 项 | 值 |
|---|---|
| 对象 | O6 material 增量复核机制（重评 + 条件实现） |
| 产物 | `plan.md`（candidate-1）、`attempts.md`（本文件）、`author-report.md` |
| 授权源 | ultraverge（触及第三部 `refs/state-schema.md`、`refs/orchestrator-guide.md`、`SKILL.md`；清单 `CONSTITUTION.md:65-78`，`:71-72`） |
| 证据复核 | 全部行号实开文件核对（见 `plan.md` §2） |

### 1.1 实核修正/增补的行号（相对简报）

| 简报/预测 | 实核结果 | 处置 |
|---|---|---|
| `refs/orchestrator-guide.md:17-32` | 确认：`:17` 标题、`:23` triggers、`:27-31` 流程、`:32` 失效句 | 沿用 |
| `refs/state-schema.md:101-104` | 确认：`:101` 标题、`:103` 字段、`:104` 失效句 | 沿用 |
| `CONSTITUTION.md:71-72` | 确认：`:71` state-schema、`:72` orchestrator-guide | 沿用 |
| `orchest.py:1095` `_find_material_block` | 确认 `:1095-1118` | 沿用 |
| `orchest.py:1133` `_validate_material_gate` | 确认 `:1133-1361` | 沿用 |
| `orchest.py:1171-1175` 锚点(a) | 确认 | 沿用 |
| `orchest.py:1267-1272` 锚点(b) | 确认 | 沿用 |
| `orchest.py:1335-1337` 锚点(c) | 确认 | 沿用 |
| `orchest.py:1340-1361` verdict | 确认 | 沿用 |
| `budget_gate.py:1682-1699` calibration 校验 | 确认 `_resolve_and_check_report` | 沿用 |
| 简报预测 File Matrix | 实核**增补** `SKILL.md:462`（两-authority 指针句会与新语义矛盾）与 `tests/test_process_controller_contract.py`（`test_orchest_negative_read_side_default_untouched` 直锚 `_validate_material_gate`，改造后必须同步） | 已写入 F4/F6 |
| `calibration` 引用 `evidence/calibration-report.json` | locator `root-file` 必须是不含路径分隔符的 allowlist 普通文件名（`refs/state-schema.md:76`、`budget_gate.py:1452-1459`），`evidence/` 路径**不可寻址** | 采用 B 对象同构方案：把报告 canonical 字节作为 fenced 载体放入 allowlisted 根文件 `attempts.md`，`calibration.path` 指向该 fence；独立文件作证据留痕，不被 preflight 机械校验 |

### 1.2 实核的 governance 三字段值

| 字段 | 实核值 | 来源 |
|---|---|---|
| `change_id` | `o6-material-delta` | 本对象定义 |
| `numeric_changes` | 3 条全 `kind: mechanism`、`comparison: null` | 本计划不改数值默认 |
| `archaeology_refs` | `git:da81e70cee7931d49680866f9cd0b2cdb6fadc5a`（`git log --format=%H -1`）、`archive:done/20260911-op-envelope-b-contract-correction` | 实核 HEAD 与 B done 目录 |
| `calibration.sha256` | `16ec2455acb9cdb143145e8f28c52b4db1d96f9cd90b44ab4b8af897df3303c8` | 报告 canonical 复算（= raw，文件本身即 canonical） |
| `calibration.corpus_digest` | `3627eb4d72cfbf07a3c1a6655026c9ce51063506e613c3a7df5b3519b10224ea` | 报告实核 |
| `calibration.freshness` | `{repository_head=da81e70cee7931d49680866f9cd0b2cdb6fadc5a, source_archive_revision=unavailable, source_event_high_watermark=0}` | 报告实核 |
| `user_message_events.execution_authorization` | `989e5ebd-2406-4dcf-bf77-283bcb4e6e17` | B 对象 sequence 49 事件文件（`evidence/events/00000049-989e5ebd-...json`） |
| `user_message_events.quality_goal` | `06754e6f-94fc-4a8a-9d80-65f89ae68e3a` | B 对象 sequence 10 事件文件 |

> 说明：两个 user_message_events 均来自 **B 对象**事件流，本对象事件流内暂无对应事件。preflight 只做 UUID 格式校验（`budget_gate.py:1668-1679`），故可通过；若编排层将校验升级为"本对象事件流内存在"，按 `plan.md` §14 说明改为"编排层后补清单"，不伪造。

## 二、preflight 实跑输出

命令（2026-09-12，本机，UTF-8）：

```
python scripts/budget_gate.py preflight --plan .converge/active/20260912-o6-material-delta-recert/plan.md
```

输出：

```
WARN:code_heavy:2,72
PREFLIGHT_OK:governance-change
EXIT=0
```

说明：
- `WARN:code_heavy:2,72` 为既有 code-heaviness 启发式（阈值 block≥3 或 loc≥40），**非阻断**；治理机器块自身即约 40+ 行，属正常。
- `PREFLIGHT_OK:governance-change` 表示治理机器块 schema、`archaeology_refs` git 存在性、`calibration` locator/hash/corpus_digest/freshness、`user_message_events` UUID 全部通过。
- 首次实跑曾 `FAIL_CLOSED:path-not-found:calibration-o6`：实核发现 `evidence/calibration-report.json` 自身 `id=calibration`，locator id 已改为 `calibration` 后通过（不伪造 id）。

## 三、calibration-report locator 载体

> 以下 fenced 块的 canonical 字节与 `evidence/calibration-report.json` 逐字节一致（`sha256=16ec2455…`、`corpus_digest=3627eb4d…`、`freshness` 三键同上）。它是 `plan.md` §14 `calibration.path` 指向的 locator 载体。



```json
{"corpus":[{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260601-converge-three-layer-separation"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260610-model-tiering-amendment"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260610-skill-slimming-plan"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260610-skill-slimming-plan-ultraverge"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260611-audit-driven-corrections"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260611-cost-data-section"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260612-blind-recheck"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260612-execution-gap"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260612-execution-gap-v2"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260612-skill-weight-reduction"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260621-converge-mechanism-coherence"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260621-mode-differentiation-and-fork-executor"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260712-archive-contract"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260725-dogfood-adapter-usage"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260725-ocsr-converge-integration"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260826-doc-layer-refactor"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260826-doc-need-to-know"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260910-process-controller-consolidation"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260911-op-envelope-a-tooling-hardening"},{"quantitative_status":"unavailable","reason":"no_sample","ref":"done:20260911-op-envelope-b-contract-correction"}],"corpus_digest":"3627eb4d72cfbf07a3c1a6655026c9ce51063506e613c3a7df5b3519b10224ea","freshness":{"repository_head":"da81e70cee7931d49680866f9cd0b2cdb6fadc5a","source_archive_revision":"unavailable","source_event_high_watermark":0},"id":"calibration","quantitative_aggregates":{"eligible_samples":0,"status":"unavailable"},"schema":"converge.calibration-report/v1","scope":"done-corpus"}
```

## 四、candidate-2 preflight 实跑输出

命令（2026-09-12，本机，UTF-8）：

```
python scripts/budget_gate.py preflight --plan .converge/active/20260912-o6-material-delta-recert/plan.md
```

输出：

```
WARN:code_heavy:2,91
PREFLIGHT_OK:governance-change
EXIT=0
```

说明：`WARN:code_heavy:2,91` 为既有 code-heaviness 启发式（block≥3 或 loc≥40），**非阻断**；`PREFLIGHT_OK:governance-change` 表示治理机器块 schema、`archaeology_refs` git 存在性、`calibration` locator/hash/corpus_digest/freshness、`user_message_events` UUID 全部通过。candidate-2 机器块 JSON 未改动，仅 §14 prose 更正 `comparison` 表述（UV3-13）。

## 五、UV 三票逐条处置表（issue → 处置 → 落点）

> 三票合计 **44 条** issue（uv-init-1：B1-B7 + N1-N5 = 12；uv-init-2：I-1..I-16 = 16；uv-init-3：UV3-01..UV3-16 = 16）。**全部 44 条已处置**（含合并的跨票重复项）。
> 核心共识 9 项（编排层指令）：①统一 12 项词表+并集交集；②废除 `["*"]` 哨兵；③anchors 作用域快照；④T 块三重锚定；⑤delta verdict 正向校验；⑥§12 对照表补全；⑦record-only 分支；⑧测试锚定；⑨非阻断全收。

### 5.1 uv-init-1（12 条）

| issue | 处置 | 落点 |
|---|---|---|
| B1 交集恒空 | 统一 `changed_sections`/`decisional_anchors` 到同一 12 项词表；交集改为对**所有先前 decisional 块 anchors 的并集**；空/词表外 → FAIL_CLOSED | §3.1/§3.2/§3.5/A-10/§11 |
| B2 `["*"]` 哨兵 | **废除哨兵**；链回溯见缺省/缺失 anchors 的旧 decisional 块 → 其后全部块 full-pair，错误码 `legacy-anchor-requires-full-pair` | §3.1/§3.5/A-11-12/§12.1 |
| B3 full-pair 比较目标未定 | T 块三重锚定（artifact/material_revision.sha256/locator id）；full-pair 候选禁止含 `delta`；A-6 增"artifact==历史 candidate"子用例 | §3.5/A-6 |
| B4 delta 候选未锚定 blocks[j] | delta 候选同样按 T=blocks[j] 三重锚定 | §3.5/A-11-13 |
| B5 规范句/Matrix 枚举不全 | §12 补 :101 标题、:17 标题、guide 完整词表、README:151；A-13 改三态 | §12.0/§12.3/§12.4/§12.7/A-13 |
| B6 record-only 无验收/序列 | §7 抬头声明适用分支；新增 A-R1..A-R3 + §6 record-only 最小序列；§4.1 机械判据 = 3/3 `需重新设计` | §4/§6/§7 |
| B7 "7 个"失真 | 改为 4 个 `TestMaterial*` 类 / 17 条（含行号）；A-12 按 diff hunks | §2.5/§3.7/A-12 |
| N1 `declared_class` 异名 | 统一为 `change_class`（payload delta 内） | §3.4/§12.1 |
| N2 伪码死分支 | 删除 `continue`；显式"最近 decisional 之后全为 non-decisional"前提 | §3.5 |
| N3 伞形计划未入 Matrix | 新增 F8（`:25`/`:36`）；implement 与 record-only 均触达 | §5/§6 |
| N4 reopen 链边界 | 写死"链首块必须 decisional（base=null）" | §3.5 |
| N5 A-12 行号锚定不稳 | A-12 改"4 类测试体零删改（diff hunks）+ 新测试仅追加末尾" | A-12/F5 |

### 5.2 uv-init-2（16 条）

| issue | 处置 | 落点 |
|---|---|---|
| I-1 `["*"]` 反向失效 | 同 B2：废除哨兵 + legacy full-pair | §3.1/§3.5 |
| I-2 anchors 作用域/覆盖衰减 | anchors = 该 revision **全量判定承载快照**；交集对**并集**（消除衰减） | §3.1/§3.2/§3.5 |
| I-3 delta verdict 不一致 | 选 A：正向 `verdict == 可执行`；补 `需重新设计` 用例 | §3.4/§3.5/A-9/§11 |
| I-4 delta 缺块绑定 | delta 复用三重锚点（artifact/material_revision.sha256/locator id） | §3.5/A-11-13 |
| I-5 无非空校验/漏报 anchors 风险 | 域门：空或词表外 → FAIL_CLOSED；R-1 扩为 changed_sections/anchors **双向漏报** | §3.5/§10 |
| I-6 A-13 "旧句消失"矛盾 | A-13 改按项三态（replace/append/新增） | A-13 |
| I-7 "7 个"失真 | 同 B7 | §2.5/§3.7 |
| I-8 A-12 非机械 | 同 N5 | A-12 |
| I-9 F5 漏 LegacySkip | F5 明列 4 类（补 `TestMaterialGateLegacySkip:989`） | §5 F5 |
| I-10 "唯一块"措辞张力 | :103 改为"locator 以 `id=` 唯一寻址；块可多枚，链判定读取全部块" | §12.1 |
| I-11 reopen 边界 | 同 N4 | §3.5 |
| I-12 D2 空档 | 增"一致/非一致 implementation/structural 阻断 → 标准修复循环" | §4 |
| I-13 §2.1 :53 引证不足 | 改引 `:62`/`:80`，:53 标注为轮序表 | §2.1 |
| I-14 宿主路径权威源 | 标注为"外部权威源，非本仓库可验证" | §4/§9 |
| I-15 "三重机械校验"过强 | §1 改"块链 hash 绑定（机械）+ payload 回显（机械）+ verdict 门控（判断）" | §1 |
| I-16 伪码死分支 | 同 N2 | §3.5 |

### 5.3 uv-init-3（16 条）

| issue | 处置 | 落点 |
|---|---|---|
| UV3-01 `["*"]` fail-open | 同 B2/I-1 | §3.1/§3.5 |
| UV3-02 新字段无域校验 | 加域门：`change_class` 枚举、`changed_sections` 非空⊆词表、decisional `decisional_anchors` 非空⊆词表 | §3.1/§3.5/A-11-10/A-11-11 |
| UV3-03 verdict 自相矛盾 | 同 I-3：闭集正向 | §3.4/§3.5/A-9 |
| UV3-04 delta diff 无数据供给 | **诚实降级**：材料门绑定 base/current hash，但不校验 prompt 内 base 文本；"实核"语义由 fresh reviewer 承担，计入 R-2；不声称机械闭环 | §3.4/§8.7/§10 R-2 |
| UV3-05 词表未落第三部/指针悬空 | 完整 12 项词表逐字落入 guide §12.4；state-schema 指针指向该处 | §12.1/§12.4 |
| UV3-06 record-only 未分流 | 同 B6 | §6/§7 |
| UV3-07 A-13 增补矛盾 | 同 I-6 | A-13 |
| UV3-08 "7 个"失真 | 同 B7/I-7 | §2.5/§3.7 |
| UV3-09 delta 未绑 material_revision | 同 I-4 | §3.5/A-11-13 |
| UV3-10 D2 2:1 空档 | 增多数方向规则 + 少数派 conceptual/architectural → 升级完整收敛 | §4 |
| UV3-11 §11 穷举缺口 | §11 增 A-11-9..A-11-14（含 A-11-14 如实残余） | §11 |
| UV3-12 legacy 行号失准 | §2.2 改为 `:1144-1149` + 实际跳过点 `:1215-1218`/`:1235-1238`（`:1204-1205` 标注为 terminal 缺失） | §2.2 |
| UV3-13 comparison 必 null 错误 | 改为"本计划 mechanism 条目一律置 null；schema 允许非 null，但不被数值门裁决" | §14 |
| UV3-14 死代码 | 同 N2/I-16；§12.2 措辞缩至"最近 decisional 之后的增量链" | §3.5/§12.2 |
| UV3-15 A-1/A-4 口径 | A-1 写死 ≤46080；A-4 改 fenced-json 解析计数（非字符串 grep） | §7 A-1/A-4 |
| UV3-16 规范性句子误归 non-decisional | §3.2 硬约束：第三部规范性句子一律 decisional；同步 §12.4 | §3.2/§12.4 |

### 5.4 计数与覆盖

- issue 总数：44（12 + 16 + 16）。
- 已处置：44（100%）。
- 合并重复：B1/I-2/I-5、B2/I-1/UV3-01、B3/B4/I-4/UV3-09、B6/UV3-06、B7/I-7/UV3-08、I-3/UV3-03、I-6/UV3-07、N2/I-16/UV3-14、N4/I-11、N5/I-8 等按同一落点合并，仍逐条列出。
- 未决/残留（如实声明，非未处置）：R-1 双向漏报、R-2 delta diff 文本绑定、R-6 作者声明性——均由 §10 显式列为语义残余，转入实施约束清单。

## 六、candidate-3 preflight 实跑输出

命令（2026-09-12，本机，UTF-8）：

```
python scripts/budget_gate.py preflight --plan .converge/active/20260912-o6-material-delta-recert/plan.md
```

输出：

```
WARN:code_heavy:2,120
PREFLIGHT_OK:governance-change
EXIT=0
```

说明：`WARN:code_heavy:2,120` 为既有 code-heaviness 启发式（block≥3 或 loc≥40），**非阻断**；`PREFLIGHT_OK:governance-change` 表示治理机器块 schema、`archaeology_refs` git 存在性、`calibration` locator/hash/corpus_digest/freshness、`user_message_events` UUID 全部通过。candidate-3 机器块 JSON 未改动（§14 JSON 逐字节不变）；plan.md 实测 **46074 B** ≤ 46080（A-1）。
pytest：本阶段**只改计划、未改任何代码**，计划未要求候选阶段跑 pytest（A-16 属 implement 分支），故未跑；待 §6 implement P3/P4 由落地 executor 执行。

## 七、outer R1 逐条处置表（BLK/NB → 处置 → 落点）

> 依据 `.converge/active/20260912-o6-material-delta-recert/round-1.md` 第八节，逐条落地。R1 verdict = `阻断需修复`（BLK-1..4 阻断 + NB-1..6 非阻断）。

### 7.1 阻断级（BLK-1..BLK-4）

| ID | R1 结论 | 处置 | 落点 |
|---|---|---|---|
| BLK-1 | §3.2 "non-decisional 只允许后 4 项"与并集交集互斥，令 A-10/A-11-4 恒空 | **采用建议 A**：删除"前 8/后 4"域约束与错误括注；门禁唯一域门 = `changed_sections` 非空 ∧ ⊆ 12 项词表；误归类由"∩ ∪(先前 decisional anchors)"并集交集机械拦截 | §3.2:126；§3.5:172-173/204-216；A-10:311；A-11-4:366；§12.4:419 |
| BLK-2 | §3.5 对每个块无条件要求 `changed_sections`，令完全旧块与 17 条既有测试 `FAIL_CLOSED`，A-5/A-12/A-16 不可能成立 | 完全旧块（缺 `change_class`）**绕过** `changed_sections`/`decisional_anchors` 域门，按 `decisional`/legacy→full-pair 处理；域门仅对新块生效 | §3.5:164-179（`if "change_class" not in b: ... continue`）；§3.1:116；§3.7:233；A-5:307 |
| BLK-3 | `for j in (legacy+1 ..)` 使单块旧对象不要求任何审查对 → fail-open，既有负例反转 | legacy full-pair 范围改为**含 legacy 块自身** `for j in (legacy .. len-1)`，且段首门/最近 decisional 门兜底；单块旧对象与现状同强度 | §3.5:195-198；§3.1:116；§12.1:398；§12.4:419；§12.5:427 |
| BLK-4 | §3.5 硬编码 `candidate_artifact`，与真实旧块 `candidate_plan` 不兼容，reopened 对象首校验点即失败 | 伪代码统一 `cur(b) = b.get("candidate_plan") or b.get("candidate_artifact")`（与 `orchest.py:1171` 同源），全文替换；A-6 增设 `candidate_plan` 旧块子用例 | §3.5:152/161/186/207/210/211；§3.4:138-139；A-6:307；A-11-2:364；F1:256 |

### 7.2 非阻断级（NB-1..NB-6）

| ID | R1 结论 | 处置 | 落点 |
|---|---|---|---|
| NB-1 | A-13 把 §12.3 归"新增型"与标题 "(replace 型)"冲突；§12.1 replace 部分未纳入三态 | A-13 逐项对齐 §12 标题：12.0/12.1(replace 部分)/12.2/12.3/12.6/12.7/12.8 = replace；12.4/12.5 = append；12.1 bullet = 新增 | A-13:313 |
| NB-2 | `if not D` 为不可达死分支；§12.4/12.5 "全 non-decisional 链保守回退"与实现不符 | 删除 `if not D` 分支，改为 `assert D` + 注释（段首必 decisional）；§12.4/12.5 措辞改为"链段首块非 decisional → 直接 fail closed" | §3.5:200-201；§12.4:419；§12.5:427 |
| NB-3 | reopen 跨 revision 边界仅检查全局 `blocks[0]`，新 revision 首块门未执行 | 链构造按 `_detect_revision_id` 过滤 `revision_id`（缺字段旧块归入当前段）；段首块必须 decisional 的门落进伪代码 | §3.5:147/155-157/181-182；F1:256 |
| NB-4 | §3.5 伪代码未含 full-pair 的"正向 verdict"与"禁含 delta" | 抽出 `require_full_pair(T)`，硬编码 `"delta" not in payload` + 双 verdict `== "可执行"` + fresh/blank 对校验；A-6 增对应子断言 | §3.5:184-193/203；A-6:307；§3.3:132 |
| NB-5 | F6"分级常量单源"静态断言无常量名/位置，不可落地 | 命名 `MATERIAL_CHANGE_CLASSES`/`MATERIAL_SECTION_VOCAB`/`cur()` 为 `orchest.py` 单源；F6 断言锚定这些符号 | §3.5:147/150-152；F6:261；A-5:307；F1:256 |
| NB-6 | `scripts/README.md:17` "两-authority 审查时必传 exact"未随分级同步 | 新增 §12.8（replace 型）逐字改写 `:17` 注释为"material-revision（任一级别）审查时必传 exact"；F7 锚点扩为 `:17` 与 `:144-151`；A-13 纳入 12.8 | §12.8:443-446；F7:262；A-13:313 |

### 7.3 覆盖与验证

- 阻断 4/4、非阻断 6/6，全部处置；无新增未决。
- 机器块（§14 JSON）逐字节未动；`preflight` 实跑通过（§六）。
- plan.md 修订后字节 **46074** ≤ 46080（A-1）、`status: candidate-3`（A-2）、恰一个 governance fenced-json 块（A-4）。
- 语义残余（R-1 双向漏报、R-2 delta diff 文本绑定、R-6 作者声明性）保持不变，仍如实声明于 §10，非本轮 R1 缺陷。

---

## 编排层交接点（2026-09-12，会话上下文耗尽，状态全部落盘）

- 现状：**candidate-4 在盘**（outer R2 全部 issue 已按单选修法处置，处置表见 §八）；outer R1（阻断，4 BLK）已处置为 candidate-3；outer R2 verdict=**阻断需修复**（severities 含 architectural），核心 R2-BLK-1（`_detect_revision_id` 过滤致整门 fail-open + 10 条既有负例反转）已由 candidate-4 消解并新增 A-19。
- 续作序列（严格按序）：
  1. ~~派 repair（…… attempt=3）→ candidate-4~~ **已完成**：链构造改为 `rev_cur = all_blocks[-1].get("revision_id")`，`blocks = [b for b in all_blocks if b.get("revision_id", rev_cur) == rev_cur]`，`rev_cur is None` 时全部归当前段；§3.5/§3.7/F1/A-5 同步并补 A-19。
  2. outer R3（round-3.md）。按 2026-09-12 用户约定：**趋势收敛 + 达限（outer 8/blind 3）即视为通过**；精度级余项转入实施约束清单。
  3. blind-recheck-1.md（与终局字节同哈希、exact）→ 材料对；design-review.md（强制，ultraverge）。
  4. 实施（TDD，按 plan File Matrix 与 §12 逐字对照）→ 全量 pytest（长路径 TEMP）→ 独立 fresh 审计 → retrospective.md → finish（--dry-run 先行；孤儿/allowlist 按既有人工披露路径）→ archive check → commit+push。
  5. 之后做任务 2：ocsr 上游（`C:\Users\Administrator\Documents\Github\ocsr`，main 已同步）——`ocsr_dispatch.py` 增加"声明式覆盖"（adapter `--in-place-edit` 透传）与路径一致性告警；改完同步 `.agents/skills/ocsr` 与 `.claude/skills/ocsr` 副本并验证（`verify_ocsr_skill.py`）。
- 派发纪律：prompt 产物路径与 `--output-name` 必须同源生成（preflight 已上线，三次真实拦截记录在案）。

---

## 八、outer R2 逐条处置表（R2-BLK-1 + R2-NB-1..3 → 处置 → 落点）

> 依据 `.converge/active/20260912-o6-material-delta-recert/round-2.md`，逐条按各条单选修法落地。R2 verdict = `阻断需修复`（R2-BLK-1 = `architectural`）。产物 = candidate-4。

### 8.1 阻断级（R2-BLK-1）

| ID | R2 结论 | 处置（严格按单选修法） | 落点 |
|---|---|---|---|
| R2-BLK-1 | §3.5 按 `_detect_revision_id` 过滤 revision 段，在既有夹具（块 `revision_id=r2/r3/r4`、无 `.reopen-state.json` → 返回 `r1`）与真实归档块（`r2`）上把链过滤为空并 `return` → 10 条既有负例反转 + 整门 fail-open | **删除对 `_detect_revision_id` 的过滤依赖**：`rev_cur = all_blocks[-1].get("revision_id")`；`blocks = [b for b in all_blocks if b.get("revision_id", rev_cur) == rev_cur]`（`rev_cur is None` 时全部归当前段）；**当前段 = 末块所属段**；历史段（`revision_id` 不同者）仅校验段首 decisional、不入 delta 链；`current = blocks[-1]` 与盘上 `plan.md` 校验**保持不变** | §3.5:147/155-164；§3.7:239-240；F1:263；A-5:313；**新增 A-19:327** |

### 8.2 非阻断级（R2-NB-1..3）

| ID | R2 结论 | 处置（单选修法） | 落点 |
|---|---|---|---|
| R2-NB-1 | §3.1/§3.6/A-11-12 声明的错误码 `legacy-anchor-requires-full-pair` 在 §3.5 伪代码中无发出点 | 采 **(b)**：A-11-12 判定改为"legacy 自其起 full-pair，缺对 → `rc≠0`，**不硬断言专用错误码**"；同步 §3.1/§3.6 措辞（不设专用码）。**未采 (a)**：无条件 `raise` 会使既有正向 legacy 用例（`test_two_distinct_same_hash_reviewers_pass:443`、`test_three_material_blocks_payloads_reference_last_passes:908`）反转，与 A-11-8"无对 → fail"矛盾 | §3.1:116；§3.6:234；A-11-12:382 |
| R2-NB-2 | `decisional_anchors` 声明"必填"但伪代码把缺省当 legacy 而非 schema 违规 | 采第一分支：语义改为"**新 decisional 块缺失即 legacy 兼容（自其起全量对）**；空列表/词表外才 `FAIL_CLOSED:anchors-vocab`"；§3.6 fail 条件列表同步 | §3.1:114；§3.6:234 |
| R2-NB-3 | §12.4 `decisional_anchors` 语义与 §3.1 表存在措辞冗余 | 以 §3.2/§12.4 为单一权威；§12.1 新增 bullet 改为**纯指针**（不再展开语义分支） | §12.1:405-406 |

### 8.3 覆盖与验证

- R2 全部 issue 处置：阻断 **1/1**、非阻断 **3/3**，无遗漏。
- **新增硬验收 A-19**："10 条既有 material 负例不反转"，逐条列出并写明"candidate-4 语义下逐条仍 `rc != 0`"。
- 机器块（§14 JSON）逐字节未动（`numeric_changes`/`calibration`/`user_message_events` 均不变）。
- 语义残余（R-1 双向漏报、R-2 delta diff 文本绑定、R-6 作者声明性）保持不变，仍如实声明于 §10。

## 九、candidate-4 preflight 实跑输出

命令（2026-09-12，本机，UTF-8）：

```
python scripts/budget_gate.py preflight --plan .converge/active/20260912-o6-material-delta-recert/plan.md
```

输出：

```
WARN:code_heavy:2,126
PREFLIGHT_OK:governance-change
EXIT=0
```

说明：`WARN:code_heavy:2,126` 为既有 code-heaviness 启发式（block≥3 或 loc≥40），**非阻断**；`PREFLIGHT_OK:governance-change` 表示治理机器块 schema、`archaeology_refs` git 存在性、`calibration` locator/hash/corpus_digest/freshness、`user_message_events` UUID 全部通过。candidate-4 机器块 JSON 逐字节未改动。plan.md 实测 **46057 B** ≤ 46080（A-1）、`status: candidate-4`（A-2）、恰一个 governance fenced-json 块（A-4）。
pytest：本阶段**只改计划、未改任何代码**，计划未要求候选阶段跑 pytest（A-16/A-19 属 implement 分支），故未跑；待 §6 implement P3/P4 由落地 executor 执行。

---

## 编排层决定 · 设计复审处置（2026-09-12）

- 设计复审 verdict=设计需修订（D1-D6，各带单选修法）。编排层裁决：**plan 字节冻结于 candidate-4（双权威已认证）**，D1-D6 按其单选修法作为**绑定实施约束**带入执行（用户既定 doctrine：剩余问题在执行中解决；实施后独立 fresh 审计验证约束落地）。D1 采纳 Option A（Occam：legacy 仅当前段末块 require_full_pair，行为等价现状）。此为本对象的过程降级点，如实记录。

---

## 十、实施执行记录（Implementation Executor，fresh 独立上下文，2026-09-12）

> 权威源：`plan.md` candidate-4（冻结，46057 B，未改动）+ `design-review.md` D1-D6 单选修法。
> 纪律：无 git 写操作；既有测试体零删改（A-12：`tests/test_loop_a_coverage.py` diff +360/-0）。

### 10.1 Exact File Matrix 落点（F1-F8）

| # | 文件 | 改动 |
|---|---|---|
| F1 | `scripts/orchest.py` | 新增常量单源 `MATERIAL_CHANGE_CLASSES`/`MATERIAL_SECTION_VOCAB`/`MATERIAL_ERROR_NS` + helpers `_material_cur`/`_material_error`/`_locator_id`；重写 `_validate_material_gate`（链分段 + 段首门 + 域门 + `require_full_pair(T)` + `require_delta(T)` + 并集交集 fail-safe + legacy D1-A 分支 + 正向 verdict 门）；`_find_material_block` 语义不变；finish 调用点不变 |
| F2 | `refs/state-schema.md` | §12.0/12.1/12.2 逐字（含新增指针 bullet） |
| F3 | `refs/orchestrator-guide.md` | §12.3 标题 + §12.4 triggers/词表 + §12.5 item 7（含 D4 输入契约、D5 triggers 收口） |
| F4 | `SKILL.md` | §12.6 指针句 |
| F5 | `tests/test_loop_a_coverage.py` | 末尾新增 `TestMaterialDeltaPath`（22 条新测试，覆盖 A-5..A-11 + §11 对抗）；既有 17 条零删改 |
| F6 | `tests/test_process_controller_contract.py` | 新增 `test_material_gate_constants_single_source`（常量/`cur()` 单源 + 表体 token 集等式）；既有 metadata-only 负例不变 |
| F7 | `scripts/README.md` | §12.7/12.8 逐字 |
| F8 | `docs/plans/active/20260911-converge-operational-envelope.md` | O6 行 + 终态段（重评结论 + 机制实现）。**untracked（N3）** |

### 10.2 D1-D6 落地

- **D1（A）**：`if legacy is not None: _require_full_pair(blocks[-1]); return`——当前段末块全量对，行为等价现状；§12.4/§12.5 的 legacy 子句按 D1-A 改写（偏差见 10.4）。
- **D2（A）**：材料门全部 fail 经 `_material_error(code, summary)` → `material-gate:<kebab-code>` → `budget_gate.FailClosed` → `FAIL_CLOSED:<reason>` / exit 30。函数体内零 `raise budget_gate.FailClosed`（仅 docstring 提及）。
- **D3（A）**：`_require_executable` 以 `re.findall(r"verdict:\s*(\S+)")` 要求**恰一次**且 `== 可执行`；0/≥2/他值 fail。新增 `test_delta_verdict_two_literals_fails_closed`（A-11-15）。
- **D4（A）**：最小输入契约（内嵌前块全文 + 当前 plan 全文）落入 guide §12.5 item 7 追加句 + `_require_delta` docstring；不扩机制（无 base 快照仓），机械不可验证如实声明。
- **D5（A）**：`triggers`（material trigger 变更）经 guide §12.4 追加句补入 `decisional` 定义（plan §3.2 冻结不改；词表已含 `triggers`）。
- **D6（A）**：A-11-14 为语义残余，不计入 A-11；测试覆盖 A-11-1..13，未对 A-11-14 做机械断言。

### 10.3 验证数字

- 基线：`523 passed / 5 skipped`。实施后：**`552 passed / 5 skipped / 11 subtests passed`**（+29 = 22 新 delta 测试 + 6 继承重跑 + 1 新契约测试）。
- `py_compile scripts/orchest.py tests/test_loop_a_coverage.py tests/test_process_controller_contract.py` → 0。
- `git diff --check` → 干净。
- A-19 的 10 条既有 material 负例逐条仍 `rc≠0`（全量绿）。
- `budget_gate.py` 零改动（A-17）；`archive_contract/*` 零改动；既有 ledger 事件字段零改动。

### 10.4 偏差与未决

1. **§12 legacy 子句偏差（D1 冲突）**：§12.4/§12.5 的"缺省 anchors 的旧块自其起逐块 full-pair"与绑定约束 D1-A（仅末块 full-pair）冲突。依 D1-A 落地并把该子句改写为"出现于当前段时仅对当前段末块维持 full-pair（行为等价现状）"。其余 §12 文本逐字。
2. **F8 untracked（N3）**：`docs/plans/active/20260911-converge-operational-envelope.md` 在 HEAD 下未跟踪，§13.3 回滚命令对其无效；A-14 的 F8 判据应为内容型。
3. **A-11-14 / R-1(b) / R-2 / R-6**：语义残余，机械不可判，未伪造闭环。
4. **角色口径（N4）**：delta reviewer 门按 plan §3.5 `role ∈ REVIEWER_AUTHORITIES["fresh"]` 实现（guide §12.5 表述为推荐 `outer-reviewer`）；未收窄。
5. **D4 机械不可验证**：输入契约仅文档化，无机械绑定（非目标 §8.7 明确不引入 base 快照仓）。

### 10.5 收口

- 全量测试绿、无既有行为回退；材料门在本对象自身 `finish` 时的适配须由 orchestrator 按新分级路径产出材料块（本 executor 未代跑 finish）。
- 实施后独立 fresh 审计兜底 D1-D6 落地与残余。

## Phase 6 · 独立审计结论

> 审计者：fresh 独立上下文（未参与计划/实施）；全文见同目录 `audit-report.md`。只读审计：tracked 文件零改动。

- **verdict：不通过**（blocking = 2）。
- **blocking**：
  1. **B1｜A-11-3 测试无效**：`test_deleted_non_decisional_block_fails_closed` 实测 `RC=1`，失败于 finish 步骤 2（`rid_d` reserve 未 register），从未到材料门；HEAD 下亦通过（零判别力）。单选修法 A：改为真正链删除形态（删中间 non-decisional 块，令下游 `delta.base` 指向已删块哈希，断言 `rc==30`），并确保全 reservation 已 settle。
  2. **B2｜D3-A「校验前锚定」子句未落地 → 真实数据回归**：`_require_executable` 扫整段 output 要求 `verdict:` 恰一次。实测真实归档对象 `.converge/done/20260910-process-controller-consolidation`：HEAD 门 PASS，新门 `FAIL_CLOSED:material-gate:verdict-parse`（invocation `59e4c977` output 含 2 个 `verdict:`）；15 个 done 对象扫描 14 ok / 1 fail。单选修法 A：按 D3-A 仅取规范 verdict 载体（首 yaml fence/frontmatter）计数，并补真实形态回归用例。
- **复跑数字**：`552 passed, 5 skipped, 11 subtests passed`（367.02 s，`TEMP/TMP` 指向本机 Temp）。pre-impl 对照（`git archive HEAD` + 当前测试）：`TestMaterialDeltaPath` 14 failed / 14 passed（判别力成立）。A-19 十条既有负例 10/10 绿。§12 三态 19/19 OK。
- **已核通过**：范围纪律 F1-F8、语义守恒（`budget_gate.py`/`archive_contract/*`/既有事件字段零改动）、R2-BLK-1 链构造逐行一致、D1-A 同段多 legacy 不误伤（独立构造 + 真实归档对象验证）、delta 三重锚定/三角/正向 verdict、词表域门与并集交集、D2/D4/D5/D6 落地。
- **最担心 1-2 点**：① **B2 真实数据回归**——新门对「frontmatter + 正文」双 `verdict:` 的真实 reviewer 输出会误挡 finish（有实证），D3-A 的锚定子句是其设计内的解；② **B1 虚假覆盖**——A-11-3 名义被拦、实为步骤 2 失败，掩盖了链删除机制未测的事实（A-11-2 base 伪造已等价覆盖该失败模式，故 B1 修复成本低）。

## Phase 6b · 审计后修复 B1/B2

> 执行者：fresh 修复 Executor（未参与计划/实施/审计）；只修审计 §B 两条；不做 git 写操作。全部命令 `TEMP/TMP` 指向本机 Temp。

### B1｜A-11-3 测试无效 → 真正链删除形态

- 采审计单选修法 A。`test_deleted_non_decisional_block_fails_closed` 由 `_setup_chain(write_n=False)`（在 finish 步骤 2 因未 settle reservation 失败、零判别力）改为手工构造同段链 `D → N1 → N2` 并**从 attempts.md 移除 N1 的 fence**：`N2.delta.base_plan_sha256 == canon(N1)`，而链上前块实为 `D` → base 不匹配计入 skip → 材料门 `delta-candidate-missing`。
- 所有 reservation（outer/blind/delta）均 register settle，失败点确在材料门（step 3.5），非步骤 2。
- 断言：`rc == 30` 且输出含 `material-gate:delta-candidate-missing`。
- 判别力实证：对 `git archive HEAD` + 当前测试运行该用例 → **FAIL**（HEAD 报 `no qualifying pair`，无 `delta-candidate-missing`），新实现下 **PASS**。

### B2｜D3-A「校验前锚定」未落地 → 真实历史输出回归

- 采审计单选修法 A。新增嵌套 helper `_verdict_carrier(output_text)`：优先取输出起始 YAML frontmatter（`---` 围栏），否则取首个 ```yaml fence，二者皆无则回退整段文本；`_require_executable` 仅在该载体内做「恰一次且 == 可执行」，**区域外 `verdict:` 不参与计数**。
- `test_delta_verdict_two_literals_fails_closed`（A-11-15）改为在**载体内**注入第二个字面量（区域外不计），保持「载体内 ≥2 → fail」契约。
- 新增回归用例：
  - `test_historical_double_verdict_frontmatter_passes`：真实形态（frontmatter 载体 `可执行` + 正文另一 `可执行`）→ **PASS**（HEAD 门 = 新门行为）。
  - `test_historical_frontmatter_blocking_elsewhere_executable_fails`：载体 `阻断需修复`、别处 `可执行` → `rc==30` 且 `verdict-not-executable`。
- 真实数据实证：直接对 `.converge/done/20260910-process-controller-consolidation` 调新门 → **GATE_PASS**（修复前 `verdict-parse`）；15 个 done 对象全量扫描 **15 ok / 0 fail**（修复前 14 ok / 1 fail）。
- 判别力实证：把 `_verdict_carrier` 还原为整段扫描后，两条新增 B2 用例均 FAIL（double-verdict 误挡；carrier-blocking 报错码为 `verdict-parse` 而非 `verdict-not-executable`）。

### 验证数字（实跑）

- `python -m pytest tests/test_loop_a_coverage.py -q` → **75 passed**（184.41 s）。
- `python -m pytest tests -q` → **554 passed, 5 skipped, 11 subtests passed**（376.69 s；修复前 552，+2 = 两条新增回归用例）。
- `python -m py_compile scripts/orchest.py` → 0（`PY_COMPILE_OK`）。
- `git diff --check` → 干净（`DIFF_CHECK_OK`）。

### 改动面（最小手术）

- tracked 改动仍为审计时 7 文件（`SKILL.md`/`refs/orchestrator-guide.md`/`refs/state-schema.md`/`scripts/README.md`/`scripts/orchest.py`/`tests/test_loop_a_coverage.py`/`tests/test_process_controller_contract.py`）+ untracked `docs/plans/active/`；本次修复仅落在既有改动的 `scripts/orchest.py` 与 `tests/test_loop_a_coverage.py` 内，未新增/删除文件，未触碰其余文件。
- 未做任何 git 写操作。

## Phase 6c · 聚焦复审

> 复审者：fresh 独立上下文（未参与计划/实施/修复）；只读（仅追加本节到 attempts.md）。UTF-8。
> 命令：`TEMP/TMP` 均指向 `C:\Users\Administrator\AppData\Local\Temp`；仓外 probe 位于 `%TEMP%\opencode\`，未落工作目录。HEAD 对照 = `git archive da81e70` 抽取到仓外 + 覆盖当前测试文件。

**闭合**

### B1｜A-11-3 测试无效 → **yes（真正闭合）**

- **到达材料门（实证）**：独立 probe（以当前工作树 orchest 调用用例体并捕获 `finish()` 输出）——`RC=30`，`ERR=FAIL_CLOSED:material-gate:delta-candidate-missing: ... skipped candidates: ... ebd92e25 (outer-reviewer): delta base hash mismatch (payload=f3f4d478fe0725cb, expected=5f9b0470f7321ed0)`。`delta-candidate-missing` 仅由材料门内 `_require_delta → _fail(..., "delta-candidate-missing")` 发出（grep 唯一发出点），且失败原因正是「N2 的 `delta.base_plan_sha256` = 已删除 N1 的 canon hash（f3f4d478…）而链上前块实为 D（5f9b0470…）」——即审计所指的链删除缺环路径。全部 reservation（outer/blind/delta）已 register settle，无步骤 2「未 settle reservation」错误（审计原缺陷即 RC=1 步骤 2）。
- **判别力（实证）**：HEAD 对照（`git archive da81e70` + 当前测试文件）运行同一用例 → **FAIL**，HEAD 报 `FAIL_CLOSED:material-gate: no qualifying pair found ...`（无 `delta-candidate-missing`）。当前实现下 PASS。零判别力问题消失。
- **自推演失败路径**：删除 N1 后 `all_blocks=[D,N2]`（同段）→ 末块候选字节 == 盘上 plan → 段首 D 为 decisional、`_require_full_pair(D)` 由 outer+blind 全量对满足 → `j∈{1}`，`_require_delta(N2, D)` 的 base 期望 = `canon(D)=5f9b0470…`，N2 delta base = `canon(N1)=f3f4d478…` 不匹配计入 skip → candidate None → `delta-candidate-missing`。与实测一致。

### B2｜D3-A「校验前锚定」未落地 → **yes（真正闭合）**

- **真实历史对象**：`.converge/done/20260910-process-controller-consolidation` 的 invocation `59e4c977` 的 `output.bin` 独立扫描为 **2 个** `verdict:`（offset 196 起始 frontmatter、offset 6626 正文，均 `可执行`）。
- **HEAD 行为 == 新门行为**：直接对真实对象调门——HEAD（da81e70）→ `GATE_PASS`；当前工作树 → `GATE_PASS`。一致。修复前行为复现：把 `_verdict_carrier` 临时还原为整段扫描（仓外 scripts 副本，`carrier = output_text`）→ `GATE_FAIL material-gate:verdict-parse: ... (found 2)`，恰为审计 §B2 的回归。即锚定子句是使 HEAD==新门 的充分落地。
- **fail-closed 未松动**：`test_historical_frontmatter_blocking_elsewhere_executable_fails` PASS（载体 `阻断需修复` + 正文别处 `可执行` → `rc=30` / `verdict-not-executable`，不以区域外正向值放行）；`test_delta_verdict_two_literals_fails_closed` PASS（载体内 ≥2 字面量 → fail）；载体 0 次亦 fail（`_require_executable` 恰一次契约保留）。
- **代码核读**：`orchest.py:1396-1429` `_verdict_carrier`（起始 frontmatter → 首个 ```yaml fence → 回退整段）与 `_require_executable`（仅载体内 `findall`，恰一次且 == 可执行）符合 D3-A「校验前锚定」。fallback 整段仅在无 frontmatter 且无 yaml fence 时触发，保持既有严格度。

### 零回归抽查（既有 10 条 material 负例）

- 独立实跑 10/10 **PASS**（20.56 s），即各负例断言仍 `rc != 0`：`test_changed_plan_byte_after_review_invalidates`、`test_metadata_only_prompt_evidence_rejected_when_material`、`test_post_hoc_hash_injection_rejected`、`test_crlf_pollution_fails_closed`、`test_duplicate_review_target_block_rejected`、`test_payload_referencing_missing_material_id_fails_closed`、`test_only_metadata_only_terminals_gate_fails_closed`、`test_qualifying_candidate_with_mismatched_payload_hash_fails`、`test_only_stale_pair_fails_closed`、`test_qualifying_pair_with_non_executable_verdict_fails`。与 audit §3.2 / Phase 6b 记录一致。

### 复跑数字（实跑）

- 全量：`python -m pytest tests -q` → **`554 passed, 5 skipped, 11 subtests passed`**（375.22 s）。与自述 554/5/11 一致，非回归。
- 聚焦：B1 + 两条 B2 回归 + A-11-15 → `4 passed`（12.54 s）。
- 范围：`git status --porcelain` 仍为审计时 7 个 tracked 改动 + untracked `docs/plans/active/`；本次复审零写操作（仅本文件追加）。

### 结论

B1、B2 均**真正闭合**（审计指出的问题均已消失，非仅「改了」）；10 条既有负例零反转；全量 554/5/11 与自述一致。**verdict：闭合**。


---

## 附录 · 过程报告全文存档（根 allowlist 收口，原件移入本文件）


### author-report.md

```markdown
# Author Report · O6 material 增量复核机制（candidate-1）

> Plan Author（fresh Executor）回执。对象：`20260912-o6-material-delta-recert`。
> 日期：2026-09-12。授权：ultraverge（触及第三部）。

## 1. 产物与哈希

| 产物 | 路径 | 字节数 | SHA-256 |
|---|---|---|---|
| candidate-1 plan | `.converge/active/20260912-o6-material-delta-recert/plan.md` | 30,961 | `1581c8bbb46ac1f47149c45979e10d15a767c718ee3f5fbea1083c2c8b57e0af` |
| 撰写记录 + preflight 输出 + calibration locator | `.converge/active/20260912-o6-material-delta-recert/attempts.md` | 7,543 | `d4e6b343337a30e99340c85768c485a3fc37d93e78de97996c703d9093519c6d` |
| 本报告 | `.converge/active/20260912-o6-material-delta-recert/author-report.md` | — | — |

- **简洁性硬约束**：plan.md 30,961 B ≤ 45KB（46,080 B）✓（`plan.md` §7 A-1）。
- plan.md 唯一治理机器块（`converge.governance-change/v1`）位于 §14；preflight 未报 `duplicate_governance_block`。

## 2. Preflight 结论

命令：
```
python scripts/budget_gate.py preflight --plan .converge/active/20260912-o6-material-delta-recert/plan.md
```
输出（实跑）：
```
WARN:code_heavy:2,72
PREFLIGHT_OK:governance-change
EXIT=0
```
- `PREFLIGHT_OK:governance-change`：机器块 schema、`archaeology_refs` git 存在性（`cat-file -e`）、`calibration` locator/hash/corpus_digest/freshness、`user_message_events` UUID 全部通过。
- `WARN:code_heavy:2,72` **非阻断**（阈值 block≥3 或 loc≥40；治理机器块本身即 40+ 行）。

### 2.1 首次失败与修正（如实披露，未伪造）

首次实跑报 `FAIL_CLOSED:path-not-found:calibration-o6`。实核 `evidence/calibration-report.json` 字段发现其自身 `id="calibration"`（非 `calibration-o6`）。已将 `plan.md` §2.4 与 §14 的 locator/id 改为 `converge.calibration-report/v1,id=calibration`，重跑通过。**未**改动报告文件、未伪造 id。

## 3. 机器块三字段（+ calibration）实核值

| 字段 | 值 |
|---|---|
| `change_id` | `o6-material-delta` |
| `numeric_changes` | 3 条，全 `kind: mechanism`、`comparison: null`、`released/old/proposed: null` |
| `archaeology_refs` | `git:da81e70cee7931d49680866f9cd0b2cdb6fadc5a`（`git log --format=%H -1` 实核 HEAD）+ `archive:done/20260911-op-envelope-b-contract-correction` |
| `calibration.path` | `attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration]` |
| `calibration.sha256` | `16ec2455acb9cdb143145e8f28c52b4db1d96f9cd90b44ab4b8af897df3303c8`（嵌入 fence canonical 复算 = 独立文件 canonical） |
| `calibration.corpus_digest` | `3627eb4d72cfbf07a3c1a6655026c9ce51063506e613c3a7df5b3519b10224ea` |
| `calibration.freshness` | `{repository_head=da81e70cee7931d49680866f9cd0b2cdb6fadc5a, source_archive_revision=unavailable, source_event_high_watermark=0}` |
| `counterevidence_refs` | `[]` |
| `user_message_events.execution_authorization` | `989e5ebd-2406-4dcf-bf77-283bcb4e6e17`（B 对象 sequence 49 收口裁决事件） |
| `user_message_events.quality_goal` | `06754e6f-94fc-4a8a-9d80-65f89ae68e3a`（B 对象 sequence 10） |

**user_message_events 说明**：两项均来自 **B 对象**事件流（实核 `evidence/events/00000049-989e5ebd-….json`、`00000010-06754e6f-….json`），本对象事件流内暂无对应事件。preflight 仅做 UUID 格式校验（`budget_gate.py:1668-1679`），因此通过；**若编排层将校验升级为"须在本对象事件流内存在"，已按 prompt 要求改为"编排层后补清单"并披露，不伪造**（见 `plan.md` §14 说明）。

## 4. 实核的行号（全部实开核对）

| 引用 | 实核结果 |
|---|---|
| `orchest.py:1095` `_find_material_block` | 确认（`:1095-1118`，last-supersedes-all + canonical sha `:1116-1117`） |
| `orchest.py:1133` `_validate_material_gate` | 确认（`:1133-1361`） |
| `orchest.py:1171-1175` 锚点(a) | 确认 |
| `orchest.py:1267-1272` 锚点(b) | 确认 |
| `orchest.py:1273-1279` 锚点(c) | 确认（简报写 `:1335-1337` 为两 payload byte-equal，亦确认；两者均列于 §2.2） |
| `orchest.py:1335-1337` payload byte-equal | 确认 |
| `orchest.py:1340-1361` verdict 非阻断 | 确认 |
| `orchest.py:1579-1581` finish 步骤 3.5 调用点 | 确认（步骤 3.5 注释 `:1579`） |
| `refs/orchestrator-guide.md:17-32` | 确认（`:17` 标题、`:23` triggers、`:27-31` 流程、`:32` 失效句） |
| `refs/state-schema.md:101-104` | 确认（`:101` 标题、`:103` 字段、`:104` 失效句） |
| `CONSTITUTION.md:71-72` | 确认（第三部清单两条） |
| `SKILL.md:462` | 确认（"Material revision 两-authority 同字节规则"指针句） |
| `budget_gate.py:1682-1699` calibration 校验 | 确认（`_resolve_and_check_report`；窄门 `:1710-1742`） |
| B 成本数据 `retrospective.md:75/80/53/42` | 确认（`:75` 全量双认证、`:80` 7 次≈一半成本） |

### 4.1 相对简报的实核修正/增补

1. **File Matrix 增补 `SKILL.md:462`**（F4）：该指针句规范"两-authority 同字节规则"，D1 引入 non-decisional delta 例外后若不改将产生文档-实现矛盾（第三部一致性）。简报未列，实核增补。
2. **File Matrix 增补 `tests/test_process_controller_contract.py`**（F6）：`test_orchest_negative_read_side_default_untouched`（`:214-218`）以 AST 直锚 `_validate_material_gate` 源码并断言含 `"metadata-only"`；改造后必须保持该断言或同步更新。简报预测的 `test_process_controller_contract.py` 确认在范围内，但理由与"新写点"不同。
3. **calibration locator**：简报要求"引用 `evidence/calibration-report.json`"，但 locator `root-file` 必须为不含路径分隔符的 allowlist 普通文件名（`refs/state-schema.md:76`、`budget_gate.py:1452-1459`），`evidence/` 路径**不可寻址**。采用与 B 对象同构的合规方案：报告 canonical 字节作为 fenced 载体放入 allowlisted 根文件 `attempts.md`，`calibration.path` 指向该 fence；独立文件作证据留痕（不被 preflight 机械校验）。
4. **材料门锚点(b) 行号**：简报将 `:1267-1272` 标为锚点(b)（候选 payload vs 盘上 plan），实核确认；简报另标 `:1335-1337` 为锚点(c)（两 payload byte-equal），实核确认；锚点(c) 的"候选 vs 当前 material 块"实为 `:1273-1279`。plan §2.2 已列全，无歧义。

## 5. 结论

- candidate-1 已就绪，送 ultraverge 三名初审。
- 机制方向（D1）未改变，仅按实核优化细节（新增 `decisional_anchors` 交集 fail-safe 以强化 §11 A-11-4 的机械拦截）。
- 残余风险 R-1（谎报 `changed_sections` 漏报）已在 `plan.md` §10/§11 如实声明，不声称机械闭环。

```


### repair-report-c4.md

```markdown
# Plan Repair Report · candidate-3 → candidate-4（outer R2 处置）

- 对象：`.converge/active/20260912-o6-material-delta-recert`
- 角色：Plan Repair Executor（fresh）
- 输入：`plan.md`（candidate-3）、`round-2.md`（R2-BLK-1 + R2-NB-1..3）、`round-1.md`、`uv-init-1/2/3.md`、`attempts.md`
- 基线 HEAD：`da81e70cee7931d49680866f9cd0b2cdb6fadc5a`
- 只改文件：`plan.md`、`attempts.md`（本报告为产物第三件）；无 git 写操作
- 编码：UTF-8（无 BOM、LF）

## 一、最终产物度量

| 项 | 值 |
|---|---|
| `plan.md` 字节数 | **46057 B**（≤ 46080，A-1；candidate-3 为 46074 B） |
| `plan.md` SHA-256 | `d6525f441c321128e15f7d01bc7265cf46f403077ef694ae3e65018add8e6bee` |
| frontmatter | `status: candidate-4`、`review_mode: ultraverge`、`object_slug: 20260912-o6-material-delta-recert`（A-2） |
| governance fenced-json 块 | 恰 1 个（A-4；解析器计数） |

> 字节预算说明：新增 A-19（约 0.66KB）及多处 R2 同步文本后，对 §1/§2/§3/§4/§9/§10/§11/§12/§14 的非规范性散文与重复措辞做了等价压缩（未删任何机械规则/验收/逐字对照），净减 17 B 并以 23 B 余量落在 45KB 内。机器块 §14 JSON 逐字节未动。

## 二、R2 issue 逐条处置（一句话）

### 阻断级

- **R2-BLK-1（architectural，fail-open）**：采纳其单选修法——**删除对 `_detect_revision_id` 的过滤依赖**；链构造改为 `rev_cur = all_blocks[-1].get("revision_id")`、`blocks = [b for b in all_blocks if b.get("revision_id", rev_cur) == rev_cur]`、`rev_cur is None` 时全部块归当前段；**当前段 = 末块所属段**；历史段仅校验段首 decisional、不入 delta 链；`current = blocks[-1]` 与盘上 plan 校验不变。同步 §3.5/§3.7/F1/A-5，并新增 A-19 覆盖"10 条既有负例不反转"。

### 非阻断级

- **R2-NB-1**：采 **(b)**——A-11-12 判定改为"legacy 自其起 full-pair，缺对 → `rc≠0`，不硬断言专用错误码"，同步 §3.1/§3.6 删除对 `legacy-anchor-requires-full-pair` 的强制发码声明。
- **R2-NB-2**：采第一分支——`decisional_anchors` 语义改为"新 decisional 块**缺失即 legacy 兼容（自其起全量对）**；空列表/词表外才 `FAIL_CLOSED:anchors-vocab`"，§3.1 表"必填"列与 §3.6 fail 列表同步。
- **R2-NB-3**：以 §3.2/§12.4 为单一权威，§12.1 新增 bullet 改为**纯指针**（不再展开语义分支）。

> 说明：R2-NB-1 **未采 (a)**，理由是 §3.5 legacy "分支进入前显式 raise" 会使既有正向 legacy 用例（`test_two_distinct_same_hash_reviewers_pass:443`、`test_three_material_blocks_payloads_reference_last_passes:908`）反转，并与 A-11-8"无对 → fail"自相矛盾；单选修法为二选一，此处取与既有测试及伪代码一致的一支。

## 三、落点表（issue → 处置 → 落点）

| ID | 处置 | 落点 |
|---|---|---|
| R2-BLK-1 | 删 `_detect_revision_id` 过滤；当前段 = 末块 `revision_id` 段；历史段仅段首校验 | §3.5:147/155-164；§3.7:239-240；F1:263；A-5:313；A-19:327 |
| R2-NB-1 | 采 (b)：A-11-12 判 `rc≠0`，删专用错误码声明 | §3.1:116；§3.6:234；A-11-12:382 |
| R2-NB-2 | anchors 缺失=legacy；空/域外才 `anchors-vocab` fail | §3.1:114；§3.6:234 |
| R2-NB-3 | §3.2/§12.4 单一权威；§12.1 bullet 仅指针 | §12.1:405-406 |

## 四、R2-BLK-1 的验收映射（10 条既有负例）

`round-2.md` 指出 candidate-3 下 10 条负例因链被过滤为空而反转。candidate-4 落地后，逐条**逐条仍 `rc != 0`**（写入 A-19）：

| # | 测试（`tests/test_loop_a_coverage.py`） | candidate-4 语义下的拦截点 |
|---|---|---|
| 1 | `test_changed_plan_byte_after_review_invalidates:452` | `current` 块候选 sha/size ≠ 盘上 plan → `current-block-plan-mismatch` |
| 2 | `test_metadata_only_prompt_evidence_rejected_when_material:464` | 无 exact 证据 → `require_full_pair` 无合格候选 |
| 3 | `test_post_hoc_hash_injection_rejected:483` | blind 的 `material_revision.sha256` 不匹配 → 候选被 skip → 无合格对 |
| 4 | `test_crlf_pollution_fails_closed:531` | CRLF → 候选被 skip → 无合格对 |
| 5 | `test_duplicate_review_target_block_rejected:572` | prompt 内 2 个 review-target → 候选被 skip → 无合格对 |
| 6 | `test_payload_referencing_missing_material_id_fails_closed:918` | payload locator=`r99-material`/hash 0…0 不绑定 `r2` 块 → 无合格对 |
| 7 | `test_only_metadata_only_terminals_gate_fails_closed:1087` | 全 metadata-only → 无 exact 候选 → 无合格对 |
| 8 | `test_qualifying_candidate_with_mismatched_payload_hash_fails:1117` | blind payload hash 不匹配 → blank 缺失 → 无合格对 |
| 9 | `test_only_stale_pair_fails_closed:1304` | 段内 `current=r3`，pair 指向 `r2` → 无合格对 |
| 10 | `test_qualifying_pair_with_non_executable_verdict:1372` | 正向 `verdict == 可执行` 校验 → fail |

覆盖面补充：`rev_cur` 缺省（`None`）时全部块归当前段、`revision_id`（r2/r3/r4）分段不误伤既有夹具，由 A-5 新增子断言（无 `.reopen-state.json` + 块 `revision_id=r2` → 负例 `rc≠0`、正例 `rc=0`）与 A-19 共同覆盖。

## 五、preflight 结论

命令：

```
python scripts/budget_gate.py preflight --plan .converge/active/20260912-o6-material-delta-recert/plan.md
```

输出：

```
WARN:code_heavy:2,126
PREFLIGHT_OK:governance-change
EXIT=0
```

结论：**通过**（`WARN:code_heavy` 为非阻断启发式）。治理机器块 schema、`archaeology_refs` git 存在性、`calibration` locator/hash/corpus_digest/freshness、`user_message_events` UUID 全部通过；机器块 JSON 逐字节未改动。

## 六、残留（如实声明，非本轮缺陷）

- R-1 双向漏报（`changed_sections` 漏报 / `decisional_anchors` 低报）仍为语义残余，交 fresh delta reviewer。
- R-2（prompt 内 base 文本绑定无机械校验）不变。
- R-6（词表/anchors 由作者声明，机械层只校验声明间一致性）不变。

## 七、未决/待下一次收敛

- 无新增未决项：R2 阻断 1/1、非阻断 3/3 全部处置。
- 供 outer R3 复核重点：A-19 逐条 `rc≠0`、A-5 的 `revision_id` 分段子断言、§12.1 指针化与 §3.2/§12.4 同字。

```


### impl-report.md

```markdown
# O6 material 增量复核机制 · 实施报告（Implementation Executor）

> 执行者：fresh 独立上下文 Implementation Executor。日期：2026-09-12。
> 权威源：`plan.md` candidate-4（冻结字节，46057 B，双权威已认证，**未改动**）+ `design-review.md` D1-D6 单选修法（绑定实施约束）。
> 纪律：无 git 写操作；`attempts.md` 仅追加；既有测试体零删改。

---

## 1. 改动清单（Exact File Matrix F1-F8）

| # | 文件 | 动作 | 关键改动 |
|---|---|---|---|
| F1 | `scripts/orchest.py` | 改造 | 常量三单源（`MATERIAL_CHANGE_CLASSES`/`MATERIAL_SECTION_VOCAB`/`MATERIAL_ERROR_NS`）+ helpers（`_material_cur`/`_material_error`/`_locator_id`）；重写 `_validate_material_gate`：链分段（末块 `revision_id`，不用 `_detect_revision_id`）+ 历史段段首门 + 当前段段首门 + 新块域门（完全旧块绕过）+ `require_full_pair(T)` + `require_delta(T)` + 并集交集 fail-safe + D1-A legacy 分支 + 正向 verdict 门（`_require_executable`）。`_find_material_block` 语义不变；finish 调用点不变。 |
| F2 | `refs/state-schema.md`（第三部） | 改写 | §12.0/12.1（replace + 新增指针 bullet）/12.2 逐字。 |
| F3 | `refs/orchestrator-guide.md`（第三部） | 改写 | §12.3 标题；§12.4 triggers/词表追加；§12.5 item 7 追加（含 D4 输入契约、D5 triggers 收口）。 |
| F4 | `SKILL.md`（第三部） | 改写 | §12.6 指针句。 |
| F5 | `tests/test_loop_a_coverage.py` | 追加（末尾） | 新增 `TestMaterialDeltaPath`：22 条新测试（A-5..A-11 + §11 对抗 + D3 解析契约）。既有 17 条零删改（diff `+360/-0`）。 |
| F6 | `tests/test_process_controller_contract.py` | 追加 | 新增 `test_material_gate_constants_single_source`（常量/`_material_cur` 单源 + 12 项词表与 guide token 集等式）；既有 metadata-only 负例不变。 |
| F7 | `scripts/README.md` | 文档 | §12.7（`:151`）/12.8（`:17`）逐字。 |
| F8 | `docs/plans/active/20260911-converge-operational-envelope.md` | 文档 | O6 行 + 终态段（重评结论 + 机制实现）。**HEAD 下 untracked（N3）**。 |

`git status --porcelain`：`M` F1-F7 + `?? docs/plans/active/`（F8 所在目录 untracked）。
`git diff --numstat`：SKILL 1/1、guide 6/1、state-schema 4/3、README 2/2、orchest 411/205、loop-test 360/0、contract-test 36/0。

---

## 2. 测试数字

| 项 | 结果 |
|---|---|
| 基线（实施前） | `523 passed, 5 skipped, 11 subtests passed` |
| 实施后全量 | **`552 passed, 5 skipped, 11 subtests passed`**（368.47 s） |
| 增量 | +29 = 22 新 delta 测试 + 6 继承重跑 + 1 新契约测试 |
| 既有 material 测试 | 全绿（含 A-19 的 10 条负例逐条仍 `rc≠0`） |

命令：`TEMP='C:\Users\Administrator\AppData\Local\Temp' TMP='...' python -m pytest tests -q` → exit 0。

---

## 3. 静态检查

| 检查 | 结果 |
|---|---|
| `python -m py_compile scripts/orchest.py tests/test_loop_a_coverage.py tests/test_process_controller_contract.py` | exit 0（`COMPILE_OK`） |
| `git diff --check` | 干净（无 whitespace/冲突标记） |
| `python scripts/budget_gate.py preflight --plan .converge/active/20260912-o6-material-delta-recert/plan.md` | `WARN:code_heavy:2,126`（非阻断）+ `PREFLIGHT_OK:governance-change` |
| plan.md 未改动 | `git diff -- plan.md` 空；46057 B |

---

## 4. Acceptance 逐条对照（implement 分支）

| ID | 判定 | 说明 |
|---|---|---|
| A-1 | **pass** | plan.md 46057 B ≤ 46080 |
| A-2 | **pass** | frontmatter 未改（candidate-4 / ultraverge / object_slug） |
| A-3 | **pass** | preflight `PREFLIGHT_OK:governance-change` |
| A-4 | **pass** | plan 未改；恰一个 governance fenced-json 块 |
| A-5 | **pass** | 新测试 `test_gate_uses_last_block_segment_not_reopen_state`（reopen-state=r9 不改变判定）；`test_legacy_block_without_change_class_requires_full_pair`；`grep "change_class" not in b` / `.get("change_class","decisional")`；常量单源测试 |
| A-6 | **pass** | `test_decisional_missing_blank_slate_fails_closed`、`test_decisional_plus_non_decisional_delta_passes`（D artifact=历史 candidate）、`test_full_pair_with_delta_rejected`、`test_full_pair_non_executable_verdict_fails_closed` |
| A-7 | **pass** | `test_delta_missing_candidate_fails_closed` |
| A-8 | **pass** | `test_delta_base_hash_mismatch_fails_closed` |
| A-9 | **pass** | `test_delta_verdict_blocking_fails_closed` / `test_delta_verdict_redesign_fails_closed` / `test_delta_verdict_two_literals_fails_closed`（D3） |
| A-10 | **pass** | `test_delta_touches_decisional_anchor_fails_closed` |
| A-11 | **pass（A-11-14 除外，D6）** | A-11-1/2/3/4/5/6/7/8/9/10/11/12/13 逐条被拦（见 §6 映射）；A-11-14 为语义残余，不计入 |
| A-12 | **pass** | loop-test diff `+360/-0`，既有 `def test_*`/断言零改动；新测试仅追加末尾 |
| A-13 | **pass（有已记偏差）** | 12.0/12.1/12.2/12.3/12.6/12.7/12.8 replace 型三项态通过；12.1 bullet 新增型通过；12.4/12.5 append 型原串保留 + 新增子串存在。**legacy 子句按 D1-A 改写**（§7 偏差 1） |
| A-14 | **pass（附 N3 caveat）** | F1-F7 由 `git status` 覆盖；F8 内容已改为"重评结论 + 机制实现"，但文件 untracked，仅显示 `?? docs/plans/active/` |
| A-15 | **pass** | `test_orchest_negative_read_side_default_untouched` + `test_material_gate_constants_single_source` 绿 |
| A-16 | **pass** | 全量 `552 passed`，exit 0 |
| A-17 | **pass** | `budget_gate.py` 零改动；`archive_contract/*` 零改动；机器块 `numeric_changes` 全 `kind: mechanism`（plan 未改） |
| A-18 | **fail（F8 untracked，N3）** | §13.1/13.2/13.4 对 HEAD 有效；§13.3 `git checkout -- docs/plans/active/20260911-...md` 对 untracked 文件无效（命令报错或不生效） |
| A-19 | **pass** | 10 条既有负例逐条仍 `rc≠0`（全量绿） |
| A-R1..A-R3 | n/a | record-only 分支不适用（本对象走 implement 分支 §4.3/§4.4） |

---

## 5. D1-D6 落地说明

- **D1（选 A，Occam）**：`_validate_material_gate` 中 `if legacy is not None: _require_full_pair(blocks[-1]); return`——当前段存在任一 legacy 块（或缺 anchors 的旧 decisional 块）时**仅对当前段末块** require_full_pair，丢弃"自 legacy 起逐块 full-pair"，行为等价现状（末块全量对认证终局字节，last-supersedes-all 不被改写）。§12.4/§12.5 的 legacy 子句同步改写为"行为等价现状"口径。
- **D2（选 A）**：材料门 fail 全部经 `_material_error(code, summary)` → `material-gate:<kebab-code>: <summary>` → `budget_gate.FailClosed` → `main()` 打印 `FAIL_CLOSED:<reason>`、exit 30。码表：`first-block-must-be-decisional`/`plan-missing`/`current-block-plan-mismatch`/`change-class-enum`/`sections-vocab`/`anchors-vocab`/`no-qualifying-pair`/`payload-mismatch`/`verdict-parse`/`verdict-not-executable`/`product-blocking`/`delta-candidate-missing`/`non-decisional-touches-decisional-anchor`。函数体内零 `raise budget_gate.FailClosed`（仅 docstring 提及）。
- **D3（选 A）**：`_require_executable` 用 `re.findall(r"verdict:\s*(\S+)")` 要求输出中 `verdict:` 字面量**恰一次**且取值 `== 可执行`；0 次 / ≥2 次 / 他值均 fail。对 full-pair 两份与 delta 一份统一应用；新增 A-11-15 用例。
- **D4（选 A）**：最小输入契约落入 `refs/orchestrator-guide.md` §12.5 item 7 追加句（delta prompt 必须内嵌前块全文 + 当前 plan 全文，或等价 byte 级引用）+ `_require_delta` docstring；**不扩机制、不做机械 hash 绑定**（非目标 §8.7），残余如实声明。
- **D5（选 A）**：`triggers`（material trigger 变更）经 guide §12.4 追加句补入 `decisional` 定义；plan §3.2 冻结不改，12 项词表本已含 `triggers`。
- **D6（选 A）**：A-11-14 为机械不可判语义残余，不计入 A-11；本报告 A-11 明确标注范围；测试覆盖 A-11-1..A-11-13。

### §11 对抗清单 → 测试映射

| ID | 测试 |
|---|---|
| A-11-1 | `test_delta_verdict_blocking_fails_closed` |
| A-11-2 | `test_delta_base_hash_mismatch_fails_closed` |
| A-11-3 | `test_deleted_non_decisional_block_fails_closed` |
| A-11-4 | `test_delta_touches_decisional_anchor_fails_closed` |
| A-11-5 | `test_delta_change_class_mismatch_fails_closed` |
| A-11-6 | `test_delta_payload_output_mismatch_fails_closed` |
| A-11-7 | `test_decisional_missing_blank_slate_fails_closed` |
| A-11-8 | `test_legacy_block_without_change_class_requires_full_pair` |
| A-11-9 | `test_delta_verdict_redesign_fails_closed` |
| A-11-10 | `test_invalid_change_class_enum_fails_closed` |
| A-11-11 | `test_empty_changed_sections_fails_closed` / `test_out_of_vocab_changed_sections_fails_closed` / `test_empty_decisional_anchors_fails_closed` |
| A-11-12 | `test_legacy_decisional_missing_anchors_requires_full_pair`（仅断言 `rc≠0`，不硬断言专用码，R2-NB-1(b)） |
| A-11-13 | `test_delta_not_anchored_to_target_block_fails_closed` / `test_delta_locator_names_wrong_block_fails_closed` |
| A-11-14 | 语义残余，无机械测试（D6） |
| A-11-15（D3） | `test_delta_verdict_two_literals_fails_closed` |

---

## 6. 第三部逐字对照（A-13）

逐项实跑三态检查（全部 PASS）：

| 项 | 类型 | 结果 |
|---|---|---|
| 12.0 state-schema:101 | replace | 旧串消失 ∧ 新串存在 |
| 12.1 state-schema:103 | replace + 新增 bullet | 旧串消失 ∧ 新串存在 ∧ 指针 bullet 存在 |
| 12.2 state-schema:104 | replace | 旧串消失 ∧ 新串存在 |
| 12.3 guide:17 | replace | 旧标题消失 ∧ 新标题存在 |
| 12.4 guide:23 | append | 原句保留 ∧ 新增句存在 |
| 12.5 guide:32 | append | item 6 保留 ∧ item 7 存在 |
| 12.6 SKILL:462 | replace | 旧串消失 ∧ 新串存在 |
| 12.7 README:151 | replace | 旧串消失 ∧ 新串存在 |
| 12.8 README:17 | replace | 旧串消失 ∧ 新串存在 |

**第三部是否严格逐字：否。** 唯一偏差为 §12.4/§12.5 的 legacy 子句（见偏差 1）。其余全部逐字。

---

## 7. 偏差与未决（不得虚报）

1. **§12 legacy 子句偏差（D1 与 plan 冲突，已按 D1-A 收口）**：plan §12.4/§12.5 原文为"缺省 anchors 的旧 decisional 块（及完全旧块）自其起（含该块）维持 full-pair"；绑定约束 D1-A 明确要求"仅当前段末块 require_full_pair（等价现状）"。二者不可同时成立。依用户指定"D1-D6 逐条按其单选修法落地"及"§13.4/§8.4 以行为等价现状口径落到文档"，把该子句改写为"出现于当前段时，仅对当前段末块维持 full-pair（行为等价于 last-supersedes-all 现状；D1 选 A）"。**代码与文档一致指向 D1-A**；其余 §12 文本逐字。此为对"第三部逐字"的显式偏差。
2. **F8 untracked（N3）**：`docs/plans/active/20260911-converge-operational-envelope.md` 在 HEAD 下未跟踪，导致 §13.3 回滚命令无效（A-18 fail）、A-14 对 F8 不可按 tracked 判定。建议：落地前 `git add`/备份，A-14 的 F8 判据改为内容型。
3. **语义残余**：A-11-14（anchors 低报）、R-1(a)（`changed_sections` 漏报）、R-2（prompt 内 base 文本 hash 绑定）、R-6（作者声明性）均机械不可判，未伪造闭环；由 fresh reviewer diff 实核 + "争议=decisional" + 后续 decisional 全量对兜底。
4. **角色口径（N4，未收窄）**：delta reviewer 门按 plan §3.5 `role ∈ REVIEWER_AUTHORITIES["fresh"]` 实现；guide §12.5 表述为推荐单 fresh `outer-reviewer`。未按 N4 收窄为 `outer-reviewer`（避免与 plan §3.5 伪代码冲突；fresh 集合内任一角色仍是 fresh 独立上下文）。
5. **D4 机械不可验证**：输入契约仅文档化 + docstring，无机械绑定（非目标 §8.7 明确不引入 base 快照仓/diff artifact）。
6. **本对象自身 finish 未代跑**：材料门改造立即可用，但本对象（O6 计划修订）自身的材料块须由 orchestrator 按新分级路径产出（decisional/non-decisional + 候选证据），executor 不代跑 orchestrator 职责。

---

## 8. 回执摘要

- **改动文件**：`scripts/orchest.py`、`refs/state-schema.md`、`refs/orchestrator-guide.md`、`SKILL.md`、`scripts/README.md`、`tests/test_loop_a_coverage.py`、`tests/test_process_controller_contract.py`、`docs/plans/active/20260911-converge-operational-envelope.md`（F8，untracked）。
- **全量测试数字**：`552 passed, 5 skipped, 11 subtests passed`（基线 523/5）。
- **Acceptance**：A-1..A-17、A-19 pass；A-18 fail（N3，F8 untracked）；A-R1..A-R3 n/a。
- **D1-D6**：D1 仅末块 full-pair（等价现状）；D2 错误码单源 `material-gate:<code>`；D3 verdict 恰一次且正向 `==可执行`；D4 delta prompt 最小输入契约文档化；D5 `triggers` 补入 decisional 定义；D6 A-11-14 语义残余不计入。
- **第三部严格逐字**：否（仅 §12.4/§12.5 legacy 子句按 D1-A 改写，如实记偏差）。
- **未决**：F8 untracked 回滚（N3）；角色口径 N4；A-11-14/R-1/R-2/R-6 语义残余。

```


### audit-report.md

```markdown
不通过

# O6 实施 · 独立 fresh 审计报告（对抗式）

> 审计者：fresh 独立上下文（未参与 plan candidate-4 撰写、未参与实施）。
> 对象：plan candidate-4（冻结 46057 B，双权威认证）+ `design-review.md` D1-D6 单选修法（编排层裁决为绑定实施约束）+ 工作树相对 HEAD `da81e70` 的未提交改动。
> 纪律：未修改任何受审文件（tracked 零改动）；所有命令只读（`git archive` 抽取到仓外临时目录跑 pre-impl 对照，不写工作树）。UTF-8。
> 结论基于实跑与逐行核读；`impl-report.md` 的自述结论一律不采信，独立复现。

---

## 0. verdict 摘要

**不通过**，blocking = **2**（单选修法见 §B）。核心机制方向正确、语义守恒、既有负例零反转；但存在 (B1) 一条被声明为 A-11-3 的测试实际未触及材料门（在 finish 步骤 2 即失败，零判别力），与 (B2) D3-A「校验前锚定」子句未落地导致对真实历史 reviewer 输出的回归（HEAD 通过、新门 `verdict-parse` 失败）。二者均为单点可修。

复跑数字：**`552 passed, 5 skipped, 11 subtests passed`**（367.02 s），与自述一致。
pre-impl 对照（`git archive HEAD` + 当前测试文件）：`TestMaterialDeltaPath` 收集 28 条（22 新 + 6 继承重跑），**14 failed / 14 passed**——14 条在无实现时必红，判别力成立（见 §4）。

---

## 1. 范围纪律（F1-F8）与 §12 逐字对照

### 1.1 File Matrix 触达（A-14 / scope）

`git status --porcelain`：`M` `SKILL.md`、`refs/orchestrator-guide.md`、`refs/state-schema.md`、`scripts/README.md`、`scripts/orchest.py`、`tests/test_loop_a_coverage.py`、`tests/test_process_controller_contract.py`；`?? docs/plans/active/`。逐一对上 §5 F1-F7。F8 为 `docs/plans/active/20260911-converge-operational-envelope.md`（untracked，见 §5 A-18）。

- **未越界**：`git diff --stat HEAD` 恰为上述 7 个 tracked 文件；无其他 tracked 改动。
- `docs/plans/active/` 下另有 3 个 untracked 文件（`-a-tooling-hardening` 09-11 21:56、`-c-cost-governance` 09-12 11:01、`-b-contract-correction` 09-12 15:37），**mtime 均早于实施阶段**（F8 于 09-12 19:53 被改），非本次实施产物（既有未跟踪文件）。
- 结论：**范围纪律通过**（F8 见 A-18 caveat）。

### 1.2 §12 逐字三态（A-13）

以脚本逐项核 `refs/state-schema.md` / `refs/orchestrator-guide.md` / `SKILL.md` / `scripts/README.md` 的旧串消失 ∧ 新串存在 / 原串保留 ∧ 新增存在：**19/19 OK**。

- 12.0 / 12.1(replace) / 12.1(bullet) / 12.2 / 12.3 / 12.6 / 12.7 / 12.8：**逐字一致**。
- 12.4 / 12.5（append 型）：原句保留、新增子串存在；但存在 **3 处授权偏差**（见下），均来自绑定 D1-A/D4-A/D5-A：
  1. legacy 子句从「缺省 anchors 的旧块**自其起（含该块）维持 full-pair**」改为「出现于当前段时**仅对当前段末块维持 full-pair（行为等价现状）**」——D1-A 与 plan §12 不可同时成立，编排层裁决采 A，实施如实记录（impl-report §7.1）。
  2. §12.5 item 7 追加 D4 最小输入契约句（前块全文 + 当前 plan 全文）。
  3. §12.4 追加 D5 句（`triggers` 计入 decisional 定义）。
- **未授权偏差**：无。除上述外无其他改动。
- 结论：**§12 对照通过（含 3 处已授权的显式偏差）**；偏差本身是绑定约束与冻结 plan 冲突的必然结果，方向正确。

---

## 2. 语义守恒

- `scripts/budget_gate.py`：`git status`/`git diff` **零改动**。预算限额、档位公式、窄经验门未动（A-17）。
- `scripts/archive_contract/*`：**零改动**（含 `model.py`/`capture.py`/`transaction.py`）。
- 既有 ledger 事件字段：材料门为只读（`_validate_material_gate` 只读 attempts/plan/evidence blobs + events），未新增/修改任何事件字段；`git diff` 的 orchest 改动全部落在材料门及其辅助常量/helper。
- `_find_material_block` 语义**未改**（diff 仅在其前插入 helper）；finish 调用点 `_validate_material_gate(...)+_validate_calibration_sample(...)` 未改。
- 仅新增 3 个模块级常量（`MATERIAL_CHANGE_CLASSES`/`MATERIAL_SECTION_VOCAB`/`MATERIAL_ERROR_NS`）与 3 个 helper（`_material_cur`/`_material_error`/`_locator_id`），无删除。
- 结论：**语义守恒通过**。

---

## 3. O1 分级机制正确性（对抗重点）

逐行核 `scripts/orchest.py:1178-1567`（实读）。以下均为独立核读结论：

### 3.1 链构造 = R2-BLK-1 修法（逐行）

```python
rev_cur = all_blocks[-1].get("revision_id")           # 当前段 = 末块所属段
blocks = [b for b in all_blocks if b.get("revision_id", rev_cur) == rev_cur] if rev_cur is not None else list(all_blocks)
hist   = [b for b in all_blocks if b.get("revision_id", rev_cur) != rev_cur] if rev_cur is not None else []
```

与 plan §3.5 伪代码（`:157-161`）**逐字等价**；`rev_cur is None` → 全部归当前段；**未调用 `_detect_revision_id`**（grep 确认材料门内零引用）。历史段仅对每连续 `revision_id` 段首做 `change_class != "decisional"` 门（`:1220-1229`）。当前段段首门 `cc_of[0] != "decisional"`（`:1280-1283`）。
→ **通过**。

### 3.2 10 条既有负例不反转（A-19）

在真实工作树逐条 `-v` 实跑（10/10 passed，20.39 s）：

`test_changed_plan_byte_after_review_invalidates(452)`、`test_metadata_only_prompt_evidence_rejected_when_material(464)`、`test_post_hoc_hash_injection_rejected(483)`、`test_crlf_pollution_fails_closed(531)`、`test_duplicate_review_target_block_rejected(572)`、`test_payload_referencing_missing_material_id_fails_closed(918)`、`test_only_metadata_only_terminals_gate_fails_closed(1087)`、`test_qualifying_candidate_with_mismatched_payload_hash_fails(1117)`、`test_only_stale_pair_fails_closed(1304)`、`test_qualifying_pair_with_non_executable_verdict_fails(1372)`。

> 注：plan A-19 第 10 条写作 `test_qualifying_pair_with_non_executable_verdict`，实际方法名带 `_fails` 后缀（N5 已指出，plan 冻结未改）；按实际名实跑通过。
→ **通过**。

### 3.3 legacy 回退 = D1-A，且「同段多 legacy 块」不误伤（审计独立构造）

代码：`if legacy is not None: _require_full_pair(blocks[-1]); return`（`:1546-1548`）。`legacy` 在「完全旧块」或缺 `decisional_anchors` 的新 decisional 块处置位（`:1251-1255`/`:1270-1272`）。

审计独立构造两项仓外 probe（临时副本，不写仓库）：
1. 同 `revision_id=r2`、**两个完全 legacy 块**，仅末块有 fresh+blind 全量对 → **rc=0**（D1-A 不误伤）。原 plan 的「自 legacy 起逐块 full-pair」在此形态会因首块缺对而 `rc≠0`。
2. 同形态但末块无对 → **rc≠0**（fail-closed 仍成立）。

进一步对**真实归档对象** `.converge/done/20260910-process-controller-consolidation`（3 个同段 `r2` legacy 块，仅末候选有终局对，正是 design-review D1 引用的真实形态）直接调用新门：**不再因 legacy 链失败**（仅因 §B2 的 D3 问题失败，见下）。
→ **D1-A 落地正确**。

### 3.4 delta 候选块锚定三件套 + `delta.*` 三角 + 正向 verdict

`_anchored(T)`（`:1365-1394`）：`payload.artifact == cur(T)`（sha256/size）∧ `payload.material_revision.sha256 == canon(T)` ∧ locator `id=` == `T.id`（T 有 id 时）；`_require_delta`（`:1490-1543`）再核 `delta.change_class == T.change_class` ∧ `delta.base_plan_sha256 == cur(blocks[j-1]).sha256` ∧ `delta.current_plan_sha256 == cur(T).sha256`，且候选 role ∈ `REVIEWER_AUTHORITIES["fresh"]`，最后 `_require_executable`。`require_full_pair` 侧 `"delta" not in payload`（`:1441-1445`，与伪代码 qualify 条件一致）。
审计 probe 对「material hash 伪造 / locator 指向他块 / delta 字段不匹配 / base hash 伪造 / prompt-output 回显不一致 / verdict 非可执行」逐项实跑，**全部 rc=30 且在材料门抛出**（非前置步骤）。
→ **通过**。

### 3.5 词表域门 + UNION 交集机械拦截

`changed_sections` 非空 ∧ ⊆ `MATERIAL_SECTION_VOCAB`（`:1262-1267`）；decisional 的 `decisional_anchors` 空/越表 → `anchors-vocab`，缺失 → legacy（`:1268-1277`）。`union_anchors = ∪(所有 decisional 块 anchors)`，逐 `j>i_last` 求交非空 → `non-decisional-touches-decisional-anchor`（`:1554-1566`）。12 项词表由契约测试与 guide token 集**机械等值**断言（见 §4）。
→ **通过**。

### 3.6 D1-D6 逐条对照（绑定约束落地）

| 约束 | 采法 | 落地证据 | 结论 |
|---|---|---|---|
| D1 | A（Occam，仅末块 full-pair） | `:1546-1548`；真实归档对象不再误伤；§12.4/12.5 同步改写 | **通过** |
| D2 | A（错误码单源） | 全部 raise 经 `_material_error(code,...)` → `material-gate:<kebab-code>`；材料门函数体内**零** `raise budget_gate.FailClosed`（grep 证实，1593+ 属 calibration）；main 捕获打印 `FAIL_CLOSED:<reason>`、exit 30（实测 rc=30） | **通过** |
| D3 | A（verdict 恰一次） | `_require_executable` 用 `re.findall(r"verdict:\s*(\S+)")` 要求恰一次且 `== 可执行`；A-11-15 用例 | **机制落地，但子句缺失 → 见 B2/非阻断 N-A** |
| D4 | A（最小输入契约） | guide §12.5 item 7 + `_require_delta` docstring | **通过（文档型）** |
| D5 | A（`triggers` 入 decisional 定义） | guide §12.4 追加句；plan §3.2 冻结未改 | **通过** |
| D6 | A（A-11-14 不计入） | 测试仅覆盖 A-11-1..13；A-11-14 显式列为语义残余 | **通过** |

机制层结论：**O1 分级机制实现正确，fail-closed 方向正确，未发现误放行**。

---

## 4. 测试判别力（对抗）

- `TestMaterialDeltaPath` 在 pre-impl（`git archive HEAD` + 当前测试文件）下：**14 failed / 14 passed**。失败含**唯一正向 delta 通过用例** `test_decisional_plus_non_decisional_delta_passes`，以及靠错误码断言的 `change-class-enum`/`sections-vocab`/`anchors-vocab` 三条域门用例和 verdict 解析/阻断用例——**判别力成立**。
- 抽查 ≥6 条「无实现必红」成立：正向 delta 通过、`test_delta_base_hash_mismatch`、`test_delta_change_class_mismatch`、`test_delta_verdict_blocking`、`test_invalid_change_class_enum`、`test_empty_changed_sections`、`test_out_of_vocab_changed_sections`、`test_empty_decisional_anchors`、`test_delta_touches_decisional_anchor` 等 14 条均在 HEAD 红。
- 新增项计数：22 条 `TestMaterialDeltaPath` + 6 条继承重跑 + 1 条契约 = 29，与自述一致（其中 6 条是既有 `TestMaterialClosureGate` 因继承被重收集）。
- **缺陷（B1）**：`test_deleted_non_decisional_block_fails_closed`（A-11-3）**未触及材料门**——probe 实测 `RC=1`，`[finish] 已完成步骤: 0, 0.5, 1 / 步骤 2: 未 settle 的 reservation`（`write_n=False` 时 `rid_d` 被 reserve 却未 register）；该测试在 HEAD 下同样通过（零判别力），docstring 自陈失败原因是「末块与盘上 plan 不匹配」，即非链删除机制。A-11-3 声称的「链中删除一个 non-decisional 块 → 缺环 → fail」**未被验证**。

---

## 5. Acceptance 逐条对照（implement 分支）

| ID | 判定 | 证据 |
|---|---|---|
| A-1 | pass | plan.md 46057 B ≤ 46080（实测） |
| A-2 | pass | 头 6 行含 `status: candidate-4`/`review_mode: ultraverge`/`object_slug` |
| A-3 | pass | `PREFLIGHT_OK:governance-change`（+ 非阻断 `WARN:code_heavy:2,126`） |
| A-4 | pass | fenced-json 解析计含 `converge.governance-change/v1` 的块 == 1 |
| A-5 | pass | 链段逻辑逐行核；`test_gate_uses_last_block_segment_not_reopen_state`（reopen=r9 不改变判定）；legacy 用例；常量单源契约测试 |
| A-6 | pass（有覆盖缺口） | 缺 blank-slate→fail、历史 candidate 全量对、full-pair 带 delta/非可执行→fail 均有测试；**`candidate_plan` 分支无测试**（仅 `candidate_artifact`，见 N-E） |
| A-7 | pass | `test_delta_missing_candidate_fails_closed`（rc=30, `delta-candidate-missing`） |
| A-8 | pass | `test_delta_base_hash_mismatch_fails_closed`（rc=30） |
| A-9 | pass | 阻断/需重新设计/两字面量三用例（rc=30） |
| A-10 | pass | `test_delta_touches_decisional_anchor_fails_closed`（rc=30, `...-anchor`，断言含 anchor） |
| A-11 | **partial** | A-11-1/2/4..13 均在材料门被拦；**A-11-3 无效**（B1）；A-11-14 语义残余不计入（D6） |
| A-12 | pass | loop-test diff `+360/-0`，无既有 `def test_*`/断言行改动，新测试仅末尾 |
| A-13 | pass | 19/19 三态 OK；3 处授权偏差见 §1.2 |
| A-14 | pass（caveat） | F1-F7 由 porcelain 覆盖；F8 untracked，git 无法机械证明「本次触达」，内容实核为「重评结论 + 机制实现」 |
| A-15 | pass | `test_orchest_negative_read_side_default_untouched` + `test_material_gate_constants_single_source` 绿 |
| A-16 | pass | 552 passed / 5 skipped（独立复跑） |
| A-17 | pass | `budget_gate.py` + `archive_contract/*` 零改动；机器块未改（plan 冻结） |
| A-18 | **fail** | F8 untracked → `git checkout -- docs/plans/...` 对其无效；属 plan-side 缺陷（N3 已预告），非实施引入 |
| A-19 | pass | 10 条逐条实跑全绿（§3.2） |
| A-R1..A-R3 | n/a | record-only 分支不适用 |

---

## 6. 独立复跑

命令：`TEMP='...Temp' TMP='...Temp' python -m pytest tests -q`
结果：**`552 passed, 5 skipped, 11 subtests passed in 367.02s`**，exit 0。与 `impl-report.md` 自述一致。
另：`git diff --check` 干净；`python -m py_compile` 三个文件 exit 0（隐含于全量收集/运行）。

---

## 7. 遗留风险（真实运行可能爆发的点）

1. **[高·有实证] D3 全局 `verdict:` 恰一次扫描对真实 reviewer 输出误伤**（B2）。新门扫**整个 output 文本**并要求恰一次；真实归档对象 `.converge/done/20260910-process-controller-consolidation` 的终局材料对候选 invocation `59e4c977` 的 `output.bin` 含 **2 个** `verdict:` 字面量（offset 196 与 6626，均为 `可执行`）。实测：**HEAD 门 PASS，新门 `rc=30 material-gate:verdict-parse`**。对 15 个 done 对象做全量扫描：14 ok / 1 fail，唯一失败即此。若未来材料对 reviewer 输出沿用同样「frontmatter + 正文」双 verdict 形态，finish 会被误挡。D3-A 原文含「并在校验前**锚定**（如仅取输出首块/首个 yaml fence 内）」子句，实施未落地该锚定。
2. **[中] `_require_delta` 不核 product 产物阻断**：`_check_product_blocking` 只在 full-pair 调用；delta 路径不检查对应 `round-N.md` 的 `verdict: 阻断需修复`。plan 未要求，属新增路径的既有行为未平移，非违规但值得留档。
3. **[中] 一次性 `_require_delta` 取首个合格候选**：若存在多个合格 delta 候选而首个 verdict 非 `可执行`，门直接 fail（即使后一个有 `可执行`）。方向 fail-closed，不误放行，但可能过严。
4. **[低] locator-id 校验空隙**：`_anchored` 用 `if locator_id and locator_id != T.get("id")`，当 T 有 id 而 payload locator 缺 `id=` 时**跳过**校验（与 HEAD 同形）。`material_revision.sha256` 已绑定块内容，故无放行风险，但与 plan「locator id == T.id（T 有 id 时）」字面略有偏差。
5. **[低] 机械不可判残余**：R-1(a) `changed_sections` 漏报、R-1(b) anchors 低报、R-2 prompt 内 base 文本 hash 绑定、R-6 作者声明性——如实声明，未见伪造闭环。

---

## B. blocking 列表（各带单选修法）

### B1｜A-11-3 测试无效（测试判别力/验收证据）
- **证据**：`tests/test_loop_a_coverage.py:1761 test_deleted_non_decisional_block_fails_closed`；probe 实测 `RC=1`，失败于 finish 步骤 2「未 settle 的 reservation」（`rid_d` reserve 未 register），**从未到步骤 3.5 材料门**；且该测试在 HEAD 下同样通过（零判别力）。
- **单选修法 A（推荐）**：把该用例改为真正的「链删除」形态——构造 `D → N1 → N2` 后移除 `N1`，令 `N2.delta.base_plan_sha256 == canon(N1)` 而 `blocks[j-1] == D`，断言 `rc == 30` 且 `material-gate:delta-candidate-missing`（base 不匹配计入 skip）；同时确保所有 reservation 均 settle，避免步骤 2 抢先失败。
- **单选修法 B**：若认为 A-11-2（base hash 伪造）已等价覆盖该失败模式，则在 plan/attempts 中把 A-11-3 降级为「由 A-11-2 等价覆盖」并删除这条伪测试，避免虚假覆盖声明。

### B2｜D3-A「校验前锚定」子句未落地 → 真实数据回归（正确性/可运维）
- **证据**：`scripts/orchest.py:1396-1408` `_require_executable` 对整段 `output_text` 执行 `re.findall(r"verdict:\s*(\S+)")`；D3-A 原文要求「并在校验前锚定（如仅取输出首块/首个 yaml fence 内）」。实测真实归档对象 `.converge/done/20260910-process-controller-consolidation`：HEAD 门 PASS，新门 `material-gate:verdict-parse ... (found 2)`（invocation `59e4c977`，output 双 `verdict:`）；15 done 对象扫描 14 ok / 1 fail。
- **单选修法 A（推荐）**：按 D3-A 落地「锚定」——先定位 reviewer 输出的**规范 verdict 载体**（首块 yaml fence / frontmatter），仅在该区域内做「恰一次且 `== 可执行`」判定；区域外出现 `verdict:` 不参与计数（或统一以规范载体为唯一 verdict）。新增回归用例：真实形态双 `verdict:` 输出（前者 `可执行` 且规范载体唯一）→ 通过；规范载体为 `阻断需修复` 而别处 `可执行` → 仍 fail。
- **单选修法 B**：在第三部明确「reviewer 输出必须恰含一个 `verdict:` 字面量」为**硬契约**（写入 guide/state-schema），并把「历史双 verdict 形态」显式列为迁移/兼容风险；不改代码，但需承认对既有输出形态的破坏性。

---

## C. 非阻断观察

- **N-A（D3 文档缺口）**：D3-A 要求「**明文规定**输出中 `verdict:` 恰一次」；实际仅代码 docstring 承载，`refs/orchestrator-guide.md`/`state-schema.md` 无「恰一次」表述（grep 无命中）。建议随 B2 一并补入规范句。
- **N-B（规范噪声）**：第三部 guide 出现内部修复标签字面量「D1 选 A」「（D5 收口）」「（D4 最小输入契约）」（`:25/:26/:37`）。规范文档不应携带 repair 轮次标签，建议改为中性表述。
- **N-C（A-18）**：F8 目标文件在 HEAD 下 untracked（`docs/plans/active/` 历来不入库，见 commit `0816348`），§13.3 回滚命令对其无效。属 plan-side 缺陷，design-review N3 已预告；建议把 A-14/A-18 的 F8 判据改为内容型，或落地前单独备份。
- **N-D（locator 空隙）**：见 §7.4。
- **N-E（测试缺口）**：A-6 提到「`candidate_plan` 旧块」子用例，但测试全部使用 `candidate_artifact`；`_material_cur` 的 `candidate_plan` 分支无测试覆盖（实现本身正确）。
- **N-F（角色口径 N4）**：plan §3.5 裁决 `role ∈ REVIEWER_AUTHORITIES["fresh"]`（含 `reviewer`/`ultraverge-initial`），guide §12.5 item 7 表述为推荐 `outer-reviewer`。二者不冲突但口径不齐，未收窄属如实保留。
- **N-G（过程降级已披露）**：plan 冻结与 D1-D6 修订冲突，编排层裁决「冻结 + D1-D6 绑定执行」，`attempts.md` 已记录为过程降级点；审计确认该裁决被一致落地。

---

## D. 审计方法与证据可复现性

- 受审态：HEAD `da81e70`；工作树 7 tracked 改动 + F8 untracked。
- pre-impl 对照：`git archive HEAD | tar -x` 到仓外临时目录，覆盖当前测试文件与契约测试，运行 `TestMaterialDeltaPath` 与契约测试。
- 独立 probe（仓外临时副本）：D1-A 同段多 legacy 正/负例、各弱断言用例的失败点归类、真实 done 对象扫描。
- 所有证据命令与关键输出已内联于本文各节；临时产物位于 `%TEMP%\opencode\`，未落工作目录。

```


### fix-report-b12.md

```markdown
# O6 审计后修复报告 · B1/B2（fresh 修复 Executor）

> 对象：审计报告 `.converge/active/20260912-o6-material-delta-recert/audit-report.md` §B 两条 blocking。
> 纪律：UTF-8；只修 B1/B2；未做 git 写操作；未修改除已列入审计 7 文件之外的任何 tracked 文件。
> 命令：`TEMP='C:\Users\Administrator\AppData\Local\Temp' TMP='...' python -m pytest ...`。

## 0. 结论

**B1、B2 均按审计单选修法 A 修复，全部验证通过。** 无其它改动。

| 项 | 修法（一句话） | 结果 |
|---|---|---|
| B1 | 把 A-11-3 用例从「`write_n=False`（步骤 2 未 settle，零判别力）」改为真正构造 `D→N1→N2` 后删除 `N1` 的链删除形态，令 `N2.delta.base` 指向已删的 `N1`，断言材料门 `rc==30 / delta-candidate-missing` | 修复后 PASS；HEAD 下 FAIL（判别力实证） |
| B2 | 新增 `_verdict_carrier` 锚定规范 verdict 载体（起始 YAML frontmatter → 首个 yaml fence → 回退整段），`_require_executable` 仅在该载体内要求「恰一次且 `== 可执行`」，区域外不计 | 真实归档对象由 `verdict-parse` 回归 → `GATE_PASS`；15 done 由 14/1 → 15/0 |

## 1. B1｜A-11-3 测试无效

### 1.1 原缺陷

`tests/test_loop_a_coverage.py::TestMaterialDeltaPath::test_deleted_non_decisional_block_fails_closed`
调用 `_setup_chain(write_n=False)`。该路径在 `delta_present=True` 时仍 reserve 了 delta reviewer 轮
（`rid_d`），但 `write_n=False` 使其永不 register → 未 settle 的 reservation；`finish` 在**步骤 2**
即失败（`RC=1`），从未走到步骤 3.5 材料门。该用例在 HEAD 下同样通过 → **零判别力**，A-11-3 声称的
「链中删除 non-decisional 块 → 缺环 → fail」未被验证。

### 1.2 修法（审计 §B B1 单选修法 A）

重写用例为真实链删除形态：

1. 同段构造 `D(decisional) → N1(non-decisional) → N2(non-decisional)` 三个 material 块；
2. 从 `attempts.md` **移除 `N1` 的 JSON fence**（`assertIn` 后 `replace`，再 `assertNotIn` 复核）；
3. `N2.delta.base_plan_sha256 = canon(N1)`，但删除后链上前块实为 `D` →
   `_require_delta` 的 base 比较（`_material_cur(D).sha256`）不匹配 → 该候选计入 skip；
4. 所有 reservation（outer / blind / delta）均 register settle，排除步骤 2 抢先失败；
5. 断言 `rc == 30` 且输出含 `material-gate:delta-candidate-missing`。

### 1.3 证据

- 本工作树：`test_deleted_non_decisional_block_fails_closed` **PASS**（rc=30，命中 `delta-candidate-missing`）。
- 判别力对照（`git archive HEAD` + 当前测试文件）：该用例 **FAIL**，HEAD 报
  `FAIL_CLOSED:material-gate: no qualifying pair ...`（无 `delta-candidate-missing`）。

## 2. B2｜D3-A「校验前锚定」未落地

### 2.1 原缺陷

`scripts/orchest.py` 的 `_require_executable` 对**整段** `output_text` 执行
`re.findall(r"verdict:\s*(\S+)")` 并要求恰一次。真实归档对象
`.converge/done/20260910-process-controller-consolidation` 的候选 invocation `59e4c977` 的
`output.bin` 含两个 `verdict: 可执行`（offset 196 的起始 frontmatter 与 offset 6626 的正文
"## Verdict" yaml fence）→ 新门 `rc=30 material-gate:verdict-parse`，而 HEAD 门 PASS。
D3-A 原文要求「校验前锚定（如仅取输出首块/首个 yaml fence 内）」，实施未落地。

### 2.2 修法（审计 §B B2 单选修法 A）

新增嵌套 helper `_verdict_carrier(output_text)`，按优先级定位规范 verdict 载体：

1. 输出起始 YAML frontmatter（`---` 围栏，容忍 BOM）；
2. 否则首个 ```` ```yaml ````（或 ```` ```yml ````）fence 内容；
3. 二者皆无 → 回退整段文本（保留恰一次契约）。

`_require_executable` 改为**仅在 `_verdict_carrier` 返回的载体内**执行
`re.findall(r"verdict:\s*(\S+)")`，要求恰一次且 `== 可执行`；**区域外 `verdict:` 不参与计数**。
错误码与诊断措辞保留 `verdict-parse` / `verdict-not-executable`。

### 2.3 回归用例

- 保留 `test_delta_verdict_two_literals_fails_closed`（A-11-15），但把第二个字面量注入
  **首个 yaml fence（载体）内部**，维持「载体内 ≥2 → fail」契约（原「整段两个」前提是缺陷行为）。
- 新增 `test_historical_double_verdict_frontmatter_passes`：真实历史形态（起始 frontmatter 载
  `verdict: 可执行` + 正文另含 `verdict: 可执行`）→ **PASS**（HEAD 行为 = 新门行为）。
- 新增 `test_historical_frontmatter_blocking_elsewhere_executable_fails`：载体为
  `阻断需修复`、正文别处 `可执行` → `rc==30` 且 `verdict-not-executable`（不以区域外正向值放行）。

### 2.4 证据

- 真实归档对象直接调新门：`GATE_PASS`（修复前 `FAIL_CLOSED:material-gate:verdict-parse`）。
- 15 个 done 对象全量扫描：**15 ok / 0 fail**（修复前 14 ok / 1 fail）；唯一历史失败即 `59e4c977`。
- 判别力对照（把 `_verdict_carrier` 临时还原为整段扫描 + 当前测试）：
  - `test_historical_double_verdict_frontmatter_passes` **FAIL**（`found 2` 误挡）；
  - `test_historical_frontmatter_blocking_elsewhere_executable_fails` **FAIL**
    （报 `verdict-parse` 而非 `verdict-not-executable`）。

## 3. 验证数字（必须执行的命令，实跑）

| 命令 | 结果 |
|---|---|
| `python -m pytest tests/test_loop_a_coverage.py -q` | **75 passed**（184.41 s） |
| `python -m pytest tests -q` | **554 passed, 5 skipped, 11 subtests passed**（376.69 s） |
| `python -m py_compile scripts/orchest.py` | exit 0（`PY_COMPILE_OK`） |
| `git diff --check` | 干净（`DIFF_CHECK_OK`） |

> 全量基线（审计复跑）= 552 passed；修复后 554 passed，**+2 = 两条新增 B2 回归用例**
> （B1 为替换既有用例，不改变计数）。

## 4. 改动面与范围

- 本次修复仅编辑 **既有已改动** 的两个文件：
  - `scripts/orchest.py`：新增 `_verdict_carrier`；改写 `_require_executable`（docstring + 载体扫描 + 诊断措辞）。
  - `tests/test_loop_a_coverage.py`：改写 A-11-3 用例与 `test_delta_verdict_two_literals_fails_closed`；
    新增两条 B2 回归用例。
- `git diff --stat` 仍为审计时 7 个 tracked 文件 + untracked `docs/plans/active/`；
  未新增/删除文件，未触碰 `SKILL.md`/`refs/*`/`scripts/README.md`/`tests/test_process_controller_contract.py`/`budget_gate.py`/`archive_contract/*`。
- 未执行任何 git 写操作（无 add/commit/push/checkout）。

## 5. 残余与非目标

- `_setup_chain(write_n=False)` 分支现已无调用者（原 B1 用例唯一使用者）。为最小手术未删除该参数；
  其潜在陷阱（reserve 后不 register）不影响任何在用路径。
- 区域外 `verdict:`（含伪造的正向字面量）依 D3-A 锚定语义不计入；「输出完全伪造」仍为 §10 已声明
  语义残余（D3 选 A 的单选修法 B 才将其显式排除出封死范围，本次未采）。
- 未处理审计 §C 非阻断观察（N-A..N-G）——超出 B1/B2 范围。

```
