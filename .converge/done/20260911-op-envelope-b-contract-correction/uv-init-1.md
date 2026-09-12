---
round: 1
reviewer_backend: opencode
reviewer_instance_id: 20260912_111815_01ced3
generated_at: 2026-09-12T03:34:16.866094+00:00
verdict: 阻断需修复
---
阻断需修复

# uv-init-1 · ultraverge 初审（独立 Reviewer）

对象：`.converge/active/20260911-op-envelope-b-contract-correction/plan.md`（candidate-1）
基线：HEAD `13da6055f173ab1459f62cb36de11bb05b2b19cc`（与计划声明一致）；测试收集 485。
本报告独立实开核对了计划中全部 `文件:行` 断言与相关测试/账本；未修改任何文件。

---

存在 4 条阻断（3 条 architectural + 1 条 structural），核心是：D3 的新门禁触发条件会击穿 21 处既有治理 preflight 测试与 legacy 治理调用路径且计划未给更新路径（B1）；O3 bootstrap 声明的宿主文件/定位器/单次计量载体完全未定义（B2）；O1 有效视图与 manifest 冻结投影的语义冲突未裁决（B3）；O6「实现」分支无有界实施路径（B4）。事实层面另有若干行号/符号失真（N1-N4）。以下逐项。

---

## 一、前置自检 5 问

1. **产物身份自洽**：**基本通过，但有命名漂移**。产物自述「归档契约更正语义 + 自指 bootstrap 通道 + 治理成本边界」，四域各有决策（D1-D4），身份不矛盾。但 D3 标题称「治理类任务」而机制触发条件是 `review_mode: ultraverge`（见 N7），名称与实现指向的集合不一致。
2. **产物边界诚实**：**不通过（issue）**。Goal 声明「消除归档与被修机制之间的依赖循环」（plan.md:28-30），但 D2 自述「不放松任何 fail-closed 校验」（plan.md:149）——既然不放松校验，归档仍要求被修代码已落地，依赖循环并未被该机制打破（见 N12）。「机械下限 = 10」被当作下界用于否定 small/medium，但该 10 不是机械下界（见 N10）。
3. **产物数据纯度**：**通过**。未携带业务数据；新增值为机制常量（`CORRECTABLE_FIELDS`、closed 字段集），无环境硬编码。
4. **职责边界自洽**：**通过但偏弱**。D2 的计量职责显式委托给 D3（plan.md:168「由 D3 保证已配置」），形成 D2→D3 的顺序依赖，而 O3 与 O5 又被并入同一对象，属边界耦合（见 N12）；bootstrap 校验落在 `orchest.cmd_finish`（F7），声明却无宿主文件，职责落位不清（B2）。
5. **命名一致性**：**不通过（issue）**。「治理类」与「`review_mode: ultraverge`」在同一节内互换使用（D3 标题 vs :174-178 触发条件），二者不是同一集合；O1 的 `correction` 事件与历史散文 `disclosed_correction` 的对比表述不精确（见 N1）。

---

## 二、DR 7 维逐维结论

| 维度 | 结论 | 依据 |
|---|---|---|
| DR1 一致性 | **issue** | 治理类/ultraverge 命名不一致（N7）；O6a 锚点 `state-schema.md:95-97` 实际不含失效规则（N2）；closure 规则列了不存在的字段（N5）。 |
| DR2 完整性 | **issue** | bootstrap 声明宿主文件/定位器缺失（B2）；O6 实现分支无文件矩阵（B4）；无 `converge.governance-change/v1` 机器块与授权 user-message 事件（N8）；`validate_event` 的 correction 分支未声明（N13）。 |
| DR3 可维护性 | **issue** | 治理 preflight 现有 21 处调用均不带 `--active-dir`，共享 helper 未纳入 File Matrix（B1）；`docs/plans/active/` 存在计划副本，双份维护（N9/DR5）。 |
| DR4 职责边界 | **issue** | 有效视图（校验）与 manifest 投影（披露）职责未定界（B3）；D2 计量前提依赖 D3 未落地状态（N12）。 |
| DR5 残留与冗余 | **issue（轻）** | `docs/plans/active/20260911-op-envelope-b-contract-correction.md`（64 行草案）与 `.converge/.../plan.md`（416 行 candidate）并存且内容已分叉，未列入 File Matrix；`docs/plans/active/` 当前 untracked（N9）。 |
| DR6 可移植性 | **pass** | 新增均为仓库相对路径与机制常量，无新环境特定路径/用户名。 |
| DR7 可扩展性 | **issue（轻）** | 「每 (事件,字段) 至多一次」的可扩展边界被承认；但 `CORRECTABLE_FIELDS` 硬编码于代码而 `state-schema` 复述同一集合（双单源），未来新增字段须两处同改（N7 同域）。另 bootstrap 的「同 slug 单次」在 reopen 后如何续算未定义（B2）。 |

---

## 三、逐条 issue

### 阻断

#### B1 — [architectural] D3 preflight 新门禁的触发条件击穿既有治理 preflight 与 legacy 治理调用路径

- **文件:行**：`plan.md:174-178`（D3 第 1 点）、`:216`（F4）、`:226`（F14）；证据：`scripts/budget_gate.py:1763-1778`、`tests/test_budget_gate.py:1448-1750`（`TestGovernancePreflight`，21 处 `self.preflight`，helper 定义于 :1546-1547，均不传 `--active-dir`）。
- **原文**：计划 :175「仅当进入治理模式（`args.governance` 或检测到唯一 `converge.governance-change/v1` 块）才检查」；:176「治理模式下缺 `--active-dir` → `FAIL_CLOSED:governance_active_dir_required`」。
- **影响**：现有 `TestGovernancePreflight` 的正/负例全部内嵌 gov 块且不传 `--active-dir`（例如 :1550-1556 期望 `PREFLIGHT_OK`、:1571-1576 期望 exit 15 `BLOCK:empirical_conflict`）。按计划的触发条件，这些调用会先命中新门禁并返回 `FAIL_CLOSED:governance_active_dir_required`（exit 30），**至少 21 处既有断言被击穿**；计划仅说 F14「加信封门用例」，未把共享 helper 与既有用例的更新列入 File Matrix，A1/A2「全绿」按现文案不可达。计划宣称的「纯 legacy 路径逐字节不变」（:329 A10）只覆盖「无 gov 块」路径，不覆盖「隐式检测到 gov 块」的既有治理调用。此外 `cmd_preflight` 全仓无编排层调用点（Grep 仅测试与文档），故受影响面被低估为「测试 + 手工调用」而非零。
- **建议（单选）**：**把新门禁的触发收窄为仅 `args.governance` 显式传入**（隐式检测到块时不启用信封门，保持既有治理 preflight 行为逐字节不变）；若要保留隐式触发，则必须在 F14 中显式把所有既有 `TestGovernancePreflight` 用例与 `self.preflight` helper 的改造写入 File Matrix，并在 A2 之外单列回归命令。

#### B2 — [architectural] O3 bootstrap 声明没有宿主文件/定位器，且与 material 同字节冻结冲突、单次计量无机械载体

