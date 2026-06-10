# Model Tiers — 家族档位对照表

> 本文件为数据层、非治理文档，对 Agent 行为无规范性约束力（规范在 SKILL.md「模型分层」小节）；更新无需修宪程序，每次更新注明核实日期与核实方式（联网核实，不依赖任何 agent 的记忆）。
> 强档列为参考信息（判断密集角色当期主力档）；Orchestrator 模型由用户会话决定，converge 无权选择。
> 核实日期与方式：Claude 行 Fable 5 由运行时会话佐证（2026-06-10）；OpenAI / Gemini / DeepSeek 三家族为联网核实（2026-06-10）。

| 家族 | 低档（Executor 降档目标） | 强档（参考：判断密集角色当期主力档） |
|------|--------------------------|--------------------------------------|
| Claude | Haiku 4.5（备注：Sonnet 4.6 为介于两档之间的备选，不构成独立档位） | Fable 5、Opus 4.8 |
| OpenAI GPT | GPT-5.4 mini、GPT-5.4 nano | GPT-5.5、GPT-5.4 |
| Gemini | Gemini 3.5 Flash、Gemini 3.1 Flash-Lite | Gemini 3.1 Pro |
| DeepSeek | DeepSeek-V4-Flash | DeepSeek-V4-Pro |

使用规则：

1. 档位是家族内相对概念。单元格列出多个型号时，取该家族当期最便宜的通用档。
2. 过期兜底：表过期时以该家族当期定价最低的通用档为准，不阻塞执行。
