# Orchestrator 操作指南

> Orchestrator 承担的不只是"别偷懒"——每一条责任都是需要判断力的语义推理。本文件提供操作步骤、偏见意识和边界场景处置。

---

## Archive / reopen 操作

每次 Spawn/Continue 的宿主调用前运行 `scripts/archive_convergence.py begin-invocation`；返回后立即 `complete-invocation`，中断则 `recover-invocation`。先 reserve 后 begin，先取得宿主返回再 settle/complete，并让 terminal 的 settlement ref 指向 ledger。缺 receipt 或 resolved model 时记录 unavailable/configured degradation，不猜测。

归档顺序只有一条：完成 canonical round/retrospective 对 terminal decision event id/value 的引用，必要时记录 design-review advisory completion，然后运行 `python scripts/archive_convergence.py archive .converge/active .converge/done <slug>`。不得手工 finalize、生成 INDEX 或移动目录。失败时按 diagnostic 的 code/path/next_action 修复 owner fact；存在 journal 时先检查 `preparing/source-backed-up/committed/rolled-back/reopen-prepared/reopen-moved/recoverable`，直接重试同一命令触发幂等恢复，不得手工删除 source、backup、staging 或 journal。

收敛后修订运行 `python scripts/archive_convergence.py reopen .converge/active .converge/done <slug>`。它验证 done、原子移回 active、保存旧 manifest revision；修订只追加 events/canonical 记录，重新审查并再次 archive。旧 INDEX 不保存，因为旧 manifest 可重建它。

bootstrap 只在 staging 副本导入 legacy raw evidence。绑定必须由 ledger reservation、state instance registry、round log 或显式 mapping 唯一确定；无法唯一绑定即停止，不按文件名猜 role/model。旧 done 目录由 scan 报 legacy，只读且不原地升级。

## 〇、启动决策：converge 还是直接改？

在 spawn 任何 agent 之前，先按以下顺序判断任务是否需要走 converge。

### 三问 + 宪法自检

在判定 converge 还是直接改之前，以下宪法级约束优先于所有三问：

- **Bitter Lesson 自检**：这个改动是通用机制，还是针对当前模型能力的补丁？若是补丁，不固化到章程——做成 compiled / 可替换的产物（如 config 参数、外部脚本、retrospective 经验项）。若是机制，才允许写入 SKILL.md 或 refs/。
- **Occam 自检**：这个改动解决什么具体问题？说得出 → 保留。只是"让体系更完整"、覆盖 "可能以后会用到" 的场景 → 删除。

以上两条**否决权重高于三问**——宪法不过，后面的决策没有意义。

### 三问

1. **可机械验证吗？**
   - 有测试/lint 能自动判对错 → **不用 converge**。直接改 + 跑测试。测试通过即完成。
   - 无自动验证手段（如 prose 产物、设计决策、架构方案）→ 继续第 2 问

2. **连锁影响范围大吗？**
   - 单文件、单模块、< 30 行变更 → 倾向不用 converge
   - 跨文件、跨模块、涉及架构决策 → 倾向用 converge

3. **回滚成本高吗？**
   - 改错了容易撤销（git revert、单文件回退）→ 倾向不用
   - 改错了难以回到当前状态（多文件联动、状态难以重建）→ 倾向用

### 硬底线

**任何没有机械验证手段的产物（当前所有 prose 产物属于此类），走 converge。** 理由：无 lint/测试等自动硬约束，独立上下文交叉审查是唯一的验证机制。这不是对 prose 的永久判定——若未来某类 prose 产物获得了机械验证手段，本条自动对该类产物失效。

### 决策表

| 产物类型 | 可机械验证 | 连锁范围 | → 决策 |
|---------|-----------|---------|--------|
| 代码 bug fix | ✅ 有测试 | 单文件 | 直接改 |
| 代码重构 | ✅ 有测试 | 跨模块 | 视回滚成本 |
| 代码架构变更 | ❌ 无自动判对错 | 跨模块 | **converge** |
| plan / 设计文档 | ❌ | — | **converge** |
| SKILL 描述 | ❌ | — | **converge** |
| 配置文件 tweak | ✅ 有 schema/lint | 单文件 | 直接改 |
| prose 类产物 | ❌ | 任意 | **converge** |

### 收敛后设计审查

converge 主循环收敛后，若产物满足以下任一条件，可选触发**设计审查**（`refs/design-review-prompt.md`，单轮咨询式，不给阻断权重）：

