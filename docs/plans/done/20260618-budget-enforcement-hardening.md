---
type: plan
status: active
created: 2026-06-18
revised: 2026-06-19
revision: v7
scope: converge SKILL 预算执行硬化 — atomic reserve + 宿主角色 FSM + 总 spawn 硬上限（单调）兜底 + 仅追加事件流（含 decision 事件）+ 按 scope 有效计数
governance: true
note: 动预算/终止判定属治理域，落地修改本身按明线规则走 ultraverge
trigger: 某执行侧 agent 31 轮（20 outer + 11 blind）失控未收敛后的复盘反馈
feedback_source: "C:/Project/computer-use-mcp/.converge/active/20260617-post-review-improvements/skill-feedback.md"
audit_trail: "v1=需重新设计(6) → v2(6) → v3(3) → v4(2) → v5(2) → v6(3) → v7 据 v6 复审闭合总量上限契约内部不一致（单调计数/确定性默认/total scope/decision 语义/tier 表述）。审计已确认 FSM 枚举冻结转测试。逐轮处置见 §审计响应"
related:
  - "SKILL.md"
  - "CONSTITUTION.md"
  - "refs/state-schema.md"
  - "refs/orchestrator-guide.md"
  - "refs/framework-adapters.md"
  - "scripts/"
---

# 预算执行硬化（Budget Enforcement Hardening）· v6

## 摘要

某执行侧 agent converge 一份 post-review 计划时跑了 **31 轮**（20 outer + 11 盲审），远超默认预算（`max_outer_loops=5` / `max_blind_rechecks=2`），未收敛、用户主动暂停。根因：预算上限是 prose 主循环里的数字，没有检查点强制 `current_round ≥ 上限` 在每次 spawn 前真正比较；计数活在工作记忆里，跨 compaction 停止比较。

设计经六轮审计收敛。核心脊柱：

- **信任边界二元分级 + 总量兜底**：宿主具备 Agent-不可写的 session→slug 绑定 + 角色 FSM 时 → pre-spawn hook 原子裁决拒绝超预算/越权 spawn（**enforced**）；任一缺失 → 整体 **auditable-only**（无宿主强制，仅审计 + 可阻断 push）。**enforced tier 内、无论角色分类**，一律附加一个单调的总 spawn 硬上限——即便角色被伪标也能兜住 runaway 的最后防线。auditable-only 路径不经宿主强制，故无此硬上限（与其降级定义一致）。
- **计数与角色均为宿主事件流上的确定性函数**：reserve/settle/decision 由宿主 hook 自动驱动并落 ledger，角色由宿主 FSM 派生。

**核心立场**：不把修复寄托在 orchestrator 的记忆或承诺上。

## 审计响应（逐轮处置）

> 完整轨迹见 frontmatter `audit_trail`。本表是论证记录，不进 SKILL.md 规范文本。

**v1→v2**：信任边界分级、ledger、extension 列表、确定性判据、测试矩阵、层级 gate。
**v2→v3**：三态绑定、原子 reserve、ledger 事件流、extension 仅追加链、覆盖范围表、`>=50%`。
**v3→v4**：角色须宿主校验、计数模型 + 自动 settle、孤儿按额度隔离、ultraverge 独立上限。
**v4→v5**：角色 FSM 契约、extension scope-agnostic 字段、二元 tier。

**v5→v6（本轮 3 缺口）**：

