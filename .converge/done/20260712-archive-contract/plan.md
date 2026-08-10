---
type: plan
status: landed
object_slug: 20260712-archive-contract
generated_at: 2026-07-12T03:10:00+08:00
amended_at: 2026-07-12T13:20:00+08:00
landed_at: 2026-07-12T14:05:00+08:00
contract: converge-archive-v1
---

# Converge Archive Contract v1 修复计划

## 1. 目标、能力与威胁模型

Archive Contract v1 让 `.converge/done/<slug>/` 在归档时点形成一个可确定性检查的内部一致性闭包，使后续审计者能够：

1. 30 秒内从 `INDEX.md` 定位最终结论、风险与推荐阅读顺序；
2. 按 invocation sequence 复盘 Spawn、Continue、失败、仲裁、盲审和设计审查；
3. 识别每次调用所声明/观测到的模型 provenance 及其证据等级；
4. 将结论绑定到归档捕获的 reviewed artifact 字节或其身份摘要；
5. 在整体移动或改名归档目录后继续使用内部导航；
6. 通过标准库 CLI 发现缺失、篡改、孤儿事件、非法路径和半完成归档。

v1 的安全主张仅是**归档时点的内部一致性、结构完整性和声明 provenance 可追溯性**。它不提供外部签名或不可变信任锚，不能证明历史真实性，也不能对抗能够以同等写权限整体重写归档目录、event log、manifest、budget ledger 与 Git 历史的攻击者。`hash` 不是来源认证；`configured`/`inherited` 模型也不是“实际模型已证明”。所有文档、INDEX 和 CLI 输出必须使用这个收窄后的表述。

## 2. 非目标、兼容与数据边界

- 不自动改写既有 `done/` 历史目录；只读 `scan` 对旧目录分类。
- 不快照整个仓库；只处理本次声明并通过路径策略的 reviewed artifacts。
- 不支持跨卷原子归档，不引入守护进程、数据库、网络服务、签名系统或第三方依赖。
- 不以日期判断版本；以 `schema_id` 和 `schema_version` dispatch。
- 默认不持久化 prompt/output 或 workspace 外文件的原始内容，不把“可读取”当作“获准长期归档”。
- 保留根级 canonical consumer 接口，但 raw prompt/output、执行报告和 reviewer 原始输出进入 `evidence/invocations/`，禁止双份权威。

证据模式为逐 invocation/逐 artifact 显式字段，且能力必须诚实降级：

| `evidence_mode` | 保存内容 | 能力声明 |
|---|---|---|
| `metadata-only`（默认） | locator 的脱敏表示、原始字节 hash、字节数、provenance/状态；不保存内容 | `identity-only` |
| `redacted` | 经调用方确认的脱敏副本及其独立 hash；同时保留原始输入的 hash/size（如可得） | `redacted-copy`，不得称 exact |
| `exact` | 明确 opt-in 后保存精确捕获字节 | `snapshot` |

常见秘密文件、设备/管道、workspace 外文件默认为拒绝；workspace 外 exact/redacted 必须有本次调用的新鲜显式授权和脱敏 display locator。设置单文件和总归档字节上限，超限 fail closed，不自动读取源做 `source_drift`。归档后文件权限尽力收紧为当前用户；权限能力不可用时记录 capability degradation，不伪称保密。

## 3. v1 目录、canonical allowlist 与现有产物映射

```text
done/<slug>/
├── INDEX.md                         # 由 manifest 确定性派生
├── manifest.json                    # 冻结事实索引，v1 长期权威
├── plan.md / contract.md / attempts.md / retrospective.md
├── round-N.md / design-review.md
├── _orchestrator-state.md / gate-ledger.jsonl / _budget-state.json
└── evidence/
    ├── events/<SEQ>-<event-id>.json # 所有事实的 append-only event
    ├── invocations/<invocation-id>/
    │   ├── prompt.bin               # 仅 redacted/exact 且允许时存在
    │   └── output.bin               # 仅 redacted/exact 且允许时存在
    ├── artifacts/<artifact-id>/
    │   └── snapshot                 # 仅 redacted/exact 且允许时存在
    └── revisions/<revision-id>/
        └── manifest.json            # 前一 revision 的冻结 manifest；不重复保存可重建 INDEX
```

