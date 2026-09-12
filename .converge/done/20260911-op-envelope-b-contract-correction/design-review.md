# 设计审查报告 · 20260911-op-envelope-b-contract-correction（ultraverge 终局）

设计需修订

- 审查对象（终局字节，冻结）：`.converge/active/20260911-op-envelope-b-contract-correction/plan.md`（candidate-3，695 行）
- 基线：HEAD `13da6055f173ab1459f62cb36de11bb05b2b19cc`；`git status --porcelain` = `?? docs/plans/active/`
- 审查者身份：fresh、跨厂商设计审查者；只读（除本文件外未修改任何文件）。事实核验已由双权威完成，本报告**不重复事实核对**，只审设计决策本身的合理性、自洽性与可持续性。
- 依据：`refs/design-review-prompt.md` 7 维 + 代码实核（`model.py` / `capture.py` / `archive_convergence.py` / `transaction.py` / `budget_gate.py` / `converge_loop.py` / `ocsr_spawn_adapter.py`）

> 定位声明：本报告不是审批，是设计盲区检测。首行二选一是本任务要求的交付结论，不是 converge 主循环的 blocking verdict。

---

## 一、按 DR 维度逐维结论

### DR1 一致性（Consistency）— issue

- **[设计级] "唯一语义读取点" 的声明与设计实现不一致。** `plan.md:240-241` 声称唯一语义读取点是 `validate_event_graph` / `validate_ledger` 入口，`project_manifest` 只"供投影使用"；但 `plan.md:242-245` 又让 `project_manifest` 自行 `resolve_events`，而 **`capture.py` 的写入前判定链完全未纳入有效视图**。实核：`capture._prepare_terminal_decision`（`capture.py:523-575`）用 raw `existing` 调 `derive_decision_fields`→`derive_presented_degradations`（`model.py:902-921`，读 `evidence_level`/`reproduction_capability`）与 `validate_reviewer_verdict_authority(existing, values)`（`capture.py:560`）。这使"所有语义读取经有效视图"成为不成立的断言。详见 §三 M1。
- **[设计级] `DECISION_REFERENCED` 的保护方向与动态白名单的放行方向不一致。** `plan.md:168-177` 只保护"被 decision 引用的事件"（入边），但 `plan.md:144-153` 的 `allowed()` 会放行 target 事件自身的**出边结构字段**（如 `invocation-terminal.started_event_id`、`invocation-started.parent_event_id`、`design-review-completion.invocation_event_id`）。计划没有声明"出边结构字段是否可更正"的原则，也没有任何对抗用例覆盖。详见 §三 M2。
- 命名与既有约定协调：`event-correction` / `corrections` / `correction:` / `CORRECTION_CLOSED_FIELDS` 与 `EVENT_TYPES`/`acknowledged_orphan_reservations`/`model-provenance:` 前缀风格一致；`FAIL_CLOSED:governance_requires_task_envelope` 与 `task_envelope_not_configured` 同构；`--allow-unconfigured-envelope` 与既有 `--allow-legacy` 前缀一致。此处无问题。
- 一处轻微措辞自相矛盾：`plan.md:128` 命名锁定 `CORRECTION_CLOSED_FIELDS`，但 `plan.md:147` 又写 `CLOSED = CORRECTION_CLOSED_FIELDS = {...}`，同一含义两个别名，易在实现时产生两个常量（Minor，不列 must-fix）。

### DR2 完整性（Completeness）— issue