| # | v5 复审阻断 | v6 处置 |
|---|------------|---------|
| 1 | FSM 只分配角色**标签**，不能验证 Agent 实际执行的角色；Orchestrator 仍可在 FSM 期待 executor 时提交 reviewer prompt，按 `consumes:none` 放行 | **接受**：(a) 增加**与角色无关的总 spawn 硬上限** `max_total_reserved_spawns`（兜底，伪标也受限）;(b) **诚实降级主张**——宿主不拥有 prompt/template 时（含 Claude Code），enforced 只声称"计费标签 FSM 受控 + 总量硬上限 + 按 scope 预算尽力计费"，**不**声称"角色不可伪造"。宿主能拥有 prompt 模板时才升级为角色不可伪造（M1-role）|
| 2 | 转换表有一条错误（concept/arch 阻断跳过 executor）+ 多处未覆盖（标准 deliberate、Round 0 三步、ultraverge 模式位、arbitration 返回、executor 后 inner-loop）| **接受**：FSM state 增 `mode` / `return_phase` / `inner-verify` 阶段;转换表纠错并补全（M1-role 转换表）|
| 3 | extension 引用的 `triggering_block_event_id` 指向不存在的 BLOCK 事件 | **接受**：ledger 增 **decision 事件**（每次 BLOCK/DENY/MODE_SWITCH/FAIL_CLOSED 原子追加）;extension 三项交叉校验 scope / granted_at_usage / prior_ceiling 与 decision 事件一致（M2-decision + M2-ext）|
| 判断 | 二元 tier | 维持（审计确认）|

**v6→v7（总量上限契约一致性，审计确认这是计划层最后一个机制修订）**：

| # | v6 复审阻断 | v7 处置 |
|---|------------|---------|
| 1 | `total_reserved` 排除 failed/cancelled → 反复失败可无限消耗 | **接受**：改单调 `total_reservations_issued`（永不被失败递减）;仅宿主背书 `pre_execution:true` 的 cancellation 不计（§计数模型）|
| 2 | `max_total_reserved_spawns` 无默认/推导公式 | **接受**：给确定性公式（随 budget 参数缩放，stock=44）（§计数模型）|
| 3 | extension schema 不接受 `scope=total` | **接受**：scope enum 加 `total`（M2-ext）|
| 4 | total-cap decision 用 `scope:null` 无法表达总量值 | **接受**：total-cap decision 用 `scope=total`，observed_usage/effective_ceiling 取总量值;`null` 仅留给 DENY/FAIL_CLOSED 等非 scope 决策（M2-decision）|
| 5 | "无论 tier 均有硬上限"不成立（auditable-only 直接放行）| **接受**：改"**enforced tier 内**一律附加";auditable-only 无宿主强制上限（摘要）|
| FSM 枚举 | 未枚举转换由 fail-closed 覆盖 | **冻结转实现测试**（审计同意 altitude 分界）|

## 设计原则自检（宪法第一部）

| 原则 | 自检 | 结论 |
|------|------|------|
| **Bitter Lesson** | 通用机制还是模型补丁？ | 通用：FSM/计数/总量上限是确定性资源边界，独立于哪个模型编排。总 spawn 硬上限尤其是"不验证语义、只界定资源"的 Bitter-Lesson 兜底。**通过** |
| **Occam** | 多余实体？ | 总量上限是一个标量 + 一个 reserve 前置检查，复用既有 reserve/ledger;decision 事件复用 ledger。**通过** |

## 核心机制

### M1 · file-authoritative budget gate（原子 reserve）

脚本 `scripts/budget_gate.py`（**只定义契约，不附实现**）。**自行从磁盘 + ledger + FSM 重算，不接受外部传入计数/角色**。

| 模式 | 用途 | 输出 / exit |
|------|------|------------|
| `reserve` | **原子**：加锁→**总量上限检查**→重算有效计数→FSM 领取角色→预算裁决→（PROCEED 时）追加 `reserved`+签发 reservation_id;（非 PROCEED 时）追加 **decision 事件**→解锁 | `PROCEED:<reservation_id>`(0) / `BLOCK:total_spawn_cap`(13) / `BLOCK:{budget,blind,ultraverge}_exhausted`(10/11/12) / `MODE_SWITCH_REQUIRED`(20) / `DENY:{unknown,illegal}_role`(21/22) / `FAIL_CLOSED:<reason>`(30) |
| `settle` | 宿主 `PostToolUse`/`PostToolUseFailure` 自动调用，追加结果事件 + 回收 in_flight | `OK`(0) / `FAIL_CLOSED`(30) |
| `ingest_verdict` | 解析已落成产物 structured verdict 驱动 FSM 转换;解析失败 → fail-closed | `next_phase`(0) / `FAIL_CLOSED:verdict_parse`(30) |
| `preflight` | M4 plan 代码片段检查 | `CLEAN`(0) / `WARN:code_heavy:<blocks>,<loc>`(0) |

