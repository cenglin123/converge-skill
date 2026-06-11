---
type: post-mortem
object_slug: 20260611-audit-driven-corrections
generated_at: 2026-06-11T18:10:00
model: glm-5.1
scope: converge SKILL 自举审计修正全流程复盘（审计验证→ultraverge评议→裁决→执行→设计审查→归档）
---

# Post-Mortem · Converge SKILL 自举审计修正

## 全景数据

| 阶段 | tokens | 时间 | agent 数 | 关键产出 |
|------|--------|------|----------|---------|
| 审计验证（15项逐项核对） | ~120K | ~8 min | 1 | 全部15项属实的核实报告 |
| 计划审阅（用户已提供） | 0 | 0 | — | 计划已就绪，无需修订 |
| Ultraverge R1 (3× 并行 Reviewer) | ~310K | ~18 min | 3 | 2 可执行 + 1 阻断需修复(2项) + 共9建议 |
| Orchestrator 裁决 + 裁断 | ~5K | ~2 min | — | 5裁决项裁断 + 2 plan amendment |
| A 组执行 (7项治理域修改) | ~15K | ~5 min | — | SKILL.md / reviewer-prompt.md / state-schema.md / decomposition-protocol.md / orchestrator-guide.md / README.md |
| B 组执行 (7项非保护域修改) | ~10K | ~4 min | — | antipatterns.md / testing-toolbox.md / quality-gate.md / l1_gate.py / distill_antipatterns.py / README_en.md |
| C1 distill --write | ~2K | ~1 min | — | 注册表统计回写（false_generality count=1） |
| C2 .gitignore 策略 | ~1K | ~1 min | — | .gitignore 改为 done/ 入库 |
| 验收 grep 全量核对 | ~3K | ~2 min | — | 6 项 grep 零命中确认 |
| 设计审查 (强制触发) | ~95K | ~5 min | 1 | 3 advisory findings (H1-H3) |
| H1 立即修复 (Positioning流程图) | ~2K | ~1 min | — | SKILL.md 流程图添加回退箭头 |
| Retrospective + 归档 | ~5K | ~2 min | — | retrospective.md / round-1.md / design-review.md |
| **总计** | **~568K** | **~49 min** | **4** | — |

## 各环节时间占比

```
Ultraverge R1 (3×并行)  ████████████████░░░░░░░░  37%  (18 min)
审计验证                  ████████░░░░░░░░░░░░░░░░  16%   (8 min)
A组执行                   █████░░░░░░░░░░░░░░░░░░░  10%   (5 min)
B组执行                   ████░░░░░░░░░░░░░░░░░░░░   8%   (4 min)
设计审查                  █████░░░░░░░░░░░░░░░░░░░  10%   (5 min)
其他 (裁决+C1+C2+验收+归档)  ███████░░░░░░░░░░░░░░░░░  14%   (9 min)
```

## 各阶段 agent 效率分析

| Agent | tokens | 持续时间 | 工具调用 | 有效产出率 |
|-------|--------|---------|---------|-----------|
| 审计验证 (Orchestrator) | ~120K | ~8 min | ~45 | ✅ 15/15 项核实，无假阳性 |
| Ultraverge R1 Reviewer #1 | ~100K | ~6 min | ~30 | ✅ 0 阻断, 4 建议, 7 维全评 |
| Ultraverge R1 Reviewer #2 | ~105K | ~6 min | ~40 | ✅ 2 阻断(事实核查精度), 1 建议 |
| Ultraverge R1 Reviewer #3 | ~105K | ~6 min | ~25 | ✅ 0 阻断, 5 建议, Bitter Lesson 视角 |
| Design Review | ~95K | ~5 min | ~10 | ✅ 3 highlights, DR1/DR2/DR7 concerns |

## 审计验证质量分析

15 项审计发现由 Claude 产出，由 Orchestrator (GLM-5.1) 逐项交叉验证。验证方法：读原始文件 → grep 定位锚点 → 与审计声称对比 → 实跑 distill dry-run。

