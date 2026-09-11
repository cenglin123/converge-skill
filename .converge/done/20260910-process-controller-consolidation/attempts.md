# Attempt Log - 20260910-process-controller-consolidation

## Round 1 attempt · issue controller-boundary
- source: converge_loop
- reviewer_backend: opencode
- Issue: "计划必须决定这些内容如何降为 Converge 下的 Executor-local/domain handoff guidance，并把所有受影响文件及回归测试列入矩阵；仅删除 scripts/converge_orchestrator.py 不足以完成控制器合并。"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 将 Converge 权限收窄到本 OpenCode 工作流及显式选择 Converge 的编排，并把 init-agent-docs 的 Coordinator/Owner/Reviewer 定义为控制器之下或无 Converge 时由用户管理的领域交接角色。
- Rejected alternatives: 拒绝让所有生成项目依赖 Converge；拒绝仅删除 bespoke controller 而保留文本控制器。
- Upstream scope check: 上溯到 `AGENTS.md.tpl`、`workflow-patterns.md`、SKILL Step 0/8/工作模式段及静态契约测试。
- Diff: `Goal`、`D1. Controller and Handoff Boundary`、两仓 `Exact File Change Matrix`、Phase 1、Controller acceptance criteria。
- R1 verdict: Accepted

## Round 1 attempt · issue loop-semantics
- source: converge_loop
- reviewer_backend: opencode
- Issue: "inner_streak 只统计连续 Executor spawn，并不是宪法要求的‘Executor 修复后 Continue 同一 Reviewer 验收’。文件矩阵仅要求 driver 改默认常量，无法兑现‘显式 max_inner_loops=3 在 manual 和 loop-driver 中允许恰好三次 Continues’。"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 保留 driver 为 fresh-review scheduler，将 Continue 限额与 fresh Executor 重试拆成 `max_inner_loops` 和 `driver_config.max_executor_repair_attempts`，并要求每次修复后进入 fresh Reviewer。
- Rejected alternatives: 当前 OCSR 后端不能忠实保留同一 Reviewer instance，故不虚构 true Continue；也不再让一个数字冒充两种事件。
- Upstream scope check: 上溯到 v1/v2 spec 兼容、driver journal 字段、fresh-review 路由、治理文档和对应测试。
- Diff: `D3` 的 `Continue versus driver repair retries`、Converge 矩阵、Phase 2、Budget and Loop Semantics acceptance criteria、Compatibility。
- R1 verdict: Accepted

## Round 1 attempt · issue budget-config
- source: converge_loop
- reviewer_backend: opencode
- Issue: "计划必须定义唯一配置优先级并让 driver 通过同一 validated state/config-init 路径解析 mode、blind 与 inner，否则 21/23 只在选定 fixture 中成立，不是所有承诺入口的 stock 行为。"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 以 `budget_gate.py` 的 typed initializer/resolver 为 manual、adapter、driver 三路共享边界，规定新建时 mode overlay 后显式值胜出，已有 active state 权威，显式冲突和畸形配置 fail closed。
- Rejected alternatives: 拒绝 adapter、driver 各自复制初始化逻辑；拒绝 resume 静默覆盖 active state。
- Upstream scope check: 纳入 `refs/orchestrator-guide.md`、`ocsr_spawn_adapter.py`、所有实际硬编码 Continue 默认及 empty/active/spec/conflict/malformed 测试。
- Diff: `D3` 的 stock budgets/config initializer/precedence，Converge 矩阵，Phase 2 和 Phase 6 scans，Budget acceptance criteria。
- R1 verdict: Accepted

## Round 1 attempt · issue no-git-closure
- source: converge_loop
- reviewer_backend: opencode
- Issue: "必须逐文件定义 Small × Git/no-Git 的裁剪结果，把承载修复的文件纳入矩阵，并用合成目标断言不存在未安装路径和 Git-only 指令。"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 定义 Small/Medium+ x Git/no-Git 四个精确输出，逐项处理 workflow、AGENTS、README、CURRENT、audit checklist、STRUCTURE、MEMORY、bugfix、maintain 和 pitch 中的无条件 Git/plan/overview 假设。
- Rejected alternatives: 拒绝全局 no-Git；拒绝用“按需裁剪”代替可核对的 profile 合同；拒绝把内部 `assets/references` 复制到目标只为修死链。
- Upstream scope check: 上溯到 medium no-Git 维护脚本不得尝试 Git，以及 generated AGENTS 的 worktree 指针必须指向已安装入口。
- Diff: `D4. init-agent-docs Profile and No-Git Contract`、init-agent-docs 矩阵、Phase 4/5、profile acceptance criteria。
- R1 verdict: Accepted

