---
type: retrospective
object_slug: 20260911-op-envelope-a-tooling-hardening
generated_at: 2026-09-12T00:00:00Z
---

# Retrospective · 20260911-op-envelope-a-tooling-hardening

## 1. 结束模式

标准评议严格收敛（`review_mode: standard-review`，未升级 ultraverge）。4 轮计划修订 + 5 轮 fresh outer 评议，终局 round-5 返回 `可执行` 且零阻断；Phase 0 升级闸门全程未触发（`refs/orchestrator-guide.md`、`refs/state-schema.md` 未修改）。

## 2. 阻断轨迹

| 轮次 | verdict | 阻断数 | 主要构成 |
|---|---|---|---|
| R1 | 阻断需修复 | 4 | B1 治理边界未决；B2 连续编号两处实现只挂一处；B3 **原 O4 诊断被证伪**；B4 默认值自相矛盾 |
| R2 | 阻断需修复 | 4 | B5 `ingest-verdict` 声明门与 guide:248 冲突；B6 漏 `test_loop_a_coverage.py`；B7 漏 `_ensure_te_companion`；B8 `validate_ledger` 符号不存在 |
| R3 | 阻断需修复 | 1 | P1 D2 漂移门打断 `test_budget_gate.py` 既有用例未枚举（+ P2/P3/P4 非阻断） |
| R4 | 阻断需修复 | 1 | N1 D3 finish 降级打断既有 finish 用例未枚举（+ N2/N3/N4 非阻断） |
| R5 | 可执行 | 0 | 穷举扫描附录独立验证通过 |

单调下降 4 → 4 → 1 → 1 → 0；归因以 `plan_defect` 为主，无 conceptual 级未决。

## 3. Antipattern 巡查

| Round | 类型 | 对象 | 触发结果 |
|---|---|---|---|
| R1 | wrong_root_cause | O4 诊断"取消预约占号" | 命中；Reviewer 实核证明连续编号检查只读文件系统产物、不读 ledger；真因是"预约 `target_round` vs 产物文件名错位" |
| R3/R4 | enumeration_gap（新） | 新增门禁 × 既有测试调用点 | 连续两轮命中同一类：新增门禁会打断既有测试，而 File Matrix 未完整枚举 → "全量测试绿"与"范围受限"互斥 |
| 实施 | self_hosting_live_migration_race（新） | 在飞适配器进程 vs 中途上线的 gate 门禁 | 命中：实施者改 `budget_gate.py` 期间，内存中运行的旧版适配器 settle 被新门禁判 `FAIL_CLOSED`（rc=30），产生 1 条真实 `[manual-fallback]` |
| 审计 | substring_counting（新） | `finish` 的 `[manual-fallback]` 计数 | 命中：按子串计数把正文 18 次字面量引用计成手工转移；已修为行首锚定 |
| — | identity_crisis / false_generality / environment_lock-in | — | 本对象未命中（环境项已在 r2 沉淀为验证前置：长路径 TEMP） |

## 4. Executor 路径依赖评估

计划修订未做折中小修：R1 后按评议分支**收窄**（D3 去 `ingest-verdict`、D2 不入 ledger 语义、加升级闸门）；R1 的 O4 方案被整体替换为"预约号钉到文件系统推导的下一个连续轮号"。R4 后以**穷举扫描附录**（`scripts/`+`tests/` 全部记账与编排调用点逐条判定）取代"每轮补一个漏点"，一次性关闭枚举缺口。

## 5. Reviewer 间 Verdict 分歧分布

| 轮次 | Verdict | 阻断数 | 归因分布 |
|---|---|---|---|
| R1 | 阻断需修复 | 4 | conceptual / architectural / implementation / evidence |
| R2 | 阻断需修复 | 4 | implementation ×3 / architectural ×1 |
| R3 | 阻断需修复 | 1 | implementation ×1（+ wording ×2、architectural ×1 非阻断） |
| R4 | 阻断需修复 | 1 | implementation ×1 |
| R5 | 可执行 | 0 | — |

各轮 Reviewer 均为 fresh、跨厂商；无同源连带分歧。

## 6. 降级影响评估

- 模型 provenance：全部派发使用 `deepseek/deepseek-flash`（OCSR configured），非宿主 host-reported；独立性成立，但模型解析证据强度弱于宿主原生 spawn。
- `DEGRADED:manual-fallback=1`：唯一 1 条真实手工转移——实施派发（`reservation 871cc12196b2`）完工后，在飞的旧版适配器无法用新门禁 settle，由编排层用 `--manual-fallback` 补结算；reason 已写入 `attempts.md`。
- 记账误分类（**如实记录、未回填**）：
  1. 白名单校验阶段失败（模型从未调用）被记为 `spawn_failed pre_execution=false`；
  2. 4 次"原地修订 `plan.md`"的成功 Executor 被 ocsr 判为"非预期覆盖既有文件"→ exit≠0 → 记为 `failed/backend-error`。
  两者均为 fail-safe 但污染 `model_invocation` 计数，属适配器/派发层缺陷，已列入后继对象建议。
- 预算：outer 使用 5/8，未触天花板，未使用 blind/ultraverge 额度。

## 7. 经验教训

- **最值得独立挑战的是"诊断"，不是"方案"**：本轮 R1 直接证伪了编排层对 O4 根因的判断。计划里"根因分析"必须被当作可证伪断言，并要求 Reviewer 实核证据链。
- **新增门禁 = 既有测试的枚举义务**：任何在 gate/编排层新增 fail-closed 门禁的计划，必须同时穷举"会被打断的既有调用点"，否则"全量测试绿"与"范围受限"不可兼得。应把该扫描上升为实施前置步骤。
- **自指改造要先停流**：改造编排/门禁自身时，在飞的同族进程仍持旧版代码，跨进程 live-migration 会 fail-closed。正确顺序是先停流、再改门。
- **计数型判定不要用子串计数**：`[manual-fallback]` 这类会被正文引用的字面量必须行首锚定，否则门在"聊过这件事"的对象上持续误触发。
- **收窄是避免 ultraverge 的合法路径**，但必须在计划里写明"若实现必须触及第三部规范句则停止升级"的硬闸门，否则收窄只是措辞。

## 8. 后续建议

- 交后继对象 **C（成本治理 O5+O6）** 与 **B（契约更正 O1+O3，ultraverge）**。
- 建议把"新增门禁 × 既有调用点穷举扫描"写入实施前强制步骤（本对象的失败模式可复用为检查表）。
- 建议把 `self_hosting_live_migration_race`、`substring_counting`、`enumeration_gap` 三个新反模式纳入反模式清单。
- 适配器层两个记账缺陷（pre-execution 误分类、原地修订误判为 backend-error）建议独立小对象处理，不塞入 C/B。

## 9. Round 0 合同谈判评估

| 维度 | 评估 |
|------|------|
| 是否启用 | 否（standard-review，无 Round 0 谈判环节） |
| contract 是否减少预期错位 | 不适用 |
| contract_amendment 触发次数 | 0 |

---

## 实施结果（2026-09-12）

### 实施阶段与产出

| 阶段 | 执行者 | 产出 |
|---|---|---|
| Phase 1 扫描 + TDD 红测 | OCSR `deepseek/deepseek-flash` | 直调记账/编排调用点穷举扫描表；红测先行 |
| Phase 2 O4/D2 | 同上 | `budget_gate.next_contiguous_round`/`contiguous_missing` 单一权威；`cmd_reserve` 漂移门（`FAIL_CLOSED:target_round_drift:<scope>`，零 ledger）；`orchest._finish_step1_missing` 复用；既有预算用例适配 |
| Phase 3 O2/D1 | 同上 | `orchest` continue/dry-run/`finish` 写出点参数化 + 崩溃恢复缺省**继承 started**；`converge_loop` loop-spec 顶层 `evidence_mode`；`scripts/README.md` 口径 |
| Phase 4 O7/D3 | 同上 | `reserve`/`settle` 来源声明门（`--orchest-managed` / `--manual-fallback` 恰好一个，否则 fail-closed；`reserve` 门先于 `cmd_companion_for`；`ingest-verdict` 不设门）；`orchest`/adapter（含 `_ensure_te_companion`）注入；`finish` 步骤 3 之后扫描 + 显式降级（`--dry-run` 同样生效） |
| Phase 5 验证 | OCSR（跨厂商、只读、对抗式） | verdict `通过`，9 节全 PASS；独立复跑 478 passed |
| Phase 5b 审计后修复 | OCSR | N1：`[manual-fallback]` 计数改行首锚定；DEGRADED 计数 18 → 1；全量 480 passed |

### 验证结果

- `converge-skill` 全量：**480 passed, 5 skipped, 11 subtests passed**（基线 450 → 实施后 478 → 审计后修复后 480）。
- `py_compile`（10 个改动脚本/测试）通过；`git diff --check` 通过；`refs/*`、`SKILL.md`、`CONSTITUTION.md`、`scripts/archive_contract/*` 未修改（`git status` 为空）。
- 改动范围：11 个文件、626 insertions / 43 deletions，全部落在 Exact File Matrix 授权范围。
- Acceptance：逐条 PASS（独立审计第 7 节）。

### 环境事实（可复用）

- 测试须用**长路径** TEMP/TMP（`C:\Users\Administrator\AppData\Local\Temp`）；8.3 短路径造成 4 项假失败。
- 改造编排/门禁自身时，在飞进程持旧版代码；**先停流再改门**，否则 settle 会 `FAIL_CLOSED`。
- 用 OCSR 派发"原地修订既有产物"的任务时，ocsr 会因"非预期覆盖既有文件"返回非零，适配器据此记为 `failed/backend-error`（工作其实成功）——审阅账目时须区分。

### 成本数据（估算）

| 阶段 | agent 数 | 备注 |
|---|---|---|
| 计划修订（R1-R4 后） | 4 | 全部 `deepseek/deepseek-flash` |
| fresh outer 评议 | 5 | 同上；outer 用量 5/8 |
| 实施 | 1 | 21.0 min |
| 独立审计 | 1 | 7.7 min |
| 审计后修复 | 1 | 6.3 min |
| 失败/误分类派发 | 3 | 1 次白名单拒绝（未调用模型）+ 2 次 settle 异常 |
| 合计 | 15 | 无 ultraverge/blind 用量 |

### 后续

后继对象：C（O5+O6，standard-review）、B（O1+O3，ultraverge）。适配器记账缺陷建议独立小对象。
terminal_decision_event_id: 2351cbed-c2d5-49d9-8ac8-1073a5a86191
terminal_decision_value: 可执行
