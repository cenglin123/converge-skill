# Plan · dogfood — ocsr_spawn_adapter usage doc

> Phase 3 end-to-end dogfood target. Slug: `20260725-dogfood-adapter-usage`.
> Purpose: prove the wired Spawn chain (adapter → archive Contract v1 + budget_gate)
> can drive a real small converge that passes `archive` (valid) + `check` (valid-v1).

## 收敛对象

`docs/dogfood/ocsr-adapter-usage.md` —— 一个面向使用者的简短文档（≤200 行），
说明 `scripts/ocsr_spawn_adapter.py` 是什么、典型工作流、与 converge 主循环的关系。

## 目标

- 文档覆盖：用途、CLI 接口、典型调用顺序（reserve→begin→dispatch→complete→settle）、
  provenance 选择（configured + cli_argument + backend-does-not-expose）的诚实降级、
  失败路径（recover-invocation + settle failed）、已知限制。
- 读者：converge 用户（不熟悉 ocsr 内部）。
- 风格：简洁，命令示例可直接复制；引用权威源文件路径。

## 验收（reviewer 标准）

1. 所有 CLI 参数在文档中均有示例或说明（与 `scripts/ocsr_spawn_adapter.py` 的 argparse 一致）。
2. 调用顺序与 design.md §3.2 一致（reserve → begin → dispatch → complete → settle）。
3. provenance 选择与 PROVENANCE_MATRIX 兼容（不出现 host-reported 误用）。
4. 失败路径明确（recover-invocation + settle failed/cancelled + pre_execution 语义）。
5. 不夸大能力（不声称 ocsr 暴露 resolved model；不声称 enforce tier）。

## 非目标

- 不重复 design.md 的源码证据链（指向即可）。
- 不替代 ocsr SKILL.md 或 converge refs/framework-adapters.md。

## 流程

1. Round 1：reviewer 审 stub（几乎空）→ verdict 阻断（必然）→ executor 写完整内容。
2. Round 2：reviewer 审完整版 → verdict 可执行 → 收敛。
3. record-terminal-decision + archive + check。