根级 allowlist 是固定文件名加受控模式：`INDEX.md`、`manifest.json`、`plan.md`、`contract.md`、`attempts.md`、`retrospective.md`、`design-review.md`、`_orchestrator-state.md`、`gate-ledger.jsonl`、`_budget-state.json`、`round-[1-9][0-9]*.md`。缺少非适用项允许由 schema 标记，但根级其他文件一律拒绝；比较采用规范化后的大小写无关唯一键，拒绝 Unicode 规范化碰撞。

现有产物采用以下单一映射：

- `plan/contract/attempts/retrospective/round-N/_orchestrator-state/ledger/budget` 是根级 canonical orchestration records，由 manifest 承诺；`round-N.md` 是轮次摘要，不是 raw 模型输出。
- `design-review.md` 保留为根级 canonical design-review advisory 摘要；对应 reviewer 原始输出只在 invocation evidence 中，且该摘要不拥有 final verdict。
- `uv-init-*.md`、`round-*-reviewer.md`、`blind-recheck-*.md`、`arbitration*.md`、`landing*.md`、`execution*.md`、`*prompt*.md|txt` 与 `*report*.md` 是 raw invocation evidence。`archive` 的 bootstrap importer 依据 `_orchestrator-state.md`、round log 和显式 mapping file 将它们原字节导入 invocation 目录，记录 `legacy_source_path`，随后在 staging 副本中移除根级原件；无法唯一绑定时拒绝归档，不靠文件名猜角色或模型。
- INDEX 为每个 canonical event 链接对应 invocation；raw prompt/output 中出现的路径或 Markdown 不重写、也不视作导航。
- INDEX、生成文档以及 canonical Markdown 中的真实 Markdown 链接必须是归档根内 POSIX 相对路径，目标与 anchor 均可验证；绝对 `active` 路径或越界链接导致 archive 失败。整体移动/改名后重新 check 必须通过。

本次 `20260712-archive-contract` active 目录必须作为 bootstrap fixture 原样复制后成功导入，证明 `uv-init-1/2/3` 等当前产物不被误判为 clutter。

## 4. 单一权威、派生规则与哈希覆盖闭包

权威生命周期如下：

1. **采集期**：`evidence/events/` 是不可变、append-only 事实日志；每次 begin、terminal、artifact capture、terminal decision 与 design-review completion 都创建一个新的 event 文件，CLI 独占锁内分配 sequence 并 exclusive-create，不原地更新、不手写、不覆盖。
2. **归档时**：`archive` 从 event log、canonical records 和严格 budget ledger 投影规范对象，生成 canonical JSON `manifest.json`；归档后 manifest 是当前 revision 的冻结物化事实索引，而不是事件事实的产生者。
3. **导航层**：`INDEX.md` 只由 manifest 生成，不是独立事实源。`check` 必须从 manifest 重建 INDEX 并逐字节比较。

manifest 记录并闭合：

- 所有根级 canonical records 的 POSIX 相对路径、原始字节 SHA-256 和字节数；
- 每个 append-only event、允许保存的 prompt/output 字节及其 SHA-256/size；
- 每个 artifact capture event、snapshot 字节及其 SHA-256/size；
- 全局 invocation sequence、event 主外键、ledger binding、finalization/revision id，以及闭合 terminal decision 联合类型中的最终 verdict/decision 事件引用；
- 精确允许的目录树集合。未声明的额外文件、缺失文件、路径/大小写/NFC 碰撞均为 invalid。

SHA-256 一律对实际捕获的原始字节流计算，格式为 64 位小写 hex，size 单位为 byte。manifest 不自哈希；其完整性由严格 schema、canonical JSON 序列化，以及从 event owners/canonical references 重新投影后与 manifest 语义比较来检查。INDEX 排除在 manifest 的内容哈希闭包之外，因为它由 manifest 唯一派生，但其路径被 allowlist 约束且字节必须与再生成结果相等。这个闭包仍受 §1 的同权限整体重写限制。

JSON 解析拒绝重复 key、NaN/Infinity、非法数字、未知必填组合；v1 writer 输出 UTF-8 无 BOM、LF、排序 key、固定分隔符与终止换行。event 与 manifest 重复字段不构成双权威：archive 仅按下表投影不可变 owner facts；不一致或非法值直接失败，不择一吞掉，也不通过修改 manifest 或历史 event “修复”冲突。

