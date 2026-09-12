---
round: 4
reviewer_backend: opencode
verdict: 可执行
reviewer_instance_id: 20260912_131340_e51b47
generated_at: 2026-09-12T05:19:01.610651+00:00
---

可执行

# round-4 · 子计划 B 完整收敛 outer 评议（candidate-5，blind-2 处置后重新认证）

- 受审对象（本轮实核字节）：`.converge/active/20260911-op-envelope-b-contract-correction/plan.md`（frontmatter `status: candidate-5`，**786 行 / 122,808 B / SHA-256 `f926f32cca66787140c091b60f61ad53537e15a0baedffb5ff2aad5047ec8f99`**）。
- 基线：HEAD `13da6055f173ab1459f62cb36de11bb05b2b19cc`；`git status --porcelain` = `?? docs/plans/active/`（与计划声明一致；`.converge/active/` 被 `.gitignore` 忽略）。
- 身份：fresh 独立 Reviewer（跨厂商，与 plan 作者、UV 初审、round-1/2/3、design-review、blind-1/2 均无共享上下文）；只读实核，除本报告外未修改任何文件；UTF-8。
- 判定：**可执行**。blind-2 I-1..I-7 逐条按单选修法落地（7/7）；R1-1/R1-2/R1-3 三条前轮阻断全部实质闭合；D1 三项闭包自洽且 I-2/I-3 未引入新矛盾；D3 穷举经独立重数完整且分类正确；§12 全部逐字；代码事实逐行实核无失真。发现 5 条 low 精度/覆盖问题 + 1 条 info 设计边界，均不构成事实失真、不构成穷举缺项，故不升级为阻断。

> **⚠ 简报与实物不一致（前置声明，非计划缺陷）**：本任务简报「受审对象」写为「candidate-3，83,818 B」，与工作树实际内容（candidate-5，122,808 B / `f926f32c…`）不一致；candidate-3 的 83,818 B / `e7690e76…` 记录仅见于 `attempts.md:13`/§八 与 `round-2.md:12`。标题「blind-2 处置后重新认证」、正文 §0.6/I-1..I-7 与 §17 修订历史均指向 candidate-5。**本轮以工作树实际 candidate-5 字节为唯一受审对象**。该不一致不影响判定。

> **本轮我实际复跑的自验（逐字留痕）**：
> - 机器块自验：`python scripts/budget_gate.py preflight --plan .converge/active/20260911-op-envelope-b-contract-correction/plan.md` → `WARN:code_heavy:5,80` / `PREFLIGHT_OK:governance-change` / `EXIT=0`，与 `attempts.md` §12.1 逐字一致。
> - calibration 生成器复现：`python scripts/distill_antipatterns.py --calibration --root . --output <TEMP>/calib_r4.json --id calibration-op-b --source-revision r1` → `EXIT=0`；与仓库内 `evidence/calibration-report.json` **逐字节一致**（2385 B，SHA-256 均为 `c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581`）。
> - 单文件测试基线（I-1 复核）：`python -m pytest tests/test_archive_convergence.py -q` → `4 failed, 97 passed, 2 skipped in 13.35s`。
> - 全量基线沿用 round-3/blind-2 在同一工作树的 `4 failed, 476 passed, 5 skipped, 11 subtests`（本轮未重跑全量，因其与本轮 I-1..I-7 无关联且已有两次独立复现）。
> - r2 事件流机械复算：57 条事件；`terminal-decision` 恰 3 条（seq 17/45/54）；`DECISION_REFERENCED` = {14,42,53,17,45} 不含事件 55；事件 55 `reservation_id=81a2537ea9eb`。
> - gate-ledger 复算：`reserved` 共 23 条（executor 5 / ultraverge-initial 3 / outer-reviewer 6 / design-reviewer 5 / blind-reviewer 4）。
> - A2-13 相关：`read_state` 对损坏 state 抛 `state_corrupt:*`（`budget_gate.py:253-256`）实核属实。

---

## 一、前置自检 5 问

1. **产物身份自洽 — 通过**。frontmatter `status: candidate-5`；Goal（§1）、Track 结构（§4）、File Matrix（§5）、Acceptance（§8）指向一致；O3/O6 显式降为处置记录（§13/§14）。§17 修订历史自述 candidate-5 = `blind-recheck-2.md` I-1..I-7，与正文 §0.6 及 §8 新增行一致。
2. **产物边界诚实 — 通过**。§3 D4 明确 record-only 且无「若裁决为实现则实施」分支；§9 Non-Goals 与之一致；数值披露诚实（真机械下界=4 / 典型估计≈10 标注非下界 / r2 实测 23 且如实写 `initial 20 < 23`，`plan.md:325`）。
3. **产物数据纯度 — 通过**。全篇为仓库真实路径、实核行号、既有常量；`numeric_changes` 两条全 `kind: mechanism`；无业务数据、无环境硬编码。
4. **职责边界自洽 — 通过**。D1 唯一语义读取点（`validate_event_graph`/`validate_ledger` 入口各自 resolve，`plan.md:265`）；M1 显式把 capture 写入期纳入同一 `resolve_events`（`plan.md:266-269`）；I-3 显式把 `record_correction` 落盘前纳入完整有效视图校验（`plan.md:291`）；D3 门禁/披露三处/adapter 写入点职责清晰。
5. **命名一致性 — 通过**。`plan.md:165` 命名锁定：事件 `event-correction`、manifest/INDEX 键 `corrections`、降级串前缀 `correction:`、常量 `CORRECTION_CLOSED_FIELDS` + `CORRECTION_STRUCTURAL_REF_FIELDS` + `CORRECTION_EVIDENCE_FIELDS`；D3 触发统一为「含唯一 `converge.governance-change/v1` 机器块」（`plan.md:301`）。

