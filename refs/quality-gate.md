# 质量门控

> converge 作为 Dynamic Workflows 的质量门控协议。门控不是审批者（不否决不阻断），是**参谋团**——在 phase 交接处插入独立的"方向性审视"，让指挥部的决策在行动前暴露自己看不到的风险点。

## 定位

### 门控 vs 审批

| | 审批（现有对抗验证） | 门控（本协议） |
|---|---|---|
| 审什么 | 士兵报告对不对 | 指挥部方向偏不偏 |
| 输出 | 同意 / 不同意 | 风险点、遗漏假设、矛盾信号 |
| 对流程影响 | 可能重做当前 step | 标记给下一个 phase 参考 |
| 启动方式 | 脚本预设，每轮固定 | 信号驱动，按需 |

门控不替指挥官做决定——它出发现，指挥官决策。编排器始终保留最终决策权，但必须记录决策理由。

### 适用范围

- **激活**：converge 被嵌入多阶段 Dynamic Workflows pipeline 时
- **独立单层 converge**：L1 不适用（无 Worker 或阶段可度量）；L2 可手动触发——当用户显式请求关卡式审查时

### converge ↔ Dynamic Workflows 接口

| 层 | 提供 |
|---|---|
| converge | L1 信号模式 + 默认阈值、L2 Reviewer 生成协议、gate_findings 格式、预算框架 |
| Dynamic Workflows | L1 指标值（Worker 一致性/测试通过率/Token 偏差）、阶段边界、当前预算消耗 |

---

## 两级门控

### L1 轻量级（信号检测，零 LLM 成本）

独立 Python 脚本（~50 行），接收 DW 提供的 JSON 指标，输出判定。编排器通过 shell 调用。

**输入**（DW 在每次 phase 收口后传入）：

```json
{
  "phase": "phase-2",
  "worker_consistency": {
    "overlap_ratio": 0.72,
    "variance_threshold_exceeded": false
  },
  "test_pass_rate": {
    "current": 0.94,
    "previous": 0.97
  },
  "token_budget": {
    "phase_spent": 120000,
    "phase_expected": 100000,
    "total_spent_pct": 0.45
  }
}
```

**阈值**（pilot，待校准）：

| 信号 | 阈值 | 说明 |
|------|------|------|
| Worker 分类重叠率 | < 0.6 → warn | Worker 之间对同一问题的分类分歧过大 |
| 测试通过率下降 | ≥ 20% vs 上一阶段 → warn | 新改动大面积破坏了已有功能 |
| Token 超出预算 | 阶段消耗超出预期 30% → warn | 本阶段复杂度或效率偏离计划 |

**输出**：`pass` / `warn`。warn 时附带异常信号标签（如 `test_decline`、`budget_overrun`）。

**触发**：硬性设定——每 N 个 phase（`gate_l1_interval`）强制运行。不跳过。

### L2 重量级（单轮对抗审查，按需）

**做什么**：Spawn 独立 Reviewer，按 converge 标准做一轮深度审查。审查对象是当前 phase 的中间产物 + 收口模型的综合判断。不跑完整多轮 converge——太重。跑一轮快审。

**触发条件**（优先级递降）：

1. **硬性设定**：`gate_l2_mode = always` 时，每次 phase 切换
2. **信号触发**（推荐默认）：`gate_l2_mode = signal` 时，L1 输出 `warn` 后自动触发
3. **模型自判**：`gate_l2_mode = adaptive` 时，收口模型自评风险分 ≥ 阈值（**未实现，pilot 存根，待校准后启用**）

**输出**：`gate_findings` 格式（非 `blocking_issues`）：

```yaml
gate_findings:
  - id: 1
    severity: critical_gap  # info | risk | critical_gap
    finding: |
      <发现的具体风险、遗漏假设或矛盾信号>
    evidence: "<引用 phase 产物中的具体内容>"
    suggestion: "<建议的处理方向，非强制>"
```

**编排器决策路径**：

```
编排器读 gate_findings →
  若 severity = info → 记录到 state，不阻断（可选在后续 phase 注意）
  若 severity = risk → 记录 + 向用户发出警报 + 可视情况调减后续 phase 预算
  若 severity = critical_gap → 记录 + 触发完整 L2 converge 审查（走标准 Round 0-1+ 流程）
编排器始终保留最终决策权——但必须在 _orchestrator-state.md 中记录决策理由
```

**门控不跑的**：不触发 Executor、不跑多轮迭代、不走合同谈判、不写 round-N.md。门控产物写在 `.converge/gate/<slug>/` 下，与主 converge 循环的 `.converge/active/` 隔离。

---

## 预算统筹

```
门控预算池 = 总预算 × gate_max_token_share（默认 15%）
每次 L2 前检查：
  若 budget.remaining() < 门控预算池 × 30%
    → 降级：L2 → L1（不 spawn Reviewer，只跑信号检测）
门控消耗不计入 converge 的 max_outer_loops 预算
```

Dynamic Workflows 脚本骨架：

```js
const GATE_BUDGET = budget.total * 0.15;

// 在 phase 切换时：
if (gate_l2_mode === 'signal') {
  const l1Result = await runL1Script(phaseMetrics);
  if (l1Result === 'warn') {
    if (budget.remaining() > GATE_BUDGET * 0.3) {
      const findings = await agent(
        `独立审查本阶段产物……（自足 prompt）`,
        { schema: GATE_FINDINGS_SCHEMA }
      );
      // 编排器决策路径处理 findings
    } else {
      // 降级：预算不足，跳过 L2
      log(`门控预算不足，L2 跳过。剩余: ${budget.remaining()}`);
    }
  }
}
```

---

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `gate_l1_interval` | 1 | L1 每 N 个 phase 触发 |
| `gate_l2_mode` | `signal` | `always` / `signal` / `adaptive`（`adaptive` pilot 存根，待校准） |
| `gate_l2_signal_threshold` | `warn` | 信号触发条件 |
| `gate_max_token_share` | 0.15 | 门控 token 预算占总预算比例上限 |

## 产物目录

```
.converge/
├── gate/<slug>/              # 门控产物（与 active/ 隔离）
│   └── gate-findings.md      # L2 Reviewer gate_findings 汇总
├── active/<slug>/             # 主 converge 循环产物
└── done/<slug>/               # 已完成
```