最终 verdict 不接受 `archive --verdict` 任意注入。manifest 的 `final_verdict_ref` 只能引用 §5 定义的闭合 terminal decision 联合类型：fresh/blank-slate Reviewer 的 verdict event，或终止-b/终止-c 的 user-decision event。`design-review` 只能产生 advisory completion event，用于证明设计审查步骤完成，不能产生、覆盖或改变 final verdict。被引用事件、最终 `round-N.md` 与 `retrospective.md` 必须通过同一个 event id 和 verdict/decision 值双向一致：manifest 引用的事件必须被两份 canonical record 引用，二者引用也必须反向解析到 manifest 的同一事件；冲突、缺失、悬空或时间线不闭合即失败。

## 5. Invocation lifecycle、ledger 绑定与模型 provenance

“run”提升为 invocation/event lifecycle，覆盖 fresh Spawn 和 Continue：

1. `begin-invocation` 在模型调用前、budget reserve 后执行：工具在锁内分配 invocation id，以及归档 event log 全局连续且无缺口的 `sequence` 和 UUID `event_id`，冻结 prompt identity/evidence，以 exclusive create 写入不可变 `invocation-started` event。
2. 宿主执行 Spawn 或 Continue。
3. `complete-invocation` 绑定宿主返回的 instance/receipt、output evidence、settlement 和 terminal status；它追加新的不可变 `invocation-terminal` event 并引用 started event，绝不更新旧文件。进程中断后的 `recover-invocation` 也只能追加 `failed|cancelled|timeout` terminal event，不能伪造成功输出。

必填关系：

- started event：`event_id`、`sequence`、`invocation_id`、`invocation_kind=spawn|continue`、`role`、`phase`、`round`、`attempt`、`parent_event_id|null`、`started_at`；terminal event 使用自己的 event id/sequence，引用 `started_event_id`，并拥有 `completed_at`、`terminal_status` 与 resolved/receipt 字段。
- Spawn：必须绑定唯一 `reservation_id`、ledger reserve/settle event id、instance id/host receipt（宿主提供时）；reservation、role、phase、target round、status 必须双向一致。
- Continue：`reservation_id` 按现有预算语义可为 null，但必须引用同 instance 的 parent Spawn event，并记录本次 host receipt（如有）。
- terminal 枚举：`succeeded|failed|cancelled|timeout`。仅 succeeded 要求 output evidence；其他状态允许无 output，但必须使用闭合 `failure_reason_code` 并可附非敏感 detail。started 不是可归档 terminal。
- sequence 由 CLI 为所有事件类型统一分配，归档内从 1 全局连续；event id、invocation id、receipt、reservation、instance 的唯一性与允许复用规则由 schema 明确。

`archive/check` 调用同一个严格 ledger validator，而不是仅检查 pending=0：每个受预算约束的成功 Spawn reservation/settlement 必须恰好对应一个 Spawn invocation，反向亦然；孤儿、重复 receipt、role 伪标、字段冲突、失败调用却带成功 settlement 都 fail closed。auditable-only 和 ledger 本身同样不抵抗同权限整体重写。

terminal decision 是与 invocation terminal status 分离的闭合联合类型，只允许：

- `reviewer-verdict`：引用一个已成功闭合的 fresh Reviewer 或 blank-slate Reviewer invocation，必填 `reviewer_event_id`、`review_kind=fresh|blank-slate`、`verdict`、`verdict_output_ref` 和生成时间；不得引用 Continue 后被主上下文污染且不满足 fresh/blank-slate 条件的 reviewer，也不得引用 design-review。
- `user-decision`：只用于 converge 终止-b 或终止-c，必填 `decision_kind=accept-terminal-b|accept-terminal-c`、用户作出决定时的原话 `user_quote`、可审计来源 `source_ref`（宿主 message/event id 或受 manifest 承诺的 canonical transcript locator）、`presented_degradations` 引用、决定时间和所接受的最终状态。缺少新鲜用户接受、原话或来源引用时不得构造该事件，也不得完成归档。