- **文件:行**：`plan.md:151-166`（D2 closed 字段与约束）、`:219`（F7）、`:401`（F8 新段）；对照 `refs/orchestrator-guide.md:19`、`refs/state-schema.md:99`（material-revision 块宿主为 `attempts.md`，有唯一 locator 语法）。
- **原文**：:161「`independent_audit_ref` 在归档前填入一个『未参与实现』的 fresh 角色的产物 locator」；:166「`orchest.cmd_finish` 在步骤 7/8（`:1686-1698`）识别 bootstrap 声明」。
- **影响**：计划通篇未说明 `converge.bootstrap-channel/v1` 块写在哪（plan.md / attempts.md / 新文件），也未给 locator 语法。三处硬伤：(a) 若放在 `plan.md`，则 :161「归档前填入 `independent_audit_ref`」会在 material 双审后再次改写 `plan.md` 字节，直接违反 `SKILL.md:462` / `state-schema.md:100` 的「任何字节变化使两份审查同时失效」；(b) `orchest.cmd_finish` 无从确定扫描哪个文件、解析哪个 fenced block；(c) 「同一 active 对象第二次声明」「reopen 重算同 slug 单次」需要持久载体，而声明本身若为可覆盖的 fenced 块，无法机械判「第二次」。
- **建议（单选）**：**将声明块固定在 `attempts.md`（与 material-revision 同宿主、同 locator 惯例），closed 字段增加 `declared_at`/单调顺序锚，单次性由「事件流中已存在的 `authorization` user-message + 归档 manifest 的 `bootstrap_channel` 披露」联合判定；`independent_audit_ref` 只指向已登记的事件 locator，不改写 plan.md**。

#### B3 — [architectural] O1 有效视图与 manifest 冻结投影的语义冲突未裁决

- **文件:行**：`plan.md:139-141`（D1 有效视图/披露）、`:213`（F1）、`:326`（A7）。
- **原文**：:139「`validate_event_graph` / `validate_ledger` / `project_manifest` 的语义校验一律走有效视图」；:141「manifest 保留原值并披露更正」「原值保留在两处：raw 事件文件字节不变 + correction 事件的 `original_value`」。
- **影响**：「校验走有效视图」与「manifest 保留原值」并置时，manifest 的 `invocations`/`artifacts` 投影（`model.py:757-781`）到底呈现 raw 还是 corrected 未定义。若投影保留 raw：manifest 会出现 `invocations` 中 invocation-started 的 `reservation_id=PENDING`，而同一 manifest 的 ledger 校验以被更正值通过、且 invocation-terminal 的 `settlement_ref=gate-ledger.jsonl:81a2537ea9eb`——即冻结投影不再是「被校验事实的投影」，违反 `refs/state-schema.md:36,60` 的「manifest 是 owners 的冻结投影」。若投影用 corrected：`events[].sha256` 仍应取 raw 磁盘字节（计划 A7 已要求），需明确区分「字段值投影走有效视图、字节哈希走 raw」。计划没有裁决，实现者两种都写得出。
- **建议（单选）**：**裁定「投影字段值走有效视图、`events[].sha256`/`size`/`path` 一律取 raw 字节、correction 的 `original_value` 作为唯一原值留痕」**，并在 D1 与 A7 各加一句显式断言（例如 A7 增：`manifest.invocations` 中该 invocation-started 的 `reservation_id == corrected_value`）。

#### B4 — [structural] O6 的「实现」分支没有有界实施路径（File Matrix / 阶段 / Acceptance 均缺）

- **文件:行**：`plan.md:191-203`（D4 裁决协议）、`:299-302`（Phase 5）、`:221`（F9 条件修改）、`:321-335`（Acceptance 无 O6 条目）。
- **原文**：:201「满足实现方 1+2+3 → 允许实现，且仍须独立 fresh 审计验收」；:301「产出裁决记录……若裁决为 record-only，则 F9 `:17-36` 不改，且不新增代码」。
- **影响**：计划以「Bounded Implementation Sequence」自居，但 D4 明确允许裁决为「实现」，而 §4 File Matrix 没有任何 delta 复核机制的代码/测试宿主，§6 没有实现阶段，§7 没有对应 Acceptance。一旦 Phase 5 裁决为「实现」，计划即无有界路径可执行——这正是「计划必须可执行」的硬伤。
- **建议（单选）**：**把本对象的 O6 产出限定为「只记录裁决证据与结论（record-only）」，并在 D4 写明「任何『实现』分支一律移交新对象、重新走计划与 File Matrix 评议」**；相应删除 :201「允许实现」的本地执行含义。

