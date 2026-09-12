阻断需修复

# 子计划 B · 终局计划 blank-slate 独立复核（第二权威盲审侧）

- 仓库：`C:\Users\Administrator\Documents\Github\converge-skill`（HEAD `13da6055f173ab1459f62cb36de11bb05b2b19cc`，`git status --porcelain` = `?? docs/plans/active/`）
- 受审对象：`.converge/active/20260911-op-envelope-b-contract-correction/plan.md`
- **实算 SHA-256**：`23bded6b038d3382c93f09316a8d2fa8f238250814a36f17e5f13129972782a4`（`sha256sum`，2026-09-12 本机实算）
- 复核方式：通读全文 + 实开核对 ≥28 处 `文件:行` 断言 + 实跑 `budget_gate.py preflight` + 实跑 pytest 基线 + 自数 O5 测试影响面
- **版本漂移（先声明）**：任务书写「candidate-5」，但实际字节 `plan.md:2` 自声明 `status: candidate-6`，`:4` 记录「candidate-5 → candidate-6（blind-3 Issue-1..4 与观察 a/b 逐条落地）」。本报告的一切结论只对**上述 SHA 的实际字节**负责。同目录已存在一份 `blind-recheck-3.md`（即产生 candidate-6 的那次评审），本次写入将覆盖它，而 `plan.md:788/790` 的修订历史仍逐条引用 `blind-recheck-3.md` 的 Issue-1..4——见观察 O-0，此为流程风险而非计划本体缺陷。

---

## 1. 抽查核对表（断言 → 实核结果）

> 全部为实开文件核对；`model.py` = `scripts/archive_contract/model.py`，`capture.py` = `scripts/archive_contract/capture.py`，`budget_gate.py` = `scripts/budget_gate.py`。

