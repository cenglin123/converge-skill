verdict: "阻断需修复"
blocking_issues:
  - id: "R3-B1"
    severity: "architectural"
    source_issue: "B-1"
    location: "scripts/archive_contract/capture.py:91-118,152-176,305-370"
    finding: >-
      capture 的目标 containment 仍只有 lexical relative_to；写入前不验证既有父目录是否为
      symlink/junction/reparse。workspace-relative artifact 也在确认 source 位于 workspace 之前
      lstat/open/read 源文件。fresh 反例把 active/evidence 预置为指向同一临时目录内 sibling 的目录
      symlink，begin_invocation 成功把 event 写到了 archive root 外；另一个反例证明 workspace 外文件
      已被 Path.open 后才返回 artifact-outside-workspace。
    required_fix: >-
      在任何源读取前完成 workspace/external locator、授权和路径策略验证；写 blob/event 时通过已验证的
      非 reparse 目录链或安全目录句柄逐级创建，exclusive create 后复核最终 handle identity/containment。
      capture API 入口先拒绝 unsafe active/evidence tree，并增加父目录 symlink/junction escape 与
      workspace-outside-read-order 的零越界、零读取回归。

  - id: "R3-B2"
    severity: "architectural"
    source_issue: "B-2"
    location: "scripts/archive_contract/model.py:414-426,635-696"
    finding: >-
      fresh Reviewer role、Spawn reservation、reviewer output 和 Continue instance 主链已闭合；但
      user-decision authority 仍只检查非空 user_quote/source_ref/list/accepted_state。validate_event_graph
      不解析 source_ref、不核对 presented_degradations，也不约束 accepted_state。fresh 反例中的
      source_ref='fabricated:does-not-resolve'、不存在的 degradation ref 和任意 accepted_state 被
      validate_event 与 validate_event_graph 同时接受，因而 terminal-b/c 的“新鲜用户授权”不可机械证明。
    required_fix: >-
      把 user-decision 做成可执行的 authority tagged union：source_ref 必须解析到 manifest 承诺的
      canonical transcript/message event，quote 与 source 双向一致；presented_degradations 必须逐项解析到
      当时实际 degradation，accepted_state 使用闭合枚举并与 decision_kind 一致。补 terminal-b/c 正反测试。

  - id: "R3-B3"
    severity: "architectural"
    source_issue: "B-3"
    location: "scripts/archive_contract/model.py:334-390; refs/framework-adapters.md:7-19"
    finding: >-
      observed/host-reported 现在要求 receipt/tool evidence 和 resolved provider/model-or-family，manifest/INDEX
      也投影 provenance，修复了 Round 2 的直接反例；但 tagged union 尚未闭合。requested/resolved/backend、
      receipt 和 host evidence 的标量类型/格式大多未验证，reason 与 evidence level 的语义矩阵也未绑定。
      fresh 反例证明 configured + agent_config + invocation-failed-before-resolution 可被接受；该 reason
      表示调用在解析前失败，却可出现在 succeeded terminal。文档也只给采集优先级，没有逐 backend 的
      可执行 contract fixture。
    required_fix: >-
      对每个 provenance variant 定义 exact types、required/forbidden 字段和 level/source/reason/status 矩阵；
      host evidence ref 必须采用可解析且绑定本 invocation 的结构。用机器可读 adapter matrix 驱动
      opencode/Codex/Claude/orchestrator_self 的正反 fixture，并让文档标记与常量防漂移。

  - id: "R3-B4"
    severity: "structural"
    source_issue: "B-4"
    location: "scripts/archive_contract/model.py:307-446,790-835"
    finding: >-
      exact-key event schema、owner-derived blob allowlist、artifact/revision uniqueness 和 orphan 拒绝已实现；
      但字段值 schema 仍不严格。fresh 反例中的 dict reservation_id、dict requested_provider、list
      requested_model 可通过 validate_event；instance/receipt/settlement/backend/source/user/advisory 字段也有
      同类缺口，artifact snapshot size 还接受 bool。部分非法值随后会在 set/dict 操作中产生 TypeError，
      不是稳定 fail-closed diagnostic。
    required_fix: >-
      为所有 event union 字段执行 exact scalar/container schema、长度/枚举/identifier/ref 校验；禁止 bool
      冒充 int。逐 event 类型加入字段删/改/增和错误类型测试，并断言 check 对固定种子畸形输入只返回稳定
      ArchiveError diagnostic，不泄漏未捕获异常。

  - id: "R3-B5"
    severity: "architectural"
    source_issue: "B-5"
    location: "scripts/archive_contract/capture.py:35-69; scripts/archive_contract/transaction.py:47-152,194-264"
    finding: >-
      terminal 唯一性已移入 EventLock，archive 的 source-backed-up journal failure 与 reopen move 后 journal
      failure 可以重试；但恢复状态机仍未覆盖每个破坏性写点。_finish_reopen 直接 write_bytes parent manifest
      和 reopen marker，不使用临时文件、fsync、replace 或可恢复子状态。fresh 故障注入在 parent manifest
      部分写后抛错，第二次重试稳定失败为 reopen-revision-conflict，journal 悬挂。journal 自身也未 fsync
      文件/父目录。dead-owner reclaim 读取 owner 后直接 unlink，未用 nonce/identity 防止两个恢复者误删新锁。
    required_fix: >-
      parent revision、marker 和 journal 全部采用 durable temp+fsync+atomic replace，并在 journal 中记录可幂等
      识别的子状态；对 partial write/replace/fsync/unlink/post-check 每点做第一次失败、第二次重试测试。
      stale lock reclaim 必须复核 nonce/文件 identity，无法原子证明仍为同一个 dead owner 时 fail closed。

  - id: "R3-B6"
    severity: "structural"
    source_issue: "B-6"
    location: "scripts/archive_contract/model.py:841-927; scripts/hooks/pre-push:10-28; scripts/hooks/stale-check.py:164-195; refs/orchestrator-guide.md:220-228,244-248"
    finding: >-
      check 已保留首个 validator diagnostic，INDEX 已增加 model/artifact/risks，hook 也使用 NUL 输入并对任意
      done 路径取 slug；但完整审计旅程仍未成立。INDEX revision timeline 只显示 current 与直接 parent，
      不遍历多 revision 链；artifact 行不展示 locator/source-resolution/degradation reason。pre-push 对新 branch
      的 remote zero SHA 只检查 tip commit 的 diff-tree，较早待推 commit 中引入或篡改的 archive 可绕过；它还
      校验 working tree 而非待推 commit 的 archive bytes。stale-check 复制自己的宽松 journal JSON 解析器，未与
      transaction 状态机共用。orchestrator-guide 后部仍明确要求手工 done->active 和“重新移至 done”，与顶部
      reopen/archive 唯一路径冲突。
    required_fix: >-
      INDEX 投影完整 parent chain、artifact locator/capability reason 和每 revision next-read；hook 计算每条 ref
      真正待推 range，并验证对应 commit tree（或安全 materialized tree），任何 Git range 解析失败 fail closed。
      journal 分类调用 transaction/model 公共只读解析器。消除治理文档所有手工 move 指令，并补 valid/invalid/
      degraded/三 revision 的审计 E2E 与真实 hook 仓库行为测试。

  - id: "R3-B7"
    severity: "structural"
    source_issue: "B-7"
    location: "tests/test_archive_convergence.py; docs/problems/bugfix/convergence-archive-auditability.md"
    finding: >-
      Archive Contract suite 从 17 增至 32 项且本轮独立执行全部通过，但仍远未覆盖 plan §10：四 terminal
      状态矩阵、terminal-b/c authority、失败/取消 ledger、provenance 全矩阵、总量/权限、ADS/device/UNC/
      extended/NFC/case、固定种子 property、逐故障点事务、四场景 30 秒旅程和真实 hook 推送范围均缺失。
      本轮未要求无特权创建 Windows 对象；现有 reparse 测试允许 capability skip，恢复报告/bugfix 风险文字也
      没有把无法创建对象写成已实物验证，这一点可接受。但 bugfix 仍标 status=fixed，并概括“journal 故障恢复”，
      与 fresh 复现的不可恢复点不符；该必需文件仍被 .gitignore:2 的 docs/ 忽略且未被 Git 跟踪。
    required_fix: >-
      先把本轮四个 fresh 反例固化为失败测试，再补 §10 的核心矩阵和行为 E2E。平台对象不可创建时记录明确
      capability skip/degradation，不夸大保证。bugfix 状态和验证描述只陈述实际覆盖，并以项目认可方式将文件
      纳入交付。

