---
round: 5
verdict: 可执行
reviewer_backend: fresh-independent
review_scope: plan.md (46,380 B, SHA-256 9c7bf4bbdf51b153ce5ff725f06e5087d8cda91cf5fb5d3389016825e08bf420) vs. HEAD 529e691 工作树
generated_at: 2026-09-12
reviewer_instance_id: 20260912_002710_27f8c7
---

# Round 5 · fresh 独立评议

首行 verdict：**可执行**。

> 说明：本轮 fresh、与 plan 作者及 R1–R4 reviewer 无共享上下文。所有行号/符号均已实际打开 HEAD（`529e691`）工作树逐条核对，不接受"看起来改好了"。本轮**独立重扫**了 `tests/` 与 `scripts/` 全部 `budget_gate reserve/settle/ingest-verdict/summary` 直调点与 `orchest reserve-round/register-round/finish` 调用点，与计划附录 A 逐条比对：**穷举无误、无计划未列的受打断点**。R4 阻断 N1 三项（i/ii/iii）与 N2/N3/N4 全部闭合；未发现新矛盾；Acceptance 条条可机械判定；收窄仍不触碰 `CONSTITUTION.md` 第三部规范句。

---

## 一、前置自检（逐项）

1. **产物身份自洽：通过** — 标题「子计划 A · 工具与纪律硬化（O2 + O4 + O7）」与 Goal、D1/D2/D3、Exact File Matrix、Phase、Acceptance、附录 A 指向同一问题；D1↔O2、D2↔O4、D3↔O7 映射一致，无"声称做 A 实际做 B"。
2. **产物边界诚实：通过** — `refs/orchestrator-guide.md` / `refs/state-schema.md` 在 File Matrix 中保持"不修改（若需要则升级）"（plan:110-111），硬升级闸门在 plan:29；`ingest-verdict` 已移出声明门（plan:26/:87/:151）；外部驱动器适配说明在 plan:98（P4 已闭合）。附录 A.5 显式标出 out-of-repo fixture 的不可机械保证项（plan:271），非静默略过。
3. **产物数据纯度：通过** — 纯机制类计划，无业务数据、无环境硬编码。
4. **职责边界自洽：通过** — D2 single-source 方向 orchest → budget_gate 成立（`orchest.py:77` 已 `import budget_gate`，`budget_gate.py` 不 import orchest，实核无环）；D1 收敛点（`orchest.py:392`/`:576`/`:1535`/`:1766`/`:1789`）、D3 注入点（`orchest.py:143 _gate`、adapter `:83`/`:97`/`:264`）枚举完整。
5. **命名一致性：通过** — 计划内不变量函数统一为 `budget_gate.validate_integrity`（`budget_gate.py:843`）；归档契约同名函数以全限定名 `archive_contract.model.validate_ledger`（`archive_contract/model.py:594`）消歧（plan:80）。实核 `budget_gate.py` 无 `def validate_ledger`。
6. **事实核验：通过** — 逐条打开 HEAD 文件核对，plan 内全部文件:行引用准确（见附录 A 逐项实核）；新符号 `next_contiguous_round`/`contiguous_missing`/`FAIL_CLOSED:naked_state_transition`/`target_round_drift`/`EXIT_USAGE` 均为待实现新符号，非对现有代码的误引。
7. **验收可判定：通过** — 见第五节。

---

## 二、独立扫描结果表（本轮最关键）

> 方法：独立执行 plan 附录 A.0 的 grep/rg 命令，并**另以** `run_gate|_run_gate|run_cli\(GATE|str\(GATE\)|budget_gate\.cmd_|_gate\(|_run_cli\(gate_script` 等模式交叉复扫 `tests/`+`scripts/` 全量 `*.py`，逐条实开文件核对角色/scope/`target_round`/产物/`attempts.md`。判定三类机制：**D2 漂移门**（`consumes ∈ CONTIGUOUS_SCOPES={outer,blind}`（`budget_gate.py:139`）且 `target_round ≥ 2` 且不满足 `target_round == next_contiguous_round`）；**D3 声明门**（裸直调 `reserve`/`settle`，非经 `orchest`/adapter 注入）；**D3 finish 降级**（finish 前同一 active 的 `attempts.md` 含 `[manual-fallback]`）。

