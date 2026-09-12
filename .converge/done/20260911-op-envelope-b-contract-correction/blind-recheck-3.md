阻断需修复

# blind-recheck-3 · 终局计划 blank-slate 独立复核（第二权威盲审侧）

- 受审对象：`.converge/active/20260911-op-envelope-b-contract-correction/plan.md`（candidate-5，冻结字节）
- 复核角色：fresh 独立 Reviewer（未参与此前任何评审；写作时未读 `round-*.md`/`uv-init-*.md`/`attempts.md`/`design-review.md`/`blind-recheck-1/2.md`）
- 复核日期：2026-09-12；工作树 HEAD `13da6055f173ab1459f62cb36de11bb05b2b19cc`
- 字节数：122808 bytes；行数：786

## 0. SHA-256 实算（字节核对）

```
sha256(plan.md) = f926f32cca66787140c091b60f61ad53537e15a0baedffb5ff2aad5047ec8f99
```

`certutil -hashfile` 与 `python hashlib.sha256` 两次独立计算一致；同一字节。本报告即对该字节负责。

---

## 1. 抽查核对表（≥12 条：断言 → 实核结果）

全部为 2026-09-12 亲自打开工作树核对，非转述。

| # | 计划断言（文件:行） | 实核结果 |
|---|---|---|
| V1 | `EVENT_TYPES` 恰 6 类，无更正类型（`model.py:21-24`） | ✅ 实开命中：`invocation-started/invocation-terminal/artifact-captured/terminal-decision/design-review-completion/user-message` |
| V2 | `COMMON_EVENT_FIELDS :178`、`EVENT_FIELDS :179-205`（`model.py`） | ✅ 精确命中；六类字段集逐一对应 |
| V3 | `validate_event` 定义 `:437`、terminal-decision 二次特化 `:445-455`、等集判定 `:456-458` | ✅ 逐行命中：`:456 set(event) != set(expected_fields)`、`:457` extra/missing |
| V4 | event graph 校验 `model.py:958-1037` | ✅ `def validate_event_graph` 在 958，`return sorted(graph_degradations)` 在 1037 |
| V5 | ledger 配对 `ledger-binding-missing :642-644`；status 配对 `:678-686`（含 :679-682 pre_execution） | ✅ 逐行命中，含 `cancelled + pre_execution=True` 并 failed 的并集分支 |
| V6 | `validate_archive` 以 raw events 调 graph/ledger：`:1178-1181` | ✅ `:1178 load_events` → `:1179 validate_event_graph` → `:1180 _verify_evidence_bytes` → `:1181 validate_ledger`；`:1185-1188` 才重投影 |
| V7 | 结构引用锚点：`invocation-terminal.started_event_id` `:186`/校验 `:488`；`invocation-started.parent_event_id` `:182`/校验 `:481-486`；`design-review-completion.invocation_event_id` `:202`/校验 `:569` | ✅ 全部逐行命中 |
| V8 | 证据字段锚点：`prompt_evidence :183/:477`、`output_evidence :189/:520`、`source_locator :194/:537`、`snapshot :194/:538-547`；`validate_evidence_ref :313-332` | ✅ 全部逐行命中；确认 `validate_event` 对形状合法证据 dict 只钉 path/格式，不做盘上字节比对 |
| V9 | `capture.py` 写入期判定 `_prepare_terminal_decision :523-575`、`:560` authority、`:566-574` quote 逐字匹配；`derive_decision_fields :509-520` | ✅ 逐行命中（def 523，body 至 575；quote 比对在 571-574） |
| V10 | continue-parent 查找读 raw：`capture.py:332-340` | ✅ `begin_invocation` 分支 `:332`，`_read_existing`→找 parent started/terminal 至 `:340` |
| V11 | `capture.py` 无 `__all__`（仅 `archive_contract/__init__.py:5` 有） | ✅ grep 命中 `__init__.py:5`，capture.py 零命中 |
| V12 | `archive_convergence.py` record-user-message parser `:286-287`、main dispatch `:360-362` | ✅ parser 在 `:286`、dispatch 在 `:360`（计划用“近”表述，成立） |
| V13 | `TASK_TIERS` `budget_gate.py:126-132`（small/medium/feature/critical + `critical/ultraverge` 别名） | ✅ 4/8、8/16、16/24、20/30，别名指向 critical |
| V14 | `_task_envelope_configured :692-694`；`_task_envelope_initial :697-706`（`raise` 在 `:705`）；`_task_envelope_hard_cap :709-718` | ✅ 逐行命中；仅 cap 时 initial 在 705 抛，计划 UV3-15 成立 |
| V15 | `read_state :247-263` 对缺失 state 返回空 config 不抛；`_validate_state_shape :208-244` 不拒额外顶层键；`initialize_state` 的 `needs_write :390-395` 只比 config/fsm/extensions | ✅ 逐行命中——O5n/I-5 前提为真：额外顶层键会因 needs_write 漏写 |
| V16 | preflight parser 仅 `--plan/--governance :2134-2139`；`cmd_preflight :1730-1778`；早返回 `1769/1770-1771/1775`；`duplicate_governance_block` 判定在 `:1776`（print 在 `:1777`） | ✅ 全部命中；插入点“1777 之后、1778 之前”即 governance handler 前一行，成立 |
| V17 | 治理 preflight 结构：`_validate_governance_change :1540-1652`、`_resolve_and_check_report :1655-1680`（canonical hash 复算 1661-1663）、`_numeric_empirical_conflicts :1683-1715` | ✅ 逐行命中；确认 sha256/corpus_digest/freshness 为机械复算，非形式声明 |
| V18 | 三处 init 披露 `budget_gate.py:2012-2014`、`converge_loop.py:1093-1095`、`ocsr_spawn_adapter.py:400-402` | ✅ 三处均为 `[init] local ceilings / task-envelope / quality_path_guaranteed` 三行；adapter CLI 在 `:760-771`、写入点 `:378-386` |
| V19 | `TestGovernancePreflight :1448`、helper `:1546-1547`、`self.preflight` 共 21 处、`TestPreflight :265-279`（2 处） | ✅ 严格计数：类体 1448-1744，`self.preflight(` 恰 21 处（逐行已列）；TestPreflight 调用在 272/278 |
| V20 | `tests/test_archive_convergence.py` 全文件 `def test_*` = 103；锚点 306/408/680 | ✅ grep 计数 103；三锚点逐条命中 |
| V21 | 其余测试锚点 `test_converge_loop.py:1003`、`test_ocsr_spawn_adapter.py:315`、`test_process_controller_contract.py:130/199/268` | ✅ 全部精确命中；`README.md:164` 治理 preflight 段、`:174` `quality_path_guaranteed: false` 命中，且 test_process_contract :161 断言该串 |
| V22 | r2 实含 **3** 条 terminal-decision（seq 17/45/54），立身 target 事件 55 不在 `DECISION_REFERENCED` | ✅ 实开：17→14、45→42（supersedes 17）、54→53（supersedes 45），三条均无 `source_ref` 键；无 user-decision；事件 55 `cabcac00…` 为 invocation-started；事件 57 `9254cf87…` 以 `started_event_id` 引用 55（非 decision 边） |
| V23 | r2 单对象 gate-ledger reserved 共 23（executor 5/ultraverge-initial 3/outer-reviewer 6/design-reviewer 5/blind-reviewer 4） | ✅ 实测 23；`target_role` 分布 5/3/6/5/4 完全一致 |
| V24 | §12 第三部「原文」逐字定位片段 | ✅ 6 组全部在源文件中逐字命中并出现在 plan.md：`state-schema.md:40/42/60/454`；`orchestrator-guide.md:44-47` 四行；`SKILL.md:453/466`。`:60` 行长度实测 **588 = 588**，与计划“完整逐字原行”声明一致 |
| V25 | 第三部受保护清单/程序 `CONSTITUTION.md:67-78`、`:91-96` | ✅ `:67 CONSTITUTION`、`:68 SKILL`、`:71 state-schema`、`:72 orchestrator-guide`、`:77 reviewer-discipline`；第四部程序 `:91-96` 命中 |
| V26 | 测试基线：单文件 `4 failed/97 passed/2 skipped`；全量 `4 failed/476 passed/5 skipped/11 subtests`；4 fail 为 Windows 8.3 短路径 | ✅ 实跑两次复现完全相同数字；4 个失败均为 `ADMINI~1` vs `Administrator` 路径断言 |
| V27 | 事件 55 现值为更正后字节、仓库无法独立证实曾存在的 `PENDING`；O1h 已如实披露 | ✅ 事件 55 现值 `81a2537ea9eb`；事件 56 `user_quote` 授权文本存在；git 该文件仅一次提交 |
| V28 | HEAD/工作树：HEAD `13da605`、仅 `?? docs/plans/active/`（4 个文档） | ✅ `git rev-parse HEAD` 与 `git status --porcelain` 实核一致，目录内 4 文件 |

