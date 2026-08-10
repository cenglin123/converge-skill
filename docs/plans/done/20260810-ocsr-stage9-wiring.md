# 计划：OCSR 阶段 9 —— converge 侧接线

> 状态：**已完成**（2026-08-10 创建并收口）
> owner：主对话 orchestrator（Claude Opus 5）
> 对侧计划：ocsr 仓库 `docs/plans/active/20260810-deterministic-run-spec.md` 阶段 9
> 落地：本仓库 PR #7（`b98860b`）+ PR #8（`3040109`，把落单的 kimi shim 一并归位）；
> ocsr 仓库 PR #3（`f8f6a2d`，模板文法新增 `{{steps.<id>.capture.<name>}}`）
>
> **9a / 9b / 9d / 9e 已落地；9c 经跨族独立评审后裁定不落地**（见下方「独立评审结果」），
> 其遗留缺口已登记进 tracked 的 `refs/framework-adapters.md`。

## 背景

ocsr 仓库已完成阶段 1–8：`dispatch` 的退出码契约（0/1/2/3）与确定性步骤运行器
`ocsr_dispatch.py run --spec` 均已落地并有回归测试。阶段 9 是**本仓库**的对侧接线。

同时，ocsr 的两次收敛在**归档**这一步连续失败，失败点全部落在 converge 的
`record-terminal-decision`：

| slug | 失败码 | 直接原因 |
|---|---|---|
| `20260809-execution-layer-integrity` | `decision-chain` | 两条 terminal-decision 的 `supersedes_decision_event_id` 都手填成 `null` |
| `20260810-deterministic-run-spec` | `user-decision-degradations` | `presented_degradations` 手填成自拟散文，而契约要求逐字等于从事件图机械导出的集合 |

两笔同源：**这两个字段本来就可以从事件图机械导出，却要求调用方手填。**
`record-terminal-decision` 的 CLI 是 `--data '<整块 JSON>'`，把最容易算错的两个值
交给人手写，是这一类错误的结构性成因。

> 用户 2026-08-10 已裁定旧账不追修。本计划**不修复既有归档**，只消除成因。

## 范围

| 项 | 内容 | 性质 | 评审强度 |
|---|---|---|---|
| 9a | `ocsr_spawn_adapter` 接线 OCSR 退出码契约 0/1/2/3 | 接口对齐 | 常规 |
| 9b | `record-terminal-decision` 机械导出 `supersedes_decision_event_id` 与 `presented_degradations` | **收紧**约束 | 独立评审 |
| 9c | `validate_event_graph` 对**已被超越**的 user-decision 放宽 degradations 校验 | **放宽**约束 | **必须**跨族独立评审 → **评审后裁定不落地**，见下 |
| 9d | ocsr 侧缺口：独立 `hook` 步骤的捕获不可被引用（阻塞 9e） | 缺陷修复 + 封闭文法扩张 | 独立评审 |
| 9e | converge 侧 run spec 模板 + `refs/framework-adapters.md` 接线说明 | 新增 | 常规 |

**不在范围**：修复既有归档；把 converge 的多轮主循环整体交给 runner（本次只接终局
链路这一段——它是失败率最高、且完全确定性的一段）。

## 9a — 退出码契约接线

`refs/dispatch-patterns.md`（ocsr 仓库）是退出码语义的单一事实源：

```
0 全部落盘 ｜ 1 看门狗超时 ｜ 2 确定性失败 ｜ 3 路径碰撞
混合结局优先级：3 > 1 > 2 > 0
```

退出码 `2` 是 2026-08 新增。在此之前 `dispatch --watch` 在 worker 失败时返回 **0**
并打印「✅ 全部 worker 完成」，调用方无法用退出码区分成败——本仓库的适配层正是在这个
前提下写的，因此有两处需要订正：

1. `_map_ocsr_outcome` 的注释仍写着「launcher 错误通常表现为 rc=0 + error.log」。
   该描述在新契约下已过时：launcher 错误现在表现为 **rc=2 + error.log**。
2. **更要紧的一处**：happy path 的判据只看「产物存在且非空」，**完全不看 `ocsr_rc`**。
   于是 rc=3（路径碰撞：产物落了盘，但**别的既有文件被覆盖**）会被记成
   `succeeded`。这与「不采信完成声明、以证据判定」的方向一致，但**证据不止产物一项**，
   退出码同样是证据。

