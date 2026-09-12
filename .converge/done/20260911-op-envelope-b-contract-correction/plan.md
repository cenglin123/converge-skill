---
status: candidate-8
created_at: 2026-09-12
updated_at: 2026-09-12（candidate-7 → candidate-8：设计复审 MF-1..MF-4 逐条落地；修订历史见文末）
review_mode: ultraverge
scope:
  - converge-skill
depends_on:
  - 20260911-op-envelope-a-tooling-hardening（已完成并归档，`.converge/done/20260911-op-envelope-a-tooling-hardening`）
object_slug: 20260911-op-envelope-b-contract-correction
---

# 子计划 B · 归档契约更正语义（O1）+ 治理信封默认（O5）（O3/O6 处置记录，不实现）

> 2026-09-12 用户裁决：撤销独立子计划 C，把 O5（治理信封默认）并入本对象一并 ultraverge 收敛。
> 本文件是 **candidate-8**：candidate-2 是 fresh Plan Repair Executor 对三票初审（`uv-init-1/2/3.md`）的合并处置产物；
> candidate-3 是 fresh Plan Repair Executor 对 outer R1（`round-1.md`）3 条阻断 + 5 条非阻断的处置产物；
> candidate-4 是 fresh Plan Repair Executor 对终局设计审查（`design-review.md`）M1–M6 与 outer round-2（`round-2.md`）R2-1..R2-8 的处置产物（逐条见 §0.4/§0.5 与文末「修订历史」）。
> candidate-5 是 fresh Plan Repair Executor 对第二权威盲审 `blind-recheck-2.md` I-1..I-7（三条 high + 四条 low）的处置产物（逐条见 §0.6 与文末「修订历史」）。
> candidate-6 是 fresh Plan Repair Executor 对第二权威盲审 `blind-3`（原件已被 blind-4 错位评审覆盖、不可恢复）Issue-1..4 与观察 a/b 的处置产物；candidate-7 是对 **blind-4**（现文件名 `blind-recheck-3.md`，错位评审；内容为对 candidate-6 的第 4 次盲审）Issue-1..4 + O-0 的处置产物（逐条见文末「修订历史」与 `attempts.md` §十三/§十四）。
> candidate-8（本版）是对**设计复审**（现 `design-review.md`，verdict=设计需修订）MF-1..MF-4 的处置产物（逐条见文末「修订历史」与 `attempts.md` §十五；原 M1–M6 评审原文已被同名覆盖，其单选修法处置留档于 §0.4 与 `attempts.md`）。
> 所有 `文件:行` 引用以 2026-09-12 HEAD `13da6055f173ab1459f62cb36de11bb05b2b19cc` 工作树实核为准（核验日期 2026-09-12）。
>
> **编排层已定裁决（S1–S5，必须执行）**：S1 删除 D2/O3（自指 bootstrap 通道）→ 处置记录；S2 O6 定案 record-only；
> S3 保留 D1（O1 更正事件）并改造；S4 保留 D3（O5 治理信封默认）并改造，两族机制按独立 Track 组织；
> S5 本计划自身内嵌 `converge.governance-change/v1` 机器块并自验 preflight。详见 §0。

---

## 0. 三票合并处置矩阵（编排层裁决 S1–S5）与修订摘要

### 0.1 S1–S5 落实表

| 裁决 | 内容 | 落实位置 | 依据（UV 票） |
|---|---|---|---|
| S1 | 删除 D2/O3（自指 bootstrap 通道整体移出实现），改“处置记录”：O3 结论 = 自指修复合法时序为「最小修复先落地 → fresh 审计验收 → 对象归档」，r2 已实践且归档成功，不存在被死锁拒绝的操作；bootstrap 通道 record-only | §4、§13；删除原 D2 §3、原 F7、原 F8⑤、原 G4、原 Phase 3、原 A13/A14、原 R2、原 §10 O3 组 | UV3-1(conceptual)、UV2 I2-2/I2-3/I2-4、UV1 B2/N12 |
| S2 | O6 定案 record-only：删除“裁决为实现则实施”分支；D4 改写为处置协议“评议已定：不实现”，给出理由结构（缺真实复现样本 + 首轮双审成本未实证超阈）；保留“何时应重启该议题”判据清单 | §3 D4、§4、§14；删除原 F9:17-36 条件修改、原 B4 实现分支、原 Phase 5 实现分支 | UV1 B4、UV2 I2-6、UV3-16 |
| S3 | 保留 D1（O1 更正事件）并按逐条修复要求改造 | §3 D1、§5 Track-1、§6、§7 Track-1、§8 Track-1、§11、§12 | UV1 B3/N5/N6/N11/N13/N14、UV2 I2-1/I2-7/I2-15、UV3-6/7 |
| S4 | 保留 D3（O5 治理信封默认）并改造；两族机制按独立 Track（Track-1=O1，Track-2=O5）组织，各有 File Matrix 行组/Phase/Acceptance；写“为何不拆对象” | §3 D3、§4、§5、§7、§8 | UV3-16 建议拆分 → 以结构化 Track 回应用户已裁决的合并 |
| S5 | 本计划自身合规：内嵌 `converge.governance-change/v1` 机器块；`execution_authorization=ab8896b1-...`（sequence 9）、`quality_goal=06754e6f-...`（sequence 10）；`numeric_changes` 用 `kind: mechanism`；真实完整 SHA；`counterevidence_refs: []`；`change_id: op-envelope-b`；calibration 引用 `distill_antipatterns.py --calibration` **真实生成**的报告（candidate-3 落实 R1-3；candidate-4 复跑自验见新增「修订历史」节与 `attempts.md`） | §15 附录 A；生成报告落盘 `evidence/calibration-report.json`，canonical fenced 载体在 `attempts.md`；preflight 自验输出见 `attempts.md` | UV1 N8、R1-3 |

### 0.2 逐票 issue 处置索引（完整处置表见 `attempts.md`）

- **UV1**：B1→§6/§7 Track-2（21 处穷举，17 受影响）；B2/N12/UV3-1/UV3-2/UV3-12→S1 删除；B3→§3 D1 有效视图定界；B4→S2；N1/UV2 I2-11/UV3-10→删除“grep=0”（§2）；N2/UV2 I2-12/UV3-9→§2 改 :97-100；N3→§2 改抛出点 :705；N4/UV2 I2-13→§5 F2 删 `__all__`；N5/UV3-7→§3 D1 引用字段归属；N6→§3 D1/§8 A1-7 INDEX omit-when-empty；N7/UV2 I2-9/UV3-3→§3 D3 触发谓词；N8→§15；N9/UV2 I2-14→§7 Phase 0；N10/UV2 I2-8/UV3-8→§3 D3 数值依据；N11→§3 D1 授权绑定；N13/UV2 I2-15→§3 D1 `validate_event` 分支；N14→§3 D1 命名锁定；UV1 拆分建议→§4；I2-1→§3 D1 闭包重设计；I2-5/UV3-4→§6；I2-7→§3 D1 单层施加点；I2-3/I2-4→S1；I2-6→S2；I2-10/UV3-11→S1 删除（不再引入新 bootstrap 命名）；I2-16/UV3-13→§12 逐字对照；UV3-5→§3 D3 active-dir 生命周期；UV3-6→§3 D1 批量机械化；UV3-14→§3 D3 opt-out；UV3-15→§3 D3 谓词修正；UV3-16→S2/§14。

### 0.3 outer R1 处置索引（完整处置表见 `attempts.md`）

- **R1-1（阻断，事实失真）**：r2 `terminal-decision` 实数实核为 **3 条**（seq 17/45/54），D1 立身用例推导链第 3 步已按全事件流机械求值重写（§3 D1 步骤 3）。
- **R1-2（阻断，Acceptance 自相矛盾）**：A-S4 已补 `--active-dir`；§8.4 给出全部「命令 + 期望 exit 0」条目与 Track-2 门禁的交互复核表。**该 `--active-dir` 处置已被 M6 取代**：candidate-4 取消 `--active-dir`、改以 `plan.parent` 读 state，A-S4/§8.4 同步重写。
- **R1-3（阻断，治理自举）**：改用 `distill_antipatterns.py --calibration` **真实生成**的报告（`corpus_digest=ff64a62b…`、`eligible_samples=0`），删除「bootstrap 内嵌块」表述（§5.3 S-F7、§15；生成命令与输出见 `attempts.md`）。
- **R1-4..R1-8（非阻断）**：§12 逐字补全（5 行）；§3 D1 有效视图派生面显式行号；§7/§8/§11「4 处零改动」精确化；§10 R8 记录全量测试环境事实。**R1-5 的规则 10 谓词映射已被 M4 取代**（删除映射表与 `_validate_field_value`，单源 = 规则 10b 的完整 `validate_event`）。

### 0.4 设计审查 M1–M6 处置索引（单选修法，逐条落地；完整记录见 `attempts.md`）

- **M1（有效视图覆盖不完整：capture 写入前判定仍读 raw）**：提升为「写入期与归档期共用同一 `resolve_events`」——`_prepare_terminal_decision`（`capture.py:523-575`）与 continue-parent 查找（`capture.py:332-340`）在入口先 resolve 再派生/判定，raw 仅用于身份/字节/哈希读取；Acceptance 增 A1-11（更正先于 decision → capture 与 archive 结论一致）。
- **M2（出边结构字段边界未定义/未测试）**：新增最小结构引用集 `invocation-terminal.started_event_id`、`invocation-started.parent_event_id`、`design-review-completion.invocation_event_id` 一律不可更正（`reservation_id` 保留可更正，立身用例）；三者各加一条拒绝 + `correction-field-not-allowed` 对抗用例（A1-12/13/14）。
- **M3（更正自身无修复/取代路径）**：规则 7 改为「后更正取代先更正的 effective 值」——允许同 `(target, field)` 追加，其 `original_value` 必须等于**当前 effective 值**，每条独立授权；raw append-only；披露列出全部更正及取代关系（A1-15/16）。
- **M4（规则 10 谓词表与 10b 重复）**：删除规则 10 的字段映射表与 `_validate_field_value` 抽取，仅保留「应用全部更正后运行完整 `validate_event`」（原规则 10b）为唯一值/跨字段谓词来源；`original_value` raw 逐字相等校验保留。
- **M5（授权缺少内容绑定）**：`authorized_by` 所指 `user-message` 的 `user_quote` 必须**同时**包含 `corrected_event_id` 逐字子串与被更正 `field` 名（或逐字 `corrected_value`），否则 `correction-unauthorized`（A1-17；blind-4 Issue-1 收紧，**删除原 `reason` 子串分支**）。
- **M6（O5 门禁旁路与审计闭环）**：**取消 `--active-dir` 参数**，改以 `plan.parent`（被检 plan 的父目录）作为对象 active 目录读取 state（消除任意目录旁路、免去 21 处 helper 迁移、删除 A2-5 类负例）；opt-out reason 持久写入对象 `_budget-state.json` 顶层 `envelope_opt_outs`（选定此载体，无非 gate-ledger 分支），不只打印 WARN（A2-11/12）。

### 0.5 outer round-2 R2-1..R2-8 处置索引（非阻断建议，已一并落进 plan）

- **R2-1**：A1-1 期望列改「非新增失败」（对齐 §8.4）。
- **R2-2**：A-S2 删除「≥480」，改「通过数 ≥ 改造前同环境基线通过数」。
- **R2-3**：§6.2 行 19 早返回行号改 `:1767-1768`（legacy 分支 CRLF 检查）。
- **R2-4**：§12 `state-schema.md:60`「原文」补全为完整逐字原行；标题限定为「逐字定位片段（无省略号）」。
- **R2-5**：§3 D1 步骤 3「三条 source_ref 全为 null」改「三条均无 `source_ref` 键」。
- **R2-6**：§3 D1 批量不可表达补值谓词归因（`corrected_event_id` 单 UUID、`field` 单字符串 ∈ `allowed`）。
- **R2-7**：T1-F2 锚点 `:523-554` 改 `:523-575`。
- **R2-8**：`DECISION_REFERENCED` 边界写死为「被 4 个 decision 字段**直接**引用」；不含经 `started_event_id` 间接关联的 started（后者可更正）。

### 0.6 blind-recheck-2 I-1..I-7 处置索引（第二权威盲审，单选修法逐条落地；完整记录见 `attempts.md` §十一）

- **I-1（high，事实失真）**：A1-1 单文件基线由 `4 failed/476 passed` 改为本机实测 `4 failed/97 passed/2 skipped`；全量基线留在 A-S2（A1-1 命令保持单文件，删除误挂的全量数字）。
- **I-2（high，自洽性/事实）**：取建议 (a)，新增显式常量 `CORRECTION_EVIDENCE_FIELDS`（`prompt_evidence`/`output_evidence`/`source_locator`/`snapshot`）并入「不可更正集合」；§3 D1 `allowed()`、§11 O1.10/17、§12 `:42` 同步；删除「会被 `validate_event` 拒绝」失真表述。
- **I-3（high，闭包不完整）**：`record_correction` prepare 钩子对 `raw + [pending]` 跑**完整有效视图校验**（`validate_event_graph` 含 reviewer-verdict authority + `validate_ledger`，非仅 `validate_corrections`）；加两条对抗用例 A1-19（reviewer started.role 不得落盘）/A1-20（不得使既有 user-decision 的 `presented_degradations` 重算失配）。
- **I-4（low，自洽性）**：§12 标题行 `state-schema.md:60` 由「完整原行的逐字前缀」改「完整逐字原行」（588=588，逐字相等）。
- **I-5（low，实现陷阱）**：写死门禁 opt-out 持久化路径 = 直接 `read_state`→改 dict→`write_state(plan.parent, state)`，**绕过 `initialize_state` 的 `needs_write`**；同步 R13 与 §6.2。
- **I-6（low，覆盖缺口）**：§8.2 增 A2-13「`_budget-state.json` 存在但损坏」负例；统一失败语义写死：捕获 `read_state` 异常（含 `state_corrupt:*`）→ 映射为 `FAIL_CLOSED:governance_requires_task_envelope`（`state_corrupt:*` 仅作内部 detail）。
- **I-7（low，措辞）**：§15/§16 明确 fenced 块与独立文件**仅在 canonical 形式下逐字节一致**（raw body sha `9a08eb6e…` ≠ canonical `c4755e…`）；注明独立文件不被 preflight 机械校验、仅作证据留痕。

---

## 1. Goal

本对象只做两件事，且两件事互不共享代码路径（见 §4）：

1. **O1（归档契约更正语义）**：让 append-only 归档契约在不改写任何历史字节的前提下，容纳「编排层记录错误」的合法、显式、可审计、单字段的更正；校验一律经有效视图，manifest 冻结披露更正值且保留 raw 字节哈希。
2. **O5（治理信封默认）**：让「含 `converge.governance-change/v1` 机器块的计划」在 preflight 时默认要求对象 active 目录已配置可用的 task-envelope，并提供显式、审计可见的 opt-out。

**处置记录（不实现）**：O3（自指 bootstrap 通道）按 S1 记录结论、不再设计；O6（material 增量复核）按 S2 定案 record-only、不新增机制。

对应决策：D1=O1（保留并改造）、D2=O3（删除，记处置）、D3=O5（保留并改造）、D4=O6（record-only）。

---

## 2. 证据（全部经本作者 2026-09-12 实核；行号即当前 HEAD 工作树值）

> 修正说明：candidate-1 中少数断言失真，本表给**实核值**并在「修正」列注明；凡未实核者不写入决策依据。
> 本次核验删除 candidate-1 的 `grep -rin "disclosed_correction" = 0` 断言（该词在本计划草案与 `docs/plans/active/` 草案中 self-reference 命中，UV1 N1 / UV2 I2-11 / UV3-10）。

### 2.1 O1 依据（归档契约封闭性）

| # | 断言 | 实核位置 | 实核结论 | 修正 |
|---|---|---|---|---|
| O1a | `EVENT_TYPES` 恰为 6 类，无更正类型 | `scripts/archive_contract/model.py:21-24` | 已核：`invocation-started/invocation-terminal/artifact-captured/terminal-decision/design-review-completion/user-message` | 一致 |
| O1b | `EVENT_FIELDS` 定义 6 类事件字段集 | `model.py:178-205`（`COMMON_EVENT_FIELDS` :178，`EVENT_FIELDS` :179-205） | 已核 | 一致 |
| O1c | `validate_event` 为封闭等集（extra/missing 即拒绝） | `model.py:437`（定义）、`:445-455`（terminal-decision 二次特化）、`:456-458`（等集判定） | 已核 | 一致 |
| O1d | event graph 校验 | `model.py:958-1037` | 已核 | 一致 |
| O1e | ledger 配对 binding | `model.py:642-644`（`ledger-binding-missing`） | 已核 | 一致 |
| O1f | ledger status 配对，`cancelled+pre_execution=True` 可配 failed | `model.py:678-686`（含 :679-682） | 已核 | 一致 |
| O1g | 全仓无 `event-correction`/`correction` 事件类型，无相应字段 | `EVENT_TYPES`/`EVENT_FIELDS` 实核无；`disclosed_correction` 一词仅出现在 `docs/plans/active/20260911-op-envelope-b-contract-correction.md:25` 草案散文与本计划引述中，**不构成契约机制** | 已核（修正 candidate-1 的“=0 命中”裸断言：该断言失真，已删除） | 删除“grep=0”（N1/I2-11/UV3-10） |
| O1h | 事故：r2 事件 55 `reservation_id` 记录为 `PENDING`，由用户授权披露式更正 | `.converge/done/20260910-process-controller-consolidation/evidence/events/00000056-bbdffdc8-....json`（`user-message`，`host_message_id=opencode-20260911-event55-correction`，`user_quote=授权披露式更正：把事件 55 的 reservation_id 从 PENDING 改为真实存在的 81a2537ea9eb`）；事件 55 现值为 `81a2537ea9eb` | 已核：事故与授权留痕真实存在；**当前树事件 55 已是更正后字节，仓库内无法独立证实曾存在的 `PENDING` 字节**（git 该文件仅一次提交 `529e691`） | 立身用例按事件 56 的授权文本重放（见 §3 D1） |
| O1i | 先例：`--declare-orphan-reservation` 披露机制 | `scripts/archive_convergence.py:291-294` → `model.py:884-893`（`acknowledged_orphan_reservations`，omit-when-empty） + 降级串 `model.py:656-666` | 已核 | 一致 |
| O1j | `validate_archive` 以 **raw** events 直接调用 `validate_event_graph`/`validate_ledger` | `model.py:1178-1181`（`load_events` → `validate_event_graph(events)` → `_verify_evidence_bytes` → `validate_ledger`）；`:1185-1188` 才 `project_manifest` | 已核；这是 candidate-1「有效视图」未定界、`check` 仍会失败的根因 | 新增（I2-7） |
| O1k | `capture.py` 无 `__all__`；`archive_convergence.py` record-* 子命令 parser 在 :286-287、main dispatch 在 :360-362 | `grep __all__ scripts/archive_contract/capture.py` 无命中（仅 `scripts/archive_contract/__init__.py:5` 有）；`archive_convergence.py:286-287`（`record-user-message` parser）、`:360-362`（dispatch） | 已核 | 修正 F2/F3（N4/I2-13） |
| O1l | capture 写入前判定以 **raw** `existing` 派生/授权（M1 缺陷面） | `capture.py:523-575`（`_prepare_terminal_decision`，函数体至 :575）；`:509-520`（`derive_decision_fields`）；`:560`（`validate_reviewer_verdict_authority(existing, values)`）；`:566-574`（user-decision-source quote 匹配） | 已核：写入期与归档期可能看到不同事实（写入期 raw、归档期 effective），会把一条合法更正后的字段判定成 `decision-derived-field-conflict`/`user-decision-source` 等「永久 fail-closed」失败 | 新增（M1） |
| O1m | continue-parent 查找读 **raw** events（M1 缺陷面） | `capture.py:332-340`（`begin_invocation` 的 `invocation_kind == "continue"` 分支：`_read_existing(root)` → 找 parent started / parent terminal） | 已核：`parent_event_id` 为 M2 新增结构引用集（不可更正），但 parent 的 `invocation_kind`/`instance_id` 等经更正的字段仍须由有效视图一致判定 | 新增（M1） |
| O1n | target 事件自身的出边结构引用字段（M2 缺陷面） | `invocation-terminal.started_event_id`（`EVENT_FIELDS` `model.py:186`；校验 `:488`）、`invocation-started.parent_event_id`（`:182`；校验 `:481-486`）、`design-review-completion.invocation_event_id`（`:202`；校验 `:569`） | 已核：`allowed()`（§3 D1）原仅排除闭合身份字段，会放行这三类出边引用字段；M2 将其列为不可更正结构引用集 | 新增（M2） |
| O1o | 证据/定位载体字段（blind-2 I-2 缺陷面） | `invocation-started.prompt_evidence`（`EVENT_FIELDS` `model.py:183`；校验 `:477`）、`invocation-terminal.output_evidence`（`:189`；校验 `:520`）、`artifact-captured.source_locator`（`:194`；校验 `:537`）、`artifact-captured.snapshot`（`:194`；校验 `:538-547`） | 已核：四者均不在闭合身份字段与 M2 结构引用集内，candidate-4 的 `allowed()` 会放行；`validate_evidence_ref`（`:313-332`）对形状合法 dict 只钉死 path、不拒绝，`validate_locator`/snapshot 同理，故 candidate-4「会被 `validate_event` 拒绝」不成立；blind-2 I-2 改以 `CORRECTION_EVIDENCE_FIELDS` 在 `allowed()` 层整体闭合 | 新增（blind-2 I-2） |