reservation 键 = `PreToolUse` 的 `session_id` + `tool_use_id`。原子性消除 TOCTOU。

#### M1-tier · 二元信任边界

| 绑定 + 角色 FSM 完整性（宿主域权威）| hook 行为 | tier |
|------------------------------|----------|------|
| session 绑定唯一 slug 可解析 **且** 角色 FSM 可用 | 运行 `reserve`，非 PROCEED → **deny** | enforced |
| 已绑定但歧义/损坏，**或** FSM 不可用/损坏 | **deny**（fail-closed）| enforced 区间内安全拒绝 |
| **未绑定** | **放行**，明确 auditable-only | auditable-only |

**enforced 前提**：绑定 + FSM 状态须位于 Agent 工具**无法写入**的宿主域。任一缺失 → 整体 auditable-only。能力位仅内部诊断记录，不对用户暴露"半强制"口径。

#### M1-role · 角色 FSM 契约 + 执行不可验证的诚实边界（解决 v5 #1/#2）

**角色权威 = 宿主 FSM**，角色由 phase 派生、不读 Agent prompt;reserve 即向 FSM 原子领取角色配额，reservation 即授权令牌（无独立 token）。

**但 FSM 只能控制角色的计费标签，不能验证 Agent prompt 实际让其做什么**（Orchestrator 控制 prompt 内容）。据此分两档诚实声称：

| 宿主能力 | enforced 实际保证 |
|---------|------------------|
| 宿主**拥有** role→prompt/template（Orchestrator 只能填参数槽，不能提交自由 prompt）| **角色不可伪造** + 总量上限 + 按 scope 预算 |
| 宿主**不拥有** prompt（含 Claude Code，subagent prompt 由调用方全权控制）| **计费标签 FSM 受控** + **总 spawn 硬上限**（兜底 runaway）+ 按 scope 预算**尽力计费**;**不声称角色不可伪造** |

> 第二档的残余漏洞：Orchestrator 可把 reviewer prompt 标成 executor 拿 `consumes:none`，绕过该 spawn 的 scope 计费。**但 `max_total_reserved_spawns` 对所有角色（含 `consumes:none`）一律计数**，故伪标无法突破总量——31 轮 runaway 在总量上限下被硬停，无论标签如何。这是"无法验证语义就界定资源总量"的 Bitter-Lesson 兜底。

**FSM 状态**（Agent-不可写宿主域，每 slug 一份）：

```yaml
fsm:
  phase: <round-0 | deliberate | outer-review | outer-execute | inner-verify | blind | arbitration | design-review | completed>
  mode: <standard | ultraverge>          # 持久；ultraverge 在收口强制 design-review
  round: <N>
  return_phase: <phase 或 null>           # 中断式阶段（arbitration）恢复用
  allowed_roles: [{role, quota, consumes}]
  in_flight: {<role>: <未 settle 数>}      # 配额集合，非标量
  awaiting_verdict: [<reservation_id> ...]
```

**原子领取**（reserve 锁内）：总量上限 → 候选角色（`in_flight[role] < quota`）→ 无候选 `DENY:illegal_role` / 未注册 `DENY:unknown_role` → 预算裁决 → 成功 `in_flight[role]++` + 签发。

**转换表**（`ingest_verdict`，settle 后;settle 仅表调用完成，转换需 verdict）：