## Round 1 attempt · issue sync-closure
- source: converge_loop
- reviewer_backend: opencode
- Issue: "四个 assets/hooks/pre-commit-*.sh 当前在失败时都指示运行不带 mode 的 agent_links.py repair；把 parser 默认改为 copy 后，这条指令会把明确选择 hardlink 的项目静默转回 copy。"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 为 copy/hardlink 定义目标 AGENTS 中的精确 repair/check 合同，所有 hook、inline hook、check_all、checklist 和 README 的 remediation 都指回该声明。
- Rejected alternatives: 拒绝让 bare repair 根据新默认猜测项目模式；拒绝削弱 non-force divergence refusal。
- Upstream scope check: 覆盖全部四个 pre-commit shell assets、SKILL inline hook、check_all 和同步测试。
- Diff: `D5. Synchronization Contract`、init-agent-docs 矩阵、Phase 3、sync acceptance criteria 和 migration。
- R1 verdict: Accepted

## Round 1 attempt · issue verification-honesty
- source: converge_loop
- reviewer_backend: opencode
- Issue: "必须把‘静态指导契约’‘脚本 fixture’和‘Agent 行为评估’分开，给前两者可执行命令及结果判据，并明确 Windows 临时路径基线，否则‘两个全量套件通过’和 no-Git 行为验收无法作为确定性 gate。"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 划分静态契约、可执行合成 fixture、Agent/人工行为 eval 三层，仅前两层作为 deterministic gate，并声明 Windows TEMP/TMP 必须用存在的 long-form path。
- Rejected alternatives: 拒绝把 eval-baseline 清单称为机械 runner；拒绝用环境说明豁免规范化后仍存在的真实失败。
- Upstream scope check: 上溯到 Phase 4 fixture 证据、Phase 5 advisory eval、Phase 6 环境记录和验收措辞。
- Diff: `D6. Verification Layers`、Phase 4-6、Verification acceptance criteria。
- R1 verdict: Accepted

## Round 1 attempt · issue scope-occam
- source: converge_loop
- reviewer_backend: opencode
- Issue: "不修改 Constitution/Archive Contract 合理，未为本任务新增控制器或 registry。"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 将新增实体限制为共享 typed initializer 和区分真实事件所需的 driver config；其余修复落入既有文件、测试和 fixture，不新增 controller、registry、renderer、runner 或目标依赖。
- Rejected alternatives: 拒绝为了机械执行 prose 而新建 profile renderer；拒绝复制 skill-internal reference 到生成项目。
- Upstream scope check: 逐项复核矩阵文件均对应已证实矛盾，并列出明确 unchanged files/assets。
- Diff: `Non-Goals`、两仓 `Exact File Change Matrix` 的 unchanged 说明、D6、Ultraverge checklist item 10。
- R1 verdict: Accepted

## Round 1 attempt · issue method-boundary
- source: converge_loop
- reviewer_backend: opencode
- Issue: "D1 应明确‘Every Executor invocation before ready_for_review’的适用边界。Round 0 contract proposer/finalizer 和收敛后的 Plan-Execution Executor 并不都产生 ready_for_review，但同样可能需要完成证据；建议定义为所有会修改产物的 Executor 在交回控制权前执行 completion verification，并逐项说明纯合同提议等只读/文本角色的例外。"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 以“是否修改 durable artifact”而非状态名划线；写产物必验，no-write 分析豁免，非权威 contract proposal 做结构核对，contract finalizer 写文件则必验。
- Rejected alternatives: 拒绝按 documentation/generated artifact 类别 blanket 免 red；拒绝把 Executor 自检升格为 Reviewer 验收。
- Upstream scope check: 同时纳入 UV3 建议“generated artifacts 免红灯应改为基于可测试性和现有 characterization evidence”。
- Diff: `D2. Executor-Local Methods`、Converge method files matrix、Phase 1、Controller and Methods acceptance criteria。
- R1 verdict: Accepted

