---
type: retrospective
object_slug: 20260621-mode-differentiation-and-fork-executor
generated_at: 2026-06-21T00:00:00Z
---

# Retrospective · 模式分层 + Fork Executor

## 1. 结束模式
**收敛成立**（clean）。ultraverge 流程：3 并行评议（全 阻断需修复）→ 完整收敛 R1（可执行，5 block 全 resolved）→ 盲审复核 pass（零阻断）→ 盲审后 2 项精度 polish → 强制设计审查（咨询式，3 highlights）。最终 fresh reviewer 可执行 + 盲审 pass，零残留阻断，无需用户 b/c 确认。
> 注意：本次收敛是对 **plan 文件**的设计批准；plan 描述的源码改动（budget_gate.py:55 / tests:604 / SKILL.md / executor-prompt.md / framework-adapters.md / CONSTITUTION）**尚未落地**，须经 CONSTITUTION 第四部人工审议 + 人工提交批准后执行。

## 2. 阻断轨迹
评议(3R 合并)=5 → R1=0 → 盲审=0。单调。

## 3. Antipattern 巡查
| Round | 类型 | 对象 | 触发结果 |
|-------|------|------|---------|
| 评议 | （无 executor 反模式，Round 1 无 attempts 历史） | — | — |
| R1 | none | executor 修复 | reviewer 确认方向一致，无 over_compromise / minimum_patch / 锚定 |
| 盲审 | archaeology_leftover: none | plan 全文 | 盲审确认无修复痕迹；split ruling 记录属合法产物内容 |

## 4. Executor 路径依赖评估
R1 executor 按评议 findings 直修，未发明中间值（反折中保持）；CB4 未在"预置裁断"上打补丁而是真正降级 B-5 为条件项（打破方案锚定）。盲审 polish 仅按盲审 reviewer 逐字指定改措辞，无越界。

## 5. Reviewer 间 Verdict 分歧分布
| 轮次 | Verdict | 阻断数 | 归因分布 |
|------|---------|--------|---------|
| 评议 R1(uv-init-1) | 阻断需修复 | 2 | plan_defect×2 (structural) |
| 评议 R2(uv-init-2) | 阻断需修复 | 2 | plan_defect×2 (structural+impl) |
| 评议 R3(uv-init-3) | 阻断需修复 | 2 | plan_defect×2 (conceptual+architectural) |
| R1 验收 | 可执行 | 0 | — |
| 盲审 | 可执行 | 0 | — |

**关键分歧**：R1/R2 聚焦"零 diff 证伪"（structural 事实层），R3 独立捕获 #7-Q1 程序自相矛盾（conceptual）+ 抗锚定无硬门（architectural）——R1/R2 将后者列 boundary clean。按 ultraverge 裁决规则：少数派 conceptual/architectural 阻断 → 强制完整收敛（已执行）。R3 的深层 block 是本次收敛最高价值发现，验证了 ultraverge ≥3 并行 Reviewer 的盲区覆盖价值（Pilot 经验 #6 同源）。

## 6. 降级影响评估
无降级。3/3 ultraverge Reviewer 实 spawn，无 orchestrator_self，无 inner_loop 降级。预算全程 auditable-only（未 bind 总量 hook）——见 §诚实边界。

## 7. 经验教训
- **机制层**：盲审分层这类"改默认值"的改动极易被误判为"纯文档/零代码"——3 名 Reviewer 中 2 名独立去 grep 源码才戳破"默认值硬编码在 .py:55、测试断言 cap=44"。教训：凡声称"零代码 diff"的预算/配置改动，必须核对默认值的物理定义位置 + 关联测试断言。
- **机制层**：自举收敛中，#7（角色分离）的"字面 vs 立法意图"分歧无法靠 Reviewer 多数决解决，正确做法是渲染 split ruling 并 defer 第四部人工审议，而非让 plan 自行拍板（CB4）。
- **对象层**：设计审查（发散）捕获了 5 名收敛 Reviewer（收敛）都未提的承重问题——fork 边界是封锁清单非生成式原则（H1）、两 Part 独立性削弱器在默认路径叠加（H2）。印证 design review 的"视角切换"价值。

## 8. 后续建议
1. **落地前**：用户决策是否折入设计审查 H1（生成式边界）+ H2（耦合 fork/盲审/自主落地的风险预算）——见 design-review.md。若折入 → 走收敛后修订（done/→active/）。
2. **落地执行**：Part A 源码改动（budget_gate.py:55、tests:604）+ 治理文档改动须经第四部人工审议（尤其 B-5 对 #7 的解释）+ 人工提交批准。**本次收敛不构成 fork 收益的实证，仅为设计批准**；fork 真实收益须由不变量 #8 的 pilot 对照在落地阶段度量。
3. **Q1 残余**：fork 是否合规 #7 的意图层，交第四部裁决；裁决结果记 GOVERNANCE-DECISIONS（GD-x）。

## 9. Round 0 合同谈判评估
| 维度 | 评估 |
|------|------|
| 是否启用 | 否（跳过理由：plan 已含「不变量（验收硬条件）」+「不可逾越约束」充当合同；用户要求直接走 ultraverge） |
| contract 是否减少预期错位 | N/A |
| contract_amendment 触发次数 | 0 |

