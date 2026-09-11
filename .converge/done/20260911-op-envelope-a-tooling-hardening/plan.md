---
status: draft
created_at: 2026-09-11
review_mode: standard-review
scope:
  - converge-skill
depends_on: []
source_evidence:
  - .converge/done/20260910-process-controller-consolidation/retrospective.md（R2 实施节）
  - .converge/done/20260910-process-controller-consolidation/attempts.md（manual-fallback 条目）
  - .converge/active/20260911-op-envelope-a-tooling-hardening/round-1.md（R1 评议，阻断 B1-B4）
  - .converge/active/20260911-op-envelope-a-tooling-hardening/round-2.md（R2 评议，阻断 B5-B8 + S1-S5）
  - .converge/active/20260911-op-envelope-a-tooling-hardening/round-3.md（R3 评议，阻断 P1 + 非阻断 P2/P3/P4）
  - .converge/active/20260911-op-envelope-a-tooling-hardening/round-4.md（R4 评议，阻断 N1 + 非阻断 N2/N3/N4）
---

# 子计划 A · 工具与纪律硬化（O2 + O4 + O7）

## Goal

消除"官方路径造不出契约要求的证据"这一根因，让编排层不再依赖手工状态转移，并修正预约轮号与产物文件名错位的执行层锐边。判定机制与归档契约事件类型不变。

## 范围与治理边界（收窄决定，回应 B1）

本计划**保留在 `review_mode: standard-review`**，按评议 B1 给出的分支显式收窄，使 D2/D3 不触及 `CONSTITUTION.md` 第三部治理文档：

- **D3（O7）只做脚本机制**：在 `orchest.py` / `budget_gate.py` 层实现"无声明的裸状态转移被拒绝 + 声明的 `[manual-fallback]` 强制披露 + `finish` 归档显式降级"。D3 的 `reserve`/`settle` 部分**是对 `refs/orchestrator-guide.md:231/232` 既有强制禁令的脚本化执行，不新增规范句**：`:231` 已写"**每次 spawn 经 orchest.py（收敛循环内）**"，`:232` 已写"**不得手跑裸 budget_gate.py reserve/settle 序列**"；`--manual-fallback` 的披露依据是 `SKILL.md:215` 既有 `[manual-fallback]` 义务。二者均属执行既有规范，**不新增、不修改 `refs/orchestrator-guide.md` / `refs/state-schema.md` 的任何规范句**。`ingest-verdict` 已按 round-2 B5 从声明门**移出**（其直调是 `refs/orchestrator-guide.md:248` 的既有规范指令，强制声明会 fail-closed 冲突），故 D3 只覆盖 `reserve` / `settle`。D3 的规范性归属（把上述既有强制句升格为 state-schema 契约等）**移出本计划**，见 Non-Goals。
- **D2（O4）不引入新的 ledger 事件类型或 state 字段**，不改归档契约，与 Non-Goals 对齐。
- **升级闸门（硬约束）**：实现过程中若发现 D1/D2/D3 的任一机制**必须新增或修改 `CONSTITUTION.md` 第三部清单内文件（尤其 `refs/orchestrator-guide.md`、`refs/state-schema.md`、`SKILL.md`、`archive_contract` 规范）的规范句**才能成立，则**立即停止本计划、不自行扩范围**，把发现、所需规范句与证据交回 orchestrator，**升级 ultraverge**（CONSTITUTION 第四部：≥3 Reviewer + 收敛 + 设计审查）。"同步文档"不构成扩范围理由。
- 据此，Exact File Matrix 中 `refs/orchestrator-guide.md` / `refs/state-schema.md` 两行为"**不修改（若需要则升级）**"。
- 过程侧：本轮有 1 次派发被误分类，已按"如实记录、不回填"写入 `attempts.md`，不作为本计划实现项（见 Non-Goals）。

## 证据（事实已按当前代码与 r2 账本修正）

- **O2（exact evidence 工具化收口）**：`orchest.py` 仍有 `metadata-only` **硬编码写出点**，透传点已部分就绪。按符号名定位（当前行号仅作辅助）：
  - `_reserve_continue` 内 `begin-invocation` 写出点（`orchest.py:392`）硬编码 `"metadata-only"`——continue 轮无 CLI 覆盖。
  - `cmd_reserve_round` 内 `begin-invocation`（`orchest.py:628`）与 `cmd_register_round` 内 `complete-invocation`（`orchest.py:759`）、`_register_continue` 内 `complete-invocation`（`orchest.py:492`）已用 `getattr(args, "evidence_mode", "metadata-only")` 透传。
  - reserve-round **dry-run 展示串**（`orchest.py:576`）写死显示 `evidence-mode=metadata-only`，与实际参数不联动（仅展示）。
  - **`finish` 步骤 3 崩溃恢复**的 `complete-invocation`（`orchest.py:1535`）硬编码 `"metadata-only"`，且 `finish` 子命令（`orchest.py:1820-1828`）**没有 `--evidence-mode` 参数**——该路径无法经 CLI 声明，是 Acceptance"全部由 CLI 参数驱动"的漏点（评议 B4）。
  - CLI 定义：`reserve-round --evidence-mode`（`orchest.py:1766`，默认 `metadata-only`）、`register-round --evidence-mode`（`orchest.py:1789`，默认 `metadata-only`）。读取侧默认值（`orchest.py:1226-1227`）非写出点。
  - `ocsr_spawn_adapter.py`：已读 `args.evidence_mode`（`:441`）并用于 begin/complete（`:480`/`:538`），CLI 默认 `metadata-only`（`:733-734`）——只剩"默认策略"待文档化。
  - `converge_loop.py`：driver 的 `Driver.reserve`（`:453-468`）与 `Driver.register`（`:470-477`）**都没传 `--evidence-mode`**，实际落在 CLI 默认 `metadata-only`。
- **O7（手工状态转移）**：r2 的 3 次编排错误全部发生在手工状态转移时（cancelled/failed 口径、字面量 `PENDING`、`round-5.md` 命名），见 `done/.../attempts.md:202/207/211`。
- **O4（轮号语义）——原诊断已证伪，按真实机制重述**：
  - 连续编号检查**基于文件系统产物**，不读 ledger：`budget_gate.realized_round_numbers`（`budget_gate.py:533-543`）对 `SCOPE_PRODUCT`（`:133-137`）glob 取号，`budget_gate.validate_integrity`（`budget_gate.py:843`）在 `:903-907` 对 `CONTIGUOUS_SCOPES`（`:139`）判 `round_gap`；`orchest._finish_step1_missing`（`orchest.py:999-1010`，由 finish 步骤 1 `:1465-1470` 调用）是同源重复实现。故 **`cancelled` 不"占号"**。
  - `cancelled` 仅在 `double_target` 判定被跳过（`budget_gate.py:896-897`，及 `cmd_reserve` 的 `:1040-1042`）。
  - r2 的 `round_gap:outer` 真因是**预约 `target_round` 与产物文件名的错位**：成功预约 `target_round` 为 `{1,2,4,5}`（3 为 `pre_execution` cancelled），而产物命名为 `round-1..4`——reservation `8f7d80e83731`（target_round 4 → 产物 `round-3.md`）、reservation `4bd2541195c7`（target_round 5 → reviewer 按预约号写 `round-5.md`，触发 `round_gap:outer`），操作者把 in-flight `round-5.md` 归位为 `round-4.md` 才绕过（`done/.../attempts.md:202/207`）。
  - 因此**"改用成功结算的轮次集合"会更不连续**（`{1,2,4,5}`），且会放松"忘写 `round-N.md`"这一既有不变量（`orchest.py` 模块 docstring `:27`/`:47` 明确该检查防此错）——该拟议修法**废弃**。

