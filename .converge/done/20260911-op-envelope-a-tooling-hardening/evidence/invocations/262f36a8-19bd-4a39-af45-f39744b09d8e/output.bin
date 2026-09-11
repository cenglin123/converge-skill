---
round: 3
verdict: 阻断需修复
reviewer_backend: fresh-independent
review_scope: plan.md (25,006 B, SHA-256 前缀 88c17e5fd3ce9a2b) vs. HEAD 529e691 工作树
generated_at: 2026-09-12
---

# Round 3 · fresh 独立评议

首行 verdict：**阻断需修复**。

> 说明：本轮 fresh、与 plan 作者及 R1/R2 reviewer 无共享上下文。所有行号/符号均已实际打开 HEAD 工作树文件核对，不接受"看起来改好了"。B5-B8 与 S1-S5 经实核**全部闭合**；新发现 1 条阻断（D2 门禁层与既有测试冲突，计划未列入 File Matrix）与 3 条非阻断项。

---

## 一、前置自检（逐项）

1. **产物身份自洽：通过** — 标题「子计划 A · 工具与纪律硬化（O2+O4+O7）」与 Goal、D1-D3、Exact File Matrix、Phase、Acceptance 指向同一问题，无"声称做 A 实际做 B"。D1/D2/D3 分别对应 O2/O4/O7，映射一致。
2. **产物边界诚实：通过（附非阻断保留）** — `refs/orchestrator-guide.md` / `refs/state-schema.md` 两行已改"不修改（若需要则升级）"（plan:102-103），并有硬升级闸门（plan:27）。`ingest-verdict` 已移出声明门（见 B5 确认）。保留项：外部参考驱动器直调 `budget_gate reserve/settle` 的路径（guide:536）未进入计划的边界诚实表述（见 P4，非阻断）。
3. **产物数据纯度：通过** — 纯机制类计划，无业务数据、无环境硬编码。
4. **职责边界自洽：通过** — D2 single-source 方向 orchest→budget_gate 成立：`orchest.py:77` 已 `import budget_gate`，`budget_gate.py` 无 `import orchest`，无循环；helper 落在 `budget_gate`（plan:67-69/73）。D1 的收敛点、D3 的注入点枚举完整（见 B7）。
5. **命名一致性：通过** — 计划内不变量函数统一为 `budget_gate.validate_integrity`；归档契约同名函数以全限定名 `archive_contract.model.validate_ledger` 明确消歧（plan:75）。`grep validate_ledger plan.md` 仅命中该消歧句。
6. **事实核验：通过** — 逐条打开 HEAD 文件核对，计划内**全部**文件:行引用准确（见附录 A 逐项实核）。前两轮的行号漂移问题已消除。
7. **验收可判定：部分不通过** — Acceptance 第 3 条"两处给出相同缺口集合"对 `validate_integrity` 不可直接观测（见 P3，非阻断）。**关键**：Acceptance 第 4 条"全量测试绿"在本轮发现的新阻断 P1 未处置前不可自动满足（D2 门禁会打断既有 `tests/test_budget_gate.py` 用例）。

---

## 二、逐条问题

### P1 · implementation · **阻断** — D2 的预约号钉定落在 `budget_gate.cmd_reserve`，会打断既有 `tests/test_budget_gate.py` 用例，而计划未把受影响用例列入 File Matrix

