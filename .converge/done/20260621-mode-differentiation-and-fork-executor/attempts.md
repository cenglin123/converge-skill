# Attempts · 模式分层 + Fork Executor

> Round 1 — plan revision pass. Editing plan text only; change-list describes future source edits (not applied).

## Round 1 attempt · CB1
- source: converge_loop
- reviewer_backend: claude-code
- Issue: "零代码 diff 主张证伪——invariant #6 + §A1 同时主张 budget_gate.py/tests 零 diff 又降 max_blind_rechecks 默认 2→1，自相矛盾"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 采纳 path (a)——把轻量值设为真实默认；§A1/Part A 改动清单/invariant #6/摘要/硬边界/验收命令全部改为「裁决逻辑零 diff，仅 :55 默认值 + test:604 期望两行变更」，新增 A-7/A-8 行
- Diff: inline (plan sections 摘要 / §A1 设计 / Part A 改动清单 / 不变量 #6 / 硬边界 / 验收命令)
- R1 verdict:

## Round 1 attempt · CB2
- source: converge_loop
- reviewer_backend: claude-code
- Issue: "公式术语错配——SKILL.md:370 写 max_ultraverge_initial 但代码 budget_gate.py:349 base 取 ultraverge_min_reviewers；且 stock 数字未具体化"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: A-2 增「修正公式符号 max_ultraverge_initial → ultraverge_min_reviewers」；§A1/invariants/摘要写死 普通=42 / ultraverge=44（单调、无下溢），SKILL 配置表 stock 注解改为模式相关
- Diff: inline (plan sections §A1 设计 / Part A 改动清单 A-2 / 不变量 #1)
- R1 verdict:

## Round 1 attempt · CB3
- source: converge_loop
- reviewer_backend: claude-code
- Issue: "残留『重算确认单调』TODO 措辞，应替换为已解析数字"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 折入 CB1/CB2——全文 TODO 措辞替换为 42/44 结论；Q4 由开放问题划为「已定」并写明无下溢、无残余 TODO；测试期望同步（A-8）
- Diff: inline (plan sections §A1 设计 / Part A 改动清单 A-2/A-8 / 待裁决 Q4)
- R1 verdict:

## Round 1 attempt · CB4
- source: converge_loop
- reviewer_backend: claude-code
- Issue: "#7/Q1 自相矛盾——Q1 标『待 Reviewer 定』却在 张力1 写定论『fork 不违反 #7 字面』且预置 B-5 为已完成改动项"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: 张力1 改写为「裁决中的主张」并记录本轮 ultraverge split ruling（3 致字面合规、1+设计审查认意图层灰区）；B-5 降级为条件项（仅第四部确认后执行）；Q1 更新为记录 split ruling + 残余裁决 deferred 第四部
- Diff: inline (plan sections §Part B 评估 张力1 / Part B 改动清单 B-5 / 待裁决 Q1)
- R1 verdict:

## Round 1 attempt · CB5
- source: converge_loop
- reviewer_backend: claude-code
- Issue: "抗锚定无硬验收门——fork 继承叙事可能锚定更强，补偿仅靠『显式重申』，验证留作开放 Q2"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: §不变量 增 #8 强制门——Part B 落地前必须跑 fork-vs-fresh pilot 对照（over_compromise/past_commitment_anchoring 出现率），仅无实质性升高方接受补偿；Q2 由开放问题升级为引用 #8 硬门
- Diff: inline (plan sections 不变量 #8 / 待裁决 Q2 / §Part B 评估 张力2)
- R1 verdict:

## Round 1 attempt · 建议折入（B-3/B-4/A-4/A-5/B-1/frontmatter）
- source: converge_loop
- reviewer_backend: claude-code
- Issue: "B-3 须重申全部 §1–§7；B-4 tier 别名 + Agent matcher 计数注；A-4/A-5 执行动词明线；B-1/B-4 fork 为探测能力；frontmatter status → in_review"
- Issue 归因（reviewer 判定）: plan_defect
- plan_amendment_required: true
- Approach: B-3 改为重申 §1–§7（张力2 同步）；B-4 增 tier 别名注 + PreToolUse matcher 计数注；A-4/A-5/A2 表行加「并执行/落地/apply」机械明线；B-1/B-4/框架适配标注 fork 为探测能力、不支持降级 fresh；frontmatter status draft→in_review
- Diff: inline (plan sections frontmatter / §A2 确认表 / Part A 改动清单 A-4/A-5/A-6 / §Part B 评估 张力2 / §设计 框架适配 / Part B 改动清单 B-1/B-3/B-4)
- R1 verdict:


## Blind-recheck polish · S1+S2
- source: converge_loop
- reviewer_backend: claude-code (blind af733ec7bdfe44fa8)
- Issue: 不变量#6「精确为两行」与「新增断言」字面张力；A-2「错配」暗示不存在的算术 bug
- Issue 归因（reviewer 判定）: plan_defect (precision)
- plan_amendment_required: true
- Approach: 「两行」→「两处改动点」；「术语错配」→「术语对齐（值恒等）」
- Diff: inline (不变量#6 / §A1 / A-2 / 摘要)
- R verdict: Accepted (blind reviewer pre-specified wording)

## 收敛后修订 · 触发（user_external_input）
- source: user_external_input
- 触发时间: 2026-06-21（原收敛完成后同日）
- 触发内容: 用户决定折入设计审查 H1（生成式边界）+ H2（耦合风险预算）；并实地调用 opencode 1.17.8 与 codex 0.141.0 框架原生 agent 评审 Part B 可移植性，返回实证报告（见 cross-framework-codex.md / cross-framework-opencode.md）。
- 实质性挑战: 是——证伪 H3「fork 仅 Claude Code」前提（Codex 实测有原生 fork），并引入新硬约束（fork 继承父模型 → fork 与 executor 降档互斥）。
- 待 Executor 折入的范围: 见 Executor 追加的 PR-1..PR-N entries。

## 收敛后修订 attempt · PR-1
- source: user_external_input
- Issue: H1 设计审查——fork 适用边界应为生成式原则，而非角色封锁清单（防滑坡）
- Approach: 折入生成式 fork 边界（fork 仅授予产出受下游 fresh 独立 reviewer 机械复核的角色），role table 降为该原则推论；§Part B 设计/适用边界 + 张力1 同步
- Diff: inline (plan section §Part B 设计 适用边界 / role table / 张力1 / 待裁决 Q1)
- verdict:

## 收敛后修订 attempt · PR-2
- source: user_external_input
- Issue: H2 设计审查——三个独立性削弱器（fork + A2 自主落地 + blind 2→1）不得在默认路径叠加；pilot 须测 composed 路径
- Approach: 不变量 #8 改为测 composed 路径（fork→自主落地→blind=1）；新增不变量 #9 风险预算耦合（叠加时 blind 保持 2）；§A2 加耦合约束段
- Diff: inline (plan sections 不变量 #8/#9 / §A2 与 Part B 的耦合约束)
- verdict:

## 收敛后修订 attempt · PR-3
- source: user_external_input
- Issue: H3 实证证伪——跨框架实测确证 Codex 0.141.0 原生支持 live fork，「fork 仅 Claude Code」不对称论证不成立
- Approach: 撤销不对称论证，重写张力3 / §框架适配为「3 框架中 2 个原生支持，opencode 干净降级 fresh」；保留 H3 较弱版本（sunset / 重评触发）
- Diff: inline (plan sections §Part B 评估 张力3 / §设计 框架适配 / 可移植性结论)
- verdict:

## 收敛后修订 attempt · PR-4
- source: user_external_input
- Issue: forked executor 继承父模型（CC + Codex 实测均确立）→ fork 与 executor 模型降档互斥，原文缺此硬约束
- Approach: §设计 增「fork ⊥ 降档」新硬约束段（~line 146）；新增不变量 #10；Part B 改动清单增 B-7（SKILL.md §模型分层 + executor_model_tier 交互注）
- Diff: inline (plan sections §Part B 设计 fork⊥降档 / 不变量 #10 / Part B 改动清单 B-7)
- verdict:

## 收敛后修订 attempt · PR-5
- source: user_external_input
- Issue: 跨框架实测发现 framework-adapters.md A.2/A.3 需校正（Codex Spawn fork_context 变体 + 两步 Continue + resume_agent + per-agent override 仅 fresh；opencode task_id Continue + subagent_type 非普遍可用 + CLI --fork 非 live fork）
- Approach: Part B 改动清单增 B-8（refs/framework-adapters.md §A.2/A.3 跨框架实测校正），枚举上述未来编辑为子项
- Diff: inline (plan section Part B 改动清单 B-8)
- verdict:

## 收敛后修订 attempt · PR-6
- source: user_external_input
- Issue: budget-tier 可移植性数据（opencode 经插件/permission deny 可得 deny-before-spawn；Codex 0.141.0 无可验证 deny-before-spawn）应记为未来扩展数据，不声称已实现
- Approach: Part B 改动清单增 B-9（best-effort guarded 可移植性注，记录未来扩展数据；CC 仍是唯一已落地 best-effort guarded 框架）
- Diff: inline (plan section Part B 改动清单 B-9)
- verdict:
