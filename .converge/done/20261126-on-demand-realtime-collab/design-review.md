```yaml
design_review:
  reads:
    - docs/plans/active/20261126-on-demand-realtime-collab.md
    - refs/design-review-prompt.md
    - CONSTITUTION.md
    - SKILL.md
    - refs/orchestrator-guide.md
  dimensions:
    - name: consistency
      status: concerns_found
      findings:
        - finding: |
            方案将已归档 retrospective.md 定为落地审计权威，允许直接追加且无需 reopen，同时允许在 plan frontmatter 中镜像。现行指南将 finish、归档后检查和 reopen 都放进有 manifest 的生命周期。方案没有交代落地追加和镜像分别属于哪一个完整性域，也没有交代归档后校验如何看待这些写入。
          location: "方案 §4 编辑点 3、5.3、5.6；SKILL.md L251、L416、L495；refs/orchestrator-guide.md L7–15、L43–45"
          impact: "若这些文件属于 manifest 校验范围，落地可以成功而归档校验随后失败。若允许追加，复核者仍需要知道哪些字节属于已封存决策、哪些属于归档后证据。限定输入未包含归档实现，实际校验行为待核。"
        - finding: |
            方案把手工传话限定于已归档的 slug，保留振荡裁判写入原 gate ledger，却只明确落地执行方的门控豁免。归档流程要求先结清调用、完成终局再封存，方案未说明归档后由哪个预算生命周期接收裁判调用及其 settlement。
          location: "方案 §4 编辑点 4、5.7；SKILL.md L251、M-11；refs/orchestrator-guide.md L7–11"
          impact: "手工传话达到裁判触发点时，不同编排器可能跳过裁判、尝试使用已封存的 gate，或产生归属不明的消费记录。"
    - name: completeness
      status: concerns_found
      findings:
        - finding: |
            方案写明宿主能力缺失时回退，也允许发现无效循环时回退，但没有规定已经启动且部分写入后的交接。缺少对旧执行方停止写入、未提交改动或分散提交的接管，以及接任范围和验收基线的约定。
          location: "方案 §4 编辑点 1、4、5.6；refs/orchestrator-guide.md §八"
          impact: "宿主半途故障或协同被中止时，新旧执行方可能同时修改同一文件，接任者也可能重复应用或遗漏已有改动，最终难以重建清单核对所用的改动范围。"
    - name: maintainability
      status: concerns_found
      findings:
        - finding: |
            载体准入已有单一权威定义，执行留痕的字段、核验强度和追加规则却在 C-21(c)、脚本化映射和执行标识留痕三处各自完整定义。验收依赖三处人工逐字同步。
          location: "方案 §4 编辑点 3、5.3、5.6；§5 第 2 项；CONSTITUTION.md §一 Occam"
          impact: "新增证据字段或调整归档边界时，维护者要同时更新三处。局部漂移会让宿主迁移、异常交接和复盘使用不同口径。"
    - name: boundary_clarity
      status: concerns_found
      findings:
        - finding: |
            协作会话标识、成员标识和所选方式可以客观记录会话与人员，但条文赋予它们证明实际变更归属、排除 Orchestrator 代改的语义。方案未要求将文件操作或提交与实际执行身份绑定。类似地，单次 Spawn 的 instance_id 可以佐证启动，fresh 上下文还依赖启动调用本身的语义。
          location: "方案 §4 编辑点 3、5.3、5.6；CONSTITUTION.md §二 #7"
          impact: "宿主记录了真实执行成员时，同一工作树仍可能由其他参与者写入。复盘容易据成员清单得出超出证据覆盖范围的责任结论。"
        - finding: |
            独立审查的角色枚举覆盖了收敛后设计审查，且共享板被排除在 gate ingest 之外。功能规则主要限制直接共用会话，未明确持续执行成员能否换新会话接任独立验收，也未限定通过摘要、转录或宿主自动注入把协作历史传入独立审查。按需提供审查产物与传入形成共识的过程信息，在这里需要不同的输入边界。
          location: "方案 §4 编辑点 1、4；refs/design-review-prompt.md L43–56"
          impact: "即使会话和消息板 ID 分开，审查方仍可能继承对方案结论的先验承诺或并行审查意见，削弱独立性。"
    - name: residue_and_redundancy
      status: clean
      findings: []
    - name: portability
      status: concerns_found
      findings:
        - finding: |
            宿主协议交给宿主文档，有利于保持核心框架无关，但准入只说宿主具备原生实时协同能力，没有界定哪些能力缺失等同于仅部分支持。例如宿主可以提供共享板却无法导出稳定成员标识，或自动恢复会话时无法约束历史注入。
          location: "方案 §4 编辑点 1、4、5.3；CONSTITUTION.md §三对适配层的定位"
          impact: "同样宣称支持实时协作的宿主可能具备不同的审计和隔离能力。没有最小能力口径时，编排器对启用还是回退会做出不一致的选择。"
    - name: scalability
      status: concerns_found
      findings:
        - finding: |
            新载体服务于多 Executor 强耦合落地，但保留按 N = M 宣告完成的规则，并允许 diff/计数满足强耦合场景的最低验收形态。变更集合的基数无法识别同数换项，也无法覆盖计划内多个编辑点集中在同一文件或多个正确局部变更合并后接口失配。
          location: "方案 §3 文件改动清单、§4 编辑点 4、5.4、5.6；refs/orchestrator-guide.md L422–429"
          impact: "参与者和变更数增多后，遗漏计划文件与误改额外文件可以相互抵消。即使路径全部命中，跨文件集成仍可能失败而清单计数相等。"
  highlights:
    - finding: |
        归档后落地留痕与收敛档案的完整性边界未定义，手工传话裁判也缺少归档后的记账归属。
      why_it_matters: |
        追加留痕与记账是日常动作。归属不清会让复盘难以判断档案是合法扩充、校验失配，还是调用未被完整记录。
      suggested_direction: |
        明确归档封存的完整性边界，以及落地证据和续生账目的权威载体与校验方式。覆盖一次归档后落地及一次达到裁判触发点的验证场景。
    - finding: |
        会话和参与者标识被赋予超出其覆盖范围的改动归属证明。
      why_it_matters: |
        会话里有独立执行成员，并不能推出目标文件由该成员写入。角色分离在复盘时需要可以核验的证据。
      suggested_direction: |
        按启动、参与、写入归属和上下文隔离明确证据强度，并将所需的最低证据能力纳入宿主启用与回退判断。
    - finding: |
        多执行方落地的回退与验收缺少共同的变更基线。
      why_it_matters: |
        部分成功后切换执行方最容易丢失责任归属、已有改动和接口验证结果，清单总数相同也可能掩盖错误。
      suggested_direction: |
        界定交接时的写入所有权与验收基线，按计划路径集合核对覆盖，并用合并后的接口验收验证强耦合变更。
```

审查范围说明：DR5 在本次拟议变更范围内无新增清理项。计划注明的旧锚点属于已知存量，留痕规则的重复维护风险见 DR3。目录实际状态、忽略规则、脚本实现和宿主能力均未纳入本次读取范围。报告为单轮咨询意见。
