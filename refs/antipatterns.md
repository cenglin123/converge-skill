---
type: antipattern-registry
last_distilled_at: "2026-06-11T09:48:59Z"                   # 由 distill 脚本首次运行后写入
dormant_threshold: 8                     # 连续 N 次收敛零命中 → active 降 dormant（前期观察窗口，积累实证数据）
archive_threshold: 20                    # 连续 N 次收敛零命中 → dormant 降 archived（保守阈值，避免过早丢失未验证的反模式）
new_prefix_window: 5                     # 统计 new: 前缀的滑动窗口大小（最近 N 次收敛）
new_prefix_promote_threshold: 3          # 窗口内出现 ≥ N 次 → 提示人工固化
---

# Antipattern Registry

> **compiled 产物**。raw source = `done/*/retrospective.md` §3 Antipattern 巡查表。
> 删除本文件后运行 `scripts/distill_antipatterns.py` 可完全重建。
> 只有 `status: active` 的条目被注入 reviewer-prompt。

## 字段说明

| 字段 | 维护者 | 说明 |
|------|--------|------|
| `id` | 人工 | 与 reviewer-prompt.md `antipattern_observations.type` 枚举**逐字一致** |
| `layer` | 人工 | `executor` / `design` / `orchestrator` |
| `status` | distill 脚本 | `active` → `dormant` → `archived` |
| `last_confirmed` | distill 脚本 | 最后命中的收敛对象 slug |
| `confirmed_count` | distill 脚本 | 历史累计命中次数 |
| `zero_streak` | distill 脚本 | 当前连续零命中收敛数 |
| `resurrection_log` | 人工 | 人工复活记录 `[{date, reason}]` |
| `detection_constraint` | 人工 | 仅 `layer: orchestrator`，值为 `indirect` |

## 初始值约定

首次创建（首次 distill 运行前）：`status: active`（全部），`confirmed_count: 0`，
`last_confirmed: ""`，`zero_streak: 0`，`resurrection_log: []`。
distill 首次运行后回填真实统计值。

---

