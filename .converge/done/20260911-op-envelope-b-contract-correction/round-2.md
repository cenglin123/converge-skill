---
round: 2
reviewer_backend: opencode
reviewer_instance_id: 20260912_041643_57eefa
generated_at: 2026-09-12T04:16:43.567476+00:00
verdict: 可执行
---
可执行

# round-2 · 子计划 B 完整收敛 outer 评议（candidate-3）

- 对象：`.converge/active/20260911-op-envelope-b-contract-correction/plan.md`（candidate-3，695 行 / **83,818 B** / SHA-256 `e7690e761f07330ba76cdb2aef35871af06e6cb7d9cd1c9c372a5b6d439887f8`）
- 基线：HEAD `13da6055f173ab1459f62cb36de11bb05b2b19cc`；`git status --porcelain` = `?? docs/plans/active/`（4 个未跟踪规划文档，与计划声明一致）
- 身份：fresh 独立 Reviewer（与 plan 作者及 UV 初审无共享上下文）；只读实核，除本报告外未修改任何文件；UTF-8
- 判定：**可执行**（R1 三条阻断 R1-1/R1-2/R1-3 全部实质闭合；无事实失真阻断、无 D3 穷举缺项；8 条非阻断精度问题，均局部可修）

> 本轮我实际复跑的自验（逐字留痕）：
> - 机器块自验：`python scripts/budget_gate.py preflight --plan .converge/active/20260911-op-envelope-b-contract-correction/plan.md` → `WARN:code_heavy:4,63` / `PREFLIGHT_OK:governance-change` / `EXIT=0`，与 `attempts.md` §7.2 逐字一致。
> - calibration 生成器复现：`python scripts/distill_antipatterns.py --calibration --root . --output <TEMP>/calib_check.json --id calibration-op-b --source-revision r1` → `EXIT=0`；`cmp` 与仓库内 `evidence/calibration-report.json` **IDENTICAL**，SHA-256 均为 `c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581`。
> - 全量测试基线复跑：`python -m pytest -q` → `4 failed, 476 passed, 5 skipped, 11 subtests passed`（4 fail 全为 `tests/test_archive_convergence.py` 的 Windows 8.3 短路径 `ADMINI~1` vs `Administrator`），与 `plan.md:533`/`:563` 声明一致。
> - 计划文件实核：83,818 B / `e7690e76…`，与 `attempts.md` §八一致。

---

## 一、前置自检 5 问

1. **产物身份自洽 — 通过**。candidate-3 = Track-1（O1）/Track-2（O5）双轨，O3/O6 为处置记录（§13/§14）；frontmatter、Goal（§1）、Track（§4）、File Matrix（§5）指向一致。R1-1 的立身用例前提失真已重写为「全事件流机械求值」（§3 D1 步骤 3，`plan.md:183-187`）。
2. **产物边界诚实 — 通过**。§3 D4 明确 record-only 且删除「若裁决为实现则实施」；§13 明确 O3 不实现；Non-Goals（§9）与之一致。数值披露诚实：真机械下界=4 / 典型估计≈10（标注非下界）/ r2 实测 23 且如实写 `initial 20 < 23`（`plan.md:292-294`）。
3. **产物数据纯度 — 通过**。全篇为仓库真实路径、实核行号、既有常量；`numeric_changes` 两条全 `kind: mechanism`；无业务数据、无环境硬编码（`administrator` 仅出现在 R1-8 环境事实中）。
4. **职责边界自洽 — 通过**。D1 唯一语义读取点（`validate_event_graph`/`validate_ledger` 入口各自 resolve，`plan.md:240-241`）；R1-6 已补 `project_manifest` 的 `raw_events`/`effective_events` 双列表与逐行号派生面（`plan.md:242-245`）；D3 门禁/披露三处/adapter 写入点职责清晰。
5. **命名一致性 — 通过**。`plan.md:128` 命名锁定：事件 `event-correction`、manifest/INDEX 键 `corrections`、降级串前缀 `correction:`、常量 `CORRECTION_CLOSED_FIELDS`；D3 触发统一为「含唯一 `converge.governance-change/v1` 机器块」（`plan.md:272`）。

