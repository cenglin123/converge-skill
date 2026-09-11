---
round: 2
verdict: 阻断需修复
reviewer_backend: fresh-independent
review_scope: plan.md (17,936 B) vs. HEAD code
generated_at: 2026-09-12
---

# Round 2 · fresh 独立评议

首行 verdict：**阻断需修复**。

---

## 前置自检（逐项）

1. **产物身份自洽**：通过 — 标题「子计划 A · 工具与纪律硬化（O2+O4+O7）」与 Goal / D1-D3 / Exact File Matrix / Acceptance 指向同一问题，未见"声称做 A 实际做 B"。
2. **产物边界诚实**：通过（附保留）— `refs/orchestrator-guide.md` / `refs/state-schema.md` 两行已改为"不修改（若需要则升级）"，并有硬升级闸门（plan:26）。但 D3 把 `ingest-verdict` 纳入声明门，与 `refs/orchestrator-guide.md:248` 的既有规范指令正面冲突（见 B5），边界并非全闭合。
3. **产物数据纯度**：通过 — 纯机制类计划，无业务数据、无环境硬编码。
4. **职责边界自洽**：部分通过 — D2 已把 `orchest._finish_step1_missing` 明确纳入复用（plan:72、File Matrix plan:94、Phase 2 plan:110），single-source 方向 orchest→budget_gate 成立（orchest.py:77 已 `import budget_gate`；budget_gate.py 无 `import orchest`，无循环）。但 D3 的适配器注入点枚举不完整（见 B7），`cmd_reserve` 的声明门相对 `--companion-for` 分支的位置未定义。
5. **命名一致性**：不通过 — 计划 5 处使用 `validate_ledger` 指代 `budget_gate.py:903-907`，但该函数不存在；`budget_gate.py` 的不变量校验函数名是 `validate_integrity`（`budget_gate.py:843`），而 `validate_ledger` 实际定义在 `archive_contract/model.py:594`（见 B8）。这与计划"改用符号名"（plan:32）的自我承诺矛盾。默认策略一致性已修复（plan:51 vs plan:134 均为 metadata-only，B4(b) 收口）。
6. **事实核验**：基本通过 — 逐条打开文件核对，除下列项外行号全部准确：
   - plan:42/71/72/120 `validate_ledger` 符号错误（B8）。
   - plan:84 称 `[manual-fallback]` 是 `refs/state-schema.md §二` 惯例；实测 `refs/state-schema.md` 全文 0 处 `manual-fallback`，§二（state-schema.md:133-162）只定义 Round attempt entry schema（S2）。
   - plan:24 称 guide:231/232 为"既有建议句"；实测 guide:232 是禁令式规范句（"**不得手跑裸 budget_gate.py reserve/settle 序列**"）（S3）。
   - 其余（orchest.py:392/492/576/628/759/999-1010/1465-1470/1535/1766/1789/1820-1828；budget_gate.py:133-137/139/533-543/896-897/903-907/1018/1040-1042；ocsr_spawn_adapter.py:441/480/538/733-734；converge_loop.py:331-333/453-477）全部与当前 HEAD 一致。
7. **验收可判定**：不通过 — Acceptance 第 4 条"全量测试绿；`git diff` 范围限于本计划授权文件"在 D3 现存形态下不可同时满足（B6）；Acceptance 第 3 条"取消预约后该轮号被重用"以绝对句表述，但仅在纯骨架删除路径成立（S4）。

---

## 逐条问题

### B5 · architectural · 阻断 — D3 的 `ingest-verdict` 声明门与治理文档既有规范句冲突

**事实证据**
- `plan.md:80`：「`budget_gate` 的记账变更子命令 `reserve` / `settle` / `ingest-verdict` 在 CLI 入口要求**恰好一个**来源声明」。
- `refs/orchestrator-guide.md:248`（原文）：「5. **ingest-verdict**：reviewer 输出落盘后，`budget_gate.py ingest-verdict --target-round N --verdict <可执行|阻断需修复|需重新设计> [--severities ...] [--mode ...]`，驱动 mode 记录与边际递减判定。」
- `CONSTITUTION.md:72` 将 `refs/orchestrator-guide.md` 列为第三部治理文档；`CONSTITUTION.md:94` 规定其修改须走 ultraverge。
- 对照：`refs/orchestrator-guide.md:232` 已有「**不得手跑裸 budget_gate.py reserve/settle 序列**」——故 `reserve`/`settle` 的门禁是对既有禁令的脚本化执行，**不需**改 refs；唯一冲突源是 `ingest-verdict`。