### 2.1 `scripts/` 侧记账调用点（经编排 → 注入 `--orchest-managed`）

| 文件:行 | 命令 | 机制 | 是否受影响 | 与计划表一致 |
|---|---|---|---|---|
| `orchest.py:143`（`_gate` 定义） | 通用 | D3 门 | 注入点 | ✅ 一致（A.1:186） |
| `orchest.py:196/200`（`_settle_te_companion_for_continue`） | `settle` | D3 门 | 是（经 `_gate`） | ✅ 一致（A.1:187） |
| `orchest.py:612`（`cmd_reserve_round`） | `reserve` | D3 门 / D2（官方连续） | 是（经 `_gate`） | ✅ 一致（A.1:188） |
| `orchest.py:719`（register 崩溃窗口） | `settle` | D3 门 | 是 | ✅ 一致（A.1:189） |
| `orchest.py:771`（register 主路径） | `settle` | D3 门 | 是 | ✅ 一致（A.1:190） |
| `orchest.py:845`（cancel 崩溃窗口） | `settle` | D3 门 | 是 | ✅ 一致（A.1:191） |
| `orchest.py:881`（cancel 主路径） | `settle` | D3 门 | 是 | ✅ 一致（A.1:192） |
| `orchest.py:972`（`cmd_record_verdict`） | `ingest-verdict` | — | 否（B5 移出） | ✅ 一致（A.1:193） |
| `ocsr_spawn_adapter.py:86`（`_gate_reserve`） | `reserve` | D3 门 | 是 | ✅ 一致（A.1:194） |
| `ocsr_spawn_adapter.py:100`（`_gate_settle`） | `settle` | D3 门 | 是 | ✅ 一致（A.1:195） |
| `ocsr_spawn_adapter.py:296`（`_ensure_te_companion`） | `reserve --companion-for` | D3 门 | 是（须门前置） | ✅ 一致（A.1:196） |
| `ocsr_spawn_adapter.py:406`（summary 调用）/`:764`（parser） | `summary` | — | 否 | ✅ 一致（A.1:197） |
| `converge_loop.py:456`（`Driver.reserve`） | `reserve-round`（经 orchest） | D2/D3 | 否：`next_round`（`:331-333`）推导恒等；D3 由 orchest 注入 | ✅ 一致（A.1:198） |
| `converge_loop.py:471`（`Driver.register`） | `register-round` | — | 否 | ✅ 一致（A.1:199） |
| `converge_loop.py:480`（`Driver.cancel`） | `cancel-round` | — | 否 | ✅ 一致（A.1:200） |
| `converge_loop.py:496`（`Driver.finish`） | `finish` | D3 降级 | 否：官方路径无 `[manual-fallback]` | ✅ 一致（A.1:201） |
| `hooks/kimi_pretooluse_shim.py` | 仅 `hook-pretooluse`（`BUDGET_GATE:103`） | — | 否 | ✅ 一致（A.1:202） |
| `hooks/stale-check.py` | 只读 import（`:292`） | — | 否 | ✅ 一致（A.1:203） |
| `distill_antipatterns.py` | 无记账调用 | — | 否 | ✅ 一致（A.1:204） |

**独立交叉复扫结论**：全 `scripts/` 树中会写 gate ledger 的路径只有 `orchest._gate`（`reserve`/`settle`）与 adapter 三 helper（`reserve`/`settle`/`reserve --companion-for`）；adapter 的 `_run_cli(gate_script,…)` 仅出现在 `:91`/`:108`/`:299`/`:406`，无遗漏。另有 1 处**进程内** `budget_gate.append_ledger`（`orchest.py:424`，`_reserve_continue` 的 task-envelope companion）——它不经 `budget_gate` CLI，属 orchest 官方路径内部写入，**不在 D3 CLI 声明门定义域内**，非"手工裸转移"；计划未列它属正确（它是 orchest-managed，而非 `budget_gate reserve` 直调）。见第四节非阻断观察 O3。

