---
round: 3
reviewer_backend: opencode
generated_at: 2026-11-25T18:41:24.920935+00:00
invocation_id: 8fcdc6a5-a21e-4ef5-b0de-4cb9fd00e29b
reservation_id: df20dd0426c5
reviewer_instance_id: ses_debfcc1c7ffeA4a5f9zANlwSoF
verdict: 阻断需修复
---
# 盲审复核报告（Round 3 · 空白上下文）

> 本次审查在**未读取任何修复历史**的空白上下文中完成：未打开 `attempts.md`、`round-1..9.md`、`blind-recheck-1/2.md`、`uv-init-1..3.md`，也未读取任何历史审查结论。以下判断仅基于待审计划、宪法、机制文档与脚本实现。

## 0. 审查范围与基准

- 待审产物：`docs/plans/active/20261126-on-demand-realtime-collab.md`（最终版计划）。
- 宪法基准：`CONSTITUTION.md` §一（Bitter Lesson 三分判据 / Occam）、§二（#6 降级告知、#7 Planner 不执行）、§三（治理文档清单）。
- 契约基准：`refs/state-schema.md` §Archive Contract v1（规范单源）、§relay-ledger。
- 机制基准：`SKILL.md`（核心角色、主循环 `d2→finish→d3`、C-21、§传话编排、M-11、配置参数）、`refs/orchestrator-guide.md` §八、`scripts/README.md`、`refs/reviewer-discipline.md`。
- 实现基准（只读核对，不做状态变更）：`scripts/orchest.py` §6 `checkpoint-paths`、`scripts/budget_gate.py` `ROLE_CONSUMES`、`scripts/converge_loop.py` ultraverge 初审派发。

## 1. 结构化输出