| # | 计划断言（位置） | 实核结果 |
|---|---|---|
| 1 | `EVENT_TYPES` 恰 6 类、无更正类型（§2 O1a，`model.py:21-24`） | ✅ `:21-24` 实为 `invocation-started/invocation-terminal/artifact-captured/terminal-decision/design-review-completion/user-message`，恰 6 类 |
| 2 | `COMMON_EVENT_FIELDS :178`、`EVENT_FIELDS :179-205`（§2 O1b） | ✅ 精确一致 |
| 3 | `validate_event` 定义 `:437`、terminal-decision 特化 `:445-455`、等集判定 `:456-458`（§2 O1c） | ✅ 精确一致 |
| 4 | `validate_event_graph :958-1037`（§2 O1d） | ✅ 函数体 :958–:1037 |
| 5 | `ledger-binding-missing :642-644`（§2 O1e） | ✅ :644 抛出；:642-643 为前置判定 |
| 6 | `cancelled+pre_execution=True` 可配 failed（§2 O1f，`:678-686`） | ✅ :679-682 扩集、:683-684 判定；`model.py:678-686` 成立 |
| 7 | `validate_archive` 以 raw 调 graph/ledger（§2 O1j，`:1178-1181`），`:1185-1188` 才 `project_manifest` | ✅ :1178 `load_events`、:1179 `validate_event_graph`、:1180 `_verify_evidence_bytes`、:1181 `validate_ledger`；:1185-1188 重投影 |
| 8 | `capture.py` 无 `__all__`；`archive_convergence.py` parser `:286-287`、dispatch `:360-362`（§2 O1k） | ✅ `capture.py` 无 `__all__`（仅 `__init__.py:5` 有）；`:286-287` = `record-user-message` parser；`:360-362` = 其 dispatch |
| 9 | `_prepare_terminal_decision :523-575`、`derive_decision_fields :509-520`、authority `:560`、quote 匹配 `:566-574`（§2 O1l / M1 / R2-7） | ✅ 函数体止于 :575；`validate_reviewer_verdict_authority(existing, values)` 精确在 :560；`source.user_quote != values.user_quote` 在 :571-574 |
| 10 | continue-parent 查找读 raw（§2 O1m，`capture.py:332-340`） | ✅ :332 `if invocation_kind=="continue"`、:333 `_read_existing`、:337 找 parent terminal |
| 11 | 三出边结构字段（§2 O1n）：`invocation-terminal.started_event_id` `:186`/校验 `:488`；`invocation-started.parent_event_id` `:182`/校验 `:481-486`；`design-review-completion.invocation_event_id` `:202`/校验 `:569` | ✅ 五处行号全部精确 |
| 12 | 四证据/定位字段（§2 O1o）：`prompt_evidence :183`/`:477`；`output_evidence :189`/`:520`；`source_locator :194`/`:537`；`snapshot :194`/`:538-547`；`validate_evidence_ref :313-332`、`validate_locator :578-591` | ✅ 全部精确；`validate_evidence_ref` 对形状合法 dict 只钉 path（:326-332），确不拒绝 |
| 13 | `validate_reviewer_verdict_authority :125-144`、`DECISION_REFERENCED` 的 `reviewer_event_id` `:137`、`verdict_output_ref` `:144`、`supersedes` `:1008`、`source_ref` `:1032`、`started_event_id` 解析 `:978`（§3/§2） | ✅ 六处精确 |
| 14 | artifact `sha256`/`size` 仅格式校验 `model.py:530-533`（blind-3 Issue-1） | ✅ `:530-531` 模式/hex、`:532-533` size |
| 15 | `_verify_evidence_bytes :1040-1054` 不绑定 `sha256/size` 与盘上 blob（blind-3 Issue-1） | ✅ :1043 只遍历 `prompt_evidence/output_evidence/snapshot`，不含 artifact `sha256/size` |
| 16 | `project_manifest :740`、`load_events :745`、graph `:746`、ledger `:747`、event_refs `:759-762`、投影循环 `:758-781`、final `:782-790`、`allowed_blobs :792-796`、degradations `:856-862`、ack `:884-893` | ✅ 全部成立（投影 `for event in events` 起于 :758） |
| 17 | `render_index_bytes :1194-1291` | ✅ 函数体 :1194–:1291 |
| 18 | O5 `TASK_TIERS :126-132`（small 4/8、medium 8/16、feature 16/24、critical 20/30、critical/ultraverge 别名） | ✅ `:126-131` 基表、`:132` 别名；数值精确 |
| 19 | opt-in `_task_envelope_configured :692-694`；`_task_envelope_initial :697-706`（`:705` 抛）；hard_cap `:709-718`；ceiling `:679-680`；reserve 调用 `:1137-1139` | ✅ 全部精确；`:705` 确为 `raise FailClosed("task_envelope_not_configured")` |
| 20 | `companion-reserve` 显式码 `:1314` | ✅ `cmd_companion_for`（:1298）内 :1314 `print("FAIL_CLOSED:task_envelope_not_configured")` |
| 21 | `read_state :247-263`、`_validate_state_shape :208-244`、`initialize_state` 既有态分支 `:324-398`、`needs_write :390-395`、`state_corrupt` `:253-256` | ✅ 全部成立：`_validate_state_shape` 只校验 `config/extensions/fsm`，**不校验顶层额外键**；`needs_write` 确只比 `config/fsm/extensions` |
| 22 | `_run :2077-2086`、`:2082` 打印 | ✅ `:2082 print("FAIL_CLOSED:{reason}")`、`:2085` 兜底 |
| 23 | 治理 preflight 结构 `:1730-1778`、fence `:1754-1762`、gov 判定 `:1762-1777`、`:1778` 调用 `cmd_preflight_governance :1718-1727`、`_validate_governance_change :1540-1652`、`_resolve_and_check_report :1655-1680`、`_numeric_empirical_conflicts :1683-1715` | ✅ 全部精确；`:1775` no_block、`:1776` duplicate/`:1777` print、CRLF 早返回 `:1767-1768`/`:1770-1771`、legacy `:1769` |
| 24 | parser `:2134-2139` 仅 `--plan`/`--governance` | ✅ 精确 |
| 25 | 三处 init 披露：`budget_gate.py:2012-2014`、`converge_loop.py:1093-1095`、`ocsr_spawn_adapter.py:400-402` | ✅ 三处均为三行打印（local ceilings / task-envelope / quality_path_guaranteed） |
| 26 | adapter CLI `:760-771`、`cmd_config_init` config `:378-386` | ✅ `:760-771` 为 `config-init` parser 全部选项；`:378-386` 为 config dict 逐项写入 |
| 27 | r2：3 条 `terminal-decision`（seq 17/45/54），`reviewer_event_id=verdict_output_ref` = 事件 14/42/53，链式 supersedes，三条均无 `source_ref` 键（§3 D1 步骤 3 / R1-1 / R2-5） | ✅ 实开 `evidence/events/` 逐条核对，完全一致；`DECISION_REFERENCED={14,42,53,17,45}`，事件 55 不在内 |
| 28 | 事件 55 `reservation_id=81a2537ea9eb`、role=design-reviewer；事件 56 user-message（`host_message_id=opencode-20260911-event55-correction`）；事件 57 terminal 以 `started_event_id` 引用 55（§2 O1h/§3） | ✅ 全部实核；事件 55/56 git 仅一次提交 `529e691`，仓库内确无法独立证实曾存在 `PENDING` 字节 |
| 29 | r2 单对象 gate-ledger 共 23 条 reserved（executor 5、ultraverge-initial 3、outer-reviewer 6、design-reviewer 5、blind-reviewer 4）（§2 O5l） | ✅ 脚本复算 23，分类逐一吻合 |
| 30 | r2 `check` valid（§13） | ✅ `{"diagnostics":[],"state":"valid","valid":true}`，exit 0 |
| 31 | §12 第三部「原文」为完整逐字行（R2-4 / blind-2 I-4）：`state-schema.md:40/42/60/454`、`SKILL.md:453/466` | ✅ 程序化逐字比对：quote_len == actual_len（430/467/588/234/321/143），**全部 EXACT MATCH**；`state-schema.md:60` 588=588 证实 |
| 32 | §12 `refs/orchestrator-guide.md:44-47` 四行逐字 | ✅ `:44`-`:47` 与计划引文逐字一致 |
| 33 | 受保护清单/程序 `CONSTITUTION.md:67-78`、`:91-96`；保护级别引用 `:68/:71/:72/:77/:67` | ✅ `:67-78` 为清单（SKILL :68、state-schema :71、orchestrator :72、reviewer-discipline :77、CONSTITUTION :67）；`:91-96` 为第四部程序 |
| 34 | `scripts/README.md :164` 治理 preflight 散文、`:174` 保留 `quality_path_guaranteed: false`（test_process_controller_contract :161 依赖） | ✅ `:164` 标题、`:174` 句子；`:161` 断言存在 |
| 35 | O6a 锚点 `SKILL.md:462`、`refs/orchestrator-guide.md:17-36`、`refs/state-schema.md:97-100`（失效句 :100、bootstrap 例外 :95） | ✅ 四处内容逐字吻合 |
| 36 | O5 测试影响面：`TestGovernancePreflight` 共 21 处 `self.preflight`，17 到达新门禁 / 4 早返回；`TestPreflight :265-279` 另有 2 处 legacy（§2 O5m/§6.2） | ✅ 独立 `grep` 得 21 处；逐用例分类得 17 到达（:1554/:1566/:1575/:1584/:1591/:1602/:1613/:1623/:1633/:1641/:1656/:1666/:1675/:1690/:1699/:1708/:1717）、4 早返回（:1682 duplicate、:1724 CRLF legacy、:1736 无块 legacy、:1743 `--governance` 无块）；`:272/:278` 两处 legacy |
| 37 | 测试锚点：`test_archive_convergence.py` 103 个 `def test_`、`:306/:408/:680`；`test_budget_gate.py` 类 `:265/:785/:1448`；`test_converge_loop.py:1003`；`test_ocsr_spawn_adapter.py:315`；`test_process_controller_contract.py:130/:199/:268` | ✅ 全部精确（103 计数一致） |
| 38 | A1-1 单文件基线 `4 failed/97 passed/2 skipped`；§8.4 全量 `4 failed/476 passed/5 skipped/11 subtests`（blind-2 I-1、R1-8、R2-2） | ✅ 本机实跑逐字复现两个数字；4 fail 均为 `test_archive_convergence.py` 的 `ADMINI~1`/`Administrator` 路径差异 |
| 39 | §15 机器块可过当前 preflight；calibration 报告 `sha256=c4755e…`、`corpus_digest=ff64a62b…`、4 个 `git:` archaeology 引用存在 | ✅ 实跑 `preflight --plan …/plan.md` → `PREFLIGHT_OK:governance-change` EXIT=0；报告文件 sha256 实测 `c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581`；4 个 commit 均在 `git log` |
| 40 | `user_message_events` = 对象事件 sequence 9/10（`ab8896b1…`/`06754e6f…`） | ✅ 对象 `evidence/events/00000009-ab8896b1….json`、`00000010-06754e6f….json` 精确对应（均 user-message） |
| 41 | 全仓无 `event-correction`/`correction` 事件类型；`disclosed_correction` 仅 drafts/引述（§2 O1g/N1） | ✅ `scripts/` 无 `event-correction`/`CORRECTION_`；`disclosed_correction` 仅 `docs/plans/active/…b….md:25` 与评审文本，非契约机制 |