- 产物涉及 ≥ 3 个独立模块/组件，或引入新目录结构/命名约定/跨组件接口，或定义了新工作区框架
- 用户显式请求设计审查

产出 `design-review.md`（写入 `.converge/done/<slug>/`），不进入 blocking→repair 管道。

---

## 一、每次 Spawn 前自检

Spawn reviewer 或 executor 前，逐项确认：

- [ ] **prompt 完全自足？** 一个没读过任何历史文件的人，拿到这份 prompt 能否理解任务？
- [ ] **所有 `<placeholder>` 已替换为具体路径？** 检查 `<plan_path>`、`<attempts_md_path>`、`<antipatterns_path>`、`<round_N_reviewer_output_path>`、`<contract_path>` 等
- [ ] **若存在 contract.md**：prompt 中已包含 contract 路径和 Rubrics 维度？
- [ ] **若存在原始背景材料**：prompt 中已注入 `<reference_materials_path>`。发现流程：先检查产物自身的引用（计划文件 top section 的 source/related 字段），其次询问用户"有无原始问题报告或需求文档需要纳入审查"。找不到 → 如实记 `reference_materials: none`，不伪造"不存在"。一旦注入，所有轮次必须一致——不得跨轮更换或增减
- [ ] **未暗示期望结果？**
  - ❌ "请确认 plan 已经可以执行"
  - ✅ "审查此 plan，给出 verdict"
  - ❌ "这里应该只有一些小问题"
  - ✅ 不附加任何评价性前缀
- [ ] **必读文件路径有效？** 确认 `<plan_path>`、`<attempts_md_path>` 等所指文件确实存在
- [ ] **若收敛对象是代码项目**：查阅 `testing-toolbox.md`，确定 `<test_command>` 和 `<lint_command>` 的注入值。优先使用项目声明的入口（Makefile / package.json scripts / CI 配置），其次按技术栈信号查速查表。检测不到测试框架时两个占位符都留空
- [ ] **升级复查（Round ≥ 2）**：读上一轮 attempts.md，提取 verdict ≠ Accepted 的 blocking issues，汇编为 `<escalated_issues>` 块注入 Reviewer prompt（含原 issue id、原 reviewer 描述原文、当前状态）。参见 reviewer-prompt.md§升级复查
- [ ] **instance_id 已记录？** Spawn 返回后立即写入 round-N.md frontmatter 和 `_orchestrator-state.md`

---

## 二、语义判定操作步骤

### Overturn 检测（每轮）

当 reviewer 给出 blocking issue 时，逐条对照 attempts.md 中已 Accepted 的修复：

1. **定位**：attempts.md 中是否已有针对**同一对象**（同一段落 / 同一函数 / 同一决策点）的 Accepted entry？
2. **比较方向**：本轮 issue 的修改方向和 Accepted entry 的修改方向是否**相反**？
   - 一个要加 X，一个要删 X → 方向相反
   - 一个说"应该用方案 A"，一个说"应该用方案 B"且 A ≠ B → 方向相反
3. **确认**：方向确实相反 → 标记 Overturn，累加 Type O 计数
4. **不确定时**：标注 `[Orchestrator Detection · 不确定]`，说明不确定的理由，**不做强行判断**。让下一轮 reviewer 独立裁决。

### Type R 等价检测（每轮）

1. **提取**：本轮每个 blocking issue 的核心诉求（一句话）
2. **匹配**：逐条对比上轮 blocking issue 的核心诉求
3. **等价条件**：诉求本质相同，但措辞不同 → 标记 Type R
   - 例：R1 说"缺少错误处理"，R2 说"异常路径未覆盖" → 可能同源
4. **不确定时**：标注 `[Orchestrator Detection · 不确定]`，不做强行等价。

### Inner Loop 验收（同轮）

Executor 修复后，通过 Continue 让 reviewer 验收。Orchestrator 自己也需要对照：

1. **逐条勾**：对照 reviewer 原话（不是自己记忆中的摘要），逐条检查 executor 的 diff
2. **不凭感觉**：如果 reviewer 原话说"必须重写为独立函数"，而 diff 只是加了个 flag 参数——这就是不够
3. **reviewer 打回时**：不要替 executor 解释。把 reviewer 的意见原样转发给 executor，让它自己判断是误解还是真不足
4. **计数强制执行**：每轮 inner loop Continue 前检查次数。达 3 次后不再 Continue，在该轮 round-N.md 的 Orchestrator 处理记录中标注 `[Inner Loop Exhausted: 3/3]`，直接进入下一 outer loop

