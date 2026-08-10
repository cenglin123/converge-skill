---
reviewer: uv-init-2
review_focus: workflow-wiring-backward-compatibility-operations
verdict: 阻断需修复
blocking_count: 4
highest_severity: architectural
plan_amendment_required: true
contract_amendment_required: false
drift_detected: false
rubric_scores:
  correctness: 3
  completeness: 2
  consistency: 2
  maintainability: 3
  operability: 2
---

# Ultraverge 初始评议 · Reviewer 2

## Verdict

```yaml
verdict: 阻断需修复
rationale: >-
  方向正确，且保留根级 canonical 文件、schema_version 能力标记、相对链接和
  legacy-unverifiable 是合理的兼容基线；但计划尚未把现有 ultraverge 产物、
  active→done 的失败恢复、收敛后修订，以及 manifest 非 v1 情形接成可执行状态机。
  按当前文字直接实现，会让本次自举归档自身无法 finalize，或在移动失败/旧归档扫描时
  产生错误阻断，因此不能直接执行。
blocking_severities:
  architectural: 2
  structural: 2
suggestions_count: 4
```

## Q1-Q5 前置自检

| 问题 | 结论 | 依据 |
|---|---|---|
| Q1 产物身份是否明确 | pass | `manifest.json` 是事实层、`INDEX.md` 是导航层、根级 canonical 文件继续作为既有 consumer 接口，身份清楚。 |
| Q2 边界是否诚实 | blocking | “每次 fresh Spawn 都记录”与“拒绝空 output”没有覆盖 spawn 失败、取消、工具只返回内存文本、模型不可观测等真实边界。 |
| Q3 数据是否保持事实纯度 | blocking | `provider/model/family` 未区分 observed、configured、inherited、self-reported；仅有 `model_resolution=unavailable` 不足以防止把配置推断写成实际模型事实。 |
| Q4 职责边界是否合理 | blocking | `finalize/check`、目录移动和 stale hook 之间没有明确单一编排者及提交/恢复顺序；“成功后才允许移动”仍留下半完成状态。 |
| Q5 命名是否一致 | pass-with-suggestion | record-run/finalize/check/scan 基本一致；但 legacy、unsupported schema、invalid v1 尚未形成互斥状态名。 |

## DR1-DR7 设计审查

| 维度 | 结论 | 评议 |
|---|---|---|
| DR1 目的与身份 | 4/5 | 30 秒定位、事件复盘、精确版本和模型谱系均对应已确认缺口，没有为“完整”而造实体。 |
| DR2 可维护性 | 3/5 | 单个标准库 CLI 集中契约是可维护方向，但若目录状态机、schema dispatch、hash/link 校验全隐含在命令分支中，后续恢复逻辑会难以推理；应先把状态转换和错误分类写成表。 |
| DR3 可扩展性 | 3/5 | `schema_version` 提供扩展点，但计划只定义 v1/无 manifest，没有定义未知新版本和损坏 manifest 的前向兼容行为。 |
| DR4 数据纯度与可审计性 | 3/5 | hash、字节数、snapshot 与 run entry 是强事实层；模型来源语义和失败 run 记录仍可能混入推断或丢失事件。 |
| DR5 职责边界 | 2/5 | archive CLI、Orchestrator 移动、stale-check 三方对“何时 completed、何时可见于 done、谁负责恢复”尚未闭合。 |
| DR6 一致性与命名 | 2/5 | 新根级 clutter 规则与当前 `uv-init-*.md`、盲审/设计审查产物体系不一致；`manifest.json` 存在也不等于 v1。 |
| DR7 复杂度与残留冗余 | 3/5 | evidence/runs + artifacts 的复杂度由真实审计需求支撑；但若同时保留根级原始 reviewer 输出和 `output.md` 会双份权威，若一律迁移又会破坏现有 consumer，必须明确一处 canonical、一处 raw evidence 的映射。 |

## Blocking issues

### B1 · 当前 ultraverge/盲审/设计审查产物没有迁移契约

