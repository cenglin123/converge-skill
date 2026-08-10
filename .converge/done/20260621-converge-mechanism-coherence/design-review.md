# Design Review — converge 机制协调性调整（强制 ultraverge 设计审查）

reviewer reservation: b4b90fc46939，settled succeeded. 单轮咨询式，不阻断。findings 供用户决策。

## highlights（最重要的 3 个设计层发现，供用户优先定夺）

### Highlight 1：四层架构疑似为本次 § 判例 迁移**量身定制**

「操作指导层 = `refs/*-guide.md / *-prompt.md`」的载体定义恰好匹配迁移目的地（orchestrator-guide.md）。但 refs/ 实际 13 个文件中**仅 4 个**匹配该 glob；**8 个**（contract-negotiation / decomposition-protocol / framework-adapters / model-tiers / quality-gate / rubrics / state-schema / testing-toolbox）在四层架构中**无显式归属**——placement elimination 推理未对它们验证。

- **why it matters**：若批准并正式化进 CONSTITUTION，converge 将拥有"理论通用、实践 N=1"的层架构。model-tiers.md 自称"数据层"（四层无此类别）、rubrics/quality-gate/state-schema 性质各异——证明 converge 数据载体**不止四类**。把未充分验证的抽象固化成宪法级判据有风险。
- **suggested direction**（两选，可并用）：(a) **收窄野心**——四层定位为"本次迁移判据"，非通用框架；正式化时声明"覆盖范围限于本次迁移路径文件"。(b) **扩展范围**——对全 13 refs/ 文件做 placement 验证，对不能干净归属的扩展层类别（引入"数据层"/"参考层"）。

### Highlight 2：3 hedge 约束力严重不均

- **hedge #2（外部锚点 = 用户 ultraverge 关键词）**：结构性可观测、agent **不可伪造** → **硬约束**
- **hedge #1（反转举证 + parking-discipline）**：载体是 plan 自创规则，自评循环被 hedge 自身承认，缓解依赖"独立 Reviewer 复核"——但**复核的机械接驳点 plan 未给**（仅声明"留作 Reviewer 复核标的"）→ **软约束**
- **hedge #3（结构切换 > 打补丁）**：设计纪律声明，**无机制强制**，只是承诺 → **声明**

"3 hedge"框架让自评议显得严肃，实际仅 1 hedge 不可绕过。若未来引用本 plan 作"hedge 模板"，会降级对冲实际强度。
- **suggested direction**：plan 内对 hedge 显式分级（硬/软/声明）+ hedge #1 指定机械接驳点（如 Reviewer 必须在 plan 修订中显式回应 parking 自评，否则 plan 不进下一轮）。

### Highlight 3："provisional binding"无生命周期 = 永久 binding 加弱标签

plan 承认 N=1 vs binding 不对称，用 "provisional" 前缀调和。但 provisional **无 sunset、无计数载体、无转正触发器**：谁计 N？哪里记录？何时评估转正？plan 沉默。
- **why it matters**：没 sunset 的 provisional = 永久 binding 加弱标签。下次 ultraverge 不自动重审；converge 自身不主动重计 N（自举悖论延续）。"provisional" 沦为修辞让步。
- **suggested direction**：定义 provisional 生命周期——placement 验证事件记录载体（GD frontmatter 字段或独立 registry）+ 转正触发（N≥3 或时间≥6 月）+ 未转正时复审义务（每次 ultraverge 自动扫一次）。

---

## 其余维度 findings（DR1-DR7）

- **DR1 一致性 concerns**：四层与 refs/ 实际分布不一致（8 文件悬空）+ model-tiers 自称"数据层"vs 四层无数据层（两套层词汇并存）+ SKILL 拆分文件索引（用途视角）与四层（层视角）未同步
- **DR2 完整性 concerns**：文件改动清单只 4 文件，但"正式化四层"隐含对 13 refs/ 的层归属声明（范围低估）+ placement elimination 缺 tie-breaking + parking-discipline (b)"核心功能"缺可验证锚点
- **DR3 可维护性 concerns**：层归属缺**物理载体**（如 frontmatter `layer:` 字段）→ 每次新人/新 agent 需重走推理 + provisional→stable 无维护机制（谁计数/记录/触发）
- **DR4 职责边界 concerns**：model-tiers 是 framework-agnostic 但 model-specific 数据 → 四层无"数据层"类别 + 操作指导层内未细分"运行时必读 vs 按需查阅"
- **DR5 残留冗余 concerns**：GD-2 § 判例 历史快照 + orchestrator-guide live 双份存在，分歧时无提示机制 + 新旧层词汇残留并存
- **DR6 可移植性 clean**：四层 + placement elimination 是 framework-agnostic 抽象，可移植
- **DR7 可扩展性 concerns**：缺通用**层属变更程序**（§ 判例 迁移是个案未泛化）+ placement 判据缺 falsification 修订路径（只可"重设"）

---

## 处置建议

设计审查**不阻断**——convergence 已完成（round 3 可执行 + 盲审 2 通过）。上述 findings 供用户决策：
- 哪些**修复后落地**（如 highlight 1 的收窄野心、highlight 3 的 provisional 生命周期）
- 哪些**延后**（如 DR7 通用层属变更程序——可作未来 N≥2 迁移时提炼）
- 哪些**忽略/接受**（如 DR5 双份存在——audit 纯度的可接受 tradeoff）

**orchestrator 倾向**：highlight 1 + 3 值得在落地前处置（收窄四层范围 + 定义 provisional 生命周期），highlight 2 的 hedge 分级 + 机械接驳点也值得加（让自评议对冲真有牙齿）。但这些是用户的治理决策，不由 orchestrator 自定。