```yaml
round: blind-recheck
verdict: 阻断需修复
blocking_issues:
  - id: BR-1
    description: |
      转发记录的落盘位置在最终文本中仍有两个互相矛盾的规范来源，且计划声称已消除冲突。编辑点 4 要求手工传话的每次转发记录（以及振荡裁判 spawn/结论、boundary_violation_pending）追加到「项目源计划文件」的「落地记录」节；但 `refs/state-schema.md` §relay-ledger（L171–L173）仍以规范语句规定该日志就是 `relay-ledger.md`、放在收敛对象目录 `active/<slug>/` 下并与 attempts.md 同级。该文件属 `CONSTITUTION.md` §三 保护清单，计划既未列入 `target_files`，也未对其条款做任何范围限定。由于 C-21 落地固定发生在 `finish` 归档之后，`active/<slug>/` 已不存在，按 state-schema 落盘物理上不可行；按 SKILL.md 落盘又使 state-schema 的规范条款失效——两份治理文档无法同时被遵守。计划 §5.2 却判定「全部一致」「无悬空引用与规范冲突」。同一根因还遗留 `SKILL.md` L452 `relay_oscillation_interval` 的「输入仅 relay-ledger」表述，与新的「落地记录」节形成第二处措辞分叉。
    attribution: pending
    severity: structural
    plan_amendment_required: true
    location: 计划 §4 编辑点 4（SKILL.md §传话编排「振荡检测」段）；§5.2 跨文件核对结论；对照 refs/state-schema.md §relay-ledger（L171–L173、L177）
  - id: BR-2
    description: |
      编辑点 5 子项 7 的逐字终态把 spawn 生命周期三命令的适用范围写成「仅适用于收敛循环内各角色派发——主循环 reviewer/executor、盲审、Inner Loop Continue」。该穷尽式枚举与仓库既有角色表和实现直接冲突：`scripts/budget_gate.py` 的 `ROLE_CONSUMES` 还注册了 `ultraverge-initial`（scope=ultraverge）、`contract-proposer` / `contract-challenger` / `contract-finalizer`（Round 0）与 `arbiter`；`scripts/converge_loop.py` 的 `do_parallel_review`（「ultraverge 初审：N reviewer 批量并行」）明确调用 `drv.reserve("ultraverge-initial", ...)`，而该 driver 的 reserve 即 `orchest.py reserve-round`。计划自身新增的独立审计红线段也把「Round 0 合同挑战 Reviewer」「ultraverge 并行 Reviewer」「仲裁/振荡裁判」列为需要隔离的独立评审角色。按「仅」字面执行，会让 ultraverge 初审、Round 0 合同三方与仲裁 spawn 绕过 reserve-round，直接抵触 M-11「禁止在未取得 PROCEED 时 spawn」；这正是本次改动试图守护的预算记账边界，却在同一节的适用范围声明中被挖开。
    attribution: pending
    severity: implementation
    plan_amendment_required: true
    location: 计划 §4 编辑点 5 子项 7（refs/orchestrator-guide.md L401 逐字终态）
suggestion_issues:
  - description: |
      `SKILL.md` L356（M-11）仍保留「落地执行 spawn 豁免（设计裁决，见 §执行阶段/§落地执行编排）」，其中「§执行阶段」在本仓不存在对应章节，是悬空锚点。计划已在 §5.2 明确将其排除在本次编辑范围外，但本次改动恰好重写了落地执行豁免的语义；建议顺手改为「见 §落地执行编排」，避免同一治理变更交付后仍留一个已知悬空引用。
  - description: |
      宿主原生实时协同路径的振荡处置存在机制不对称：手工传话路径用一个一次性独立「振荡裁判」并规定 orchestrator「保持沉默——不自行做语义判定」；宿主协同路径则改由 Orchestrator「依据宿主板面与执行日志自主识别反复推翻或往返翻转等无效循环」。后者把手工路径刻意剥离给独立 agent 的语义判定又收回给已被判定为「独立性降级」的 Orchestrator。建议要么给出等价的最低独立信号（如周期性 fresh 板面摘要复核），要么在文中显式说明该不对称及其理由，避免读者认为红线段「独立审计」要求被绕过。
  - description: |
      `refs/orchestrator-guide.md` §八 硬约束逐字终态第一条使用「必须由独立执行方落地」，但同段又允许「持续会话/共享消息板」参与方并承认「持续会话不主张 fresh 上下文」。此处「独立」若指「独立于 Orchestrator」应改写成「不得由 Orchestrator 兼任 executor 或直接编辑产物」；若指 fresh 上下文，则与允许持续会话的裁量自相矛盾。当前措辞会让 C-21(b) 的证据边界（不证明 fresh 启动）与硬约束产生解释冲突。
  - description: |
      `refs/executor-prompt.md` §Plan-Execution 模式（L112–L120）声明「这是一个 fresh-context spawn」「不读 attempts.md、round 文件或 contract.md」。当 C-21(a) 选用手工传话或宿主原生实时协同时，该模板的自我描述与载体事实不符。建议在 §八 硬约束中补一句：非 Spawn 载体不得沿用该模板的 fresh-context 声明，须按 §传话编排 的范围约束改造 prompt。
  - description: |
      C-21(c) 要求记录「宿主协作会话标识、实际执行成员标识及所选协作方式」，但未定义这些标识的最小形态，也未规定宿主不暴露成员标识时的处置（记录 `unavailable` 并回退 Spawn？）。作为「客观执行标识」要求，建议给出最小字段或明确「宿主不提供即按不可用如实标注并降级」，否则该条在部分宿主上无法验收。
  - description: |
      计划 §1「背景与目标」只写「同步更新 `SKILL.md`（主循环 `d3`、C-21、传话编排）」，遗漏了 §3/§4 中新增的「核心角色表后独立审计红线」这一首要改动。§3 表格与 §5.2 均包含该项，三处范围描述不一致，建议统一，防止执行者按 §1 少改一处。
  - description: |
      本次改动触及「角色与权限」（落地阶段允许持续会话/共享板参与方、独立审计角色隔离红线）与振荡裁判的预算适用性。按 `refs/orchestrator-guide.md` §Material revision 的 `decisional` 定义（角色与权限、fail-closed 行为、File Matrix 等），该修订很可能属 `decisional`，须在 attempts.md 记录 `converge.material-revision/v1` 块并执行同字节双权威（outer + blank-slate）复核。计划 §5.4 只写了 ultraverge 流程，建议显式声明该分级与双 Spawn 复核义务；`converge.governance-change/v1` 机器块确实不适用（无数值默认/阈值/停止条件变更），这两件事不应混为一谈。
  - description: |
      C-21(c) 的「（亦不触发 reopen）」过于绝对。落地期间若发现方案本身有缺陷，`SKILL.md` §收敛后修订 的 reopen 通道仍是合法逃生舱。建议限定为「不因追加落地留痕而自动 reopen」，并注明方案缺陷仍按 §收敛后修订 由用户输入触发，避免关闭宪法 §一 要求的逃生舱。
antipattern_observations:
  - type: minimum_patch
    evidence: |
      计划把改动严格限定在 SKILL.md / orchestrator-guide.md / scripts/README.md 三文件，并以「不新增 refs/state-schema.md 字段」作为免改理由；但转发记录从 `relay-ledger.md` 迁到源计划「落地记录」节改变的是**位置与规范归属**，不是字段集。最小补丁绕过了真正的单源冲突（BR-1），使 state-schema 的规范条款原地失效。
  - type: solution_anchoring
    evidence: |
      编辑点 4/6 与 §5.2 反复以「`.converge/done/<slug>/` 已封存只读」为锚点推导落盘位置，但未回头校验 `refs/state-schema.md` §relay-ledger 的既有位置条款是否仍成立；锚定在「不能写 done/」这一半结论上，跳过了「那 state-schema 怎么改」的另一半。
reads:
  - docs/plans/active/20261126-on-demand-realtime-collab.md
  - CONSTITUTION.md
  - SKILL.md
  - refs/orchestrator-guide.md
  - scripts/README.md
  - refs/reviewer-discipline.md
  - refs/state-schema.md (L20-64, L150-219)
  - refs/framework-adapters.md (L30-59)
  - refs/executor-prompt.md (L108-170)
  - scripts/orchest.py (L1930-1999)
  - scripts/budget_gate.py (L92-113)
  - scripts/converge_loop.py (reserve 封装与 ultraverge 初审派发)
  - refs/quality-gate.md (grep: reserve/角色名)
  - refs/reviewer-prompt.md (grep: 盲审变体)
  - .converge/active/20261126-on-demand-realtime-collab/blind-recheck-3.md (输出骨架，仅此文件)
```

