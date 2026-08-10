---
type: convergence-contract
object_slug: 20260601-converge-three-layer-separation
generated_at: 2026-06-01T12:00:00
rubric_dimensions: Correctness,Completeness,Consistency
---

## 验收断言

| # | 交付物 | 断言 | 验证方式 |
|---|--------|------|----------|
| 1 | `refs/antipatterns.md` | 包含 10 个具名反模式（executor×4 / design×4 / orchestrator×2），全 `status: active`，id 与 reviewer-prompt.md 枚举逐字一致 | text_review |
| 2 | `refs/antipatterns.md` | YAML frontmatter 含 dormant_threshold / archive_threshold / new_prefix_window / new_prefix_promote_threshold / last_distilled_at | text_review |
| 3 | `SKILL.md` | Red Flags 重组为"宪法级约束"小节（7 条 + 修宪门槛声明），#1/#6 已迁出并注明去向 | text_review |
| 4 | `refs/reviewer-prompt.md` | 两处硬编码 antipattern 清单替换为占位符，变量表含 `<antipatterns_path>`，type 枚举含全部 10 个 antipattern id（executor×4 + design×4 + orchestrator×2） | text_review |
| 5 | `refs/state-schema.md` | retrospective §3 含 id 硬约束 + `new:` 前缀规则 | text_review |
| 6 | `SKILL.md` 文件索引表 | 含 antipatterns.md 行 | text_review |
| 7 | `refs/orchestrator-guide.md` | Spawn 前自检清单含 `<antipatterns_path>` | text_review |
| 8 | `README.md` | 目录树含 antipatterns.md，最近变更段记录宪法依据和改动摘要 | text_review |
| 9 | 三处 id 一致性 | antipatterns.md id ↔ reviewer-prompt.md type 枚举 ↔ state-schema.md 约束互相一致 | text_review |
| 10 | 跨层清晰度 | executor/design/orchestrator 三层的检测责任区分显式，orchestrator 层正确标记为间接检测 | text_review |

## 宪法级审查维度

除上述功能断言外，Reviewer 应从 converge SKILL 自身宪法框架出发审查：

- **查表 vs 模式识别的区分是否被正确执行**：留在 SKILL.md 的 7 条是否确属"明确规则被打破"（离散事件，查表检测），迁入 antipatterns.md 的 #1/#6 是否确属"plausible 认知偏误"
- **修宪门槛声明是否充分**：是否明确"本节约束需经人工审议后修改，不接受 Agent 自主变更"
- **机制层是否未被触碰**：三角色、对抗循环、契约驱动、振荡熔断的存在性是否未被配置化或弱化
