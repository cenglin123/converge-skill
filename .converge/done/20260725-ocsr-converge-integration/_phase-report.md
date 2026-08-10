# Phase Report — OCSR↔converge 钩子对接

## Phase 0 · 调研 + 对接设计 ✅ 完成（2026-07-25 17:25）

### 已完成
- 读透 plan.md + orchestrator-brief.md（指挥结构、宪法强制点、升级协议）。
- 调研三处源码（详见 _orchestrator-state.md 进度摘要）。
- 状态文件就位（本文件 + _orchestrator-state.md）。
- **Smoke test 通过**：嵌套 `opencode run` 0.2min wall，产物正确，无 DB 锁。
- **design.md 产出**（`.converge/active/20260725-ocsr-converge-integration/design.md`）：adapter-layer 决策（选项 B），源码证据链完整。
- **Round 1 design review**（xiaomi/mimo-v2.5-pro）：1 blocking + 4 suggestion，verdict=阻断需修复。
- **Executor fix**（deepseek-v4-flash）+ orchestrator 残余清理：5 项全部修复，design 内部一致。

### 关键源码证据
1. **OCSR 生命周期钩子点**（`ocsr/scripts/ocsr_dispatch.py`）：
   - `cmd_dispatch`（dispatch 入口）：解析 workers → 生成 launcher → `Start-Process` → 调 `_watch_loop`。
   - `_watch_loop`（产物回收循环）：三个分支——landed（success）/ error_file / exit_code 检测 / 超时。
   - **每条事件已统一调 `_append_dispatch_ledger(ledger, {...})` 和 `_append_telemetry(...)`**，但**未**调 converge 的 `archive_convergence.py begin/complete-invocation`，也**未**调 `budget_gate.py reserve/settle`。
   - 角色 enum `ROLE_VALUES` 与 budget_gate `ROLE_CONSUMES` 在适配层使用的 6 个角色子集上一致。

2. **converge Archive Contract 的事件要求**（`scripts/archive_contract/capture.py`）：
   - `begin_invocation`：spawn 必须传 `reservation_id`（line 214）。
   - `complete_invocation`：succeeded 必须有 output bytes/identity；`settlement_ref` 在有 reservation 时自动生成规范值。
   - `recover_invocation`：仅追加 failed/cancelled/timeout terminal，自动写入 unavailable/none/invocation-failed-before-resolution。

3. **provenance 诚实降级（关键修正）**（`scripts/archive_contract/model.py:PROVENANCE_MATRIX` + lines 494-513）：
   - `host-reported` reasons = `frozenset({None})`，且必须有 bound host receipt + concrete resolved 字段。
   - OCSR 无 per-invocation tool_response 绑定 → 必须用 `configured + cli_argument + backend-does-not-expose`（strictest legal honest choice）。
   - `--instance-id`/`--receipt` 在 configured 层级下作为非约束性关联句柄保留（debug/audit 用），不升格 provenance。

4. **`ocsr-dispatch-ledger.jsonl` 已被 archive 识别**（`archive_contract/model.py:ROOT_FIXED` line 59）：但仅作为 root 文件纳入 manifest，**不构成 invocation event**——`events-missing` fail-closed 是因为 `evidence/events/` 目录无 invocation-started/terminal 事件。

### 产物
- design.md（17KB，含 Revision Log）
- reviews/review-design-round-1.md（9422B）
- reviews/executor-round-1-attempt.md（7007B）
- ocsr-dispatch-ledger.jsonl（含 R1 review + R1 executor 两条 landed 记录）

### 下一步：Phase 1 · 事件流接线
- 实现 `scripts/ocsr_spawn_adapter.py`（adapter layer B）
- 路径：dispatch → begin-invocation → ocsr dispatch → complete/recover-invocation + settle
- 含失败注入测试（看门狗超时 → recover-invocation）
- Phase 1 完成后派非-glm reviewer 验收

---

## Phase 1 · 事件流接线 ✅ 完成（2026-07-25 17:40，终止-a 严格首轮通过）

### 产物
- `scripts/ocsr_spawn_adapter.py`（26756B，stdlib only）：5 步原子化 Spawn 包装（reserve→begin→dispatch→complete/recover→settle）
- `tests/_fake_ocsr_dispatch.py`（test shim，模拟 happy/fail-launcher/fail-timeout/fail-collision 4 种 ocsr 行为）
- `tests/test_ocsr_spawn_adapter.py`（6 tests，全绿）：happy path / fail-launcher / fail-timeout / unknown-role-DENY / outer-reviewer scope / event-graph validity

### 关键实现细节
- provenance：configured + cli_argument + backend-does-not-expose（PROVENANCE_MATRIX 下严格合法选择，不含 resolved 字段）
- 失败路径映射：watchdog timeout → archive timeout + gate failed (pre_execution=false)；launcher error → archive failed + gate failed/cancelled (pre_execution=true)
- instance_id：解析 ocsr-dispatch-ledger.jsonl 的 batch_id 作为非约束性关联句柄
- settlement_ref：由 archive_contract capture.py 自动生成（gate-ledger.jsonl:<rid>）
- receipt：adapter 显式传 ocsr-dispatch-ledger.jsonl:<rid>（关联元数据，configured 层级下不参与 host-evidence 绑定）

### Phase 1 R1 review（deepseek/deepseek-v4-pro）
- verdict = **可执行**（零阻断，终止-a）
- 160 pre-existing + 6 new tests 全绿，无回归
- 6 suggestion 全 defer 到 Phase 4 retrospective（均 severity=implementation、非阻断）

### 下一步：Phase 2 · 预算门控接线
- 用接好的 ocsr_spawn_adapter 跑真实 converge（而非裸 ocsr_dispatch）
- dispatch 前 reserve（adapter 已内置）、落盘后 settle（adapter 已内置）
- `_budget-state.json` config 初始化（ultraverge max_blind_rechecks=2 覆盖等既有规则）
- ledger 写入 converge active 目录（adapter 已通过 `--ledger-dir` 自动补全）
- Phase 2 完成后派非-glm reviewer 验收

---

## Phase 2 · 预算门控接线 ✅ 完成（2026-07-25 17:38，终止-a）

### 产物（增量）
- `scripts/ocsr_spawn_adapter.py` 增加：
  - `config-init` 子命令：写初始 `_budget-state.json`（idempotent；`--mode ultraverge` 自动应用 `max_blind_rechecks=2` 覆盖；`--force` 覆盖）
  - `summary` 子命令：透传到 budget_gate summary
- `tests/test_ocsr_spawn_adapter.py` 增加 8 个测试：
  - TestConfigInit（6 个：standard/ultraverge/override/idempotent/force/LF endings）
  - TestBudgetAccounting（2 个：per-scope 阻断、summary 双计数 attempted/model_invocation）

### Phase 2 R1 review（xiaomi/mimo-v2.5-pro）
- verdict = **可执行**（终止-a，零阻断、零建议、零 antipattern）
- 168 pre-existing+new tests 全绿，无回归
- 7 个语义检查项全 PASS：config-init ultraverge 覆盖、idempotent fail-closed、LF 钉位、per-scope 阻断、summary 透传、双计数区分、Phase 1 无回归

### 下一步：Phase 3 · 端到端 dogfood 验证

---

## Phase 3 · 端到端 dogfood ✅ 完成（2026-07-25 17:46，验收 3 项全通过）

### 验收证据
1. **`archive` 返回成功**：`{"archived":"...done\\20260725-dogfood-adapter-usage","status":"committed"}`
2. **`check` 返回 valid-v1**：`valid-v1: .converge\done\20260725-dogfood-adapter-usage`
3. **事件序号连续 + provenance 诚实 + 无孤儿 reservation**：
   - sequence 1-7 连续无缺口
   - 3 次 Spawn（R1 reviewer / R1 executor / R2 reviewer）全部有 started+terminal 对
   - succeeded terminal evidence_level=configured（正确降级）
   - failed terminal evidence_level=unavailable（pre-execution 失败路径正确）
   - `list-orphan-reservations` 返回 `none`

### 关键产物
- 新增 dogfood converge 对象：`docs/dogfood/ocsr-adapter-usage.md`（140 行，R2 reviewer verdict=可执行）
- 归档位置：`.converge/done/20260725-dogfood-adapter-usage/`

### 关键 dogfood 发现（写入 Phase 4 文档）
**适配层对 "edit X" 类任务的产物判定过严**：watcher 期望单一产物文件，但 executor 的实际交付可能是 "edit doc + write log"。当 executor 完成实际工作但未写到 watcher 期望路径时，事件图标会记为 `failed`（recover-invocation + settle failed）。

这是 **faithful recording**（archive Contract 捕获真实事件，包括路径不匹配的失败路径），不是适配层 bug。但用户层面需要明确指导：
- "edit 类任务" prompt 应同时让 executor 写一个 sentinel 文件（如 `done.marker`）作为 `--output-name`，否则 watcher 会判定失败。
- Phase 4 的 ocsr SKILL.md + framework-adapters.md 文档将写明此模式。

### 下一步：Phase 4 · 文档同步与收口
- ocsr SKILL.md：派发驱动器节加对接能力说明
- converge refs/framework-adapters.md §A.2：OCSR 作为 Spawn 实现的接线说明
- 两仓库 CHANGELOG
- retrospective（dogfood 已写一份；主任务 retrospective 在 Phase 4 末尾）
- 最终待验收清单（改动文件列表 + 测试证据）写入 _phase-report.md

---

## Phase 4 · 文档同步与收口 ✅ 完成