## 决策

### D1. exact evidence 工具化收口（O2）

- **默认策略（单处表述，消除 B4 矛盾）**：**默认 `metadata-only`；material / 终局同字节绑定相关的轮由调用方显式传 `--evidence-mode exact`**（同 `scripts/README.md` 现有口径）。唯一例外是 `finish` 步骤 3 崩溃恢复：缺省**继承**该 invocation 的 started 记录（见下第 3 点）。不改变历史归档的只读兼容。
- 清点并收口全部写出点与透传点：
  1. `_reserve_continue` 的 begin 写出点（`orchest.py:392`）：由硬编码改为 `getattr(args, "evidence_mode", "metadata-only")`——continue 轮可能承载 material 复核，需要可声明。
  2. reserve dry-run 展示串（`orchest.py:576`）：改为联动 `args.evidence_mode`，不再显示写死值。
  3. **`finish` 步骤 3 崩溃恢复的 complete-invocation（`orchest.py:1535`）**：给 `finish` 子命令新增 `--evidence-mode`（choices 同 others），**`default=None`（哨兵值；不得沿用 `reserve-round`/`register-round` 的 `default="metadata-only"`，否则缺省恒被覆盖、继承失效——round-4 N3）**；恢复写出点**缺省继承对应 invocation-started 的 `prompt_evidence.evidence_mode`**（经 `orchest._started_of` 从 `invocation-started` 事件读出发起时记录；与 material gate 判定同源，`orchest.py:1224-1230`），`--evidence-mode` **仅作显式覆盖**（采纳 round-2 S5）。material/终局相关的崩溃恢复轮因此默认与 started 记录一致，不再存在"无法经 CLI 声明"或"调用方忘传即降级"的路径。该点在本计划中被**点名并纳入方案**（补漏路径）。
  4. `cmd_reserve_round`/`cmd_register_round`/`_register_continue` 已透传，保持不变（仅纳入静态检查基线）。
  5. `ocsr_spawn_adapter.py` 保持 `args.evidence_mode` 透传；只补默认策略文档与静态检查。
  6. `converge_loop.py`：driver 的 `reserve`/`register` 增加 `evidence_mode` 透传——**单一来源**为 loop-spec **顶层新键 `evidence_mode`**（默认 `metadata-only`，取值校验 `archive_contract.model.EVIDENCE_MODES`，`archive_contract/model.py:27`）；`Driver.reserve`（`:453-468`）/`Driver.register`（`:470-477`）将其注入 `reserve-round --evidence-mode` 与 `register-round --evidence-mode`。**不使用 meta 通道、不复用 `spec` 既有键承载**（`meta` 仅承载 ocsr `--meta` KV，`converge_loop.py:515-519`，用于承载 evidence-mode 属职责倒置）。`validate_spec`（`converge_loop.py:178`）对未知顶层键不报错（`FORBIDDEN_SPEC_KEYS` 仅禁轮号，`converge_loop.py:49`），无需改 spec 版本语义；不改变轮号由 `next_round`（`:331-333`）从 realized 产物推导的语义。
- `scripts/README.md` 单一权威记录默认/必需边界："默认（缺省）`metadata-only`；material / 终局绑定轮**必需** `exact`；`finish` 崩溃恢复缺省继承 started"。
- 防回退静态检查（`tests/test_process_controller_contract.py`）：以**函数 / 调用点**为单位断言"需要 exact 的写出点不得回退为字面量 `metadata-only`"，覆盖 `_reserve_continue` 与 `finish` 恢复点；**负例**：不误伤 reserve dry-run 展示串（已改为联动参数）与读取侧默认值（`orchest.py:1226-1227`），也不误伤 `ocsr_spawn_adapter.py:733` 的 CLI 默认。

### D2. 轮号语义修正（O4）——唯一选定方案

**方案（单选）：把预约 `target_round` 钉到文件系统推导的"下一个连续轮号"上，使预约号恒等于产物号。**

- 在 `budget_gate.py` 新增单一权威 helper：
  - `next_contiguous_round(active, scope)`：`CONTIGUOUS_SCOPES` 的 `max(realized_round_numbers)+1`（无产物时 1）；
  - `contiguous_missing(active, scope) -> list[int]`：既有缺口检测的单一实现。
- `budget_gate.cmd_reserve`：对 `consumes ∈ CONTIGUOUS_SCOPES` 的新预约强制 `target_round == next_contiguous_round(active, scope)`，否则 `FAIL_CLOSED:target_round_drift:<scope>`（零 ledger 写入）。（resume 路径不经本命令，见 `orchest.py:594-610`；`budget_gate.cmd_reserve` 无 `--resume-reservation` 概念。）`cmd_reserve` 进入时已 `validate_integrity`（`:1018`），故此刻产物必连续，判据良定义。
  - **执行次序（同一 `Lock` 内，round-3 P1 要求显式化）**：`validate_integrity`（`:1018`）→ `canonical_round`（`:1030-1033`）→ 重复 `reservation_id` 校验（`:1036-1038`）→ **新增漂移门（本节）** → `double_target`（`:1039-1042`）→ `total`/scope 预算裁决（`:1044-1073`）→ `MODE_SWITCH`（`:1075-1079`）。漂移门排在重复 rid 校验**之后**，故 `TestAdversarial.test_duplicate_reservation_id_blocked`（`tests/test_budget_gate.py:270-277`）的期望仍为 `FAIL_CLOSED:duplicate_reservation_id`。
