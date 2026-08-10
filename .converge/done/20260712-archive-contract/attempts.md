# Attempts · 20260712-archive-contract

## Plan convergence

- source: ultraverge_initial
- issues: AC-1..6, UV2-B1..4, SEC-1..6, TST-1
- approach: 收窄 threat model，闭合 invocation/provenance/artifact/schema/transaction 合同，并加入 30 秒审计旅程
- verdict: Accepted by 3/3 initial reviewers after inner loop

## Landing Round 2

- source: converge_loop
- issues: B-1..B-7
- approach: 以越界写、伪 Reviewer、无 reservation、孤儿 evidence、虚假 observed 与事务故障反例驱动实现修复
- verdict: Rejected；测试全绿但 fresh 语义反例仍成立

## Landing Round 3

- source: converge_loop
- issues: R3-B1..R3-B7
- approach: 加固祖先 reparse、user-decision authority、provenance tagged union、exact event schema、durable reopen、commit-tree hook 与完整 INDEX
- verdict: Accepted by final blank-slate OCSR review

## Orchestrator-authorized final delta

- source: orchestrator_self
- authorization: 用户明确要求停止原生子代理并授权 Orchestrator 自行完成剩余修复，再用 OCSR 独立审计
- changes: 删除不可达 dead code；更新 bugfix fixed/验证事实；将 test_budget_gate.py 转 LF
- verdict: Accepted by OCSR same-session delta recheck；88/88 tests pass