| (phase, 事件/verdict) | next |
|----------------------|------|
| (round-0, proposer settled) | round-0 · challenger |
| (round-0, challenger settled) | round-0 · finalizer |
| (round-0, finalizer settled) | deliberate |
| (deliberate[standard 单 reviewer], 可执行) | mode==ultraverge?→design-review : (round≥2?blind:completed) |
| (deliberate[standard], 阻断 任意级) | outer-execute（concept/arch 置 escalation 标志）|
| (deliberate[ultraverge 批次全 settle+汇总], 可执行) | design-review（强制）|
| (deliberate[ultraverge 批次], ≠可执行) | outer-review（round=1，mode 保持 ultraverge）|
| (outer-review, 可执行) | **mode==ultraverge?→design-review** : (round≥2?blind:completed) |
| (outer-review, 阻断 impl/struct) | outer-execute |
| (outer-review, 阻断 concept/arch) | **outer-execute（escalation 标志）** ← 纠错：仍需 executor 修复 |
| (outer-execute, executor settled) | **inner-verify** ← 纠错：inner loop 先于下一轮 reviewer |
| (inner-verify, Continue 验收=可执行) | mode==ultraverge?→design-review : (round≥2?blind:completed) |
| (inner-verify, Continue 打回 且 Continue 次数<`max_inner_loops`) | outer-execute（同轮再修，executor consumes:none）|
| (inner-verify, Continue 次数==`max_inner_loops` 未通过) | outer-review（round+1，fresh reviewer）|
| (blind, 零阻断) | completed |
| (blind, 有阻断) | outer-execute |
| (arbitration 触发于 phase P) | 置 `return_phase=P`，phase=arbitration |
| (arbitration, arbiter settled) | `return_phase` |
| (design-review, settled) | completed |

> 本表是 **normative 转换契约**；落地阶段须以测试**逐分支**覆盖（见 §测试），不在本文档穷举每个微转换（守 M4，避免把 plan 拖入实现层穷举）。未覆盖分支 → fail-closed（宁拒不漏）。

**阶段终止**：顺序阶段 = 唯一 in_flight 归 0 且 verdict ingest;并行阶段（deliberate/ultraverge 批次）= `in_flight==0` 且 verdict 汇总。**inner-verify 是 Continue 驱动的无 Spawn 阶段**，仅用于阻止过早 spawn 下一轮 reviewer。

**FSM fail-closed**：verdict 解析失败;in_flight≠0 时请求转换;领取角色 ∉ allowed_roles。

### §计数模型（解决 v3 #2）

每 scope `s ∈ {outer, blind, ultraverge}`：

```text
realized(s) = | 已落成产物 |     # outer: round-N.md; blind: blind-recheck-N.md; ultraverge: uv-init-N.md
pending(s)  = | reservations: consumes=s, status∈{reserved,spawn_succeeded}, target 尚不存在 |
effective_usage(s) = realized(s) + pending(s)
reserve: PROCEED iff total_reservations_issued < max_total_reserved_spawns  AND  effective_usage(s) < ceiling(s)   # 锁内
```

去重（target 存在→realized 排除 pending）、释放（failed/cancelled 排除两者）、孤儿（reserved 无 settle→占 pending 自己一格不全局阻断）、并发正确性（锁内原子）同 v4/v5。

**总量计数（与 scope 计数语义**故意非对称**，解决 v6 #1）**：`total_reservations_issued` = ledger 中**所有 `reserved` 事件的单调累计**（含 `consumes:none`），**永不被 failed / spawn 失败递减**——否则可用"反复失败"无限消耗 Agent 调用。唯一例外：带宿主背书 `pre_execution: true` 的 `cancelled`（证明工具从未执行、零消耗）不计入。`total` **不**走 realized+pending 模型，是独立单调计数器。

> 为何 scope 释放 failed 而 total 不释放：scope 是**产出预算**（失败 spawn 无 round 产出 → 可释放）;total 是**资源消耗上限**（失败 spawn 仍消耗一次调用，且必须封堵失败循环 → 单调）。

