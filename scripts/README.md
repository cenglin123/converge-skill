# scripts/

## orchest.py — 执行层编排（六命令一段式用法）

> 本文件为脚本命令/用法清单的**单源**。SKILL.md 已接线 orchest.py（Orchestrator 主循环总则引用）；
> 本文件承载全部脚本命令/用法/其他脚本清单。任何脚本或文档改写涉及该清单时须**同步维护本文件**，
> 并走常规评审（本文件不在 CONSTITUTION 保护文件清单内，不适用保护文件豁免路径）。
> 设计契约与验收见 KB 仓 plan `docs/plans/active/20260815-converge-exec-orchestration.md`。

单次宿主派发的完整生命周期（LLM 只写 prompt 文件与裁决 verdict，机械步骤全走脚本）：

```bash
# ① 宿主 Spawn 之前：gate reserve → begin-invocation → SCOPE_PRODUCT 骨架
python scripts/orchest.py reserve-round --active-dir <dir> --role outer-reviewer \
    --round 1 --phase review --attempt 1 --prompt-file <已落盘的自足 prompt> \
    --requested-provider <p> --requested-model <m>
# 输出 reservation_id + invocation_id（LLM 全程不经手 invocation_id 的转录）
# begin 失败 → reservation 保持 open，修复后同 rid 重试：
python scripts/orchest.py reserve-round ... --resume-reservation <rid>

# ② 宿主 Spawn（orchest.py 不做这一步）

# ③ 成功返回：
python scripts/orchest.py register-round --active-dir <dir> --reservation-id <rid> \
    --instance-id <sid> [--backend <b>] [--output <path>]   # consumes=none 角色必传 --output

# ③' 失败/取消/弃用：
python scripts/orchest.py cancel-round --active-dir <dir> --reservation-id <rid> \
    --reason-code cancelled-by-host|backend-error|timeout [--pre-execution] [--detail <s>]

# ④ 裁决落账（产物 frontmatter 契约字段自动补齐 + gate ingest-verdict）：
python scripts/orchest.py record-verdict --active-dir <dir> --round <N> \
    --verdict <可执行|阻断需修复|需重新设计> [--severities s1,s2] [--product blind-recheck-N.md]

# ⑤ 收尾一条命令（固定顺序 0→8：拒已归档 → 交叉核对 → round 连续 → 全 settle →
#    孤儿显性化 → 异常恢复 → 终局 decision → stamp → prompt 归位 → archive → check）：
python scripts/orchest.py finish --active-dir <dir> --verdict <终局 verdict> \
    [--done-root <dir>] [--slug <s>]

# ⑥ plan checkpoint 路径清单（git diff-tree 现算，零手抄）：
python scripts/orchest.py checkpoint-paths --commit <sha> [--repo <外部仓库路径>]
```

所有命令支持 `--dry-run`（只打印序列不落盘）。幂等语义：register/cancel 对已终态
reservation 重跑识别后退出 0；finish 每步可安全重跑，decision 已 record 即复用。

错误防线（为什么用脚本而不是手跑 budget_gate / archive_convergence 分步）：
骨架忘写、UUID 手抄漏字符、archive 前忘删 prompt、把未 spawn 的 reservation 写成
succeeded、归档后二次操作等 8 类历史执行错误在此机制层消除——映射表见
`orchest.py` 模块 docstring。

## Loop A（收敛循环）接线示例

SKILL.md 主循环/盲审/Inner Loop 的机械动作全部经 orchest.py（见 SKILL.md §Orchestrator 主循环 总则）：

```bash
# 主循环 reviewer 轮（spawn 前先落盘 prompt 文件，再单命令预约）
python scripts/orchest.py reserve-round --active-dir <dir> --role outer-reviewer \
    --round 1 --phase review --attempt 1 --prompt-file <prompt.md> \
    --requested-provider <p> --requested-model <m>
# → Spawn reviewer → 成功：
python scripts/orchest.py register-round --active-dir <dir> --reservation-id <rid> --instance-id <sid>
# → 失败/取消：
python scripts/orchest.py cancel-round --active-dir <dir> --reservation-id <rid> --reason-code <c>
# verdict 确定后（替代手写 frontmatter + 裸 ingest-verdict）：
python scripts/orchest.py record-verdict --active-dir <dir> --round 1 --verdict 阻断需修复 --severities structural

# executor 修复轮（consumes=none，无骨架，--output 必填）
python scripts/orchest.py reserve-round --active-dir <dir> --role executor \
    --phase repair --attempt 1 --prompt-file <prompt.md>   # executor 无 --round
python scripts/orchest.py register-round --active-dir <dir> --reservation-id <rid> \
    --instance-id <sid> --output attempts.md
# 崩溃窗口（spawn_succeeded-缺-terminal）官方恢复 = 重跑上面 register-round（幂等），禁手工补 terminal

# 盲审轮（--round 为盲审独立序列号；consuming 角色缺 --round 直接被拒——实测教训）
python scripts/orchest.py reserve-round --active-dir <dir> --role blind-reviewer \
    --round 1 --phase review --attempt 1 --prompt-file <blind-prompt.md>
python scripts/orchest.py register-round --active-dir <dir> --reservation-id <rid> --instance-id <sid>
python scripts/orchest.py record-verdict --active-dir <dir> --round 1 \
    --product blind-recheck-1.md --verdict 可执行   # verdict 用 gate 三档；pass/fail/waived 只进 retrospective

# Inner Loop Continue（续命同实例；无 reservation，计数入 max_inner_loops=3）
python scripts/orchest.py reserve-round --active-dir <dir> --continue-of <父rid> \
    --phase inner-review --prompt-file <prompt.md>   # role/round 派生自父轮
python scripts/orchest.py register-round --active-dir <dir> --invocation-id <iid> \
    --instance-id <父实例id>   # continue 入口；实例冲突被拒（续命同实例）

# 收敛归档（必检清单★语义 → retrospective★LLM → finish 机械三段的前者已完成后再跑）
python scripts/orchest.py finish --active-dir <dir> --verdict 可执行
```