## Round 1 attempt · issue prompt-process-correction
- source: converge_loop
- reviewer_backend: opencode
- Issue: "prompt-uv-2.md 以‘You are fresh Reviewer 2 in an ultraverge initial review’开头，但没有 reviewer-discipline.md 要求的‘## Mode: <...>’头标。"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 如实记录三个 initial prompt 均漏 `## Mode`，归因为 orchestrator-origin process defect；后续 prompt 在首部使用显式 mode。
- Rejected alternatives: 不回写三个历史 prompt，不把缺失伪装为 Reviewer 或 Executor 过失。
- Upstream scope check: 三份初审均受同一 prompt 构造缺陷影响；本轮只记录事实并修正未来序列。
- Diff: `Authoritative Inputs`、Phase 0 step 2；本 attempts entry 为流程缺陷记录。
- R1 verdict: Accepted

## Post-convergence repair · empirical calibration and recertification
- source: user_external_input
- received_at: 2026-09-10
- Issue: 用户指出计划把有真实历史依据的 `8/3/3` 降为 `3/1/1`，且 ultraverge blind 再降为 `2`，属于忽略既有运行数据后再以 cost-first 事后合理化；要求回到 Git 历史、复盘和知识库方法，形成可机械防复发的最小修复，同时保留已完成的正确未提交实现。
- Issue 归因（外部反馈后复核）: plan_defect + review_process_defect
- plan_amendment_required: true
- Evidence: `0137fce` 记录 outer 实际 `7/12`、blind 实际 `3/4` 且持续推进后将默认调为 `8/3`；`20c8993` 引入 `max_inner_loops=3`；`d3c82cb` 对应真实治理任务到 outer R8 后仍需 blind recheck #2 才通过；`uv-init-1.md:65` 已识别冲突但降级为 suggestion，`retrospective.md:48` 又将其合理化。
- Approach: 恢复新状态 `8/3/3` 并移除 ultraverge blind 倒挂；用 `defaults_version` 冻结已有 v2 运行而不静默迁移；新增窄化的历史证据/经验冲突门、原始用户目标核对、重大修订最终 plan hash 盲审复核、结构化 retrospective calibration sample，并把既有可选 task-envelope 作为全部真实模型调用的任务级成本边界。
- Rejected alternatives: 拒绝保留 `3/1/1` 仅依赖 extension 补救；拒绝用 design review 替代独立 authority recertification；拒绝修改 `CONSTITUTION.md`、新增控制器/registry、自动调参、扩张 issue taxonomy 或新造 task tier/hard cap。
- Bootstrap note: 新 governance preflight 尚未实现，本计划先由 fresh Reviewer 对同等证据做人工门检；Phase 2 落地后必须对本计划机械复跑通过，后续计划无此例外。
- Protected worktree: 两仓现有 D1/D2/D4-D6 与 `init-agent-docs` 未提交实现全部保留，尤其不得恢复已删除的 `scripts/converge_orchestrator.py`；本次文档修订只触碰 active `plan.md` 和追加本 entry。
- Diff: frontmatter/Goal/Authoritative Inputs、`Historical Evidence`、D3、D7-D10、Non-Goals、Converge 文件矩阵、Phase 0/2-4/7-8、验收、兼容迁移、Landing Sequence、Ultraverge checklist。
- Status: pending fresh outer review and final-hash blank-slate recertification

