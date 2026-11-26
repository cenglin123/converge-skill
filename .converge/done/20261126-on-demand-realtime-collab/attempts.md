# Attempts Log

<!-- append-only -->

## Round 1 Repair (Ultraverge Initial Deliberation)

- source: ultraverge-initial (uv-init-1 glm-5.3-flash, uv-init-2 MiniMax-M3.1-Flash, uv-init-3 deepseek-v4.1-flash-1017)
- verdict_summary: 3/3 阻断需修复（核心发现高度收敛）
- fixes_applied:
  1. Bitter Lesson 分层修正：保留传话编排条件 1（产物已收敛定稿）与条件 2（验收判据机械可核）为硬前置，仅将条件 3（参与方 ≤ 2）与落地载体选择交还 Orchestrator 裁量，消除绕开主循环 M-11/orchest.py 的风险。
  2. 独立审计红线补全：按功能判据覆盖全部 6 类独立评审角色（outer loop / 盲审 / ultraverge / Round 0 / L2 gate / 设计审查），同时禁止 Reviewer↔被审者 与 并行 Reviewer↔Reviewer 共享板，隔离生命周期。
  3. 明确不适用范围：限定实时协同仅用于收敛后落地（C-21），明确不适用于主循环且不减损层级模式「子收敛之间不通信」与「子任务间无实时数据依赖」。
  4. 登记为可选宿主扩展：明示 canonical 路径仍是 Spawn/Continue/Identify，宿主不支持时回退 Spawn/传话，保持框架无关。
  5. 跨文件同步纳入 target_files：新增 `SKILL.md` `d3`、C-21(a)(c) 逐字终态与 `refs/orchestrator-guide.md` §八 全节同步，保留客观执行标识留痕与多 Executor 文件集汇总。
  6. 补齐新路径约束：明确宿主实时协同的载荷成本边界、宪法 #6 独立性降级声明（协作互查不产 verdict）、宪法 #7 不直改产物、以及振荡检测回归全局 Type O/R/F/S。

## Round 2 Repair (Outer Loop Round 1)

- source: outer-reviewer Round 1 (round-1.md, deepseek-v4.1-flash-1017, ses_dec4dd23effeNLAxJx80LT2gnr)
- verdict_summary: 阻断需修复（前 6 项修复 6/6 resolved；新引入 1 项 structural 阻断 B1）
- fixes_applied:
  1. B1：将持续会话/宿主原生实时协同的适用门与载体偏好收口到 `SKILL.md §传话编排` 单一权威定义（均须满足硬前置 1 与硬前置 2；多 Executor 强耦合优先宿主原生能力，不支持回退 Spawn/手工传话），核心角色段、C-21(a) 与 `refs/orchestrator-guide.md §八` 全部改为指针引用。
  2. S1–S5 & S6/S8：删除条件 1 冗余 disjunct 仅留归档 `done/` 机械判据；统一 `retrospective.md` 为执行标识审计权威（frontmatter 为镜像）；补齐宿主实时协同的 Type O 等价振荡守卫；明示该扩展不入抽象能力层/适配层矩阵；明示非默认载体沿用 Plan-Execution 等价纪律；校正 §八 范围 L388–L469 并补 preflight 自检记录。


## Round 3 Repair (Outer Loop Round 2)

- source: outer-reviewer Round 2 (round-2.md, deepseek-v4.1-flash-1017, ses_dec4884e1ffe6M4JxmAh1sWYfm)
- verdict_summary: 阻断需修复（B1 及 S1/S3/S4/S5/S6/S8 全部 resolved；仅剩 B2 即 `refs/orchestrator-guide.md` L399 未同步）
- fixes_applied:
  1. B2 & S-1：将 `refs/orchestrator-guide.md` L399「脚本化映射」段纳入编辑点 5 第 6 项，统一执行标识以 `retrospective.md` 为审计权威（frontmatter 为镜像），并统一 `d3` / C-21(d) / guide L399 三处 `checkpoint-paths` 优先机械生成 + 无统一 commit 边界时降级 LLM 汇总并标注。
  2. S-2 / S-3 / S-6 / S-7：补齐宿主实时协同振荡检测对 Type F 的计数覆盖；将非权威处载体偏好全部收敛为指针引用；明示核心角色表「Executor 全新上下文」作用于收敛主循环；明示已归档 `retrospective.md` 的落地条目为 append-only 追加、不触发 reopen；精确列举 §八 6 个编辑子项。


## Round 4 Repair (Outer Loop Round 3)

