---
round: 3
reviewer_backend: opencode
reviewer_instance_id: 20260912_124111_079d96
generated_at: 2026-09-12T04:53:21.205653+00:00
verdict: 可执行
---
可执行

# round-3 · 子计划 B 完整收敛 outer 评议（candidate-4，设计修订后重新认证）

- 对象（本轮实核字节）：`.converge/active/20260911-op-envelope-b-contract-correction/plan.md`（frontmatter `status: candidate-4`，**754 行 / 109,410 B / SHA-256 `c50876de3bb53865b2c513dcfd711a19fcb0b402c88c3f2c52f12432a25d23ae`**）。
- 基线：HEAD `13da6055f173ab1459f62cb36de11bb05b2b19cc`；`git status --porcelain` = `?? docs/plans/active/`（与计划声明一致；`.converge/active/` 被 `.gitignore` 忽略）。
- 身份：fresh 独立 Reviewer（跨厂商，与 plan 作者、UV 初审、round-1/2 及 design-review 无共享上下文）；只读实核，除本报告外未修改任何文件；UTF-8。
- 判定：**可执行**（M1–M6 逐条落地；R1-1/R1-2/R1-3 三条前轮阻断全部实质闭合；D3 穷举经独立重数完整且分类正确；代码事实逐行核对无失真。发现 3 条 low/精度级问题 + 1 条 info 级设计观察，均不构成事实失真、不构成穷举缺项，故不升级为阻断）。

> **⚠ 简报与实物不一致（前置声明，非计划缺陷）**：本任务简报「受审对象」写为「candidate-3，83,818 B」，与工作树实际内容（candidate-4，109,410 B / `c50876de…`）不一致；candidate-3 的 83,818 B / `e7690e76…` 记录仅见于 `attempts.md:12`/§八 与 `round-2.md:12`。标题与本类「设计修订后重新认证」均指向 candidate-4。**本轮以工作树实际 candidate-4 字节为唯一受审对象**。该不一致不影响判定。

> **本轮我实际复跑的自验（逐字留痕）**：
> - 机器块自验：`python scripts/budget_gate.py preflight --plan .converge/active/20260911-op-envelope-b-contract-correction/plan.md` → `WARN:code_heavy:5,73` / `PREFLIGHT_OK:governance-change` / `EXIT=0`，与 `attempts.md` §10.1 逐字一致。
> - calibration 生成器复现：`python scripts/distill_antipatterns.py --calibration --root . --output <TEMP>/calib_check_r3.json --id calibration-op-b --source-revision r1` → `EXIT=0`；与仓库内 `evidence/calibration-report.json` **逐字节一致**（2385 B，SHA-256 均为 `c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581`）。
> - 全量测试基线复跑：`python -m pytest -q` → `4 failed, 476 passed, 5 skipped, 11 subtests passed in 281.80s`；4 fail 全为 `tests/test_archive_convergence.py` 的 Windows 8.3 短路径（`ADMINI~1` vs `Administrator`），与 `plan.md:563`/§10 R8 声明一致。
> - Phase 0 可执行性：把对象 active 目录整体复制到临时路径后 `python scripts/budget_gate.py init --active-dir <copy> --task-tier critical` → `EXIT=0`，输出四行披露（含计划新增第 4 行）；空目录 init 亦 `EXIT=0`。
> - r2 事件流机械复算：57 条事件；`terminal-decision` 恰 3 条（seq 17/45/54）；`DECISION_REFERENCED={14,42,53,17,45}` 不含事件 55。

---

## 一、前置自检 5 问

1. **产物身份自洽 — 通过**。frontmatter `status: candidate-4`；Goal（§1）、Track 结构（§4）、File Matrix（§5）、Acceptance（§8）指向一致；O3/O6 显式降为处置记录（§13/§14）。§17 修订历史自述 candidate-4 = design-review M1–M6 + round-2 R2-1..R2-8，与正文落点一致。
2. **产物边界诚实 — 通过**。§3 D4 明确 record-only 且无「若裁决为实现则实施」分支；§9 Non-Goals 与之一致；数值披露诚实（真机械下界=4 / 典型估计≈10 标注非下界 / r2 实测 23 且如实写 `initial 20 < 23`，`plan.md:302-304`）。
3. **产物数据纯度 — 通过**。全篇为仓库真实路径、实核行号、既有常量；`numeric_changes` 两条全 `kind: mechanism`；无业务数据、无环境硬编码（`ADMINI~1` 仅出现在 R1-8 环境事实中）。
4. **职责边界自洽 — 通过**。D1 唯一语义读取点（`validate_event_graph`/`validate_ledger` 入口各自 resolve，`plan.md:243-244`）；M1 显式把 capture 写入期纳入同一 `resolve_events`（`plan.md:245-249`）；D3 门禁/披露三处/adapter 写入点职责清晰。
5. **命名一致性 — 通过**。`plan.md:153` 命名锁定：事件 `event-correction`、manifest/INDEX 键 `corrections`、降级串前缀 `correction:`、常量 `CORRECTION_CLOSED_FIELDS` + `CORRECTION_STRUCTURAL_REF_FIELDS`；D3 触发统一为「含唯一 `converge.governance-change/v1` 机器块」（`plan.md:280`）。