### 2.2 O5 依据（治理信封）

| # | 断言 | 实核位置 | 实核结论 | 修正 |
|---|---|---|---|---|
| O5a | `TASK_TIERS` 四档 + `critical/ultraverge` 别名 | `scripts/budget_gate.py:126-132` | 已核：small 4/8、medium 8/16、feature 16/24、critical 20/30，`critical/ultraverge=critical` | 一致 |
| O5b | opt-in 判定 | `budget_gate.py:692-694` | 已核：`"task_tier" in c or "task_envelope_cap" in c`（**注意：只是“已配置”，不等于“可用”**） | 谓词修正见 O5e |
| O5c | 未配置时 `reserve --role task-envelope` fail-closed | `budget_gate.py:697-706`（`_task_envelope_initial`，`raise FailClosed("task_envelope_not_configured")` 在 **:705**）；触发调用点 `ceiling(state,"task-envelope")` :679-680，reserve 调用 :1137-1139；`companion-reserve` 显式码 :1314；输出格式经 `_run` :2077-2086（`:2082`） | 已核；**抛出点为 :705，非 candidate-1 所称 :1139** | 修正（N3） |
| O5d | 未配置行为向后兼容（A8） | `refs/state-schema.md:454` | 已核 | 一致 |
| O5e | 信封可用判定应取“initial/cap 可解析” | `budget_gate.py:697-706`（`_task_envelope_initial`）、`:709-718`（`_task_envelope_hard_cap`） | 已核：仅配 `task_envelope_cap` 时 `_task_envelope_configured` 为真但 `_task_envelope_initial` 在 :705 抛，故不能直接用 `_task_envelope_configured` 当门禁谓词 | 新增（UV3-15） |
| O5f | preflight 当前不读 gate state | `budget_gate.py:2134-2139`（parser 仅 `--plan`/`--governance`） | 已核。M6 决策：**不新增 `--active-dir`**，门禁改以 `plan.parent` 为对象 active 目录调用 `read_state`；`read_state`（`:247-263`）对缺失 `_budget-state.json` 返回空 config 而不抛，故「未配置」表现为 `_task_envelope_usable` 为假 → fail-closed | 决策（M6；取代 R1-2 的 `--active-dir` 处置） |
| O5n | `_budget-state.json` 可承载持久披露（M6 选定载体） | `read_state` `:247-263`（未知顶层键不校验、不剥离）；`initialize_state` `:324-398`（既有 state 经 json 载入后 `setdefault`，未知顶层键随 `state` 保留并按需写回）；`_validate_state_shape` `:208-244`（只校验 `config`/`extensions`/`fsm`，不拒绝额外顶层键） | 已核：opt-out reason 可持久写入顶层 `envelope_opt_outs` 列表而无需改动既有 config 键校验；**选定 `_budget-state.json`（不选 gate-ledger，避免改 `KNOWN_EVENTS`/`validate_integrity`）** | 新增（M6） |
| O5g | 治理 preflight 结构 | `budget_gate.py:1730-1778`（fence 提取 :1754-1762、gov 块判定 :1762-1777、:1778 → `cmd_preflight_governance` :1718-1727 → `_validate_governance_change` :1540-1652 → `_resolve_and_check_report` :1655-1680 → `_numeric_empirical_conflicts` :1683-1715） | 已核 | 一致 |
| O5h | 最小侵入插入点 | `budget_gate.py:1777` 之后、`:1778` 之前；其前已有 `no_governance_block` :1775、`duplicate_governance_block` 判定 :1776／print :1777 | 已核 | 一致 |
| O5i | 初始化披露三处 | `budget_gate.py:2012-2014`；`scripts/converge_loop.py:1093-1095`；`scripts/ocsr_spawn_adapter.py:400-402` | 已核 | 一致 |
| O5j | adapter CLI 未暴露 `--task-*` | `ocsr_spawn_adapter.py:760-771`（仅 `--converge-active/--mode/--max-outer-loops/--max-blind-rechecks/--ultraverge-min-reviewers/--max-inner-loops/--force`）；`cmd_config_init` 写入点在 :378-386 | 已核 | 一致 |
| O5k | 第三部受保护清单与修改程序 | `CONSTITUTION.md:67-78`（清单）；`:91-96`（第四部程序） | 已核 | 一致 |
| O5l | r2 单对象 gate-ledger 共 23 条 reserved | `.converge/done/20260910-process-controller-consolidation/gate-ledger.jsonl` 实测：executor 5、ultraverge-initial 3、outer-reviewer 6、design-reviewer 5、blind-reviewer 4 | 已核（脚本计数复算） | 一致 |
| O5m | 既有治理 preflight 测试调用面 | `tests/test_budget_gate.py:1448`（`TestGovernancePreflight`），helper `preflight` :1546-1547，`self.preflight` 共 **21** 处；`TestPreflight` :265-279 另有 2 处 legacy 调用 | 已核（逐处列于 §6）。M6 后逐用例重判：`write_plan` 写至 `self.dir`，故新门禁读取的 `plan.parent` 即 `self.dir`；**17 处**（恰好 1 gov 块）到达新门禁，需 `setUp` 在 `self.dir` 配置 state；**4 处**早返回不受影响；helper 无需迁移 | 重判（M6） |

### 2.3 O6a 锚点（供 record-only 记录）

| # | 断言 | 实核位置 | 修正 |
|---|---|---|---|
| O6a | material revision 后两个不同 fresh Spawn 审查相同最终 plan 字节；任何字节变化使两份审查同时失效 | `SKILL.md:462`；`refs/orchestrator-guide.md:17-36`；`refs/state-schema.md:97-100`（失效句在 **:100**，`:95` 为 calibration bootstrap 例外，`:97-99` 为 `converge.review-target/v1` 字段） | 修正为 `:97-100`（UV2 I2-12 / UV3-9） |

### 2.4 既有测试区（实核类/行）

| 文件 | 实核锚点 |
|---|---|
| `tests/test_archive_convergence.py` | `test_b4_unknown_event_field_is_rejected` :680、`test_strict_ledger_bidirectional_binding` :306、`test_terminal_decision_union_rejects_design_review` :408 等；全文件 `def test_*` 实核 **103** 处（修正 candidate-1“44+”的低估表述，UV2 事实核验） |
| `tests/test_budget_gate.py` | `class TestPreflight` :265、`class TestTaskEnvelope` :785、`class TestGovernancePreflight` :1448 |
| `tests/test_converge_loop.py` | `class TestInitializationDisclosure` :1003 |
| `tests/test_ocsr_spawn_adapter.py` | `class TestConfigInit` :315 |
| `tests/test_process_controller_contract.py` | `test_r2_governance_contracts_present` :130、`test_orchest_exact_write_points_not_hardcoded` :199、`test_no_new_direct_gate_accounting_calls_outside_authorized_files` :268 |
| `scripts/README.md` | `:164` 治理 preflight 模式散文（M6 后需补 `plan.parent` 读 state 与 opt-out 持久披露语义，**不含** `--active-dir`） |

---

## 3. 决策

> 全篇不做「A 或 B」式未选定表达；凡出现分叉，均在本节选定并在 Acceptance 验证。ADR 取舍与被拒备选见 §3.5。

### D1（O1）— 最小 in-band `event-correction` 事件 + 单层有效视图投影

**命名锁定**（UV1 N14）：事件类型固定为 `event-correction`；manifest 与 INDEX 披露键固定为 `corrections`；降级串前缀固定为 `correction:`；新增闭合身份字段常量 `CORRECTION_CLOSED_FIELDS`、结构引用字段常量 `CORRECTION_STRUCTURAL_REF_FIELDS`（M2）与**不可更正证据字段常量 `CORRECTION_EVIDENCE_FIELDS`（blind-2 I-2）**（三者均无别名）。

**Closed 字段集**（加入 `EVENT_FIELDS["event-correction"]`，仍走 `validate_event` 的等集模型 `model.py:456-458`）：

```
COMMON_EVENT_FIELDS | frozenset({
  "corrected_event_id",                  # 被更正事件（必为更低 sequence 的既有事件）
  "field",                               # 被更正字段名（恰好一个）
  "original_value",                      # 必须与被更正事件当前 raw 值逐字相等
  "corrected_value",                     # 更正后的值（恰好一个字段的值）
  "authorized_by_user_message_event_id", # 必须引用更早的 user-message 事件
  "reason",                              # 非空有界字符串
  "corrected_at",                        # 时间戳
})
```

**可更正字段规则（动态正向白名单，单源 = `EVENT_FIELDS`）**：

```
CORRECTION_CLOSED_FIELDS = {"event_id","sequence","event_type","schema_id","schema_version"}
CORRECTION_STRUCTURAL_REF_FIELDS = {                 # M2 出边结构引用 + blind-4 Issue-4/MF-1 身份/拓扑邻接字段，一律不可更正
    ("invocation-terminal", "started_event_id"),
    ("invocation-started", "parent_event_id"),
    ("design-review-completion", "invocation_event_id"),
    ("invocation-started", "invocation_id"),       # blind-4 Issue-4：实例身份锚点
    ("invocation-terminal", "invocation_id"),      # blind-4 Issue-4：实例身份锚点
    ("invocation-started", "invocation_kind"),     # blind-4 Issue-4：spawn/continue 拓扑邻接
    ("invocation-started", "parent_instance_id"),  # blind-4 Issue-4：continue 实例邻接
    ("invocation-terminal", "instance_id"),        # MF-1：terminal 实例身份锚点（validate_event_graph:1002 / validate_ledger:689-693 交叉校验）
}
CORRECTION_EVIDENCE_FIELDS = frozenset({             # blind-2 I-2 + blind-3 Issue-1：证据身份/定位载体，一律不可更正
    "prompt_evidence",   # invocation-started
    "output_evidence",   # invocation-terminal
    "source_locator",    # artifact-captured
    "snapshot",          # artifact-captured
    "sha256",            # artifact-captured（blind-3 Issue-1）
    "size",              # artifact-captured（blind-3 Issue-1）
})
allowed(target, f) := target.event_type not in {"terminal-decision","event-correction"}
                   and f in EVENT_FIELDS[target.event_type]
                   and f not in CORRECTION_CLOSED_FIELDS
                   and f not in CORRECTION_EVIDENCE_FIELDS
                   and (target.event_type, f) not in CORRECTION_STRUCTURAL_REF_FIELDS
```

即：可更正字段 = **被更正事件自身 `EVENT_FIELDS` 中实际存在的字段**，排除闭合身份/顺序字段（`CORRECTION_CLOSED_FIELDS`）、**事件自身的出边结构引用与身份/拓扑邻接字段**（`CORRECTION_STRUCTURAL_REF_FIELDS`，M2 + blind-4 Issue-4 + MF-1）与**证据/定位载体字段**（`CORRECTION_EVIDENCE_FIELDS`，blind-2 I-2 + blind-3 Issue-1：`prompt_evidence`/`output_evidence`/`source_locator`/`snapshot`/`sha256`/`size`）；`terminal-decision` 与 `event-correction` 类型事件整体不可更正（判定闭合）。该规则直接解决了 UV2 I2-1 指出的「白名单与闭包互斥」：不再硬编码 5 个字段，不再把 `started_event_id` 混入 decision 引用集。

**`CORRECTION_EVIDENCE_FIELDS` 的理由（blind-2 I-2 + blind-3 Issue-1）**：`prompt_evidence`/`output_evidence`/`source_locator`/`snapshot` 与 `artifact-captured.sha256`/`size` 是**已冻结证据字节的身份/定位载体**——`validate_evidence_ref`（`model.py:313-332`）把 path 钉死为 `evidence/invocations/{owner_id}/{owner_kind}.bin`，`validate_locator`（`:578-591`）与 snapshot 校验（`:538-547`）把定位锚定到 owner；它们虽在 `allowed()` 下原本被放行（不在闭合身份字段与结构引用集内），但允许更正等于让「落盘证据引用」的 sha/size/mode/定位在有效视图里改变，违反 append-only 证据身份不变量。故新增显式常量整体闭合（→ `correction-field-not-allowed`）。这取代 candidate-4 中「写入 `corrected_value` 会被 `validate_event` 在 `validate_evidence_ref`/`validate_locator`/snapshot 处拒绝」的失真表述——`validate_event` 对形状合法的证据 dict **不会**拒绝（仅 path 被钉死），故必须在白名单层显式排除。`original_value` 逐字比对（规则 6）不受影响。补盲（blind-3 Issue-1）：`sha256`/`size` 不被 `validate_event`（`model.py:530-533` 仅格式）或 `_verify_evidence_bytes`（`:1040-1054`）与盘上 blob 绑定，`project_manifest` 的 `artifacts`/`blobs` 亦互不比对，故须在此闭合，否则 artifact 身份可与实际字节脱钩。

**M2 出边结构引用集的理由与边界**：`DECISION_REFERENCED`（规则 5）只保护「**入边**」——被 decision 引用的事件；但 target 事件自身的**出边**引用字段同样决定图结构（`invocation-terminal.started_event_id` 绑定 started、`invocation-started.parent_event_id` 绑定 continue parent、`design-review-completion.invocation_event_id` 绑定被审查 invocation）。若允许更正这些字段，等于在有效视图里改写图拓扑，而 `DECISION_REFERENCED` 的闭包论证（用一半闭包）并不覆盖它。故 M2 以显式最小集合整体闭合这三者（`correction-field-not-allowed`），只保留值/载荷字段可更正。**blind-4 Issue-4 进一步把身份/拓扑邻接字段 `invocation_id`（`invocation-started`/`invocation-terminal` 均有）、`invocation_kind`、`parent_instance_id`（均属 `invocation-started`）并入同一 `CORRECTION_STRUCTURAL_REF_FIELDS`**：它们虽非出边引用，但同为实例身份与 continue 拓扑的锚点，允许更正会使「实例身份」在有效视图里漂移（与 M2「只保留值/载荷字段可更正」的叙述不一致），故一并 `correction-field-not-allowed`。**立身用例所需的 `reservation_id` 是值字段，不在结构引用集内，仍可更正**——这正是「切得更窄反而更安全且不伤立身用例」的落点。三个出边引用各有一条对抗用例：A1-12/A1-13/A1-14。**MF-1 再补 `("invocation-terminal","instance_id")`**：它是 `validate_event_graph` 的 `continue-instance-conflict`（`model.py:1002`）与 `validate_ledger` 的 `ledger-instance-conflict`（`model.py:689-693`）的**实例身份锚点**，而 `validate_event` 对它只做可选文本校验（`model.py:490-493`），故规则 10 的完整 `validate_event` 拦不住它，必须并入本集（对抗用例 A1-22）。类别完备性扫描（以「图/账本用作实例身份锚点的 `*_id`/identity 字段」为类）确认除它外无其他同类遗漏，结论见 `attempts.md` §十五。

**闭包规则 `validate_corrections(events)`（由 `resolve_events` 在应用前调用，任一违反 fail-closed）**：

1. `correction-target-missing`：`corrected_event_id` 不在事件图中；
2. `correction-sequence`：`sequence(target) < sequence(correction)`（严格小于；自我更正因此不可表达）；
3. `correction-closure-violation`（判定闭合）：`target.event_type ∈ {"terminal-decision","event-correction"}`；
4. `correction-field-not-allowed`：`allowed(target, field)` 为假（含未知字段、闭合身份字段、M2 出边结构引用字段、MF-1 实例身份锚点字段、I-2 证据/定位载体字段）；
5. `correction-closure-violation`（判定被引用闭合）：`target.event_id` ∈ `DECISION_REFERENCED`；
6. `correction-original-mismatch`（M3 改写）：`original_value` 必须与 target 字段的**当前 effective 值**逐字相等——无前序更正时即 raw 值（`model.py:409-414` 载入的字节解码值），已有前序更正时即该链最新的 `corrected_value`。这样第一条更正仍须逐字引用 raw，后续更正必须逐字引用当前有效值，杜绝「用旧 raw 值覆盖已更正的 effective 值」；
7. **取代语义（M3，取代原 `correction-chained` 拒绝规则）**：**允许**对同一 `(corrected_event_id, field)` 追加第二条及以后更正；每条更正独立授权（规则 8/9 对每条分别适用），后更正取代先更正的 effective 值。raw 事件日志保持 append-only，`resolve_events` 按 `sequence` 升序逐条应用；manifest/INDEX 披露**全部**更正及其取代关系（见「manifest 投影」）。**不再有 `correction-chained` 码**；
8. `correction-unauthorized`：`authorized_by_user_message_event_id` 必须解析到 `event_type == "user-message"` 的事件，**且**该 `user-message` 的 `user_quote` 必须**同时**包含（a）`corrected_event_id` 的逐字子串、与（b）被更正 `field` 名或逐字 `corrected_value`（M5 内容绑定，blind-4 Issue-1：**删除原 `reason` 子串分支**——`reason` 是更正作者可自由填写的文本，取任意一条较早 `user-message` 曾出现的字符串即可伪造授权）；任一不满足 → 本码；
9. `correction-authorization-order`：`sequence(correction) > sequence(user-message) > sequence(corrected event)`（先有错误、后有授权、最后更正）；
10. `correction-value-type`（M4）：对每个存在更正的 target，应用其**全部**更正生成候选有效事件后运行**完整 `validate_event`**（含 `model.py:445-455` 的二次特化与全部类型谓词/跨字段一致性）；任一失败 → 本码。**这是值谓词与跨字段约束的唯一来源**；不设字段映射表、不抽取 `_validate_field_value`。

