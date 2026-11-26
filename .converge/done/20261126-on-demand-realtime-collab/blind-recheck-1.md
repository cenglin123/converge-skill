---
round: 1
reviewer_backend: opencode
generated_at: 2026-11-25T17:39:54.349310+00:00
invocation_id: 78ca9299-7cc7-4e60-9504-c578c8544ee2
reservation_id: 85b4c1f97ba8
reviewer_instance_id: ses_dec350f8affetsrZoZ5692QZrL
verdict: 阻断需修复
---
# 盲审复核报告 · 20261126-on-demand-realtime-collab

## Reviewer 完整输出

### 结论

`verdict: 阻断需修复`

审查方式：空白上下文、只读。未读取 `attempts.md`、`round-*.md`、`uv-init-*.md` 或任何历史审查报告；未运行会修改仓库状态的命令，未修改除本输出文件外的任何仓库文件。以下判断基于计划全文、宪法、`SKILL.md`、`refs/orchestrator-guide.md`、`refs/reviewer-discipline.md`，以及为核验"单源"声明而静态查阅的 `refs/state-schema.md`、`scripts/orchest.py`、`scripts/archive_contract/model.py`、`scripts/budget_gate.py` 与相关测试。未运行 pytest，测试仅作静态核对。

### 结构化输出

