# Reviewer 3 Inner-loop 验收 · 第 1 轮

```yaml
round: ultraverge-initial-3-inner-1
reviewed_artifacts:
  - plan.md
  - plan-amendment-report.md
threat_model_applied: |
  非 hostile-same-writer：v1 只保证归档时点的内部一致性、结构完整性和声明 provenance 可追溯性；不要求防御能够以同等权限整体改写归档、sidecar、ledger 与 Git 历史的攻击者，不要求外部签名服务或不可变信任锚。
verdict: 可执行
blocking_issues: []
issue_rechecks:
  - id: SEC-1
    status: Accepted
    evidence: |
      §1 已明确 hash 不是来源认证，将能力收窄为内部一致性与声明 provenance，并明确 configured/inherited 不等于实际模型已证明；§4 说明 manifest 不自哈希及同权限整体改写残余边界；§5 用 requested/resolved/evidence_level 分级。该修订在指定威胁模型内消除了原先的概念性过度承诺，无需外部签名服务。
  - id: SEC-2
    status: Accepted
    evidence: |
      §6 已覆盖 canonical roots、same-file/containment、UNC、extended-length path、ADS、设备名、尾随点/空格、symlink/junction/reparse point、hardlink、非普通文件、句柄读取后的 identity/size/mtime/type 复核、随机 staging、exclusive create 与原子 replace；§10.6–10.7 给出相应对抗测试。
  - id: SEC-3
    status: Accepted
    evidence: |
      §5 将 sequence 改为 CLI 在锁内分配的全局连续编号；§8 定义按 slug 的单写者锁、owner-dead 恢复、同卷 staging、journal、post-move check、原子回滚和幂等恢复；§10.8 覆盖 sequence 竞争、并发 archive、崩溃与恢复。
  - id: SEC-4
    status: Accepted
    evidence: |
      §5 要求 archive/check 复用同一个严格 ledger validator，并建立 reservation、reserve/settle event、Spawn invocation、role/phase/round/status/instance/receipt 的双向一致与全覆盖；孤儿、重复和状态冲突均 fail closed。计划也诚实保留 auditable-only 与 ledger 不抗同权限整体改写的边界，符合本轮指定威胁模型。
  - id: SEC-5
    status: Accepted
    evidence: |
      §2 已将 metadata-only 设为默认，区分 redacted/exact 的能力声明和显式 opt-in；默认拒绝 secret、设备/管道及 workspace 外内容，外部内容要求本次新鲜授权和脱敏 locator，并设置单文件/总量上限与权限降级披露。§6 默认离线、不回读外部源，补齐了任意读取与长期持久化边界。
  - id: SEC-6
    status: Accepted
    evidence: |
      §3 使用根级显式 allowlist、大小写无关唯一键和 Unicode 碰撞拒绝；§4 精确闭合 canonical、invocation sidecar、prompt/output、artifact metadata/snapshot，并拒绝多余、缺失和碰撞路径；JSON 拒绝重复 key/NaN/未知非法组合，INDEX 从 manifest 重建并逐字节比较，scan 不跟随链接。
  - id: TST-1
    status: Accepted
    evidence: |
      §10 已扩为 12 组测试矩阵，覆盖 lifecycle、ledger 双向绑定、provenance 合法矩阵、逐类及联合篡改、证据模式与秘密拒绝、TOCTOU/链接/ADS/设备、Windows 路径等价、并发/锁/崩溃恢复、五态 schema、移动后链接、bootstrap fixture 和固定种子 property-style 不变量；同时明确 hostile same-writer 联合改写不可检测，不把错误安全主张写成测试目标。
suggestion_issues:
  - description: |
      在 `refs/state-schema.md` 落地时明确 reopen 后旧 manifest/INDEX 的 revision-history 具体相对目录及其如何进入新 manifest 闭包；§3 根级 allowlist 只允许 current `manifest.json`/`INDEX.md`，因此历史副本不应重新落在根级。
  - description: |
      将 slug 锁文件放在不会随 active→done/reopen 移动的稳定锁命名空间，并在 schema/guide 中写明；否则实现若把锁放进被移动目录，可能产生两个锁域。计划已经要求单写者锁，此项是实现约束澄清。
  - description: |
      为 redacted/exact 的“新鲜显式授权”定义可审计字段（授权来源、时间、scope/evidence item），并确保它进入 manifest；不要只依赖调用者记忆或 CLI flag。
  - description: |
      Windows CI 应把能在普通权限下创建的 junction/symlink 与不能创建的对象分开报告；只有平台/权限确实不支持的 fixture 可以 skip，containment 和不跟随链接的核心断言不得被整组 skip。
antipattern_observations: []
contract_amendment_required: false
```

## 验收结论

SEC-1 至 SEC-6、TST-1 均已针对原问题完成实质修订，且 plan-amendment-report 的 resolution map 与 `plan.md` 实际条款一致。原 blocking 全部解除。

最终 verdict：**可执行**。上述四项 suggestion 属落地时的 schema/实现精化，不阻断计划进入执行阶段；landing Reviewer 仍需以测试实际全绿、核心安全测试未跳过和 validator 代码行为为准独立复验。
