---
round: 1
verdict: 阻断需修复
reviewer_backend: opencode
reviewer_instance_id: 20260911_215656_d5102b
generated_at: 2026-09-11T14:00:15.935775+00:00
---

## 前置自检

1. **产物身份自洽**：通过 — plan 标题「子计划 A · 工具与纪律硬化（O2+O4+O7）」与 Goal / 决策 D1-D3 / Exact File Matrix 指向同一问题，未见「声称做 A 实际做 B」。附注：一个计划捆绑 O2/O4/O7 三个机制，与父索引「不要把多个机制塞进同一个巨型计划」的教训有张力，但父索引已显式如此拆分，属有意范围，不判失败。
2. **产物边界诚实**：通过 — scope 限 converge-skill；Non-Goals 明确不改判定机制/归档事件类型；未虚构「通用/领域」式扩展。附注：`refs/orchestrator-guide.md` / `refs/state-schema.md` 以「评议时判定」保留在文件矩阵，使边界处于未决状态，此点在治理边界单独处理。
3. **产物数据纯度**：通过 — 纯机制类计划，无项目业务数据、无硬编码环境依赖。
4. **职责边界自洽**：不通过 — D2 的「连续编号」不变量同时实现在 `budget_gate.py`（validate_ledger，`:903-907`）和 `orchest.py`（`_finish_step1_missing`，`:999-1010`，由 finish 步骤 1 `:1465-1469` 调用），但 Exact File Matrix 只把 D2 指派给 `scripts/budget_gate.py`；`scripts/orchest.py` 行仅覆盖 D1/D3。两个组件形成「都以为对方会改」的灰区，Phase 2 只改一处会让 Acceptance 的 `round_gap` 断言在 finish 步骤 1 落空。→ 见 B2。
5. **命名一致性**：不通过 — D1 决策明写「**默认 metadata-only，material/终局相关轮必须 exact**」（plan:29），Risks 却写「D1 "默认 exact" 若影响既有 metadata-only 兼容」（plan:82）。同一默认值前后矛盾，executor 无法确定该把默认设为哪一档。→ 见 B4。

## 事实核对

- **O2 现状描述（基本属实，line ref 过期）**：`orchest.py` 确实仍存在 `metadata-only` 硬编码写出点——`:392`（`_reserve_continue` 的 `begin-invocation`）、`:576`（reserve-round dry-run 展示串，仅显示）、`:1535`（`finish` 步骤 3 崩溃恢复的 `complete-invocation`）。`reserve-round`/`register-round` 的 spawn 主路径已经可透传：`:628` / `:759` 用 `getattr(args, "evidence_mode", "metadata-only")`，CLI 定义在 `:1766`/`:1789`（默认 `metadata-only`）。`:1226-1227` 为读取侧默认值，非写出。→ 计划「多处硬编码」成立。**但计划给出「脚本约 :436/:562/:693，CLI 约 :1612/:1635」与现状不符**（`:436` 是 `_reserve_continue` 内的 te_note，非 evidence-mode；实际写出透传点为 `:628/:759`，CLI 为 `:1766/:1789`），偏差约 150-180 行，非「约」可覆盖的噪声。
- **O2 遗漏路径**：计划的「清点三处入口（`orchest.py` / `ocsr_spawn_adapter.py` / `converge_loop.py`）」未点名 `orchest.py:1535` 的 finish 崩溃恢复写出点。该路径无法经 CLI 参数声明 exact，与 Acceptance「全部由 CLI 参数驱动」直接冲突。`ocsr_spawn_adapter.py` 的透传已存在（`:441` 读 `args.evidence_mode`，`:480`/`:538` 使用，CLI `:733` 默认 metadata-only），实际只剩「默认策略」待定。`converge_loop.py` 的 driver 封装（`reserve` `:453-468`、`register` `:470-477`）根本没传 `--evidence-mode`，计划已列该文件，属实。
- **O4 现状描述（检查机制属实，因果描述不准）**：连续编号确实由文件系统产物驱动——`budget_gate.py:533-543` `realized_round_numbers()` 对 `SCOPE_PRODUCT`（`:133-139`）glob 结果取号，validate 在 `:903-907` 判 `round_gap`；`orchest.py:999-1010` 同源重复。`cancelled` 确实在 `double_target` 判定被跳过：`budget_gate.py:896-897`（计划写的 `:883` 实为 settle 生命周期循环，`:890-894` 是 double_target 段，行号不准）。「`cancelled` 占号」的因果**与机制不一致**：连续编号检查完全不读 ledger，`cancelled` 不写产物也不会在 FS 检查里「占号」；`_cancel_skeleton`（`orchest.py:282-300`）对纯骨架**删除**文件、对已写实质内容**保留并标注** `status: cancelled`。r2 实证的 `round_gap:outer`（attempts.md:207）真实成因是**预约 target_round 与产物文件名的错位**：ledger 中 outer 成功预约 target_round 为 {1,2,4,5}（gate-ledger.jsonl:14/28/38/48，其中 3 被 pre_execution cancelled，:40），而落盘产物是 round-1..4，操作者把 round-5.md 归位成 round-4.md 才绕过。若按 D2 字面「改为基于成功结算的轮次集合」用 target_round 重算，r2 的 {1,2,4,5} 反而**不连续**。故 D2 的诊断与拟议修法均需重写。
- **O7 证据**：attempts.md 的三条 `[manual-fallback]`（:202 orch est metadata-only 硬编码、:207 round-5.md 归位、:211 字面量 `PENDING`）与 retrospective.md:118 一致，O7 描述属实。
- **非治理文档判定**：`scripts/README.md` 不在 CONSTITUTION 第三部清单内，「非治理文档」判断正确（plan:50）。
- **重复不变量**：`budget_gate.py:903-907` 与 `orchest.py:999-1010`+`:1465-1469` 是同一不变量的两处实现，File Matrix 未把 D2 同时挂到 `orchest.py`。

