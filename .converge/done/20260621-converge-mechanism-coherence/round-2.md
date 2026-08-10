# Round 2 — convergence re-review（单个 fresh outer-reviewer）

reviewer reservation: 4e0ee3541341，settled succeeded.

## Verdict

**阻断需修复** — 但 **8/8 round-1 escalated_issues 全部 `resolved`**（结构修复生效），仅发现 **2 个新的、更浅层** blocking + 4 个 suggestion。这是**健康收敛信号**（问题逐轮缩小，非发散）。

## Round-1 escalated 复查（8 条全 resolved）

| # | theme | status | 要点 |
|---|-------|--------|------|
| 1 | 可达性悖论 | **resolved** | 判据迁至 orchestrator-guide（Orchestrator 运行时必读）→ 真 dissolved，结构迁移非措辞修补 |
| 2 | parking 自我取消 | **resolved** | 判据 agent-readable 后，N≥3 计数可达 → 触发器不再自我屏蔽 |
| 3 | § 判例 层级错位 | **resolved** | audit → 操作指导层；placement elimination 推理自洽 |
| 4 | 缺 operational-guidance 中间层 | **resolved** | 四层架构显式命名 + placement 判据 |
| 5 | Bitter Lesson 误用 | **resolved** | pointer ≠ mechanism 显式区分；asymmetric application 消除 |
| 6 | 自举偏见无对冲 | **resolved** | 自举声明 3 条对冲（反转举证/外部锚点/结构切换）—— 但 hedge #2 强度略高估（见 suggestion） |
| 7 | plan 内部矛盾 | **resolved** | "迁出"被执行，"park at GD"消除 —— 但新矛盾产生（见 blocking #1） |
| 8 | resolution density 过低 | **resolved** | 4 项文件改动 + 3 项结构规则 + 自举声明，从 deferral log 升级为 coherent proposal |

## 新 blocking issues（2 个，比 round-1 浅层）

### #1：GD append-only 原则 vs § 判例 改为指针 的操作冲突（structural）

plan § 调整 2 自我宣告"GD = append-only audit trail（不可回改已记条目）"，§ 调整 1 执行操作"GD-2 § 判例 改为指针"却是对已 approved 条目的内容修改 → 直接冲突。若 substitutive → 违反 append-only；若 additive → 内容双处。reviewer 给三选项：(a) additive（GD-2 全文保留 + 镜像注记）；(b) substitutive + GD-3 授权；(c) substitutive + 宪法层豁免。

**orchestrator 倾向**：(a) additive 的严格形态——**GD-2 完全不动**（它是历史记录，§ 判例 内容作为"批准时的持有位置"保留），orchestrator-guide § 发散检测 = live source，迁移由后续 GD 条目或注记记录（不回改 GD-2 entry 本身）。最保 audit 纯度。

### #2：parking-discipline 规则持久化归属未指明（structural）

规则在 plan 内定义+应用+自验证，但 § 文件改动清单不含其持久化。plan 归档后脱离 agent 必读集 → 下一轮自举场景规则失效 → 自举对冲 hedge #1 失效 → 偏见回归。

**reviewer 选项**：A. refs/orchestrator-guide.md（操作指导层）；B. CONSTITUTION.md 第一部（机制级）；C. 作 Bitter Lesson+Occam 具体化（引用 pointer）。

**orchestrator 倾向**：A——parking-discipline 是 Orchestrator 做停放决策的运行时规则，属操作指导层。加进 § 文件改动清单。

## Suggestions（4 个，非阻断）

1. 自举 hedge #2（外部锚点）措辞过强——应明示"必要非充分"，hedge #1 才是实质对冲。
2. placement 判据 step 1 方向不对称（负向排除 vs 后续正向归属）——可改为显式 "audit 否决测试"。
3. "agent-readable" scope 模糊——本 context 指 Orchestrator（divergence-detector），非所有 agent；plan 应明示。
4. "CONSTITUTION 第一部新增四层小节（描述性，非新约束）"措辞误导——placement 判据一旦写入即 binding criterion；应改"正式化已隐式存在的结构 + 给归属判据"。

## DR 7 维 findings

- DR1：blocking #1 的内部一致性问题（append-only vs 内容迁移）
- DR2：blocking #2 的完整性缺口（规则无持久化路径）
- DR3/DR5：与 blocking #1 联动（双处维护 vs 单处+跳转的取舍）
- DR4/DR6：清晰 + framework-agnostic，设计亮点
- DR7：placement step 4 fallback 未来可能被滥用；建议观测频率

## 下一步

spawn executor 按 round-2 fix-list（2 blocking + 4 suggestion）修订 plan → round 3 re-review。预期 round 3 可达 `可执行`（修复明确、范围小）。
