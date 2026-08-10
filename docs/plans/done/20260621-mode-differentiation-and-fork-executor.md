---
type: plan
status: done
resolution: "Part A 落地（PR #4 / commit 5e61d14+042d74a）；Part B dropped（GD-2，2026-06-21——rigor-escalation 发散 + Bitter Lesson 判 fork 为贬值补丁）"
created: 2026-06-21
scope: 两项改进——(A) ultraverge 与普通 converge 的模式分层（盲审预算 + 自主执行）；(B) Executor 改用「context 继承变体 spawn」（fork orchestrator 上下文）减少重读/漂移
governance: true
note: 动 SKILL.md / refs/executor-prompt.md / refs/framework-adapters.md / CONSTITUTION（#7 解释）/ 配置参数——按明线规则走 ultraverge（≥3 Reviewer + 收敛 + 设计审查）+ 人工提交批准
trigger: 用户提出两项改进建议（模式分层 + fork executor），要求评估后落计划
related:
  - "SKILL.md"
  - "CONSTITUTION.md"
  - "refs/executor-prompt.md"
  - "refs/framework-adapters.md"
  - "refs/orchestrator-guide.md"
  - "GOVERNANCE-DECISIONS.md"
---

# 模式分层 + Fork Executor

## 摘要

两项相互独立的改进，合并为一个计划走 ultraverge（均触碰治理文档）：

- **Part A — 模式分层**：把 ultraverge 与普通 converge 在两处区分开。(A1) 普通 converge 的**盲审预算降为 1**（ultraverge 经 config 覆盖保持 2）；(A2) 普通 converge **默认自主执行到完成**，仅在宪法强制点向用户确认，移除非必要的中途 check-in。A1 需两处真实源码改动（`scripts/budget_gate.py:55` 默认值 2→1、`tests/test_budget_gate.py:604` 期望同步），**裁决逻辑零 diff**；具体 stock 总量上限：**普通 converge = 42，ultraverge = 44**（单调、无下溢）。
- **Part B — Fork Executor**：把**收敛循环内的 Executor** 从「fresh-context Spawn + 自足 prompt」改为「**继承 orchestrator 上下文的 spawn 变体**（fork）」，省去 executor 重读 plan/attempts/round/contract 的开销、降低消息传递的语义漂移。Reviewer 与落地执行 Executor **不变**（仍 fresh Spawn）。

两项都不是纯文档修正——它们改变运行语义与角色模型，**必须走完整 ultraverge**，Part B 还需对 CONSTITUTION #7 作一次显式解释裁决。

---

## 背景与动机（用户原始建议）

> 1. 对 ultraverge 和普通 converge 进行区分，后者的盲审预算改为 1，且非必要情况下不要向用户确认，而是尽可能直接执行到任务完成。
> 2. converge 里的 executor，能否改为 fork orchestrator 的主对话进行任务执行，而不是还要 orchestrator 通过特定格式传递消息给它？本质上只有 reviewer 需要上下文独立，executor 仅是执行；现状下 executor 执行前还要根据 orchestrator 给的任务去阅读理解相关内容才能开始，浪费 token 也浪费时间，且消息传递可能偏差导致上下文漂移。直接 fork 可尽量不漂移、省 token 和时间。

---

## Part A — 模式分层

### A1. 盲审预算分层（普通 → 1，ultraverge → 2）

**现状**：`max_blind_rechecks = 2`，对普通 converge 与 ultraverge **一视同仁**；盲审仅在收敛经历 ≥2 轮 outer loop 后触发（SKILL.md §盲审复核）。

**评估**：合理且低风险。普通 converge 绝大多数在 1 轮评议内完成（"严格首轮通过"是默认目标），根本不触发盲审；只有走到 ≥2 轮的多轮收敛才会用到盲审预算。对这类普通收敛，1 次盲审复核足以提供"空白视角再认证"，第 2 次盲审的边际发现概率低、却抬高总 spawn 上限与决策菜单频率。ultraverge 面向宪法/治理/基础架构产物，保留 2 次盲审的冗余有其价值。

**设计（path (a)：让轻量值成为真实默认 —— 需两处真实源码改动，裁决逻辑零 diff）**：

诚实前提：盲审默认值物理上写死在 `scripts/budget_gate.py:55`（`DEFAULTS["max_blind_rechecks"] = 2`），且 `tests/test_budget_gate.py:604` 断言 stock 默认 `cap=44`。因此「降默认值」无法做到 budget_gate.py / tests **零行数 diff**——必须改这两行。本计划采纳 **path (a)**：把轻量值设为真实默认，并同步测试期望。

- **真实改动 (i)**：`scripts/budget_gate.py:55` —— `DEFAULTS["max_blind_rechecks"]` 由 `2` → **`1`**。这是普通 converge 的新真实默认。
- **真实改动 (ii)**：`tests/test_budget_gate.py:604` —— stock 默认 cap 期望由 `44` → **`42`**；并新增/调整一条断言：当 config 覆盖 `max_blind_rechecks=2`（即 ultraverge 路径）时 cap = **44**。
- **裁决逻辑零 diff**：`budget_gate.py` 的 `cfg()` / `reserve` / `validate_integrity` 等裁决路径**完全不动**——它读 config 值裁决，不感知模式名。本计划仅改一个默认常量值 + 其测试期望，不改任何分支或算术。
- ultraverge 路径在初始化 `_budget-state.json` 时写入 **config 覆盖 `max_blind_rechecks = 2`**（复用既有 config 覆盖机制，见 state-schema.md §预算 gate；**纯 orchestrator 行为，零代码**）。
- `max_total_reserved_spawns` 的确定性公式含 `max_blind_rechecks` 项。基数 = `3 + ultraverge_min_reviewers(3) + max_outer_loops(5)×(1+max_inner_loops(3)) + max_blind_rechecks + 1 = 27 + max_blind_rechecks`。故：
  - 普通 converge（mbr=1）：`ceil(1.5 × 28)` = **42**。
  - ultraverge（config 覆盖 mbr=2）：`ceil(1.5 × 29)` = **44**。
  - 两者均 > 任何单轮所需 spawn 数，单调递增、**无边界下溢**（Q4 结论已定，见下）。