### 非阻断

#### N1 — [evidence] 「`grep -rin "disclosed_correction"` = 0」为失真断言

- **文件:行**：`plan.md:52`（O1h）。
- **原文**：「`grep -rin "disclosed_correction"` = 0」。
- **影响**：实际全仓有命中：`docs/plans/active/20260911-op-envelope-b-contract-correction.md:25`（含 `disclosed_correction`），且本计划 :52 自身即引述该词。计划「修正」列已把结论softening为「无事件类型/字段」，但表内 `= 0` 的裸断言仍不实；A 对象曾因同类失真连续受阻。
- **建议（单选）**：把该单元格改为「无 `disclosed_correction` 字段/事件类型；该词仅出现在本计划引述与 docs 草案散文中」，删除 `= 0` 字样。

#### N2 — [evidence] O6a 的 `refs/state-schema.md:95-97` 锚点不含所述失效规则

- **文件:行**：`plan.md:87`（O6a）。
- **原文**：「`refs/state-schema.md:95-97`」用于支撑「任何字节变化使两份审查同时失效」。
- **影响**：`:95` 是 governance bootstrap 例外、`:97` 是 `converge.review-target/v1` 标题；失效句实际在 `:100`。锚点错位。
- **建议（单选）**：改为 `refs/state-schema.md:97-100`（核心句 :100）。

#### N3 — [evidence] O5c 把 `FailClosed` 抛出点写成 `:1139`，实际抛点在 `:705`

- **文件:行**：`plan.md:72`（O5c）。
- **原文**：「raises 点在 :1139」。
- **影响**：`ceiling(state,"task-envelope")` 在 `:1139` 被调用，但 `raise FailClosed("task_envelope_not_configured")` 实际在 `_task_envelope_initial`（`budget_gate.py:705`）；`:1139` 是触发调用点而非抛出点。对实现定位有轻微误导。
- **建议（单选）**：表述改为「触发点 `:1139`（经 `ceiling`→`_task_envelope_initial:705` 抛出）」。

#### N4 — [evidence] F2/F3 的符号断言失真：`capture.py` 无 `__all__`；F3 漏记 main dispatch 分支

- **文件:行**：`plan.md:214`（F2）、`:215`（F3）。
- **原文**：F2「`__all__`/导出对齐」；F3「加 `record-correction` 子命令接线 | 近 :283-287」。
- **影响**：`scripts/archive_contract/capture.py` 全文无 `__all__`（实核），该断言指向不存在的结构；`archive_convergence.py` 除 parser（:283-287）外还必须在 `main()` dispatch（现有 `record-user-message` 分支在 :360-362）增分支，计划未列。
- **建议（单选）**：F2 删除 `__all__` 断言；F3 补「parser :283-287 + main dispatch 近 :360」。

#### N5 — [structural] O1 closure 规则把 `started_event_id` 当作 terminal-decision 引用字段

- **文件:行**：`plan.md:134`（规则 5）。
- **原文**：「目标事件被**任何** terminal-decision 引用（`reviewer_event_id`/`started_event_id`/`source_ref`/`supersedes_decision_event_id`/`verdict_output_ref`）」。
- **影响**：`terminal-decision` 字段集为 `model.py:196-200`，不含 `started_event_id`；`started_event_id` 属于 `invocation-terminal`（`model.py:185-191`）。若按字面实现，该条为 no-op；若实现者「修正」为检查 `invocation-terminal.started_event_id`，则会禁止更正任何已有 terminal 的 invocation-started，直接杀死 O1 的唯一动机场景（r2 事件 55 是有 terminal 的 invocation-started）。
- **建议（单选）**：把规则 5 的引用集精确写为 `terminal-decision` 的 `{reviewer_event_id, source_ref, supersedes_decision_event_id, verdict_output_ref}`，并显式声明「invocation-terminal.started_event_id 不在闭包引用集内（否则 r2 场景不可更正）」。