---

## 二、R1 三条阻断闭合清单（逐条 yes/no + 证据）

### R1-1（阻断，事实失真）— **YES，闭合**

- R1 指控：D1 立身用例推导链第 3 步称「r2 唯一 terminal-decision 事件 54」，事实失真（r2 实含 3 条）。
- 我的独立实核（`rg -l '"event_type": ?"terminal-decision"'` 于 r2 `evidence/events/`）：
  - seq 17 `e4182ce3-fe3e-4683-9533-f36ecab465fd`：`reviewer_event_id`=`verdict_output_ref`=事件 14 `4952d7de…`，`supersedes_decision_event_id`=null；
  - seq 45 `ea64c374-d650-43ae-a81a-1935aa06dfb9`：`reviewer_event_id`=`verdict_output_ref`=事件 42 `ef98b9ea…`，`supersedes`=事件 17；
  - seq 54 `777a0e2d-859f-462d-80a5-7d135d5f04b5`：`reviewer_event_id`=`verdict_output_ref`=事件 53 `0aa365ab…`，`supersedes`=事件 45。
- 机械求值：`DECISION_REFERENCED` = {reviewer_event_id}∪{verdict_output_ref}∪{supersedes}∪{source_ref(user-decision)} = {14,42,53}∪{14,42,53}∪{17,45}∪{} = **{14,42,53,17,45}**；r2 全事件流无 `user-decision`（`rg` 计数 = 0）；目标事件 55 `cabcac00-bd16-4161-b857-c45733630580` **不在集合内**。
- 事件 57 `9254cf87…` 以 `started_event_id` 引用事件 55（`invocation-terminal`，非 `terminal-decision`）——该边按 `plan.md:177` 的显式排除不构成闭包。
- 结论：`plan.md:183-187` 的推导链与仓库事件流**逐步可复算**，R1-1 已闭合。

### R1-2（阻断，Acceptance 自相矛盾）— **YES，闭合**

- R1 指控：A-S4 缺 `--active-dir`，实现后必被自身新门禁判 exit 30，与期望 exit 0 冲突。
- 实核：`plan.md:518` A-S4 已补 `--active-dir .converge/active/20260911-op-envelope-b-contract-correction`，并注明 Phase 0 按 (a) 配置 `critical`；`plan.md:520-531` 新增 §8.4「Acceptance × Track-2 门禁交互复核」表。
- 我独立重扫 §8 全部「命令 + 期望 exit 0」条目：只有 **A2-1**（带 `--active-dir`）、**A2-4**（opt-out）、**A-S4**（已补 `--active-dir`）三条走 preflight 且期望 exit 0；A2-2/3/5/6 期望 exit 30；A2-7 legacy；A1-1..A1-10/A2-8/9/10/A-S1/2/3 不经 preflight。**无其他 exit 语义翻转条目**。
- Phase 0 可行性实核：对象 active 目录现有 `_budget-state.json` 的 `config={}`，`initialize_state` 对缺失键走 `setdefault`（`budget_gate.py:365-366`），故 `init --task-tier critical` 无需 `--force` 即可配置成功，A-S4 可实现。R1-2 已闭合。

### R1-3（阻断，治理自举）— **YES，闭合**