- source: outer-reviewer Round 3 (round-3.md, openai-codex/gpt-6.2-sol, 01a213bf-7659-7cc1-bf77-96ec8c75aa82)
- verdict_summary: 阻断需修复（B2 残留 + 新发现 B3/B4）
- fixes_applied:
  1. B2：将 `checkpoint-paths` 仅生成 M 侧列表、前置 commit 要求、未 commit/无统一 commit 边界一律降级 LLM 汇总并标注、N vs M 比较归 Orchestrator 的规则单源定义在 `refs/orchestrator-guide.md` L399，其余三处（`d3` / C-21(d) / 清单项数核对）均改为单源指针。
  2. B3：同步 `refs/orchestrator-guide.md` L407（按 C-21(a) 自主推进落地）与 L401（明示豁免仅限落地执行方，不改动手工传话振荡裁判原有记账约定），并补入 §3 表与 §5 验收 8 项子清单。
  3. B4：移除宿主实时协同路径上新引入的硬停规则，明示不新增停止条件或计数阈值，由 Orchestrator 按板面日志自主识别无效循环并中止/回退 Spawn，彻底对齐 §1/§5「不改变停止条件」声明。
  4. R3-S1/S2/S3：同步 §3 摘要表与 §4 逐字终态、修复编辑点 5 第 1 项外层 4 反引号围栏、在降级声明中补齐「及其对结论可靠性的影响」对应宪法 #6。


## Round 5 Repair (Outer Loop Round 4)

- source: outer-reviewer Round 4 (round-4.md, openai-codex/gpt-6.2-sol, 01a213c4-0f25-7461-a5ad-939b96cf6871)
- verdict_summary: 阻断需修复（B2/B3/B4/R3-S2/R3-S3 全部 resolved；新发现 B5/B6 两项文本精度缺口）
- fixes_applied:
  1. B5：在编辑点 4 `**振荡检测**` 手工传话分支逐字完整恢复原 `SKILL.md` L396 的「输入仅为 relay-ledger」与「orchestrator 保持沉默、不自行做语义判定」全部条文。
  2. B6：三载体（单次 Spawn / 手工传话 / 宿主原生实时协同）执行标识口径全覆盖，明确复用会话时核验的是非 Orchestrator 代改的执行归属而非 fresh 启动证明；将 `plan frontmatter implementation` 在 C-21(c) / guide L399 / guide L418–L420 三处统一为「可作镜像」，`retrospective.md` 为唯一审计权威（已归档时 append-only 不触发 reopen）。
  3. R4-S1：清单项数核对 L424/L427 对齐 L399 单源取数规则，执行方报告用于交叉核验或降级汇总；同步更新 §3 摘要与 §5 验收。

## Blind Recertification 1 Findings (source: blind_recheck)

- source: blind_recheck (blind-recheck-1.md, deepseek-v4.1-flash-1017, ses_dec350f8affetsrZoZ5692QZrL)
- verdict: 阻断需修复
- escalated_issues:
  - BR-1 (architectural, attribution: pending): 向已归档 `retrospective.md` 追加字节违反 Archive Contract v1 `manifest.json` 哈希校验。
  - BR-2 (implementation, attribution: pending): `orchest.py checkpoint-paths` 产出 `implementation_paths`，而非未定义的 `implementation` 字段。
  - BR-3 (implementation, attribution: pending): guide L401「三命令仅限 step f」与主循环 reviewer/blind/continue 过 gate 冲突。
  - BR-4 (architectural, attribution: pending): 会话/成员标识仅佐证启动/在场参与，不能过度宣称证明逐文件写入归属或 fresh 启动。

## Round 6 Repair (Post-Blind-Recertification 1)

- fixes_applied:
  1. BR-1 & BR-2：落地执行标识统一写回**计划文件落地日志节**（配合 `checkpoint-paths` 产出的 `implementation_paths`），明示**绝不向已归档的 `done/<slug>/retrospective.md` 追加字节**，彻底遵守 Archive Contract v1。
  2. BR-3：修正 guide L401 表述为「三命令适用于收敛循环内各角色派发（主循环 reviewer/executor、盲审、Inner Loop Continue），不用于收敛后的落地执行方」。
  3. BR-4：三处诚实降调核验语义——标识为启动/在场参与的客观留痕，不单独证明逐文件写入归属或 fresh 启动。
  4. S-5 / S-6 / S-7：补齐宪法 #7 的 A.4 例外指针、明确功能判据为穷尽标准（括号为示例）、对齐 §3 表与 L418 原/新标题锚点。

## Round 7 Repair (Outer Loop Round 6)

- source: outer-reviewer Round 6 (round-6.md, openai-codex/gpt-6.2-sol, 01a213d4-a8ad-7703-9a6f-7e4eaccdac16)
- verdict_summary: 阻断需修复（BR-1..BR-4 全部 resolved 且归因落定 plan_defect；仅剩 R6-B1 一处 §A.4 例外优先关系措辞）
- fixes_applied:
  1. R6-B1：在 C-21(b)/(c)、§传话编排 角色边界、guide 硬约束第 1 条及执行标识留痕/L399 明确 §A.4（Spawn 完全不可用）的触发条件与优先关系：降级为 `orchestrator_self` 时在计划文件落地日志如实标注 `source: orchestrator_self` 并告知用户影响，不要求也不得伪造独立执行标识。

## Blind Recertification 2 Findings (source: blind_recheck)