**语义澄清（必须写清，否则 Reviewer 会挑战）**：盲审预算 = 1 意味着——做 1 次盲审；通过则收敛；若盲审出阻断 → findings 升级、Executor 修复、fresh Reviewer 验收通过后，**不再做第 2 次盲审**，直接收口（retrospective 记 `blind_recheck: pass`，注明单次盲审 + 修复）。若修复后仍需再盲审却已超预算 → `BLOCK:blind_exhausted` → 决策菜单（此为宪法第二部 #3 强制点，不可省，见 A2）。

### A2. 普通 converge 默认自主执行

**现状**：终止-a（严格首轮通过）已无需确认、自动归档；但落地执行需用户"后续要求"（SKILL.md 主循环 d3）。实践中 orchestrator 倾向在多个非强制点追加 check-in。

**评估（核心是确认点分类，不能一刀切"不确认"）**。用户意图是"非必要不确认、直达完成"，但 CONSTITUTION 第二部 #3/#5 与 GD-1 设了不可移除的硬确认点。必须把确认分两类：

| 确认点 | 类别 | 处置 |
|--------|------|------|
| 终止-a（零阻断首轮通过） | 非强制 | **已自主**，保持 |
| 收敛后落地执行（原始指令含执行意图——**机械明线**：指令含执行动词「并执行 / 落地 / apply」等才算；否则不算自主授权，仍需确认） | 非强制（GD-1 已授权默认预算 + 落地） | **改为默认自主推进**，不再追加"现在要执行吗"check-in |
| `需重新设计` verdict | 强制（方向性缺陷） | 保留——必须报告用户决定重写/缩范围/主观接受 |
| 终止-b / 终止-c（渐近 / 主观接受） | 强制（宪法 #1/#5） | 保留显式确认 |
| 预算软停 / `budget_exhausted` / `blind_exhausted` / `MODE_SWITCH_REQUIRED` | 强制（宪法 #3/#5，GD-1 不授权扩展/切换） | 保留决策菜单 |
| `FAIL_CLOSED` / `DENY:illegal_role` | 强制（状态损坏/非法） | 保留停机 |

**结论**：A2 的可落地内核是——把"非强制确认点"显式标注为**默认自主**，让普通 converge 在原始指令含执行意图时一路跑完 终止-a → 落地，无中途请示；同时**逐字保留**全部宪法强制确认点。这不是"少确认"，是"把自主与强制的边界写成明线规则"，消除 orchestrator 的过度保守。

**与 GD-1 的关系**：GD-1 已确认"走 converge 并执行"授权 (a) 推进至默认预算、(b) 落地执行；A2 不扩大授权，只是把这条已批准的授权落到执行流程的明线，避免 orchestrator 在已授权范围内仍反复请示。

**与 Part B 的耦合约束（H2 折入 —— 不得叠加独立性削弱器）**：A2 的自主落地是三个"独立性削弱器"之一（另两个：Part B fork executor 更易锚定；A1 盲审 2→1 削弱 fresh-eyes 兜底）。**禁止在同一默认路径上叠加三者**：当某次**普通模式**运行**同时**采用 forked executor **且**走 A2 自主落地时，盲审预算**生产默认保持 2**（或必须插入一轮 fresh、非 fork 的验收）——不得降到 1（见 §不变量 #9）。即：A1 的 blind=1 只在该运行**未**叠加 fork+自主落地时生效。**该 blind=2 生产约束的「保留 vs 松绑」由不变量 #8 的 2×2 pilot 实证裁决**（Cell A 干净 → #9 松绑；Cell A 升高、Cell B 干净 → #9 保留为生产硬约束；两单元均升高 → Part B 阻断；详见 #8 决策矩阵）——pilot 前 #9 一律按保守默认 blind=2 生效。

### Part A 改动清单

| # | 文件 | 改动 |
|---|------|------|
| A-1 | `SKILL.md` 配置参数表 | `max_blind_rechecks` 默认 2→1；新增脚注：ultraverge 经 config 覆盖回写 2 |
| A-2 | `SKILL.md` 配置参数表（`max_total_reserved_spawns` 行） | (i) **公式术语对齐（值恒等，消除文档符号 `max_ultraverge_initial` 与代码命名 `ultraverge_min_reviewers` 的分歧；当前公式数值已正确）**：将公式中的 `max_ultraverge_initial` 改为 `ultraverge_min_reviewers`（对齐代码 `budget_gate.py:349`，base 实际取后者）；(ii) 把 stock 参数注解由「= 44」改为**模式相关：普通 = 42 / ultraverge = 44**；脚注写明两组数已重算、单调、无下溢 |
| A-3 | `SKILL.md` §Ultraverge 路径 | 增一行：ultraverge 初始化时写 `max_blind_rechecks=2` config 覆盖 |
| A-4 | `SKILL.md` 主循环 / 终止状态表 | 增「确认点分类」明线：标注哪些为默认自主、哪些为宪法强制确认（引用上表）。「原始指令含执行意图」给出可机械检验的明线：指令含执行动词（如「并执行 / 落地 / apply」）才算自主授权，否则仍需确认（防 orchestrator 滥用「autonomous」跳过本应保留的确认） |
| A-5 | `SKILL.md` 主循环 d3 | 落地执行：原始指令含执行意图（同 A-4 明线判据）时默认自主推进，删除非必要 check-in 语义 |
| A-6 | `refs/orchestrator-guide.md` | 同步落地执行编排：默认自主推进的判据（含 A-4 执行动词明线）+ 强制确认点清单 |
| A-7 | `scripts/budget_gate.py:55` | `DEFAULTS["max_blind_rechecks"]` 默认值 `2` → `1`（path (a) 真实改动 (i)；这是普通 converge 新真实默认）。**裁决逻辑（cfg/reserve/validate_integrity）不动** |
| A-8 | `tests/test_budget_gate.py:604` | stock 默认 cap 期望 `44` → `42`（path (a) 真实改动 (ii)）；新增/调整断言：config 覆盖 `max_blind_rechecks=2`（ultraverge）时 cap = `44` |

> **注**：path (a) 下 `scripts/budget_gate.py` 与 `tests/` 并非零行 diff——A-7/A-8 是两处必需的真实改动。但 budget_gate.py 的**裁决逻辑零 diff**：仅改一个默认常量值及其测试期望，不动任何分支或算术。ultraverge 的 mbr=2 仍由 config 覆盖（零代码 orchestrator 行为）实现。

---

## Part B — Fork Executor（context 继承变体）

### 评估

**用户洞察成立的部分**：独立性是 **Reviewer** 的本质需求（对抗式交叉验证、fresh-eyes 盲审、双重测试独立运行）；**Executor 从来不靠独立性提供价值**——它只是执行修复。现状 Executor 每轮 fresh Spawn 后必须重读 `plan + attempts + round-N + skill + contract` 才能动手，这是 orchestrator 上下文里**已有**的信息，重读纯属重新派生。fork（继承上下文）省掉这步、并消除"orchestrator → 结构化文件 → executor 重新解读"链路上的重新派生偏差。**架构上方向正确。**

**必须诚实对待的三个张力（否则 Reviewer 会阻断）**：

1. **CONSTITUTION #7「Planner 不执行」（裁决中的主张，非定论）**。一种**待仲裁的主张**是：fork 出的是**独立 agent 实例**，真正持笔写文件的仍非 orchestrator 实例本身——机械层面的"谁持笔"角色分离未破；#7 的立法意图是"防止 orchestrator 亲自抄起编辑工具、边界蔓延"，约束**持笔者身份**而非**持笔者上下文**，据此 fork "不违反 #7 字面"。

   **本轮 ultraverge 实际裁决（split ruling，记入此处）**：3 名 Reviewer 一致认为 fork **在字面上**合规 #7（持笔者是独立实例）；但其中 1 名 Reviewer（及设计审查视角）持保留意见——#7 的立法意图保护的是角色分离的**认知独立性**，而 fork 通过继承 orchestrator 叙事**削弱**了这一独立性，故该问题落在**灰区**。结论：字面合规已获共识，**意图层是否合规存争议**，残余决定（是否需为 #7 加解释性附注）上交 CONSTITUTION 第四部人工审议（见 Q1、B-5）。

   **生成式边界对本张力的约束（H1 折入）**：上述认知独立性顾虑正是**生成式 fork 边界**（见 §设计 适用边界）要回答的——fork 仅授予"其产出受下游 fresh、独立 reviewer 机械复核"的角色，故收敛循环 executor 的认知独立性缺失由 inner-loop fresh reviewer 补偿；落地/R0 executor 因无此下游复核而被原则判否、保持 fresh。第四部审议 #7 时应以该生成式原则（而非角色封锁清单）为评估对象。

2. **路径依赖防护（executor-prompt §1–§7）反折中/打破"过往同意"锚定**。这些纪律本就为对抗"对历史轮次的锚定"。fresh executor 读 attempts.md 时不带 orchestrator 的叙事框架；**forked executor 继承 orchestrator 全程叙事（含其自身的滚动解读），可能比读去叙事化 attempts.md 的 fresh executor 锚定得更强**。这是 Part B **最强的技术反对意见**。处置：保留 **§1–§7 全部纪律**（§4–§7 在 fork 下同样失去 fresh-context 兜底，必须一并显式重申，不只 §1–§3），并在 executor-prompt fork 变体中**显式重申**"继承的历史只是 fact 不是 commitment，本轮按 reviewer 本轮要求做"——把纪律从"靠 fresh context 自然获得"转为"靠显式指令维持"。该补偿的有效性**不假定成立**，须经验收硬门 pilot 对照验证（见不变量 #8、Q2）。