**结论：41 项断言全部实核通过，未发现任何 `文件:行` 事实失真。**

---

## 2. 特别独立判断三项

### 2.1 O1 更正闭包与 `resolve_events` 有效视图在 `model.py` 真实校验链上是否成立

**成立（核心机制），但授权强度与写期门有两个未闭合缺口。**

- **注入点覆盖正确**：全仓对 `validate_event_graph`/`validate_ledger` 的直接调用只有 `model.py:746/747`（`project_manifest`）与 `:1179/:1181`（`validate_archive`）两处，`capture.py` 只在注释里出现。因此在两个校验器入口接 `resolve_events`，可无遗漏地覆盖 `archive`/`check`/`project_manifest` 三条路径，`validate_archive` 的 `:1178-1181` 确实无需改动。
- **立身用例在真实事件流上成立**：r2 三条 `terminal-decision` 的 `DECISION_REFERENCED={14,42,53,17,45}`，事件 55 不在集合；55 是 `invocation-started`，`reservation_id` 属值字段，`allowed()` 放行；改后 `reservation_id=81a2537ea9eb` 使 `model.py:642-644` 绑定通过。链式推导与计划一致。
- **闭包规则集自洽**：`history`/`structural ref`/`evidence` 三集互不重叠，`event-correction`/`terminal-decision` 整体闭合，`original_value` 比 effective 值（M3）在有取代链时仍可判定；`validate_events` 纯函数、禁二次施加的约束可避免 `correction-original-mismatch` 误报。
- **缺口 A（high，见 Issue-1）**：M5 的「quote 含 `corrected_event_id` **或** 本次 `reason` 子串」中，`reason` 是更正事件作者自由填写的字段（计划仅要求「非空有界字符串」）。因此只要 `reason` 取任意一条较早 user-message 里出现过的字符串（例如「继续」），内容绑定即被满足——这恰恰是计划自称被 M5 挡住的场景。该保证未兑现。
- **缺口 B（medium，见 Issue-2）**：写期 `record_correction` 对 `raw+[pending]` **直接跑完整 `validate_event_graph`/`validate_ledger`**，而 `validate_event_graph` 无条件要求所有 invocation 闭合（`:992-994`）、`validate_ledger` 要求所有 reservation 结清（`:642-644`、`:653`）。未完成对象上的合法更正会被 `invocation-open`/`ledger-*` 误拒。**本对象自身即为例证**：其事件流 seq 37 是 `invocation-started` 且无 terminal，此刻任何 `record_correction` 都必然 fail-closed。计划未声明「仅对已闭合事件流可用」这一前置条件。
- **缺口 C（low，见 Issue-3）**：`find_orphan_reservations`（`model.py:697-737`，读 raw）未纳入 File Matrix/有效视图；`reservation_id` 更正后 `list-orphan-reservations` 可报出与严格 `check` 不一致的幻影孤儿。
- **缺口 D（low，见 Issue-4）**：白名单仍放行 `invocation_id`/`invocation_kind`/`parent_instance_id` 等身份/拓扑邻接字段，与 M2「只保留值/载荷字段可更正」的叙述不完全一致（虽由图校验兜底，最终不会生成非法归档）。

### 2.2 O5 门禁在 `tests/test_budget_gate.py` 现有用例上的真实影响面（自数）

**计划的 17/4/2 计数准确，setUp 修法可行。**

- 自数：`self.preflight` 恰 **21** 处；门禁插入点定在 `:1777` 之后、`:1778`（`return cmd_preflight_governance`）之前，故只有「无 CRLF + malformed=0 + **恰好 1 个** gov 块」的调用到达。逐用例分类得 **17 到达 / 4 早返回**（`:1682` 双块、`:1724` CRLF legacy、`:1736` 无块 legacy、`:1743` `--governance` 无块）。
- `TestPreflight` `:272/:278` 两处无 gov 块 → legacy 早返回，不受影响。
- 全部 17 处到达用例的 plan 均写在 `self.dir`（`write_plan` 恒 `self.dir/name`；`test_locator_wrong_schema` 亦手写 `self.dir/plan.md`），故 `plan.parent == self.dir` 成立，`setUp` 在该目录 `init --task-tier critical` 即可全覆盖。
- 可行性：`initialize_state` 新建分支（`:400-416`）以空 ledger 调 `validate_integrity`，在干净临时目录执行 `init --task-tier critical` 可成功写 state；`_task_envelope_usable` 随后为真。
- 无 stdout 冲突：17 处到达用例全部只断言 `assertEqual(c,…)`/`assertIn(…)`，**无一处**对 `out` 做整段相等断言（唯一 `assertEqual(out,"CLEAN")` 的 `:1738` 属早返回用例）。门禁成功时静默即可。
- 结论：该影响面判断独立复核通过，未发现遗漏或误判。

