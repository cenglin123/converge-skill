---
round: 4
verdict: 阻断需修复
reviewer_backend: fresh-independent
review_scope: plan.md (30,466 B, SHA-256 360df6861b482b30a297aa0e5c83923e5c7d11a1b45f7984ada0ff6eb4a170a4) vs. HEAD 529e691 工作树
generated_at: 2026-09-12
---

# Round 4 · fresh 独立评议

首行 verdict：**阻断需修复**。

> 说明：本轮 fresh、与 plan 作者及 R1/R2/R3 reviewer 无共享上下文。所有行号/符号均已实际打开 HEAD 工作树文件逐条核对（HEAD = `529e691`）。**P1–P4 全部闭合**（P1 的受影响用例经独立 grep 复核，计划枚举**完整无遗漏**）；但 D3 的 `finish` 显式降级机制与"测试侧新增 `--manual-fallback` 声明"之间存在一处计划未枚举的既有测试冲突，会使 Acceptance"全量测试绿"不可机械达成 → 新增 1 条阻断（N1）。另有 3 条非阻断精度项。

---

## 一、前置自检（逐项）

1. **产物身份自洽：通过** — 标题「子计划 A · 工具与纪律硬化（O2+O4+O7）」与 Goal、D1-D3、Exact File Matrix、Phase、Acceptance 指向同一问题；D1/D2/D3 ↔ O2/O4/O7 映射一致，无"声称做 A 实际做 B"。
2. **产物边界诚实：通过** — `refs/orchestrator-guide.md` / `refs/state-schema.md` 两行保持"不修改（若需要则升级）"（plan:106-107），硬升级闸门在 plan:28；`ingest-verdict` 已移出声明门（plan:26/:86）；round-3 P4 要求的外部驱动器适配说明已补入"边界诚实"段（plan:94，引 `refs/orchestrator-guide.md:536` 原文已核）。
3. **产物数据纯度：通过** — 纯机制类计划，无业务数据、无环境硬编码。
4. **职责边界自洽：通过** — D2 single-source 方向 orchest → budget_gate 成立（`orchest.py:77` 已 `import budget_gate`，`budget_gate.py` 无 `import orchest`，无循环）；D1 收敛点、D3 注入点枚举完整（含 `_ensure_te_companion`）。
5. **命名一致性：通过** — 计划内不变量函数统一为 `budget_gate.validate_integrity`；归档契约同名函数以全限定名 `archive_contract.model.validate_ledger` 消歧（plan:79）。`grep validate_ledger plan.md` 仅命中该消歧句。
6. **事实核验：通过** — 逐条打开 HEAD 文件核对，计划内**全部**文件:行引用准确（见附录 A）。新引入符号 `next_contiguous_round`/`contiguous_missing`/`FAIL_CLOSED:naked_state_transition`/`target_round_drift` 均为**待实现**新符号，非对现有代码的误引。
7. **验收可判定：部分不通过** — Acceptance 第 1/3/5 条均可机械判定；但 Acceptance 第 4 条"全量测试绿"在本轮新增的 N1 未处置前不可自动满足（D3 finish 降级会打断 `tests/test_orchest.py::TestFinishRecoveryCancelledSettle` 两条既有用例）。→ 见 N1。

---

## 二、P1–P4 确认清单（逐条实核）

### P1（round-3 唯一阻断 · D2 门禁打断既有测试）— **yes，已闭合**

**结论**：`tests/test_budget_gate.py` 受 D2 漂移门影响的既有用例已被**完整枚举**，更新方式明确、能保住原期望；"全量测试绿"在 D2 维度上可达。我独立复核了全部直调 `budget_gate reserve/settle` 的用例，计划枚举**无遗漏**。

