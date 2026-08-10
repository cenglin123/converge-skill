# Design · OCSR ↔ converge 治理钩子对接

> 路径：`.converge/active/20260725-ocsr-converge-integration/design.md`
> 作者：glm-5.2 orchestrator | 状态：待评议 | 2026-07-25
> 上游：`plan.md` / `orchestrator-brief.md`

## 1. 问题陈述（来自 plan §背景）

OCSR 作为 converge 的 Spawn 后端时：
- `archive_convergence.py archive` fail-closed（`events-missing`）：归档契约要求每次 Spawn/Continue 经 `begin-invocation`/`complete-invocation` 记录连续序号事件（`evidence/events/`，禁止回填），而 OCSR 派发链路从未调用该协议。
- OCSR 路径未接 `budget_gate.py` 的 reserve/settle：本次人工控制 spawn 量代替机械门控。

**目标**：OCSR 驱动的完整 converge 能通过 `archive`（valid）+ done/ 只读 `check`（valid-v1）。

## 2. 决策：**独立适配脚本（adapter layer）**，不改 ocsr_dispatch 主循环

### 2.1 决策

在 **converge 仓库侧**新增 `scripts/ocsr_spawn_adapter.py`，包装 `ocsr_dispatch.py dispatch`：
- reserve（前置 gate）→ begin-invocation → 调 ocsr_dispatch → complete/recover-invocation + settle（按 outcome）。
- 保持 `ocsr_dispatch.py` **完全不变**（框架无关原则：ocsr SKILL.md §三 "脚本不做编排判断"，且本机知识库教训"运维须框架无关"——ocsr 是普适执行后端，converge 只是它的客户之一）。

### 2.2 源码证据（Occam 路径选择）

| 选项 | 优点 | 缺点 | 决议 |
|------|------|------|------|
| **A. ocsr_dispatch 加 `--converge-dir` 原生 flag** | 单文件、调用方零额外路径 | (a) 违反 ocsr SKILL.md §三"脚本不做编排判断"边界（预算/事件 = 编排判断）；(b) 把 converge 协议塞进普适执行后端，未来其它"客户"（如 release executor、独立审计）也得各自加 flag；(c) `ocsr_dispatch.py:_append_dispatch_ledger` 已是它自己的账本，再嵌套 converge 的 ledger 在同一进程内语义混乱 | ✗ 拒绝 |
| **B. converge 侧适配脚本 `scripts/ocsr_spawn_adapter.py`** | (a) ocsr 保持框架无关，converge 是它的客户；(b) 适配层只关心"调 dispatch 前后该做什么"，主循环逻辑零侵入；(c) 与 `archive_contract` 同仓库，provenance/事件 schema 可直接 import | 多一个文件、多一层调用 | ✓ **采纳** |
| C. 直接在 orchestrator prompt 里手拼命令 | 0 代码 | (a) 易遗漏 begin/complete（这恰是当前 bug 根因）；(b) 不可复用，每个 orchestrator 都要重学 | ✗ 拒绝 |

**关键证据**：
- `ocsr/scripts/ocsr_dispatch.py:51` 已暴露 `CONVERGE_LEDGER_NAME = "ocsr-dispatch-ledger.jsonl"`——ocsr **已知** converge 存在，且把"账本路径"作为 caller 显式 opt-in（`--ledger-dir`）。
- `ocsr/SKILL.md:62` 明文："脚本不做编排判断——选模型、prompt 残注入、verdict 裁决、重试时的 prompt 修订仍由 orchestrator 负责"；"预算门控由上层机制承担（如 converge 的 budget_gate）"。
- `ocsr/SKILL.md:66` 明文："skill 版仅在显式传 `--ledger-dir` 时写派发账本，不做 `.meta/converge/` 自动探测——**vault 适配层会自动补全该参数**"——这条直接预告了适配层的存在与职责。
- `converge/scripts/archive_contract/model.py:59` 已在 `ROOT_FIXED` 中含 `"ocsr-dispatch-ledger.jsonl"`，注释指向 `.meta/scripts/ocsr_dispatch.py` 的 vault-side 适配层模式——本设计是同一思路的 skill-side 落地。
- budget_gate.py 角色枚举（`ROLE_CONSUMES`）与 ocsr_dispatch.py 角色枚举（`ROLE_VALUES`）在适配层用到的 6 个角色（outer-reviewer / blind-reviewer / ultraverge-initial / executor / arbiter / design-reviewer）范围内**子集一致**——两边的全集不同（ROLE_CONSUMES 还有 contract-proposer/challenger/finalizer 和 l2-gate-reviewer；ROLE_VALUES 还有 reviewer / release-executor），但适配层只使用两边共有且 consumes 语义一致的角色，无需翻译。

