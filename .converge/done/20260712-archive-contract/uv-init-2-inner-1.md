---
reviewer: uv-init-2
review_mode: inner-loop-acceptance
iteration: 1
verdict: 可执行
original_blocking_count: 4
accepted_count: 4
rejected_count: 0
plan_amendment_required: false
contract_amendment_required: false
---

# UV2 Inner-loop 验收 · 第 1 次

## 最终 verdict

```yaml
verdict: 可执行
blocking_issues: []
acceptance_summary:
  UV2-B1: Accepted
  UV2-B2: Accepted
  UV2-B3: Accepted
  UV2-B4: Accepted
rationale: >-
  修订后的 plan.md 已逐条闭合原四项阻断的 required_fix 与 acceptance，
  并为对应路径配置了确定性测试。未发现原阻断仍有未落实部分。
```

## 逐条验收

### UV2-B1 · Accepted

原问题：现有 ultraverge、盲审、设计审查等产物没有根级 allowlist、单一权威映射和自举迁移契约。

验收依据：

- §3 给出完整根级 canonical allowlist，明确保留 `round-N.md` 与 `design-review.md`，并将 `uv-init-*`、盲审、仲裁、landing、execution、prompt/report 等 raw 产物映射到 `evidence/invocations/`。
- §3 明确根级文件是 canonical 摘要、invocation evidence 是 raw 字节，禁止双份权威；无法唯一绑定时 fail closed，不靠文件名猜角色或模型。
- §3 要求 INDEX 将 canonical event 链接到 invocation evidence，并排除 raw 内容中的链接导航语义。
- §3 与 §10.11 明确使用本次 `20260712-archive-contract` active 目录作为 bootstrap fixture，覆盖当前 `uv-init-1/2/3` 等真实产物，同时验证旧 consumer 继续读取根级 round/retrospective。

结论：满足原 required fix 与 acceptance，`Accepted`。

### UV2-B2 · Accepted

原问题：active→done 仅有 happy path，没有原子提交、目标冲突、移动失败、中断恢复和修订回流协议。

验收依据：

- §8 将完成流程收敛为单一 `archive` 写路径：排他锁、同卷 staging、staging 内 check、受控原子 rename、done 最终路径 post-check、成功后才确认 `archived` terminal state。
- §8 明确拒绝跨卷、覆盖和目录合并；done 冲突、锁冲突、移动中断、staging 残留与 post-check 失败均有 journal、稳定非零退出码和幂等恢复。
- post-check 失败时按 journal 回滚到 active，要求任何时点只存在一个 authoritative 副本。
- 收敛后修订由独立 `reopen` 完成，验证 valid done、active 不存在、同卷移动、revision id 和 sequence 续接，不再要求人工删除 manifest/INDEX。
- §8/§11 将 stale-check 接到 `preparing|reopened|recoverable` 状态；§10.8 覆盖 done 冲突、move 后 check 失败、崩溃恢复和重试。

结论：满足原 required fix 与 acceptance，`Accepted`。

### UV2-B3 · Accepted

原问题：record-run 无法记录 failed/cancelled/timeout，prompt/output 落盘时序不清，模型配置或继承可能被误写成实际观测值。

验收依据：

- §5 用 `begin-invocation → host Spawn/Continue → complete-invocation` 定义无歧义生命周期，并提供 `recover-invocation` 闭合中断调用。
- terminal 状态覆盖 `succeeded|failed|cancelled|timeout`；仅 succeeded 要求 output，其他状态必须记录闭合 reason code，started 不允许归档。
- sequence 由 CLI 在锁内分配；§4/§6 定义原始字节 hash、binary evidence、严格 JSON、UTF-8 无 BOM/LF、exclusive create、atomic replace 和失败清理，消除了手写落盘步骤。
- §5 将 requested 与 resolved provider/model 分离，并定义 `observed|host-reported|configured|inherited|unavailable` 证据等级、resolution source 和 reason code；明确禁止把 configured/inherited 升格为 observed。
- §5/§11 要求 adapters 分别定义 opencode、Codex、Claude Code、orchestrator_self 的字段可得性和合法组合；ledger 与 invocation 做双向一一绑定。
- §10.1-3 覆盖成功/失败/取消/超时、继承但 concrete model 不可见、非法 unknown escape 和 ledger 双向关联。

结论：满足原 required fix 与 acceptance，`Accepted`。

### UV2-B4 · Accepted

原问题：旧归档、损坏 manifest、无版本 manifest 与未来 schema 没有互斥 dispatch，可能误按 v1 检查或误称 legacy。

验收依据：

- §7 定义互斥五态：`missing`、`malformed`、`unsupported`、`invalid`、`valid`。
- `unsupported` 明确细分无版本、foreign schema、未来版本；未知新版本 fail-safe 报 unsupported，不误称 invalid v1。
- §7 表格明确 check 对前四态返回非零、scan 分别报告且不修改输入；valid v1 才返回成功。
- `schema_id="converge.archive"`、`schema_version="1.0"` 及 minor 兼容规则指定写入 state-schema，避免用日期或 manifest 存在性猜版本。
- §10.9 明确测试 missing、malformed、unversioned/未来 unsupported、invalid、valid，并验证 scan 字节级只读。

结论：满足原 required fix 与 acceptance，`Accepted`。

## 验收边界

本次仅复查 UV2-B1..B4 是否已被计划修订闭合；没有对修订计划引入新的审查范围。上述 `Accepted` 表示计划已具备可执行规格与验收路径，不替代后续对实际实现和测试结果的 landing review。