**`max_total_reserved_spawns` 确定性默认（解决 v6 #2，非"pilot 拍脑袋"）**：

```text
default = ceil( TOTAL_SAFETY × [ 3(Round0) + max_ultraverge_initial
                + max_outer_loops × (1 + max_inner_loops)        # 每轮 1 reviewer + 至多 inner-loop executor 修复
                + max_blind_rechecks + 1(design-review) ] )
TOTAL_SAFETY 默认 1.5（含 arbitration 等 consumes:none 触发余量）
# stock 参数(outer5/inner3/blind2/uv3): base=3+3+20+2+1=29 → default=ceil(43.5)=44
```

扩容经 `scope=total` 的 extension 显式授权（见 M2-ext）。

### M2 · gate ledger（事件流，仅追加）

`active/<slug>/gate-ledger.md`，**无历史改写**：`reserved` / `spawn_succeeded` / `spawn_failed|cancelled` / **`decision`**。

#### M2-decision · 决策事件（解决 v5 #3）

每次非 PROCEED 裁决（BLOCK*/DENY*/MODE_SWITCH/FAIL_CLOSED）在 reserve 锁内**原子追加**：

```yaml
- event: decision
  decision_event_id: <id>
  ts: <ISO>
  verdict: <BLOCK:* | DENY:* | MODE_SWITCH_REQUIRED | FAIL_CLOSED:*>
  scope: <outer | blind | ultraverge | total | null>   # null 仅用于 DENY/FAIL_CLOSED/MODE_SWITCH 等非 scope 决策（解决 v6 #4）
  observed_usage: <effective_usage(scope);scope=total → total_reservations_issued;scope=null → null>
  effective_ceiling: <ceiling(scope);scope=total → max_total_reserved_spawns;scope=null → null>
```

> `BLOCK:total_spawn_cap` 的 decision 用 `scope=total`（非 null），故 observed_usage/effective_ceiling 能表达总量值，extension 才可交叉校验。BLOCK 系决策的 scope 永不为 null。

#### M2-settle · 宿主自动结算

`PostToolUse`→`spawn_succeeded`（带 instance_id）;`PostToolUseFailure`→`spawn_failed`;工具调用在执行前被中止 → `cancelled`（**带宿主背书 `pre_execution: <bool>`**：仅宿主能证明工具从未执行时为 true，此类不计入 `total_reservations_issued`）。settle 同时回收 FSM `in_flight`、reviewer reservation 入 `awaiting_verdict`。auditable-only 宿主无 Post hook → settle 落责任清单（可能孤儿，收口/pre-push 检出）。

#### M2-orphan · 孤儿按额度隔离

consuming 孤儿占自己一格不全局阻断;`consumes:none` 孤儿记异常不阻断;收口前全解决;仅生命周期非法/重复 settlement → FAIL_CLOSED。

#### M2-ext · extension 仅追加链 + decision 绑定（解决 v4 #2 + v5 #3）

state `budget_extensions` 仅追加，新记录写 `supersedes`，旧记录不可改：

```yaml
budget_extensions:
  - extension_id: <id>
    ts: <ISO>
    scope: <outer | blind | ultraverge | total>            # 含 total（解决 v6 #3）
    triggering_block_event_id: <对应 decision 事件 id>     # 必须指向真实 BLOCK decision
    granted_at_usage: <int>
    prior_ceiling: <int>
    new_ceiling: <int>
    supersedes: <旧 id 或 null>
    user_quote: <用户原话>      # 人类可审计凭据，非机械证据
```

**校验（确定性，违反 → FAIL_CLOSED）**：
- `triggering_block_event_id` 指向 ledger 中真实存在的 `decision` 事件，且其 verdict 为 BLOCK 系;
- `scope` == 该 decision.scope;
- `granted_at_usage` == 该 decision.observed_usage;
- `prior_ceiling` == 该 decision.effective_ceiling;
- 同 scope `supersedes` 线性链（无分叉/环）、`new_ceiling` 沿链单调递增且 `> prior_ceiling`。

