# scripts/

## orchest.py — 执行层编排（六命令一段式用法）

> 过渡可发现性入口：SKILL.md 接线（在 Orchestrator 主循环一节引用 orchest.py）留后续
> plan；接线前经本文件找到 orchest.py。设计契约与验收见 KB 仓 plan
> `docs/plans/active/20260815-converge-exec-orchestration.md`。

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

## 其他脚本

- `budget_gate.py` — 预算执行硬化（reserve/settle/ingest-verdict/summary）
- `archive_convergence.py` — Archive Contract v1 CLI（begin/complete/recover/
  record-terminal-decision/stamp/archive/check/reopen）
- `ocsr_spawn_adapter.py` — OCSR 派发的五步原子 Spawn 适配
- `archive_contract/` — Archive Contract v1 可执行单源（model/capture/transaction）