3. **token 节省是有条件的，不能夸大；且 fork 非单框架特性（H3 折入，张力3 重写）**。fork 省的是 executor 重读那几个文件的成本；但 fork **继承 orchestrator 整个上下文**（含用户对话、历轮输出、历次 reviewer prompt），到收敛中后期这通常**大于**目标必读集。因此：**延迟下降（省去重读往返）与漂移降低是稳健收益；原始 token 节省只在 orchestrator 上下文 < executor 必读集时成立（多见于前 1–2 轮）**。计划**不主张无条件省 token**，而是主张"延迟 + 抗漂移"为主、token 中性到正向、并在 pilot 中实测（见验收）。

   **H3「单框架补丁」前提已被实证证伪——不对称论证撤销**：跨框架实测确证 fork 在 **3 框架中 2 个**原生可用（Claude Code + Codex 0.141.0，后者实测验证），opencode 干净降级 fresh。故 H3 原论证里"只有一个框架真正使用它 / 治理复杂度只为一个框架承担"的**不对称性已不成立**——撤销该论证，**不**把 fork 当作"Claude-Code-only 补丁"。**保留 H3 的较弱版本**：重读开销确随上下文经济学（更长上下文 / 更便宜 token）改善而收缩，故 fork 优化收益可能随时间下降——据此给 fork **挂一个 sunset / 重评触发条件**（绑定上下文经济学，由 #8 pilot + 周期重评把关），但这是跨框架的成本-收益再评估，**不是单框架补丁**。

### 设计

**作为 Spawn 的「上下文继承变体」而非新原子能力（遵守 Occam）**。抽象能力层仍是 Spawn / Continue / Identify 三原子；fork 表述为 **Spawn 的一个参数化变体**：`Spawn(context=inherited)` vs 默认 `Spawn(context=fresh)`。框架不支持继承时**降级为 fresh Spawn**（语义等价、无功能损失，仅失去省读收益）。

**适用边界（生成式原则，非封锁清单 —— H1 折入）**：

> **治理规则（governing principle）**：**上下文继承（fork）仅允许用于：其产出会被下游 fresh、独立 spawn 的 reviewer 机械复核的角色。** 任何"为某角色开 fork"的提案，必须先证明该角色受下游 fresh 复核；不能证明者，默认 fresh Spawn。这是 Part B 的设计/适用边界的**唯一来源**——下表不是规则本身，而是该原则在当前角色集上的**推论（derived consequence）**。
>
> **生成式优于封锁式的理由**：枚举"哪些 executor 不 fork"是滑坡引擎——"非独立角色可继承上下文"会被未来"落地 executor 只是机械套改动清单、也不需要独立性，为提速也 fork 它"援引。生成式原则自带否决依据：落地/R0 executor 之所以不 fork，不是因为被列入黑名单，而是因为**它们的产出无下游 fresh 复核**，原则直接判否。**Codex 0.141.0 与 opencode 1.17.8 两个框架原生 agent 在跨框架实测中各自独立 ENDORSE 了这一生成式边界**（见 §框架适配）。

| 角色 | 模式 | 原则推论（是否有下游 fresh 复核） |
|------|------|------|
| 收敛循环内 Executor（Round N 修复） | **fork（继承）** | **合格**：inner-loop fresh reviewer 本轮机械复核其产出 → 可继承；省读 + 抗漂移；独立性非必需 |
| 所有 Reviewer（评议/主循环/inner loop/盲审/设计审查/gate） | **fresh Spawn（不变）** | **永不继承**：reviewer **本身就是**那道复核（the verification），无"下游再复核它"之说；fork 会摧毁对抗式价值 |
| 落地执行 Executor（Plan-Execution 模式） | **fresh Spawn（不变）** | **不合格**：落地产出**无下游 fresh 复核**（刻意"独立于 converge 循环、只读 plan 改动清单、机械落地"）→ 原则判否；继承收敛循环历史会诱导越界"改进" |
| Round 0 合同提议 Executor | **fresh Spawn（不变）** | **不合格**：合同提议**无下游 fresh 复核**、需对 plan 作独立解读 → 原则判否；继承会污染 |
| 层级模式 Worker | 暂不变（未来工作） | 由 sub-orchestrator 调度，超出本计划范围；如未来开 fork，须先按上述原则证明其受下游 fresh 复核 |

**框架适配（fork 是 *探测* 能力；跨框架实测：3 框架中 2 个原生支持 —— H3 折入）**：

> **可移植性结论（实证更新，证伪 H3「fork 仅 Claude Code」前提）**：fork 在 **3 个框架中的 2 个**有原生实现（Claude Code + Codex，后者 0.141.0 经框架原生 agent **实测验证**）；opencode 干净降级为 fresh Spawn。**fork 不是单框架特性**，因此 H3"仅一个框架行使 / 为一个框架承担治理复杂度"的不对称论证**不成立、已撤销**（见 §张力3、H3 处置）。

- **Claude Code**：`Agent` 工具的 `subagent_type: fork`（forks 继承父对话；**模型亦继承——"forks always inherit the parent model"**）。**先探测该子类型是否可用**（不假定所有 CC 版本支持），可用则收敛循环 executor 用之；其余角色用 `general-purpose`（fresh）。`PreToolUse` `matcher: "Agent"` 按工具名匹配，故 fork spawn **仍被预算 hook 计数**、仍走 `reserve --role executor` → 不绕过 gate。
- **Codex 0.141.0（实测验证 / EMPIRICALLY VERIFIED）**：原生 live fork = `multi_agent_v1.spawn_agent(fork_context=true)`——框架原生 agent 实测同时 spawn 了 `fork_context` true/false 两种子 agent。`fork_context=false`（或省略）= fresh Spawn。**注**：CLI `codex fork` / `codex resume` 只是**已保存 SESSION 的 fork**，非 live 机制，不得编码为 adapter。约束：full-history fork **必须继承 agent type / model / reasoning effort**（与 CC 一致），故 fork 不可叠加 per-fork model override（见下「fork ⊥ 降档」）。能力探测 = 检视 `spawn_agent` schema 是否含 `fork_context` 参数。
- **opencode 1.17.8（无 live 子 agent fork → 干净降级 fresh）**：`task` 子 agent 是 fresh child-session；`opencode run --fork` 只 fork 一个**可恢复的 CLI session**，**不是** live in-conversation 子 agent。故 Part B 在 opencode 上**降级为 fresh Spawn**，retrospective 标 `executor_context: fresh (no-fork-support)`。**原生最佳替代 = fresh executor + 经 state files / attempt logs 的压缩上下文交接**（= converge 现行模型，保留既有 task 抽象，不把 CLI `--fork` 当等价物）。
- 通用降级（§A.4 Spawn 完全不可用）不变。

