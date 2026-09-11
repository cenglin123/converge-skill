---
type: retrospective
object_slug: 20260910-process-controller-consolidation
generated_at: 2026-09-10T00:00:00Z
---

# Retrospective · 20260910-process-controller-consolidation

## 1. 结束模式

严格收敛。三名 ultraverge 初审 Reviewer 的 verdict 为 `需重新设计 / 阻断需修复 / 阻断需修复`；按少数 conceptual 阻断规则升级完整收敛。计划修订后，首个 fresh outer Reviewer 返回 `可执行` 且零阻断。强制设计审查已完成。

## 2. 阻断轨迹

UV 初审合并后 9 个问题域 → plan repair → outer R1 = 0 blocking。单调下降；无 Type O/R/F/S。

## 3. Antipattern 巡查

| Round | 类型 | 对象 | 触发结果 |
|-------|------|------|---------|
| UV1 | prompt_mode_missing | 初始 Reviewer prompts | 命中；后续 prompt 已补 Mode，过程缺陷已记录 |
| UV1 | false_generality | inner loop 数值统一 | 命中；改为 true Continue 与 driver fresh Executor retry 两个概念 |
| UV1 | identity_crisis | Converge 与 init-agent-docs Coordinator | 命中；改为顶层控制与领域 handoff 的明确权限边界 |
| UV1 | environment_lock-in | Git-only/no-Git 与 Windows TEMP | 命中；纳入 profile 与验证前置条件 |

## 4. Executor 路径依赖评估

Executor 未做折中式小修：上溯到 controller 权限、driver 事件语义、预算状态权威、四 profile 输出与同步模式声明。初稿中过度统一 `max_inner_loops` 的方案锚定被 Reviewer 打破。

## 5. Reviewer 间 Verdict 分歧分布

| 轮次 | Verdict | 阻断数 | 归因分布 |
|------|---------|--------|---------|
| UV1 | 需重新设计 | 5 | conceptual/architectural/structural/implementation |
| UV2 | 阻断需修复 | 4 | conceptual/architectural/structural |
| UV3 | 阻断需修复 | 5 | plan_defect |
| outer R1 | 可执行 | 0 | — |

## 6. 降级影响评估

原生 outer Reviewer 因宿主用量上限在执行前失败，已如实取消；随后改用一次 OCSR `xiaomi/mimo-v2.5-pro` fresh Reviewer。其模型 provenance 为 configured 而非 host-reported，故独立性成立但具体模型解析证据较弱。OpenCode 预算门为 auditable-only，没有可阻断的 pre-spawn hook；所有本流程 spawn 仍逐次 reserve/settle。

## 7. 经验教训

- “共享一个默认数值”不等于“共享一个事件语义”；Reviewer Continue 与 fresh Executor retry 必须拆名。
- 稀疏 active state 若动态回退新版本默认值，就不能声称跨版本权威。
- 删除一个 bespoke controller 不足以形成唯一控制边界；模板和 reference 中的文本流程也要降级为领域 handoff。
- 小型预算应明确是成本优先默认，而不是经验最优；以后用 extension 命中率再校准。
- 规则追踪本次发现了真实问题，现有追踪机制仍有必要。

## 8. 后续建议

落地时采纳设计审查的实现关键点：共享初始化器先于任何 driver 副作用；旧 journal 显式迁移或拒绝；修改后 fresh Reviewer 路由成为 spec 拓扑不变量；Small profile 显式包含 `docs/initialization.md`；同步模式使用稳定机器可读声明；copy 验证覆盖完整和部分 hardlink 组。

## 9. Round 0 合同谈判评估

| 维度 | 评估 |
|------|------|
| 是否启用 | 否；已有自足验收标准，三名 ultraverge 初审承担了独立挑战 |
| contract 是否减少预期错位 | 不适用；初审发现并修复 9 个问题域 |
| contract_amendment 触发次数 | 0 |
| contract 与 plan 的同步性 | 不适用 |

## 10. Rubrics 评估

| 维度 | 评估 |
|------|------|
| 使用的维度 | Correctness, Completeness, Consistency, Maintainability, Boundary Clarity, Portability, Scalability |
| 未使用/总高分的维度 | 无；初审与设计审查均实际使用 |
| rubric_gap 触发次数 | 0 |
| 跨轮分数趋势 | 初审多项 concerns → outer R1 全部 clean |

## Suggestions 处置

- S1 scripts/README 残留扫描：采纳，实施核验覆盖整个治理/脚本范围。
- S2 driver 读取 validated active state：采纳，作为共享配置实现关键点。
- S3 copy 仅在 samefile 情况强制解组：采纳，避免无差别覆盖。
- S4 新建 controller contract test：采纳。
- S5 advisory eval 使用项目外临时目录：采纳。

## 盲审复核

未触发：完整收敛仅经历 1 个 outer loop。

## 成本数据（估算）

