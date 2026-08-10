---
id: bugfix-convergence-archive-auditability
type: bugfix
title: Converge 归档缺少可验证审计闭包
status: fixed
severity: high
scope:
  - workflow
  - archive
modules:
  - archive-contract
  - hooks
tags:
  - archive
  - auditability
  - provenance
  - append-only
symptoms:
  - done 目录文件平铺且最终结论需要手工搜索
  - 无法机械区分 legacy、损坏和不支持版本
  - 模型与 artifact 证据能力被过度表述
error_signatures:
  - legacy-unverifiable
  - manifest-projection-mismatch
related_files:
  - scripts/archive_convergence.py
  - scripts/archive_contract/model.py
  - tests/test_archive_convergence.py
verification:
  level: automated
  kind: regression-test
  path: tests/test_archive_convergence.py
  command: python -B -m unittest discover -s tests -p 'test_*.py'
created_at: 2026-07-12
updated_at: 2026-07-12
---

# Converge 归档缺少可验证审计闭包

## 现在的行为

旧归档把 prompt、reviewer 输出、round 与报告平铺在根目录，没有 manifest、确定性 INDEX 或事件生命周期。审计者需跨文件搜索最终结论，文件被删改、增加或路径失效时也没有统一诊断。

## 预期的行为

新归档应从 append-only owner events 与 canonical records 投影冻结 manifest，再派生 INDEX；check 能识别五种 schema 状态并验证树、hash、ledger、invocation、decision 与 revision 闭包。旧归档保持只读。

## 复现方式

对无 `manifest.json` 的旧 done 目录运行 `archive_convergence.py check`，旧实现不存在统一入口；人工查看目录也无法在 30 秒审计路径中确定 final decision、degradation 和 next reads。

## 原因是什么

历史流程把“写 retrospective、移动目录”当完成门禁，但未定义事实 owner、投影规则、schema dispatch、原子事务与证据能力降级；同一信息可能存在于多个文件且没有冲突规则。

## 怎么修复的

新增单 CLI façade 和 model/capture/transaction/presentation 四模块。invocation、artifact、terminal decision 与 design-review completion 以 exclusive-create event 追加；archive 在同卷 staging 完成严格检查后原子提交，reopen 保存旧 manifest revision。archive/reopen 在第一步破坏性移动前写 journal，重试会恢复到唯一 authoritative 副本。Windows 锁 owner 探测使用 waitable process handle，不使用可能终止目标进程的 signal-zero API。INDEX 只由 manifest 生成，hooks 对 journal 和任意变更的 v1 done 目录做 NUL-safe 只读检查。

## 验证结果

最终实际执行 `python -B -m unittest discover -s tests -p 'test_*.py'`，88 项测试全部通过；其中 Archive Contract 专项 38 项，覆盖路径越界零副作用、授权先于读取、Spawn/Continue/ledger 闭包、Reviewer 与用户终止权限、模型 provenance、孤儿 evidence、并发 terminal、archive/reopen 故障恢复、稳定诊断与 hook 路径处理。静态门禁确认实现中不存在 `os.kill(pid, 0)`、`TerminateProcess` 或等价破坏性存活探测，`git diff --check` 通过。

随后使用单个 fresh OCSR Reviewer（`xiaomi/mimo-v2.5-pro`）独立读取规范、实现、测试和文档并复跑 88 项测试，结论为“可执行”、零 blocking。平台权限不允许创建的 Windows 特殊对象仍按 capability degradation 处理，不把未执行的实物测试写成已验证。

## 风险和后续

SHA-256 只验证归档内部一致性，不认证来源；拥有同等写权限的攻击者可整体重写归档、ledger、manifest 和 Git 历史。Windows 无法在当前权限创建的 reparse 对抗对象必须显式 skip，不得将其写成已验证。legacy 只读且不可自动升级。