### 2.3 与 plan 的"倾向适配层优先"对齐

plan §Phase 0 已写明："倾向适配层优先（保持 ocsr 框架无关，呼应知识库'运维须框架无关'教训），以源码证据定夺"——§2.2 的证据链即定夺依据。

## 3. 适配层接口设计（`scripts/ocsr_spawn_adapter.py`）

### 3.1 CLI 表面

```bash
python scripts/ocsr_spawn_adapter.py dispatch \
  --converge-active <converge-active-dir> \      # 含 gate-ledger.jsonl / _budget-state.json / evidence/
  --converge-scripts <converge-scripts-dir> \     # 含 archive_convergence.py / budget_gate.py
  --ocsr-dispatch <ocsr-scripts>/ocsr_dispatch.py \
  --role <budget_gate role> \                     # outer-reviewer | blind-reviewer | ultraverge-initial | executor | ...
  --phase <converge phase name> \                 # reviewer-round-1 / executor-round-2 / ...
  --round <int|0> \                               # canonical_round: 0 → null
  --attempt <int> \                               # attempt index
  --prompt <abs path to prompt file> \
  --model <opencode -m model id> \                # = requested provenance
  --backend <backend name> \                       # 默认 opencode
  --backend-version <version> \                    # 默认 auto-detect via `opencode --version`
  --label <label for ocsr --worker>
  --output-dir <dir> \                            # 产物目录（同时是 archive evidence source）
  --output-name <filename> \
  [--evidence-mode metadata-only|redacted|exact] \  # 默认 metadata-only
  [--watch] [--timeout <min>] \
  [--reserved-reservation-id <rid>]               # 若上层已 reserve，跳过本工具 reserve
```

**单一职责**：把"reserve + begin + dispatch + complete + settle"五步原子化；失败路径调 recover + settle failed。

### 3.2 调用顺序（happy path / failed / timeout）

**Happy path**（spawn → 产物落盘）：
```
1. budget_gate.py reserve --role <role> --target-round <round>
   → 解析 PROCEED:<rid>；非 PROCEED 直接 return（不调 begin/dispatch）
2. archive_convergence.py begin-invocation <active-root>
     --kind spawn --role <role> --phase <phase>
     --round <round> --attempt <attempt>
     --reservation-id <rid>
     --requested-provider <provider> --requested-model <model>
     --prompt <prompt-path>
     --evidence-mode <mode>
   → 解析返回 JSON 得 invocation_id 和 started event_id
3. ocsr_dispatch.py dispatch --worker <prompt|model|label>
     --output-dir <out> --output-pattern <name>
     --watch --timeout <min> --progress
     --ledger-dir <active-root>           # ← 适配层自动补全（呼应 ocsr SKILL.md:66）
     --meta task_id=... --meta role=<role> --meta scope=<consumes>
4. 检查 --output-name 是否落盘且 >0 字节
   - 落盘：调 complete-invocation
       archive_convergence.py complete-invocation <active-root> <invocation_id>
         --status succeeded
         --instance-id "<ocsr batch_id>"      # configured 层级下的非约束性关联句柄（见 §3.3）
         --receipt "ocsr-dispatch-ledger.jsonl:<rid>"
         --backend opencode --backend-version <opencode --version>
         --evidence-level configured --resolution-source cli_argument
         --resolution-reason-code backend-does-not-expose   # ← 诚实降级（见 §3.3）
         --output <产物路径> --evidence-mode <mode>
       budget_gate.py settle --reservation-id <rid> --result succeeded --instance-id "<batch_id>"
    - 未落盘（看门狗超时 / exit≠0 / error.log）：
        archive_convergence.py recover-invocation <active-root> <invocation_id>
          --status timeout|failed  --failure-reason-code timeout|backend-error
          --instance-id "<batch_id>"
        budget_gate.py settle --reservation-id <rid> --result failed|cancelled
          --pre-execution (默认 false——Start-Process 成功即模型有调用。仅 Start-Process 自身失败、cmd_dispatch 返回前终止才加 --pre-execution)
```

**Begin 失败（reserve PROCEED 但 begin-invocation 异常）**：尽快调 `settle --result cancelled --pre-execution`，写明 reason。

**Complete 失败（产物已落盘但 archive complete-invocation 异常）**：不撤销产物（已经发生），但向 stderr 报错并以非零退出；调用方决定是否 retry complete（archive 容忍 complete 重放前先 recover，但**禁止**重复 complete——`invocation-already-terminal` fail-closed）。