| 阶段 | tokens | 时间 | agent 数 | 关键产出 |
|------|--------|------|----------|---------|
| 计划作者 | 未提供 | — | 1 | plan.md 初稿 |
| ultraverge 初审 | 未提供 | — | 3 | 三份独立审查 |
| 计划修订 | 未提供 | — | 1 | plan.md + attempts.md |
| outer R1 | 未提供 | ≈10 min | 1 | 可执行 verdict |
| 设计审查 | 未提供 | — | 1 | design-review.md |
| **总计** | **无法精确取得** | — | **7 次成功 spawn；1 次 pre-execution 取消** | 收敛计划 |

---

## 修订 R2 · 数据驱动反馈闭环（2026-09-11，收敛后修订）

### 触发来源

用户外部输入（user-message `bdd405f3-2b03-40eb-9db2-09a32afacae2`）：多轮迭代审计应能集不同视角查漏补缺并得到更优方案，但本次 `8/3/3 → 3/1/1` 削减证明历史实证未进入决策面。执行授权：user-message `87c4f9f7-72f9-4c45-a2d2-409ae8d83120`（"好的，修复它吧"）。

### R2 阻断轨迹

- 修订 R2 初审（三 fresh Reviewer，exact evidence）：3 × `阻断需修复`（A1-A5、B1-B5、C-B1-C-B6，覆盖 calibration 闭环、结构化 preflight 输入、双审同 hash 绑定、reopened superseding decision、instrumented-only 计量、v3 兼容层过度设计、task tier 可达性措辞、material 触发定义、无条件实施确认）。
- R2 修复后候选 `8835f41d…`：outer `阻断需修复`（R2-B1 伪 anchor locator；R2-B2 无 versioned review-target + metadata-only prompt 证据），blank-slate `可执行` 但随字节变更失效。
- 最终候选 `ef2e8441…`（34302 字节）：outer round 4 与 blank-slate round 3 双 fresh Spawn 同字节复核，均 `可执行` 零阻断；四份 `converge.review-target/v1` payload canonical 字节一致。终止 = 终止-a（material-revision 双权威变体）。

### 实证冲突的处置

`uv-init-1.md:65` 的 suggestion 在 R2 被正确升级为核心修复对象：`0137fce`（outer 7/12、blind 3/4 且持续推进）与 `d3c82cb`（outer R8 + blind #2 才通过）证明 `3/1/1` 会拦正常收敛；`aac95bd` 的 2-3 轮众数说明 8/3 是止损上限而非目标用量。结论：恢复新状态 `8/3/3`、取消 ultraverge blind=2 倒挂；inner=3 属已发布兼容保留。成本控制归位 task-envelope（instrumented-only，opt-in，可早于局部上限阻断，不承诺 8/3/3 最坏路径可达）。

### 降级与 manual-fallback 申报

- OpenCode 为 auditable-only：无 pre-spawn hook，预算门为审计层；全部 spawn 均逐次 reserve/settle，无遗漏。
- `3/2/1` 显式配置在本对象内保持权威至 finish（不中途迁移）；outer/blind 耗尽后以两条 budget_extension（outer 3→4、blind 2→3）续跑，关联真实 BLOCK decision 与 user-message `29c90690-7bd7-47f1-98a8-f7c727f86216`（"授权扩展完成双审"）。
- 最终双审 prompt/output 需 exact evidence，orchest.py 当前硬编码 metadata-only，故该两段生命周期走 budget_gate + archive CLI 手工等价序列（attempts.md 已记 [manual-fallback]）。
- Executor `b6f4e8a3` 遇宿主 usage limit 但已完成写入；遗留两个未派发孤儿已 recover(process-interrupted)。原生 `task` 续命对长上下文有上限——这是本次真实的后端约束。

### 经验教训（R2 增量）

- 找到证据 ≠ 证据进入目标函数；`empirical_conflict` 必须有机械承载（结构化输入 + preflight），否则可被降级为 suggestion。
- 终止规则的强度必须与修订幅度联动：material revision 需要双 fresh 同字节权威，单一零阻断只是一次样本。
- 预算数值的"成本优先"声明不能消解实证冲突；质量—成本取舍必须有显式用户决策记录。
- 宿主层面（task 续命上限、orchest metadata-only 硬编码、GATE_TO_RECOVER 解包 bug）会在长流程末端集中暴露；r2 实施清单已纳入。

### 成本数据（R2，估算）

| 阶段 | agent 数 | 关键产出 |
|------|---------|---------|
| 修订起草 + 阻断修复（Executor，含 1 次 usage-limit 中断续作） | 2 | plan.md r2 最终版 |
| R2 初审 | 3 | A/B/C 三份阻断报告 |
| R2 same-hash 复核（metadata-only，无终局资格） | 2 | round-2.md / blind-recheck-1.md |
| R2 最终 exact 双审 | 2 | round-3.md / blind-recheck-2.md（0 阻断） |
| **R2 合计** | **9 次成功 spawn + 1 次 continue 修复** | 收敛计划 r2 |

终局 decision 见下方 stamp 标记。

### 后续对象（操作包络层，独立计划）

