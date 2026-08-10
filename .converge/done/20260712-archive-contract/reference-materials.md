# 原始背景材料

## 用户反馈

用户指出 `.agents/skills/ocsr/.converge/done/20260712-ocsr-remediation` 内容平铺且杂乱，要求先报告，随后明确要求修复 converge 当前归档规范的设计缺口。

## 已确认事实

- 样本归档包含 27 个平铺文件，其中 prompt 9 个、评审/执行报告 9 个。
- 目录没有审计入口、manifest 或 Markdown 导航链接。
- 多个归档文件仍引用已不存在的 `.converge/active/...` 绝对路径。
- session id 与角色可追踪，但 provider/model/family 没有集中 provenance。
- plan 声称保留修改前后机械哈希，归档实际没有目标快照、哈希或完整 diff。
- 最终结论需要跨 8 个文件手工重建。

## 用户授权边界

- 用户已授权修复 converge 归档规范。
- 未授权删除历史归档证据；旧归档必须保持只读兼容。