> **record-terminal-decision 归属**：适配层的职责是单次 Spawn 生命周期（begin→dispatch→complete/recover）。**最终 converge 终止决策（终止-a/b/c）的 terminal-decision 事件**不由适配层写入，而是由 **orchestrator** 在最后一次 fresh review Spawn 的 terminal 事件持久化后，调用 `archive_convergence.py record-terminal-decision` 登记。缺失该步骤会导致 archive 时 `final-decision-missing` 错误（`archive_convergence.py:76-77`）。

### 3.3 provenance 诚实降级（关键设计点）

依据 `refs/framework-adapters.md §Archive Contract provenance 采集` 的 opencode 行：

> | opencode | subagent type 配置 | task_id；tool response 若含 provider/model 才可记录 resolved | task_id 为 host-reported；配置 pin 为 configured，继承但 concrete 隐藏为 inherited + reason |

**OCSR 派发的 `opencode run` 在产物（Markdown 报告）中**没有稳定字段**暴露 provider/model**，且 ocsr 的 dispatch ledger 是批级别账本而非绑定至本次 `invocation` 的 tool response（见 model.py:494-513 的 PROVENANCE_MATRIX 校验逻辑）——故选择**严格诚实**的降级组合：

- `evidence_level=configured`
- `resolution_source=cli_argument`
- `resolution_reason_code=backend-does-not-expose`
- `requested_provider/requested_model`：从 `--worker` 解析的 MODEL 字段（如 `deepseek/deepseek-v4-flash` → provider=`deepseek`, model=`deepseek-v4-flash`）。
- `resolved_provider/resolved_model/resolved_family`：**必须省略**——`configured` 层级依法不允许携带 resolved 字段（model.py:498 禁止 `configured`/`inherited` 含 `resolved_model`；model.py:512-513 禁止 degraded provenance 携带 resolved 类字段）。

**为什么不能选 `host-reported`**（与评审前版本的关键修正）：

| 约束 | `host-reported` 要求 | OCSR 能否满足 |
|------|----------------------|---------------|
| reason 必须是 `None`（model.py:96） | `frozenset({None})` | ✗ OCSR 没有 tool_response 绑定，只能带降级 reason |
| 必须同时有 bound host receipt 和 concrete resolved 字段（model.py:503-508） | `host_bound && (resolved_provider && (resolved_model \|\| resolved_family))` | ✗ 无 per-invocation tool_response 可绑定；dispatch ledger 是批级别记录，非本 invocation 的 tool response |
| `configured` 合法原因（model.py:97） | `backend-does-not-expose` 和 `receipt-missing` 均在列 | ✓ 选择 `backend-does-not-expose`（后端不暴露 per-invocation 解析结果）是诚实描述 |

综上，`configured + cli_argument + backend-does-not-expose` 是 **PROVENANCE_MATRIX 下 strictest legal honest choice**（`model.py:494-513`）。

**`--instance-id` 与 `--receipt` 作为关联句柄**：尽管 evidence level 为 `configured` 时 `--receipt` 不参与 host-evidence 绑定校验，我们仍将 `--instance-id` 传 ocsr `batch_id`（格式 `YYYYMMDD_HHMMSS_<6hex>`）、`--receipt` 传 `"ocsr-dispatch-ledger.jsonl:<rid>"`。这两个字段在 `configured` 层级下是**非约束性的关联元数据**，对调试和审计追踪有意义——例如通过 batch_id 在 dispatch ledger 中反查该批次的全量派发记录。用 §3.5 的 ledger 双写语义支撑这一可追溯性。

**未来升级路径**：若后续 opencode 的 `--format json` 暴露 per-invocation `provider`/`model` 字段且绑定至本次 tool response，可将 evidence 组合升级为：
```
evidence_level=host-reported
resolution_source=host_receipt
resolution_reason_code=None
host_evidence_ref=invocation:<invocation_id>:tool-response
```
此时 `--instance-id`/`--receipt` 将从关联句柄变为约束性的 host-evidence 绑定字段。

**Pre-execution 失败**（reserve 成功但 ocsr Start-Process 失败、模型从未调用）：`recover_invocation` 自动写入 `evidence_level=unavailable`、`resolution_source=none`、`resolution_reason_code=invocation-failed-before-resolution`（capture.py:324-335）。

### 3.4 角色 → consumes 映射（直接对齐）