```yaml
verdict: 阻断需修复
blocking_issues:
  - id: BR-1
    attribution: pending
    severity: architectural
    plan_amendment_required: true
    location: "plan §4 编辑点 3 C-21(c)；§4 编辑点 5 子项 3（guide L418–L420）与子项 6（guide L399）"
    description: |
      计划三处规定：若 retrospective.md 已归档，落地执行标识以 append-only 追加、不覆盖原内容、
      不触发 reopen。该规则与 Archive Contract v1 的规范单源直接冲突：refs/state-schema.md L28
      要求 retrospective 的任何修订必须先经 reopen 保存旧 manifest revision；archive_contract/model.py
      的 check_view 对 manifest 声明的每个文件复算 SHA-256/size（L1400–L1408），retrospective.md
      在 ROOT_FIXED 中（L53–L55）且被写入 records（L945–952），追加字节必然触发 content-mismatch。
      计划同时声称落地执行“不进 Archive Contract”，却要求写入受 Archive Contract 哈希约束的
      retrospective，构成自相矛盾；state-schema §四的 retrospective 模板也没有“落地执行条目”格式，
      “复用现有条目”不成立。按计划执行会使 done/ 归档校验、check-done-changes 或 pre-push 失败，
      或迫使 Orchestrator 手工改写 manifest（违反 Archive Contract）。
  - id: BR-2
    attribution: pending
    severity: implementation
    plan_amendment_required: true
    location: "plan §4 编辑点 3 C-21(c)；§4 编辑点 5 子项 3/6；§3 表第 3、5 行的 implementation 表述"
    description: |
      计划三处把执行标识镜像字段写成 plan frontmatter `implementation`，但唯一机械产出方
      orchest.py checkpoint-paths 输出的是 `implementation_paths:`（scripts/orchest.py L1983/L1988；
      tests/test_orchest.py L618 断言该字面量），refs/state-schema.md 也没有 `implementation` 字段。
      `implementation` 与 `implementation_paths` 是两个不同名字；执行者按计划粘贴
      `implementation_paths` 后，C-21(c)/guide 的审计指针指向不存在的 `implementation`，
      “三处完全一致”与“单源”均不成立。计划还声称不新增 state-schema 字段，实际却需要一个
      未定义的镜像字段。
  - id: BR-3
    attribution: pending
    severity: implementation
    plan_amendment_required: true
    location: "plan §4 编辑点 5 子项 7（替换 guide 原 L401 的“显式不适用”段）"
    description: |
      计划替换后的“显式不适用”段写“spawn 生命周期三命令仅限收敛循环内 executor 修复轮，
      即 SKILL.md 主循环 step f”。该句与 SKILL.md 主循环 a0+a（L226–235，spawn reviewer 前
      reserve-round）、盲审复核（L283，role=blind-reviewer）、Inner Loop（L306，--continue-of）
      以及 M-11（L356，“收敛循环内每次 spawn（reviewer / executor / 各类角色）”）直接矛盾；
      step f 只是 executor 修复轮，不是三命令的唯一使用点。计划 §5.2 却声称“无规范冲突”。
      该句会诱导 reviewer/blind/continue 轮跳过 gate，属于治理机械层错误。
  - id: BR-4
    attribution: pending
    severity: architectural
    plan_amendment_required: true
    location: "plan §4 编辑点 3 C-21(c)；§4 编辑点 5 子项 3（guide L418–L420）与子项 6（guide L399）"
    description: |
      计划把三载体的执行标识称为“客观证据”，并声称单次 Spawn 的 instance_id 能“证明执行方
      独立启动”，复用/持续会话或宿主协同的会话/成员标识能“证明非 Orchestrator 代改的执行归属”。
      但：① 抽象能力层中 instance_id 由 Spawn 产生，Continue 不产生新 id，仅记 id 无法区分
      fresh Spawn 与对同一实例的 Continue/复用；落地 spawn 又豁免 orchest.py/gate ledger，
      没有 invocation_kind 或 reservation/host receipt 可交叉核验。② 宿主协同只记会话标识、
      成员标识和“协作方式”，没有逐文件写入归属（host op-log / commit author / per-member diff）；
      Orchestrator 本身可以是协同板成员，因此这组标识最多证明“谁在场”，不能证明“谁写了哪个文件”，
      更不能排除 Orchestrator 代改。计划自己用“不冒充 fresh 启动证明”承认证据较弱，却又用
      “证明”表述，核验语义超出记录字段。该缺口直接削弱宪法 #7 在新载体上的可审计性。
suggestion_issues:
  - description: |
      S-1 审计内容隔离：红线段只规定“审计会话与落地协同板生命周期分离”，没有规定内容隔离。
      guide 新增硬约束要求落地执行方“不读审计历史”，但落地协同板若由同一 Orchestrator 主持，
      Orchestrator 已读全部 round/retrospective，可能在板上转述 reviewer 推理。建议明确：
      落地协同板必须是全新板、不得承载 round/reviewer 文本，Orchestrator 不得向执行方粘贴审计内容；
      做不到时按宪法 #6 披露该残余降级。
  - description: |
      S-2 宿主能力探测：计划明确不把该扩展写入 refs/framework-adapters.md，却写“宿主不支持时
      自动回退”；没有任何权威位置声明某宿主是否支持宿主原生实时协同，也没有探测规则。
      建议增加一行“能力声明/探测”指针（宿主文档章节或适配层备注），但不把它做成第四个抽象能力，
      否则“自动回退”不可验证。
  - description: |
      S-3 治理分类：把“参与方 ≤ 2”从硬条件改为默认值，属于适用性/权限层变化。§5.5 用
      “无数值默认/阈值/停止条件变更”解释不写 converge.governance-change/v1，只有当该变化被
      明确归类为 mechanism（而非 threshold/stopping_condition）时才成立。建议在 §2/§5.5 明写
      该分类，或在治理块中补一条 kind=mechanism、comparison=null 的记录，避免治理记录静默。
  - description: |
      S-4 振荡裁判记账语义：传话编排说振荡裁判 spawn“记入现有 gate ledger，落在 total_safety（1.5）
      余量内”，而 C-21/M-11 说落地 spawn 不进预算门；新“显式不适用”又说该记账约定不受豁免影响。
      建议用一句话明确：它是“仅记账、不占 reservation”，还是“例外地消费 total”；否则读者会
      误以为落地阶段仍有预算门，或误以为裁判 spawn 可绕过记账。
  - description: |
      S-5 宪法 #7 逃生舱：新硬约束写“无论采用单次 Spawn、传话编排还是宿主原生实时协同，
      Orchestrator 均不兼任 executor”，C-21(b) 也写“无论采用何种载体……不得直接编辑文件”。
      宪法 #7 保留 A.4 例外（Spawn 完全不可用时降级为 orchestrator_self，必须标注降级并告知用户）。
      建议在绝对表述后补该例外，或写明“#7 连同其 A.4 例外一并适用”，以免文本覆盖三分判据要求的
      逃生舱。
  - description: |
      S-6 角色枚举完整性：红线段自称“全角色枚举”，但未列 Inner Loop Reviewer（Continue 实例）、
      Material revision 的 non-decisional delta Reviewer、仲裁/振荡裁判等独立判断角色；同时列入了
      不产出 verdict 的设计审查 Reviewer。建议补齐按功能判据应覆盖的角色，或明确“括号内为示例，
      功能判据才是穷尽标准”，否则“全角色”表述不成立并留下解释漏洞。
  - description: |
      S-7 编辑锚点与改动清单精度：§4 编辑点 5 子项 3 写“替换 `### 执行标识留痕（instance_id）`
      （L418–L420）”，但当前 guide 的标题是 `### instance_id 留痕`；执行者按字面搜索会找不到。
      建议同时给出当前标题与目标标题，或明确以行号锚定。另 §3 表第 3 行只写 C-21(a)/(c)/(d)，
      但逐字终态也改了 (b)；§3 表第 1 行承诺“受控词表”，逐字文本却没有独立词表。请对齐清单与终态。
  - description: |
      S-8 悬空锚点：SKILL.md L356（M-11）仍写“见 §执行阶段/§落地执行编排”，其中 §执行阶段
      在 SKILL.md 不存在；计划明确把它排除在本次编辑范围外，但同时又改写 guide L399 的同一旧锚点。
      建议顺手修正这一处一词级悬空引用（或记录为明确 follow-up），否则 §5.2 “无悬空引用”只能
      靠范围排除成立，且同一概念在两份治理文档中留下不一致。
  - description: |
      S-9 三处逐字重复与 Occam：三载体证据段在 C-21(c)、guide L399、guide L418–L420 逐字重复，
      计划把“三处完全一致”当作优点，但这会形成漂移风险，也与既有的 C-21“职责要点 + 指针”去重
      方向相反。建议在 guide §执行标识留痕 保留唯一规范定义，C-21(c)/L399 只放指针与差异点。
  - description: |
      S-10 commit 责任与顺序：脚本化映射要求 M 侧由 checkpoint-paths 从 commit 生成，但计划没有
      指定“谁在何时 commit”（执行方？Orchestrator？人工 pre-commit 确认？），也没有说明多执行方
      无统一 commit 边界时的默认降级触发点。建议补一条最小顺序（执行方完成后由谁提交/人工确认，
      再跑 checkpoint-paths），否则该单源路径会经常退化为 LLM 汇总。
  - description: |
      S-11 d3 授权指针：d3 写“按 C-21(a) 自主推进落地”，但 C-21(a) 是载体选择，不承载自主授权；
      自主授权来自 d3 的“执行意图机械明线”与 §确认点分类。建议把授权判据指向 §确认点分类，
      C-21(a) 只用于载体选择，避免执行者把“载体可选”误读为“可自主落地”。