- **消除错位根因**：一处 `pre_execution` cancelled 不改变 realized，故下一个预约只能重用同一轮号（不会被"烧掉"），预约号与产物号永远一致；r2 的 `target_round 4 → round-3.md` 与 `target_round 5 → round-5.md` 两类命名错位在机制上不再可能。
- **不放松既有不变量**：FS 连续编号检查（`validate_integrity`，`budget_gate.py:903-907`）**原样保留**，仍会拦截"忘写 `round-N.md`"；本方案只是让预约号无法跑到产物号前面，属**加强**耦合。**不得**改动 `realized()/pending()/effective_usage()` 的预算计数语义（`budget_gate.py:533-567`）。
- **两处一致（回应 B2；按 round-3 P3 改写为可判定两段式）**：`budget_gate.validate_integrity`（`budget_gate.py:903-907`）与 `orchest._finish_step1_missing`（`orchest.py:999-1010`）改为复用同一 `budget_gate.contiguous_missing`；调用方向为 **orchest → budget_gate**（orchest 已 import budget_gate），single source = `budget_gate.py`。回归测试在**同一缺口 fixture**（例：有 `round-1.md` 与 `round-3.md`、缺 `round-2.md`）上分两段机械断言，替代不可直接观测的"两处相同集合"：
  - **(a)** `budget_gate.contiguous_missing(active, scope)` 等于预期整数列表（上例 `outer` → `[2]`）；该函数是缺口集合的**唯一可观测权威**。
  - **(b)** 对同一 fixture，`budget_gate.validate_integrity` 抛 `FailClosed("round_gap:{scope}")`（`budget_gate.py:903-907` 分支只抛异常、不暴露集合），且 `orchest._finish_step1_missing` 返回与 (a) 对应的文件名单（`SCOPE_PRODUCT[scope].format(n=n)`，上例 → `["round-2.md"]`）。
- 不改 ledger 事件类型/字段；历史 ledger 不被追溯 fail（强制点在 reserve 命令，不进 `validate_integrity`）。
- **符号消歧（round-2 B8）**：本计划所指不变量函数是 `budget_gate.validate_integrity`（`budget_gate.py:843`）。同名 `validate_ledger` 位于归档契约模块（全限定名 `archive_contract.model.validate_ledger`，`archive_contract/model.py:594`），与本计划的函数**不是同一个**；本计划不引用、不修改归档契约模块。
- 补回归：`pre_execution` / 纯骨架删除路径下取消预约后下一次预约必须重用被取消轮号、后续产物连续且不触发 `round_gap`；已写实质内容的取消**不**重用轮号（保留的 `round-N.md` 计入 realized，下一轮为 N+1）；预约号跳到 realized+2 被拒；缺口判定按上述 (a)/(b) 两段断言（结构同源：`validate_integrity` 与 `_finish_step1_missing` 均复用 `budget_gate.contiguous_missing`）。

### D3. 手工状态转移的机制约束（O7）——已收窄为脚本机制

**单一机制：无声明的裸状态转移被拒绝；有声明者强制披露并在归档时显式降级。**（不新增/修改任何 `refs/*` 规范句。）

- **覆盖范围（round-2 B5 单选）**：声明门只覆盖 `budget_gate` 的 `reserve` / `settle` **两个**记账变更子命令。`ingest-verdict` **已移出**——其直调是 `refs/orchestrator-guide.md:248` 既有规范指令，强制声明会把它 fail-closed，从而必然触及第三部治理文档。保留的 reserve/settle 的规范依据是 `refs/orchestrator-guide.md:232` 既有禁令（"不得手跑裸 budget_gate.py reserve/settle 序列"）+ `SKILL.md:215` 既有 `[manual-fallback]` 义务，**不新增第三部规范句**。
- **声明门（authority = `budget_gate.py` CLI）**：`reserve` / `settle` 在 CLI 入口要求**恰好一个**来源声明：
  - `--orchest-managed`：由 `orchest.py`（`_gate` 对 `reserve`/`settle` 注入）与 `ocsr_spawn_adapter.py`（`_gate_reserve` / `_gate_settle` / `_ensure_te_companion` 注入）内部加注；
  - `--manual-fallback <reason>`：非经上述编排的直调必须显式声明；
  - 两者皆无 → **fail-closed**：打印 `FAIL_CLOSED:naked_state_transition` 并以 `EXIT_FAIL_CLOSED` 退出，**零 ledger 写入**；两者同传 → 用法错误（**新常量 `EXIT_USAGE = 2`**，加入 `budget_gate.py` 退出码区 `:46-56`，取值与 `argparse` 用法错误退出码一致；零 ledger 写入）——round-4 N2。
- **companion 路径同受门禁（round-2 B7）**：`reserve` 的声明门置于 `cmd_reserve` 入口、`cmd_companion_for` 分派（`budget_gate.py:1012-1013`）**之前**（建议位置：`:1009` 的 `no_active_dir` 检查之后），使 `--companion-for` 路径同受约束；`settle` 的声明门置于 `cmd_settle`（`:1167`）进入 `Lock`（`:1171`）之前。**不得**把声明门放在 `cmd_companion_for` 分派之后（否则 companion 路径成为漏网点）。`ocsr_spawn_adapter.py:_ensure_te_companion`（`:264`，其 `reserve --companion-for` 调用在 `:296-299`）与 `_gate_reserve`（`:83`）/ `_gate_settle`（`:97`）列为**同级** D3 注入点，均注入 `--orchest-managed`。
- **披露记录（无新 schema）**：`--manual-fallback` 时，`budget_gate` 追加一条 `[manual-fallback]` bullet 到 `attempts.md`（append-only，命令 + reason + reservation_id + ts，脚本代写）；依据是 `SKILL.md:215` 既有 `[manual-fallback]` 义务，**不新增 ledger 事件/state 字段**。`refs/state-schema.md` 全文 0 处 `manual-fallback`，不是该惯例的来源（S2 更正）。
- **归档显式降级**：`orchest finish` 在归档前扫描 `attempts.md` 的 `[manual-fallback]` 条目；若存在，打印 `DEGRADED:manual-fallback=N` 并要求 `--acknowledge-manual-fallback` 才继续（否则停止，`EXIT_ERROR`）。降级**不静默通过**。该检查落在 `orchest` 层，不改归档契约 schema。
  - **扫描位置（round-4 N1-ii，写死）**：扫描**置于 finish 步骤 3（异常恢复循环，含"产物无法解析"早退分支 `orchest.py:1523-1525`）之后、步骤 3.5 之前（`orchest.py:1547` 步骤 3 循环末之后、`:1549` 步骤 3.5 之前）**，从而位于**归档（步骤 7，`orchest.py:1656-1662`）之前**；步骤 3 的任何 fail 早退都先于扫描发生。**不得**把扫描放在步骤 3 之前（否则会先于步骤 3 的"产物无法解析"失败，打断 `tests/test_loop_a_coverage.py:275-278` 的既有断言）。
  - **`--dry-run` 语义（round-4 N1-iii，择一写死：生效）**：该扫描在 `--dry-run` 下**同样生效**——插入点（`:1548`/`:1549` 之间）位于 dry-run 早退分支（`orchest.py:1628`）之前，故 dry-run 与实跑均先经扫描；dry-run 下同样打印 `DEGRADED:manual-fallback=N` 且缺 `--acknowledge-manual-fallback` 时非零退出。扫描本身只读（不改 `attempts.md`、不写 ledger、不动归档），dry-run 的"零写入"不变量不受影响。
  - **`finish` 新增 `--acknowledge-manual-fallback` 开关**（boolean，`orchest.py` finish 子命令 parser `:1820-1828`）；未传该开关且扫描命中 → 停止且零归档写入。
- **边界诚实**：`archive_convergence.py` 无法区分调用者；本计划**不**尝试 archive 侧 caller 检测（那需要 archive/schema 层改动 → 触发升级闸门）。机制锚点选在 `budget_gate` 记账 CLI + `orchest finish`。另：外部参考驱动器（`refs/orchestrator-guide.md:536`，实现在 vault 侧、不在本仓库）须同步以 `--manual-fallback <reason>`（或在后续对象中改走 `orchest`）适配 D3 门禁；此适配属 out-of-repo，不改本计划文件、不触发升级闸门。
- 对抗回归：无声明直调 `budget_gate reserve` / `budget_gate settle` 被 `FAIL_CLOSED:naked_state_transition` 拒绝（零 ledger 写入）；声明 `--manual-fallback` 正常记账、attempts.md 落披露、`finish` 输出降级并需显式确认；`ingest-verdict` 直调**不受门禁影响**（保护 guide:248 既有路径）。

## Exact File Matrix

| File | 计划改动 | 备注 |
|---|---|---|
| `scripts/budget_gate.py` | D2：`next_contiguous_round`/`contiguous_missing` 单一权威 + `cmd_reserve` 预约号钉定；D3：`reserve`/`settle` 来源声明门（置于 `cmd_companion_for` 分派之前）+ `[manual-fallback]` 落 attempts.md | 不动预算裁决/计数语义、不动 ledger 事件类型与字段、不动归档契约；`ingest-verdict` 不设门 |
| `scripts/orchest.py` | D1：`_reserve_continue` 透传、reserve dry-run 展示联动、`finish --evidence-mode` + 步骤 3 崩溃恢复点缺省继承 started、`--evidence-mode` 仅作覆盖；D2：`_finish_step1_missing` 复用 `budget_gate.contiguous_missing`；D3：`_gate` 对 `reserve`/`settle` 注入 `--orchest-managed`、`finish` 扫描 manual-fallback 并显式降级 | 保留既有 material gate / supersession 行为；`ingest-verdict` 调用不注入 |
| `scripts/ocsr_spawn_adapter.py` | D1：dispatch 的 evidence-mode 默认策略与透传；D3：`_gate_reserve`/`_gate_settle`/`_ensure_te_companion` 注入 `--orchest-managed` | 保持既有原子生命周期；`_ensure_te_companion` 的 `reserve --companion-for` 与另两处同级 |
| `scripts/converge_loop.py` | D1：loop-spec 顶层新键 `evidence_mode`（默认 `metadata-only`，校验 `archive_contract.model.EVIDENCE_MODES`）→ `Driver.reserve`/`Driver.register` 透传 | 不改 loop-spec 版本语义、不改轮号推导、不用 meta 通道 |
| `scripts/README.md` | D1：记录"默认 metadata-only / material 必需 exact / finish 恢复缺省继承 started"；D3：记录 `--manual-fallback` 声明与降级（非治理文档） | 单源为脚本行为 |
| `refs/orchestrator-guide.md` | **不修改（若需要则升级）** | 触及即触发升级闸门 → ultraverge |
| `refs/state-schema.md` | **不修改（若需要则升级）** | 触及即触发升级闸门 → ultraverge |
| `tests/test_budget_gate.py` | D2 回归（取消后重用轮号、跳号被拒、(a)/(b) 两段缺口断言）；**D2 既有用例适配（round-3 P1，实核枚举见下方注）**：`TestScopeBudget.test_outer_boundary`（`:85-94`）、`test_failed_releases_scope`（`:96-103`）、`TestAdversarial.test_duplicate_reservation_id_blocked`（`:270-277`）、`TestModeSwitch.test_impl_streak_triggers_mode_switch`（`:230-238`）、`test_structural_streak_no_switch`（`:240-247`）；D3 来源声明门/披露；既有直调 `reserve` helper（`:40`）、`settle` helper（`:47`）、`:715`、`_companion_for`（`:2015`，内部 `run("reserve", "--companion-for", …)`，非 `reserve`/`settle` helper——round-4 N4）补 `--manual-fallback <reason>` | TDD 先红；`ingest-verdict` 调用（`:233`/`:243`/`:304`/`:309`/`:312`/`:883`）不补 |
| `tests/test_orchest.py` | D1 exact 透传（含 `finish` 恢复点继承 started）；D2 与 budget_gate 缺口一致；D3 finish 降级与确认；既有直调 settle（`:413`）补 `--manual-fallback <reason>`；**D3 finish 降级既有用例适配（round-4 N1-i，显式枚举）**：`TestFinishRecoveryCancelledSettle`（`:405-452`）两条 `finish` 调用 — `:425`（`--dry-run`）补 `--acknowledge-manual-fallback`（调用形如 `self.finish(FINAL_VERDICT, "--dry-run", "--acknowledge-manual-fallback")`）、`:438`（real）补 `--acknowledge-manual-fallback`（`self.finish(FINAL_VERDICT, "--acknowledge-manual-fallback")`）；并在该 TestCase 内显式断言 `DEGRADED:manual-fallback=1` 仍被打印（保留 D3 验收） | TDD 先红；`:413` 的 `--manual-fallback` 使 `attempts.md` 落 1 条 `[manual-fallback]`，故 `:425`/`:438` 必须确认 |
| `tests/test_ocsr_spawn_adapter.py` | D1 evidence-mode 默认与透传；D3 `--orchest-managed` 注入（含 `_ensure_te_companion` 路径）；既有直调 `reserve`/`settle`（`:446`/`:723`/`:737`/`:835`/`:846`/`:882`）补 `--manual-fallback <reason>` | TDD 先红 |
| `tests/test_converge_loop.py` | D1 driver 对 loop-spec 顶层 `evidence_mode` 的透传；既有直调 reserve（`:1064`）补 `--manual-fallback <reason>` | TDD 先红 |
| `tests/test_loop_a_coverage.py` | D3：既有直调 settle 两处注入合法声明——`run_gate("settle")`（`:263`）与直接 subprocess settle（`:800`），手工路径用 `--manual-fallback <reason>` | TDD 先红；经 round-2 B6 新增授权。**round-4 N1 说明**：`:263`（`_crash_window_setup`）产生的 `[manual-fallback]` 在 `TestExecutorCrashWindow` 的第一次 finish（`:275`）前存在，但扫描置于 finish 步骤 3 之后，`:275` 先在步骤 3 以"产物无法解析"失败（`:277-278` 断言）而不进入扫描；`:289` 前 `attempts.md` 已在 `:283-284` 覆写，故两处 finish 均无需 `--acknowledge-manual-fallback` |
| `tests/test_process_controller_contract.py` | 防回退静态检查（按函数/调用点锚定；含负例排除 dry-run 展示串与读取默认值）；断言 `reserve`/`settle` 直调在授权文件外不再新增 | 追加断言 |

