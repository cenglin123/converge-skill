---
round: 5
reviewer_backend: opencode
verdict: 可执行
generated_at: 2026-09-12T06:04:59+00:00
reviewer_instance_id: 20260912_135942_663365
---

可执行

# round-5 · 子计划 B 完整收敛 outer 评议（candidate-7，blind-4 错位评审处置后最终认证）

- 受审对象（本轮实核字节）：`.converge/active/20260911-op-envelope-b-contract-correction/plan.md`（frontmatter `status: candidate-7`，**799 行 / 132,806 B / SHA-256 `6ac0bb8a395c745b06d766bcbd9c6fa9c1491eb62485d7b2084a3daca55e82d8`**）。
- 基线：HEAD `13da6055f173ab1459f62cb36de11bb05b2b19cc`；`git status --porcelain` = `?? docs/plans/active/`（与计划声明一致；`.converge/active/` 被 `.gitignore` 忽略）。
- 身份：fresh 独立 Reviewer（跨厂商，与 plan 作者、UV 初审、round-1..4、design-review、blind-1..4 均无共享上下文）；只读实核，除本报告外未修改任何文件；UTF-8。
- 判定：**可执行**。blind-4（错位评审）Issue-1..4 + O-0 逐条按单选修法落地（5/5）；R1-1/R1-2/R1-3 三条前轮阻断实质闭合；D1 三项闭包自洽且 Issue-1/2 未引入机制级新矛盾；D3 穷举经独立重数完整且分类正确；§12 七处逐字对照全部逐字；代码事实逐行实核无失真。发现 1 条 medium 内部残留表述（§2 O1h 与新 M5 矛盾，文档同步级、不触碰机制/验收）+ 4 条 low 精度/覆盖问题 + 1 条 info，均不构成事实失真、不构成穷举缺项，故不升级为阻断。

> **⚠ 简报与实物不一致（前置声明，非计划缺陷）**：本任务简报「受审对象」写为「candidate-3，83,818 B」，与工作树实际内容（candidate-7，132,806 B / `6ac0bb8a…`）不一致；candidate-3 的 83,818 B / `e7690e76…` 记录仅见于 `attempts.md:15`/§八、`round-2.md:12`。标题「R5 / blind-4 错位评审处置后」、正文 §0.4/§0.6/§17 修订历史与 `attempts.md` §十四均指向 candidate-7。**本轮以工作树实际 candidate-7 字节为唯一受审对象**。该不一致不影响判定。

> **本轮我实际执行的自验（逐字留痕）**：
> - 机器块自验：`python scripts/budget_gate.py preflight --plan .converge/active/20260911-op-envelope-b-contract-correction/plan.md` → `WARN:code_heavy:5,86` / `PREFLIGHT_OK:governance-change` / `EXIT=0`，与 `attempts.md` §14.1 逐字一致。
> - calibration 文件实核：`evidence/calibration-report.json` = 2385 B / SHA-256 `c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581`，与 §15/§16 声明一致。
> - r2 事件流机械复算：57 事件；`terminal-decision` 恰 3 条（seq 17/45/54）；`DECISION_REFERENCED` = {14,42,53,17,45}，事件 55 `cabcac00-…` 不在集合；事件 55 现值 `reservation_id=81a2537ea9eb`；事件 56 `user_quote` 确不含 target UUID。
> - 对象授权事件实核：seq 9 `ab8896b1…`、seq 10 `06754e6f…` 均为 `user-message`；§15 4 个 `git:` archaeology 引用经 `git cat-file -e` 全部存在。
> - r2 gate-ledger 复算：`reserved` = 23（executor 5 / ultraverge-initial 3 / outer-reviewer 6 / design-reviewer 5 / blind-reviewer 4），与 O5l/§3 D3 逐项相符。
> - D3 影响面复算：`TestGovernancePreflight` 内 `self.preflight(` = 21 处，逐用例分类 17 到达 / 4 早返回。
> - §12 逐字比对：6 条「」引文 + orchestrator-guide 四行，程序化 `quote == actual` 全部 True。

---

## 一、前置自检 5 问