| 验证维度 | 结果 |
|---------|------|
| 文件路径 + 行号准确性 | 15/15 命中 |
| 锚点文本逐字匹配 | 15/15 匹配 |
| 严重度分级合理性 | 15/15 合理（阻断级4项均涉及机制自相矛盾） |
| distill dry-run 实证 | false_generality 数据过期确认 |
| 假阳性率 | 0% |

**跨模型审计验证的价值**：Claude 产出审计 → GLM 验证，两个独立模型对全部 15 项达成一致。这是天然的对抗式交叉验证——如果审计有假阳性，验证阶段就会暴露。

## Ultraverge R1 深度剖析

### 三家 Reviewer 分工

| Reviewer | 角色定位 | verdict | 阻断 | 建议 | 独有价值 |
|----------|---------|---------|------|------|---------|
| R1 | 全量审查 + DR7维 | 可执行 | 0 | 4 | 防漂移注释采纳建议; 需裁决项的裁决建议 |
| R2 | 事实核查 + 锚点验证 | 阻断需修复 | 2 | 1 | **A5 验收 grep 假阳性** (SKILL.md:298); **A6 第三处遗漏** (reviewer-prompt.md:156) |
| R3 | Bitter Lesson + Occam + 宪法合规 | 可执行 | 0 | 5 | **"需裁决"系统性过度审慎**; A4 不存在合法跳过路径论证 |

### R2 的独有阻断：验收精度问题

R2 发现的两个阻断都不是设计方向问题，而是**修复合同的执行精度问题**：

1. **A5 验收 grep 假阳性**：计划要求 `grep '.meta/' 零命中`，但 SKILL.md:298 配置参数示例含 `.meta/.converge/`（合法内容）。修复简单（删除一行），但验收命令会永远判定失败——"验收比修复更难"的典型案例。
2. **A6 第三处遗漏**：计划列出两处替换，但 reviewer-prompt.md:156 "在 blocking issue 中标注 `deterministic_check: skipped`" 存在歧义（YAML 顶层字段 vs issue 内字段），虽被提及但归为"同步核对"而非确定性修改。

**教训**：对低档 executor 执行的修复合同，验收命令的精度和修改点的穷举是独立于修复本身的正确性课题。

### 并行裁决规则的实际运行

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

**关键设计验证**：并行裁决规则的"少数派 conceptual/architectural 自动升级"条件未触发——说明规则对"方向分歧"和"执行精度分歧"的区分是有效的。R2 的阻断是"你说删第144行，但验收命令会误判第298行"——这是精度问题，不是方向问题。

### "需裁决"项的裁决效率

| 项 | R1建议 | R3建议 | 裁决 | 是否真正需要裁决 |
|---|---|---|---|---|
| A1 第四条 | 允许缩小范围 | 允许缩小范围 | 允许 | **是** — 存在设计权衡 |
| A2 防漂移 | 采纳 | 直接纳入 | 直接纳入 | **否** — 纯维护注释 |
| A4 方案 | 方案一 | 方案一 | 方案一 | **否** — 宪法措辞明确 |
| A5 删除/改写 | 改写 | 删除 | 删除 | **边缘** — Occam指向删除但需判断信息丢失 |
| A7 重命名 | 重命名 | 重命名 | 重命名 | **否** — 备选方案违反自家反模式 |

**4/5 的裁决项有明确最优解**——R3 正确指出这是系统性过度审慎。过度裁决化的成本：每个裁决项需要 ultraverge Reviewer 逐条裁断 + 用户确认，增加了 2-3 分钟的流程开销。建议后续计划将裁决项限定为"确实存在两个可行方向"的决策，对 Occam 有明确答案的项直接纳入修复合同。

## 自举特性分析：医者自医

本次收敛的对象是 converge SKILL 自身。这产生了几个独特性质：

### 自举的正确性

- **15 项审计发现中，多数命中了 SKILL 自定义的反模式**：naming_drift (verdict枚举不一致)、archaeology_leftover (Red Flag悬空引用)、data_tool_coupling (项目路径泄漏)。审计者用 converge 教 Reviewer 抓的反模式来抓 converge 自己——且全部命中。这说明反模式定义的实证有效性。
- **三层分离经受住了修改压力测试**：A 组（治理域）改 5 个文件、B 组（非保护域）改 6 个文件、C 组（运维）无文件修改——三组的修改程序不同（ultraverge / 标准评议 / 用户裁决），执行时零越界。
- **CONSTITUTION.md 第四部修改程序实际运行**：A 组修改走 ultraverge（≥3 Reviewer + 收敛 + 设计审查），B 组走标准评议——宪法规定的分层修改程序被完整执行。