- source: blind_recheck (blind-recheck-2.md, deepseek-v4.1-flash-1017, ses_dec1cb51effexZeIcl1qd17IzW)
- verdict: 阻断需修复
- escalated_issues:
  - BR-1 (architectural, attribution: pending): Archive Contract manifest 同时哈希 `done/<slug>/plan.md` 与 `retrospective.md`；须明确点名 `.converge/done/` 之外的项目源计划文件（`docs/plans/...`）及「落地记录」节，并将 `done/` 全部封存文件列为只读。
  - BR-2 (architectural, attribution: pending): 已归档 `done/` 后 `active/<slug>/` 不存在且 `gate-ledger.jsonl` 已封存；须明确手工传话 `relay-ledger`/裁判记账在未封存前与封存后的合法落盘边界。
  - BR-3 (structural, attribution: pending): `scripts/README.md` L97 仍写旧的 `plan frontmatter implementation`，须纳入 `target_files` 同步。

## Round 8 Repair (Post-Blind-Recertification 2)

- fixes_applied:
  1. BR-1：明确落地记录写回 `.converge/done/` 之外的项目源计划文件（如 `docs/plans/active/<slug>.md` 或对应 `docs/plans/done/` 源计划）的「落地记录」节；明示 `.converge/done/<slug>/` 全部封存文件（含 `plan.md`、`retrospective.md`、`gate-ledger.jsonl`）均为只读。
  2. BR-2：明示手工传话 `relay-ledger` 与振荡裁判记账在未封存前沿用 `active/<slug>/`，归档封存后不得回写 `done/` 或重建 `active/`、改记于源计划「落地记录」节。
  3. BR-3：将 `scripts/README.md` L97 纳入 `target_files` 与编辑点 6 同步对齐。
  4. SG-3 / SG-4：将持久会话纪律改为诚实的范围约束表述；修正 §3 表第 1 行摘要区分全局红线与 C-21 裁量权。


## Round 9 Repair (Outer Loop Round 8, after user-authorized outer extension 8→10)

- source: outer-reviewer Round 8 (round-8.md, openai-codex/gpt-6.2-sol, 01a213ec-b654-7380-9710-ba15b8aa1879)
- verdict_summary: 阻断需修复（BR-1/BR-3 resolved，仅剩 BR-2 归档先后顺序与裁判输入/记账路径）
- fixes_applied:
  1. BR-2：彻底消除双态冲突，统一 C-21 落地一律在 `finish` 归档之后执行（与 `SKILL.md` d2→finish→d3 及 `guide` L390 完全一致）；手工传话转发记录、裁判输入（仅取该节转发记录）、裁判 spawn 记录与结论统一落于项目源计划文件「落地记录」节，与落地执行方同享不回写已封存 `gate-ledger.jsonl` 的豁免；同步 `guide` L401 与 L467 边界自检落点。
  2. R8-S1：`scripts/README.md` L97 补入 `checkpoint-paths` 优先 + 无统一 commit 边界时降级汇总并标注的单源指针。

## Blind Recertification 3 Findings (source: blind_recheck)

- source: blind_recheck (blind-recheck-3.md, opencode, ses_debfcc1c7ffeA4a5f9zANlwSoF)
- verdict: 阻断需修复
- escalated_issues:
  - BR-1 (structural, attribution: plan_defect): `refs/state-schema.md` §relay-ledger（L173）仍规定转发日志放在 `active/<slug>/relay-ledger.md`，与编辑点 4 落盘于项目源计划文件「落地记录」节形成单源冲突，且 `refs/state-schema.md` 未列入 `target_files`。
  - BR-2 (implementation, attribution: plan_defect): 编辑点 5 第 7 项（`refs/orchestrator-guide.md` L401 `**显式不适用**`）将 spawn 生命周期三命令适用范围写成局部枚举，遗漏 `scripts/budget_gate.py` `ROLE_CONSUMES` 中的 `ultraverge-initial`、Round 0 合同三方与 `arbiter`。

## Final Pre-Archive Repair (user-authorized terminal-c, blind_recheck: waived)

- acceptance_mode: user-authorized terminal-c, blind_recheck: waived
- fixes_applied:
  1. BR-1：将 `refs/state-schema.md` 加入 `target_files`（4 个文件），在 `§3` 与 `§4` 新增编辑点 7 替换 `refs/state-schema.md` L173（`## relay-ledger` 导语）为因 C-21 落地在 `finish` 归档之后、`.converge/done/<slug>/` 已封存只读且不得重建 `active/<slug>/`，转发记录追加于项目源计划文件（`docs/plans/...`）的「落地记录」节（沿用下方字段集，append-only，不改写）。
  2. BR-2：将编辑点 5 第 7 项（`refs/orchestrator-guide.md` L401 `**显式不适用**`）的三命令适用范围改为全称「spawn 生命周期三命令仅适用于**收敛循环内**全部受门控角色派发（见 `scripts/budget_gate.py` `ROLE_CONSUMES` 及 Inner Loop Continue）」。
  3. 同步更新 `§2 Occam` 与 `§5` 验收第 2 条为覆盖 4 个文件（7 个编辑点）。