- **[设计级] 更正机制自身无修复路径。** 规则 3（`plan.md:159`）禁止 target 为 `event-correction`，规则 7（`plan.md:163`）禁止同一 `(target, field)` 二次更正，且没有 correction 的 supersede/undo 语义。因此**一条 `corrected_value` 语义写错的更正（类型合法、`validate_event` 通过）会永久占据有效视图，无任何 in-band 补救路径**。这与 D1 的立身动机（"修复记录错误"）直接冲突：一个用于修复记录的机制，本身可以制造不可修复的记录错误。详见 §三 M3。
- **[设计级] opt-out 的"审计可见"只有瞬态 stdout。** `plan.md:278` 以 `WARN:unconfigured-envelope:<reason>` 声明审计面可见，但该 WARN 不落盘、不进 manifest、不进 ledger；计划自己在别处引用的先例 `--declare-orphan-reservation`（`plan.md:81`、`archive_convergence.py:291-294`→`model.py:884-893`）恰恰是**持久披露**（写进 manifest）。门禁以可审计性为立身理由，却给出比先例更弱的披露通道。详见 §三 M6。
- legacy/回滚路径：每项改动的"独立回滚"声明基本可信（Track-1 为 model/capture/cli/测试一体，Track-2 为门禁+parser+披露一体），无跨 Track 回滚依赖。此处无问题。
- 错误路径：10 个 `correction-*` 码 + `governance_requires_task_envelope` 均有退出码/披露定义；规则 10 与 10b 都映射到 `correction-value-type`，底层码经 detail 携带（`plan.md:232`），可诊断性可接受。

### DR3 可维护性（Maintainability）— issue

- **[设计级] 规则 10 的"单源值谓词映射表 + `_validate_field_value` 抽取"与规则 10b 重复，构成维护陷阱。** `plan.md:195` 抽出 `_validate_field_value(kind, field, value)` 供 `validate_event` 与 `validate_corrections` 共用，并在 `plan.md:197-231` 维护一张覆盖全部放行字段的表，且"未列出的字段一律 `correction-value-type` 拒绝"。但 `plan.md:232` 的规则 10b 已对**每个存在更正的 target** 应用全部更正后运行**完整 `validate_event`**——后者在构造上就是单源，且已包含类型与跨字段校验。于是规则 10 的表是第二次手工枚举，未来任何对 `validate_event` 的字段新增都不会自动反映到白名单，会静默地把新字段变成"不可更正"。这正是该仓库多处注释反复警告的"两个真相"模式。详见 §三 M4。
- 陷阱：`_validate_field_value` 的抽取要动 `validate_event` 这一最安全攸关的函数，改动面积大而收益与规则 10b 重叠，属"为了显式而增加耦合"。
- 文档可维护性：第三部文件的逐字对照（`plan.md:593-607`）质量高，可机械 `git diff` 核验（A-S3），是亮点。

### DR4 职责边界（Boundary Clarity）— issue

- **[设计级] O5 门禁的 `--active-dir` 责任无人强制。** `plan.md:283` 规定 `--active-dir` "指向治理对象自身的 active 目录"，但机制只做 `read_state(active_dir)`，**没有任何断言把传入目录与 `--plan` 所在对象绑定**。调用方可传任意一个已配置信封的目录（包括无关对象、甚至共享目录）静默通过门禁——不打印 WARN，也不留差异证据。门禁的"保证"弱于其散文表述。详见 §三 M6。
- Track 边界：Track-1/Track-2 共享 `state-schema.md` 但不相邻段落、共享测试文件的声明清楚（`plan.md:330-336`），第三部允许性说明完整。此处基本无问题。
- `resolve_events` 的职责（"谁负责 resolve"）在 `validate_event_graph`/`validate_ledger`/`project_manifest`/`capture` 四处分散，缺少一张"read raw vs read effective"的总表（`plan.md:242-245` 只覆盖 `project_manifest` 内部），是 DR1 问题的边界版。

### DR5 残留与冗余（Residue & Redundancy）— issue

- **[设计级] 见 DR3 的规则 10/10b 双份枚举**（`plan.md:195` + `:232`）。删除谓词表后，`validate_event` 仍是唯一权威，规则 10b 自动覆盖。
- 迁移考古：`plan.md:16-17`、`:32-36`、`:44-47`、`:66-67`、`:79` 有大量"candidate-1 曾称…""修正 candidate-2…"叙述。对一份**计划**而言属可接受的过程留痕（计划是转瞬产物），但其中一部分（如 `plan.md:66-67` 的"本次核验删除…"）描述"过去发生了什么"而非"现在是什么"，属设计审查 prompt 点名的迁移考古形态（Minor，不列 must-fix）。
- `plan.md:147` 的 `CLOSED = CORRECTION_CLOSED_FIELDS` 双名（同上 Minor）。

