设计需修订

# O6 material 增量复核 · 终局设计审查（ultraverge）

> 审查者：fresh 独立设计审查（单轮、只读；不进入 blocking→repair，不构成 converge blocking）。
> 对象：`plan.md` candidate-4（冻结字节，sha256 `d6525f44…`，46057 B）。
> 依据：`refs/design-review-prompt.md`（DR1-DR7）；`scripts/orchest.py:1089-1361`（材料门）；`scripts/archive_contract/model.py`；`scripts/budget_gate.py`；`tests/test_loop_a_coverage.py`。
> 纪律：事实已由双权威复核，本报告**不重复事实核对**，只评设计决策本身（架构落点、失败语义、约定、系统边界、兼容/回滚、可测性、实施顺序）。
> 说明：本报告与 converge 主 Reviewer 视角不同——主 Reviewer 问"是否匹配标准"，本报告问"标准/机制本身是否自洽、可持续、有无更简等价设计"。

---

## 0. 结论

**方向成立，但设计尚需收口，判 `设计需修订`。**

- **值得肯定**：三段式架构（decisional 全量双权威不变 + non-decisional 单 fresh delta + 链式回溯到最近 decisional）方向正确；落点集中在 `_validate_material_gate` 的三个不变量（T 块三重锚定、base/current hash 链、并集交集），职责边界（机械封"如实声明下的违规"、语义 diff 交 fresh reviewer）划分清楚，且对机械不可判的残余（A-11-14 / R-1 / R-2 / R-6）如实声明，不伪造机械闭环。这在设计伦理上是加分项。
- **必须收口**：独立审查发现 **6 项设计级问题（D1-D6）**，其中 D1（legacy 回退与 last-supersedes-all 的隐性冲突）、D2（fail-closed 错误码无单源）、D3（verdict 正向门的解析契约缺失）、D4（delta reviewer 输入契约未定义）触及正确性/可诊断性/安全论证，建议实施前解决。D5/D6 为便宜的自洽收口。
- 与既有 R3/blind 报告的关系：R3-1..R3-6、BR-01..BR-07 多为实现约束级；本报告在其之上追加**设计结构级**发现（尤其 D1、D4），并对其中若干项给出"是否设计级"的再定性（D2/D3/D6）。

---

## 1. DR 维度逐维结论

> 状态：`pass` = 无设计级问题；`issue` = 有设计级问题（细节见第 2 节）。

### DR1 一致性（Consistency）— **issue**
- **定义与词表自相矛盾**：§3.2:120 的 `decisional` 定义未列 `triggers`，但 §3.2:125-126 把 `triggers` 计入"前 8 项判定承载章节"。material trigger 变更（guide:23 的触发条件）显属判定承载，却不在定义内 → 交集 fail-safe 的锚点集合与"判定承载"叙述不一致（见 D5）。
- **Non-Goal 与 §3.5 冲突**：§8.4:339 声明"不改 `_find_material_block` 的 last-supersedes-all 语义"，但 §3.5:201-204 的 legacy 分支使当前段每个 legacy 块各自需要 full-pair，实际改变了"早块被末块取代"的语义（见 D1）。
- **验收与清单计数不一致**：A-11:319 写"A-11-1..A-11-13 全部被拦"，而 §11 表含 A-11-14（自认为机械不可判的语义残余）（见 D6）。
- **失败码风格不一致**：§3.5 内新码混用 `material-gate:` 前缀与裸码，kebab-case 与仓库既有 `snake_case:...`（budget_gate）/`kebab-case`（ArchiveError）两套并存（见 D2）。
- **角色口径宽窄不一**：§3.4:136"复用 outer-reviewer"vs §3.5:219`role ∈ REVIEWER_AUTHORITIES["fresh"]`（含 `reviewer/ultraverge-initial`）（R3-3，实现级）。

