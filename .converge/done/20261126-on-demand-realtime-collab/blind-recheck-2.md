---
round: 2
reviewer_backend: opencode
generated_at: 2026-11-25T18:06:31.097621+00:00
invocation_id: b62481a7-43bf-43aa-850d-7e9cc8c553f9
reservation_id: 7ce6019c5739
reviewer_instance_id: ses_dec1cb51effexZeIcl1qd17IzW
verdict: 阻断需修复
---
# Blind Recheck 2 — 20261126-on-demand-realtime-collab

## Reviewer 完整输出

### 结论

```yaml
round: blind-recheck
verdict: 阻断需修复
blocking_issues:
  - id: BR-1
    description: |
      执行标识与落地日志的落盘位置未定义，且计划对 Archive Contract 哈希保护范围的陈述不完整：归档 manifest 同时哈希 plan.md，而不只是 retrospective.md。若“计划文件”指 .converge/done/<slug>/plan.md，按其写入会破坏归档校验，并直接违反计划 §2“不触碰已归档 done/ 封存文件”；若“计划文件”指 docs/plans 下的源计划，计划又未点名具体路径和“落地日志节”的格式。仓库中也不存在可供“复用”的 plan 落地日志节。
    attribution: pending
    severity: architectural
    plan_amendment_required: true
    location: "plan §2 Occam；§3 表 #3；§4 编辑点 3 C-21(b)/(c)；§4 编辑点 5 第 3/6 项；§5 第 2 项"
  - id: BR-2
    description: |
      传话编排在“已归档 done/”之后没有合法的 relay-ledger 与 gate-ledger 落盘位置。计划把适用门条件 1 收紧为“该 slug 已完成终局 decision 并归档 done/”，而主循环 d3 落地执行发生在 finish 归档之后；state-schema 规定 relay-ledger.md 位于 active/<slug>/ 且 append-only，归档根 allowlist 又不含 relay-ledger.md。落到 done/ 会破坏封存，重建 active/ 会产生第二个 authoritative 副本。振荡裁判“记入现有 gate ledger”同样落在已封存且被哈希的 gate-ledger.jsonl 上；计划新增的“不受本豁免影响”句子没有给出可执行的命令路径。
    attribution: pending
    severity: architectural
    plan_amendment_required: true
    location: "plan §4 编辑点 4 适用门条件 1、振荡检测；§4 编辑点 5 第 7 项；refs/state-schema.md §relay-ledger 与 Archive Contract 根 allowlist"
  - id: BR-3
    description: |
      计划未同步 scripts/README.md，导致同一落盘位置存在两套互相冲突的指令：README 仍写“instance_id 记 plan frontmatter”，而计划改后的 C-21(c)/guide §八 写“计划文件的落地记录（plan 落地日志节）”。计划 §2 声称只改 2 个文件，§5 的跨文件核对清单也只覆盖 SKILL/guide；但 guide 本身就指向 scripts/README.md ⑥，执行方会直接读到旧指令。
    attribution: pending
    severity: structural
    plan_amendment_required: true
    location: "scripts/README.md:97；plan §2 Occam；§3 文件改动清单；§4 编辑点 3 C-21(c)；§4 编辑点 5 第 3/6 项；§5 第 2 项"
suggestion_issues:
  - id: SG-1
    description: |
      本计划实质变更了传话适用门这一“一般机制”，但 §1/§5 以“无数值默认/阈值/停止条件变更”为由判定 converge.governance-change/v1 机器块不适用。state-schema 的 numeric_changes 明确支持 kind: mechanism（comparison 可为 null），机制变更并非只能靠散文记录。建议至少说明为何不提供 mechanism 条目，或补一条 mechanism 记录，避免治理变更对机器 preflight 与 task-envelope 门禁不可见。
    location: "plan §1 非变更声明；§5 第 5 项；refs/state-schema.md §converge.governance-change/v1"
  - id: SG-2
    description: |
      SKILL.md L356 仍引用不存在的“§执行阶段”锚点；计划已知悉但明确不修。该锚点与本计划要消除的跨文档矛盾同源，且修改成本极低。建议在同一变更中把 L356 改为“§落地执行编排 / C-21”，或在 §5 中明确登记为遗留项，而不是仅以“不在编辑范围”带过。
    location: "SKILL.md:356；plan §3 表 #5；§5 第 2 项"
  - id: SG-3
    description: |
      guide §八 新增“选用宿主原生实时协同或传话编排时……沿用 Plan-Execution 的等价纪律（自足 prompt、仅读方案文件、不读审计历史）”。但 Plan-Execution 在 refs/executor-prompt.md 中被定义为 fresh-context spawn；持续会话/共享板天然带有既往上下文，“自足 prompt / 仅读方案文件”最多只能作为本次任务的范围约束，不能作为等价纪律。建议明确写出持久会话下保留什么、放宽什么（例如消息自足、仅以方案文件为任务输入、禁止读取审计历史、不主张逐文件归属），避免不可执行的“等价”要求。
    location: "plan §4 编辑点 5 第 2 项；refs/executor-prompt.md §Plan-Execution 模式"
  - id: SG-4
    description: |
      §3 表 #1 把新增段概括为“明确仅适用于收敛后 C-21、不适用于主循环与层级子收敛”，但计划正文的红线本身是全局适用于所有 verdict/审计角色的，只有“宿主原生实时协同”的裁量权才限于 C-21。建议把表内概括改为“红线全局适用；宿主协同裁量权仅限 C-21”，避免执行方误读红线范围。
    location: "plan §3 表 #1；§4 编辑点 1"
reads:
  - '<user-home>\Documents\GitHub\converge-skill\docs\plans\active\20261126-on-demand-realtime-collab.md'
  - '<user-home>\Documents\GitHub\converge-skill\CONSTITUTION.md'
  - '<user-home>\Documents\GitHub\converge-skill\SKILL.md'
  - '<user-home>\Documents\GitHub\converge-skill\refs\orchestrator-guide.md'
  - '<user-home>\Documents\GitHub\converge-skill\refs\reviewer-discipline.md'
  - '<user-home>\Documents\GitHub\converge-skill\refs\state-schema.md'
  - '<user-home>\Documents\GitHub\converge-skill\refs\framework-adapters.md'
  - '<user-home>\Documents\GitHub\converge-skill\refs\executor-prompt.md'
  - '<user-home>\Documents\GitHub\converge-skill\scripts\README.md（grep 读取 L46/L97/L168）'
  - '<user-home>\Documents\GitHub\converge-skill\scripts\orchest.py（L1933-2022、L2070-2119 及 grep）'
  - '<user-home>\Documents\GitHub\converge-skill\scripts\budget_gate.py（L1418-1487、L1735-1824）'
  - '<user-home>\Documents\GitHub\converge-skill\.converge\active\20261126-on-demand-realtime-collab\blind-recheck-2.md（骨架）'
  - '<user-home>\Documents\GitHub\converge-skill\.converge\active\20261126-on-demand-realtime-collab\_orchestrator-state.md'
  - '<user-home>\Documents\GitHub\converge-skill\.converge\done\20260912-o6-material-delta-recert\manifest.json（仅用于核验 plan.md 是否被哈希）'
```