**影响**
D3 一旦对 `ingest-verdict` 强制声明，guide:248 的规范性指令（直调 `budget_gate.py ingest-verdict`）就会 fail-closed，该句必须被改写（触及第三部）或删除。计划却宣称"D3 只做脚本机制、不改任何 `refs/*` 规范句"（plan:24、78）。因此 B1 的收窄对 `ingest-verdict` 并未成立：要么继续执行会必然触发计划自己的升级闸门（plan:26、108、112 的 Phase 0/4），使"standard-review 可执行"落空；要么在错误评议模式下静默改治理文档。

**建议（单选，不并列）**
把 `ingest-verdict` 从 D3 的声明门集合中移除，D3 只覆盖 `reserve` / `settle`。保留的这两条已有 `refs/orchestrator-guide.md:232` 的既有禁令作为规范依据，`--manual-fallback` 则是 `SKILL.md:215` 既有 `[manual-fallback]` 义务的脚本化执行——二者均无需新增/修改第三部规范句，收窄合法。若作者坚持 gate `ingest-verdict`，则 B1 升级分支成立，本计划必须先转 ultraverge。

---

### B6 · implementation · 阻断 — D3 的 `settle` 声明门会打断未列入 File Matrix 的测试文件，使 Acceptance 第 4 条不可满足

**事实证据**
- `tests/test_loop_a_coverage.py:263`：`rc, out, err = run_gate("settle", "--active-dir", str(self.active), "--reservation-id", rid_exe, "--result", "succeeded", "--instance-id", "inst-exe-1")`。
- `tests/test_loop_a_coverage.py:800`：`[sys.executable, str(GATE), "settle", "--active-dir", str(self.active), "--reservation-id", rid, "--result", "cancelled", "--pre-execution"]`。
- `plan.md:100-104` 的 Exact File Matrix 测试行只列 `test_budget_gate.py` / `test_orchest.py` / `test_ocsr_spawn_adapter.py` / `test_converge_loop.py` / `test_process_controller_contract.py`，**不含** `tests/test_loop_a_coverage.py`。
- `plan.md:121` Acceptance：「全量测试绿；`git diff` 范围限于本计划授权文件」。

**影响**
D3 实现后，上述两处裸 `settle` 调用（无 `--orchest-managed` / `--manual-fallback`）会 `FAIL_CLOSED:naked_state_transition`，全量测试变红；要修就得改一个未授权文件。两条 Acceptance 互斥。

**建议（单选）**
将 `tests/test_loop_a_coverage.py` 加入 Exact File Matrix 的 D3 测试行，并在 Phase 1 明确其 `run_gate("settle")` / 直接 subprocess settle 处注入合法声明（模拟手工路径时用 `--manual-fallback <reason>`）；同时在矩阵备注里声明"任何直调 gate 记账命令的既有测试须同步补声明"的扫描步骤。

---

### B7 · implementation · 阻断 — D3 的 ocsr 适配器注入点不完整，遗漏 `_ensure_te_companion`

**事实证据**
- `scripts/ocsr_spawn_adapter.py:296-299`：`args = ["reserve", "--active-dir", str(active_dir), "--role", "task-envelope", "--tier", tier, "--companion-for", role_reservation_id]`，经 `_run_cli(gate_script, args)` 直调 `budget_gate reserve`。
- `plan.md:81` 只声明 `ocsr_spawn_adapter.py`（`_gate_reserve` / settle 调用）内部注入；`plan.md:95` File Matrix 对适配器也只写"D3：注入 `--orchest-managed`"，未列 `_ensure_te_companion`。
- `budget_gate.py:1012-1013`：`cmd_reserve` 首先 `if getattr(args, 'companion_for', None): return cmd_companion_for(args)`——声明门若置于该分支之后，`--companion-for` 路径即成为漏网点；若置于之前，上述 `_ensure_te_companion` 调用会 fail-closed。

**影响**
D3 对 companion 预约的覆盖不确定：要么该路径无门的"裸转移"仍可直调，要么适配器 happy-path 在创建 companion 时被拒。两种结果都与 O7 目标相悖或造成回归。

**建议（单选）**
在计划中把 `_ensure_te_companion` 的 `reserve --companion-for` 调用一并列入 D3 注入点（与 `_gate_reserve` / `_gate_settle` 同级），并显式规定 `cmd_reserve` 的声明门置于 `cmd_companion_for` 分派**之前**，使 companion 路径同受 `--orchest-managed` 约束。

---

### B8 · implementation · 阻断 — 核心不变量函数名 `validate_ledger` 不存在于 `budget_gate.py`