### DR2 完整性（Completeness）— **issue**
- **delta reviewer 输入契约缺位**：§3.4:141 要求 reviewer"实核前块 bytes → 本块 bytes 的增量"，但全文未规定 delta prompt 必须内嵌哪些输入；§3.4:142/§8.7:342/§10 R-2 只声明"不做机械绑定"。安全论证依赖一个未定义的接口（见 D4）。
- **revision 连续性不变量未成文**：delta 链隐含"non-decisional 块须与其 base 同 `revision_id`（同段）"，且"新段首块必 decisional"；后果是 reopen 后若唯一变更为 non-decisional，delta 路径不可用。计划未把该不变量写成显式限制（BR-03 的升级表述）。
- **delta 失败诊断未定义**：现有门把 `skipped` 原因聚合进错误消息（orchest:1305-1310）；新链对每个 T 块可能各自缺失候选，计划未要求指出"哪个块、缺哪类候选"，诊断粒度可能退化。
- **兼容性论证的覆盖缺口**：A-12/A-19 以现有 17 条测试为兼容证据，但现有测试的 material 块 `revision_id` 互异（`_setup_three_material_blocks` r2/r3/r4；`_setup_two_material_blocks_two_review_pairs` r2/r3），**不含"同段多 legacy 块"**这一被新语义改变的真实形态（见 D1）。故"既有测试不变"不等于"行为不变"。

### DR3 可维护性（Maintainability）— **issue**
- **12 词表双权威无等式校验**：代码常量单源声明在 `orchest.py`（§3.5:151 / F6），规范权威在 `refs/orchestrator-guide.md`（§12.4:427）。A-5/A-13 只做存在性/域与 diff 三态检查，缺"代码常量集合 == 文档 token 集合"的机械等式断言（round-3 的 F11 是人工比对，未固化为测试）。
- **两个"当前 revision"源并存**：材料门改用"末块所属段"（§3.5:157），而同一 finish 流程中的 `_validate_calibration_sample` 仍用 `_detect_revision_id`（orchest:1375）。二者语义不同，计划未说明谁权威、何时会不一致。
- **重构与静态断言的耦合**：现 `test_process_controller_contract.py:214-218` 以 `function_source("_validate_material_gate")` 断言函数体内含 `"metadata-only"`；若把候选收集抽成 helper，字面量可能移出该函数体。F6 已预期"调整"，但这是设计对测试写法的隐式依赖（实现陷阱）。
- 伪代码 `assert D`（§3.5:207）表达安全不变量不佳（`-O` 下剥离、抛非 FailClosed）；已被 BR-07 指出。

### DR4 职责边界（Boundary Clarity）— **issue（轻）**
- 宏观边界清晰（机械 vs 语义，§1:42 明示）。但 `changed_sections` 只表达"章节种类"，不表达"文件范围"：`doc-refs` 在普通文档里是 non-decisional，在 `CONSTITUTION.md` 第三部清单文件的**规范性句子**里必须是 decisional（§3.2:122）。同一 token 承载两种相反归类，机械层看不见文件路径 → `doc-refs` 的归类只能靠作者声明/reviewer 挑战，交集 guard 对此无效。属已承认残余（R-1/R-6）的边界，但 token 设计本身模糊，值得收口。

### DR5 残留与冗余（Residue & Redundancy）— **pass**
- `declared_class`、`["*"]` 哨兵、死分支"全 non-decisional 回退"均已清除（candidate-3/4 修订历史）。
- `_detect_revision_id` 保留但仍有真实调用方（calibration），非残留。
- 无过时文件/迁移考古措辞。

### DR6 可移植性（Portability）— **pass**
- 无新增环境硬编码；路径/角色沿用既有常量。
- 宿主外部权威源（`~/.config/opencode/memories.md` 的收敛裁决）被显式标注"非本仓库可验证"且不放松 §7 机械验收，披露得当。