### 1. 前置自检（Q1–Q6）

| 问题 | 结论 | 依据 |
|---|---|---|
| Q1 产物身份自洽 | 部分不通过 | 计划明确是“给 converge-skill 增加可选宿主实时协同 + 独立审计红线”的治理计划；但新增的“计划文件落地日志节”在本计划、仓库模板和 state-schema 中都没有定义，产物声称要“复用”一个不存在的载体。 |
| Q2 产物边界诚实 | 不通过 | C-21(c)/guide 三处都声称执行标识“完全处于 Archive Contract 封存域之外”；归档 manifest 同时记录 plan.md 的哈希。若“计划文件”按最自然的 `.converge/.../plan.md` 理解，该声称不成立（详见 BR-1）。 |
| Q3 产物数据纯度 | 通过 | 计划没有夹带特定项目数据、绝对路径或环境硬编码；宿主协同能力以“可选扩展 + 回退”表述，保持框架无关。 |
| Q4 职责边界自洽 | 基本通过，有张力 | Orchestrator / Executor / Reviewer / 振荡裁判的边界总体清楚；但 guide 要求持久会话“沿用 Plan-Execution 的等价纪律”，与 Plan-Execution 的 fresh-context 定义存在张力（SG-3）。 |
| Q5 命名一致性 | 不通过 | 同一落盘位置出现两种最终指令：“plan frontmatter implementation 条目”（README）与“计划文件的落地记录 / plan 落地日志节”（guide/C-21）；另有旧 C-21 的“retrospective/落地日志”作为第三种历史措辞。这不是措辞差异，而是不同写入面。 |
| Q6 产物 vs 原始需求 | 通过 | 计划的核心主张（审计隔离红线 + 可选宿主协同 + 回退）与背景目标一致，没有方向性偏离。 |

