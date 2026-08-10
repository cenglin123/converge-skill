# 变更记录

本文件按时间倒序记录已完成且影响后续维护的变更。

## 2026-08-10

### chore: `docs/` 纳入版本控制

#### 变更内容

- `.gitignore` 移除 `docs/`；`docs/` 下 16 个文件入库（CHANGELOG、plans、problems/bugfix、dogfood）。
- 删除 `docs/.git`——`docs/` 此前**自成一个无远端的嵌套 git 仓库**（3 个 commit，仅 tracked 6 个文件，其余 11 个一直未提交）。完整历史已 `git bundle` 备份到仓库外（`<user-home>/.claude/skills/converge-docs-nested-repo.bundle`）。
- 删除 `docs/.gitattributes`（内容与父仓库逐字相同，只因当初是独立仓库才需要）。
- `README.md` 的目录结构补上 `docs/`、`CONSTITUTION.md`、`archive_contract/` 等此前缺失的条目，并说明 `.converge/`（不入库）与 `docs/`（入库）的分工。
- 一处 CRLF 归一为 LF（`docs/plans/done/20260612-execution-gap-后收敛执行.md`）。

#### 动机

`CONSTITUTION.md` 第四部第 1 条要求「任何对治理文档清单中文件的修改，**须先写入计划文件**」——而这些计划文件此前全部不入库。**修宪程序的审计凭据不在仓库里**，这是内部矛盾。

实证代价：2026-08-10 的阶段 9 计划文档与两位跨族评审的结论（包括否掉一项放宽提案的关键论证）都落在 `docs/plans/`，克隆者一行看不到；要害只能被迫重抄进 `refs/framework-adapters.md`。同一份事实存两处，迟早不一致。

嵌套仓库让情况更糟而非更好：它*看起来*受版本控制（有 commit），但无远端、无备份，且父仓库一次 `git clean -xdf` 就会静默清掉整个历史。

删除前已证明该历史无独有内容：三个 commit 全为纯新增，`git diff HEAD` 对已 tracked 文件为空，工作树即最新状态。

#### 相关

- 同日的 `20260810-ocsr-stage9-wiring` 计划随本次入库，并按完成状态移入 `plans/done/`。

### feat: OCSR 阶段 9 接线 —— 退出码契约 + 终局链路机械化 + run spec 模板

#### 变更内容

- **`ocsr_spawn_adapter.py` 接线 ocsr 新的退出码契约**（0 落盘 / 1 超时 / 2 确定性失败 / 3 路径碰撞，优先级 3>1>2>0）。**破坏性行为变更**：判成功的条件由「产物存在且非空」改为「产物落盘**且** `rc == 0`」——此前 `rc=3`（路径碰撞：本 worker 产物落了盘，但**别的既有文件被覆盖**）会被记成一次干净的 `succeeded` Spawn。失败记录里的 `failure_detail` 现在如实区分「产物缺失」与「产物在但派发失败」。
- **`record-terminal-decision` 的两个字段改为从事件图机械导出**：`supersedes_decision_event_id` 与 `presented_degradations` 缺省则自动填充；调用方给了值且与导出值不符即 `decision-derived-field-conflict` **拒绝写入**（不静默改写）。新增 `derive_presented_degradations` / `derive_supersedes_decision_event_id`（`model.py`，与 `validate_event_graph` 共用同一实现）。
- **`user-decision` 的 `source_ref` / `user_quote` 绑定同样前移到写入前校验**。
- **`_commit_event` 新增 `prepare(fields, existing)` 钩子，在 `EventLock` 内调用**；`reviewer-verdict` 授权检查随之从锁外移入锁内（原先自带一次锁外 `_read_existing`，有 TOCTOU 窗口）。
- **新增 `stamp-decision-markers` 子命令**：把最终决策的 `terminal_decision_event_id` / `terminal_decision_value` 盖进 `retrospective.md` 与最后一个 `round-N.md`（`archive` 逐字比对这两个 marker），替代手抄 UUID。配套 `model.final_decision_summary`。
- **`record-terminal-decision` 新增 typed flags**（`--decision-type` / `--decision-kind` / `--user-quote` / `--source-ref` / …），`--data` 保留兼容；`accepted_state` 由 `--decision-kind` 蕴含（`model.DECISION_ACCEPTED_STATE`）。新增只读诊断 `derive-decision-fields`。
- **新增 `refs/run-specs/terminal-chain.yaml`**：终局链路（`record-user-message → record-terminal-decision → stamp-decision-markers → archive → check`）的 OCSR `run --spec` 模板。只接终局这一段——它失败率最高且完全不含判断；多轮主循环仍归 agent。
- `refs/framework-adapters.md` 补退出码契约小节与「终局链路交给 OCSR 运行器」小节（含诚实边界：运行器不是安全沙箱）。