### DR7 可扩展性（Scalability）— **issue（轻）**
- 链回溯 O(n)、词表为受控集合，规模无碍。
- 但"新增章节/级别需同时改代码单源与 guide"是已承认边界，却无等式测试兜底（同 DR3）；这是典型的双写漂移面（改一处忘改另一处）。

---

## 2. 必须在实施前修正的设计级问题清单（每条单选修法）

### D1（架构/兼容）legacy 回退与 last-supersedes-all 冲突，且兼容证据不覆盖
- **位置**：§3.5:201-204（`for j in legacy..end: require_full_pair`）、§3.1:116、§3.7:239、§8.4:339、A-12:320/A-19:327。
- **问题**：现门是 latest-supersedes-all——只校验**最后一个** material 块；candidate-4 在 legacy 分支要求 `legacy` 起**每个**块各自 full-pair。对"同一 revision 内多个 legacy 块"（真实形态：`done/20260910-process-controller-consolidation/attempts.md` 三块同 `revision_id=r2`、仅末候选有终局对）会因早块缺对而 `rc≠0`。但现有 17 条测试的块 `revision_id` 互异，不会触发该形态 → A-12/A-19 的"兼容"结论对该形态无效；§8.4 又声称保留该语义。
- **为何是设计问题**：这不是精度问题，而是"新门对一类真实合法历史数据比现门更严"的行为漂移，且计划的兼容性主张建立在未覆盖该形态的测试集上。任何逐块 full-pair 的要求都应能回答"末块 full-pair 已认证终局字节，为何还需早块自成对"——答案是否定的。
- **单选修法 A（Occam，推荐）**：legacy 分支简化为——若当前段存在任一 legacy 块（或缺失 anchors 的旧 decisional 块），**仅对当前段末块 `require_full_pair`**（等价于现状，且终局字节被末块 full-pair 认证，安全等价）；丢弃"自 legacy 起逐块 full-pair"。
- **单选修法 B**：保留逐块 full-pair，但显式承认它改写了 last-supersedes-all，删/改 §8.4 与 §13.4 的"旧数据无需迁移"表述，并新增"同段多 legacy 块仅末对"的正例/负例测试以证明这是**有意**更严。

### D2（失败语义/约定）fail-closed 错误码无单源、与仓库约定不齐
- **位置**：§3.5:147/177/179/185/188/222、§3.6:234、A-11:319；对照 `orchest.py:1883-1885`（`FAIL_CLOSED:{e.reason}`、exit 30）、`budget_gate.py:152-155`（`FailClosed(reason)`）。
- **问题**：新码混用 `FAIL_CLOSED:material-gate:first-block-must-be-decisional`（带前缀）、`FAIL_CLOSED:change-class-enum` / `sections-vocab` / `anchors-vocab`（裸码），kebab-case 与仓库既有码风格（`state_corrupt:` / `config_type:`、ArchiveError 的 `evidence-ref-missing`）并存；且未声明码如何经 `budget_gate.FailClosed` 映射到 `FAIL_CLOSED:<reason>` 与 exit 30，也未与既有 prose（"no qualifying pair"）协调。A-11 要求"指定错误码"却没有可依赖的码面。
- **单选修法 A（推荐）**：在 §3.5/§12 增"错误码表"单源，统一为 `<namespace>:<kebab-code>`（如 `material-gate:change-class-enum`），全部经 `budget_gate.FailClosed` 抛出 → 打印 `FAIL_CLOSED:material-gate:<code>`、exit 30；既有 prose 保留为 code 之外的人类摘要，A-11 断言前缀+码。
- **单选修法 B**：全部沿用现有 prose 风格，不引入结构化码，A-11 只断言 `rc!=0` + 关键子串。