## 2. 阻断问题详解

### BR-1 · 转发记录的单源分裂（structural）

**事实链**

1. 计划编辑点 4 的逐字终态规定：手工传话路径下，「orchestrator 对每次转发在项目源计划文件（`docs/plans/...`）的「落地记录」节追加一条转发记录（字段格式仍沿用 `refs/state-schema.md` §relay-ledger 单源）」；振荡裁判 spawn 与结论、`boundary_violation_pending` 同样记入该节。
2. `refs/state-schema.md` §relay-ledger 的规范语句仍为：「## relay-ledger（`relay-ledger.md`）……放在收敛对象目录下（`active/<slug>/`），与 `attempts.md`、`_orchestrator-state.md` 同级。」该节还规定 append-only 与字段集。
3. `refs/state-schema.md` 属 `CONSTITUTION.md` §三 保护清单；计划 `target_files` 只有 `SKILL.md`、`refs/orchestrator-guide.md`、`scripts/README.md`，且 §1「非变更声明」写明「不修改 `CONSTITUTION.md`」、§2 写明「不新增 `refs/state-schema.md` 字段」——但这回避了**位置条款**，位置条款不是「字段」。
4. 时序使旧条款不可满足：C-21 落地固定在 `finish` 归档之后（计划 §5.2 自述 `d2→finish→d3`），此时 `.converge/done/<slug>/` 已封存、`active/<slug>/` 被禁止重建。`relay-ledger.md` 无处可放；即便放回 active 也会因 Archive Contract 根 allowlist 不含 `relay-ledger.md` 而在归档 check 处被拒。
5. 计划 §5.2 断言「本次新增与改写文本无悬空引用与规范冲突」，与上述事实不符；`SKILL.md` L452 的「输入仅 relay-ledger」也未同步。