**独立复核方法**：`rg -n 'run("reserve"|run("settle"|"reserve",|"settle",' tests/ scripts/ --glob '*.py'`，并逐条判 scope/round/是否落产物。D2 漂移门只对 `consumes ∈ {outer, blind}`（`budget_gate.py:139` `CONTIGUOUS_SCOPES`）生效，故只需找**直调 gate、scope=outer/blind、`target_round >= 2` 且不落 `round-{n}.md`** 的用例。

**直调 gate 的文件全集（实核）**：
- `tests/test_budget_gate.py`：helper `reserve`(`:40`)/`settle`(`:47`)、`:715`、`:2015`（`_companion_for`）；
- `tests/test_ocsr_spawn_adapter.py`：`:446`/`:723`/`:737`/`:835`/`:846`/`:882`（均为 `executor`(consumes=none) 或 `task-envelope`，**不受 D2 影响**）；
- `tests/test_converge_loop.py`：`:1064`（`outer-reviewer` 但 `target-round 1`，`next_contiguous_round=1`，**不受 D2 影响**）。

**`tests/test_budget_gate.py` 中 outer/blind 且 `rnd>=2` 的全部点（实核）**：`:90/:92`、`:102`、`:112`、`:236/:246`、`:275`、`:299`、`:354`、`:373`。逐条判定：
- 受影响且计划已枚举（5 条）：`test_outer_boundary`(`:85-94`)、`test_failed_releases_scope`(`:96-103`)、`test_duplicate_reservation_id_blocked`(`:270-277`)、`test_impl_streak_triggers_mode_switch`(`:230-238`)、`test_structural_streak_no_switch`(`:240-247`)。
- 不受影响（实核，计划注解准确）：`:112`（`test_realized_dedup` 在 `:110` 已落 `round-1.md`，`next=2`）；`:299`（`test_round_gap_fail_closed` 在 `:297-298` 造出 round-1/round-3 缺口，**先**于漂移门在 `validate_integrity`(`:1018`/`:903-907`) 抛 `round_gap:outer`）；`:354`/`:373`（注入畸形 reserved 事件，同样先在 `validate_integrity` 失败）。

**更新方式核实（数据依赖，非文字承诺）**：
- `test_outer_boundary` plan:118 的算法成立：`:89` 后写 `round-1.md`、`:91` 后写 `round-2.md`；`pending()`(`budget_gate.py:556-561`) 跳过已落盘轮、`realized()`(`:546-547`) 补位，`effective_usage()`(`:566-567`) 不变 → `r2` 仍 `usage 1 < 2` → PROCEED，`r3` 仍 `usage 2 == 2` → `BLOCK:budget_exhausted`。实核 `budget_gate.py:550-567` 与断言一致。
- `test_failed_releases_scope` plan:119 的"改 `rnd=1`、不落产物"正确：`r1` 已 `spawn_failed`，`pending()` 在 `:556` 排除之；不落产物则 `realized=0`，`effective_usage=0 < 1` → PROCEED。若照搬"落 `round-1.md`"会把失败轮计入 `realized` 致 `effective_usage=1` → BLOCK，破坏语义——计划已识别并拒绝该机械照搬，属正确判断。
- `test_duplicate_reservation_id_blocked` plan:120 依赖执行次序 `... → 重复 rid(:1037-1038) → 漂移门 → ...`；实核 `budget_gate.py:1037-1038` 在 `:1040-1042` 之前，计划把漂移门插在其后，`:275` 先返回 `FAIL_CLOSED:duplicate_reservation_id`，**无需改 fixture**，成立。
- `TestModeSwitch` 两条 plan:121 成立：写 `round-1.md`/`round-2.md` 后 `next_contiguous_round==3`；`mode_switch_required` 只读 `state.fsm.severities`（`budget_gate.py:979-992`），不受产物影响，故 MODE_SWITCH / PROCEED 期望不变。

**执行次序明确性**：plan:72 显式列出 `validate_integrity(:1018) → canonical_round(:1030-1033) → 重复 rid(:1036-1038) → 漂移门 → double_target(:1039-1042) → 预算裁决(:1044-1073) → MODE_SWITCH(:1075-1079)`，与实核代码一致。

