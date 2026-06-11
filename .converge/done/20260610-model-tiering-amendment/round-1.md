---
round: 1
reviewer_backend: claude-code (×3 并行)
reviewer_instance_id: af971407c69ddbae4 (A), acd19c731218704d4 (B), afa254d6596e2d01b (C)
generated_at: 2026-06-10T12:30:00+08:00
---

# Round 1 · 20260610-model-tiering-amendment（3 并行扩域评议）

> 注：三个 Reviewer 收到相同 prompt 后均自取代号 "Granite"——代号去重失败，按 A/B/C 区分。Orchestrator 教训：代号应由 prompt 注入而非让 agent 自取。

## 三方 verdict 与阻断（合并去重后）

3/3 = 阻断需修复（全一致，采纳）。原始阻断 A×4 + B×3 + C×4 = 11 条，去重合并为 6 条联合阻断：

| 联合 | 来源 | severity | 内容 |
|------|------|----------|------|
| U1 | A-B2 / B-B1 / C-B1 | structural | M1(b) 声称与 A.3 #4"同义"为假——A.3 #4 含第三许可路径（"scope 有清晰的任务级理由"，无需用户授权），M1(b) 实为收紧。落地后一宽一严并存且无裁决语句。修复：改"同义"为"收紧并推广"，加优先级声明（Executor 降档场景以本节为准，A.3 #4 管辖其余 override） |
| U2 | A-B1 / B-B2 | implementation | "仅当 M1 三条件满足"——计划内部标号"M1"将被机械转写进 SKILL.md 成悬空引用，且验收项 2 引号锁定该缺陷措辞。修复：改自足表述"仅当「模型分层」小节三条件满足"，验收同步 |
| U3 | B-B3 | structural | 档位词表不闭合：强档/低成本档/中档/最低档四词、M4 两列表、M2 枚举仅 inherit/low——"最低档"在数据层无定义。修复：统一两档词表 |
| U4 | A-B4 / C-B2 | conceptual | 术语碰撞："降级"在现行全部语料中专指能力/流程降级（A.4、ultraverge 降级路径、必检 L269、宪法 #6/#7、orchestrator-guide §五）。"不降级角色：Reviewer"将与 A.4"Reviewer 降级"同文档对撞。修复：全部改用"降档"词系 + 语义切割声明 |
| U5 | A-B3 / C-B4 | structural | "盲评"未定义（全仓零命中）且含判断成分，与"Reviewer 不降级（判断力密集）"自相矛盾，构成绕过漏洞。修复：给判别准绳（存在客观判准、可机械复核）并换例（清点/diff） |
| U6 | C-B3（A-S1/B-S1 同域） | structural | **计划违反自身降档条件 (a)**：声明低成本执行但合同非确定化——M1-M4 只有要点无逐字插入文本，插入锚点不唯一（核心角色表后的 `---` 前/后、##/### 层级未定）。要点级验收兜不住措辞级偏差。修复：附 M1-M4 逐字插入块 + 唯一引文锚点 |

## 三方 YAML 完整输出

（A/B/C 三份 YAML 原文及 evidence 简表见本轮三个 agent 的返回，关键内容已逐字并入上表与下方 suggestion 清单；attribution 全部 plan_defect；C 报 antipattern: false_generality——M1(b) 以"同义"包装实际收紧，A/B 零报。）

## Suggestion 去重清单（Orchestrator 处置：全部采纳）

1. (C-S1) tier 落地通道：档位经由各框架 Spawn 的模型选择参数实现；不支持则视同 inherit
2. (C-S2) M1(c) 挂载点：收敛完成前必检追加一条 checkbox（纯新增行，不动责任清单四分组）
3. (C-S3/B-S2) M4 强档列：Orchestrator 模型由会话决定、converge 无权选择——列语义改为参考信息（判断密集角色当期主力档）
4. (B-S3) 层级模式角色收口：未列出角色（Worker/仲裁/L2 gate Reviewer）默认 inherit
5. (B-S4) M4 头部加"本文件为数据层、非治理文档"声明，封堵 SKILL.md"边界按最高强度"升格读法
6. (A-S2) 档位取值与三条件核对结果记入 attempt log
7. (A-S3) M4 Claude 行 Fable 5 标注核实来源（运行时会话佐证）
8. (A-S4) 验收项 1 改可判定表述（收紧关系明示 + 管辖切分语句存在）
9. (B-S6/C-S4) 删执行注记的行号死条款
10. (三方 lean_template_assessment 共识) 范式声明追加两条适用规则：声明低成本执行的计划必须附逐字插入块；治理文档类计划必须附入边引用盘点结果

## Orchestrator 处理记录

- **[Orchestrator Detection]** 裁决：3/3 一致阻断需修复 → 进入完整收敛。无 Type O/R/F/S（首轮）。
- **[Orchestrator Detection]** U1/U4/U6 均为入边引用与既有语义类缺陷——上次修宪的 U2 教训（入边盘点）已注入 prompt 仍漏（计划作者盘点了"模型选择"入边但漏了"降级"同词入边与 A.3 #4 的语义关系）。确认该检查应机制化（候选：reviewer-prompt 增补，走后续治理）。
- **[Orchestrator Detection]** Executor 模型决策：本轮修复含治理条文逐字起草（判断密集）→ **不降档**，用继承模型。这本身是 M1 三条件 (a) 的活案例：合同未确定化前不许降档。
- **[Orchestrator Detection]** 轻量范式裁定（三方一致）：范式可成立，但适用条件需从自由声明改为可检验判据。修复后的计划即首个合规样本。
