---
type: retrospective
object_slug: 20260911-op-envelope-b-contract-correction
generated_at: 2026-09-12T00:00:00Z
---

# Retrospective · 20260911-op-envelope-b-contract-correction

## 1. 结束模式

ultraverge 完整收敛。3 名 UV 初审（candidate-1）全部阻断且含 conceptual → 完整收敛；历经 candidate-2..8 共 7 次计划修订、outer R1-R5、blind-1..4、强制设计审查初评（M1-M6）与复审（MF-1..4）；终局由**用户裁决在 candidate-8 收口评审循环**（"评审差不多就可以了，只要方向明确，剩下的问题可以在执行中去解决"，user-message `989e5ebd`），MF-1..4 作为实施约束带入执行，实施后独立 fresh 审计兜底（通过，0 blocking）。

## 2. 阻断轨迹（时序）

| 步骤 | 对象 | verdict | 要点 |
|---|---|---|---|
| UV1/2/3 | candidate-1 | 3×阻断（含 conceptual 5 条） | D2/O3 被三票一致判为"不解决任何被拒操作"（Occam）；D4 实现分支无界；D3 门禁击穿既有测试未枚举；计划自身缺治理机器块 |
| R1 | candidate-2 | 阻断 3 | 立身用例前提失真；共享验收与门禁矛盾；bootstrap 例外已被 r2 消耗 |
| R2 | candidate-3 | **可执行** | blind-1 同字节复核亦 **可执行**（材料对 #1） |
| 设计初评 | candidate-3 | 设计需修订 | M1 写入期/归档期两个真相；M2 出边字段；M3 更正无取代；M4 双谓词源；M5 授权弱绑定；M6 --active-dir 旁路 |
| R3 | candidate-4 | **可执行** | M1-M6 落地核验 |
| blind-2 | candidate-4 | 阻断（3 high） | I-1 数字失真；I-2 规则与文字矛盾；I-3 record_correction 闭包不完整 |
| R4 | candidate-5 | **可执行** | |
| blind-3 | candidate-5 | 阻断 | Issue-1 `artifact sha256/size` 未入闭集（**原件后被覆盖，blob 恢复**） |
| blind-4* | candidate-6 | 阻断 | M5 reason 分支可绕过；record_correction 未闭合前置（*错位于 blind-recheck-3.md，见事故披露） |
| R5 | candidate-7 | **可执行** | |
| blind 终局 | candidate-7 | **可执行** | （材料对 #2） |
| 设计复审 | candidate-7 | 设计需修订 | MF-1 `instance_id` 漏闭；MF-2 opt-out 产 legacy state；MF-3 生命周期未定；MF-4 前置失败码 |
| 用户裁决 | candidate-8 | 收口 | MF-1..4 带入实施 |

单调性：blocking 密度从 UV 的每票 4-5 条降至后期每轮 1-4 条精度项；两轮"可执行"被后续新证据（设计复审）打破后均再认证成功。

## 3. Antipattern 巡查

| 类型 | 对象 | 触发结果 |
|---|---|---|
| wrong_root_cause | candidate-1 的 D2/O3 | 命中（conceptual）："鸡生蛋"实为"先实施后归档"的正常时序；整节删除，改为处置记录 |
| enumeration_gap（A 已沉淀） | D3 门禁 × TestGovernancePreflight | 命中两轮；穷举扫描附录 + M6 取消 --active-dir（消除 21 处迁移）后闭合 |
| **dispatch path/prompt drift（新）** | blind-4 与设计复审两次派发 | **事故 ×2**：prompt 内产物路径与 `--output-name` 不一致 → 覆盖 blind-recheck-3.md 与 design-review.md 原件；均已从 evidence blob（exact 模式 output.bin）完整恢复并披露 |
| **verdict literal misrecord（新）** | blind-2 记账 | 编排层向 record-verdict 传错字面量；frontmatter 已恢复，attempts.md 披露 |
| substring_counting（A 已修） | — | 未再犯（O1 设计即用行首锚定/集合判定） |
| plan bloat / Occam | candidate-1→8：41KB→133KB | UV3 建议拆分对象；因用户合并裁决以双 Track 结构回应；成本显著（见 §7），O6 议题获得活体样本 |

## 4. Executor 路径依赖评估

7 次修订全部由 fresh Executor 按编排层指令（含 UV/R/blind/设计的单选修法）落地；无折中小修、无静默扩围。authoring Executor 从简报产出 candidate-1（41KB，含机器块与全部调研行号）。实施 Executor 一次完成两 Track（23.3 min，14 文件，+1084/-13），审计顺手闭合 +1 文件。

## 5. Reviewer verdict 分歧分布

| 轮次 | verdict | 阻断数 | 备注 |
|---|---|---|---|
| UV1/2/3 | 阻断需修复 ×3 | 4/4/4（conceptual 4+1+0） | 少数派 conceptual 规则触发完整收敛 |
| outer R1-R5 | 阻断/可执行/可执行/可执行/可执行 | 3/0/0/0/0 | R2 起进入材料重认证循环 |
| blind 1-4 | 可执行/阻断/阻断/可执行 | 0/7/4/4 | blind-4 错位登记（文件名=3） |
| 设计审查 ×2 | 需修订 ×2 | M1-M6 / MF-1..4 | 复审发现修订引入的新缺口，证明复审必要 |

