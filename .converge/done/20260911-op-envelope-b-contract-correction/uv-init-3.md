---
round: 3
reviewer_backend: opencode
reviewer_instance_id: 20260912_112849_b0ec83
generated_at: 2026-09-12T03:34:17.455808+00:00
verdict: 阻断需修复
---
verdict: 阻断需修复

reviewer: uv-init-3（ultraverge 初审，fresh / 跨厂商 / 只读）
对象: `.converge/active/20260911-op-envelope-b-contract-correction/plan.md`（candidate-1）
基线: 2026-09-12 HEAD `13da6055f173ab1459f62cb36de11bb05b2b19cc`（工作树另含未跟踪 `docs/plans/active/`）
框架: 前置自检 5 问 + DR 7 维 + 事实核验 + O1/O3/O5/O6 专项 + 治理合规 + 范围回归

> 判定说明：本对象四域合一（D1/D2/D3/D4）中，D1（更正事件）与 D3（治理信封）的方向基本成立但有必须修复的架构/结构问题；**D2（自指 bootstrap 通道）存在 conceptual 缺陷**：它自称"打破循环"却按自己的文字明确"不放松任何 fail-closed 校验"，且没有任何机械承载，属"未观测故障预设机制"（与本文 Non-Goals、父索引口径冲突）。因此整体判 `阻断需修复`，D2 需要按 §issue UV3-1/UV3-2 给出的替代设计重做或降级为 record-only。

---

## 一、前置自检 5 问

**Q1 产物身份自洽 —— 不通过（issue UV3-1）。**
产物标题自述同时是"归档契约更正语义 + 自指 bootstrap 通道 + 治理成本边界（O1+O3+O5+O6）"，Goal 段对 D1/D2 各给一句，但 D2 的机制本体与其声称要解决的"鸡生蛋"之间不自洽：D2 §3 原文（:149）"只授权「顺序 + 计量 + 事后独立审计」，**不放松任何 fail-closed 校验**"，而 :166 的顺序语义是"最小修复先落地 → fresh 审计 → 再 finish/archive"——这正是普通 converge 的既有顺序（Phase 2-5 实现、Phase 6 审计、Phase 7 finish/archive）。既不放行任何此前被拒的操作，就无法"打破"它声称存在的依赖循环。产物在 D2 上"声称做 A（破环），实际做 B（给一次记录性声明）"。

**Q2 产物边界诚实 —— 基本通过，但 O5 边界措辞与机器触发条件不一致（issue UV3-3）。**
D1 明确声明边界（不删除事件、不改已闭合判定、不批量重写），诚实；但 §11 把"治理类（ultraverge）对象默认要求配置"写成 policy，而机器门只由 `converge.governance-change/v1` 块 / `--governance` 触发（:174-178）。两个集合不等价，"声称的范围 > 实际机器的范围"，属虚假边界扩展。

**Q3 产物数据纯度 —— 通过。**
计划内硬编码的只有本仓真实路径、实核行号与既有常量（8/3/3、TASK_TIERS），无外部项目业务数据；数值依据（O5l=23）可复核。

**Q4 职责边界自洽 —— 不通过（issue UV3-2）。**
D2 的职责落在 `orchest.cmd_finish`（F7），却要求判定一个"机器声明"并检查 `independent_audit_ref` "已在事件流中登记"（:166）。计划未定义：声明存于何处、由谁解析、`independent_audit_ref` 用哪个事件/字段登记、`bootstrap-second-declaration` 从哪读到"第一次声明"、`bootstrap-scope-not-ultraverge` 如何读 `review_mode`。没有 owner 与数据流的职责描述，属职责错位/灰色地带。