### 2.2 `tests/` 侧直调记账子命令（D3 声明门适用）

| 文件:行 | 命令 | 是否受影响 | 与计划表一致 |
|---|---|---|---|
| `test_budget_gate.py:40`（helper `reserve`） | `reserve` | 是（D3） | ✅ 一致（A.2:210） |
| `test_budget_gate.py:47`（helper `settle`） | `settle` | 是（D3） | ✅ 一致（A.2:211） |
| `test_budget_gate.py:715` | `reserve`（executor，`target-round -1`） | 是（D3；D2 否，consumes=none） | ✅ 一致（A.2:212） |
| `test_budget_gate.py:2015`（`_companion_for`） | `reserve --companion-for` | 是（D3；D2 否） | ✅ 一致（A.2:213） |
| `test_budget_gate.py:233/:243/:304/:309/:312/:883` | `ingest-verdict` | 否（B5） | ✅ 一致（A.2:214） |
| `test_budget_gate.py:741/:1903/:1928` | `summary` | 否 | ✅ 一致（A.2:215） |
| `test_converge_loop.py:1064`（`_run_gate`） | `reserve`（outer，target 1） | 是（D3；D2 否） | ✅ 一致（A.2:216） |
| `test_converge_loop.py:1079`（helper 定义） | — | 不改 | ✅ 一致（A.2:217） |
| `test_ocsr_spawn_adapter.py:446/:723/:835/:846/:882` | `reserve`（executor/te；`:846` 为 `--companion-for`） | 是（D3；D2 否） | ✅ 一致（A.2:218/220） |
| `test_ocsr_spawn_adapter.py:737` | `settle` | 是（D3） | ✅ 一致（A.2:219） |
| `test_ocsr_spawn_adapter.py:421` | `summary` | 否 | ✅ 一致（A.2:221） |
| `test_loop_a_coverage.py:263`（`run_gate("settle")`） | `settle` | 是（D3） | ✅ 一致（A.2:222） |
| `test_loop_a_coverage.py:800`（subprocess） | `settle` | 是（D3） | ✅ 一致（A.2:223） |
| `test_loop_a_coverage.py:745/:772` | `summary` | 否 | ✅ 一致（A.2:224） |
| `test_orchest.py:413`（`run_cli(GATE,"settle")`） | `settle` | 是（D3） | ✅ 一致（A.2:225） |

**独立交叉复扫结论**：以下文件经实核**不含**任何直调 `reserve`/`settle`/`ingest-verdict`（故不列入 A.2 属正确）：`test_continue_extension.py`（仅 `reserve-round`，含 `--continue-of` 与 round 1）、`test_archive_convergence.py`（仅 import `SCOPE_PRODUCT`/读 ledger）、`test_kimi_pretooluse_shim.py`（仅 `hook-pretooluse` + mock gate）、`test_process_controller_contract.py`、`test_distill_antipatterns.py`。**未发现任何计划未列的直调点**。

### 2.3 D2 漂移门逐调用点判定（`CONTIGUOUS_SCOPES` 且 `target_round ≥ 2`）

