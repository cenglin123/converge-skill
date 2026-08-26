<!-- design review (advisory, non-blocking), generated for ultraverge closure -->

```yaml
design_review:
  dimensions:
    - name: consistency
      status: concerns_found
      findings:
        - finding: budget_extension 记录在改后会出现三处并列描述——guide §六（作者字段清单，补齐后的 extension_id/ts/granted_at_usage 加既有字段）、state-schema §预算 gate L437（extension 校验细节，保留）、scripts/budget_gate.py validate_extensions（机器校验）。同一记录三种说法，且各自宣称的权威不同（作者基准 vs 校验细节 vs 机器实现）。
          location: refs/orchestrator-guide.md §六预算追踪+gate编排 / refs/state-schema.md §预算 gate L437 / scripts/budget_gate.py validate_extensions
          impact: 与本计划“单一权威源”的主线相矛盾；三处任一漂移都会让 manual-fallback 手写 extension 的 agent 写出“脚本能过校验但漏 user_quote”或“guide 字段清单与脚本校验不一致”的令牌。
        - finding: 压缩后的 framework-adapters 指针只枚举 §A.1(Claude Code)/§A.6(kimi-code)/§A.7(dsh)，未列 opencode(§A.2，OCSR 后端)与 codex(§A.3，auditable-only)；而 SKILL.md M-11 宿主能力矩阵明确列出 opencode。宿主集合两处不一致。
          location: 本计划 SKILL.md 预算执行哲学注压缩句 vs refs/framework-adapters.md 索引(§A.2/§A.3)
          impact: 在默认 auditable-only 的 opencode/codex 上运行的 agent 依此枚举找不到自己的 tier 指引与 A.5 可移植性矩阵，宿主能力覆盖面被隐式缩小。
    - name: completeness
      status: concerns_found
      findings:
        - finding: refs/state-schema.md 删除 gate-ledger.jsonl 精确字段规格、_budget-state.json 内部字段、计数模型后，§预算 gate 只剩 agent 摘要 +「全量机器数据契约单一权威源 = scripts/budget_gate.py」一句。文件名为 state-schema 却在预算 gate 整段不再讲机器 schema。
          location: refs/state-schema.md §预算 gate（被删的 L386-420/L427-435/L476-499 与替换句）
          impact: 事件类型/字段/判定枚举（reserved/spawn_failed pre_execution/decision verdict/attempted_dispatch vs model_invocation/counts_before/ceilings）在 schema 文档中完全消失；新 agent 或工具在 doc 里 grep 字段名会 0 命中，只能翻 Python 源码。手册层理解预算行为的可发现性显著下降。
        - finding: 删除判据应用不对称：本 delta 删 [^totalcap] 脚注（63/62 推导、DEFAULTS+git 0137fce 调优历史），却保留同类的 [^mbr] 脚注（SKILL.md L450，max_blind_rechecks 原1→3、同样 DEFAULTS+git 单源）。
          location: SKILL.md [^mbr] L450（未改） vs [^totalcap] L452（删）
          impact: 针对“复算/调优历史引起漂移”的修复只做了一半；max_blind_rechecks 默认值一变，[^mbr] 会像旧的 63/62 一样静默过期。
    - name: maintainability
      status: concerns_found
      findings:
        - finding: SKILL.md L442 保留「普通=63 / ultraverge=62」为一行行为事实，只是删了推导。这正是本计划 L21 诊断出的“复述脚本得出值→漂移”根因，现在又把它留在最被 agent 读的配置表中。
          location: SKILL.md 配置参数表 max_total_reserved_spawns 行（L442）+ 验收#4 将其判定为允许残留
          impact: outer/mbr/total_safety 任一默认值调整后，63/62 会再次过期而公式与脚本仍正确；agent 顺手复述硬编码值即重演 42/44 vs 63/62 漂移。
        - finding: 预算 gate 的机器契约从“schema 文档”整体转移到“Python 源码作为编译权威源”，对新鲜 agent 意味着理解 gate 机制要先读代码（validate_integrity/_validate_event/计数函数），而非读面向人的字段契约。
          location: refs/state-schema.md §预算 gate 的替代句（单一权威源=budget_gate.py）
          impact: 自助排查 `FAIL_CLOSED:event_field:*` 或理解 summary 输出（attempted_dispatch/model_invocation 区别）的前置成本变高；错误消息兜底只在失败后生效，不支撑“先理解再操作”。
    - name: boundary_clarity
      status: concerns_found
      findings:
        - finding: budget_extension 的权威边界未收拢：脚本是机器校验权威、guide §六是作者基准、state-schema L437 是“校验细节（判断/作者基准，保留）”；三者对同一字段清单都有话要说，且 user_quote 明确“不指向脚本”，却没有一处写明“manual-fallback 照 guide，调试照脚本/state-schema”。
          location: guide §六 / state-schema L437 / budget_gate.py validate_extensions
          impact: 同一扩展令牌字段的“作者说 vs 校验说 vs 实现说”重叠，是文档/脚本职责最模糊的一处；正是 agent 出错率最高的路径。
        - finding: 文档/脚本边界反转：state-schema（名字即“schema”）对预算 gate 退居“摘要+指针”，而脚本成为真 schema；同时 agent 需读的 角色→consumes 摘要、quality-gate L82 指针、budget_gate L91 注释都在人工维护同一 ROLE_CONSUMES 的镜像。
          location: refs/state-schema.md §预算 gate 角色对照表 / refs/quality-gate.md L82 / scripts/budget_gate.py L91
          impact: “脚本单源”只对机器契约成立，对面向人的角色摘要并不单源——谁是权威、谁必须手工同步，仍不清晰。
    - name: residue_and_redundancy
      status: concerns_found
      findings:
        - finding: M-11 明确声明 hook-wiring 命令级细节“已单源至 claude-code §A.1 (#16 已落地)”，但 SKILL.md L348 仍整段保留 best-effort guarded 机制描述（cap 派生自 validated ceiling、deny、runaway 兜底、互不干扰不双计），与 §A.1 并行重复。
          location: SKILL.md L348 M-11 vs refs/framework-adapters/claude-code.md §A.1
          impact: 声明“已单源”与实际文本不符；两处同机制描述需同步，agent 重复读到机制，减负目标对 M-11 未真正达成，且本 delta 明确把它划出范围，残留在未来继续累积。
        - finding: 计划本体为保留可追溯性，塞入大量“原 L168/原 L454/原 L456”、逐轮 “评审处置记录”、“映射表现 10 行(历史)/当前表 8 行”、折叠进 row5 等迁移考古标注；行号锚点随执行迁移会陈旧。
          location: 20260826-doc-need-to-know.md 评审处置记录/改动范围/验收#2 等处
          impact: 一个以“减冗长”为目标的计划自身高度自引用且以行号定位，执行时行号漂移会让“原 Lxxx”失真；考古层与裁决信息混排，后续维护者需剥离历史快照才能看当前设计。
    - name: portability
      status: clean
      findings: []
    - name: scalability
      status: concerns_found
      findings:
        - finding: 角色→consumes 映射并存于脚本 ROLE_CONSUMES、state-schema 角色对照表摘要、quality-gate L82 指针文本、budget_gate L91 注释，以及 SKILL.md 相关引用；新增角色/scope 需多处手工同步。
          location: scripts/budget_gate.py ROLE_CONSUMES / state-schema 角色对照表 / quality-gate L82 / budget_gate L91
          impact: 框架/角色/scope 增多后，doc 面同步负担线性增长且漏改易发；好在此处有 fail-closed 兜底（未知角色→DENY:unknown_role，agent 会被脚本告知），因此同步更多是“发现性/可读性”而非“正确性”缺口，但仍是维护负担。
  highlights:
    - finding: 最关键的裂缝是“单一权威源”没有落实到预算扩展令牌这个最需要单源的路径——同一 budget_extension 记录在脚本(校验)、guide §六(作者基准)、state-schema L437(校验细节/判断保留)三处被描述，且 user_quote 被明确排除在脚本单源之外，authoritative 归属悬空。
      why_it_matters: 预算扩展是 manual-fallback 下 orchestrator 亲手写入、脚本 fail-closed 校验的核心动作；三处字段清单一漂移，agent 就会写出“脚本能过但缺 user_quote”或“guide 清单与脚本校验不一致”的令牌，而这正是治理阈值最不能出错之处；同时它暴露了“脚本单源”目前只对机器契约成立、对面向人的作者/校验契约并不成立。
      suggested_direction: 为 budget_extension 指定唯一“作者字段清单权威”（建议 guide §六），state-schema 与脚本只保留“校验视角”并明确“字段清单以 guide 为准”；把三处字段枚举收敛为“一处列举、两处指向”，并明确 user_quote 的人类可审计性质由哪一个文档正式兜底。同类还建议把 SKILL.md 中的硬编码 63/62 与 [^mbr] 调优历史一并改为“以脚本 DEFAULTS/公式为准”或标注 as-of 日期，否则会重演本计划要修复的数值漂移。