生效令牌 = 同 scope 不被 `supersedes` 指向者。`user_quote` 只证明 state 存在该文本，不机械证明来自用户。

### M3 · 盲审疲劳 + 边际递减 → 模式切换

盲审连续失败达 `max_blind_rechecks` → `BLOCK:blind_exhausted`(11) + 菜单（继续需 extension / 终止-c / 简化 / 终止）。近 `impl_severity_streak_threshold`(默认 3) 轮每轮 blocking 中 `implementation` 占比 `>=50%` 且每轮都满足 → `MODE_SWITCH_REQUIRED`(20)。依赖 reviewer 逐条 severity。

### M4 · plan 代码片段前置自检（最高杠杆）

`preflight` 超 `preflight_code_block_threshold` → `WARN:code_heavy`，提示剥离或标 `非规范`。`非规范`：盲审免逐行实现审查，**仍查**与规范/验收/安全边界矛盾。

## 预算覆盖范围

armed session 每个 `Agent` spawn 经 `reserve`，角色由 FSM 派生;**所有角色（含 `consumes:none`）一律计入 `max_total_reserved_spawns`**。

| spawn 角色 | scope 计费 / 上限 |
|-----------|-------------------|
| outer-loop reviewer | outer / `max_outer_loops` |
| 盲审 reviewer | blind / `max_blind_rechecks` |
| ultraverge 初审 reviewer | ultraverge / `max_ultraverge_initial`（默认=`ultraverge_min_reviewers`）|
| executor / Round 0 / 仲裁 / L2 gate / 设计审查 | none（但计入总量）|
| inner loop 验收 | N/A（Continue 非 Spawn，不计总量）|
| 未注册角色 | `DENY:unknown_role`(21) |
| 越权角色（FSM allowed_roles 外）| `DENY:illegal_role`(22) |
| **任意角色累计 ≥ 总量上限** | `BLOCK:total_spawn_cap`(13) |

## 确定性判据

- **退出码优先级**：`FAIL_CLOSED`(30) > `DENY`(21/22) > `BLOCK`(10/11/12/13) > `MODE_SWITCH_REQUIRED`(20) > `PROCEED`(0)。总量上限 BLOCK(13) 在锁内最先检查，但 FAIL_CLOSED/DENY 仍优先返回。
- **fail-closed 触发**：state 缺失/损坏 / round 断号/重复 / ledger 与磁盘不一致 / extension 链或 decision 绑定非法 / reservation 生命周期非法或重复 settlement / verdict 解析失败 / in_flight≠0 请求转换 / 路径不可解析。（单纯未结孤儿不全局 FAIL_CLOSED。）
- **简化不重置预算**：原 slug 内不清零;全新收敛 = 新 slug + 显式用户决定 + 记录。
- **BLOCK 与 MODE_SWITCH 同发**：返回 BLOCK，模式切换作为菜单选项。

## 测试与验收

> 列**验收用例**，落地实现为测试;不附测试码（守 M4）。仓库当前无 `tests/`，落地须新建。