### 发散检测（Divergence Detection）

振荡检测 4 型（Type O/R/F/S，见 `SKILL.md` §振荡检测）全部抓「同议题的重复/翻转」——收敛的隐含定义是「修复使问题集单调缩小」，振荡 = 问题集在原地打转。但 converge 还存在另一种失效模式：**发散**——问题集不是重复，而是**持续深化/更换**，且可接受距离不缩。振荡检测对这种「非重复、持续深化」的失效模式存在盲区，本节给出识别判据。

**发散识别 5 判据（联合信号，非任一单触发）**：

以下判据是**联合信号**，不是任一命中即可自动触发的规则。应先排除漏改关联产物、验收未执行等普通执行缺口；单条命中不足以判定发散，也不授权 agent 自行终止目标。

1. **深化趋势**：每轮阻断指向更深抽象层（表层 → 设计 → 基础原则），而非同层数量减少。
2. **净新增 > 净消解**：修 round N 的阻断竟使 round N+1 冒出「此前不可讨论的」新议题。
3. **过程复杂度反超产物**：验证 apparatus 比被验证特性更复杂（Occam 比例信号）。
4. **可接受距离不缩**：修后再评，「距通过」不缩、横移或扩大。
5. **元重设消解而非解答**：第一性问题（「这值得收敛吗？」）使原 loop 失去意义——合理处置可能是放弃目标、缩小范围或重设问题，而不是继续堆叠当轮修补。

**处置原则**：判据 5 尤其关键——发散可能意味着「在收敛一个错误的问题」，出路是先质疑问题。此时应**层升至用户用第一性原则决定放弃、缩范围或重设目标**，而非由 agent 自动终止或继续无条件消耗预算/轮次。

**示例（self-contained）**：若某收敛呈现「修 round-N 阻断竟引发 round-N+1 此前不可讨论的新议题」模式（rigor-escalation），且验证 apparatus 复杂度反超被验证特性、可接受距离横移不缩，宪法第一部仲裁倾向于判其为「收敛一个错误的问题」并放弃（完整判例见 `GOVERNANCE-DECISIONS.md` GD-2，可选扩展阅读，非必要依赖）。

**晋升门槛（Bitter Lesson 自律）**：本判据为 N=1 观察提炼，**不**据此硬编码新检测机制（如往振荡表加 `Type D (Divergence)` 并赋予硬停语义）——那正是 Bitter Lesson 反对的行为。当前作为操作指导供 Orchestrator 人工识别 + 层升至用户；若跨多个收敛复现 ≥3 次，再走 ultraverge 议 Type D 晋升，届时凭数据不凭单点。

---

## 三、自身偏见意识

两条硬纪律：

1. **先读本轮 reviewer 原文，再对比历史。** 如果先读 attempts.md 再看本轮 reviewer 输出，会带着"找印证"的预期去读——锚定效应。正确的读序：本轮 reviewer 全文 → attempts.md → 做对比。

2. **Inner loop 验收时逐条勾 reviewer 原话，不凭感觉。** 你亲自 spawn 了 executor 修了某个 issue，会自然偏向"修好了"。用 checklist 对抗确认偏误。

---

## 四、边界场景处置

