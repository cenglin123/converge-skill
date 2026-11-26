---
slug: 20261126-on-demand-realtime-collab
artifact: docs/plans/active/20261126-on-demand-realtime-collab.md
round: 1
role: reviewer
reviewer_id: uv-init-2
mode: main-loop
scope: ultraverge-initial-deliberation (extended domain: preflight Q1-Q6 + design-review DR1-DR7)
verdict: 阻断需修复
blocking_count: 8
suggestion_count: 8
generated_at: 2026-11-26T01:06:02+08:00
reviewer_backend: opencode
reviewer_instance_id: ses_dec56db47ffekt5xEIbhLY2MEo
---

# 初始评议审查报告（ultraverge · Reviewer 2）

> 独立 fresh-context 审查。只读审查，未修改本仓任何既有文件；本文件是本次唯一写入产物。
> 审查对象：`docs/plans/active/20261126-on-demand-realtime-collab.md`（63 行）。
> 扩域：前置自检 Q1–Q6（`refs/reviewer-discipline.md` 第 5–21 行）+ 设计审查 DR1–DR7（`refs/design-review-prompt.md` 第 58–99 行）。
> 未提供 contract.md，因此无 rubric 维度评分、无 `contract_amendment_required` 判定依据。

---

## 1. 结论

**verdict: `阻断需修复`**（8 条 blocking，其中 conceptual 3 / architectural 3 / structural 1 / implementation 1；suggestion 8 条）

**不是 `需重新设计`**：计划的**方向**成立且与宪法精神一致——把"协作基底选择"从硬编码门槛交还 Orchestrator 判断侧，符合 `CONSTITUTION.md` 第 36 行"verdict 裁决、prompt 工程、机制阈值与参数的设定永远留在 Orchestrator 判断侧"的分类。缺陷集中在三处：**宪法自检的方向误用**（把防呆/契约型前提与封顶型先验一并放开）、**跨文件机制冲突未消解**（只改 `SKILL.md` 而 §八 细则在 `refs/orchestrator-guide.md`）、**新路径的约束真空**（宿主原生实时协同替代传话后，载荷/振荡/降级三项防护失去载体）。这些均可通过回写 plan 本体 + 补齐改动清单修复，不需要推翻目标。

**按 `SKILL.md` Ultraverge 路径**（第 162–165 行）：评议 verdict ≠ 可执行 → 进入标准完整收敛流程（Round 0 → 多轮 → 收敛），收敛后强制设计审查。本报告不构成收敛终局。

---

## 2. blocking_issues