1. **产物身份自洽 — 通过**。frontmatter `status: candidate-7`；Goal（§1）、Track 结构（§4）、File Matrix（§5）、Acceptance（§8）指向一致；O3/O6 显式降为处置记录（§13/§14）。§17 修订历史自述 candidate-7 = blind-4（错位评审）Issue-1..4 + O-0，与正文 §0.4/§0.6 一致（唯 line anchor 有偏移，见低-2 issue F2）。
2. **产物边界诚实 — 通过**。§3 D4 明确 record-only 且无「若裁决为实现则实施」分支；§9 Non-Goals 与之一致；数值披露诚实（真机械下界=4 / 典型估计≈10 标注非下界 / r2 实测 23 且如实写 `initial 20 < 23`，`plan.md:332`）。
3. **产物数据纯度 — 通过**。全篇为仓库真实路径、实核行号、既有常量；`numeric_changes` 两条全 `kind: mechanism`；无业务数据、无环境硬编码。
4. **职责边界自洽 — 通过**。D1 唯一语义读取点（`validate_event_graph`/`validate_ledger` 入口各自 resolve，`plan.md:271-272`）；M1 显式把 capture 写入期纳入同一 `resolve_events`（`plan.md:273-277`）；I-3 显式把 `record_correction` 落盘前纳入完整有效视图校验（`plan.md:298`）；D3 门禁/披露三处/adapter 写入点职责清晰。
5. **命名一致性 — 通过**。`plan.md:166` 命名锁定：事件 `event-correction`、manifest/INDEX 键 `corrections`、降级串前缀 `correction:`、常量 `CORRECTION_CLOSED_FIELDS` + `CORRECTION_STRUCTURAL_REF_FIELDS` + `CORRECTION_EVIDENCE_FIELDS`；D3 触发统一为「含唯一 `converge.governance-change/v1` 机器块」（`plan.md:308`）。

---

## 二、blind-4（错位评审 `blind-recheck-3.md`）Issue-1..4 + O-0 逐条落地核对（yes/no + 原文行号 + 独立复核）

> 说明：现 `blind-recheck-3.md` 内容实为对 **candidate-6** 的第 4 次盲审（verdict=阻断），其 Issue-1..4 已由 candidate-7 逐条处置。以下按该报告正文（`blind-recheck-3.md:103-125`）逐条核对。

| # | blind-4 单选建议 | plan candidate-7 落点（实核行号） | 落地 | 我的独立复核 |
|---|---|---|---|---|
| **Issue-1** (high) | 删除 `reason` 分支：`user_quote` 必须同时含 `corrected_event_id` 逐字子串 + `field` 名或逐字 `corrected_value`；立身链步骤 6 声明历史重放依赖被删分支 | `plan.md:58`（§0.4 M5）、`:225`（规则 8 正文）、`:264`（授权绑定-内容绑定）、`:267`（越权用例③）、`:551`（A1-17）、`:661`（§11 O1.15）、`:688`（§12 `:42` 新文）、`:251`/`:254`（立身链步骤 6 与结论注）、`:631`/`:633`（R10/R12） | **YES** | 实开确认规则 8（`:225`）已删「或含 `reason` 子串」，改为「**同时**含 (a) UUID、(b) field 名或逐字 corrected_value」；A1-17 三分支（仅 id 缺 field/value、仅 field/value 缺 id、语义无关 quote）齐备；立身链步骤 6（`:251`）明写事件 56 quote 不含 target UUID → 历史操作在新 M5 下不可原样重放。事件 56 实核 `user_quote` 仅含「事件 55 / reservation_id / PENDING / 81a2537ea9eb」，确无 `cabcac00-…`。**结论：落地，且保护确已兑现（不再是自由文本可绕过的空承诺）。** |
| **Issue-2** (medium) | 接受「仅事件流已闭合」并显式写入：`record_correction` 增前置条件「无未闭合 invocation / 未结清 reservation」 | `plan.md:298`（调用入口，**前置条件（blind-4 Issue-2）** 段）、`:392`（T1-F2）、`:536`（A1-2 fixture 注明完整事件流）、`:553`（A1-19）、`:554`（A1-20） | **YES** | 实开确认 `plan.md:298` 写明「仅可在事件流已闭合时调用」并给出机制理由（`validate_event_graph:992-994` 无条件拒绝未闭合 invocation；`validate_ledger:642-644/:653` 无条件拒绝未结清 reservation）。与 blind-4 建议的「接受并显式写入」一致。**闭合前置 vs 写期哲学：不冲突**——plan 把该前置定位为「注定 fail-closed 的更正不落盘」哲学的自然推论（`:298` 与 `capture.py:523-540` 同哲学）。 |
| **Issue-3** (low) | `find_orphan_reservations` 改走 `resolve_events`（或显式注明语义差异）+ 加回归 | `plan.md:391`（T1-F1：`find_orphan_reservations`（`:697-737`，现 `load_events` 直读 raw）改走 `resolve_events`）、`:555`（A1-21）、`:509`（T1-P3）、`:590`（§8.4 列 A1-21） | **YES** | 实开 `model.py:697-737`：`:727` 确以 `load_events` 直读 raw、`:728` 只筛 `invocation_kind=="spawn"` 的 `reservation_id`。改走 `resolve_events` 后与严格 `check` 同源的目标成立。见低-4 issue F4（lenient 契约），不改变落地事实。 |
| **Issue-4** (low) | `invocation_id`/`invocation_kind`/`parent_instance_id` 并入 `CORRECTION_STRUCTURAL_REF_FIELDS`，或显式定位 | `plan.md:186-194`（常量：`invocation-started.invocation_id`、`invocation-terminal.invocation_id`、`invocation-started.invocation_kind`、`invocation-started.parent_instance_id` 四条并入）、`:214`（M2 边界段补述）、`:631`（R10）、`:688`（§12 `:42` 新文） | **YES** | 实开 `model.py:181-183/186`：`invocation_id` 确在 started 与 terminal 两型、`invocation_kind`/`parent_instance_id` 仅在 started；常量覆盖齐全。`allowed()`（`:203-208`）经 `(target.event_type, f) not in CORRECTION_STRUCTURAL_REF_FIELDS` 整体闭合。**立身用例的 `reservation_id` 未被误伤**。 |
| **O-0** (process) | 修订历史注明 blind-4 错位与后续双认证约定 | `plan.md:795`（§17 candidate-7 行）、`:797`（O-0 披露段） | **YES** | 实开确认 §17 已披露「现 `blind-recheck-3.md` 内容实为对 candidate-6 的第 4 次盲审（blind-4）」，`attempts.md:549-558` 有完整事故链与对账。 |