---

## 二、blind-2 I-1..I-7 逐条落地核对（yes/no + plan 原文行号 + 独立复核）

| # | blind-2 单选建议 | plan 落点（实核行号） | 落地 | 我的独立复核 |
|---|---|---|---|---|
| **I-1** (high) | A1-1 单文件基线改本机实测 `4 failed/97 passed/2 skipped`；全量数只留 A-S2 | `plan.md:527`（A1-1）、`:571`（A-S2）、`:588`（§8.4） | **YES** | 我实跑 `pytest tests/test_archive_convergence.py -q` = `4 failed, 97 passed, 2 skipped`，与 A1-1 逐字一致；`plan.md:527` 已删误挂的 476，`plan.md:571` 保留全量 476。 |
| **I-2** (high) | 取 (a)：新增 `CORRECTION_EVIDENCE_FIELDS={prompt_evidence,output_evidence,source_locator,snapshot}` 并入不可更正集，删「会被 `validate_event` 拒绝」 | `plan.md:165`（命名）、`:190-195`（常量定义）、`:196-201`（`allowed()`）、`:203`、`:205`（理由）、`:214`（规则 4）、`:251`（M4 删除面）、`:344`（ADR）、`:384`（T1-F1）、`:544`（A1-18）、`:602`（Non-Goal）、`:618`（R1）、`:654`（O1.17）、`:679`（§12 `:42`） | **YES** | 实开 `model.py:183`（`prompt_evidence`）、`:189`（`output_evidence`）、`:194`（`source_locator`/`snapshot`）；`allowed()` 的 `f not in CORRECTION_EVIDENCE_FIELDS` clause 在 `plan.md:199`。四字段名在 `EVENT_FIELDS` 中全局唯一，无跨类型误伤。全文已无「会被 `validate_event` 拒绝」的活表述（仅作被删对象的引述）。 |
| **I-3** (high) | `record_correction` prepare 钩子对 `raw + [pending]` 跑完整有效视图校验（`validate_event_graph` 含 authority + `validate_ledger`）；加 A1-19/A1-20 | `plan.md:291`（调用入口）、`:385`（T1-F2）、`:427`（G1）、`:500-501`（T1-P2/P3）、`:545-546`（A1-19/20）、`:618`（R1）、`:621`（R9）、`:655-656`（O1.18/19）、`:679`（§12 `:42`） | **YES** | 实开 `model.py:125-144`（`validate_reviewer_verdict_authority`）、`:1024`/`:1027`（graph 调用点）、`:1031-1036`（`user-decision-degradations` 重派生）、`:594`（`validate_ledger`）、`:1178-1181`（归档期同链）、`capture.py:198-213`（prepare 在锁内以 raw `existing` 调用）、`:523-575`（同哲学先例）。设计可行、落点行号属实。 |
| **I-4** (low) | §12 标题对 `state-schema.md:60` 改「完整逐字原行」 | `plan.md:674`（§12 前言） | **YES** | 实算 `state-schema.md:60` 长度 = 588 字符，与 `plan.md:674`「588=588，逐字相等，非前缀」逐字吻合。 |
| **I-5** (low) | 写死门禁直接 `read_state`→改 dict→`write_state`，绕过 `needs_write` | `plan.md:307`/`:310`（§3 D3）、`:394`（T2-F1）、`:478`（§6.2 更新方式）、`:625`（R13）、`:668`（O5.10）、`:681`（§12 `:454`） | **YES** | 实开 `initialize_state` 的 `needs_write`（`budget_gate.py:390-395`）确只比较 `config`/`fsm`/`extensions`；`write_state`（`:266-271`）直接覆写整 dict。plan 的绕过规定正确。 |
| **I-6** (low) | §8.2 增损坏 state 负例 A2-13；统一映射 `governance_requires_task_envelope` | `plan.md:305`（门禁行为 1）、`:394`（T2-F1）、`:401`（T2-F8）、`:478`（§6.2）、`:564`（A2-13）、`:626`（R14）、`:667`（O5.9）、`:681`（§12 `:454`） | **YES** | 实开 `read_state`（`budget_gate.py:247-263`）：JSONDecodeError/OSError → `state_corrupt:{e}`（`:253-254`）、非 dict → `state_corrupt:not_object`（`:255-256`）。plan 的「捕获任何异常统一映射」可实现。 |
| **I-7** (low) | §15/§16 限定 canonical 形式逐字节一致；注明独立文件不被 preflight 校验 | `plan.md:716`（§15 前言）、`:771`（§16 bullet） | **YES** | 实算 `attempts.md` fence raw body SHA = `9a08eb6e…`，canonical SHA = `c4755e…`（与独立文件相同）；preflight 只经 locator 读 fence，不校验独立文件。`plan.md:716`/`:771` 均已限定。 |

