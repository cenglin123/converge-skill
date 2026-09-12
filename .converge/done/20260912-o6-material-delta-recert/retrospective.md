---
type: retrospective
object_slug: 20260912-o6-material-delta-recert
generated_at: 2026-09-12T00:00:00Z
---

# Retrospective · 20260912-o6-material-delta-recert

## 1. 结束模式

ultraverge 完整收敛（O6 material 增量复核机制）。3 UV 初审全阻断（conceptual/architectural 密集）→ candidate-2 → outer R1 阻断（4 BLK，伪代码一致性级）→ candidate-3 → outer R2 阻断（抓到 fail-open：revision 过滤短路整门）→ candidate-4 → **outer R3 可执行 + blind-1 可执行（材料对）** → 设计复审判修订（D1-D6）→ 编排层裁决：plan 字节冻结于 candidate-4，D1-D6 作为绑定实施约束带入执行 → 实施（7 文件，+820/-212）→ 独立审计不通过（2 blocking，单点）→ 修复 → 聚焦复审**闭合**。

## 2. 新约定的首次完整实践

- 用户 2026-09-12 约定（趋势收敛 + 达限即通过）在本对象落地为：R1→R2 的 issue 明显精度化后，修复直取单选修法；设计复审 D 级发现不再回炉 plan 字节，而是作为绑定实施约束 + 实施后审计兜底。
- 成本对照：B 对象同量级机制变更 ≈30 次派发、7 次材料重认证；本对象 ≈16 次派发、1 次材料对（candidate-4 一次成型后未再变更字节）。**O6 的成本问题以"按新约定运行"的方式自证了解法**。

## 3. 机制结论（O6 从 record-only 转为落地）

- `converge.material-revision/v1` 块新增 `change_class`（decisional/non-decisional）+ `changed_sections`/`decisional_anchors`（12 项统一受控词表）；归类作者声明、复核者挑战、争议=decisional。
- `decisional` → 全量双权威同字节（不变）；`non-decisional` → 单 fresh delta reviewer（verdict 正向 `== 可执行`），payload 增 `delta{base,current,change_class}` 并按目标块三锚定。
- 材料门链式回溯：`rev_cur = all_blocks[-1].get("revision_id")`；legacy 块 → 仅当前段末块 require_full_pair（D1 Option A，行为等价现状）；任何一环缺失 fail-closed。
- 规范句（`refs/orchestrator-guide.md:17-32`、`refs/state-schema.md:96-118`）按 §12 逐字改写，失效句保留 decisional 语义、新增 delta 语义。

## 4. 事故与降级

- 无产物覆盖事故（路径一致性 preflight 上线后零复发；期间 preflight 拦截 2 次编排层坏 prompt——机制自证）。
- 误分类结算照旧存在（repair/审计的 in-place 改写仍被 ocsr 判非零），已在 `da81e70` 的 adapter 侧缓解（`--in-place-edit`），ocsr 上游根治列为后续（任务 2）。
- 过程降级点（如实记录）：①设计复审 D 级发现未回炉 plan 字节，以绑定实施约束带入执行；②A-18（伞形计划 untracked）为 plan-side 已知缺陷，非实施引入；③用户收口裁决（`989e5ebd`）授权评审循环提前收口。

## 5. 经验教训

- **fail-open 比阻断更危险**：R2 抓到的 revision 过滤缺陷会把整门短路且反转 10 条负例——"新增门禁"的每一行过滤逻辑都要对既有负例做反转推演。
- **设计复审与事实复审互补且不可互相替代**：R2 抓 fail-open（代码级），设计复审抓"闭集漏一个身份锚点 / legacy 语义漂移"（设计级）。
- **审计后聚焦复审**是低成本闭合的正确形态（9.5 min vs 全量重审）。
- **单选修法纪律**让修复轮保持机械：三票/R1/R2/设计复审共 ~30 条 issue 全部按单选修法落地，零回摆。

## 6. 实施结果

- 7 文件（+820/-212）+ 审计后修复（B1 用例重做、B2 校验前锚定）。
- 全量：**554 passed / 5 skipped**（基线 523 → 552 → 554）；`py_compile`、`git diff --check` 通过。
- 独立审计 → 2 blocking 修复 → 聚焦复审**闭合**；10 条既有负例零反转（A-19 pass）。

## 7. 成本数据

| 阶段 | 派发数 |
|---|---|
| 撰写 + 修订 ×3 | 4 |
| UV 初审 | 3 |
| outer R1-R3 | 3 |
| blind | 1 |
| 设计审查 | 1 |
| 实施 + 审计 + 修复 + 聚焦复审 | 4 |
| 合计 | **16**（B 同量级 ≈30） |

## 8. 后续

- 任务 2：ocsr 上游（声明式覆盖 + 路径一致性）。
- 伞形计划 F8（O6 状态行）随本对象入库更新。
terminal_decision_event_id: 6b3e306a-39e8-4ebd-9b1a-18f35c534f1d
terminal_decision_value: 可执行