**统计：Issue-1..4 + O-0 全部落地（5/5）**；无「或」式未选定方案。

---

## 三、R1-1 / R1-2 / R1-3 闭合清单（逐条 yes/no + 独立复算）

### R1-1（阻断，事实失真：r2 `terminal-decision` 实数）— **YES，闭合**

- 独立实开 r2 `.converge/done/20260910-process-controller-consolidation/evidence/events/`（57 事件），`terminal-decision` 恰 **3 条**：
  - seq 17 `e4182ce3-…`：`reviewer_event_id`=`verdict_output_ref`=事件 14 `4952d7de-…`，`supersedes`=null，无 `source_ref` 键；
  - seq 45 `ea64c374-…`：=事件 42 `ef98b9ea-…`，`supersedes`=事件 17，无 `source_ref` 键；
  - seq 54 `777a0e2d-…`：=事件 53 `0aa365ab-…`，`supersedes`=事件 45，无 `source_ref` 键。
- 机械求值：`DECISION_REFERENCED` = {14,42,53}∪{17,45} = **{14,42,53,17,45}**；事件 55 `cabcac00-…` **不在集合内**。
- `plan.md:244-254` 推导链逐步可复算：步骤 3 的 5 个集合元素、步骤 4（事件 57 以 `started_event_id` 引用 55、非 decision 引用边）、步骤 5-8 与我的实算逐项吻合。**R1-1 闭合。**

### R1-2（阻断，Acceptance 自相矛盾：A-S4 vs D3 门禁）— **YES，闭合**

- `plan.md:48` 明示 R1-2 的 `--active-dir` 处置已被 M6 取代；`plan.md:310-315` 取消 `--active-dir`、改以 `plan.parent` 读 state；`plan.md:582` A-S4 已改为无参命令 + Phase 0 在 `plan.parent` 配置；`plan.md:584-595` §8.4 逐条重审。
- **我独立重扫 §8 全部「命令 + 期望 exit」条目**：走 `preflight` 且期望 exit 0 的仅 **A2-1**（`plan.parent` 已配置）、**A2-4**（显式 opt-out + 持久写入）、**A-S4**（Phase 0 init 后 = `plan.parent` 已配置）三条；期望 exit 30 为 A2-3/A2-6/A2-11/A2-13；A1-1..A1-21 为 pytest / `archive_convergence check` / `list-orphan-reservations`（不触发 preflight 门禁）；A2-7/A2-8/A2-9/A2-10/A2-12 为 legacy/init/adapter/pytest/opt-out 持久披露；A-S1/A-S2/A-S3 为 pytest/git diff。**未发现任何「实现后 exit 语义翻转」的遗留条目**；A2-2/A2-5 已显式删除（`plan.md:562`/`:565`）。**R1-2 闭合。**

### R1-3（阻断，治理自举：calibration 来源）— **YES，闭合**

- `refs/state-schema.md:95` 确为「bootstrap 例外（一次性）…后续治理变更必须由 `--calibration` 生成的报告提供」；`plan.md:725-726` 显式声明**不使用**该例外。
- 独立文件 `evidence/calibration-report.json` 真实存在：2385 B / SHA-256 `c4755e…`（我实算）。报告字段：`schema=converge.calibration-report/v1`、`id=calibration-op-b`、`scope=done-corpus`、`corpus_digest=ff64a62b…`、`freshness={13da6055…, r1, 0}`、`quantitative_aggregates={eligible_samples:0,status:unavailable}`、corpus 19 条 `done:<slug>`——与 `plan.md:725`/§16 声明逐字一致。
- locator `attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration-op-b]`：`attempts.md` 的 fence canonical 字节与独立文件 sha256 一致（§16 已按 blind-2 I-7 限定 canonical 形式、注明 raw body sha `9a08eb6e…` 不同）；preflight `EXIT=0` 即机械证明 canonical hash/digest/freshness 三者一致。**R1-3 闭合。**

---

## 四、Issue-1/2 改动引入新矛盾排查（评审重点 2）