- R1 指控：candidate-2 复用已被 r2 消耗的一次性 bootstrap 例外，且生成器已落地可产出真实报告。
- 实核（替换来源确为生成器产物）：
  1. `refs/state-schema.md:95` 确为「bootstrap 例外（一次性）…后续治理变更必须由 `--calibration` 生成的报告提供」；`plan.md:638`/`:690` 显式声明**不使用**该例外。
  2. 独立文件 `.converge/active/20260911-op-envelope-b-contract-correction/evidence/calibration-report.json` 真实存在，2,385 B，SHA-256 `c4755e111b6902f64b4623ab994cc4cd0f3dd7d6f448469d7c83e9ca814ed581`。
  3. 我用同一命令重新生成到临时路径，产出与仓库文件**逐字节一致**（`cmp` IDENTICAL），证明其为生成器确定性输出而非手写。
  4. locator 载体 `attempts.md::json-fence[schema=converge.calibration-report/v1,id=calibration-op-b]` 经 `_resolve_report_locator` 解析（`budget_gate.py:1502-1537`，`plan.parent / fname` = 对象目录/attempts.md，`attempts.md ∈ _ROOT_ALLOWLIST` `budget_gate.py:1428`）；preflight 复跑 `PREFLIGHT_OK`（exit 0）即证明 fence canonical hash = `c4755e…`、`corpus_digest=ff64a62b…`、`freshness={13da6055…, r1, 0}` 三者逐字段机械相等。
  5. 报告形状与 `plan.md:694` 声明一致：`corpus` 19 条 `done:<slug>`、`eligible_samples=0`、`status=unavailable`。
- 结论：治理来源已从「一次性 bootstrap 例外」切换为 `--calibration` 真实生成报告，符合 `refs/state-schema.md:95`，R1-3 已闭合。

---

## 三、UV 三票处置抽查表（≥10 条；逐条回 plan 原文 + 代码实核）

统计核对：UV1 18 条（B1-B4 + N1-N14）+ UV2 16 条 + UV3 16 条 = **50** 条，与 `attempts.md` §一一致。抽查如下：

| # | UV issue | 处置 | plan 落点实核 | 独立复核结论 |
|---|---|---|---|---|
| 1 | UV1 B1 / UV2 I2-5 / UV3-4（新门禁击穿既有治理 preflight） | 修复 | `plan.md:396-436`（§6.2 逐处表）、`:509`（A2-10） | **真修复**。`rg "self\.preflight\("` 实核 = **21** 处（1554/1566/1575/1584/1591/1602/1613/1623/1633/1641/1656/1666/1675/1682/1690/1699/1708/1717/1724/1736/1743），与 §6.2 表行号逐一相符；`TestPreflight` :272/:278 两处 legacy 无 gov 块。17 受影响 / 4 早返回的分类经 `cmd_preflight` 早返回链（`budget_gate.py:1763-1778`）复核成立。**无漏项**。 |
| 2 | UV2 I2-1（白名单与闭包互斥） | 修复 | `plan.md:144-153`（动态白名单）、`:179-193`（立身用例） | **真修复**。`allowed()=EVENT_FIELDS[type]−CLOSED`；`DECISION_REFERENCED` 仅取 `model.py:137/144/1008/1032` 四条真实 decision 边；事件 55 可更正，闭包不再清空白名单。 |
| 3 | UV1 B3 / UV2 I2-7（有效视图未定界） | 修复 | `plan.md:238-247` | **真修复**。`validate_archive:1178-1181` 经 `validate_event_graph`/`validate_ledger` 入口 resolve 覆盖；唯一施加点与 I2-7 的单选建议完全一致。 |
| 4 | UV1 N3（`FailClosed` 抛出点 :1139） | 修复 | `plan.md:91` | **真修复**：改为 :705（`_task_envelope_initial` 内），:1139 注为触发点；实核 `budget_gate.py:705`/`:1137-1139` 属实。 |
| 5 | UV1 N2 / UV2 I2-12 / UV3-9（O6a 锚点） | 修复 | `plan.md:107` | **真修复**：改为 `:97-100`；实核失效句确在 `refs/state-schema.md:100`。 |
| 6 | UV1 N5 / UV3-7（`started_event_id` 归属错误） | 修复 | `plan.md:168-177` | **真修复**：显式排除 `invocation-terminal.started_event_id`；引用集仅 4 个 decision 字段，行号 `:186/:978/:140` 实核属实。 |
| 7 | UV3-15（谓词 `_task_envelope_configured` ≠ 可用） | 修复 | `plan.md:281` | **真修复**：新增 `_task_envelope_usable`（initial+cap 均不抛）；实核 cap-only 配置过 `:692-694` 却在 `:705` 抛。 |
| 8 | UV3-14（无显式 opt-out） | 修复 | `plan.md:276-279`、`:503`、`:505` | **真修复**：`--allow-unconfigured-envelope <reason>` + `WARN:unconfigured-envelope:<reason>`，空 reason 仍 exit 30。 |
| 9 | UV3-6（禁止批量无机械承载） | 修复 | `plan.md:234` | **基本真修复**：以单字段闭集排除批量；但归因表述有精度问题（见 R2-6）。 |
| 10 | UV1 N6（`corrections` 须 omit-when-empty） | 修复 | `plan.md:252`、`:254` | **真修复**：manifest 键与 `render_index_bytes` 段均 omit-when-empty，沿用 `model.py:884-893` 惯例。 |
| 11 | UV1 N4 / UV2 I2-13（`__all__` 不存在） | 修复 | `plan.md:350` | **真修复**：实核 `rg __all__ scripts/archive_contract/capture.py` = 无命中；T1-F2 已删该断言。 |
| 12 | UV1 N13 / UV2 I2-15（`validate_event` correction 分支） | 修复 | `plan.md:166`、`:349` | **真修复**：`plan.md:349` 锚点 `:573-575`（user-message 分支之后插入）；实核属实。 |
| 13 | UV1 B4 / UV2 I2-6 / UV3-16（O6 实现分支无界） | 因 S2 删除 | `plan.md:299-307`、`:620-629` | **处置可追溯**：record-only 定案，删除实现分支，给重启判据 4 条 + 主观项披露。 |
| 14 | UV1 B2/N12、UV2 I2-2/3/4/10、UV3-1/2/11/12（O3 bootstrap） | 因 S1 删除 | `plan.md:266-268`、`:611-616` | **处置可追溯**：D2 整体删除；§13 引 r2 `attempts.md:210` 逐字（实核逐字）+ r2 `check` 实测 `{"valid":true}`。 |
| 15 | UV1 N8（本计划自身缺机器块/授权事件） | 修复 | `plan.md:633-686`、`:688-695` | **真修复**：§15 机器块 + §16 载体；`ab8896b1…`（seq 9）、`06754e6f…`（seq 10）实核为对象 `evidence/events/` 的 `user-message`，preflight 复跑通过。 |
| 16 | UV2 I2-16 / UV3-13（§12 对照非逐字） | 修复 | `plan.md:593-607` | **基本真修复**：5 处原含省略号的「原文」均已补为完整逐字原行；唯 `:60` 行为逐字前缀（见 R2-4）。 |