| 用例域 | 必覆盖场景 |
|--------|-----------|
| 总量上限 | 累计 spawn 达 `max_total_reserved_spawns` → `BLOCK:total_spawn_cap`;**reviewer 伪标 executor 仍计入总量、到顶仍硬停**;**反复 spawn_failed 不释放总量（单调，封堵失败循环）**;`pre_execution:true` cancellation 不计入总量;确定性默认公式随 budget 参数缩放;total-cap decision 用 `scope=total` 且 extension 可交叉校验 |
| 边界值 | round = ceiling-1/=ceiling/=ceiling+1（outer/blind/ultraverge 各自）|
| 并发 | 并发 reserve 争最后额度仅一个 PROCEED;并行 `consumes:none` 不互阻 |
| 计数去重 | reservation 与完成 round 不双计;target 出现后 pending→realized |
| FSM 转换 | **逐分支**：round-0 三步;标准 deliberate;**concept/arch→executor（非跳过）**;**executor→inner-verify→(通过/打回再修/耗尽换轮)**;**ultraverge mode 位在收口强制 design-review**;**arbitration return_phase 恢复**;ultraverge 批次领满 quota 第 N+1 DENY;out-of-phase→`DENY:illegal_role`;verdict 解析失败→FAIL_CLOSED;in_flight≠0 请求转换→FAIL_CLOSED |
| 角色伪造 | 宿主拥有 template：reviewer 不能被当 executor;宿主不拥有：标签可错但总量兜底，且 ledger 留痕 |
| settlement | `PostToolUse`/`PostToolUseFailure` 自动 settle + 回收 in_flight;failed/cancelled 释放额度 |
| 孤儿 | consuming 占自己一格不全局阻断;`consumes:none` 记异常;重复 settlement→FAIL_CLOSED;收口前未结孤儿检出 |
| extension+decision | 每次 BLOCK 落 decision 事件;extension 三项交叉校验（scope/usage/ceiling）一致才生效，不一致或指向不存在事件→FAIL_CLOSED;`supersedes` 链单调;ultraverge 扩容 |
| 绑定/FSM 二元 | 绑定+FSM 全在→enforce;任一缺→auditable-only;歧义/损坏→deny |
| 多 slug | 多 active slug 并存 reserve 命中正确 slug |
| 畸形 state | 缺失/损坏/断号/重复/不一致 → FAIL_CLOSED |
| pre-push | `CONVERGE_STRICT=1` 违规 exit 1 阻断;未设 exit 0 仅提示 |
| preflight | code-heavy→WARN;纯任务/边界/验收→CLEAN |

## 层级模式

每个子收敛独立执行自己的 gate（各自 `active/<sub-slug>/`、独立 ledger + extension 链 + 计数 + FSM + 总量上限）。Planner 层不设全局预算 gate。修改通用主循环后层级路径自动继承。

## 文件改动清单

| 文件 | 改动 |
|------|------|
| `scripts/budget_gate.py` | **新增**（不附码）。模式 `reserve`（原子：总量→FSM→预算）/ `settle` / `ingest_verdict` / `preflight`;fail-closed |
| `scripts/hooks/` + 宿主 hook 配置 | **新增** `PreToolUse`（reserve+deny）+ `PostToolUse`/`PostToolUseFailure`（自动 settle）;session→slug 绑定 + 角色 FSM 须存于 Agent-不可写宿主域，否则 auditable-only |
| `SKILL.md` 执行流程 · 主循环 | spawn 前 `reserve`、spawn 后自动 `settle`、产物落成后 `ingest_verdict`;step 4 改为 gate BLOCK → 决策菜单 + extension 方可续 |
| `SKILL.md` 盲审复核小节 | 超 `max_blind_rechecks` 改 gate 裁决 + 菜单 |
| `SKILL.md` 配置参数 | 新增 `impl_severity_streak_threshold`(3)、`preflight_code_block_threshold`、`max_ultraverge_initial`、**`max_total_reserved_spawns`（总 spawn 硬上限，确定性默认见 §计数模型公式，可经 scope=total extension 扩容）**、`TOTAL_SAFETY`(1.5) |
| `SKILL.md` 责任清单 | 新增"reserve 编排 + 孤儿收口"、"FSM verdict ingest + mode/return_phase 维护（enforced）"、"授权链 + decision 绑定核验";标 auditable-only 宿主为降级 |
| `SKILL.md` 收敛完成前必检 | 每个预算内 spawn 有有效 reservation 且已 settle、无未结孤儿;extension 仅改 ceiling 不替代 reservation;每个 extension 关联真实 decision 事件 + user_quote;总量未突破 |
| `CONSTITUTION.md` 第二部 | #3/#5 **澄清强化**（不改底线）：明确"走 converge 并执行"不授权预算扩展/mode switch/终止-b/c。**须人工审议** |
| `refs/state-schema.md` | 新增 `gate-ledger.md` 事件流（含 decision）+ 计数模型 + 角色 FSM 状态（含 mode/return_phase）schema、`budget_extensions` 仅追加链 + decision 绑定;rule_frequency 加 `budget_gate` |
| `refs/orchestrator-guide.md` | reserve/settle/ingest_verdict 编排、FSM 阶段/转换表（含 inner-verify/arbitration/ultraverge mode）、决策菜单、extension+decision 绑定、孤儿收口、fail-closed 处置 |
| `refs/reviewer-prompt.md` | 核实/补逐条 severity + structured verdict（FSM 转换依赖可解析 verdict）;盲审变体加 `非规范`"免逐行实现审查、仍查矛盾" |
| `refs/framework-adapters.md` | A.1 增补 pre/post-spawn hook + session 绑定 + 角色 FSM + **是否拥有 role→prompt 模板**（决定 enforced 是否声称角色不可伪造）;各 adapter 注明 enforced 要件有无 |
| `tests/` | **新增** + §测试与验收 用例 |
| `scripts/hooks/stale-check.py` + `pre-push` | 增 CRITICAL：预算突破 / 总量突破 / 缺 reservation 轮次 / 未结孤儿 |