### 产物
- **ocsr SKILL.md**：§三 派发驱动器节新增「作为 converge Spawn 后端」子节（~35 行）。覆盖：适配层调用示例、provenance 诚实降级策略、"edit X" 类任务的 sentinel 模式、架构定位（ocsr 框架无关 + converge 是客户之一）。交叉引用 design.md + framework-adapters.md。
- **converge refs/framework-adapters.md §A.2**：新增 OCSR 作为 opencode Spawn 实现子节（~50 行）。覆盖：CLI 表面、关键属性（provenance / 角色映射 / 失败路径 / sentinel / config-init / ledger 双写）、测试覆盖、架构定位。交叉引用 design.md + tests + dogfood 归档路径。
- **ocsr/docs/CHANGELOG.md**：通过 `changelog.py add` 追加 `2026-07-25` 条目：`feat: SKILL.md 新增 converge 治理钩子对接说明`。
- **converge/docs/CHANGELOG.md**（新建）：初始文档，含 2026-07-25 完整条目（adapter 变更内容 + 验证 + 相关引用）。
- **converge retrospective**：`.converge/active/20260725-ocsr-converge-integration/retrospective.md`（~120 行）：过程摘要、关键发现（adapter 决策 / sentinel 模式 / 预算门控）、延后项清单（6 条 + 建议处置）、已知限制、边界违规记录、复盘判定。

---

# 待验收清单（k3 终验）

## 改动文件列表

### converge 仓库（`<user-home>/.agents/skills/converge/`）

| 文件 | 状态 | 说明 |
|------|------|------|
| `scripts/ocsr_spawn_adapter.py` | **新增** | 适配层主体 ~32KB, stdlib only |
| `tests/test_ocsr_spawn_adapter.py` | **新增** | 14 tests (stdlib unittest) |
| `tests/_fake_ocsr_dispatch.py` | **新增** | test shim (4 modes) |
| `refs/framework-adapters.md` | **修改** | §A.2 新增 OCSR Spawn 实现子节 (~50 行) |
| `docs/CHANGELOG.md` | **新建** | converge 变更记录 |
| `docs/dogfood/ocsr-adapter-usage.md` | **新增** | 使用者文档 140 行 (dogfood R2 可执行) |
| `.converge/active/20260725-ocsr-converge-integration/` | **修改** | plan + brief + state + design + reviews |
| `.converge/active/20260725-dogfood-adapter-usage/` | **新增** | dogfood 收敛对象 |
| `.converge/done/20260725-dogfood-adapter-usage/` | **新增** | dogfood 归档 (valid-v1) |

### ocsr 仓库（`<user-home>/.agents/skills/ocsr/`）

| 文件 | 状态 | 说明 |
|------|------|------|
| `SKILL.md` | **修改** | §三 新增 converge Spawn 后端子节 (~35 行) |
| `docs/CHANGELOG.md` | **修改** | 2026-07-25 追加 1 条 |

### 未改动文件（确认无回归）

- `scripts/archive_convergence.py` — **未改**
- `scripts/archive_contract/{capture,model,transaction,presentation}.py` — **未改**
- `scripts/budget_gate.py` — **未改**
- `ocsr/scripts/ocsr_dispatch.py` — **未改**
- converge SKILL.md + CONSTITUTION.md + 所有 refs/*.md（除 framework-adapters.md） — **未改**

## 测试证据

```
Tests:  14 adapter + 69 budget_gate + 85 archive_convergence = 168
Status: ALL PASS (zero failures, zero regression)
Exit:   0

Adapter tests detail:
  TestHappyPath::test_reserve_begin_dispatch_complete_settle            PASS
  TestHappyPath::test_role_outer_reviewer_consumes_outer_scope         PASS
  TestFailurePaths::test_fail_launcher_uses_pre_execution_true         PASS
  TestFailurePaths::test_fail_timeout_uses_pre_execution_false         PASS
  TestReserveGate::test_unknown_role_blocks_before_begin               PASS
  TestArchiveCheckValid::test_event_graph_passes_model_validation       PASS
  TestConfigInit::test_standard_mode_writes_empty_config               PASS
  TestConfigInit::test_ultraverge_mode_applies_blind_rechecks_override PASS
  TestConfigInit::test_explicit_overrides_win_over_ultraverge_default  PASS
  TestConfigInit::test_idempotent_no_force_fails_closed                PASS
  TestConfigInit::test_force_overwrites                                PASS
  TestConfigInit::test_state_file_uses_lf_line_endings                 PASS
  TestBudgetAccounting::test_outer_scope_reservation_blocks_at_ceiling PASS
  TestBudgetAccounting::test_summary_reports_attempted_and_model_inv   PASS
```

## Dogfood 归档验收

```
archive_convergence.py archive: {"archived":"...done/20260725-dogfood-adapter-usage","status":"committed"}
archive_convergence.py check:   valid-v1
Event sequence:                 1-7 continuous (no gaps)
Orphan reservations:            none
Provenance:                     configured (succeeded) | unavailable (failed)
Gate ledger:                    3 reserves all settled (2 succeeded + 1 failed)
```

## CRLF 合规

所有新增/修改文件均为 LF-only（`.gitattributes`: `* text=auto eol=lf`）——无新引入 CRLF。

## 延后项清单（供 k3 决策）

见 `retrospective.md` §延后项：6 条 Phase 1 留下的 suggestion（目标行号已标注，可在一轮 executor 内批量修复；<30 min 总计）。

> 以上。**orchestrator 已按 brief 执行完 Phase 0→4 全流程，停止等待 k3 终验。落地提交（git commit/push）由 k3 验收后执行。**