#### 动机

ocsr 的两次真实收敛在归档处连续失败，全部落在本仓库的 `record-terminal-decision`：`20260809` 两条 terminal-decision 的 `supersedes` 都手填成 null（`decision-chain`）；`20260810` 的 `presented_degradations` 手填成自拟散文（`user-decision-degradations`）。两次都**不可追加修复**。这两个字段本来就是事件图的函数——把它们交给人手填是这类错误的结构性成因。

#### 验证

- 205 tests 全绿（+12：7 条 derived-decision + 5 条 terminal-chain 吃狗粮）。
- **端到端吃狗粮**：`tests/test_terminal_chain_spec.py` 用**真实 ocsr 运行器**执行模板，产出真实归档并独立 `check` 为 `valid-v1`，全程零模型调用。ocsr 位置由 `OCSR_SKILL_DIR` 指定，缺失即 skip。
- 退出码接线有**鉴别力测试**：`collide-but-landed`（产物落盘 + rc=3）在修复前返回 0（记成功），修复后返回 5（recover）。

#### 未落地

`validate_event_graph` 对**已被超越**的 `user-decision` 放宽 `presented_degradations` 校验（原计划 9c）经两位跨族独立评审后**裁定不落地**——界线未被论证，且该损害已由写入前拒绝在上游堵住。评审分歧与遗留缺口见 `docs/plans/active/20260810-ocsr-stage9-wiring.md`。

#### 相关

- 对侧计划：ocsr 仓库 `docs/plans/active/20260810-deterministic-run-spec.md` 阶段 9。
- ocsr 侧对等变更：模板文法新增 `{{steps.<id>.capture.<name>}}`（独立 `hook` 步骤的 `expect` 捕获此前存得进、取不出，而文档写着可被后续步骤引用）。

## 2026-08-05

### feat: kimi-code PreToolUse hook shim（best-effort guarded 可接线）+ M-11 混合后端检查点

#### 变更内容
- 新增 `scripts/hooks/kimi_pretooluse_shim.py`（stdlib only）：kimi-code hook payload 归一化（工具名键变体 `tool_name`/`toolName`/`tool` 容忍）→ 子进程调用 `budget_gate.py hook-pretooluse` → 逐字转发 stdout（deny JSON 与 Claude Code 格式一致，可直接消费）；支持 `--record-session <文件>` 模式挂 `SessionStart` hook 落盘 session_id 供 orchestrator `bind` 前读取。
- `refs/framework-adapters.md` 新增 §A.6 kimi-code：Spawn/Continue/Identify 能力矩阵、继承式模型分层（降档走 OCSR）、接线三件（shim / config.toml PreToolUse+SessionStart 两行 / bind 前读取 session_id）、fail-open 诚实边界与退化矩阵（shim 正常 → best-effort guarded；shim 崩溃/超时/budget_gate 缺失 → auditable-only）。当前 tier 声明维持 auditable-only，接线并端到端验证后方可声明 best-effort guarded。
- `SKILL.md` M-11 新增「混合后端检查点」：混用 gated 通道与原生 spawn 时每次 spawn 前显式确认已过预算门；检测到漏 gate 不停止当前收敛，按 `orchestrator_self` 降级标注并继续、retrospective 申报；附宿主能力矩阵（Claude Code / kimi-code / opencode）与 auditable-only 无机械兜底的明示。
- 新增 `tests/test_kimi_pretooluse_shim.py`：覆盖 payload 归一化、子进程转发、record-session 落盘与失败路径。