「修复」项以外的 S1/S2 删除项均可在 plan/attempts 追溯；抽查未发现名义修复、未发现与代码相悖的落点。

---

## 四、D1 三项闭合性复核

- **白名单 vs 判定闭合 vs DECISION_REFERENCED — 自洽**：`allowed()` 排除 `{terminal-decision,event-correction}` 类型与 5 个闭合身份字段（`plan.md:147-151`）；规则 3 对这两类整体闭合；规则 5 以四条真实 decision 边额外保护 `invocation-terminal`/`user-message`/前序 decision。三者叠加后仍保留 `{invocation-started, artifact-captured, design-review-completion}` 可更正，立身用例（事件 55）不被误伤。type-predicate 表（`plan.md:197-231`）经我逐字段比对 `EVENT_FIELDS`（`model.py:179-205`），**覆盖 allowed() 放行的全部字段**，未列字段默认 fail-closed；规则 10b 用完整 `validate_event` 兜住跨字段约束（`:534-536` 等），无 fail-open 缺口。
- **有效视图单层施加 — 自洽**：`validate_event_graph`（`:958`）、`validate_ledger`（`:594`）入口各自 resolve；`project_manifest` 保留 raw（校验入口 + `events[].sha256/size/path`）与 effective（projections/final/allowed_blobs/degradations）双列表（`plan.md:242-245`）；`validate_archive:1178-1181` 无需改动即走有效视图；`_verify_evidence_bytes` 只读结构字段（不可更正）。未发现二次施加路径。
- **授权时序 — 自洽**：规则 8/9 = exists ∧ `user-message` ∧ `seq(corr)>seq(umsg)>seq(target)`，与立身用例（>56>55）及越权三例（`plan.md:236`）自洽；规则 7 禁链式、单字段闭集禁批量、规则 6 强制 `original_value` 与 raw 逐字相等。
- **candidate-3 的修改未引入新矛盾**：R1-6 的双列表声明与 §5 T1-F1 锚点一致；R1-7 的「零改动」措辞已在 §6.2 表行 18-21、§7 T2-P4、§8 A2-10、§11 O5.7 四处统一。

---

## 五、D3 穷举复核（独立重数）

- `TestGovernancePreflight` 的 `self.preflight` 实核 = **21** 处（行号见 §三 #1），`plan.md:396-422` 逐处列表完整、无遗漏。
- **到达新门禁（17 处）**：行 1554/1566/1575/1584/1591/1602/1613/1623/1633/1641/1656/1666/1675/1690/1699/1708/1717——均为 `write_plan(gov, report)` 形态、恰好 1 个 gov 块，注入 `--active-dir` 后先过门禁再走原路径，断言不变。
- **不达新门禁（4 处）**：`1682`（2 gov 块，`:1776` 先返回）、`1724`（整文件 CRLF，见 R2-3 行号精度）、`1736`（无 fence，legacy `:1769`）、`1743`（`--governance` 无块，`:1775`）。
- **legacy 放行证明**：`cmd_preflight` 在无 gov 块且无 `--governance` 时于 `budget_gate.py:1769` 早返回，位于插入点 `:1777→:1778` 之前；`TestPreflight:272/278` 两处 legacy 调用确不受影响。全仓 `preflight` 调用仅测试（`rg` 实核），无编排层自动调用点，G2 波及面被完整列举。
- **数值依据**：r2 `gate-ledger.jsonl` 实核 `reserved` = **23**（executor 5、ultraverge-initial 3、outer-reviewer 6、design-reviewer 5、blind-reviewer 4），与 `plan.md:294`/O5l 逐项相符；`cap 30` 余量 7、`feature cap 24` 余量 1、`initial 20 < 23` 均为真。

---

## 六、逐条 issue（全部非阻断；无阻断项）

> 以下均为**文案/精度**问题，不改变机制结论、不构成执行障碍；编号 R2-x，severity 标注，单选建议。

#### R2-1 — [wording/acceptance · low] A1-1 期望列与 §8.4 判据不一致
- **文件:行**：`plan.md:485`（A1-1「全绿，0 fail」）对照 `plan.md:533`（「A1-1/A-S1/A-S2 的判据是『非新增失败』，而非字面『0 fail / 全绿』」）与 `plan.md:563`（R8）。
- **实核**：本机 `python -m pytest tests/test_archive_convergence.py -q` 基线含 4 个 Windows 8.3 短路径既有失败，字面「全绿，0 fail」不可满足；A-S1/A-S2 已改为「非新增失败」，唯 A1-1 表项未同步。
- **影响**：Phase 6「§8 全绿」的字面判据与 §8.4 的覆盖判据并存，易被机械执行者误判。非事实失真、非穷举缺项。
- **单选建议**：将 A1-1 期望列改为「非新增失败（本机基线 4 failed/476 passed；4 fail 为 Windows 8.3 短路径环境差异，见 §8.4/§10 R8）」。

#### R2-2 — [wording/acceptance · low] A-S2 并用相对与绝对判据
- **文件:行**：`plan.md:516`。
- **原文**：「非新增失败（Windows 短路径 TEMP 环境前置，见 §10 R8）；通过数 ≥ A 对象环境基线 480」。
- **影响**：本环境通过数基线为 476，「≥480」与本环境基线的相对判据并列，机械判定时存在二义。非阻断（§8.4 已给出相对判据）。
- **单选建议**：删除「≥A 对象环境基线 480」，或改为「通过数 ≥ 改造前同环境基线通过数」。

