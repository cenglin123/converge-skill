---
type: retrospective
object_slug: 20260712-archive-contract
generated_at: 2026-07-12T14:05:00+08:00
---

# Retrospective · 20260712-archive-contract

## 1. 结束模式

Ultraverge 收敛并落地。最终 blank-slate OCSR Reviewer 给出“可执行”、零 blocking；同 session delta recheck 再次确认。

## 2. 阻断轨迹

计划初审 17 → plan inner loop 2 → 0；landing R2=7 → R3=7（更深反例）→ OCSR final=0。轨迹非单调，但后续问题均有可复现反例与回归测试。

## 3. Antipattern 巡查

| Round | 类型 | 对象 | 触发结果 |
|-------|------|------|----------|
| landing | report_hallucination | 全绿测试声明 | 触发；fresh Reviewer 证明测试未覆盖真实安全缺口 |
| R2 | minimum_patch | transaction/path fixes | 触发；代表性故障点修复未闭合整个状态机 |
| R3 | environment_lock-in | Windows owner liveness | 触发；Unix `os.kill(pid, 0)` 语义误用于 Windows，造成执行通道异常退出 |

## 4. Executor 路径依赖评估

多轮 Executor 逐步补丁曾导致“测试全绿但 fresh 反例仍成立”。最终通过 authority graph、tagged union、owner allowlist、durable journal 和审计旅程统一上溯，避免只修单点。

## 5. Reviewer 分歧

初始 Reviewer 对严重度存在差异但方向一致。landing Reviewer 与 Executor 自报告明显分歧，机械反例支持 Reviewer。最终 OCSR MiMo Reviewer 独立复跑 88 项测试并给出零阻断。

## 6. 降级影响评估

- 原生 Codex 子代理继承高档主模型，消耗用户 usage 过快；用户为此使用了一次配额重置。后半程停止所有原生 agent，改为 Orchestrator 直接修复 + 单个 OCSR Reviewer。
- 一次原生 Executor 在用户消息切入后实例消失，reservation 记 `spawn_failed`，落盘半成品由新 Executor 接管。
- `os.kill(pid, 0)` 在 Windows 导致三次测试执行通道异常退出。修复后静态门禁与隔离测试确认危险调用消失。
- Orchestrator 最终直接修改 3 个低风险项，属于用户明确授权的 `orchestrator_self`；通过 OCSR Continue 独立验收补偿角色隔离下降。
- budget gate 为 auditable-only，不是宿主级 enforced。

## 7. 设计审查决策

用户确认采纳全部三项 highlights：单 CLI façade + 四个内部职责模块；字段级 ownership/projection matrix；30 秒 schema-naive 审计旅程。

## 8. 建议处置

- OCSR S1 dead code：已采纳。
- OCSR S2 CRLF：已采纳。
- privileged Windows ADS/device/reparse 实物穷举：延后，作为 capability degradation 明示，不夸大验证范围。
- 当前自举收敛在 v1 invocation capture 落地前已启动，无法诚实补造完整 provenance；按 legacy bootstrap 归档，不宣称 v1-valid。未来收敛必须使用新 archive 命令。

## 9. 验证与成本

- Archive Contract: 38/38；全量: 88/88；`git diff --check`: pass。
- OCSR fresh session: `ses_0ab02dc84ffeyCR8VVZ31P2gRe`，MiMo V2.5 Pro，约 153 秒；一次 Continue 约 82 秒。
- OCSR JSON 中可见的逐 step 成本字段合计约 USD 0.016；输出没有提供可靠的单次聚合总价，因此只作近似，不消耗 Codex 原生子代理高档模型配额。
- 原生 agent 精确 token 未提供；其 usage 消耗过高是本次流程主要失误。

## 10. Blind Recheck

```yaml
blind_recheck:
  status: pass
  traces_reported: 0
  rounds_used: 1
  findings_count: 0
  escalated_to_main_loop: false
  backend: ocsr-opencode-run
  model: xiaomi/mimo-v2.5-pro
```

## 11. Rule Activity

| rule | triggered | status |
|------|-----------|--------|
| boundary_guard | true | disclosed-and-compensated |
| reviewer_boundary_audit | true | OCSR recheck pass |
| intent_drift_check | false | active |
| design_review_trigger | true | completed |
| blind_recheck | true | pass |
| budget_gate | true | auditable-only |