### 自举的局限

- **无法验证 Executor 路径**：ultraverge 单轮评议直接通过，未进入 Executor 修复循环。SKILL 的 Executor 降档机制、inner loop 验收、overturn 检测等运行时机制未受实际考验。
- **收敛者=被收敛者**：Orchestrator 在修改 SKILL.md 的同时遵循 SKILL.md 的流程——存在"在修改规则的同时按规则行事"的自指风险。缓解措施：用户触发 ultraverge（打破闭环），3 个独立 Reviewer 用全新上下文审查（不共享 Orchestrator 的修改意图）。

## 设计审查 Highlights 处置

| # | 发现 | 影响 | 处置 |
|---|------|------|------|
| H1 | Positioning 流程图未反映需重新设计回路 | Fresh Reviewer 心智模型不完整 | ✅ 已修复（SKILL.md:18-23 添加回退箭头） |
| H2 | Antipattern 枚举奇偶性无自动化校验 | "三处统一"硬约束仅靠注释维护 | 📝 建议在 distill 脚本中加入 ~10 行奇偶校验 |
| H3 | C2 悬置导致"可完全重建"声明不可靠 | antipatterns.md 声明与 .gitignore 矛盾 | ✅ 用户已裁决：.gitignore 改为 done/ 入库 |

## 经验沉淀

### 做得好的

1. **跨模型审计验证**：Claude 审计 → GLM 验证，两个独立模型对 15 项达成一致。零假阳性的审计报告让后续 ultraverge 聚焦于修复合同精度而非事实核实。
2. **并行裁决的少数派保护机制**：R2 的 implementation 级阻断未升级完整收敛（正确），但其事实性发现仍被采纳为 plan amendment——并行裁决不是"赢者通吃"。
3. **R3 的 Bitter Lesson 视角**：对"需裁决"的系统性过度审慎提出了有说服力的批评——4/5 裁决项有 Occam 明确最优解。这是 DR 层面的洞察，不是单条修复意见。
4. **A/B/C 三组分组有效**：治理域 (ultraverge) / 非保护域 (标准评议) / 运维决策 的三层修改程序在执行中零越界，验证了 CONSTITUTION 第三部分组策略的可操作性。

### 可改进的

1. **裁决项应设准入门槛**：当前"需裁决"标记由计划作者自行标注，缺乏客观标准。建议：只有存在≥2 个可行方向且有真实 trade-off 的决策才标记为裁决项；Occam 有明确答案的项直接纳入修复合同并标注理由。
2. **验收命令应在计划阶段做假阳性分析**：A5 的 `grep '.meta/' 零命中` 验收命令在 R2 事实核查时才暴露假阳性。建议：计划中每条验收命令都应先跑一遍当前代码库，确认基线状态。
3. **设计审查 H2 (枚举奇偶性) 应优先级更高**：A2 修复的正是枚举漂移问题，但修复方式是注释——用"逐字同步"文字约束来防止文字漂移。在 distill 脚本中加入 ~10 行奇偶校验的成本极低，应在下个维护周期内完成。
4. **README_en.md 双维护风险未解决**：B2 重译了英文版并加了"以中文版为准"声明，但终止状态表仍需 SKILL.md 与 README.md / README_en.md 三处同步。未引入单源化机制。

### 模式建议

- **治理文档修改 → Ultraverge**（宪法级约束，≥3 Reviewer + 设计审查）
- **自举修正 → 跨模型审计 + Ultraverge**（避免单模型盲区，Claude 审计 + GLM 验证 + 3 并行 Reviewer）
- **修复合同精度 → 事实核查专家 Reviewer**（R2 角色证明：锚点验证 + 验收命令假阳性分析是独立价值层）
- **"需裁决"标记 → 设准入门槛**（Occam 有明确答案的项直接纳入，仅保留有真实 trade-off 的决策）