**事实证据**
- 计划选定方案（plan:65、:70）：「**把预约 `target_round` 钉到文件系统推导的"下一个连续轮号"上**」；「`budget_gate.cmd_reserve`：对 `consumes ∈ CONTIGUOUS_SCOPES` 的新预约（**非 `--resume-reservation`**）强制 `target_round == next_contiguous_round(active, scope)`，否则 `FAIL_CLOSED:target_round_drift:<scope>`」。
- helper 定义（plan:68）：「`next_contiguous_round(active, scope)`：`CONTIGUOUS_SCOPES` 的 `max(realized_round_numbers)+1`（**无产物时 1**）」。即只读 `round-{n}.md` 文件系统产物。
- 实核 `budget_gate.cmd_reserve`（`budget_gate.py:1006-1160`）**不创建任何 `round-N.md` 产物**——它只 `append_ledger`（`:1114/:1127`）。产物骨架由 `orchest reserve-round` 创建（`refs/state-schema.md:106`），不在此路径。
- 因此对**直调 `budget_gate reserve`** 的调用者，realized 恒为空（除非测试自己写 `round-N.md`），`next_contiguous_round` 恒为 1；任何 `target_round >= 2` 的预约都会被新门禁拒绝。
- 受影响的既有用例（实核原文）：
  - `tests/test_budget_gate.py:85-94` `TestScopeBudget.test_outer_boundary`：`self.reserve("outer-reviewer","r1",rnd=1)` → PROCEED；`self.reserve("outer-reviewer","r2",rnd=2)`（`:90`）→ 期望 `PROCEED`（注释"usage 1 < 2"）；`self.reserve("outer-reviewer","r3",rnd=3)`（`:92`）→ 期望 `BLOCK:budget_exhausted`。该用例全程不写 `round-*.md`。D2 后 `rnd=2` 得到 `FAIL_CLOSED:target_round_drift:outer`（且 `rnd=3` 是否得到 BLOCK 还取决于新门禁与预算裁决的先后，计划未定义）。**该用例必红**。
  - `tests/test_budget_gate.py:96-103` `test_failed_releases_scope`：`self.settle("r1","failed")` 后 `self.reserve("outer-reviewer","r2",rnd=2)`（`:102`）→ 期望 PROCEED；无产物，D2 后 drift。**必红**。
  - `tests/test_budget_gate.py:270-277` `test_duplicate_reservation_id`：`:273` `rnd=1` 后 `:275` `self.reserve("outer-reviewer","same",rnd=2)` → 期望 `FAIL_CLOSED:duplicate_reservation_id`；无产物，D2 后若新门禁在重复 rid 校验之前则得 drift（门禁次序计划未定义）。**至少语义漂移，大概率红**。
- 计划授权该测试文件（plan:104）但只写「D2 回归（取消后重用轮号、跳号被拒、两处缺口一致）」与「既有直调 reserve/settle helper（`:40/:47/:715/:2015`）补 `--manual-fallback <reason>`」，**未提及上述既有用例会因新门禁改变期望**；Risks（plan:145）仅笼统称"降低回归面"。
- 对照：走 `orchest reserve-round` 的官方路径测试不受影响——`reserve-round` 在 reserve 同时落 round 骨架（`refs/state-schema.md:106`），故 `test_loop_a_coverage.py:151-158`（`outer_round`）、`test_orchest.py:169-174`（`completed_round`）、`test_orchest.py:419-421/433-435` 等 serial reserve 均能连续推进。这反证问题**只**出在"直调 gate 且不落产物"的既有用例上。

**影响**
Phase 2「实现 `budget_gate` 单一权威 helper 与 `cmd_reserve` 钉定……跑 budget/orchest 定向测试至绿」将直接卡死；Acceptance 第 4 条"全量测试绿；`git diff` 范围限于本计划授权文件"在**未列出这些用例**时无法机械达成。执行者面临两种非计划内选择：(a) 自行改写既有预算用例的 setup（属未授权语义的静默变更）；(b) 把门禁挪到 `orchest`（偏离计划明写的"落在 `budget_gate.cmd_reserve`"）。二者都超出计划授予的范围。

**建议（单选）**
在 Exact File Matrix 的 `tests/test_budget_gate.py` 行与 Phase 2 中**显式枚举**受影响的既有用例（至少 `test_outer_boundary`、`test_failed_releases_scope`、`test_duplicate_reservation_id`），并规定其更新方式：在这些用例的连续预约之间写入对应的 `round-N.md` 产物（例如 `:89` 后写 `round-1.md`、`:91` 后写 `round-2.md`），从而让 `next_contiguous_round` 与实际预约号一致，同时保持 `effective_usage` 的预算语义不变（写产物后 `pending()` 跳过已落盘轮，`realized` 补位，`effective_usage` 不变，见 `budget_gate.py:550-567`）。保留门禁在 `budget_gate.cmd_reserve`（维持计划的单一权威与 O4 对手动回退路径的覆盖）。

---

### P2 · wording · 非阻断 — D2 门禁的"非 `--resume-reservation`"限定在 `budget_gate` 层不成立

**事实证据**：计划 plan:70 以「（非 `--resume-reservation`）」限定 `budget_gate.cmd_reserve` 的强制点。但 `--resume-reservation` 是 `orchest reserve-round` 的 CLI 参数（`orchest.py:1764-1765`），其 resume 分支（`orchest.py:594-610`）**根本不调用** `_gate reserve`（只有非 resume 的 `else` 分支在 `:611-616` 才调用）；`budget_gate.cmd_reserve` 无此 flag，也无从感知。
**影响**：限定语会被执行者误读为"要在 budget_gate 增加 resume 概念"。
**建议（单选）**：删除该括号限定，或在括号内改为"（resume 路径不经本命令，见 `orchest.py:594-610`）"，把语义落在 orchest 层。

---

### P3 · wording · 非阻断 — Acceptance"两处给出相同缺口集合"对 `validate_integrity` 不可直接观测

**事实证据**：plan:73/129 要求「回归测试在**同一 fixture** 上断言两处给出相同缺口集合」。但 `budget_gate.validate_integrity` 的缺口分支只 `raise FailClosed(f"round_gap:{scope}")`（`budget_gate.py:903-907`），**不暴露缺口集合**；只有 `orchest._finish_step1_missing`（`orchest.py:999-1010`）返回文件名单。所谓"两处相同集合"在 `validate_integrity` 侧无输出可比。
**影响**：该验收条不可按字面机械判定（前置自检 Q7 部分不通过）。
**建议（单选）**：改写为可判定的两段式——(a) 断言 `budget_gate.contiguous_missing(active, scope)` 在缺口 fixture 上等于预期整数列表；(b) 断言 `validate_integrity` 对同一 fixture 抛 `round_gap:{scope}`、`orchest._finish_step1_missing` 返回与 (a) 对应的文件名单。用"结构同源 + 各自可观测输出"替代不可观测的"相同集合"。

---

### P4 · architectural · 非阻断 — 外部参考驱动器直调 `budget_gate reserve/settle` 的兼容性未进入边界诚实表述（经核实**不**触发 ultraverge）

**事实证据**
- `refs/orchestrator-guide.md:536`：「**预算 gate**：`budget_gate.py reserve/settle/summary`（含 `task-envelope` scope）。驱动器在每次 `ingest` 时自动调用 reserve（幂等），settle 由调用方在 spawn 后执行。」该驱动器实现在 vault 侧、不在本仓库（guide:530-534）。
- D3 声明门（plan:83-86）要求**所有** `reserve`/`settle` 直调恰好带 `--orchest-managed` 或 `--manual-fallback`，否则 fail-closed。`--orchest-managed` 的定义仅覆盖 `orchest.py` 与 `ocsr_spawn_adapter.py`（plan:84）；外部驱动器两者皆非，只能声明 `--manual-fallback`，从而被当作"手工降级"路径对待。
- 计划的"边界诚实"（plan:90）只声明 archive 侧 caller 不可区分，未提该外部驱动器路径。

**影响**：外部驱动器若未同步补声明会 fail-closed（迁移兼容问题）；且把自动化适配层归入 `manual-fallback` 语义属职责错配。**但**经核实这**不构成**对 `CONSTITUTION.md` 第三部规范句的修改：guide:536 描述的是"驱动器调用 reserve/settle"这一事实，附加一个声明 flag 不使其句子为假；`refs/state-schema.md:454`「其它任何角色的 reserve/settle 行为与改造前一致」的括号已把"行为"限定为 `counts_before`/`ceilings` 记账键（D3 不触碰），故亦不被 D3 否定。
**建议（单选）**：在计划的"边界诚实"段补一句：外部参考驱动器（guide:536）必须同步以 `--manual-fallback <reason>`（或在后续对象中改走 `orchest`）适配 D3 门禁；此适配属 out-of-repo，不构成本计划文件改动，也不触发升级闸门。

---

## 三、B5-B8 / S1-S5 确认闭合清单（逐条实核）

### Blocking（R2）

- **B5（`ingest-verdict` 移出 D3 声明门）— yes**
  - 覆盖范围已收窄为 `reserve`/`settle` 两命令：plan:82「声明门只覆盖 `budget_gate` 的 `reserve` / `settle` **两个**记账变更子命令。`ingest-verdict` **已移出**」。
  - 全计划无残留"对 `ingest-verdict` 设门"表述：plan:25/:82/:91/:97/:98/:104/:111/:137 均为"移出 / 不设门 / 不注入 / 不补"。
  - 规范依据为既有句，已核原文：`refs/orchestrator-guide.md:232`「**不得手跑裸 budget_gate.py reserve/settle 序列**」；`SKILL.md:215`「确需绕过时必须在 attempts.md 记录 `[manual-fallback]` 及原因」。`refs/orchestrator-guide.md:248`（ingest-verdict 直调指令）不再被门禁威胁。
  - 计划不再宣称改 `refs/*`：File Matrix 两行（plan:102-103）为"不修改（若需要则升级）"；plan:25「不新增、不修改 `refs/orchestrator-guide.md` / `refs/state-schema.md` 的任何规范句」。
- **B6（`tests/test_loop_a_coverage.py` 入矩阵 + settle 点声明 + 扫描义务）— yes**
  - 已入矩阵：plan:108 新增该文件行，点名 `run_gate("settle")`（`:263`）与直接 subprocess settle（`:800`），并用 `--manual-fallback <reason>`。
  - 实核调用点准确：`tests/test_loop_a_coverage.py:263` 为 `run_gate("settle", ...)`；`:800` 为 `[sys.executable, str(GATE), "settle", ...]`。该文件内**仅**此两处直调 settle（`rg` 实扫：`run_gate(` 仅出现在定义 `:42` 与 `:263`；字符串字面量 settle 仅 `:263/:800`）。
  - 扫描义务可执行：plan:111 规定 Phase 1 grep `scripts/`、`tests/` 中所有直调 `reserve`/`settle`/`ingest-verdict`，逐处决定并写入 attempts.md，发现未授权文件即停止。独立 `rg` 复扫（`scripts/`+`tests/` 全部 `"reserve"|"settle"|"ingest-verdict"` 字面量）与 attempts.md 的扫描表（引用自 `.converge/active/.../attempts.md:207-236`）**逐条一致**，无漏网文件。
- **B7（`_ensure_te_companion` 入 D3 注入点 + 声明门在分派之前）— yes**
  - plan:87 明列 `ocsr_spawn_adapter.py:_ensure_te_companion`（`:264`，其 `reserve --companion-for` 调用在 `:296-299`）与 `_gate_reserve`（`:83`）/`_gate_settle`（`:97`）**同级**，均注入 `--orchest-managed`；File Matrix（plan:99）同步。
  - 位置明确且"必须之前"：plan:87「`reserve` 的声明门置于 `cmd_reserve` 入口、`cmd_companion_for` 分派（`budget_gate.py:1012-1013`）**之前**（建议位置：`:1009` 的 `no_active_dir` 检查之后）……**不得**把声明门放在 `cmd_companion_for` 分派之后」。
  - 实核准确：`budget_gate.py:1006` `cmd_reserve`；`:1008-1009` `no_active_dir`；`:1012-1013` `if getattr(args,'companion_for',None): return cmd_companion_for(args)`；`cmd_companion_for` 定义 `:1214`。
