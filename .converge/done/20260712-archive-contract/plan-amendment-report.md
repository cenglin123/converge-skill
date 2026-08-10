---
type: plan-amendment-report
status: completed
object_slug: 20260712-archive-contract
amended_at: 2026-07-12T13:20:00+08:00
executor_role: ultraverge-plan-amendment-executor
modified_files:
  - plan.md
---

# Archive Contract v1 计划修订报告

## 结果

已把三个 ultraverge 初始 Reviewer 的所有 blocking 合并进单一可实施计划。修订后的契约把目标收窄为“归档时点内部一致性与声明 provenance”，并以标准库 CLI、单写者锁、invocation lifecycle、冻结 manifest、派生 INDEX、五态 schema dispatch、默认数据最小化和单一 `archive`/`reopen` 编排闭合实现路径。

本次仅修改 `plan.md`，未修改目标代码、skill 或治理文档。

## Blocking resolution map

| Reviewer issue | 处理结果 | 计划位置 |
|---|---|---|
| AC-1：manifest/sidecar/canonical 无唯一权威与哈希闭包 | resolved：sidecar 是采集期 append-only 权威；manifest 是归档后冻结事实索引；INDEX 只由 manifest 派生。manifest 承诺 canonical、sidecar、evidence、snapshot 的精确路径/hash/size，并从底层重新派生校验；明确不自哈希及同权限整体改写边界。 | §4 |
| AC-2：run 无法重建 Continue/失败与 ledger/round 关联 | resolved：run 提升为 invocation lifecycle；定义 begin/complete/recover、Spawn/Continue、连续 sequence、event/parent、reservation、round/phase/attempt 和四种 terminal status。 | §5 |
| AC-3：artifact hash、复现能力、workspace、TOCTOU 不明确 | resolved：hash 固定为捕获原始字节 SHA-256；定义 byte、snapshot/redacted/identity-only、workspace identity、POSIX locator、句柄读取与前后 identity 复核。 | §2、§6 |
| AC-4：模型 provenance 是未分级声明 | resolved：拆分 requested/resolved provider/model/family，增加 backend/version、evidence_level、resolution_source 和闭合 reason code；adapters 定义合法组合。 | §5、§11 |
| AC-5：canonical 导航与 raw evidence 边界不清 | resolved：canonical/generated Markdown 的真实链接必须使用归档内相对路径并验证 anchor；raw prompt/output 保持字节不变并排除导航判定；整体移动后复验。 | §3、§10 |
| AC-6：legacy/schema dispatch 与部分写入无状态机 | resolved：定义 missing/malformed/unsupported/invalid/valid 五态及 reason；未知版本 fail-safe；archive 原子 staging/journal，scan 只读不迁移。 | §7、§8 |
| UV2-B1：现有 uv-init/盲审/设计审查等产物无迁移契约 | resolved：列出根 canonical allowlist；逐类映射 uv-init、blind、arbitration、landing、execution、prompt/report 到 invocation evidence；design-review 变为 canonical 摘要；增加本次 active 自举 fixture。 | §3、§10.11 |
| UV2-B2：active→done 无原子提交与恢复 | resolved：单一 archive 在锁内完成 prepare、同卷 staging/check/rename、done post-check 和 journal rollback；拒绝覆盖、合并和跨卷；reopen 负责修订。 | §8 |
| UV2-B3：失败 Spawn 丢失且实际模型证据等级未定义 | resolved：failed/cancelled/timeout 可无 output 但必须闭合 reason；begin 在调用前冻结 prompt，complete 绑定 receipt/settlement；模型 provenance 使用证据等级而非过度声明。 | §5 |
| UV2-B4：旧/未来 schema dispatch 不完整 | resolved：五态覆盖 no manifest、JSON 损坏、无版本/外来/未来 schema、invalid v1 与 valid v1；check/scan 行为和只读策略明确。 | §7 |
| SEC-1：自包含 hash 被误称历史/模型真实性证明 | resolved：威胁模型明确只保证归档时点内部一致性，不能抵抗同权限整体重写；hash 不是认证；模型能力随 evidence level 降级。未引入超出项目范围的外部信任锚。 | §1、§4、§13 |
| SEC-2：Windows reparse/symlink/ADS/TOCTOU 边界缺失 | resolved：canonical root allowlist、平台感知 containment、UNC/extended/ADS/设备拒绝、reparse/hardlink/非普通文件拒绝、句柄复核、随机 staging/exclusive create/atomic replace。 | §6 |
| SEC-3：sequence 与 finalize 无并发协议 | resolved：sequence 由 CLI 在单写者锁内原子分配；evidence 使用临时项与原子提交；archive 同卷 staging/journal；锁超时和 owner-dead 恢复有确定性策略。 | §5、§8 |
| SEC-4：ledger 与 invocation 可分别伪造 | resolved：archive/check 复用严格 ledger validator，验证 reservation/settlement/invocation 双向全覆盖与字段一致；孤儿、伪 role、重复 receipt、状态冲突 fail closed，同时保留同权限攻击边界。 | §5 |
| SEC-5：默认持久化 prompt/output/artifact 泄密 | resolved：默认 metadata-only；redacted/exact 必须显式选择，外部文件另需新鲜授权；secret/设备默认拒绝，locator 脱敏，限制单文件/总量，默认离线不回读源。 | §2、§6 |
| SEC-6：manifest/check 未覆盖完整文件集合 | resolved：manifest 精确枚举根 canonical、sidecar、prompt/output、metadata/snapshot；拒绝额外/缺失/碰撞文件；canonical JSON 严格解析；INDEX 从 manifest 重建比较；scan 不跟随链接。 | §3、§4 |
| TST-1：缺少并发、路径、故障和联合篡改对抗测试 | resolved：扩充为 12 组矩阵，覆盖 lifecycle/ledger、联合篡改边界、证据模式、Windows 特殊路径、链接/TOCTOU、并发/崩溃恢复、schema 五态、bootstrap 和固定种子 property-style 测试；保持 stdlib，并禁止声称可防 hostile same-writer。 | §10 |