#### N6 — [structural] manifest/INDEX 的 `corrections` 段必须 omit-when-empty，否则 A15 既有归档回归必破

- **文件:行**：`plan.md:141`（D1 披露）、`:334`（A15）。
- **原文**：:141「`INDEX.md` 渲染 `corrections` 块（`render_index_bytes`，与 `degradations` 同风格）」；A15「`check .converge/done/20260910-...` → `[]`」。
- **影响**：`validate_archive` 用 `render_index_bytes(manifest)` 逐字节比对 `INDEX.md`（`model.py:1189`）。若 corrections 段无条件渲染（含 `- none`），所有既有归档的 INDEX 字节会变，A15 立刻 `index-mismatch`。计划只对 manifest 段写了 omit-when-empty，对 INDEX 段没写。
- **建议（单选）**：明确「manifest `corrections` 与 INDEX `Corrections` 段均 omit-when-empty」，A15 作为该约定的回归门。

#### N7 — [structural] 「治理类」与「`review_mode: ultraverge`」不是同一集合，规范句与门禁语义不一致

- **文件:行**：`plan.md:170`（D3 标题）、`:174-178`（触发条件）、`:400`（§11 state-schema 新文）、`:403-404`（SKILL 新文）。
- **原文**：D3 标题「治理类任务默认要求配置」；:177「`_task_envelope_configured(state)` 为 false → `governance_envelope_not_configured`」；:400「`review_mode: ultraverge` 的治理对象默认要求配置」。
- **影响**：门禁实际触发 = 治理 preflight（gov block / `--governance`）；规范句却声明对 `review_mode: ultraverge` 对象生效。一个不含 gov block 的 ultraverge 对象不会命中门禁，但规范句说它「默认要求配置」；反之一个 standard-review 但含 gov block 的对象会命中。两集合交叉导致「规范与机制不一致」。
- **建议（单选）**：统一判据——要么规范句改成「进入治理 preflight 的对象」，要么门禁改读 `_budget-state.json` 的 `fsm.mode == "ultraverge"`（并按该集合重估对既有 ultraverge 对象的影响面）。

#### N8 — [structural] 本计划自身缺 `converge.governance-change/v1` 机器块，且无 2026-09-12 授权的 user-message 事件

- **文件:行**：`plan.md:15-18`（用户裁决散文化）、`:220`（F8 ⑤ bootstrap 段）、`:397-405`（§11 改第三部）；证据：`.converge/active/.../evidence/events/` 仅 3 事件（executor 起止 + 1 个 ultraverge-initial），无 user-message；gate-ledger 无 task-envelope 预约；`_budget-state.json` `config:{}`。
- **原文**：:15「2026-09-12 用户裁决：撤销独立子计划 C……」。
- **影响**：本计划要改第三部受保护文件并新增治理门禁。`refs/state-schema.md:87-94` 规定治理 preflight 的唯一机器输入是 `converge.governance-change/v1`（含 `user_message_events` UUID）；r2 计划含该块，本候选不含。若走 `preflight --governance` 会 `FAIL_CLOSED:no_governance_block`；若不走则治理数值经验门无从执行。D2 的 `authorized_by_user_message_event_id` 与 D3 的授权留痕同样需要一条真实 `user-message` 事件，而事件流中尚不存在。用户裁决目前只有散文留痕，不可机械引用。
- **建议（单选）**：在 `plan.md` 内嵌唯一的 `converge.governance-change/v1` 块（D3 为 `kind: mechanism`，released/old/proposed 为 null），并先用 `record-user-message` 落一条承载 2026-09-12 裁决的 user-message 事件，把其 UUID 填入 `user_message_events`。

#### N9 — [evidence] Phase 0 的「工作树除本 active 目录外无未提交改动」当前不成立