**官方路径不受影响的交叉验证**：`orchest.cmd_reserve_round` 先 `_gate reserve`(`:612-620`)、**后**创建骨架(`:648-658`)，故第 N 轮预约时 FS 只有 `round-1..N-1`，`next_contiguous_round=N`；官方串行路径的 `target_round` 恒等于 N。`test_orchest`/`test_loop_a_coverage` 中 `reserve-round` 的 `round_no=2` 调用（如 `test_orchest.py:376/:412/:1032`、`test_loop_a_coverage.py:655/:1032/:1247`）均在 `round-1.md` 落盘之后，实核不受漂移门影响。

### P2（round-3 非阻断 · `--resume-reservation` 限定语层错位）— **yes**

plan:71 已删除 `budget_gate` 层的 `--resume-reservation` 限定，改为「resume 路径不经本命令，见 `orchest.py:594-610`；`budget_gate.cmd_reserve` 无 `--resume-reservation` 概念」。实核 `orchest.py:586-610` 为 resume 前置校验体、`:611-616` 为非 resume 的 `else` 分支才调 `_gate reserve`；`budget_gate` parser（`:2011-2019`）确无此 flag。语义已落在 orchest 层，准确。

### P3（round-3 非阻断 · "两处相同缺口集合"不可观测）— **yes**

plan:75-77 已改写为可判定两段式：**(a)** `budget_gate.contiguous_missing(active, scope)` 等于预期整数列表；**(b)** `validate_integrity` 抛 `round_gap:{scope}`、`_finish_step1_missing` 返回与 (a) 对应的文件名单（plan:77 例 `["round-2.md"]`）。实核 `budget_gate.py:903-907` 只 `raise FailClosed(f"round_gap:{scope}")`、`orchest.py:999-1010` 返回文件名单——原"相同集合"确实不可观测，改写后可判定。Acceptance plan:139 同步。**yes**。

### P4（round-3 非阻断 · 外部驱动器兼容性未入边界诚实）— **yes**

plan:94 已补：「外部参考驱动器（`refs/orchestrator-guide.md:536`，实现在 vault 侧、不在本仓库）须同步以 `--manual-fallback <reason>`（或后续对象改走 `orchest`）适配 D3 门禁；此适配属 out-of-repo，不改本计划文件、不触发升级闸门」。实核 guide:536 原文（「预算 gate：`budget_gate.py reserve/settle/summary`……驱动器在每次 `ingest` 时自动调用 reserve」）与 `refs/state-schema.md:454`（"行为一致"被括号限定为 `counts_before`/`ceilings`）——补 flag 不使两句为假，不触第三部。**yes**。

### B5–B8 / S1–S5（round-2）复核

经本轮抽查：`ingest-verdict` 全计划无残留设门表述（plan:26/:86/:101/:102/:108/:115/:138/:147）；`validate_integrity` 消歧保留（plan:79）；`[manual-fallback]` 出处 `SKILL.md:215`（实核命中）；`_ensure_te_companion` 与"声明门在 `cmd_companion_for` 分派之前"保留（plan:87，实核 `budget_gate.py:1012-1013` 分派、`:1009` `no_active_dir`）；S5 finish 继承 started 保留（plan:53/:57，实核 started 事件含 `prompt_evidence`：`archive_contract/model.py:183`、`capture.py:349`）。

---

## 三、新发现（阻断）

### N1 · implementation · **阻断** — D3 的 `finish` 显式降级会打断"测试侧新增 `--manual-fallback` 声明"之后的既有 `finish` 成功用例，File Matrix/Phase 未枚举受影响调用点

**事实链（全部实核）**
1. plan:92：「`--manual-fallback` 时，`budget_gate` 追加一条 `[manual-fallback]` bullet 到 `attempts.md`」。
2. plan:93：「`orchest finish` 在归档前扫描 `attempts.md` 的 `[manual-fallback]` 条目；若存在，打印 `DEGRADED:manual-fallback=N` 并要求 `--acknowledge-manual-fallback` 才继续（否则停止）」；Acceptance plan:138 同。
3. plan:109（File Matrix `tests/test_orchest.py` 行）规定「既有直调 settle（`:413`）补 `--manual-fallback <reason>`」。
4. 实核 `tests/test_orchest.py`：
   - `:409-417` `_crash_after_gate_cancel` 在 `:412` `self.reserve(round_no=2)`（官方路径）后于 `:413` **直调** `run_cli(GATE, "settle", ..., "--result", "cancelled", "--pre-execution")`——按 3 会补 `--manual-fallback`，从而在 `self.active/attempts.md` 落一条 `[manual-fallback]`。
   - `:419-431` `test_finish_dry_run_resolves_pair_without_writes` 在 `:425` `rc, out, err = self.finish(FINAL_VERDICT, "--dry-run")` 后 `:426` **断言 `rc == 0`**。
   - `:433-452` `test_finish_real_recover_writes_explicit_cancelled_terminal` 在 `:438` `rc, out, err = self.finish()` 后 `:439` **断言 `rc == 0`**。
5. 两条用例的 active 目录在 `finish` 前**存在** `attempts.md` 的 `[manual-fallback]` 条目（`OrchestBase.setUp`(`:116-126`) 用全新临时目录；`completed_round(1)` 走官方路径不产生该条目；条目仅由 `:413` 的 `--manual-fallback` 产生）。
6. 因此按 plan:93/:138，`finish` 会输出 `DEGRADED:manual-fallback=1` 并**停止**，两条用例的 `assertEqual(rc, 0)` 必红。plan:109 的「D3 finish 降级与确认」只笼统授权，**未点名** `:425`/`:438` 需补 `--acknowledge-manual-fallback`，也未规定 `finish --dry-run` 下的扫描语义。
7. 同类（潜在，取决于扫描位置）：`tests/test_loop_a_coverage.py:263`（plan:112 规定补 `--manual-fallback`）→ `TestExecutorCrashWindow.test_finish_fails_on_crash_window_then_register_recovers` 在 `:275` 调 `self.finish(...)` 后 `:276-278` **断言 combined 含「产物无法解析」**（即 step 3 失败先于扫描）。若 `finish` 的 manual-fallback 扫描被放在 step 3 **之前**（plan:93 只说"归档前"，未限定在 step 3 之后），`:275` 的 finish 会改为在扫描处停止，`:278` 的 `assertIn("产物无法解析", combined)` 必红。该用例 `:283-284` 会用新内容覆盖 `attempts.md`，故 `:289` 的第二次 finish 不受影响。

**影响**：Acceptance plan:140「全量测试绿」在 D3 维度上不可机械达成；与 round-3 P1（D2 未枚举受影响用例）属同一类完备性缺口，且正落在"测试必须补 `--manual-fallback`"与"finish 必须确认 `[manual-fallback]`"两条新机制的交叉盲区。执行者若 TDD 跑到红，只能自行决定改哪些 finish 调用、扫描放在哪一步（未授权语义）。

**建议（单选）**
在 Exact File Matrix 与 Bounded Sequence Phase 4/Phase 5 中**显式枚举**：(i) `tests/test_orchest.py:425`（dry-run）与 `:438`（real）两条 `finish` 调用补 `--acknowledge-manual-fallback`（并在 `TestFinishRecoveryCancelledSettle` 中显式断言 `DEGRADED:manual-fallback=1` 仍被打印以保留 D3 验收）；(ii) 明确 `orchest finish` 的 manual-fallback 扫描步骤位于 **step 3 之后、归档之前**，以保 `test_loop_a_coverage.py:275-278` 的「产物无法解析」先发生；(iii) 在 plan:93 同步写明 `--dry-run` 下该扫描同样生效（或明确豁免），使 `:425` 的期望可判定。