| 文件:行 | 角色/scope | target_round | 是否受影响 | 与计划表一致 |
|---|---|---|---|---|
| `test_budget_gate.py:90`（`test_outer_boundary`） | outer | 2 | **是**（realized 空） | ✅ 一致（A.3:231） |
| `test_budget_gate.py:92`（同上） | outer | 3 | **是** | ✅ 一致（A.3:232） |
| `test_budget_gate.py:102`（`test_failed_releases_scope`） | outer | 2 | **是** | ✅ 一致（A.3:233） |
| `test_budget_gate.py:112`（`test_realized_dedup`） | outer | 2 | 否（`:110` 已落 `round-1.md`） | ✅ 一致（A.3:234） |
| `test_budget_gate.py:236`（`test_impl_streak_triggers_mode_switch`） | outer | 3 | **是** | ✅ 一致（A.3:235） |
| `test_budget_gate.py:246`（`test_structural_streak_no_switch`） | outer | 3 | **是** | ✅ 一致（A.3:236） |
| `test_budget_gate.py:275`（`test_duplicate_reservation_id_blocked`） | outer | 2 | 否（重复 rid `:1037-1038` 先于漂移门） | ✅ 一致（A.3:237） |
| `test_budget_gate.py:299`（`test_round_gap_fail_closed`） | outer | 4 | 否（`validate_integrity:1018` 先抛 `round_gap:outer`） | ✅ 一致（A.3:238） |
| `test_budget_gate.py:354/:373`（畸形 reserved 注入） | outer | 2 | 否（`validate_integrity` 先失败） | ✅ 一致（A.3:239） |
| `test_orchest.py:376`（`completed_round(1)` 后） | outer | 2 | 否（`round-1.md` 已存在） | ✅ 一致（A.3:240） |
| `test_orchest.py:412`/`:435`（`completed_round(1)` 后） | outer | 2 | 否（`round-1.md` 已存在） | ✅ 一致（A.3:241） |
| `test_orchest.py:754`（`:746` 已 register r1） | outer | 2 | 否（`round-1.md` 已存在） | ✅ 一致（A.3:242） |
| `test_loop_a_coverage.py:655`（reopen 后） | outer | 2 | 否（`round-1.md` 随 reopen 回迁） | ✅ 一致（A.3:243） |
| `test_loop_a_coverage.py:1032`（`:1029` 已 reserve r1） | outer | 2 | 否 | ✅ 一致（A.3:244） |
| `test_loop_a_coverage.py:1248`（`:1210` 已 reserve r1） | outer | 2 | 否 | ✅ 一致（A.3:245） |
| `test_loop_a_coverage.py:1250`（`:1212` blind r1） | blind | 2 | 否（`blind-recheck-1.md` 已存在） | ✅ 一致（A.3:246） |
| `converge_loop.py:456`（driver） | outer/blind | 由 `next_round` 推导 | 否（恒等于 `next_contiguous_round`） | ✅ 一致（A.3:247） |

**独立核对补充**（我额外穷举了 `test_budget_gate.py` 全部 `reserve(...,rnd>=2)` 与 `test_*` 全部 `reserve-round` 调用）：`test_budget_gate.py` 中 `rnd>=2` 的点仅上表所列 10 处；`test_budget_gate.py` **不存在** outer/blind 无 `--target-round` 的直调（已 grep 确认）；`test_continue_extension.py` 的 3 处 `reserve-round` 全为 `--continue-of`（`_reserve_continue` 无 gate reserve，`orchest.py:322`）或 round 1。**D2 受影响既有测试点=4 条用例/5 个调用点，无计划外新增。**

### 2.4 D3 finish 降级逐 `finish` 调用点判定（同一 active 是否有 `[manual-fallback]`）