**新硬约束：fork ⊥ 降档（fork 与 executor 模型降档互斥 —— PR-4）**：forked executor **继承 orchestrator（主对话）模型**——CC「forks always inherit the parent model」、Codex「full-history forks must inherit agent type, model, reasoning effort」两处实测均确立此为硬约束。因此 **fork 与 `executor_model_tier=low`（降档）互斥**：一次运行若 fork executor，则 **MUST NOT** 同时降档（**fork 胜出 → 继承 orchestrator 模型**）；需要降档则必须改用 **fresh Spawn**（降档/per-agent model override 仅对 fresh spawn 可用）。见 §模型分层 交互注、不变量 #10。

**审计与预算不变**：fork 仍经 `Agent` 工具 → PreToolUse 总量 hook + `budget_gate.py reserve` 照常裁决、照常计数；instance_id 照常记录；attempts.md 照常写（fork 不取消文件落盘义务——盲审/审计仍需文件证据，且 fork 仅省"读"不省"写"）。

**fork executor 的 prompt 形态**：不再是完整自足模板，而是**追加式任务指令**（"你继承了本次收敛的完整上下文；本轮 = Round N；针对 round-N reviewer 的全部 blocking_issues 修复；遵守路径依赖防护 §1–§7；继承的历史是 fact 非 commitment"）。必读清单从"5 项重读"压成"指向 round-N reviewer 输出 + 提示历史已在上下文"。

### Part B 改动清单

| # | 文件 | 改动 |
|---|------|------|
| B-1 | `SKILL.md` §抽象能力层 | Spawn 增「context: fresh \| inherited」语义；注明 inherited 仅用于收敛循环 executor。**fork 是 *探测* 能力**——不得硬编码假设所有框架/CC 版本均支持；探测能力，不支持则降级 fresh |
| B-2 | `SKILL.md` §核心角色 + 主循环步骤 f | Executor 行说明改为 fork（继承）；明确 Reviewer/落地/R0 executor 仍 fresh |
| B-3 | `refs/executor-prompt.md` | 新增「Fork（继承上下文）变体」节：追加式指令模板 + 显式重申**全部 §1–§7**抗锚定纪律（§4–§7 在 fork 下同样失去 fresh-context 兜底，不可只重申 §1–§3）；标注 Plan-Execution / R0 提议仍 fresh |
| B-4 | `refs/framework-adapters.md` §A.1/A.2/A.3 | 各框架 fork 实现/降级；Claude Code = `subagent_type: fork`，并**探测后降级**（不假定版本支持）。增两条注：(1) ledger `tier` 字段仅取 `enforced` / `auditable-only`——"best-effort guarded" 是 auditable-only + hook 的文档别名，**不是可传入的 tier 值**（传入会 FAIL_CLOSED）；(2) Claude Code `PreToolUse` `matcher: "Agent"` 按工具名匹配，故 `subagent_type: fork` 的 spawn **仍被预算 hook 计数**、仍走 `reserve --role executor`（consumes none、占 total）→ 不变量 #5 成立、fork 不绕过 gate |
| B-5 | `CONSTITUTION.md` #7（**条件项，非自动执行**） | **仅当** CONSTITUTION 第四部人工审议确认 fork 合规且需附注时，才增解释性附注（fork 出独立实例持笔 ≠ Planner 亲自执行）；**否则不改 #7**。本项不预先执行、不预判 Q1——它取决于第四部对本轮 split ruling 灰区的最终裁定 |
| B-6 | `refs/state-schema.md` | retrospective/attempts 增 `executor_context: fork \| fresh` 字段，便于审计与 pilot 实测（含不变量 #8 的 fork-vs-fresh 对照） |
| B-7 | `SKILL.md` §模型分层 + 配置参数 `executor_model_tier` | 增交互注：forked executor 继承 orchestrator 模型 → fork 与降档（`executor_model_tier=low`）互斥；fork 运行不可降档，降档须用 fresh Spawn |
| B-8 | `refs/framework-adapters.md` §A.2/A.3 跨框架实测校正 | A.3（Codex）：增 `fork_context` Spawn 变体（Spawn 同时支持 fresh `fork_context=false` 与 inherited `fork_context=true`）；Continue 改为两步 `send_input`（返回 submission_id）+ `wait_agent`；增 `resume_agent`；注明 per-agent model override（model/reasoning_effort/service_tier）仅对 **fresh** spawn 可用——fork 必须继承 agent type/model/effort；将 `/goal` 段标 `[UNCERTAIN]`（0.141.0 无可验证 /goal 设施）；能力探测 = 检视 `spawn_agent` schema 是否含 `fork_context` 参；注明 `codex fork`/`codex resume` 是已保存 SESSION 的 fork，非 live 机制。A.2（opencode）：subagent handle 是 session 式 `task_id`；Continue = 用同一 `task_id` 重新调 `task`（实测）；`subagent_type: general` **非**普遍可用（restricted/plan 模式被拒，`explore` 可用）；无 per-spawn `model` 参（model 经已配置 subagent 类型）；澄清 `opencode run --fork` 是 CLI-session fork，**非** live in-conversation 子 agent fork |
| B-9 | `refs/framework-adapters.md`（best-effort guarded 可移植性注） | 记录未来扩展数据，不声称已实现：opencode 可经 `tool.execute.before` 插件或静态 `permission.task` deny 获得 deny-before-spawn（默认未加载插件 → 今日仍 auditable-only）；Codex 0.141.0 无可验证的 deny-before-spawn（notify 仅注入不可拒、token_budget 禁用）→ 维持 auditable-only。CC 仍是唯一已落地 best-effort guarded 的框架 |