### 2.3 机器块（§15/§16）能否通过 `budget_gate.py preflight` 当前代码的机械校验

**能过，已实跑。**

- 实跑：`python scripts/budget_gate.py preflight --plan .converge/active/20260911-op-envelope-b-contract-correction/plan.md` → 输出 `WARN:code_heavy:5,82` + `PREFLIGHT_OK:governance-change`，**EXIT=0**。
- 机械校验链逐环通过：`_validate_governance_change`（`numeric_changes` 全 `kind=mechanism`、`replacement` 型字段允许 null、`archaeology_refs` 4 个 `git:` 经 `:1591-1602` cat-file 存在性核验、`counterevidence_refs=[]`、`user_message_events` 两个 UUID）、`_resolve_and_check_report`（locator `attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration-op-b]` 恰命中一个、canonical sha 复算一致、corpus_digest/freshness 一致、eligible_samples=0 一致）、`_numeric_empirical_conflicts`（全 mechanism → 无论裁决）。
- 字节核对：独立文件 `evidence/calibration-report.json` 实测 sha256 = `c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581`，与 §15/§16 声明一致。
- 说明：该实跑只证明机器块对**当前**（candidate-6）字节有效；证据独立文件不被 preflight 机械校验（blind-2 I-7 已声明），raw body sha `9a08eb6e…` 的差异属 canonical 与 raw 之别，不影响判定。

---

## 3. 逐条 issue

### Issue-1 — [high] M5 授权内容绑定可被自由文本 `reason` 绕过，计划自称的防护未兑现
- 位置：`plan.md:220`、`plan.md:259`（M5 规则）；关联 `plan.md:262` 越权用例③、A1-17（`:546`）。
- 事实：`reason` 是更正事件作者可自由填写的非空字符串；规则为「`user_quote` 含 `corrected_event_id` **或** 含本次 `reason` 子串」。作者取 `reason="继续"` 并引用任意一条含「继续」的旧 user-message，即可通过 M5——正是计划文字「这防止任意一条较早、语义无关的 user-message（如「继续」「可以」）被引作授权凭据」所声称被阻止的场景。A1-17 只覆盖「既不含 id 也不含 reason 子串」，构造不出该绕过。
- 单选建议：**删除 `reason` 分支**——M5 改为「`user_quote` 必须含 `corrected_event_id` 的逐字子串，且（新增）含 `field` 名或其逐字 `corrected_value`」；同步修 `plan.md:220`、`:259`、`:682`（§12 state-schema:42 新文）、`§11 O1.15`、A1-17，并在立身链（`:235-249` 步骤 6）补齐 M5 实核（现 r2 事件 56 的 quote 只写「事件 55」、不含 UUID，重放必然依赖被删除的 `reason` 分支）。