## 治理边界判定

**必须升级 ultraverge。** 理由：

- CONSTITUTION 第三部把 `refs/orchestrator-guide.md`（Orchestrator 语义判定指南）与 `refs/state-schema.md`（State & log 格式规范）列为治理文档；第四部规定对其修改须走 ultraverge（≥3 Reviewer + 收敛 + 设计审查）。
- D3 的实质内容是**对 Orchestrator 行为的规范性约束**：「收敛循环内的 reserve/begin-invocation/complete-invocation 只允许经 orchest 命令族；其余直接调用需显式 `--manual-fallback` 声明，并强制在 attempts.md 落 `[manual-fallback]`；归档把未声明裸转移作为显式降级」。该规则的自然且必需归属地是 `refs/orchestrator-guide.md`——该文件 `:231` 已有「每次 spawn 经 orchest.py（收敛循环内）」的规范句，D3 是对其的强化，不写回该文件则机制不可被 agent 发现（治理缺口）。同时 `[manual-fallback]` 披露属于 `refs/state-schema.md` §二 Attempt Log 的格式契约。两条都落在第三部清单内。
- D2 的「允许显式声明该轮号作废」若落为新的 ledger 事件/字段，则触及 Archive Contract / `refs/state-schema.md`；计划 Non-Goals 又明写「不改归档契约事件类型」，二者不可同时成立，需在超验流程中先定界。
- 因此 plan frontmatter 的 `review_mode: standard-review 入口；若评议判定触及治理文档语义则升级 ultraverge` 在此判定为**升级分支成立**：D1（脚本 + `scripts/README.md`）本身可 standard，但 D2/D3 以当前形态不能。
- 反过来说，若要把 A 保留在 standard-review，plan 必须**显式收窄 D2/D3**：D3 只做脚本机制（不改 `refs/` 规范句），D2 不引入新 ledger 事件/字段。当前 plan 未做此收窄。

## Blocking Issues

```yaml
blocking_issues:
  - id: B1
    description: |
      D2/D3 以当前形态触及 CONSTITUTION 第三部治理文档（refs/orchestrator-guide.md 的
      "spawn 经 orchest" 规范句强化；refs/state-schema.md §二 attempts.md 的 [manual-fallback]
      披露契约；D2 "作废声明" 若入 ledger/state 则触及归档契约），按第四部必须走 ultraverge，
      但 plan 的 review_mode 仍是 standard-review 入口且把升级留给"评议时判定"，未落定。
      plan 也未显式收窄 D2/D3 以留在 standard-review。此边界未决使执行路径非法（在错误
      评议模式下实施治理文档修改）。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: plan.md frontmatter review_mode；决策 D2/D3；Exact File Matrix refs/orchestrator-guide.md 与 refs/state-schema.md 行；Risks 第 3 条
  - id: B2
    description: |
      D2 的"连续编号"不变量在两处实现：budget_gate.py:903-907（validate_ledger）与
      orchest.py:999-1010（_finish_step1_missing，finish 步骤 1 :1465-1469 调用）。Exact File
      Matrix 只把 D2 指派给 scripts/budget_gate.py，scripts/orchest.py 行只写 D1/D3。若 Phase 2
      只改 budget_gate.py，finish 步骤 1 仍按文件系统产物判 gap，Acceptance"取消预约后不再产生
      round_gap"在官方收尾路径上不成立；两处职责形成"都以为对方管"的灰区（前置自检 Q4 不通过）。
    attribution: plan_defect
    severity: conceptual
    plan_amendment_required: true
    location: Exact File Matrix 的 scripts/orchest.py 行与 scripts/budget_gate.py 行；Bounded Implementation Sequence Phase 2；Acceptance 第 3 条
  - id: B3
    description: |
      D2 的机制未定义且诊断与真实机制不符：(a) "改为基于成功结算的轮次集合，或允许显式声明
      该轮号作废"用"或"把两种不同方案并列，未选定，executor 无法实施；(b) 连续编号检查当前
      完全基于文件系统产物（budget_gate.py:533-543 + :903-907），不读 ledger，cancelled 不
      "占号"；(c) r2 的 round_gap 真因是预约 target_round（成功值 {1,2,4,5}，见 gate-ledger.jsonl
      :14/:28/:38/:48，3 为 pre_execution cancelled :40）与产物文件名 round-1..4 的错位，按
      target_round 重算反而不连续。按 (a) 实施既可能不消除错位根因，也可能以 ledger 集合替换
      FS 检查从而放松"忘写 round-N.md"不变量（orchest.py 模块 docstring :27 明确该检查防此错）。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: 决策 D2；Evidence O4 行；Risks 第 2 条
  - id: B4
    description: |
      D1 范围与默认策略均未闭合：(a) Acceptance 要求"需要 exact evidence 的路径全部由 CLI
      参数驱动"，但 orchest.py:1535（finish 步骤 3 崩溃恢复的 complete-invocation）硬编码
      metadata-only，无 CLI 覆盖点；对 material 轮，该恢复产物不满足 exact 两权威同字节绑定，
      恢复路径无法成功（虽 fail-closed，但正是 O2 要消除的官方路径摩擦）。计划"清点三处入口"
      未点名该点。(b) D1 决策为"默认 metadata-only"（plan:29），Risks 却写"D1 '默认 exact'"
      （plan:82），自相矛盾，executor 无法确定默认档（前置自检 Q5 不通过）。另 :392 的 continue
      begin 也硬编码 metadata-only，是否需 exact 未判定。
    attribution: plan_defect
    severity: implementation
    plan_amendment_required: true
    location: 决策 D1；Evidence O2 行；Acceptance 第 1 条；Risks 第 1 条
```

## Suggestions

```yaml
suggestions:
  - description: |
      刷新事实引用的行号。plan:21 的"脚本约 :436/:562/:693，CLI 约 :1612/:1635"与 plan:23 的
      ":890-894 / :883"均与当前代码不符（实际 evidence-mode 透传写出点为 orchest.py:628/:759，
      CLI :1766/:1789；连续编号在 budget_gate.py:903-907，double_target 跳过 cancelled 在
      :896-897）。过期行号会误导 executor 定位。
  - description: |
      D3 的"裸状态转移拒绝/声明"缺可区分机制：orchest.py 与手工路径最终调用同一个
      archive_convergence.py begin/complete CLI，archive 侧无法区分调用者。需在计划中写明靠
      何种信号（orchest 注入的内部标记 / 仅仲裁侧 flag）区分"经 orchest"与"裸调用"，否则
      "拒绝"不可实现，只能退化为"强制声明 + 归档降级"。
  - description: |
      D2 应明确限定在 validate 层（budget_gate.py:903-907 与 orchest.py:999-1010），不得改动
      realized()/pending()/effective_usage() 的预算计数（budget_gate.py:533-567），以兑现
      File Matrix"不动预算裁决"。
  - description: |
      防回退静态检查需覆盖负例：除断言"exact 必需路径不得出现硬编码 metadata-only"外，补一条
      "该断言按调用点/函数锚定、不误伤 :576 dry-run 展示串与 :1226-1227 读取默认值"，避免
      检查本身过宽。
  - description: |
      `scripts/README.md` 的默认策略措辞应区分"默认（缺省）"与"必需（material/终局）"，避免
      与 D1 的 Risks 矛盾延续到文档单源。
```

## 验收核对

- 「需要 exact evidence 的路径全部由 CLI 参数驱动，手工 archive 绕过不再必要；有静态检查防回退。」→ **fail**：`orchest.py:1535` 的 finish 恢复路径无法经 CLI 声明 exact，「全部由 CLI 参数驱动」不成立；静态检查范围亦未含该点（B4）。
- 「手工状态转移要么被机制拒绝，要么被强制记 `[manual-fallback]` 并在归档中显式降级。」→ **uncertain**：拒绝机制不可区分调用者（见 Suggestions），且该规范性要求落 `refs/` → 需 ultraverge（B1）。
- 「取消预约后不再产生 `round_gap`，且不放松 `double_target`；有回归测试。」→ **fail**：D2 机制未定义且只指派到 `budget_gate.py`，`orchest.py:999-1010` 的 finish 步骤 1 仍会触发 gap；测试矩阵未覆盖该路径（B2/B3）。
- 「全量测试绿；`git diff` 范围限于本计划授权文件；独立审计 verdict 可执行或已处置阻断。」→ **uncertain**（计划阶段，未执行；且授权文件范围需先按 B1 重定）。