| 文件:行 | `[manual-fallback]` 来源 | 是否受影响 | 与计划表一致 |
|---|---|---|---|
| `test_orchest.py:425`（dry-run） | `:413` 直调 settle（补声明） | **是**（1 条） | ✅ 一致（A.4:255） |
| `test_orchest.py:438`（real） | `:413` | **是**（1 条） | ✅ 一致（A.4:256） |
| `test_orchest.py:348/:363/:384/:461/:463/:590/:802` | 官方 reserve/register/cancel | 否 | ✅ 一致（A.4:257） |
| `test_orchest.py:625/:663`（out-of-repo fixture） | 外部 fixture | 否（实核 0 条 `[manual-fallback]`） | ✅ 一致（A.4:258） |
| `test_loop_a_coverage.py:275`（首次） | `:263` 直调 settle（补声明） | 否（扫描在步骤 3 后；步骤 3 先 fail） | ✅ 一致（A.4:259） |
| `test_loop_a_coverage.py:289`（恢复后） | `:263`，但 `:283-284` 已覆写 attempts.md | 否 | ✅ 一致（A.4:260） |
| `test_loop_a_coverage.py` 其余 finish（`:210/:248/:447/:457/:476/:524/:565/:610/:630/:665/:698/:724/:827/:913/:949/:980/:1080/:1107/:1167/:1297/:1359/:1413/:1425`） | 官方 reserve/register | 否 | ✅ 一致（A.4:261） |
| `test_continue_extension.py:114/:166`、`test_converge_loop.py` driver finish、`test_orchest.py:819`（`_finish_step6` 单测非 `orchest finish`） | 官方路径 | 否 | ✅ 一致（A.4:262） |
| `test_budget_gate.py` / `test_ocsr_spawn_adapter.py` | 无 `orchest finish`（rg 命中 0） | 否 | ✅ 一致（A.4:263） |

**独立核对补充**：全仓 `orchest finish` 调用点已穷举；产生 `[manual-fallback]` 的测试文件仅 `test_budget_gate.py`/`test_ocsr_spawn_adapter.py`/`test_converge_loop.py`/`test_loop_a_coverage.py`/`test_orchest.py`，其中前两者**无** `orchest finish`，`test_converge_loop.py:1064` 所在 TestCase（`TestDriverNoDoubleCount`）**无** finish，`test_loop_a_coverage.py:800` 所在 TestCase（`TestCrashRecovery`）**无** finish。故 finish 降级受影响点=2，与计划一致。**out-of-repo fixture 实核**：`FIXTURE_REL=.meta/converge/done/20260815-embeddings-cleanup`，本机 `D:/OneDrive/Cr/Obsidian_Vault/...` 存在，其 `attempts.md` `[manual-fallback]` 计数=0，计划 A.5 记录准确。

### 2.5 扫描总判定

- **D2 受影响 = 4 条用例 / 5 个调用点**（`test_outer_boundary`、`test_failed_releases_scope`、`test_impl_streak_triggers_mode_switch`、`test_structural_streak_no_switch`），全部在授权文件 `tests/test_budget_gate.py` 内。
- **D3 声明门受影响 = §2.1 + §2.2 全部直调 `reserve`/`settle`**，全部在授权文件内；`ingest-verdict`/`summary` 不设门。
- **D3 finish 降级受影响 = `tests/test_orchest.py:425`/`:438`**，均在授权文件内。
- **范围外点：无**。**计划未列而会被打断的点：0**（逐条比对无差异）。

---

## 三、N1–N4 确认清单

