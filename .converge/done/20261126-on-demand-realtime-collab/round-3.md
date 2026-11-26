---
round: 3
reviewer_backend: codex
generated_at: 2026-11-25T17:27:23.189621+00:00
invocation_id: 041a0281-7aa4-4703-a548-6bd717ae9785
reservation_id: d5e12af722a9
reviewer_instance_id: 01a213bf-7659-7cc1-bf77-96ec8c75aa82
verdict: 阻断需修复
---

# Round 3 独立复审

```yaml
round: 3
verdict: 阻断需修复
blocking_issues:
  - id: B2
    attribution: plan_defect
    severity: structural
    plan_amendment_required: true
    location: "计划 §4 编辑点 2、3(d)、5 第 4/6 项"
    description: >-
      L399 已纳入编辑，retrospective.md 已统一为执行标识的审计权威。
      checkpoint-paths 降级仍有不同口径。L399 覆盖所有无法机械生成的情形，并明确须先 commit，
      C-21(d) 与清单项数核对只覆盖多 Executor 无统一 commit 边界，d3 则只写无统一 commit 边界。
      单 Executor 完成改动但尚未 commit 时，L399 明确允许降级，其余三处没有一致指令。
      L399 又把 N vs M 核对写成机械生成，而 C-21(d) 只让脚本生成 M，比较仍归 Orchestrator。
      必须单源规定脚本只生成 M、机械生成的前置条件和失败时汇总全体实改文件集并标注的规则，
      其余各处引用同一规则。
  - id: B3
    attribution: plan_defect
    severity: structural
    plan_amendment_required: true
    location: "计划 §3 编辑点 5、§4 编辑点 4 和 5；操作指南 §八 L401、L407"
    description: >-
      L407 保留原来的「自主 spawn executor 落地」，把普通 converge 的授权判据写成固定载体，
      与同节新版流程及 C-21(a) 冲突。L401 又把落地语境的 gate 生命周期命令限制为收敛循环内
      executor 修复轮，而新版传话编排要求落地振荡裁判记入现有 gate ledger。
      必须把 L407 改为按 C-21(a) 推进落地，并明确 L401 的豁免只适用于落地执行方，
      区分振荡裁判原有记账职责；同步更新编辑清单与验收。
  - id: B4
    attribution: plan_defect
    severity: structural
    plan_amendment_required: true
    location: "计划 §1、§3 编辑点 4、§4 编辑点 4、§5 第 5 项"
    description: >-
      新增了一个此前不存在的宿主落地协同硬停：同一接口或文件被推翻达到 type_o_threshold
      时立即停止协同并上报。复用默认值 3 仍然新增了停止条件的适用范围和计数对象。
      §1 与 §5 据「不改变停止条件」跳过机器块和 task-envelope 的论证失效。
      必须如实描述停止规则变化并按适用的治理门修订计划，或重新限定复用既有规则的范围并给出
      足以支撑 preflight 判定的依据。若触发 material revision，还须按操作指南执行对应复核。
suggestion_issues:
  - id: R3-S1
    description: >-
      计划 L36 只说给出 C-21(a)/(c) 终态，正文也改了 (d)；L37 仍把条件 1 写成
      「归档 done/ 或已定稿」，并把实时协同写成回归全局 O/R/F/S。
      逐字终态要求终局 decision 后归档，并仅适用 O 等价守卫和 F 计数覆盖。
      建议让摘要引用终态，避免保留第二份简化口径。
  - id: R3-S2
    description: >-
      编辑点 5 第 1 项将同长度的反引号围栏嵌套在一起，渲染时无法表达逐字替换块。
      建议使用更长的外层围栏。
  - id: R3-S3
    description: >-
      计划要求持续会话在使用前披露降级，并描述了失效的反锚定机制。
      建议在逐字终态把「向用户说明影响」写入同一句义务，直接对应宪法 #6。
antipattern_observations: []
rechecks:
  B2: still_blocking
  S-1: still_blocking
  S-2: resolved
  S-3: still_blocking
  S-6: resolved
  S-7: resolved
reads:
  - '<user-home>\Documents\GitHub\converge-skill\docs\plans\active\20261126-on-demand-realtime-collab.md'
  - '<user-home>\Documents\GitHub\converge-skill\.converge\active\20261126-on-demand-realtime-collab\attempts.md'
  - '<user-home>\Documents\GitHub\converge-skill\CONSTITUTION.md'
  - '<user-home>\Documents\GitHub\converge-skill\SKILL.md'
  - '<user-home>\Documents\GitHub\converge-skill\refs\orchestrator-guide.md'
  - '<user-home>\Documents\GitHub\converge-skill\refs\reviewer-discipline.md'
  - '<user-home>\Documents\GitHub\converge-skill\.converge\active\20261126-on-demand-realtime-collab\round-3.md'
```

## 前轮事项逐项核验

| 项 | 结论 | 依据 |
|---|---|---|
| B2 | `still_blocking` | 计划 L38、L106–108、L116 补齐 L399 的范围、终态和验收。计划 L60、L102、L108 统一审计权威。L54、L60、L104、L108 仍存在上述降级范围及机械职责差异。 |
| S-1 | `still_blocking` | attempts L31 将此项与 B2 合并记载。审计权威部分已闭合，合并项承诺的 checkpoint-paths 一致性仍缺。 |
| S-2 | `resolved` | 计划 L77 明示 A↔B 翻转纳入同一计数，R/S 在宿主实时路径不适用。此项的语义补齐成立，新增硬停的治理问题由 B4 单独记录。 |
| S-3 | `still_blocking` | 计划 L47、L60、L87、L105、L108 均指向统一适用门或 C-21(a)，但指南 L407 仍是独立的强制 Spawn 口径，见 B3。 |
| S-6 | `resolved` | 计划 L47 明示核心角色表的 Executor 全新上下文约束作用于收敛主循环，L60、L96 同时为落地默认 Spawn 保留 fresh-context。 |
| S-7 | `resolved` | 计划 L102、L108 明示已归档执行条目只追加、保留原内容且不触发 reopen，L60、L102、L108 均将 frontmatter 定位为镜像。L38 与 L116 正确列出当前六个计划编辑子项。 |

S 编号依据 attempts L31–32 的合并摘要及其列举顺序核对。前轮报告未在本轮读入范围内，S-1 按合并记载核验，S-7 同时核验追加规则与编辑范围清单。

## 宪法与范围核验

计划 §2 保留收敛定稿及机械验收两个硬前置，载体和参与规模交给 Orchestrator；§4 将可选宿主扩展限制在落地阶段，保留收敛主循环的预算门和层级模式的不通信约束。独立审计按功能判据隔离被审者及同行 Reviewer，协作互查不得产出 verdict 或进入 gate。降级告知和 Orchestrator 禁止代改均写入终态，宪法 #1–#5 的现有确认点与验收边界未见被移除。受保护文档继续走 ultraverge、收敛后设计审查与人工确认提交。B3 涉及操作指引的适用范围，B4 涉及新增停止条件的治理程序。

本轮审查对象为计划及其拟议终态。执行了文本交叉核对。测试套件、preflight 和归档后的写入行为未实测。输出文件仅为保留骨架 frontmatter 及核验报告而读取。

