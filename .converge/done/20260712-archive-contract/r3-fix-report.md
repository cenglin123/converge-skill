# Round 3 Inner-loop Fix Report

## Safety gate

在运行任何 Python 测试前执行：

`rg -n --hidden -S 'os\.kill\s*\(|TerminateProcess|kill\s*\(\s*pid\s*,\s*0' scripts tests refs SKILL.md`

结果无匹配。Windows owner liveness 继续使用 waitable process handle；未重新引入危险 API。

## R3 status

- R3-B1：resolved。capture 入口及每次目标父目录创建后执行 non-reparse safe-tree 验证；workspace containment 在 `lstat/open/read` 前完成。新增父目录 symlink 越界零写入和 workspace-outside 零读取测试。
- R3-B2：resolved。新增 canonical `user-message` owner event；user-decision 的 `source_ref` 必须是先前 user-message event UUID，quote 必须逐字一致；presented degradations 必须等于决定时实际 degradation；terminal-b/c 分别绑定闭合 accepted state。新增正反测试。
- R3-B3：resolved for executable schema。`PROVENANCE_MATRIX` 成为 level/source/reason 单源；所有 scalar 先做 bounded type 校验；failure-before-resolution 禁止用于 succeeded；tool response ref 必须绑定当前 invocation。adapter 文档指向同一矩阵。
- R3-B4：resolved for all current event unions。event type、started/terminal owner 字段、decision、locator、advisory 与 snapshot size 均执行显式类型校验，bool 不再冒充 size；畸形 owner scalar 返回 ArchiveError。新增 dict/list 反例。
- R3-B5：resolved for reported reproduction。journal、parent revision 与 reopen marker 改为 exclusive temp + fsync + atomic replace；reopen 增加 parent-stored/marker-stored durable substate；重试可从 stored parent 继续。dead lock reclaim 在 unlink 前复核 nonce bytes 与 file identity。Round 2 两个 rename/journal 故障测试继续通过；Reviewer 的 `Path.write_bytes` partial-write 注入点已不存在。
- R3-B6：resolved in implementation。INDEX 投影完整 parent chain、artifact locator/capability/hash 与 risks；pre-push 由 CLI 解析真实 base/head range，并用 `git archive <head>` materialize 待推 commit bytes 后 check，不读 working tree；new branch 使用 empty-tree baseline。stale-check 调用 transaction 的共享 journal parser。治理文档中的手工 move 已替换为 reopen/archive。
- R3-B7：partially resolved。fresh 四类反例已固化，Archive suite 增至 38 项；bugfix 状态改为 `fixing`，旧绿测不再表述为已完成。plan §10 的全部组合仍未穷举，ignored docs tracking 仍需 Orchestrator 处理。

## Verification

- 五个最初失败的 Round 3 反例：先确认 5/5 FAIL，再修复后 5/5 PASS。
- `python -B tests/test_archive_convergence.py`：PASS，38 tests in 2.151s。
- `python -B -m unittest discover -s tests -p test_*.py`：PASS，88 tests in 12.185s。
- `git diff --check`：PASS。
- 未 commit。

## Remaining honest boundaries

- 未扩展到 hostile same-writer 防御；lock identity 复核是 cooperative crash recovery，不声称抵抗同权限恶意竞态。
- 未无特权伪造平台不允许创建的 ADS/device/reparse 对象。
- pre-push commit-tree 路径已实现，但本轮未新增真实 remote push 的集成仓库测试；fresh Reviewer 应继续把这一点作为验证重点，而不是根据代码声明直接视为已证明。
- Bugfix 文档仍受 `.gitignore:2 docs/` 影响；Executor 未越过 §12 修改 `.gitignore`，Orchestrator 必须选择项目认可的显式 tracking 方式。
