# Round 2 Recovery Executor Report

## Scope and safety incident

接管时 `capture.EventLock` 使用 `os.kill(pid, 0)`。在 Windows CPython 中该调用会映射到进程终止，能够解释三次测试执行通道异常退出。危险实现先经静态编辑移除；在移除前未运行测试。替代实现位于 schema/model 公共层：Windows 使用 `OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION)`、`WaitForSingleObject(..., 0)` 与 `CloseHandle`，Linux 使用 `/proc`，其余平台返回 unknown。unknown 一律 fail closed。`EventLock` 与 `SlugLock` 共用该 helper。

安全处置顺序：

1. 静态替换危险 owner probe；
2. 添加 current-PID 与 unknown-owner 隔离测试；
3. 运行单个不创建锁的 probe 测试，PASS；
4. 运行 Archive Contract suite，执行通道稳定；
5. 才继续事务故障注入与全量测试。

## Blocking remediation

- B-1：artifact/slug identifier 在任何读取与路径构造前验证；CLI 将 prompt/output 路径交给 capture 安全读取，不先 `read_bytes`；external authorization 在 source `lstat/open` 前检查；blob/event 同锁事务提交，失败回滚。
- B-2：Spawn 强制 reservation；ledger reserve/settle 与 role/round/status/instance 双向闭合；Reviewer verdict 绑定授权 fresh Spawn terminal 与该 terminal output；Continue 绑定 parent Spawn 的同一 instance。
- B-3：provenance tagged union 严格校验 observed/host-reported receipt、host evidence 与 resolved fields；configured/inherited/unavailable 使用闭合 reason。manifest 和 INDEX 投影 requested/resolved/source/reason/degradation。
- B-4：event exact-key schema、UUID/time/positive integer、artifact revision uniqueness 已执行；manifest blob 只从 owner ref allowlist 生成，孤儿 evidence fail closed。
- B-5：invocation blob+event 与 terminal 唯一性置于同一 EventLock；锁 owner 探测跨平台且非破坏；archive/reopen 在破坏性 rename 前 durable journal，重试恢复。新增 source-backed-up journal failure 与 reopen-moved journal failure 两个故障注入回归。
- B-6：check 保留首个稳定 validator diagnostic；INDEX 增加 model provenance、artifact provenance、risks、degradation、revision/event/next-read；pre-push 使用 Git `--name-only -z`，任意 `done/<slug>/` 变更均通过单一 CLI helper 检查；stale-check 识别 archive 与 reopen journal 状态。
- B-7：Archive Contract 测试由接管时 30 项扩为 32 项，新增非破坏 owner probe 与 archive/reopen journal recovery；既有半成品已包含 B-1..B-6 的反例。Bugfix 文档写入本次实际命令与结果，不再只转指 landing report。

## Verification evidence

- `python -B tests/test_archive_convergence.py ArchiveContractTests.test_event_lock_liveness_probe_never_uses_os_kill` — PASS，1 test。
- `python -B tests/test_archive_convergence.py` — PASS，32 tests in 1.845s。
- `python -B -m unittest discover -s tests -p test_*.py` — PASS，82 tests in 11.803s。
- `git diff --check` — PASS。
- `rg` 确认实现中无危险 signal-zero 调用；唯一文本命中是测试对源码“不含该调用”的断言。
- 测试派生的两个 `__pycache__` 目录已清理。
- 未 commit。

## Honest limitations and handoff

- Round-2 B-7 列出的 Windows ADS/device/UNC/extended path 与 reparse privilege 分支没有在当前主机把每一个平台对象都真实创建；现有 normalize/filetype/reparse 检查覆盖合同路径，无法创建的对象仍应作为 capability skip 报告，不能宣称全部平台实物验证。
- `docs/problems/bugfix/convergence-archive-auditability.md` 仍被仓库 `.gitignore` 的 `docs/` 规则忽略。文件已更新但未擅自执行 Git 纳入；Orchestrator 落地时需要显式采用项目认可的 tracking 方式。
- `.gitattributes` 是接管前已存在的未跟踪文件，本 Executor 未修改、未删除。
- 本报告仅陈述实际执行的 32/82 项自动化证据，不把计划 §10 的每个组合都表述为已穷举验证。
