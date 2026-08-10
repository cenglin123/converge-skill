issue_id: 1
approach: 将 §3.3 provenance 组合从 host-reported+host_receipt+receipt-missing 改为 configured+cli_argument+backend-does-not-expose，遵守 PROVENANCE_MATRIX 约束并引用 model.py:494-513 校验逻辑
rejected_alternatives: 考虑保留 host-reported 但增加 Note 说明"不合法但未来修复"——违反 executor discipline §1 反折中（reviewer 要求真改，不打补丁）
upstream_scope_check: 无——provenance 选型是 §3.3 局部决策，不影响 CLI 接口、调用顺序、ledger 语义等上游设计
diff: §3.3 全文重写：host-reported→configured, host_receipt→cli_argument, receipt-missing→backend-does-not-expose；移除 resolved 字段声明；保留 --instance-id/--receipt 作为关联句柄；添加 model.py 引用和升级路径说明
attempt_log_entry: |
  ## Round 1 attempt · issue 1
  - reviewer_backend: xiaomi/mimo-v2.5-pro
  - Issue: "§3.3 provenance selection uses evidence_level=host-reported with resolution_reason_code=receipt-missing. This combination is illegal per PROVENANCE_MATRIX (model.py:94-99): host-reported only allows reason=None. Additionally, host-reported requires concrete resolved fields AND a bound host receipt (model.py:503-508), neither of which OCSR dispatch can provide."
  - Issue 归因（reviewer 判定）: plan_defect
  - plan_amendment_required: false
  - Approach: 将 evidence 组合严格切换为 configured + cli_argument + backend-does-not-expose（PROVENANCE_MATRIX 下该场景最严格的合法选择）；添加 model.py:494-513 引用说明校验路径；保留 --instance-id/--receipt 为非约束性关联句柄；添加 future upgrade path 注释
  - Rejected alternatives: 保留 host-reported 但加免责声明——违反 executor discipline §1（reviewer 要求真改）
  - Upstream scope check: 无
  - Diff: §3.3 全文替换（old: host-reported / host_receipt / receipt-missing + resolved 默认省略；new: configured / cli_argument / backend-does-not-expose + resolved 显式禁止 + model.py 引用 + upgrade note）
  - R1 verdict:

---

issue_id: suggestion-1
approach: 在 §3.1 CLI 表面添加 --backend（默认 opencode）和 --backend-version（默认 auto-detect）参数
rejected_alternatives: 无——reviewer 明确指定
upstream_scope_check: 无——仅补充 CLI 参数声明，不改变调用语义
diff: §3.1 在 --model 行后插入 "  --backend <backend name> \  # 默认 opencode" 和 "  --backend-version <version> \  # 默认 auto-detect via `opencode --version`"
attempt_log_entry: |
  ## Round 1 attempt · suggestion-1
  - reviewer_backend: xiaomi/mimo-v2.5-pro
  - Issue: "§3.1 CLI surface is missing --backend and --backend-version parameters, but §3.2 happy-path complete-invocation call requires them"
  - Issue 归因（reviewer 判定）: plan_defect
  - plan_amendment_required: false
  - Approach: 在 CLI 参数列表 --model 后添加 --backend（默认 opencode）和 --backend-version（默认 auto-detect via `opencode --version`）
  - Rejected alternatives: 无
  - Upstream scope check: 无
  - Diff: 插入两个参数行 + 注释
  - R1 verdict:

---

issue_id: suggestion-2
approach: 在 §3.2 Complete 失败段落后添加 Note，说明 record-terminal-decision 由 orchestrator（非适配层）在最后一次 fresh review Spawn 的 terminal 事件后调用
rejected_alternatives: 考虑在适配层内自动调 record-terminal-decision——被拒绝，因适配层不知道 converge 循环何时"最终结束"
upstream_scope_check: 无——仅文档补充，不改变调用顺序
diff: §3.2 Complete 失败段落后新增 record-terminal-decision 归属说明块，引用 archive_convergence.py:76-77
attempt_log_entry: |
  ## Round 1 attempt · suggestion-2
  - reviewer_backend: xiaomi/mimo-v2.5-pro
  - Issue: "§3.2 does not mention the record-terminal-decision step. The archive requires a terminal-decision event (model.py:76-77: 'final-decision-missing') for final_verdict_ref."
  - Issue 归因（reviewer 判定）: plan_defect
  - plan_amendment_required: false
  - Approach: 在 §3.2 Complete 失败段落后添加 Note，阐明 record-terminal-decision 由 orchestrator 在最后一次 fresh review Spawn terminal 后调用，引用 archive_convergence.py:76-77
  - Rejected alternatives: 让适配层自动判断并调用——适配层无 converge 循环终止语义
  - Upstream scope check: 无
  - Diff: 添加 ~50 字的 Note 段落
  - R1 verdict:

---

issue_id: suggestion-3
approach: 在 §3.2 failure-path 表中将 --pre-execution 的注释放大为明确说明"默认 false"，只当 Start-Process 自身失败时才加
rejected_alternatives: 无
upstream_scope_check: 无
diff: 将 "(仅当 ocsr Start-Process 失败、模型从未真调时加)" 扩展为 "(默认 false——Start-Process 成功即模型有调用。仅 Start-Process 自身失败、cmd_dispatch 返回前终止才加 --pre-execution)"
attempt_log_entry: |
  ## Round 1 attempt · suggestion-3
  - reviewer_backend: xiaomi/mimo-v2.5-pro
  - Issue: "§3.2 happy path does not explicitly show --pre-execution defaulting to false on settle. Making it explicit would improve clarity."
  - Issue 归因（reviewer 判定）: plan_defect
  - plan_amendment_required: false
  - Approach: 将 failure-path 表中 --pre-execution 注释扩展，明确默认 false（Start-Process 成功即有调用），仅 Start-Process 自身失败才加
  - Rejected alternatives: 无
  - Upstream scope check: 无
  - Diff: 单行注释扩展
  - R1 verdict:

---

issue_id: suggestion-4
approach: 将 §2.2 ROLE_CONSUMES/ROLE_VALUES 的完全对齐声明限制为"适配层用到的 6 个角色子集一致"，列出两边全集差异
rejected_alternatives: 无——reviewer 明确指定措辞
upstream_scope_check: 无——仅措辞修正，不改证据链含义
diff: 从 "**完全一致**（outer-reviewer / blind-reviewer / ultraverge-initial / executor / arbiter / design-reviewer）——适配层无需做角色翻译。" 改为 "在适配层用到的 6 个角色（outer-reviewer / blind-reviewer / ultraverge-initial / executor / arbiter / design-reviewer）范围内**子集一致**——两边的全集不同（ROLE_CONSUMES 还有 contract-proposer/challenger/finalizer 和 l2-gate-reviewer；ROLE_VALUES 还有 reviewer / release-executor），但适配层只使用两边共有且 consumes 语义一致的角色，无需翻译。"
attempt_log_entry: |
  ## Round 1 attempt · suggestion-4
  - reviewer_backend: xiaomi/mimo-v2.5-pro
  - Issue: "§2.2 claims 'ROLE_CONSUMES and ROLE_VALUES are fully aligned'. The shared subset used by the adapter (6 roles) matches exactly, but the full sets differ."
  - Issue 归因（reviewer 判定）: plan_defect
  - plan_amendment_required: false
  - Approach: 将"完全一致"限定为"适配层用到的 6 个角色子集一致"，列出两边全集中不在子集内的角色
  - Rejected alternatives: 无
  - Upstream scope check: 无
  - Diff: 单句替换
  - R1 verdict:
