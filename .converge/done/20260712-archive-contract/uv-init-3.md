# Ultraverge 初始评议 · Reviewer 3（对抗性 / 安全边界 / 自动化测试）

```yaml
round: ultraverge-initial-3
reviewer_focus: adversarial-security-and-tests
verdict: 阻断需修复
deterministic_check: skipped
deterministic_check_skip_reason: "当前审查对象是落地前计划；计划中的 archive_convergence.py 与 test_archive_convergence.py 尚不存在，不能把现有 budget_gate 测试当作新 validator 的执行证据。"
blocking_issues:
  - id: SEC-1
    description: |
      [plan_amendment_required]: true 当前“证明精确文件版本/实际后端与模型谱系”的主张无法由同一归档内可共同改写的 manifest、run.json、文件和 SHA-256 自证。攻击者同时替换 artifact（或 prompt/output）与其哈希后，check 仍可通过；record-run 又发生在 Spawn 之后，用户提供的 provider/model/instance_id 与 prompt/output 路径也不能证明这些字节确实是该次调用的输入、输出或真实模型回执。这是 hash 自证循环，不是来源真实性证明。计划必须二选一：引入归档外、不可由 archive 工具共同改写的信任锚（例如宿主原始 receipt + 签名/受保护审计日志或提交对象），并验证其绑定；或把目标、manifest/INDEX 文案诚实收窄为“归档时点的内部一致性与声明 provenance”，明确不能证明历史未被整体重写。`model_resolution=unavailable` 也必须使“已证明实际模型”的能力降级，而非仍满足总目标。
    attribution: plan_defect
    severity: conceptual
    plan_amendment_required: true
    location: "§1, §4, §5, §6, §7"
    rubric_gap: true
  - id: SEC-2
    description: |
      [plan_amendment_required]: true 路径边界只写“拒绝路径逃逸”，未定义 Windows 上可执行的安全判据。仅做 `resolve()`/前缀判断不足以覆盖目录 junction/reparse point、symlink、hardlink、UNC/extended-length 路径、ADS（`file:stream`）、设备名、大小写及尾随点/空格等价、Unicode 规范化碰撞和 safe-name 冲突；先检查再 `copy` 还存在 TOCTOU，攻击者可在验证后替换链接或源文件。必须规定：active/done/workspace 根的规范化与 same-file/containment 规则；拒绝或受控处理任何 reparse point、非普通文件和 ADS；使用不可预测 staging、排他锁、原子创建/rename、打开句柄后的 fstat/identity 复核与复制后复核；禁止跟随归档树内链接。失败必须清理临时项且不污染 active/done。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: "§3, §5, §7"
    rubric_gap: true
  - id: SEC-3
    description: |
      [plan_amendment_required]: true run sequence 与 finalize 没有并发协议。两个 record-run 可同时观察相同“下一 sequence”、通过重复检查并互相覆盖 run.json；record-run、budget settle、finalize/check/move 之间也可交错，制造遗漏 run、伪闭合或“check 通过后再变更”的归档。必须把 sequence 分配定义为工具在锁内的原子操作（不能信任调用者手填），为每个 run 用临时目录 + exclusive create + atomic rename，给整个 convergence 目录定义单写者锁/锁超时/陈旧锁策略，并让 finalize 在同一锁和同卷 staging 下冻结输入、重建输出、验证后原子提交；移动到 done 后再按最终路径复验。不得声称跨卷 move 原子。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: "§4, §7, §8"
    rubric_gap: true
  - id: SEC-4
    description: |
      [plan_amendment_required]: true “预算闭合”和 run provenance 目前是两套可分别伪造的数据。现有 test_budget_gate 明确保留 auditable-only 下把 reviewer 伪标 executor 绕过 per-scope 的漏洞；计划也未要求 run.json 携带 reservation_id、ledger event/receipt 标识，未要求 reservation→spawn_succeeded→settle 与 run entry 一一对应并交叉核对 role、instance_id、target_round/sequence、状态。仅检查“无 pending reservation”可由补写假的 settlement 或伪标签得到假闭合。finalize/check 必须调用同一个严格 ledger validator，并验证所有 fresh Spawn 的 run 与成功 reservation/settlement 的双向全覆盖及字段一致；孤儿 run、孤儿成功 spawn、重复 instance_id/receipt、失败/取消却有成功输出均应 fail-closed。仍须诚实标注 auditable-only 无法防止具备写权限者重写整本 ledger。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: "§4, §7, §8, §9；tests/test_budget_gate.py::TestRoles"
    rubric_gap: true
  - id: SEC-5
    description: |
      [plan_amendment_required]: true 默认复制完整 prompt/output 与任意 artifact 会把密钥、令牌、个人数据、绝对用户名/外部路径和超范围文件持久化进通常可提交的 done 归档；“不复制到归档之外”没有解决归档本身的泄漏面。artifact 参数还是一项任意文件读取能力。必须定义数据分级与最小化策略：默认仅保存哈希/字节数和经批准的可公开副本，敏感内容采用显式 opt-in、脱敏或加密；禁止归档常见秘密文件、设备/管道及 workspace 外文件，除非有新鲜明确授权；外部 locator 应可脱敏且不得因 source_drift 自动读取未授权位置；设置大小/总量上限、防压缩或稀疏文件资源耗尽，并规定文件权限。prompt/output 非空不等于安全可归档。
    attribution: plan_defect
    severity: architectural
    plan_amendment_required: true
    location: "§2, §3, §4, §5, §7"
    rubric_gap: true
  - id: SEC-6
    description: |
      [plan_amendment_required]: true manifest/check 的规范覆盖不足。计划只明确重算“归档快照哈希”，没有要求 canonical 文件、run.json、prompt/output、metadata.json、INDEX 的完整集合和路径映射都被封闭地承诺；多余未声明文件、缺失文件、重复/大小写碰撞路径、manifest 篡改、INDEX 内容漂移可能逃逸。应定义 canonical serialization、manifest 可承诺对象集合（排除自身或使用外部锚，避免自哈希循环）、拒绝重复 JSON key/非规范数字与未知字段、精确枚举允许的目录树，并让 check 从底层文件重新派生 manifest/INDEX 后做字节级或语义规范化比较。scan 必须拒绝 done 子项中的链接/reparse point，不能越界遍历。
    attribution: plan_defect
    severity: structural
    plan_amendment_required: true
    location: "§3, §6, §7"
    rubric_gap: true
  - id: TST-1
    description: |
      [plan_amendment_required]: true §9 的九个测试不足以让 validator 可信，主要是顺序 happy-path 与单文件篡改测试，未验证上述信任边界。必须增加：manifest+payload 联合篡改（应由外部锚发现，或证明只能报告内部一致性）；canonical/run/prompt/output/metadata/INDEX 各类删改增；ledger/run 双向绑定与伪 settlement/伪 role/重复 receipt；并发 record-run/finalize、锁崩溃恢复、check 后竞态；symlink/junction/reparse point/hardlink/ADS/命名碰撞；父目录逃逸和扫描链接；FIFO/设备/稀疏/超大文件与权限错误；复制中源文件替换；失败注入下 active/done 不污染。Windows 测试不能只测“中文+UTF-8”，还要覆盖大小写、保留名、尾随点空格、UNC/`\\?\`、NFC/NFD 和长路径；不支持创建某类 reparse point 时必须显式 skip reason，并由 Windows CI 真跑。另应做属性/模糊测试验证任意输入下“不越界写、失败不移动、check 不抛未捕获异常”。
    attribution: plan_defect
    severity: structural
    plan_amendment_required: true
    location: "§9"
    rubric_gap: true
suggestion_issues:
  - description: "把 `record-run` 拆为 `begin-run`（在 Spawn 前冻结 prompt hash 与 reservation）和 `complete-run`（绑定宿主 receipt、output、settlement），比 Spawn 后一次性补录更容易形成真实时序证据。"
  - description: "为 source_drift 单独定义三态：same / drifted / unavailable；unavailable 不应把历史快照判坏，也不能被误报为 same。默认 check 应可完全离线且不读取 workspace 外源，源漂移检查改成显式选项。"
  - description: "finalize 生成时间与 started/completed 时间只用于展示，不作为顺序或安全判断；事件顺序以锁内 sequence 与绑定 receipt 为准，并验证 completed >= started。"
  - description: "修订归档时不要简单删除旧 INDEX/manifest 后覆盖；若要求可复盘修订历史，保存 generation/revision 链或由外部版本控制锚定，否则会丢失先前归档签发状态。"
  - description: "根级 clutter 规则应采用显式 allowlist，而不是容易被大小写、Unicode 或新命名绕过的若干 glob 黑名单。"
antipattern_observations:
  - round_referenced: 1
    type: false_generality
    evidence: |
      计划把“manifest 内 SHA-256 一致”泛化为“证明精确历史版本与实际模型谱系”，跨越了其信任边界。
  - round_referenced: 1
    type: environment_lock-in
    evidence: |
      只列“Windows 路径与中文 UTF-8”测试，未把 Windows reparse point、ADS、路径等价与原子 rename 语义纳入设计。
rubric_scores:
  - dimension: 目标与边界诚实性
    score: 2
    evidence: "legacy 与 source_drift 边界写得清楚，但自包含哈希不能支撑‘证明’主张。"
  - dimension: 安全与信任边界
    score: 1
    evidence: "缺少 symlink/junction/TOCTOU、敏感复制、外部信任锚和任意文件读取防护。"
  - dimension: 一致性与可审计性
    score: 2
    evidence: "结构有 manifest/INDEX/run/artifact 分层，但 run、ledger、receipt 尚未一一绑定，manifest 可整体重写。"
  - dimension: 自动化验证充分性
    score: 2
    evidence: "九项测试覆盖基础回归，却未覆盖联合篡改、并发、故障注入和 Windows 对抗路径矩阵。"
  - dimension: 可实施性与运维韧性
    score: 2
    evidence: "stdlib CLI 方向可实施，但原子提交、锁、恢复、权限与跨卷语义未定义。"
contract_amendment_required: false
```