**事实准确性小结**：28 组、>60 个 `文件:行` 断言全部实核成立，未发现失真。R1-1（3 条 decision）、I-1（单文件基线）、I-4（588 行）、O5m（21/17/4）等关键数字均经独立复算吻合。

---

## 2. 独立判断三项

### 2.1 O1 更正事件的闭包规则 + `resolve_events` 有效视图在 `model.py` 真实校验链上是否成立

**结论：主体成立，但白名单存在一处未闭合的静默缺口（见 Issue-1）。**

成立之处（逐一在真实链上验证）：

- `validate_event_graph :958` 与 `validate_ledger :594` 确为语义读取上游：所有图结构/账本绑定都从传入 `events` 派生，且入口无其它缓存。计划把 `resolve_events` 放在这两个函数入口，能覆盖 `validate_event_graph` 内 `reviewer_event_id`（:137）、`source_ref`（:1032）、`presented_degradations`（:1035）与 `validate_ledger` 的 `by_reservation`（:639）全部语义点。
- `validate_archive :1178-1181` 的顺序（load→graph→evidence→ledger）确实使 “不直接读事件字段” 的说法成立：`:1180 _verify_evidence_bytes` 只读 `prompt_evidence/output_evidence/snapshot`，而这三者恰被计划设为不可更正，raw==effective，故无需改动。
- 立身用例（事件 55 `reservation_id`）在真实 chain 上闭合：事件 55 不被 3 条 decision 的任何引用字段命中；M2 结构集只闭合目标**自身**的出边字段（55 的 `reservation_id` 是值字段），故可更正；`validate_ledger :642-644` 会按 effective 的 `81a2537ea9eb` 通过。
- I-3 的写期完整有效视图校验在真实链上确有拦截力：A1-19（reviewer started.role）会触发 `validate_reviewer_verdict_authority :142`；A1-20（user-decision 前 evidence_level）会触发 `:1035 derive_presented_degradations` 失配。两者都在 `record_correction` 落盘前可判。
- M3 取代链、M5 内容绑定、M2 三条结构拒绝、`load_events :413` 仍只校验 raw 且 correction 事件走新分支——均与现链自洽。