**事实证据**
- `plan.md:42`：「`validate_ledger` 在 `:903-907` 对 `CONTIGUOUS_SCOPES`（`:139`）判 `round_gap`」；同处符号出现在 `plan.md:71`、`plan.md:72`、`plan.md:120`。
- 实测 `budget_gate.py` 无 `def validate_ledger`；`:903-907` 的连续编号检查位于 `def validate_integrity`（`budget_gate.py:843`）。
- `validate_ledger` 实际定义在 `scripts/archive_contract/model.py:594`。
- 计划自述（plan:32、attempts.md:60）"全部行号改用符号名并校准为当前文件"。

**影响**
执行者按符号名检索时，`budget_gate.py` 内查无此函数，而 `archive_contract/model.py` 恰有一个同名函数——存在误改归档契约模块（且该模块的改动会放大治理风险）的实质风险；同时 D2 的"两处一致"验收（plan:120）指向一个不存在的符号，可判定性受损。

**建议（单选）**
把 plan:42/71/72/120 的 `validate_ledger` 全部改为 `validate_integrity`（并保留连续编号段的 `budget_gate.py:903-907` 行号），与 plan:69 已正确使用的 `validate_integrity`（`:1018`）保持一致。

---

### S1 · wording — `converge_loop.py` 的 evidence-mode 来源未选定（"或"并列）

**事实证据**：`plan.md:58`：「从 loop-spec（`spec` 键或既有 meta 通道）读缺省，注入 `reserve-round --evidence-mode` 与 `register-round --evidence-mode`」。
**影响**：违反本仓库"不得以未选定的并列方案交付给 executor"的纪律；`meta` 通道（`converge_loop.py:515-519`）语义是 ocsr `--meta` KV，用它承载 evidence-mode 属职责倒置。
**建议**：选定单一来源——在 loop-spec 顶层新增 `evidence_mode`（默认 `metadata-only`，取值校验 `archive_contract.model.EVIDENCE_MODES`），由 `Driver.reserve`/`Driver.register` 透传；`validate_spec`（`converge_loop.py:178`）对未知顶层键不报错（`FORBIDDEN_SPEC_KEYS` 仅禁轮号，`converge_loop.py:49`），故无需改 spec 版本语义。

### S2 · wording — `[manual-fallback]` 的规范出处引用错误

**事实证据**：`plan.md:84` 称与 `refs/state-schema.md §二既有 attempts 的 [manual-fallback] 标注惯例一致`；`refs/state-schema.md` 全文 0 处 `manual-fallback`，§二（state-schema.md:133-162）只定义 Round attempt entry 字段格式。真正出处为 `SKILL.md:215`。
**影响**：本项的单一权威被错指，后续若有人据 §二 校验会在格式上误导。
**建议**：将出处改引 `SKILL.md:215`，并声明本机制的规范性归属被显式移出（与 plan:127 Non-Goals 一致）。

### S3 · wording — 对 `orchestrator-guide.md` 既有句强度的描述失真

**事实证据**：`plan.md:24` 称把"spawn 经 orchest""从既有建议句升级为强制句"；`refs/orchestrator-guide.md:231-232` 已是强制句——`:231` "**每次 spawn 经 orchest.py（收敛循环内）**"、`:232` "**不得手跑裸 budget_gate.py reserve/settle 序列**"。
**影响**：把"执行既有规范"误述为"新增规范"，反而削弱收窄论证的清晰度。
**建议**：改写为"D3 的 reserve/settle 部分是对 guide:231/232 既有强制禁令的脚本化执行，不存在新增规范句"，以巩固 standard-review 的合法性（并与 B5 的 ingest-verdict 例外并列言明）。

### S4 · wording — "取消后重用轮号"未限定骨架状态

**事实证据**：`plan.md:74` / `plan.md:120` 以绝对句断言取消后下一预约重用被取消轮号。但 `orchest._cancel_skeleton`（`orchest.py:291-295`）仅在 reservation 匹配、无 `reviewer_instance_id`、正文逐字等于 `SKELETON_BODY` 时删除；否则保留并标注 `status: cancelled`（`:296-300`），此时 `round-N.md` 已计入 realized，下一轮号为 N+1，不重用 N。
**影响**：D2 回归若用"已写入实质内容"的取消做 fixture，会误判。
**建议**：将验收句限定为"`pre_execution` / 纯骨架删除路径下，被取消轮号被重用"。

### S5 · architectural（待人工判断）— finish 崩溃恢复的 evidence-mode 由调用方声明，而非继承 started 事件