| 项 | 是否闭合 | 证据 |
|---|---|---|
| **N1-(i)** `:425`/`:438` 补 `--acknowledge-manual-fallback` + DEGRADED 断言 | **yes** | plan:113（File Matrix 显式枚举两条调用形如 `self.finish(FINAL_VERDICT, "--dry-run", "--acknowledge-manual-fallback")` / `self.finish(FINAL_VERDICT, "--acknowledge-manual-fallback")`，并断言 `DEGRADED:manual-fallback=1`）；plan:135（Phase 4）；plan:142（Acceptance 第 2 条）。实核 `test_orchest.py:405-452`：`:413` settle→`:425`/`:438` finish，`:426`/`:439` `assertEqual(rc,0)`，仅两条需补。✅ |
| **N1-(ii)** 扫描置于 step 3 之后、归档之前 | **yes** | plan:95 写死"`orchest.py:1547` 步骤 3 循环末之后、`:1549` 步骤 3.5 之前"，archive 步骤 7 `:1656-1662` 之后；plan:142 同步。实核 `orchest.py:1496-1547` 为 step 3 循环（`:1523-1525` 为"产物无法解析"早退），`:1549` 为 step 3.5。故 `test_loop_a_coverage.py:275` 先在 step 3 fail（`:277-278` 断言保持），`:289` 因 `:283-284` 覆写 attempts.md 不触发降级。✅ |
| **N1-(iii)** `--dry-run` 语义写死 | **yes** | plan:96 明确"扫描在 `--dry-run` 下同样生效"，插入点位于 dry-run 早退分支（`:1628`）之前，dry-run 下同样打印 `DEGRADED` 且缺确认时非零退出；扫描只读，dry-run 零写入不变量不受影响。plan:97 新增 `--acknowledge-manual-fallback`（finish parser `:1820-1828`）。✅ |
| **N2** `EXIT_USAGE` 新常量 | **yes** | plan:91 改为"新常量 `EXIT_USAGE = 2`（加入 `budget_gate.py` 退出码区 `:46-56`）"。实核 `budget_gate.py:46-56` 现无 `EXIT_USAGE`，现有 `FAIL_CLOSED=30` 等三档；新常量不与现有取值冲突。✅ |
| **N3** `finish --evidence-mode` 缺省哨兵 | **yes** | plan:58 明写 `default=None`（哨兵），并注明不得沿用 `reserve-round`/`register-round` 的 `default="metadata-only"`。实核 `orchest.py:1766`/`:1789` 为 `default="metadata-only"`，`:1820-1828` 无 finish evidence-mode。✅ |
| **N4** `:2015` 措辞更正 | **yes** | plan:112 改为"既有直调 `reserve` helper（`:40`）、`settle` helper（`:47`）、`:715`、`_companion_for`（`:2015`，内部 `run("reserve", "--companion-for", …)`，非 `reserve`/`settle` helper）"。实核 `test_budget_gate.py:2014-2017`。✅ |

---

## 四、非阻断观察（均为 wording/实现精度，不构成阻断）

- **O1 · wording · 计数措辞不一致**：plan:249 结论写"仅 `tests/test_budget_gate.py` 的 5 条用例"，而 A.5（plan:269）写"D2 = 4 条用例…共 5 个调用点"。实为 **4 条用例 / 5 个调用点**。建议统一为"4 条用例（5 个调用点）"。不影响执行。
- **O2 · wording · attempts.md 缺失时创建语义未明写**：D3 声明门在 `--manual-fallback` 时"追加 bullet 到 attempts.md"；`tests/test_budget_gate.py` 的直调 helper 在全新临时目录（无 attempts.md）上调用。实现须以 append 模式创建文件（Python `open(...,'a')` 天然创建），否则这些用例会因写披露失败而红。建议在 Phase 4 一句话写死"attempts.md 不存在时创建"。属实现细节，不阻断。
- **O3 · 边界说明 · `orchest.py:424` 进程内 append**：`_reserve_continue` 直接 `budget_gate.append_ledger` 写 task-envelope companion（绕过 `budget_gate` CLI，故不受 D3 声明门覆盖）。它是 orchest 官方路径内部写入，**不是**"手工裸转移"，计划未列它属正确。建议 Phase 1 扫描时在 attempts.md 一句话记录该边界，避免后续将"未覆盖"误读为漏网。不阻断。

---

## 五、Acceptance 可机械判定性