escalated_issue_recheck:
  B-1:
    status: "still_blocking"
    resolved_parts: "artifact/slug identifier、external authorization 前置、CLI 不先 read_bytes 已修复。"
    remaining: "父目录 reparse 越界写与 workspace containment 后置读取均已 fresh 复现。"
  B-2:
    status: "still_blocking"
    resolved_parts: "Reviewer Spawn role/output、Spawn reserve/settle、Continue same-instance 主链已机械校验。"
    remaining: "terminal-b/c user source/degradation/accepted-state authority 不可解析，可伪造。"
  B-3:
    status: "still_blocking"
    resolved_parts: "Round 2 的 observed-without-receipt/resolved 反例已拒绝，INDEX 已显示 provenance。"
    remaining: "字段类型与 level/source/reason/status tagged union 不闭合，adapter contract 无机器 fixture。"
  B-4:
    status: "still_blocking"
    resolved_parts: "未知字段、orphan blob、artifact revision 冲突已拒绝。"
    remaining: "多类 owner 字段类型仍不校验，非法 schema 可通过或触发非稳定异常。"
  B-5:
    status: "still_blocking"
    resolved_parts: "并发 terminal 与两个代表性 rename/journal failure 已恢复。"
    remaining: "reopen owner/marker partial write、durability 与 nonce-safe dead lock recovery 未闭合。"
  B-6:
    status: "still_blocking"
    resolved_parts: "首个稳定 diagnostic、基础 provenance/risks、NUL-safe slug 收集已实现。"
    remaining: "多 revision/完整 artifact journey、真实推送范围、共享 recovery parser 和治理一致性不足。"
  B-7:
    status: "still_blocking"
    resolved_parts: "测试增至 32/82；Windows 无特权对象的 capability limitation 已诚实陈述。"
    remaining: "核心验收矩阵缺失，fresh 反例未覆盖，bugfix fixed/跟踪状态不成立。"

