# 变更记录

本文件按时间倒序记录已完成且影响后续维护的变更。

## 2026-08-10

### chore: `20260725-ocsr-converge-integration` 按 legacy 归入 `done/`——`active/` 清空

与上一条同样的处置。**`.converge/active/` 现在为空**，两项悬置全部落定。

#### 情况：做完了，产物已上线，但契约要件不全

`_orchestrator-state.md` 记 `current_phase: completed`，`retrospective.md` 记 `status: completed`（终止-a，各 Phase 设计审查与代码审查均零阻断首轮通过）。产物 `scripts/ocsr_spawn_adapter.py` 已随 `5d8aff5` / `6bcdc21` 上线。

比 `flow-prior-legitimacy` 多了三样：`_orchestrator-state.md`、`retrospective.md`、`ocsr-dispatch-ledger.jsonl`（9 行）。但仍缺 `gate-ledger.jsonl` / `_budget-state.json` / `evidence/events/` / `manifest.json` / `round-N.md` / `attempts.md`——`archive` 同样 `events-missing` fail-closed。

一处值得记的讽刺：它的 Phase 3 dogfood **是**正经归档的（`.converge/done/20260725-dogfood-adapter-usage`，至今 `valid=True`）——**被验证的是适配层，而验证适配层的那场收敛自己没被验证。** 其 `_orchestrator-state.md` 另自报 `boundary_check: violated-but-documented`。

#### 占位化时抓到一个真实的清洗盲区

脚本的替换表原先只有 `C:\Users\<用户名>` 与 `C:/Users/<用户名>` 两种形态。`ocsr-dispatch-ledger.jsonl` 里 15 处只命中 4 处——**JSON 里的 Windows 路径是转义过的双反斜杠 `C:\\Users\\<用户名>`**，不匹配单反斜杠形态。

脚本的 `assert` 残留检查 当场拦下，**拒绝写出半清洗的文件**。补上转义形态后 15 处全清。转义形态必须排在单反斜杠形态**之前**，否则会被后者切成两半、留下半截 `\Users\<用户名>`。

顺带复查了**已经公开**的 `origin/master`：`.converge/done/` 与 `docs/` 里残留的用户名只有 2 处，正是既有取舍中刻意保留原字节的那两个受 manifest 保护的文件——早前几批清洗没有被这个盲区漏掉。

#### 验证

`ocsr-dispatch-ledger.jsonl` 含 CRLF，入库后 `git ls-files --eol` 显示 `i/crlf w/crlf attr/-text`——**这是 `.converge/done/** -text` 在本仓库第一次真正吃到活儿**：没有它，这个文件的索引字节就会被悄悄改成 LF。

| 项 | 结果 |
|---|---|
| 新增文件 | 17，全部 `attr/-text` |
| 索引与工作树字节不一致 | **0** |
| `check-git-ref --from-index` | 仍 `valid = True` |
| `scan .converge/done` | 17 个：1 valid + 16 legacy-unverifiable |
| `.converge/active/` | **空** |

### chore: `20260725-flow-prior-legitimacy` 按 legacy 归入 `done/`

`.converge/active/` 里悬了 16 天的这一项，查明是**做完了、产物也上线了，但整场收敛从头到尾没走契约机制**——不是漏跑 `archive`，是当时根本归不了档。

#### 它确实做完了

完整 ultraverge：三族并行初评（`review-ds` 可执行 / `review-mimo` 可执行 / `review-glm` **阻断需修复**）→ 修复后复评 `review-r2` 可执行、零阻断 → 盲审复核 `review-blind` 可执行、零阻断 → **强制设计审查** `design-review.md` 可执行、`deterministic_check: pass`、仅 3 条 suggestion。设计审查是 ultraverge 的最后一步，链条走到底了。

产物（plan.md 的目标是「三仓库贯彻流程先验合法性判据」）三处全部落在各自默认分支：

| 仓库 | 落点 | commit |
|---|---|---|
| converge | `CONSTITUTION.md` L32-34 | `dace767` |
| ocsr | `SKILL.md` L64 | `33c8bf2` |
| init-agent-docs | `SKILL.md` L157 | `4f1a92c` |

#### 为什么归不了档

契约要件**一个都不存在**：无 `_orchestrator-state.md` / `attempts.md` / `retrospective.md` / `round-N.md` / `gate-ledger.jsonl` / `_budget-state.json` / `evidence/events/`。目录里只有 `plan.md`、`prompts/`、`reviews/`、`artifact/*.diff`、`design-review.md`——**全是人工命名的文件，没有一个是机器写的**。`archive` 在这种状态下必然 `events-missing` fail-closed。

时间线上说得通：`20260712-archive-contract` 才刚把契约建起来，`20260725` 当天还在同时跑 `ocsr-converge-integration`（把 OCSR 接进事件流那件事）——**契约当时正在被搭建，尚未成为默认路径**。这是过渡期的产物。

#### 处置

**不补造证据。** 归档要的 invocation 事件对、reservation、settlement 都是「当时发生了才有」的事实，事后造出来就是伪造。按 legacy 处理：移入 `.converge/done/`，以 `legacy-unverifiable` 身份入库——与另外 14 个 pre-contract 归档同类。`scan` 会机械地把它报成 `legacy-unverifiable`，无需在目录里再放一个说明文件（那反而是「rewrite legacy archive in place」）。