**统计：I-1..I-7 全部落地（7/7）**；无未选定分叉；无名义修复。

---

## 三、R1-1 / R1-2 / R1-3 闭合清单（逐条 yes/no + 独立复算证据）

### R1-1（阻断，事实失真：r2 terminal-decision 实数）— **YES，闭合**

- 独立实核（实开 r2 `.converge/done/20260910-process-controller-consolidation/evidence/events/`，57 事件）：
  - seq 17 `e4182ce3-…`：`reviewer_event_id`=`verdict_output_ref`=事件 14 `4952d7de-…`，`supersedes`=null，**无 `source_ref` 键**；
  - seq 45 `ea64c374-…`：=事件 42 `ef98b9ea-…`，`supersedes`=事件 17，**无 `source_ref` 键**；
  - seq 54 `777a0e2d-…`：=事件 53 `0aa365ab-…`，`supersedes`=事件 45，**无 `source_ref` 键**。
- 机械求值：`DECISION_REFERENCED` = {14,42,53}∪{17,45}∪{} = **{14,42,53,17,45}**；事件 55 `cabcac00-…` **不在集合内**。事件 57 `9254cf87-…`（`invocation-terminal`）以 `started_event_id` 引用事件 55，非 decision 引用边。
- `plan.md:233-247` 的推导链逐步可复算，步骤 3 的 5 个集合元素与我的实算逐项吻合。R1-1 闭合。

### R1-2（阻断，Acceptance 自相矛盾：A-S4 vs D3 门禁）— **YES，闭合**

- `plan.md:46` 明示 R1-2 的 `--active-dir` 处置已被 M6 取代；`plan.md:303-305` 取消 `--active-dir`、改以 `plan.parent` 读 state；`plan.md:573` A-S4 已改为无参命令 + 注明 Phase 0 在 `plan.parent` 配置；`plan.md:575-588` §8.4 逐条重审。
- **我独立重扫 §8 全部「命令 + 期望 exit 0」条目**：走 `preflight` 且期望 exit 0 的仅 **A2-1**（`plan.parent` 已配置）、**A2-4**（显式 opt-out + 持久写入）、**A-S4**（Phase 0 init 后 = `plan.parent` 已配置）三条；期望 exit 30 为 A2-3/A2-6/A2-11/A2-13；A1-1..A1-20 为 pytest/`archive_convergence check`；A2-7 legacy；A2-8/A2-9 输出形状；A2-10/A-S1/A-S2 pytest；A-S3 git diff。**未发现任何「实现后 exit 语义翻转」的遗留条目**；A2-2/A2-5 已显式删除（`plan.md:553`/`:556`）。
- A-S4 可实现性：对象 active 目录现 `_budget-state.json` 为 `config={}` 且 `defaults_version=2`，`cmd_init` 支持 `--task-tier` passthrough（`budget_gate.py:1995-1999`），Phase 0 `init --task-tier critical` 可达。R1-2 闭合。

### R1-3（阻断，治理自举：calibration 来源）— **YES，闭合**

- `refs/state-schema.md:95` 确为「bootstrap 例外（一次性）…后续治理变更必须由 `--calibration` 生成的报告提供」；`plan.md:716`/`:774` 显式声明**不使用**该例外。
- 独立文件 `evidence/calibration-report.json` 真实存在：2385 B / SHA-256 `c4755e…`；我用同一命令重新生成到临时路径 → **逐字节一致**（`identical True`），证明为生成器确定性输出而非手写。
- 报告字段逐字段实核：`schema=converge.calibration-report/v1`、`id=calibration-op-b`、`scope=done-corpus`、`corpus_digest=ff64a62b…`、`freshness={13da6055…, r1, 0}`、`quantitative_aggregates={eligible_samples:0,status:unavailable}`、`corpus` 19 条 `done:<slug>`——与 `plan.md:716`/§16 声明逐字一致。
- locator `attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration-op-b]`：`attempts.md ∈ _ROOT_ALLOWLIST`（实核）；preflight `EXIT=0` 即机械证明 canonical hash/digest/freshness 三者一致。R1-3 闭合。

---

## 四、I-2 / I-3 新矛盾排查（评审重点 2）