- **M5 严格化 vs 立身链 — 机制层无矛盾，证据表层有 1 处残留（见 F1）**。§3 D1 步骤 6（`:251`）与结论注（`:254`）显式声明：事件 56 quote 不含 target UUID → 历史操作在新 M5 下**不可原样重放**，机械重放须构造一条同时含 UUID 与 `reservation_id`/`81a2537ea9eb` 的新 `user-message`；「字段可更正性」结论（步骤 1–5、7–8）不受影响。A1-2（`:536`）已相应改为「合成…重放事件 55 **形态**（完整事件流）」而非逐字复用事件 56。**机制自洽**。唯一残留：§2 O1h 行的「修正」列仍写「立身用例按事件 56 的授权文本重放（见 §3 D1）」（`plan.md:113`），与新 M5/步骤 6 直接矛盾 → 见 issue **F1**（文档同步级）。
- **闭合前置 vs 写期哲学 — 无矛盾**。Issue-2 的前置条件（`:298`）正是「注定 fail-closed 的更正不落盘」哲学的延伸；plan 明确以「未满足即 fail-closed 拒绝调用，而非把『对象尚未闭合』误报为『更正非法』」界定语义（`:298` 末句）。
- **Issue-4 新闭包 vs 立身用例 — 无矛盾**。新增四条身份/拓扑邻接字段不在立身用例字段路径上；`reservation_id` 仍可更正（`:214`/`:243`）。

---

## 五、D1 三项闭合性复核（评审重点 3）

- **闭包规则自洽**：规则 1–5（`plan.md:218-222`）覆盖 target 缺失、序列、判定闭合、字段白名单、被 decision 直接引用闭合；`allowed()`（`:203-208`）= `EVENT_FIELDS[target_type]` − `CORRECTION_CLOSED_FIELDS` − `CORRECTION_EVIDENCE_FIELDS` − `CORRECTION_STRUCTURAL_REF_FIELDS`。规则 3 对 `{terminal-decision,event-correction}` 整体闭合；规则 5 以四条真实 decision 边（`model.py:137/144/1008/1032`，我实开全部命中）额外保护入边。三者叠加后仍保留 `{invocation-started, artifact-captured, design-review-completion}` 的可更正值/载荷字段，立身用例不被误伤。**自洽**。
- **有效视图单层施加自洽**：`resolve_events` 前置 raw（`plan.md:271`）；`validate_event_graph`（`model.py:958`）/`validate_ledger`（`:594`）入口各自 resolve；`project_manifest` 按 `raw_events`（`:745`/`:759-762` 字节哈希路径）与 `effective_events`（`:758-781` 投影、`:782-790` final、`:792-796` allowed_blobs、`:856-862` degradations）双列表划分（`plan.md:278-281`）；M1 将 capture 写入期纳入同源（`:273-277`）。`resolve_events` 纯函数、单次 apply 不变量明确。**未发现二次施加路径**。
- **授权时序自洽**：规则 8/9（`plan.md:225-226`）= exists ∧ `user-message` ∧ `user_quote` 内容绑定（M5 收紧）∧ `seq(corr)>seq(umsg)>seq(target)`；与立身用例（>56>55）及越权四例（`:267`）一致；规则 6（首条比 raw、后续比 effective）与规则 7（取代链）自洽。
- **结论：D1 三项闭合性仍自洽；candidate-7 的 Issue-1/2/4 改动未引入机制级新矛盾。**

---

## 六、D3 穷举复核（独立重数）+ legacy 放行证明 + 数值依据（评审重点 4）

- `TestGovernancePreflight`（`tests/test_budget_gate.py:1448`）内 `self.preflight(` 实核 = **21** 处，行号 `1554/1566/1575/1584/1591/1602/1613/1623/1633/1641/1656/1666/1675/1682/1690/1699/1708/1717/1724/1736/1743`，与 `plan.md:445-467` 逐行一致。
- 我逐用例实开 `tests/test_budget_gate.py:1448-1745` 并按 `cmd_preflight`（`budget_gate.py:1730-1778`）控制流分类：
  - **17 处到达新门禁**：均为「恰好 1 个 gov 块」——`:1554/:1566/:1575/:1584/:1591/:1602/:1613/:1623/:1633/:1641/:1656/:1666/:1675/:1690/:1699/:1708/:1717`。特别核：`:1641` `extra_fences=[report]`（report 为 `converge.calibration-report/v1`，非 gov）→ 仍 1 个 gov 块；`:1651-1655` 手写的 wrong-schema 用例也是 1 个 gov 块。`write_plan`（`:1534-1544`）恒写 `self.dir`，`plan.parent == self.dir`。
  - **4 处早返回**：`:1682`（`extra_fences=[gov]` → 2 个 gov 块，`:1777` 先返回）；`:1724`（`crlf=True` → `:1767-1768` 返回）；`:1736`（无 fence → `:1769` legacy 早返回，输出 `CLEAN`）；`:1743`（`--governance` 无块 → `:1775` 返回）。
  - 与 `plan.md` 分类**完全一致，无漏项**。
