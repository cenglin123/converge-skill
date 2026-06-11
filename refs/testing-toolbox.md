# 测试工具箱

> Orchestrator 在 Spawn Reviewer 前查阅本文件，确定 `<test_command>` 和 `<lint_command>` 的注入值。Reviewer 不需要读本文件——它只执行注入的命令。

---

## 一、命令速查表

### JavaScript / TypeScript

| 工具 | 检测信号 | test_command | lint_command |
|------|---------|-------------|-------------|
| npm (默认) | `package.json` 存在，无其他信号 | `npm test` | `npx eslint .` |
| Jest | `package.json` 含 `jest` 依赖 | `npx jest --no-coverage` | `npx eslint .` |
| Vitest | `package.json` 含 `vitest` 依赖 | `npx vitest run` | `npx eslint .` |
| Mocha | `package.json` 含 `mocha` 依赖 | `npx mocha` | `npx eslint .` |
| TypeScript | `tsconfig.json` 存在 | — | `npx tsc --noEmit`（类型检查，替代或补充 eslint） |

> npm 项目优先看 `package.json` 的 `scripts.test` 字段，它可能覆盖默认命令（如 `"test": "vitest run"`）。

### Python

| 工具 | 检测信号 | test_command | lint_command |
|------|---------|-------------|-------------|
| pytest | `pyproject.toml` / `setup.cfg` 含 `pytest`，或 `conftest.py` 存在 | `pytest` | `ruff check .` |
| unittest | `import unittest` 出现在测试文件中 | `python -m pytest` 或 `python -m unittest discover` | `ruff check .` |
| mypy | `pyproject.toml` 含 `mypy` | — | `mypy .`（类型检查，补充 ruff） |
| Poetry | `pyproject.toml` 含 `[tool.poetry]` | `poetry run pytest` | `poetry run ruff check .` |

> Python 项目优先用 `ruff`（替代 flake8 + isort + black 的检查）。若项目用其他 linter（flake8、pylint），在测试文件中检测 `# noqa` 注释推断。

### Rust

| 工具 | 检测信号 | test_command | lint_command |
|------|---------|-------------|-------------|
| Cargo | `Cargo.toml` 存在 | `cargo test` | `cargo clippy -- -D warnings` |

### Go

| 工具 | 检测信号 | test_command | lint_command |
|------|---------|-------------|-------------|
| go test | `go.mod` 存在 | `go test ./...` | `go vet ./...` |

### Java / Kotlin

| 工具 | 检测信号 | test_command | lint_command |
|------|---------|-------------|-------------|
| Maven | `pom.xml` 存在 | `mvn test` | — |
| Gradle | `build.gradle` 或 `build.gradle.kts` 存在 | `./gradlew test` | — |

### C# / .NET

| 工具 | 检测信号 | test_command | lint_command |
|------|---------|-------------|-------------|
| dotnet | `*.csproj` 或 `*.sln` 存在 | `dotnet test` | `dotnet format --verify-no-changes` |

### Ruby

| 工具 | 检测信号 | test_command | lint_command |
|------|---------|-------------|-------------|
| RSpec | `Gemfile` 含 `rspec` 或 `spec/` 目录存在 | `bundle exec rspec` | `bundle exec rubocop` |
| Minitest | `Gemfile` 含 `minitest` 或 `test/` 目录存在 | `bundle exec rake test` | `bundle exec rubocop` |

---

## 二、发现流程

Orchestrator 按以下顺序确定要注入的命令（每一步给出具体的 agent 执行动作）：