> **扫描义务（round-2 B6）**：任何直调 gate 记账命令（`reserve`/`settle`/`ingest-verdict`）的既有脚本或测试须先经 Phase 1 扫描识别，逐处决定是否补声明（`ingest-verdict` 不补）。扫描结果与逐处决定写入 `attempts.md`。若扫描发现需补声明却未列入本矩阵的文件 → 停止并交回 orchestrator，不静默扩范围。

> **既有预算用例适配（round-3 P1；D2 门禁落在 `budget_gate.cmd_reserve`）**：实开 HEAD 工作树核对，`next_contiguous_round` 只读 `round-{n}.md` 文件系统产物（`budget_gate.py:533-543`）：对**直调 gate 且不落产物**的既有 outer 用例，realized 为空 → `next_contiguous_round=1`，`target_round>=2` 的预约会被新门禁拒绝。受影响的既有用例及逐一更新方式如下（行号均实核）：
> - `TestScopeBudget.test_outer_boundary`（`:85-94`）：在 `:89`（首次预约断言后）写 `round-1.md`、`:91` 后写 `round-2.md`。写产物使 `pending()` 跳过已落盘轮、`realized` 补位，`effective_usage` 不变（`budget_gate.py:550-567`）：`:90` 的 `r2` 仍 `usage 1 < 2` → PROCEED，`:92` 的 `r3` 仍 `usage 2 == 2` → `BLOCK:budget_exhausted`。
> - `TestScopeBudget.test_failed_releases_scope`（`:96-103`）：`:102` 的第二预约改 `rnd=1`（＝`next_contiguous_round`）。**不得**在该用例落 `round-1.md`——r1 已 `spawn_failed`（`pending()` 排除，`:556`），落产物会把失败轮计入 `realized` 使 `effective_usage=1`，令 `max_outer_loops=1` 的第二预约变 `BLOCK:budget_exhausted`，破坏"失败释放 scope 额度"语义。失败释放后重用同一轮号正是 D2 期望行为。
> - `TestAdversarial.test_duplicate_reservation_id_blocked`（`:270-277`）：漂移门排在重复 rid 校验**之后**（见 D2 执行次序），`:275` 的重复 rid 先返回，期望仍为 `FAIL_CLOSED:duplicate_reservation_id`；**无需改 fixture**。
> - `TestModeSwitch.test_impl_streak_triggers_mode_switch`（`:230-238`）与 `test_structural_streak_no_switch`（`:240-247`）：在 `:236`/`:246` 的 `rnd=3` 预约前写 `round-1.md`/`round-2.md`，使 `next_contiguous_round==3`；`mode_switch_required` 只读 `state.fsm.severities`（`budget_gate.py:979-992`），不受产物影响，故 MODE_SWITCH / PROCEED 期望不变。

## Bounded Implementation Sequence

1. **Phase 0 升级闸门检查**：任何实现步开工前先确认不需要改 `refs/*`（CONSTITUTION 第三部清单）；一旦需要 → 停止并交回升级 ultraverge。
2. **Phase 1 扫描 + 红测**：
   - **扫描**：用 grep 找出 `scripts/`、`tests/` 中所有直调 gate 记账命令（`reserve`/`settle`/`ingest-verdict`）的位置，逐处决定是否补声明（`ingest-verdict` 不补），结果写入 `attempts.md`；对照 Exact File Matrix，发现未授权文件立即停止交回 orchestrator。
   - **红测**：D2 轮号钉定/两处一致、D1 exact 透传（含 `finish` 恢复点继承 started）、D3 来源声明门/披露/降级、防回退静态检查，全部先写红；并对 `tests/test_loop_a_coverage.py` 的 `run_gate("settle")`（`:263`）与 subprocess settle（`:800`）注入 `--manual-fallback <reason>`。
3. **Phase 2 O4**：实现 `budget_gate` 单一权威 helper 与 `cmd_reserve` 钉定（门禁次序：`canonical_round` → 重复 rid → 漂移门 → `double_target` → 预算裁决 → `MODE_SWITCH`）；`orchest._finish_step1_missing` 改复用；**先适配 `tests/test_budget_gate.py` 既有用例**（round-3 P1，实核枚举）：`TestScopeBudget.test_outer_boundary`（`:85-94`）在 `:89`/`:91` 后落 `round-1.md`/`round-2.md`；`test_failed_releases_scope`（`:96-103`）`:102` 改 `rnd=1`（失败释放后重用轮号；**不落产物**，否则失败轮进 realized 使第二预约变 BLOCK）；`TestAdversarial.test_duplicate_reservation_id_blocked`（`:270-277`）不改 fixture，期望 `FAIL_CLOSED:duplicate_reservation_id` 由"重复 rid 先于漂移门"保证；`TestModeSwitch.test_impl_streak_triggers_mode_switch`（`:230-238`）与 `test_structural_streak_no_switch`（`:240-247`）在 `:236`/`:246` 预约 `rnd=3` 前落 `round-1.md`/`round-2.md`；跑 budget/orchest 定向测试至绿。
4. **Phase 3 O2**：收口 `orchest`（continue 写出点 + dry-run 展示 + `finish --evidence-mode` 与步骤 3 缺省继承）、`ocsr_spawn_adapter`、`converge_loop`（loop-spec 顶层 `evidence_mode`）的 evidence-mode 与默认策略；补 `scripts/README.md`。
5. **Phase 4 O7**：实现 `budget_gate` `reserve`/`settle` 来源声明门（`reserve` 门置于 `cmd_companion_for` 分派之前）+ attempts.md 披露；`orchest`/adapter（含 `_ensure_te_companion`）注入 `--orchest-managed`；`finish` 显式降级（扫描置于步骤 3 之后、步骤 3.5 之前；`--dry-run` 下同样生效）；按 Phase 1 扫描结果补测试声明。**并按 round-4 N1-i 显式适配既有 finish 用例**：`tests/test_orchest.py:425`（`--dry-run`）与 `:438`（real）两条 finish 补 `--acknowledge-manual-fallback`，且 `TestFinishRecoveryCancelledSettle` 断言 `DEGRADED:manual-fallback=1`；`tests/test_loop_a_coverage.py:275` 的步骤 3"产物无法解析"断言保持先发生（扫描在其后）。
6. **Phase 5 验证**：定向 → 全量 → `py_compile` → `git diff --check` → 静态扫描；独立 fresh 审计（OCSR 便宜模型）。定向验证 D3 降级：`TestFinishRecoveryCancelledSettle` 两条 finish（`:425`/`:438`）在带 `--acknowledge-manual-fallback` 下绿且 `DEGRADED:manual-fallback=1` 命中；`tests/test_loop_a_coverage.py:275` 仍以"产物无法解析"失败；附录 A 扫描中标记"受影响/补声明"的调用点全部按处置落实。
7. **Phase 6 收尾**：本计划不再"按需更新治理文档"；若真被触发则已在 Phase 0/任一步停止并升级。归档、复盘。

