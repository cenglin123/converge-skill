# Orchestrator 操作指南

> Orchestrator 承担的不只是"别偷懒"——每一条责任都是需要判断力的语义推理。本文件提供操作步骤、偏见意识和边界场景处置。

---

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

如果 Spawn 完全不可用，按 SKILL.md 附录 A.4 降级。额外注意：

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

### 预算追踪（对应职责 #7）

1. **粒度**：以 outer loop 轮次为单位追踪（当前轮 / max_outer_loops）
2. **预警**：达 70% 轮次预算时在 _orchestrator-state.md Compact Recovery Notes 中记录
3. **触顶**：达 max_outer_loops 时不自行收敛，向用户展示阻断趋势，问用户是否续费
4. **记录**：retrospective 中分析预算消耗是否合理

### Rubrics 维度选择（对应职责 #12）

1. **默认规则**：按 rubrics.md 选用规则表（Plan=3维度/代码=4维度/UI=5维度）
2. **写入 contract**：选定的维度写入 contract.md 的 rubric_dimensions 字段
3. **跳过合同谈判时**：在 _orchestrator-state.md 中记录选定的维度，在 reviewer prompt 中注入
4. **Fallback**：若收敛对象不明确属于三类（如混合型文档+代码），取并集（如 Plan+代码 = Correctness+Completeness+Consistency+Maintainability）
5. **扩展条件**：若 reviewer 连续 2 轮标 `rubric_gap: true`，说明维度库不够，向用户建议扩展维度并在 contract 中追加

### 收敛后修订处理（对应职责 #14）

当收敛完成后用户提供外部输入时：

1. **判断实质性**：输入是否引入新维度、动摇核心判断、或修正遗漏事实？措辞微调不触发。
2. **重新激活**：将 `done/<slug>/` 移回 `active/<slug>/`，在 `_orchestrator-state.md` 中记录修订触发。
3. **修订执行**：Executor 根据外部输入修改产物，attempts.md 追加 entry 并标注 `source: user_external_input`。
4. **独立审查**：Spawn fresh Reviewer 审查修订后的**完整产物**（不只看新增部分）。Reviewr prompt 中应包含：产物全文 + 之前的 round log + 用户的原始外部输入。
5. **归档**：通过后更新 retrospective（追加 §11 收敛后修订记录），重新移至 `done/`。

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