- **legacy 放行证明**：插入点位于 `:1777`（duplicate 判定/print）之后、`:1778`（`return cmd_preflight_governance`）之前；无 gov 块且无 `--governance` 时于 `:1769` 早返回，早于插入点。`TestPreflight`（`:265-279`）两处裸 `run("preflight", ...)`（`:272`/`:278`）均无 gov 块 → 不受影响。**放行证明成立。**
- **数值依据**：r2 `gate-ledger.jsonl` 实算 `reserved` = **23**（`target_role`：executor 5 / ultraverge-initial 3 / outer-reviewer 6 / design-reviewer 5 / blind-reviewer 4），与 `plan.md:332`/O5l 逐项相符；`cap 30` 余量 7、`feature cap 24` 余量 1、`initial 20 < 23` 均为真。**穷举完整、分类正确、数值属实。**

---

## 七、UV 三票处置抽查表（≥10 条；逐条回 plan 原文 + 代码实核）

统计核对：UV1 18 + UV2 16 + UV3 16 = **50** 条，与 `attempts.md` §一一致（37 修复 / 10 因 S1 删除 / 3 因 S2 删除）。

| # | UV issue | 落点（实核行号） | 独立复核结论 |
|---|---|---|---|
| 1 | UV1 B1 / UV2 I2-5 / UV3-4（新门禁击穿既有 preflight） | `plan.md:439-469`（§6.2 逐处） | **真修复**：21 处调用、17/4 分类经我独立重数成立（§六），无漏项。 |
| 2 | UV2 I2-1（白名单与闭包互斥） | `plan.md:182-210`、`:240-254` | **真修复**：动态白名单；`DECISION_REFERENCED={14,42,53,17,45}` 实算成立，事件 55 可更正。 |
| 3 | UV1 B3 / UV2 I2-7（有效视图未定界） | `plan.md:269-283` | **真修复**：`validate_archive:1178-1181` 经入口 resolve 覆盖；`project_manifest` 双列表逐行号声明。 |
| 4 | UV1 N3（`FailClosed` 抛出点 :1139） | `plan.md:128` | **真修复**：抛出点实核 **:705**（`_task_envelope_initial` 内），`:1137-1139` 为触发点。 |
| 5 | UV1 N2 / UV2 I2-12 / UV3-9（O6a 锚点） | `plan.md:145` | **真修复**：`refs/state-schema.md:97-100`；失效句确在 `:100`，`:95` 为 bootstrap 例外（`:96` 空行；实开逐行核对）。 |
| 6 | UV1 N5 / UV3-7（`started_event_id` 归属） | `plan.md:229-238` | **真修复**：引用集仅 4 个 decision 字段；`model.py:137/144/1008/1032` 实开命中。 |
| 7 | UV3-15（`_task_envelope_configured` ≠ 可用） | `plan.md:319` | **真修复**：仅配 `task_envelope_cap` 时 `:692-694` 为真但 `:705` 抛（实开核）；新增 `_task_envelope_usable`。 |
| 8 | UV3-14（无显式 opt-out） | `plan.md:314`/`:317`/`:564` | **真修复**：`--allow-unconfigured-envelope <reason>` + 持久写入 + 空 reason fail-closed。 |
| 9 | UV3-6 / R2-6（禁止批量无机械承载） | `plan.md:260` | **真修复**：单字段闭集（`model.py:456-458` 等集）+ 值谓词单一来源。 |
| 10 | UV1 N6（`corrections` 须 omit-when-empty） | `plan.md:288`/`:290` | **真修复**：manifest 键与 `render_index_bytes` 段均 omit-when-empty（沿用 `model.py:884-893`）。 |
| 11 | UV1 N4 / UV2 I2-13（`__all__` 不存在） | `plan.md:392` | **真修复**：实核 `capture.py` 无 `__all__`。 |
| 12 | UV2 I2-16 / UV3-13 / R1-4 / R2-4 / blind-2 I-4（§12 逐字） | `plan.md:683-693` | **真修复（逐字）**：7 处引文程序化比对全部 `quote==actual`（§八）。 |
| 13 | UV1 B4 / UV2 I2-6 / UV3-16（O6 实现分支无界） | `plan.md:337-345`、`:708-717` | **处置可追溯**：record-only 定案，删实现分支，给重启判据 4 条。 |
| 14 | UV1 B2/N12、UV2 I2-2/3/4/10、UV3-1/2/11/12（O3 bootstrap） | `plan.md:302-304`、`:699-704` | **处置可追溯**：D2 整体删除；§13 引 r2 `attempts.md:210` + `check valid`。 |
| 15 | UV1 N8（本计划自身缺机器块/授权事件） | `plan.md:721-774`、`:776-783` | **真修复**：机器块 + 生成报告载体；seq 9/10 `user-message` 实核；4 个 `git:` 引用 `cat-file -e` 存在；preflight `EXIT=0`。 |
| 16 | UV3-16（拆分建议） | `plan.md:368-378` | **已回应**：Track-1/Track-2 独立 File Matrix/Phase/Acceptance + 「为何不拆对象」；用户已裁决合并。 |