```yaml
blocking_issues:
  - id: UV2-01
    severity: conceptual
    attribution: plan_defect
    plan_amendment_required: true
    rubric_gap: false
    location: plan §2（第 22 行）/§3 改动 2（第 30 行）/§4 改动 2（第 52–56 行）
    description: |
      宪法自检把传话编排的三条适用条件整体当作"可放松的硬门槛"，方向与 Bitter Lesson 的精确边界相反。
      `CONSTITUTION.md` 第 32 行界定："反对封顶型先验（任务知识、局部最优启发式——随模型变强而减值），不反对防呆型机制
      （契约校验、过程监督、预算门控——防御机械失误；机械失误随任务量缩放、不随模型强度减值）"；第 34 行三分判据③要求
      "对契约违反 fail-closed，对判断分歧 fail-open"。
      而 plan 改动 2 要删除的三条（`SKILL.md` 第 385–388 行）性质并不齐一：「参与方 ≤ 2」是封顶型先验；「产物已收敛且方案已定稿」
      与「验收判据机械可核」是契约型/防呆型前提——后者正是 `refs/orchestrator-guide.md` §八 介入判据（第 453–457 行"可机械核验的差异"）
      得以成立的前置条件。
      plan §2（第 22 行）以单一"去除僵化硬门槛"论证一次性放开三条，未做防呆/封顶的分层判别，等于用"判断分歧 fail-open"
      覆盖了本应保留的"契约违反 fail-closed"前置。宪法自检不成立。
    fix_direction: |
      在 plan §2 中逐条分类三条适用条件：封顶型（参与方 ≤ 2）可按 Bitter Lesson 放开或降为"典型"；防呆/契约型（产物已收敛且定稿、
      验收判据机械可核）保留为硬前置，仅放开"协作基底选择"。或：整体保留三条，仅把"宿主原生实时协同"新增为并列可选协作基底
      （不触碰准入定义）。两种走法都需在 plan 中补写分层论证而非单一标签。

  - id: UV2-02
    severity: architectural
    attribution: plan_defect
    plan_amendment_required: true
    rubric_gap: false
    location: plan frontmatter target_files（第 6–7 行）/§3 表第 2 行/§4 改动 2(1)(2)/§5.2（第 61 行）
    description: |
      改动只落在 `SKILL.md`，但被改机制的操作细则在治理文档 `refs/orchestrator-guide.md` §八，构成跨文档机制冲突，且 plan 自身的
      验收项因此不可满足。
      plan 改动 2(1)（第 44 行）允许落地阶段改用"宿主原生实时协同"，与 §八硬约束（`refs/orchestrator-guide.md` 第 415 行
      "**必须 spawn executor，不得直接编辑** — 宪法硬约束 #7 在落地阶段同样适用"、第 416 行"executor 使用
      `refs/executor-prompt.md` Plan-Execution 模式（fresh-context spawn，仅读方案文件）"）、§八流程（第 395–397 行）、
      instance_id 留痕（第 418–420 行）、清单项数核对（第 422–429 行）直接冲突；改动 2 还把"适用条件"改名为"典型适用参考"，
      使 `refs/orchestrator-guide.md` 第 433 行"适用条件见 SKILL.md Orchestrator 责任清单"成为悬空引用。
      plan frontmatter 的 target_files（第 6–7 行）仅列 `SKILL.md`，未列 `refs/orchestrator-guide.md`——而后者是
      `CONSTITUTION.md` 第 72 行所列治理文档（修改须走 ultraverge）。
      净结果：plan §5.2（第 61 行）"与 `refs/orchestrator-guide.md` §八无矛盾"作为验收标准在现状下不可满足；且
      `CONSTITUTION.md` 第 4 行"运行时机制冲突时以 SKILL.md 为准……冲突本身即触发修宪程序"——本计划制造冲突而非消解冲突。
    fix_direction: |
      二选一并落到 plan：(A) 把 `refs/orchestrator-guide.md` §八（流程/硬约束/instance_id 留痕/N-vs-M 核对/传话编排引用句）纳入
      改动清单，给出逐字改动规格；(B) 放弃"落地阶段可用宿主原生实时协同"，只保留协作基底的表述而不改落地执行机制，使 §八全部条款
      继续适用。同时把 plan §5.2 改写为可机械逐条核对的条款清单（列出 §八 哪几条仍适用、哪几条被改）。

  - id: UV2-03
    severity: architectural
    attribution: plan_defect
    plan_amendment_required: true
    rubric_gap: false
    location: plan §4 改动 2（第 54 行与第 56 行并列）/§3 改动 2(b)（第 30 行）
    description: |
      新授权的"宿主原生实时协同"路径以**替代关系**写入，而三项防护以"传话编排"这一模式名为载体，因此新路径上无约束，形成约束真空。
      plan 第 54 行明写"Orchestrator 可直接选用宿主能力替代手工传话"，第 56 行同时要求"保留该节其余硬约束（载荷强制文件引用、
      独立性降级声明、角色边界宪法 #7、振荡裁判）不变"。
      但：①载荷强制文件引用（`SKILL.md` 第 390 行）针对的正是"消息载荷下两侧 agent 各自累积对方全部历史，输入 token 随轮次二次增长"，
      而共享消息板恰恰是消息载荷——绕过传话编排即绕过该约束；②振荡裁判（`SKILL.md` 第 396 行）由 relay-ledger 驱动，
      共享板路径不产生 relay-ledger，因而无振荡检测；③独立性降级声明（`SKILL.md` 第 392 行）在改动 1 中仅对"以实时协同开展互审"做了
      carry-over（第 39 行），落地阶段的持续会话/共享板协作未被覆盖。
      净效果：出现一条"无载荷约束 + 无振荡检测 + 无降级声明"的协同通道，违反 `CONSTITUTION.md` 第 36 行的机制分类与第 34 行
      三分判据③。宪法 #6 的"降级必须告知用户"义务在本路径上失去触发点。
    fix_direction: |
      把三项约束的载体从"模式名"上移到"协同类别"：任何持续会话/共享消息板协同（无论经传话编排还是宿主原生能力）一律适用
      （a）载荷成本边界或等效的最小上下文策略，（b）宪法 #6 降级告知，（c）等效的振荡/冲突检测。若不打算引入新机制，
      则在 plan 中明确限定"宿主原生实时协同"仅可用于无对抗诉求、无共享历史需求的场景，并写清该边界。

  - id: UV2-04
    severity: architectural
    attribution: plan_defect
    plan_amendment_required: true
    rubric_gap: false
    location: plan §1（第 14 行）/§4 改动 1（第 39 行）
    description: |
      计划明确把"层级并发施工"列为可采用实时协同的非审计环节，与 `SKILL.md` 层级模式的两条现存不变量直接矛盾，且改动 1 的兜底措辞未做排除。
      plan 第 14 行把"层级并发施工"列入主控自主决定的非审计环节；改动 1（第 39 行）写的是"非审计环节（如方案落地执行、多模块并行施工、
      作者间接口对齐）……由 Orchestrator 按耦合度自主决定，不作强制"。
      而 `SKILL.md` 层级模式写着"启用条件（三个同时满足）"第 2 条"子任务间无实时数据依赖"（第 514 行）与关键约束
      "**子收敛之间不通信**"（第 519 行）。
      改动 1 既未排除"层级收敛的子收敛"，也未区分"层级模式的子收敛"与"落地阶段的并行施工"，读者在同一文件内会读到两条互斥规范：
      层级模式禁通信 / 非审计多模块并行可实时协同。
    fix_direction: |
      在改动 1 中显式排除层级收敛子收敛（写明"层级模式下的子收敛之间不通信、子任务间无实时数据依赖"两条不变量不变），把实时协同的
      适用面限定为落地执行与跨作者接口对齐等不含独立收敛 scope 的场景。若确需支持层级并发协同，须另立带前置条件的例外，并同步
      `refs/decomposition-protocol.md`（该文件为 `CONSTITUTION.md` 第 74 行治理文档，须纳入 target_files）。

  - id: UV2-05
    severity: conceptual
    attribution: plan_defect
    plan_amendment_required: true
    rubric_gap: false
    location: plan §4 改动 1（第 39 行）/§2（第 23 行）/§3（第 29–30 行）
    description: |
      前置自检 Q4（职责边界自洽）不成立：新增的"按耦合度自主决定"裁量权没有归属定义、没有可操作判据、也没有留痕位置，产生灰色地带。
      plan 第 39 行把决策权交给 Orchestrator，但：①"耦合度"无定义、无判据、无示例，跨宿主/跨会话实现会分叉；②该决策在
      `SKILL.md` 第 347–379 行的责任清单（M-1…C-21）中无对应条目——没有任何一条责任承载"协同方式选择"；③plan §2（第 23 行）声明
      "不新增文件、不新增模式、不新增脚本或字段"，因此选择结果在 attempts.md / `_orchestrator-state.md` / retrospective.md 中无处记录，
      事后无法核验"当初是否按规则选择"。
      对照本仓既有惯例：`refs/orchestrator-guide.md` §八 介入判据（第 453–457 行）明确区分"可机械核验的差异"与"语义层判断分歧"，
      `SKILL.md` 第 350 行 M-3 要求每轮记录边界自检结果——本计划在此处引入了既不可核验、也不留痕的自由裁量，与仓库纪律不一致。
    fix_direction: |
      在 plan 中补齐职责归属：明确该裁量属 Orchestrator 判断侧（与 `CONSTITUTION.md` 第 36 行分类一致），给出可复述的判据
      （例：需共享中间产物/频繁互问 = 实时协同；单向可交付 = 隔离派发）；并把"协作方式选择及其理由"落到既有留痕字段之一
      （attempts.md / retrospective.md），或在 plan 中显式接受"不留痕"并论证为何不构成治理缺口（`CONSTITUTION.md` 第 32 行二分判据要求
      先问"必要还是多余"，此处是"必要但未给位置"）。

  - id: UV2-06
    severity: conceptual
    attribution: plan_defect
    plan_amendment_required: true
    rubric_gap: false
    location: plan 第 14/29/39/44/54 行（术语）/§4 改动 2（第 52–56 行，改小节标题）
    description: |
      前置自检 Q5（命名一致性）不成立：新术语无定义落点、与既有术语无映射，且改标题造成跨文档悬空引用。
      ①同物多词：plan 第 14/29/39/44/54 行交替使用"宿主原生实时协同"、"实时协同"、"实时对话"、"共享消息板"、"Swarm"指称同一事物。
      ②新造词无定义："独立审计红线"（plan 第 39 行）在仓库内无定义，而既有术语是"独立审计环节"、"盲审复核"（`SKILL.md` 第 176 行附近 ultraverge 描述、
      第 276–300 行盲审复核节）；新词与旧词并存但无映射关系说明。
      ③概念层级混淆："协作互审（非独立盲审）"（plan 第 39 行）与既有"独立性降级"（`SKILL.md` 第 392 行）不是同一层级概念——
      前者是审查形式，后者是"反锚定机制不生效"的状态；两者并列出现但未说明关系。
      ④悬空引用：改动 2 把小节标题「适用条件」改为「典型适用参考」后，`refs/orchestrator-guide.md` 第 433 行
      "适用条件见 SKILL.md Orchestrator 责任清单"的指代失效。
    fix_direction: |
      在改动 1 段内给出受控词表：每个术语一次定义并在全文统一（建议统一为「宿主原生实时协同能力」，宿主示例放括号或移入
      `refs/framework-adapters.md` 分册）；"独立审计红线"改用既有术语或显式定义其与"独立审计环节/盲审复核"的包含关系；
      "协作互审"给出与"独立性降级"的区别；随 UV2-02 一并修正 `refs/orchestrator-guide.md` §八 的引用措辞。

  - id: UV2-07
    severity: structural
    attribution: plan_defect
    plan_amendment_required: true
    rubric_gap: false
    location: plan frontmatter（第 1–8 行）/全文（第 1–63 行，无任何 fenced JSON 块）
    description: |
      治理变更计划缺少 preflight 的唯一机器输入块，治理元数据不可被机器消费。
      `SKILL.md` 第 460 行："`converge.governance-change/v1` 是 Orchestrator/preflight 的唯一机器输入（prose/表格不进入机器解析）"；
      第 453 行：治理计划默认要求配置 task-envelope，未配置则 `FAIL_CLOSED:governance_requires_task_envelope`；
      `refs/reviewer-discipline.md` 第 278 行重申"唯一 fenced JSON 块是 preflight 的唯一机器输入……Reviewer 不得从散文或表格中提取数字作为机器裁决依据"。
      本 plan 的治理元数据（`governance_level: ultraverge`、`target_files: SKILL.md`）只存在于 frontmatter/prose；plan 全文三个 fenced 块
      （第 38–40、47–51、53–55 行）全部是 markdown 引用文本，无任何 JSON 机器块。
      因此机器层无法把本计划识别为治理变更、无法绑定治理路径的强制项；而 target_files 指向 `SKILL.md`（`CONSTITUTION.md` 第 68 行治理文档）
      又要求必须走 ultraverge（`SKILL.md` 第 181 行）。二者只能取一：要么补机器块，要么该计划不具备被治理 preflight 识别的资格。
    fix_direction: |
      在 plan 中补入 `converge.governance-change/v1` fenced JSON 机器块（目标文件、变更类型、是否触及数值阈值/停止条件、治理层级、
      target_files 等），使 preflight 能机器判定并按 `SKILL.md` 第 453 行绑定 task-envelope。若本计划按设计不提供机器块，则必须在 plan 中
      显式声明"本计划不作为 `converge.governance-change/v1` 治理输入"，并说明与 `SKILL.md` 第 181 行"治理文档修改必须 ultraverge"的衔接方式
      （例如人工以 ultraverge 流程兜底并记录来源），不能两者悬空。

  - id: UV2-08
    severity: implementation
    attribution: plan_defect
    plan_amendment_required: true
    rubric_gap: false
    location: plan §1（第 18 行）/§2（第 23 行）/§4 改动 2（第 52–56 行）
    description: |
      plan 的自述与其实际改动不一致，且该不一致使"窄数值经验门"是否适用悬空。
      plan 第 18 行称"本变更不修改 `CONSTITUTION.md` 任何条款，不修改任何数值默认/阈值/停止条件"，第 23 行称"不新增文件、不新增模式、
      不新增脚本或字段，仅在 `SKILL.md` 现有两处位置做最小规范态修订"。
      但改动 2 实际删除的是含数值门限「参与方 ≤ 2」的三条适用条件（`SKILL.md` 第 385–388 行 → plan 第 54 行），即确实移除了一个数值阈值型条件；
      同时"传话编排"的准入定义被取消，plan 第 18 行"不新增模式"的说法与"准入结构被改写"之间存在解释张力。
      `refs/reviewer-discipline.md` 第 280–286 行对"numeric defaults/thresholds/stopping conditions 的治理变更"设有专门纪律
      （`empirical_conflict` / `user_decision_required` 字段，且"已验证的 empirical conflict 不得降级为 suggestion"）。
      本计划是否落入该门正取决于这一定性；定性悬空 = 门是否开启不可判定。
      （本轮核对结论：`empirical_conflict: false`——我未获得任何与该阈值相关的可比较生产性证据，无从证实方向冲突；
      `user_decision_required: false`——无 verified empirical conflict，故不触发用户决策。该判定依赖 plan 先把定性写清楚。）
    fix_direction: |
      在 plan 中把自述改为逐条精确表述（逐条列出实际删除/新增/未改的条件），并显式判定"参与方 ≤ 2"是否属于受窄数值经验门约束的
      threshold：若是，按 `refs/reviewer-discipline.md` 第 280–286 行补齐对应字段处置说明（无实证冲突则显式记 none 并给出依据）；
      若否，给出不属于该门的理由。
```