- **文件:行**：`plan.md:277`（Phase 0 验证）。
- **原文**：「工作树除本 active 目录外无未提交改动」。
- **影响**：实核 `git status --porcelain` 为 `?? docs/plans/active/`（含本计划的 docs 副本与 C 存根），`.converge/active/` 被 `.gitignore` 忽略。Phase 0 按字面无法通过。
- **建议（单选）**：把 `docs/plans/active/` 明列为「本对象预期存在的未跟踪文档产物」，或将其纳入提交后重述 Phase 0 判据。

#### N10 — [implementation/wording] 「机械下限 = 10」不是机械下界

- **文件:行**：`plan.md:182-185`（D3 推荐档位）。
- **原文**：「**推导 A（机械下限）**：一次 ultraverge 通过的最少派发 = 3 初审 + ≥1 修复轮 outer + 2 material 双审 + 1 设计审查 + 1 终审 + 1 实施 + 1 独立审计 = **10**」。
- **影响**：该式把「≥1 修复轮」「2 material 双审」当作必经项。若首轮 verdict = `可执行`（ultraverge 明线规定可跳过完整收敛）且无 material revision，最少派发可以显著小于 10；故 10 是「含一轮修复的典型路径」，不是机械下界。用它断言 small/medium「必在机械下限前阻断」论证强度过高。
- **建议（单选）**：改称「典型最少派发（假设一轮修复 + 一次 material 修订）≈10」，或在脚本中把「无 material/无修复」路径显式纳入推导并给出各自下界。

#### N11 — [architectural] O1 授权绑定过弱（任意更早 user-message 即可授权）——「后门」风险未被机械封死

- **文件:行**：`plan.md:135`（规则 6）、`:357`（R1）。
- **原文**：规则 6「`authorized_by_user_message_event_id` 未解析到更早的 `user-message` 事件」即拒绝；`user-message` 字段仅 `host_message_id/user_quote/recorded_at`（`model.py:204`）。
- **影响**：规则只校验「存在更早的 user-message」，不校验该消息内容与本次更正的对应关系。任何早先的普通用户消息都能充当任意 correction 的授权凭据；`opposed to user-decision` 的 `source_ref` 还要求 quote 逐字匹配（`model.py:1032-1034`），correction 反而更弱。R1 声称「正向白名单 + 闭包 + 对抗测试」控制后门，但授权绑定这一步是 fail-open 的。
- **建议（单选）**：要求 `authorized_by_user_message_event_id` 绑定的 user-message 的 `user_quote` 含机器可判定的授权串（如 `correction:<corrected_event_id>:<field>=<corrected_value>`），由 `validate_corrections` 逐字复核；或在 closed 字段集加 `authorization_quote` 并与来源事件 quote 比对。

#### N12 — [architectural] O3 未打破「用当前代码验证被修对象」的循环，且计量前提在本对象上未满足

- **文件:行**：`plan.md:149`（D2「不放松校验」）、`:166`（依赖当前代码重放）、`:168`（「由 D3 保证已配置」）；证据：`.converge/active/.../_budget-state.json` `config:{}`。
- **原文**：:166「`orchest.cmd_finish` 在步骤 7/8（`:1686-1698`）识别 bootstrap 声明……否则 fail-closed」；:168「该对象全部真实调用计入 `task-envelope`（由 D3 保证已配置）」。
- **影响**：finish 步骤 7 调 `archive_convergence.py` 逐事件 `validate_event`（`model.py:413`），D2 明确不放松该校验——因此被修对象要归档，仍要求修复代码已存在于工作树；bootstrap 只增加了「声明 + 事后审计 + 披露」，并不构成对「当前代码重放」的机械绕行。Goal「消除依赖循环」属过度声称（可接受的说法是「授权自指修改的落地顺序与事后审计」）。另外 D2 的计量前提（task-envelope 已配置）在当前 active 对象上不成立（config 为空，gate-ledger 亦无 task-envelope 预约），D3 又晚至 Phase 4 才实现，Phase 0-3 的自指调用无法按 D2 声称计入信封。
- **建议（单选）**：把 D2 的 Goal 收窄为「为自指修改提供显式、单次、可审计的授权与事后独立审计」；并在 Phase 0 增加「配置 task-envelope 并将其 user-message 授权落事件流」的显式步骤（否则删除「由 D3 保证已配置」的依赖表述）。