本次自指收敛暴露的 5 类**操作层**缺口（append-only 无更正事件、exact evidence 未工具化、无自指 bootstrap 通道、轮号被取消预约烧掉、任务级成本治理缺位）已落盘为独立计划 `docs/plans/active/20260911-converge-operational-envelope.md`，待本对象 r2 落地收尾完成后单独评议与收敛。判定机制层本次未被证伪，不在该计划范围内。**教训**：不要把多个机制塞进同一个巨型计划——r2 的范围膨胀是本次成本的主要来源。

---

## 修订 R2 · 实施结果（2026-09-11）

### 实施阶段与产出

| 阶段 | 执行者 | 产出 |
|---|---|---|
| Phase 2 默认值恢复 + D11 闭包配对 + GATE_TO_RECOVER 修复 | fresh Executor（宿主 task） | `budget_gate.py` DEFAULTS 8/3/3、移除 ultraverge blind 叠加；`model.py` pre_execution cancelled↔failed 配对；`orchest.py` GATE_TO_RECOVER 显式元组；state-schema 规范句 |
| Phase 1/3 calibration + 治理 preflight | fresh Executor（宿主 task） | `distill_antipatterns.py --calibration`；`budget_gate.py` governance preflight（唯一 `converge.governance-change/v1`、窄数值门 `BLOCK:empirical_conflict`、locator 三类错误 fail-closed、CRLF fail-closed）；`refs/state-schema.md` 四份 JSON 契约 |
| Phase 4 material gate + reopened supersession | OCSR `xiaomi/mimo-v2.5-pro` | `orchest.py` 同字节双审门、calibration sample 校验、reopened superseding decision；`converge_loop.py` material+outer1 强制 blank-slate |
| Phase 5a task-envelope 配对核心 | OCSR | `budget_gate.py` call_id/原子 companion/幂等 settle/accounting_coverage；`orchest.py` Continue 单预约链接 |
| Phase 5b adapter/loop + 初始化披露 | OCSR | `ocsr_spawn_adapter.py`/`converge_loop.py` 配对与 coverage 呈现；`quality_path_guaranteed: false` 披露 |
| Phase 6 文档对齐 | OCSR | SKILL/README/README_en/scripts/README/refs 措辞与指针；`tests/test_process_controller_contract.py` 静态断言 |
| Phase 7 独立审计 | OCSR（跨厂商，只读） | verdict `可执行`、0 阻断、2 建议 |
| 审计后修复 ×3 | OCSR | 见下 |

### 审计发现与处置

| 项 | 内容 | 处置 |
|---|---|---|
| S1 | `model.py` D11 注释"乱码" | **误报**：注释为合法 UTF-8，审计方终端按 GBK 显示所致 |
| S2 | `cmd_companion_for` 用 `_rewrite_ledger` 就地改写 gate-ledger | **真缺陷**，违反 append-only 不变量与计划 Non-Goals。已修：删除 `_rewrite_ledger`，改反向查找纯追加，并加"ledger 字节前缀不变"回归 |
| — | `_finish_step6` 在 archive 前搬走 `.reopen-state.json` | **真缺陷**（自查发现）：会丢 r2 parent 链接。已修：不搬走、允许其留在原地，加 finish→archive revision/parent 回归 |
| — | `_find_material_block` 取第一个 material 块 | **真缺陷**（自查发现）：多块对象会选中被 supersede 的候选。已修：按 review-target payload 的 `material_locator` 解析指定块并校验 canonical hash；无 id 时取最后一块 |

### 验证结果

- `converge-skill` 全量：**436 tests OK**（skipped=5）。
- `init-agent-docs` 全量：**85 tests OK**；`scripts/converge_orchestrator.py` 保持删除。
- `py_compile`（7 个改动脚本）通过；`git diff --check` 通过；stale 数字扫描（3/1/1、blind 叠加、硬编码 Continue）零命中。
- 本对象 finish dry-run：步骤 0-4 + material-gate/calibration 校验通过；终局 decision 复用 `777a0e2d`。

### 环境事实（可复用）

- 测试须用**长路径** TEMP/TMP（`C:\Users\Administrator\AppData\Local\Temp`）。默认 8.3 短路径（`ADMINI~1`）导致 4 项假失败；`TEMP=C:\Temp` 又使 OCSR fake dispatch 路径变形导致 13 项假失败。
- OCSR 复杂任务实测约 10-30 分钟；看门狗 60 分钟足够，15 分钟会误杀。
- OCSR `--output-pattern` 监视路径与 prompt 内指定报告路径必须一致，否则出现"exit 0 但未落盘"的假失败。

### 成本数据（R2 实施，估算）

| 阶段 | agent 数 | 备注 |
|---|---|---|
| 计划实施（Phase 2/D11、Phase 1/3） | 2 | 宿主 task（本对话模型） |
| 计划实施（Phase 4/5a/5b/6 + 审计 + 3 修复） | 7 | OCSR `xiaomi/mimo-v2.5-pro` |
| 合计 | 9 | 全部通过独立验收 |

### 后续

操作包络层缺口见 `docs/plans/active/20260911-converge-operational-envelope.md`（用户指示：先收尾 r2，再修操作层）。
terminal_decision_event_id: 777a0e2d-859f-462d-80a5-7d135d5f04b5
terminal_decision_value: 可执行