**`DECISION_REFERENCED` 的机械定义（UV1 N5 / UV3-7；边界写死 R2-8）**：只取 `validate_event_graph`/`validate_reviewer_verdict_authority` 中**被 4 个 decision 字段直接引用**的事件——即其**入边**为下列四条之一的事件；**不含**经 `invocation-terminal.started_event_id` 间接关联的 `invocation-started`（后者属可更正载荷面，见 M2 对「出边结构引用」的独立闭合）。这四条边为：

| decision 字段 | 指向 | 实核行 |
|---|---|---|
| `reviewer_event_id` | `invocation-terminal`（reviewer 的成功终态） | `model.py:137`（`by_id.get(decision.get("reviewer_event_id"))`） |
| `verdict_output_ref` | 同一 `invocation-terminal` 的 `event_id` | `model.py:144`（`decision.get("verdict_output_ref") != terminal.get("event_id")`） |
| `supersedes_decision_event_id` | 前一条 `terminal-decision` | `model.py:1008` |
| `source_ref` | `user-message`（user-decision） | `model.py:1032` |

**明确排除** `invocation-terminal.started_event_id`（字段属 `invocation-terminal`，`model.py:186`；解析边在 `model.py:978` 与 `:140`，但**不是** decision 引用字段）。这是立身用例可更正的关键：r2 事件 57 以 `started_event_id` 引用事件 55，但事件 57 是 `invocation-terminal`，不是 `terminal-decision`，故事件 55 不被 `DECISION_REFERENCED` 命中。

**立身用例推导链（r2 事件 55 `reservation_id` 更正重放）**：

1. target = 事件 55（`invocation-started`，role=design-reviewer，`sequence=55`）；`event_type ∉ {terminal-decision,event-correction}`；
2. `EVENT_FIELDS["invocation-started"]`（`model.py:180-184`）含 `reservation_id`，且 `reservation_id ∉ CLOSED` → `allowed(target,"reservation_id")=true`；
3. `DECISION_REFERENCED` 在 r2 全事件流上机械求值（**修正 candidate-2「唯一 terminal-decision 事件 54」的事实失真，R1-1**）：r2 实含 **3 条** `terminal-decision`（实开 `.converge/done/20260910-process-controller-consolidation/evidence/events/`）：
   - seq 17 `e4182ce3-fe3e-4683-9533-f36ecab465fd`：`reviewer_event_id`=`verdict_output_ref`=事件 14（`4952d7de-...`），`supersedes_decision_event_id`=null，**无 `source_ref` 键**；
   - seq 45 `ea64c374-d650-43ae-a81a-1935aa06dfb9`：`reviewer_event_id`=`verdict_output_ref`=事件 42（`ef98b9ea-...`），`supersedes`=事件 17（`e4182ce3-...`），**无 `source_ref` 键**；
   - seq 54 `777a0e2d-859f-462d-80a5-7d135d5f04b5`：`reviewer_event_id`=`verdict_output_ref`=事件 53（`0aa365ab-...`），`supersedes`=事件 45（`ea64c374-...`），**无 `source_ref` 键**。
   逐条代入 `DECISION_REFERENCED` = {`supersedes`} ∪ {`reviewer_event_id`} ∪ {`verdict_output_ref`} ∪ {`source_ref`(user-decision)} = {14,42,53,17,45}；**事件 55（`cabcac00-bd16-4161-b857-c45733630580`）不在集合内** → 事件 55 ∉ `DECISION_REFERENCED`（r2 无 user-decision，三条均无 `source_ref` 键，R2-5）；
4. 事件 55 的 `invocation-terminal` 事件 57（`9254cf87-...`）用 `started_event_id` 引用它；该边不是 decision 引用边（`started_event_id` 属 `invocation-terminal`，`model.py:186/:978`），按第 3 步的全量求值不构成闭包；
5. 原值：`original_value="PENDING"`（依事件 56 `user_quote` 记录的更正前值；当前树事件 55 已为更正后字节，故测试以重建的前更正 fixture 复现）；
6. 授权时序：事件 56（`user-message`，`sequence=56`）满足 `sequence(correction) > 56 > 55`（更正事件落于 56 之后）；**但事件 56 的 `user_quote` 只写「事件 55 / `PENDING` / `81a2537ea9eb`，不含 target UUID `cabcac00-…`」，故在新 M5 下 (a) 不满足，该历史操作不再可机械重放**。此处**不放松规则**：r2 的历史更正是在更宽松的手工披露下完成的；本规则比 r2 实践更严格，是**刻意收紧**——历史个案不可重放恰说明规则收紧的必要性（防伪自由文本授权凭据）。立身用例的「字段可更正性」结论（步骤 1–5、7–8 与 `allowed()`/闭包/值谓词）不受影响；机械重放时须按新 M5 构造一条**同时**含 target UUID 与 `reservation_id`（或 `81a2537ea9eb`）的 `user-message` 授权事件；
7. 无同 `(55,"reservation_id")` 既有更正 → 本条为首条更正，`original_value` 即 raw 值（M3：首条比 raw、后续比当前 effective 值）；
8. `corrected_value="81a2537ea9eb"` 为有界非空字符串；应用该更正后的候选事件（`reservation_id="81a2537ea9eb"`）通过完整 `validate_event`（M4：唯一值谓词来源）。
   → 结论：在该规则下事件 55 的 `reservation_id` **在字段可更正性上合法**（`allowed()` 放行、闭包不命中、值谓词通过）；配合一条满足新 M5 的授权 `user-message`（同时含 target UUID 与 `reservation_id`/`81a2537ea9eb`）即可重放，有效视图中事件 55 之 `reservation_id` 显示 `81a2537ea9eb`，使 `validate_ledger` 的 reservation 绑定（`model.py:642-644`）通过。**注（blind-4 Issue-1）**：r2 现存事件 56 的 quote 文本不足以满足新 M5，故历史字节不可原样重放，属刻意收紧（见步骤 6）。

**值 / 跨字段谓词的唯一来源（规则 10，M4 取代 R1-5）**：`validate_corrections` 对每个存在更正的 target，先应用其**全部**更正（按 `sequence` 升序）生成候选有效事件，再对该候选运行**完整 `validate_event`**（含 `model.py:445-455` 的二次特化与全部类型谓词、跨字段一致性、闭集校验）；任一失败 → `correction-value-type`（detail 携带底层 `validate_event` 码）。**不再维护字段→值谓词映射表，不再抽取 `_validate_field_value`**：`validate_event` 在构造上即单源，覆盖类型 + 跨字段 + 闭集，未来任何字段新增都自动反映，不存在「未列出即静默不可更正」的漂移（M4 / DR3 / DR5）。`original_value` 与 raw/effective 的逐字相等校验（规则 6）独立保留。

> 说明（M4 删除面）：原 candidate-3 规则 10 的显式字段映射表与 `_validate_field_value(kind, field, value)` 抽取、以及原规则 10b 的独立段落，统一删除并折叠为本条。证据/定位载体字段（`prompt_evidence`/`output_evidence`/`source_locator`/`snapshot`）已由 `CORRECTION_EVIDENCE_FIELDS`（blind-2 I-2）在 `allowed()` 层整体排除，命中即 `correction-field-not-allowed`，**不经** `validate_event` 判定；**删除** candidate-4「会被 `validate_event` 拒绝」的失真表述。其余字段值域中的 dict/list 由该完整 `validate_event` 自然拒绝（不作独立预筛）。

**禁止批量重写（机械化，UV3-6；R2-6 补值谓词归因）**：`event-correction` 的字段集为**单字段闭集**——只有单个 `corrected_event_id` 与单个 `field`。`validate_event` 的**等集判定**（`model.py:456-458`）只约束 key 集合（extra/missing），拒绝任何多字段/多目标 key 形态；对**值形态**（`corrected_event_id` 为数组、`field` 为数组等），由 `event-correction` 分支的值谓词拒绝——`corrected_event_id` 必须是单个 UUID（`_uuid`）、`field` 必须是单个字符串且 ∈ `allowed(target, field)`。两者合起来使“一次更正多个事件或多个字段”在结构上不可表达。M3 后规则 7 允许同一 `(target, field)` 的**取代链**（不是「二次更正被拒」），但每次仍只能是单事件单字段；多次独立更正不同字段、以及同字段取代链，每次都有独立授权与披露。

**授权绑定加固（UV1 N11；M5 内容绑定）**：`authorized_by_user_message_event_id` 必须满足：
- **存在与类型**：解析到 `event_type == "user-message"` 的既有事件，否则 `correction-unauthorized`；
- **内容绑定（M5；blind-4 Issue-1 收紧）**：该 `user-message` 的 `user_quote` 必须**同时**包含（a）`corrected_event_id` 的逐字子串、与（b）被更正 `field` 名（如 `reservation_id`）或逐字 `corrected_value`（如 `81a2537ea9eb`），否则 `correction-unauthorized`。复用 `capture._prepare_terminal_decision` 对 `user-decision-source` 的逐字匹配哲学（`capture.py:571-574`）。这防止任意一条较早、语义无关的 `user-message`（如「继续」「可以」）被引作授权凭据；**删除原「或含本次更正 `reason` 逐字子串」分支**——`reason` 是更正事件作者可自由填写的非空文本，只要取一条较早 `user-message` 中出现过的字符串即可凑合内容绑定，恰是 M5 声称挡住的场景（blind-4 Issue-1）。收紧后内容绑定锚定到**被更正事件身份 + 被更正字段/值**，与更正目标一一对应，更正作者无法用自由文本伪造；
- **时序**：`sequence(correction) > sequence(user-message) > sequence(corrected event)`，否则 `correction-authorization-order`。

越权用例：① 指向不存在的事件 → `correction-unauthorized`；② 指向非 `user-message` → `correction-unauthorized`；③ `user_quote` 未**同时**含 `corrected_event_id` 逐字子串与（`field` 名或逐字 `corrected_value`）（含「仅含 id 缺 field/value」「仅含 field/value 缺 id」与「语义无关 quote」三例）→ `correction-unauthorized`（A1-17，blind-4 Issue-1）；④ user-message 的 sequence 不小于 target（授权早于错误）或 correction 的 sequence 不大于 user-message（授权晚于更正）→ `correction-authorization-order`。

**有效视图（单层施加点，UV1 B3 / UV2 I2-7）**：

- `resolve_events(events) -> list[dict]`：先 `validate_corrections(events)`，再逐条按 correction 的 `sequence` 升序把 `corrected_value` 写入被更正事件的浅拷贝对应字段；返回有效视图（被更正字段显示 `corrected_value`）。**输入前置条件是 raw 事件列表**；其结果不再被任何校验器二次 resolve（避免双施加）。
- 唯一语义读取点：`validate_event_graph` 与 `validate_ledger` 各自在函数入口调用 `resolve_events(输入)`；`project_manifest` 在 `load_events` 之后调用一次 `resolve_events` 供投影使用，同时把 **raw** 列表传给 `validate_event_graph`/`validate_ledger`（二者各自 resolve）。`validate_archive` 自身不直接读事件字段，其语义完全经由上述三者（故 `:1178-1181` 无需改动即走有效视图）。
- **写入期与归档期共用同一 `resolve_events`（M1）**：`capture.py` 的写入前判定链必须与归档期同源，消除「写入期读 raw、归档期读 effective」的两个真相：
  - `_prepare_terminal_decision(fields, existing)`（`capture.py:523-575`）在入口先 `existing = resolve_events(existing)`，再 `derive_decision_fields`（:543）、`validate_reviewer_verdict_authority`（:560）、`user-decision-source` 逐字匹配（:566-574）；raw 仅在 `_read_existing` 的字节读取层使用。
  - continue-parent 查找（`begin_invocation` 的 `invocation_kind == "continue"` 分支，`capture.py:332-340`）在入口先 resolve 再定位 `parent_event_id` 对应的 `invocation-started` 与其 `invocation-terminal`，使「父实例身份」在写入期即按有效值判定。
  - `raw` 仅用于：`strict_json_bytes` 身份/字节读取、`_exclusive_write`、`model.load_events` 的逐事件闭合校验与序列/ID 唯一性、`events[].sha256/size/path`。这样一条在 target 之后、decision 之前更正了 `invocation-started.role` 或 `invocation-terminal.evidence_level`（二者仍可更正，见 M2 结构引用集边界）的事件，不会在写入期与归档期得出两个结论（消除 `decision-derived-field-conflict`/`user-decision-degradations` 这类由 raw/effective 分叉触发的永久 fail-closed）。
  - 结构引用字段（M2）不可更正，保证 `started_event_id`/`parent_event_id`/`invocation_event_id` 的图拓扑在 raw 与 effective 下完全一致；M1 的 resolve 不改变这些边。
- **`project_manifest` 双列表与派生面显式声明（R1-6）**：在 `project_manifest`（`model.py:740`）内保留两份列表——`raw_events = load_events(root)`（:745）与 `effective_events = resolve_events(raw_events)`（一次计算）。划分固定为「**除字节哈希/路径/身份外一律读有效视图**」：
  - `raw_events`：传给 `validate_event_graph(raw_events)`（:746，内部自 resolve）与 `validate_ledger(root, raw_events, …)`（:747，内部自 resolve）；`event_refs` 的 `path/sha256/size`（:759-762）取 raw 磁盘字节。
  - `effective_events`：`invocations`/`artifacts`/`decisions`/`advisories` 投影循环（**:758-781** 的 `for event in events`）、`final_ref`/`final_event`/`final_decision`（**:782-790**）、`allowed_blobs`（**:792-796**）、`degradations` 的 `model-provenance:` 与 `artifact:` 两项（**:856-862**）。这四处全部改读有效视图，`degradations` 不再直接读 raw `evidence_level`/`reproduction_capability`，消除「invocations 显示更正值、degradations 仍按旧值」的两个真相。
  - 不变量：`resolve_events` 对同一 raw 输入的返回值是纯函数；`project_manifest` 内只 resolve 一次（拒绝二次 apply）。`validate_archive` 重投影比较（:1185-1188）因此在有效视图上自洽。
- `load_events` 仍只做 raw 逐事件校验与序列/ID 唯一性（保持 append-only 字节与文件名契约）。
- 原始值只存在于 correction 事件本体的 `original_value`（append-only，不覆盖任何既有事件字节）。

**manifest 投影（披露）**：

- `invocations` 等字段值投影走有效视图（`project_manifest` 的逐事件循环 `model.py:757-781` 改用有效视图）；`events[].path/sha256/size` 一律取 **raw 磁盘字节**（`model.py:759-762` 不变）。
- 新增 `corrections` 键（**omit-when-empty**，沿用 `acknowledged_orphan_reservations` `model.py:884-893` 惯例），内容为按 `(corrected_event_id, field, correction_event_sequence)` 排序的列表，**列出全部更正**（含被后续取代者），每条含 `corrected_event_id/field/original_value/corrected_value/authorized_by_user_message_event_id/correction_event_id`，并含 `supersedes_correction_event_id`（本条取代的前一条同 `(target,field)` 更正的 `correction_event_id`，首条为 null）与 `effective`（本条是否为该字段当前有效更正，`bool`）——披露完整的取代链与最终有效值（M3）。
- `degradations` 增加 `correction:{corrected_event_id}:{field}`（复用 `model.py:856-862` 的集合并集模式）。
- `render_index_bytes`（`model.py:1194-1291`）新增 `## Corrections` 段，但**仅当 `corrections` 非空时插入**——对无更正的既有归档不产生任何字节差异。

**如何同时满足三项硬约束**：
1. `check` 不再因旧值失败：`validate_event_graph`/`validate_ledger` 经 `resolve_events` 读取有效值，`reservation_id` 绑定按更正值通过（`model.py:642-644` / :683-686）。
2. manifest 哈希仍可复算：`corrections` 与 `degradations` 均由 raw `event-correction` 事件确定性派生；`events[].sha256` 取 raw 字节；`validate_archive` 重投影（`model.py:1185-1188`）相等。
3. A15 既有归档回归不破：r2 归档无 `event-correction` 事件 → `corrections` 键与 INDEX 段均 omit-when-empty，`project_manifest` 输出与旧 manifest 逐字节相等（追加新事件类型不影响既有事件与渲染路径）。
4. `original_value` 与磁盘字节留痕：字段的**原始 raw 值**只出现于 raw 事件文件（未改）与**首条** correction 的 `original_value`；取代链中后续更正的 `original_value` 等于其前一条的 `corrected_value`（M3），同样 append-only、可核。

**调用入口**：`capture.py` 新增 `record_correction(root, *, corrected_event_id, field, original_value, corrected_value, authorized_by_user_message_event_id, reason)`，落盘前先 `validate_corrections`（更正闭包，含 `raw + [pending]`），再对 `raw + [pending]` **直接调用** `validate_event_graph`（含 `validate_reviewer_verdict_authority`，`model.py:125-144`）与 `validate_ledger`（`model.py:594`）——**二者各自入口 `resolve_events` 一次；不得先 `resolve_events` 再把结果传入**（对已施加输入二次施加会误报 `correction-original-mismatch`）；这就是归档期 `validate_archive`（`:1178-1181`）同源的完整检查链，**而非仅 `validate_corrections`**（blind-2 I-3；与 `_prepare_terminal_decision` `capture.py:523-575` 同哲学：注定 fail-closed 的更正不落盘；R2-7 修正锚点范围）。这样「decision 之后追加的更正」不会写期接受、归档期永久 fail-closed：更正 reviewer terminal 的 `started_event_id` 所指 started 的 `role`（归档期 `decision-reviewer-authority`）、或更正 user-decision 之前未被直接引用的 `invocation-terminal.evidence_level`（归档期 `user-decision-degradations`）都会在落盘前被拒（A1-19/A1-20）。`record_correction` 的 `original_value` 比较基准取**当前 effective 值**（`resolve_events(raw)` 后该字段值，M3），使取代链在写入期即可判定。`archive_convergence.py` 新增 `record-correction` 子命令（parser 近 `:286-287`，main dispatch 近 `:360-362`）。**前置条件（blind-4 Issue-2）**：`record_correction` **仅可在事件流已闭合（无未闭合 invocation、无未结清 reservation）时调用**——落盘前跑的是与归档期同源的**完整**图/账本校验，而 `validate_event_graph`（`model.py:992-994`）与 `validate_ledger`（`model.py:642-644`/`:653`）无条件要求所有 invocation 闭合、所有 reservation 结清，故未闭合对象上的合法更正会被 `invocation-open`/`ledger-*` 误拒；调用入口显式检查该前置条件，未满足即返回专用码 **`FAIL_CLOSED:correction-precondition-unclosed`（`EXIT_FAIL_CLOSED`，exit 30）** 拒绝调用（而非把「对象尚未闭合」误报为「更正非法」；**MF-4，唯一口径**登记于 §6.1/§11 O1.21，不得退化为 `invocation-open`/`ledger-*` 或任何 `correction-*` 码）。