订正后的判据：**产物落盘 且 `rc == 0`** 才走 complete-succeeded；
`rc != 0` 一律走 recover 路径，且当产物确实存在时，`failure_detail` 必须明说
「产物已落盘但派发以 rc=N 收尾」——不得让失败记录暗示产物不存在。

## 9b — 终局决策字段改为机械导出（收紧）

两个字段本来就是事件图的函数：

- `supersedes_decision_event_id` = 现有最后一条 terminal-decision 的 `event_id`（没有则 `null`）
- `presented_degradations` = `validate_event_graph` 里那段 `actual` 推导的结果

**改法**：`record_terminal_decision` 在**写入前**（且在 `EventLock` 内）自行推导：

- 字段缺省 → 自动填充导出值；
- 字段给定 → 与导出值比对，不符即拒绝写入（`ArchiveError`），**不静默改写调用方给的值**。

这与既有的 `reviewer-verdict` 前置授权检查是同一模式，理由也逐字相同——
「一个越权角色永远不能被登记为 terminal owner，**这个事实本身都不应该被写入 ledger**」。
一条注定在归档时 fail-closed 的决策事件，同样不应该先落盘再在归档时才被发现。

**推导必须在锁内。** 现有 `reviewer-verdict` 检查在 `record_terminal_decision` 里、
`EventLock` **之外**执行，存在 TOCTOU 窗口。本次给 `_commit_event` 增加一个在锁内、
读到 `existing` 之后调用的 `prepare(fields, existing)` 钩子，把两处检查都移进锁内。

配套：

- `record-terminal-decision` 增加 typed flags（`--decision-type` / `--decision-kind` /
  `--user-quote` / `--source-ref` / `--accepted-state` / `--reviewer-event-id` / …），
  保留 `--data` 向后兼容。**手拼整块 JSON 本身就是易错面**，而 hook 步骤的 argv
  写 typed flags 比写 JSON 字面量安全得多。
- 新增只读诊断子命令 `derive-decision-fields`，打印当前事件图导出的两个值，
  供 orchestrator 派发前肉眼复核、供 spec 的 hook 步骤捕获。

**这条不放宽任何约束**：校验强度不变，只是把「写入后归档时才发现」提前到「写入时拒绝」，
并把可导出的值改为默认导出。

## 9c — 被超越的 user-decision 的 degradations 宽免（放宽，需评审）

`validate_event_graph` 对 `reviewer-verdict` 已有一条明确的宽免：只有**最后一条**
（未被超越的）决策做全强度授权校验，被超越的那些若校验失败，降级为可审计的
`degradations` 条目而非 raise。其理由注释写得很清楚：

> 被后来者超越的决策不再决定 `final_decision`……要求它仍然可解析，等于让一条
> 记错的历史决策永久 fail-closed 归档，而**除了超越它之外没有合规修复路径**——
> 这正是本宽免要消除的缺陷。

`user-decision` 分支**没有**对应宽免：`presented_degradations` 对每一条决策都做全强度
比对，包括已被超越的。后果实测于 `20260810-deterministic-run-spec`：追加一条值正确的
user-decision 并保持链完整，**仍然无法修复**——因为旧的那条还在被校验。
「超越它」这条合规修复路径**在 user-decision 上是不通的**。

拟改：`presented_degradations` 的比对只对最后一条决策做全强度，被超越的失配降级为
`decision:superseded-degradations-unverified:<event_id>` 记入 `graph_degradations`。

**刻意不动的**：`user-decision-source`（决策必须绑定一条在先的 user-message 且引用逐字
相符）保持全强度、对被超越的决策同样适用。理由：`presented_degradations` 是**决策时
上下文的元数据**，记错是记录缺陷；而 quote 绑定是**决策的身份**（这是用户的哪一句话），
绑定断裂的决策不是「记错的决策」，是「无法认定的决策」。两者不该同等对待。

**这是一次放宽，且论证由改动的实现者自己撰写。** ocsr 阶段 8 刚有过实证：
实现者为自己实现撰写的豁免论证，被两个独立家族的评审分别证伪（一个抓到事实性虚假声称，
一个抓到论证结构缺陷）。因此本项**必须**取得跨族独立评审证据后才落地。

## 9d — ocsr 侧缺口：独立 hook 步骤的捕获不可引用

接 9e 时实测发现（ocsr 仓库）：

```
spec: hook 步骤 expect: '^VALUE:(?P<token>\w+)$'，后续步骤引用 {{steps.emit.capture.token}}
--validate → template-unresolvable：支持的形式仅有
            run.id / run.workdir / vars.<name> / scope.<key>.next_index / steps.<id>.(pre|post)[<n>].<name>
```