```yaml
id: UV2-B1
severity: architectural
attribution: plan_defect
rubric_gap: false
plan_amendment_required: true
problem: >-
  计划禁止根级 transient evidence，并只明确 round-N.md 为权威摘要；但当前流程和
  stale-check.py 明确认识 uv-init-*.md、round-*.md、blind-recheck-*.md，SKILL.md 还要求
  design-review.md 位于归档根。正在评议本计划的 uv-init-1/2/3 本身就是根级文件。
  计划既未把这些文件列入 canonical allowlist，也未定义 finalize 如何导入/重写为
  evidence/runs，导致本次自举归档很可能被自己的 clutter check 拒绝。
required_fix:
  - 列出完整根级 canonical allowlist，至少明确 round、uv-init、blind-recheck、design-review、arbitration/landing 现有产物各自去向。
  - 为每类现有文件定义 source-of-truth 映射：根级摘要保留还是迁入 raw output；禁止同时成为两份权威。
  - 增加“用本次 20260712-archive-contract active 目录原样 finalize”回归夹具，证明自举路径可过。
acceptance: >-
  finalize 能处理现有 ultraverge 初审、盲审和设计审查命名；check 不误报合法 canonical，
  且 INDEX 可导航至每个事件及其 raw run evidence。
```

### B2 · active→done 没有原子提交、冲突和失败恢复协议

```yaml
id: UV2-B2
severity: architectural
attribution: plan_defect
rubric_gap: false
plan_amendment_required: true
problem: >-
  “finalize/check 均成功才移动”只定义 happy path。finalize 在 active 中生成 status/manifest 后，
  move 可能因 done 同名目录、跨卷、文件占用或中断失败；现有 stale-check 随后会把
  current_phase: completed 的 active 目录报 CRITICAL。反过来，移动前 check 也没有证明 done
  路径下的最终布局。收敛后修订还要求 done→active 并删除生成物，进一步扩大半完成窗口。
required_fix:
  - 定义明确状态机和单一编排顺序，例如 prepared(active) → move/rename → check(done) → archived；不要在最终落位前宣称 archived。
  - 定义 done 目标已存在、移动失败、移动后 check 失败、进程中断时的非破坏性恢复/重试行为与退出码。
  - finalize、check 必须幂等；禁止覆盖已有 done 目录或静默合并两个归档。
  - 更新 stale-check 接线，使合法 prepared/revision 状态不被当成“请直接 archive”的错误操作提示，同时真正半成品仍可检出。
acceptance: >-
  自动化测试覆盖目标冲突、move 后 check 失败和中断后重试；任何失败都只留下一个可恢复的
  权威副本，且不会把未通过最终校验的目录宣称为 done。
```

### B3 · record-run 无法完整记录失败 Spawn，且“实际模型”证据等级未定义

```yaml
id: UV2-B3
severity: structural
attribution: plan_defect
rubric_gap: false
plan_amendment_required: true
problem: >-
  契约要求每次 fresh Spawn 有 run entry，却又拒绝空 output；真实 spawn 可能 failed、cancelled、
  timeout，且不同框架常只把 prompt/response 暂存在编排器内存。当前 adapters 也说明 Codex/opencode
  常为继承或 agent-type 配置，未必暴露实际 concrete model。若只接受 completed output，失败 spawn
  会从 provenance 消失；若把 inherited/configured 当 observed，则“实际模型谱系”声明过强。
required_fix:
  - 把 run 生命周期拆成可执行的 begin/complete，或让 record-run 支持 terminal failed/cancelled 状态；失败允许无 output，但必须有错误分类、时间和已知 provenance，且 entry 仍不可丢。
  - 定义 prompt/output 从工具返回值安全落盘的责任方、UTF-8/LF 规则、原子写和 record-run 调用顺序；“Spawn 后立即”改成无歧义时序。
  - 为 provider/model/family 增加 evidence level/source（observed、host-reported、configured、inherited、unavailable），禁止把推断升级为 observed。
  - 对 Claude Code、opencode、Codex、orchestrator_self 分别给出可获得字段、不可获得字段和 unknown_reason 固定枚举/自由文本边界。
acceptance: >-
  测试覆盖 succeeded、failed、cancelled、timeout、模型继承但 concrete model 不可见、模型已知却写 unknown；
  manifest 能证明每个 budget-settled spawn 都恰有一个 run entry，反向亦成立。
```

