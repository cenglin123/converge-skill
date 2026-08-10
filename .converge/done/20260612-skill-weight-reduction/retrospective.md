---
type: retrospective
object_slug: 20260612-skill-weight-reduction
generated_at: 2026-06-12T17:35:00+08:00
---

# Retrospective · 20260612-skill-weight-reduction

## 1. 结束模式

终止-b 渐近通过。R1（3 Reviewer，3/3 block）→ Executor 修复 → R2 = 0 blocking。共 2 轮。

## 2. 阻断轨迹

R1=4 (B1 structural, B2 architectural, B3 structural, B4 implementation) → R2=0

## 3. Antipattern 巡查

| Round | 类型 | 对象 | 触发结果 |
|-------|------|------|---------|
| (无) | | | |

## 4. Executor 路径依赖评估

Executor 正确修复了 4 个阻断：补 A.5、补 5 处内部引用、补 2 处跨文件引用、修正百分比。未触发 antipattern。

## 5. Reviewer 间 Verdict 分歧分布

| 轮次 | Verdict | 阻断数 | 归因分布 |
|------|---------|--------|---------|
| R1-A | 阻断需修复 | 4 | plan_defect ×4 |
| R1-B | 阻断需修复 | 5 | plan_defect ×5 |
| R1-C | 阻断需修复 | 3 | plan_defect ×3 |
| R2 | 可执行 | 0 | — |

R1 无分歧——三个 Reviewer 一致阻断。核心问题高度一致（A.5 遗漏、引用断裂），证明阻断判断可靠。

## 6. 降级影响评估

无降级。

## 7. 经验教训

1. **外提操作必须审计所有引用**：附录 A 被 7 处引用（5 内部 + 2 外部），计划一个都没处理。这是外提操作的系统性风险——内容移走了但指针没更新。**教训**：外提计划的第一步应该是 grep 所有引用，而不是直接设计替换文本。

2. **"~40%" 是精确度陷阱**：三个 Reviewer 都独立验证了百分比不成立。减重方案中的数据必须可审计——"~115 行"是对的，但 115/544 ≠ 40%。**教训**：百分比必须用计算器，不用直觉。

3. **A.5 遗漏是扫视偏差**：A.5 只有 6 行，在 545 行文件的末尾。计划作者扫到"通用降级"就停了。**教训**：列举小节时应从文件末尾往前数，而非从头往后扫。

## 8. 后续建议

方案可执行。落地后 SKILL.md 预计从 ~545 行减至 ~430 行（~19% 减重）。

## 9-10. 合同/Rubrics

N/A

## 成本数据

| 阶段 | tokens | 时间 | agent 数 | 关键产出 |
|------|--------|------|----------|---------|
| R1 Ultraverge（3 Reviewer） | ≈55K | ≈5min | 3 | 4+5+3 阻断（高度一致） |
| R1 Executor | ≈15K | ≈2min | 1 | 4 处修复 + 2 suggestion |
| R2 Reviewer | ≈12K | ≈1min | 1 | verdict=可执行，4/4 resolved |
| **总计** | **≈82K** | **≈8min** | **5** | 减重方案（可执行） |