`design-review-completion` 是单独的 advisory event 类型，只能记录 design review invocation、完成状态和 highlights 引用；schema 禁止它出现在 `final_verdict_ref`。terminal decision event 自身由 manifest 承诺，其 source invocation/用户来源和 round/retrospective 交叉引用必须全部可解析。

### 5.1 字段级 ownership / projection matrix

| 事实/投影 | 唯一 owner 与物理落点 | 派生消费者 | 冲突规则 |
|---|---|---|---|
| invocation open/terminal status | `invocation-started` / `invocation-terminal` events；terminal 事件引用 started event，不覆盖它 | manifest invocation projection、INDEX timeline、check | 同一 started 有多个 terminal、非法跃迁或 terminal 字段冲突即 invalid |
| role / round / phase / attempt | `invocation-started` event | terminal event 只引用；manifest/round/INDEX 投影 | 后续记录不得重新定义；ledger/round 不一致即 fail closed |
| budget settlement | `gate-ledger.jsonl` 中 budget gate settlement event | invocation-terminal 仅保存 settlement ref；manifest/check 投影 | archive 不复制 status 为新事实；引用缺失、重复或字段不一致即 invalid |
| terminal decision | `terminal-decision` event，物理位于 `evidence/events/` | manifest `final_verdict_ref`、最终 round、retrospective、INDEX | 只有 §5 联合类型合法；三方 event id/value 不一致、多个 current decision 或 design review 越权即 invalid |
| design-review completion | `design-review-completion` event，物理位于 `evidence/events/` | manifest advisory-completion projection、INDEX highlights | 只能 advisory；出现于 `final_verdict_ref` 或改变 verdict 即 invalid |
| requested model provenance | `invocation-started` event | manifest/INDEX | terminal/adapter 不得重写 requested 值；差异即 invalid |
| resolved model provenance | `invocation-terminal` event，绑定 host evidence ref | manifest/INDEX degradation projection | configured/inherited 不得投影为 observed；非法 evidence 组合即 invalid |
| artifact byte hash/size/locator/capability | `artifact-captured` event；snapshot 位于 `evidence/artifacts/<id>/snapshot` | manifest artifact projection、INDEX artifact/degradation 摘要、check | snapshot 重算不符、重复 artifact revision 或 locator 联合类型冲突即 invalid |
| revision history | 前 revision 的冻结 manifest，物理位于 `evidence/revisions/<revision-id>/manifest.json`；current manifest 记录 parent revision hash/ref | current manifest revision projection、INDEX revision timeline、check | history manifest 不改写；parent 缺失/hash 不符/链分叉即 invalid；旧 INDEX 不保存，按旧 manifest 按需重建 |
| manifest projection | `archive_contract.model` 的确定性 projector；物理位于根 `manifest.json` | check、只读 presentation、hooks | 必须由 owners 重新投影并语义相等；manifest 不反向成为 source event |
| INDEX projection | `archive_contract.presentation` renderer；物理位于根 `INDEX.md` | 人类审计者 | 只从已验证 manifest 生成；字节不等或包含未承诺事实即 invalid |

Canonical round/retrospective 是面向人的受承诺摘要：它们只引用 owner event id，不拥有 invocation status、settlement、model、artifact hash 或 final decision。字段 schema、owner 和 projection 规则的可执行单源位于 `archive_contract.model`；`refs/state-schema.md` 解释同一契约并由测试防漂移，不让 importer、hooks 或 renderer各自抄录枚举。

模型 provenance 不使用一个含混的 `model` 字段：

- `requested_provider`、`requested_model`：调用配置所请求的值，可 null；
- `resolved_provider`、`resolved_model`、`resolved_family`：宿主/后端实际回执可观察值，可 null；
- `backend`、`backend_version`；
- `evidence_level=observed|host-reported|configured|inherited|unavailable`；
- `resolution_source`：闭合枚举，例如 `host_receipt|tool_response|cli_argument|agent_config|parent_instance|none`；
- `resolution_reason_code`：仅 partial/unavailable 时必填，闭合枚举，例如 `backend-does-not-expose|receipt-missing|inherited-concrete-model-hidden|invocation-failed-before-resolution`。