入库前把 13 个文件里的真实用户路径占位化为 `<user-home>`（该归档无 manifest，改写不破坏任何哈希）。

#### 同批次的另一项：`20260725-ocsr-converge-integration`

**同样的病，程度较轻**（已在下一条中同样处理）。它有 `_orchestrator-state.md`（`current_phase: completed`）、`retrospective.md`（`status: completed`，终止-a）和 `ocsr-dispatch-ledger.jsonl`（9 行），但同样缺 `gate-ledger.jsonl` / `_budget-state.json` / `evidence/events/` / `manifest.json` / `round-N.md` / `attempts.md`——`archive` 同样会 `events-missing`。产物（`scripts/ocsr_spawn_adapter.py`）已随 `5d8aff5` / `6bcdc21` 上线。

有意思的是它的 Phase 3 dogfood **是**正经归档的（`.converge/done/20260725-dogfood-adapter-usage`，至今 `valid=True`）——**被验证的是适配层，验证适配层的那场收敛自己没被验证**。

其 `_orchestrator-state.md` 还自报了 `boundary_check: violated-but-documented`。

### chore: `.converge/done/` 纳入版本控制

#### 变更内容

- `.gitignore` 由忽略整个 `.converge/` 改为只忽略 `.converge/active/` 与 `.converge/tmp/`；`done/` 下 **118 个文件**入库。
- `.gitattributes` 新增 **`.converge/done/** -text`**。归档是内容寻址的，manifest 按字节记录 sha256 + size，而 `* text=auto eol=lf` 的换行归一化会改字节。**实测：去掉该行，`done/` 下 14 个 CRLF 文件的索引字节即与工作树不一致**（它们全在 legacy 归档里、无 manifest，所以没有任何东西会报错——静默改写证据）。
- 删除 `.converge/.git`——`.converge/` 此前也是一个**无远端的嵌套 git 仓库**（1 个 commit，仅 tracked 30/118 个文件）。历史已 `git bundle --all` 备份到仓库外并 `verify` 通过；删前已证明其无独有内容（单个纯新增 commit，`git diff HEAD` 为空）。
- **legacy 归档中 4 个文件的真实用户路径占位化为 `<user-home>`**（这 4 个所在归档均无 manifest，改写不破坏任何哈希）。

#### 刻意未做：唯一 valid 归档中的 2 个文件保持原字节

`20260725-dogfood-adapter-usage` 是 15 个归档里**唯一** `check` 通过的（其余 14 个是 `legacy-unverifiable`，无 manifest）。它的 `ocsr-dispatch-ledger.jsonl`（在 `manifest.records` 中）与一个 event JSON 含真实用户路径。

**实测：占位化后 `check` 立刻变成 `valid=False`（`content-mismatch`）。** 字节完整性与路径隐私在这两个文件上真实冲突，无两全解。用户裁定：**保持原字节**——宁可公开这一处路径，也不让唯一可机械复验的归档变成永久无效，更不为此伪造归档状态（违反「不得覆盖证据 / 不得伪造归档成功状态」）。

#### 验证

| 项 | 结果 |
|---|---|
| 入库文件数 | 118，无 gitlink |
| `git ls-files --eol` | 全部 `attr/-text`；索引与工作树字节不一致数 = **0** |
| **从 git 索引**复验 manifest（`check-git-ref --from-index`） | `valid = True` |
| `scan .converge/done` | 1 valid + 14 legacy-unverifiable（与入库前一致） |
| `active/` `tmp/` | 仍被忽略，0 文件入库 |

#### 附带修正：`check-push-range` 把「无契约可校验」当成了「契约违反」

入库后第一次推送即被 `pre-push` 拒绝——`check-push-range` 对 14 个 `legacy-unverifiable` 归档判 `valid: false` 并阻断。

该检查原先把两件事混为一谈：

- **契约违反**——manifest 存在，字节/事件图与之不符。这是 hook 要抓的篡改，必须阻断。
- **没有契约可校验**（`legacy-unverifiable`）——归档早于 Archive Contract v1，压根没有 manifest，无从篡改检测。

不做区分的后果是：**pre-contract 归档永远无法进入版本控制**。首次提交必被拒，而"修复"它需要重写归档本身——`check_archive` 自己的 `next_action` 明说不许（"do not rewrite legacy archives in place"）。这是缺一条合规路径，不是刻意选择的策略。

改法遵循仓库既有的 `archive --declare-orphan-reservation` 形状：**豁免是调用点显式 opt-in，不烧进检查器**。

- `check-push-range` 新增 `--allow-legacy`（默认关闭，CLI 默认行为**不变**）
- `scripts/hooks/pre-push` 三处调用显式带上该参数，并把理由写在调用点上方
- 被豁免的 slug **打印到 stderr**——没人看见的豁免，与从未运行过的检查无法区分

两条回归测试：① 豁免只对「唯一诊断是 `legacy-unverifiable`」生效，契约违反与混合诊断仍阻断，且默认关闭时三者全阻断；② hook 的三处调用都必须带该参数，CLI 签名默认必须仍是 `allow_legacy: bool = False`。

#### 动机

归档是这套治理机制**唯一的事后凭据**：`pre-push` hook 早就在跑 `check-push-range` 校验「本次推送范围内改动过的 done 目录」——它本来就是按 `done/` 入库设计的，只是 `done/` 一直不在库里，**那条检查从来没有真正跑过真实数据**。上面那处缺陷正是这次第一次跑才暴露的。

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