- **不可更正集合 vs 立身用例**：`CORRECTION_EVIDENCE_FIELDS` 只含四个证据/定位载体字段（`plan.md:190-195`），不含 `reservation_id`；`CORRECTION_STRUCTURAL_REF_FIELDS` 仍只含三结构引用字段（`plan.md:185-189`）。立身用例（事件 55 的 `reservation_id`）可更正不变。四字段名在 `EVENT_FIELDS` 中全局唯一（`model.py:183/189/194`），无跨事件类型误伤。**未引入矛盾**。
- **完整校验 vs 写期哲学**：I-3 的写期 `validate_event_graph`+`validate_ledger` 正是把归档期「注定 fail-closed 的更正不落盘」哲学延伸到 `record_correction`（`plan.md:291` 与 `capture.py:523-540` 同哲学）。补强而非冲突。**未引入矛盾**。
- **全文同步性**：`correction-chained` 仅出现在「被 M3 删除」的引述中（`plan.md:217`/`:348`/`:644`），8 个 active `correction-*` 码清单一致（`plan.md:427`）；`CORRECTION_EVIDENCE_FIELDS` 的同步点在 `plan.md:165/190/199/203/205/214/251/344/384/544/602/618/654/679` 全部到位。**未发现残留旧表述**。
- 补充观察（非矛盾）：I-3 使「user-decision 之后」「会改变 `presented_degradations` 重算」的值字段更正被写期拒绝；这不使归档 fail-closed（归档仍 valid，只是拒绝新更正），且仍可经「追加新 terminal-decision 取代旧 decision」在带内推进（详见 §九 R4-6）。

---

## 五、D1 三项闭合性复核（评审重点 3）

- **闭包规则自洽**：规则 1–5（`plan.md:211-215`）覆盖 target 缺失、序列、判定闭合、字段白名单、被 decision 直接引用闭合；`allowed()`（`:196-201`）= `EVENT_FIELDS[target_type]` − 闭合身份字段 − 证据字段集 − 结构引用集。规则 3 对 `{terminal-decision,event-correction}` 整体闭合；规则 5 以四条真实 decision 边（`model.py:137/144/1008/1032`）额外保护入边。三者叠加后仍保留 `{invocation-started, artifact-captured, design-review-completion}` 的可更正载荷字段，立身用例不被误伤。
- **有效视图单层施加自洽**：`resolve_events` 前置 raw（`plan.md:264`）；`validate_event_graph`（`model.py:958`）/`validate_ledger`（`:594`）入口各自 resolve；`project_manifest` 按 `raw_events`（`:746-747`/`:759-762` 字节哈希路径）与 `effective_events`（`:758-781` 投影、`:782-790` final、`:792-796` allowed_blobs、`:856-862` degradations）双列表划分（`plan.md:271-274`）；M1 将 capture 写入期纳入同源（`:266-269`）。`resolve_events` 纯函数、单次 apply 不变量明确。未发现二次施加路径。
- **授权时序自洽**：规则 8/9（`plan.md:218-219`）= exists ∧ `user-message` ∧ `user_quote` 内容绑定（M5）∧ `seq(corr)>seq(umsg)>seq(target)`；与立身用例（>56>55）及越权四例（`:260`）一致；规则 6（首条比 raw、后续比 effective）与规则 7（取代链）自洽。
- **结论：D1 三项闭合性仍自洽；candidate-5 的 I-2/I-3 改动未引入新矛盾。**

---

## 六、D3 穷举复核（独立重数）与 legacy 放行证明 + 数值依据

- `TestGovernancePreflight`（`tests/test_budget_gate.py:1448`）内 `self.preflight(` 实核 = **21** 处，行号 1554/1566/1575/1584/1591/1602/1613/1623/1633/1641/1656/1666/1675/1682/1690/1699/1708/1717/1724/1736/1743，与 `plan.md:439-459` 逐行一致。
- 我逐用例实开 `tests/test_budget_gate.py:1448-1744` 并按 `cmd_preflight`（`budget_gate.py:1730-1778`）控制流分类：
  - **17 处到达新门禁**：均为「恰好 1 个 gov 块」（`write_plan(gov, report)` 或含非 gov 的 extra fence）。特别核：`:1640` `extra_fences=[report]`（report 是 `converge.calibration-report/v1`，非 gov）→ 仍 1 个 gov 块；`:1651-1655` 手工构造的 wrong-schema 用例也是 1 个 gov 块。`write_plan` 恒写 `self.dir`（`:1534-1544`），`plan.parent == self.dir`。
  - **4 处早返回**：`:1682`（`:1681` `extra_fences=[gov]` → 2 个 gov 块，`:1776` 先返回）；`:1724`（`:1723` `crlf=True` 整文件 CRLF → `:1767-1768` 返回）；`:1736`（无 fence → `:1769` legacy 早返回，输出 `CLEAN`）；`:1743`（`--governance` 无块 → `:1775` 返回）。
  - 分类结论与 `plan.md` 完全一致，**无漏项**。
