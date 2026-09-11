# Advisory Design Review

本报告为收敛后单轮咨询式审查，不给出 verdict，也不重开收敛。

## DR1-DR7

| 维度 | 状态 | 发现 |
|---|---|---|
| DR1 Consistency | concerns_found | D3 同时要求“active state 创建后权威”与“standard state 不写冗余默认值”。当前 `cfg()` 对缺失键回退到代码 `DEFAULTS`，因此跨版本恢复会随默认值变化；这与权威性和冲突 fail-closed 的承诺不一致。D4 的四 profile 表称输出“精确”，但 Small 两行未列出其出生档案 `docs/initialization.md`，与“记录 Git/no-Git 和规模”及后文双出生档案验收不一致。 |
| DR2 Completeness | concerns_found | v1 spec 迁移已定义，但现存 `.loop-journal.json` 的 `inner_streak` 到 `executor_repair_streak` 没有迁移或拒绝策略。另需定义 v2 phase 拓扑约束：parallel/blind repair 只有在后续可达 fresh outer Reviewer 时，才能兑现“每次修改后独立复查”。 |
| DR3 Maintainability | concerns_found | 四种 profile 需要跨大量模板和脚本手工投影，同时明确不引入 renderer。静态测试和手工构造 fixture 可以证明文本与脚本局部性质，却不能证明初始化 Agent 实际生成了同一套 profile；若期望集、模板条件和 SKILL 表分别维护，会形成三份事实源。 |
| DR4 Boundary Clarity | clean | D1 的五实体权限表清楚地区分顶层控制、Executor-local 方法和领域交接；Converge 仅在被选择时拥有控制权，生成项目不被迫安装或引用 Converge。Reviewer Continue 与 driver fresh Executor retry 也已按事件、配置和验证责任分开。 |
| DR5 Residue & Redundancy | concerns_found | 删除 bespoke controller 的方向正确。同步合同仍缺少稳定的机器可读声明语法：`check_all.py` 要按 AGENTS 中声明的模式检查，而 hooks 又只指回该声明；若实现通过自由文本或命令片段猜测模式，会重新引入重复解析和漂移。 |
| DR6 Portability | clean | Git/no-Git、不同 upstream/branch、Windows 临时路径和 hardlink 可用性边界均被承认，且未向目标项目上游 OA、用户名或本机路径。绝对路径仅用于本次计划定位和验证前置条件。 |
| DR7 Scalability | concerns_found | 小预算加显式 extension 是合理的成本优先边界，但 standard `blind=1` 只足以发现一次问题，不能覆盖“发现 -> 修复 -> 再盲审”；当 outer 已用满 3 轮时还会同时需要 outer 扩容。该取舍应以扩容频率和盲审发现率验证，而不应被表述为完整修复周期预算。Profile 组合增长也会放大手工投影漂移。 |

## Highlights

1. **Sparse state cannot be authoritative across versions.** 只保存显式 override、其余键动态读取 `DEFAULTS`，意味着活动流程在升级后会静默改变有效预算。建议方向：让创建时的有效预算具备可识别的版本或不可变快照，或在旧 sparse state 恢复时明确 fail closed；不要仅依赖“升级前先完成”的人工纪律。
2. **Exact profiles need one authoritative projection contract.** Small profile 漏列出生档案只是当前可见症状；更深层代价是 SKILL 表、模板条件、fixture 期望集和出生记录可能分别漂移。建议方向：在不新增控制器的前提下，明确一个现有位置为 profile 输出与条件的唯一权威，其他测试和文档从它核对或引用，并把 deterministic 证明范围限定在真正可机械执行的部分。
3. **Fresh-review routing must be a topology invariant, not an `accepted` convention.** driver 当前可在 UV/blind Executor 后直接完成 phase；计划要求改为 fresh outer review，但任意 v2 spec 未必提供可达的 outer phase。建议方向：把“修改后必有可达 fresh Reviewer”纳入 spec/状态机结构约束，而不是依赖操作者在 resume 时提供正确 action。

## Implementation-Critical Watchpoints