---

## 3. suggestion_issues

```yaml
suggestion_issues:
  - id: UV2-S1
    description: |
      落地文本避免固化具体宿主专名。plan 第 29 行与第 44 行把"如 Swarm""宿主原生实时协同（如 Swarm）"带入拟写入 `SKILL.md` 的规范文本，
      而 `SKILL.md` 第 10 行声明"框架无关"、第 48–58 行的抽象能力层只定义 Spawn/Continue/Identify。宿主专名建议留在 plan §1 背景，
      规范文本只用能力泛称（"宿主原生实时协同能力"），宿主实例放 `refs/framework-adapters.md` 对应分册。
    location: plan §3 表第 1 行/§4 改动 1/改动 2(1)

  - id: UV2-S2
    description: |
      新增的"协同基底"在抽象能力层（`SKILL.md` 第 48–58 行）没有落位。要么在能力层补一行（协同基底的抽象与降级语义），
      要么在改动 1 中显式声明"协同基底属宿主能力，不改变抽象能力层契约，宿主不支持时回退隔离派发"。目前的写法留下"规范里有、
      接口层没有"的空位。
    location: SKILL.md 第 48–58 行 vs plan §4 改动 1

  - id: UV2-S3
    description: |
      "作者间接口对齐"（plan 第 14/29/39 行）是 converge 之外的域工作流。`CONSTITUTION.md` 第 28 行 Occam 判据问"这东西解决什么具体问题？
      不解决具体问题的实体删除"。若本变更不打算承载该域的约束（谁隔离、谁留痕、如何验收），建议从规范文本中删除或改为不承载约束的举例措辞，
      避免 Q2 的"虚假扩展"读法。
    location: plan §1/§3/§4 改动 1

  - id: UV2-S4
    description: |
      plan §5.4（第 63 行）写"≥3 跨模型族独立 Reviewer 并行评议"，比 `SKILL.md` 第 168 行"至少 Spawn `ultraverge_min_reviewers`（默认 3）个
      独立 Reviewer"更严（跨模型族）。建议注明这是本实例的加严执行约束而非机制变更，避免读者误以为要改默认参数——
      plan 第 18 行已声明"不修改任何数值默认/阈值"，此处口径应保持一致。
    location: plan §5.4 vs SKILL.md 第 168 行

  - id: UV2-S5
    description: |
      改动 2(1) 把 `C-21(c)` 的"记录 executor instance_id"放宽为"instance_id 或宿主协作记录"（plan 第 44 行），与
      `refs/orchestrator-guide.md` 第 420 行"**这是客观证据……非 self-report**"存在张力：若"宿主协作记录"是 Orchestrator 自述，
      留痕强度下降。建议要求宿主协作记录具备可核查标识（会话 id / 消息 id / 记录文件路径），使该条仍落在"客观证据"一侧。
    location: plan §4 改动 2(1) vs refs/orchestrator-guide.md 第 418–420 行

  - id: UV2-S6
    description: |
      plan 内三个 fenced 块（第 38–40、47–51、53–55 行）均为"拟逐字替换的规范文本"，但未标注性质。按
      `refs/reviewer-discipline.md` 第 258 行 A3，未标注的可执行代码块按常规审查并可能触发 preflight 的 `code_heavy` 提示
      （阈值见 `SKILL.md` 第 451 行 `preflight_code_block_threshold`）。建议在块首加一行"（拟替换原文 / 非规范示意）"，
      既避免 code_heavy 误触，也使 Executor 明确这些是逐字落地文本而非伪代码。
    location: plan §4（第 38–40、47–51、53–55 行）

  - id: UV2-S7
    description: |
      验收标准可加一条针对本次改动的最小机械核对（不只依赖全量 pytest）。例如：grep 断言 `SKILL.md` 中"适用条件（三条同时满足"已按裁定消失、
      "独立审计"红线位于核心角色节后、且 `refs/orchestrator-guide.md` 中不存在指向已删除小节标题的引用。可核对的验收比散文验收更抗漂移。
    location: plan §5.3

  - id: UV2-S8
    description: |
      plan frontmatter `status: in_progress`（第 2 行）。落地后应更新为 `done`/`landed`，否则 `SKILL.md` 第 476 行
      `plan_status_critical` 判定会把它标为 CRITICAL stale 项（pre-push hook，`CONVERGE_STRICT=1` 时阻断 push）。建议在 §5 中写明这一步。
    location: plan frontmatter 第 2 行 / SKILL.md 第 470–476 行
```

---

## 4. 前置自检 Q1–Q6（`refs/reviewer-discipline.md` 第 5–21 行）

| # | 维度 | 结论 | 依据 / 关联阻断 |
|---|------|------|--------------------|
| Q1 | 产物身份自洽 | **通过（附保留）** | 标题（第 10 行）、§1 目标（第 12–18 行）、§3–§4 改动三处指向同一问题（增加协同方式裁量 + 明示独立审计红线），无"声称做 A 实际做 B"。保留：改动 1 引入的"宿主原生实时协同"是宿主能力而非 `SKILL.md` 第 48–58 行抽象能力层的一等公民，身份上有"机制内引入宿主能力"的张力；以 UV2-S1/S2 处理，不单独计 blocking。 |
| Q2 | 产物边界诚实 | **不通过** | 声称范围（§1 第 18 行"不修改任何数值默认/阈值/停止条件"、§2 第 23 行"不新增模式……仅两处最小修订"、§5.2 第 61 行"与 §八 无矛盾"）与实际改动范围不匹配：删除了含数值门限的准入条件、取消了既有模式的准入定义、落地执行机制的操作细则在 `refs/orchestrator-guide.md` §八（`CONSTITUTION.md` 第 72 行治理文档）而非 `SKILL.md`，只改 `SKILL.md` 必然产生跨文档矛盾。另："作者间接口对齐"接入 converge 的协作决策存在 `/` 连接不兼容领域的虚假扩展风险（`refs/reviewer-discipline.md` 第 10 行定义）。→ blocking **UV2-02**（主）、**UV2-08**（次）；UV2-S3。 |
| Q3 | 产物数据纯度 | **通过（条件）** | 全文无项目特定业务数据、无路径/用户名/IP/工具版本硬编码；唯一宿主专名 "Antigravity Swarm" 出现在 §1 背景与 §3 表格（第 14/29 行），拟落地正文（第 39/54 行）用能力泛称。条件：落地文本不得把 "Swarm" 固化为规范术语（UV2-S1）。 |
| Q4 | 职责边界自洽 | **不通过** | 三处灰色地带：①"按耦合度自主决定"的裁量权未归入任何责任清单条目（对照 `SKILL.md` 第 347–379 行）、无可操作判据、无留痕位置；②实时协同路径与传话编排路径的约束归属不清（谁负责载荷边界/振荡检测/降级声明）；③层级模式子收敛是否在授权范围内不清。→ blocking **UV2-05**（主）、**UV2-03**、**UV2-04**。 |
| Q5 | 命名一致性 | **不通过** | 同物多词（实时协同 / 实时对话 / 共享消息板 / Swarm）；新词无定义（"独立审计红线" vs 既有"独立审计环节/盲审复核"）；"协作互审"与"独立性降级"层级混淆；改小节标题造成 `refs/orchestrator-guide.md` 第 433 行悬空引用。→ blocking **UV2-06**。 |
| Q6 | 产物 vs 原始需求一致 | **通过** | 本次无外部 reference_materials，唯一可用的原始需求即 plan 自身 §1（第 12–18 行）。改动方向与 §1 一致（放开非审计环节的协作裁量 + 保留独立审计隔离），§3/§4 未出现与 §1 相反的方向（如扩大审计环节的共享权限）。`background_mismatch: false`。 |

> Q2/Q4/Q5 三项"否"按 `refs/reviewer-discipline.md` 第 19 行触发 blocking 义务，映射到 UV2-02 / UV2-05 / UV2-06（severity = conceptual），
> 其机制性后果另以 architectural / structural 档位独立列出，避免同一事实重复计两条。

---

## 5. 设计审查 DR1–DR7（`refs/design-review-prompt.md` 第 58–99 行）

| 维度 | 结论 | 关键发现 |
|------|------|----------|
| **DR1 一致性** | concerns_found | (a) `SKILL.md` ↔ `refs/orchestrator-guide.md` §八 硬约束/流程/留痕/核对冲突（UV2-02）；(b) `SKILL.md` 第 514/519 行层级模式不变量 ↔ 新授权"层级并发施工"冲突（UV2-04）；(c) 抽象能力层（第 48–58 行）未覆盖新增"协同基底"能力（UV2-S2）；(d) `refs/orchestrator-guide.md` 第 433 行悬空引用（UV2-06）；(e) plan §5.2 验收与改动内容自相矛盾（UV2-02）。 |
| **DR2 完整性** | concerns_found | 缺 `refs/orchestrator-guide.md` 改动项（UV2-02）；缺 `converge.governance-change/v1` 机器块（UV2-07）；缺"宿主不支持实时协同能力"的回退路径（UV2-S2）；缺层级收敛排除条款（UV2-04）；缺三类硬约束在新路径上的承载（UV2-03）；缺协作方式选择的留痕（UV2-05）；改动 2 改标题后，§八 的包裹格式/记录字段/介入判据/介入前自检（第 435–468 行）是否仍适用未说明。 |
| **DR3 可维护性** | concerns_found | 同一规则（协作方式选择 + 独立性约束）落地后将散布于四处：`SKILL.md` 核心角色注记、`C-21(a)(c)`、传话编排节、`refs/orchestrator-guide.md` §八——"改一处忘另一处"的漂移风险（DR3 明确点名的风险）；新增 5 个未定义术语；"耦合度"无可复述判据，新 agent 读 `SKILL.md` 后不足以据以行动。 |
| **DR4 职责边界** | concerns_found | 三处灰色地带同 Q4。额外风险：宪法 #7 的边界在共享消息板场景更易被侵蚀——共享板让 Orchestrator 具备"顺手改一行"的可达性，而"纠偏 vs 越界"自检（`SKILL.md` 第 394 行 / `refs/orchestrator-guide.md` 第 459–468 行）是写在传话编排语境下的，改动 1 未把该自检扩展到共享板路径。 |
| **DR5 残留与冗余** | concerns_found | "机制保留而准入口被移走"型残留：传话编排在准入软化后，其专属机制（relay-ledger、振荡裁判、包裹格式、载荷强制）仅在被选中时生效，形成选择性生效的冗余机制（UV2-03）；`refs/orchestrator-guide.md` §八 对旧措辞"适用条件"的转述在改动后成为残留引用（UV2-06）。DR5 末项（"描述过去发生什么"的迁移考古）无问题。 |
| **DR6 可移植性** | concerns_found | "宿主原生实时协同（如共享消息板/Swarm）"隐含宿主能力假设，但 `SKILL.md` 第 10 行声明框架无关、第 48–58 行能力层未变；无能力探测与回退定义；不同宿主对"共享消息板"的语义（是否共享被审者可见历史、是否持久化、是否可被第三方读）未加区分——同一规范文本在不同宿主上可能行为相反，尤其"独立审计不得共享公开消息板"在部分宿主上无法机械保证。建议在改动中给出最小能力契约（是否有独立上下文 / 是否可共享历史 / 是否持久化 / 是否可读被审者消息）。 |
| **DR7 可扩展性** | concerns_found | "按耦合度自主决定"无判据 = DR7 末项"通用性边界未被承认"；新增协同基底轴无接口契约，未来接入更多宿主能力（不同 Swarm 语义）将无统一抽象位；plan 声明"不新增字段"使该轴不可观测，规模增长后无法回溯决策质量（UV2-05）。 |