**为什么是阻断而非措辞建议**

这不是「字段格式沿用哪份文档」的表述问题，而是**同一份必需日志有两个互斥的规范位置**：执行者按 state-schema 做会失败（目录不存在），按 SKILL.md 做会违反 state-schema 的规范语句。该冲突位于本次改动的正中心（转发记录正是被迁移的对象），且计划以「无规范冲突」作为可执行判据之一。零阻断要求下不能带着一个已知的规范单源分裂交付。

**最小修复建议**

- 将 `refs/state-schema.md` 加入 `target_files`，在 §relay-ledger 增加一段限定：`relay-ledger.md` 仅用于收敛循环内的传话（如存在）；收敛后 C-21 落地路径的转发记录写入项目源计划文件「落地记录」节，字段集与 append-only 语义不变，该节为落地路径的唯一落盘位置。因 state-schema 受保护，本就属 ultraverge 范围，不改变流程等级。
- 同步 `SKILL.md` L452 `relay_oscillation_interval` 的「输入仅 relay-ledger」为「输入仅为「落地记录」节中的转发记录」或等价表述。
- 修正 §5.2 的「无规范冲突」结论为「已同步 state-schema §relay-ledger 的范围限定」。

### BR-2 · 三命令适用范围枚举与实现/角色表冲突（implementation）

**事实链**

1. 计划给出的 guide L401 终态：「spawn 生命周期三命令仅适用于**收敛循环内**各角色派发——主循环 reviewer/executor、盲审、Inner Loop Continue」。
2. `scripts/budget_gate.py` `ROLE_CONSUMES`（L98–L106）注册的角色除上述外，还含 `ultraverge-initial`（scope=ultraverge）、`contract-proposer`、`contract-challenger`、`contract-finalizer`、`arbiter`。
3. `scripts/converge_loop.py` `do_parallel_review`（L609–L626）注释即为「ultraverge 初审」，并对每个 reviewer 调用 `drv.reserve("ultraverge-initial", ...)`；`Driver.reserve`（L461–L473）组装的是 `orchest.py reserve-round`。
4. 计划自身编辑点 1 的红线段把「Round 0 合同挑战 Reviewer」「ultraverge 并行 Reviewer」「仲裁/振荡裁判」都列为独立评审角色。
5. `SKILL.md` M-11 的原文是「收敛循环内每次 spawn（reviewer / executor / **各类角色**）」，并未把范围收窄到三个具名角色。

**为什么是阻断**

「仅适用于」是排他性规范语句。执行者若照字面理解，会认为 ultraverge 初审、Round 0 合同三方、仲裁不需要（甚至不应该）走 `reserve-round`。这些 spawn 若不走 gate，即违反 M-11「禁止在未取得 PROCEED 时 spawn」，并使 `max_ultraverge_initial` 预算与 ledger 记账失效。该句正是用来界定「落地执行例外」的，误伤收敛流程内的受控角色，属于把例外写成了新的漏洞。

**最小修复建议**

二选一：

- 删除枚举，改为「spawn 生命周期三命令适用于收敛流程内的全部角色派发；不适用于收敛后 C-21 落地执行（含手工传话振荡裁判）」；或
- 补全枚举：「主循环 reviewer/executor、盲审、Inner Loop Continue、ultraverge 初审、Round 0 合同三角色、仲裁（L2 gate 按 `refs/quality-gate.md` 既有 `budget_gate.py reserve --role l2-gate-reviewer` 约定，不经 orchest）」。

## 3. 已核对且通过的关键项