reads:
  - "<user-home>/Documents/GitHub/converge-skill/docs/plans/active/20261126-on-demand-realtime-collab.md"
  - "<user-home>/Documents/GitHub/converge-skill/CONSTITUTION.md"
  - "<user-home>/Documents/GitHub/converge-skill/SKILL.md"
  - "<user-home>/Documents/GitHub/converge-skill/refs/orchestrator-guide.md"
  - "<user-home>/Documents/GitHub/converge-skill/refs/reviewer-discipline.md"
  - "<user-home>/Documents/GitHub/converge-skill/.converge/active/20261126-on-demand-realtime-collab/blind-recheck-1.md"
  - "<user-home>/Documents/GitHub/converge-skill/refs/state-schema.md"
  - "<user-home>/Documents/GitHub/converge-skill/scripts/budget_gate.py"
  - "<user-home>/Documents/GitHub/converge-skill/scripts/archive_contract/model.py"
  - "<user-home>/Documents/GitHub/converge-skill/scripts/orchest.py"
  - "<user-home>/Documents/GitHub/converge-skill/tests/test_process_controller_contract.py"
```

### 阻断问题详解

#### BR-1 · 已归档 retrospective 的 append-only 规则违反 Archive Contract v1

计划在 C-21(c)、guide L399、guide L418–L420 三处给出的终态是：

> 若 `retrospective.md` 已归档，落地条目为 append-only 追加、不覆盖原内容、不触发 reopen。

这条规则把“审计权威”放在一个已被 manifest 冻结投影的文件上，但 Archive Contract v1 的规范单源给出的是相反规则：

- `refs/state-schema.md` L28：retrospective 追加修订记录，不覆盖原有内容；**修订必须经 reopen 保存旧 manifest revision 后再追加事实**（见 Archive Contract v1）。
- `scripts/archive_contract/model.py` L1400–L1408：`check_view` 用 `actual_files` 与 manifest 声明比对，并对每个声明文件复算 `sha256_size`；不一致即 `content-mismatch`。
- `scripts/archive_contract/model.py` L53–L55：`retrospective.md` 在 `ROOT_FIXED`；L945–L952：所有根文件（除 INDEX/manifest）写入 `records` 并带 sha256/size。

因此“append-only 追加”不是无害的：只要向 `done/<slug>/retrospective.md` 追加一个字节，manifest 的 `records` 哈希就不再匹配，`archive_convergence.py check`、`check-done-changes` 以及依赖 `check_view` 的 pre-push 检查都会报 `content-mismatch`。计划同时声称“落地执行不进 Archive Contract”，却要求写入 Archive Contract 管理的文件，这是自相矛盾；而且 state-schema §四的 retrospective 模板（L294–L353）没有“落地执行条目”小节或字段定义，所谓“复用现有条目”并不存在，实际是在不修改 state-schema 的前提下引入一个未定义格式。

**必须修复**：在三处统一选择一条可执行规则——

1. 把落地执行标识的权威放到归档之外（例如 plan frontmatter 的 `implementation_paths`，或一个明确的非归档 landing 记录），不再写入已归档 retrospective；或
2. 明确要求 `reopen` 后再追加，然后重新 `archive`（保存旧 manifest revision，形成新 revision），删除“不触发 reopen”；或
3. 若确实要新增归档根文件/小节，则把 `refs/state-schema.md` 与 Archive Contract 的 allowlist/格式一并纳入本次改动（这超出当前“仅两个文档”的范围，需重新评估治理范围）。

在上述选择确定前，C-21(c)/L399/L418–L420 的“审计权威”无法落地。

#### BR-2 · `implementation` 与 `implementation_paths` 字段名不一致

计划三处都把镜像字段写成 plan frontmatter `implementation`：

- C-21(c)：“plan frontmatter `implementation` 条目可作镜像”；
- guide L399：“plan frontmatter `implementation` 条目可作镜像”；
- guide L418–L420：同。

但唯一机械产出方 `scripts/orchest.py checkpoint-paths` 输出的是：

- `scripts/orchest.py` L1983：`lines = ["implementation_paths:"]`；
- L1988：空集时 `implementation_paths: []`；
- `tests/test_orchest.py` L618 断言首行必须是 `implementation_paths:`。

`refs/state-schema.md` 没有 `implementation` 字段；`scripts/README.md` L97 也只说“instance_id 记 plan frontmatter”，没有定义 `implementation`。执行者按计划把 `checkpoint-paths` 的输出粘进 plan frontmatter 后，C-21(c)/guide 的审计指针会指向一个不存在的 `implementation`，而“三处完全一致”只是三处一致地写错。计划 §1 又声称“不新增 `refs/state-schema.md` 新字段”，但要让 `implementation` 成为可审计镜像，必须定义它；当前文本既没有定义，也没有说明它与 `implementation_paths` 的关系。

**必须修复**：统一使用 `implementation_paths`，并在 C-21(c)/L399/L418–L420 说明它是 `checkpoint-paths --commit <sha>` 的机器产出块；若确实需要单独的 `implementation` 人类摘要，必须定义其字段、产出方和与 `implementation_paths` 的优先级，不能两个名字混用。

#### BR-3 · “spawn 生命周期三命令仅限 step f”与主循环/M-11 矛盾

计划替换后的“显式不适用”段写：

> spawn 生命周期三命令仅限**收敛循环内** executor 修复轮，即 SKILL.md 主循环 step f。

这句话在事实层面不成立：

- `SKILL.md` L226–L235：主循环 a0+a 在 Spawn reviewer 之前执行 `reserve-round`，reviewer 轮同样使用三命令；
- `SKILL.md` L283：盲审复核使用 `reserve-round role=blind-reviewer`；
- `SKILL.md` L306：Inner Loop 用 `reserve-round --continue-of`；
- `SKILL.md` L356 M-11：收敛循环内每次 spawn（reviewer / executor / 各类角色）的 gate 生命周期统一经 `orchest.py reserve-round / register-round / cancel-round`。

step f 只是 executor 修复轮，不是三命令的唯一使用点。计划 §5.2 却把该段列为“精确同步”并声称“无规范冲突”。这不是措辞问题：执行者若按该句理解，会认为 reviewer/blind/continue 轮不需要三命令，直接削弱 M-11 和预算门。

**必须修复**：改为“spawn 生命周期三命令仅限收敛循环内各轮（reviewer / executor / 盲审 / Continue）；落地执行方不适用”，并保留“手工传话振荡裁判的 gate ledger 记账约定不受此豁免影响”这一句。

#### BR-4 · 三载体“证明”语义超出记录字段

计划要求记录：

- 单次 Spawn：executor `instance_id`，声称“证明执行方独立启动”；
- 手工传话：参与执行方 `instance_id` 列表；
- 宿主协同：宿主协作会话标识、实际执行成员标识、协作方式，声称“证明非 Orchestrator 代改的执行归属”。

问题有两层：

1. **fresh Spawn 无法由 id 单独证明。** 抽象能力层中 `instance_id` 由 Spawn 产生；Continue 是对已有实例发消息，不产生新 id（`SKILL.md` L54–L56）。因此一个 `instance_id` 既可能来自本轮 fresh Spawn，也可能来自对旧实例的 Continue/复用。落地 spawn 又豁免 `orchest.py`/gate ledger，没有 `invocation_kind`、reservation 或 host receipt 可供交叉核验。只记 id 不能支持“证明独立启动”的强断言。
2. **宿主协同的成员标识不能证明逐文件归属。** 会话 id + 成员名册 + “协作方式”最多证明谁在场、用了什么模式；它不记录“哪个成员写了哪个路径”。Orchestrator 本身可以是协同板成员，因此这组证据不能排除 Orchestrator 代改，也不能在事后审计中把某个文件的写入归给某个执行方。计划用“不冒充 fresh 启动证明”承认了弱化，但同一句又使用“证明非 Orchestrator 代改”，前后强度不一致。

**必须修复**：把“客观证据”的最小字段写清楚——

- fresh Spawn：`invocation_kind=spawn` + `instance_id` + reservation/host receipt（或其 locator）；
- 手工传话/宿主协同：逐文件归属证据（host op-log 的成员 id + path、commit author/Co-authored-by、或 per-member diff）的 locator；
- 若宿主无法提供逐文件归属，则把措辞降为“参与与归属证据（不证明具体写入者）”，并按宪法 #6 明确披露 #7 在此载体上只能做到行为约束、不能机械证明，不能继续使用“证明”二字。

### 建议问题

- **S-1 审计内容隔离**：红线段只规定“审计会话与落地协同板生命周期分离”，没有规定内容隔离。guide 新增硬约束要求落地执行方“不读审计历史”，但落地协同板若由同一 Orchestrator 主持，Orchestrator 已读全部 round/retrospective，可能在板上转述 reviewer 推理。建议明确：落地协同板必须是全新板、不得承载 round/reviewer 文本，Orchestrator 不得向执行方粘贴审计内容；做不到时按宪法 #6 披露该残余降级。
- **S-2 宿主能力探测**：计划明确不把该扩展写入 `refs/framework-adapters.md`，却写“宿主不支持时自动回退”；没有任何权威位置声明某宿主是否支持宿主原生实时协同，也没有探测规则。建议增加一行“能力声明/探测”指针（宿主文档章节或适配层备注），但不把它做成第四个抽象能力，否则“自动回退”不可验证。
- **S-3 治理分类**：把“参与方 ≤ 2”从硬条件改为默认值，属于适用性/权限层变化。§5.5 用“无数值默认/阈值/停止条件变更”解释不写 `converge.governance-change/v1`，只有当该变化被明确归类为 `mechanism`（而非 `threshold`/`stopping_condition`）时才成立。建议在 §2/§5.5 明写该分类，或在治理块中补一条 `kind=mechanism`、`comparison=null` 的记录，避免治理记录静默。
- **S-4 振荡裁判记账语义**：传话编排说振荡裁判 spawn“记入现有 gate ledger，落在 `total_safety`（1.5）余量内”，而 C-21/M-11 说落地 spawn 不进预算门；新“显式不适用”又说该记账约定不受豁免影响。建议用一句话明确：它是“仅记账、不占 reservation”，还是“例外地消费 total”；否则读者会误以为落地阶段仍有预算门，或误以为裁判 spawn 可绕过记账。
- **S-5 宪法 #7 逃生舱**：新硬约束写“无论采用单次 Spawn、传话编排还是宿主原生实时协同，Orchestrator 均不兼任 executor”，C-21(b) 也写“无论采用何种载体……不得直接编辑文件”。宪法 #7 保留 A.4 例外（Spawn 完全不可用时降级为 `orchestrator_self`，必须标注降级并告知用户）。建议在绝对表述后补该例外，或写明“#7 连同其 A.4 例外一并适用”，以免文本覆盖三分判据要求的逃生舱。
- **S-6 角色枚举完整性**：红线段自称“全角色枚举”，但未列 Inner Loop Reviewer（Continue 实例）、Material revision 的 non-decisional delta Reviewer、仲裁/振荡裁判等独立判断角色；同时列入了不产出 verdict 的设计审查 Reviewer。建议补齐按功能判据应覆盖的角色，或明确“括号内为示例，功能判据才是穷尽标准”，否则“全角色”表述不成立并留下解释漏洞。
- **S-7 编辑锚点与改动清单精度**：§4 编辑点 5 子项 3 写“替换 `### 执行标识留痕（instance_id）`（L418–L420）”，但当前 guide 的标题是 `### instance_id 留痕`；执行者按字面搜索会找不到。建议同时给出当前标题与目标标题，或明确以行号锚定。另 §3 表第 3 行只写 C-21(a)/(c)/(d)，但逐字终态也改了 (b)；§3 表第 1 行承诺“受控词表”，逐字文本却没有独立词表。请对齐清单与终态。
- **S-8 悬空锚点**：`SKILL.md` L356（M-11）仍写“见 §执行阶段/§落地执行编排”，其中 §执行阶段在 `SKILL.md` 不存在；计划明确把它排除在本次编辑范围外，但同时又改写 guide L399 的同一旧锚点。建议顺手修正这一处一词级悬空引用（或记录为明确 follow-up），否则 §5.2 “无悬空引用”只能靠范围排除成立，且同一概念在两份治理文档中留下不一致。
- **S-9 三处逐字重复与 Occam**：三载体证据段在 C-21(c)、guide L399、guide L418–L420 逐字重复，计划把“三处完全一致”当作优点，但这会形成漂移风险，也与既有的 C-21“职责要点 + 指针”去重方向相反。建议在 guide §执行标识留痕 保留唯一规范定义，C-21(c)/L399 只放指针与差异点。
- **S-10 commit 责任与顺序**：脚本化映射要求 M 侧由 `checkpoint-paths` 从 commit 生成，但计划没有指定“谁在何时 commit”（执行方？Orchestrator？人工 pre-commit 确认？），也没有说明多执行方无统一 commit 边界时的默认降级触发点。建议补一条最小顺序（执行方完成后由谁提交/人工确认，再跑 `checkpoint-paths`），否则该单源路径会经常退化为 LLM 汇总。
- **S-11 d3 授权指针**：d3 写“按 C-21(a) 自主推进落地”，但 C-21(a) 是载体选择，不承载自主授权；自主授权来自 d3 的“执行意图机械明线”与 §确认点分类。建议把授权判据指向 §确认点分类，C-21(a) 只用于载体选择，避免执行者把“载体可选”误读为“可自主落地”。

