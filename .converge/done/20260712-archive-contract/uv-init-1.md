verdict: 阻断需修复
blocking_issues:
  - id: AC-1
    description: >-
      manifest、run.json、artifact metadata 与 canonical 文件之间没有定义唯一权威源和完整性闭包。计划同时让 manifest“包含 run provenance”、run.json 保存同一 provenance、metadata.json 保存 artifact 信息，却未规定字段重复时谁胜出、finalize 从哪里派生最终 verdict/时间线、check 比较哪一份，也未要求 manifest 覆盖 canonical 文件、run.json、metadata.json 本身的哈希。这样篡改 round-N.md、run.json 或 metadata.json 后仍可能得到一组内部自洽但不真实的 INDEX/manifest，无法证明归档所代表的精确状态。必须在 state-schema 中给出规范字段级 schema、主键/外键、派生规则和哈希覆盖图：建议 manifest 是冻结的事实索引，INDEX 只由 manifest 派生；run/artifact sidecar 是采集期权威记录，finalize 将其规范化写入 manifest 并锁定其内容哈希；最终 verdict 必须从明确列出的权威事件/用户接受记录派生而非 CLI 任意传参。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: "§3, §4, §5, §6, §7"
  - id: AC-2
    description: >-
      run schema 不能完整重建实际执行序列。现有最小字段没有 reservation_id、round/phase、attempt 或父子关联，无法把一次 Spawn 与 gate-ledger 的 reserve/settle、round-N.md、盲审或设计审查机械关联；“单调 sequence”也未说明是否全归档全局连续、是否允许缺口。更严重的是契约只记录 fresh Spawn，而 converge 的 inner-loop Continue 同样产生决定 verdict 的模型输出；record-run 又同时拒绝空 output，却要求记录 status，导致 spawn_failed、cancelled、超时或无输出调用无法合法留痕。必须把 schema 提升为 invocation/event 契约：覆盖 Spawn 与 Continue，定义全局连续 sequence、稳定 event_id、reservation_id（Continue 可为 null 并指向 parent instance）、role/phase/round/attempt、started/completed、terminal status 及各状态允许的 prompt/output/null 组合，并让 finalize 对 ledger、round log 与 run 集合做双向完整性校验。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: "§4, §7 record-run, §8"
  - id: AC-3
    description: >-
      reviewed artifact 的“精确版本”与 hash 语义仍不确定。计划没有规定 SHA-256 是对原始字节、规范化文本还是复制后文件计算，也没有规定大小单位、hex 格式、符号链接/目录/特殊文件、复制期间源文件变化（TOCTOU）和 source_hash 与 snapshot_hash 不同的合法条件。hash-only 条目只有摘要而没有字节，不能“精确复现”，却没有把归档能力降级为仅可验证身份；source locator 也缺少 workspace 根身份和跨平台路径规范，移动到另一台机器后无法可靠解析 source_drift。必须定义对同一捕获字节流计算小写 SHA-256、原子/变更检测策略、文件类型与 symlink 策略、path 使用 POSIX 相对形式及 workspace identity，并在 manifest 暴露 reproduction_capability（snapshot | identity-only）而不是把 omitted 快照仍计作可复现。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: "§2, §5, §6, §7 finalize/check"
  - id: AC-4
    description: >-
      模型 provenance 仍是声明而不是可审计事实。provider/model/family/model_resolution 没有规范枚举、requested 与 resolved 的区分、值的采集来源/证据、backend 版本，也没有说明 instance 继承模型、别名、路由模型和框架只能返回部分信息时如何表达。“已知模型不得写 unknown”无法由脚本机械判断，而 unavailable_reason 可能成为通用逃生口。必须在 framework-adapters 与 state-schema 定义每个 backend 的采集优先级和可验证来源，至少记录 requested_model、resolved_model、provider、family、backend/backend_version、resolution_status、resolution_source/evidence；为 unavailable/partial 设闭合原因码和按 backend 能力允许的组合，check 对非法组合 fail closed，并在 INDEX 显示 provenance 降级而非静默视为完整。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: "§4, §7 record-run, §8"
  - id: AC-5
    description: >-
      相对链接缺口只对新生成的 INDEX 有明确承诺，没有解决归档内 canonical Markdown 的移动语义。样本问题正是 round/报告仍指向 active 绝对路径；当前计划既不说明 finalize 是否重写这些链接，也不说明 check 是扫描全部 Markdown、仅导航层，还是把 prompt/output 中的原样文本排除。直接重写历史输出又会破坏证据字节。必须划清“导航链接”与“原始证据文本”的边界：INDEX/所有生成文档和 canonical 文档中的真实 Markdown link 必须使用归档根内 POSIX 相对路径并验证目标及 anchor；原始 prompt/output 保持字节不变且不参与可导航链接判定，必要时由 manifest 提供映射。测试应先 finalize、整体移动/改名归档目录，再对全部规范导航入口运行 check，而不只是验证 INDEX。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: "§3, §6, §7 check, §9.1"
  - id: AC-6
    description: >-
      legacy 兼容只有“无 manifest = legacy-unverifiable”一条，缺少可迁移的版本判定状态机。未定义 manifest 的 schema_id、schema_version 格式、未知未来版本、损坏/部分写入 v1、错误类型或目录内偶然同名 manifest 的分类；scan 因而可能把损坏的新归档当 legacy 宽松放行，或把未来版本误按 v1 检查。收敛后修订还要求删除旧 manifest/INDEX，形成中间态且没有原子提交/恢复规则。必须定义 missing、malformed、unsupported-version、invalid-v1、valid-v1 的互斥分类，只有 missing 才能 legacy-unverifiable；加入 schema_id 和版本兼容规则、临时文件加原子 replace 的 finalize 协议、失败恢复行为，以及显式的只读 migration/upgrade 策略（可以选择不自动迁移，但必须说明如何保留并验证 v1、未来如何增加 v2 reader）。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: "§2, §6, §7 scan, §8"