---

## 二、R1-1 / R1-2 / R1-3 闭合清单（逐条 yes/no + 我独立复算证据）

### R1-1（阻断，事实失真：r2 terminal-decision 实数）— **YES，闭合**

- 指控回顾：candidate-2 立身用例推导链称「r2 唯一 terminal-decision 事件 54」，实为 3 条。
- 我的独立实核（实开 `.converge/done/20260910-process-controller-consolidation/evidence/events/`，57 条事件；`json` 逐条读 `event_type`）：
  - seq 17 `e4182ce3-fe3e-4683-9533-f36ecab465fd`：`reviewer_event_id`=`verdict_output_ref`=事件 14（`4952d7de-3dff-4fab-b778-196d76417239`），`supersedes_decision_event_id`=null，**无 `source_ref` 键**；
  - seq 45 `ea64c374-d650-43ae-a81a-1935aa06dfb9`：`reviewer_event_id`=`verdict_output_ref`=事件 42（`ef98b9ea-0526-4b3f-b7e3-cdf1236be6e7`），`supersedes`=事件 17，**无 `source_ref` 键**；
  - seq 54 `777a0e2d-859f-462d-80a5-7d135d5f04b5`：`reviewer_event_id`=`verdict_output_ref`=事件 53（`0aa365ab-72ab-4ed8-a320-b8e5c668b6e7`），`supersedes`=事件 45，**无 `source_ref` 键**；
  - 全事件流无 `user-decision`（type 集合仅 `invocation-started/invocation-terminal/terminal-decision/user-message`）。
- 机械求值：`DECISION_REFERENCED` = {reviewer_event_id}∪{verdict_output_ref}∪{supersedes}∪{source_ref(user-decision)} = {14,42,53}∪{14,42,53}∪{17,45}∪{} = **{14,42,53,17,45}**；事件 55（`cabcac00-bd16-4161-b857-c45733630580`）**不在集合内**。
- 事件 57（`9254cf87-cb91-4f08-9281-1648904f0a09`，`invocation-terminal`）以 `started_event_id` 引用事件 55——按 `plan.md:210-211` 的显式排除不构成闭包。
- 结论：`plan.md:216-226` 的推导链**逐步可复算**，且与 `round-2.md` §二一致；R1-1 已闭合。

### R1-2（阻断，Acceptance 自相矛盾：A-S4 vs D3 门禁）— **YES，闭合**

- 指控回顾：A-S4 缺 `--active-dir`，实现后必被自身新门禁判 exit 30。
- 实核：`plan.md:46` 明示 R1-2 的 `--active-dir` 处置已被 M6 取代；`plan.md:284` 取消 `--active-dir`、改以 `plan.parent` 读 state；`plan.md:548` A-S4 已改为无参命令 + 注明 Phase 0 在 `plan.parent` 配置；`plan.md:550-561` §8.4 逐条重审。
- **我独立重扫 §8 全部「命令 + 期望 exit 0」条目**：
  - 走 `preflight` 且期望 exit 0 的仅 **A2-1**（`plan.parent` 已配置）、**A2-4**（显式 opt-out）、**A-S4**（Phase 0 init 后 = `plan.parent` 已配置）三条；均与 M6 门禁自洽。
  - 期望 exit 30：A2-3 / A2-6 / A2-11；期望 `[]`/非 preflight：A1-1..A1-17、A2-7 legacy、A2-8/A2-9 输出形状、A2-10 pytest、A-S1/A-S2 pytest、A-S3 git diff。
  - **未发现任何「实现后 exit 语义翻转」的遗留条目**；A2-2/A2-5 已显式删除（`plan.md:529`/`:532`）。
- A-S4 可实现性：我用对象 active 目录副本实跑 `init --task-tier critical` → `EXIT=0`，该目录即 `plan.parent`，故实现后门禁通过、`PREFLIGHT_OK:governance-change`（机器块 `numeric_changes` 全 mechanism，无数值门冲突）。R1-2 已闭合。

### R1-3（阻断，治理自举：calibration 来源）— **YES，闭合**