#### N13 — [structural] `validate_event` 的 `correction` 分支未声明，字段级类型校验落空

- **文件:行**：`plan.md:110-121`（closed 字段集）、`:137`（规则 8）；对照 `model.py:437-575`。
- **影响**：`validate_event` 在闭集判定后按 `kind` 走类型分支（`model.py:464-575`），没有 `correction` 分支则 `corrected_at`/`reason`/`corrected_event_id`/`authorized_by_user_message_event_id` 的 UUID/时间戳/文本边界均不被 `validate_event` 检查，只剩 `validate_corrections` 的规则 8 覆盖 `corrected_value`。计划未声明补该分支。
- **建议（单选）**：F1 显式写明「`validate_event` 增加 `correction` 分支：`corrected_at` 走 `_timestamp`、`corrected_event_id`/`authorized_by_user_message_event_id` 走 `_uuid`、`field`/`reason` 走 `_text`」。

#### N14 — [wording] `correction` 与 `disclosed_correction` 的对比表述、以及 `corrections` 披露键名在三处未统一

- **文件:行**：`plan.md:52`、`:141`、`:399`。
- **影响**：一处称「无 `correction` 事件类型」，一处称 manifest 段 `corrections`，一处 §11 写「corrections（omit-when-empty……）」。键名/事件名/历史散文词三者需在实现前 lock 死，避免 renderer 与 model 用不同键。
- **建议（单选）**：在 D1 顶部加「命名锁定」小节：事件类型 `correction`、常量 `CORRECTABLE_FIELDS`、manifest/INDEX 键 `corrections`、降级串前缀 `correction:`。

---

## 四、O 专项小结（对应任务框架 4-7）

- **O1**：closed 字段设计与 `validate_event` 等集模型方向一致，正向白名单正确（fail-closed）；图级约束有 `validate_corrections` 全图 + 落盘前校验的机械承载，链式/批量可拦。问题在：closure 引用集错列字段（N5）、manifest 投影语义未裁决（B3）、授权绑定过弱（N11）、`validate_event` 分支未声明（N13）、披露 emoji-omit 约定未覆盖 INDEX（N6）。与 `--declare-orphan-reservation` 先例的一致性成立（复用 `degradations` + omit-when-empty 披露）。
- **O3**：触发条件/单次上限/审计披露在文本上齐备，但与 finish 7/8 的关系说明含糊，实际不构成机械破环（N12）；声明宿主与单次载体缺失（B2）；会不会成常规后门——`use_limit==1` + ultraverge-only + 必含受保护路径 + 独立审计能压制频次，但 `repairs` 为自声明且不由 git diff 机械核验，属残余风险。
- **O5**：参数设计（新增 `--active-dir`）合理；fail-closed vs BLOCK 选 fail-closed，与既有 `task_envelope_not_configured` 一致；但触发面击穿既有测试（B1）；无显式 opt-out（仅能以最小 `initial=1` 变相满足，建议明说）；legacy 兼容仅覆盖无 gov 块路径（B1）；三处 init 披露改动点实核一致（`budget_gate.py:2012-2014`、`converge_loop.py:1093-1095`、`ocsr_spawn_adapter.py:400-402`）；推荐档位依据可复核但「机械下限」表述不成立（N10）；对未配置任务的影响面被低估（B1/N7）。
- **O6**：默认 record-only 立场保持，裁决规则对「实现」给了 3 条举证义务（其中回放样本可机械复现属可判定），方向正确；但「实现」分支无有界路径（B4）。