suggestions:
  - id: "S-1"
    location: "working tree / .gitattributes"
    finding: "未跟踪 .gitattributes 仍存在，恢复报告称为接管前文件，但当前交付没有可审计归属记录。"
    recommendation: "由 Orchestrator 明确归属与是否纳入本轮；Reviewer 未修改或删除。"
  - id: "S-2"
    location: "refs/design-review-prompt.md:159"
    finding: "该文档仍说产物移入 done 后再触发设计审查，与 archive final closure/design-review event 的顺序存在歧义，且不在当前 §12 修改清单。"
    recommendation: "先由 Orchestrator 判断是否需 plan amendment；不要让 Executor 越范围静默修改。"

rubric_scores:
  authority_and_projection_integrity:
    score: 2
    rationale: "Reviewer/owner blob 闭包明显改善，但 user-decision authority 与多类字段 schema 仍可伪造。"
  invocation_ledger_and_model_evidence:
    score: 2
    rationale: "Spawn/Continue/observed 主反例已修；provenance reason/type matrix 与失败态 ledger 验证不足。"
  filesystem_and_transaction_safety:
    score: 1
    rationale: "fresh 复现 archive-root 外写、授权域外先读和 reopen 不可恢复 partial write。"
  audit_journey_and_compatibility:
    score: 2
    rationale: "五态、基础 INDEX/check 可用，但多 revision、hook commit-tree coverage 与治理接线未闭合。"
  verification_and_landing_honesty:
    score: 1
    rationale: "32/82 全绿但未覆盖已复现阻断；bugfix fixed 与 ignored 状态仍超出证据。"

plan_section_audit:
  "§4": "partial; owner-derived projection improved, strict owner value schema remains blocked by R3-B4"
  "§5": "partial; Reviewer/ledger/Continue improved, user authority and provenance union blocked by R3-B2/R3-B3"
  "§6": "blocked by R3-B1"
  "§7": "partial; five-state dispatch works, stable schema rejection remains blocked by R3-B4"
  "§8": "blocked by R3-B5"
  "§9": "blocked by R3-B1/R3-B6"
  "§10": "blocked by R3-B7"
  "§11": "blocked by R3-B6/R3-B7"
  "§12": "partial; required bugfix file exists but is ignored; .gitattributes attribution unresolved"
  "§13": "blocked; fresh Round 3 has seven blocking issue groups"

verification_summary:
  dangerous_api_static_gate:
    command: "rg -n --hidden -S 'os\\.kill\\s*\\(|TerminateProcess|kill\\s*\\(\\s*pid\\s*,\\s*0' scripts tests refs SKILL.md"
    result: "PASS — no matches; tests were run only after this gate"
  archive_contract_unittest:
    command: "python -B -m unittest discover -s tests -p test_archive_convergence.py"
    result: "PASS — 32 tests in 1.878s"
  full_unittest:
    command: "python -B -m unittest discover -s tests -p 'test_*.py'"
    result: "PASS — 82 tests in 11.955s"
  adversarial_capture:
    result: "FAIL — symlink parent wrote one event outside archive root; workspace-outside source was opened before artifact-outside-workspace rejection"
  adversarial_user_authority:
    result: "FAIL — unresolved fabricated source/degradation user-decision accepted by validate_event_graph"
  adversarial_schema:
    result: "FAIL — dict/list owner fields and semantically contradictory provenance reason accepted"
  adversarial_reopen:
    result: "FAIL — partial parent revision write makes retry fail reopen-revision-conflict with journal left present"
  diff_check:
    command: "git diff --check"
    result: "PASS"
  line_endings:
    result: "Changed/new implementation files inspected without new CRLF finding; repository has pre-existing tracked w/crlf files outside this review output."
  derived_artifacts_cleanup:
    result: "PASS — test-created scripts/__pycache__ and scripts/archive_contract/__pycache__ removed; Reviewer wrote only round-3.md"
  required_bugfix_tracking:
    result: "FAIL — git check-ignore reports .gitignore:2 docs/ and git ls-files does not contain the bugfix document"