---

## 四、非阻断精度项

1. **N2 · wording · 非阻断 — `EXIT_USAGE` 不是现有常量**。plan:90「两者同传 → 用法错误（`EXIT_USAGE`，零 ledger 写入）」。实核 `budget_gate.py:46-56` 无 `EXIT_USAGE`（现有：PROCEED=0 / BLOCK 10-15 / MODE_SWITCH=20 / DENY 21-22 / FAIL_CLOSED=30）。建议改为「新常量 `EXIT_USAGE`（或 argparse 互斥组自动 exit 2）」以消歧；属实现细节，不影响机制成立。
2. **N3 · wording · 非阻断 — `finish --evidence-mode` 的缺省值未明写**。plan:57 要求"缺省继承 started、`--evidence-mode` 仅作显式覆盖"，但 plan:57 只写"新增 `--evidence-mode`（choices 同 others）"；若照搬 `reserve-round`/`register-round` 的 `default="metadata-only"`（`orchest.py:1766`/`:1789`），则缺省恒被覆盖、继承失效。建议明写 `default=None`（或哨兵值）。
3. **N4 · wording · 非阻断 — plan:108 把 `:2015` 称作 "reserve/settle helper"**。实核 `tests/test_budget_gate.py:2015` 是 `_companion_for`（内部 `run("reserve", ..., "--companion-for", ...)`），非 `reserve`/`settle` helper；attempts.md:224-229 的扫描表标注准确。仅措辞，不影响执行。

---

## 五、转"可执行"所需的最小修订（前置条件）

按 N1 的单选建议执行后，本计划可转 `可执行`：

1. 在 File Matrix `tests/test_orchest.py` 行与 Phase 4/5 显式枚举 `:425`/`:438` 的 `finish` 调用补 `--acknowledge-manual-fallback`，并写明 `DEGRADED` 断言；
2. 在 plan:93 明确 manual-fallback 扫描位于 finish **step 3 之后、归档之前**（保住 `test_loop_a_coverage.py:275` 期望），并写明 `--dry-run` 语义。

（建议同时按 N2/N3/N4 修正措辞。因当前 verdict=阻断，不列"实施前必须满足的前置条件"清单；上列即所需修订。）

---

## 六、结尾：是否建议升级 ultraverge

**否。**

理由：
- P1 已闭合，P2/P3/P4 均已按 round-3 单选落实且实核准确；N1 是**计划完备性**问题（既有测试适配未枚举），修订计划即可，不构成修宪需求。
- D3 只做 `budget_gate` 的 `reserve`/`settle` 脚本机制，规范依据是 `refs/orchestrator-guide.md:232` 既有强制禁令与 `SKILL.md:215` 既有 `[manual-fallback]` 义务，**不新增/不修改** `CONSTITUTION.md` 第三部清单内文件的规范句；`refs/orchestrator-guide.md` / `refs/state-schema.md` 在 File Matrix 中仍为"不修改（若需要则升级）"。收窄合法。
- N2/N3/N4 为措辞/默认值精度项，不触第三部。仅当作者坚持把 D3 扩回 `ingest-verdict`，或坚持让 D2/D3 必须改写 `refs/*` 规范句才能成立时，才因触及第三部而升级 ultraverge。

---

## 附录 A · 本轮实核的文件:行清单（全部命中）