### 2. 阻断问题详述

#### BR-1：执行标识的落盘位置未定义，并与 Archive Contract 的 plan.md 哈希事实冲突

计划在三个位置写入同一段终态文本：

> 统一记录于**计划文件的落地记录（plan 落地日志节，配合 `scripts/orchest.py checkpoint-paths` 产出的 `implementation_paths`）**，完全处于 Archive Contract 封存域之外；**绝不向已归档的 `done/<slug>/retrospective.md` 追加字节**……

问题有三层：

1. **“plan 落地日志节”不是既有约定。** 当前活跃计划、`refs/state-schema.md` 的计划结构、`docs/plans` 下的历史计划都没有这个节；全仓检索“落地日志 / 落地记录”只命中了本计划自身、旧 C-21 的“retrospective/落地日志”措辞，以及一份历史计划中的“落地日志条目”提法，没有任何可复用的节格式。§2 说“复用计划文件落地日志”，但没有可复用的对象，也没有给出新节的字段、插入位置和写入顺序。执行方只能自行发明，无法机械验收。
2. **“完全处于 Archive Contract 封存域之外”只对 `docs/plans` 源计划成立，对归档副本不成立。** `refs/state-schema.md` §Archive Contract 的根 allowlist 明确包含 `plan.md`；我用本仓一个已归档对象核验，`manifest.json` 的 `records` 同时记录 `plan.md`（sha256 `d6525f44…`）与 `retrospective.md`（sha256 `5205…`），并不只保护 retrospective。计划只警告“绝不向 retrospective.md 追加字节”，却把 plan.md 留在风险中。
3. **与计划自身 §2 冲突。** §2 写“不触碰已归档 `done/` 封存文件”。如果“计划文件”是 `.converge/done/<slug>/plan.md`，C-21(c) 的指令就是要求触碰封存文件；如果“计划文件”是 `docs/plans/active/<slug>.md`，计划必须点名这个路径，并说明它在收敛后是否会被移动到 `docs/plans/done/`、写入是否仍安全。当前文本把两种解释都留着，正好覆盖了“违反 Archive Contract”和“写到错误副本”两种失败模式。

这不是措辞问题：执行方按字面执行就可能破坏 `archive_convergence.py check` 的字节校验，或把执行标识写到一个与归档副本不一致的文件里，导致 provenance 分裂。

**建议修法（任选其一，但必须明确）：**

- 明确指定一个 `.converge` 封存域之外的落地记录文件（例如 `docs/plans/active/<slug>.md` 的“落地记录”节，或 `.converge/landing/<slug>.md` 之类的新位置），并给出字段与写入顺序；
- 或者把执行标识写入一个独立的、不受 Archive Contract 管理的文件，并在 C-21(c)/guide 中用同一路径引用；
- 无论哪种，都要把“已归档的 `plan.md` 与 `retrospective.md` 均为只读”写清楚，不能只点名 retrospective。

#### BR-2：传话编排在归档后没有合法的 relay-ledger / gate-ledger 落盘位置

计划把传话适用门条件 1 收紧为：

> **硬前置**：产物已收敛且方案已定稿（该 slug 已完成终局 decision 并归档 `done/`）

这与主循环顺序一致：`d2` 先写 retrospective 并 `finish` 归档，`d3` 才落地执行。因此传话编排只可能在归档之后运行。但传话编排的两个状态载体都在归档域内：