## 10. Rubrics 评估
未启用独立 Rubrics；评议以前置自检 5 问 + DR 7 维 + CONSTITUTION 第一部（Bitter Lesson/Occam）为判据。

## 11. 收敛后修订记录

### 修订 1（user_external_input，2026-06-21，原收敛完成后同日）
- **触发来源**：用户决定折入设计审查 H1（生成式 fork 边界）+ H2（耦合风险预算）；并实地调用 **opencode 1.17.8** 与 **codex 0.141.0** 框架原生 agent 评审 Part B 可移植性，返回实证报告（cross-framework-codex.md / cross-framework-opencode.md）。
- **输入摘要**：跨框架实测证伪 H3「fork 仅 Claude Code」前提——**Codex 0.141.0 原生支持 live fork**（`multi_agent_v1.spawn_agent(fork_context=true)`，框架 agent 实测 spawn 双变体验证）；opencode 无 live 子 agent fork（`--fork` 仅 CLI session fork）→ 干净降级 fresh。引入新硬约束：**fork 继承父模型 → fork 与 executor 降档互斥**。两框架 agent 均独立 ENDORSE H1 生成式边界。
- **影响范围**：§Part B 评估（张力1/2/3）、§设计（适用边界生成式原则 + fork⊥降档）、§框架适配、不变量 #8/#9/#10、改动清单 B-1/B-3/B-4/B-7/B-8/B-9、待裁决 Q1/Q2。
- **新增轮次**：R2（收敛后修订验收，不计入 max_outer_loops）。Executor 折入（PR-1..PR-6，跨两次 spawn——首个 executor API 中断后由第二个补完 invariant#10 / B-7/B-8/B-9 / attempts 条目）→ fresh Reviewer R2 对照源报告核验。
- **结论变化**：H3 不对称论证撤销（fork 非单框架补丁，2/3 框架原生）；fork 边界从封锁清单升级为生成式原则；新增 fork⊥降档硬约束 + 风险预算耦合（不叠加 fork+blind1+自主落地）。
- **Reviewer 验证**：R2 fresh 独立 Reviewer verdict = **可执行**，6 PR 全 resolved，零回归，跨框架声明逐条对照源报告无失真。2 条 suggestion：(1) SKILL.md:370 旧值为 A-2/B-7 的 pending 编辑（非缺陷）；(2) 采纳——落地时在 B-8/B-3 加一行「inherited payload fidelity 框架不确定（[UNCERTAIN]）」。
- **降级说明**：Continue（SendMessage）在本宿主会话未暴露，首个 executor API 中断后无法续命，按 framework-adapters §A.4 改为 fresh spawn 补完（功能等价，已记于 instance registry）。
- **二次盲审**：未触发——收敛后修订为加性/校正性，原盲审 pass 对收敛核心仍有效；修订内容经 fresh 独立 Reviewer 对照源报告核验（符合 SKILL §收敛后修订 step 4）。

## 盲审复核
```yaml
blind_recheck:
  status: pass
  traces_reported: 0          # archaeology_leftover: none
  rounds_used: 1
  findings_count: 0
  escalated_to_main_loop: false
```

## 成本数据
| 阶段 | agent 数 | 关键产出 |
|------|----------|---------|
| ultraverge 评议（并行） | 3 | 5 合并 blocking（含 R3 的 #7+抗锚定深层项） |
| R1 Executor | 1 | CB1-CB5 修复 + 折入 7 suggestion |
| R1 Reviewer | 1 | 可执行，5 block 全 resolved（源码核验） |
| 盲审 Reviewer | 1 | 可执行 + 2 精度 suggestion |
| 盲审 polish Executor | 1 | 「两行」→「两处改动点」；「错配」→「术语对齐」 |
| 设计审查 | 1 | 3 highlights（H1 边界/H2 交互/H3 Bitter Lesson） |
| **总计** | **8 spawn** | total cap 44，8/44，无孤儿 reservation |

## Rule Activity
| rule | triggered | zero_streak | status |
|------|-----------|-------------|--------|
| boundary_guard | false | 1 | active |
| reviewer_boundary_audit | false | 1 | active |
| intent_drift_check | false | 1 | active |
| gate_l1 | false | 1 | active |
| design_review_trigger | true | 0 | active |
| blind_recheck | true | 0 | active |
| budget_gate | true | 0 | active |

> 追踪机制执行成本：本次约 8 次 gate reserve/settle + 1 次 ingest-verdict，开销低（确定性脚本，零 LLM token）。被追踪 guard 规则 >2 条，追踪机制仍必要。

## 诚实边界（降级告知）
本次收敛全程 **auditable-only**——未 bind 宿主 PreToolUse 总量 hook（best-effort guarded 未启用）。预算强制力依赖 Orchestrator 按 M-11 手动 reserve/settle（已全程执行，ledger 完整、零孤儿）+ pre-push hook 兜底检测。用户知悉：该模式下预算强制力为"可审计但非宿主硬阻断"。