| 场景 | 处置 |
|------|------|
| Reviewer verdict = `可执行` 但有 3 条 suggestion 看起来像阻断 | **不要自行升级为阻断**。suggestion 和 blocking 的边界是 reviewer 的权力。若确有疑虑 → Spawn 第二个 reviewer 交叉验证 |
| R1 reviewer 说 attribution=plan_defect，R2 reviewer 说同一问题的 attribution=executor_limit | 标 Type S 振荡（归因翻转），记录但不硬停。让 R3 reviewer 独立裁决归因 |
| 用户说"够了"但还有 2 个阻断未修 | 这是终止-c 主观接受。标注、写 retrospective、**不标"收敛"**——标"主观接受" |
| Reviewer 的 YAML 输出格式错误（缺 attribution / verdict 拼写错 / YAML 解析失败） | **Orchestrator 不自行推断**。通过 Continue 要求 reviewer 修正格式。Reviewer 原意只有 reviewer 自己能还原 |
| Reviewer 和 Executor 的结论矛盾，无法判断谁对 | 不要选边。记录矛盾、Spawn 第三个 agent 作为仲裁（给出双方论据，让它独立判断）。**仲裁只限一次**：若仲裁 agent 的结论仍无法打破矛盾，在 retrospective 中记录为未解决争议，不继续消耗预算 |
| Type O 触发但直觉觉得不是真正的振荡 | 规则优先：触 ≥3 次就硬停。可以在 retrospective 中分析"这次硬停是否合理"，作为后续调参依据 |
| Executor 的 diff 涉及 reviewer 未提到的文件 | 问 executor 为什么改这里。如果是合理的 scope 上溯（见 executor-prompt.md 纪律 #4）→ 接受。如果是 scope creep → 回退 |
| Reviewer 标 `contract_amendment_required: true` | 先回写 contract.md（追加/修订断言），再审查 attempts.md 中哪些 Accepted entry 的验收依据因此失效，追加 `**[Contract Amendment]**` annotation。contract 演进导致的矛盾不计入 Type O |
| Contract 修订后，已 Accepted 的修复方向与新 contract 矛盾 | 标注 `[Not Type O: contract amendment]`。不累加 Type O 计数。让 executor 按新 contract 返工，新 attempt 按正常格式记录 |
| Round 0 中 Executor 提议的合同断言过于笼统 | 不要替 Executor 细化——交给 Reviewer 挑战。Orchestrator 只做传递，不做内容加工 |
| Reviewer 所有 Rubrics 维度 ≥ 4 但 verdict ≠ 可执行 | Reviewer 必须在 blocking_issues 中标 `rubric_gap: true`。若未标 → Continue 要求 Reviewer 解释 |

---

## 五、Spawn 失败时的降级

如果 Spawn 完全不可用，按 refs/framework-adapters.md §A.4 降级。额外注意：

- 降级模式下 `reviewer_backend: orchestrator_self` 是**必须标注的**，不是可选的
- 降级模式的 retrospective 中必须写 §6 "降级影响评估"
- 降级模式不应默默发生——**告知用户**当前处于降级模式，结论可信度降低

## 六、职责操作指引

### plan_amendment_required 处理（对应职责 #5）

1. Reviewer 标 `plan_amendment_required: true` 时，在 attempts.md 中标注该 issue
2. **先回写 plan**：定位 plan 中需要修订的段落，直接修改 plan 文件
3. **通知 executor**：在 executor prompt 中明确指出 plan 已修订的部分，要求 executor 按新 plan 调整下游
4. **验证**：下轮 reviewer 审查时，确认 plan 修订是否被正确引用

### 漂移检测（对应职责 #6）

1. **频率**：每 5 轮（配置参数 `plan_drift_check_interval`）或触 Type O 时执行
2. **方法**：将当前 plan 与初版 plan 做 diff，识别"新增/删除/改写"的段落
3. **报告用户**：列出漂移点，问用户"这些变更是否符合你的本意？"
4. **严重漂移**：若 plan 已面目全非，建议用户重新审视是否需要重启收敛

### 预算追踪 + gate 编排（对应职责 #7 / M-11）

预算执行由确定性脚本 `scripts/budget_gate.py` 承担，**不靠 Orchestrator 记忆比较计数**。数据契约见 `refs/state-schema.md` §预算 gate。

1. **每次 spawn 前 reserve**：`python scripts/budget_gate.py reserve --active-dir <active> --role <角色> --reservation-id <session>:<tool_use> [--target-round N]`。
   - `PROCEED:<rid>` → 继续 spawn；spawn 后 `settle`（成功 `--result succeeded --instance-id <id>`，**instance_id 必填**；失败 `--result failed`；执行前中止 `--result cancelled --pre-execution`）。
   - reserve/settle 一律由 Orchestrator 手动执行并确保结果落 ledger（两个已落地 tier 都如此；当前无 PostToolUse 自动 settle）。`best-effort guarded` 仅额外提供独立 PreToolUse 总量 cap——hook 不写 ledger、hook counter 与 ledger 不双计、bind/refresh-cap/unbind 只管理总量 backstop；per-scope gate 仍须 Orchestrator 手动执行。
2. **非 PROCEED 处置**（对应 SKILL.md 主循环步骤 4）：
   - `BLOCK:*` → **停止**，向用户呈现菜单：继续迭代 / 接受（终止-c）/ 简化 plan / 终止。续跑须写 `budget_extension` 令牌（见下）。
   - `MODE_SWITCH_REQUIRED` → 呈现：接受进入执行 / 简化 plan 重收敛 / 终止。
   - `DENY:*` → 角色非法/未注册，复查后重试。
   - `FAIL_CLOSED:*` → 状态损坏（含 ledger schema 校验失败、孤儿 reservation、extension 链非法），按 reason 修复后重试，**绝不 fail-open**。