- `refs/state-schema.md` §relay-ledger 明确写：`relay-ledger.md` 放在**收敛对象目录下（`active/<slug>/`）**，与 `attempts.md`、`_orchestrator-state.md` 同级，append-only。
- 归档后 `active/<slug>/` 已被移动到 `done/<slug>/`；Archive Contract 的根 allowlist 不含 `relay-ledger.md`，所以把它放进 `done/` 会被归档树拒绝；重建 `active/<slug>/` 又会形成第二个 authoritative 副本，违反“任一时刻只接受 active、backup 或 done 中一个 authoritative 副本”。
- 计划保留“orchestrator 对每次转发追加一条 relay-ledger 记录”和“relay-ledger 记录格式以 `refs/state-schema.md` §relay-ledger 为唯一单源”，但没有给出归档后的合法位置。
- 振荡裁判同样没有路径：计划说它“记入现有 gate ledger，落在 `total_safety`（1.5）的余量内”，而 `gate-ledger.jsonl` 在 `done/` 内且被 manifest 哈希；计划新增的“手工传话路径中振荡裁判原有的 gate ledger 记账约定不受本豁免影响”只是重述义务，没有给出命令路径。`SKILL.md` L215/L231 要求跨会话机械动作经 `orchest.py`、禁止手跑裸 `budget_gate.py` 序列；即使认为振荡裁判不属于 guide 所说的“收敛后的落地执行方”，`reserve-round` 仍需要 `active/<slug>/` 目录，而该目录在 `finish` 后已不存在。于是振荡裁判既无法经三命令落到 active，也不能手写已封存的 ledger，处于不可执行状态。

这使“手工传话”这条被保留的路径在归档后无法合规运行。新加的宿主原生实时协同路径没有 relay-ledger，反而是自洽的；问题集中在计划没有同步处理旧路径的载体。

**建议修法：**

- 要么把手工传话限定在归档前的窗口，并把 `relay-ledger.md` 加入归档 allowlist / 明确归档后的只读语义；
- 要么把 relay-ledger 与振荡裁判记账移到一个 `.converge` 封存域之外的落地记录（与 BR-1 的落盘位置统一）；
- 要么在归档后只保留宿主原生实时协同，明确手工传话不适用于 post-archive landing，并删除/改写相应条文。三条路必须选一条并在 SKILL/guide/state-schema 之间对齐。

#### BR-3：未同步 `scripts/README.md`，同一落盘位置存在两套指令

当前 `scripts/README.md:97` 写：

> 落地执行（收敛完成后）**不进**上述循环：spawn 走宿主原生 + instance_id 记 plan frontmatter，仅改动清单核对经 `checkpoint-paths`——映射表见 `refs/orchestrator-guide.md` §落地执行编排。

计划改后的 guide §八 和 C-21(c) 则写“计划文件的落地记录（plan 落地日志节）”。这不是同一个位置：frontmatter 与正文“落地日志节”是两种不同的写入面。计划 §2 说只改 2 个受保护文档，§5 的跨文件核对清单也只覆盖 SKILL/guide；但 guide §八 自己就指向 `scripts/README.md` ⑥，执行方按 README 操作会写回 frontmatter，按 guide 操作会写落地日志节，二者不可能同时为真。

**建议修法：** 把 README L97 改成与 C-21(c)/guide 相同的单一落盘位置（或反过来，把 README 降为指针并删除具体位置），并把 `scripts/README.md` 纳入 `target_files` 与 §5 的跨文件核对清单。

### 3. 建议问题

#### SG-1：机制变更未提供 governance-change 机器块

计划的 §1 说“不修改任何数值默认/阈值/停止条件（因此 `converge.governance-change/v1` 机器块不适用）”。但 `refs/state-schema.md` 的 `numeric_changes[]` 明确允许 `kind: mechanism`，且 `comparison` 可为 `null`；本计划把传话适用门条件 3 从“三条缺一不可”改成裁量项，属于一般机制变更，不是纯文字澄清。机器块不是“只有数值变更才用”的载体；它是治理计划 preflight 的唯一机器输入。建议至少补一条 `kind: mechanism` 记录，或明确说明为什么本变更不需要机器记录，避免“无机器块 → 不触发 task-envelope 门禁”成为事实上的绕行。

#### SG-2：`SKILL.md` L356 的“§执行阶段”旧锚点仍然悬空