---

## 6. 宪法级自检复核（plan §2 的自检是否成立）

**Bitter Lesson（`CONSTITUTION.md` 第 27、30–36 行）**
- 成立的部分：把"协作基底选择"交还 Orchestrator 判断侧，与第 36 行"verdict 裁决、prompt 工程、机制阈值与参数的设定永远留在 Orchestrator 判断侧"一致；
  保留"独立审计上下文隔离"作为硬红线属于防呆型机制（第 32 行明确"不反对防呆型机制"），方向正确。
- 不成立的部分（→ **UV2-01**）：对三条适用条件整体放松，未区分封顶型先验与防呆/契约型前提；等于用"判断分歧 fail-open"覆盖了应保留的"契约违反 fail-closed"。
  第 34 行三分判据②要求"必须留逃生舱且真实可用"——放松准入后，收敛机制自身的防呆保护是否仍真实可用，plan 未作论证。

**Occam（`CONSTITUTION.md` 第 28 行）**
- 成立的部分：不新增文件、不新增脚本、不新增模式（以不改 §八 细则为前提），改动面最小。
- 不成立的部分（→ **UV2-05**）："不新增字段"与"新增一项决策权"不匹配——决策既不可核验也不留痕，等于新增了一个没有观测点的自由度；
  若采纳 DR6 的最小能力契约建议，会新增少量文本但显著降低跨宿主行为分叉，净 Occam 收益为正。