**更正生命周期定案（MF-3）**：`record_correction(root)` / `record-correction <root>` 的 `root` **必须是 active 对象根**；对已归档（done）对象不得直接追加事件——直接追加会破 `tree-closure`/`manifest-projection-mismatch`（`model.py:1170-1188`）。修复已归档历史对象的合法路径固定为：`reopen`（`archive_convergence.py:299-300` → `transaction.reopen`，`transaction.py:305-327`；旧 manifest 原字节进入 `revisions`、新 manifest `revision_id` 递增，新事件从历史最大 sequence 继续）→ 在 reopen 后的 active 根 `record-correction`（必要时先 `record-user-message` 补一条 M5 合规授权）→ `archive` 重投影 manifest/INDEX（进入 `revision_chain`）。端到端验收见 A1-23；绝不原地改写 done 字节（S-F2）。

**明确边界**：更正只能修复「语法合法但语义/记录写错」的字段值（`validate_event` 先于更正运行，语法非法的事件永不被更正拯救）；不提供删除事件、不提供修改已闭合判定、不提供批量重写。

### D2（O3）— 自指 bootstrap 通道：删除，改处置记录（S1）

依 S1，本对象**不设计、不实现**任何自指 bootstrap 通道；candidate-1 的 D2 整体删除。完整处置记录与依据见 §13。

### D3（O5）— 含治理机器块的计划默认要求配置 task-envelope

**触发谓词（UV3-3 / UV1 N7 / UV2 I2-9）**：机器触发条件 = 计划内含**唯一** `converge.governance-change/v1` 机器块。全篇规范句一律改写为「含治理机器块的治理计划」，**不得**使用模糊的「治理类任务」，**不得**绑定 `review_mode`（`review_mode` 无任何机器解析，`fsm.mode` 才是机器字段，但本决策刻意不以 mode 为触发，以与既有 gov-block 机制一致）。

**门禁行为（M6：取消 `--active-dir`，对象 active 目录 = `plan.parent`）**：在 `cmd_preflight` 的 `:1777` 之后、`:1778` 之前插入治理信封门（位置在 legacy 早返回 `:1763-1769`、CRLF `:1770-1771`、`no_governance_block` `:1775`、`duplicate_governance_block` 判定 `:1776`／print `:1777` 之后）：

1. **对象 active 目录固定 = `plan.parent`（被检 plan 的父目录）**，不新增任何 CLI 参数；门禁读取 `state = read_state(plan.parent)`，并**捕获 `read_state` 的任何异常**（含 `state_corrupt:*`，`budget_gate.py:253-256`）统一映射为 `FAIL_CLOSED:governance_requires_task_envelope`（**blind-2 I-6**；`state_corrupt:*` 仅作内部 detail，不直接作为对外码）。门禁不校验任何「传入目录」，因为除了 `plan.parent` 根本没有可传入的目录——从机制上消除「传任意已配置目录静默通过」的旁路（M6，取代 R1-2 的 `--active-dir` 处置）。
2. 若 `--allow-unconfigured-envelope <reason>` 未被使用：`_task_envelope_usable(state)` 为假（`plan.parent` 下无 `_budget-state.json`，或其 task-envelope initial/cap 不可解析）→ `FAIL_CLOSED:governance_requires_task_envelope`（exit 30）。
3. 若 `--allow-unconfigured-envelope <reason>` 被使用且 reason 非空 → **持久写入**对象 `_budget-state.json` 顶层 `envelope_opt_outs`（`read_state(plan.parent)` → dict 顶层 append 一条 `{reason, plan, recorded_at}` → **写盘前 `state.setdefault("defaults_version", 2)`（MF-2：缺则置 2，与 `initialize_state` 新 state `:406-411` 同形；仅缺时补写，不覆盖既有 legacy v1）** → `write_state(plan.parent, state)`；**直接写盘、绕过 `initialize_state` 的 `needs_write`，blind-2 I-5**），并打印 `WARN:unconfigured-envelope:<reason>` 后继续（exit 0，审计面持久可见，与 `--declare-orphan-reservation` 的持久披露同强度）；reason 缺失或空串 → `FAIL_CLOSED:governance_requires_task_envelope`。
4. 信封可用（initial/cap 均可解析）时正常进入 `cmd_preflight_governance`，不使用 opt-out、不写 opt-out、不打印 WARN。

**opt-out 持久披露载体（M6，选定写死）**：选定 **对象 `_budget-state.json` 顶层 `envelope_opt_outs`**，不选 gate-ledger。**写盘路径写死（blind-2 I-5）**：门禁**直接** `state = read_state(plan.parent)` → 在 dict 顶层 append `envelope_opt_outs`（文件不存在时 `read_state` 返回空 config，补 `fsm/extensions` 默认与 `defaults_version=2`（缺则置 2，MF-2）后写）→ `write_state(plan.parent, state)`，**绕过 `initialize_state`**——因为 `initialize_state` 的 `needs_write`（`:390-395`）只比较 `config`/`fsm`/`extensions`，若经它追加 `envelope_opt_outs` 而其余三者未变会静默不写盘（I-5 陷阱）。理由：`read_state`（`:247-263`）已在该处读取、未知顶层键不校验不剥离；`initialize_state`（`:324-398`）对既有 state 经 json 载入后按需写回，额外顶层键随 `state` 保留（O5n 实核）；而 gate-ledger 路径需扩 `KNOWN_EVENTS`（`:142`）与 `validate_integrity`（`:869-914`）的事件类型集，侵入面更大。`_validate_state_shape`（`:208-244`）新增对 `envelope_opt_outs` 的形状校验（`list[dict{reason,plan,recorded_at}]`）。绝不静默：无 opt-out 时不写、不改既有 state 字节。

**信封可用判定修正（UV3-15）**：谓词为「`_task_envelope_initial(state)` 与 `_task_envelope_hard_cap(state)` 均不抛 `FailClosed`」（`budget_gate.py:697-706`、`:709-718`），新增 `_task_envelope_usable(state)` 近 `:719`。**不得**直接用 `_task_envelope_configured`（`:692-694`）——仅配 `task_envelope_cap` 时它为真但 initial 在 :705 抛。

**plan.parent 生命周期与治理自举交互（UV3-5，M6 口径）**：门禁读取的 active 目录由 `plan.parent` 唯一确定，强制顺序为「对象初始化（在该父目录配置信封）→ 治理 preflight」；不存在生命周期倒置，也不存在「指向别的对象目录」。对既有 calibration bootstrap 例外（`refs/state-schema.md:95`）的交互语义：该例外只豁免“内嵌 calibration-report”的机器输入来源，**不豁免**本门禁；首次治理变更若尚无已配置信封，只能 (a) 先在 plan 所在目录 `budget_gate init --task-tier ...` 配置信封，或 (b) 显式 `--allow-unconfigured-envelope <reason>`（并持久写入 `envelope_opt_outs`）。本对象自身即按 (b) 在实现前自验、按 (a) 在 Phase 0 配置（见 §7；本对象 `plan.parent` 已是对象 active 目录，故 Phase 0 的 `init` 直接满足门禁）。

**初始化披露补全（三处，措辞一致）**：`budget_gate.cmd_init`（`:2012-2014`）、`converge_loop._init_budget_config`（`:1093-1095`）、`ocsr_spawn_adapter.cmd_config_init`（`:400-402`）各在既有 `if _task_envelope_configured(state):` 内追加**恰好一行**确定输出：
`[init] envelope-may-block-before-local-ceiling: true`
（仅已配置时打印；前三行不变。）

**adapter CLI 对齐（UV3-14 前置调研已证实不可达）**：`ocsr_spawn_adapter.py:760-771` 增加 `--task-tier`（choices=`TASK_TIERS`）、`--task-envelope-initial`（int）、`--task-envelope-cap`（int）；并在 `cmd_config_init`（`:378-386`）写入 config dict，使披露分支可达。

**推荐档位（推荐与披露，不新增 hard cap、不改 `TASK_TIERS` 数值；UV1 N10 / UV2 I2-8 / UV3-8）**：
- **真机械下界 = 4**：`ultraverge_min_reviewers(3)` 初审 + 1 设计审查 = 4（一次首轮直接通过的最小派发）。
- **典型路径估计 ≈ 10（标注“估计非下界”）**：假设一轮修复 + 一次 material 双审 + 实施 + 独立审计的典型情形；无修复、无 material 时低于 10。
- **推荐 `critical`（`critical/ultraverge`；initial 20 / cap 30）的依据 = r2 实测**：r2 单对象 reserved = 23（O5l：executor 5、ultraverge-initial 3、outer-reviewer 6、design-reviewer 5、blind-reviewer 4）→ `cap 30` 余量 7，`feature cap 24` 仅余量 1。如实披露：`initial 20 < 23`，按 r2 轨迹推荐档通常需一次 extension 才到 cap；用户亦可用 `task_envelope_initial/cap` 显式取更小值并接受 `quality_path_guaranteed: false`。
- **机制上只要求“已配置且可用”**，不强制具体档位；不引入任何新数值 hard cap，不改 `TASK_TIERS`（`budget_gate.py:126-132` 不变）。

**legacy 兼容**：无 gov 块且无 `--governance` 的路径在 `:1769` 早返回，行为完全不变（现有负例逐一保持，见 §8 A-B4）。

### D4（O6）— material 增量复核：评议已定，不实现（record-only，S2）

依 S2，本决策**不含任何“若裁决为实现则实施”的分支**。O6 处置协议 = **评议已定：不实现**。

**record-only 的理由结构**：
1. **缺真实复现样本**：没有任何已归档对象被定义为「X 类修订」，更无法机械复现「delta 复核结论 == 全量同字节复核结论」（candidate-1 的举证义务 2 无样本可指，三票均指出无法核实）。
2. **首轮双审成本未实证超阈**：动机只有“节省 spawn”（r2 gate-ledger blind-reviewer 4 / outer-reviewer 6），没有任何实测阈值显示全量双审成本超出可接受界；以成本为唯一理由推进违反 Non-Goal「不为未观测故障预设机制」。

**本对象产出**：只把结论与证据写入 `attempts.md` / retrospective；不改 `SKILL.md:462`、`refs/orchestrator-guide.md:17-36`、`refs/state-schema.md:97-100`，不新增代码、不新增 File Matrix 行。重启该议题的判据清单见 §14。

### 3.5 ADR 取舍与被拒备选

| 决策 | 选定 | 被拒备选 | 被拒理由 |
|---|---|---|---|
| D1 可更正字段 | 动态白名单（`EVENT_FIELDS[target_type]` − 闭合身份字段 − 出边结构引用集 `CORRECTION_STRUCTURAL_REF_FIELDS` − 证据字段集 `CORRECTION_EVIDENCE_FIELDS`），decision/correction 事件整体闭合 | ① 硬编码 5 字段白名单；② 字段黑名单；③ 只排除闭合身份字段、放行出边引用/证据字段（candidate-3/candidate-4） | ① 与闭包互斥（UV2 I2-1）；② 黑名单对未来字段 fail-open；③ 用一半闭包证明整体，未声明/未测试出边结构字段（M2）与证据字段（blind-2 I-2）。 |
| D1 闭包引用集 | 仅 `terminal-decision` 的 `{reviewer_event_id, verdict_output_ref, source_ref, supersedes_decision_event_id}` **直接**引用（入边） | 含 `started_event_id`（candidate-1 原案） | `started_event_id` 属 `invocation-terminal`，若纳入则立身用例（事件 55）不可更正；M2 另以出边结构集独立闭合该字段本身（UV1 N5/UV3-7、R2-8）。 |
| D1 有效视图 | 单层 `resolve_events`：校验器入口各自 resolve raw；**写入期（capture）与归档期共用同一 `resolve_events`**（M1），禁止二次施加 | 只覆盖校验器/投影、capture 仍读 raw（candidate-3） | 写入期与归档期两个真相，会制造计划自定为「永久 fail-closed」的失败（M1）。 |
| D1 授权绑定 | exists + user-message + `seq(corr)>seq(umsg)>seq(target)` + **`user_quote` 内容绑定**（M5） | 仅 exists/type/时序（candidate-3） | 任意较早的语义无关 user-message 可当凭据（M5/DR「授权强度不应低于 user-decision」）。 |
| D1 取代语义 | 规则 7 = 取代链：允许同 `(target,field)` 追加，`original_value` 必须等于当前 effective 值，每条独立授权，raw append-only（M3） | 每字段至多一次、二次即 `correction-chained`（candidate-3） | 更正机制自身无修复路径，写错的 `corrected_value` 永久生效（M3/DR2）。 |
| D1 值谓词来源 | 唯一来源 = 应用全部更正后的候选有效事件跑**完整 `validate_event`**（M4） | 显式字段映射表 + `_validate_field_value` 抽取（candidate-3） | 第二份手工枚举会随 `validate_event` 演化静默漂移（M4/DR3/DR5）。 |
| D1 批量语义 | schema 层单字段闭集（key 等集 + 值谓词），批量不可表达 | 附设 `correction-batch` 图级规则 | 单字段闭集已从结构上排除批量，附设规则冗余（UV3-6；R2-6 补值谓词归因）。 |
| D2/O3 | 删除，处置记录 | 新增 `converge.bootstrap-channel/v1` + finish 门 | 不放松任何校验 ⇒ 不改变可执行集；无机械承载；与 r2 既有 ordering 先例重复（UV3-1、UV2 I2-3/I2-4、UV1 B2/N12）。 |
| D3 触发 | 含唯一 gov 机器块 | ① `review_mode: ultraverge`；② 模糊“治理类任务”；③ `fsm.mode` | ①②无机器解析/集合与机制不一（UV3-3/N7/I2-9）；③ 与本对象 S5 自验冲突（本对象 `fsm.mode=ultraverge` 但按 gov 块触发）。 |
| D3 门禁失败语义 | `FAIL_CLOSED:governance_requires_task_envelope` + opt-out 披露 | 仅 WARN 放行 / 静默跳过 | 会让门禁形同虚设，重演 A 对象「未穷举旧路径」教训（B1/I2-5）。 |
| D3 谓词 | initial/cap 可解析 | `_task_envelope_configured` | cap-only 配置过门但运行期仍抛（UV3-15）。 |
| D3 对象 active 目录 | `plan.parent`（无 CLI 参数；M6） | `--active-dir <dir>` 由调用方指定（candidate-3） | 不校验目录与对象归属，可指向任意已配置目录静默通过；且需迁移 21 处 helper 与保留 A2-5 类负例（M6/DR4）。 |
| D3 opt-out 披露 | 持久写入 `_budget-state.json` 顶层 `envelope_opt_outs`（M6 选定） | 仅 stdout `WARN`；或写 gate-ledger | 仅 stdout 是瞬态、无持久审计面；gate-ledger 需扩 `KNOWN_EVENTS`/`validate_integrity`，侵入面更大（M6/DR2）。 |
| D4/O6 | record-only | “满足 1+2+3 则实现” | 无 X 类定义 / 无 File Matrix / 无 Acceptance，实现分支无界（B4/I2-6）。 |

---

## 4. Track 结构与「为何不拆对象」

本对象按两条**独立 Track** 组织，回应用户已裁决的合并（撤销子计划 C、O5 并入 B），同时回应 UV3-16 的拆分建议：

- **Track-1 = O1（归档契约更正语义）**：`model.py` / `capture.py` / `archive_convergence.py` / `state-schema.md`（archive 段）/ `test_archive_convergence.py`。
- **Track-2 = O5（治理信封默认）**：`budget_gate.py` / `converge_loop.py` / `ocsr_spawn_adapter.py` / `state-schema.md`（task-envelope 段）/ `orchestrator-guide.md` / `SKILL.md` / `scripts/README.md` / `test_budget_gate.py` / `test_converge_loop.py` / `test_ocsr_spawn_adapter.py`。
- **共享**：`tests/test_process_controller_contract.py` 的静态断言（:130/:199/:268）、Phase 0（升级闸门）与 Phase 6（集成 + 独立 fresh 审计）、Phase 7（finish/archive）。

两 Track **无共享代码路径**：Track-1 的全部改动在 `scripts/archive_contract/**` 与 `archive_convergence.py`；Track-2 的全部改动在预算/披露链（`budget_gate.py`、两个 init 入口）。唯一交点是 `state-schema.md` 的两个**不相邻**章节（archive 段 vs task-envelope 段）与共享测试文件，互不依赖。可以独立红测、独立转绿、独立验收。

**为何不拆为两个对象**：合并省一次完整 ultraverge 全流程（用户裁决已确认的理由），而两 Track 的审查面并未因此叠加——Track-1 与 Track-2 的 mechanism、失败语义、回滚路径、受影响文件集完全不相交，任一 Track 的阻断不会拖住另一 Track 的实现（测试按 Track 分组，Acceptance 按 Track 分组）。唯一真正的耦合面（第三部文件 `state-schema.md`）已在 §12 逐句对照中显式隔离。故以结构化 Track 回应 U V3-16 的拆分建议，而不拆对象。

---

## 5. Exact File Matrix

> 行号均为 2026-09-12 实核（HEAD `13da605`）。第三部受保护文件显式标出「改哪一句、为什么 ultraverge 允许」（逐字对照见 §12）。
> **本计划未列出的文件一律不改**；Phase 1 扫描发现任何未授权文件即停止（§6）。

### 5.1 Track-1（O1）File Matrix

