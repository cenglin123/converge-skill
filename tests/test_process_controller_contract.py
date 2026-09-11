"""Static contracts for controller ownership and Executor-local methods."""
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT_ROOT = ROOT.parent / "init-agent-docs"


def read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def authoritative_files(root: Path):
    excluded_parts = {".git", ".converge", ".pytest_cache", "__pycache__", "docs", "tests"}
    excluded_files = {Path(__file__).resolve(), root / "docs" / "CHANGELOG.md"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".sh", ".tpl", ".html"}:
            continue
        if path.resolve() in excluded_files or excluded_parts.intersection(path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith("docs/plans/"):
            continue
        yield path


class ProcessControllerContractTest(unittest.TestCase):
    def test_converge_owns_selected_workflow_but_not_every_generated_project(self):
        skill = read(ROOT, "SKILL.md")
        for phrase in (
            "被用户或宿主选为当前工作流时",
            "唯一顶层控制器",
            "Executor-local",
            "不使生成项目依赖 Converge",
        ):
            self.assertIn(phrase, skill)

    def test_executor_method_contract_is_behavior_based_and_evidenced(self):
        discipline = read(ROOT, "refs/executor-discipline.md")
        prompt = read(ROOT, "refs/executor-prompt.md")
        reviewer = read(ROOT, "refs/reviewer-discipline.md")
        for phrase in (
            "可观察的预变更失败",
            "可证伪假设",
            "最后一次写入之后",
            "无写入分析角色",
            "非权威合同提议",
        ):
            self.assertIn(phrase, discipline)
        self.assertIn("测试身份、红灯结果、绿灯结果", prompt)
        self.assertIn("不得为了仪式性红灯", reviewer)
        self.assertIn("独立运行", reviewer)

    def test_domain_roles_defer_top_level_control(self):
        sources = [
            read(INIT_ROOT, "SKILL.md"),
            read(INIT_ROOT, "assets/references/workflow-patterns.md"),
            read(INIT_ROOT, "assets/templates/zh/AGENTS.md.tpl"),
            read(INIT_ROOT, "README.md"),
        ]
        for text in sources:
            self.assertIn("当前选定的控制器", text)
        patterns = sources[1]
        for phrase in ("领域交接角色", "不拥有全局模式", "不签发终局结论", "不自行启动反复修复循环"):
            self.assertIn(phrase, patterns)

    def test_stale_stock_claims_absent_from_runtime_sources(self):
        banned = [
            "max_inner_loops" + "=3",
            "最多 " + "3 次 Continue",
            "普通 = " + "63 / ultraverge = 62",
            "MAX_INNER" + "_LOOPS",
            "MAX_INNER_LOOPS" + "_DEFAULT",
            "inner_" + "streak",
            "默认 " + "8 轮",
            "DEFAULTS = " + "3",
            "原默认 " + "5",
            "7/" + "12 轮超限",
            "原默认 " + "1",
            "3 覆盖「打回→修复→再审」完整周期",
            "原 1" + "→3",
            "[^" + "mbr]",
            "3/" + "1/1",
        ]
        hits = []
        for path in authoritative_files(ROOT):
            text = path.read_text(encoding="utf-8", errors="replace")
            for literal in banned:
                if literal in text:
                    hits.append(f"{path.relative_to(ROOT)}: {literal}")
        self.assertEqual(hits, [])

        skill = read(ROOT, "SKILL.md")
        self.assertIn("stock 默认（由 `scripts/budget_gate.py` 的 `DEFAULTS` 提供", skill)
        # r2: 8/3/3 is the evidence-restored stop-loss ceiling
        self.assertIn("8/3/3", skill)
        # r2: no ultraverge blind overlay in governance docs
        self.assertNotIn("ultraverge 初始化时，Orchestrator 向 `_budget-state.json` 的 config 覆盖为 `max_blind_rechecks=2`", skill)
        readme = read(ROOT, "README.md")
        readme_en = read(ROOT, "README_en.md")
        for doc in (readme, readme_en):
            self.assertNotIn("叠加 `max_blind_rechecks=2`", doc)
            self.assertNotIn("ultraverge 模式叠加", doc)
            self.assertNotIn("Ultraverge mode overlays", doc)

    def test_bespoke_controller_is_deleted(self):
        stale = INIT_ROOT / "scripts" / ("converge_" + "orchestrator.py")
        self.assertFalse(stale.exists(), stale)

    def test_r2_governance_contracts_present(self):
        """r2: machine-input, empirical-conflict, quality-goal, same-hash echo obligations."""
        reviewer_disc = read(ROOT, "refs/reviewer-discipline.md")
        reviewer_prompt = read(ROOT, "refs/reviewer-prompt.md")
        orchestrator = read(ROOT, "refs/orchestrator-guide.md")
        state_schema = read(ROOT, "refs/state-schema.md")
        scripts_readme = read(ROOT, "scripts/README.md")

        # Machine-input: converge.governance-change/v1 is the only machine input
        self.assertIn("converge.governance-change/v1", state_schema)
        self.assertIn("唯一机器输入", reviewer_disc)

        # Empirical conflict fields and no-downgrade rule
        self.assertIn("empirical_conflict", reviewer_disc)
        self.assertIn("不得降级为 suggestion", reviewer_disc)

        # Quality-goal event id requirement
        self.assertIn("quality_goal_event_id", reviewer_prompt)

        # Same-hash output echo for material revisions
        self.assertIn("byte-identical", reviewer_prompt)

        # Material-revision two-authority dispatch in orchestrator guide
        self.assertIn("material-revision", orchestrator)
        self.assertIn("同字节", orchestrator)

        # Closure-pairing rule documented
        self.assertIn("pre_execution", scripts_readme)
        self.assertIn("closure-pairing", scripts_readme.lower())

        # Task-envelope quality_path_guaranteed disclosure
        self.assertIn("quality_path_guaranteed: false", scripts_readme)

    def test_r2_readme_budget_profile_aligned(self):
        """r2: README budget profile uses 8/3/3, not stale 3/1/1/21/23."""
        readme = read(ROOT, "README.md")
        readme_en = read(ROOT, "README_en.md")
        # Correct stock defaults present
        self.assertIn("8", readme)
        self.assertIn("63", readme)
        self.assertIn("63", readme_en)
        # Stale budget profile table values absent
        for text in (readme, readme_en):
            # The old table had "3 | 1 | 1 | 21" and "3 | 2 | 1 | 23"
            self.assertNotIn("| 3 | 1 | 1 | 21 |", text)
            self.assertNotIn("| 3 | 2 | 1 | 23 |", text)


if __name__ == "__main__":
    unittest.main()