---

## 不可逾越的约束（硬边界）

- **不得移除任何宪法强制确认点**（终止-b/c、预算软停、`*_exhausted`、`MODE_SWITCH_REQUIRED`、`FAIL_CLOSED`、`需重新设计`）。A2 只标注自主/强制边界，不缩小强制集。
- **不得让 Reviewer 走 fork**——任何 Reviewer（含盲审、设计审查、gate）必须 fresh Spawn。
- **不得让落地执行 Executor / R0 提议 Executor 走 fork**（保持其刻意的 clean context）。
- **不得改 `scripts/budget_gate.py` 的裁决逻辑**（`cfg`/`reserve`/`validate_integrity` 分支与算术不动）。Part A 允许且仅允许改 `:55` 的 `max_blind_rechecks` 默认常量值（2→1）+ 同步其测试期望（A-7/A-8）；ultraverge 经 config 覆盖回到 2；fork 仍走既有 reserve/hook 计数。
- **不得以 fork 为由取消文件落盘**（attempts/round/state 仍写）。
- **不得主张无条件 token 节省**——表述限定为"延迟 + 抗漂移为主，token 中性到正向，需实测"。
- **不得顺带重构无关内容**。

---

## 待裁决问题（交 ultraverge Reviewer 定）

- **Q1（宪法）·本轮 ultraverge 已渲染 split ruling，残余裁决交第四部**：fork executor 共享 orchestrator 上下文，是否仍满足 CONSTITUTION #7「Planner 不执行」？**本轮 ultraverge 层已裁决**：3 名 Reviewer 一致认 **字面合规**（持笔者为独立实例）；1 名 Reviewer + 设计审查视角认为 **意图层（认知独立性）存争议**，属灰区（详见 §Part B 评估 张力1）。**残余决定**——是否为 #7 加解释性附注（B-5）——**deferred 到 CONSTITUTION 第四部人工审议**；B-5 为条件项，非自动执行。**评估对象已收敛后修订（H1）**：第四部应以**生成式 fork 边界**（fork 仅授予产出受下游 fresh、独立 reviewer 机械复核的角色）为审议对象，而非角色封锁清单——该原则获 Codex 与 opencode 两框架原生 agent 独立背书，已成为 §设计 适用边界的唯一来源。
- **Q2（抗锚定有效性）·已升级为验收硬门（2×2）**：forked executor 继承 orchestrator 叙事，§1–§7 的显式重申是否足以抵消锚定放大？**不再是"是否需要"的开放问题**——已定为强制门：见不变量 #8，Part B 落地前**必须**跑 **2×2 pilot**（Cell A/B/C/D，同组收敛对象配对、adverse-flip 判据，详见 #8）。决策矩阵把 Cell A/B 结果映射到 #9 保留/松绑 + Part B 落地与否。
- ~~**Q3（A 与 B 是否拆分收敛）**~~ → **已定（用户 2026-06-21）：A 与 B 一次 ultraverge 一起收敛**。Reviewer 不得自行拆分；若评议复杂度过高，按分阶段管控（同一收敛内分 scope 处理），不另起第二次 ultraverge。
- ~~**Q4（盲审预算分层的总量公式）**~~ → **已定**：重算确认普通模式 cap = **42**（`ceil(1.5×28)`）、ultraverge cap = **44**（`ceil(1.5×29)`）。两者均 > 单轮所需 spawn、单调递增、**无边界下溢**（arbitration / consumes:none 余量仍由 `total_safety=1.5` 覆盖）。无残余 TODO。

---

## 不变量（验收硬条件）

> **【撤回声明 · 2026-06-21 · Part B dropped（GD-2）】** 不变量 **#4 / #5 / #8 / #9 / #10 随 Part B 撤回**（pilot/guard/fork 相关，Part B 不采纳故全部 moot）。**#1 / #2 / #3 / #6 / #7 仍有效**（Part A 已落地；#3 是通用 fresh 约束）。下方原文本保留作历史记录。