3. **budget_extension 令牌**（超默认预算续跑的唯一合法途径）：在 `_budget-state.json` 的 `extensions` 追加一条，**关联触发它的真实 BLOCK `decision` 事件**（`triggering_block_event_id` + 与该 decision 的 scope/observed_usage/effective_ceiling 逐项一致），含用户原话 `user_quote`；新记录写 `supersedes`，旧记录不可改，`new_ceiling` 单调递增且 `prior_ceiling` 接上链。校验不过 → gate FAIL_CLOSED。**不得用记忆中的旧授权续费**（呼应宪法第二部授权粒度澄清）。
4. **孤儿 reservation**：收口前必须全部 settle 或显式作废；consuming 孤儿占自己一格不全局阻断，但收口必检与 pre-push 会拦未结孤儿。
5. **ingest-verdict**：reviewer 输出落盘后，`budget_gate.py ingest-verdict --target-round N --verdict <可执行|阻断需修复|需重新设计> [--severities ...] [--mode ...]`，驱动 mode 记录与边际递减判定。
6. **记录**：retrospective 中分析预算消耗（ledger 事件数 / 是否触发 extension / 总量水位）是否合理；rule_frequency 的 `budget_gate` 由 ledger `decision` 事件触发。

### Rubrics 维度选择（对应职责 #12）

1. **默认规则**：按 rubrics.md 选用规则表（Plan=3维度/代码=4维度/UI=5维度）
2. **写入 contract**：选定的维度写入 contract.md 的 rubric_dimensions 字段
3. **跳过合同谈判时**：在 _orchestrator-state.md 中记录选定的维度，在 reviewer prompt 中注入
4. **Fallback**：若收敛对象不明确属于三类（如混合型文档+代码），取并集（如 Plan+代码 = Correctness+Completeness+Consistency+Maintainability）
5. **扩展条件**：若 reviewer 连续 2 轮标 `rubric_gap: true`，说明维度库不够，向用户建议扩展维度并在 contract 中追加

### 收敛后修订处理（对应职责 #14）

当收敛完成后用户提供外部输入时：

1. **判断实质性**：输入是否引入新维度、动摇核心判断、或修正遗漏事实？措辞微调不触发。
2. **重新激活**：运行 `python scripts/archive_convergence.py reopen .converge/active .converge/done <slug>`，在 `_orchestrator-state.md` 中记录修订触发；禁止手工移动。
3. **修订执行**：Executor 根据外部输入修改产物，attempts.md 追加 entry 并标注 `source: user_external_input`。
4. **独立审查**：Spawn fresh Reviewer 审查修订后的**完整产物**（不只看新增部分）。Reviewr prompt 中应包含：产物全文 + 之前的 round log + 用户的原始外部输入。
5. **归档**：通过后更新 retrospective（追加 §11 收敛后修订记录），运行唯一 `archive` 命令重新归档；禁止手工移动。

**关键原则**：用户外部输入的价值在于提供 Executor 和 Reviewer 都缺少的外部视角。不要试图将用户的输入"翻译"成 Reviewer 能理解的格式——将用户的原始输入直接传入 Reviewer prompt，让 Reviewer 独立判断。

### 盲审复核编排（对应职责 #20）

当收敛经历 ≥2 轮 outer loop 且 verdict=可执行时，在 retrospective 写入前执行盲审复核。

**Spawn 前自检**（在标准自检基础上追加）：

- [ ] 确认收敛轮次 ≥2（检查 _orchestrator-state.md 的 current_round）
- [ ] 确认当前在 `active/` 内（盲审不触发 done/→active/ 回流）
- [ ] 盲审 Reviewer prompt 使用 `refs/reviewer-prompt.md §盲审复核变体`——Required reading 中不含 attempts.md
- [ ] 传入 amended contract.md + reference_materials（若存在）
- [ ] 检查 max_blind_rechecks 预算

**盲审结果处置**：

1. **零阻断**：盲审通过
   - retrospective 记 `blind_recheck: {status: pass, traces_reported: N, rounds_used: 1, findings_count: 0, escalated_to_main_loop: false}`
   - 继续执行收敛完成前必检，移 done/