| # | 文件 | 改动 | 实核锚点（改点落位） | 保护级别 |
|---|---|---|---|---|
| T1-F1 | `scripts/archive_contract/model.py` | `EVENT_TYPES` 加 `event-correction`；`EVENT_FIELDS["event-correction"]`；`CORRECTION_CLOSED_FIELDS` + `CORRECTION_STRUCTURAL_REF_FIELDS`（M2 + MF-1：含 `invocation-terminal.instance_id`）+ `CORRECTION_EVIDENCE_FIELDS`（blind-2 I-2）；`resolve_events`/`validate_corrections`（**无 `_validate_field_value`**，M4）；`validate_event` 加 `event-correction` 分支；`validate_event_graph`/`validate_ledger`/`project_manifest` 接 `resolve_events`；`find_orphan_reservations`（:697-737，现 `load_events` 直读 raw）改走 `resolve_events`，使其孤儿诊断与严格校验同源（blind-4 Issue-3）；`project_manifest` 投影走有效视图 + `corrections` 键（含取代链）+ `correction:` 降级串；`render_index_bytes` 条件插入 `Corrections` 段 | `EVENT_TYPES` :21-24；`EVENT_FIELDS` :179-205；新常量/函数近 :178/:957；`validate_event` 分支近 :573-575；`validate_event_graph` :958；`validate_ledger` :594；`find_orphan_reservations` :697-737；`project_manifest` :745-781/:856-862/:884-898；`render_index_bytes` :1194-1291 | 无（可执行单源） |
| T1-F2 | `scripts/archive_contract/capture.py` | 加 `record_correction(...)`，落盘前跑**完整有效视图校验**（`validate_corrections` + 有效视图 `validate_event_graph`（含 reviewer-verdict authority）/`validate_ledger`，blind-2 I-3；`original_value` 比 effective）；**前置条件（blind-4 Issue-2）**：仅事件流已闭合（无未闭合 invocation / 未结清 reservation）时可调用，未闭合则返回 `FAIL_CLOSED:correction-precondition-unclosed`（`EXIT_FAIL_CLOSED`，MF-4）拒绝调用而非误报更正非法；**M1**：`_prepare_terminal_decision`（:523-575）与 continue-parent 查找（:332-340）入口先 `resolve_events` 再派生/判定；**不引入 `__all__`**（本文件无该结构，实核） | `_prepare_terminal_decision` :523-575（R2-7）/ continue 分支 :332-340 / `record_terminal_decision` :578-581 | 无 |
| T1-F3 | `scripts/archive_convergence.py` | 加 `record-correction` 子命令：parser 近 :286-287；main dispatch 近 :360-362 | `:286-287`、`:360-362` | 无 |
| T1-F4 | `refs/state-schema.md`（archive 段） | ①:40 事件清单补 `event-correction`；②:42 后加更正闭包段；③:60 manifest 闭包补 `corrections` | `:40`、`:42` 后、`:60` | **第三部**（`CONSTITUTION.md:71`） |
| T1-F5 | `tests/test_archive_convergence.py` | 追加 correction 正/负例（含 §11 O1 全部对抗项）、有效视图、披露、立身用例重放；既有用例 `test_b4_unknown_event_field_is_rejected` :680 等不受影响（无 correction 时零行为变化） | 文件末追加 | 无 |

### 5.2 Track-2（O5）File Matrix

| # | 文件 | 改动 | 实核锚点（改点落位） | 保护级别 |
|---|---|---|---|---|
| T2-F1 | `scripts/budget_gate.py` | **不新增 `--active-dir`**（M6）；parser 仅加 `--allow-unconfigured-envelope <REASON>`；`cmd_preflight` 在 :1777→:1778 插入治理信封门（读 `plan.parent` state）；新增 `_task_envelope_usable`；opt-out 持久写入 `envelope_opt_outs`（**直接 `read_state`→改 dict→`write_state`，绕过 `needs_write`，I-5**）；`read_state` 异常（`state_corrupt:*`）统一映射为 `governance_requires_task_envelope`（I-6）；`_validate_state_shape` 加该键形状校验；`cmd_init` 披露加一行 | parser :2134-2139；插入点 :1777→:1778；`_task_envelope_usable` 近 :719；`_validate_state_shape` :208-244；披露 :2012-2014 | 无 |
| T2-F2 | `scripts/converge_loop.py` | 披露加一行 | `:1093-1095` | 无 |
| T2-F3 | `scripts/ocsr_spawn_adapter.py` | CLI 加 `--task-tier/--task-envelope-initial/--task-envelope-cap`；`cmd_config_init` 写入 config；披露加一行 | CLI :760-771；config :378-386；披露 :400-402 | 无 |
| T2-F4 | `refs/state-schema.md`（task-envelope 段） | `:454` 后追加治理计划默认要求 + opt-out + 推荐档位 | `:454` 后 | **第三部**（`CONSTITUTION.md:71`） |
| T2-F5 | `refs/orchestrator-guide.md` | `:44-47` 披露清单补第 4 条 | `:44-47` | **第三部**（`CONSTITUTION.md:72`） |
| T2-F6 | `SKILL.md` | `:453` task_tier 行、`:466` 诚实声明行补治理计划默认要求与推荐档位指针 | `:453`、`:466` | **第三部**（`CONSTITUTION.md:68`） |
| T2-F7 | `scripts/README.md` | `:164` 治理 preflight 模式散文补 `plan.parent` 读 state / opt-out 与门禁行为（**不含** `--active-dir`，M6）；保留 `:174` 既有 `quality_path_guaranteed: false` 句（test_process_controller_contract :161 依赖） | `:164-166`（保留 :174） | 无 |
| T2-F8 | `tests/test_budget_gate.py` | `TestGovernancePreflight`（:1448）**helper :1546-1547 不变**（无 `--active-dir`）；`setUp`（:1449-1451）在 `self.dir` 初始化 `--task-tier critical` state（即 `plan.parent` 的 state）；新增门禁/opt-out 负例（裸 `run`：`plan.parent` 未配置、**损坏 state（I-6）**、opt-out 空 reason、opt-out 持久写入断言）；`TestTaskEnvelope`（:785）加治理默认用例 | `:1448`（helper :1546-1547 / setUp :1449-1451）、`:785` | 无 |
| T2-F9 | `tests/test_converge_loop.py` | `TestInitializationDisclosure`（:1003）加第 4 行断言 | `:1003` | 无 |
| T2-F10 | `tests/test_ocsr_spawn_adapter.py` | `TestConfigInit`（:315）加 `--task-*` passthrough + 第 4 行断言 | `:315` | 无 |

### 5.3 共享 / 只读 / 显式不改

| # | 文件 | 处置 | 实核锚点 | 保护级别 |
|---|---|---|---|---|
| S-F1 | `tests/test_process_controller_contract.py` | 复核并更新跨文件不变量（新写入点、公开 API 面、未授权直调扫描） | `:130`、`:199`、`:268` | 无 |
| S-F2 | `.converge/done/**`（历史归档） | **只读**，不重写、不迁移、不原地升级 | — | Archive Contract 不变量 |
| S-F3 | `refs/reviewer-discipline.md` | **不修改**（显式声明；本计划不触及 reviewer 行为规范） | — | 第三部（`CONSTITUTION.md:77`） |
| S-F4 | `CONSTITUTION.md` | **不修改**（自指保护；任何修改超出本对象范围） | — | 第三部（`CONSTITUTION.md:67`） |
| S-F5 | `refs/orchestrator-guide.md:17-36`（material revision 段） | **不修改**（D4 record-only，永不修改） | — | 第三部（`:72`） |
| S-F6 | `docs/plans/active/`（4 个未跟踪规划文档） | **只读，不删不改**；Phase 0 仅将其明列为预期未跟踪产物 | `git status` 实核 `?? docs/plans/active/` | 无 |
| S-F7 | `.converge/active/20260911-op-envelope-b-contract-correction/evidence/calibration-report.json` | **新建**（candidate-3 落实 R1-3）：由落地生成器 `python scripts/distill_antipatterns.py --calibration --root . --output <此路径> --id calibration-op-b --source-revision r1` 真实产出；`sha256=c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581`，`corpus_digest=ff64a62b27970bb8064c9cbbf11037c0f049383270d167c1090eab64ee5e07eb`，`freshness={13da6055…, r1, 0}` | 新文件（对象 `evidence/` 下，非第三部） | 无（为什么 ultraverge 允许：`refs/state-schema.md:95` 规定 r2 之后的治理变更**必须**由 `--calibration` 生成的报告提供；本文件即该合规输入，是对象本地的非受保护证据产物，不触碰第三部任何规范句。locator 语法 `state-schema.md:72` 的 `root-file` 限 bare allowlist 文件名、不寻址 `evidence/` 路径，故其 canonical 字节另以 allowlisted 根文件 `attempts.md` 的 fenced 块承载并被 §15 `calibration.path` 引用，两处 sha256/digest 一致） |
| S-F8 | 对象 active 目录内 `attempts.md`/`scan-report.md`/`_budget-state.json` | **对象本地过程文件**：仅对象 active 目录内，非源文件、非第三部（`attempts.md` 为 fence 载体/记录，另二者为 Phase 0/§6.3 产物） | 对象 active 目录内 | 无 |

**第三部允许性说明**：本对象 `review_mode: ultraverge`，依 `CONSTITUTION.md:91-96` 第四部程序修改第三部规范句合法；T1-F4 / T2-F4 / T2-F5 / T2-F6 的每一处改动都在 §12 给出逐字「原文 → 新文」对照。

---

## 6. 新增门禁 × 既有调用点穷举（A 对象教训）

### 6.1 本计划新增/变更的判定位点

| 门禁 ID | 位点 | 预期失败码 | 受影响面 |
|---|---|---|---|
| G1 | `resolve_events`→`validate_corrections`（`model.py`）+ `record_correction` 写期完整有效视图门（`capture.py`，I-3） | 8 个 active `correction-*` 码（`correction-target-missing`/`correction-sequence`/`correction-closure-violation`/`correction-field-not-allowed`/`correction-original-mismatch`/`correction-unauthorized`/`correction-authorization-order`/`correction-value-type`；M3 删除 `correction-chained`）+ 归档期派生码（`decision-reviewer-authority`/`user-decision-degradations`，写期同样 fail-closed）+ 前置未闭合专用码 `FAIL_CLOSED:correction-precondition-unclosed`（`EXIT_FAIL_CLOSED`，exit 30；**MF-4 唯一口径**：对象事件流未闭合时 `record-correction` 拒绝调用，不退化为 `invocation-open`/`ledger-*` 或任何 `correction-*` 码） | 所有归档/检查路径 + `record_correction` 落盘前（`validate_corrections` 后对有效视图跑 `validate_event_graph`（含 reviewer-verdict authority）与 `validate_ledger`，与归档期同源）；**无 correction 事件时零行为变化** |
| G2 | `budget_gate.cmd_preflight` 治理信封门（读 `plan.parent` state；M6 无 `--active-dir`） | `governance_requires_task_envelope` | 所有含唯一 gov 块的 `preflight` 调用；其对象 active 目录恒为 `plan.parent` |
| G3 | 三处 init 披露第 4 行 | 无 fail-closed（输出形状变更） | `cmd_init`/`_init_budget_config`/`cmd_config_init` 的调用者与测试 |

### 6.2 `TestGovernancePreflight` 21 处调用逐处分类（M6 重判：**21 处调用；17 处到达新门禁**——其 `plan.parent` 即 `self.dir`，需 `setUp` 在该目录配置 state；**4 处早返回不受影响**；**helper 无需迁移**）

helper `preflight`（`tests/test_budget_gate.py:1546-1547`）：`run("preflight", "--plan", str(plan), *extra)`——**M6 下保持不变**（无 `--active-dir`）。`write_plan` 恒写至 `self.dir`，故新门禁读取的 `plan.parent == self.dir`。插入点 `:1777→:1778` 位于 `duplicate_governance_block`（判定 :1776／print :1777）与 CRLF（:1770-1771）/`no_governance_block`（:1775）/legacy 早返回（:1769）之后，故**只有“恰好一个 gov 块”的调用会到达新门禁**（到达者才读 state）。

> 结论（M6）：**无需迁移 21 处 helper 调用形态**；只需 `setUp` 在临时目录（= `plan.parent`）初始化一次 `--task-tier critical` state。17 处到达门禁者在 state 配置后转绿且断言不变；4 处早返回者测试方法体、断言、调用形态均零改动。下表保留逐处穷举作为影响面证据。

| # | 行 | 用例 | 计划内容 | 是否到达新门禁 | 处理 |
|---|---|---|---|---|---|
| 1 | :1554 | `test_bootstrap_restore_passes` | 1 gov 块 | 是 | 到达门禁；`setUp` 在 `self.dir`（= `plan.parent`）配置 state；用例体/断言不变 |
| 2 | :1566 | `test_eligible_but_not_undercut_passes` | 1 gov 块 | 是 | 同上 |
| 3 | :1575 | `test_empirical_conflict_blocks` | 1 gov 块 | 是 | 同上；原期望 exit 15 不变 |
| 4 | :1584 | `test_counterevidence_discharges_conflict` | 1 gov 块 | 是 | 同上 |
| 5 | :1591 | `test_user_tradeoff_discharges_conflict` | 1 gov 块 | 是 | 同上 |
| 6 | :1602 | `test_inner_comparison_null_not_adjudicated` | 1 gov 块 | 是 | 同上 |
| 7 | :1613 | `test_role_mechanism_change_not_adjudicated` | 1 gov 块 | 是 | 同上 |
| 8 | :1623 | `test_locator_path_not_found_missing_file` | 1 gov 块 | 是 | 到达门禁；state 配置后仍走原 locator 路径，期望 `path-not-found` 不变 |
| 9 | :1633 | `test_locator_path_not_found_absent_id` | 1 gov 块 | 是 | 到达门禁；同上（state 配置后） |
| 10 | :1641 | `test_locator_duplicate_target` | 1 gov 块 | 是 | 到达门禁；state 配置后仍 `duplicate-target` |
| 11 | :1656 | `test_locator_wrong_schema` | 1 gov 块 | 是 | 到达门禁；state 配置后仍 `wrong-schema` |
| 12 | :1666 | `test_unknown_governance_field_fails_closed` | 1 gov 块 | 是 | 到达门禁；state 配置后仍 `FAIL_CLOSED`（gov 字段校验） |
| 13 | :1675 | `test_missing_governance_field_fails_closed` | 1 gov 块 | 是 | 到达门禁；同上 |
| 14 | :1690 | `test_calibration_hash_mismatch_fails_closed` | 1 gov 块 | 是 | 到达门禁；state 配置后仍 `hash` 失败 |
| 15 | :1699 | `test_stale_corpus_digest_fails_closed` | 1 gov 块 | 是 | 到达门禁；state 配置后仍 `stale` |
| 16 | :1708 | `test_stale_high_watermark_fails_closed` | 1 gov 块 | 是 | 到达门禁；state 配置后仍 `stale` |
| 17 | :1717 | `test_report_aggregate_inconsistency_fails_closed` | 1 gov 块 | 是 | 到达门禁；state 配置后仍 exit 30 |
| 18 | :1682 | `test_duplicate_governance_block_fails_closed` | 2 gov 块 | **否**（:1777 先返回） | 测试方法体/断言/调用形态零改动；仅共享 `setUp` 变化（早返回不读 state，故不受门禁影响）；断言仍 exit 30 不变 |
| 19 | :1724 | `test_crlf_payload_fails_closed` | CRLF 污染 | **否**（:1767-1768 legacy 分支 CRLF 检查先返回，R2-3） | 测试方法体/断言/调用形态零改动；仅共享 `setUp` 变化，因早返回不受门禁影响；`crlf` 失败不变 |
| 20 | :1736 | `test_prose_and_table_not_parsed` | 无 gov 块 | **否**（legacy :1769 早返回） | 测试方法体/断言/调用形态零改动；仅共享 `setUp` 变化，因 legacy 早返回不受门禁影响；`CLEAN` 不变 |
| 21 | :1743 | `test_governance_flag_requires_block` | `--governance` 无块 | **否**（:1775 先返回） | 测试方法体/断言/调用形态零改动；仅共享 `setUp` 变化，因早返回不受门禁影响；`FAIL_CLOSED` 不变 |

另：`TestPreflight`（`tests/test_budget_gate.py:265-279`）的 2 处 `run("preflight", "--plan", ...)` 均无 gov 块 → legacy 早返回，**不受影响**。

**更新方式（机械，M6）**：`setUp`（`tests/test_budget_gate.py:1449-1451`）在 `self.dir` 初始化 state（该目录即所有 `write_plan` 的 `plan.parent`）：
```
原文：    def setUp(self):
              self._tmp = tempfile.TemporaryDirectory()
              self.dir = Path(self._tmp.name)
新文：    def setUp(self):
              self._tmp = tempfile.TemporaryDirectory()
              self.dir = Path(self._tmp.name)
              run("init", "--active-dir", str(self.dir), "--task-tier", "critical")
```
helper `preflight` **保持不变**（无 `--active-dir`；M6 已消除该参数）：
```
    def preflight(self, plan, *extra):
        return run("preflight", "--plan", str(plan), *extra)
```
新增门禁负例**必须绕过 helper**（裸 `run`）以覆盖：`plan.parent` 未配置 state（把 plan 写到无 state 的独立目录）、**`plan.parent/_budget-state.json` 存在但损坏（I-6，映射统一失败码）**、opt-out 空 reason、opt-out 有 reason 的 WARN 通过并断言 `_budget-state.json` 顶层 `envelope_opt_outs` **由门禁直接 `read_state`→改 dict→`write_state` 持久写入（绕过 `needs_write`，I-5）**。**删除 A2-5 类「错误 `--active-dir`」负例**（无该参数即无该旁路）。`scripts/README.md:164` 同步补 `plan.parent` 读 state、损坏 state 统一失败码与 opt-out 持久披露语义（T2-F7）。

### 6.3 Phase 1 扫描步骤（产物：`scan-report.md`）

1. `grep -rn` 穷举：`load_events(`、`project_manifest(`、`validate_archive(`、`validate_event_graph(`、`validate_ledger(`、`resolve_events(`、`_prepare_terminal_decision(`、`_read_existing(`、`read_state(`、`cmd_preflight(`、`preflight`、`cmd_init(`、`initialize_state(`、`_task_envelope_configured(`、`_task_envelope_initial(`、`_task_envelope_hard_cap(` 的全部调用点；
2. `grep -rn "record-"` 穷举 `archive_convergence.py` 子命令装配点；
3. 对每个命中判定是否落在 §5 File Matrix 授权文件内；**未授权文件即停止并升级本计划**（不得带内绕过）；
4. 结论写入本对象 `scan-report.md`（在 `.converge/active/...` 内，不污染根目录），作为 Phase 2 红测输入。

---

## 7. Bounded Implementation Sequence

> 每步均有产物与验证；未通过验证不进入下一步。实现轮由便宜模型承担，验收由未参与实现的 fresh 角色承担。

### Phase 0 · 升级闸门（共享，先于任何写操作）
- 动作：确认 `review_mode: ultraverge`；确认本计划将修改第三部文件（T1-F4/T2-F4/T2-F5/T2-F6）故必须 ultraverge；**在本对象 active 目录配置 task-envelope**（`budget_gate init --active-dir .converge/active/20260911-op-envelope-b-contract-correction --task-tier critical`）以消除 D3 对自身对象生效时的不确定状态；生成 HEAD SHA 与工作树证据。
- 产物：`attempts.md` 顶部 Phase 0 记录（HEAD、计划 hash、modest 声明、信封配置命令与输出）。
- 验证：HEAD == 评议基线 SHA；**除已知未跟踪 `docs/plans/active/`（4 个规划文档）外无未提交改动**（`git status --porcelain` 实核为 `?? docs/plans/active/`；`.converge/active/` 被 `.gitignore` 忽略）。

