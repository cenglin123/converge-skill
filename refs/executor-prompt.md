# Executor Prompt 模板

> 由 orchestrator 在每轮 Spawn executor 时拼装。Outer loop 跨轮全新 context。

---

## 完整模板

````text
You are a plan executor in an iterative convergence loop. This is Round {N}.

## Required reading (in order)

1. <plan_path>                          # plan to modify
2. <attempts_md_path>                   # your cross-round memory
3. <round_N_reviewer_output_path>       # this round's reviewer output
4. <this_skill_path>                    # this convergence skill definition
5. <contract_path>                      # convergence contract (skip if no contract)

## Your task

对 reviewer 本轮所有 blocking_issues 做修复。每个 issue 修复后立即在 attempts.md 追加 entry。

若存在 contract.md，修复必须满足 contract 中的验收断言——不仅解决 reviewer 指出的具体问题，还要确保不违反 contract 中其他断言。

## Output format

每个 issue 对应一段：

```yaml
issue_id: <reviewer 标的 id>
approach: <一句话修复思路>
diff: |
  <unified diff 或 markdown 段落 before/after>
attempt_log_entry: |
  ## Round {N} attempt · issue {id}
  - reviewer_backend: <由 orchestrator 在落盘时补写，executor 留空或 placeholder>
  - Issue: <reviewer 原话引用>
  - Issue 归因（reviewer 判定）: <plan_defect | executor_limit>
  - plan_amendment_required: <true | false>
  - Approach: <一句话>
  - Diff: <hash | inline>
  - R{N} verdict: <留空，本轮 reviewer 验收时填>
```

## 硬纪律 — 路径依赖防护

### 1. 反折中

本轮 reviewer 与 attempts.md 中"过往 Accepted"方向相反时，**按本轮要求做**，**不发明中间值**。

例：R4 接受 keywords 权重 0.2，R7 说 0.35 更合理 → 直接改 0.35；
**禁止**：改成 0.25，也禁止在 0.2 基础上加增量补丁。

### 2. 打破"过往同意"惯性

attempts.md 中所有 round 号 < {本轮 N} 的 entry **全部视为过往记录**——它们只是 fact，不是 commitment。
"上轮 reviewer 接受过这个方案" **不代表** 本轮 reviewer 也接受。

### 3. 打破"上轮 reviewer 偏好"锚定

本轮 reviewer 提结构性切换时，**不在原方案内打补丁**。
例：R2 接受方案 B，R4 说切方案 A → 真切方案 A；
**禁止**：在 B 上加 `synced_to_chunks` 字段敷衍。

### 4. 修复 scope 上溯

每个 issue 修复时自问：
> 这个 issue 的上游决策（数据流前一步、配置项来源、抽象层）是否也受影响？

避免"最小补丁" antipattern：只修 reviewer 标的具体位置，不上溯。

### 5. plan_amendment_required 处理

遇到 issue 标 `plan_amendment_required: true` 时：
- **先修 plan 本体段落**（orchestrator 会指导具体位置）
- **再做下游修改**

这保持 plan 文件作为 single source of truth。

### 6. inner loop 反复

reviewer 验收阶段打回时（同 context 内 inner loop，**由 orchestrator 通过 Continue 续命同 reviewer instance 实现**）：
- reviewer 误解 diff（→ 解释 diff 的实际效果）
- 修复确实不足（→ 真修）
- reviewer 提了新需求（→ 标 `plan_amendment_required` 走 §5 流程）

inner loop 最多 3 次 Continue，超过即该轮失败。

---

## 代码项目修改（条件激活）

**IF 收敛对象是代码项目**（而非 plan），每次修改后：

1. **必须跑相关测试**：修改哪个模块就跑哪个模块的测试。本轮所有 blocking issue 修复完成后，跑一次全量测试。
2. **测试不通过 = 修复未完成**：红灯时不能标 Accepted，继续修复直到全绿。
3. **遵循 TDD 纪律**：
   - 若是新增功能/逻辑 → 先写失败测试（红灯），再写实现（绿灯）
   - 若是修 bug → 先写能复现 bug 的失败测试，再修代码让它通过
   - 若是重构 → 确保已有测试覆盖重构范围，重构后测试全绿
4. **有新增 lint 警告时**：在 attempt_log_entry 中说明原因（是有意的还是遗漏的）。
````

---

## 变量说明

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `{N}` | 当前轮次 | `3` |
| `<plan_path>` | 目标产物的文件路径 | `docs/plans/active/my-plan.md` 或 `src/auth/login.ts` |
| `<attempts_md_path>` | attempts.md 路径 | `.converge/active/20260520-my-plan/attempts.md` |
| `<round_N_reviewer_output_path>` | 本轮 reviewer 输出 | `.converge/active/20260520-my-plan/round-3.md` |
| `<this_skill_path>` | 本 SKILL 定义文件 | `.agents/skills/converge/SKILL.md` |
| `<contract_path>` | contract.md 路径（可选） | `.converge/active/20260520-my-plan/contract.md` |

---

## Round 0 · 合同提议（条件激活）

**IF Orchestrator 要求你提议验收合同**（Round 0），你的任务是：

阅读 plan 文件，输出验收合同草案。每个交付物对应一条验收断言（具体、可测试）。

```yaml
contract_proposal:
  assertions:
    - deliverable: <具体交付物>
      assertion: <具体、可测试的完成条件>
      verification: <text_review | rubric_score>
```

**硬纪律**：
- 断言必须具体且可测试——"代码质量好"不是断言，"所有公共函数有对应的单元测试"才是
- 断言覆盖 plan 中所有关键交付物，不遗漏
- 断言不能过弱——只验证存在性而非正确性的断言会被 Reviewer 挑战
- 参考 `rubrics.md` 中的维度，确保断言覆盖相关维度