### DR6 可移植性（Portability）— pass

- 未硬编码环境特定路径/用户名/IP；`correction-*` 码与 `FAIL_CLOSED:governance_requires_task_envelope` 均 ASCII；新 gate 复用既有 `read_state`/`FailClosed`，不引入 OS 假设。`plan.md:533`/`:563` 的 Windows 8.3 短路径事实是既有测试环境问题，非本设计引入。无问题。

### DR7 可扩展性（Scalability）— pass

- `resolve_events` 为纯函数 + 浅拷贝，`validate_corrections` 对 `(target,field)` 唯一性约束天然有界；更正事件随事件流线性增长，对数百事件量级无压力。规模化风险主要是 DR3 的双份枚举随 `validate_event` 演化而漂移，已计入 M4。无独立问题。

---

## 二、关键设计决策的独立评价

### 决策 A：单层有效视图（`resolve_events`）+ in-band 事件

**方向正确，是该问题域的最小可行结构。** 三项硬约束（check 不再因旧值失败 / manifest 哈希可复算 / 既有归档零字节差异）确实要求"raw 字节不变、语义视图可派生"，而 in-band `event-correction` 比 sidecar 覆盖文件更能保持 append-only 与单一 owner。**没有更简单的等价设计**能同时满足这三项——这是本计划最值得肯定的架构判断。

但"单层"目前只覆盖校验器与投影，未覆盖 capture 写入前判定，导致同一事实在写入期与归档期两个真相。这不是"更简单设计"问题，是**覆盖不完整**问题（M1）。

### 决策 B：动态白名单 `EVENT_FIELDS[target_type] − CLOSED`

**动机（避免硬编码 5 字段与闭包互斥）正确**，但边界定义过粗：它只排除"身份/顺序"，未处理"出边结构字段"。计划用 `DECISION_REFERENCED`（入边）论证安全，属于**用一半的闭包证明整体的闭包**。多数出边字段会被下游图校验间接挡住（例如 `started_event_id` 因 `invocation-id-duplicate` 实际上没有第二个合法目标），但设计不应依赖"下游恰好挡住"而不声明、不测试（M2）。这也说明"更简单的等价设计"存在：把可更正集切得更窄反而更安全，且不伤立身用例（立身用例更正的是值字段 `reservation_id`）。

### 决策 C：授权绑定 `exists ∧ user-message ∧ seq(corr)>seq(umsg)>seq(target)`

比 N11 修复前强，但**仍缺少"授权内容与本次更正绑定"**：任何一条较早的、语义无关的 `user-message`（如"继续""可以"）都可被引作授权凭据，`reason` 只是自由文本，不与 `user_quote` 交叉校验。对比 `user-decision` 的 `_prepare_terminal_decision` 采用**逐字 quote 匹配**（`capture.py:561-574`），此处明显更弱。更正会改写归档语义，其授权强度不应低于 user-decision。这是超出已收敛 N11 的独立发现（M5）。

### 决策 D：O5 触发谓词 = 含唯一 gov 机器块（不绑 `review_mode`/`fsm.mode`）

**评价：正确。** 与既有 `cmd_preflight` 的 gov-block 机制同源（`budget_gate.py:1762-1777`），避免"声明性 mode"与"机器解析"两套集合不一致。无需改动。

### 决策 E：门禁失败语义 fail-closed + `--allow-unconfigured-envelope <reason>` opt-out

**fail-closed 方向正确**，且 opt-out 必填 reason、空串即 fail（`plan.md:278`）符合宪法"留逃生舱且真实可用"。但两点设计代价计划未处理：(1) 逃生舱是 `--active-dir` 可任意指向（M6a）；(2) opt-out 无持久披露（M6b）。逃生舱本身合理，问题在审计闭环。