| 核对项 | 结论 | 证据 |
|---|---|---|
| 宪法 §一 三分判据 ①机制不执行任务 | 通过 | 仅新增适用门与红线，不替代 reviewer/executor 判断 |
| 宪法 §一 ②不收窄解空间、逃生舱可用 | 基本通过（S-8 建议澄清 reopen） | 默认仍为 Spawn；`需重新设计` 与 §收敛后修订 保留 |
| 宪法 §一 ③契约违反 fail-closed、判断分歧 fail-open | 通过 | 条件 1/2 为硬前置；载体选择与条件 3 交裁量 |
| 宪法 §二 #6 降级告知 | 通过 | 手工与宿主两条路径都要求告知「独立性降级模式及其对结论可靠性的影响」 |
| 宪法 §二 #7 Planner 不执行 | 通过 | C-21(b) 与 guide 硬约束均保留 §A.4 `orchestrator_self` 例外并要求标注 |
| Archive Contract v1 封存边界 | 通过 | 落地记录完全落在 `.converge/done/<slug>/` 之外，不追加字节、不重建 active、不 reopen |
| `d2→finish→d3` 时序 | 通过 | 与 `§传话编排` 条件 1、guide L390 一致 |
| 层级模式不变量 | 通过 | 明文不减损 L514「子任务间无实时数据依赖」与 L519「子收敛之间不通信」 |
| 行号锚点 | 通过 | SKILL L252/L356/L379/L385–L398、guide L388–L469（L394–397/399/401/407/413–416/418–420/422–429/433/467）、README L97 均与磁盘一致 |
| `checkpoint-paths` 事实性 | 通过 | `orchest.py` L1977–L1990 确实输出 `implementation_paths:`，且依赖 commit（`git diff-tree`） |
| 数值默认/阈值/停止条件 | 通过 | 未改任何默认值；`relay_oscillation_interval` 仍为 3 |
| 独立审计红线覆盖 | 通过 | 功能判据 + 角色示例穷尽，含并行 Reviewer 互不共享 |
| 可选宿主扩展不新增抽象能力 | 通过 | 明示非第四能力、不入适配层矩阵、宿主不支持即回退 |

## 4. 总体判断

方向与架构成立：把宿主原生实时协同严格限制在收敛后 C-21、以 `Spawn` 为 canonical 路径、把不可封存的落地留痕移出 Archive Contract 域，均符合宪法 §一 的分层判据与 §二 #6/#7。问题不在设计取向，而在**规范单源没有收口**（BR-1）与**例外条款的适用范围写反了边界**（BR-2）。两处都是可局部修复的文本/范围缺陷，不构成重写或重新设计。

因此本轮 verdict 为 **阻断需修复**。BR-1、BR-2 修复后，应再以 fresh 盲审复核最终字节（含 state-schema 的新增限定句）方可进入 `finish`。

## 5. reads（如实记录）

- `docs/plans/active/20261126-on-demand-realtime-collab.md`（全文）
- `CONSTITUTION.md`（全文）
- `SKILL.md`（L1–L547，全文）
- `refs/orchestrator-guide.md`（L1–L546，全文）
- `scripts/README.md`（L1–L180，全文）
- `refs/reviewer-discipline.md`（L1–L300，全文）
- `refs/state-schema.md`（L20–L64、L150–L219）
- `refs/framework-adapters.md`（L30–L59）
- `refs/executor-prompt.md`（L108–L170，另 grep commit/落地/instance_id）
- `scripts/orchest.py`（L1930–L1999）
- `scripts/budget_gate.py`（L92–L113）
- `scripts/converge_loop.py`（reserve 封装 L457–L511、ultraverge 初审 L600–L634，另 grep）
- `refs/quality-gate.md`（grep：reserve/spawn/角色名）
- `refs/reviewer-prompt.md`（grep：盲审/共享/消息板）
- `.converge/active/20261126-on-demand-realtime-collab/blind-recheck-3.md`（仅读取输出骨架并覆写正文）

**确认未读取**：`attempts.md`、`round-1.md`～`round-9.md`、`blind-recheck-1.md`、`blind-recheck-2.md`、`uv-init-1.md`～`uv-init-3.md`、`_orchestrator-state.md`、`gate-ledger.jsonl`、`.converge/done/**` 及任何历史审查报告。

## Orchestrator 处理记录

(pending)