## 不做的事

- **不附 `budget_gate.py` / hook / FSM 实现码**——否则重演反馈 §3.1 螺旋（M4 自洽性检验）。
- **不声称无条件物理硬停 / 无条件角色不可伪造**——按宿主能力诚实分档，总量上限是普适兜底。
- **不为预算检查开多脚本**。
- **不改默认上限值**（`max_outer_loops` 等）。
- **不让 gate 替用户决策**。
- **不在原 slug 内重置预算**。
- **不让单纯孤儿全局阻断**。
- **不另设独立一次性 token**——reservation 即授权令牌。
- **不在本 plan 穷举 FSM 每个微转换**——normative 表 + 实现层逐分支测试，未覆盖 fail-closed。

## 风险评估

| 风险 | 等级 | 缓解 |
|------|------|------|
| 宿主不拥有 prompt 模板 → 角色可伪标 | 中 | 总 spawn 硬上限兜底（伪标也计入）+ 诚实降级主张 + ledger 留痕 |
| `max_total_reserved_spawns` 设太低误伤 / 太高失兜底 | 低 | 确定性公式默认（§计数模型）随 budget 参数自动缩放，无需拍脑袋;scope=total extension 显式扩容 |
| FSM 转换表漏某真实分支 → 误 DENY/FAIL_CLOSED | 中 | 未覆盖即 fail-closed（宁拒不漏）+ 逐分支测试 + 落地补全 |
| 宿主无法提供 Agent-不可写绑定/FSM → enforced 落空 | 中 | 前提硬性：缺则整体 auditable-only |
| 孤儿收口前未解决 | 中 | 收口必检 + pre-push CRITICAL + consuming 孤儿占额度自然压力 |
| severity 分级不可靠 → M3 误判 | 中 | M3 只触发 MODE_SWITCH（建议）|

## 落地约束

动 `SKILL.md` 预算/终止判定 + `CONSTITUTION.md` 第二部 + 新增脚本/hook/tests，属治理域且触及宪法。**落地修改本身按明线规则走 ultraverge**（≥3 并行 Reviewer + 收敛 + 强制设计审查），收敛通过后**人工确认**提交（宪法第四部）;`CONSTITUTION.md` 第二部改动额外需人工审议记录。

> 元层自洽性检验：本 plan 只写契约 + 数据 schema、不附实现码——若附了 gate/hook/FSM 源码，会在 ultraverge 时把 reviewer 拖入实现层审查，重演触发本方案的 31 轮螺旋。本 plan 是否遵守自己的 M4，是它能否收敛的前提。