## Reviewer suggestions 的吸收情况

- 加入 `reopen` 和 revision id，禁止人工删除旧 manifest/INDEX；sequence 从历史最大值追加。
- source drift 改为显式三态、默认离线，不自动读取 workspace 外路径。
- 时间戳只用于展示与基本顺序校验；事件权威顺序由锁内 sequence 与 receipt/parent binding 决定。
- 根目录使用显式 allowlist，不使用容易绕过的 transient glob 黑名单。
- prompt/output 使用 exact/redacted/metadata-only 三模式，避免把 redacted 证据误称 exact。
- 文件变更清单仅增加必要的 stale-check/pre-push 轻量接线，不扩张为独立服务或 migration framework。

## 自检

- 所有 17 个 blocking（AC-1..6、UV2-B1..4、SEC-1..6、TST-1）均有明确计划条款与验收路径。
- threat model、数据最小化、provenance evidence level 与 reproduction capability 的能力声明一致。
- `archive` 是唯一完成编排者；`check/scan` 只读；`reopen` 是唯一归档修订入口。
- 实现范围仍为一个 stdlib CLI、现有 refs/skill/hook 接线、测试和 bugfix 文档，没有新增常驻组件。

## Amendment 2：inner-loop AC-1 / AC-3

根据 `uv-init-1-inner-1.md` 的两项 Rejected 做了局部收紧：

| Inner-loop issue | 状态 | 修订映射 |
|---|---|---|
| AC-1：final verdict 事件类型仍未闭合，design-review 被错误列为 verdict 来源，终止-b/c 缺 user decision event | resolved | §4 将 `final_verdict_ref` 限定为 fresh/blank-slate Reviewer verdict event 或终止-b/c user-decision event；§5 定义闭合联合类型，用户事件必须保存用户原话、可审计 source reference 与已呈现降级引用。design-review 明确降为 advisory completion，schema 禁止其产生或覆盖 final verdict。manifest、最终 round 与 retrospective 必须以同一 event id/value 双向一致。§10.1 增加非法引用与缺失用户证据测试。 |
| AC-3：workspace 外 artifact 与必填 workspace-relative path 自相矛盾 | resolved | §6 将 `source_locator` 改为 tagged union：workspace-relative 分支必填 `workspace_id/path` 并禁止 external 字段；external 分支必填脱敏 `display_locator`、`portable:false`、新鲜 `authorization_ref`，禁止 workspace/path/绝对可解引用字段。external 默认 `source_resolution=disabled`，check/source_drift 不回读并明确能力降级；§10.6 增加联合类型字段矩阵测试。 |

Amendment 2 只修改 `plan.md` 并追加本报告，没有触碰任何目标实现或治理文档。

## Amendment 3：用户采纳 design-review highlights

用户明确采纳 `design-review.md` 的三个 highlights 后，计划完成以下设计收紧：

| Highlight | 状态 | 修订映射 |
|---|---|---|
| 单一 CLI 入口内部职责过度集中 | adopted / resolved | §9 保留 `scripts/archive_convergence.py` 唯一 CLI façade，同时新增小型 `scripts/archive_contract/` 包：`model.py`、`capture.py`、`transaction.py`、`presentation.py`。依赖固定为 `capture -> model <- transaction`、`presentation -> model`；presentation 只读且禁止反向依赖，CLI 仅做 dispatch/错误呈现。§12 同步更新必要文件清单，没有引入服务、数据库或签名系统。 |
| 多源互证但缺逐字段 owner，append-only 与可变 sidecar 冲突，关键事件/revision 无物理落点 | adopted / resolved | §3 将事实存储改为 `evidence/events/<sequence>-<event-id>.json` append-only event log；begin/terminal 各写新 event，不原地更新。§5.1 新增字段级 ownership/projection matrix，覆盖 invocation status、role/round/phase、settlement、terminal decision、design-review completion、model provenance、artifact identity、revision、manifest 和 INDEX。terminal decision/design advisory 位于 event log；旧 revision manifest 位于 `evidence/revisions/<revision-id>/manifest.json`，旧 INDEX 不重复保存。冲突一律 fail closed。 |
| 30 秒目标没有独立审计旅程与 UX 验收 | adopted / resolved | §9.1 定义 schema-naive 三步旅程：scan → INDEX 首屏 → check；INDEX 固定显示 final decision、threat boundary、degradations、revision、timeline 和 next reads。稳定诊断统一包含 `code/summary/path/next_action`。§10.13 增加 valid、invalid、degraded、多 revision 的 30 秒 E2E，不夸张承诺复杂历史的人类理解时间。 |

同时消除了 design review 指出的两个相邻歧义：done post-check 成功后不再写闭包文件，archived 状态由 canonical done location + valid 派生；reopen 只保存前 revision manifest，不永久复制可重建 INDEX。

Amendment 3 仍只修改 `plan.md` 并追加本报告，未修改目标实现、skill 或治理文档。