| `--role` (传入) | budget_gate consumes | 是否需要 round | 典型场景 |
|---|---|---|---|
| outer-reviewer | outer | 是 | converge 主循环评议 |
| blind-reviewer | blind | 是 | 盲审复核 |
| ultraverge-initial | ultraverge | 是 | ultraverge 并行初审 |
| executor | none | 否 | 主循环修复（不计 outer/blind） |
| arbiter | none | 否 | 振荡裁判 |
| design-reviewer | none | 否 | 收敛后设计审查 |
| contract-proposer / contract-challenger / contract-finalizer | none | 否 | Round 0 合同谈判 |

`round=0` 经 `canonical_round` 自动归一化为 `None`（archive_contract/model.py:103 + budget_gate.py 的同一函数）。

### 3.5 ledger 双写语义（无重复计费）

- `gate-ledger.jsonl`（converge）：reserve/settle 决策流，archive Contract 的预算依据。
- `ocsr-dispatch-ledger.jsonl`（ocsr）：派发事实流（launched/landed/failed/path_anomaly），作为 host receipt。

两账本语义独立、互不覆盖。archive Contract 的 `validate_ledger` 只看 gate-ledger；ocsr ledger 在当前 `configured` 层级下作为**非约束性关联句柄**（per §3.3），不参与 provenance 升格；未来若升级到 `host-reported`，它将转变为支撑 receipt。**不重复计费**：budget_gate 的 `model_invocation` 计数只从 gate-ledger 的 spawn_succeeded/spawn_failed(pre_execution=false) 派生。

## 4. 失败注入测试（Phase 1 包含）

为验证 recover-invocation 路径，必须构造一次"看门狗超时"：
- 派一个**故意停滞**的 prompt（例如 prompt 内指示"sleep 10 分钟不做任何事"）给 ocsr，`--timeout 2`（2 分钟看门狗），验证：
  1. ocsr 看门狗 kill 进程，ledger 写 `failed/watchdog_timeout`。
  2. 适配层调 `recover-invocation --status timeout --failure-reason-code timeout`。
  3. budget_gate settle `--result failed --pre-execution=false`（模型被调过但停滞）。
  4. archive 后 evidence/events 含完整的 started + terminal(timeout) 双事件。

## 5. 非目标（逐字保留自 plan）

- 不合并 ocsr 与 converge。
- 不做嵌套派生的成本归因汇总。
- 不改 converge 的归档契约语义与 ocsr 的派发核心逻辑（只加对接面）。

## 6. 风险

| 风险 | 缓解 |
|------|------|
| 适配层若 begin 成功但 ocsr 失败前未 recover → 孤儿 started event | 适配层用 try/finally：begin 后任何异常都尝试 recover；ocsr 失败统一映射到 recover |
| `instance_id` 用 batch_id 是降级，未来 opencode 暴露 task_id 时需升级 | 适配层注释明确；Phase 4 文档同步写明降级标志 |
| 嵌套派发可能 ocsr 内部再 spawn（深度 3） | 本期不处理；ocsr SKILL.md §七"嵌套派发失账"已预告，本期正是修复它的第一层 |
| provenance 误升格（host-reported 被解读为 observed） | framework-adapters 表 + reason code 双重标注；reviewer 评议设计文档时复核 |

## 7. 验收锚点（Phase 3 用）

- `archive_convergence.py archive <active> <done> <slug>` 返回 `status: archived`。
- `archive_convergence.py check <done>/<slug>` 返回 `valid-v1`。
- `evidence/events/` 中 sequence 连续无缺口，started 与 terminal 1:1。
- `gate-ledger.jsonl` 中每条 reservation 都有对应 spawn invocation 的 started.reservation_id；无孤儿 reservation（`list-orphan-reservations` 返回 `none`）。
- ocsr ledger 与 archive manifest 中的事件在时间戳、字节数、模型 ID 上一致。

## Revision Log

### Round 1 fix (2026-07-25)
- Blocking #1: §3.3 provenance changed host-reported→configured per PROVENANCE_MATRIX constraint. Added model.py:494-513 reference.
- Suggestion #1: §3.1 added --backend, --backend-version params.
- Suggestion #2: §3.2 added orchestrator record-terminal-decision step note.
- Suggestion #3: §3.2 failure-path table made pre_execution default explicit.
- Suggestion #4: §2.2 ROLE_VALUES alignment claim scoped to adapter subset.
- **[Orchestrator Detection]** Residual cleanup: §3.2 happy-path example block and §3.5 ledger semantics still referenced the old `host-reported/host_receipt/receipt-missing` combination after executor's main fix; orchestrator applied the same substitution mechanically to keep the doc internally consistent. source: orchestrator_self (boundary_check: violated-but-documented; same fix executor already applied to §3.3, no semantic change).