## Acceptance

- 需要 exact evidence 的路径全部由 CLI 参数驱动；`finish` 崩溃恢复缺省继承对应 invocation-started 的 `prompt_evidence.evidence_mode`，`--evidence-mode` 仅作显式覆盖，手工 archive 绕过不再必要；有按函数/调用点锚定的静态检查防回退。
- 手工状态转移：无声明直调 `budget_gate reserve`/`settle` 被 **fail-closed** 拒绝，精确输出 `FAIL_CLOSED:naked_state_transition` 且零 ledger 写入；声明 `--manual-fallback <reason>` 者落 attempts.md 披露，且 `finish` 输出 `DEGRADED:manual-fallback=N` 并要求显式 `--acknowledge-manual-fallback`；该扫描位于 finish **步骤 3 之后（`orchest.py:1547` 之后）、归档（步骤 7）之前、步骤 3.5（`:1549`）之前**，且 **`--dry-run` 下同样生效**（打印 `DEGRADED` 并同样要求确认）；`tests/test_orchest.py::TestFinishRecoveryCancelledSettle` 两条 finish（`:425` dry-run、`:438` real）带 `--acknowledge-manual-fallback` 后绿且断言 `DEGRADED:manual-fallback=1`，而 `tests/test_loop_a_coverage.py:275` 的步骤 3「产物无法解析」断言仍先发生；`ingest-verdict` 直调不受门禁影响。
- 预约 `target_round` 恒等于 FS 推导的下一个连续轮号；在 `pre_execution` / 纯骨架删除路径（`orchest._cancel_skeleton`）下被取消轮号被重用、不产生 `round_gap`；已写实质内容的取消**不**重用轮号（`round-N.md` 保留并计入 realized，下一轮为 N+1）；缺口判定以两段可观测输出判定——**(a)** `budget_gate.contiguous_missing(active, scope)` 等于预期整数列表，**(b)** `budget_gate.validate_integrity` 抛 `round_gap:{scope}` 且 `orchest._finish_step1_missing` 返回与 (a) 对应的文件名单；`tests/test_budget_gate.py` 既有受门禁用例（`test_outer_boundary`/`test_failed_releases_scope`/`test_duplicate_reservation_id_blocked`/`test_impl_streak_triggers_mode_switch`/`test_structural_streak_no_switch`）已按 File Matrix 适配并保持原期望（绿）；不放松 `double_target` 与"忘写 round-N.md"拦截；有回归测试。
- 全量测试绿；`git diff` 范围限于本计划授权文件（不含 `refs/*`）；独立审计 verdict 为可执行；若审计提出阻断，则该阻断已完成处置并有记录。
- 未触发升级闸门（若触发则本计划停止并交回 ultraverge，而非继续）。

## Non-Goals

- 不改 reviewer 拓扑、fail-closed 语义、预算门裁决、归档契约事件类型；不新增控制器/registry。
- **D3 的规范性归属不在本计划**：不把 `refs/orchestrator-guide.md:231` 的既有强制句升格为新的 state-schema 契约句，不把 `[manual-fallback]` 写入 `refs/state-schema.md` 契约句。若实现判定必须写回这些治理文档才能成立 → 停止并升级 ultraverge（见范围与治理边界）。
- **不对 `ingest-verdict` 设声明门**（round-2 B5）——保留 `refs/orchestrator-guide.md:248` 的直调路径；若坚持对 `ingest-verdict` 设门，则必须先转 ultraverge。
- D2 不引入新的 ledger 事件/字段，不改预算计数语义。
- 本轮披露项（`orchest` 派发在模型白名单校验阶段即失败，账本却记 `spawn_failed pre_execution=false reason=timeout`，污染 `model_invocation` 计数；reservation `813bc923511a` / invocation `4a6bcfee-1a9f-4cb8-a4bf-743043ba088c`，事件序列 3/4）**仅如实记录于 attempts.md，不在本计划实现修复**。
- 不为未观测场景预设机制；无复现证据的设想只记录不实现。

## Risks

- D1：默认 `metadata-only`；`finish` 崩溃恢复缺省继承 started、`--evidence-mode` 仅覆盖；历史归档保持只读，不追溯改档。
- D2：预约号钉定会拒绝"跳号预约"这一历史手工习惯；以"先 `validate_integrity` 再钉定"和单一 helper 降低回归面，且保留 FS 连续编号检查以免放松"忘写 round-N.md"。
- D3：来源声明门只覆盖 `budget_gate` 的 `reserve`/`settle` + `orchest finish`，不覆盖 archive 侧 caller（能力边界已显式声明）；若需 archive 侧区分则触发升级闸门。Phase 1 扫描若发现未授权文件需补声明 → 停止交回 orchestrator（不静默扩范围）。
- 升级闸门：若任一机制被证必须落 `refs/*` 规范句，本计划停止并交回 ultraverge，不以"同步文档"补写。

## 附录 A · 直调记账命令与编排调用点穷举扫描（round-4 硬要求）

> **方法**：对 HEAD 工作树（`529e691`）独立执行下述 grep/rg，并**逐条实开文件核对**（不凭记忆）。判定三类机制：**D2 漂移门**（`consumes ∈ CONTIGUOUS_SCOPES = {outer, blind}`（`budget_gate.py:139`）且 `target_round ≥ 2` 且产物不满足 `target_round == next_contiguous_round`）；**D3 声明门**（裸直调 `reserve`/`settle`，非经 `orchest`/adapter 注入 `--orchest-managed`）；**D3 finish 降级**（`orchest finish` 前同一 active 的 `attempts.md` 含 `[manual-fallback]`）。`ingest-verdict` 与 `summary` 不设门（B5）；`ultraverge` 不在 `CONTIGUOUS_SCOPES`。

### A.0 扫描命令（原文）

