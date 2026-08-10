---
type: landing-report
status: completed
object_slug: 20260712-archive-contract
generated_at: 2026-07-12T16:30:00+08:00
executor_role: plan-execution
contract: converge-archive-v1
---

# Archive Contract v1 落地报告

## 结果

已按 `plan.md` §12 落地 Archive Contract v1，未修改 `.gitattributes`，未 commit。实现保持单一 `scripts/archive_convergence.py` CLI façade，并以 `model/capture/transaction/presentation` 四模块承载可执行 schema、append-only 采集、归档事务和只读展示。

## 已修改文件

- `SKILL.md`
- `refs/state-schema.md`
- `refs/orchestrator-guide.md`
- `refs/framework-adapters.md`
- `scripts/archive_convergence.py`
- `scripts/archive_contract/__init__.py`
- `scripts/archive_contract/model.py`
- `scripts/archive_contract/capture.py`
- `scripts/archive_contract/transaction.py`
- `scripts/archive_contract/presentation.py`
- `tests/test_archive_convergence.py`
- `docs/problems/bugfix/convergence-archive-auditability.md`
- `scripts/hooks/stale-check.py`
- `scripts/hooks/pre-push`

本报告位于计划指定的过程报告路径。bugfix 文档已创建，但仓库现有 `.gitignore` 的 `docs/` 规则会忽略它；本次未越权修改 `.gitignore`，后续纳入 Git 时需要显式 `git add -f docs/problems/bugfix/convergence-archive-auditability.md`。

## 合同覆盖

- 事件以 exclusive-create JSON 文件追加，Spawn/Continue 使用 started/terminal 两事件生命周期，全局 sequence 连续；失败恢复只追加 terminal。
- manifest 从 events、canonical records、严格 budget ledger、evidence bytes 与 revision manifest 重投影；INDEX 只从 manifest 确定性生成。
- terminal decision 为 reviewer-verdict/user-decision 闭合联合，design review 仅 advisory；最终 round 与 retrospective 使用同一 decision id/value marker。
- requested/resolved provenance 分离，configured/inherited/unavailable 不提升为 observed；INDEX 展示 degradation。
- artifact 支持 metadata-only/redacted/exact，校验原始字节 hash/size、独立 redacted hash、workspace/external locator 联合、TOCTOU、hardlink、symlink/reparse、稀疏/特殊文件和大小上限。
- check/scan 实现 missing/malformed/unsupported/invalid/valid 五态；legacy 只读，不自动迁移。
- archive 使用同卷安全 staging、排他锁、journal、预提交 check、原子 rename、最终路径 post-check 与回滚；reopen 保存前 revision manifest 并从历史 sequence 继续。
- plan-time active fixture 原字节复制后的 bootstrap import 通过：raw `uv-init-*`、plan amendment 和 reference material 进入 evidence，根级仅保留 canonical allowlist，不被当作 clutter。
- stale-check 识别事务 journal；pre-push 对 push 中新建/变更的 v1 done manifest 运行只读 check。

## 验证

- `python -m unittest discover -s tests -p 'test_*.py'`：67 tests，全部通过。
- Archive CLI E2E：archive → done、整体改名后 check、内容篡改失败、reopen → r2 → 再 archive，全部通过。
- bootstrap fixture：导入成功；回归测试断言 raw evidence 已移出根目录。
- Windows 对抗子集：hardlink 与 symlink/reparse fixture 均成功创建并被拒绝，无平台 skip。
- Python in-memory compile：12 个 Python 文件通过。
- frontmatter：`SKILL.md` 与 bugfix 文档通过。
- UTF-8 无 BOM/LF：§12 全部文本目标通过。
- `git diff --check`：通过。
- 既有 `tests/test_budget_gate.py` 包含在全量 67 tests 中并通过。

## 能力降级与残余风险

- 默认 evidence mode 是 `metadata-only`，能力仅为 `identity-only`；redacted 仅为 `redacted-copy`，不得称 exact。
- Windows 标准库无法证明 ACL 机密性，manifest/INDEX 记录 `permissions:acl-confidentiality-not-verified`，不声称归档内容已由 ACL 保密。
- receipt 或 resolved model 不可得时保留 unavailable/configured/inherited 和 closed reason code，不声称实际模型已证明。
- legacy done 无 manifest 时只报告 `legacy-unverifiable`；不会自动改写。
- SHA-256 只支持归档时点内部一致性与结构完整性，不认证来源，也不能对抗拥有同等写权限者整体重写归档、events、ledger、manifest 和 Git 历史。