## Post-convergence repair · A/B/C merged blockers
- source: fresh_reviewers
- reviewer_exact_evidence: `77f4e293-2296-471c-b1a0-a509c7c05f71`, `9252ec00-0209-465b-9224-3df2958c21c0`, `e04cc121-ccce-4381-b5f1-4192161df4b4`
- verdicts: `阻断需修复 / 阻断需修复 / 阻断需修复`
- Issue 归因（reviewer 判定）: conceptual + architectural + structural + implementation plan_defect
- plan_amendment_required: true
- Calibration disposition: finish 对当前 revision sample fail-closed；state/ledger/products/attempts/Reviewer terminal 全绑定；productive true/false 必须有 evidence_refs，否则 unavailable；legacy unavailable 不进定量结论；report 带 corpus digest 与 high-water freshness。
- Preflight disposition: 删除散文/表格解析，改为唯一 `converge.governance-change/v1` JSON；机械 empirical gate 仅审有可比样本的数值默认/阈值/停止条件，角色权限和一般机制留给 Reviewer 语义审查。
- Recertification disposition: material 是初审后的记录事实；终局要求不同 outer 与 blank-slate fresh Spawn 审查相同 plan 字节，复用 exact prompt/output 外键链，任何 plan 字节变化使二者失效；reopen 严格通过追加 superseding terminal decision。
- Task-envelope disposition: 承诺收窄为 supported/instrumented dispatch；定义 call_id、Spawn 原子 companion pair、Continue 单 reservation 例外、幂等 settle/cancel、事实驱动崩溃恢复和 accounting_coverage；不完整则 model_invocations=unavailable；明确 opt-in envelope 可能早于 `8/3/3` 阻断且不保证最坏路径可达。
- State/version disposition: 不新增 v3 或迁移命令；未发布 defaults_version=2 的新状态默认直接恢复 `8/3/3`；旧 sparse 状态与显式 active config 保持字节权威；budget state version 与 loop spec version 分离。
- History disposition: 加入 `aac95bd`、`0137fce`、`20c8993`、`d3c82cb` 完整时间线；outer/blind 为实证恢复，inner=3 仅为已发布兼容；`8/3` 是止损上限而非目标用量。
- Scope disposition: 文件矩阵区分既有 dirty baseline 与 r2 delta；`capture.py` 8 行 EventLock 修复及 `test_archive_convergence.py` 35 行测试不归入本轮；复用现有 Archive Contract exact evidence 和 supersedes 字段，不扩 schema。
- Authorization disposition: `bdd405f3-2b03-40eb-9db2-09a32afacae2` 是完整质量目标；`87c4f9f7-72f9-4c45-a2d2-409ae8d83120` 仅是执行授权。删除无条件实施确认，保留既有宪法强制点及 commit/push 审批。
- Reopen disposition: r1 terminal/completed/manifest 与当前显式 `3/2/1` 不改写；当前 Plan Executor invocation `8ec4465c-a6a8-4c0d-8063-30c2543e5b44` 正常收口；最终生成 superseding decision。
- Rejected alternatives: 永久 v2/v3 兼容层、state migration CLI、Archive Contract 扩展、Markdown DSL、host-wide auditable-only 计量保证、新 task tier/cap、单 Reviewer material 终止、post-hoc hash、再次实施确认。
- Status: candidate frozen; requires outer + blank-slate fresh review of the bound plan bytes below

```json
{
  "schema": "converge.material-revision/v1",
  "revision_id": "r2",
  "recorded_after_review": true,
  "trigger_kinds": ["conceptual_or_architectural_blocking", "core_numeric_stopping_change", "empirical_conflict"],
  "triggering_reviewer_invocation_ids": [
    "77f4e293-2296-471c-b1a0-a509c7c05f71",
    "9252ec00-0209-465b-9224-3df2958c21c0",
    "e04cc121-ccce-4381-b5f1-4192161df4b4"
  ],
  "prior_terminal_decision_event_id": "e4182ce3-fe3e-4683-9533-f36ecab465fd",
  "candidate_plan": {
    "path": "plan.md",
    "sha256": "8835f41defa98a9cae76e66ba653acb86389b44594ba46b82c261271a75959d9",
    "size": 30784
  },
  "quality_goal_event_id": "bdd405f3-2b03-40eb-9db2-09a32afacae2",
  "execution_authorization_event_id": "87c4f9f7-72f9-4c45-a2d2-409ae8d83120"
}
```