- **B8（`validate_ledger` → `validate_integrity` + 归档函数全限定名）— yes**
  - 计划全部改称 `budget_gate.validate_integrity`（plan:43/:70/:72/:73/:75/:97/:98/:129/:145），行号 `:843`、缺口段 `:903-907` 保留且实核准确。
  - 归档契约同名函数以**全限定名**出现：plan:75「`archive_contract.model.validate_ledger`（`archive_contract/model.py:594`）……本计划不引用、不修改归档契约模块」。实核 `budget_gate.py` 无 `def validate_ledger`；`archive_contract/model.py:594` 为 `def validate_ledger`。

### Suggestions（R2）

- **S1（loop-spec evidence-mode 单一来源）— yes**：plan:59 选定**顶层新键 `evidence_mode`**（默认 `metadata-only`，校验 `archive_contract.model.EVIDENCE_MODES`，`archive_contract/model.py:27`），由 `Driver.reserve`（`:453-468`）/`Driver.register`（`:470-477`）注入；明确"不使用 meta 通道、不复用 `spec` 既有键"。实核 `validate_spec`（`converge_loop.py:178`）不拒未知顶层键（`FORBIDDEN_SPEC_KEYS` 仅 `{round, round_number, target_round}`，`:49`），方案可行。
- **S2（`[manual-fallback]` 出处更正）— yes**：plan:88 改引 `SKILL.md:215`，并声明「`refs/state-schema.md` 全文 0 处 `manual-fallback`，不是该惯例的来源（S2 更正）」。实核 `refs/state-schema.md` `grep -c manual-fallback` = 0。
- **S3（既有句强度描述）— yes**：plan:25 改写为「对 `refs/orchestrator-guide.md:231/232` 既有强制禁令的脚本化执行，不新增规范句」。实核 `:231`「**每次 spawn 经 orchest.py（收敛循环内）**」、`:232`「**不得手跑裸 budget_gate.py reserve/settle 序列**」均为强制句。
- **S4（取消后重用限骨架）— yes**：plan:76「`pre_execution` / 纯骨架删除路径下取消预约后下一次预约必须重用被取消轮号……已写实质内容的取消**不**重用轮号」；Acceptance（plan:129）同步限定并点名 `orchest._cancel_skeleton`。实核 `orchest.py:291-295` 仅在 rid 匹配 + 无 `reviewer_instance_id` + 正文恰为 `SKELETON_BODY` 时 `unlink`，否则 `:296-300` 标注 `status: cancelled` 保留。
- **S5（finish 崩溃恢复继承 started）— yes**：plan:52「唯一例外是 `finish` 步骤 3 崩溃恢复：缺省**继承**该 invocation 的 started 记录」；plan:56「恢复写出点**缺省继承对应 invocation-started 的 `prompt_evidence.evidence_mode`**（经 `orchest._started_of`……与 material gate 判定同源，`orchest.py:1224-1230`），`--evidence-mode` **仅作显式覆盖**」。实核：`orchest._started_of`（`orchest.py:311-314`）按 `invocation_id` 取 `invocation-started`；material gate 同源读 `prompt_evidence`（`orchest.py:1224-1230`）；started 事件确含 `prompt_evidence`（`archive_contract/capture.py:349`、`model.py:183`）。File Matrix/Phase/Acceptance/Risks/README 口径一致。

---

## 四、阻断闭合所需的最小修订（转"可执行"的前置条件）

按 P1 的单选建议执行后，本计划可转 `可执行`：

1. 在 Exact File Matrix 的 `tests/test_budget_gate.py` 行与 Phase 2 中，**显式枚举** `test_outer_boundary`（`:85-94`）、`test_failed_releases_scope`（`:96-103`）、`test_duplicate_reservation_id`（`:270-277`）等既有用例，并写明其更新方式（在连续预约之间落 `round-N.md` 产物，或把不同 target 改为 `next_contiguous_round`），使"全量测试绿"可达。
2. （建议同时）按 P2 修正限定语、按 P3 改写"两处一致"的可判定表述、按 P4 补一句外部驱动器适配说明。