实现侧 `ocsr_run_spec.py` **确实**把独立 hook 的捕获存进了
`ctx["captures"][sid]["self"]`，但模板文法里没有任何形式能引用它；
而 `refs/run-spec.md` 写着「`expect` 的命名组捕获进 run context，**供后续步骤引用**」。
**文档承诺了实现不提供的能力。**

这直接阻塞 9e：converge 的终局链路需要「导出步骤的输出 → 流入记录步骤的 argv」。

修复归 ocsr 仓库（分支 `agent/stage9-hook-capture`）：补一条模板形式引用独立 hook 的捕获，
同步 `refs/run-spec.md` 的文法表，并加回归测试。
**注意这是对封闭文法的扩张**，按 ocsr 的治理规则需独立视角复查——与 9c 同批送审。

## 9e — converge 侧 run spec 模板

把终局链路写成 spec，交给 `ocsr_dispatch.py run --spec` 确定性执行：

```
record-user-message → derive-decision-fields → record-terminal-decision → archive → check
```

**凡可从事件图导出的参数一律禁止手填**——这正是 9b 提供导出能力、9d 提供值流通道的目的。

模板落在本仓库（converge 是 spec 的作者，ocsr 不认识 converge 语义，
`refs/converge-integration.md` 的边界不变）。`refs/framework-adapters.md` 补接线说明
与诚实边界。

## 模型调用披露

评审派发**上限 4 次**（2 位跨族独立评审 × 1 轮 + 预留 2 次用于修复后复评）：

- `deepseek/deepseek-v4-pro`（deepseek-thinking 族）
- `xiaomi/mimo-v2.5-pro`（mimo 族）

评审类角色不降档。**本批派发不属于 converge 流程**——不新建 `.converge/active/`、
不走预算门、不产生归档事件。理由需明说：9b/9c 修的正是终局归档链路本身，
为审这两项而跑一次正式 converge，会撞上同一条待修的链路。
证据以派发产物文件形式保留，在本文件登记。

## 验收标准

- 9a：`_map_ocsr_outcome` 对 rc 0/1/2/3 各有测试；「产物落盘 + rc≠0」判为失败有测试。
- 9b：缺省自动填充、给定不符即拒写、推导在锁内——各有测试；既有测试不回归。
- 9c：取得**两个不同家族**的独立评审结论后方可落地；被超越失配降级为 degradation
  且**出现在 INDEX.md**有测试；`user-decision-source` 仍全强度有测试。
- 9d：ocsr 仓库 `pytest tests/ -q` 全绿；新文法有 `--validate` 正例与反例测试；
  `refs/run-spec.md` 文法表与实现一致。
- 9e：模板经 `run --spec --validate` 通过；至少一次**不含真实模型调用**的端到端干跑
  （全部步骤为 hook/assert），产出真实归档并 `check` 为 `valid-v1`。
- 两仓库各自 `pytest tests/ -q` 全绿。

## 独立评审结果（2026-08-10）

派发 2 位跨族 design-reviewer，各审 P1（9c 放宽）/ P2（9b 收紧）/ P3（9d 文法扩张）：

| 评审 | 模型 | P1 | P2 | P3 | blocking |
|---|---|---|---|---|---|
| r1 | `deepseek/deepseek-v4-pro` | `legitimate-relaxation` | safe | `needs-governance-review` | 2 |
| r2 | `xiaomi/mimo-v2.5-pro` | **`needs-different-approach`** | safe | acceptable | 2 |

**两族在 P1 上分歧，这正是跨族的价值。** 两人都指出了同一个我没看见的事实，却推出相反结论：

> `reviewer-verdict` 的既有宽免，放掉的是 `reviewer_event_id` **授权绑定**——
> 那是该决策类型最关键的「身份」字段（谁是这条 verdict 的合法拥有者）。

我原来的界线是「放宽 `presented_degradations`（元数据）、保留 `user-decision-source`
（身份）」，论据是「元数据记错是记录缺陷，身份断裂是无法认定」。
r2 指出：**先例已经放掉了身份**，所以这条界线没有被论证——
要么给出「为什么 `reviewer_event_id` 可放、`source_ref` 不可放」的区分判据，
要么连 `source_ref` 一起放宽以与先例对齐。r2 倾向后者。
r1 从同一观察推出「按 `is_final` 区分即达成对称」，但同时又赞成保留 `source_ref` 全强度——
r1 这一段自相矛盾。