**Q5 命名一致性 —— 不通过（issue UV3-11）。**
`bootstrap` 在本仓已承载两个既有义：`capture.bootstrap_import_legacy`（legacy raw evidence 导入）与 `state-schema.md:95` / `orchestrator-guide.md:34-36` / `budget_gate.py:1403` 的"治理自举例外（内嵌 calibration-report）"。本计划引入第三种义 `converge.bootstrap-channel/v1`。一词三义，且 §11 F8 把新段放在 `state-schema.md` "近 :95"——恰与旧 bootstrap 例外相邻，歧义会被后来者放大。

（附 Q6 原始需求一致：存在 background mismatch，见 issue UV3-14。）

---

## 二、DR 7 维逐维结论

- **DR1 一致性 — issue。** 触发条件与 policy 集合不一致（UV3-3）；`bootstrap` 一词三义（UV3-11）；D2 测试归属错位（UV3-12）；O6a 行号引用失真（UV3-9）。
- **DR2 完整性 — issue。** D2 缺机械承载（UV3-2）；D3 未处理与既有治理自举例外的交互（UV3-5）；未更新既有 17+ 个治理 preflight 正例（UV3-4）；无 opt-out（UV3-14）。
- **DR3 可维护性 — issue。** `bootstrap` 语义碰撞（UV3-11）；§11 对照表"原文"列多处用省略/转述，后续核验成本高（UV3-13）。
- **DR4 职责边界 — issue。** D2 声明/登记/校验无 owner（UV3-2）；F14 承载 D2 测试但 D2 实现在 orchest.py（UV3-12）。
- **DR5 残留与冗余 — issue。** D2 在"不放行任何被拒校验"前提下与既有正常顺序重复，属冗余机制（UV3-1）。计划本身无"迁移考古"残留。
- **DR6 可移植性 — pass。** 无环境特定硬编码；沿用 `read_state`/`ceiling` 既有抽象。（`--active-dir` 生命周期问题归 DR4/UV3-5，不属移植性。）
- **DR7 可扩展性 — pass（带上限）。** 正向白名单 `CORRECTABLE_FIELDS` 对未来字段 fail-closed，扩展性好；`corrections` omit-when-empty 沿用既有惯例。但"批量"约束未随扩展定义（UV3-6）。

---

## 三、事实核验（实开核对结果）