## R2 same-hash review · locator and exact-evidence blockers
- source: fresh_reviewers
- outer_reviewer_invocation: `775c0a46-3ab9-463c-afb3-11aee26fda6e`（sequence 30 start / sequence 32 terminal）
- blank_slate_invocation: `ab822a65-85ec-4935-a5c4-370c3bcbeb15`（sequence 31 start / sequence 33 terminal）
- verdicts: outer `阻断需修复`; blank-slate `可执行但随 plan 变更失效`
- R2-B1 disposition: 将伪 anchor `plan.md#bootstrap-calibration` 替换为真实唯一 locator `plan.md::json-fence[schema=converge.calibration-report/v1,id=bootstrap-calibration-r2]`；目标 report 增加固定 `id`，定义 Archive root allowlist、严格 fenced-JSON 解析、唯一性、canonical sub-block hash 和 `path-not-found / duplicate-target / wrong-schema` 三类失败及测试。report 子块不引用其自身或整个 plan hash，无自引用不动点。
- R2-B2 disposition: 在 D8 增加 `converge.review-target/v1` 精确 shape、canonical 单行 UTF-8+LF 字节规则、prompt/output locator 及完整 finish 外键链。sequence 30/31 与 32/33 均为 metadata-only，只保留为历史且永久无终局资格；禁止回填。冻结新计划后必须新建 outer + blank-slate prompts，在 Spawn 前 exact capture，输出 exact capture 并逐字回显同一 target payload。
- Invalidation: 旧 candidate `8835f41defa98a9cae76e66ba653acb86389b44594ba46b82c261271a75959d9` 及其两份审查均被本次 plan 字节变更 supersede；不得用于 finish。
- Scope: 仅修改 active `plan.md` 并向 `attempts.md` 追加本条；未改源码、治理文档、测试或既有审查文件。
- Status: candidate frozen; requires two new exact-evidence fresh Spawns against the candidate below

```json
{
  "schema": "converge.material-revision/v1",
  "id": "material-r2-candidate-2",
  "revision_id": "r2",
  "recorded_after_review": true,
  "trigger_kinds": ["architectural_blocking", "review_evidence_binding_failure"],
  "triggering_reviewer_invocation_ids": [
    "775c0a46-3ab9-463c-afb3-11aee26fda6e",
    "ab822a65-85ec-4935-a5c4-370c3bcbeb15"
  ],
  "supersedes_candidate_plan_sha256": "8835f41defa98a9cae76e66ba653acb86389b44594ba46b82c261271a75959d9",
  "prior_terminal_decision_event_id": "e4182ce3-fe3e-4683-9533-f36ecab465fd",
  "candidate_plan": {
    "path": "plan.md",
    "sha256": "ef2e844130a62e33ab8d33c92179f2becabcc27b3c9b929f6c5c3f1d1c3487cb",
    "size": 34302
  },
  "quality_goal_event_id": "bdd405f3-2b03-40eb-9db2-09a32afacae2",
  "execution_authorization_event_id": "87c4f9f7-72f9-4c45-a2d2-409ae8d83120"
}
```

## R2 final recertification · manual-fallback annotations