### 反模式观察

- `over_compromise`：BR-1 中的“append-only 追加、不触发 reopen”用便利性换取了 Archive Contract 的完整性，是典型的“为省一次 reopen 而弱化冻结投影”的折中。
- `iterative_sediment`：三载体证据段在三个位置逐字沉积（BR-2/BR-4/S-9），后续任一处修订都可能留下两处旧文本。
- `archaeology_leftover`：未发现计划正文引用轮次/retrospective/修复历史；计划本身没有考古层，这一点通过。

### 已核对且未发现阻断的项

- **宪法 §一（Bitter Lesson）**：条件 1（产物已收敛且方案已定稿）与条件 2（验收判据机械可核）保留为硬前置，仅条件 3 与落地载体选择交还 Orchestrator；方向与三分判据一致。未阻断的遗留点是：宿主协同路径“不新增停止条件/计数阈值”没有在 §2 的三分判据中显式归类（见 S-3/S-4）。
- **宪法 §二 #6/#7**：两处都写明独立性降级告知“及其对结论可靠性的影响”；三载体均禁止 Orchestrator 直接编辑。遗漏 #7 的 A.4 逃生舱（S-5），但不是本次新增的独立违规。
- **目标文件范围**：仅 `SKILL.md` 与 `refs/orchestrator-guide.md`，二者都在 `CONSTITUTION.md` 第三部治理文档清单内；不涉及 `CONSTITUTION.md` 或其他治理文档，未发现打包越界。
- **行号锚点**：`d3` L252、C-21 L379、guide §八 L388–L469、流程 L394–L397、脚本化映射 L399、显式不适用 L401、自主推进明线 L407、硬约束 L413–L416、执行标识留痕 L418–L420、清单项数核对 L422–L429、传话首句 L433 与当前文件一致；仅“执行标识留痕”的标题名与实际不符（S-7）。
- **不变量与非变更声明**：层级模式“子收敛之间不通信”（L519）与“子任务间无实时数据依赖”（L514）未被改写；M-11 的预算门、`orchest.py` 记账、Archive Contract 的“落地 spawn 不进预算门”等声明与原文方向一致——除 BR-1 要求写入已归档 retrospective 的自相矛盾外。
- **ultraverge 程序**：§5.4 的“≥3 独立 Reviewer 初评 → 修复 → fresh Reviewer 重审 → 强制收敛后设计审查 → finish 归档”与 `SKILL.md` 的 ultraverge 要求一致；计划本身的 `governance_level: ultraverge` 与目标文件性质匹配。
- **盲审纪律**：计划正文未出现 `attempts.md`/`round-*` 历史引用或“本轮已修”类痕迹；未发现要求改写历史 entry 的指令。

### 读取清单

**完整读取（`read`）**

- `<user-home>/Documents/GitHub/converge-skill/docs/plans/active/20261126-on-demand-realtime-collab.md`（全文 L1–129）
- `<user-home>/Documents/GitHub/converge-skill/CONSTITUTION.md`（全文 L1–96）
- `<user-home>/Documents/GitHub/converge-skill/SKILL.md`（L1–547）
- `<user-home>/Documents/GitHub/converge-skill/refs/orchestrator-guide.md`（L370–529，重点 §八）
- `<user-home>/Documents/GitHub/converge-skill/refs/reviewer-discipline.md`（L1–300）
- `<user-home>/Documents/GitHub/converge-skill/.converge/active/20261126-on-demand-realtime-collab/blind-recheck-1.md`（L1–16，仅骨架）
- `<user-home>/Documents/GitHub/converge-skill/refs/state-schema.md`（L1–60、L70–119、L294–353）
- `<user-home>/Documents/GitHub/converge-skill/scripts/budget_gate.py`（L1400–1519）
- `<user-home>/Documents/GitHub/converge-skill/scripts/archive_contract/model.py`（L52–81、L940–1089、L1388–1427）
- `<user-home>/Documents/GitHub/converge-skill/scripts/orchest.py`（L1933–2002）
- `<user-home>/Documents/GitHub/converge-skill/tests/test_process_controller_contract.py`（L30–159、L210–269）

**辅助检索（grep，仅片段，未作全文阅读）**

- `refs/framework-adapters.md`
- `GOVERNANCE-DECISIONS.md`
- `scripts/README.md`
- `tests/test_orchest.py`
- `docs/plans/done/` 下与 `implementation`/`instance_id` 相关的历史命中

**明确未读**

- `attempts.md`
- 任何 `round-*.md`（含历史轮次报告）
- 任何 `uv-init-*.md`
- 任何历史审查/修复报告

## Orchestrator 处理记录

(pending)