#### 验证
- 192 tests 全绿（含新增 shim 测试），无既有测试回归。

#### 相关
- 实证来源：2026-08-04 两次原生 executor 漏 gate 事件与 ultraverge R2 评审锚定污染事件。
- OCSR 侧对等变更：`ocsr_dispatch.py dispatch --forbid-paths`（禁令块注入 + `reads:` 机械审计），见 ocsr 仓库 `docs/plans/active/20260804-ocsr-review-hardening.md`。
- 证据归档 `.converge/done/20260804-ocsr-review-hardening`（check=valid-v1）。

## 2026-07-25

### feat: OCSR ↔ converge 治理钩子对接（事件流 + 预算门控）

#### 变更内容
- 新增 `scripts/ocsr_spawn_adapter.py`（~32KB, stdlib only）：薄适配层，把 `ocsr_dispatch.py dispatch` 包装为 converge Archive Contract v1 的 Spawn 实现——每次 Spawn 原子化为 reserve → begin-invocation → dispatch → complete/recover-invocation → settle 五步。
- 新增 `tests/_fake_ocsr_dispatch.py`（test shim，模拟 4 种 ocsr dispatch 行为）和 `tests/test_ocsr_spawn_adapter.py`（14 tests，覆盖 happy path / fail-launcher / fail-timeout / unknown-role-DENY / outer-reviewer scope / event-graph closure / config-init 6 cases / per-scope BLOCK / summary 双计数区分）。
- `refs/framework-adapters.md` §A.2 新增 OCSR 作为 opencode Spawn 实现子节（provenance 诚实降级策略、sentinel 模式、"edit X"类任务兼容性说明、config-init 辅助、ledger 双写无重复计费）。
- `SKILL.md` 的 `ROOT_FIXED`（`archive_contract/model.py:59`）已自包含 `ocsr-dispatch-ledger.jsonl`——OCSR 派发账本在 v1 归档契约中被视为根级固定文件纳入 manifest，无需回填 schema。
- Provenance 选择：`configured + cli_argument + backend-does-not-expose`（PROVENANCE_MATRIX 下 OCSR 无 per-invocation tool_response 时的 strictest legal honest choice）。`--instance-id`（ocsr batch_id）和 `--receipt` 作为非约束性关联句柄，不升格 evidence level。

#### 验证
- 168 tests 全绿（14 adapter + 69 budget_gate + 85 archive），无既有测试回归。
- 端到端 dogfood：单 reviewer + 单 executor 的真实 converge 链（3 次 adapter Spawn），archive `committed` + check `valid-v1` + sequence 1-7 连续 + 零孤儿 reservation。
- 设计经两轮独立评议（Phase 0 mimo R1 + Phase 1 deepseek-pro R1，均终止-a；Phase 2 mimo R1 终止-a）。

#### 相关
- ocsr SKILL.md §三「作为 converge Spawn 后端」新增对等说明。
- 设计文档：`.converge/active/20260725-ocsr-converge-integration/design.md`
- Dogfood 归档：`.converge/done/20260725-dogfood-adapter-usage/`（valid-v1）
- Plan：`.converge/active/20260725-ocsr-converge-integration/plan.md`

### docs: 新增 adapter 使用文档

#### 变更内容
- 新增 `docs/dogfood/ocsr-adapter-usage.md`（140 行）：使用者文档，覆盖 CLI 表面、调用顺序、provenance 诚实降级、失败路径、sentinel 模式、已知限制。

---

## 2026-07-12 (from README.md)

### 初始版本

converge — 双 Agent 迭代收敛器。SKILL.md, CONSTITUTION.md, refs/, scripts/, tests/。
