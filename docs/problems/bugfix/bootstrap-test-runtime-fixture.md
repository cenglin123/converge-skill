---
id: bugfix-bootstrap-test-runtime-fixture
type: bugfix
title: Bootstrap 回归测试依赖已归档的运行时目录
status: fixed
severity: medium
scope:
  - test
  - archive
modules:
  - archive-contract
tags:
  - bootstrap
  - fixture
  - clean-clone
  - regression
symptoms:
  - 完整测试集在归档运行目录清理后出现 FileNotFoundError
error_signatures:
  - "FileNotFoundError: .converge/active/20260712-archive-contract/gate-ledger.jsonl"
related_files:
  - tests/test_archive_convergence.py
verification:
  level: automated
  kind: regression-test
  path: tests/test_archive_convergence.py
  command: python -B -m unittest discover -s tests -p 'test_*.py'
created_at: 2026-07-12
updated_at: 2026-07-12
---

# Bootstrap 回归测试依赖已归档的运行时目录

## 现在的行为

`test_plan_time_bootstrap_fixture_imports_raw_evidence_without_root_clutter` 从 Git 忽略的 `.converge/active/20260712-archive-contract` 复制夹具。该运行完成并归档后目录不再存在，完整测试集因此稳定报 `FileNotFoundError`；干净克隆同样不具备这个目录。

## 预期的行为

回归测试应只依赖版本控制中的代码和测试内构造的数据，在运行时目录为空、已归档或干净克隆环境中都能验证 legacy bootstrap 的证据导入和根目录清理行为。

## 复现方式

确保 `.converge/active/20260712-archive-contract` 不存在，然后运行 `python -B -m unittest discover -s tests -p 'test_*.py'`。旧测试在复制 `gate-ledger.jsonl` 时失败，其他 87 项测试通过。

## 原因是什么

测试把一次真实 convergence 运行目录误当成稳定 fixture。该目录属于被忽略的瞬态状态，会在 archive 后移动或清理，不受 Git 历史保证。

## 怎么修复的

测试现在在临时目录中构造最小、确定性的 ledger、固定根文件、reviewer/executor 原始输出和 reference artifact，再调用同一个 `_bootstrap_import` 入口。保留了原有断言，并移除了不再使用的 `shutil` import。

## 验证结果

定向 bootstrap 回归测试通过。最终完整测试命令再次运行，88 项全部通过。

## 风险和后续

自包含夹具覆盖两个 reservation、同一 reviewer 的 inner continuation、executor 输出和 reference artifact，未复制原运行目录的全部文本体量；其目标是验证绑定、导入和清理机制，不验证历史报告内容。