落地执行（收敛完成后）**不进**上述循环：spawn 走宿主原生 + instance_id 记 plan frontmatter，仅改动清单核对经 `checkpoint-paths`——映射表见 `refs/orchestrator-guide.md` §落地执行编排。

## converge_loop.py — 可选循环调度器（loop-spec 驱动的机械调度）

converge_loop.py 是收敛循环的**可选调度器**（OPTIONAL scheduler），不替代 SKILL.md 主循环
的语义判定：verdict、修复指令、prompt 内容、retrospective 等★步骤仍由 LLM 按
SKILL.md 主循环承担；本驱动器只做机械组合——以 subprocess 调用 orchest.py 六命令
（记账合同唯一事实源）与 spec 提供的**外部 `ocsr_dispatch` 可执行文件**（经 spec 提供，
非本仓库内置执行体），不重新实现预算/归档/角色语义。设计契约见
`docs/plans/active/20260818-converge-loop-driver.md`。

命令：

- `run --spec <spec>` — 从零驱动 loop spec（先校验、初始化 budget config、写入 journal；暂停以 pause-request.json 边界交接）。
- `resume --spec <spec> [--answer k=v ...]` — 续跑已暂停的 journal，处理 pause 等待的裁决答案。
- `validate --spec <spec>` — 只校验 spec 合法性并列出 phases（不驱动）。
- `status --spec <spec>` — 输出 journal 的 phase_index / paused / aborted / history（JSON）。

loop-spec 驱动派发阶段的机械调度：轮号推导、预约、派发、落账、产物三方对齐、归档均由
驱动器机械执行。spec **禁止**出现轮号字段（`round` / `round_number` / `target_round`），
轮号只能由驱动器从 realized 产物（`round-N.md` 等）推导，防止轮号误用。

**单活约束**：spec 驱动路径与人工主循环**不得并发驱动同一 active 目录**——二者同时写会造成
ledger/budget 双计数风险；同一 active 目录同一时刻只允许一条驱动路径（spec 驱动或人工主循环）。

退出码：`0` 全流程完成；`1` 步骤失败（不可机械恢复或 agent abort）；`2` spec 非法/用法错误；
`10` 暂停待裁决（已写 pause-request.json）；`11` resume 状态不确定（journal 损坏/答案缺失/输入未就位）。

## 其他脚本

- `budget_gate.py` — 预算执行硬化（reserve/settle/ingest-verdict/summary）
- `archive_convergence.py` — Archive Contract v1 CLI（begin/complete/recover/
  record-terminal-decision/stamp/archive/check/reopen）
- `ocsr_spawn_adapter.py` — OCSR 派发的五步原子 Spawn 适配
- `archive_contract/` — Archive Contract v1 可执行单源（model/capture/transaction）
- `converge_loop.py` — 循环级机械调度器（可选，见上节；run/resume/validate/status）
- `l1_gate.py` — L1 信号检测前端：读取 Dynamic Workflow 各 phase 收口 JSON 指标，按阈值判定 pass/warn
- `distill_antipatterns.py` — Antipattern 蒸馏器：从 done/*/retrospective.md 的 Antipattern 巡查表编译 refs/antipatterns.md 的 status/zero_streak（确定性，零 LLM；--write 才落盘）
- `hooks/pre-commit` — 检测治理文档变更，提醒走 ultraverge 流程（CONSTITUTION 第三部保护文件）
- `hooks/pre-push` — 检查 active/ 陈旧项（stale-check）+ 变更的 Archive Contract v1 done 目录（check-push-range）
- `hooks/stale-check.py` — 扫描 .converge/active/ 与 docs/plans/active/ 的 stale 项（CRITICAL/WARNING/NOTE；CONVERGE_STRICT=1 阻断 push）
- `hooks/kimi_pretooluse_shim.py` — 把 kimi-code 宿主 hook 事件桥接到 converge budget_gate（字段归一化后子进程调用）