**事实证据**：`plan.md:55` 让 `finish --evidence-mode` 默认 metadata-only，material/终局轮由调用方显式传 `exact`。而 invocation-started 事件本身已记录原始 `prompt_evidence.evidence_mode`，`orchest._validate_material_gate` 正是读它做判定（`orchest.py:1224-1230`）。
**影响**：若调用方在 finish 恢复时忘记传 `exact`，会写出与 started 记录不一致的 metadata-only terminal，material gate 随后跳过/拒绝该候选（非静默通过，但产生一次新的官方路径摩擦）。
**建议（单选）**：finish 步骤 3 恢复的 `--evidence-mode` 默认继承对应 invocation-started 的 `prompt_evidence.evidence_mode`；`--evidence-mode` 仍保留为显式覆盖。是否采纳留待人工判断。

---

## 确认闭合项清单（B1-B4）

- **B1（治理边界）— no（部分闭合）**。D2 与 D3-reserve/settle 的收窄成立：D3-reserve/settle 只是 `refs/orchestrator-guide.md:232` 既有禁令的脚本化执行，`--manual-fallback` 是 `SKILL.md:215` 既有义务的脚本化执行，不需改第三部文件。但 D3 把 `ingest-verdict` 纳入（plan:80），与 `refs/orchestrator-guide.md:248` 直调指令冲突，需改治理文档或删除该项（B5）。收窄未覆盖 `ingest-verdict`，故 B1 未完全闭合。
- **B2（两处一致）— yes**。`plan.md:72` 明确 `validate_ledger`（应为 `validate_integrity`）与 `orchest._finish_step1_missing` 复用 `budget_gate.contiguous_missing`，single source 落在 `budget_gate.py`；Exact File Matrix 的 `scripts/orchest.py` 行已含 D2（plan:94），Phase 2 亦含（plan:110），Acceptance 第 3 条含两处一致（plan:120）。调用方向无环：`orchest.py:77` import budget_gate，budget_gate 不 import orchest。回归测试已列（plan:74）。符号名缺陷不改变闭合结论，由 B8 处理。
- **B3（轮号机制）— yes（附 S4 限定）**。`plan.md:62-74` 选定唯一方案（target_round 钉到 `next_contiguous_round`），`plan.md:41-45` 废弃旧诊断；`validate_integrity` 的 FS 连续性检查原样保留，不放松"忘写 round-N.md"；不改 ledger 事件/字段（plan:73）；`cancelled` 跳过 `double_target`（budget_gate.py:896-897、1040-1042）与新钉定自洽——pre_execution cancelled 若为纯骨架会被 `_cancel_skeleton` 删除（orchest.py:291-295），realized 不变，下一预约重用同号。唯一缺口是 S4 的绝对句表述。
- **B4（D1 闭合）— yes**。默认策略在 decision 与 Risks 两处统一为 metadata-only（plan:51 vs plan:134）；`orchest.py:1535` finish 崩溃恢复点被点名并纳入方案（plan:55），且给 `finish` 新增 `--evidence-mode`；`_reserve_continue`（orchest.py:392）与 dry-run 展示串（orchest.py:576）均收口（plan:53-54）；`reserve-round`/`register-round` CLI 行号（1766/1789）与 `ocsr_spawn_adapter.py` 透传（441/480/538/733-734）、`converge_loop.py` 未传（453-477）均核实准确。残留为 S5 的"调用方声明 vs 继承"选择。

---

## 未决 / 待人工判断项

1. **D3 是否保留 `ingest-verdict`**（B5）：这是"是否触发 ultraverge"的分水岭，须由作者定夺；本轮建议移除该项以维持 standard-review。
2. **finish 恢复模式来源**（S5）：调用方显式声明 vs 继承 started 事件——属设计取舍。
3. **`tests/test_loop_a_coverage.py` 的修改授权**（B6）：需确认将其纳入本计划授权文件范围。
4. **`--companion-for` 路径是否纳入 D3 声明门**（B7）：影响 te-companion 的 happy-path 是否回归。

---

## 结尾：是否建议升级 ultraverge

**否。**

理由：B1 的残余冲突（B5）可通过**计划内收窄**解决——把 `ingest-verdict` 从 D3 的声明门移出。D3 剩余的 `reserve`/`settle` 部分是对 `refs/orchestrator-guide.md:232` 既有强制禁令与 `SKILL.md:215` 既有 `[manual-fallback]` 义务的脚本化执行，不需要新增或修改 `CONSTITUTION.md` 第三部清单内文件的规范句，因此 standard-review 合法。B6/B7/B8 均为计划完备性与事实校准问题，修订计划即可，不构成修宪需求。仅当作者拒绝移除 `ingest-verdict`、坚持对其强制声明时，才因必然触及 `refs/orchestrator-guide.md:248` 而升级 ultraverge。