### Track-1（O1）
- **T1-P1 · 穷举扫描 + 红测**：执行 §6.3；对 G1 写失败红测（先证当前代码无 correction 能力）。产物：`scan-report.md` + 红测。验证：`python -m pytest tests/test_archive_convergence.py -q` 红测按预期失败。
- **T1-P2 · 实现契约**：实现 T1-F1/F2/F3；补 T1-F5（正例：重放的 `reservation_id` 更正使 r2 形态对象可归档；负例：§11 O1 全部对抗项，含 I-2 证据字段闭包与 I-3 写期完整有效视图两条）。`record_correction` 落盘前必须对 `raw + [pending]` 跑完整有效视图校验（`validate_event_graph` 含 reviewer-verdict authority + `validate_ledger`）。产物：代码 + 测试 + `record-correction` 可运行。验证：G1 红测转绿；含 correction 的合成归档 `check` 返回 `[]`；未更正错误值仍返回对应 fail diagnosis；I-3 两条注定 fail-closed 的更正不落盘；事件流未闭合时调用返回 `FAIL_CLOSED:correction-precondition-unclosed`（MF-4）。
- **T1-P3 · 有效视图与披露验证**：验证 manifest 投影 = 有效视图 + raw 字节哈希；A15 既有归档回归；验证 M1 写入期/归档期同源、M2 结构引用/身份邻接拒绝、M3 取代链、M5 授权内容绑定、I-2 证据字段拒绝、I-3 写期完整有效视图校验、blind-4 Issue-3 孤儿诊断同源、MF-1 实例身份锚点闭合（A1-22）、MF-3 生命周期（reopen→record→archive 重投影，A1-23）。产物：A1-1..A1-23 证据。验证：见 §8 Track-1 Acceptance。

### Track-2（O5）
- **T2-P1 · 穷举扫描 + 红测**：执行 §6.3；对 G2/G3 写失败红测（含 §6.2 全部 21 处分类确认）。产物：红测。验证：红测按预期失败。
- **T2-P2 · 实现门禁**：实现 T2-F1（`--allow-unconfigured-envelope` parser、`plan.parent` 读 state 的门禁、`_task_envelope_usable`、`envelope_opt_outs` 持久写入与形状校验）与 T2-F8 门禁用例。产物：preflight 信封门。验证：G2 红测转绿；legacy 路径逐字节不变；opt-out reason 落盘可复核。
- **T2-P3 · 披露与 adapter**：实现 T2-F2/F3；补 T2-F9/F10。产物：三处第 4 行 + adapter `--task-*`。验证：G3 红测转绿；adapter `config-init --task-tier critical` 写入 config。
- **T2-P4 · 既有用例适配（M6：无需 helper 迁移）**：按 §6.2 仅在 `setUp` 于 `self.dir`（= `plan.parent`）初始化 state；helper 保持不变。确认 17 处到达门禁者转绿；另 4 处**测试方法体、断言、调用形态零改动**（早返回不读 state，不受门禁影响）。产物：T2-F8 更新。验证：`TestGovernancePreflight` 全绿。

### Phase 6 · 验证（共享，含独立 fresh 审计）
- 动作：对 T1-F4/T2-F4/T2-F5/T2-F6 的规范句改动做逐句对照核验；跑完整测试；由**未参与 Track-1/Track-2 实现**的 fresh 角色做独立审计。
- 产物：测试报告 + 独立审计报告。
- 验证：§8 全绿；独立审计无未关闭阻断。

### Phase 7 · 收尾（共享）
- 动作：`finish` → `archive` → `check`；补 retrospective/round-N 决策 marker（由工具派生）。
- 产物：归档目录 + `check` 返回 `[]`。
- 验证：归档后 `check` valid；契约不变量（append-only、manifest 哈希、reopen/supersede）全部保持。

---

## 8. Acceptance（条条可机械判定）

### 8.1 Track-1（O1）

| # | 命令/操作 | 期望 |
|---|---|---|
| A1-1 | `python -m pytest tests/test_archive_convergence.py -q` | **非新增失败**（**本机单文件基线 `4 failed/97 passed/2 skipped`**，2026-09-12 实测；全量基线 `4 failed/476 passed/5 skipped/11 subtests` 见 A-S2/§8.4/§10 R8；4 fail 为 Windows 8.3 短路径环境差异；R2-1、blind-2 I-1） |
| A1-2 | 合成含 `event-correction`（重放事件 55 形态；**完整事件流**：无未闭合 invocation、无未结清 reservation——blind-4 Issue-2 前置）的归档：`python scripts/archive_convergence.py check <合成根> --format json` | 输出 `[]` |
| A1-3 | 合成「target 为 terminal-decision，或被 terminal-decision 直接引用」：`... check ... --format json` | 含 `code == "correction-closure-violation"` |
| A1-4 | 合成「target 被 `invocation-terminal.started_event_id` 引用（非 decision）」（该引用字段本身不可更正，但 target 的**值字段**如 `reservation_id` 可更正） | `check` 返回 `[]`（证明该边不构成入边闭包，立身用例可更正） |
| A1-5 | 合成「`original_value` 与当前 effective 值不符」 | 含 `code == "correction-original-mismatch"` |
| A1-6 | 合成「同一 `(target,field)` 取代链」：第二条更正 `original_value` = 当前 effective 值 | `check` 返回 `[]`；有效视图显示后者；manifest 披露**两条**更正及 `supersedes_correction_event_id`/`effective`（M3） |
| A1-7 | 合成「`field` 为 `event_id`/`sequence`/`event_type`/`schema_id`/`schema_version` 或不属于 target 的 `EVENT_FIELDS`」 | 含 `code == "correction-field-not-allowed"` |
| A1-8 | 合成「`authorized_by` 不存在/非 user-message/`user_quote` 未**同时**含 `corrected_event_id` 与（`field` 名或逐字 `corrected_value`）/时序不满足」 | `correction-unauthorized`（前三）/ `correction-authorization-order`（后一） |
| A1-9 | manifest 投影：对 A1-2 归档读取 `manifest.json` | 含 `corrections` 段；`degradations` 含 `correction:<event_id>:<field>`；被更正事件 `events[].sha256` 与磁盘原始字节一致；`invocations` 中该 started 的 `reservation_id == corrected_value` |
| A1-10 | `python scripts/archive_convergence.py check .converge/done/20260910-process-controller-consolidation --format json` | `[]`（既有归档不因新增事件类型/渲染段而失效） |
| A1-11 | **M1**：合成「更正 `invocation-started.role`/`invocation-terminal.evidence_level` 先于某 **reviewer-verdict** `terminal-decision`」（**无 user-decision** 时），分别在 **capture 写入期**与 **archive/check 期**求值 | 两期结论一致（capture 不因 raw/effective 分叉抛 `decision-derived-field-conflict`；check 返回 `[]`） |
| A1-12 | **M2**：合成更正 `invocation-terminal.started_event_id` | 含 `code == "correction-field-not-allowed"` |
| A1-13 | **M2**：合成更正 `invocation-started.parent_event_id` | 含 `code == "correction-field-not-allowed"` |
| A1-14 | **M2**：合成更正 `design-review-completion.invocation_event_id` | 含 `code == "correction-field-not-allowed"` |
| A1-15 | **M3**：合成两条同 `(target,field)` 更正且第二条 `original_value` = 当前 effective（= 第一条 `corrected_value`） | `check` 返回 `[]`；manifest `corrections[1].supersedes_correction_event_id == corrections[0].correction_event_id` 且 `corrections[1].effective == true`、`corrections[0].effective == false` |
| A1-16 | **M3**：合成第二条更正但 `original_value` = raw（≠ 当前 effective） | 含 `code == "correction-original-mismatch"` |
| A1-17 | **M5（blind-4 Issue-1）**：合成 `authorized_by` 指向的 `user-message`，其 `user_quote` 未**同时**满足（a）含 `corrected_event_id` 逐字子串、与（b）含 `field` 名或逐字 `corrected_value`（分别构造：仅含 id 缺 field/value；仅含 field/value 缺 id；以及语义无关 quote） | 含 `code == "correction-unauthorized"`（`reason` 不再构成授权依据） |
| A1-18 | **blind-2 I-2 + blind-3 Issue-1**：合成更正 `CORRECTION_EVIDENCE_FIELDS` 全成员（四证据字段 + `artifact-captured.sha256`/`size`） | 含 `code == "correction-field-not-allowed"`（**不**归 `correction-value-type`） |
| A1-19 | **blind-2 I-3**：合成更正某 `invocation-terminal.started_event_id` 所指 `invocation-started.role`（该 started 不被 decision **直接**引用，**完整事件流**——blind-4 Issue-2 前置），经 `record-correction` 落盘 | `record_correction` 在写盘前 fail-closed（对 `raw+[pending]` **直接**调 `validate_event_graph`，各自入口 resolve 一次，reviewer-verdict authority 拒绝）；**落盘目录无新 correction 事件** |
| A1-20 | **blind-2 I-3**：合成更正某 user-decision 之前、未被 decision **直接**引用的 `invocation-terminal.evidence_level`（**完整事件流**——blind-4 Issue-2 前置），经 `record-correction` 落盘 | `record_correction` 在写盘前 fail-closed（有效视图 `presented_degradations` 重算失配 → `user-decision-degradations`）；既有 decision 不变砖、**无新 correction 事件落盘** |
| A1-21 | **blind-4 Issue-3**：合成「更正 `invocation-started.reservation_id`（立身用例形态，**完整事件流**）」后分别跑 `python scripts/archive_convergence.py check <合成根> --format json` 与 `python scripts/archive_convergence.py list-orphan-reservations <合成根>` | 二者语义一致：`check` 返回 `[]`，且 `list-orphan-reservations` 经 `resolve_events` 有效视图求值，不再把已被更正绑定的 reservation 报为孤儿（与严格校验同源） |
| A1-22 | **MF-1**：合成更正 `invocation-terminal.instance_id`（实例身份锚点，被 `validate_event_graph`/`validate_ledger` 交叉校验） | 含 `code == "correction-field-not-allowed"` |
| A1-23 | **MF-3 生命周期端到端**：以 r2 的**副本**（复制 `.converge/done/20260910-process-controller-consolidation` 至临时 done_root；原归档只读，S-F2）→ `python scripts/archive_convergence.py reopen <temp_active_root> <temp_done_root> <slug>` → 追加一条 M5 合规授权（`record-user-message`，其 `user_quote` **同时**含 target UUID 与 `field`/`corrected_value`）→ `record-correction`（更正 `reservation_id`）→ `python scripts/archive_convergence.py archive <temp_active_root> <temp_done_root> <slug>` → `python scripts/archive_convergence.py check <temp_done_root>/<slug> --format json` | 归档后 `check` 返回 `[]`；新 manifest `revision_id` 递增且旧 manifest 原字节进入 `revisions`（`revision_chain` 含旧 revision）；证明「已归档对象须 reopen→record→archive 重投影」路径闭合 |

### 8.2 Track-2（O5）

| # | 命令 | 期望 |
|---|---|---|
| A2-1 | gov 块 + `plan.parent` 已配置：`python scripts/budget_gate.py preflight --plan <gov-plan>`（gov-plan 置于已 `init --task-tier critical` 的目录） | exit 0，`PREFLIGHT_OK:governance-change`（或原 BLOCK:empirical_conflict，按用例语义） |
| A2-2 | ~~gov 块 + 缺 `--active-dir`~~（**M6 删除**：无该参数，无该负例） | — |
| A2-3 | gov 块 + `plan.parent` 未配置 state + 无 opt-out（plan 置于无 `_budget-state.json` 的目录） | `FAIL_CLOSED:governance_requires_task_envelope`，exit 30 |
| A2-4 | gov 块 + `plan.parent` 未配置 state + `--allow-unconfigured-envelope <reason>` | `WARN:unconfigured-envelope:<reason>`，exit 0；且 `plan.parent/_budget-state.json` 顶层 `envelope_opt_outs` 新增该 `{reason,plan,recorded_at}`；该文件 `defaults_version == 2` 且核心键（`config`/`extensions`/`fsm`）与 `initialize_state` 新 state 同形（MF-2） |
| A2-5 | ~~错误 `--active-dir`~~（**M6 删除**：旁路被参数取消而消除） | — |
| A2-6 | `--allow-unconfigured-envelope` 空 reason | `FAIL_CLOSED:governance_requires_task_envelope`，exit 30 |
| A2-7 | 纯 legacy（无 gov 块、无 `--governance`） | 输出与改造前逐字节一致（`CLEAN`/`WARN:code_heavy`） |
| A2-8 | 三处 init（已配置信封） | 均含 `[init] envelope-may-block-before-local-ceiling: true` |
| A2-9 | `ocsr_spawn_adapter config-init --task-tier critical ...` | 成功写入 `_budget-state.json` 的 `config.task_tier`；且 `--task-envelope-initial/-cap` 同样可写 |
| A2-10 | `python -m pytest tests/test_budget_gate.py tests/test_converge_loop.py tests/test_ocsr_spawn_adapter.py -q` | 全绿；`TestGovernancePreflight` 21 处调用中 17 处到达门禁者全绿；另 4 处测试方法体/断言/调用形态零改动（仅共享 `setUp` 变化，见 §6.2） |
| A2-11 | **M6 旁路消除证明**：一个 gov plan 位于未配置 state 的目录 A，同时在另一目录 B 存在已配置的 `_budget-state.json`（B≠plan.parent） | `preflight` 无任何参数可指向 B → `FAIL_CLOSED:governance_requires_task_envelope`，exit 30（证明旁路已从 CLI 面消除） |
| A2-12 | **M6 opt-out 审计闭环**：A2-4 后读 `plan.parent/_budget-state.json` | 顶层 `envelope_opt_outs` 含该条 reason（持久披露，非仅 stdout WARN）；`defaults_version == 2` 且键形同 `initialize_state` 新 state（MF-2）；未使用 opt-out 的运行不写该键、不改 state 字节 |
| A2-13 | **blind-2 I-6**：gov 块 + `plan.parent/_budget-state.json` 存在但**损坏**（非法 JSON 或形状非法，`read_state` 抛 `state_corrupt:*`） | `FAIL_CLOSED:governance_requires_task_envelope`，exit 30（门禁捕获 `read_state` 异常后统一映射为治理码；`state_corrupt:*` 仅作内部 detail，不直接作为对外码） |

### 8.3 共享

| # | 命令 | 期望 |
|---|---|---|
| A-S1 | `python -m pytest tests/test_archive_convergence.py tests/test_budget_gate.py tests/test_converge_loop.py tests/test_ocsr_spawn_adapter.py tests/test_process_controller_contract.py -q` | 非新增失败；本环境前置 = 见 §8.4 与 §10 R8 |
| A-S2 | `python -m pytest -q`（全量） | 非新增失败（Windows 短路径 TEMP 环境前置，见 §10 R8）；通过数 ≥ 改造前同环境基线通过数（R2-2：删除「≥480」绝对口径，本环境基线为 476） |
| A-S3 | `git diff` 第三部文件 | 每一处改动都能在 §12 对照表中找到逐字「原文 → 新文」行，无表外改动 |
| A-S4 | 本计划自身（实现后；Phase 0 已按 (a) 在对象 active 目录配置 `critical` 信封，该目录即 `plan.parent`）：`python scripts/budget_gate.py preflight --plan .converge/active/20260911-op-envelope-b-contract-correction/plan.md` | exit 0，`PREFLIGHT_OK:governance-change`（实现前基线自验见 `attempts.md`；M6 无 `--active-dir`，门禁读 `plan.parent`，Phase 0 配置后通过） |

### 8.4 §8 Acceptance × Track-2 新门禁交互复核（M6 口径，取代 R1-2）

M6 后门禁读取 `plan.parent` state（无 `--active-dir`）。逐条重审「命令 + 期望 exit 0」在实现后是否会被 D3 门禁改成 exit 30：

| 条目 | 命令类型 | 是否含 gov 块 / 走 preflight | 实现后风险 | 处置 |
|---|---|---|---|---|
| A1-1..A1-23 | pytest / `archive_convergence.py check` / `list-orphan-reservations` | 否 | 无（archive 路径不触发 preflight 门禁） | 不变 |
| A2-1 | `preflight --plan <gov-plan>`（`plan.parent` 已配置） | 是 | 无 | 不变 |
| A2-4 | `preflight … --allow-unconfigured-envelope <reason>` | 是，显式 opt-out | 无 | 不变（并断言 `envelope_opt_outs` 持久写入） |
| A2-7/A2-8/A2-9/A2-10/A2-11/A2-12 | legacy / init / adapter / pytest / 负例 | 否 / 负例 | 无 | 不变 |
| A-S1/A-S2/A-S3 | pytest / git diff | 否 | 无 | 不变 |
| **A-S4** | `preflight --plan <本计划>` | **是**；`plan.parent` 即对象 active 目录 | 实现前该目录 state `config={}` 尚未配置 → 若 Phase 0 未 `init` 则 exit 30；Phase 0 `init` 后 exit 0 | 命令已按 M6 去掉 `--active-dir`；Phase 0 在 `plan.parent` `init --task-tier critical` |

另（R1-8 / R2-1 环境事实）：本机 `python -m pytest -q` 基线为 `4 failed, 476 passed, 5 skipped, 11 subtests passed`，4 个失败均为 `tests/test_archive_convergence.py` 的 Windows 8.3 短路径差异（`ADMINI~1` vs `Administrator`），与 Track-1/Track-2 改动无关。故 A1-1/A-S1/A-S2 的判据是「**非新增失败**」，而非字面「0 fail / 全绿」（R2-1/R2-2）；A 对象「480 passed」为其环境等价结果。长路径 TEMP 前置下可复现 A 对象的 480/全绿。

### 8.5 A2-3/A2-4 的 `plan.parent` 构造示例（机械可复现）

- **未配置**：把 gov plan 写到 `<temp>/unconfigured/plan.md`（该目录无 `_budget-state.json`）→ A2-3（exit 30）。
- **已配置**：`budget_gate init --active-dir <temp>/configured --task-tier critical` 后把 gov plan 写到 `<temp>/configured/plan.md` → A2-1（exit 0）。
- **opt-out 持久披露**：A2-4 后断言 `<temp>/unconfigured/_budget-state.json` 存在且 `envelope_opt_outs[0].reason == <reason>`（该文件由门禁在 opt-out 时创建，M6）。
- **旁路消除**：A2-11 中目录 B 已配置但 `preflight` 无任何参数可指向 B，故仍 exit 30。

---

## 9. Non-Goals