**已核为真（举要）**：`EVENT_TYPES` 6 类（model.py:21-24）；`COMMON_EVENT_FIELDS`:178、`EVENT_FIELDS`:179-205；`validate_event` 定义 :437、terminal-decision 特化 :445-455、封闭等集 :456-458；event graph :958-1037；`ledger-binding-missing`:642-644；:678-686 含 :679-682；`derive_supersedes_decision_event_id`:924-937；`capture` conflict :549；`transaction.reopen**:305-327 marker :321-326；`orchest` 步骤 7/8 = :1686-1698（`cmd_finish` 起 :1445）；`model.py:413` 逐事件 `validate_event`；`TASK_TIERS`:124-132；opt-in :692-694；reserve fail-closed :1139、companion :1314；`_run`:2077-2086(:2082)；preflight parser :2134-2139；插入点 :1777/:1778；三处披露 `budget_gate` 2012-2014、`converge_loop` 1093-1095、`ocsr` 400-402；adapter CLI :760-771；CONSTITUTION :67-78/:91-96；r2 gate-ledger reserved=23（脚本复算：executor 5 / ultraverge-initial 3 / outer-reviewer 6 / design-reviewer 5 / blind-reviewer 4）；`archive_convergence` check r2 返回 `[]`；测试锚点 :680/:306/:408、:785/:1448、:1003、:315、:130/:199/:268 全部命中；O1j 先例 `archive_convergence.py:291-294`→`model.py:884-893`+`:656-666` 为真。

**已核为失真/需修正（已列 issue）**：
1. `refs/state-schema.md:95-97`（:87、:199 引用）为数据耦合引用——:95 是**治理** bootstrap 例外，material 同字节规则实为 **:100**（UV3-9）。
2. O1h `grep -rin "disclosed_correction"` = 0 不实：命中至少 `docs/plans/active/20260911-op-envelope-b-contract-correction.md:25` 与本 plan.md:52 自身（UV3-10）。结论列已 soft-caveat，但"=0"裸断言仍失真（A 对象连续受阻的同型问题）。
3. O1i "更正实际是以带外方式改写了事件 55"：仅能证实事件 56 的 `host_message_id=opencode-20260911-event55-correction` 与 `user_quote` 授权；`git log --follow` 该文件只有一次提交 `529e691`，其中已是 `81a2537ea9eb`，仓库内**无法独立证实**曾存在 `PENDING` 字节（见结尾"无法核实"）。
4. §11 对照表多处"原文"并非逐字（state-schema:40/:60、SKILL.md:453 等），削弱 A16 的机械可核性（UV3-13）。

---

## 四、O1 专项（更正事件）

- 封闭字段设计与 `validate_event` 等集模型一致（`COMMON | {corrected_event_id, field, original_value, corrected_value, authorized_by_user_message_event_id, reason, corrected_at}`，仍走 `set(event)==set(expected)`），**pass**。
- 正向白名单 + fail-closed 取舍正确，**pass**。
- **闭包规则 5 表述有误**：`started_event_id` 是 `invocation-terminal` 的字段，不是 `terminal-decision` 的字段；把两类引用的字段混在"被任何 terminal-decision 引用"的括号里，会让实现者写出错误的作用域（见 UV3-7）。
- **"禁止批量重写"无机械承载**：规则 7 只禁止同一 `(target,field)` 二次更正；同一目标事件的不同白名单字段可被一次/多次全量改写（§10 对抗项 5 只在某字段闭包违规时整图拒绝）。要求句 :145"不提供批量重写"与机制不符（见 UV3-6）。
- manifest degraded 呈现复用既有 `degradations` set 并集 + `acknowledged_orphan_reservations` 的 omit-when-empty 惯例，**正确**；`events[].sha256` 保持 raw 字节（:759-762）与 A7 自洽，**pass**。
- 与 `--declare-orphan-reservation` 先例一致性：**pass**（同类"只披露、不改事件字节"）。
- 有效视图改造点已覆盖全部实核调用点：`project_manifest`(model.py:745-747)、`validate_archive`(:1178-1185)、`archive_convergence.py:147`；`load_events` 保持 raw，**方向正确**（但实现时须保证 `validate_ledger` 与 `_verify_evidence_bytes` 各自拿到正确视图，计划未点明 `_verify_evidence_bytes` 必须用 raw——它只校验 evidence 字段，白名单未含 evidence 字段，风险低）。
- 未覆盖：`correction-value-type`（规则 8）无对应验收用例，且未约束目标 `invocation_kind`（continue 的 `reservation_id` 可被更正为非空而不被任何既有校验阻挡）。

## 五、O3 专项（自指 bootstrap）

- 触发条件/次数上限/审计呈现**均只停留在自然语言**：无 schema 解析实现、无声明存储位置、无 `bootstrap-second-declaration` 的读取来源、`independent_audit_ref` "在事件流中登记"无事件类型/字段（见 UV3-2）。
- 与 finish 步骤 7/8 的关系：F7 只说"在 :1686-1698 识别声明"，但该处只调用 `_archive_cli`；解析机器声明需要额外机制，计划未授权。
- **是否真的打破"用当前代码验证改代码对象"的循环：否。** 归档始终由工作树中的当前（修复后）代码执行；D2 明文"不放松任何 fail-closed 校验"，且其顺序（先落地→审计→finish）就是既有顺序。故 D2 不能证明消除了任何此前会失败的操作（conceptual，UV3-1）。
- 是否成为常规后门：**否**（因未放松任何校验；但这也正是它无效的原因）。若未来把它改成"放松某校验"，则必须显式定义被放松项 + 补偿控制 + 实测失效证据。

## 六、O5 专项（治理信封）

- preflight 读 state 参数设计：`--active-dir` 可选 + 治理模式缺省 fail-closed，位置（:1777/:1778）在 legacy 早返回（:1763-1769）之后，legacy 逐字节不变的论证成立，**方向正确**。
- **fail-closed vs BLOCK 选择**：选 fail-closed（exit 30）与"契约违反 fail-closed"原则一致，**pass**。
- **opt-out**：未提供，与源需求风险条款"需保留显式 opt-out 并披露后果"冲突（UV3-14）。
- **推荐档位数值依据**：可复核但方法有瑕（UV3-8）："推导 A=10"实为"假设 1 轮修复 + 1 次 material 双审"的典型路径，不是机械下限（无修复、无 material 的情形可低至 6）；且 r2 实测 23 > critical initial 20，推荐 critical 仍会在 initial 处 BLOCK 并需要 extension——恰恰没有消除 r2 的"extension+多次授权"症状。
- **legacy（无 gov 块）兼容**：A10 覆盖，方向正确；但未覆盖"既有治理 preflight 正例"（UV3-4）与"治理自举例外"（UV3-5）。
- 三处 init 披露一致性：均在 `if _task_envelope_configured(state)` 内追加第四行，**一致**；但计划未显式声明"仅已配置时才打印"，且 A11 只覆盖已配置路径。
- 对未配置任务影响面：因触发条件是 gov 块而非 `review_mode`，存在"该管的没管、不该管的被管"（UV3-3）。
- 门禁谓词 `_task_envelope_configured` 不等价于"可用"（cap-only 配置过门但 `_task_envelope_initial` 仍 raise，UV3-15）。

## 七、O6 专项（material 增量复核）

- 默认 record-only 立场**被保持**，且实现分支以"pro 举证 1+2+3 全满足"为前提、仍须独立 fresh 审计，**pass**。
- 可判定性：**部分**。item 2（回放样本机械复现）与 item 3（失效边界）可机械判定；item 1"相同判定置信的可反驳论证"无机械判据，只可人工评议。鉴于默认是 record-only、"举证不足即不改"，该缺口可接受，但应在协议中显式承认"item 1 由评议人主观判定"，避免执行期争论（见 UV3-16，suggestion 级）。

## 八、治理合规

- File Matrix 对第三部文件（F8/F9/F10）逐处列出改动与 §11 对照，**结构合规**；但对照表"原文"非逐字（UV3-13）、O6a 行号失真（UV3-9）。
- 升级闸门保留：Phase 0 明确 ultraverge + HEAD 基线，**pass**。
- `refs/reviewer-discipline.md`（F11）、`CONSTITUTION.md`（F12）显式不改，**pass**。
- **四域合一是否合理：否，建议拆分（见结尾）。**

## 九、范围与回归

- 新增门禁 × 既有调用点穷举义务：§5.2 已定义扫描，**方向正确**；但未预先识别"既有治理 preflight 正例 17+ 个将因新 `--active-dir` 门禁失败"（UV3-4），也未识别"治理自举例外"（UV3-5），属 A 对象教训的同一失效模式。
- 已知测试区枚举：F13-F17 覆盖了 5 个文件，但 D2 测试放错文件（UV3-12）。
- Acceptance：A1-A16 大多可机械判定；但 **A1 在当前计划下必然失败**（既有 TestGovernancePreflight 正例未授权更新，UV3-4），故 Acceptance 自相矛盾。

---

## 十、逐条 issue

### UV3-1 — [conceptual] D2 自指 bootstrap 通道不解决任何被拒操作，破环主张不成立
- 位置: plan.md:147-168（D2）、:149、:166
- 原文: "只授权「顺序 + 计量 + 事后独立审计」，**不放松任何 fail-closed 校验**"；"允许「最小修复先落地 → 事后由未参与实现的 fresh 审计验收 → 再 finish/archive」。"
- 影响: 归档始终用工作树当前代码执行；该顺序与既有 Phase 2-5/6/7 顺序相同。"鸡生蛋"（O3e）实为"实现先于归档"的正常时序，不是死锁。不放松任何校验 ⇒ D2 不改变任何可执行集，只增加一个声明与失败码，违反 Occam / "不为未观测故障预设机制"，并使本对象的 Non-Goals 自相矛盾。
- 建议（单选）: **把 D2 降级为 record-only**（在 retrospective 记录"自指顺序已是常态时序，无需专门通道"），计量需求并入 D3；若坚持机制化，必须先给出一个"当前会被 fail-closed 挡住、且通道能合法放行"的**具体操作与实测证据**，并明列被放松的校验 + 补偿控制。

### UV3-2 — [architectural] D2 缺机械承载：声明存储/解析/validator/登记路径全未定义
- 位置: plan.md:151-166、:166；F7（:219，`:1686-1698`）
- 原文: "新增机器声明 `converge.bootstrap-channel/v1`"；"`independent_audit_ref` 在归档前填入一个「未参与实现」的 fresh 角色的产物 locator"；"要求 `independent_audit_ref` 已在事件流中登记"；"同一 active 对象第二次声明 → `bootstrap-second-declaration` fail-closed"。
- 影响: 无 File Matrix 行实现 bootstrap 块解析/校验，无字段登记载体，`bootstrap-scope-not-ultraverge` 需读 plan frontmatter 但 F7 只改 orchest 步骤 7/8。G4 与 A13/A14 无法实现；`independent_audit_ref` "在事件流中登记"在本契约不存在对应事件/字段。
- 建议（单选）: 若保留 D2，新增明确的载体与 owner——(a) 声明 = plan.md 内唯一 `converge.bootstrap-channel/v1` fenced 块；(b) validator = `model.py` 新函数（列入 File Matrix F1）；(c) `independent_audit_ref` 用一条既有 `design-review-completion` 或新增 closed 字段登记（列入 F1/F8）；(d) 首/二次声明判定基于该块在事件流中的唯一性。否则执行 UV3-1。

### UV3-3 — [architectural] O5 机器触发条件与 policy 声称范围不一致
- 位置: plan.md:174-178（门禁）、:179、:222、:400-404
- 原文: ":174 仅当进入治理模式（`args.governance` 或检测到唯一 `converge.governance-change/v1` 块）才检查"；":403 治理类（ultraverge）对象默认要求配置"；":400 `review_mode: ultraverge` 的治理对象默认要求配置 task-envelope"。
- 影响: 一个 ultraverge 对象若只改受保护文件而无 governance-change 块（本 plan.md 本身即无该块），门禁不触发；反之一个普通标准评议的数值 tweak 带 gov 块也被强制配信封。"默认要求"名不副实。
- 建议（单选）: 把 policy 措辞统一为机器可判定集合——即在 §3/§11 明说"触发条件 = 计划含唯一 `converge.governance-change/v1` 块或 `--governance`"，不再使用 `review_mode: ultraverge`/"治理类"泛称。

### UV3-4 — [structural] 新 preflight 门禁将击穿既有 17+ 个 TestGovernancePreflight 正例，A1 必失败
- 位置: plan.md:226（F14）、:260（测试区表）、:320（A1）；tests/test_budget_gate.py:1550-1750
- 原文: F14 "`TestGovernancePreflight`（`:1448`）加信封门用例"；A1 "全绿，0 fail"。
- 影响: 既有正例（如 `test_bootstrap_restore_passes`、`test_eligible_but_not_undercut_passes`、`test_role_mechanism_change_not_adjudicated` 等）均以 `self.preflight(plan)` 调用，无 `--active-dir`；加入门禁后它们将返回 `FAIL_CLOSED:governance_active_dir_required`。计划只授权"加用例"、未授权"迁移既有用例"，A1 与计划自相矛盾。这正是 A 对象"新增 fail-closed 门禁未穷举旧调用点误杀合法旧路径"的同型错误。
- 建议（单选）: 在 F14/§5.2 明确列出并授权"迁移全部既有 TestGovernancePreflight 正例：补 `--active-dir` + 已配置 envelope 的临时 state"，并把该项写入 Phase 1 扫描产物；否则改为"缺 active-dir 时回退旧行为（仅 WARN）"。

### UV3-5 — [architectural] D3 门禁未处理与既有治理自举例外的交互，且 active-dir 生命周期可能倒置
- 位置: plan.md:174-178；budget_gate.py:1403-1407；refs/state-schema.md:95
- 原文: "治理模式下缺 `--active-dir` → `FAIL_CLOSED:governance_active_dir_required`"。
- 影响: 既有"一次性 bootstrap 例外"（自引用 calibration-report 的首次治理变更）同样含 gov 块，会进入新门；若此时尚无 active 目录/未配置信封，则首次自举被自身门禁挡住。preflight 天然发生在 active 目录初始化之前，存在时序死锁。
- 建议（单选）: 在门禁中显式豁免"计划内嵌 calibration-report 自举块"这一既有例外（或在文档中定义 init-before-preflight 的强制顺序），并补一条覆盖该例外的验收/测试。

### UV3-6 — [implementation] D1 "禁止批量重写"无机械承载
- 位置: plan.md:136（规则 7）、:145、:373（§10 对抗项 5）
- 原文: "`correction-chained`：同一 `(corrected_event_id, field)` 已存在一条 correction（每字段至多更正一次，禁止链式重写）"；"不提供批量重写"。
- 影响: 规则只按 `(事件,字段)` 限量；同一目标事件的不同白名单字段可被一次或多次全量改写（5 个字段全部可改），"禁止批量重写"未被任何规则承载，与要求句冲突。
- 建议（单选）: 增加"每个 `corrected_event_id` 至多一条 correction 事件"的图级规则（`correction-batch`），或删除"不提供批量重写"的表述并把批量定义为允许。

### UV3-7 — [implementation] 闭包规则 5 字段归属错误（`started_event_id` 不在 terminal-decision 上）
- 位置: plan.md:134、:371
- 原文: "目标事件被**任何** terminal-decision 引用（`reviewer_event_id`/`started_event_id`/`source_ref`/`supersedes_decision_event_id`/`verdict_output_ref`）"。
- 影响: `started_event_id` 是 `invocation-terminal` 字段（model.py:186），不是 terminal-decision 字段；按字面实现会漏掉 invocation-terminal 的引用关系或错误作用域，闭包可能不足或误拒。
- 建议（单选）: 按 owner 事件类型重述引用集（`invocation-terminal.started_event_id`；`terminal-decision.reviewer_event_id/verdict_output_ref/source_ref/supersedes_decision_event_id`），或简化为"目标必须是 invocation-started，且不得被任何终态/判定引用链命中"。

### UV3-8 — [evidence] O5 数值依据：推导 A 不是机械下限；推荐 critical(initial 20) 仍低于 r2 实测 23
- 位置: plan.md:182-185
- 原文: "**推导 A（机械下限）**：一次 ultraverge 通过的最少派发 = 3 + ≥1 + 2 + 1 + 1 + 1 + 1 = **10**"；"critical initial 20 ≥ 10（机械下限 + 一轮完整修复周期仍在 initial 内）"；"critical initial 20 ≥ 10、cap 30 ≥ 23 且余量 7"。
- 影响: "最少派发"未含"无修复轮、无 material 双审"的更小情形（可低至 ~6），故 10 是典型值而非下界；且 r2 实测 reserved=23 > critical initial=20，采用推荐档位后仍会在 initial 处 BLOCK、仍需 extension + 用户授权——即未消除 r2 的原始症状。结论"推荐 critical"缺乏满足目标的数值依据。
- 建议（单选）: 把推导 A 改称"典型路径估算（含 1 轮修复 + 1 次 material 双审）"；并在结论中明说"critical 预期需 ≥1 次 extension"，或直接推荐按实测取 `task_envelope_initial=23 / task_envelope_cap=30`（用户显式选择）而非档位别名。

### UV3-9 — [evidence] O6a 行号引用失真：material 同字节规则在 state-schema:100，非 :95-97
- 位置: plan.md:87、:199
- 原文: "`refs/state-schema.md:95-97`"；表内 "O6a ... `refs/state-schema.md:95-97`"。
- 影响: :95 是治理 bootstrap 例外，:97-100 才是 `converge.review-target/v1` 及其"plan.md 事后任何字节变化使两份审查同时失效"规则（实为 :100）。行号失真制造误导性交叉引用（A 对象曾因同类连续受阻）。
- 建议（单选）: 全部改为 `refs/state-schema.md:97-100`（或具名 §converge.review-target/v1）。

### UV3-10 — [evidence] O1h `grep -rin "disclosed_correction" = 0` 不实
- 位置: plan.md:52
- 原文: "`grep -rin "disclosed_correction"` = 0；… 已核"
- 影响: 实际有命中（`docs/plans/active/20260911-op-envelope-b-contract-correction.md:25`；本 plan.md:52 自身引述该词）。结论列虽已 caveat 为"无事件类型/字段"，但 `= 0` 裸断言仍失真，且探针本身会把计划自身算作命中——探针设计未排除自指。
- 建议（单选）: 把单元格改成"契约内无 `disclosed_correction` 字段/事件类型；该串仅出现在 docs 草案与本计划引文中（grep 排除本对象与 docs 后为 0）"。

### UV3-11 — [wording] `bootstrap` 一词三义，命名冲突
- 位置: plan.md:147-166、:401（§11 新段近 state-schema:95）
- 原文: "新增机器声明 `converge.bootstrap-channel/v1`"。
- 影响: 与 `capture.bootstrap_import_legacy`（legacy 证据导入）及 `state-schema.md:95`/`orchestrator-guide.md:34-36`/`budget_gate.py:1403` 的治理自举例外撞名；Q5/DR1 歧义，且新段选址紧邻旧义。
- 建议（单选）: 重命名为不复用的词，如 `converge.self-referential-repair/v1`（或 `converge.self-ref-channel/v1`）。

### UV3-12 — [structural] D2 测试归属错位：分配进 test_budget_gate.py，实现在 orchest.py
- 位置: plan.md:226（F14 关联 "D2/D3"）、:290（Phase 3 "补 F14 中 D2 用例"）
- 原文: "F14 | `tests/test_budget_gate.py` | ... 加治理默认用例 … | D2/D3"；"Phase 3 ... 补 F14 中 D2 用例（bootstrap 声明 schema、单次、缺审计 fail-closed）"。
- 影响: bootstrap 门在 `orchest.cmd_finish`，budget_gate 测试文件非其测试宿主；F17（process_controller_contract）只是"复核更新跨文件不变量"，不能承接功能用例。D2 无授权测试落点。
- 建议（单选）: 指定 D2 测试落点（如 `tests/test_process_controller_contract.py` 新增用例类，或新增 orchest 专用测试文件并写入 File Matrix）。

### UV3-13 — [evidence] §11 对照表"原文"列非逐字，A16 的机械核验被削弱
- 位置: plan.md:397、:399、:403
- 原文: 如 "「公共字段：…。…`invocation-started` 拥有…」"；"「manifest 承诺 canonical records、events、…、degradations、parent revision。」"；"「| `task_tier` | 未配置 | …」"。
- 影响: "原文 → 新文"对照用省略号/转述，A16"git diff 每一处都能在表中找到对应行"退化为人工判断，无法机械匹配。
- 建议（单选）: 对第三部每一处改动给出**逐字**"原文"片段（含首尾定位词），或直接引用真实行文本块。

### UV3-14 — [implementation] 未提供显式 opt-out，与源需求风险条款冲突
- 位置: plan.md:185、:404；docs/plans/active/20260911-op-envelope-c-cost-governance.md:44
- 原文: 源需求 "默认要求 task-envelope 可能与既有未配置任务冲突，需保留显式 opt-out 并披露后果"；plan :404 新文 "治理类任务默认必须选定（不再纯 opt-in）"。
- 影响: 本对象无任何合法绕过被要求的 `background_mismatch`：旧治理流程若无法配置信封将无法 preflight，只能接受；与源需求"保留 opt-out"方向矛盾。
- 建议（单选）: 增加显式 opt-out 令牌（如 `--accept-envelope-absent`，在 gate-ledger/manifest 记披露降级），或在计划中显式记录"经用户裁决不再提供 opt-out"的决策与理由。

### UV3-15 — [implementation] 门禁谓词 `_task_envelope_configured` 不等价于"信封可用"
- 位置: plan.md:177；budget_gate.py:692-706
- 原文: "`_task_envelope_configured(state)` 为 false → `FAIL_CLOSED:governance_envelope_not_configured`"。
- 影响: 只配 `task_envelope_cap`（无 tier/initial）时谓词为 true（过门），但 `_task_envelope_initial` 仍抛 `task_envelope_not_configured`（:703-705），运行期以不同码 fail-closed——门禁放行了"不可用"配置。
- 建议（单选）: gate 改为探测 `ceiling(state,"task-envelope")`（或 try `_task_envelope_initial`），失败统一映射为 `governance_envelope_not_configured`。

### UV3-16 — [wording/suggestion] D4 裁决 item 1 无机械判据
- 位置: plan.md:193-196、:200-203
- 原文: "给出「…产出相同判定置信」的可反驳论证"。
- 影响: "相同判定置信"由评议人主观裁量，非机械判据；虽因默认 record-only 且举证责任在 pro 方而风险有限，但执行期易生争论。
- 建议（单选）: 在协议中显式写"item 1 由评议人主观判定，item 2/3 机械判定；任一不满足即 record-only"，消除歧义。

---

## 结语

- **是否建议拆分对象：是。** 理由：本对象把两个彼此独立的机制（archive contract 更正 = D1/D2；budget gate 治理信封 = D3）与一个纯评议协议（D4）合并，File Matrix 同时改 `model.py`+`capture.py`+`archive_convergence.py` 与 `budget_gate.py`+三处 init，并同改三份第三部文件。任一域的 conceptual/architectural 争议都会阻断另一域。具体建议：**D3 拆为独立计划**（其规范句本来就必须 ultraverge，合并省的只是一次流程，却把爆炸半径翻倍）；**D2 在拆分时先按 UV3-1 降级为 record-only 或重做**；D1 与 D4 可保留同对象（D4 默认不产码）。若用户坚持合并，至少把 D2 移出实现序列（Phase 3 取消），只留 D4 式记录。
- **是否存在我无法核实的事实断言：是。**
  1. O1i "事件 55 曾为字面量 `PENDING`、后被带外改写"——仓库 `git log --follow` 该文件仅一次提交 `529e691`，且其中已是 `81a2537ea9eb`；只能证实事件 56 的授权披露文本，无法独立证实历史 `PENDING` 字节。
  2. O3 的"依赖循环"存在性——只能核实 `ledger-status-conflict` 校验位置（model.py:683-684）与 finish 调用链；"若不做 bootstrap 通道则无法推进"的反事实未提供任何实测/回放证据。
  3. D4 的"回放样本"是否真实存在、能否机械复现 delta==full 结论——计划未给出具体已归档对象，无法核实。
  4. O5 "该对象全部真实调用计入 task-envelope"——依赖 Orchestrator 运行期为每次调用创建 companion 的行为，非静态可核实；本文仅核实机制存在（`_ensure_te_companion`）与 r2 计数 23。