计划 §3 表 #5 和 §5 已知悉该锚点，但选择不修。它和本计划要消除的跨文档矛盾同源：L356 的“见 §执行阶段/§落地执行编排”中，`§执行阶段` 在 SKILL.md 和 guide 中都不存在。既然本次已经在改 SKILL.md 的 C-21 和 d3，建议顺手把 L356 改为“§落地执行编排 / C-21”，或至少在 §5 把它登记为显式遗留项；不要把“本次新增文本无悬空引用”与“仓库仍有一个已知悬空锚点”混在一起。

#### SG-3：持久会话与 Plan-Execution 的“等价纪律”需要更精确的边界

`refs/executor-prompt.md` §Plan-Execution 模式开头就写“这是一个 fresh-context spawn，不是继续 converge 循环”，Required reading 只有 `<plan_path>`，并明确“不读 attempts.md、round 文件或 contract.md”。计划新增的硬约束却要求宿主原生实时协同/传话编排“沿用 Plan-Execution 的等价纪律（自足 prompt、仅读方案文件、不读审计历史）”。持续会话和共享板天然带有既往上下文，“自足 prompt / 仅读方案文件”只能作为本次任务的范围约束，不能真的等价于 fresh context。建议把“等价”拆成可执行条款：消息自足、任务输入仅限方案文件、禁止读取审计历史、不主张逐文件写入归属；同时明确既往上下文属于已披露的独立性降级，而不是假装不存在。

#### SG-4：新增段的范围概括与正文不完全一致

§3 表 #1 把新增段概括为“明确仅适用于收敛后 C-21、不适用于主循环与层级子收敛”。正文的红线本身是全局适用于所有 verdict / blocking / 收敛裁决 / 独立验收角色的（包括主循环 Reviewer、盲审、L2 gate 等），只有“宿主原生实时协同”的裁量权才限于 C-21。建议把表内概括改为“红线全局适用；宿主协同裁量权仅限 C-21”，避免执行方把红线也缩到落地阶段。

### 4. 关键交叉核对

| 计划主张 | 实际文件/事实 | 结论 |
|---|---|---|
| 落地日志可写在“计划文件”且完全在 Archive Contract 封存域外；计划只点名 retrospective.md 为不可追加对象 | 已归档对象的 `manifest.json` 的 `records` 同时含 `plan.md` 与 `retrospective.md` 的 sha256；state-schema 根 allowlist 含 `plan.md` | 不成立 / 位置未定义（BR-1） |
| 传话编排在归档后仍写 `relay-ledger.md`，格式以 state-schema 为单源 | state-schema 规定 `relay-ledger.md` 位于 `active/<slug>/`；归档后该目录已移走；allowlist 不含该文件 | 不可执行（BR-2） |
| 振荡裁判“记入现有 gate ledger”，且不受落地豁免影响 | `gate-ledger.jsonl` 在 done 内且被哈希；三命令都需要 `active/<slug>/`，而归档后该目录已移走 | 无合法路径（BR-2） |
| 只改 2 个受保护文档即可消除跨文件矛盾 | `scripts/README.md:97` 仍要求 `instance_id` 记 plan frontmatter | 存在第三处矛盾（BR-3） |
| 本次新增/改写文本无悬空引用 | `SKILL.md:356` 的 `§执行阶段` 仍悬空（计划已知悉） | 遗留项，建议同修（SG-2） |
| 机制变更不需要 `converge.governance-change/v1` | schema 的 `numeric_changes` 支持 `kind: mechanism` | 结论过强，建议补记录（SG-1） |

### 5. 审查边界与未读声明

本次为空白上下文盲审：未读取 `attempts.md`、任何 `round-*.md`、`uv-init-*.md` 或 `blind-recheck-1.md`；未使用历史修复记录作为判断依据。为核验 Archive Contract 的事实前提，只读查看了一个已归档对象的 `manifest.json` 与目录清单，以及 `scripts/` 下的机械实现（`orchest.py`、`budget_gate.py`）和 `refs/state-schema.md`；这些都不是本任务的历史审查报告。

`reads` 的完整清单见上方 YAML 块。除此之外仅做了只读的 `grep` / 目录列举 / `Get-FileHash` 核验，没有修改任何仓库文件。

## Orchestrator 处理记录

(pending)