**缺口（阻断点）**：`CORRECTION_EVIDENCE_FIELDS`（plan.md:190-195）只列 `prompt_evidence/output_evidence/source_locator/snapshot`，遗漏了同为“已冻结证据身份载体”的 `artifact-captured.sha256` 与 `artifact-captured.size`。实测证据链：

- `model.py:194` 中 `artifact-captured` 顶层含 `sha256/size`；
- `validate_event :530-533` 对二者只做“HEX64/非负整数”格式校验，**不与任何盘上 blob 比对**；
- `_verify_evidence_bytes :1040-1054` 只遍历 `prompt_evidence/output_evidence/snapshot`，**不含 artifact**；
- `project_manifest :777` 的 `artifacts` 投影直接取事件字段的 `sha256/size`，而 `blobs :831-835` 的 digest 来自盘上字节，两者之间**没有任何交叉校验**。

因此，按 candidate-5 的 `allowed()`（动态正向白名单，artifact-captured 可更正），一条把 `artifact-captured.sha256` 改成另一合法 hex 的更正：(a) rule 10 的完整 `validate_event` 会通过（格式合法）；(b) 归档期 `validate_event_graph`/`validate_ledger` 都不读该字段；(c) `project_manifest` 重投影用 effective 事件自洽比较，不会产生 `manifest-projection-mismatch`。结果是 manifest 披露的 artifact 身份与实际证据字节静默脱钩——这恰恰是计划自己在 plan.md:205 用来论证“必须整体闭合证据字段”的同一条不变量。且 A1-18 只覆盖那四个字段，无法机械捕获此路径。