### D3（失败语义/可测性）verdict 正向门的解析契约缺失
- **位置**：§3.5:198/220、A-9:317、A-11-9:379；对照现实现 `orchest.py:1343-1347`（`re.search(r"verdict:\s*(\S+)")` 取**首个**匹配）。
- **问题**：设计把"verdict 必须为 `可执行`"提升为安全门，但未规定解析契约。若实现沿用首个匹配，输出中前置/引号内的 `verdict: 可执行` 可覆盖真实阻断；A-11-9 只覆盖取值错误/缺失/变体，不覆盖"多次出现"。这使正向门的安全声明强于其解析保证。
- **单选修法 A（推荐）**：明文规定"输出中 `verdict:` 字面量**恰一次**；0 次或 ≥2 次 → `FAIL_CLOSED`"，并在校验前锚定（如仅取输出首块/首个 yaml fence 内）；新增 A-11-15 对抗用例。
- **单选修法 B**：明确 verdict 读取仅限输出 frontmatter/首块，并把"输出伪造"从"封死"表述中排除、计入 §10 残余。

### D4（系统边界/安全论证）delta reviewer 的输入契约未定义
- **位置**：§3.4:141-142、§8.7:342、§10 R-2:359、§12.5 item 7:435。
- **问题**：non-decisional 路径的全部语义价值在于"reviewer 实核了前块→本块的 diff"。计划只声明"不做 prompt 内 base 文本与 hash 的机械绑定"，却**未规范 prompt 至少要内嵌哪些输入**。缺最小输入契约时，不同执行器可供给不同上下文，reviewer 可能根本没见过 base，而流程在名义上完全合规——这会让新路径实质空转，且不能以"诚实残余"完全解释（残余是"不可机械验证"，不是"输入未定义"）。
- **单选修法 A（不扩机制，推荐）**：在 §3.4/§12.5 item 7 规范最小输入契约——delta prompt **必须内嵌链上前一有效块全文与当前 `plan.md` 全文**（或等价的 byte 级引用），仍不机械校验其 hash 绑定，残余如实声明。
- **单选修法 B**：引入 base 快照/`base_ref` 使门可复算绑定（触碰 §8.7，明确代价）。

### D5（约定/一致性）`triggers` 不在 `decisional` 定义却计入判定承载
- **位置**：§3.2:120（定义）vs §3.2:125-126（前 8 判定承载，含 `triggers`）、§12.4:426。
- **问题**：material trigger 变更（guide:23）属判定承载，却不在 `decisional` 定义内；交集 fail-safe 依赖 `decisional_anchors`，若作者按定义不把 `triggers` 视为 decisional，相关变更可被声明 non-decisional 且不被拦截。定义与词表自相矛盾。
- **单选修法 A（推荐）**：在 §3.2 定义与 §12.4 中补 `triggers`（material trigger 变更）。
- **单选修法 B**：把 `triggers` 移出"判定承载"集并同步 §3.2:126 与 A-10（需说明理由）。

### D6（可测性/一致性）A-11 声明与 §11 表体计数不一致
- **位置**：A-11:319 vs §11:384（A-11-14）。
- **问题**：A-11 写"A-11-1..A-11-13 全部被拦"，但表含 A-11-14（机械不可判的语义残余）。机械验收口径与清单不自洽。
- **单选修法 A（推荐）**：A-11 补一句"`A-11-14` 为语义残余，不计入 A-11"。
- **单选修法 B**：把 A-11-14 移出 §11 表，改述于 §10 R-1(b)。

---

## 3. 非阻断设计观察（可转实施约束清单）