（因当前 verdict=阻断，不列"实施前必须满足的前置条件"清单；上列即所需修订。）

---

## 五、结尾：是否建议升级 ultraverge

**否。**

理由：
- B5 已按 R2 单选把 `ingest-verdict` 移出声明门；D3 剩余的 `reserve`/`settle` 部分确系 `refs/orchestrator-guide.md:232` 既有强制禁令与 `SKILL.md:215` 既有 `[manual-fallback]` 义务的脚本化执行，**不需要新增或修改 `CONSTITUTION.md` 第三部清单内文件的规范句**。
- 本轮新发现的 P1/P2/P3 属计划完备性与事实精度问题，修订计划即可；P4 经原文核实**不**使 guide:536 / state-schema:454 为假（state-schema:454 的"行为一致"被括号限定为记账键），故不构成修宪需求。
- 仅当作者坚持把 D3 扩回 `ingest-verdict`，或坚持让 D2/D3 必须改写 `refs/*` 规范句才能成立时，才因触及第三部而升级 ultraverge（CONSTITUTION:72/:94）。

---

## 附录 A · 本轮实核的文件:行清单（全部命中）

- `scripts/orchest.py`：`:27/:47`（docstring #1/#8）、`:77`（import budget_gate）、`:143`（`_gate`）、`:196`、`:264/:296-299`（adapter，另见下）、`:282-300`（`_cancel_skeleton`）、`:311-314`（`_started_of`）、`:392`、`:492`、`:576`、`:594-616`（resume/else）、`:628`、`:759`、`:771`、`:881`、`:972`、`:999-1010`、`:1224-1230`、`:1226-1227`、`:1465-1470`、`:1535`、`:1764-1765`、`:1766`、`:1789`、`:1820-1828`。
- `scripts/budget_gate.py`：`:133-137`（`SCOPE_PRODUCT`）、`:139`（`CONTIGUOUS_SCOPES`）、`:533-543`（`realized_round_numbers`）、`:550-567`（`pending`/`effective_usage`）、`:843`（`validate_integrity`）、`:896-897`（cancelled 跳过 double_target）、`:903-907`（round_gap）、`:1006-1042`（`cmd_reserve` 入口/companion 分派/duplicate/double_target）、`:1018`、`:1040-1042`、`:1167/:1171`（`cmd_settle`/`Lock`）、`:1214`（`cmd_companion_for`）。
- `scripts/ocsr_spawn_adapter.py`：`:83`、`:97`、`:264`、`:296-299`、`:441`、`:480`、`:538`、`:733-734`。
- `scripts/converge_loop.py`：`:49`、`:178`、`:331-333`、`:453-468`、`:470-477`、`:515-519`。
- `scripts/archive_contract/model.py`：`:27`（`EVIDENCE_MODES`）、`:594`（`validate_ledger`）；`capture.py:349`（started 含 `prompt_evidence`）。
- `tests/test_budget_gate.py`：`:40`、`:47`、`:85-94`、`:96-103`、`:110`、`:233/:243/:304/:309/:312/:715/:883`、`:2015`、`:270-277`、`:297-299`。
- `tests/test_orchest.py`：`:169-174`、`:413`、`:419-421`、`:433-435`。
- `tests/test_ocsr_spawn_adapter.py`：`:446/:723/:737/:835/:846/:882`（调用起始行）。
- `tests/test_converge_loop.py`：`:1064`。
- `tests/test_loop_a_coverage.py`：`:42`、`:151-158`、`:263`、`:800`、`:1029-1033`。
- 治理文档：`CONSTITUTION.md:63-96`；`refs/orchestrator-guide.md:231/:232/:248/:536`；`SKILL.md:215`；`refs/state-schema.md:106/:454`（全文 0 处 `manual-fallback`）。
- 历史证据：`.converge/done/20260910-process-controller-consolidation/attempts.md:202/:207/:211`（reservation `8f7d80e83731` target4→round-3.md、`4bd2541195c7` target5→round-5.md、字面量 `PENDING`）。