**宪法第三部/第四部程序（`CONSTITUTION.md` 第 65–78、93–96 行）**
- target_files = `SKILL.md`（`CONSTITUTION.md` 第 68 行治理文档）→ 必须 ultraverge（`SKILL.md` 第 181 行），plan §5.4 已满足。
- 但若采纳 UV2-02 的走法 (A)（连带修改 `refs/orchestrator-guide.md`），该文件同为治理文档（第 72 行），须一并走 ultraverge 且纳入 plan 的 target_files 与改动清单。

---

## 7. 事实前提核对（`CONSTITUTION.md` 第 49 行 / `refs/orchestrator-guide.md` §九 信息源核对）

| plan 的事实主张 | 核对结果 | 依据 |
|---|---|---|
| §5.3「本仓既有测试套件通过：`python -X utf8 -m pytest tests/ -q`」 | **成立** | 只读目录列举确认 `tests/` 存在且含 13 个测试文件（含 `test_orchest.py`、`test_budget_gate.py`、`test_archive_convergence.py` 等） |
| §4 改动 2 引用的 `SKILL.md` 原文三条适用条件 | **逐字一致** | `SKILL.md` 第 385–388 行 vs plan 第 47–51 行 |
| §3/§4 所指的 `C-21` 与传话编排小节位置 | **成立** | `SKILL.md` 第 379 行（C-21）、第 381–398 行（传话编排） |
| §5.2「与 `refs/orchestrator-guide.md` §八 无矛盾」 | **不成立** | §八 硬约束第 415–416 行、流程第 395–397 行与改动 2(1) 直接冲突 |
| §1「不修改任何数值默认/阈值/停止条件」 | **不成立** | 「参与方 ≤ 2」这一数值门限条件被删除（`SKILL.md` 第 388 行 → plan 第 54 行） |
| 层级模式约束可作为背景事实引用 | **成立** | `SKILL.md` 第 514 行、第 519 行 |
| §5.4「≥3 跨模型族独立 Reviewer」 | **成立但更严于机制** | `SKILL.md` 第 168 行（默认 3，独立 Reviewer，未要求跨模型族）→ UV2-S4 |
| plan 含 `converge.governance-change/v1` 机器块 | **不存在** | 全文 63 行、三个 fenced 块均为 markdown 引用文本 → UV2-07 |

---

## 8. 归因说明与纪律自检