- **N1｜两个"当前 revision"源**：材料门用末块 `revision_id`（§3.5:157），calibration 用 `_detect_revision_id`（orchest:1375）。建议注明二者关系，或统一单源，避免未来 reopen 场景出现"材料门认 r3、calibration 认 r2"的解释分裂。
- **N2｜词表双写**：建议把 round-3 的人工 F11 固化为测试——断言代码常量集合恰等于 `orchestrator-guide.md` 的 12 项 token 集合（同时覆盖 DR3/DR7 的漂移面）。
- **N3｜F8 untracked（R3-2）**：`docs/plans/active/20260911-converge-operational-envelope.md` 在 HEAD 下未跟踪，致 §13.3 回滚命令失效、A-14 对 F8 不可判定。落地前 `git add`/备份，并把 A-14 的 F8 判据改为内容型。
- **N4｜角色口径（R3-3）**：统一 delta reviewer 为 `outer-reviewer`，或 §3.4 改述"复用 fresh 权威集合（推荐 outer-reviewer）"。
- **N5｜A-5 判定偏软 / A-19 符号（R3-4/R3-1）**：A-5 的"grep change_class 命中缺省"写死为对 `b.get("change_class","decisional")` 形态的静态断言；A-19 第 10 条补 `_fails` 后缀。
- **N6｜回滚分组语义**：§13.1（代码+测试）与 §13.2（规范）各自单独回滚都会留下 code/规范不一致（规范描述不存在的 `delta`，或代码违背规范）。建议显式声明为**原子语义组**，不可只执行其中一条。
- **N7｜滥用面的诚实边界**：A-10/A-11-4 只拦"如实声明下的误标"——谎报者只要**漏报** `changed_sections`（不含决策章节 token）即可绕过交集；§11 注与 §10 R-1 已如实承认，但 A-11 的"全部被拦"措辞应限定 scope，避免被读成"机械闭环"。

---

## 4. highlights（最值得警惕 / 最值得肯定）

1. **[最值得警惕·安全论证]** delta reviewer 的**输入契约缺位**（D4）。新路径把"增量复核"的安全责任交给 reviewer，却没规定 prompt 必须给它看什么。这不是精度问题：若 reviewer 只见当前 `plan.md`，`base_plan_sha256` 只是两个数字，"实核 diff"无从谈起，而门会照样通过。**若不处理，未来可能发生**：non-decisional 路径成为事实上的"无复核直通"，O6 的成本收益以削弱 material 门为代价。**方向**：至少规范 prompt 的最小内嵌内容（base+current），机械绑定可继续声明为残余。

2. **[最值得警惕·架构/兼容]** legacy 分支与 last-supersedes-all 的**隐性冲突 + 兼容证据缺口**（D1）。"现有测试不变"被用作兼容论据，但测试集的块 `revision_id` 互异，恰好绕开了被新语义改变的形态。**若不处理，未来可能发生**：某对象在机制落地时累积了同段多 legacy 块，finish 突然 `rc≠0`，且被误诊为数据损坏。**方向**：若不需要早块自成对，直接简化为"仅末块 full-pair"（Occam 等价安全）。

3. **[最值得警惕·可诊断性]** fail-closed 的**错误码无单源 + verdict 解析契约缺失**（D2/D3）。安全门若不能被稳定解读，就无法稳定验收；`re.search` 取首个 `verdict:` 的隐患是"正向门"名不副实。**方向**：统一 `<namespace>:<code>` 并经 `FailClosed`→exit 30，verdict 行规定"恰一次"。

4. **[最值得肯定]** **T 块三重锚定 + base/current hash 链 + 并集交集 + 正向 verdict** 是干净、机械可判的落点，且计划对机械不可判处（锚点低报、diff 供给、归类挑战）如实声明、不伪造机械闭环。`_find_material_block` 语义保持、legacy 纯增量、回滚无需数据迁移，都是对的方向。

5. **[值得收口·便宜]** 定义自洽的两处小洞：`triggers` 漏列（D5）与 A-11/A-11-14 计数（D6）。二者修复成本极低，但漏了会让"判定承载"的锚点语义与验收口径都可被质疑，间接削弱交集 fail-safe 的可解释性。

---

## 5. 审查纪律声明

- 本报告为单轮咨询式设计审查，**不给出对 converge verdict 的否决**，findings 不自动进入 blocking→repair。
- 事实层面（行号/字节/sha/pytest 计数/事件存在性）由双权威已复核，本报告未重复核对，仅引用其结论作为设计推理的输入。
- 修复方案以"方向 + 单选修法"给出，具体落地由 author/executor 与用户决策。