1. **D1**：`finish --evidence-mode default=None` + 缺省继承 started 的 `prompt_evidence.evidence_mode`（读侧同源 `orchest.py:1224-1230`）→ 可由 `test_orchest.py` 的 finish 恢复用例 + 静态检查（按函数/调用点锚定，负例排除 dry-run 展示串与读侧默认值）机械判定。✅
2. **D3**：精确字符串 `FAIL_CLOSED:naked_state_transition`（零 ledger 写入）、`DEGRADED:manual-fallback=N`、`--acknowledge-manual-fallback`、扫描位置（step 3 后/step 3.5 前/归档前）与 `--dry-run` 生效；`TestFinishRecoveryCancelledSettle` 两条 finish 带确认后绿且断言 `DEGRADED:manual-fallback=1`；`test_loop_a_coverage.py:275` 仍以"产物无法解析"失败；`ingest-verdict` 不受门禁影响。✅
3. **D2**：`target_round` 恒等 FS 推导的下一连续轮号；纯骨架取消后重用轮号、实质内容取消不重用；缺口判定用 (a) `contiguous_missing` 列表 + (b) `validate_integrity` 抛 `round_gap:{scope}` 且 `_finish_step1_missing` 返回对应文件名单（两段可观测）；5 个既有调用点适配后保持原期望。✅
4. **全量测试绿 + `git diff` 范围 + 独立审计**：机械。✅
5. **未触发升级闸门**：机械（File Matrix `refs/*` 两行为"不修改"）。✅

---

## 六、实施前必须满足的前置条件清单

**无。** 计划当前形态可直接进入实施（Phase 0 升级闸门检查 → Phase 1 扫描 + 红测 → …）。第四节 O1–O3 为非阻断，可在实施中顺带处置。

---

## 七、结尾：是否建议升级 ultraverge

**否。**

理由：
- 收窄仍合法：D3 只做 `budget_gate` `reserve`/`settle` 的脚本化声明门与 `orchest finish` 显式降级，规范依据是既有 `refs/orchestrator-guide.md:232`（"不得手跑裸 budget_gate.py reserve/settle 序列"，实核为强制句）与 `SKILL.md:215`（`[manual-fallback]` 既有义务，实核命中）；`refs/orchestrator-guide.md` / `refs/state-schema.md` 在 File Matrix 中仍为"不修改（若需要则升级）"，不新增/不修改 `CONSTITUTION.md` 第三部清单内文件的规范句。`scripts/README.md` 不在第三部清单（`CONSTITUTION.md:65-78`），可自由更新。
- D1/D2 不触归档契约事件/字段，不新增 ledger 事件类型；D2 single-source 落在 `budget_gate.py`，方向无环。
- 穷举性已独立验证、N1–N4 全部闭合、行号/符号逐条实核准确、Acceptance 可机械判定 → 依判定纪律给 **可执行**。

---

## 附录 A · 本轮实核的文件:行清单（全部命中）