### Issue-2 — [medium] `record_correction` 写期「完整有效视图校验」过宽，会误拒未闭合对象上的合法更正
- 位置：`plan.md:293`（调用入口）、`plan.md:548`（A1-19）、T1-F2（`:387`）。
- 事实：`validate_event_graph` 无条件拒绝未闭合 invocation（`model.py:992-994`），`validate_ledger` 无条件拒绝未结清 reservation（`model.py:642-644/:653`）。对象在实现/收敛过程中通常存在开放 invocation（本对象 seq 37 即无 terminal）、未结清预约；此时任何更正都会因 `invocation-open`/`ledger-*` 被拒，而非因该更正本身有问题。计划未写明 `record_correction` 仅可用于「事件流已闭合到可归档」的时点。
- 单选建议：**接受「仅归档前/已闭合事件流可用」并显式写入计划**——在 `:293` 与 T1-F2 增加前置条件「调用前事件流须已无未闭合 invocation / 未结清 reservation」，并在 A1-2/A1-19/A1-20 的合成 fixture 说明其为完整事件流；或改为只对 correction 目标域运行 `validate_reviewer_verdict_authority` + `derive_presented_degradations` 重算，再对「已完整」图才跑全局链。

### Issue-3 — [low] `find_orphan_reservations` 仍读 raw，更正后诊断与严格校验可能不一致
- 位置：计划未列；`model.py:697-737`（`:727` `load_events` 直读 raw），关联 §5 File Matrix T1-F1、§6.3 扫描步骤 1。
- 事实：若更正 `invocation-started.reservation_id`，严格 `check` 走有效视图通过，而 `list-orphan-reservations` 走 raw 会把真实预约报为孤儿，可能与 `archive --declare-orphan-reservation` 决策相互误导。
- 单选建议：在 T1-F1 明确 `find_orphan_reservations` 亦改走 `resolve_events`（或显式注明其为 raw 诊断、与严格校验的语义差异），并加一条回归。

### Issue-4 — [low] 白名单仍放行 `invocation_id`/`invocation_kind`/`parent_instance_id`，与 M2 叙述不完全一致
- 位置：`plan.md:184-202`（`allowed()` 定义）、`:209`（M2 叙述「只保留值/载荷字段可更正」）。
- 事实：这三个字段是身份/拓扑邻接字段，均不在 `CORRECTION_CLOSED_FIELDS`/`CORRECTION_STRUCTURAL_REF_FIELDS`/`CORRECTION_EVIDENCE_FIELDS` 中，`allowed()` 放行；更正通常会被 `validate_event_graph`（`:978` started↔terminal invocation_id 绑定、`:972` parent 语义）兜底拒绝，故不产生非法归档，但白名单面大于 M2 的措辞。
- 单选建议：把 `invocation_id`/`invocation_kind`/`parent_instance_id` 一并纳入闭合集（与 M2 结构引用集合并），或在 `:209` 明确其「可更正但受图校验兜底」的定位。

### 观察 O-0 — [process] 版本漂移与证据覆盖
- 位置：`plan.md:2`（`candidate-6`）、`:4`、`:788`/`:790`（引用 `blind-recheck-3.md` Issue-1..4）。
- 事实：任务书称 candidate-5，实际为 candidate-6；同路径已有一份产生 candidate-6 的 `blind-recheck-3.md`，本次覆盖后 `:788/790` 的引用将不再指向对应文本。此为编排层流程问题，不影响计划可执行性；建议编排层保留原评审副本或在修订历史注明本次复评的 SHA。

---

## 4. 第二权威结论

**否**——本计划事实准确性极高（41 项 `文件:行` 断言零失真）、机器块实跑通过、O5 影响面自数吻合，但 M5 授权内容绑定可被更正作者自由填写的 `reason` 绕过，计划自称的「授权强度不低于 user-decision」未兑现（Issue-1 high），且 `record_correction` 写期全图门在未闭合对象上会误拒合法更正（Issue-2 medium）；须先修复这两项再进入实施。