- 不引入通用事件编辑能力；不提供「重写历史」的批量工具。
- 不放松 fail-closed 默认；correction 为 opt-in 且显式授权（不可更正闭合身份字段、**出边结构引用与身份锚点字段**（M2 + MF-1：`started_event_id`/`parent_event_id`/`invocation_event_id`/`instance_id`）、**证据/定位载体字段**（blind-2 I-2：`prompt_evidence`/`output_evidence`/`source_locator`/`snapshot`）、判定事件、被 decision **直接**引用的事件）。
- 不新增控制器/registry/renderer；不为未观测故障预设机制。
- **O3 不实现**（自指 bootstrap 通道删除，仅处置记录，§13）。
- **O6 不实现**（record-only 是定案；重启须满足 §14 判据并另立对象）。
- 不修改 `CONSTITUTION.md`（含自指保护清单本身）。
- 不修改 `refs/reviewer-discipline.md`；不修改 `refs/orchestrator-guide.md:17-36`。
- 不改判定机制本身（reviewer 拓扑、verdict 语义、预算门裁决）。
- 不迁移/重写任何历史归档（`.converge/done/**` 只读）。
- 不新增数值 hard cap；O5 只推荐既有档位，不改 `TASK_TIERS`。

---

## 10. Risks

| R | 风险 | 触发条件 | 处置 |
|---|---|---|---|
| R1 | correction 被当后门 | 用 correction 改写闭合身份字段/出边结构引用字段/证据载体字段/判定/被 decision 直接引用的事件 | D1 动态白名单（排除闭合身份字段 + M2 结构引用集 + I-2 证据字段集）+ 判定整体闭合 + I-3 写期完整有效视图校验（消除写期—归档期永久 fail-closed 门）+ §11 O1 对抗回归；Phase 6 独立审计 |
| R2 | G1 误杀既有归档 | 新增 correction 校验误判合法旧事件 | `correction-*` 只在存在 `event-correction` 事件时触发；无更正时 `resolve_events` 仅做浅拷贝；A1-10 回归必过 |
| R3 | G2 误杀既有治理 preflight | 新门禁打断 17 处到达门禁的既有用例/手工调用 | §6.2 逐处穷举 + `setUp` 在 `plan.parent` 统一配置 state；§8 A2-10；legacy 路径逐字节不变 |
| R9 | M1 分叉 | 写入期读 raw、归档期读 effective，产生两个真相 | 写入期链路（`_prepare_terminal_decision`/continue-parent）入口先 `resolve_events`；A1-11 双期一致性用例 |
| R10 | M2 出边拓扑/身份邻接改写 | 用 correction 改写 `started_event_id`/`parent_event_id`/`invocation_event_id`，或身份/邻接字段 `invocation_id`/`invocation_kind`/`parent_instance_id`/`instance_id`（blind-4 Issue-4 + MF-1） | `CORRECTION_STRUCTURAL_REF_FIELDS` 整体闭合 + A1-12/13/14/A1-22 |
| R11 | M3 取代链滥用 | 借取代链反复覆盖 effective 值 | 每条独立授权 + `original_value` 必须等于当前 effective + 全链披露；A1-15/16 |
| R12 | M5 授权挂靠 | 引用无关旧 user-message 作凭据（含用自由 `reason` 文本凑合） | `user_quote` 必须**同时**含 `corrected_event_id` 与被更正 `field` 名/逐字 `corrected_value`（**删除 `reason` 分支**，blind-4 Issue-1）；A1-17 |
| R13 | M6 opt-out 持久写入改变 state 字节 | 未使用 opt-out 却写 state；或写入形状非法；或经 `initialize_state` 因 `needs_write` 漏写（blind-2 I-5）；或产出缺 `defaults_version` 的 legacy v1 state（MF-2） | 仅 opt-out 路径写；门禁**直接** `read_state`→改 dict→`write_state`（**绕过 `needs_write`，I-5**）；写盘前 `setdefault("defaults_version", 2)` 使产出与新 state 同形（MF-2）；`_validate_state_shape` 校验 `envelope_opt_outs`；A2-12 断言未使用时字节不变 |
| R14 | 损坏 state 的门禁失败码不统一（blind-2 I-6） | `plan.parent/_budget-state.json` 存在但损坏 → `read_state` 抛 `state_corrupt:*`，经 `_run` 输出非治理码 | 门禁捕获 `read_state` 异常并统一映射为 `FAIL_CLOSED:governance_requires_task_envelope`（exit 30）；`state_corrupt:*` 仅作内部 detail；A2-13 |
| R4 | init 第 4 行破坏既有输出断言 | 测试对三行输出做整段匹配 | 第 4 行只追加不改前三行；T2-F8/F9/F10 同步更新 |
| R5 | 规范句修改无法回滚 | 第三部改动引入语义漂移 | §12 逐字对照 + A-S3 `git diff` 核验；只增不删关键不变量 |
| R6 | opt-out 被滥用 | 无理由/滥用 `--allow-unconfigured-envelope` | reason 必填且空串即 fail；使用后**持久写入** `_budget-state.json` 顶层 `envelope_opt_outs` 并打印 `WARN:unconfigured-envelope:<reason>`，审计面持久可见（M6） |
| R7 | 本计划自身 governance 块被误判 | 自验 preflight 失败 | §15 机器块经 `_validate_governance_change`/`_resolve_and_check_report` 机械校验；A-S4 自验输出留痕 |
| R8 | 全量测试绝对数字与环境绑定（R1-8） | Windows 8.3 短路径 TEMP：既有 4 个 `tests/test_archive_convergence.py` 用例因 `ADMINI~1` vs `Administrator` 路径差异失败 | 本机基线 `4 failed / 476 passed / 5 skipped / 11 subtests`；A1-1/A-S1/A-S2 判据取「非新增失败」（A-S2 按 R2-2 改为「≥改造前同环境基线」），A 对象 480 为长路径 TEMP 下的环境等价结果，见 §8.4 |

---

## 11. 对抗回归要求（必须逐条测试）

### O1（`event-correction`）
1. **越权/闭合身份字段**：`field ∈ {event_id,sequence,event_type,schema_id,schema_version}` → 拒绝（`correction-field-not-allowed`）。
2. **未知字段**：`field` 不在 target 的 `EVENT_FIELDS` → 拒绝（`correction-field-not-allowed`）。
3. **缺授权**：`authorized_by_user_message_event_id` 指向不存在或非 `user-message` → 拒绝（`correction-unauthorized`）。
4. **时序颠倒**：authorization `<` target，或 correction `≤` authorization → 拒绝（`correction-authorization-order`）；correction `≤` target → 拒绝（`correction-sequence`）。
5. **decision 事件**：target 本身是 `terminal-decision`/`event-correction`，或 target 被 terminal-decision 的 `{reviewer_event_id,verdict_output_ref,source_ref,supersedes_decision_event_id}` 引用 → 拒绝（`correction-closure-violation`）。
6. **非 decision 引用不算入边闭包**：target 仅被 `invocation-terminal.started_event_id` 引用 → 其**值字段**（如 `reservation_id`）允许更正（A1-4，立身用例）；但该 `started_event_id` 字段**本身**不可更正（M2，见 12）。
7. **取代链（M3）**：同一 `(target,field)` 追加第二条更正且其 `original_value` = 当前 effective 值 → **允许**（A1-15）；effective 显示后者，manifest 披露全部及取代关系。**不再有 `correction-chained` 拒绝**。
8. **批量不可表达**：一次提交含多个 `corrected_event_id`/`field` 的更正事件 → `validate_event` 等集判定拒绝（`event-fields`）；值形态（数组 id/field）由值谓词拒绝（R2-6）。
9. **原值伪造**：`original_value` 与当前 effective 值不符 → 拒绝（`correction-original-mismatch`）。含 M3 的第二条更正误用 raw（非 effective）值 → 同码（A1-16）。
10. **值 / 关系闭包（M4）**：候选有效事件（应用全部更正后）未通过**完整 `validate_event`** → 拒绝（`correction-value-type`），涵盖值谓词、跨字段一致性（如 `reproduction_capability` 与 `evidence_mode` 冲突、provenance 矩阵）与闭集校验。**无独立字段映射表**（M4 删除）。证据/定位载体字段不经此门（见 17）。
11. **目标缺失**：`corrected_event_id` 不存在 → 拒绝（`correction-target-missing`）。
12. **M2 结构引用闭合（出边）**：`field == started_event_id`（`invocation-terminal`）→ 拒绝（`correction-field-not-allowed`，A1-12）。
13. **M2 结构引用闭合（出边）**：`field == parent_event_id`（`invocation-started`）→ 拒绝（`correction-field-not-allowed`，A1-13）。
14. **M2 结构引用闭合（出边）**：`field == invocation_event_id`（`design-review-completion`）→ 拒绝（`correction-field-not-allowed`，A1-14）。
15. **M5 授权内容未绑定（blind-4 Issue-1）**：`authorized_by` 指向的 `user-message.user_quote` 未**同时**含（a）`corrected_event_id` 逐字子串、与（b）`field` 名或逐字 `corrected_value`（「仅含 id 缺 field/value」与「仅含 field/value 缺 id」各一例）→ 拒绝（`correction-unauthorized`，A1-17）；**`reason` 不再作为授权依据**。
16. **M1 双期一致**：更正先于 **reviewer-verdict** decision（无 user-decision）时，capture 写入期与 archive/check 期对同一事件流得出相同结论（A1-11）；两期均对 `raw + [pending]` 直接调 `validate_event_graph`/`validate_ledger`（各自 resolve 一次，禁二次 resolve）。
17. **证据/定位载体字段闭包（blind-2 I-2 + blind-3 Issue-1）**：`field ∈ {prompt_evidence, output_evidence, source_locator, snapshot, artifact-captured.sha256, artifact-captured.size}`（`CORRECTION_EVIDENCE_FIELDS`）→ 拒绝（`correction-field-not-allowed`，A1-18）；**不**归入 `correction-value-type`（`validate_event` 不会拒绝形状合法的证据 dict，`sha256`/`size` 亦仅过格式校验）。
18. **I-3 写期完整有效视图校验（reviewer started.role 不得落盘）**：更正某 `invocation-terminal` 的 `started_event_id` 所指 `invocation-started` 的 `role`（该 started 不被任何 decision 直接引用，故原 `validate_corrections` 会放行）→ 对 `raw + [pending]` **直接调用** `validate_event_graph`（含 reviewer-verdict authority）与 `validate_ledger`（各自入口 resolve 一次，不得先 resolve 再传入）应在 **`record_correction` 落盘前 fail-closed**，**不得落盘**（A1-19）。
19. **I-3 写期完整有效视图校验（presented_degradations 不得因更正失配）**：更正某 user-decision 之前、且未被 decision **直接**引用的 `invocation-terminal.evidence_level`（值字段）→ 有效视图会改变该 decision 的 `presented_degradations` 重算结果 → 完整有效视图校验应在 `record_correction` 落盘前 fail-closed，**不得使既有 user-decision 变砖**（A1-20）。
20. **MF-1 实例身份锚点闭合**：`field == instance_id`（`invocation-terminal`，被 `validate_event_graph:1002`/`validate_ledger:689-693` 交叉校验的实例身份锚点）→ 拒绝（`correction-field-not-allowed`，A1-22）。类别完备性扫描确认除它外无其他同类 `*_id`/identity 遗漏（结论见 `attempts.md` §十五）。
21. **MF-4 前置未闭合专用码（唯一口径）**：对象事件流未闭合（存在未闭合 invocation 或未结清 reservation）时调用 `record-correction` → `FAIL_CLOSED:correction-precondition-unclosed`（`EXIT_FAIL_CLOSED`，exit 30）；不得退化为 `invocation-open`/`ledger-*` 或任何 `correction-*` 码。
22. **MF-3 生命周期**：更正仅在 **active** 根调用；已归档对象须 `reopen`→`record-correction`→`archive` 重投影（旧 manifest 原字节入 `revisions`/`revision_chain`，新 manifest `revision_id` 递增）→ `check` 返回 `[]`（A1-23）；绝不原地改写 done 字节。

### O5（治理信封）
1. **legacy 放行**：无 gov 块且无 `--governance` → 输出与改造前逐字节一致（不读 state）。
2. **gov 块 + `plan.parent` 未配置 + 无 opt-out → 拒**：`FAIL_CLOSED:governance_requires_task_envelope`。
3. **gov 块 + `plan.parent` 未配置 + opt-out → WARN 通过**：`WARN:unconfigured-envelope:<reason>`，exit 0；并**持久写入** `plan.parent/_budget-state.json` 的 `envelope_opt_outs`（A2-12）。
4. **gov 块 + `plan.parent` 已配置 → 通过**：`PREFLIGHT_OK:governance-change`（或按原 gov 语义）。
5. **不可用 state → 拒**：`plan.parent` 无 `_budget-state.json`、或无 `task_tier`/cap-only 配置（initial 不可解析）→ `FAIL_CLOSED:governance_requires_task_envelope`。
6. **opt-out 无 reason → 拒**：空串/缺值 → `FAIL_CLOSED:governance_requires_task_envelope`。
7. **M6 旁路消除**：无 `--active-dir` 参数；另一目录的已配置 state 无法被引用 → 仍拒（A2-11）。
8. **既有 17 处到达门禁用例**：仅共享 `setUp` 在 `plan.parent` 配置 state，断言不变；另 4 处测试方法体/断言/调用形态零改动（早返回不读 state）。
9. **损坏 state 统一失败码（blind-2 I-6）**：`plan.parent/_budget-state.json` 存在但损坏 → `read_state` 抛 `state_corrupt:*`，门禁统一映射为 `FAIL_CLOSED:governance_requires_task_envelope`（A2-13）。
10. **opt-out 写盘路径（blind-2 I-5）**：opt-out 持久写入必须直接 `read_state`→改 dict→`write_state`，绕过 `needs_write`（否则 `envelope_opt_outs` 可能漏写）；A2-4/A2-12。

---

## 12. 规范句修改：原文 → 新文逐字对照（第三部受保护文件）

> 依 `CONSTITUTION.md:91-96` 第四部程序，本对象 ultraverge 允许修改第三部规范句。以下每处「原文」均为 2026-09-12 实核**逐字定位片段（无省略号）**：**全部为完整逐字原行**（含首尾定位词）；`state-schema.md:60` 亦为完整逐字原行（quote 长度 588 = 实际行长度 588，逐字相等，**非**前缀；R2-4、blind-2 I-4）。`SKILL.md:453` 原行本身是 Markdown 表格行、含 `|`（原样保留以保证逐字可匹配）。

| 文件:行 | 原文（逐字） | 新文 | 理由 |
|---|---|---|---|
| `refs/state-schema.md:40` | 「公共字段：`schema_id/schema_version/event_type/event_id/sequence`。event id 为 UUID；sequence 在所有 event 类型中从 1 连续且无缺口。`invocation-started` 拥有 invocation kind（spawn/continue）、role、phase、round、attempt、parent、reservation、started_at 与 requested provenance；`invocation-terminal` 只引用 started event，拥有 terminal status、completed_at、host receipt、settlement ref 与 resolved provenance。同一 started 恰有一个 terminal。Continue 必须引用同 instance 的 Spawn parent。」（在该段末尾追加） | 追加新段：「`event-correction` 是第 7 种事件类型，携带 `corrected_event_id/field/original_value/corrected_value/authorized_by_user_message_event_id/reason/corrected_at`；它不修改任何既有事件字节，只经有效视图（`model.resolve_events`）生效。」 | D1 需规范层声明事件类型，否则可执行单源与规范单源不一致 |
| `refs/state-schema.md:42` 后 | 「terminal status 为 `succeeded|failed|cancelled|timeout`；仅 succeeded 必须有 output evidence。失败 reason 为 `backend-error|cancelled-by-host|timeout|process-interrupted`。terminal decision 是闭合联合：`reviewer-verdict` 只引用成功 fresh/blank-slate Reviewer terminal；`user-decision` 只用于 terminal-b/c，必须含 `user_quote/source_ref/presented_degradations/accepted_state`。`design-review-completion` 是 advisory，禁止出现在 `final_verdict_ref`。最终 round 与 retrospective 必须反向引用同一 decision event id/value。」（在该段末尾追加） | 加新段：「更正闭包（`event-correction`）：可更正字段 = 被更正事件 `EVENT_FIELDS` 中实际存在、不属于闭合身份字段 `{event_id,sequence,event_type,schema_id,schema_version}`、不属于结构引用字段集 `{invocation-terminal.started_event_id, invocation-started.parent_event_id, design-review-completion.invocation_event_id, invocation-started.invocation_id, invocation-terminal.invocation_id, invocation-started.invocation_kind, invocation-started.parent_instance_id, invocation-terminal.instance_id}`（M2 出边结构引用 + blind-4 Issue-4 + MF-1 身份/拓扑邻接）、且不属于证据/定位载体字段集 `{prompt_evidence, output_evidence, source_locator, snapshot, artifact-captured.sha256, artifact-captured.size}`（blind-2 I-2 + blind-3 Issue-1）的字段；`terminal-decision` 与 `event-correction` 事件整体不可更正；被任何 `terminal-decision` 经 `{reviewer_event_id,verdict_output_ref,source_ref,supersedes_decision_event_id}` 直接引用的事件不可更正；允许对同一 `(corrected_event_id,field)` 追加更正（后更正取代先更正的 effective 值，M3），每条更正的 `original_value` 必须等于其应用时该字段的当前 effective 值（首条即 raw 值）；授权 `user-message` 须满足 `sequence(correction) > sequence(user-message) > sequence(corrected event)`，且其 `user_quote` 必须**同时**含 `corrected_event_id` 的逐字子串与被更正 `field` 名或逐字 `corrected_value`（M5，否则 `correction-unauthorized`；blind-4 Issue-1 删除 `reason` 分支）；更正落盘前须对 `raw + [pending]` 运行完整有效视图校验（`validate_event_graph` 含 reviewer-verdict authority 与 `validate_ledger`，而不止更正闭包），注定 fail-closed 的更正不落盘（blind-2 I-3）；值/跨字段谓词由应用全部更正后的候选有效事件经完整 `validate_event` 判定（M4，无独立字段映射表）；违者对应 `correction-*` fail-closed。一条 `event-correction` 恰好更正一个事件的一个字段（schema 层单字段闭集，批量不可表达）。」 | D1 定义闭包，保证 append-only 与判定不可改写 |
| `refs/state-schema.md:60` | 「manifest 承诺 canonical records、events、invocation/artifact blobs、revision manifests 的相对路径/hash/size，以及 invocation projection、artifact projection、final decision、advisory refs、degradations、parent revision。manifest 不自哈希；检查从 owners 重投影做语义比较，再逐字节重建 INDEX。archive 事务状态为 `preparing -> source-backed-up -> committed`，post-check 失败进入 `rolled-back`；reopen 使用 `reopen-prepared -> reopen-moved` journal。异常 journal 报 `recoverable`。重试从 journal 恢复，且任一时刻只接受 active、backup 或 done 中一个 authoritative 副本。只有 canonical done root 内且 check valid 才是 archived。reopen 将旧 manifest 原字节进入 revisions，新事件从历史最大 sequence 继续。」（R2-4：完整逐字原行） | 在清单中 `degradations` 与 `parent revision` 之间插入「corrections（omit-when-empty，含被更正事件的 original_value/corrected_value/authorized_by，以及取代链关系），」 | D1 披露进入 manifest 冻结投影 |
| `refs/state-schema.md:454` 后 | 「- **未配置行为**：`config` 中既无 `task_tier` 也无 `task_envelope_cap` 时，`reserve --role task-envelope` 直接 `FAIL_CLOSED:task_envelope_not_configured`；**其它任何角色的 reserve/settle 行为与改造前一致**（`counts_before`/`ceilings` 不出现 `task-envelope` 键）——A8 向后兼容。」（在该 bullet 之后追加） | 追加 bullet：「- **治理计划默认**：含唯一 `converge.governance-change/v1` 机器块的治理计划，preflight 以**被检 plan 的父目录**（`plan.parent`）为对象 active 目录读取其 `_budget-state.json`，要求 task-envelope initial/cap 可解析；否则 `FAIL_CLOSED:governance_requires_task_envelope`（**读取异常含 `state_corrupt:*` 亦统一映射为该码**，blind-2 I-6）。显式 `--allow-unconfigured-envelope <reason>` 可绕过，打印 `WARN:unconfigured-envelope:<reason>` 并把 `{reason,plan,recorded_at}` 持久追加到 `plan.parent/_budget-state.json` 顶层 `envelope_opt_outs`（**直接经 `read_state`→`write_state`，绕过 `needs_write`**，blind-2 I-5；审计持久可见）。推荐 `task_tier: critical`（initial 20/cap 30）：机械下界 = `ultraverge_min_reviewers(3) + 设计审查 1 = 4`，r2 实测 23 reserved（cap 30 余量 7；feature cap 24 仅余量 1）；这是推荐与披露，不新增 hard cap、不改 `TASK_TIERS`。非治理计划（无机器块且无 `--governance`）行为与改造前逐字节一致。」 | D3 规范层声明门禁与推荐依据 |
| `refs/orchestrator-guide.md:44-47` | 逐字四行：`task-envelope 初始化时显示：` / `- 本地 ceilings（outer/blind/inner）` / `- 选定 envelope initial/cap` / `- `quality_path_guaranteed: false`（选档是质量-成本权衡，非到达保证）` | 在该列表追加第 4 条：`- 信封可能先于本地 per-scope 上限（8/3/3）阻断 instrumented run（机器输出 `[init] envelope-may-block-before-local-ceiling: true`）` | D3 把既有散文声明（`SKILL.md:466`）落成机器可测输出 |
| `SKILL.md:453` | 「| `task_tier` | 未配置 | 任务级总信封档位：`small`(4/8) / `medium`(8/16) / `feature`(16/24) / `critical`(20/30)（初始额度/一次性授权上限，见下）。未配置时 `task-envelope` scope 不可用（`reserve --role task-envelope` → `FAIL_CLOSED:task_envelope_not_configured`），对其它角色的 reserve/settle 无任何影响（A8 向后兼容）。初始化时显示 `quality_path_guaranteed: false`——选档是质量-成本权衡，非到达保证 |」（在该行句末追加） | 句末补：「**治理计划（含 `converge.governance-change/v1` 机器块）默认要求配置 task-envelope**（preflight 未配置 → `FAIL_CLOSED:governance_requires_task_envelope`）；推荐 `critical`，依据见 `refs/state-schema.md`。非治理计划行为不变。」 | D3 规范层与机制一致 |
| `SKILL.md:466` | 「> **Task-envelope 诚实声明**：task-envelope 是用户选定的更严格质量-成本叠加层，可能在本地 8/3/3 上限到达前阻断 instrumented run；它不保证8/3/3 最坏路径可达；在 auditable-only 宿主上无法证明宿主级全量记账。」 | 句首补：「**治理计划默认必须选定**（不再纯 opt-in）；」 | D3 与门禁语义对齐 |

