---
type: retrospective
object_slug: 20260611-audit-driven-corrections
generated_at: 2026-06-11T17:58:22Z
---

# Retrospective · 20260611-audit-driven-corrections

## 1. 结束模式

终止-a 严格首轮通过（ultraverge 并行评议，3 Reviewer 中 2:1 verdict = 可执行）

## 2. 阻断轨迹

Ultraverge 单轮评议，无多轮收敛。R1=可执行(0), R2=阻断需修复(2), R3=可执行(0)。

R2 的两个阻断均为 implementation/structural 级别（A5 验收 grep 假阳性、A6 第三处修改遗漏），无 conceptual/architectural 阻断，按并行裁决规则多数方向推进。两个事实性发现作为 plan amendment 在执行时一并修复。

## 3. Antipattern 巡查

| Round | 类型 | 对象 | 触发结果 |
|-------|------|------|---------|

本收敛未触发任何已知 antipattern。计划本身的修复合同命中了 SKILL 自定义的多个反模式（archaeology_leftover、naming_drift、data_tool_coupling），但这是审计发现而非收敛过程中的 executor/reviewer 行为。

## 4. Executor 路径依赖评估

不适用——ultraverge 单轮评议直接通过，未进入 Executor 修复循环。

## 5. Reviewer 间 Verdict 分歧分布

| 轮次 | Reviewer | Verdict | 阻断数 | 归因分布 |
|------|----------|---------|--------|---------|
| R1 | R1 (全量审查 + DR7维) | 可执行 | 0 | 4 建议 |
| R2 | R2 (事实核查 + 锚点验证) | 阻断需修复 | 2 | plan_defect×2 (implementation, structural) |
| R3 | R3 (Bitter Lesson + Occam + 宪法合规) | 可执行 | 0 | 5 建议 |

分歧分析：R2 作为事实核查专家发现了两个验收精度问题（A5 grep 范围过宽、A6 仅列两处而非三处），均为修复合同的执行精度问题，非设计方向分歧。三 Reviewer 对计划的整体设计方向（A/B/C 分组、裁决项裁断、修复策略）无分歧。

R2 独有价值：A5 验收 grep 假阳性（SKILL.md:298）、A6 第三处遗漏（reviewer-prompt.md:156）。R3 独有价值："需裁决"系统性过度审慎、A4 不存在合法跳过路径论证。

### 并行裁决规则实际运行

```
R1=可执行  R2=阻断需修复(implementation/structural)  R3=可执行
                                    ↓
                    多数方向 = 可执行 (2:1)
                                    ↓
              检查少数派 severity = 全部 implementation/structural
              (无 conceptual/architectural → 不升级完整收敛)
                                    ↓
              R2 事实性发现 → plan amendment → 执行时一并修复
```

规则对"方向分歧"和"执行精度分歧"的区分有效——R2 的阻断是"你说删第144行，但验收命令会误判第298行"，是精度问题不是方向问题。

## 6. 降级影响评估

无降级。3 个 Reviewer 全部成功 Spawn。

## 7. 经验教训

### 做得好的

1. **跨模型审计验证**：Claude 审计 → GLM 验证，两个独立模型对 15 项达成一致（零假阳性）。验证方法：读原始文件 → grep 定位锚点 → 与审计声称对比 → 实跑 distill dry-run。这让后续 ultraverge 聚焦于修复合同精度而非事实核实
2. **并行裁决的少数派保护机制**：R2 的 implementation 级阻断未升级完整收敛（正确），但其事实性发现仍被采纳为 plan amendment——并行裁决不是"赢者通吃"
3. **R3 的 Bitter Lesson 视角**：对"需裁决"的系统性过度审慎提出了有说服力的批评——4/5 裁决项有 Occam 明确最优解。这是 DR 层面的洞察，不是单条修复意见
4. **A/B/C 三组分组有效**：治理域 (ultraverge) / 非保护域 (标准评议) / 运维决策 的三层修改程序在执行中零越界，验证了 CONSTITUTION 第三部分组策略的可操作性

### 自举特性

本次收敛的对象是 converge SKILL 自身（医者自医）：

- **反模式实证有效性**：15 项审计发现中，多数命中了 SKILL 自定义的反模式（naming_drift、archaeology_leftover、data_tool_coupling）——审计者用 converge 教 Reviewer 抓的反模式来抓 converge 自己，且全部命中
- **三层分离通过压力测试**：A/B/C 三组的修改程序不同，执行时零越界
- **宪法修改程序实际运行**：A 组走 ultraverge（≥3 Reviewer + 收敛 + 设计审查），B 组走标准评议——第四部规定的分层修改程序被完整执行
- **局限**：未进入 Executor 修复循环，运行时机制（降档、inner loop、overturn）未受考验；Orchestrator 在修改 SKILL.md 的同时遵循 SKILL.md——存在自指风险，缓解措施是用户触发 ultraverge（打破闭环）+ 3 个独立 Reviewer 全新上下文

### 可改进的

1. **裁决项应设准入门槛**：当前"需裁决"标记由计划作者自行标注，缺乏客观标准。建议：只有存在≥2 个可行方向且有真实 trade-off 的决策才标记为裁决项；Occam 有明确答案的项直接纳入修复合同并标注理由
2. **验收命令应在计划阶段做假阳性分析**：A5 的 `grep '.meta/' 零命中` 在 R2 事实核查时才暴露假阳性。建议：计划中每条验收命令都应先跑一遍当前代码库，确认基线状态
3. **设计审查 H2 (枚举奇偶性) 应优先级更高**：A2 修复的正是枚举漂移问题，但修复方式是注释。在 distill 脚本中加入 ~10 行奇偶校验的成本极低，应在下个维护周期内完成
4. **README_en.md 双维护风险未解决**：B2 重译了英文版并加了"以中文版为准"声明，但终止状态表仍需三处同步。未引入单源化机制