- [manual-fallback] 预算扩展令牌为手工写入 `_budget-state.json`（budget_gate 无 grant 命令，SKILL 明文允许的逃生门）：`ext-r2-outer-4`（outer 3→4，触发 BLOCK decision `3cf985e1b6fe`）与 `ext-r2-blind-3`（blind 2→3，触发 BLOCK decision `9ad44bad2780`）。用户原话："授权扩展完成双审"（user-message event `29c90690-7bd7-47f1-98a8-f7c727f86216`）。本次耗尽本身是 3/2/1 过小的直接实证。
- [manual-fallback] 最终双审的 reserve/begin/complete 未走 orchest.py reserve-round/register-round：orchest.py 将 prompt/output evidence 硬编码为 metadata-only（`scripts/orchest.py:503` 等），而本计划 D8 要求 exact pre-spawn 证据。改用 budget_gate reserve + `archive_convergence.py begin-invocation/complete-invocation --evidence-mode exact` 等价序列，reservation `8f7d80e83731`（outer round 4 → 产物 round-3.md）与 `abb40a730ae3`（blind round 3 → 产物 blind-recheck-2.md）。
- [manual-fallback] Executor invocation `b6f4e8a3`（sequence 34）在宿主报告 usage limit 前已自行完成 plan 修订并留下孤儿 reservation `b049d3fdc9f3`/`3e93ca1186e5`（sequences 36/37，prompt-r2-exact-*.md，未实际派发）。已按崩溃窗口官方路径 recover(process-interrupted)，事件 `7691a91c`/`d6c2360f`。
- [bug-note] `orchest.py` finish 步骤 3 发现既有 bug：`GATE_TO_RECOVER`（`scripts/orchest.py:100`）值为裸字符串而 `:1067` 按二元组解包，孤儿恢复路径触发 `ValueError: too many values to unpack`。本次用 archive CLI 手工恢复绕过；该 bug 纳入 r2 实施修复清单。
- 终局权威：outer round 4（invocation `fa907aaa-45d1-43d5-a3f2-2215126ac171`）与 blank-slate round 3（invocation `613a54bc-9ab8-49fb-98d7-ea6c4d932958`）均 verdict=可执行、零阻断；四份 `converge.review-target/v1` payload（两 prompt + 两 output）canonical 字节完全一致，plan SHA-256 `ef2e844130a62e33ab8d33c92179f2becabcc27b3c9b929f6c5c3f1d1c3487cb`（34302 字节）冻结后未变。
- [manual-fallback] reservation `0579d0730291` 是主对话在确认 Executor 已落盘后创建的多余备用预约，随即 pre-execution 取消，从未派发；因 settle-无-started 形态触发 archive 孤儿硬校验，finish 步骤 7 改用 `archive --declare-orphan-reservation 0579d0730291` 显式披露（不绕过、不回填）。`orchest.py finish` 不暴露该参数属既有设计，本次为披露式手工归档。
- [manual-fallback] 候选 3 双审（outer round 5 / blind round 4，reservation `4bd2541195c7`/`5e56487eb781`）同样因 orchest metadata-only 硬编码走手工 exact 序列。outer reviewer 按 prompt 写入 `round-5.md`，与既有"round 4 预约 → round-3.md 产物"的连续编号冲突（gate `round_gap:outer` fail-closed 实证）；完成登记前将 in-flight 产物归位为 `round-4.md`（未改写任何已登记内容）。扩展链：`ext-r2-outer-4→ext-r2-outer-5`、`ext-r2-blind-3→ext-r2-blind-4`，用户授权事件 `d2232c8d-76f9-4cd0-8164-fdcd45411d65`。
- 候选 3 终局权威：outer round 5（invocation `59e4c977-2a95-4a78-904d-4c2a383a2593`）与 blank-slate round 4（invocation `48626e28-7e2f-41b1-992f-f515a03866c7`）均 verdict=可执行、零阻断；四份 `converge.review-target/v1` payload canonical 字节一致；plan SHA-256 `c56e656d4d1486f49a95e74b73b6932219c97ad978834bff36d96d8b12dc6059`（38827 字节）。终局 decision `777a0e2d-859f-462d-80a5-7d135d5f04b5`（supersedes `ea64c374`）。
- Suggestions 处置：S1（配对豁免收窄到 process-interrupted）——记录为未来收紧候选，本次按计划实现的宽式放行（pre_execution cancelled ↔ failed）已由双审通过，不再变更计划字节；S2（仓库根 99MB 未跟踪 `NUL` 垃圾文件）——与本计划无关，报告用户另行清理；S3（GATE_TO_RECOVER 的 `"failed"` 键为死键）——采纳进 D11 实施：以 settle 事件名 `spawn_failed`/`cancelled` 为键。
- 归档次序决策：本对象的 archive 依赖 D11 代码落地（否则 ledger-status-conflict 永拦），故收敛对象的 finish/archive 推迟到实施与最终审计完成之后执行；期间 active 目录保持冻结证据，retrospective 追加实施结果后再归档。
- [manual-fallback] 设计评审 begin-invocation 的 `reservation_id` 被误写为字面量 `PENDING`（真实预约 `81a2537ea9eb` 同命令创建）。经用户授权（user-message `bbdffdc8-5bdf-4c6a-8ae7-9943514968df`）作披露式更正：事件 55 的 `reservation_id` 修正为 `81a2537ea9eb`；原值 `PENDING` 在此披露保留。契约封闭字段校验拒绝内联披露字段，故披露仅存于 attempts/retrospective。
- 后续对象：r2 暴露的操作包络层缺口已落盘为独立计划 `docs/plans/active/20260911-converge-operational-envelope.md`（用户 2026-09-11 指示：先收尾 r2，再修操作层）。