- 指控回顾：candidate-2 复用已被 r2 消耗的 `refs/state-schema.md:95` 一次性 bootstrap 例外。
- 实核：
  1. `refs/state-schema.md:95` 确为「bootstrap 例外（一次性）…后续治理变更必须由 `--calibration` 生成的报告提供」；`plan.md:686`/`:738` 显式声明**不使用**该例外。
  2. 独立文件 `evidence/calibration-report.json` 真实存在，2385 B，SHA-256 `c4755e…`（我实算）。
  3. 我用同一命令重新生成到临时路径 → 与仓库文件 **逐字节一致**（`a==b` True），证明为生成器确定性输出而非手写。
  4. `plan.md:15` 附录 A 的 `calibration.path = attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration-op-b]`；`_resolve_report_locator`（`budget_gate.py:1502-1537`）以 `plan.parent / attempts.md` 打开、`attempts.md ∈ _ROOT_ALLOWLIST`（`budget_gate.py:1427-1431`）；preflight `EXIT=0` 即证明 fence canonical hash = `c4755e…`、`corpus_digest=ff64a62b…`、`freshness={13da6055…, r1, 0}` 三者逐字段机械相等。
  5. 报告形状与 `plan.md:742` 声明一致：`corpus` 19 条 `done:<slug>`、`eligible_samples=0`、`status=unavailable`。
- 结论：治理来源已从「一次性 bootstrap 例外」切换为 `--calibration` 真实生成报告，符合 `refs/state-schema.md:95`；R1-3 已闭合。

---

## 三、M1–M6 逐条落地核对（yes/no + plan 原文行号 + 独立复核）

| # | design-review 单选修法 | plan 落点（实核行号） | 落地 | 我的独立复核 |
|---|---|---|---|---|
| **M1** | 写入期与归档期共用同一 `resolve_events`；`_prepare_terminal_decision` 与 continue-parent 入口先 resolve | `plan.md:52`（索引）、`:105-106`（O1l/O1m）、`:245-249`（§3 D1）、`:364`（T1-F2）、`:516`（A1-11）、`:596`（R9） | **YES** | 实开 `capture.py:523-575`（`_prepare_terminal_decision`）与 `:332-340`（continue 分支）；`derive` :543、`validate_reviewer_verdict_authority` :560、`user-decision-source` :566-574 均在函数体内。`_commit_event:211-213` 以 raw `existing` 调 `prepare`，故「入口先 resolve」可落在 prepare 内，机制可行。归档期 `validate_event_graph:958`/`validate_ledger:594` 入口 resolve 后 `derive_presented_degradations` 与写入期同源。锚点无失真。 |
| **M2** | 新增最小结构引用集 `{inv-terminal.started_event_id, inv-started.parent_event_id, design-review-completion.invocation_event_id}` 不可更正 + 3 条对抗 | `plan.md:53`（索引）、`:107`（O1n）、`:173-177`/`:186`（§3 D1）、`:517-519`（A1-12/13/14）、`:623-625`（§11 O1.12-14）、`:597`（R10）、`:648`（§12 :42 规范句） | **YES** | 实开 `model.py:186`（`started_event_id` 在 `invocation-terminal`）、`:182`（`parent_event_id`）、`:202`（`invocation_event_id`）与校验 `:488`/`:481-486`/`:569`——字段归属与行号全部属实。`reservation_id` 属 `invocation-started` 值字段，不在结构集，立身用例保留。 |
| **M3** | 规则 7 改取代链：允许同 `(target,field)` 追加，`original_value` 必须等于当前 effective，每条独立授权，raw append-only，披露全链；删除 `correction-chained` | `plan.md:54`、`:195-196`（规则 6/7）、`:224`/`:232`/`:260`/`:268`、`:511`（A1-6）、`:520-521`（A1-15/16）、`:618`/`:620`（§11 O1.7/9）、`:598`（R11）、`:648`（§12 :42） | **YES** | 规则 6「无前序更正即 raw、有则取该链最新 `corrected_value`」与规则 7「取代链」自洽；`correction-chained` 已从 `plan.md:196` 与 §6.1 G1 的 8 码清单中移除。A1-15/16 与规则 6/7 一一对应。 |
| **M4** | 删除规则 10 字段映射表与 `_validate_field_value` 抽取；唯一值/跨字段来源 = 应用全部更正后候选跑完整 `validate_event` | `plan.md:55`、`:199`（规则 10）、`:228-230`（唯一来源段）、`:363`（T1-F1「无 `_validate_field_value`」）、`:621`（§11 O1.10）、`:328`（ADR） | **YES** | 实开 `validate_event`（`model.py:437`）含全部值谓词/跨字段（如 `:504-519` provenance 矩阵、`:534-536` artifact capability）与二次特化 `:445-455`、等集 `:456-458`；以之为唯一来源在构造上覆盖这些约束。全文已无 `_validate_field_value` 残留。 |
| **M5** | 授权内容绑定：`user_quote` 必须含 `corrected_event_id` 或本次 `reason` 逐字子串，否则 `correction-unauthorized` | `plan.md:56`、`:197`（规则 8）、`:234-239`（授权绑定段）、`:513`（A1-8）、`:522`（A1-17）、`:626`（§11 O1.15）、`:599`（R12）、`:648`（§12 :42） | **YES** | 复用 `capture.py:571-574` 的逐字匹配哲学；规则 8 的两种绑定（id 或 reason）与 A1-17 一致。 |
| **M6** | 取消 `--active-dir`，改 `plan.parent` 读 state；opt-out reason 持久写入 `_budget-state.json` 顶层 `envelope_opt_outs`；删 A2-5 类负例 | `plan.md:57`、`:282-293`（§3 D3）、`:373`（T2-F1）、`:379`（T2-F7）、`:380`（T2-F8）、`:410-457`（§6.2）、`:528-539`（A2-1..A2-12）、`:548`（A-S4）、`:550-561`（§8.4）、`:565-570`（§8.5）、`:629-637`（§11 O5）、`:600`/`:603`（R13/R6）、`:650`（§12 :454） | **YES** | 全文 `--active-dir` 出现 22 处，逐一判定：均为 **init 命令**（`:450`/`:473`/`:568`）、**M6 删除/取代说明**（`:46`/`:57`/`:118`/`:284`/`:334`/`:373`/`:379`/`:380`/`:407`/`:412`/`:452`/`:457`/`:529`/`:532`/`:551`/`:636`）或 ADR 被拒备选——**无一处残留「preflight 传入 `--active-dir`」的活设计**，全文一致。`read_state:247-263` 对缺失 state 返回空 config、`_validate_state_shape:208-244` 只校验 `config`/`extensions`/`fsm`、不拒绝额外顶层键（实开核）——`envelope_opt_outs` 载体可行。 |