1. 普通 converge：`max_blind_rechecks` 生效值 = 1，stock 总量 cap = **42**；ultraverge：经 config 覆盖 = 2，cap = **44**。两组单调、无下溢。
2. 全部宪法强制确认点在改后仍存在且被触发（用例覆盖）。
3. 任何 Reviewer / 落地 executor / R0 提议 executor 仍为 fresh Spawn（无 fork）。
4. 收敛循环 executor 为 fork（框架支持时）；不支持时降级 fresh 并标注。
5. fork executor 仍经 budget gate 计数 + 写 attempts.md（审计链完整）。
6. `scripts/budget_gate.py` **裁决逻辑零 diff**（`cfg`/`reserve`/`validate_integrity` 等分支与算术不动）；仅 `max_blind_rechecks` 默认值及其测试期望变更——精确为两处改动点（一处常量值 + 一处测试文件，后者含 stock cap 44→42 期望调整 + 新增 ultraverge config 覆盖 cap=44 断言）：`scripts/budget_gate.py:55`（默认 `2→1`）、`tests/test_budget_gate.py:604`（stock cap `44→42`，并新增 ultraverge config 覆盖 cap=44 断言）。ultraverge 的 mbr=2 由 config 覆盖（零代码）实现。
7. 文档不出现"无条件省 token"类未证主张。
8. **【验收硬门 · 2×2 组合路径 pilot；2026-06-21 二次修正（4 单元 + 配对 + 样本匹配判据 + 流程定序），回应 Codex 复评 #2/#3/#4/#5】Part B 落地前，必须在同一组收敛对象上完成 **2×2 pilot**，测 *composed* 路径，**4 个实验单元**：

   |  | blind=1 | blind=2 |
   |---|---|---|
   | **fork loop-executor** | **Cell A**（最坏情况） | **Cell B**（生产保守） |
   | **fresh loop-executor** | **Cell C**（控 blind 效应） | **Cell D = 基线**（现行生产） |

   - **配对**：4 单元跑**同一组 ≥3 个收敛对象**（within-object 配对，控对象难度）。基线 = **Cell D**（fresh + blind=2 = 现行生产配置）。
   - **流程定序（每单元 composed path）**：`fork(or fresh) loop-executor 做 Round-N 修复 → fresh inner-loop Reviewer + fresh blind-recheck（次数 = 该单元 blind 设定）→ 收敛 → fresh Plan-Execution landing-executor 自主落地（A2）`。**landing-executor 永远 fresh，绝不 fork**（按适用边界无下游 fresh 复核）。矩阵中"forked executor → 自主落地"指此**完整 flow**，非单个 forked agent 兼任落地。
   - **评分与判据（与 N≥3 匹配；弃虚假 Δ<5pp）**：反模式检测保持**二元**（per blocking_issue，`over_compromise` / `past_commitment_anchoring` present/absent，沿用 reviewer-prompt）。"实质性升高" = **配对 adverse-flip**：某 blind 设定下，fork 单元（A 或 B）相对**同 blind 的 fresh 配对**（C 或 D）出现 **≥1 对象** adverse flip（fork 检出而 fresh 配对未检出、无反向抵消）→ 该单元"升高"。**样本量坦诚**：N≥3 对象为**探索性**，只检出**大体回归**（effect ≥1 对象级）；"干净" = 未现大体回归 → **有条件落地 + 生产遥测**（`executor_context` 字段持续追踪 fork-vs-fresh 锚定率；遥测显回归则经 cold-store 撤销）。
   - **决策矩阵（按 Cell A / Cell B 是否升高；"升高" 见上判据）**：
     - **A 干净、B 干净** → **#9 松绑**：生产 composed path 允许 blind=1；§1–§7 重申补偿被接受；Part B 落地（B-1~B-7）。
     - **A 干净、B 升高**（悖论：更多复核反更差）→ **测量完整性存疑**：标红、加测 N+2 对象复跑；若可复现 → 按 A（绑定最坏情况）判干净，Part B 落地、#9 松绑，retrospective 强制 flag 进生产遥测重点监控。
     - **A 升高、B 干净** → **#9 保留**为生产硬约束（composed path 必须 blind=2）；§1–§7 重申 + blind=2 冗余共同补偿；Part B 落地（B-1~B-7），生产 composed path 强制 blind=2。
     - **A 升高、B 升高** → **Part B 阻断**：§1–§7 重申不足以补偿 fork 锚定放大；Part B 不落地，cold-store 或 drop。
   - 对照结果记 `executor_context` 字段（B-6）+ retrospective，含每单元锚定率、adverse-flip 明细、决策矩阵落点。
   - **验收边界**：§验收命令（rg/py_compile/test/diff）**仅验证 Part A 代码+文档卫生**，**不**验证 pilot 设计。pilot 有效性是**独立经验门**，由 (a) 方法论清单满足（4 单元/配对/盲化/N≥3/二元/adverse-flip 判据）、(b) 4 单元结果入 retrospective、(c) 决策矩阵落点记录 合取证。
9. **【风险预算耦合，H2 折入；2026-06-21 修正：保留/松绑 tied to #8 pilot outcome】三个独立性削弱器不得在默认路径叠加**：当一次普通模式运行**同时**用了 forked executor **且**自主落地（A2）时，盲审预算**生产默认保持 2**（或必须插入一轮 fresh、非 fork 的验收）——不得降到 1。普通模式 blind=1 仅在该运行**未**叠加 fork+自主落地时适用。理由：盲审是"可能被 fork 锚定的收敛"与"自主写文件"之间唯一的 fresh-eyes 关口，三处同时减摩擦会在新增自主性处集中风险。**此 blind=2 生产约束是 #8 pilot 前的保守默认**——其「保留 vs 松绑」由 #8 pilot 的 **Cell A（fork+blind=1）** 结果裁决：Cell A 干净 → 本约束松绑（composed path 允许 blind=1）；Cell A 升高 → 本约束保留为生产硬约束。pilot 未跑前，一律按 blind=2 执行。
10. **【fork ⊥ 降档，PR-4】**forked executor 继承 orchestrator 模型；fork 与 executor_model_tier=low（降档）互斥。一次运行 fork executor 则不得同时降档（fork 胜出，继承 orchestrator 模型）；需降档必须改用 fresh Spawn。**此为 converge 调度层约束（orchestrator 在 fork 时不传 model override 来满足），非平台层约束——平台是否「允许」per-fork override 不构成本条违反、亦非 Part B 阻断点**（Codex 可行性评估 #2 澄清）。落地时此约束须在 SKILL.md §模型分层 与配置参数 executor_model_tier 说明中体现。