「修复」项以外均有 `attempts.md` §一/§九/§十一/§十三/§十四可追溯；抽查未发现名义修复，未发现与代码相悖的落点。

---

## 八、§12 逐字对照复核（第三部，评审重点 5）

- 程序化逐字符比对（实开目标文件对应行 vs `plan.md` 引文）：
  - `refs/state-schema.md:40`（len 430=430）、`:42`（467=467）、`:60`（588=588）、`:454`（234=234）——**EXACT**；
  - `SKILL.md:453`（321=321，Markdown 表格行含 `|` 原样保留）、`:466`（143=143，含「不保证8/3/3」无空格）——**EXACT**；
  - `refs/orchestrator-guide.md:44-47` 四行——按「 / 」拼接逐字**EXACT**。
- **7/7 逐字**；`plan.md:683` 标题「逐字定位片段（无省略号）」与事实相符；A-S3 的 `git diff` 机械核验条件成立。

---

## 九、逐条 issue

> 以下均为精度/覆盖/文档同步问题，不改变机制结论、不构成执行障碍。编号 F-x，severity 标注，单选建议。

#### F1 — [internal-consistency · medium] §2 O1h 的「修正」列仍称立身用例「按事件 56 的授权文本重放」，与新 M5/§3 D1 步骤 6 直接矛盾

- **文件:行**：`plan.md:113`（§2 O1h「修正」列）对照 `plan.md:251`（§3 D1 步骤 6）、`:254`（结论注）。
- **原文**：`plan.md:113`「…| 立身用例按事件 56 的授权文本重放（见 §3 D1）|」；而 `plan.md:251`「**但事件 56 的 `user_quote` 只写「事件 55 / `PENDING` / `81a2537ea9eb`，不含 target UUID `cabcac00-…`」，故在新 M5 下 (a) 不满足，该历史操作不再可机械重放**…机械重放时须按新 M5 构造一条**同时**含 target UUID 与 `reservation_id`（或 `81a2537ea9eb`）的 `user-message` 授权事件」。
- **实核**：事件 56 的 `user_quote` 逐字实开确认仅含「事件 55 / reservation_id / PENDING / 81a2537ea9eb」，**确无 target UUID**；故二者不可同时为真。
- **影响**：属 candidate-7 落实 blind-4 Issue-1 时**未同步的残留旧表述**（candidate-2..6 的 M5 较宽时该句曾成立）。**不触碰机制、闭包、Acceptance 与实现路径**（权威推导在 §3 D1，已正确声明历史不可重放），也不构成对外部代码/仓库事实的失真（故不升级为阻断，见判定说明）。但作为治理计划的「最终认证」字节，内部自相矛盾应消除。
- **单选建议**：将 `plan.md:113` 的「修正」列改为「立身用例以**重建的前更正 fixture**（`original_value="PENDING"`）+ **按新 M5 构造的授权 `user-message`**（同时含 target UUID 与 `reservation_id`/`81a2537ea9eb`）重放；事件 56 现存 quote 文本本身不满足新 M5（见 §3 D1 步骤 6）」。

#### F2 — [anchor · low] §17 candidate-7 修订历史的行号锚点为 candidate-6 旧值（整体 +5 偏移）

- **文件:行**：`plan.md:795`。
- **原文（锚点片段）**：「…（`:220`/`:259`/`:262`/A1-17/§11 O1.15/§12 `:42`）…（`:293`/T1-F2）…（`:209`/§12 `:42`）」。
- **实核**（实开 `plan.md`）：`:220` = 规则 3（`correction-closure-violation`），非 M5 规则 8（应为 `:225`）；`:259` = 空行（内容绑定在 `:264`）；`:262` = 「授权绑定加固」标题（越权用例在 `:267`）；`:293` = 「`check` 不再因旧值失败」，record_correction 前置条件在 `:298`；`:209` = 空行（Issue-4 常量在 `:186-194`、M2 边界段在 `:214`）。偏移量均为 +5，系候选版本行号未随 candidate-7 插入 5 行而刷新。
- **影响**：仅 §17 过程元数据的自引用锚点；不影响机制/验收。属精度问题（与 round-4 R4-4、blind-4 观察-a 同类）。
- **单选建议**：将 `:220`→`:225`、`:259`→`:264`、`:262`→`:267`、`:293`→`:298`、`:209`→`:194`（或 `:214`）刷新为 candidate-7 值。

#### F3 — [coverage · low] blind-4 Issue-4 新并入的三条身份/拓扑邻接字段无专门的对抗/Acceptance 用例

