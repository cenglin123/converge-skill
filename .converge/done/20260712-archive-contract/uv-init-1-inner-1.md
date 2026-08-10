verdict: 阻断需修复
reviewed_artifact: plan.md
amendment_report: plan-amendment-report.md
issue_results:
  - id: AC-1
    status: Rejected
    assessment: >-
      权威生命周期、manifest 哈希闭包、sidecar 规范化、INDEX 单向派生及重复字段冲突处理已经补齐；但最终 verdict 的权威事件仍未闭合。§4 写成“最终 outer/blind/design review”均可作为 authoritative terminal event，而现行 design-review 契约明确不给 verdict；同时终止-b/终止-c 的最终成立依赖用户显式接受，§5 的 invocation lifecycle 只覆盖 Spawn/Continue，没有定义可由 manifest 引用的 user-decision event。仅由 retrospective 反向佐证不能替代新鲜用户决策的权威记录。因此 AC-1 关于“最终 verdict 必须从明确权威事件派生”的核心要求仍有一处未满足。
    required_amendment: >-
      在计划中明确 terminal decision 的闭合联合类型：fresh reviewer/blind reviewer 的 verdict event，或终止-b/c 对应的 user-decision event（含可审计用户原话/来源引用）；design-review 只能作为 advisory completion event，绝不能产生或覆盖最终 verdict。manifest 的 final_verdict_ref 必须只引用上述合法 verdict/decision event，并与 round/retrospective 双向一致。
    location: "§4 最终 verdict 段；§5 invocation lifecycle"
  - id: AC-2
    status: Accepted
    assessment: >-
      §5 已把 run 提升为覆盖 Spawn/Continue 的 invocation lifecycle，定义调用前 begin、完成/恢复、全局连续无缺口 sequence、event/parent、round/phase/attempt、reservation/ledger 双向绑定，以及 succeeded/failed/cancelled/timeout 的合法 output 组合；§10.1-2 提供了对应对抗验证。原阻断已闭合。
    evidence: "§5；§10.1-2"
  - id: AC-3
    status: Rejected
    assessment: >-
      原始字节 SHA-256、64 位小写 hex、byte 单位、evidence/reproduction capability 分级、workspace identity、句柄读取、TOCTOU 和链接/特殊文件策略均已补齐；但 locator schema 自相矛盾。§2 明确允许经新鲜授权处理 workspace 外文件，§6 却规定“每个 artifact 记录 POSIX workspace_relative_path”，workspace 外文件不可能具有合法的 workspace-relative path。若实现者伪造相对路径会破坏可移植身份，若写绝对路径又违反脱敏/便携目标。因此 AC-3 的 source locator 合法组合仍未完全定义。
    required_amendment: >-
      将 locator 定义为闭合 tagged union：workspace 内使用 `{kind: workspace-relative, workspace_id, path}`；workspace 外使用 `{kind: external, display_locator, portable: false, authorization_ref}`，不得要求或保存 workspace_relative_path，默认 check/source_drift 不回读。分别定义两种分支的必填/禁止字段及 manifest 能力降级。
    location: "§2 workspace 外证据策略；§6 首段"
  - id: AC-4
    status: Accepted
    assessment: >-
      §5 已拆分 requested/resolved provider/model/family，增加 backend/version、evidence_level、resolution_source 与闭合 reason code，并明确 configured/inherited 不得冒充 observed；§11 将 backend 合法组合的规范责任放入 framework-adapters，§10.3 要求矩阵测试。原阻断已闭合。
    evidence: "§5 模型 provenance；§10.3；§11"
  - id: AC-5
    status: Accepted
    assessment: >-
      §3 已明确 canonical/generated Markdown 的真实导航链接必须使用归档根内 POSIX 相对路径并验证 target/anchor，raw prompt/output 保持原字节且排除导航判定；同时要求整体移动/改名后复验，§10.10 覆盖相应测试。原阻断已闭合。
    evidence: "§3；§10.10"
  - id: AC-6
    status: Accepted
    assessment: >-
      §7 已定义 missing/malformed/unsupported/invalid/valid 五态、schema_id/version、未来版本与外来 schema 的 fail-safe 行为，以及 scan 只读策略；§8 用 staging、journal、post-check、rollback 和 reopen revision 消除半完成归档与人工删除生成物，§10.8-9 覆盖故障和状态分派。原阻断已闭合。
    evidence: "§7；§8；§10.8-9"
summary:
  accepted: 4
  rejected: 2
  remaining_blocking_ids:
    - AC-1
    - AC-3
  conclusion: >-
    修订已解决绝大多数 schema、事件、hash、provenance、链接与 legacy 问题，但 AC-1 的 verdict 权威事件类型和 AC-3 的外部 artifact locator 分支仍会导致实现产生互相冲突的合法状态。两处均可通过局部 plan amendment 修复，无需重新设计总体方案。