**M6 特别项（本轮重点）**：
- **受影响用例重判（D3 穷举）**：见 §四，独立重数 = 21 处调用 / 17 到达新门禁 / 4 早返回，与 `plan.md:410` 及 `attempts.md:401` 完全一致。
- **机器块自验**：`EXIT=0` 复现（见文首）。
- **`--active-dir` 已不存在于现版 parser**：实开 `budget_gate.py:2134-2139`，仅 `--plan`/`--governance`；实跑带 `--active-dir` → `EXIT=2`，与 `attempts.md:421-429` 一致。

---

## 四、D3 穷举复核（独立重数）与 legacy 放行证明

- `TestGovernancePreflight`（`tests/test_budget_gate.py:1448`）内 `self.preflight(` 实核 = **21** 处，行号 1554/1566/1575/1584/1591/1602/1613/1623/1633/1641/1656/1666/1675/1682/1690/1699/1708/1717/1724/1736/1743，与 `plan.md:416-438` 逐行一致。
- 我逐用例实开 `tests/test_budget_gate.py:1448-1744` 并按 `cmd_preflight`（`budget_gate.py:1730-1778`）控制流分类：
  - **17 处到达新门禁**：`write_plan` 恒写 `self.dir`（`:1534-1544`），均为「恰好 1 个 gov 块」；`plan.parent == self.dir`，故需 `setUp`（`:1449-1451`）在该目录 init state。
  - **4 处早返回**：`:1682`（`extra_fences=[gov]` → 2 个 gov 块，`:1776` 检查先返回）、`:1724`（`crlf=True` 整文件 CRLF → `_extract_json_fences:1494` 归入 `crlf`、`payloads` 空 → 走 legacy 分支 `:1763`、在 `:1767-1768` 的 `any(b"converge." in p ...)` 返回）、`:1736`（无 fence → `:1769` legacy 早返回，输出 `CLEAN`）、`:1743`（`--governance` 无块 → `:1775` 返回）。
  - 分类结论与 `plan.md` 完全一致，**无漏项**。
- **legacy 放行证明**：`cmd_preflight` 在无 gov 块且无 `--governance` 时于 `:1769` 早返回，位于插入点 `:1777→:1778` 之前；`TestPreflight`（`:265-279`）两处 `run("preflight", ...)`（`:272`/`:278`）均无 gov 块 → 不受影响。
- **全仓调用面**：`grep` 实核 `scripts/**` 无 `preflight` 生产调用点（仅 parser/docstring）；测试中仅 `tests/test_budget_gate.py` 出现 `preflight`。G2 波及面被完整列举。
- **数值依据**：r2 `gate-ledger.jsonl` 实算 `reserved` = **23**（executor 5、ultraverge-initial 3、outer-reviewer 6、design-reviewer 5、blind-reviewer 4），与 `plan.md:304`/O5l 逐项相符；`cap 30` 余量 7、`feature cap 24` 余量 1、`initial 20 < 23` 均为真。