- `scripts/budget_gate.py`：`:46-56`（退出码，无 `EXIT_USAGE`）、`:133-137`（`SCOPE_PRODUCT`）、`:139`（`CONTIGUOUS_SCOPES`）、`:533-543`（`realized_round_numbers`）、`:546-567`（`realized`/`pending`/`effective_usage`）、`:843`（`validate_integrity`）、`:896-897`（cancelled 跳过 double_target）、`:903-907`（round_gap 只抛异常）、`:979-992`（`mode_switch_required`）、`:1006-1018`（`cmd_reserve` 入口/`no_active_dir`/`validate_integrity`）、`:1012-1013`（companion 分派）、`:1030-1033`（canonical_round）、`:1036-1038`（duplicate rid）、`:1040-1042`（double_target）、`:1044-1073`（预算裁决）、`:1076-1079`（MODE_SWITCH）、`:1167-1171`（`cmd_settle`/`Lock`）、`:1214`（`cmd_companion_for`）、`:2011-2019`（reserve parser，无 resume 概念）。
- `scripts/orchest.py`：`:77`（import budget_gate）、`:143`（`_gate`）、`:196-200`（te companion settle）、`:282-300`（`_cancel_skeleton`）、`:311-314`（`_started_of`）、`:392`（continue begin 硬编码）、`:492`（continue complete 透传）、`:548-665`（`cmd_reserve_round`；`:576` dry-run 写死；`:594-610` resume 校验；`:611-616` else 调 `_gate reserve`；`:648-658` 骨架）、`:672-787`（`cmd_register_round`；`:723`/`:771` settle；`:759` complete 透传）、`:845`/`:881`（cancel settle）、`:947-978`（record-verdict → ingest-verdict，无门）、`:999-1010`（`_finish_step1_missing`）、`:1128-1230`（material gate；`:1224-1227` 读 `prompt_evidence.evidence_mode`）、`:1440-1547`（`cmd_finish`；`:1465-1470` step 1；`:1496-1547` step 3；`:1535` 硬编码）、`:1747-1793`（reserve/register CLI；`:1766`/`:1789` evidence-mode default `metadata-only`）、`:1820-1828`（finish parser，无 `--evidence-mode`）。
- `scripts/ocsr_spawn_adapter.py`：`:83`（`_gate_reserve`）、`:97`（`_gate_settle`）、`:264`（`_ensure_te_companion`）、`:296-299`（`reserve --companion-for`）、`:441`/`:480`/`:538`（evidence_mode 透传）、`:733-734`（CLI default）。
- `scripts/converge_loop.py`：`:49`（`FORBIDDEN_SPEC_KEYS`）、`:178-199`（`validate_spec` 不拒未知顶层键）、`:331-333`（`next_round`）、`:453-468`（`Driver.reserve` 未传 evidence-mode）、`:470-477`（`Driver.register` 未传）、`:515-519`（meta 通道）。
- `scripts/archive_contract/model.py`：`:27`（`EVIDENCE_MODES`）、`:53`（root allowlist 含 `attempts.md`）、`:183`（invocation-started 含 `prompt_evidence`）、`:594`（`validate_ledger`）；`capture.py:349`（started 写 `prompt_evidence`）。
- `tests/test_budget_gate.py`：`:40`、`:47`、`:85-94`、`:96-103`、`:110-113`、`:230-247`、`:270-277`、`:295-300`、`:336-375`、`:715`、`:2015`。
- `tests/test_converge_loop.py`：`:1064`。
- `tests/test_ocsr_spawn_adapter.py`：`:446`/`:723`/`:737`/`:835`/`:846`/`:882`。
- `tests/test_loop_a_coverage.py`：`:120`/`:130`/`:146`（helpers）、`:255-291`（`TestExecutorCrashWindow`，`:263` settle、`:275`/`:289` finish）、`:800`（subprocess settle）、`:995-1003`、`:1032`。
- `tests/test_orchest.py`：`:113-174`（`OrchestBase`）、`:360-368`、`:374-400`、`:405-452`（`TestFinishRecoveryCancelledSettle`，`:413` settle、`:425`/`:438` finish）、`:546-556`、`:684-777`、`:813-829`。
- 治理文档：`CONSTITUTION.md:63-96`；`refs/orchestrator-guide.md:231/:232/:248/:536`；`SKILL.md:215`；`refs/state-schema.md:106/:454`（全文 0 处 `manual-fallback`）。
