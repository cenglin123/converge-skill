verdict: "阻断需修复"
blocking_issues:
  - id: "B-1"
    severity: "architectural"
    location: "scripts/archive_contract/capture.py:183-230; scripts/archive_convergence.py:108,118"
    plan_refs: ["§6", "§9", "§10.5-10.7"]
    finding: >-
      artifact_id 未经过任何相对路径或标识符校验就拼入 snapshot 路径；exact/redacted capture
      可以在 event 创建前把文件写出 archive root。CLI 还在 capture 层验证之前直接 read_bytes(prompt/output)，
      会跟随调用方提供的链接并绕过句柄级 TOCTOU、secret、大小和授权策略。external artifact 也先读取源，
      后检查 authorization_ref，违背“外部内容无本次新鲜授权不得读取/持久化”的边界。
    evidence: >-
      临时目录反例调用 capture_artifact(..., artifact_id='../../../escaped', evidence_mode='exact')；
      返回的 snapshot 解析到 archive root 外，artifact_escaped_root=True，且文件实际存在。
    required_fix: >-
      在任何读取或写入前验证 artifact/invocation 标识和所有目标路径；路径必须由安全目录句柄/受控 basename
      构造并复核 containment。把 prompt/output/artifact 的安全打开、授权、secret、file/total limit、
      reparse/hardlink/TOCTOU 校验收口到 capture API，CLI 不得先行读取任意 Path。补越界写与“拒绝后零副作用”测试。

  - id: "B-2"
    severity: "architectural"
    location: "scripts/archive_contract/model.py:194-250,304-352,414-451"
    plan_refs: ["§4", "§5", "§5.1", "§13"]
    finding: >-
      authority、invocation 与 ledger 关系没有被 schema 闭合。reviewer-verdict 只检查所引 terminal 成功，
      不检查 started owner 的 role、fresh/blank-slate 资格、verdict_output_ref 是否绑定该 invocation output；
      任意 worker 可成为 final Reviewer。Spawn 可完全不带 reservation 且无 ledger，仍能 archive；
      Continue 只检查 parent 是 Spawn started event，不检查同一 instance，数据模型中也没有可执行的同-instance 绑定。
    evidence: >-
      临时目录构造 role='worker'、无 reservation 的成功 Spawn，再写 decision_type='reviewer-verdict'；
      archive 后 schema_state=valid。现有 test_archive_check_move_and_tamper 也把无 reservation Spawn 当合法基线。
    required_fix: >-
      由 started/terminal owner graph 机械证明 Reviewer 身份、review kind、output ref、Spawn reservation/settlement
      双向绑定以及 Continue 的同-instance parent；所有 Spawn 无 reserve 必须 fail closed。为成功、失败、取消、超时
      和 Continue 分别补正反向 ledger/instance/receipt 测试。

  - id: "B-3"
    severity: "architectural"
    location: "scripts/archive_contract/model.py:194-250,354-411,595-650; refs/framework-adapters.md"
    plan_refs: ["§4", "§5 模型 provenance", "§9.1"]
    finding: >-
      model evidence 的合法矩阵不足且 INDEX 会过度声明。observed/host-reported 不要求 receipt、resolved provider/model
      或绑定本 invocation 的 host evidence；一个 resolved 字段全空、receipt 为空的 terminal 可声明 observed，且不会生成
      model-provenance degradation。manifest 的 invocation projection 也只保留 event_id/invocation_id/type，
      INDEX timeline 不呈现 requested/resolved/source/reason，因此审计者无法完成计划要求的模型证据旅程。
    evidence: >-
      临时 valid archive 使用 evidence_level='observed'、resolution_source='host_receipt'，但 receipt 和所有 resolved
      字段为空；最终 manifest 无任何 model-provenance degradation（observed_without_model_has_degradation=False）。
    required_fix: >-
      将 adapter 合法组合变成严格可执行 tagged union：observed/host-reported 必须有绑定本次调用的 host evidence
      和可说明的 resolved 字段；字段不可得必须降为 configured/inherited/unavailable 并带闭合 reason。
      manifest/INDEX 投影 requested、resolved、source、reason 和 degradation，并补各 backend 正反矩阵测试。

  - id: "B-4"
    severity: "structural"
    location: "scripts/archive_contract/model.py:194-250,354-411,525-593"
    plan_refs: ["§4", "§5.1", "§7"]
    finding: >-
      manifest 不是从 owner allowlist 投影精确闭包：project_manifest 会把 evidence 下除 events 外的任意普通文件
      一概收进 blobs，使无 owner event 的孤儿文件自动成为“合法事实”。event validator 也不拒绝未知字段，
      invocation/artifact evidence ref 的字段集合、hash/size/mode/capability 组合及 artifact/revision 唯一性未完整校验。
      这与“未声明额外文件 invalid、owner 冲突 fail closed、严格 schema”相反。
    evidence: >-
      在合法 active 中预置 evidence/orphan.txt 后 archive；结果 orphan_blob_declared=True，最终 check 为 valid。
    required_fix: >-
      blob 列表只能由已验证 owner event/revision 引用生成；先计算允许路径，再拒绝任何孤儿或错误目录形状。
      对每种 event 使用 exact-key schema 和闭合 tagged union，验证 UUID/类型/时间/正整数/唯一性及所有 evidence ref；
      补逐类删改增、未知字段、孤儿 blob 和联合冲突测试。

  - id: "B-5"
    severity: "architectural"
    location: "scripts/archive_contract/capture.py:38-176; scripts/archive_contract/transaction.py:19-185"
    plan_refs: ["§4 append-only", "§5", "§6", "§8"]
    finding: >-
      append-only 写入与 archive/reopen 事务不具备声明的失败恢复。prompt/output/snapshot 在 event lock 外先写，
      event append 失败会留下孤儿；complete 的“查未 terminal”在锁外，两个并发 complete 可同时追加 terminal。
      archive 不读取现有 journal、不实现 owner-dead lock 恢复；source 移到 backup 后若 journal 写失败，
      active 与 done 都不存在，重试只报 source FileNotFound。reopen 更是在无 journal/rollback 下先移动 done，
      再分步写 revision、删 manifest/INDEX，任一步失败都会留下半 reopen。
    evidence: >-
      注入 source-backed-up journal 写失败后：source_exists_after_failure=False、done_exists_after_failure=False、
      backup_count=1、staging_count=1；第二次 archive 返回 FileNotFoundError，未按 journal 幂等恢复。
    required_fix: >-
      让 invocation blob+event 和 terminal 唯一性在同一排他事务中提交或可确定性回滚；实现带 nonce/owner-dead
      规则的锁恢复。archive/reopen 在第一次破坏性动作前 durable journal，逐状态提供幂等 recovery，覆盖每个
      rename/journal/fsync/post-check/cleanup 故障点，并保证失败后恰有一个 authoritative 副本。

  - id: "B-6"
    severity: "structural"
    location: "scripts/archive_contract/presentation.py:13-56; scripts/archive_contract/model.py:460-650; scripts/hooks/pre-push:14-43; scripts/hooks/stale-check.py:164-192"
    plan_refs: ["§7", "§8", "§9.1", "§11"]
    finding: >-
      30 秒审计与 hook 接线未达到合同。invalid check 通过 schema_state 丢弃原 ArchiveError，只返回泛化 manifest 路径
      与通用 next_action；INDEX 不展示完整模型/artifact provenance、manifest risks 或多 revision 链。
      pre-push 仅当 diff 中出现 .converge/done/*/manifest.json 才 check：只改 plan.md、event、snapshot 或 INDEX
      可绕过 hook。shell 的 for path in $changed 还会拆分空格路径。stale-check 只认识 archive journal，
      而 reopen 根本没有 journal 状态可识别。
    required_fix: >-
      保留 validator 的首个稳定 code/summary/path/next_action；INDEX 按固定章节完整投影 decision、所有 degradation、
      revision/event/next-read 信息。pre-push 对任意 changed done/<slug>/ 路径去重后 check，并使用 NUL 安全 Git 输出；
      stale-check 与真实 archive/reopen recovery 状态机共用解析器。补 valid/invalid/degraded/多 revision E2E 与 hook 篡改测试。

  - id: "B-7"
    severity: "structural"
    location: "tests/test_archive_convergence.py; .converge/active/20260712-archive-contract/landing-report.md; docs/problems/bugfix/convergence-archive-auditability.md"
    plan_refs: ["§10", "§12", "§13"]
    finding: >-
      67 个全量 unittest 虽通过，但 Archive Contract 只有 17 个测试方法，未覆盖计划列出的多数核心验收：
      四种 terminal 状态和 recovery、user terminal-b/c、Continue 同-instance、无 reservation Spawn、
      exact opt-in/外部授权读取顺序、总量/稀疏/权限、ADS/设备/UNC/extended/NFC/case、
      故障点恢复/重试、逐类闭包篡改、固定种子 property、四场景 30 秒旅程和 hook 行为。
      因此 landing-report 的“合同覆盖”和 E2E/对抗验证表述不能由现有自动化证据支持。
    required_fix: >-
      先把上述反例固化为失败测试，再补齐 §10.1-13 的正反路径与故障注入；landing report 和 bugfix 文档只报告
      实际执行且可由测试名/输出复核的范围。bugfix frontmatter 必填元数据本身合规，但文件被 .gitignore:2 的 docs/
      忽略，落地交付必须显式纳入版本控制或采用项目认可的跟踪方式，并在正文写入实际验证结果而非仅转指 landing report。

suggestions:
  - id: "S-1"
    location: "working tree / .gitattributes"
    finding: >-
      当前 git status 另有未跟踪 .gitattributes，而 landing-report 声明未修改该文件；fresh reviewer 无法判定其归属。
    recommendation: "归档前由 Orchestrator 核实该文件是既有用户改动还是本轮产物，并在改动范围记录中说明；不要擅自删除。"
  - id: "S-2"
    location: "scripts/archive_contract/model.py 与 refs/state-schema.md"
    finding: "人类规范只给摘要，而可执行 schema 接受大量未声明形状，‘双单源防漂移’目前没有 contract fixture。"
    recommendation: "修复 blockers 后增加字段/枚举/ownership matrix 的机器可读 contract fixture，测试文档标记与 model 常量一致。"

rubric_scores:
  authority_and_projection_integrity:
    score: 1
    rationale: "非 Reviewer 可拥有 final verdict，任意 evidence blob 会被自动合法化，owner/projection 闭包失效。"
  invocation_ledger_and_model_evidence:
    score: 1
    rationale: "Spawn 可绕过 reservation；Continue 同-instance 未证明；observed 可在无 receipt/resolved model 时成立且无 degradation。"
  filesystem_and_transaction_safety:
    score: 1
    rationale: "已复现 archive-root 越界写和 source-backed-up 后不可恢复，核心安全与原子性门槛不成立。"
  audit_journey_and_compatibility:
    score: 2
    rationale: "五态和基础 INDEX/check 可运行、legacy scan 只读，但诊断、完整 provenance、revision timeline 与 hook 覆盖不足。"
  verification_and_landing_honesty:
    score: 1
    rationale: "现有测试全绿但覆盖远低于 §10/§13，landing 声明超出自动化证据；必需 bugfix 文档仍被忽略。"

plan_section_audit:
  "§4": "blocked by B-2, B-4, B-5"
  "§5": "blocked by B-2, B-3, B-5"
  "§6": "blocked by B-1, B-5"
  "§7": "partial; blocked by B-4, B-6"
  "§8": "blocked by B-5"
  "§9": "blocked by B-1, B-6"
  "§10": "blocked by B-7"
  "§11": "blocked by B-6, B-7"
  "§12": "partial; file set exists, but required bugfix file is ignored and scope attribution needs resolution"
  "§13": "blocked; fresh landing review has seven blockers"

verification_summary:
  unittest:
    command: "$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -p 'test_*.py'"
    result: "PASS — 67 tests in 9.898s"
  diff_check:
    command: "git diff --check"
    result: "PASS"
  derived_artifacts_cleanup: "PASS — no __pycache__ directories found after review; all adversarial fixtures used TemporaryDirectory and were removed"
  change_scope_observation:
    tracked_modified: ["SKILL.md", "refs/framework-adapters.md", "refs/orchestrator-guide.md", "refs/state-schema.md", "scripts/hooks/pre-push", "scripts/hooks/stale-check.py"]
    untracked: [".gitattributes", "scripts/archive_contract/", "scripts/archive_convergence.py", "tests/test_archive_convergence.py"]
    ignored_required_file: "docs/problems/bugfix/convergence-archive-auditability.md (.gitignore:2 docs/)"