---

## 五、UV 三票处置抽查表（≥10 条；逐条回 plan 原文 + 代码实核）

统计核对：UV1 18（B1-B4 + N1-N14）+ UV2 16（I2-1..16）+ UV3 16（UV3-1..16）= **50** 条，与 `attempts.md` §一一致；处置 37 修复 / 10 因 S1 删除 / 3 因 S2 删除 / 0 其他。

| # | UV issue | 处置 | plan 落点实核 | 独立复核结论 |
|---|---|---|---|---|
| 1 | UV1 B1 / UV2 I2-5 / UV3-4（新门禁击穿既有 preflight） | 修复 | `plan.md:400-457`、`:537`（A2-10） | **真修复**。21 处调用、17/4 分类经我逐用例重数成立（§四），无漏项。 |
| 2 | UV2 I2-1（白名单与闭包互斥） | 修复 | `plan.md:169-184`、`:212-226` | **真修复**。动态白名单 = `EVENT_FIELDS[type] − CLOSED − STRUCTURAL`；事件 55 可更正；`DECISION_REFERENCED={14,42,53,17,45}` 实算成立。 |
| 3 | UV1 B3 / UV2 I2-7（有效视图未定界、`validate_archive` raw 校验） | 修复 | `plan.md:241-255` | **真修复**。`validate_archive:1178-1181` 经 `validate_event_graph`/`validate_ledger` 入口 resolve 覆盖；`_verify_evidence_bytes:1040` 仅读字节/结构字段。 |
| 4 | UV1 N3（`FailClosed` 抛出点 :1139） | 修复 | `plan.md:115` | **真修复**：抛出点 **:705**（`_task_envelope_initial` 内），:1137-1139 为触发点；实开核属实。 |
| 5 | UV1 N2 / UV2 I2-12 / UV3-9（O6a 锚点） | 修复 | `plan.md:132` | **真修复**：改为 `:97-100`；失效句确在 `refs/state-schema.md:100`。 |
| 6 | UV1 N5 / UV3-7（`started_event_id` 归属） | 修复 | `plan.md:201-211` | **真修复**：显式排除 `invocation-terminal.started_event_id`；4 个 decision 字段行号 `model.py:137/144/1008/1032` 实开属实。 |
| 7 | UV3-15（谓词 `_task_envelope_configured` ≠ 可用） | 修复 | `plan.md:291` | **真修复**：新增 `_task_envelope_usable`（initial+cap 均不抛）；实开核 cap-only 过 `:692-694` 但在 `:705` 抛。 |
| 8 | UV3-14（无显式 opt-out） | 修复 | `plan.md:286`、`:531`、`:533` | **真修复**：`--allow-unconfigured-envelope <reason>` + `WARN:unconfigured-envelope:<reason>` + 持久写入；空 reason 仍 exit 30。 |
| 9 | UV3-6 / R2-6（禁止批量无机械承载/归因） | 修复 | `plan.md:232`、`:619` | **真修复**：schema 层单字段闭集（`validate_event:456-458` 等集）+ 值谓词（单 UUID/单字符串）；归因完整。 |
| 10 | UV1 N6（`corrections` 须 omit-when-empty） | 修复 | `plan.md:260`、`:262` | **真修复**：manifest 键与 `render_index_bytes` 段均 omit-when-empty，沿用 `model.py:884-898` 惯例。 |
| 11 | UV1 N4 / UV2 I2-13（`__all__` 不存在） | 修复 | `plan.md:364` | **真修复**：实核 `grep __all__ scripts/archive_contract/capture.py` 无命中；T1-F2 已删该断言。 |
| 12 | UV1 N13 / UV2 I2-15（`validate_event` correction 分支） | 修复 | `plan.md:363`（T1-F1） | **真修复**：锚点 `:573-575`（user-message 分支之后插入）；实开 `:573-575` 直接相邻，落位合理。 |
| 13 | UV2 I2-16 / UV3-13 / R1-4 / R2-4（§12 对照非逐字） | 修复 | `plan.md:643-653` | **真修复（逐字）**。我用脚本把 §12 七行「原文」与目标文件逐字符比对：`state-schema.md:40/:42/:60/:454`、`SKILL.md:453/:466` 六处均为**逐字子串**；`orchestrator-guide.md:44-47` 四行经直接实开核亦逐字。R1-4/R2-4 闭合。 |
| 14 | UV1 B4 / UV2 I2-6 / UV3-16（O6 实现分支无界） | 因 S2 删除 | `plan.md:309-317`、`:668-677` | **处置可追溯**：record-only 定案，删实现分支，给重启判据 4 条 + 主观项披露。 |
| 15 | UV1 B2/N12、UV2 I2-2/3/4/10、UV3-1/2/11/12（O3 bootstrap） | 因 S1 删除 | `plan.md:274-276`、`:659-664` | **处置可追溯**：D2 整体删除；§13 引 r2 `attempts.md:210` 逐字 + `check valid`。 |
| 16 | UV1 N8（计划自身缺机器块/授权事件） | 修复 | `plan.md:681-734`、`:736-743` | **真修复**：机器块 + 生成报告载体；`ab8896b1…`（seq 9）、`06754e6f…`（seq 10）为对象 `evidence/events/` 的 `user-message`；4 个 `archaeology_refs` 经我 `git cat-file -e` 全部存在；preflight 复跑通过。 |
| 17 | UV3-16（拆分建议） | 结构化回应 | `plan.md:340-350` | **已回应**：Track-1/Track-2 独立 File Matrix/Phase/Acceptance + 「为何不拆对象」；用户已裁决合并。 |