```
1. 检查项目声明的测试入口
   动作：Read 项目根目录，查找以下文件
   - Makefile → 搜索含 "test" 的 target → 注入 `make test`
   - justfile → 搜索含 "test" 的 recipe → 注入 `just test`
   - package.json → Read "scripts.test" 字段 → 注入 `npm test`
   → 找到任何一个：使用项目声明的命令，跳过步骤 2

2. 按技术栈检测信号查速查表（§一）
   动作：Read 项目根目录，查找检测信号文件（Cargo.toml / go.mod / pyproject.toml 等）
   → 找到匹配：使用表中对应的 test_command 和 lint_command
   → 多个匹配：按收敛对象涉及的模块选择对应命令

3. 检查 CI 配置作为后备信号（§四）
   动作：Read .github/workflows/ 或 .gitlab-ci.yml 等 CI 文件
   → 找到测试命令：使用 CI 中实际运行的命令

4. 检查可执行脚本（§六）
   动作：审查对象是否包含 CLI 入口（argparse/click/cobra 等）、含 `__main__` 的 Python 脚本、或 `bin` 字段？
   → 是：两命令均留空；Reviewer 按 reviewer-prompt.md §代码项目审查第 3 条，检测到可执行入口后自行构造最小 happy-path 并实际运行。无法复现时按 `deterministic_check: skipped` + skip_reason 上报
   → 否：进入 step 5

5. 以上均未检测到
   → <test_command> 和 <lint_command> 都留空，Reviewer 跳过确定性检查（`deterministic_check: skipped`）
```

**优先级**：项目入口 > 技术栈信号 > CI 配置 > 脚本验证（§六） > 跳过

---

## 三、多语言项目

若项目包含多种技术栈（如 Python 后端 + TypeScript 前端）：

1. 分别检测，分别注入
2. `<test_command>` 用 `&&` 连接：`cd backend && pytest && cd ../frontend && npm test`
3. 或按 converge 的 scope 拆分——如果收敛对象只涉及其中一个，只注入对应的命令

---

## 四、CI/CD 作为信号源

如果项目有 CI 配置文件，它们是测试命令的最佳信号源：

| CI 文件 | 提取方式 |
|---------|---------|
| `.github/workflows/*.yml` | 找 `run:` 行中的测试命令 |
| `.gitlab-ci.yml` | 找 `script:` 行中的测试命令 |
| `Jenkinsfile` | 找 `sh '` 行中的测试命令 |
| `.circleci/config.yml` | 找 `command:` 行中的测试命令 |

CI 配置里的测试命令是最权威的——它是项目实际在用的、持续验证过的命令。

---

## 五、安全约束

- 所有命令以**只读方式**运行——测试不应修改产物代码或持久化文件
- 若测试框架有 `--coverage` 选项，**不加**——coverage 报告会产生临时文件，干扰 converge 的文件追踪
- 若 lint 命令有 `--fix` 选项，**不加**——Reviewer 只检查不修复，修复是 Executor 的事
- 若测试命令需要**外部服务**（数据库、API endpoint、网络服务）且环境不可用，在 `<test_command>` 注入时标注为不可用——Reviewer 会收到空 `<test_command>` 并跳过确定性检查（`deterministic_check: skipped`）。不建议 Mock——converge 的测试验证应跑真实测试，Mock 的测试结论可信度不足

---

## 六、无测试套件的可执行脚本验证

**即使项目没有形式化的测试套件（pytest / jest / cargo test 等），Reviewer 也不应直接跳过确定性检查。** 如果审查对象包含可执行脚本（CLI、Python 脚本等），Reviewer 应在语义审查之前**构造最小 happy-path 场景并实际运行**。

**实证**：DW SKILL 的 scheduler.py 没有测试套件，但 codex Reviewer 通过运行 `init → dispatch → complete → dispatch → done` 的 CLI 假流程发现了 4 个 bug（pipe 优先级错误、budget 未执行、stage 校验缺失、barrier/loop ack 可跳过），这些是纯文档审查完全无法发现的。

**触发条件**：审查对象包含以下任一可执行入口：
- CLI 工具（argparse / click / cobra / clap 等）
- 有 `if __name__ == "__main__"` 的 Python 脚本
- 有 `main()` 函数 + 可编译入口的语言项目
- `package.json` 的 `bin` 字段

**执行方式**：
1. Orchestrator 在注入 `<test_command>` 时，若所有检测步骤（§二 1-4）均未命中，但审查对象包含可执行脚本，则两命令均留空
2. Reviewer 按 reviewer-prompt.md §代码项目审查第 3 条，检测到可执行入口后自行构造最小 happy-path 并实际运行
3. 若文档中描述了预期的 CLI 行为但 Reviewer 无法在环境中复现（如依赖缺失），标注 `deterministic_check: skipped` 并在 `deterministic_check_skip_reason` 说明原因
4. 这不是"运行测试套件"——只是验证"文档描述的行为在实际执行时是否成立"