## 8. 后续建议

1. **Antipattern 枚举奇偶性自动化**：在 distill_antipatterns.py dry-run 模式中加入枚举奇偶校验，~10 行代码
2. **A6 语义审查行措辞一致性**：建议后续审查确认所有 deterministic_check 相关措辞统一指向 YAML 顶层字段
3. **裁决项准入门槛**：后续计划模板中增加"裁决项准入检查"——Occam 有明确答案的项不标记为裁决项

## 9. Round 0 合同谈判评估

| 维度 | 评估 |
|------|------|
| 是否启用 | 否（跳过理由：计划含明确逐字修复合同，无需谈判验收标准） |
| contract 是否减少预期错位 | 不适用 |
| contract_amendment 触发次数 | 0 次 |
| contract 与 plan 的同步性 | 不适用 |

## 10. Rubrics 评估

| 维度 | 评估 |
|------|------|
| 使用的维度 | Correctness, Consistency, Completeness（无 formal contract，注入于 state 文件） |
| 未使用/总高分的维度 | — |
| rubric_gap 触发次数 | 0 次 |
| 跨轮分数趋势 | 不适用（单轮） |

## 11. 成本数据

| 阶段 | tokens | 时间 | agent 数 | 关键产出 |
|------|--------|------|----------|---------|
| 审计验证（15项逐项核对） | ~120K | ~8 min | 1 | 全部15项属实的核实报告 |
| Ultraverge R1 (3× 并行 Reviewer) | ~310K | ~18 min | 3 | 2 可执行 + 1 阻断需修复(2项) + 共9建议 |
| Orchestrator 裁决 + 裁断 | ~5K | ~2 min | — | 5裁决项裁断 + 2 plan amendment |
| A 组执行 (7项治理域修改) | ~15K | ~5 min | — | 6 文件修改 |
| B 组执行 (7项非保护域修改) | ~10K | ~4 min | — | 6 文件修改 |
| C1 distill --write | ~2K | ~1 min | — | 注册表统计回写 |
| C2 .gitignore 策略 | ~1K | ~1 min | — | .gitignore 改为 done/ 入库 |
| 验收 grep 全量核对 | ~3K | ~2 min | — | 6 项 grep 零命中确认 |
| 设计审查 (强制触发) | ~95K | ~5 min | 1 | 3 advisory findings (H1-H3) |
| H1 立即修复 + 归档 | ~7K | ~3 min | — | 流程图修复 + retrospective |
| **总计** | **~568K** | **~49 min** | **4** | — |

```
Ultraverge R1 (3×并行)  ████████████████░░░░░░░░  37%
审计验证                  ████████░░░░░░░░░░░░░░░░  16%
设计审查+修复+归档         ██████████░░░░░░░░░░░░░░  20%
A+B组执行                 ████████░░░░░░░░░░░░░░░░  16%
其他 (裁决+C1+C2+验收)     ████░░░░░░░░░░░░░░░░░░░░  11%
```

## 设计审查 Highlights

| # | 发现 | 影响 | 处置 |
|---|------|------|------|
| H1 | Positioning 流程图未反映需重新设计回路 | Fresh Reviewer 心智模型不完整 | ✅ 已修复 |
| H2 | Antipattern 枚举奇偶性无自动化校验 | "三处统一"硬约束仅靠注释维护 | 📝 建议在 distill 脚本中加入 |
| H3 | C2 悬置导致"可完全重建"声明不可靠 | antipatterns.md 声明与 .gitignore 矛盾 | ✅ 用户已裁决：done/ 入库 |

## 裁决结果

| 项 | 裁决 | 理由 | 是否真正需要裁决 |
|---|---|---|---|
| A1 第四条 | 允许缩小范围后重新评议 | R1/R3 共识：产物可能有局部可执行中间态 | **是** |
| A2 防漂移条款 | 直接纳入修复合同 | 纯维护注释，无需裁决 | **否** |
| A4 | 方案一（机制层向宪法对齐） | R1/R3 共识：宪法 #2 措辞明确 | **否** |
| A5 | 删除 | R3 裁定 Occam 指向删除 | **边缘** |
| A7 | 重命名（终止-a/b/c） | 备选方案违反 archaeology_leftover | **否** |

## Plan Amendment

R2 的两个事实性发现作为 plan amendment 在执行时一并修复：

1. **A5 验收收窄**：grep .meta/ → grep .meta/deliberations（排除 SKILL.md:298 合法配置示例）
2. **A6 第三处明确修改**：reviewer-prompt.md:156 "在 blocking issue 中标注" → "在输出中标注"
3. **A7 README.md 纳入 A 组**：避免跨组原子提交间的 D11/终止命名间隙
4. **Positioning 流程图更新**：设计审查发现后立即修复

## 模式建议

- **治理文档修改 → Ultraverge**（宪法级约束，≥3 Reviewer + 设计审查）
- **自举修正 → 跨模型审计 + Ultraverge**（避免单模型盲区）
- **修复合同精度 → 事实核查专家 Reviewer**（R2 角色：锚点验证 + 验收命令假阳性分析）
- **"需裁决"标记 → 设准入门槛**（Occam 有明确答案的项直接纳入，仅保留有真实 trade-off 的决策）