- **legacy 放行证明**：插入点位于 `:1777`（duplicate 检查）之后、`:1778`（`return cmd_preflight_governance`）之前；无 gov 块且无 `--governance` 时于 `:1769` 早返回，早于插入点。`TestPreflight`（`:265-279`）两处 `run("preflight", ...)`（`:272`/`:278`）均无 gov 块 → 不受影响。全仓 `scripts/**` 无 `preflight` 生产调用点，测试仅 `tests/test_budget_gate.py`（我 `grep` 实核）。
- **数值依据**：r2 `gate-ledger.jsonl` 实算 `reserved` = **23**（executor 5 / ultraverge-initial 3 / outer-reviewer 6 / design-reviewer 5 / blind-reviewer 4），与 `plan.md:325`/O5l 逐项相符；`cap 30` 余量 7、`feature cap 24` 余量 1、`initial 20 < 23` 均为真。

---

## 七、UV 三票处置抽查表（≥10 条；逐条回 plan 原文 + 代码实核）

统计核对：UV1 18（B1-B4 + N1-N14）+ UV2 16 + UV3 16 = **50** 条，与 `attempts.md` §一一致；处置 37 修复 / 10 因 S1 删除 / 3 因 S2 删除 / 0 其他。

| # | UV issue | 处置 | plan 落点实核 | 独立复核结论 |
|---|---|---|---|---|
| 1 | UV1 B1 / UV2 I2-5 / UV3-4（新门禁击穿既有 preflight） | 修复 | `plan.md:431-478`（§6.2 逐处）、`:561`（A2-10） | **真修复**。21 处调用、17/4 分类经我独立重数成立（§六），无漏项。 |
| 2 | UV2 I2-1（白名单与闭包互斥） | 修复 | `plan.md:196-207`、`:233-247` | **真修复**。动态白名单 = `EVENT_FIELDS[type] − CLOSED − EVIDENCE − STRUCTURAL`；事件 55 可更正；`DECISION_REFERENCED={14,42,53,17,45}` 实算成立。 |
| 3 | UV1 B3 / UV2 I2-7（有效视图未定界） | 修复 | `plan.md:262-276` | **真修复**。`validate_archive:1178-1181` 经 `validate_event_graph`/`validate_ledger` 入口 resolve 覆盖；`project_manifest` 双列表逐行号声明。 |
| 4 | UV1 N3（`FailClosed` 抛出点 :1139） | 修复 | `plan.md:127` | **真修复**：抛出点 **:705**（`_task_envelope_initial` 内），`:1137-1139` 为触发点；实开核属实。 |
| 5 | UV1 N2 / UV2 I2-12 / UV3-9（O6a 锚点） | 修复 | `plan.md:144` | **真修复**：`refs/state-schema.md:97-100`；失效句确在 `:100`，`:95-96` 为 bootstrap 例外。 |
| 6 | UV1 N5 / UV3-7（`started_event_id` 归属） | 修复 | `plan.md:222-231` | **真修复**：显式排除 `invocation-terminal.started_event_id`（`model.py:186`/解析 `:978`/`:140`），4 个 decision 字段行号实开属实。 |
| 7 | UV3-15（谓词 `_task_envelope_configured` ≠ 可用） | 修复 | `plan.md:312` | **真修复**：cap-only 过 `:692-694` 但 `:705` 抛 `task_envelope_not_configured`（实开核）；新增 `_task_envelope_usable`。 |
| 8 | UV3-14（无显式 opt-out） | 修复 | `plan.md:306-307`、`:555`、`:557` | **真修复**：`--allow-unconfigured-envelope <reason>` + `WARN` + 持久写入；空 reason 仍 exit 30。 |
| 9 | UV3-6 / R2-6（禁止批量无机械承载/归因） | 修复 | `plan.md:253`、`:645` | **真修复**：schema 层单字段闭集（`model.py:456-458` 等集）+ 值谓词（单 UUID/单字符串 ∈ allowed）。 |
| 10 | UV1 N6（`corrections` 须 omit-when-empty） | 修复 | `plan.md:281`、`:283` | **真修复**：manifest 键与 `render_index_bytes` 段均 omit-when-empty，沿用 `model.py:884-898` 惯例。 |
| 11 | UV1 N4 / UV2 I2-13（`__all__` 不存在） | 修复 | `plan.md:385` | **真修复**：实核 `grep __all__ scripts/archive_contract/capture.py` 无命中；T1-F2 已删该断言。 |
| 12 | UV2 I2-16 / UV3-13 / R1-4 / R2-4 / blind-2 I-4（§12 对照非逐字） | 修复 | `plan.md:674-684` | **真修复（逐字）**。7 行「原文」（`state-schema.md:40/:42/:60/:454`、`orchestrator-guide.md:44-47`、`SKILL.md:453/:466`）经我逐字符比对全部逐字命中，含 `:60`（588=588）与 SKILL 表格行。 |
| 13 | UV1 B4 / UV2 I2-6 / UV3-16（O6 实现分支无界） | 因 S2 删除 | `plan.md:330-338`、`:699-708` | **处置可追溯**：record-only 定案，删实现分支，给重启判据 4 条 + 主观项披露。 |
| 14 | UV1 B2/N12、UV2 I2-2/3/4/10、UV3-1/2/11/12（O3 bootstrap） | 因 S1 删除 | `plan.md:295-297`、`:690-695` | **处置可追溯**：D2 整体删除；§13 引 r2 `attempts.md:210` 逐字 + `check valid`。 |
| 15 | UV1 N8（本计划自身缺机器块/授权事件） | 修复 | `plan.md:712-765`、`:767-774` | **真修复**：机器块 + 生成报告载体；`ab8896b1…`（seq 9，`user-message`）、`06754e6f…`（seq 10，`user-message`）实核存在；4 个 `archaeology_refs` 经我 `git cat-file -e` 全部存在；preflight 复跑 `EXIT=0`。 |
| 16 | UV3-16（拆分建议） | 结构化回应 | `plan.md:361-371` | **已回应**：Track-1/Track-2 独立 File Matrix/Phase/Acceptance + 「为何不拆对象」；用户已裁决合并。 |