## 五、事实核验汇总（计划断言 vs 实核）

| 断言 | 实核 | 结论 |
|---|---|---|
| HEAD `13da605` | `13da6055f1...` | 一致 |
| `EVENT_TYPES` :21-24 六类 | 实核一致 | 一致 |
| `EVENT_FIELDS` :179-205 / COMMON :178 | 实核一致 | 一致 |
| `validate_event` :437-458，特化 :445-455，等集 :456-458 | 实核一致 | 一致 |
| `validate_event_graph` :958-1037 | 实核一致 | 一致 |
| `ledger-binding-missing` :642-644 | 实核一致 | 一致 |
| `ledger-status-conflict` :678-686（含 :679-682） | 实核一致 | 一致 |
| `Acknowledged` :884-893 / 降级串 :656-666 | 实核一致 | 一致 |
| reopen :305-327 marker :321-326 | 实核一致 | 一致 |
| `derive_supersedes_decision_event_id` :924-937 | 实核一致 | 一致 |
| capture 派生冲突 :523-554 / :549 | 实核一致（函数延伸至 :575） | 基本一致 |
| finish 步骤 7/8 :1686-1698 | 实核一致（archive 调用 :1688-1691，check :1694-1698） | 一致 |
| `TASK_TIERS` :124-132 含别名 | 实核一致 | 一致 |
| opt-in :692-694 | 实核一致 | 一致 |
| reserve 未配置 :1137-1139，companion :1314，输出 :2082 | 触发点一致；抛出点实为 :705 | **失真（N3）** |
| preflight parser :2134-2139 | 实核一致 | 一致 |
| governance preflight :1730-1778，各校验函数起止 | 实核一致 | 一致 |
| 插入点 :1777→:1778 | 实核一致 | 一致 |
| 三处 init 披露 | 实核一致 | 一致 |
| adapter CLI :760-771 | 实核一致 | 一致 |
| `disclosed_correction` grep = 0 | 有命中（docs 草案 :25、本计划 :52） | **失真（N1）** |
| O6a `state-schema:95-97` | 失效句在 :100 | **失真（N2）** |
| r2 gate-ledger 23 reserved（5/3/6/5/4） | 实核一致（文件 51 行、reserved 23） | 一致 |
| 测试锚点 :680/:306/:408、:785/:1448、:1003、:315、:130/:199/:268 | 逐一实核一致 | 一致 |

## 六、结尾

- **是否建议拆分对象**：**否（本轮不建议强拆），但为条件性**。理由：O3 的计量语义显式依赖 O5 的 task-envelope 已配置（D2:168），强拆会在两个对象间制造未定接口；四域共享同一证据源（r2 操作包络缺口）且已划定独立 Phase 与 File Matrix。**但**若 B3（有效视图/投影语义）与 B2（bootstrap 宿主）无法在不新增 File Matrix 行的前提下定清，则应把 O1（归档契约语义）拆为独立对象单独 ultraverge——它是四域中唯一的契约语义变更，影响面（所有归档/检查路径）与其余三域不可比。
- **无法核实的事实断言**（列出）：
  1. 2026-09-12「撤销子计划 C、O5/O6 并入 B」的用户裁决——无对应 `user-message` 事件，仅散文留痕，无法机械核实。
  2. r2 当年事件 55 的原始失败态（`ledger-binding-missing`）与其后带外改写的精确时间线——现树事件 55 已是更正值，git 侧未逐版回溯核实。
  3. D3「机械下限 = 10」的路径假设（是否必有 1 修复轮 + material 双审）——属推导，非实测。
  4. 「r2 4 条 extension、9 次 spawn」等成本数字——属父索引/C 草案叙述，本次未复算 extension 链。
  5. `review_mode: ultraverge` 之外是否还有别的调用方会把 gov block 计划送入 `preflight`——已实核仓库内无编排层调用点，但无法排除仓库外/人工脚本调用。