- **二元归因**：8 条全部 `plan_defect`。本轮审查对象是 plan 本身（Round 1，无修复历史），不存在 executor_limit 的成立条件。
- **归因一致性**：无上轮可比对（Round 1），不存在切归因。
- **措辞强度**：blocking 均为"必须修复"级；suggestion 均为建议级，未用"blocking"语言（DR 纪律第 1–5 条）。
- **`plan_amendment_required`**：8 条全部为 `true`——修复必须先回写 plan 本体（改动清单、宪法自检、验收标准），再让 Executor 改下游文件。
- **`[Orchestrator Detection]` 挑战**：本轮未读 attempts.md / round 文件（初始评议，无历史），无此类标注可挑战。
- **意图漂移检查**：条件未激活（单轮初始评议）。
- **确定性检查**：`skipped`（只读审查；本仓为 prose 治理变更，plan 自带测试命令由 Executor 在落地阶段执行），`deterministic_check_skip_reason: "只读评审任务，禁止修改仓库状态；plan §5.3 的测试套件由落地 Executor 执行"`。
- **禁止操作自检**：未执行任何 `git reset/checkout/restore/stash/clean/commit` 类操作；仅使用只读文件读取与目录列举。
- **窄数值经验门**（条件激活）：`empirical_conflict: false`（无可比较生产性证据）、`user_decision_required: false`（无 verified empirical conflict）。该判定依赖 UV2-08 先把"参与方 ≤ 2"的定性写清楚。

```yaml
antipattern_observations:
  - round_referenced: 1
    type: environment_lock-in
    evidence: |
      plan 第 29 行「宿主原生实时协同（如 Swarm）」与第 39 行「（如共享消息板/Swarm）」拟写入 `SKILL.md`，
      而 `SKILL.md` 第 10 行声明"框架无关"、第 48–58 行的抽象能力层只定义 Spawn/Continue/Identify——
      宿主专名进入框架无关的规范文本，构成环境锁定风险（见 UV2-S1）。
  - round_referenced: 1
    type: false_generality
    evidence: |
      plan 第 39 行「由 Orchestrator 按耦合度自主决定，不作强制」：通用化地授予一项裁量权，却无判据、无能力契约、
      无留痕位置——同一规范文本在不同宿主与不同会话上的实际行为不可预测（见 UV2-05 / DR6 / DR7）。
```

---

## 9. reads

```yaml
reads:
  - "<user-home>\\Documents\\GitHub\\converge-skill\\docs\\plans\\active\\20261126-on-demand-realtime-collab.md"   # 全文 63 行（输入 1）
  - "<user-home>\\Documents\\GitHub\\converge-skill\\CONSTITUTION.md"                                              # 全文 96 行（输入 2）
  - "<user-home>\\Documents\\GitHub\\converge-skill\\SKILL.md"                                                    # 全文 547 行（输入 3，分两次读取：1–486、487–547）
  - "<user-home>\\Documents\\GitHub\\converge-skill\\refs\\reviewer-discipline.md"                                   # 全文 300 行（输入 4）
  - "<user-home>\\Documents\\GitHub\\converge-skill\\refs\\design-review-prompt.md"                                  # 全文 188 行（输入 5）
  - "<user-home>\\Documents\\GitHub\\converge-skill\\refs\\orchestrator-guide.md"                                   # 第 55–184 行、第 380–539 行（输入 6；§八落地执行编排与传话编排全文在第 388–468 行）
```

补充（只读目录列举，未读取文件内容；用于核实 plan §5.3 与 §7 的事实前提）：

```yaml
read_only_directory_listings:
  - "<user-home>\\Documents\\GitHub\\converge-skill\\tests\\**"            # 13 个测试文件存在性
  - "<user-home>\\Documents\\GitHub\\converge-skill\\.converge\\**"        # 审查前不存在（本报告写入时创建）
  - "<user-home>\\Documents\\GitHub\\converge-skill\\docs\\plans\\active\\*.md"  # 1 个 plan 文件
```

---

## 10. 处置建议（供 Orchestrator 裁决，非本 Reviewer 的执行动作）

1. **不要跳过完整收敛**：本轮 verdict ≠ 可执行且含 conceptual/architectural 阻断，按 `SKILL.md` 第 162–165 行 ultraverge 路径进入标准收敛流程。
2. **先回写 plan 本体**（8 条全部 `plan_amendment_required: true`），再让 Executor 改下游文件；其中 UV2-02、UV2-07 需要改 plan 的 frontmatter 与改动清单（target_files 增加 `refs/orchestrator-guide.md`；新增机器块），属于结构性回写。
3. **优先裁定的两个二选一决策**（其余修复依赖其结果）：
   - UV2-01/UV2-02：三条适用条件是"分层保留"还是"整体保留 + 新增并列协作基底"；落地执行是否允许改用宿主原生实时协同（决定是否连带修改 §八）。
   - UV2-03：三项硬约束的载体是否从"模式名"上移到"协同类别"。
4. **收敛后强制设计审查**（`SKILL.md` 第 177 行 ultraverge 强制项）：本变更触及 `SKILL.md` 与 `refs/orchestrator-guide.md` 两份治理文档、定义了新的协作基底轴，DR4/DR6/DR7 仍有 open 项。