`refs/framework-adapters.md` 为 opencode、Codex native agent、Claude Code 与 orchestrator_self 定义采集优先级、可获得字段和合法组合。不得把 configured/inherited 提升为 observed；缺 resolved 值时 INDEX 显示 provenance degradation，最终能力不得写“实际模型已证明”。

## 6. Artifact identity、workspace 与文件系统策略

每个 artifact 记录 `artifact_id`、`revision_id`、capture 时间、原始字节 SHA-256/size、`evidence_mode`、`reproduction_capability=snapshot|redacted-copy|identity-only`、snapshot 元数据，以及如下闭合 `source_locator` tagged union：

- `{kind: "workspace-relative", workspace_id, path}`：`workspace_id` 必须引用 manifest 中已声明的 workspace identity，`path` 必须是该 workspace 根内规范 POSIX 相对路径；禁止 `display_locator`、`portable`、`authorization_ref` 和任何绝对路径字段。
- `{kind: "external", display_locator, portable: false, authorization_ref}`：`display_locator` 只能是经脱敏、不可直接用于打开文件的展示标识，`authorization_ref` 必须引用本次新鲜显式授权；禁止 `workspace_id`、`path`、`workspace_relative_path`、真实绝对路径和可自动解引用 locator。external 默认为能力降级：manifest 标记 `source_resolution=disabled`，`check` 与普通 `source_drift` 永不回读；只有另一次显式授权的独立 capture 操作才能读取并生成新 revision，不能把 unavailable 报为 same。

workspace identity 至少包含显式 logical name；若在 Git worktree 中则增加 normalized remote fingerprint（不得保存凭证）和 commit/tree/dirty 标记，若不可得则明确 `workspace_identity_level=logical-only`，不得用本机绝对用户名路径冒充可移植身份。workspace-relative source drift 是显式离线操作，状态 `same|drifted|unavailable`；external locator 不参与普通 drift 检查并固定报告 `unavailable/external-read-disabled`。默认 check 不回读任何源文件。

安全策略：

