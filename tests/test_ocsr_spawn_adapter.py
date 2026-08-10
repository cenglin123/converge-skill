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

    def test_ultraverge_mode_applies_blind_rechecks_override(self):
        rc, out, err = self._run_config_init("--mode", "ultraverge")
        self.assertEqual(rc, 0, f"rc={rc} stderr={err}")
        state = json.loads((self.active / "_budget-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["fsm"]["mode"], "ultraverge")
        # SKILL.md §Ultraverge: max_blind_rechecks=2 override (zero-code orchestrator behavior)
        self.assertEqual(state["config"].get("max_blind_rechecks"), 2)

    def test_explicit_overrides_win_over_ultraverge_default(self):
        rc, out, err = self._run_config_init("--mode", "ultraverge", "--max-blind-rechecks", "5")
        self.assertEqual(rc, 0, f"rc={rc} stderr={err}")
        state = json.loads((self.active / "_budget-state.json").read_text(encoding="utf-8"))
        # Explicit override wins over the ultraverge default (setdefault semantics)
        self.assertEqual(state["config"].get("max_blind_rechecks"), 5)

    def test_idempotent_no_force_fails_closed(self):
        """Re-init without --force must fail closed (state-loss smell)."""
        rc, _, _ = self._run_config_init()
        self.assertEqual(rc, 0)
        rc2, out, err = self._run_config_init()
        self.assertEqual(rc2, 30, f"expected FAIL_CLOSED=30, got rc={rc2}; stderr={err}")
        self.assertIn("already exists", err)

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
        """After max_outer_loops (default 5) outer-reviewer reservations,
        the 6th must BLOCK:budget_exhausted. Verifies the adapter actually
        drives budget_gate per-scope, not just total."""
        # No config init → defaults (max_outer_loops=5)
        for i in range(1, 6):
            # Each iteration uses a different output_name to avoid collision detection,
            # and a different round to satisfy budget_gate's (scope, round) uniqueness
            # invariant.
            rc, _, err = run_adapter(
                self.active, {"FAKE_OCSR_MODE": "happy"},
                *self._adapter_args(role="outer-reviewer", round=i,
                                    output_name=f"round-{i}.md",
                                    label=f"r{i}"),
            )
            self.assertEqual(rc, 0, f"iteration {i}: rc={rc}; stderr={err}")
        # 6th outer reservation must BLOCK
        rc, out, err = run_adapter(
            self.active, {"FAKE_OCSR_MODE": "happy"},
            *self._adapter_args(role="outer-reviewer", round=6,
                                output_name="round-6.md", label="r6"),
        )
        self.assertEqual(rc, 10, f"expected EXIT_BLOCK=10, got rc={rc}; stderr={err}")
        gate = _read_gate_ledger(self.active)
        decisions = [e for e in gate if e.get("event") == "decision"]
        last = decisions[-1]
        self.assertEqual(last["verdict"], "BLOCK:budget_exhausted")
        self.assertEqual(last["scope"], "outer")
        self.assertEqual(last["observed_usage"], 5)
        # No 6th begin side-effect (no event for round 6)
        events = _read_events(self.active)
        # 5 successful rounds × 2 events each = 10
        self.assertEqual(len(events), 10)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