#### R2-3 — [factual-precision · low] §6.2 表行 19 的早返回行号不精确
- **文件:行**：`plan.md:420`（第 19 行，`test_crlf_payload_fails_closed`）。
- **原文**：「**否**（:1770-1771 先返回）」。
- **实核**：该用例 `write_plan(..., crlf=True)` 使**整文件** CRLF，`_extract_json_fences` 将所有 fence 归入 `crlf`、`payloads` 为空，故 `gov_blocks=[]` → 进入 legacy 分支，在 `budget_gate.py:1767-1768` 的 `any(b"converge." in p for p in crlf)` 处返回；`:1770-1771` 处理的是「已解析出 gov 块 + 其他 fence CRLF」的另一形态。
- **影响**：分类结论（不达新门禁）**不变**，仅归因行号不精确。非事实性阻断。
- **单选建议**：行 19 改注 `:1767-1768（legacy 分支 CRLF 检查）`，或写「早于插入点」。

#### R2-4 — [evidence-precision · low] §12 `state-schema.md:60`「原文」为逐字前缀而非完整原行
- **文件:行**：`plan.md:601` 对照 `refs/state-schema.md:60`；标题 `plan.md:595` 声称「完整逐字原行（含首尾定位词，**无省略号**）」。
- **实核**：该行实际更长（在「parent revision。」之后还有「manifest 不自哈希；检查从 owners 重投影…」）。给出的「原文」是**逐字前缀**（与行首字符级一致，插入点在其内），可机械定位，但非「完整原行」。
- **影响**：A-S3 的机械匹配仍成立；仅标题的「完整逐字原行」对 `:60` 属过度声称。非阻断。
- **单选建议**：将 `:60` 的「原文」补全至整行，或把 §12 标题限定为「逐字定位片段（无省略号）」。

#### R2-5 — [factual-precision · low] D1 步骤 3「三条 source_ref 全为 null」不精确
- **文件:行**：`plan.md:187`。
- **实核**：三条 `reviewer-verdict` 形态的 `terminal-decision`（seq 17/45/54）**没有 `source_ref` 键**（absent），并非显式 `null`。用于 `DECISION_REFERENCED` 求值时结果一致（无 user-decision，source_ref 贡献空集），结论不改。
- **单选建议**：改为「三条均无 `source_ref` 键（r2 无 user-decision）」。

#### R2-6 — [implementation-precision · low]「批量不可表达」的机械归因不准确
- **文件:行**：`plan.md:234`。
- **原文**：「`validate_event` 的等集判定（`model.py:456-458`）拒绝任何数组/多字段/多目标形态」。
- **实核**：等集判定只约束 **key 集合**（extra/missing）；对 `corrected_event_id` 为数组、`field` 为数组等**值形态**，须由 `event-correction` 分支的值类型谓词（`corrected_event_id` 单 UUID、`field` 单字符串 ∈ `allowed`）拒绝。结论「批量不可表达」成立，但归因应补值谓词。
- **单选建议**：在 `plan.md:234` 补一句「并依赖 `event-correction` 分支对 `corrected_event_id`（单 UUID）与 `field`（单字符串）的值谓词」。

#### R2-7 — [anchor-precision · low] T1-F2 的 `_prepare_terminal_decision` 锚点范围偏短
- **文件:行**：`plan.md:350`（T1-F2「新函数近 `_prepare_terminal_decision` :523-554」）。
- **实核**：`_prepare_terminal_decision` 定义 `capture.py:523`，函数体延伸至 `:575`（`:578` 起才是 `record_terminal_decision`）。`:523-554` 只覆盖 docstring+derive 循环。
- **单选建议**：改为 `:523-575`。

#### R2-8 — [design-boundary · low, optional] DECISION_REFERENCED 的「被 decision 引用」应明确为「被四条 decision 字段**直接**引用」
- **文件:行**：`plan.md:161`（规则 5）、`:540`/`:556`（Non-Goal/R1 措辞「被 decision 引用的事件」）。
- **观察**：被 decision 的 `reviewer_event_id` 所指向 terminal 通过 `started_event_id` 关联的 `invocation-started` 事件（如 r2 event 51 之于 event 53）**不在** `DECISION_REFERENCED` 内，其非闭合字段（如 `role`）仍可经授权更正。更正需真实 user-message 授权且会在 manifest 披露，且契约威胁模型本不抵抗同权限整体重写，故**非阻断**；但 `plan.md` 的「被 decision 引用的事件」措辞应在边界上写死为「被 4 个 decision 字段直接引用的事件」。
- **单选建议**：在 §3 D1 规则 5 或 §10 R1 补一句「含被 decision 直接引用的 terminal；不含经 `started_event_id` 间接关联的 started 事件（后者为可更正面）」。

> **说明**：以上 8 条无一属于「事实失真」或「穷举缺一」。§二/§三/§五 已确认三条 R1 阻断闭合、UV 50 条处置可追溯、D3 受面穷举完整，故不因这些精度问题升级为阻断。

---

## 七、可执行判定与实施前置条件

- **判定：可执行**。两 Track 的 Phase 均 bounded（§7），每步有产物与验证；Acceptance 除 R2-1/R2-2 的文案二义（判据已由 §8.4 明确）外可机械判定；第三部修改授权（`review_mode: ultraverge` + `CONSTITUTION.md:91-96` 第四部）成立；S-F3/S-F4/S-F5 显式不改；机器块 + 用户授权 user-message（seq 9/10）+ ultraverge 要素齐备，preflight 机械校验通过。
- **实施前必须满足的前置条件（阻断性）：无**。
- **建议随实施一并修订（非阻断，建议在 Phase 0 前落地，以免 Phase 6 机械执行歧义）**：
  1. R2-1、R2-2：同步 A1-1/A-S2 的期望列为「非新增失败」口径。
  2. R2-3、R2-4、R2-5、R2-6、R2-7：行号/措辞精度修订。
  3. R2-8：补写 `DECISION_REFERENCED` 的直接引用边界（建议，非必须）。

---

## 八、结尾

- **是否需拆分对象：否**。Track-1（O1）与 Track-2（O5）的代码路径、失败语义、回滚面不相交（唯一交点是 `state-schema.md` 两处不相邻章节 + 共享测试文件，§4/§12 已隔离）；本轮 8 条问题全为局部文案/精度，不涉及机制重设计。UV3-16 的拆分建议已由用户合并裁决与结构化 Track 回应。
- **无法核实 / 环境相关断言清单**：
  1. **A 对象「480 passed / 全绿」基线**：本机复跑为 `4 failed, 476 passed, 5 skipped, 11 subtests`，4 fail 系 Windows 8.3 短路径（`ADMINI~1` vs `Administrator`），无法在本环境复现 480/全绿；计划已如实记录（`plan.md:533`/`:563`），判为环境等价。
  2. **r2 事件 55 曾存在的字面量 `PENDING` 字节**：事件 55 文件 `git log --follow` 仅一次提交 `529e691` 且内容已是 `81a2537ea9eb`，只能证实事件 56 的授权文本，无法独立证实历史 `PENDING` 字节（与计划 O1h 自述一致）。
  3. **实现后才可验证的行为**：`resolve_events`/`validate_corrections` 的 10+10b 规则、`_task_envelope_usable`、preflight 信封门、三处 init 第 4 行、adapter `--task-*`——本轮只能确认设计可行与落点/接口存在。
  4. **「机械下界 = 4」**：源自 `ultraverge_min_reviewers(3) + 设计审查 1 = 4` 的机制推导，属可辩护的下界论证，无法静态机械证明「最小派发」；r2 实测 23 已独立复算属实。
  5. **calibration 报告 freshness 相对活 HEAD 的实时性**：`_resolve_and_check_report`（`budget_gate.py:1655-1680`）仅比较 gov 块与报告内的 `freshness`，不重算活 HEAD/high-water；报告 `repository_head=13da6055` 与当前 HEAD 一致，但该「新鲜度」在代码语义上非实时校验（计划未声称相反，非计划缺陷）。
  6. **用户 2026-09-12 授权范围是否语义覆盖「O5 并入 B」**：`ab8896b1…`（seq 9）事件文本涵盖 C→B 合并，属语义判断，非纯机械。