「修复」项以外的 S1/S2 删除项均可在 `attempts.md` §一追溯；抽查未发现名义修复，未发现与代码相悖的落点。

---

## 六、D1 三项闭合性复核 + candidate-4 新矛盾排查（评审重点 2/3）

- **闭包规则（规则 1–5）自洽**：`allowed()` 排除 `{terminal-decision,event-correction}` 类型、5 个闭合身份字段、M2 三条出边结构字段（`plan.md:172-184`）；规则 3 对判定类型整体闭合；规则 5 以四条真实 decision 字段（**直接**引用，R2-8）额外保护相关 `invocation-terminal`/`user-message`/前序 decision。三者叠加后仍保留 `{invocation-started, artifact-captured, design-review-completion}` 的可更正载荷字段，立身用例（事件 55 的 `reservation_id`）不被误伤。**未发现 candidate-4 引入的新矛盾**。
- **有效视图单层施加**：`resolve_events` 前置 raw；`validate_event_graph:958`/`validate_ledger:594` 入口各自 resolve；`project_manifest:745-781/:782-790/:792-796/:856-862` 按 `raw_events`（字节哈希/路径/校验入口）与 `effective_events`（全部语义派生）双列表划分（`plan.md:250-253`）；M1 将 capture 写入期纳入同源（`:245-249`）。`resolve_events` 为纯函数、单次 apply 的不变量明确。**未发现二次施加路径**。
- **授权时序**：规则 9 `seq(corr) > seq(umsg) > seq(target)` 与规则 8 内容绑定、规则 6 effective 比较、规则 7 取代链自洽；立身用例（`>56>55`）成立；越权四例（`plan.md:239`）与 A1-8/A1-17 对应。
- **M3 取代链 vs append-only vs 授权时序**：取代链只追加新 `event-correction` 事件、不改写任何既有字节；每条独立授权；`original_value` 逐条比当前 effective。无「用旧 raw 覆盖已更正 effective」路径。
- **M2 出边集 vs 立身用例**：`reservation_id` 不在结构集，保留可更正；`started_event_id`/`parent_event_id`/`invocation_event_id` 三字段整体闭合。无矛盾。
- **M1 与既有判定链**：我实开 `capture._commit_event:198-243`，`prepare(fields, existing)` 在锁内、以 raw `existing` 调用；M1 的「入口先 resolve」落在 `_prepare_terminal_decision` 内即可，与其后 `validate_event(event):220`（只校验新事件）不冲突。写入期 `derive_decision_fields`/`validate_reviewer_verdict_authority`/`user-decision-source` 与归档期 `validate_event_graph` 的对应调用均读 effective，两期同源。

---

## 七、逐条 issue（全部非阻断；无事实失真、无 D3 穷举缺项）

#### R3-1 — [evidence-anchor · low] §2.4 把 `scripts/README.md:164` 标为「治理 preflight 模式散文」，但该行是节标题，散文在 `:166`

- **文件:行**：`plan.md:143`（§2.4 表末行）对照 `scripts/README.md:164` / `:166`。
- **原文**：「`scripts/README.md` | `:164` 治理 preflight 模式散文（…）」。
- **实核**：`:164` = `### 治理 preflight 模式`（标题）；治理 preflight 散文实体在 `:166`（「`budget_gate.py` 支持读取 `converge.governance-change/v1` …」）。
- **影响**：无机制影响；`plan.md:379`（T2-F7）已给 `:164-166` 区间，故 F7 的落位不受影响。仅 §2.4 行内锚注偏指标题。
- **单选建议**：§2.4 该格改为「`:164-166` 治理 preflight 模式节（标题 :164 / 散文 :166）」。