- `scripts/budget_gate.py`：`:46-56`（退出码，无 `EXIT_USAGE`）、`:97-139`（`ROLE_CONSUMES`/`SCOPE_PRODUCT`/`CONTIGUOUS_SCOPES`）、`:266/:396/:414`（write_state）、`:533-567`（realized/pending/effective_usage）、`:843`（`validate_integrity`）、`:896-897`（cancelled 跳过 double_target）、`:903-907`（round_gap 只抛异常）、`:979-992`（`mode_switch_required`）、`:1006-1140`（`cmd_reserve` 入口/companion 分派 `:1012-1013`/`canonical_round :1030-1033`/duplicate rid `:1037-1038`/double_target `:1040-1042`/预算裁决 `:1044-1073`/MODE_SWITCH `:1075-1079`）、`:1167-1211`（`cmd_settle`/Lock `:1171`）、`:1214-1275`（`cmd_companion_for`）、`:2011-2028`（reserve/settle parser）。
- `scripts/orchest.py`：`:77`（import budget_gate）、`:143`（`_gate`）、`:181-203`（`_settle_te_companion_for_continue`，settle 于 `:196/200`）、`:282-300`（`_cancel_skeleton`）、`:311-314`（`_started_of`）、`:317-444`（`_reserve_continue`；begin `:392`；append `:424`）、`:447-508`（`_register_continue`；complete 透传 `:492`）、`:548-665`（`cmd_reserve_round`；dry-run 写死 `:576`；resume `:586-610`；else `:611-616`；begin 透传 `:628`；骨架 `:648-658`；app 在 `:612`）、`:672-787`（`cmd_register_round`；settle `:719`/`:771`）、`:845`/`:881`（cancel settle）、`:947-978`（record-verdict→ingest-verdict `:972`，无门）、`:999-1010`（`_finish_step1_missing`）、`:1120-1233`（material gate；`:1224-1230`）、`:1440-1672`（`cmd_finish`；step1 `:1465-1470`；step3 `:1496-1547`（`:1523-1525` 早退、`:1535` 硬编码）；step3.5 `:1549`；dry-run 早退 `:1628`；archive `:1656-1662`）、`:1747-1793`（reserve/register CLI；`:1766`/`:1789`）、`:1820-1828`（finish parser）、`:1846-1848`（`FAIL_CLOSED`→30）。
- `scripts/ocsr_spawn_adapter.py`：`:59-65`（`_run_cli`）、`:83-94`（`_gate_reserve`，调用 `:91`）、`:97-109`（`_gate_settle`，调用 `:108`）、`:115-158`（begin/complete evidence-mode 透传）、`:264-305`（`_ensure_te_companion`，`:296-299`）、`:401-406`（summary）、`:441/:480/:538`（evidence_mode 透传）、`:657`（selftest 固定 metadata-only）、`:733-734`（CLI default）、`:764`（summary parser）。
- `scripts/converge_loop.py`：`:49`（`FORBIDDEN_SPEC_KEYS`）、`:178-199`（`validate_spec`）、`:331-333`（`next_round`）、`:453-468`（`Driver.reserve`）、`:470-477`（`Driver.register`）、`:479-484`（`Driver.cancel`）、`:495-503`（`Driver.finish`）、`:506-522`（dispatch；meta `:515-519`）。
- `scripts/archive_contract/model.py`：`:27`（`EVIDENCE_MODES`）、`:109`（`canonical_round`）、`:594`（`validate_ledger`）。
- `tests/test_budget_gate.py`：`:40`、`:47`、`:85-94`、`:96-103`、`:105-113`、`:146`、`:230-247`、`:270-300`、`:336-375`、`:409-424`、`:440-444`、`:699-717`、`:741`、`:1903/:1928`、`:1993-2039`、`:2015`。
- `tests/test_orchest.py`：`:113-174`（OrchestBase；settle helper `:159-161`、finish helper `:163-167`）、`:342-355`、`:360-368`、`:373-400`、`:405-452`（`:413`/`:425`/`:438`）、`:456-465`、`:545-606`、`:611-679`（`:625`/`:663`）、`:684-776`（`:754`）、`:781-805`（`:802`）、`:808-937`（`:819`）。
- `tests/test_ocsr_spawn_adapter.py`：`:49-54`（run_gate）、`:421`、`:445-452`、`:717-742`、`:828-902`（`:835`/`:846`/`:882`）。
- `tests/test_converge_loop.py`：`:1052-1085`（`:1064`；`_run_gate :1079`）。
- `tests/test_loop_a_coverage.py`：`:42-45`（run_gate）、`:104-144`（helpers）、`:257-291`（`:263`/`:275`/`:283-289`）、`:739-806`（`:745`/`:772`/`:800`）、`:1010-1072`、`:1196-1269`（`:1248`/`:1250`）。
- `tests/test_continue_extension.py`：`:44-56`、`:58-116`（`:52`/`:114`）、`:156-168`（`:166`）、`:202-246`（`:208`/`:237`）。
- 治理文档：`CONSTITUTION.md:63-96`；`refs/orchestrator-guide.md:229/231/232/248/530-540`；`SKILL.md:215`；`refs/state-schema.md`（全文 0 处 `manual-fallback`）。
- out-of-repo fixture（只读核）：`D:/OneDrive/Cr/Obsidian_Vault/.meta/converge/done/20260815-embeddings-cleanup/attempts.md`（`[manual-fallback]` 计数=0）。
terminal_decision_event_id: 2351cbed-c2d5-49d9-8ac8-1073a5a86191
terminal_decision_value: 可执行