**裁定：P1（9c）不落地，转为记录。** 理由：

1. **它要修的损害，9b 已在上游堵住。** 写入前拒绝之后，错误的
   `presented_degradations` 根本写不进去。P1 剩下的价值只是「万一还是写进去了」的
   修复路径——而那已经收窄到 `append_event` 直写、bootstrap 导入、9b 之前的旧归档三种情形。
2. 两位评审**都没有**认可按原文落地：r2 判 `需重新设计`，r1 要求配套审计信号。
3. 在界线未被论证的情况下落地一次放宽，正是 ocsr 阶段 8 已经栽过的那个跟头。

**遗留的已知缺口**（不作为待办，作为事实登记）：若一条 `presented_degradations` 或
`user-decision-source` 有误的决策**确实**进了事件图（绕过 9b 的写入前检查），
归档将永久 fail-closed，**且「超越它」这条合规修复路径不通**。
9b 把这种情形从「常态」降为「异常」，但没有消除它。

### r1 的 B2（P3 必须走文法准入，不能以 bugfix 名义绕过）——已响应

r1 要求三条证明，逐条兑现：

| 要求 | 兑现 |
|---|---|
| (a) 新形式与既有形式无二义性 | 新增回归测试：同时存在 `a` 与 `a.capture` 两个步骤时，`{{steps.a.capture.token}}` 与 `{{steps.a.capture.capture.token}}` 各自解析到确定且不同的目标 |
| (b) `.capture` 仅对 `type: hook` 成立，解析不了即 fail-closed | 已有三条反例测试：非 hook 步骤 / 无 `expect` / 命名组不存在，各以 `template-unresolvable` 拒绝 |
| (c) 没有既有形式已提供同等能力 | 已实证：修复前 `--validate` 直接报 `template-unresolvable` 并列出全部支持形式，无一可达 |

本次跨族评审即 ocsr「治理规则变更需独立视角复查」所要求的复查，证据见下。

### 评审自身的一处失误（值得记录）

r2 的 B1 判定「P2 声称的三项变更已全部存在于当前代码，其中『把 `reviewer-verdict`
授权检查从锁外移进锁内』是**事实性错误**」。

**该判定不成立**，已用 git 核实：`git show HEAD:scripts/archive_contract/capture.py`
里 `record_terminal_decision` 是

```python
    if values.get("decision_type") == "reviewer-verdict":
        validate_reviewer_verdict_authority(_read_existing(root), values)   # 锁外，独立读
    return append_event(root, values)                                       # 锁在这里面
```

——检查确实在 `EventLock` **之外**，且自带一次 `_read_existing`。

失误的成因值得单独记下：**评审读到的是已改过的工作树**。
`~/.agents/skills/converge` 与 `~/.claude/skills/converge` 是同一目录（junction，
`os.path.samefile` 为真），r2 顺着路径找过去读了改后的 `capture.py`，
于是「评审这份提案」悄悄变成了「评审当前代码」。
派发时**没有加 `--forbid-paths`**——ocsr 正是为这类评审锚定污染提供了该参数，本次漏用。
下次审「提案 vs 现状」类问题必须禁读工作树，或改为只发 diff。

### 派发实况

声明上限 4 次，**实际用 2 次**。首次派发因 prompt 未按 ocsr 约定写明
【输出】落盘路径，两个 worker 都以 `exit=0 但产物未落盘` 收尾——
`dispatch` 返回新契约的 **rc=2**（确定性失败），契约本身工作正常。
评审正文完整留在 worker 的 `run.log` 里，已按证据取用，**没有伪造产物落盘**。
（`run.log` 里的中文经历过一次 UTF-8→GBK 误解码，约 9% 字符不可逆丢失，
不影响论证可读性；原始 log 与还原文本存于 scratchpad。）

## 风险

- **9c 是放宽。** 缓解：跨族独立评审前不落地；失配不被吞掉而是升为可审计 degradation。
- **9b 改变了 `record-terminal-decision` 的既有行为**：过去接受的（错误的）手填值现在会被
  拒绝。这是有意的，但对既有调用方是破坏性变更，需在 CHANGELOG 明示。
- **跨仓库不同步窗口**：9d 在 ocsr 仓库、9e 依赖它。两仓库的 PR 需同期合并，
  9e 的模板在 9d 落地前只能 `--validate` 失败。
