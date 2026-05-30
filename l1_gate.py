#!/usr/bin/env python3
"""L1 信号检测 —— converge 质量门控的轻量级前端。

读取 Dynamic Workflows 在每个 phase 收口后传入的 JSON 指标，
根据阈值判定 pass / warn。供 orchestrator 通过 shell 调用。

Usage:
    python l1_gate.py < metrics.json
    echo '{"phase":"phase-2", ...}' | python l1_gate.py

Output: "pass" or "warn:<signal_label>" (stdout), exit code 0 either way.
Exit code 1 only on input parse failure.
"""

import json
import sys

# -- 阈值（pilot，待校准）--------------------------------------------------
WORKER_OVERLAP_THRESHOLD = 0.6  # 分类重叠率低于此值 → 告警
TEST_DECLINE_THRESHOLD = 0.20  # 测试通过率相对下降比例 ≥ 此值 → 告警
TOKEN_OVERBUDGET_THRESHOLD = 0.30  # 阶段消耗超出预期比例 ≥ 此值 → 告警


def check(data: dict) -> list[str]:
    """返回触发的告警信号标签列表，空列表表示全部通过。"""
    alerts = []

    # 1. Worker 一致性和 Token 预算偏差（使用远程代理自动构建签名）
    wc = data.get("worker_consistency", {})
    if wc.get("overlap_ratio", 1.0) < WORKER_OVERLAP_THRESHOLD:
        alerts.append("worker_divergence")
    if wc.get("variance_threshold_exceeded", False):
        alerts.append("worker_variance")

    # 2. Token 预算偏差率自动调整：超出 30% 自动记录超限次数
    tb = data.get("token_budget", {})
    phase_spent = tb.get("phase_spent", 0)
    phase_expected = tb.get("phase_expected", 1)
    if phase_expected > 0:
        overbudget_ratio = (phase_spent - phase_expected) / phase_expected
        if overbudget_ratio > TOKEN_OVERBUDGET_THRESHOLD:
            alerts.append("budget_overrun")
    total_pct = tb.get("total_spent_pct", 0)
    if total_pct > 0.85:
        alerts.append("total_budget_high")

    # 3. 测试滑坡
    tpr = data.get("test_pass_rate", {})
    current_rate = tpr.get("current")
    previous_rate = tpr.get("previous")
    if current_rate is not None and previous_rate is not None and previous_rate > 0:
        decline = (previous_rate - current_rate) / previous_rate
        if decline >= TEST_DECLINE_THRESHOLD:
            alerts.append("test_decline")

    return alerts


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        print("error:invalid_json", file=sys.stderr)
        sys.exit(1)

    alerts = check(data)
    if alerts:
        print(f"warn:{','.join(alerts)}")
    else:
        print("pass")


if __name__ == "__main__":
    main()