**显式不修改**：`refs/orchestrator-guide.md:17-36`（material revision 段，D4 record-only）、`refs/reviewer-discipline.md`、`CONSTITUTION.md`。

---

## 13. O3 处置记录（S1，不实现）

- **结论**：自指修复的合法时序是「**最小修复先落地 → fresh 审计验收 → 对象归档**」；r2 已实践且归档成功（`.converge/done/20260910-process-controller-consolidation`，`check` 实测 `valid`），不存在被死锁拒绝的操作。因此**不需要** `converge.bootstrap-channel/v1` 或任何 finish 期 bootstrap 门禁；本对象不设计、不实现该通道。
- **依据**：r2 `attempts.md:210` 逐字记录「本对象的 archive 依赖 D11 代码落地（否则 ledger-status-conflict 永拦），故收敛对象的 finish/archive 推迟到实施与最终审计完成之后执行；期间 active 目录保持冻结证据，retrospective 追加实施结果后再归档」；r2 归档 `check` 返回 `{"valid":true}`（2026-09-12 实核）。全过程未引入任何新机器声明/事件/门禁。
- **原 D2 的各条缺陷处置**：B2/I2-3（宿主/解析/单次无机械承载）→ 随删除消解；I2-4（与 r2 先例重复）→ 本记录确认既有 ordering 已解决；N12/I2-2（Goal 过度声称“消除循环”）→ 本记录改述为“合法时序”而非“消除依赖”；UV3-1（不放松校验故不破环）→ 记录确认不存在需被放行的操作。
- **Non-Goal 呼应**：本处置即「不为未观测故障预设机制」的落实。

---

## 14. O6 处置协议（S2，record-only）与重启判据

- **处置 = record-only（评议已定：不实现）**：`refs/orchestrator-guide.md:17-36`、`SKILL.md:462`、`refs/state-schema.md:97-100` **不改**；不新增代码/File Matrix/Phase/Acceptance。
- **理由结构**：① 缺真实复现样本（无已归档对象被定义为「X 类修订」，无法机械复现「delta 复核结论 == 全量同字节复核结论」）；② 首轮双审成本未实证超阈（仅有“节省 spawn”动机；无实测界）。
- **重启判据清单**（任一议题只有在**新对象**中满足全部下列条件才应重启，本计划不预置实现）：
  1. 至少一个已归档历史对象可作回放样本，且能机械复现「delta 复核结论 == 全量同字节复核结论」；
  2. 定义出既可机械判定又不被滥用的「X 类修订」边界（仅措辞/格式/非语义段落，或含判定语义），并给出明示的 fail-closed 回退条件（何种字节变化必须回退全量双审）；
  3. 给出可复核的成本阈值证据，证明全量同字节双审成本超出可接受界（不得以“节省 spawn”为唯一理由）；
  4. 任何对 `SKILL.md:462` 的修改给出不削弱质量门的新不变量表述，并经新一轮评议。
- **主观项披露（UV3-16）**：「相同判定置信」属评议人主观判定；因默认 record-only、举证责任在提议实现方，该主观性在“不满足即不改”下不产生执行歧义。

---

## 15. 附录 A：本计划的 `converge.governance-change/v1` 机器块（S5）

> 本块是本计划作为治理计划的唯一机器输入。`numeric_changes` 全部 `kind: mechanism`（本计划不改任何数值默认；`critical` 只是推荐档位）。
> `user_message_events.execution_authorization = ab8896b1-68e1-4170-9545-a1ab4e960c4b`（对象事件流 sequence 9，用户 2026-09-12 合并裁决），`quality_goal = 06754e6f-94fc-4a8a-9d80-65f89ae68e3a`（sequence 10）。
> calibration 引用 `distill_antipatterns.py --calibration` **真实生成**的报告（candidate-3 落实 R1-3）：`calibration.path = attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration-op-b]`；该 fenced 块的 canonical 字节与独立生成文件 `.converge/active/20260911-op-envelope-b-contract-correction/evidence/calibration-report.json` 在 **canonical 形式下逐字节一致**（`sha256=c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581`，`corpus_digest=ff64a62b27970bb8064c9cbbf11037c0f049383270d167c1090eab64ee5e07eb`）；该独立文件**不被 preflight 机械校验**，仅作证据留痕（blind-2 I-7）。生成命令与输出、preflight 复跑输出见 `attempts.md`。
> **不使用** `refs/state-schema.md:95` 的一次性 bootstrap 例外（该例外已由 r2 消耗）：本报告是生成器产物，非计划内嵌自举。locator 语法（`refs/state-schema.md:72`）的 `root-file` 限 plan 同目录 allowlist 根文件名、不寻址 `evidence/` 路径，故其 fenced 载体落在 allowlisted 根文件 `attempts.md`（非 plan 自身），机器块经 `budget_gate.py:1655-1680` 机械校验。

```json
{
  "schema": "converge.governance-change/v1",
  "change_id": "op-envelope-b",
  "numeric_changes": [
    {
      "control": "archive-event-correction",
      "kind": "mechanism",
      "released": null,
      "old": null,
      "proposed": null,
      "comparison": null,
      "basis": "add_in_band_append_only_correction_with_effective_view"
    },
    {
      "control": "governance-preflight-envelope-gate",
      "kind": "mechanism",
      "released": null,
      "old": null,
      "proposed": null,
      "comparison": null,
      "basis": "require_configured_task_envelope_for_plans_with_governance_block"
    }
  ],
  "archaeology_refs": [
    "git:13da6055f173ab1459f62cb36de11bb05b2b19cc",
    "git:a49a2a1828f185a3060e0981d8724a7fa6617c0d",
    "git:529e691672a341b9c4cc0fe798eb63c487d25dfc",
    "git:43e76b64b8dc434695acd413b5870e050b95d8dc"
  ],
  "calibration": {
    "path": "attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration-op-b]",
    "sha256": "c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581",
    "corpus_digest": "ff64a62b27970bb8064c9cbbf11037c0f049383270d167c1090eab64ee5e07eb",
    "freshness": {
      "repository_head": "13da6055f173ab1459f62cb36de11bb05b2b19cc",
      "source_archive_revision": "r1",
      "source_event_high_watermark": 0
    }
  },
  "counterevidence_refs": [],
  "user_message_events": {
    "quality_goal": "06754e6f-94fc-4a8a-9d80-65f89ae68e3a",
    "execution_authorization": "ab8896b1-68e1-4170-9545-a1ab4e960c4b"
  }
}
```

## 16. 附录 B：生成报告载体（candidate-3 取代原「内嵌 bootstrap 块」）

> R1-3 处置：**不再使用** `refs/state-schema.md:95` 的一次性 bootstrap 例外。
> - **独立报告文件（File Matrix S-F7）**：`.converge/active/20260911-op-envelope-b-contract-correction/evidence/calibration-report.json`，canonical SHA-256 = `c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581`。
> - **locator 载体**：`attempts.md` 内 `converge.calibration-report/v1`（`id=calibration-op-b`）fenced 块；其 canonical 字节与独立文件在 **canonical 形式下逐字节一致**（`sha256` 均为 `c4755e…`；但 fence 的 **raw body sha256 为 `9a08eb6e…`**，故**仅 canonical 意义一致、非 raw 逐字节**，blind-2 I-7），§15 `calibration.path` 指向它。**独立文件 `evidence/calibration-report.json` 不被 preflight 机械校验**（preflight 只经 locator 读 `attempts.md` fence），仅作证据留痕。
> - **生成命令**：`python scripts/distill_antipatterns.py --calibration --root . --output .converge/active/20260911-op-envelope-b-contract-correction/evidence/calibration-report.json --id calibration-op-b --source-revision r1`（EXIT=0）。
> - **报告形状（实核）**：`scope=done-corpus`；corpus 为 19 条按 `ref` 排序的 `done:<slug>` 条目（均 `quantitative_status=unavailable`、`reason=no_sample`）；`eligible_samples=0`、`status=unavailable`；`corpus_digest=ff64a62b27970bb8064c9cbbf11037c0f049383270d167c1090eab64ee5e07eb`；`freshness={repository_head=13da6055f173ab1459f62cb36de11bb05b2b19cc, source_archive_revision=r1, source_event_high_watermark=0}`。
> - **为何不在 plan.md 内嵌**：`refs/state-schema.md:95` 的 bootstrap 例外（plan 自嵌、locator 指向 plan 自身）已由 r2 消耗；本对象改用生成器产物。locator 语法（`state-schema.md:72`）的 `root-file` 必须是 plan 同目录的 bare allowlist 文件名，`evidence/` 路径不可寻址，故 canonical fenced 载体落在 allowlisted 根文件 `attempts.md`。

## 17. 修订历史

| 版本 | 触发 | 修订摘要 |
|---|---|---|
| candidate-1 | 初稿 | 三票初审前的初版设计 |
| candidate-2 | fresh Plan Repair Executor 合并三票初审（`uv-init-1/2/3.md`，50 条） | S1 删除 O3/D2、S2 O6 record-only、S3 改造 D1、S4 保留 D3 并按 Track 组织、S5 自验合规；逐条处置见 `attempts.md` §一 |
| candidate-3 | outer round-1（`round-1.md`）3 阻断 + 5 非阻断 | R1-1 r2 `terminal-decision` 实数改 3 条并按全事件流机械求值；R1-2 A-S4 补 `--active-dir` + §8.4；R1-3 改用生成器 calibration 报告；R1-4..R1-8 落点修正 |
| candidate-4 | 终局设计审查（`design-review.md`）M1–M6 + outer round-2（`round-2.md`）R2-1..R2-8 | M1 写入期/归档期共用 `resolve_events`（`_prepare_terminal_decision` :523-575、continue-parent :332-340）；M2 新增结构引用集 `{invocation-terminal.started_event_id, invocation-started.parent_event_id, design-review-completion.invocation_event_id}` 不可更正 + 3 条对抗（A1-12/13/14）；M3 规则 7 改取代链、`original_value` 比当前 effective（A1-15/16）；M4 删除规则 10 映射表与 `_validate_field_value`，单源 = 完整 `validate_event`；M5 授权 `user_quote` 内容绑定（A1-17）；M6 取消 `--active-dir`、改 `plan.parent` 读 state、opt-out 持久写入 `_budget-state.json` 顶层 `envelope_opt_outs`（A2-11/12）；R2-1..R2-8 文案/行号；§8 Acceptance 扩至 A1-17/A2-12；§6.2 21 处按 M6 重判（17 到达 / 4 早返回、helper 无需迁移）；§15 机器块与 calibration 报告字节未变 |
| **candidate-5** | 第二权威盲审 `blind-recheck-2.md` I-1..I-7（3 high + 4 low） | I-1 A1-1 单文件基线改本机实测 `4 failed/97 passed/2 skipped`（全量留 A-S2）；I-2 新增 `CORRECTION_EVIDENCE_FIELDS` 不可更正集（`prompt_evidence`/`output_evidence`/`source_locator`/`snapshot`），删「会被 `validate_event` 拒绝」失真表述，A1-18；I-3 `record_correction` 落盘前跑完整有效视图校验（`validate_event_graph` 含 authority + `validate_ledger`），A1-19/A1-20；I-4 §12 `:60` 措辞改「完整逐字原行」；I-5 写死 opt-out 直接 `read_state`→`write_state` 绕过 `needs_write`（R13/§6.2）；I-6 §8.2 增 A2-13 损坏 state 负例 + 统一映射 `governance_requires_task_envelope`；I-7 §15/§16 限定 canonical 形式逐字节一致、独立文件不被 preflight 校验；§8 Acceptance 扩至 A1-20/A2-13 |
| candidate-6 | blind-3（原件，已被 blind-4 错位评审覆盖、不可恢复）Issue-1..4（1 high + 1 medium + 2 low）+ 观察 a/b | Issue-1 证据集增 `artifact-captured.sha256`/`size`（A1-18/§11 O1.17/§12）；Issue-2 写期改为对 `raw+[pending]` 直接调 `validate_event_graph`/`validate_ledger`（§3 D1/§11 O1.16/O1.18/A1-19）；Issue-3 A1-11 限 reviewer-verdict（无 user-decision）；Issue-4 §5.3 增 S-F8；观察-a duplicate 锚点判定 `:1776`／print `:1777`；观察-b 例外区间改 `:95` |
| candidate-7 | **blind-4**（现文件名 `blind-recheck-3.md`，错位评审；内容实为对 candidate-6 的第 4 次盲审）Issue-1..4（1 high + 1 medium + 2 low）+ O-0 | Issue-1 M5 **删除 `reason` 子串分支**，改为 `user_quote` 须**同时**含（a）`corrected_event_id` 逐字子串、（b）被更正 `field` 名或逐字 `corrected_value`（`:220`/`:259`/`:262`/A1-17/§11 O1.15/§12 `:42`）；立身链步骤 6 与结论显式声明 r2 历史操作在新 M5 下不可原样重放（**刻意收紧**），其余推导步骤保持；Issue-2 `record_correction` 增前置条件「**仅事件流已闭合**（无未闭合 invocation / 未结清 reservation）可用」（`:293`/T1-F2），A1-2/A1-19/A1-20 fixture 注明完整事件流；Issue-3 T1-F1 `find_orphan_reservations`（`:697-737`）改走 `resolve_events`，新增回归 A1-21；Issue-4 `invocation_id`/`invocation_kind`/`parent_instance_id` 并入 `CORRECTION_STRUCTURAL_REF_FIELDS`（`:209`/§12 `:42`）；O-0 文件名错位事故披露；§8 Acceptance 扩至 A1-21 |
| **candidate-8（本版）** | **设计复审**（`design-review.md`，verdict=设计需修订）MF-1..MF-4 | MF-1 `("invocation-terminal","instance_id")` 并入 `CORRECTION_STRUCTURAL_REF_FIELDS`（§3 D1 常量/叙述/规则 4；§12 `:42` 字段集；§10 R10；§9 Non-Goal），新增对抗 A1-22，并执行「图/账本实例身份锚点」类别完备性扫描（结论见 `attempts.md` §十五）；MF-2 opt-out 写盘前缺 `defaults_version` 则置 `2`（§3 D3 门禁行为/opt-out 载体；§10 R13），A2-4/A2-12 增断言；MF-3 §3 D1 增生命周期定案（更正仅在 active 根；已归档须 `reopen`→record→`archive` 重投影进 `revision_chain`），新增端到端 A1-23；MF-4 定义 `FAIL_CLOSED:correction-precondition-unclosed`（`EXIT_FAIL_CLOSED`），登记于 §5 T1-F2/§6.1 G1/§11 O1.21/§7 T1-P2 为唯一口径；§7 T1-P3 产物扩至 A1-23；§8.4 范围同步；§15 机器块与 calibration canon 字节未改动 |

> **O-0（流程，blind-4 错位评审）**：本目录现存 `blind-recheck-3.md` 的内容**实为对 candidate-6 的第 4 次盲审（blind-4）**——编排层派发 blind-4 时复用未更新的 prompt 模板（内文写「写入 blind-recheck-3.md」），而 adapter 监视 `blind-recheck-4.md`，导致 worker 的完整复核覆盖了原 blind-3 原件（事故链路与对账见 `attempts.md` 末尾「披露 · blind-4 派发产物路径错配」）。该错位评审的结论（**阻断**）已由 candidate-7 本轮逐条处置；后续最终双认证的产物名将严格一致（派发前校验 `--output-name` 与 prompt 内产物路径一致）。

candidate-8 定稿的 preflight 复跑输出、字节数与 SHA-256 见 `attempts.md` §十五（各历史轮次见 §十一/§十二/§十四）。