### 决策 F：两 Track(1/2) 合一而非拆对象

**评价：可接受。** 用户已裁决合并；两 Track 代码路径不相交，共享面仅 `state-schema.md` 非相邻段与测试文件，且以"独立红测/独立转绿/独立验收"回应 UV3-16。唯一实质耦合是外层的 Phase 0/6/7，属编排层而非代码层。此决策不构成修订级问题。

### 更简单的等价设计（Occam 备选，独立评价）

1. **校验侧**：删除规则 10 的谓词映射表与 `_validate_field_value` 抽取，只保留"对每个 target 应用全部更正→运行完整 `validate_event`"（现规则 10b）。`validate_event` 在构造上即单源，覆盖类型 + 跨字段 + 闭集，功能等价而少一处枚举、少动最安全攸关函数（M4）。
2. **O5 门禁**：不新增 `--active-dir`，直接以 `plan.parent` 作为对象 active 目录读取 state。这消除"目录可任意指向"的旁路，且**不需要迁移 `TestGovernancePreflight` 的 21 处调用形态**（测试只需在临时 plan 同目录建 state）——比现方案更简单且更强。若坚持显式 flag，则至少校验 `active_dir == plan.parent`（M6a）。
3. **授权**：把更正授权绑定到 `user_quote` 内容（要求 quote 含目标 event_id 或 reason 为其子串），复用 `user-decision-source` 已有的逐字匹配哲学（M5）。

---

## 三、必须在实施前修正的设计级问题清单

> 每条给**单选修法**（不提供多选题，避免把设计决策转嫁实施者）。M1–M3 为设计缺陷，M4 为安全敏感区的冗余/漂移，M5–M6 为门禁与授权闭环，均为修订级。

**M1（有效视图覆盖不完整：capture 写入前判定仍读 raw）**
- 问题：`capture._prepare_terminal_decision`（`capture.py:523-575`）以 raw `existing` 派生 `presented_degradations`、执行 reviewer authority 检查；`capture._read_existing` 的 continue-parent 查找同样读 raw。计划只把 `validate_event_graph`/`validate_ledger`/`project_manifest` 纳入有效视图（`plan.md:238-247`）。后果：一条在 target 之后、decision 之前、更正了 `invocation-started.role` 或 `invocation-terminal.evidence_level`（二者均在 `allowed()` 放行集内）的 `event-correction`，会让写入期派生（raw）与归档期重派生（effective）不一致 → 产生 `user-decision-degradations` / `decision-reviewer-authority` 这类**计划自身定义为"永久 fail-closed、不可修复"**的失败。
- 单选修法：把"唯一语义读取点"提升为**写入期与归档期共用同一 `resolve_events`**——`_prepare_terminal_decision` 与 continue-parent 查找在入口对 `existing` 先 resolve 再派生/判定，raw 仅用于身份、字节、哈希读取；并在 Acceptance 增加"更正先于 decision 时 capture 与 archive 结论一致"用例。

**M2（动态白名单未定义/未测试"出边结构字段"边界）**
- 问题：`allowed()`（`plan.md:144-153`）只排除 `{event_id,sequence,event_type,schema_id,schema_version}`，放行 target 事件自身的出边引用字段；计划的闭包论证只覆盖 `DECISION_REFERENCED`（入边），§11 对抗清单亦无一条覆盖出边字段更正。
- 单选修法：在 `CORRECTION_CLOSED_FIELDS` 之外再声明一个最小结构引用集 `{invocation-terminal.started_event_id, invocation-started.parent_event_id, design-review-completion.invocation_event_id}` 一律不可更正（保留立身用例所需的值字段 `reservation_id`），并为三者各加一条"拒绝 + `correction-field-not-allowed`"对抗用例。

