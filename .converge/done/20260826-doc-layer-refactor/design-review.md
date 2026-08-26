# Design Review — 20260826-doc-layer-refactor (ultraverge mandatory, advisory)

模式:咨询式,不阻断。维度:DR1-DR7。

## 维度结论

| 维度 | 状态 | 要点 |
|---|---|---|
| DR1 maintainability | clean | 单源化降低维护成本;指针层级 1-2 跳可接受 |
| DR2 consistency | concerns_found | SKILL.md 内部残留旧数值(Ultraverge 路径节 vs 配置表/DEFAULTS)——同文件自相矛盾 |
| DR3 completeness | concerns_found | max_blind_rechecks 的 ultraverge 覆盖(2/total 62)被误归为调优史;relay 字段中英文名五组映射未点名 |
| DR4 boundary_clarity | concerns_found | converge_loop 依赖仓库外 ocsr_dispatch 后端未点明;state-schema 承纳布局约定属职责扩张(已自认) |
| DR5 residue_and_redundancy | concerns_found | scripts/README 头部过时过渡说明未修订;done→active→re-archive 三处存在;state-schema relay-ledger 历史注驻留 |
| DR6 portability | clean | — |
| DR7 scalability | concerns_found | 受保护文件委托不受保护单源(scripts/README)的结构张力;两条驱动路径需显式单活约束 |

## Highlights(3,advisory;已按用户授权并入 plan)

1. 同文件旧数值矛盾:SKILL.md Ultraverge 路径节写 真实默认 1 / 42 重算 44,与配置表+budget_gate DEFAULTS(3/62)矛盾。→ 并入:验收新增 SKILL.md 全文残留数值一致性核对,旧数对齐 DEFAULTS/公式单源。
2. 模式相关值误归调优史:max_blind_rechecks 在 ultraverge 下被 init config 覆盖为 2、total 上限重算 62——行为事实,不是 git 历史可承载的调优注。→ 并入:2b 区分默认值单源(DEFAULTS)与模式覆盖行为注(保留 SKILL.md);验收 grep 增 max_blind_rechecks|42|44。
3. 不受保护的命令单源:scripts/README 成为命令/用法单源却在宪法保护清单外,且头部残留已过时过渡说明。→ 并入:第 1 刀修订 scripts/README 头注(过渡→已接线+单源声明);记录(不实施)治理建议:脚本命令契约保护地位留待后续修宪裁决。

## 其余边界注(并入 plan)

- converge_loop.py 的 dispatch 依赖 spec 提供的 ocsr_dispatch 路径(仓库外后端)。
- relay 字段等价映射须覆盖中英文名五组映射,不止 timestamp。
- converge_loop 与手工主循环须写明单活约束:不得同时驱动同一 active 目录(ledger/预算双计数风险)。

## 处置

全部 advisory;highlights 1-3 与边界注已并入 plan(executor attempt 3),不阻断收敛。