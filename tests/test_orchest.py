#!/usr/bin/env python3
"""orchest.py 验收用例（plan 20260815-converge-exec-orchestration §验收标准 1-11）。

std库 unittest，无外部依赖。运行（仓库根）：
    python -m pytest tests/test_orchest.py -q
或  python -m unittest tests.test_orchest -v

验收映射：
  1  reserve-round 四角色五次调用生命周期     → TestReserveRoundLifecycle
  2  register/cancel 幂等 + 崩溃窗口          → TestRegisterRoundIdempotent /
                                                TestCancelRoundIdempotent / TestCrashWindowRecovery
  3  finish round 缺口拦截                    → TestFinishRoundGap
  4  finish 未 settle 拦截                    → TestFinishUnsettled
  5  finish 含 cancelled reservation 归档成功 → TestFinishWithCancelled
  6  finish 对已归档目录二次调用拒绝          → TestFinishTwiceRefused
  7  checkpoint-paths 跨仓（fixture + 现算）  → TestCheckpointPaths
  8  全命令 --dry-run 只打印不落盘            → TestDryRun
  9  真实回归 A（孤儿必炸 fail-closed）       → TestRegressionA（KB_VAULT_ROOT，skip-if）
  10 真实回归 B（语义等价归档）               → TestRegressionB（KB_VAULT_ROOT，skip-if）
  11 begin 失败分支与救济链                   → TestBeginFailureRelief
  （补充）record-verdict 契约字段回填+ingest  → TestRecordVerdict
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
ORCHEST = SCRIPTS / "orchest.py"
ARCHIVE = SCRIPTS / "archive_convergence.py"
GATE = SCRIPTS / "budget_gate.py"

sys.path.insert(0, str(SCRIPTS))
from archive_contract import capture  # noqa: E402

KB_ENV = "KB_VAULT_ROOT"
FIXTURE_REL = Path(".meta/converge/done/20260815-embeddings-cleanup")
ORPHAN_RID = "ab38462cf307"
FINAL_VERDICT = "可执行"


def run_orchest(*args, env_extra: dict | None = None) -> tuple[int, str, str]:
    env = {**os.environ, "PYTHONUTF8": "1"}
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(
        [sys.executable, str(ORCHEST), *args],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def run_cli(script: Path, *args) -> tuple[int, str, str]:
    env = {**os.environ, "PYTHONUTF8": "1"}
    r = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _read_events(active_dir: Path) -> list[dict]:
    events_dir = active_dir / "evidence" / "events"
    if not events_dir.is_dir():
        return []
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(events_dir.glob("*.json"))]


def _read_gate_ledger(active_dir: Path) -> list[dict]:
    p = active_dir / "gate-ledger.jsonl"
    if not p.is_file():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _fm_of(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    out = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def _invocation_triples(root: Path) -> set[tuple]:
    """(reservation_id, terminal_status, instance_id) 三元组集合（忽略 sequence/uuid/时间戳）。"""
    events = _read_events(root)
    rid_by_started = {e["event_id"]: e.get("reservation_id") for e in events
                      if e["event_type"] == "invocation-started"}
    triples = set()
    for e in events:
        if e["event_type"] == "invocation-terminal":
            triples.add((rid_by_started.get(e["started_event_id"]),
                         e["terminal_status"], e.get("instance_id")))
    return triples


class OrchestBase(unittest.TestCase):
    SLUG = "t-slug"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.active_root = self.root / "converge" / "active"
        self.active = self.active_root / self.SLUG
        self.active_root.mkdir(parents=True)
        self.active.mkdir()
        self.done_root = self.root / "converge" / "done"
        self.done_root.mkdir()
        self.prompt = self.root / "prompt.md"
        self.prompt.write_text("test prompt\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    # ---- 编排便捷封装 -------------------------------------------------------

    def reserve(self, role="outer-reviewer", round_no=1, phase="review", attempt=1,
                prompt: Path | None = None) -> tuple[str, str]:
        args = ["reserve-round", "--active-dir", str(self.active),
                "--role", role, "--phase", phase, "--attempt", str(attempt),
                "--prompt-file", str(prompt or self.prompt),
                "--requested-provider", "testp", "--requested-model", "testm"]
        if round_no is not None:
            args += ["--round", str(round_no)]
        rc, out, err = run_orchest(*args)
        self.assertEqual(rc, 0, f"reserve-round rc={rc} stdout={out} stderr={err}")
        rid = next(l.split(":", 1)[1].strip()
                   for l in out.splitlines() if l.startswith("reservation_id:"))
        iid = next(l.split(":", 1)[1].strip()
                   for l in out.splitlines() if l.startswith("invocation_id:"))
        return rid, iid

    def register(self, rid: str, sid: str, output: str | None = None,
                 backend: str | None = None) -> tuple[int, str, str]:
        args = ["register-round", "--active-dir", str(self.active),
                "--reservation-id", rid, "--instance-id", sid]
        if output:
            args += ["--output", output]
        if backend:
            args += ["--backend", backend]
        return run_orchest(*args)

    def cancel(self, rid: str, reason="cancelled-by-host", *extra) -> tuple[int, str, str]:
        return run_orchest("cancel-round", "--active-dir", str(self.active),
                           "--reservation-id", rid, "--reason-code", reason, *extra)

    def finish(self, verdict=FINAL_VERDICT, *extra) -> tuple[int, str, str]:
        return run_orchest("finish", "--active-dir", str(self.active),
                           "--verdict", verdict,
                           "--done-root", str(self.done_root),
                           "--slug", self.SLUG, *extra)

    def completed_round(self, n=1, backend="testhost") -> str:
        """一轮完整 outer 生命周期（reserve→register），返回 rid。"""
        rid, _ = self.reserve(round_no=n)
        rc, out, err = self.register(rid, f"inst-r{n}", backend=backend)
        self.assertEqual(rc, 0, f"register rc={rc} stderr={err}")
        return rid


# ── 验收 1：reserve-round 四角色五次调用 ─────────────────────────────────────

class TestReserveRoundLifecycle(OrchestBase):
    def test_four_roles_five_reservations(self):
        """每次调用后（模拟宿主派发前）events 已有 invocation-started；骨架按
        SCOPE_PRODUCT 分派；完整生命周期后 reserve/settle 严格配对。"""
        specs = [
            ("outer-reviewer", 1, "round-1.md"),
            ("outer-reviewer", 2, "round-2.md"),
            ("blind-reviewer", 1, "blind-recheck-1.md"),
            ("ultraverge-initial", 1, "uv-init-1.md"),
            ("executor", None, None),
        ]
        rids = []
        expected_events = 0
        for role, round_no, skeleton in specs:
            # executor 之前已有产物骨架（前四次 reserve 创建）——以快照差分断言
            products_before = {p.name for p in self.active.iterdir()
                               if p.suffix == ".md"}
            rid, iid = self.reserve(role=role, round_no=round_no, phase="test-phase")
            rids.append(rid)
            # 时序断言：命令返回即已有 started（宿主派发前）
            expected_events += 1
            events = _read_events(self.active)
            self.assertEqual(len(events), expected_events,
                             f"after reserve {role}: expected {expected_events} events")
            latest = events[-1]
            self.assertEqual(latest["event_type"], "invocation-started")
            self.assertEqual(latest["invocation_kind"], "spawn")
            self.assertEqual(latest["role"], role)
            self.assertEqual(latest["reservation_id"], rid)
            self.assertEqual(latest["invocation_id"], iid)
            self.assertEqual(latest["attempt"], 1)
            # 骨架分派
            products_after = {p.name for p in self.active.iterdir()
                              if p.suffix == ".md"}
            if skeleton is None:
                self.assertEqual(products_after, products_before,
                                 "executor consumes=none 不应创建产物骨架")
            else:
                self.assertEqual(products_after - products_before, {skeleton},
                                 f"skeleton {skeleton} missing for {role}")
                fm = _fm_of(self.active / skeleton)
                self.assertEqual(fm.get("reviewer_backend"), "pending")
                self.assertEqual(fm.get("reservation_id"), rid)
                self.assertEqual(fm.get("invocation_id"), iid)

        # ledger reserve 行
        reserved = [e for e in _read_gate_ledger(self.active) if e.get("event") == "reserved"]
        self.assertEqual({e["reservation_id"] for e in reserved}, set(rids))

        # 完整生命周期：register 全部（executor 需显式 --output）
        (self.active / "attempts.md").write_text("## Round 1 attempt\n", encoding="utf-8")
        for rid, (role, round_no, _), sid in zip(rids, specs,
                                                 ["s1", "s2", "s3", "s4", "s5"]):
            rc, out, err = self.register(rid, sid, output="attempts.md" if role == "executor" else None)
            self.assertEqual(rc, 0, f"register {role} rc={rc} stdout={out} stderr={err}")

        # reserve/settle 严格配对
        ledger = _read_gate_ledger(self.active)
        settled = [e for e in ledger if e.get("event") in
                   ("spawn_succeeded", "spawn_failed", "cancelled")]
        self.assertEqual({e["reservation_id"] for e in settled}, set(rids))
        for e in settled:
            self.assertEqual(e["event"], "spawn_succeeded")
        started_rids = {e["reservation_id"] for e in _read_events(self.active)
                        if e["event_type"] == "invocation-started"}
        self.assertEqual(started_rids, set(rids))


# ── 验收 2：register/cancel 幂等 + 崩溃窗口 ──────────────────────────────────

class TestRegisterRoundIdempotent(OrchestBase):
    def test_repeat_register_is_idempotent(self):
        rid, _ = self.reserve(round_no=1)
        rc, out, err = self.register(rid, "s1", backend="testhost")
        self.assertEqual(rc, 0, err)
        events_before = _read_events(self.active)
        ledger_before = _read_gate_ledger(self.active)

        rc, out, err = self.register(rid, "s1", backend="testhost")
        self.assertEqual(rc, 0, f"second register rc={rc} stdout={out} stderr={err}")
        self.assertIn("幂等完成", out)
        self.assertIn("terminal=succeeded", out)
        # 零新增事件、零新增 settle
        self.assertEqual(_read_events(self.active), events_before)
        self.assertEqual(_read_gate_ledger(self.active), ledger_before)


class TestCancelRoundIdempotent(OrchestBase):
    def test_repeat_cancel_is_idempotent(self):
        rid, _ = self.reserve(round_no=1)
        rc, out, err = self.cancel(rid)
        self.assertEqual(rc, 0, err)
        self.assertFalse((self.active / "round-1.md").exists(),
                         "机械占位骨架应被删除")
        events_before = _read_events(self.active)
        ledger_before = _read_gate_ledger(self.active)

        rc, out, err = self.cancel(rid)
        self.assertEqual(rc, 0, f"second cancel rc={rc} stdout={out} stderr={err}")
        self.assertIn("幂等完成", out)
        self.assertEqual(_read_events(self.active), events_before)
        self.assertEqual(_read_gate_ledger(self.active), ledger_before)


class TestCrashWindowRecovery(OrchestBase):
    """崩溃窗口前态构造（验收 2 写死）：库调用 capture 落 terminal 后不跑 settle 即停。"""

    def test_register_crash_window_backfills_settle_and_frontmatter(self):
        rid, iid = self.reserve(round_no=1)
        capture.complete_invocation(
            self.active, iid, terminal_status="succeeded", instance_id="cw-1",
            evidence_level="configured", resolution_source="cli_argument",
            resolution_reason_code="backend-does-not-expose",
            output_path=self.active / "round-1.md", evidence_mode="metadata-only",
        )
        self.assertEqual(len(_read_events(self.active)), 2)

        rc, out, err = self.register(rid, "cw-1")
        self.assertEqual(rc, 0, f"rc={rc} stdout={out} stderr={err}")
        self.assertIn("幂等完成", out)
        # 补 settle 落盘
        settles = [e for e in _read_gate_ledger(self.active)
                   if e.get("event") == "spawn_succeeded"]
        self.assertEqual(len(settles), 1)
        self.assertEqual(settles[0]["instance_id"], "cw-1")
        # 不重复写 terminal
        self.assertEqual(len(_read_events(self.active)), 2)
        # 骨架 frontmatter 已回填（非 pending）
        fm = _fm_of(self.active / "round-1.md")
        self.assertNotEqual(fm.get("reviewer_backend"), "pending")
        self.assertEqual(fm.get("reviewer_backend"), "unknown")  # terminal 无 backend 字段
        self.assertEqual(fm.get("reviewer_instance_id"), "cw-1")

    def test_cancel_crash_window_settles_failed(self):
        rid, iid = self.reserve(round_no=1)
        capture.recover_invocation(
            self.active, iid, terminal_status="failed",
            failure_reason_code="backend-error",
        )
        rc, out, err = self.cancel(rid, reason="backend-error")
        self.assertEqual(rc, 0, f"rc={rc} stdout={out} stderr={err}")
        settles = [e for e in _read_gate_ledger(self.active)
                   if e.get("event") == "spawn_failed"]
        self.assertEqual(len(settles), 1)
        self.assertEqual(len(_read_events(self.active)), 2)
        # 骨架收尾（机械占位 → 删除）
        self.assertFalse((self.active / "round-1.md").exists())

    def test_cancel_terminal_succeeded_does_not_touch_skeleton(self):
        """terminal=succeeded 的早退分支不走骨架删除/标注（成功产物保护）。"""
        rid, _ = self.reserve(round_no=1)
        rc, out, err = self.register(rid, "s1")
        self.assertEqual(rc, 0, err)
        rc, out, err = self.cancel(rid)
        self.assertEqual(rc, 0, f"rc={rc} stdout={out} stderr={err}")
        self.assertIn("terminal=succeeded", out)
        self.assertTrue((self.active / "round-1.md").is_file())
        self.assertNotIn("status: cancelled",
                         (self.active / "round-1.md").read_text(encoding="utf-8"))


# ── 验收 3：finish round 缺口 ────────────────────────────────────────────────

class TestFinishRoundGap(OrchestBase):
    def test_missing_round_intercepted_before_archive(self):
        self.completed_round(1)
        self.completed_round(2)
        (self.active / "round-4.md").write_text("---\nround: 4\n---\nbody\n",
                                                encoding="utf-8")
        rc, out, err = self.finish()
        self.assertNotEqual(rc, 0)
        combined = out + err
        self.assertIn("round-3.md", combined)
        self.assertIn("步骤 1", combined)
        # 前置拦截：done 无残留
        self.assertFalse((self.done_root / self.SLUG).exists())
        self.assertTrue(self.active.is_dir(), "active 未被归档移动")


# ── 验收 4：finish 未 settle 拦截 ────────────────────────────────────────────

class TestFinishUnsettled(OrchestBase):
    def test_open_reservation_intercepted(self):
        rid, _ = self.reserve(round_no=1)  # started + skeleton，但未 settle
        rc, out, err = self.finish()
        self.assertNotEqual(rc, 0)
        combined = out + err
        self.assertIn(rid, combined)
        self.assertIn("步骤 2", combined)
        self.assertFalse((self.done_root / self.SLUG).exists())


# ── 验收 5：finish 含 cancelled reservation 归档成功 ─────────────────────────

class TestFinishWithCancelled(OrchestBase):
    def test_archive_success_zero_orphan(self):
        rid1 = self.completed_round(1, backend="claude-code")
        rid2, _ = self.reserve(round_no=2)
        rc, out, err = self.cancel(rid2)
        self.assertEqual(rc, 0, err)
        self.assertFalse((self.active / "round-2.md").exists())
        (self.active / "retrospective.md").write_text(
            "---\ntype: retrospective\n---\n# Retrospective\n\ntest\n",
            encoding="utf-8")

        rc, out, err = self.finish()
        self.assertEqual(rc, 0, f"finish rc={rc} stdout={out} stderr={err}")
        target = self.done_root / self.SLUG
        self.assertTrue(target.is_dir())
        # 归档后 check valid
        rc, out, _ = run_cli(ARCHIVE, "check", str(target), "--format", "json")
        self.assertEqual(rc, 0, out)
        # 零孤儿（全程未用 --declare-orphan-reservation）
        rc, out, _ = run_cli(ARCHIVE, "list-orphan-reservations", str(target),
                             "--format", "json")
        self.assertEqual(rc, 0, out)
        self.assertEqual(json.loads(out)["orphan_reservations"], [])
        manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("acknowledged_orphan_reservations", manifest)
        self.assertEqual(manifest["final_decision"]["value"], FINAL_VERDICT)
        # active 已被归档移走
        self.assertFalse(self.active.exists())


# ── 验收 6：finish 二次调用拒绝 ──────────────────────────────────────────────

class TestFinishTwiceRefused(OrchestBase):
    def test_second_finish_refused(self):
        self.completed_round(1)
        (self.active / "retrospective.md").write_text("# Retrospective\n",
                                                      encoding="utf-8")
        rc, out, err = self.finish()
        self.assertEqual(rc, 0, err)
        rc, out, err = self.finish()
        self.assertNotEqual(rc, 0)
        self.assertIn("已存在", err)


# ── 验收 7：checkpoint-paths 跨仓 ────────────────────────────────────────────

CHECKPOINT_FIXTURE = {"seed-a.txt", "seed-b.txt", "seed-new.txt", "seed-renamed.txt"}


def _git(repo: Path, *args, check=True) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                       text=True, encoding="utf-8")
    if check and r.returncode:
        raise RuntimeError(r.stderr)
    return r.stdout.strip()


def _make_rename_repo(base: Path) -> tuple[Path, str]:
    repo = base / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t.local")
    _git(repo, "config", "user.name", "t")
    (repo / "seed-a.txt").write_text("a\n", encoding="utf-8")
    (repo / "seed-b.txt").write_text("b1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "c1")
    _git(repo, "mv", "seed-a.txt", "seed-renamed.txt")
    (repo / "seed-b.txt").write_text("b2\n", encoding="utf-8")
    (repo / "seed-new.txt").write_text("n\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "c2")
    return repo, _git(repo, "rev-parse", "HEAD")


def _parse_paths_block(out: str) -> set[str]:
    lines = out.splitlines()
    if not lines or lines[0] != "implementation_paths:":
        raise AssertionError(f"unexpected output head: {out[:200]!r}")
    return {l.strip()[2:] for l in lines[1:] if l.strip().startswith("- ")}


class TestCheckpointPaths(OrchestBase):
    def test_rename_commit_matches_frozen_fixture(self):
        """(a) 输出 == 实现期由源算法现算后固化的字面 fixture（防跨机依赖）。"""
        repo, sha = _make_rename_repo(self.root)
        rc, out, err = run_orchest("checkpoint-paths", "--commit", sha,
                                   "--repo", str(repo))
        self.assertEqual(rc, 0, err)
        self.assertEqual(_parse_paths_block(out), CHECKPOINT_FIXTURE)

    def test_repo_env_strip(self):
        """--repo 给定时剥离开 GIT_DIR 等定位变量（hook 上下文中它们压过 -C）。"""
        repo, sha = _make_rename_repo(self.root)
        bogus = self.root / "not-a-repo" / ".git"
        rc, out, err = run_orchest("checkpoint-paths", "--commit", sha,
                                   "--repo", str(repo),
                                   env_extra={"GIT_DIR": str(bogus)})
        self.assertEqual(rc, 0, f"clean_env 未生效? stderr={err}")
        self.assertEqual(_parse_paths_block(out), CHECKPOINT_FIXTURE)

    def test_kb_source_algorithm_parity(self):
        """(b) KB_VAULT_ROOT 指向本机 KB 仓时，与源算法 check_plan_review.changed_paths
        现算结果集合相等（未设或不存在则 skip，不硬编码本机绝对路径）。"""
        kb = os.environ.get(KB_ENV)
        src = Path(kb) / ".meta" / "scripts" / "check_plan_review.py" if kb else None
        if not src or not src.is_file():
            self.skipTest(f"{KB_ENV} 未设置或源算法文件不存在")
        repo, sha = _make_rename_repo(self.root)
        rc, out, err = run_orchest("checkpoint-paths", "--commit", sha,
                                   "--repo", str(repo))
        self.assertEqual(rc, 0, err)
        spec = importlib.util.spec_from_file_location("kb_check_plan_review", src)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod  # dataclass 注解解析需要模块已注册
        spec.loader.exec_module(mod)
        self.assertEqual(_parse_paths_block(out), mod.changed_paths(sha, str(repo)))


# ── 验收 8：--dry-run 只打印不落盘 ───────────────────────────────────────────

class TestDryRun(OrchestBase):
    def test_reserve_round_dry_run_zero_writes(self):
        rc, out, err = run_orchest(
            "reserve-round", "--active-dir", str(self.active),
            "--role", "outer-reviewer", "--phase", "review", "--round", "1",
            "--prompt-file", str(self.prompt),
            "--requested-provider", "p", "--requested-model", "m", "--dry-run")
        self.assertEqual(rc, 0, err)
        self.assertIn("dry-run", out)
        self.assertFalse((self.active / "gate-ledger.jsonl").exists())
        self.assertEqual(_read_events(self.active), [])
        self.assertFalse((self.active / "round-1.md").exists())

    def test_register_cancel_record_dry_run_zero_writes(self):
        rid, _ = self.reserve(round_no=1)
        rc, out, err = self.register(rid, "s1", backend="testhost")
        self.assertEqual(rc, 0, err)
        product = self.active / "round-1.md"
        before_bytes = product.read_bytes()
        events_before = _read_events(self.active)
        ledger_before = _read_gate_ledger(self.active)

        rc, out, err = run_orchest("register-round", "--active-dir", str(self.active),
                                   "--reservation-id", rid, "--instance-id", "s1",
                                   "--backend", "testhost", "--dry-run")
        self.assertEqual(rc, 0, err)
        rc, out, err = run_orchest("cancel-round", "--active-dir", str(self.active),
                                   "--reservation-id", rid,
                                   "--reason-code", "cancelled-by-host", "--dry-run")
        self.assertEqual(rc, 0, err)
        rc, out, err = run_orchest("record-verdict", "--active-dir", str(self.active),
                                   "--round", "1", "--verdict", "可执行", "--dry-run")
        self.assertEqual(rc, 0, err)
        # 零写入：无新事件、无新 settle、骨架未动、无 state 写入
        self.assertEqual(_read_events(self.active), events_before)
        self.assertEqual(_read_gate_ledger(self.active), ledger_before)
        self.assertEqual(product.read_bytes(), before_bytes)

    def test_finish_dry_run_zero_writes(self):
        self.completed_round(1)
        (self.active / "retrospective.md").write_text("# Retrospective\n",
                                                      encoding="utf-8")
        events_before = _read_events(self.active)
        retro_before = (self.active / "retrospective.md").read_bytes()

        rc, out, err = run_orchest("finish", "--active-dir", str(self.active),
                                   "--verdict", FINAL_VERDICT,
                                   "--done-root", str(self.done_root),
                                   "--slug", self.SLUG, "--dry-run")
        self.assertEqual(rc, 0, f"rc={rc} stdout={out} stderr={err}")
        self.assertFalse((self.done_root / self.SLUG).exists())
        self.assertTrue(self.active.is_dir())
        self.assertEqual(_read_events(self.active), events_before)
        self.assertEqual((self.active / "retrospective.md").read_bytes(), retro_before)

    def test_checkpoint_paths_dry_run_identical(self):
        repo, sha = _make_rename_repo(self.root)
        rc1, out1, _ = run_orchest("checkpoint-paths", "--commit", sha,
                                   "--repo", str(repo))
        rc2, out2, _ = run_orchest("checkpoint-paths", "--commit", sha,
                                   "--repo", str(repo), "--dry-run")
        self.assertEqual((rc1, out1), (rc2, out2))


# ── 验收 9：真实回归 A（fail-closed 契约）────────────────────────────────────

class TestRegressionA(OrchestBase):
    def _fixture(self) -> Path | None:
        kb = os.environ.get(KB_ENV)
        src = Path(kb) / FIXTURE_REL if kb else None
        return src if src and src.is_dir() else None

    def test_orphan_reservation_fail_closed(self):
        src = self._fixture()
        if src is None:
            self.skipTest(f"{KB_ENV} 未设置或 fixture 不存在")
        copy = self.active_root / "20260815-embeddings-cleanup"
        shutil.copytree(src, copy)

        def run_finish():
            return run_orchest("finish", "--active-dir", str(copy),
                               "--verdict", FINAL_VERDICT,
                               "--done-root", str(self.done_root),
                               "--slug", "20260815-embeddings-cleanup")

        rc, out, err = run_finish()
        combined = out + err
        self.assertNotEqual(rc, 0)
        # 报错指明该 reservation（步骤 2.5 前置显性化 + 步骤 7 硬校验）
        self.assertIn(ORPHAN_RID, combined)
        self.assertIn("ledger-invocation-orphan", combined)
        # 事务回滚：临时 done-root 无该 slug 残留
        self.assertFalse((self.done_root / "20260815-embeddings-cleanup").exists())
        # 重跑得到同一失败（确定性 fail-closed，非新错误形态）
        rc2, out2, err2 = run_finish()
        self.assertNotEqual(rc2, 0)
        combined2 = out2 + err2
        self.assertIn(ORPHAN_RID, combined2)
        self.assertIn("ledger-invocation-orphan", combined2)
        self.assertFalse((self.done_root / "20260815-embeddings-cleanup").exists())


# ── 验收 10：真实回归 B（语义等价）───────────────────────────────────────────

class TestRegressionB(OrchestBase):
    def test_surgered_fixture_archives_equivalently(self):
        kb = os.environ.get(KB_ENV)
        src = Path(kb) / FIXTURE_REL if kb else None
        if not src or not src.is_dir():
            self.skipTest(f"{KB_ENV} 未设置或 fixture 不存在")
        copy = self.active_root / "20260815-embeddings-cleanup"
        shutil.copytree(src, copy)
        # fixture 手术（明文授权，仅测试副本）：移除孤儿的 reserve+settle 两行
        ledger = copy / "gate-ledger.jsonl"
        kept = [ln for ln in ledger.read_text(encoding="utf-8").splitlines()
                if ln.strip() and json.loads(ln).get("reservation_id") != ORPHAN_RID]
        ledger.write_text("\n".join(kept) + "\n", encoding="utf-8", newline="\n")

        rc, out, err = run_orchest("finish", "--active-dir", str(copy),
                                   "--verdict", FINAL_VERDICT,
                                   "--done-root", str(self.done_root),
                                   "--slug", "20260815-embeddings-cleanup")
        self.assertEqual(rc, 0, f"finish rc={rc} stdout={out} stderr={err}")
        target = self.done_root / "20260815-embeddings-cleanup"
        rc, out, _ = run_cli(ARCHIVE, "check", str(target), "--format", "json")
        self.assertEqual(rc, 0, out)

        # 语义等价（机械定义）：三元组集合 + final decision verdict 与人工归档相等
        self.assertEqual(_invocation_triples(target), _invocation_triples(src))
        new_manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        old_manifest = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(new_manifest["final_decision"]["value"],
                         old_manifest["final_decision"]["value"])
        # 零孤儿 → 无披露键
        self.assertNotIn("acknowledged_orphan_reservations", new_manifest)


# ── 验收 11：begin 失败分支与救济链 ──────────────────────────────────────────

class TestBeginFailureRelief(OrchestBase):
    def _reserve_with_bad_prompt(self, round_no) -> tuple[int, str]:
        """prompt-file 为目录 → begin-invocation 必败（capture-filetype）。"""
        bad = self.root / f"badprompt-{round_no}"
        bad.mkdir()
        rc, out, err = run_orchest(
            "reserve-round", "--active-dir", str(self.active),
            "--role", "outer-reviewer", "--phase", "review",
            "--round", str(round_no), "--prompt-file", str(bad),
            "--requested-provider", "p", "--requested-model", "m")
        return rc, out + "\n" + err

    def test_begin_failure_and_resume_relief(self):
        rc, combined = self._reserve_with_bad_prompt(1)
        self.assertNotEqual(rc, 0)
        self.assertIn("begin-invocation 失败", combined)
        ledger = _read_gate_ledger(self.active)
        reserved = [e for e in ledger if e.get("event") == "reserved"]
        self.assertEqual(len(reserved), 1)
        rid = reserved[0]["reservation_id"]
        # gate ledger 该 rid 仍 open（无 settle 行）
        self.assertEqual([e for e in ledger if e.get("reservation_id") == rid
                          and e.get("event") != "reserved"], [])
        # events 零新增
        self.assertEqual(_read_events(self.active), [])

        # 修复原因后 --resume-reservation 同 rid 重试
        rc, out, err = run_orchest(
            "reserve-round", "--active-dir", str(self.active),
            "--role", "outer-reviewer", "--phase", "review", "--round", "1",
            "--prompt-file", str(self.prompt),
            "--requested-provider", "p", "--requested-model", "m",
            "--resume-reservation", rid)
        self.assertEqual(rc, 0, f"resume rc={rc} stdout={out} stderr={err}")
        self.assertIn(f"reservation_id: {rid}", out)
        started = [e for e in _read_events(self.active)
                   if e["event_type"] == "invocation-started"]
        self.assertEqual(len(started), 1)
        self.assertEqual(started[0]["reservation_id"], rid)

    def test_cancel_on_open_no_started_refused_zero_writes(self):
        rc, _ = self._reserve_with_bad_prompt(1)
        self.assertNotEqual(rc, 0)
        ledger_before = (self.active / "gate-ledger.jsonl").read_bytes()
        events_before = sorted(
            p.read_bytes() for p in (self.active / "evidence" / "events").glob("*.json")) \
            if (self.active / "evidence" / "events").is_dir() else []
        rid = next(e["reservation_id"] for e in _read_gate_ledger(self.active)
                   if e.get("event") == "reserved")

        rc, out, err = self.cancel(rid)
        self.assertNotEqual(rc, 0)
        self.assertIn("--resume-reservation", err)
        # 零写入
        self.assertEqual((self.active / "gate-ledger.jsonl").read_bytes(), ledger_before)
        events_after = sorted(
            p.read_bytes() for p in (self.active / "evidence" / "events").glob("*.json")) \
            if (self.active / "evidence" / "events").is_dir() else []
        self.assertEqual(events_after, events_before)

    def test_resume_precheck_negatives(self):
        # 先造一个已 started 的 rid（round 1 成功生命周期）
        rid_started, _ = self.reserve(round_no=1)
        rc, out, err = self.register(rid_started, "s1")
        self.assertEqual(rc, 0, err)
        # 再造一个 open-无-started 的 rid（round 2，begin 失败遗留）
        bad = self.root / "badprompt-neg"
        bad.mkdir()
        rc, _, _ = run_orchest(
            "reserve-round", "--active-dir", str(self.active),
            "--role", "outer-reviewer", "--phase", "review", "--round", "2",
            "--prompt-file", str(bad),
            "--requested-provider", "p", "--requested-model", "m")
        self.assertNotEqual(rc, 0)
        rid_open = next(e["reservation_id"] for e in _read_gate_ledger(self.active)
                        if e.get("event") == "reserved"
                        and e["reservation_id"] != rid_started)

        cases = [
            # (rid, role, round, 期望错误子串)
            ("nosuchrid0000", "outer-reviewer", 1, "rid 错误"),
            (rid_started, "outer-reviewer", 1, "register-round"),        # 已 started
            (rid_open, "blind-reviewer", 2, "ledger-role-conflict"),     # role 不符
            (rid_open, "outer-reviewer", 3, "ledger-round-conflict"),    # round 不符
        ]
        for rid, role, round_no, needle in cases:
            rc, out, err = run_orchest(
                "reserve-round", "--active-dir", str(self.active),
                "--role", role, "--phase", "review", "--round", str(round_no),
                "--prompt-file", str(self.prompt),
                "--resume-reservation", rid)
            self.assertNotEqual(rc, 0, f"{rid}/{role}/{round_no} 应报错: {out}")
            self.assertIn(needle, err, f"{rid}/{role}/{round_no}: {err}")


# ── 补充：record-verdict ─────────────────────────────────────────────────────

class TestRecordVerdict(OrchestBase):
    def test_backfill_contract_fields_and_ingest(self):
        self.completed_round(1, backend="testhost")
        rc, out, err = run_orchest(
            "record-verdict", "--active-dir", str(self.active),
            "--round", "1", "--verdict", "阻断需修复",
            "--severities", "implementation,structural")
        self.assertEqual(rc, 0, f"rc={rc} stdout={out} stderr={err}")
        fm = _fm_of(self.active / "round-1.md")
        self.assertEqual(fm.get("round"), "1")
        self.assertEqual(fm.get("reviewer_backend"), "testhost")
        self.assertEqual(fm.get("reviewer_instance_id"), "inst-r1")
        self.assertTrue(fm.get("generated_at"))
        self.assertEqual(fm.get("verdict"), "阻断需修复")
        state = json.loads((self.active / "_budget-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["fsm"]["severities"]["1"],
                         ["implementation", "structural"])

    def test_finish_blocked_verdict_requires_ingested_severities(self):
        """finish 步骤 0.5：终局阻断 verdict 与 gate 侧零 ingest 矛盾 → 拒绝。"""
        self.completed_round(1)
        rc, out, err = self.finish(verdict="阻断需修复")
        self.assertNotEqual(rc, 0)
        self.assertIn("步骤 0.5", err)
        self.assertIn("record-verdict", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