- Shared initializer 必须在 `Driver` 创建 journal、reports、attempts 或执行 reserve 之前完成。当前 `Driver.__init__` 已产生这些副作用，不能只替换 `_init_budget_config()` 的函数体。
- 初始化器应分别处理“新建并持久化”“读取并验证”“显式冲突比较”，并验证完整 state/FSM/ledger。未知键、负数、`bool` 伪装整数和 malformed nested shape 必须在任何写入前拒绝。
- v1 `budget_config.max_inner_loops` 迁移时，过滤后的值只能进入 driver-local retry 配置，不能被共享 initializer 写入 active Continue 配置；已有 active `max_inner_loops` 仍只约束 true Continue。
- 为已有 driver journal 定义 `inner_streak` 迁移到 `executor_repair_streak` 的单义规则，或显式拒绝跨版本 resume；不得静默归零后增加重试额度。
- v2 spec 校验应保证任何可能触发 Executor 的 review phase 都能进入 fresh Reviewer；`accepted` 只能表示“准备复查”，不能完成修改后的 UV/blind phase。
- Small + Git 与 Small + no-Git 的精确输出及 fixture 应显式包含 `docs/initialization.md`；Medium/Large 应显式绑定 `docs/plans/completed/initialization.md`，audit 应能识别错误位置而非“任一存在即通过”。
- 同步模式需要一个稳定、唯一、可机械解析的 `copy|hardlink` 声明。`check_all.py`、audit 和人工 remediation 应共享该语义，避免各自解析不同命令文本。
- `copy` 的后置条件应是三文件内容相同且互不 `samefile`。测试应覆盖完整 hardlink 组和部分 hardlink 组；否则 `check --mode copy` 仍可能把部分共享 inode 误判为独立副本。
- 四 profile fixture 不应由测试直接手写出一个与生产初始化无关的“理想树”后自证。确定性测试应清楚区分 profile 合同核对、脚本在合成树上的行为、以及 Agent 实际投影行为。
- no-Git sentinel 测试应覆盖 `maintain.py` 的所有 Git 入口（memory timestamp 和 recent context），并确认 Git 检测本身不会调用 `git`；Git profile 则需保留 worktree/`.git` 文件等合法仓库形态。

## Later Enhancements

- 收集 standard/ultraverge 的 outer、blind、total extension 频率及触发阶段，再评估 `3/1/1` 与 blind overlay；当前先作为明确的成本默认值上线即可。
- 补充 Small + Git 和 Medium/Large + no-Git 的 fresh-Agent advisory eval，使四 profile 至少各有一次行为证据；继续保持其非 deterministic 定位。
- 若 profile 数量继续增长，再评估是否需要轻量数据清单；在四种组合阶段不必引入新的 controller、registry 或 renderer。

## R2 设计审查（candidate-3）

咨询式审查，不给出 verdict，不重开收敛。对象：`plan.md` 最终候选 3，SHA-256 `c56e656d4d1486f49a95e74b73b6932219c97ad978834bff36d96d8b12dc6059`（已重算一致）。重点为实施期风险：不可实现承诺、测试盲区、过度设计残留、dirty baseline 归属歧义、Windows 环境陷阱。

### DR1-DR7（candidate-3）