```
rg -n --no-heading -e '"reserve"' -e '"settle"' -e '"ingest-verdict"' -e '"summary"' \
  -e "'reserve'" -e "'settle'" -e "'ingest-verdict'" -e "'summary'" \
  -e 'reserve_round' -e 'cmd_reserve' -e 'cmd_settle' tests/ scripts/ --glob '*.py'
rg -n --no-heading -e 'reserve-round' -e 'register-round' -e 'cancel-round' \
  -e '"finish"' -e "'finish'" -e '\.finish\(' -e 'def finish' tests/ scripts/ --glob '*.py'
rg -n --no-heading -e 'def run_gate' -e 'def _run_gate' -e 'def run_cli' -e 'run_cli\(GATE' \
  -e 'run_gate\(' -e '_run_gate\(' -e 'GATE =' -e 'ORCHEST =' -e 'def run_orchest' tests/ scripts/ --glob '*.py'
rg -n -i 'finish|orchest' tests/test_budget_gate.py tests/test_ocsr_spawn_adapter.py
rg -n 'blind-reviewer' tests/*.py
rg -n 'round_no=[2-9]|--round", "[2-9]|--target-round", "[2-9]|rnd=[2-9]' tests/*.py
```

### A.1 `scripts/` 侧记账调用点（经编排 → 注入 `--orchest-managed`）

| 文件:行 | 命令 | 机制 | 是否受影响 | 处置 |
|---|---|---|---|---|
| `scripts/orchest.py:143`（`_gate` 定义） | 通用 | D3 门 | 注入点 | `_gate` 对 `args[0] ∈ {reserve, settle}` 注入 `--orchest-managed`（`ingest-verdict` 不注入） |
| `scripts/orchest.py:196`（`_settle_te_companion_for_continue`） | `settle` | D3 门 | 是（经 `_gate`） | 注入 |
| `scripts/orchest.py:612`（`cmd_reserve_round`） | `reserve` | D3 门 / D2（官方连续） | 是（经 `_gate`）；D2 由“先 gate 后骨架”保证一致 | 注入 |
| `scripts/orchest.py:719`（`cmd_register_round` 崩溃窗口） | `settle` | D3 门 | 是 | 注入 |
| `scripts/orchest.py:771`（`cmd_register_round` 主路径） | `settle` | D3 门 | 是 | 注入 |
| `scripts/orchest.py:845`（`cmd_cancel_round` 崩溃窗口） | `settle` | D3 门 | 是 | 注入 |
| `scripts/orchest.py:881`（`cmd_cancel_round` 主路径） | `settle` | D3 门 | 是 | 注入 |
| `scripts/orchest.py:972`（`cmd_record_verdict`） | `ingest-verdict` | — | **否**（B5 移出） | 不注入 |
| `scripts/ocsr_spawn_adapter.py:86`（`_gate_reserve`） | `reserve` | D3 门 | 是 | 注入 |
| `scripts/ocsr_spawn_adapter.py:100`（`_gate_settle`） | `settle` | D3 门 | 是 | 注入 |
| `scripts/ocsr_spawn_adapter.py:296`（`_ensure_te_companion`） | `reserve --companion-for` | D3 门 | 是（须门前置于 `cmd_companion_for` 分派之前） | 注入 |
| `scripts/ocsr_spawn_adapter.py:406`/`:764` | `summary` | — | 否 | 不改 |
| `scripts/converge_loop.py:456`（`Driver.reserve`） | `reserve-round`（经 orchest） | D2/D3 | D2：`round_n` 由 `next_round`（`:331-333`）从 realized 产物推导 → 恒等，不受影响；D3 由 orchest 注入 | 不改 |
| `scripts/converge_loop.py:471`（`Driver.register`） | `register-round` | — | 否 | 不改 |
| `scripts/converge_loop.py:480`（`Driver.cancel`） | `cancel-round` | — | 否 | 不改 |
| `scripts/converge_loop.py:496`（`Driver.finish`） | `finish`（经 orchest） | D3 finish 降级 | 否：官方路径不产生 `[manual-fallback]` | 不改 |
| `scripts/hooks/kimi_pretooluse_shim.py` | 仅 `hook-pretooluse` | — | 否 | 不改 |
| `scripts/hooks/stale-check.py` | 只读 import | — | 否 | 不改 |
| `scripts/distill_antipatterns.py` | 无记账调用 | — | 否 | 不改 |

### A.2 `tests/` 侧直调记账子命令（D3 声明门适用；`--manual-fallback <reason>` 补声明）

| 文件:行 | 命令 | 是否受影响 | 处置 |
|---|---|---|---|
| `tests/test_budget_gate.py:40`（helper `reserve`） | `reserve` | 是（D3；D2 视各调用点，见 A.3） | 补 |
| `tests/test_budget_gate.py:47`（helper `settle`） | `settle` | 是（D3） | 补 |
| `tests/test_budget_gate.py:715` | `reserve`（executor，`target-round -1`） | 是（D3；D2 否，consumes=none） | 补 |
| `tests/test_budget_gate.py:2015`（`_companion_for`） | `reserve --companion-for` | 是（D3；D2 否，task-envelope） | 补 |
| `tests/test_budget_gate.py:233/:243/:304/:309/:312/:883` | `ingest-verdict` | 否（B5） | 不补 |
| `tests/test_budget_gate.py:741/:1903/:1928` | `summary` | 否 | 不补 |
| `tests/test_converge_loop.py:1064`（`_run_gate`） | `reserve`（outer，target-round 1） | 是（D3；D2 否，round 1） | 补 |
| `tests/test_converge_loop.py:1079` | `_run_gate` helper 定义 | — | 不改 |
| `tests/test_ocsr_spawn_adapter.py:446/:723/:835/:882` | `reserve`（executor） | 是（D3；D2 否） | 补 |
| `tests/test_ocsr_spawn_adapter.py:737` | `settle` | 是（D3） | 补 |
| `tests/test_ocsr_spawn_adapter.py:846` | `reserve --companion-for` | 是（D3；D2 否） | 补 |
| `tests/test_ocsr_spawn_adapter.py:421` | `summary` | 否 | 不补 |
| `tests/test_loop_a_coverage.py:263`（`run_gate("settle")`） | `settle` | 是（D3） | 补（并见 A.4） |
| `tests/test_loop_a_coverage.py:800`（subprocess） | `settle` | 是（D3） | 补 |
| `tests/test_loop_a_coverage.py:745/:772` | `summary` | 否 | 不补 |
| `tests/test_orchest.py:413`（`run_cli(GATE, "settle")`） | `settle` | 是（D3；并触发 A.4） | 补 |

### A.3 D2 漂移门逐调用点判定（`CONTIGUOUS_SCOPES` 且 `target_round ≥ 2`）