- **文件:行**：`plan.md:186-194`（常量）、`:214`（M2 边界叙述）、`:646-665`（§11 O1 对抗清单）、`:546-548`（A1-12/13/14）。
- **实核**：A1-12/13/14 与 §11 O1.12/13/14 仅覆盖三个**出边结构引用**字段（`started_event_id`/`parent_event_id`/`invocation_event_id`）；Issue-4 新并入的 `invocation_id`（两型）/`invocation_kind`/`parent_instance_id` 无同名拒绝用例（仅 §11 O1.1 覆盖闭合身份字段、O1.2 覆盖未知字段，均不覆盖这些拓扑邻接字段）。
- **影响**：非机制缺陷（`allowed()` 已整体闭合），属对抗回归覆盖缺口。
- **单选建议**：新增 A1-22（或把 A1-7 扩为四例）：「合成更正 `invocation-started.invocation_kind`（或 `invocation_id`/`parent_instance_id`）→ `correction-field-not-allowed`」，并在 §11 O1 增一条；同时把 §3 D1 规则 4 括注与 §2 O1n 补上「+ Issue-4 身份/拓扑邻接字段」。

#### F4 — [contract · low] `find_orphan_reservations` 改走 `resolve_events` 与其文档化的「best-effort/lenient」契约未对齐

- **文件:行**：`plan.md:391`（T1-F1）对照 `model.py:697-702`（docstring：「Best effort and lenient by design … `validate_ledger` remains the sole strict authority」）、`:727`（现 `load_events` 直读）。
- **实核**：`resolve_events` 前置调用 `validate_corrections`（`plan.md:271`），对存在非法 correction 的对象会 fail-closed 抛 `ArchiveError`；而 `find_orphan_reservations` 现契约是「跳过 malformed ledger 行、不抛」。改走 `resolve_events` 会使该诊断命令在更正非法时抛错（行为变更），plan 未声明该语义。
- **影响**：不构成机制矛盾；`list-orphan-reservations` 属 operator aid，抛错可辩护。但应显式声明。
- **单选建议**：在 T1-F1/A1-21 补一句「`list-orphan-reservations` 在更正闭包非法时改为 fail-closed 抛出（与严格校验同源），不再是 best-effort 静默诊断」，或显式保留 lenient 包装（捕获 `correction-*` 后退回 raw 诊断并注明差异）。

#### F5 — [inheritance · low] round-4 的 R4-1..R4-6 未被 candidate-6/candidate-7 处置

- **文件:行**：`plan.md:212`（R4-1 证据字段理由段仍把 owner 锚定归给 `validate_locator`）、`:156`（R4-4 `scripts/README.md:164` 锚注）、`:317`（R4-3 `initialize_state :324-398`）、`:298`（R4-5 pending 构造未定义）、§8.2（R4-2 cap-only 无 Acceptance 行）。
- **实核**：`validate_locator`（`model.py:578-591`）只做 closed-union 形状校验、确不锚定 owner；`initialize_state` 定义确实在 `:274`，`:324-398` 为「既有 state」分支；§8.2 无 cap-only 行。
- **影响**：round-4 已判为非阻断建议；本对象未使用执行轮处理。按收敛必检清单应在 retrospective 记录采纳/拒绝/延后。
- **单选建议**：随实施一并落地（R4-1/3/4 文案、R4-2 补 cap-only 负例、R4-5 补 pending 构造与去重调用说明），或在 retrospective 显式记为延后。

#### F6 — [info · design-boundary] §12 `:42` 新文未重述 Issue-2 的「仅闭合事件流可用」前置

- **文件:行**：`plan.md:688`（§12 `:42` 新文）对照 `plan.md:298`（调用入口前置条件）。
- **观察**：§12 新文重述了 M5 内容绑定、Issue-4 结构集、blind-2 I-3 完整校验、M4 值谓词等，但未重述「`record_correction` 仅适用于已闭合事件流」。该前置是「完整图/账本校验」的必然推论，非独立契约条款。
- **影响**：不构成规范—机制分歧；实现期按 `plan.md:298` 执行即可。
- **单选建议（可选）**：无需改动；若求完备，可在 §12 `:42` 新文末尾加半句「（该完整校验要求事件流已闭合，未闭合对象不得调用 `record_correction`）」。

> **说明**：以上 1 条 medium + 4 条 low + 1 条 info 无一属于「对外部代码/仓库事实的失真」或「D3 穷举缺一」。§二/三/四/五/六/八已确认 Issue-1..4+O-0 逐条落地、R1 三条阻断闭合、D1 三项闭包自洽、D3 穷举完整、§12 逐字、机器块实跑通过，故不因这些内部同步/覆盖问题升级为阻断。

---

## 十、可执行性、治理合规与实施前前置条件

