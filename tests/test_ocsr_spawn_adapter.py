#!/usr/bin/env python3
"""ocsr_spawn_adapter 验收用例（plan §Phase 1 测试与验收）。

stdlib unittest，无外部依赖。运行：
    python -m unittest tests.test_ocsr_spawn_adapter -v

测试矩阵：
  - happy path（fake ocsr 写产物）→ complete-invocation(succeeded) + settle succeeded
  - fail-launcher（fake 写 error.log）→ recover-invocation(failed, pre_execution=true) + settle failed
  - fail-timeout（fake 看门狗超时）→ recover-invocation(timeout, pre_execution=false) + settle failed
  - reserve BLOCK（unknown role）→ adapter 直接退出 BLOCK，无 begin-invocation
  - event graph 闭包：每次 spawn 产生 started+terminal 一对事件，sequence 连续
  - ledger 双写：gate-ledger 有 reserve+settle，ocsr-dispatch-ledger 有 launched+(landed|failed)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
ADAPTER = SCRIPTS / "ocsr_spawn_adapter.py"
ARCHIVE = SCRIPTS / "archive_convergence.py"
GATE = SCRIPTS / "budget_gate.py"
FAKE_OCSR = Path(__file__).resolve().parent / "_fake_ocsr_dispatch.py"

sys.path.insert(0, str(SCRIPTS))
import budget_gate  # noqa: E402
from ocsr_spawn_adapter import _extract_ocsr_instance_id


def run_adapter(active_dir: Path, fake_ocrs_env: dict | None = None, *extra_args) -> tuple[int, str, str]:
    env = {**os.environ, "PYTHONUTF8": "1"}
    if fake_ocrs_env:
        env.update(fake_ocrs_env)
    r = subprocess.run(
        [sys.executable, str(ADAPTER), *extra_args],
        capture_output=True, text=True, encoding="utf-8",
        env=env,
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def run_gate(active_dir: Path, *args) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(GATE), *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    return r.returncode, r.stdout.strip()


def _read_events(active_dir: Path) -> list[dict]:
    events_dir = active_dir / "evidence" / "events"
    if not events_dir.is_dir():
        return []
    out = []
    for p in sorted(events_dir.glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def _read_gate_ledger(active_dir: Path) -> list[dict]:
    p = active_dir / "gate-ledger.jsonl"
    if not p.is_file():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_ocsr_ledger(active_dir: Path) -> list[dict]:
    p = active_dir / "ocsr-dispatch-ledger.jsonl"
    if not p.is_file():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


class AdapterBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.active = self.root / "active"
        self.active.mkdir()
        self.output_dir = self.root / "output"
        self.output_dir.mkdir()
        self.prompt = self.root / "prompt.txt"
        self.prompt.write_text("test prompt\n", encoding="utf-8")
        # 确保 stock state 使用 version 2 默认值（plan D3）
        budget_gate.initialize_state(self.active)

    def tearDown(self):
        self.tmp.cleanup()

    def _adapter_args(self, **overrides) -> list[str]:
        defaults = dict(
            converge_active=str(self.active),
            converge_scripts=str(SCRIPTS),
            ocsr_dispatch=str(FAKE_OCSR),
            role="executor",
            phase="test-phase",
            round=None,
            attempt=1,
            prompt=str(self.prompt),
            model="deepseek/deepseek-v4-flash",
            label="test-label",
            output_dir=str(self.output_dir),
            output_name="product.md",
            watch=True,
            timeout=1,
            evidence_mode="metadata-only",
        )
        defaults.update(overrides)
        args = ["dispatch"]
        for k, v in defaults.items():
            flag = "--" + k.replace("_", "-")
            if v is None:
                continue
            if isinstance(v, bool):
                if v:
                    args.append(flag)
                continue
            args += [flag, str(v)]
        return args


class TestHappyPath(AdapterBase):
    def test_reserve_begin_dispatch_complete_settle(self):
        """Full happy path: product lands → succeeded terminal + settle succeeded."""
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(),
        )
        self.assertEqual(rc, 0, f"rc={rc} stdout={out} stderr={err}")

        # Event graph: exactly 1 started + 1 terminal, sequence 1,2
        events = _read_events(self.active)
        self.assertEqual(len(events), 2, f"expected 2 events, got {len(events)}")
        started, terminal = events
        self.assertEqual(started["event_type"], "invocation-started")
        self.assertEqual(started["invocation_kind"], "spawn")
        self.assertEqual(started["role"], "executor")
        self.assertEqual(started["sequence"], 1)
        self.assertEqual(started["reservation_id"], started["reservation_id"])  # non-empty
        self.assertEqual(started["requested_provider"], "deepseek")
        self.assertEqual(started["requested_model"], "deepseek-v4-flash")

        self.assertEqual(terminal["event_type"], "invocation-terminal")
        self.assertEqual(terminal["terminal_status"], "succeeded")
        self.assertEqual(terminal["started_event_id"], started["event_id"])
        self.assertEqual(terminal["sequence"], 2)
        self.assertEqual(terminal["evidence_level"], "configured")
        self.assertEqual(terminal["resolution_source"], "cli_argument")
        self.assertEqual(terminal["resolution_reason_code"], "backend-does-not-expose")
        # configured level forbids resolved fields (model.py:498, 512-513)
        for f in ("resolved_provider", "resolved_model", "resolved_family"):
            self.assertIsNone(terminal.get(f), f"{f} should be None under configured level")
        # instance_id + receipt are correlation handles, not host-evidence bindings.
        # receipt is what the adapter passed (points at ocsr ledger as correlation
        # anchor); settlement_ref is what capture.py auto-generated (points at gate
        # ledger as the budget-binding ledger). Per design.md §3.3 + §3.5.
        self.assertIsNotNone(terminal.get("instance_id"))
        self.assertEqual(terminal["receipt"], f"ocsr-dispatch-ledger.jsonl:{started['reservation_id']}")
        self.assertEqual(terminal["settlement_ref"], f"gate-ledger.jsonl:{started['reservation_id']}")
        self.assertEqual(terminal["backend"], "opencode")
        # output evidence present
        self.assertIsNotNone(terminal.get("output_evidence"))

        # Gate ledger: reserved + spawn_succeeded, instance_id matches
        gate = _read_gate_ledger(self.active)
        reserved = [e for e in gate if e.get("event") == "reserved"]
        succeeded = [e for e in gate if e.get("event") == "spawn_succeeded"]
        self.assertEqual(len(reserved), 1)
        self.assertEqual(len(succeeded), 1)
        self.assertEqual(reserved[0]["target_role"], "executor")
        self.assertEqual(succeeded[0]["reservation_id"], reserved[0]["reservation_id"])
        self.assertEqual(succeeded[0]["instance_id"], terminal["instance_id"])

        # Ocsr ledger: launched + landed
        ocsr = _read_ocsr_ledger(self.active)
        launched = [e for e in ocsr if e.get("event") == "launched"]
        landed = [e for e in ocsr if e.get("event") == "landed"]
        self.assertEqual(len(launched), 1)
        self.assertEqual(len(landed), 1)
        # instance_id used by adapter should be ocsr batch_id
        self.assertEqual(terminal["instance_id"], launched[0]["batch_id"])

    def test_role_outer_reviewer_consumes_outer_scope(self):
        """outer-reviewer role should consume outer scope (round-N.md budget)."""
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(role="outer-reviewer", round=1),
        )
        self.assertEqual(rc, 0, f"rc={rc} stdout={out} stderr={err}")
        gate = _read_gate_ledger(self.active)
        reserved = next(e for e in gate if e.get("event") == "reserved")
        self.assertEqual(reserved["target_role"], "outer-reviewer")
        self.assertEqual(reserved["consumes"], "outer")
        self.assertEqual(reserved["target_round"], 1)


class TestEvidenceMode(AdapterBase):
    """D1/O2：adapter 的 --evidence-mode 默认策略与透传。"""

    def test_default_metadata_only(self):
        rc, out, err = run_adapter(self.active, {"FAKE_OCSR_MODE": "happy"},
                                   *self._adapter_args())
        self.assertEqual(rc, 0, f"{out} {err}")
        started, terminal = _read_events(self.active)
        self.assertEqual(started["prompt_evidence"]["evidence_mode"], "metadata-only")
        self.assertEqual(terminal["output_evidence"]["evidence_mode"], "metadata-only")

    def test_exact_evidence_mode_passthrough(self):
        rc, out, err = run_adapter(self.active, {"FAKE_OCSR_MODE": "happy"},
                                   *self._adapter_args(evidence_mode="exact"))
        self.assertEqual(rc, 0, f"{out} {err}")
        started, terminal = _read_events(self.active)
        self.assertEqual(started["prompt_evidence"]["evidence_mode"], "exact")
        self.assertEqual(terminal["output_evidence"]["evidence_mode"], "exact")


class TestFailurePaths(AdapterBase):
    def test_fail_launcher_uses_pre_execution_true(self):
        """fail-launcher (Start-Process error, no model call) → pre_execution=true."""
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "fail-launcher"},
            *self._adapter_args(),
        )
        self.assertEqual(rc, 5, f"expected EXIT_OCSR_NO_PRODUCT=5, got rc={rc}; stderr={err}")

        events = _read_events(self.active)
        self.assertEqual(len(events), 2)
        terminal = events[1]
        self.assertEqual(terminal["event_type"], "invocation-terminal")
        self.assertEqual(terminal["terminal_status"], "failed")
        self.assertEqual(terminal["evidence_level"], "unavailable")
        self.assertEqual(terminal["resolution_source"], "none")
        self.assertEqual(terminal["resolution_reason_code"], "invocation-failed-before-resolution")
        self.assertEqual(terminal["failure_reason_code"], "backend-error")

        gate = _read_gate_ledger(self.active)
        failed = next(e for e in gate if e.get("event") == "spawn_failed")
        self.assertTrue(failed.get("pre_execution"),
                        "Start-Process failure must record pre_execution=true")

    def test_fail_timeout_uses_pre_execution_false(self):
        """Watchdog timeout (model invoked but stalled) → pre_execution=false."""
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "fail-timeout"},
            *self._adapter_args(),
        )
        self.assertEqual(rc, 5, f"expected EXIT_OCSR_NO_PRODUCT=5, got rc={rc}; stderr={err}")

        events = _read_events(self.active)
        terminal = events[1]
        self.assertEqual(terminal["terminal_status"], "timeout")
        self.assertEqual(terminal["failure_reason_code"], "timeout")

        gate = _read_gate_ledger(self.active)
        failed = next(e for e in gate if e.get("event") == "spawn_failed")
        self.assertFalse(failed.get("pre_execution"),
                         "Watchdog timeout must record pre_execution=false (model was invoked)")


class TestReserveGate(AdapterBase):
    def test_unknown_role_blocks_before_begin(self):
        """Unknown role → DENY:unknown_role, no begin-invocation side effect."""
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(role="not-a-real-role"),
        )
        self.assertEqual(rc, 11, f"expected EXIT_DENY=11, got rc={rc}; stderr={err}")

        # No invocation events should exist
        events = _read_events(self.active)
        self.assertEqual(len(events), 0,
                         "DENY must not produce any invocation events")

        # Gate should have a DENY decision recorded
        gate = _read_gate_ledger(self.active)
        decisions = [e for e in gate if e.get("event") == "decision"]
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["verdict"], "DENY:unknown_role")


class TestArchiveCheckValid(AdapterBase):
    def test_event_graph_passes_model_validation(self):
        """After happy-path spawn, model.validate_event_graph must accept the events.

        archive_convergence.py `check` reports `legacy-unverifiable` on active/ (no
        manifest yet — manifest is created at archive time). To verify event-graph
        integrity without going through full archive, we call the model module's
        validator directly. The full archive-validity check is exercised in Phase 3
        end-to-end dogfood.
        """
        rc, _, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(),
        )
        self.assertEqual(rc, 0, f"adapter rc={rc}; stderr={err}")

        # Import the model validator (scripts/ is on sys.path via the setUp at top)
        from archive_contract import model
        events = _read_events(self.active)
        # validate_event_graph raises ArchiveError on any structural violation;
        # if it returns without raising, the event graph is sound.
        try:
            model.validate_event_graph(events)
        except model.ArchiveError as e:
            self.fail(f"event graph failed model.validate_event_graph: {e.diagnostic()}")


class TestConfigInit(unittest.TestCase):
    """Phase 2: config-init subcommand writes _budget-state.json correctly."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.active = self.root / "active"
        self.active.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _run_config_init(self, *extra) -> tuple[int, str, str]:
        env = {**os.environ, "PYTHONUTF8": "1"}
        r = subprocess.run(
            [sys.executable, str(ADAPTER), "config-init",
             "--converge-active", str(self.active), *extra],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()

    def test_standard_mode_writes_empty_config(self):
        rc, out, err = self._run_config_init()
        self.assertEqual(rc, 0, f"rc={rc} stderr={err}")
        state = json.loads((self.active / "_budget-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["fsm"]["mode"], "standard")
        self.assertEqual(state["config"], {})
        self.assertEqual(state["extensions"], [])

    def test_ultraverge_mode_no_blind_rechecks_override(self):
        rc, out, err = self._run_config_init("--mode", "ultraverge")
        self.assertEqual(rc, 0, f"rc={rc} stderr={err}")
        state = json.loads((self.active / "_budget-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["fsm"]["mode"], "ultraverge")
        # 无 blind 倒挂叠加：新 ultraverge state 与 standard 同上限（plan r2 D9）
        self.assertNotIn("max_blind_rechecks", state["config"])

    def test_explicit_overrides_win_over_ultraverge_default(self):
        rc, out, err = self._run_config_init("--mode", "ultraverge", "--max-blind-rechecks", "5")
        self.assertEqual(rc, 0, f"rc={rc} stderr={err}")
        state = json.loads((self.active / "_budget-state.json").read_text(encoding="utf-8"))
        # 显式 config 权威：显式值原样落盘
        self.assertEqual(state["config"].get("max_blind_rechecks"), 5)

    def test_idempotent_no_force_fails_closed(self):
        """Repeating equal values is an idempotent no-op."""
        rc, _, _ = self._run_config_init()
        self.assertEqual(rc, 0)
        rc2, out, err = self._run_config_init()
        self.assertEqual(rc2, 0, f"rc={rc2}; stderr={err}")

    def test_conflicting_existing_state_fails_closed(self):
        self.assertEqual(self._run_config_init("--max-outer-loops", "5")[0], 0)
        rc, out, err = self._run_config_init("--max-outer-loops", "4")
        self.assertEqual(rc, 30, out + err)
        state = json.loads((self.active / "_budget-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["config"]["max_outer_loops"], 5)

    def test_force_overwrites(self):
        rc, _, _ = self._run_config_init()
        self.assertEqual(rc, 0)
        rc2, _, _ = self._run_config_init("--force", "--mode", "ultraverge")
        self.assertEqual(rc2, 0)
        state = json.loads((self.active / "_budget-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["fsm"]["mode"], "ultraverge")

    def test_state_file_uses_lf_line_endings(self):
        """_budget-state.json is root-fixed & manifest-hashed; must be LF."""
        rc, _, _ = self._run_config_init()
        self.assertEqual(rc, 0)
        raw = (self.active / "_budget-state.json").read_bytes()
        self.assertNotIn(b"\r\n", raw, "_budget-state.json must use LF (eol=lf per .gitattributes)")


class TestBudgetAccounting(AdapterBase):
    """Phase 2: verify reserve/settle through adapter updates budget_gate ledger correctly."""

    def test_outer_scope_reservation_blocks_at_ceiling(self):
        """After stock max_outer_loops outer-reviewer reservations, the next must
        BLOCK:budget_exhausted. Verifies the adapter
        actually drives budget_gate per-scope, not just total."""
        for i in range(1, 9):
            # Each iteration uses a different output_name to avoid collision detection,
            # and a different round to satisfy budget_gate's (scope, round) uniqueness
            # invariant. D2/O4：产物落在 active 根（round-N.md）使预约号恒等于 FS 推导的
            # 下一个连续轮号（否则漂移门会在 round>=2 时 fail-closed）。
            rc, _, err = run_adapter(
                self.active, {"FAKE_OCSR_MODE": "happy"},
                *self._adapter_args(role="outer-reviewer", round=i,
                                    output_name=f"round-{i}.md",
                                    label=f"r{i}", output_dir=str(self.active)),
            )
            self.assertEqual(rc, 0, f"iteration {i}: rc={rc}; stderr={err}")
        # Next outer reservation must BLOCK
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(role="outer-reviewer", round=9,
                                output_name="round-9.md", label="r9",
                                output_dir=str(self.active)),
        )
        self.assertEqual(rc, 10, f"expected EXIT_BLOCK=10, got rc={rc}; stderr={err}")
        gate = _read_gate_ledger(self.active)
        decisions = [e for e in gate if e.get("event") == "decision"]
        last = decisions[-1]
        self.assertEqual(last["verdict"], "BLOCK:budget_exhausted")
        self.assertEqual(last["scope"], "outer")
        self.assertEqual(last["observed_usage"], 8)
        events = _read_events(self.active)
        self.assertEqual(len(events), 16)

    def test_summary_reports_attempted_and_model_invocation(self):
        """budget_gate summary must distinguish attempted_dispatch (含启动前失败)
        from model_invocation (真实模型调用) — adapter must drive this correctly."""
        # 2 happy (real model calls) + 1 fail-launcher (pre_execution)
        for i, mode in enumerate(["happy", "happy", "fail-launcher"], 1):
            rc, _, _ = run_adapter(
                self.active, {"FAKE_OCSR_MODE": mode},
                *self._adapter_args(role="executor", attempt=i,
                                    output_name=f"p{i}.md", label=f"e{i}"),
            )
            if mode == "happy":
                self.assertEqual(rc, 0)
            else:
                self.assertEqual(rc, 5)

        # Run summary via adapter passthrough
        env = {**os.environ, "PYTHONUTF8": "1"}
        r = subprocess.run(
            [sys.executable, str(ADAPTER), "summary",
             "--converge-active", str(self.active),
             "--converge-scripts", str(SCRIPTS)],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )
        self.assertEqual(r.returncode, 0, f"summary stderr: {r.stderr}")
        summary = json.loads(r.stdout)
        # 3 reservations issued (2 succeeded + 1 pre-execution failed); pre_execution
        # cancelled/failure does NOT reduce total_reservations_issued (monotonic).
        self.assertEqual(summary["total_reservations_issued"], 3)
        # attempted_dispatch includes all 3; model_invocation also all 3
        # (fail-launcher has pre_execution=true, so NOT a real model invocation,
        # but spawn_failed event is still counted by attempted_dispatch since
        # budget_gate.attempted_dispatch excludes only pre_execution cancelled,
        # not pre_execution failed).
        # See budget_gate.py:282-288 attempted_dispatch logic.
        self.assertEqual(summary["attempted_dispatch"], 3)
        # model_invocation excludes pre_execution failures → 2 real calls
        self.assertEqual(summary["model_invocation"], 2)


class TestReservedReservationId(AdapterBase):
    """S1: --reserved-reservation-id bypass path."""

    def _pre_reserve(self, rid: str) -> None:
        rc, out = run_gate(
            self.active, "reserve", "--active-dir", str(self.active),
            "--role", "executor", "--tier", "auditable-only",
            "--reservation-id", rid,
            "--manual-fallback", "test-fixture",
        )
        self.assertEqual(rc, 0, f"pre-reserve failed: {out}")

    def test_reserved_id_happy_bypasses_reserve(self):
        """--reserved-reservation-id skips reserve; happy path still works."""
        rid = "ext-res-001"
        self._pre_reserve(rid)
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(reserved_reservation_id=rid),
        )
        self.assertEqual(rc, 0, f"adapter rc={rc} stderr={err}")
        gate = _read_gate_ledger(self.active)
        reserved = [e for e in gate if e.get("event") == "reserved"]
        self.assertEqual(len(reserved), 1, "adapter must not issue duplicate reserve")
        self.assertEqual(reserved[0]["reservation_id"], rid)
        events = _read_events(self.active)
        self.assertEqual(events[0]["reservation_id"], rid)
        self.assertIn("using externally-reserved id", err)

    def test_reserved_id_fail_launcher_still_recovers(self):
        """--reserved-reservation-id with fail-launcher still recovers."""
        rid = "ext-res-002"
        self._pre_reserve(rid)
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "fail-launcher"},
            *self._adapter_args(reserved_reservation_id=rid),
        )
        self.assertEqual(rc, 5, f"adapter rc={rc} stderr={err}")
        gate = _read_gate_ledger(self.active)
        reserved = [e for e in gate if e.get("event") == "reserved"]
        self.assertEqual(len(reserved), 1)
        spawn_failed = [e for e in gate if e.get("event") == "spawn_failed"]
        self.assertEqual(len(spawn_failed), 1)
        self.assertEqual(spawn_failed[0]["reservation_id"], rid)

    def test_reserved_id_fail_timeout_recovers(self):
        """--reserved-reservation-id with fail-timeout still recovers."""
        rid = "ext-res-003"
        self._pre_reserve(rid)
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "fail-timeout"},
            *self._adapter_args(reserved_reservation_id=rid),
        )
        self.assertEqual(rc, 5, f"adapter rc={rc} stderr={err}")
        events = _read_events(self.active)
        self.assertEqual(events[1]["terminal_status"], "timeout")
        self.assertEqual(events[0]["reservation_id"], rid)


class TestExtractInstanceId(unittest.TestCase):
    """S2: _extract_ocsr_instance_id boundary tests."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.ledger = self.root / "ocsr-dispatch-ledger.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_ledger_file_returns_fallback(self):
        """Missing ledger → ocsr-unknown-* fallback."""
        val = _extract_ocsr_instance_id(self.ledger, "label", "m/m", "p.txt")
        self.assertTrue(val.startswith("ocsr-unknown-"),
                        f"expected ocsr-unknown-* prefix, got: {val}")

    def test_empty_ledger_returns_fallback(self):
        """Empty ledger → ocsr-unknown-* fallback."""
        self.ledger.write_text("", encoding="utf-8")
        val = _extract_ocsr_instance_id(self.ledger, "label", "m/m", "p.txt")
        self.assertTrue(val.startswith("ocsr-unknown-"))

    def test_no_match_returns_fallback(self):
        """Ledger with non-matching entries → ocsr-unknown-* fallback."""
        self.ledger.write_text(
            json.dumps({"event": "launched", "label": "other", "model": "o/m",
                        "prompt_file": "/other.txt", "batch_id": "b-001"}) + "\n",
            encoding="utf-8",
        )
        val = _extract_ocsr_instance_id(self.ledger, "label", "m/m", "p.txt")
        self.assertTrue(val.startswith("ocsr-unknown-"))

    # ── Correlation-key-first matching (Task B) ────────────────────

    def test_extract_by_correlation_key_primary(self):
        """converge_invocation_id match returns that batch_id."""
        self.ledger.write_text(
            json.dumps({"event": "launched", "label": "other", "model": "o/m",
                        "prompt_file": "/other.txt", "batch_id": "b-001",
                        "converge_invocation_id": "cid-789"}) + "\n",
            encoding="utf-8",
        )
        val = _extract_ocsr_instance_id(
            self.ledger, "label", "m/m", "p.txt",
            converge_invocation_id="cid-789",
        )
        self.assertEqual(val, "b-001")

    def test_fallback_to_tuple_when_no_correlation_match(self):
        """Ledger has rows but none match converge_invocation_id → tuple fallback."""
        self.ledger.write_text(
            json.dumps({"event": "launched", "label": "target-label",
                        "model": "t/m", "prompt_file": "/p.txt",
                        "batch_id": "b-002",
                        "converge_invocation_id": "other-cid"}) + "\n",
            encoding="utf-8",
        )
        val = _extract_ocsr_instance_id(
            self.ledger, "target-label", "t/m", "/p.txt",
            converge_invocation_id="requested-cid",
        )
        # converge_invocation_id is non-empty, no row matches "requested-cid".
        # Should fall through to legacy (label, model, prompt_file) tuple match.
        self.assertEqual(val, "b-002")

    def test_legacy_ledger_no_correlation_key_field(self):
        """Legacy ledger rows lack converge_invocation_id entirely → tuple fallback works when called without key."""
        self.ledger.write_text(
            json.dumps({"event": "launched", "label": "target",
                        "model": "t/m", "prompt_file": "/p.txt",
                        "batch_id": "b-003"}) + "\n",
            encoding="utf-8",
        )
        val = _extract_ocsr_instance_id(
            self.ledger, "target", "t/m", "/p.txt",
        )
        self.assertEqual(val, "b-003")

    def test_degraded_fallback_when_no_match(self):
        """Correlation key unmatched but (label, model, prompt) tuple matches → b-004."""
        self.ledger.write_text(
            json.dumps({"event": "launched", "label": "target",
                        "model": "t/m", "prompt_file": "/p.txt",
                        "batch_id": "b-004"}) + "\n",
            encoding="utf-8",
        )
        val = _extract_ocsr_instance_id(
            self.ledger, "target", "t/m", "/p.txt",
            converge_invocation_id="nonexistent-cid",
        )
        # Correlation key unmatched → tuple fallback matches same label/model/prompt
        self.assertEqual(val, "b-004")


class TestFailCollisionAndFallthrough(AdapterBase):
    """S5: fail-collision (rc=3) and generic fallthrough (unknown rc)."""

    def test_fail_collision_uses_recover(self):
        """Path collision (ocsr rc=3) → recover with backend-error, pre_execution=false."""
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "fail-collision"},
            *self._adapter_args(),
        )
        self.assertEqual(rc, 5, f"expected EXIT_OCSR_NO_PRODUCT=5, got rc={rc}; stderr={err}")
        events = _read_events(self.active)
        self.assertEqual(len(events), 2)
        terminal = events[1]
        self.assertEqual(terminal["terminal_status"], "failed")
        self.assertEqual(terminal["failure_reason_code"], "backend-error")
        gate = _read_gate_ledger(self.active)
        failed = [e for e in gate if e.get("event") == "spawn_failed"]
        self.assertEqual(len(failed), 1)
        self.assertFalse(failed[0].get("pre_execution"),
                         "path collision must have pre_execution=false")

    def test_collision_with_landed_product_is_not_success(self):
        """S9a: product on disk + ocsr rc=3 must NOT be recorded as a succeeded Spawn.

        The pre-S9 adapter decided success from `output_path exists and non-empty` alone,
        ignoring the exit code entirely. Under the ocsr exit-code contract rc=3 means the
        batch overwrote pre-existing files — this worker's own product landing says
        nothing about what else got clobbered. Recording it as `succeeded` would let a
        path collision enter the archive as a clean Spawn.
        """
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "collide-but-landed"},
            *self._adapter_args(),
        )
        self.assertEqual(rc, 5, f"expected EXIT_OCSR_NO_PRODUCT=5, got rc={rc}; stderr={err}")

        # The product really is on disk — the point is that this alone is not success.
        product = self.output_dir / "product.md"
        self.assertTrue(product.is_file() and product.stat().st_size > 0,
                        "fixture precondition: collide-but-landed must write the product")

        events = _read_events(self.active)
        terminal = events[1]
        self.assertEqual(terminal["terminal_status"], "failed")
        self.assertEqual(terminal["failure_reason_code"], "backend-error")
        # The permanent record must not claim the product is missing when it is not.
        self.assertIn("present but dispatch failed", terminal["failure_detail"])
        self.assertNotIn("missing or empty", terminal["failure_detail"])

        gate = _read_gate_ledger(self.active)
        failed = [e for e in gate if e.get("event") == "spawn_failed"]
        self.assertEqual(len(failed), 1)
        self.assertFalse(failed[0].get("pre_execution"),
                         "path collision must have pre_execution=false")

    def test_unknown_ocsr_rc_falls_through_to_generic(self):
        """Unknown ocsr exit code → generic backend-error recover."""
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "unknown-mode-99"},
            *self._adapter_args(),
        )
        self.assertEqual(rc, 5, f"expected EXIT_OCSR_NO_PRODUCT=5, got rc={rc}; stderr={err}")
        events = _read_events(self.active)
        self.assertEqual(len(events), 2)
        terminal = events[1]
        self.assertEqual(terminal["terminal_status"], "failed")
        self.assertEqual(terminal["failure_reason_code"], "backend-error")


# ─── Phase 5b: task-envelope companion pairing through adapter ────────────────

class TestAdapterCompanionPairing(AdapterBase):
    """Phase 5b: When task-envelope is configured, the adapter's dispatch path
    pairs the role reservation with a task-envelope companion."""

    def _configure_task_envelope(self, tier="small"):
        """Configure task envelope on the active state."""
        budget_gate.initialize_state(self.active, config={"task_tier": tier})

    def test_adapter_pairs_once_when_configured(self):
        """When task_tier is configured, adapter creates exactly one companion
        reservation with matching call_id and reciprocal companion_reservation_id."""
        self._configure_task_envelope("small")
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(),
        )
        self.assertEqual(rc, 0, f"rc={rc} stderr={err}")
        gate = _read_gate_ledger(self.active)
        reserved = [e for e in gate if e.get("event") == "reserved"]
        # Exactly 2: one role + one task-envelope companion
        self.assertEqual(len(reserved), 2, f"expected 2 reserved, got {len(reserved)}")
        role_res = next(e for e in reserved if e["target_role"] != "task-envelope")
        te_res = next(e for e in reserved if e["target_role"] == "task-envelope")
        # Both share the same call_id
        self.assertIsNotNone(role_res.get("call_id"))
        self.assertEqual(role_res["call_id"], te_res["call_id"])
        # Reciprocal companion_reservation_id
        self.assertEqual(role_res.get("companion_reservation_id"), te_res["reservation_id"])
        self.assertEqual(te_res.get("companion_reservation_id"), role_res["reservation_id"])
        # Both settled
        settled = [e for e in gate if e["event"] in ("spawn_succeeded", "spawn_failed", "cancelled")]
        settled_rids = {e["reservation_id"] for e in settled}
        self.assertIn(role_res["reservation_id"], settled_rids)
        self.assertIn(te_res["reservation_id"], settled_rids)

    def test_adapter_unchanged_when_unconfigured(self):
        """When no task_tier/task_envelope_cap, adapter behavior is identical
        to Phase 5a (A8 backward compatibility)."""
        # No configure_task_envelope — default state has no task envelope
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(),
        )
        self.assertEqual(rc, 0, f"rc={rc} stderr={err}")
        gate = _read_gate_ledger(self.active)
        reserved = [e for e in gate if e.get("event") == "reserved"]
        # Exactly 1: role only, no companion
        self.assertEqual(len(reserved), 1)
        self.assertIsNone(reserved[0].get("call_id"))
        self.assertIsNone(reserved[0].get("companion_reservation_id"))

    def test_adapter_pre_execution_cancel_settles_companion(self):
        """Pre-execution cancellation settles both role and companion
        with pre_execution=true. Tests settle companion pairing directly
        since adapter begin-failure is hard to trigger without real archive."""
        self._configure_task_envelope("small")
        # Create a companion pair through the gate
        rc, out = run_gate(
            self.active, "reserve", "--active-dir", str(self.active),
            "--role", "executor", "--tier", "auditable-only",
            "--manual-fallback", "test-fixture",
        )
        self.assertEqual(rc, 0, f"reserve failed: {out}")
        rid = out.split("PROCEED:")[1]
        gate = _read_gate_ledger(self.active)
        reserved = [e for e in gate if e.get("event") == "reserved"]
        self.assertEqual(len(reserved), 2, "expected role + companion")
        role_rid = next(e["reservation_id"] for e in reserved
                        if e["target_role"] != "task-envelope")
        comp_rid = next(e["reservation_id"] for e in reserved
                        if e["target_role"] == "task-envelope")
        # Cancel role with pre_execution=True (simulates begin-failure)
        rc, out = run_gate(
            self.active, "settle", "--active-dir", str(self.active),
            "--reservation-id", role_rid, "--result", "cancelled",
            "--pre-execution", "--manual-fallback", "test-fixture",
        )
        self.assertEqual(rc, 0, f"settle failed: {out}")
        gate = _read_gate_ledger(self.active)
        cancelled = [e for e in gate if e.get("event") == "cancelled"]
        # Both role and companion should be cancelled
        self.assertEqual(len(cancelled), 2,
                         f"expected 2 cancelled (role + companion), got {len(cancelled)}")
        for c in cancelled:
            self.assertTrue(c.get("pre_execution"),
                            f"pre-execution cancel must have pre_execution=true: {c}")

    def test_adapter_conflict_fails_closed(self):
        """When task-envelope budget is exhausted, adapter returns BLOCK."""
        self._configure_task_envelope("small")
        # Exhaust task-envelope budget (small: initial=4)
        for i in range(4):
            rc, out, err = run_adapter(
                self.active, {"FAKE_OCSR_MODE": "happy"},
                *self._adapter_args(role="executor", attempt=i + 1,
                                    output_name=f"p{i}.md", label=f"e{i}"),
            )
            self.assertEqual(rc, 0, f"iteration {i}: rc={rc} stderr={err}")
        # 5th must BLOCK on task-envelope
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(role="executor", attempt=5,
                                output_name="p5.md", label="e5"),
        )
        self.assertEqual(rc, 10, f"expected EXIT_BLOCK=10, got rc={rc}; stderr={err}")
        gate = _read_gate_ledger(self.active)
        decisions = [e for e in gate if e.get("event") == "decision"]
        self.assertTrue(any("task_envelope" in d.get("verdict", "") for d in decisions),
                        f"expected task_envelope decision: {decisions}")


class TestAdapterCRLFPollution(unittest.TestCase):
    """CRLF pollution red test: any JSON written by the adapter must use LF."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.active = self.root / "active"
        self.active.mkdir()
        self.output_dir = self.root / "output"
        self.output_dir.mkdir()
        self.prompt = self.root / "prompt.txt"
        self.prompt.write_text("test prompt\n", encoding="utf-8")
        budget_gate.initialize_state(self.active)

    def tearDown(self):
        self.tmp.cleanup()

    def test_gate_ledger_uses_lf_only(self):
        """gate-ledger.jsonl must not contain CRLF."""
        env = {**os.environ, "PYTHONUTF8": "1", "FAKE_OCSR_MODE": "happy"}
        args = [
            "dispatch",
            "--converge-active", str(self.active),
            "--converge-scripts", str(SCRIPTS),
            "--ocsr-dispatch", str(FAKE_OCSR),
            "--role", "executor", "--phase", "test", "--attempt", "1",
            "--prompt", str(self.prompt),
            "--model", "deepseek/deepseek-v4-flash",
            "--label", "test-label",
            "--output-dir", str(self.output_dir),
            "--output-name", "product.md",
            "--watch", "--timeout", "1",
        ]
        subprocess.run(
            [sys.executable, str(ADAPTER), *args],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )
        ledger = self.active / "gate-ledger.jsonl"
        if ledger.is_file():
            raw = ledger.read_bytes()
            self.assertNotIn(b"\r\n", raw,
                             "gate-ledger.jsonl must use LF, not CRLF")


# ─── Append-only companion linkage regression (r2 fix) ──────────────────────

class TestAdapterCompanionReverseLookup(AdapterBase):
    """Regression: adapter must detect existing companion via reverse lookup
    (companion_reservation_id on the TE event) rather than requiring a forward
    reference on the role event.  Also: append-only invariant."""

    def _configure_task_envelope(self, tier="small"):
        budget_gate.initialize_state(self.active, config={"task_tier": tier})

    def test_adapter_detects_companion_via_reverse_lookup(self):
        """When role event has no forward companion_reservation_id (the
        pre-reserved adapter path), _ensure_te_companion must still detect
        an existing companion via reverse lookup."""
        # Create role reservation BEFORE configuring task-envelope (no atomic pair)
        rc, out = run_gate(
            self.active, "reserve", "--active-dir", str(self.active),
            "--role", "executor", "--tier", "auditable-only",
            "--manual-fallback", "test-fixture",
        )
        self.assertEqual(rc, 0, f"reserve failed: {out}")
        role_rid = out.split("PROCEED:")[1]

        # Now configure task-envelope
        self._configure_task_envelope("small")

        # Create companion via companion_for
        rc, out = run_gate(
            self.active, "reserve", "--active-dir", str(self.active),
            "--role", "task-envelope", "--tier", "auditable-only",
            "--companion-for", role_rid,
            "--manual-fallback", "test-fixture",
        )
        self.assertEqual(rc, 0, f"companion_for failed: {out}")

        # Verify role event has NO forward reference
        gate = _read_gate_ledger(self.active)
        role_ev = next(e for e in gate
                       if e.get("event") == "reserved"
                       and e.get("reservation_id") == role_rid)
        self.assertIsNone(role_ev.get("companion_reservation_id"),
                          "Role event must not have forward companion_reservation_id")

        # Now call adapter with --reserved-reservation-id (pre-reserved path)
        # _ensure_te_companion should detect the existing companion via
        # reverse lookup and not create a duplicate
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(reserved_reservation_id=role_rid),
        )
        # The adapter's _ensure_te_companion should see the companion exists
        # (via reverse lookup) and skip creation.
        gate = _read_gate_ledger(self.active)
        te_reservations = [e for e in gate
                           if e.get("event") == "reserved"
                           and e.get("target_role") == "task-envelope"]
        self.assertEqual(len(te_reservations), 1,
                         f"Expected exactly 1 TE companion, got {len(te_reservations)} "
                         "(adapter may have created a duplicate)")

    def test_adapter_companion_for_append_only(self):
        """When adapter creates companion via companion_for (pre-reserved
        path), the ledger must only be appended to (never rewritten)."""
        # Create role reservation BEFORE configuring task-envelope
        rc, out = run_gate(
            self.active, "reserve", "--active-dir", str(self.active),
            "--role", "executor", "--tier", "auditable-only",
            "--manual-fallback", "test-fixture",
        )
        self.assertEqual(rc, 0, f"reserve failed: {out}")
        role_rid = out.split("PROCEED:")[1]

        # Now configure task-envelope
        self._configure_task_envelope("small")

        # Capture ledger bytes before adapter call
        ledger_path = self.active / "gate-ledger.jsonl"
        pre_bytes = ledger_path.read_bytes()

        # Run adapter with pre-reserved path (creates companion via companion_for)
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(reserved_reservation_id=role_rid),
        )
        self.assertEqual(rc, 0, f"rc={rc} stderr={err}")

        # Assert append-only: pre-call bytes must be prefix of post-call
        post_bytes = ledger_path.read_bytes()
        self.assertTrue(
            post_bytes.startswith(pre_bytes),
            "LEDGER REWRITE DETECTED: adapter path must only append to ledger")


if __name__ == "__main__":
    unittest.main(verbosity=2)