「修复」项以外的 S1/S2 删除项均可在 `attempts.md` §一追溯；抽查未发现名义修复，未发现与代码相悖的落点。

---

## 八、§12 逐字对照复核（第三部）

- 我用 UTF-8 逐字符比对（实开目标文件对应行）：
  - `refs/state-schema.md:40`、`:42`、`:60`（长度 588）、`:454`——全部逐字相等；
  - `refs/orchestrator-guide.md:44-47` 四行——逐字相等；
  - `SKILL.md:453`（Markdown 表格行，含 `|`，原样保留）、`:466`（含「不保证8/3/3」无空格）——逐字相等。
- `plan.md:674` 已按 I-4/R2-4 统一为「完整逐字原行（含首尾定位词）、无省略号」，与事实相符。
- **7/7 逐字**；A-S3 的 `git diff` 机械核验条件成立。

---

## 九、逐条 issue（全部非阻断；无事实失真、无 D3 穷举缺项）

> 以下均为精度/覆盖/设计边界问题，不改变机制结论、不构成执行障碍。编号 R4-x，severity 标注，单选建议。

#### R4-1 — [evidence-rationale · low] §3 D1 证据字段理由把「owner 锚定」错误归给 `validate_locator`

- **文件:行**：`plan.md:205`（`CORRECTION_EVIDENCE_FIELDS` 理由段）；同段 `:119`（O1o）。
- **原文**：「`validate_evidence_ref`（`model.py:313-332`）把 path 钉死为 `evidence/invocations/{owner_id}/{owner_kind}.bin`，`validate_locator`（`:578-591`）与 snapshot 校验（`:538-547`）把定位锚定到 owner」。
- **实核**：`validate_evidence_ref`（`model.py:318-332`）确把 evidence path 钉死；snapshot 校验（`:543-547`）把 snapshot path 钉死为 `evidence/artifacts/{artifact_id}/snapshot`。但 `validate_locator`（`:578-591`）只校验 `source_locator` 的 closed-union 形状（`workspace-relative{kind,workspace_id,path}` / `external{…}`），**并不把 `source_locator` 锚定到 owner**。
- **影响**：不影响任何机制/落点/Acceptance——`source_locator` 的不可更正性由 `allowed()`（`plan.md:199`）按字段名整闭，与该理由句无关；`source_locator` 作为「定位载体」不应被更正的结论仍成立。属理由段的局部过度归因。
- **单选建议**：将该句改为「`validate_evidence_ref` 钉死 prompt/output 证据 path，snapshot 校验钉死 snapshot path；`source_locator` 由 `validate_locator` 作 closed-union 形状校验——四者均为已冻结证据/定位载体，故整体不可更正」。

#### R4-2 — [coverage · low] cap-only state 仍无 §8 Acceptance 行（round-3 R3-2 遗留）

- **文件:行**：`plan.md:312`（§3 D3 修正：cap-only → initial 抛，故不可用）对照 `plan.md:554`（A2-3 仅「无 `_budget-state.json`」）、`:564`（新增 A2-13 仅「损坏 state」）、`:401`（T2-F8 负例清单）。
- **实核**：`_validate_state_shape:236-237` 与 `initialize_state:312-314` 允许仅配 `task_envelope_cap`；此时 `_task_envelope_configured:692-694` 为真而 `_task_envelope_initial:705` 抛——正是 UV3-15 修复核心，但仍无机械 Acceptance 覆盖，T2-F8 负例清单亦未含。
- **影响**：非事实失真、非 D3 的 21 处穷举缺项；`_task_envelope_usable` 的正确性（cap-only → fail-closed）无 §8 直接门。
- **单选建议**：把 A2-3 扩为两条（或新增一行 A2-14）：「`plan.parent/_budget-state.json` 存在但仅 `task_envelope_cap`、无 `task_tier`、无 opt-out → `FAIL_CLOSED:governance_requires_task_envelope`，exit 30」；T2-F8 负例清单同步。