### B4 · 旧归档与未来 schema 的 dispatch 不完整

```yaml
id: UV2-B4
severity: structural
attribution: plan_defect
rubric_gap: false
plan_amendment_required: true
problem: >-
  非目标明确说以 schema_version 而非日期判断能力，但 scan 只规定“无 manifest = legacy”。
  真实旧归档可能已有同名 manifest，却没有 schema_version、schema_version 非 v1、JSON 损坏，
  或是未来版本。把“manifest 存在”直接等同 v1 会破坏只读兼容；把未知新版本按 v1 严检又会
  造成前向不兼容。
required_fix:
  - 定义互斥分类：legacy-no-manifest、legacy-unversioned-manifest、v1-valid/v1-invalid、unsupported-newer-schema、malformed-manifest。
  - 明确 check 与 scan 对每类的 stdout/stderr、退出码和是否阻断；scan 永不修改旧归档。
  - schema_version 使用精确解析规则，并为未知更高版本 fail-safe 报告“unsupported”，不要误称 invalid v1。
acceptance: >-
  测试至少覆盖无 manifest、无版本 manifest、损坏 JSON、v1、未知更高版本，且所有旧目录字节保持不变。
```

## Suggestions

```yaml
suggestions:
  - id: UV2-S1
    area: revision
    suggestion: >-
      不要把“删除旧 INDEX/manifest”作为孤立人工步骤。增加显式 reopen/revise 命令或至少一个
      确定性 preflight：验证 done 源、active 目标、保留 run sequence 与原 manifest 备份信息，
      再进入 revision 状态。新 run sequence 必须从已存最大值追加，禁止复用。
  - id: UV2-S2
    area: artifact-revision
    suggestion: >-
      manifest 为 reviewed artifacts 增加 revision/epoch 或 finalization_id，明确重新 finalize 时是复用
      原快照还是捕获新快照；避免同一路径多次修订后 artifact 表无法说明“哪轮审了哪一版”。
  - id: UV2-S3
    area: consumer-compatibility
    suggestion: >-
      在测试中加入一个“旧 consumer 仍直接读取根级 round-N.md/retrospective.md”的夹具，并验证
      新 INDEX/manifest 是增量接口而非替代接口；这比只测新 CLI 更能兑现兼容承诺。
  - id: UV2-S4
    area: scope
    suggestion: >-
      `archive_convergence.py` 四个子命令可以保留在一个 CLI，但内部应共享 schema/path/hash 原语，
      并把状态转换表放进规范；不要再增加手写 cleanup/move 清单，否则运维复杂度会超过归档问题本身。
```

## Rubric scores

```yaml
rubric_scores:
  correctness:
    score: 3
    reason: 核心数据模型合理，但失败 run、最终落位校验和 schema dispatch 会产生错误事实或误判。
  completeness:
    score: 2
    reason: happy path 完整，真实的失败恢复、自举产物、修订 epoch、旧/未来 schema 路径缺失。
  consistency:
    score: 2
    reason: 与 SKILL/stale-check 的 uv-init、blind、design-review 根级约定尚未对齐。
  maintainability:
    score: 3
    reason: 单 CLI、标准库和生成式 INDEX 是优点；状态转换与 provenance 证据等级需显式化。
  operability:
    score: 2
    reason: 目前仍需要人工删除生成物、移动目录和判断恢复点，且中断后没有确定性续跑命令。
```

## 可执行结论

先修 B1-B4 再交 Executor。四项都可通过收紧计划和测试矩阵解决，无需推翻 evidence/runs、artifact snapshot、INDEX/manifest 双层结构；因此 verdict 为“阻断需修复”，不是“需重新设计”。