#### R3-2 — [coverage · low] §11 O5.5 的 cap-only 子情形在 §8 无 Acceptance 行，T2-F8 负例清单亦未含

- **文件:行**：`plan.md:634`（§11 O5.5「无 `task_tier`/cap-only 配置（initial 不可解析）→ 拒」）对照 `plan.md:530`（A2-3 仅覆盖「无 `_budget-state.json`」）与 `plan.md:380`（T2-F8 负例仅「未配置 / 空 reason / 持久写入」）。
- **实核**：`_validate_state_shape:236-237` 与 `initialize_state:312-314` 均允许仅配 `task_envelope_cap`（无 `task_tier`）；此时 `_task_envelope_configured:692-694` 为真，但 `_task_envelope_initial:705` 抛 `FailClosed`——正是 UV3-15 的落点。
- **影响**：`_task_envelope_usable`（M6 新增）的正确性（cap-only → fail-closed）是 UV3-15 的修复核心，却无机械 Acceptance 覆盖。非事实失真，非 D3 穷举缺项（D3 的 21 处分类完整）。
- **单选建议**：把 A2-3 扩为两条（或在 §8.2 增 A2-13）：「`plan.parent` 有 `_budget-state.json` 但仅 `task_envelope_cap`、无 `task_tier`、无 opt-out → `FAIL_CLOSED:governance_requires_task_envelope`，exit 30」；T2-F8 负例同步补该条。

#### R3-3 — [coverage · low] §11 O1 的三个 `correction-*` 码在 §8.1 无专属 Acceptance 行

- **文件:行**：`plan.md:622`（O1.11 `correction-target-missing`）、`plan.md:615`（O1.4 `correction-sequence`）、`plan.md:621`（O1.10 `correction-value-type`）对照 §8.1（`plan.md:504-522`）。
- **实核**：§8.1 有 `correction-closure-violation`（A1-3）、`correction-field-not-allowed`（A1-7/12/13/14）、`correction-original-mismatch`（A1-5/16）、`correction-unauthorized`/`correction-authorization-order`（A1-8/17）、M1/M3/M5/M2 专项；但 `correction-target-missing`、`correction-sequence`、`correction-value-type` 无独立行。
- **影响**：§11 标题为「必须逐条测试」、T1-F5 要求「含 §11 O1 全部对抗项」，故这些用例会被实现（A1-1 的 `test_archive_convergence.py -q` 覆盖）；但 §8.1 作为「条条可机械判定」的验收表未逐码映射，Phase 6 机械执行者无法从 §8.1 直接核对这三码。非事实失真。
- **单选建议**：在 §8.1 增三行（A1-18/19/20）分别断言 `correction-target-missing` / `correction-sequence` / `correction-value-type`；或在 §8.1 表头注明「§11 O1 全项由 T1-F5 实现、A1-1 承载，本表仅列代表性码位」。

#### R3-4 — [design-observation · info] decision 派生降级字段的「后更正」时序未在设计中显式声明（且 M3 已提供修复路径）

- **文件:行**：`plan.md:195-196`（规则 6/7）、`:248`（M1 示例仅覆盖「target 之后、decision 之前」）对照 `model.py:1035`（`validate_event_graph` 用 effective `derive_presented_degradations(prior)` 与 decision 已存值逐字比较）。
- **观察**：可更正字段含 `invocation-terminal.evidence_level`、`artifact-captured.reproduction_capability`（`plan.md:248` 明说二者仍可更正），而二者正是 `derive_presented_degradations`（`model.py:915-921`）的输入。若在既有 `user-decision` **之后**追加更正改变这些字段，归档期重派生将与该 decision 的已存 `presented_degradations` 不一致（`user-decision-degradations`）。M1 只声明并测试了「更正先于 decision」（A1-11），未覆盖「更正后于 decision」。
- **严重性说明（为何不升为阻断）**：`terminal-decision` 虽不可更正，但 M3 的取代链允许对同一 `(target,field)` 追加「回退更正」——把该字段 effective 值改回原值即可使重派生与已存 decision 重新一致，故**存在 in-band 修复路径，不构成永久 fail-closed**（与 `plan.md:248` 所消除的缺陷类别不同）。
- **单选建议**：在 §3 D1「有效视图」或 §10 R9 增一句边界声明：「decision 派生字段（`presented_degradations`）的依赖事件若在 decision 之后被更正，归档期将 `user-decision-degradations`；恢复方式为对同一 `(target,field)` 追加回退更正（M3 取代链）」。可选：A1-11 增补该「后于 decision + 回退」用例以固化。