2. **有阻断**：盲审失败
   - 在 attempts.md 为每个 finding 创建 entry（source: blind_recheck, Issue 归因: pending）
   - 将 findings 以 BR- 前缀独立注入块格式转为 escalated_issues：
     ```yaml
     - id: BR-{finding_id}
       source: blind_recheck
       description: |
         <finding description 原文>
       severity: <finding severity>
       attribution: pending
       plan_amendment_required: <finding 的 plan_amendment_required>
     ```
   - 注入下一主循环 Reviewer 的 escalated_issues
   - 回到主循环：Executor 修复 → Spawn fresh Reviewer（非 inner loop Continue）→ 再次可执行 → 再次盲审
   - 累计盲审次数达 max_blind_rechecks → 预算软停，问用户

3. **终止-c（主观接受）+ 盲审失败**：提示用户盲审发现，用户可确认跳过
   - retrospective 记 `blind_recheck: {status: waived, ...}`
   - waived 不计入 rule_frequency 命中率

**pending 归因过期检查**：

- 在下一主循环轮的 Reviewer 输出中，检查所有 BR- 前缀 escalated_issues 是否已落定归因（plan_defect / executor_limit）
- 未落定的 pending → 违反硬过期规则，在该轮 round-N.md 以 `[Orchestrator Detection]` 标注

### parking-discipline（停放纪律）

当 plan 或处置方案倾向"把某问题 park 起来、等未来触发器再处置"时，按以下二元判据区分"正当推迟"与"规避决策的借口"：

> **parking 可接受 ⟺ 同时满足：**
> - **(a) 迁移触发器可验证且可触发**：存在可观测事件（非计数自身的循环），且该事件在当前架构下**可达**（不会被结构性屏蔽）。
> - **(b) parking 期间核心功能仍可运作**：被 park 的 artifact 所支撑的核心功能不依赖迁移完成后才生效。
>
> **任一否 → 必须立即处置（不允许 park）。**

**典型反例**（parking 不合格）：触发器是"N≥3 复现"，但 N 的计数依赖判据可达——判据 park 在 agent 看不到的地方 → N 永远=1，触发器结构性自我取消；或触发器是"与 X 联动"形成循环依赖。**原则一致性**：Bitter Lesson 反对硬编码模型补丁，**不**反对搭最小结构 / 加导航 pointer；原则施加方向不应随结论便利翻转——不得以 Bitter Lesson / Occam 正当化 inaction。

**适用场景（自举评议的反自利纪律）**：converge 评议 converge 自身时，评议者与被审查对象共享同一套设计 DNA——存在结构性便利"少动我自己"。parking-discipline 作为反自利纪律：欲推迟某项修复，必须通过上述双条件。

**自评循环对冲 + 机械接驳点**：parking-discipline 是 plan 可能自创/引用的规则。当本规则被用于判定自身的 parking 决定时，合格判定**必须由独立 Reviewer 显式复核确认**，不采信 plan 自评——Reviewer 须在 round 输出中针对 plan 的每个 parking 自评显式标记 `parking-claim: verified` 或 `parking-claim: rejected`，并给出依据。**未标记 = plan 不进下一轮**。以弱化"自创规则又自评"的循环。

---

## 七、门控启动决策

> 门控协议详见 `refs/quality-gate.md`。本节定义编排器在何时启动哪种门控。

### 适用范围判断

- **converge 被嵌入 Dynamic Workflows pipeline**：L1 + L2 均可启用
- **独立单层 converge**：L1 不适用（无 Worker 或阶段可度量），L2 可手动触发——当用户显式请求时

### L1 触发（强制，不跳过）

L1 信号检测由非 LLM 脚本执行，编排器通过 shell 调用。触发条件：每 `gate_l1_interval` 个 phase（默认 1，即每个 phase 收口后运行一次）。

编排器操作：
1. 收集 DW 传入的指标 JSON
2. `python scripts/l1_gate.py < metrics.json` → 读 stdout 取 `pass` / `warn`
3. 若 `warn` + `gate_l2_mode = signal` → 自动触发 L2

### L2 触发（按需）

| gate_l2_mode | 触发条件 |
|---|---|
| `signal`（推荐默认） | L1 返回 `warn` 时自动触发 |
| `always` | 每次 phase 切换，不依赖 L1 |
| `adaptive` | **pilot 存根，当前未启用**：收口模型自评风险分 ≥ 阈值时才触发 |

### L2 执行

1. Spawn Reviewer（自足 prompt，含当前 phase 产物 + 收口综合判断）
2. Reviewer 输出 `gate_findings`（非 `blocking_issues`）
3. 编排器读 findings，按 severity 决策：

