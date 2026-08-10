---
type: retrospective
object_slug: 20260612-execution-gap-v2
generated_at: 2026-06-12T13:42:00+08:00
---

# Retrospective · 20260612-execution-gap-v2

## 1. 结束模式

终止-b 渐近通过。R1（3 Reviewer，1 pass + 2 block）→ Executor 修复 → R2 = 0 blocking。共 2 轮。

## 2. 阻断轨迹

R1=2 (B-A structural, B-B structural) → R2=0

## 3. Antipattern 巡查

| Round | 类型 | 对象 | 触发结果 |
|-------|------|------|---------|
| (无) | | | |

## 4. Executor 路径依赖评估

Executor 正确执行了两处修复：B-A 做减法（移除 checklist 项，改动 4→3），B-B 做加法（补充 5 部分骨架）。方案从 86 行变为更精炼的版本。未触发 antipattern。

## 5. Reviewer 间 Verdict 分歧分布

| 轮次 | Verdict | 阻断数 | 归因分布 |
|------|---------|--------|---------|
| R1-A | 可执行 | 0 | — |
| R1-B | 阻断需修复 | 2 | plan_defect ×2 |
| R1-C | 阻断需修复 | 2 | plan_defect ×2 |
| R2 | 可执行 | 0 | — |

R1 分歧：R1-A 认为方案可执行（3 suggestion 但零阻断），R1-B/R1-C 各发现 structural 级阻断。按 ultraverge 多数方向推进。R1-A 的 suggestion 与 R1-C 的阻断有重叠（checklist 位置问题），印证了 R1-C 的发现。

## 6. 降级影响评估

无降级。

## 7. 经验教训

1. **约简后的着陆方式同样需要审查**：190→86 行的约简方向完全正确，但约简后选择"checklist 项"作为约束锚点是错误的着陆——checklist 是"验证已发生事实"，不是"约束未来行为"。R1-C 的分析精准：这不是大小问题，是位置问题。**教训**：约简不只砍内容，还要审查剩余内容的着陆位置是否语义正确。

2. **"约 X 行"不是可执行规格**：改动描述只说"约 15 行"但无内容骨架，executor 无法推断必须覆盖什么。R1-C 的 5 部分骨架建议（IF/reading/task/output/disciplines）是标准 prompt 模板的最小结构——不需要写完整模板，但必须声明结构。

3. **R1-A 的"可执行"判断过于宽松**：R1-A 将 checklist 位置问题降级为 suggestion（"把交通规则贴在毕业证书上"的违和感），而 R1-C 正确将其升级为 blocking（语义模式破坏）。**教训**：当 reviewer 对同一发现给出 suggestion vs blocking 的分歧时，Orchestrator 应倾向于升级而非降级。

## 8. 后续建议

方案已收敛并通过用户审计。审计发现 5 项问题（D1 P1 + D2-D4 P2 + D5 P3），用户认同全部 5 项，Executor 已完成修订。方案等待用户确认后落地。

### 审计后修订记录

| 发现 | 级别 | 修订内容 |
|------|------|---------|
| D1 触达路径断裂 | P1 | 改动 3→4：新增 SKILL.md 主循环锚点（step d 后路由指令） |
| D2 instance_id 留痕 | P2 | orchestrator-guide 小节增加 instance_id 记录（客观证据） |
| D3 确定性核对砍过头 | P2 | 保留清单项数 vs 实改文件数核对（近零成本） |
| D4 模板骨架不完整 | P2 | 补 fresh-context 声明 + 不读 attempts/round/contract |
| D5 自举裸奔窗口 | P3 | 新增"自举声明"小节 |

### 元观察：盲审 vs ultraverge 的对比实证

独立审计 agent（fresh 视角，不读收敛历史）发现了 ultraverge 三个 Reviewer（带收敛历史）的遗漏——特别是 D1（触达路径断裂），这是真正的 blocking issue。这为盲审复核的价值假设提供了现场实证：**独立空白视角能发现带历史视角的遗漏**。n=1，且审计 agent 与 ultraverge reviewer 是不同 agent（独立性强于盲审设计的"同模型不同 spawn"），但方向明确支持。应记入盲审复核方案的实证清单。

## 9-10. 合同/Rubrics

N/A（未启用）

## 成本数据

| 阶段 | tokens | 时间 | agent 数 | 关键产出 |
|------|--------|------|----------|---------|
| R1 Ultraverge（3 Reviewer） | ≈50K | ≈4min | 3 | 2+2 阻断（R1-A 零阻断） |
| R1 Executor | ≈15K | ≈2min | 1 | 2 处修复，改动 4→3 |
| R2 Reviewer | ≈10K | ≈1min | 1 | verdict=可执行，2/2 resolved |
| 设计审查 | 跳过（方案已极简） | — | — | — |
| 审计后 Executor（修订） | ≈15K | ≈2min | 1 | 5 处修复（3→4 改动，约 98 行） |
| **总计** | **≈90K** | **≈9min** | **6** | 约 98 行最小方案（含审计修订） |

## Rule Activity

| rule | triggered | zero_streak | status |
|------|-----------|-------------|--------|
| boundary_guard | false | 1 | active |
| reviewer_boundary_audit | false | 1 | active |
| intent_drift_check | false | 1 | active |
| gate_l1 | false | 1 | active |
| design_review_trigger | false | 1 | active |

设计审查未触发（方案极简，3 处改动共约 30 行）。追踪机制执行成本：约 1 句话。当前被追踪规则总数 = 5（> 2），追踪机制仍有必要。