suggestion_issues:
  - description: >-
      Q1 基本通过：产物身份和目标清楚；Q2/Q4/Q5 未通过，主要表现为“精确复现”与 hash-only 能力不一致、manifest/run/artifact 权威边界灰色、run/Spawn/invocation 及 source/snapshot hash 命名语义未闭合。Q3 仅部分通过：允许 workspace 外绝对路径会把用户名等环境信息写入可长期保存的 manifest，建议采用可选脱敏 display locator，并把真实绝对 source 仅作为显式非便携、潜在敏感字段处理。
  - description: >-
      prompt.txt 的“精确字节证据”可能包含密钥、个人信息或私有输入；“不复制到归档之外”并不等于安全。建议在契约中明确归档本身的敏感级别、文件权限/ignore 策略和 redacted 与 exact 两种互斥模式；若采用 redaction，manifest 必须诚实标记 prompt_exact=false，不能仍宣称精确复现。
  - description: >-
      DR2/DR6/DR7 的对抗测试建议再覆盖：manifest/run sidecar 冲突、canonical 文件被篡改、sequence 缺口、failed/timeout/Continue、源文件捕获时并发变化、symlink/path case、损坏 v1、未知 v2、非 ASCII anchor 与整个 done/<slug> 跨卷移动。固定 golden fixture 与已知 SHA-256 可显著降低 schema 演进时的回归风险。
  - description: >-
      DR3/DR5：metadata.json 与 manifest 重复会增加双写漂移；若 sidecar 只服务采集期，可在规范中明确其生命周期和只生成不手改，或让 manifest 只保存 sidecar hash/引用。避免同时把两份都描述成长期事实源。
rubric_scores:
  - dimension: Correctness
    score: 3
    evidence: "六项缺口均有对应机制，但当前 hash、事件关联和最终 verdict 来源不足以证明结论正确。"
  - dimension: Completeness
    score: 2
    evidence: "缺失 invocation 生命周期、权威/完整性图、版本状态机、跨文件链接扫描边界与可复现能力分级。"
  - dimension: Maintainability
    score: 3
    evidence: "目录分层与单一脚本方向良好，但 manifest/sidecar 双写和未定义迁移规则会形成长期维护债务。"
  - dimension: Conciseness
    score: 4
    evidence: "计划结构紧凑、文件改动范围明确；新增规范应尽量集中在 state-schema，避免多处复制同一字段表。"
  - dimension: Consistency
    score: 3
    evidence: "INDEX/分层/legacy 方向一致，但精确复现与 hash-only、完整 run provenance 与仅 fresh Spawn、不可变证据与链接重写之间存在未裁决张力。"