| 维度 | 状态 | 发现 |
|---|---|---|
| DR1 Consistency | concerns_found | (a) D7 样例 `configured_limits` 的字面值 `8/3/3` 未加尖括号，形式上像合同常量；本对象 active 配置为 `3/2/1`，首个真实样本若照抄字面值会被 finish 的 state 绑定 fail-closed 拦下。(b) preflight 把"删除 ultraverge blind overlay"表示为 `proposed: 3` 的数值变更，数值门需把"控件被移除"特判为 `2→3`，表示层与机制层不一致（本对象 `eligible_samples=0` 时不触发，但机制会永久存在）。 |
| DR2 Completeness | concerns_found | 测试盲区：(1) 验收标准要求初始化展示 `quality_path_guaranteed: false`，测试矩阵无任何对应条目；(2) `counterevidence_refs` / bound-user-tradeoff 豁免路径无 fixture（且本次恒为空）；(3) "later governance changes receive no bootstrap mode" 的机械判据未定义——preflight 如何识别 bootstrap 例外（change_id 白名单？报告内嵌 vs 生成？）未规定；(4) preflight "validates relevance" 中 relevance 无法机械定义，要么退化为存在性检查，要么范围蔓延。 |
| DR3 Maintainability | concerns_found | bootstrap 例外是永久特判代码路径；`finish` 将汇聚样本校验 + 双审链 + ledger + coverage + reopen supersession，计划未给结构约束，单函数持续膨胀；同一 fence-locator 解析器复用于 `plan.md`、`attempts.md`、prompt 文件三处，prompt 内嵌 payload 提取依赖"恰好一个 fence"，对模板漂移敏感。 |
| DR4 Boundary Clarity | concerns_found | dirty baseline 归属总体清晰且经核实：`capture.py` EventLock 修复与 `test_archive_convergence.py` 既有 35 行测试已显式归 prior baseline，与 `git diff` 一致；GATE_TO_RECOVER bug（`orchest.py:100` bare string vs `:1067` 元组解包）与 D11 配对证据（ledger 行 40/41、events 43/44）均与仓库实况吻合。但仓库根存在未归属的 0 字节 `NUL` 文件（2026-09-11 09:56 生成，疑似重定向事故），不属于任何 baseline，Phase 7 "no file outside the matrix / exact dirty-baseline attribution" 会被它卡住。 |
| DR5 Residue & Redundancy | concerns_found | `counterevidence_refs`/bound-tradeoff 豁免机制无数据、无测试，属投机性通用；bootstrap 模式永存（见 DR2/DR3）。blind overlay 残留点已核实为 `budget_gate.py` 两处（state 初始化 `setdefault` 与 `merged_config`）加 `ocsr_spawn_adapter.py` 一处，测试矩阵均已覆盖。 |
| DR6 Portability | concerns_found | Windows 陷阱：(1) 字节同一性链条（canonical payload、两个 prompt 文件、输出回显、bootstrap 报告重放、attempts material 块哈希）在 Windows 文本模式写入下会发生 LF→CRLF 转换，计划未写明必须显式二进制或 `newline=''` 写入，首个真实双审链路大概率因此假性 fail-closed；(2) 根目录 `NUL` 保留设备名文件不能按常规 `del`/`rm` 删除（需 `\\?\` 前缀），遍历或审计脚本遇到它行为不一。 |
| DR7 Scalability | concerns_found | 双同字节审使每次 material revision 成本翻倍，属有意取舍；distill 语料随归档线性增长，当前规模无碍。操作性风险：本对象显式 `3/2/1` 预算下（pre_execution cancel 不计费，有效用量 outer 2/3、blind 1/2），Phase 0 两个新 Spawn 恰好顶格（outer→3/3、blind→2/2），零余量；输出回显字节不符的重试语义未定义，重 Spawn 即超额，会触发既有 budget gate/用户确认路径。 |

### R2 Highlights

1. [implement-now] **字节同一性链条的 Windows 换行风险**：review-target payload、prompt 文件、输出回显、canonical 报告重放、material 块哈希全部要求字节级一致；所有相关文件写入必须显式二进制或 `newline=''`，并应在 Phase 1 补 CRLF 污染的 red test，否则双审链路在 Windows 上大概率假性失败。
2. [implement-now] **根目录未归属的 0 字节 `NUL` 文件**（Windows 保留设备名，今日生成，疑似本次会话重定向事故）：不属于任何 dirty baseline，会阻断 Phase 7 的归属核查；删除需用 `\\?\` 前缀路径（常规 `del`/`rm` 指向设备而非文件），应归入运行残留清理，不计入 r2 delta。
3. [implement-now] **Phase 0 预算零余量**：本对象 `3/2/1` 下两个同字节审 Spawn 恰好用满 outer/blind 配额；回显字节不符的重试语义（是否允许同 reservation 重试、超额后走哪个既有 gate）需在实施前明确，否则单次模型输出格式漂移即把"零阻断自动落地"拖入用户确认路径。
4. [note] **D7 样例字面值陷阱与 overlay 表示不一致**：`configured_limits` 的 `8/3/3` 应改为占位符以免首个真实样本照抄；"删除 overlay" 在 preflight 中表示为 `proposed: 3` 需要数值门永久特判"控件移除"，建议在实现时把该 basis 显式建模为移除语义而非数值比较。
5. [implement-now] **测试矩阵漏项**：验收标准要求的 `quality_path_guaranteed: false` 初始化展示无任何测试条目，Phase 1 应补 red test；bootstrap 例外的机械识别判据（内嵌报告 vs 生成报告）应写成显式规则。`counterevidence_refs` 豁免路径无数据可测，其 fixture 可 defer 至首个真实反例。