**M3（更正自身无修复/取代路径）**
- 问题：规则 3 + 规则 7 使一条 `corrected_value` 语义写错的更正在有效视图中永久生效、不可再更正、无 supersede。
- 单选修法：把规则 7 改为"后更正取代先更正的 effective 值"语义——允许对同一 `(target, field)` 追加第二条更正，其 `original_value` 必须等于**当前 effective 值**（而非 raw 值），每条仍需独立授权；raw 日志保持 append-only，披露列出全部更正及其取代关系。

**M4（规则 10 谓词表与规则 10b 重复 → 维护漂移陷阱）**
- 问题：`plan.md:195-231` 的映射表与 `_validate_field_value` 抽取，与 `plan.md:232` 的"候选有效事件跑完整 `validate_event`"功能重叠，且"未列出即拒绝"会在 `validate_event` 新增字段时静默缩小可更正面。
- 单选修法：删除规则 10 的字段映射表与 `_validate_field_value` 抽取，仅保留规则 10b 的"应用全部更正后运行完整 `validate_event`"作为唯一值/跨字段谓词来源；`original_value` 的 raw 逐字相等校验保留。

**M5（更正授权缺少内容绑定）**
- 问题：`authorized_by_user_message_event_id` 只校验存在、类型、时序（`plan.md:164-165`、`:236`），不校验被引 `user-message` 的 `user_quote` 是否真的授权本次更正；任意较早的无关用户消息可作凭据。
- 单选修法：要求 `authorized_by` 所指 `user-message` 的 `user_quote` 必须包含 `corrected_event_id`（或包含本次更正 `reason` 的逐字子串），复用 `capture._prepare_terminal_decision` 对 `user-decision-source` 的逐字匹配语义；不满足即 `correction-unauthorized`。

**M6（O5 门禁的旁路与审计闭环）**
- 问题：`--active-dir` 可指向任意已配置目录，门禁不校验其与 `--plan` 的对象归属（`plan.md:283` 只是散文约束）；opt-out 的可见性只有瞬态 stdout WARN，无持久披露。
- 单选修法（合并一条）：**以 `plan.parent` 作为对象 active 目录读取 state，取消 `--active-dir` 参数**（同时消除旁路、删除 A2-5 类负例、免去 21 处 helper 迁移），并把 opt-out reason 持久写入对象 `_budget-state.json`（或 gate-ledger）而非仅打印 WARN，使 opt-out 与 `--declare-orphan-reservation` 一样留下可复核痕迹。

---

## 四、highlights（最值得肯定 / 最值得警惕）

1. **最值得肯定：以 in-band append-only 事件 + 派生有效视图满足"不改历史字节却可语义更正"三项硬约束。** 这是该问题域的最小结构，且 `corrections`/INDEX 段 omit-when-empty 使既有归档零字节差异，跨对象回归（A1-10）设计到位。方向没有更简单的替代。
2. **最值得警惕：有效视图只覆盖校验器与投影，未覆盖 capture 写入前判定，会在写入期与归档期制造"两个真相"。** 后果不是普通 bug，而是计划自己定义的"永久 fail-closed、追加无法修复"类失败（M1）——这正是 `model.py:1012-1029`、`capture.py:523-541` 反复用注释消除的缺陷类别，本设计又把它从新入口引了回来。
3. **最值得警惕：更正的闭包只保护"被 decision 引用的事件"，不保护 target 事件自身的出边结构字段，且无对抗覆盖。** 安全论证用一半闭包证明了整体（M2）。
4. **最值得警惕：一个用于"修复记录错误"的机制自身没有修复路径。** 写错的 `corrected_value` 永久生效（M3），与 D1 的立身动机直接矛盾。
5. **最值得肯定但也最易漂移：规则 10 的显式字段谓词表。** 它让"哪些字段可更正"一目了然，值得肯定；但正因它是第二份手工枚举，会随 `validate_event` 演化静默失效，应当删除、交由规则 10b 的单一 `validate_event` 承担（M4）。