## 6. 降级影响评估

- 模型 provenance：全部派发 `deepseek/deepseek-flash`（OCSR configured，非 host-reported）；独立性来自 fresh 独立上下文，**非厂商多样性**（用户指定单一模型）。
- 记账误分类（未回填，attempts.md 披露）：适配器将"原地修订 plan.md 的成功 Executor"记为 `failed/backend-error` ×4；一次白名单拒绝记 `pre_execution=false`（模型未调用）。
- 证据事故 ×2（已恢复）：blind-3 原件与 design-review 原件被覆盖，均从 exact evidence blob 完整恢复（18,149B / 18,545B），收据哈希↔磁盘重新一致；错位内容分别归位 `blind-recheck-4.md` 与 attempts.md 附录。
- 预算：outer 5/8；ultraverge 3/3；blind 3 + 扩展 1（ext-b-blind-4，引用用户既授权事件 `ab8896b1`）；终局材料对为 R5+blind 终局（candidate-7 字节），candidate-8 的双认证由用户裁决豁免、以独立实施审计兜底——此为本对象最大的过程降级，如实呈现。

## 7. 成本数据（估算）

| 阶段 | 派发数 | 备注 |
|---|---|---|
| 计划撰写 + 修订（repair×6 + fixab） | 8 | 全部 deepseek-flash |
| UV 初审 | 3 | 并行 target-round 1/2/3 |
| outer 评议 R1-R5 | 5 | |
| blind 复核 | 4 | 1 次扩展 |
| 设计审查 | 2 | 初评 + 复审 |
| 实施 + 审计 | 2 | 23.3 min + 10.3 min |
| 失败/误分类派发 | ~6 | 路径错配 ×2、白名单 ×1、结算误记 ×3 |
| 合计 | ≈30 | 计划字节 41KB→133KB；每轮字节变更触发全量双认证 |

## 8. 经验教训

- **设计复审是本轮价值最高的单一环节**：M1（两个真相）、M6（参数即旁路）、MF-1（闭集漏一个身份锚点）都不是事实核对能抓到的，必须独立的设计视角。
- **材料双认证的成本在多轮修订对象上爆炸**：7 次重认证 ≈ 全部评议成本的一半。O6（material 增量复核）此前"只记录"的裁决获得了活体反例——建议后续对象以真实数据重开 O6 评议。
- **派发参数必须同源生成**：prompt 内产物路径与 `--output-name` 任何一次手工编辑都可能错配；两次事故均因此。ocsr 层应加"路径一致性 preflight"。
- **exact evidence blob 是最后的可恢复性保障**：两次覆盖事故均靠 `output.bin` 完整恢复；该机制值得保持并在文档中明示"产物以 blob 为准可恢复"。
- **预算扩展链条可用但繁重**：手动触发 BLOCK → 取 decision 行 → 手写 extension → 重试；该流程应有 CLI（本次为 r2 先例的手工延续）。
- **用户的"差不多就可以了"是合法的收敛终结器**：在边际收益递减段，用户裁决 + 实施后独立审计的组合优于无限重认证；但必须如实记录降级（本复盘 §6）。

## 9. 后续建议

- **O6 重评**：以本对象 7 次重认证的实测成本为 calibration 样本。
- 独立小对象：适配器 `pre_execution` 误分类修复；ocsr 派发"prompt/输出路径一致性 preflight"；预算扩展 CLI。
- `archive --declare-orphan-reservation` 式的"低频手工路径"应逐个审一遍，凡无 CLI 的（如 extension）补齐。
- 实施期发现的 §9-c 三条补充负例（correction-target-missing / correction-sequence / 批量不可表达）留待下一个触点补齐。

## 10. 实施结果（2026-09-12）

- 改动 14 文件（+1084/-13）+ 审计顺手闭合 2 项（state-schema 1 字符对齐、`read_state` 增 `UnicodeDecodeError` → 统一治理失败码 + 1 条负例）。
- 全量测试：**509 passed, 5 skipped**（基线 480 → 实施 508 → 闭合 509）；`py_compile`、`git diff --check` 通过。
- 独立 fresh 审计：**通过，0 blocking**（范围纪律、语义守恒、三闭集独立枚举、单层有效视图、M5、MF-4、manifest 披露、零字节回归、O5 门禁/opt-out/披露、28 条新测试判别力、独立复跑一致）。
- 第三部文件（`SKILL.md`、`refs/state-schema.md`、`refs/orchestrator-guide.md`）按 §12 逐字对照修改，ultraverge 授权（CONSTITUTION 第四部）。

### 环境事实（可复用）

- 测试须长路径 TEMP/TMP（8.3 短路径 4 项假失败）。
- 派发 prompt 产物路径与 `--output-name` 必须同源生成；覆盖事故可由 evidence blob 恢复。
- 预算扩展：手动 reserve 触发 BLOCK（账本得 decision 行）→ 手写 state.extensions → 重试 reserve；无 CLI。

### 后续

操作包络层索引（`docs/plans/active/20260911-converge-operational-envelope.md`）：A ✅、B ✅（本对象）；O6 重评与适配器缺陷小对象为候选后续。
terminal_decision_event_id: fa03124b-9638-4c67-801c-fd6ef74a85cf
terminal_decision_value: 可执行