## R2 archive-closure conflict · D11 pairing clarification and recovery repair
- source: archive_contract_mechanical_block + user_external_input
- Issue: 最终归档被 Archive Contract 机械拦截 `ledger-status-conflict`：reservation `b049d3fdc9f3`/`3e93ca1186e5`（sequences 36/37）已开始 invocation 但从未派发模型，预算账本结为 `cancelled`(`pre_execution=true`)，归档恢复终态记为 `failed`/`process-interrupted`（events `7691a91c-e97c-4797-b87e-abc04929cec1`/`d6c2360f-19c4-454e-8660-1054a464875f`）；`validate_ledger` 一致性表要求 cancelled↔cancelled 精确配对，两边 append-only 不可改写，矛盾永久固化。
- Issue 归因（复核）: contract_semantics_gap（口径澄清）+ implementation_defect（`GATE_TO_RECOVER` 裸字符串被二元组解包）
- plan_amendment_required: true
- User ruling history: 既往用户事件 `65c07569-b27e-48f6-bc9a-2854977dcf4c`（直接裁决接受口径澄清，补丁式实现后已被用户撤回并回退）已被事件 `d2232c8d-76f9-4cd0-8164-fdcd45411d65`（"走正常流程确保没有问题更好"）取代；两事件均保留为不可改历史。澄清正式纳入 plan D11 经评审后实施，代码不写裁决/日期式补丁注释，历史由 git/archive 承载。
- Pairing disposition: `validate_ledger` 中 `cancelled` 且 `pre_execution=true` 的结算允许配对 `failed` 恢复终态（共同断言"从未调用模型"）；非 pre_execution 的 cancelled 仍只配 cancelled，其余配对规则不变。行为语义澄清，非 schema 扩展：无新事件类型/字段，两个 append-only 流不改写不回填。
- Schema wording disposition: `refs/state-schema.md` 加一句规范句（不写日期/裁决者）：pre_execution cancelled 结算与 failed 恢复终态是同一事实在预算层与归档层的两种词汇。
- Recovery-path disposition: `scripts/orchest.py` `GATE_TO_RECOVER`（:100）修成显式 `(status, reason)` 映射，消除 finish 步骤 3（:1067）解包 `ValueError: too many values to unpack`；`tests/test_orchest.py` 加 finish 干跑/真实恢复回归。
- Matrix disposition: `scripts/archive_contract/model.py` 由 "No change" 改为上述窄澄清；`refs/state-schema.md` 由 Clean baseline 改为加规范句；`tests/test_archive_convergence.py` 增两个回归（pre_execution cancelled+failed 放行；非 pre_execution cancelled+failed 仍 `ledger-status-conflict`）；`scripts/orchest.py` 追加 GATE_TO_RECOVER 修复；新增 `tests/test_orchest.py` 行；`scripts/archive_contract/capture.py` 明确不动。
- Acceptance disposition: 澄清后本对象 `archive --declare-orphan-reservation 0579d0730291` 能通过且 check valid；GATE_TO_RECOVER 修复后 finish 恢复路径有回归测试。
- Materiality: 本修订改核心机制校验语义，按 D8 疑义 fail-closed 判为 material，触发双 fresh 同字节复核；本对象 archive 阻塞即触发证据。
- Invalidation: 旧 candidate `ef2e844130a62e33ab8d33c92179f2becabcc27b3c9b929f6c5c3f1d1c3487cb`（candidate-2）已被本次 plan 字节变更 supersede；其双审结论不适用于新字节。
- Scope: 仅修改 active `plan.md` 并追加本条；未改源码、治理文档、测试或既有审查文件。
- Status: candidate frozen; requires two new exact-evidence fresh Spawns against the candidate below

```json
{
  "schema": "converge.material-revision/v1",
  "id": "material-r2-candidate-3",
  "revision_id": "r2",
  "recorded_after_review": true,
  "trigger_kinds": ["architectural_blocking", "review_evidence_binding_failure", "archive_contract_closure_conflict"],
  "triggering_reviewer_invocation_ids": [],
  "triggering_user_message_event_ids": [
    "65c07569-b27e-48f6-bc9a-2854977dcf4c",
    "d2232c8d-76f9-4cd0-8164-fdcd45411d65"
  ],
  "supersedes_candidate_plan_sha256": "ef2e844130a62e33ab8d33c92179f2becabcc27b3c9b929f6c5c3f1d1c3487cb",
  "prior_terminal_decision_event_id": "e4182ce3-fe3e-4683-9533-f36ecab465fd",
  "candidate_plan": {
    "path": "plan.md",
    "sha256": "c56e656d4d1486f49a95e74b73b6932219c97ad978834bff36d96d8b12dc6059",
    "size": 38827
  },
  "quality_goal_event_id": "bdd405f3-2b03-40eb-9db2-09a32afacae2",
  "execution_authorization_event_id": "87c4f9f7-72f9-4c45-a2d2-409ae8d83120"
}
```