| 文件:行 | 角色/scope | target_round | 是否受影响 | 处置 |
|---|---|---|---|---|
| `tests/test_budget_gate.py:90`（`test_outer_boundary`） | outer | 2 | **是**（realized 空） | 落 `round-1.md`（`:89` 后） |
| `tests/test_budget_gate.py:92`（同上） | outer | 3 | **是** | 落 `round-2.md`（`:91` 后） |
| `tests/test_budget_gate.py:102`（`test_failed_releases_scope`） | outer | 2 | **是** | 改 `rnd=1`；**不落产物**（保失败释放语义） |
| `tests/test_budget_gate.py:112`（`test_realized_dedup`） | outer | 2 | 否（`:110` 已落 `round-1.md`） | 不改 |
| `tests/test_budget_gate.py:236`（`test_impl_streak_triggers_mode_switch`） | outer | 3 | **是** | 预约前落 `round-1.md`/`round-2.md` |
| `tests/test_budget_gate.py:246`（`test_structural_streak_no_switch`） | outer | 3 | **是** | 同上 |
| `tests/test_budget_gate.py:275`（`test_duplicate_reservation_id_blocked`） | outer | 2 | 否（重复 rid 校验 `:1037-1038` 先于漂移门 `:1040`） | 不改 fixture |
| `tests/test_budget_gate.py:299`（`test_round_gap_fail_closed`） | outer | 4 | 否（`validate_integrity` `:1018` 先抛 `round_gap:outer`） | 不改 |
| `tests/test_budget_gate.py:354/:373`（畸形 reserved 注入） | outer | 2 | 否（`validate_integrity` 先失败） | 不改 |
| `tests/test_orchest.py:376`（`completed_round(1)` 后） | outer | 2 | 否（`round-1.md` 已存在） | 不改 |
| `tests/test_orchest.py:412`/`:435`（`completed_round(1)` 后） | outer | 2 | 否（`round-1.md` 已存在） | 不改 |
| `tests/test_orchest.py:754`（`:746` 已 register r1） | outer | 2 | 否（`round-1.md` 已存在） | 不改 |
| `tests/test_loop_a_coverage.py:655`（reopen 后） | outer | 2 | 否（`round-1.md` 随 reopen 回迁 active） | 不改 |
| `tests/test_loop_a_coverage.py:1032`（`:1029` 已 reserve r1） | outer | 2 | 否（`round-1.md` 已存在） | 不改 |
| `tests/test_loop_a_coverage.py:1248`（`:1210` 已 reserve r1） | outer | 2 | 否（`round-1.md` 已存在） | 不改 |
| `tests/test_loop_a_coverage.py:1250`（`:1212` blind r1） | blind | 2 | 否（`blind-recheck-1.md` 已存在） | 不改 |
| `scripts/converge_loop.py:456`（driver） | outer/blind | 由 `next_round` 推导 | 否（`target_round` 恒等于 `next_contiguous_round`） | 不改 |

> 结论：D2 受影响的既有测试点**仅** `tests/test_budget_gate.py` 的 5 条用例（`:90`/`:92`、`:102`、`:236`、`:246`），与 plan:108/plan:129 枚举一致，**无新增**。

### A.4 D3 finish 降级逐 `finish` 调用点判定（同一 active 是否有 `[manual-fallback]`）

| 文件:行 | `[manual-fallback]` 来源 | 是否受影响 | 处置 |
|---|---|---|---|
| `tests/test_orchest.py:425`（`TestFinishRecoveryCancelledSettle` dry-run） | `:413` 直调 settle（补声明） | **是**（1 条） | 补 `--acknowledge-manual-fallback` + 断言 `DEGRADED:manual-fallback=1` |
| `tests/test_orchest.py:438`（同 TestCase real） | `:413` | **是**（1 条） | 同上 |
| `tests/test_orchest.py:348/:363/:384/:461/:463/:590/:802` | 官方 reserve/register/cancel | 否 | 不改 |
| `tests/test_orchest.py:625/:663`（回归 fixture，skip-if-absent） | 外部 fixture `20260815-embeddings-cleanup` | 否（实核该 fixture `attempts.md` 含 0 条 `[manual-fallback]`） | 不改 |
| `tests/test_loop_a_coverage.py:275`（`TestExecutorCrashWindow` 首次） | `:263` 直调 settle（补声明） | 否（扫描在步骤 3 之后；步骤 3 先以“产物无法解析”失败） | 不改 |
| `tests/test_loop_a_coverage.py:289`（同 TestCase 恢复后） | `:263`，但 `:283-284` 已覆写 `attempts.md` | 否 | 不改 |
| `tests/test_loop_a_coverage.py` 其余 finish（`:210/:248/:447/:457/:476/:524/:565/:610/:630/:665/:698/:724/:827/:913/:949/:980/:1080/:1107/:1167/:1297/:1359/:1413/:1425`） | 官方 reserve/register（无 `--manual-fallback`） | 否 | 不改 |
| `tests/test_continue_extension.py:114/:166`、`tests/test_converge_loop.py` driver finish、`tests/test_orchest.py:819`（`_finish_step6` 单测非 orchest finish） | 官方路径 | 否 | 不改 |
| `tests/test_budget_gate.py` / `tests/test_ocsr_spawn_adapter.py` | 无 `orchest finish` 调用（rg 命中 0） | 否 | 不改 |

> 结论：D3 finish 降级受影响的既有测试点**仅** `tests/test_orchest.py:425`/`:438`，已按 round-4 N1-i 显式枚举。扫描置于步骤 3 之后保住 `tests/test_loop_a_coverage.py:275-278`。

### A.5 汇总与范围外点

- **受影响点总数（去重后）**：D2 = 4 条用例（`test_outer_boundary`、`test_failed_releases_scope`、`TestModeSwitch` 的 `test_impl_streak_triggers_mode_switch` 与 `test_structural_streak_no_switch`），共 5 个调用点（`:90`/`:92`/`:102`/`:236`/`:246`）；D3 声明门 = A.2 所列全部直调 `reserve`/`settle`（已全部落入 Exact File Matrix 授权文件）；D3 finish 降级 = `tests/test_orchest.py:425`/`:438`。
- **范围外点**：**无**。所有“受影响”点均在授权文件（`tests/test_budget_gate.py`、`tests/test_orchest.py`、`tests/test_loop_a_coverage.py`、`tests/test_ocsr_spawn_adapter.py`、`tests/test_converge_loop.py`）内；扫描未发现需补声明却未列入矩阵的文件。
- **不可机械保证项（显式标出，非静默略过）**：`tests/test_orchest.py:625`/`:663` 依赖 out-of-repo fixture（`KB_VAULT_ROOT/.meta/converge/done/20260815-embeddings-cleanup`，skip-if-absent）；本轮实核该 fixture `attempts.md` **0 条** `[manual-fallback]`（该对象早于 `[manual-fallback]` 惯例），故当前不受影响。若该 fixture 将来被替换为含 `[manual-fallback]` 的对象，则这两条 finish 会触发降级并需 `--acknowledge-manual-fallback`——属 out-of-repo 数据变更，不在本计划授权范围，已在此显式记录。