```yaml
antipatterns:
  # ── Executor 层（Reviewer 读 attempts.md 直接检测）────────────────────

  - id: minimum_patch
    layer: executor
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    description: |
      只修当前阻断点，不上溯检查同一上游决策是否也受污染。
      Reviewer 检测方式：读 attempts.md，检查 executor 是否仅修改了 reviewer
      明确标出的位置，而未主动检查同一上游决策的其他下游影响。

  - id: solution_anchoring
    layer: executor
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    description: |
      reviewer 上轮提结构性切换，executor 在原方案内打补丁敷衍。
      Reviewer 检测方式：对比 reviewer 要求的修改方向与 executor 实际 diff——
      若 reviewer 要求切方案 A 而 executor 在方案 B 上加字段/flag 应付，即命中。

  - id: over_compromise
    layer: executor
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    description: |
      reviewer 上轮要 X，executor 给了"X 和 Y 的折中"（如 0.2 vs 0.35 → 给 0.25），
      而非直接执行 reviewer 要求的精确值/方案。
      Reviewer 检测方式：对比 reviewer 要求的精确修改与 executor diff 中的实际值/方案，
      若存在无理由的中间值即命中。

  - id: past_commitment_anchoring
    layer: executor
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    description: |
      executor 盲目延续过往 Accepted 方案，未独立审视当前 reviewer 的具体要求。
      当 attempts.md 中存在已 Accepted 的修复时，executor 将其视为不可变更的承诺
      而非历史记录。
      Reviewer 检测方式：若当前 reviewer 要求的方向与过往 Accepted entry 方向冲突，
      检查 executor 是否因"上轮已接受"而拒绝执行本轮要求。

  - id: report_hallucination
    layer: executor
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    description: |
      子代理生成看似合理的"成功报告"但未实际执行关键操作。两种典型表现：
      (1) 报告声称已处理 N 个文件，但文件系统无对应产物（未调用 Write 工具）；
      (2) 报告声称矫正完成，但矫正方向错误——将正确术语"矫正"为错误的已知值
      （如 V4→V3），根因是子代理基于过时知识自信地执行了反向矫正。
      Reviewer 检测方式：(a) 对比子代理声称的产物清单与文件系统实际存在的文件
      ——缺失 > 0 或文件大小为 0 即命中；(b) 对比矫正前后的关键术语
      ——若正确术语被改为错误术语即命中。若子代理响应中包含"成功/完成/已处理"
      等声明但无具体文件路径+大小证据，标记为疑似。

  # ── 设计层（Reviewer Round 1 即可检测，前置自检用）───────────────────

  - id: false_generality
    layer: design
    status: active
    last_confirmed: "20260610-model-tiering-amendment"
    confirmed_count: 1
    zero_streak: 2
    resurrection_log: []
    description: |
      声称通用但实际专用（或反之），导致用户/agent 产生虚假预期。
      例：名称是通用工具，API 全部是领域术语。
      Reviewer 检测方式：对比产物名称/描述与 API/实现中的术语域——不一致即命中。

  - id: identity_crisis
    layer: design
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    description: |
      名称、描述、实现三者不一致，产物不清楚自己是什么。
      例：描述说"通用 docx 工具"，文件名是 product-standard-format.js。
      Reviewer 检测方式：前置自检第 1 问——"产物身份自洽"——不通过即命中。

  - id: data_tool_coupling
    layer: design
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    description: |
      工具层携带业务数据或环境硬编码，破坏纯度，导致无法干净复用。
      例：SKILL 内部包含项目特定的 JSON 数据文件。
      Reviewer 检测方式：前置自检第 3 问——"产物数据纯度"——不通过即命中。

  - id: environment_lock-in
    layer: design
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    description: |
      依赖静态快照（如复制 node_modules）或硬编码环境路径，放弃版本管理和可移植性。
      Reviewer 检测方式：检查产物是否包含硬编码的绝对路径、本地环境变量依赖、
      或复制而非引用的第三方依赖。

  - id: archaeology_leftover
    layer: design
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    description: |
      文档中包含描述"过去发生过什么"而非"现在是什么"的历史措辞。
      典型表现："已迁出"、"从 X 提取"、"曾位于"、"迁移至"等——这些是
      迁移考古，git log 是它们唯一的合法归宿。
      Reviewer 检测方式：扫描产物中是否存在描述文档演化历史（而非当前状态）的措辞。
      关键词如"已迁出"、"曾位于"、"原名为"、"从 X 提取"等迁移时态标记是线索——
      但需判断整句是否在描述历史而非现状。描述当前状态的"已完成"、"已实现"等不算。
      English equivalents: "moved from", "extracted from", "formerly located in",
      "relocated to". CHANGELOG 文件不在此检测范围内——CHANGELOG 是专用变更日志，
      其内容本身就是在记录变更历史，属于有意设计而非考古残留。

  # ── Orchestrator 层（间接检测，通过日志痕迹）─────────────────────────

  - id: orchestrator_self_review
    layer: orchestrator
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    detection_constraint: indirect
    description: |
      "reviewer 意见和上轮差不多，不用 Spawn 新的，我自己看看就行"——
      orchestrator 版 minimum_patch。
      检测方式（间接）：下一轮 Reviewer 或复盘者通过 round-N.md 的 reviewer_backend
      字段检测——若出现 orchestrator_self 而非真实 spawn 后端，即命中。
      Reviewer 不直接审查 Orchestrator 的思考过程（看不到），只通过日志痕迹间接检测。

  - id: silent_merge
    layer: orchestrator
    status: active
    last_confirmed: ""
    confirmed_count: 0
    zero_streak: 4
    resurrection_log: []
    detection_constraint: indirect
    description: |
      "这个 issue 和上轮那个本质一样，我合并处理"——
      Type R 等价标注的滥用（未记录理由的 silently merge）。
      检测方式（间接）：复盘者检查 attempts.md 中 Type R 标注是否都附带
      [Orchestrator Detection] 理由；存在无理由的等价合并即命中。
```

> **待蒸馏（Q4/Q5）**：前置自检新增的 Q4（职责边界自洽）和 Q5（命名一致性）当前通过 `blocking_issues`（severity=conceptual）进入修复管道，尚无对应 antipattern 条目。待 `distill_antipatterns.py` 积累足够实证命中数据后，应将 Q4 蒸馏为 `responsibility_mismatch`（声称/实际职责矛盾）和 Q5 蒸馏为 `naming_drift`（跨文件命名不一致）两个设计层 antipattern 条目。届时需将 `identity_crisis`（引用 Q1）和 `data_tool_coupling`（引用 Q3）的 `description` 中"前置自检第 N 问"编号更新为 5 问体系（`false_generality` 未引用 Q2 编号，无需更新）。
