design_review:
  dimensions:
    - name: consistency
      status: concerns_found
      findings:
        - finding: |
            计划同时把归档后的 manifest 定义为“冻结事实索引、v1 长期权威”，又要求 check 从 sidecar、canonical records 和 ledger 重新构建规范对象并与 manifest 做语义比较。这样一来，sidecar、ledger 和 canonical records 在归档后仍然参与裁定事实，manifest 更像签名不足的物化视图，而不是唯一事实源。若不明确逐字段所有权，后续维护者会在“修 manifest”与“修来源记录”之间作出不同选择。
          location: "plan.md §4 单一权威、派生规则与哈希覆盖闭包；§5 Invocation lifecycle、ledger 绑定与模型 provenance"
          impact: "权威边界名义上单一、实际上多源互证；新增字段或修复异常时容易产生循环校验、冲突裁决和兼容行为不一致。"
        - finding: |
            invocation sidecar 被称为 append-only，但 complete-invocation 又会把 started sidecar 原子更新为 terminal。这里混合了“不可覆盖事件流”和“可变状态快照”两种模型，导致恢复、并发和审计语义不够自洽。
          location: "plan.md §4 权威生命周期第 1 点；§5 lifecycle 第 1-3 点"
          impact: "实现者可能选择原地覆盖或追加新版本，两者会产生不同的哈希闭包、崩溃恢复和历史可见性。"
        - finding: |
            reopen 要求保留旧 manifest/INDEX 作为 revision history evidence，但 v1 目录树只定义 invocations 与 artifacts 两类 evidence，根级 allowlist 又只允许一份 manifest.json 和 INDEX.md。旧 revision 的物理位置、命名、manifest 承诺方式和 INDEX 派生规则没有落到同一结构中。
          location: "plan.md §3 v1 目录与根级 allowlist；§8 reopen"
          impact: "修订功能会迫使实现临时发明第三类 evidence 或突破 allowlist，使自举校验与 revision history 互相冲突。"
    - name: completeness
      status: concerns_found
      findings:
        - finding: |
            terminal decision 与 design-review-completion 被定义为独立事件类型并要求可解析引用，但目录结构和采集生命周期没有明确这些事件存放在哪个文件、由哪个命令创建、是否具有 sequence，以及如何进入 manifest。它们既不像模型 invocation，也不完全属于 budget ledger。
          location: "plan.md §4 final_verdict_ref；§5 terminal decision 与 design-review-completion"
          impact: "最关键的最终结论链在概念上闭合，却缺少明确的持久化边界；实现时容易把事件塞入 manifest、round 或 sidecar，重新制造多源权威。"
        - finding: |
            archive 的提交状态转换仍有一个未落定的持久化点：done 路径 post-check 成功后才“写/确认 archived terminal state”。若该状态位于 manifest 或其他被哈希的 canonical record，写入会使刚完成的 check 过期；若位于 journal，则 journal 的位置、哈希覆盖和最终保留策略尚未定义。
          location: "plan.md §8 archive 步骤 3-5"
          impact: "崩溃恢复最需要确定性的时刻仍存在状态落点歧义，可能出现目录内容有效但状态未确认，或状态已确认但闭包未重新验证。"
        - finding: |
            “30 秒内定位结论”的目标没有对应的审计旅程验收。测试覆盖完整性、篡改、路径和故障很多，但没有验证一个不了解内部 schema 的审计者能否从 scan/check 输出迅速理解失败原因、证据降级、revision 时间线和下一步阅读路径。
          location: "plan.md §1 目标；§10 自动化与对抗验证"
          impact: "新归档很可能显著更严格，却未被证明更易审计；合规性提升可能伴随人工解释成本上升。"
    - name: maintainability
      status: concerns_found
      findings:
        - finding: |
            单一 archive 命令作为用户入口是清晰的，但单个 scripts/archive_convergence.py 被要求同时承担 schema、canonical JSON、路径安全、哈希、证据采集、ledger validator、Markdown/anchor 验证、锁、journal、原子提交、reopen、scan 和 INDEX 生成。计划提到“共享原语”，文件清单却没有给这些原语独立的模块边界。
          location: "plan.md §8-§9；§12 文件改动清单"
          impact: "stdlib 依赖本身不是问题，单文件中的高耦合职责才是问题；安全修复、schema 演进和 CLI UX 变化会互相牵动，测试也更难按不变量分层。"
        - finding: |
            schema 单源被放在 Markdown 文档中，而运行时 validator、INDEX renderer、bootstrap importer、hooks 和 backend adapter 都要消费相同枚举与关系。计划没有说明如何避免这些消费者各自手工抄录规范。
          location: "plan.md §11 流程与文档接线"
          impact: "state-schema 虽是规范单源，却可能不是可执行单源；字段演进时容易出现文档正确但不同消费者实现不同步。"
    - name: boundary_clarity
      status: concerns_found
      findings:
        - finding: |
            CLI 同时处于三层职责：调用前后的宿主适配记录器、归档事务协调器、以及事后审计验证器。尤其 begin/complete 需要宿主 receipt 与 budget settlement，archive 又负责解释 canonical round/retrospective，check 还裁定 Markdown 导航。各命令共享数据是合理的，但“谁负责产生事实、谁只验证事实、谁负责展示事实”尚未形成清楚的模块边界。
          location: "plan.md §5、§8、§9"
          impact: "后端适配逻辑可能渗入核心 schema，展示需求可能反向改变安全闭包；一个 stdlib CLI 会从薄编排层逐渐变成整个 converge 的第二个 Orchestrator。"
        - finding: |
            budget ledger、invocation sidecar、round/retrospective 与 manifest 都保存部分重叠关联。计划规定双向一致，却没有字段级 ownership matrix，例如 terminal status、role/phase/round、final verdict、settlement status 分别由哪一份记录拥有，其他记录应保存副本、引用还是纯派生值。
          location: "plan.md §4-§5"
          impact: "交叉引用越完整，维护成本未必越低；没有 ownership matrix 时，每增加一种角色或终止路径都需要猜测冲突优先级。"
    - name: residue_and_redundancy
      status: concerns_found
      findings:
        - finding: |
            计划有意保留根级 canonical 摘要、invocation raw evidence、旧 revision manifest/INDEX 和 ledger，这些层次各有审计价值，但旧 INDEX 本身是由旧 manifest 唯一派生的。把每个 revision 的派生 INDEX 也永久保存，会扩大重复内容和闭包规则，而没有说明其独立证据价值是否高于按旧 manifest 重建。
          location: "plan.md §3-§4；§8 reopen"
          impact: "revision 增长后会积累事实、物化视图和原始证据三套历史；未来清理或迁移时难以判断哪些字节必须永久保留。"
        - finding: |
            bootstrap importer 负责把多种历史命名文件迁入 evidence，但 v1 又明确不自动迁移旧 done 历史。两条边界并不直接冲突，却容易让维护者误以为 importer 是通用 migration framework；其适用范围目前主要靠本次 active fixture 和文件名清单表达。
          location: "plan.md §2 非目标；§3 bootstrap importer；§10 fixture"
          impact: "临时兼容逻辑可能长期留在核心 archive 路径，并随着更多遗留命名不断膨胀。"
    - name: portability
      status: concerns_found
      findings:
        - finding: |
            设计诚实拒绝跨卷、UNC、extended-length path、reparse point 等难以统一保证的场景，这是可接受的安全收缩；但 owner-dead 锁恢复、PID 身份、file identity、fsync 目录语义、原子 rename 与权限收紧在 Python stdlib 和不同 OS 上并没有等价能力。当前只笼统规定 fail closed 或 capability degradation，尚未定义各能力的最低可用矩阵。
          location: "plan.md §6 安全策略；§8 并发与恢复；§9 CLI 边界"
          impact: "同一归档在 Windows、Linux 和受限文件系统上可能获得不同的可恢复性保证，而用户只能看到零散 skip/degradation，难以判断何种环境具备完整事务语义。"
        - finding: |
            根级名称采用大小写无关唯一键是一种跨平台保守策略，但它把 Windows 文件系统限制提升为所有平台的 archive contract；同时拒绝 \\?\ 路径可能使 Windows 长路径测试与真实大目录支持存在张力。
          location: "plan.md §3 allowlist；§6 路径策略；§10 Windows 测试"
          impact: "可移植性通过取最小公分母获得，边界是清楚的方向但需要显式声明为格式约束，而不是让用户误认为是底层平台的自然限制。"
    - name: scalability
      status: concerns_found
      findings:
        - finding: |
            check 每次需要验证精确树集合、重算文件哈希、重建 INDEX、严格重放 ledger 并检查 Markdown anchors；pre-push 又会对变更的 v1 done 调用 check。对 invocation、revision 和 exact snapshot 数量增长后的复杂度、增量策略及可接受耗时没有预算。
          location: "plan.md §4 check 闭包；§8 pre-push；§10 测试"
          impact: "小型自举 fixture 可能表现良好，但大型或多 revision 归档会让日常 pre-push 与审计验证线性读取大量字节，促使用户绕过检查。"
        - finding: |
            闭合枚举、固定根 allowlist、精确目录树和多消费者交叉验证强化了 v1，但每增加 backend、角色、event type、evidence 类别或 schema minor 都需要同步修改 schema、CLI、INDEX、importer、hooks、adapter 和 fixtures。计划只描述未来 v2 reader/upgrade，没有给扩展点分层。
          location: "plan.md §3-§7；§11"
          impact: "系统能安全拒绝未知内容，却未必能低成本吸收已知的新能力；扩展压力可能导致频繁 major revision 或在现有枚举中塞入含混 escape。"
  highlights:
    - finding: |
        “单一 archive 命令”是好的操作界面，但当前计划把调用采集、schema/ledger 校验、文件系统事务、证据复制、导航生成和审计展示都压进一个 stdlib 脚本，缺少内部职责分层。
      why_it_matters: |
        这会让最敏感的路径安全与恢复逻辑和频繁变化的 adapter、schema、INDEX UX 共同演进；单入口最终可能演变成难以审查的单体实现。
      suggested_direction: |
        保留一个 CLI façade，同时先定义少量稳定的内部边界：事实采集、规范模型/验证、归档事务、只读呈现；是否拆文件可以由实现决定，但依赖方向和不变量应先明确。
    - finding: |
        manifest、invocation sidecar、budget ledger、round/retrospective 之间目前是“全部互相闭合”，却还不是“每类事实只有一个明确 owner”；manifest 的长期权威说法与从来源记录重建它的 check 语义尤其紧张。
      why_it_matters: |
        没有逐字段权威边界时，更多交叉引用会增加冲突组合，而不是自动提高可维护性；revision、恢复和 schema 演进都会放大这个问题。
      suggested_direction: |
        建立字段级 ownership/projection matrix：明确每项事实的唯一产生者、不可变记录、派生副本和冲突处置，并据此重新命名 manifest 的角色；同时补齐 terminal decision 与 revision history 的物理落点。
    - finding: |
        计划充分证明“归档能被严格拒绝”，但尚未证明“审计者更容易完成工作”。30 秒 INDEX 目标没有覆盖 scan/check 失败解释、证据降级、revision 时间线和下一步动作的用户旅程验收。
      why_it_matters: |
        如果新机制只提高写入门槛与错误数量，审计仍需要理解内部 schema 或请实现者解释，最终会诱发绕过、手工修档或停留在 legacy-unverifiable。
      suggested_direction: |
        把审计便利性作为独立 contract：定义无内部知识审计者的最短路径、INDEX 必显信息、稳定诊断格式和 revision/degradation 摘要，并用端到端审计场景而非仅结构测试验收。