#### R4-3 — [precision · low] `initialize_state` 行号范围与 I-3「同源完整检查链」的枚举不全

- **文件:行**：`plan.md:310`（「`initialize_state`（`:324-398`）」）、`:291`（「即归档期 `validate_archive`（`:1178-1181`）同源的完整检查链」）。
- **实核**：`initialize_state` 定义在 `budget_gate.py:274`，`:324-398` 只是「已有 state」分支；`validate_archive:1178-1181` 实为 `load_events`+`validate_event_graph`+`_verify_evidence_bytes`+`validate_ledger`，而 I-3 枚举只列 graph+ledger（缺 `_verify_evidence_bytes`）。
- **影响**：无机制影响——「现有 state 分支」与「归档期检查链」的语义指向明确；且 I-2 已把证据字段整体闭合，`_verify_evidence_bytes` 结果不受更正影响，省略它无实际缺口。
- **单选建议**：把 `:324-398` 注为「既有 state 分支」；把 I-3 的「同源完整检查链」改为「与 `:1179`/`:1181` 同源（`_verify_evidence_bytes` 因 I-2 证据字段不可更正而无需重跑）」。

#### R4-4 — [anchor · low] §2.4 仍把 `scripts/README.md:164` 标为「治理 preflight 模式散文」（round-3 R3-1 遗留）

- **文件:行**：`plan.md:155`（§2.4 表末行）对照 `scripts/README.md:164`/`:166`。
- **实核**：`:164` = `### 治理 preflight 模式`（标题），散文实体在 `:166`。`plan.md:400`（T2-F7）已给 `:164-166` 区间，故 F7 落位不受影响。
- **影响**：仅 §2.4 行内锚注偏指；无机制影响。
- **单选建议**：§2.4 该格改为「`:164-166` 治理 preflight 模式节（标题 :164 / 散文 :166）」。

#### R4-5 — [implementation-clarity · low] I-3 的 `raw + [pending]` 中 pending 的构造未定义，且 `validate_corrections` 双重调用

- **文件:行**：`plan.md:291`、`:264`。
- **实核**：`_commit_event.prepare(fields, existing)` 在锁内被调用时（`capture.py:210-213`），`fields` 尚无 `sequence`/`event_id`（二者在 `:215-216` 才赋值）；而 `resolve_events`/`validate_event_graph` 需要完整事件（含 `sequence`）才能按序应用与建图。另 `resolve_events` 自身已先调 `validate_corrections`（`plan.md:264`），I-3 又显式先调一次，属冗余但无害。
- **影响**：不构成机制矛盾；实现者需自行决定为 pending 合成 `sequence=len(existing)+1` 与临时 `event_id`。若不点明，可能出现「校验用的 pending 与最终落盘事件 id 不同」的细微差异（对图校验无影响）。
- **单选建议**：在 `plan.md:291` 补一句「prepare 内以 `sequence=len(existing)+1` 与临时 `event_id` 构造 pending 事件参与校验；`resolve_events` 已内含 `validate_corrections`，无需重复调用」。

#### R4-6 — [design-boundary · info] I-3 使「decision 后、影响 degradations 的更正」被拒，M3 的「回退更正」对此类字段不再直接可用（round-3 R3-4 的强化版）

- **文件:行**：`plan.md:291`/`:546`（A1-20）、`:217`（M3 取代链）。
- **观察**：`invocation-terminal.evidence_level`/`artifact-captured.reproduction_capability` 是 `derive_presented_degradations`（`model.py:915-921`）的输入。若某 `user-decision` 已存在，则任何会改变这两个字段、进而改变 `derive_presented_degradations(prior)` 的更正，都会被 I-3 写期拒（A1-20）。因此 M3「对同一 `(target,field)` 追加回退更正」在这些字段上、在 decision 之后**不再可行**（该回退同样会被拒）。
- **严重性说明（为何不升为阻断）**：这不产生永久 fail-closed 归档——归档在旧决策下仍 valid，只是拒绝新更正；且仍存在带内推进路径（追加一条 `terminal-decision` 取代旧 decision，按新 effective 视图重派生 `presented_degradations`）。这是「决策陈述不得被事后静默改写」的正确 fail-closed 取向。
- **单选建议（可选）**：在 §3 D1「有效视图」或 §10 R9 增一句边界声明：「decision 派生字段（`presented_degradations`）的依赖事件若在 decision 之后被更正（含回退更正），写期即 `user-decision-degradations`；如需变更，须追加新 decision 取代旧 decision」；可将 A1-20 扩为「后于 decision + 尝试回退亦被拒」以固化。

> **说明**：以上 5 条 low + 1 条 info 无一属于「事实失真」或「穷举缺一」。§二/三/四/五/六/八 已确认 I-1..I-7 逐条落地、R1 三条阻断闭合、D1 三项闭包自洽、D3 穷举完整、§12 逐字，故不因这些精度问题升级为阻断。

---

## 十、可执行性、治理合规与实施前前置条件

- **两 Track Phase bounded**：Track-1（T1-P1/P2/P3）、Track-2（T2-P1..P4）、Phase 0/6/7（`plan.md:493-517`）每步有产物与验证；未通过不进入下一步。
- **Acceptance 机械可判定**：§8 各行均可机械判定（A1-1/A-S1/A-S2 已按环境事实采用「非新增失败」口径，本机单文件基线 `4 failed/97 passed/2 skipped`、全量 `4 failed/476 passed/5 skipped/11 subtests`，与声明一致）；新增 A1-18/19/20、A2-13 判据明确。
- **第三部修改授权**：`review_mode: ultraverge` + `CONSTITUTION.md:91-96` 第四部程序成立；S-F3/S-F4/S-F5 显式不改（`plan.md:411-413`）；T1-F4/T2-F4/T2-F5/T2-F6 每处改动在 §12 有逐字对照，A-S3 可 `git diff` 机械核验。
- **治理自举合规**：机器块（`plan.md:719-765`）+ 用户授权 `user-message`（seq 9/10，实核为 `user-message`）+ 生成器 calibration 报告（逐字节可复现）齐备；preflight 机械校验通过（`EXIT=0`）。
- **前置自检**：本对象 `plan.parent` 已有 `_budget-state.json`（`config={}`），Phase 0 `init --task-tier critical` 可达（`cmd_init` 支持 `--task-tier` passthrough）。
- **实施前必须满足的前置条件（阻断性）：无。**
- **建议随实施一并落地（非阻断，可并入对应 Phase 以消除执行歧义）**：
  1. R4-1：修正 §3 D1 证据字段理由段的 `validate_locator` 归因（`plan.md:205`/`:119`）。
  2. R4-2：补 cap-only 门禁 Acceptance 行并同步 T2-F8 负例清单。
  3. R4-3：收紧 `initialize_state` 行号范围与 I-3「同源」枚举表述。
  4. R4-4：修正 §2.4 的 `scripts/README.md` 锚注为 `:164-166`。
  5. R4-5：补 pending 事件构造与去重调用说明（`plan.md:291`）。
  6. R4-6：补「decision 派生字段后更正」边界声明（可选）。

---

## 十一、结尾

- **是否需拆分对象：否**。Track-1（O1）与 Track-2（O5）的代码路径、失败语义、回滚面不相交（唯一交点为 `state-schema.md` 两处不相邻章节 + 共享测试文件，§4/§12 已隔离）；本轮 5 条 low 为理由措辞/覆盖度/锚注，1 条 info 为设计边界声明，均不涉及机制重设计。UV3-16 的拆分建议已由用户合并裁决与结构化 Track 回应。
- **无法核实 / 环境相关断言清单**：
  1. **r2 事件 55 曾存在的字面量 `PENDING` 字节**：该文件 `git log --follow` 仅一次提交 `529e691` 且内容已是 `81a2537ea9eb`；可证实事件 56 的 `user_quote` 含「PENDING … 81a2537ea9eb」，无法独立证实历史 `PENDING` 字节（与 `plan.md:243` 自述一致）。
  2. **A 对象「480 passed / 全绿」基线**：本机单文件/全量分别为 `4 failed/97 passed/2 skipped`、`4 failed/476 passed/5 skipped/11 subtests`，4 fail 全为 Windows 8.3 短路径（`ADMINI~1` vs `Administrator`），无法在本环境复现 480/全绿；计划已如实记录为环境等价结果（`plan.md:588`/§10 R8）。
  3. **实现后才可验证的行为**：`resolve_events`/`validate_corrections` 规则 1–10、`CORRECTION_EVIDENCE_FIELDS` 拒绝路径、I-3 写期完整有效视图门、M1 双期一致、M2 三条结构引用拒绝、M3 取代链、M5 内容绑定、`_task_envelope_usable`、preflight 信封门、三处 init 第 4 行、adapter `--task-*`——本轮只确认设计可行、落点/接口存在、红测可先失败。
  4. **「机械下界 = 4」**：源自 `ultraverge_min_reviewers(3) + 设计审查 1 = 4` 的机制推导，属可辩护下界论证，无法静态机械证明「最小派发」；r2 实测 23 我已独立复算属实。
  5. **calibration 报告 freshness 的实时性**：`_resolve_and_check_report:1655-1680` 仅比较 gov 块与报告内的 `freshness`，不重算活 HEAD/high-water；报告 `repository_head=13da6055` 与当前 HEAD 一致，但该「新鲜度」在代码语义上非实时校验（计划未声称相反，非计划缺陷）。
  6. **用户 2026-09-12 授权范围是否语义覆盖「O5 并入 B」**：`ab8896b1…`（seq 9）事件文本涵盖 C→B 合并，属语义判断，非纯机械。
  7. **本任务简报「受审对象」文本**：简报写 candidate-3/83,818 B，与工作树实际 candidate-5/122,808 B 不一致；已按实际字节评审，无法核实简报该行的来源。
