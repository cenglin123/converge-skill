# Design Review · 20260610-skill-slimming-plan-ultraverge

> 强制设计审查（ultraverge 路径）。单轮、咨询式、不阻断。
> Reviewer instance: a0b63c6d7f8d7671c（fresh context）。
> 事实层复核：计划全部声明对照实文件核实无误（含 orchestrator-guide 5 处引用、C1 映射算术、F4 三缺陷；计划 241 行，SKILL.md 468 行）。

## Reviewer 完整输出

```yaml
design_review:
  dimensions:
    - name: consistency
      status: concerns_found
      findings:
        - finding: |
            事实层全部核实无误。但"零语义变更"承诺被计划自身定义了三处豁免：frontmatter 例外（C2/§五.3）、
            ASCII 对齐空白不计入（C2/§五.3）、触发语义标注"不计入语义变更"（§五.2）。每处豁免单独看都有理，
            但累积起来，"零语义变更"已不是一个事实判断，而是一套由计划自己立法、自己解释的测量规则。
          location: "C1/C2/§五.2/§五.3"
          impact: |
            验收 Reviewer 验证的是"是否符合计划的法条"而非"SKILL 是否变好了"。豁免清单本身成为未来争议点：
            下一次修宪若援引本计划为先例，豁免边界需要重新谈判。
    - name: completeness
      status: concerns_found
      findings:
        - finding: |
            §四 三项运维行动没有任何跟踪机制。"状态"清单只覆盖 ultraverge 程序五步，不含运维行动；
            计划归档后，F6 指出的"distill 循环从未运行"问题失去唯一的载体。
          location: "§四 + 文末状态清单"
          impact: |
            F6 的诊断（compiled 产物纯重量零收益）会原样持续。运维行动正是本计划中唯一能产生实证数据的部分，
            却是唯一没有验收和留痕设计的部分。
        - finding: |
            "改动前基线快照"未锚定。仓库是 git 仓库（当前 HEAD ec97a65），计划没有记录基线 commit hash。
          location: "§三执行注记"
          impact: "一行 hash 即可消除的歧义，留给了未来执行 agent 的判断。"
        - finding: |
            失败路径不成比例：§五.1 硬标准的预算推演是 -2~+3 行——计划自己预测有相当概率落在失败侧；
            而唯一的失败处置是最重通道（整体不提交、退回修订 = 重走 ultraverge），且未规定单项微差失败
            是否允许轻量复审。
          location: "§五.1 + 改动范围声明（原子性与回滚）"
          impact: |
            执行 agent 在 +1 行边缘时的理性选择是用格式技巧硬挤行数，而不是承认 +1 行并退回——
            硬门反而激励了对指标的操纵。
    - name: maintainability
      status: concerns_found
      findings:
        - finding: |
            C1 的"编号保持约束"将在 SKILL.md 中永久固化一份组内乱序的编号清单。冻结编号是绕开脆弱耦合
            （orchestrator-guide 按全局编号引用）而非解决它。计划没有定义扩展规则：未来新增职责 #19 进哪一组？
            任何未来重编号需要同时动一份宪法保护的 refs 文件，修宪成本被进一步抬高。
          location: "C1 编号保持约束"
          impact: |
            可读性（乱序编号）为耦合让路，且该耦合的清偿被无限期推迟。第二次修宪若想理顺编号，成本比这次更高。
    - name: boundary_clarity
      status: concerns_found
      findings:
        - finding: |
            "计划退回修订"之后的程序边界是灰色地带：是从第四部第 1 步重新开始，还是允许在原收敛基础上增量复审？
            计划与宪法第四部都未规定。
          location: "改动范围声明 + CONSTITUTION.md 第四部"
          impact: "结合 F7（程序摩擦诱发绕过），失败路径成本未定义恰恰是最容易诱发绕过的位置。"
    - name: residue_and_redundancy
      status: concerns_found
      findings:
        - finding: |
            同一约束在 F 条目、C 条目、§五 验收项三层重复陈述（frontmatter 豁免三处；18 条零删除三处；
            产物要求逐行保留两处）。这是收敛多轮修补的痕迹——每轮发现一处歧义，修复就在三层各加一句对齐。
            与 SKILL 自己的 Occam 原则相悖。
          location: "全文 F/C/§五 三层结构"
          impact: "下次按此范式写修宪计划时，三层同步成本会复现。§一的 /goal 考证作为评审记录合法，无问题。"
    - name: portability
      status: clean
      findings: []
    - name: scalability
      status: concerns_found
      findings:
        - finding: |
            frontmatter 豁免的通用性边界被明确承认并给出理由——这点处理得好。但计划范式整体的可扩展性存疑：
            241 行计划 + 8 条字面化验收 + 约 11 处加粗执行约束，换取约 10 行净减与零语义变更。
            F7 提议将本案记入 retrospective 作为"程序可负担"的实证——而本案的真实数据更像反证：
            修改/计划重量比约 1:24。
          location: "F7 + 全文"
          impact: |
            若 retrospective 只记"打包摊薄成本"的结论而不记重量比，会把一个高摩擦先例固化为"可负担"的证据，
            后续修宪按此范式只会更重。
  highlights:
    - finding: |
        计划的重量已超过它要削减的重量，且重量增长机制与 F1 诊断的 SKILL 病因同构。F1 说"清单越长，
        遵循概率越低"；本计划经三轮 Reviewer 收敛后膨胀为 241 行、三层重复陈述、三处自定义豁免——
        每轮对抗审查的修复方式都是"再加一条约束"，这正是 converge 流程作用于文本类产物时的系统性倾向
        （防御性条款单调增长）。计划没有意识到自己是这个病的标本。
      why_it_matters: |
        如果按 F7 的提议把本案记为"程序可负担"的正面实证，会把 24:1 的重量比固化为修宪范式基准。
        后续每次修宪都按此范式执行，F7 风险不会缓解而会加剧。
      suggested_direction: |
        执行本计划时如实记录重量比与各轮约束增量到 retrospective，作为中性数据而非正面案例；
        并考虑让未来的修宪计划范式区分"语义变更类"与"纯格式类"改动的计划详尽度要求
        （后者或许只需要映射表 + 验收清单，不需要 F/C/§五 三层）。
    - finding: |
        §五.1 硬标准（总行数不增加）是一个预测余量横跨失败线（-2~+3）的硬门，其失败处置是最重通道，
        而其调节手段是格式技巧。行数是"重量"的代理指标，但 F1 的真实问题是注意力衰减——为省 2 行
        而把分组标签挤成行内加粗，可能恰恰损害分组本来要提供的可扫描性。指标在边缘处与目标反向。
      why_it_matters: |
        执行 agent 在 +1 行边缘的理性行为是操纵排版凑数，验收 Reviewer 数行数通过——程序合规但产物变差，
        且 8 条验收标准全部测量文本守恒与行数，没有一条测量可读性或遵循性。
      suggested_direction: |
        考虑把行数从硬门降为带容差的软指标（如"不增加超过 N 行"），或在验收中加一条方向性判断
        （fresh reviewer 盲评：分组版是否比平铺版更易定位本轮应做项）。留给用户决策硬门是否值得保留。
    - finding: |
        "零删除、零语义变更"使 C1 只能重排信息，而计划没有任何机制验证重排是否真的改善了 F1 诊断的问题
        （Orchestrator 遵循率），也没有为"18 条本身可能存在可合并冗余"（如 #15/#16/#17 三条门控项）
        留下后续钩子。§四.1 的"积累实证"与 C1 的效果验证之间没有连线。
      why_it_matters: |
        最好情形：分组有效，问题缓解，无人知道是否该做真正的删减。最坏情形：分组无效，
        而下一次修宪因 F7 摩擦永远不来——计划精心优化了一个未经验证的中间目标。
      suggested_direction: |
        在 §四 运维行动中显式挂接 C1 效果观察（后续 3-5 次收敛的 retrospective 中记录
        "条件触发组条目是否被正确跳过/执行"），并在计划中承认本次是"重排优先、删减待实证"的
        两步走第一步，给第二步留下触发条件。
```

## 处置状态

- 发现不进入 blocking 管道（协议规定）。
- highlights 已报告用户，**用户决策待录**——录入后追加至 retrospective.md §11。