## Q1–Q5 前置自检

| 问题 | 判定 | 证据与影响 |
|---|---|---|
| Q1 产物身份自洽 | 否（blocking） | 名称是 archive contract，但目标把“可重算的一致性索引”描述成“真实性证明”；实现没有独立信任锚。 |
| Q2 产物边界诚实 | 否（blocking） | `unavailable`、auditable-only、hash-only 与“证明实际模型/精确版本”并存，能力降级没有反映到最终 claim。 |
| Q3 产物数据纯度 | 否（blocking） | 工具允许复制任意 prompt/output/artifact 和外部绝对 locator，未隔离敏感数据与环境特定路径。 |
| Q4 职责边界自洽 | 否（blocking） | archive validator、budget gate、framework adapter 与宿主 receipt 的责任未闭合；谁证明真实 Spawn、谁分配 sequence、谁冻结 finalize 输入均不明确。 |
| Q5 命名一致性 | 基本是 | INDEX/manifest/run/artifact 命名总体清楚；但“provenance”“proof”“snapshot/hash-only”需要按可信度分级，避免同词覆盖声明、内部一致性和外部认证三种语义。 |

## DR1–DR7 扩域审查

| 维度 | 结论 | 关键发现 |
|---|---|---|
| DR1 概念与命名一致性 | 不通过 | “证明”与“声明/一致性校验”混用，是本计划最核心的概念越界。 |
| DR2 可维护性 | 有条件不足 | 单一 stdlib 脚本可取，但 path policy、manifest schema、ledger validation 若各自重写会漂移；应复用单源 validator 与规范序列化器。 |
| DR3 可扩展性 | 有条件不足 | schema_version 是正确扩展点；未知字段、能力位、迁移/修订 generation 和 adapter receipt 扩展语义尚未定义。 |
| DR4 职责与系统边界 | 不通过 | record-run 在 Spawn 后补录，无法承担 invocation recorder；budget ledger 与 archive provenance 没有双向绑定。 |
| DR5 可靠性与故障恢复 | 不通过 | 无锁、无原子 sequence、无 staging/崩溃恢复、无 TOCTOU 防护，finalize→check→move 存在竞态。 |
| DR6 数据与环境纯度 | 不通过 | 默认持久化 prompt/output 与外部 locator，且 Windows 特殊路径/链接可把工具变成越界读取或泄密通道。 |
| DR7 残留冗余与复杂度 | 尚可但需约束 | INDEX + manifest 的双层设计合理；run.json/manifest/round 摘要的重复字段必须明确单源和派生关系，避免三份可漂移事实。 |

## Validator 可信度结论

现有测试计划只能证明常规 happy-path 和少数直接篡改能被发现，不能证明 validator 在恶意输入、并发、Windows 文件系统别名或具备归档写权限的攻击者面前可信。完成 SEC-1 至 SEC-6 的契约修订，并落实 TST-1 的对抗矩阵前，不应让 `finalize/check` 成为“归档真实性已证明”的收口门禁；最多可作为结构完整性检查器。