> 注：`artifact-captured.evidence_mode`/`reproduction_capability` 因 rule 10 的跨字段校验（`model.py:534-536`）无法被单独改坏，不构成同一缺口；缺口精确落在 `sha256`/`size`。

### 2.2 O5 门禁在 `tests/test_budget_gate.py` 现有用例上的真实影响面（自己数）

**结论：计划数字准确（21 处调用 / 17 处到达 / 4 处早返回 / helper 无需迁移）。**

独立逐处判定（按 `cmd_preflight` 真实控制流 `:1763-1778`）：

- `self.preflight` 共 **21** 处（1554/1566/1575/1584/1591/1602/1613/1623/1633/1641/1656/1666/1675/1682/1690/1699/1708/1717/1724/1736/1743）。
- 到达新门禁（`gov_blocks==1`，须经 `:1777→:1778`）的 **17** 处：上列除下列 4 项外全部。含 `test_locator_duplicate_target`（追加的是 calibration fence，非 gov 块）与 `test_locator_wrong_schema`（追加别的 schema）——两者 `gov_blocks` 仍为 1，会到达，计划分类正确。
- 早返回 **4** 处：`:1682` 两个 gov 块（`:1776` 先返回）、`:1724` CRLF（`:1770-1771` 先返回）、`:1736` 无 gov 块走 legacy（`:1769`）、`:1743` `--governance` 无块（`:1775`）。
- `TestPreflight :265-279` 的 2 处（272/278）均无 gov 块，legacy 早返回，不受影响。合计确认。
- `setUp` 在 `self.dir`（`write_plan` 的 `plan.parent`，实测 `write_plan` 写 `self.dir/plan.md`）执行 `run("init","--active-dir",self.dir,"--task-tier","critical")` 后，17 处门禁前移可通过；`read_state` 对存在的合法 state 不抛；`_task_envelope_usable` 为真。断言语义不变，判定成立。
- 新增负例必须绕过 helper（裸 `run`）写 plan 到独立目录，计划已写明；A2-5 类 `--active-dir` 负例确已删除（全篇无 live `--active-dir` preflight 用法）。

### 2.3 机器块（§15/§16）能否通过 `budget_gate.py preflight` 当前代码的机械校验

**结论：能，已实跑。**

```
$ python scripts/budget_gate.py preflight --plan .converge/active/20260911-op-envelope-b-contract-correction/plan.md
WARN:code_heavy:5,80
PREFLIGHT_OK:governance-change
EXIT=0
```

当前 preflight 会真正机械校验：未知/缺失字段、`kind: mechanism` 的 null 数值约束、`archaeology_refs` 的 git 对象存在性（`cat-file -e`）、`calibration.path` locator 解析、**canonical JSON 复算 sha256**、`corpus_digest`/`freshness` 新鲜度、`eligible_samples` 一致性（`:1540-1680`）。EXIT=0 意味着 §15 机器块与 §16 所述 `attempts.md` fence 在这些维度上全部通过；4 个 `git:` 考古引用真实存在。§15 的字节自洽性由该实跑背书。

---

## 3. 逐条 Issue

### Issue-1（high，正确性/静默缺口）— 建议阻断
- 位置：plan.md:190-195（`CORRECTION_EVIDENCE_FIELDS`）、plan.md:205（不变量论证）、对应实现 `model.py:194/530-533/777/1040-1054`。
- 问题：`artifact-captured.sha256`/`size` 是已冻结证据身份，但既未被 `CORRECTION_EVIDENCE_FIELDS` 排除，也不被 rule 10 的 `validate_event`（仅格式）或归档期任何校验与盘上 blob 绑定。更正可静默改写 artifact 身份披露，违反计划自述的 append-only 证据身份不变量，且 A1-18 无法捕获。
- 单选建议（取其一）：**将 `"sha256"`、`"size"` 加入 `CORRECTION_EVIDENCE_FIELDS`**（全仓 EVENT_FIELDS 中只有 `artifact-captured` 有这两个顶层名，加名集即精确闭合、零误伤），并在 A1-18 增补 “更正 `artifact-captured.sha256`/`size` → `correction-field-not-allowed`” 一条；同步 plan.md:203-205、§11 O1.17、§12 证据字段集列举。
- 理由：这是与 M2/I-2 同类、且更隐蔽的 fail-open 面；不修则“正确、可验收”不成立，但修法单点、范围极小，无需重设计。

### Issue-2（medium，实现陷阱/表述自洽）— 需修复
- 位置：plan.md:264、plan.md:291、plan.md:500。
- 问题：plan.md:291 表述为“先 `validate_corrections`，再对 `resolve_events(raw+[pending])` 的有效视图跑 `validate_event_graph`/`validate_ledger`”。若按字面先把 `resolve_events` 的结果传给 `validate_event_graph`，而后者入口又 `resolve_events`，即发生**二次施加**：第二次 `validate_corrections` 会看到 target 字段已等于 `corrected_value`，而 `original_value` 仍是 raw，从而误报 `correction-original-mismatch`（`resolve_events` 对已施加输入非幂等）。这与同段“禁止二次施加”的约束直接冲突。plan.md:500（T1-P2）写法正确（“对 raw+[pending] 跑”），但 §3 决策段是规范性文字。
- 单选建议：把 plan.md:291 改写为“对 `raw+[pending]` 直接调用 `validate_event_graph`/`validate_ledger`（各自入口 resolve 一次），不得先 `resolve_events` 再把结果传入”，并在 §11 O1.16/A1-19 写死该调用形态。

### Issue-3（low，验收可判定性）— 建议修复
- 位置：plan.md:537（A1-11）对 plan.md:546（A1-20）、`model.py:1035`。
- 问题：A1-11 要求“更正 `invocation-terminal.evidence_level` 先于某 terminal-decision … check 返回 []”且“capture 不抛 `user-decision-degradations`”。但只要该 decision 是 `user-decision`，按 `:1035` 必须 `user-decision-degradations` fail-closed（正是 A1-20 的语义）。A1-11 的期望只在“decision 为 reviewer-verdict / 无 user-decision”时才成立，当前的括号措辞使该条不是无条件可判定的。
- 单选建议：将 A1-11 场景收敛为“更正先于 **reviewer-verdict** decision”，删除对 `user-decision-degradations` 的泛指，或显式标注“无 user-decision 时”。

### Issue-4（low，范围纪律）— 可选
- 位置：plan.md:378（“未列出的文件一律不改”）对 plan.md:495/716/784（`attempts.md` 将新增机器块载体/Phase 0 记录/修订历史）。
- 问题：`attempts.md` 是被实际修改的对象本地文件，但未出现在 §5 File Matrix；`scan-report.md`、`_budget-state.json` 同样属 §6.3/Phase 0 产物而未列。严格按 §5 文义，Phase 1 扫描可能把 `attempts.md` 记为“未授权文件”。
- 单选建议：在 §5.3（S-F7 附近）补一行“对象本地过程文件：`attempts.md`（fence 载体/记录）、`scan-report.md`、`_budget-state.json` —— 仅对象 active 目录内，非源文件、非第三部”。

### 观察（非 issue）
- plan.md:303 把 `duplicate_governance_block` 标为 `:1776`，实际 print 在 `:1777`（`:1776` 是判定行）。不影响插入点 `:1777→:1778` 的语义，仅锚点表述。
- `refs/state-schema.md:95-96` 被引作 bootstrap 例外区间，实测 `:96` 为空行、内容在 `:95`。无实质影响。

---

## 4. 作为“第二权威”的结论

**是否认可该计划进入实施：否（先修复 Issue-1；Issue-2 需同批澄清）。**

一句话理由：该候选在事实准确性、治理合规（第三部逐字对照/机器块/授权事件）与 O5 影响面穷举上表现出色且全部经我独立实核成立，但 O1 的可更正白名单漏掉了 `artifact-captured.sha256/size` 这一无法被现有校验链或验收捕获的冻结证据身份字段，属静默 fail-open，须以单点、有界的方式闭合后方可实施。