---

## 八、可执行性、治理合规与实施前前置条件

- **两 Track Phase bounded**：Track-1（T1-P1/P2/P3）、Track-2（T2-P1..P4）、Phase 0/6/7（`plan.md:472-496`）每步有产物与验证；未通过不进入下一步。
- **Acceptance 机械可判定**：除 R3-2/R3-3 的覆盖补强（非机制阻断，判据本身明确）外，§8 各行均可机械判定；A1-1/A-S1/A-S2 已按环境事实采用「非新增失败」口径（本机基线 4/476/5/11，我复跑一致）。
- **第三部修改授权**：`review_mode: ultraverge` + `CONSTITUTION.md:91-96` 第四部程序成立；S-F3/S-F4/S-F5 显式不改（`:390-392`）；T1-F4/T2-F4/T2-F5/T2-F6 每处改动在 §12 有逐字对照（我逐字符核实通过），A-S3 可 `git diff` 机械核验。
- **治理自举合规**：机器块（`plan.md:688-734`）+ 用户授权 `user-message`（seq 9/10，实核为 `user-message`）+ 生成器 calibration 报告（逐字节可复现）齐备；preflight 机械校验通过。
- **实施前必须满足的前置条件（阻断性）：无。**
- **建议随实施一并落地（非阻断，可并入对应 Phase 以消除机械执行歧义）**：
  1. R3-1：修正 §2.4 的 `scripts/README.md` 锚注为 `:164-166`。
  2. R3-2：补 cap-only 门禁 Acceptance（A2-13 类）并把 T2-F8 负例清单同步。
  3. R3-3：补 `correction-target-missing`/`correction-sequence`/`correction-value-type` 的 §8.1 行或表头说明。
  4. R3-4：补 decision 派生字段「后更正 + M3 回退」边界声明与可选用例。

---

## 九、结尾

- **是否需拆分对象：否**。Track-1（O1）与 Track-2（O5）的代码路径、失败语义、回滚面不相交（唯一交点为 `state-schema.md` 两处不相邻章节 + 共享测试文件，§4/§12 已隔离）；本轮 3 条 low 问题全为锚注/覆盖度，1 条 info 为设计边界声明，均不涉及机制重设计。UV3-16 的拆分建议已由用户合并裁决与结构化 Track 回应。
- **无法核实 / 环境相关断言清单**：
  1. **r2 事件 55 曾存在的字面量 `PENDING` 字节**：该文件 `git log --follow` 仅一次提交 `529e691` 且内容已是 `81a2537ea9eb`；可证实事件 56 的 `user_quote`（UTF-8 解码为「授权披露式更正：把事件 55 的 reservation_id 从 PENDING 改为真实存在的 81a2537ea9eb」），无法独立证实历史 `PENDING` 字节（与 `plan.md:222` 自述一致）。
  2. **A 对象「480 passed / 全绿」基线**：本机复跑为 `4 failed / 476 passed / 5 skipped / 11 subtests`，4 fail 全为 Windows 8.3 短路径（`ADMINI~1` vs `Administrator`），无法在本环境复现 480/全绿；计划已如实记录为环境等价结果（`plan.md:563`）。
  3. **实现后才可验证的行为**：`resolve_events`/`validate_corrections` 规则 1–10、M1 的 capture 双期一致、M2 三条结构引用拒绝、M3 取代链、M5 内容绑定、`_task_envelope_usable`、preflight 信封门、三处 init 第 4 行、adapter `--task-*`——本轮只确认设计可行与落点/接口存在，以及红测可先失败。
  4. **「机械下界 = 4」**：源自 `ultraverge_min_reviewers(3) + 设计审查 1 = 4` 的机制推导，属可辩护下界论证，无法静态机械证明「最小派发」；r2 实测 23 我已独立复算属实。
  5. **calibration 报告 freshness 的实时性**：`_resolve_and_check_report:1655-1680` 仅比较 gov 块与报告内的 `freshness`，不重算活 HEAD/high-water；报告 `repository_head=13da6055` 与当前 HEAD 一致，但该「新鲜度」在代码语义上非实时校验（计划未声称相反，非计划缺陷）。
  6. **用户 2026-09-12 授权范围是否语义覆盖「O5 并入 B」**：`ab8896b1…`（seq 9）事件文本涵盖 C→B 合并，属语义判断，非纯机械。
  7. **本任务简报「受审对象」文本**：简报写 candidate-3/83,818 B，与工作树实际 candidate-4/109,410 B 不一致；已按实际字节评审，无法核实简报该行的来源。