| severity | 编排器处置 |
|---|---|
| `info` | 记录到 `_orchestrator-state.md`，不阻断，后续 phase 可视情况注意 |
| `risk` | 记录 + 向用户报警 + 视情况调减后续 phase 预算 |
| `critical_gap` | 记录 + 触发完整 converge 审查（标准 Round 0-1+ 流程） |

编排器始终保留最终决策权——**必须**在 state 中记录每条 finding 的决策理由。

### 降级规则

以下预算公式**仅在 converge 嵌入 Dynamic Workflows pipeline 时有效**。独立单层 converge 模式下 L2 仅手动触发，不执行预算检查。

- 门控预算池 = 总预算 × `gate_max_token_share`（默认 15%）
- 每次 L2 前检查：若 `budget.remaining() < 门控预算池 × 30%` → L2 降级为 L1（仅跑信号，不 spawn Reviewer）
- 门控消耗不计入 `max_outer_loops`

---

## 八、落地执行编排

当方案已收敛（retrospective 已写入 done/），用户要求将改动清单写入目标文件时：

### 流程

```
用户要求落地 → 读取方案中的"文件改动清单"表 → Spawn executor（Plan-Execution 模板）
→ 等待 executor 完成 → 记录 instance_id → 核对清单项数 vs 实改文件数 → 报告用户
```

### 自主推进判据（普通 converge）

普通 converge 默认**自主推进落地**，无中途请示——但仅当原始指令含执行意图时：

- **执行意图机械明线**：原始指令含执行动词（如「并执行 / 落地 / apply」等）→ 收敛后**自主**spawn executor 落地，**不**追加"现在要执行吗"check-in。
- **指令不含执行意图** → 落地前**仍需用户确认**（不得以「autonomous」为由跳过）。
- 此判据与 GD-1 一致（GD-1 已授权"走 converge 并执行"推进至默认预算 + 落地），不扩大授权范围。

**自主仅限落地推进——以下宪法强制确认点逐字保留，永不因自主而跳过**：终止-b / 终止-c（渐近 / 主观接受）、预算软停 / `budget_exhausted` / `blind_exhausted` / `ultraverge_exhausted`、`MODE_SWITCH_REQUIRED`、`FAIL_CLOSED` / `DENY:illegal_role`、`需重新设计` verdict。

### 硬约束

- **必须 spawn executor，不得直接编辑** — 宪法硬约束 #7 在落地阶段同样适用。Orchestrator 不兼任 executor
- executor 使用 `refs/executor-prompt.md` Plan-Execution 模式（fresh-context spawn，仅读方案文件）

### instance_id 留痕

Spawn executor 后，将 executor 的 `instance_id` 记录到 retrospective.md 的落地执行条目中。**这是客观证据（executor 是否被 spawn 是有/无 instance_id 的二元事实），非 self-report。**

### 清单项数核对

executor 完成后报告已修改文件列表，Orchestrator 交叉核对：

1. 统计改动清单中的项数（N）
2. 统计 executor 报告的已修改文件数（M）
3. N ≠ M → 向用户报告不一致，列出差异项
4. N = M → 确认，报告用户落地完成

### 传话编排（relay orchestration）

C-21 后收敛执行编排的变体，适用条件见 SKILL.md Orchestrator 责任清单。以下为操作指引：

#### 1. 包裹格式

固定模板，零判断零筛选：

```
[转发自 {sender_role}] — 轮次 {round_id}
产物路径: {artifact_path}
内容 hash: {content_hash}
---
{payload}
---
[转发至 {receiver_role}]
```

#### 2. 记录字段

每次转发记录以下字段：

- `timestamp`：ISO 时间戳
- `sender_role`：发送方角色（reviewer / executor）
- `round_id`：轮次标识
- `artifact_path`：产物文件路径
- `content_hash`：产物内容哈希
- `verdict_or_response`：接收方结论摘要

#### 3. 介入判据

「明显偏差」的判据：接收方产出与 plan 原文的要求存在**可机械核验的差异**（文件路径错误、遗漏清单项、未执行指定命令、输出格式不符等）。判据来源为 plan 原文 + orchestrator 纪律（CONSTITUTION.md 第二部 #7 + SKILL.md 核心角色表）。

不构成介入的情形：语义层判断分歧、偏好差异、命名风格选择——这些不属于「偏差」，不触发介入。

#### 4. 介入前自检

与主循环 M-3 `boundary_check` 同构：**「我即将做的动作是纠偏还是越界？」**