## 验收命令

```powershell
rg -n "max_blind_rechecks|subagent_type: fork|executor_context|context.*inherited|默认自主|宪法强制确认|fork_context|executor_model_tier|spawn_agent" SKILL.md refs CONSTITUTION.md
python -W always::ResourceWarning tests/test_budget_gate.py
python -m py_compile scripts/budget_gate.py
git diff --check
```

期望：测试全绿（含更新后的 stock cap=42 与 ultraverge config 覆盖 cap=44 断言）；治理文档中盲审分层、fork 边界、确认点分类均可定位；budget_gate.py **裁决逻辑零 diff**（diff 仅限 `:55` 默认值一行 + 对应测试期望，不触裁决分支/算术）。

## 流程

本计划走**完整 ultraverge**：≥3 独立 Reviewer → 必要修复收敛 → 收敛后设计审查（强制，触碰系统边界：角色模型 + 抽象能力层）→ **人工提交批准**（执行 agent 不得自行 commit）。Part B 涉及 CONSTITUTION #7 解释，须按宪法第四部 + 人工审议确认。

---

## 修订记录

- **2026-06-21（初始）**：计划创建，走 ultraverge 收敛 Part A + Part B。
- **2026-06-21（Part A 落地）**：Part A（A-1~A-8）经 commit `5e61d14` 落地、PR #4 合入 master；B-8/B-9 经 commit `042d74a` 同 PR 落地。Part A 不变量 #1/#2/#6 验收通过（50/50 测试绿、裁决逻辑零 diff）。CONSTITUTION #7 未动（B-5 条件项，第四部未裁决）。
- **2026-06-21（#8/#9 矛盾修正）**：Codex 可行性评估（主审 + fresh Reviewer 独立一致）发现不变量 #8（测 blind=1 composed path）与 #9（composed path 必须 blind=2）直接矛盾。修正：#8 改为**双臂 pilot**（blind=1 + blind=2 各 vs fresh 基线）+ 量化方法论（隔离/盲化/N≥3/Δ<5pp 阈值）+ **决策矩阵**把 pilot 结果映射到 #9 保留/松绑 + Part B 落地；#9 改为「tied to #8 pilot outcome 的保守默认」；#10 增「converge 调度层 vs 平台层」澄清（Codex 评估 #2）；§A2 耦合约束 + Q2 同步改为双臂表述。此为 bug 修正（矛盾诊断已独立确认），非特性变更。Part B（B-1~B-7）仍 gated on #8 pilot，待 Codex 复评可行性后启动。
- **2026-06-21（Part B dropped · GD-2 · 用户决断）**：经 3 轮 Codex 复评，pilot 设计每轮合理深挖一层却无收敛信号（rigor-escalation loop：2×2 → 4 单元 → 干预模型错 → 评分协议 → 生产 holdout → …）。宪法第一部仲裁：**Bitter Lesson 判 fork-executor 为「随模型进步贬值的补丁」**（重读成本随上下文经济学改善收缩，H3 已挂 sunset）、**Occam 判验证机器反客为主**（为贬值补丁投未收敛的重型验证）。用户据此决断**放弃 Part B**。处置：Part B（B-1~B-7）不采纳；不变量 #4/#5/#8/#9/#10 撤回；handoff brief 删除；framework-adapters 的 fork 描述保留为「框架能力、converge 不采纳」；CONSTITUTION #7 不受影响（fork 既未采纳、无角色模型变更，#7 审议继续 deferred）。**重激活门槛**：除非上下文经济学反转（重读成本非但不降反升）使 fork 收益质变，否则不再重启——届时须先回答本轮发散的测量难题（软效应 × 软仪器 × 小样本）。本计划移 done/。
- **2026-06-21（#8 二次修正 · Codex 复评 #2~#5）**：Codex 复评指出 #8「双臂」实为 fork/fresh × blind=1/2 **4 单元**设计、N≥3 与 Δ<5pp 在二元计分下统计不成立（min step 33.3pp）、流程未定序（loop-executor vs landing-executor）、决策矩阵漏悖论格、验收命令不证 pilot。修正：#8 改为 **2×2 = 4 单元配对设计**（Cell A/B/C/D，基线 = Cell D）+ **adverse-flip 判据**（弃虚假 Δ<5pp，坦诚 N≥3 仅检出大体回归、生产遥测补细分辨）+ **显式流程定序**（fork 仅 loop-executor，landing 永新鲜）+ **补全 4 格决策矩阵**（含 A 干净/B 升高悖论格处置）+ **验收边界声明**（静态命令仅验 Part A，pilot 是独立经验门）。#9/§A2/Q2 同步改 Cell 术语；handoff brief 同步（Q3 改信息项、Q4 加隔离、Q6 按 4 单元、§5 决策表补全）。
