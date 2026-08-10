---
id: bugfix-pre-push-subcommand-parsing
type: bugfix
title: Windows 推送被归档检查子命令解析错误阻断
status: fixed
severity: high
scope:
  - workflow
  - git-hook
modules:
  - archive-contract
  - hooks
tags:
  - pre-push
  - argparse
  - windows
  - regression
symptoms:
  - Git push 在归档检查阶段失败
error_signatures:
  - "archive_convergence.py: error: argument command: invalid choice"
related_files:
  - scripts/hooks/pre-push
  - tests/test_archive_convergence.py
verification:
  level: automated
  kind: regression-test
  path: tests/test_archive_convergence.py
  command: python -B -m unittest discover -s tests -p 'test_archive_convergence.py' -k test_b6_pre_push_is_nul_safe_and_checks_any_done_change
created_at: 2026-07-12
updated_at: 2026-07-12
---

# Windows 推送被归档检查子命令解析错误阻断

## 现在的行为

Git 推送触发 `scripts/hooks/pre-push` 后，归档检查命令立即退出，提示仓库根路径不是合法子命令。任何包含该 hook 的推送都会被阻断，归档内容是否有效不会被检查。

## 预期的行为

pre-push hook 应以规范子命令 `check-push-range` 调用归档 CLI，检查待推送范围内所有变更的 Archive Contract v1 归档；归档有效或没有相关变更时允许继续推送。

## 复现方式

在安装该 hook 的仓库执行 `git push`。旧 hook 调用 `archive_convergence.py --check-push-range <repo> <base> <head>`，argparse 把前导双横线参数当成可选项处理，随后把 `<repo>` 解析为子命令并报 `invalid choice`。该问题稳定复现。

## 原因是什么

CLI 使用 argparse subparser，规范入口是位置参数形式的 `check-push-range`。虽然 parser 声明了一个以 `--` 开头的 alias，但 argparse 在选择 subparser 之前会按可选参数语义处理它，因此 hook 中的 alias 实际不可调用。原测试只断言错误字符串存在，没有执行或约束可解析的调用形式。

## 怎么修复的

把 hook 的三个调用点统一改为规范子命令 `check-push-range`。回归测试现在断言三个调用点都使用规范形式，并明确禁止重新出现 `--check-push-range` 调用。没有绕过或放宽 pre-push 门禁。

## 验证结果

定向回归命令运行 1 项测试并通过。另使用 Git for Windows 自带的 `sh.exe` 无 stdin 直接执行 hook，stale 检查与 Archive Contract v1 变更检查均正常完成，退出码为 0。

## 风险和后续

本次只修复 pre-push 的调用形式，没有移除 CLI 中不可用的双横线 alias，以控制发布阻断修复的改动范围。后续如清理兼容入口，应单独评估 `check-done-changes` 的相同 alias 设计并更新相关文档。