- **纠偏**（允许）：指出偏差，引用 plan 原文，要求对方修正。不触及产物文件。
- **越界**（禁止）：直接编辑产物、替对方完成工作、绕过 spawn executor 修改文件。

自检违反时记录：
- 在 relay ledger（若已创建）中标注 `boundary_violation_pending`
- 若已越界执行 → 标注 `source: orchestrator_self`，告知用户降级影响（参照 C-21(b) 与宪法 #7）

---

## 九、信息源核对与申诉仲裁

当 Orchestrator 在步骤 c 逐条过 reviewer blocking 时，对每条执行信息源核对。**本机制不新增循环节点——嵌入现有步骤 c，与 overturn 检测/等价标注并列但操作对象不同：overturn 对照 attempts.md（内部记录），信息源核对对照原始材料（系统外部——用户原话 / reference_materials / contract.md）。**

### 核对规则

对每条 blocking issue，检查：

> 这个 blocking 的事实前提是否与原始材料矛盾？

**"原始材料"的精确范围**：本轮 Reviewer 收到的 reference_materials（路径记录在 round-N.md frontmatter）、contract.md（若存在）、以及本次收敛的原始触发背景（用户原话/需求文档——从 Orchestrator 上下文直接获取，不依赖文件）。

核对只覆盖**可机械核验的事实矛盾**——"Reviewer 声称 X 但原文说 Y"——不覆盖语义层的"我觉得推理不对"或笼统的"我不服"。

### 发现矛盾时的处置：自裁 vs 用户仲裁

发现 blocking 的事实前提与原始材料矛盾后，**按"可机械核验性"分流**——能机械判定的 agent 自裁，不必打扰用户；需要价值/模糊判断的才上交用户。

```
Orchestrator 发现 blocking #N 的事实前提与原始材料矛盾
  → 判定该矛盾是否"可机械核验"（对照原始材料原文即可判定，无需价值/模糊判断）：
      ├ 可机械核验（例：reviewer 称"用户没说 X"，但用户原话白纸黑字说了 X）
      │     → agent 自裁：该 blocking 从本轮清单剔除
      │       attempts.md 记 source: factual_self_adjudication，状态 rejected: factual_error
      │       retrospective 记自裁理由（矛盾点引用）
      │       不上交用户，继续其余 blocking 的修复流程
      └ 不可机械核验（需价值/模糊判断才能定）
            → 暂停收敛，向用户申诉：
                【同意的 blocking】#A, #B, … — 接受 reviewer 判定
                【异议的 blocking】#N — 矛盾点：[引用原始材料原文] vs [引用 reviewer 原文]
                申请仲裁：用户裁定 blocking #N 是否成立
            → 用户裁定：
                ├ 驳回申诉（blocking 成立）→ Orchestrator 接受，继续流程，不得就同一 blocking 二次申诉
                └ 支持申诉（blocking 不成立）→ 该 blocking 剔除，继续其余 blocking 的修复流程
```

**分流判据**："可机械核验"= 存在一段原始材料原文，直接对照即可判定 blocking 的事实前提真假（例：用户原话「基于知识库内容」vs reviewer 称「用户没说触发词」）。若判定本身需要权衡、解释或价值判断（如"这个推理是否合理"），不算可机械核验，走用户层。

### 申诉记录

仲裁结果写入 retrospective。以下为仲裁记录格式模板（权威源——本地适配层如 `convergence-logs/README.md` 可基于此延伸，但本模板为格式定义源）：

```markdown
## arbitration

### 申诉 {N}
- **轮次**：R{X}
- **异议 blocking**：#{Y}
- **矛盾点**：<引用原始材料原文> vs <引用 reviewer 原文>
- **用户裁决**：<成立 | 不成立>
- **裁决后处置**：<剔除 blocking | 接受 reviewer 判定，继续修复>
- **裁决时间**：<ISO datetime>
```

若同一收敛过程中有多次申诉，追加多条 `### 申诉 {N}`。被驳回的 blocking 在 attempts.md 以 `source: user_arbitration` 记录，状态填 `rejected: factual_error`。

### 局限

本机制不能保证 Orchestrator 主动发现 Reviewer 的信息源不忠实——Orchestrator 与 Reviewer 同模型同架构，共享盲区概率不低。其价值在于：(a) 给异议一个合法出口（从无出口的软约束升级为有机制位置的软约束）；(b) 用户介入时有机制背书的位置表达。仲裁阈值（必须指出具体矛盾、可机械核验）防的是启动后变成笼统不服——出口存在 + 出口有闸。