- canonical root、active root、done root 和 workspace root 由 CLI 参数 allowlist 明确给出，使用平台感知的规范路径与 same-file/containment 检查；拒绝 UNC、`\\?\`、ADS、设备名、尾随点/空格歧义和越界路径。
- active/done/evidence 树禁止 symlink、junction/reparse point、hardlink（link count > 1）及非普通文件；artifact source 同样默认拒绝这些类型。扫描不跟随链接。
- 复制前打开普通文件，基于已打开句柄读取并计算 hash，读后复核 file identity、size、mtime 与类型；变化即 TOCTOU failure，不保存部分结果。Python/平台不能可靠验证某能力时 fail closed 或记录测试 skip，但不得降级为静默跟随。
- 使用随机 staging、exclusive create、fsync（平台支持时）、同目录 atomic replace；失败清理本次临时项，不覆盖已有 evidence。大小、总量、稀疏文件和权限错误均有确定性上限/错误码。

## 7. Schema 状态机与只读兼容

manifest dispatch 使用互斥五态和 reason code：

| 状态 | 判据 | `check` | `scan` |
|---|---|---|---|
| `missing` | 无 manifest | 非零，`legacy-unverifiable` | 报告 legacy，不修改 |
| `malformed` | 存在但非合法 JSON/重复 key | 非零 | 报告 malformed，不按 legacy 放行 |
| `unsupported` | 缺/未知 `schema_id`、无版本、非支持 major 或更新版本 | 非零，注明 `unversioned|foreign-schema|newer-version` | 报告 unsupported，不按 v1 误检 |
| `invalid` | 可识别 v1，但 schema/闭包/check 不通过 | 非零 | 报告 invalid-v1 |
| `valid` | v1 全部验证通过 | 零 | 报告 valid-v1 |

`schema_id="converge.archive"`，`schema_version="1.0"`；解析规则和兼容 minor 策略写入 state-schema。v1 不自动迁移旧归档，不修改 scan 输入；未来 v2 增加 reader/upgrade 命令时必须保留旧字节并显式生成新 revision，未知新版本 fail-safe 为 unsupported。

## 8. 单一 archive 编排、并发与 reopen

新增单一写路径 `archive`，不再要求 Orchestrator 人工执行 finalize/check/move 清单：

1. 对 `<slug>` 获取单写者排他锁；锁含 owner、pid、started time、nonce，超时和陈旧锁只允许通过可验证 owner-dead 规则恢复，不能静默抢锁。
2. 校验 active/done canonical roots、同卷、done 目标不存在、无未闭合 invocation/ledger；在 active 同卷随机 staging 中导入 legacy raw evidence、追加所需 capture events、生成 manifest/INDEX。
3. 在 staging 内完整 `check`；成功后将 active 保留为唯一权威源，使用同卷原子 rename 把准备好的目录提交到 done。实现可以采用 `active→backup`、`staging→done` 的受控顺序，但任何时点只允许一个被标记为 authoritative 的副本，并保留可恢复 journal。
4. 在 done 最终路径再次只读 check；成功即由“位于 canonical done root 且 valid”这一可计算状态表示 archived，不再写入 manifest 或其他闭包内文件，避免 post-check 后自我失效。若 post-check 失败，按 journal 原子回滚到 active，绝不覆盖或合并已有目录。跨卷直接拒绝，绝不声称原子。
5. 重试读取 journal 幂等恢复：目标冲突、锁冲突、移动中断、staging 残留、post-check 失败都有稳定非零退出码和人工可读提示。

`prepare` 可作为 archive 内部函数但不是用户必须串联的命令。`check`、`scan` 永远只读。

收敛后修订使用独立 `reopen`：锁定并验证 valid done 源、active 目标不存在，同卷原子移动到 active，将原 manifest 原字节移入 `evidence/revisions/<revision-id>/manifest.json` 并由新 current manifest 记录 parent hash/ref；旧 INDEX 因完全可由旧 manifest 重建而不重复保存。创建递增 `revision_id` 并使新 event sequence 从历史最大值追加；不得人工删除或改写历史 manifest。再次 `archive` 生成新 current manifest。stale-check 识别 `preparing|reopened|recoverable`，只对真正悬挂/冲突状态报警；pre-push 对新/变更 v1 done 运行只读 check。

## 9. CLI 与实现边界

保留 `scripts/archive_convergence.py` 作为唯一 CLI façade；它只负责参数解析、命令 dispatch、稳定退出码与错误呈现，不承载业务事实。实现仅用 Python 标准库，并在 `scripts/archive_contract/` 放置少量内部模块：

```text
archive_convergence.py             # thin CLI façade
archive_contract/
├── __init__.py
├── model.py                       # canonical types/schema/projection/validation
├── capture.py                     # append-only fact/event collection
├── transaction.py                 # lock/staging/archive/reopen/recovery
└── presentation.py                # read-only INDEX/diagnostics/scan/check views
```

强制依赖方向是：`capture -> model <- transaction`，`presentation -> model`，CLI façade 可以组合四者；`model` 不依赖其他内部模块，`capture` 与 `transaction` 不依赖 presentation，presentation 不依赖 capture/transaction、不得写文件或产生事实。backend adapter 只向 capture 提交声明/receipt；文件系统事务不能解释 renderer 输出；展示需求不能反向改变 owner facts。通过 import-boundary 单元测试禁止反向依赖。

CLI 提供：

- `begin-invocation`、`complete-invocation`、`recover-invocation`、`record-terminal-decision`、`record-design-review-completion`；
- `archive`、`reopen`；
- `check`、`scan`。

所有写命令只写显式 canonical roots 内部，所有失败返回稳定非零码；不调用网络/模型，不跟随归档树链接。实现是 CLI，不扩张为独立服务。若宿主无法提供 receipt、resolved model 或安全落盘能力，schema 诚实记录 evidence level/degradation，而不是编造字段；无法满足路径、锁、数据授权或 ledger 闭包时停止。

### 9.1 “30 秒审计旅程”合同

不了解 schema 的审计者不需要打开 manifest/event JSON，只使用根 `INDEX.md` 与只读 `scan/check` 输出即可完成以下最短路径：

1. `scan <done-root>`：找到目标 slug、schema 状态和一条可直接执行的 next action。
2. 打开 `INDEX.md` 首屏：看到 current final decision（值、类型、event ref）、archive/revision 状态、所有 capability/evidence degradations、未决风险和“下一阅读路径”。
3. `check <done/slug>`：得到 valid/invalid 总结；失败时每条稳定诊断都含 `code`、一句话 `summary`、归档相对 `path`（无路径则为 null）和可操作 `next_action`，并链接/指向首个需要阅读的 canonical record 或 evidence event。

INDEX 固定顺序为：`Decision`、`Integrity & Threat Boundary`、`Degradations`、`Revision Timeline`、`Event Timeline`、`Next Reads`。`Next Reads` 至少列出最终 round、retrospective、terminal decision/verdict evidence 和 design-review highlights；无 degradation/revision 也显式写 `none`。human 输出与 `--format json` 使用相同稳定 diagnostic code，summary 可以改进措辞但 code 语义在 v1 内不漂移。

验收不是声称所有人必然在 30 秒内理解复杂历史，而是保证上述三步无需 schema 知识、无需手工搜索；标准小型/多 revision/degraded fixture 的 E2E 命令链在 CI 中 30 秒内完成，并断言四个诊断字段、首屏必显信息和 next-read 路径均存在且有效。

## 10. 自动化与对抗验证

新增 `tests/test_archive_convergence.py`，以 stdlib `unittest`、临时目录和固定 golden/hash fixture 覆盖：

1. Spawn 与 Continue 的 succeeded/failed/cancelled/timeout lifecycle、全局连续 sequence、parent/round/phase/attempt 关联；terminal decision 联合类型覆盖 fresh/blank Reviewer verdict 与终止-b/c 用户决定，并拒绝 design-review 充当 final verdict、缺用户原话/来源或 round/retrospective 双向引用不一致。
2. reservation/settlement/invocation 双向绑定；孤儿、重复 receipt/instance、伪 role、字段冲突、未闭合预算均失败。
3. requested/resolved/evidence-level 合法矩阵；继承但 concrete model 不可见、非法 unknown escape、闭合 reason code。
4. manifest 与 owner event 冲突；canonical、invocation/artifact/decision/advisory events、prompt/output、snapshot、revision manifest、INDEX 的逐类删改增；联合改写只能证明在同权限威胁模型下不可检测，测试和文档不得宣称相反。
5. exact/redacted/metadata-only 的文件集合、能力降级、默认最小化、secret/外部文件拒绝、大小/总量/稀疏文件/权限错误。
6. artifact 原始字节 hash、workspace-relative/external locator 合法与禁止字段矩阵、external 默认不回读及能力降级、复制中替换、TOCTOU、symlink/junction/reparse/hardlink/ADS/设备/非普通文件拒绝；扫描链接不越界。
7. Windows 大小写、保留名、尾随点/空格、UNC、`\\?\`、NFC/NFD、中文与长路径；平台无法创建的 reparse fixture 显式 skip reason，并在 Windows CI 真跑可用子集。
8. 并发 begin/archive、锁超时/owner-dead、sequence 竞争、staging 崩溃、done 冲突、move 后 check 失败、恢复/重试；失败不污染、不覆盖、不留下两个 authoritative 副本。
9. 五态 schema dispatch：missing、malformed、unsupported（含 unversioned/未来版本）、invalid、valid；scan 字节级只读。
10. canonical Markdown 链接与 anchor、raw evidence 排除、整体改名后 check；根 allowlist 和 Unicode/case 路径碰撞。
11. 本次 active 目录 bootstrap import，及旧 consumer 继续读取根级 round/retrospective 的兼容 fixture。
12. 固定种子的 property-style 随机路径/JSON 输入，验证“不越界写、失败不移动、check 不抛未捕获异常”。
13. 独立 30 秒审计旅程 E2E：schema-naive fixture 只读 INDEX/scan/check 即定位 final decision、全部 degradation、revision timeline 与下一阅读路径；每条诊断验证 `code/summary/path/next_action`，并覆盖 valid、invalid、degraded、多 revision 四种场景。

同时运行现有 `tests/test_budget_gate.py`、新增 strict ledger 回归、`git diff --check`、Python in-memory compile、skill frontmatter 检查，以及 UTF-8 无 BOM/LF 检查。对无法在当前权限创建的 Windows 对抗对象允许明确 skip，但核心 allowlist/containment/atomic-state 测试不得跳过。

## 11. 流程与文档接线

- `SKILL.md`：将 invocation lifecycle 接到所有 Spawn/Continue；完成门禁改为单一 `archive`，禁止手工移动；明确威胁模型和 evidence mode。
- `refs/state-schema.md`：作为字段、枚举、主外键、权威/派生、哈希闭包、五态 dispatch 与 archive/reopen 状态转换的规范单源。
- `refs/orchestrator-guide.md`：只保留操作者顺序、失败恢复和 bootstrap/revision 示例，不复制 schema 表。
- `refs/framework-adapters.md`：定义每个 backend 的 requested/resolved 采集优先级、receipt 和 evidence level 合法组合。
- `scripts/hooks/stale-check.py` 与 `scripts/hooks/pre-push`：轻量接线现有钩子；前者认识 archive/reopen journal 状态，后者对变更的 v1 done 调 `check`。不新增常驻服务。
- 新增中文 bugfix 文档，记录复现、根因、真实验证、兼容和残余风险，明确同权限整体重写不在防护范围。

其中 `refs/state-schema.md` 是人类规范单源，`scripts/archive_contract/model.py` 是对应的可执行 schema/projection 单源；contract fixture 对字段、枚举、owner matrix 与文档标记做一致性检查。capture、transaction、presentation、hooks 和 adapters 都调用 model 的公开接口，不复制一套私有 schema。

## 12. 文件改动清单（按必要性）

| 必要性 | 文件 | 变更 |
|---|---|---|
| 必须 | `SKILL.md` | archive contract、invocation lifecycle、单命令门禁与诚实能力声明 |
| 必须 | `refs/state-schema.md` | v1 规范单源：schema、闭包、状态机、路径/证据策略 |
| 必须 | `refs/orchestrator-guide.md` | archive/reopen 操作与恢复步骤 |
| 必须 | `refs/framework-adapters.md` | backend provenance/receipt/evidence 等级映射 |
| 必须 | `scripts/archive_convergence.py` | 单一、轻薄的 stdlib CLI façade 与命令 dispatch |
| 必须 | `scripts/archive_contract/__init__.py` | 最小包边界与公开 API |
| 必须 | `scripts/archive_contract/model.py` | canonical types、ownership/projection、schema 与验证的可执行单源 |
| 必须 | `scripts/archive_contract/capture.py` | append-only invocation/artifact/decision/advisory 事实采集 |
| 必须 | `scripts/archive_contract/transaction.py` | lock、staging、archive/reopen、journal 恢复 |
| 必须 | `scripts/archive_contract/presentation.py` | 只读 INDEX、诊断、scan/check 呈现 |
| 必须 | `tests/test_archive_convergence.py` | 功能、兼容、故障与对抗回归 |
| 必须 | `docs/problems/bugfix/convergence-archive-auditability.md` | 中文 bugfix 记录 |
| 必须接线 | `scripts/hooks/stale-check.py` | 识别准备、修订、可恢复状态 |
| 必须接线 | `scripts/hooks/pre-push` | 对变更 v1 归档运行只读 check |
| 已准备，无需再改 | `.gitattributes` | 保持 `* text=auto eol=lf` |

不新增数据库、后台服务、单独 migration framework 或额外 CLI 包。只有实现中证明确需暴露 contract 的 README 才可在后续 plan amendment 增列，Executor 不自行扩大范围。

## 13. 验收与停止条件

- 三个 ultraverge 初始 Reviewer 的全部 blocking 均在本计划中有实现项和对抗测试；conceptual 少数派阻断不降级。
- Executor 只改 §12 清单文件，且不能把 threat-model 限制改写成 hostile same-writer 防御承诺。
- archive/check 自举 fixture、全测试、strict ledger、diff/encoding/frontmatter 全绿；任何核心安全测试 skip、budget gate 非 PROCEED 或 archive validator 失败即停止。
- fresh landing Reviewer 对规范与实现给出可执行、零 blocking；治理文件变更完成强制设计审查并向用户报告 highlights。
- 经两轮或以上 outer rounds 时执行 blank-slate 盲审。
- 完成时必须报告 evidence-mode 降级、平台能力 skip、legacy 状态和同权限整体重写残余风险，不用“已证明真实模型/历史不可篡改”等过度结论。
