"""Static contracts for controller ownership and Executor-local methods."""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT_ROOT = ROOT.parent / "init-agent-docs"


def function_source(text: str, name: str) -> str | None:
    """Extract the source of a top-level/nested function by name (AST-scoped).

    Used so anti-regression assertions are anchored to a specific write point /
    function rather than the whole file (which would false-positive on read-side
    defaults elsewhere).
    """
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            lines = text.splitlines()
            return "\n".join(lines[node.lineno - 1:node.end_lineno])
    return None


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


def _authorized_direct_gate_files() -> set[str]:
    return {
        "scripts/budget_gate.py",
        "scripts/orchest.py",
        "scripts/ocsr_spawn_adapter.py",
        "scripts/converge_loop.py",
        "tests/test_budget_gate.py",
        "tests/test_orchest.py",
        "tests/test_ocsr_spawn_adapter.py",
        "tests/test_converge_loop.py",
        "tests/test_loop_a_coverage.py",
    }


class OpEnvelopeToolingHardeningTest(unittest.TestCase):
    """Sub-plan A（O2 + O4 + O7）防回退静态检查：以函数/调用点为单位锚定。"""

    def _orchest(self) -> str:
        return read(ROOT, "scripts/orchest.py")

    # ── D1/O2：需要 exact 的写出点不得回退为字面量 metadata-only ──────────────
    def test_orchest_exact_write_points_not_hardcoded(self):
        orchest = self._orchest()
        # _reserve_continue 的 begin 写出点：透传 args.evidence_mode（不得字面量）
        continue_src = function_source(orchest, "_reserve_continue")
        self.assertIsNotNone(continue_src)
        self.assertNotIn('"--evidence-mode", "metadata-only"', continue_src)
        self.assertIn('getattr(args, "evidence_mode"', continue_src)
        # cmd_finish 的步骤 3 崩溃恢复写出点：缺省继承 started，--evidence-mode 仅覆盖
        finish_src = function_source(orchest, "cmd_finish")
        self.assertIsNotNone(finish_src)
        self.assertNotIn('"--evidence-mode", "metadata-only"', finish_src)
        self.assertIn('"--evidence-mode", recovery_mode', finish_src)
        # finish --evidence-mode 缺省哨兵 None（不得 default="metadata-only"）
        self.assertIn('"--evidence-mode", default=None', orchest)

    def test_orchest_negative_read_side_default_untouched(self):
        """负例：material gate 读取侧默认值仍是 metadata-only（检查按函数锚定，不误伤）。"""
        material_src = function_source(self._orchest(), "_validate_material_gate")
        self.assertIsNotNone(material_src)
        self.assertIn('"metadata-only"', material_src)

    def test_material_gate_constants_single_source(self):
        """O6/A-5/F6：材料门常量与 ``_material_cur`` 单源在 orchest.py，且 12 项受控
        词表与 refs/orchestrator-guide.md 的枚举 token 集合机械等值（防双写漂移）。"""
        orchest = self._orchest()
        self.assertIn('MATERIAL_CHANGE_CLASSES = frozenset({"decisional", "non-decisional"})',
                      orchest)
        self.assertIn("MATERIAL_SECTION_VOCAB = frozenset({", orchest)
        self.assertIn("def _material_cur(", orchest)

        tree = ast.parse(orchest)
        vocab: set[str] | None = None
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "MATERIAL_SECTION_VOCAB":
                        value_node = node.value
                        if (isinstance(value_node, ast.Call)
                                and isinstance(value_node.func, ast.Name)
                                and value_node.func.id == "frozenset"
                                and value_node.args):
                            value_node = value_node.args[0]
                        vocab = set(ast.literal_eval(value_node))
        self.assertIsNotNone(vocab, "MATERIAL_SECTION_VOCAB assignment not found")
        assert vocab is not None
        self.assertEqual(len(vocab), 12, f"expected 12-item vocab, got {sorted(vocab)}")

        guide = read(ROOT, "refs/orchestrator-guide.md")
        marker = "**12 项受控章节词表**"
        self.assertIn(marker, guide)
        after = guide.split(marker, 1)[1]
        after = after.split("：", 1)[1] if "：" in after else after
        body = after.split("。", 1)[0]
        doc_tokens = set(re.findall(r"`([^`]+)`", body))
        self.assertEqual(doc_tokens, vocab,
                         f"guide tokens {sorted(doc_tokens)} != orchest {sorted(vocab)}")

    def test_reserve_dry_run_display_is_parameter_linked(self):
        orchest = self._orchest()
        self.assertNotIn("evidence-mode=metadata-only", orchest)

    # ── D1/O2：adapter / converge_loop 默认策略与透传 ─────────────────────────
    def test_adapter_cli_default_metadata_only_and_passthrough(self):
        adapter = read(ROOT, "scripts/ocsr_spawn_adapter.py")
        self.assertIn('d.add_argument("--evidence-mode", default="metadata-only"', adapter)
        self.assertIn("evidence_mode=evidence_mode", adapter)   # begin
        self.assertIn('"--evidence-mode", evidence_mode', adapter)  # complete

    def test_converge_loop_evidence_mode_single_source(self):
        loop = read(ROOT, "scripts/converge_loop.py")
        self.assertIn("from archive_contract.model import EVIDENCE_MODES", loop)
        self.assertIn('spec.get("evidence_mode", "metadata-only")', loop)
        reserve_src = function_source(loop, "reserve")
        register_src = function_source(loop, "register")
        self.assertIn('"--evidence-mode", self.evidence_mode', reserve_src)
        self.assertIn('"--evidence-mode", self.evidence_mode', register_src)

    # ── D3/O7：来源声明门 ────────────────────────────────────────────────────
    def test_budget_gate_source_declaration_gate(self):
        gate = read(ROOT, "scripts/budget_gate.py")
        self.assertIn("FAIL_CLOSED:naked_state_transition", gate)
        self.assertIn("EXIT_USAGE = 2", gate)
        reserve_src = function_source(gate, "cmd_reserve")
        # reserve 门置于 --companion-for 分派之前
        self.assertLess(reserve_src.index('_check_source_declaration(args, active, "reserve")'),
                        reserve_src.index("cmd_companion_for(args)"))
        settle_src = function_source(gate, "cmd_settle")
        # settle 门置于进入 Lock 之前
        self.assertLess(settle_src.index("_check_source_declaration"),
                        settle_src.index("with Lock(active)"))
        # ingest-verdict 不设门（保留 guide:248 直调路径）
        iv_src = function_source(gate, "cmd_ingest_verdict")
        self.assertNotIn("_check_source_declaration", iv_src)

    def test_orchest_and_adapter_inject_orchest_managed(self):
        orchest = self._orchest()
        gate_src = function_source(orchest, "_gate")
        self.assertIn('("reserve", "settle")', gate_src)
        self.assertIn('"--orchest-managed"', gate_src)
        adapter = read(ROOT, "scripts/ocsr_spawn_adapter.py")
        for fn in ("_gate_reserve", "_gate_settle", "_ensure_te_companion"):
            src = function_source(adapter, fn)
            self.assertIsNotNone(src, fn)
            self.assertIn('"--orchest-managed"', src, fn)

    def test_no_new_direct_gate_accounting_calls_outside_authorized_files(self):
        """reserve / settle 直调（命令数组形态）只允许出现在授权文件内。"""
        pattern = re.compile(r"""["'](reserve|settle)["']\s*,\s*["']--active-dir["']""")
        allowed = _authorized_direct_gate_files()
        offenders: set[str] = set()
        for base in (ROOT / "scripts", ROOT / "tests"):
            for path in base.rglob("*.py"):
                rel = path.relative_to(ROOT).as_posix()
                text = path.read_text(encoding="utf-8", errors="replace")
                if pattern.search(text) and rel not in allowed:
                    offenders.add(rel)
        self.assertEqual(offenders, set(), f"授权文件外的直调记账命令: {sorted(offenders)}")


if __name__ == "__main__":
    unittest.main()