- **两 Track Phase bounded**：Track-1（T1-P1/P2/P3）、Track-2（T2-P1..P4）、Phase 0/6/7（`plan.md:501-525`）每步有产物与验证；未通过不进入下一步。
- **Acceptance 机械可判定**：§8 各行均可机械判定（A1-1/A-S1/A-S2 已按环境事实采用「非新增失败」口径，本机单文件基线 `4 failed/97 passed/2 skipped`、全量 `4 failed/476 passed/5 skipped/11 subtests`，与声明一致）；新增 A1-18/19/20/21、A2-13 判据明确。
- **第三部修改授权**：`review_mode: ultraverge` + `CONSTITUTION.md:91-96` 第四部程序成立；S-F3/S-F4/S-F5 显式不改（`plan.md:418-420`）；T1-F4/T2-F4/T2-F5/T2-F6 每处改动在 §12 有逐字对照，A-S3 可 `git diff` 机械核验。
- **治理自举合规**：机器块（`plan.md:728-774`）+ 用户授权 `user-message`（seq 9/10，实核为 `user-message`）+ 生成器 calibration 报告（2385 B / `c4755e…`，可复现）齐备；preflight 机械校验通过（`EXIT=0`）。
- **实施前必须满足的前置条件（阻断性）：无。**
- **建议随实施/收口一并修正（非阻断，不改变 verdict）**：
  1. F1：同步 `plan.md:113`（§2 O1h），消除与新 M5 的矛盾（单行修复）。
  2. F2：刷新 `plan.md:795` 的行号锚点为 candidate-7 值。
  3. F3：为 Issue-4 身份/拓扑邻接字段补对抗用例（A1-22 或扩 A1-7）。
  4. F4：显式声明 `list-orphan-reservations` 的 fail-closed 语义变更。
  5. F5：处置 round-4 R4-1..R4-6（采纳或 retrospective 记为延后）。
- **注意（流程）**：candidate-7 为 candidate-5 之后再次 material revision（blind-3/blind-4 两轮阻断修复）。按 `SKILL.md:462` 两-authority 同字节规则，本轮 outer 认证**只覆盖 candidate-7 当前字节**；进入实施前仍需对**同一最终字节**取得 fresh blank-slate 认证。若为消除 F1/F2 再改字节，则两份认证同时失效、须重跑。

---

## 十一、结尾

- **是否需拆分对象：否**。Track-1（O1）与 Track-2（O5）的代码路径、失败语义、回滚面不相交（唯一交点为 `state-schema.md` 两处不相邻章节 + 共享测试文件，§4/§12 已隔离）；本轮 1 条 medium 为文档同步、4 条 low 为覆盖/锚点/契约声明，1 条 info 为设计边界，均不涉及机制重设计。UV3-16 的拆分建议已由用户合并裁决与结构化 Track 回应。
- **无法核实 / 环境相关断言清单**：
  1. **r2 事件 55 曾存在的字面量 `PENDING` 字节**：该文件 `git log --follow` 仅一次提交 `529e691` 且内容已是 `81a2537ea9eb`；可证实事件 56 的 `user_quote` 含「PENDING … 81a2537ea9eb」，无法独立证实历史 `PENDING` 字节（与 `plan.md:113` 自述一致）。
  2. **A 对象「480 passed / 全绿」基线**：本机单文件/全量分别为 `4 failed/97 passed/2 skipped`、`4 failed/476 passed/5 skipped/11 subtests`，4 fail 全为 Windows 8.3 短路径（`ADMINI~1` vs `Administrator`），无法在本环境复现 480/全绿；计划已如实记录为环境等价结果（`plan.md:597`/§10 R8）。
  3. **实现后才可验证的行为**：`resolve_events`/`validate_corrections` 规则 1–10、`CORRECTION_EVIDENCE_FIELDS` 拒绝路径、I-3 写期完整有效视图门、M1 双期一致、M2 结构引用拒绝、M3 取代链、M5 内容绑定、Issue-2 闭合前置、Issue-3 孤儿同源、`_task_envelope_usable`、preflight 信封门、三处 init 第 4 行、adapter `--task-*`、A-S4（Phase 0 init 后 `plan.parent` 通过）——本轮只确认设计可行、落点/接口存在、红测可先失败。
  4. **「机械下界 = 4」**：源自 `ultraverge_min_reviewers(3) + 设计审查 1 = 4` 的机制推导，属可辩护下界论证，无法静态机械证明「最小派发」；r2 实测 23 我已独立复算属实。
  5. **calibration 报告 freshness 的实时性**：`_resolve_and_check_report:1655-1680` 仅比较 gov 块与报告内的 `freshness`，不重算活 HEAD/high-water；报告 `repository_head=13da6055` 与当前 HEAD 一致，但该「新鲜度」在代码语义上非实时校验（计划未声称相反，非计划缺陷）。
  6. **O-0 事故（原 blind-3 原件被覆盖）**：现 `blind-recheck-3.md` 内容在对 candidate-6 的盲审证据链上自洽（其 header SHA = candidate-6 `23bded6b…`，与 `plan.md` candidate-6 修订历史一致），但「原 blind-3 全文已不可恢复」一说无法独立核实（只能确认其结论已由 `record-verdict` 与 `attempts.md` 留痕）。
  7. **用户 2026-09-12 授权范围是否语义覆盖「O5 并入 B」**：`ab8896b1…`（seq 9）事件文本与 `_budget-state.json` 的 blind extension `user_quote` 涵盖 C→B 合并，属语义判断，非纯机械。
terminal_decision_event_id: fa03124b-9638-4c67-801c-fd6ef74a85cf
terminal_decision_value: 可执行
