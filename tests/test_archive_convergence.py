import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import threading
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


class ArchiveContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.active = self.root / "active" / "case"
        self.active.mkdir(parents=True)
        (self.active / "plan.md").write_text("# Plan\n", encoding="utf-8", newline="\n")

    def _append_ledger_pair(self, rid, round_number, instance_id, event="spawn_succeeded"):
        path = self.active / "gate-ledger.jsonl"
        prior = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        issued = sum(1 for line in prior if json.loads(line).get("event") == "reserved")
        reserve = {
            "event": "reserved", "reservation_id": rid, "ts": f"2026-07-12T00:00:{issued * 2:02d}+00:00",
            "target_round": round_number, "target_role": "outer-reviewer", "consumes": "outer",
            "counts_before": {"outer": issued, "blind": 0, "ultraverge": 0, "total": issued},
            "ceilings": {"outer": 5, "blind": 1, "ultraverge": 3, "total": 42},
            "extension_id": None, "tier": "auditable-only",
        }
        settle = {"event": event, "reservation_id": rid,
                  "ts": f"2026-07-12T00:00:{issued * 2 + 1:02d}+00:00"}
        if event == "spawn_succeeded":
            settle["instance_id"] = instance_id
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(reserve) + "\n" + json.dumps(settle) + "\n")

    def test_event_lock_liveness_probe_never_uses_os_kill(self):
        from archive_contract.capture import _owner_process_liveness

        source = (SCRIPTS / "archive_contract" / "capture.py").read_text(encoding="utf-8")
        self.assertNotIn("os.kill", source)
        self.assertEqual(_owner_process_liveness(os.getpid()), "alive")

    def test_event_lock_unknown_owner_fails_closed(self):
        from archive_contract.capture import EventLock
        from archive_contract.model import ArchiveError

        lock_path = self.active / ".archive-event.lock"
        lock_path.write_text(json.dumps({
            "pid": os.getpid() + 10_000_000,
            "nonce": "owner",
            "started_at": "2026-07-12T00:00:00+00:00",
        }), encoding="utf-8")
        with mock.patch("archive_contract.capture._owner_process_liveness", return_value="unknown"):
            with self.assertRaises(ArchiveError) as caught:
                with EventLock(self.active):
                    self.fail("unknown owner must not be reclaimed")
        self.assertEqual(caught.exception.code, "lock-conflict")
        self.assertTrue(lock_path.exists())

    def test_schema_dispatch_five_states(self):
        from archive_contract.model import schema_state

        self.assertEqual(schema_state(self.active)[0], "missing")
        (self.active / "manifest.json").write_text("{", encoding="utf-8")
        self.assertEqual(schema_state(self.active)[0], "malformed")
        (self.active / "manifest.json").write_text("{}\n", encoding="utf-8")
        self.assertEqual(schema_state(self.active), ("unsupported", "unversioned"))
        (self.active / "manifest.json").write_text(
            '{"schema_id":"converge.archive","schema_version":"9.0"}\n', encoding="utf-8"
        )
        self.assertEqual(schema_state(self.active), ("unsupported", "newer-version"))

    def test_append_only_lifecycle_and_global_sequence(self):
        from archive_contract.capture import begin_invocation, complete_invocation

        started = begin_invocation(
            self.active, invocation_kind="spawn", role="reviewer", phase="review",
            round_number=1, attempt=1, reservation_id="r1",
            requested_provider="openai", requested_model="configured-model",
        )
        terminal = complete_invocation(
            self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="instance-1", receipt="receipt-1", settlement_ref="settle-1",
            resolved_provider=None, resolved_model=None,
            evidence_level="configured", resolution_source="agent_config",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"ok",
        )
        self.assertEqual((started["sequence"], terminal["sequence"]), (1, 2))
        self.assertEqual(len(list((self.active / "evidence" / "events").glob("*.json"))), 2)
        with self.assertRaises(FileExistsError):
            target = self.active / "evidence" / "events" / f"00000001-{started['event_id']}.json"
            target.open("xb")

    def test_metadata_only_does_not_persist_bytes(self):
        from archive_contract.capture import capture_artifact

        source = self.root / "workspace" / "a.txt"
        source.parent.mkdir()
        source.write_bytes(b"secret-ish")
        event = capture_artifact(
            self.active, source, artifact_id="a1", revision_id="r1",
            evidence_mode="metadata-only", workspace_root=source.parent,
            workspace_id="w1",
        )
        self.assertEqual(event["reproduction_capability"], "identity-only")
        self.assertFalse((self.active / "evidence" / "artifacts" / "a1" / "snapshot").exists())

    def test_import_boundaries(self):
        sources = {p.name: p.read_text(encoding="utf-8") for p in (SCRIPTS / "archive_contract").glob("*.py")}
        self.assertNotIn("archive_contract.capture", sources["model.py"])
        self.assertNotIn("archive_contract.transaction", sources["model.py"])
        self.assertNotIn("archive_contract.presentation", sources["model.py"])
        self.assertNotIn("archive_contract.presentation", sources["capture.py"])
        self.assertNotIn("archive_contract.presentation", sources["transaction.py"])

    def test_cli_missing_manifest_diagnostic_contract(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "archive_convergence.py"), "check", str(self.active), "--format", "json"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertNotEqual(proc.returncode, 0)
        item = json.loads(proc.stdout)["diagnostics"][0]
        self.assertEqual(set(item), {"code", "summary", "path", "next_action"})

    def test_archive_check_move_and_tamper(self):
        from archive_contract.capture import begin_invocation, complete_invocation, record_terminal_decision

        self._append_ledger_pair("r1", 1, "review-1")
        started = begin_invocation(
            self.active, invocation_kind="spawn", role="outer-reviewer", phase="final-review",
            round_number=1, attempt=1, reservation_id="r1", requested_provider=None, requested_model=None,
        )
        terminal = complete_invocation(
            self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="review-1", receipt="receipt-1", settlement_ref="gate-ledger.jsonl:r1",
            resolved_provider=None, resolved_model=None, evidence_level="unavailable",
            resolution_source="none", resolution_reason_code="backend-does-not-expose",
            output_bytes=b"verdict: executable\n",
        )
        decision = record_terminal_decision(self.active, {
            "decision_type": "reviewer-verdict", "reviewer_event_id": terminal["event_id"],
            "review_kind": "fresh", "verdict": "executable", "verdict_output_ref": terminal["event_id"],
        })
        marker = f"terminal_decision_event_id: {decision['event_id']}\nterminal_decision_value: executable\n"
        (self.active / "round-1.md").write_text(marker, encoding="utf-8", newline="\n")
        (self.active / "retrospective.md").write_text(marker, encoding="utf-8", newline="\n")
        done = self.root / "done"
        done.mkdir()
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "archive_convergence.py"), "archive",
             str(self.root / "active"), str(done), "case"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        archived = done / "case"
        self.assertFalse(self.active.exists())
        check = subprocess.run(
            [sys.executable, str(SCRIPTS / "archive_convergence.py"), "check", str(archived), "--format", "json"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        renamed = done / "renamed"
        archived.rename(renamed)
        self.assertEqual(subprocess.run(
            [sys.executable, str(SCRIPTS / "archive_convergence.py"), "check", str(renamed)],
            capture_output=True, text=True, encoding="utf-8",
        ).returncode, 0)
        (renamed / "plan.md").write_bytes(b"tampered\n")
        self.assertNotEqual(subprocess.run(
            [sys.executable, str(SCRIPTS / "archive_convergence.py"), "check", str(renamed)],
            capture_output=True, text=True, encoding="utf-8",
        ).returncode, 0)

    def test_reopen_preserves_parent_manifest_and_appends_revision(self):
        from archive_contract.capture import begin_invocation, complete_invocation, record_terminal_decision

        self._append_ledger_pair("r1", 1, "i1")
        first_start = begin_invocation(self.active, invocation_kind="spawn", role="outer-reviewer",
            phase="final-review", round_number=1, attempt=1, reservation_id="r1")
        first_terminal = complete_invocation(self.active, first_start["invocation_id"],
            terminal_status="succeeded", instance_id="i1", receipt="p1", settlement_ref="gate-ledger.jsonl:r1",
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"v1")
        first_decision = record_terminal_decision(self.active, {
            "decision_type": "reviewer-verdict", "reviewer_event_id": first_terminal["event_id"],
            "review_kind": "fresh", "verdict": "v1", "verdict_output_ref": first_terminal["event_id"],
        })
        marker = f"terminal_decision_event_id: {first_decision['event_id']}\nterminal_decision_value: v1\n"
        (self.active / "round-1.md").write_text(marker, encoding="utf-8", newline="\n")
        (self.active / "retrospective.md").write_text(marker, encoding="utf-8", newline="\n")
        done = self.root / "done"; done.mkdir()
        cli = str(SCRIPTS / "archive_convergence.py")
        self.assertEqual(subprocess.run([sys.executable, cli, "archive", str(self.root / "active"), str(done), "case"], capture_output=True).returncode, 0)
        old_manifest = (done / "case" / "manifest.json").read_bytes()
        self.assertEqual(subprocess.run([sys.executable, cli, "reopen", str(self.root / "active"), str(done), "case"], capture_output=True).returncode, 0)
        reopened = self.root / "active" / "case"
        self.assertEqual((reopened / "evidence" / "revisions" / "r1" / "manifest.json").read_bytes(), old_manifest)
        self.active = reopened
        self._append_ledger_pair("r2", 2, "i2")
        second_start = begin_invocation(reopened, invocation_kind="spawn", role="outer-reviewer",
            phase="revision-review", round_number=2, attempt=1, reservation_id="r2")
        second_terminal = complete_invocation(reopened, second_start["invocation_id"],
            terminal_status="succeeded", instance_id="i2", receipt="p2", settlement_ref="gate-ledger.jsonl:r2",
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"v2")
        second_decision = record_terminal_decision(reopened, {
            "decision_type": "reviewer-verdict", "reviewer_event_id": second_terminal["event_id"],
            "review_kind": "fresh", "verdict": "v2", "verdict_output_ref": second_terminal["event_id"],
            "supersedes_decision_event_id": first_decision["event_id"],
        })
        marker2 = f"terminal_decision_event_id: {second_decision['event_id']}\nterminal_decision_value: v2\n"
        (reopened / "round-2.md").write_text(marker2, encoding="utf-8", newline="\n")
        (reopened / "retrospective.md").write_text(marker2, encoding="utf-8", newline="\n")
        self.assertEqual(subprocess.run([sys.executable, cli, "archive", str(self.root / "active"), str(done), "case"], capture_output=True).returncode, 0)
        manifest = json.loads((done / "case" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["revision_id"], "r2")
        self.assertEqual(manifest["parent_revision"]["revision_id"], "r1")

    def test_plan_time_bootstrap_fixture_imports_raw_evidence_without_root_clutter(self):
        import archive_convergence

        target = self.root / "bootstrap"
        target.mkdir()
        reservations = [
            {
                "event": "reserved", "reservation_id": "uv-r1", "ts": "2026-07-12T00:00:00+00:00",
                "target_round": 1, "target_role": "ultraverge-initial", "consumes": "ultraverge",
                "counts_before": {"outer": 0, "blind": 0, "ultraverge": 0, "total": 0},
                "ceilings": {"outer": 5, "blind": 1, "ultraverge": 3, "total": 42},
                "extension_id": None, "tier": "auditable-only",
            },
            {"event": "spawn_succeeded", "reservation_id": "uv-r1",
             "ts": "2026-07-12T00:00:01+00:00", "instance_id": "uv-instance"},
            {
                "event": "reserved", "reservation_id": "plan-amend-r1", "ts": "2026-07-12T00:00:02+00:00",
                "target_round": None, "target_role": "executor", "consumes": "none",
                "counts_before": {"outer": 0, "blind": 0, "ultraverge": 1, "total": 1},
                "ceilings": {"outer": 5, "blind": 1, "ultraverge": 3, "total": 42},
                "extension_id": None, "tier": "auditable-only",
            },
            {"event": "spawn_succeeded", "reservation_id": "plan-amend-r1",
             "ts": "2026-07-12T00:00:03+00:00", "instance_id": "executor-instance"},
        ]
        (target / "gate-ledger.jsonl").write_text(
            "".join(json.dumps(event) + "\n" for event in reservations), encoding="utf-8", newline="\n")
        for name in ("_orchestrator-state.md", "design-review.md", "plan.md", "round-1.md"):
            (target / name).write_text(f"# {name}\n", encoding="utf-8", newline="\n")
        (target / "_budget-state.json").write_text("{}\n", encoding="utf-8", newline="\n")
        (target / "uv-init-1.md").write_text("initial review\n", encoding="utf-8", newline="\n")
        (target / "uv-init-1-inner-1.md").write_text("inner review\n", encoding="utf-8", newline="\n")
        (target / "plan-amendment-report.md").write_text("amendment\n", encoding="utf-8", newline="\n")
        (target / "reference-materials.md").write_text("reference\n", encoding="utf-8", newline="\n")
        archive_convergence._bootstrap_import(target)
        self.assertTrue((target / "evidence" / "events").is_dir())
        self.assertFalse(any(target.glob("uv-init-*.md")))
        self.assertFalse((target / "plan-amendment-report.md").exists())
        self.assertFalse((target / "reference-materials.md").exists())
        self.assertTrue({p.name for p in target.iterdir()} <= {
            "_budget-state.json", "_orchestrator-state.md", "design-review.md",
            "gate-ledger.jsonl", "plan.md", "round-1.md", "evidence",
        })

    def test_strict_ledger_bidirectional_binding(self):
        from archive_contract.capture import begin_invocation, complete_invocation
        from archive_contract.model import ArchiveError, load_events, validate_ledger

        reserve = {
            "event": "reserved", "reservation_id": "r1", "ts": "2026-07-12T00:00:00+00:00",
            "target_round": 1, "target_role": "outer-reviewer", "consumes": "outer",
            "counts_before": {"outer": 0, "blind": 0, "ultraverge": 0, "total": 0},
            "ceilings": {"outer": 5, "blind": 1, "ultraverge": 3, "total": 20},
            "extension_id": None, "tier": "auditable-only",
        }
        settle = {"event": "spawn_succeeded", "reservation_id": "r1", "ts": "2026-07-12T00:00:01+00:00", "instance_id": "i1"}
        (self.active / "gate-ledger.jsonl").write_text(
            json.dumps(reserve) + "\n" + json.dumps(settle) + "\n", encoding="utf-8", newline="\n"
        )
        started = begin_invocation(self.active, invocation_kind="spawn", role="outer-reviewer",
            phase="review", round_number=1, attempt=1, reservation_id="r1")
        complete_invocation(self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="i1", settlement_ref="gate-ledger.jsonl:r1", evidence_level="unavailable",
            resolution_source="none", resolution_reason_code="backend-does-not-expose", output_bytes=b"ok")
        validate_ledger(self.active, load_events(self.active))
        settle["instance_id"] = "different"
        (self.active / "gate-ledger.jsonl").write_text(
            json.dumps(reserve) + "\n" + json.dumps(settle) + "\n", encoding="utf-8", newline="\n"
        )
        with self.assertRaises(ArchiveError):
            validate_ledger(self.active, load_events(self.active))

    def test_provenance_matrix_rejects_configured_as_resolved(self):
        from archive_contract.capture import begin_invocation, complete_invocation
        from archive_contract.model import ArchiveError

        started = begin_invocation(self.active, invocation_kind="spawn", role="reviewer",
            phase="review", round_number=1, attempt=1, reservation_id="r1")
        with self.assertRaises(ArchiveError):
            complete_invocation(self.active, started["invocation_id"], terminal_status="succeeded",
                resolved_model="not-observed", evidence_level="configured", resolution_source="agent_config",
                resolution_reason_code="backend-does-not-expose", output_bytes=b"ok")

    def test_redacted_and_exact_capture_have_distinct_capabilities(self):
        from archive_contract.capture import capture_artifact

        workspace = self.root / "ws"; workspace.mkdir()
        exact_source = workspace / "exact.txt"; exact_source.write_bytes(b"exact")
        redacted_source = workspace / "redacted.txt"; redacted_source.write_bytes(b"token=secret")
        exact = capture_artifact(self.active, exact_source, artifact_id="exact", revision_id="r1",
            evidence_mode="exact", workspace_root=workspace, workspace_id="w")
        redacted = capture_artifact(self.active, redacted_source, artifact_id="redacted", revision_id="r1",
            evidence_mode="redacted", workspace_root=workspace, workspace_id="w", redacted_bytes=b"token=[redacted]")
        self.assertEqual(exact["reproduction_capability"], "snapshot")
        self.assertEqual(redacted["reproduction_capability"], "redacted-copy")
        self.assertNotEqual(redacted["sha256"], redacted["snapshot"]["sha256"])

    def test_path_and_locator_closed_unions(self):
        from archive_contract.model import ArchiveError, normalize_relative, validate_locator

        for value in ("../escape", "C:/absolute", "name:stream", "CON/file", "trailing./x"):
            with self.assertRaises(ArchiveError, msg=value):
                normalize_relative(value)
        validate_locator({"kind": "workspace-relative", "workspace_id": "w", "path": "中文/文件.txt"})
        with self.assertRaises(ArchiveError):
            validate_locator({"kind": "external", "display_locator": "C:\\secret.txt", "portable": False, "authorization_ref": "u1"})

    def test_terminal_decision_union_rejects_design_review(self):
        from archive_contract.capture import record_terminal_decision
        from archive_contract.model import ArchiveError

        with self.assertRaises(ArchiveError):
            record_terminal_decision(self.active, {"decision_type": "design-review", "invocation_event_id": "x"})

    def test_scan_is_byte_for_byte_read_only(self):
        from archive_contract.presentation import scan

        done = self.root / "done"; legacy = done / "legacy"; legacy.mkdir(parents=True)
        (legacy / "old.md").write_bytes(b"legacy\n")
        before = (legacy / "old.md").read_bytes()
        result = scan(done)
        self.assertEqual(result[0]["state"], "missing")
        self.assertEqual((legacy / "old.md").read_bytes(), before)

    def test_concurrent_begin_never_corrupts_sequence(self):
        from archive_contract.capture import begin_invocation
        from archive_contract.model import ArchiveError, load_events

        outcomes = []
        barrier = threading.Barrier(3)
        def worker(number):
            barrier.wait()
            try:
                outcomes.append(begin_invocation(self.active, invocation_kind="spawn", role="worker",
                    phase="parallel", round_number=number, attempt=1, reservation_id=f"r{number}"))
            except ArchiveError as exc:
                outcomes.append(exc)
        threads = [threading.Thread(target=worker, args=(number,)) for number in (1, 2)]
        for thread in threads: thread.start()
        barrier.wait()
        for thread in threads: thread.join()
        events = load_events(self.active)
        self.assertEqual([event["sequence"] for event in events], list(range(1, len(events) + 1)))
        self.assertEqual(len(outcomes), 2)
        self.assertTrue(all(isinstance(item, (dict, ArchiveError)) for item in outcomes))

    def test_hardlink_artifact_is_rejected(self):
        from archive_contract.capture import capture_artifact
        from archive_contract.model import ArchiveError

        workspace = self.root / "hardlinks"; workspace.mkdir()
        source = workspace / "a.txt"; alias = workspace / "b.txt"
        source.write_bytes(b"same inode")
        try:
            os.link(source, alias)
        except OSError as exc:
            self.skipTest(f"hardlinks unavailable: {exc}")
        with self.assertRaises(ArchiveError):
            capture_artifact(self.active, source, artifact_id="hard", revision_id="r1",
                workspace_root=workspace, workspace_id="w")

    def test_symlink_or_reparse_tree_is_rejected_or_explicitly_skipped(self):
        from archive_contract.model import ArchiveError, ensure_safe_tree

        target = self.active / "target.txt"; target.write_bytes(b"target")
        link = self.active / "link.txt"
        try:
            os.symlink(target, link)
        except OSError as exc:
            self.skipTest(f"Windows symlink/reparse creation unavailable at current privilege: {exc}")
        with self.assertRaises(ArchiveError):
            ensure_safe_tree(self.active)

    def test_b1_artifact_identifier_escape_is_rejected_without_side_effects(self):
        from archive_contract.capture import capture_artifact
        from archive_contract.model import ArchiveError

        workspace = self.root / "workspace"; workspace.mkdir()
        source = workspace / "artifact.txt"; source.write_bytes(b"reviewed")
        before = {p.relative_to(self.root).as_posix() for p in self.root.rglob("*")}
        with self.assertRaises(ArchiveError):
            capture_artifact(
                self.active, source, artifact_id="../../../escaped", revision_id="r1",
                evidence_mode="exact", workspace_root=workspace, workspace_id="w",
            )
        after = {p.relative_to(self.root).as_posix() for p in self.root.rglob("*")}
        self.assertEqual(after, before)
        self.assertFalse((self.root / "escaped" / "snapshot").exists())

    def test_b1_external_authorization_is_checked_before_source_read(self):
        from archive_contract.capture import capture_artifact
        from archive_contract.model import ArchiveError

        source = self.root / "unreadable-external.txt"
        source.write_bytes(b"must not be read")
        original = Path.open

        def guarded_open(path, *args, **kwargs):
            if Path(path) == source:
                raise AssertionError("source was read before authorization")
            return original(path, *args, **kwargs)

        with mock.patch.object(Path, "open", guarded_open):
            with self.assertRaises(ArchiveError) as caught:
                capture_artifact(self.active, source, artifact_id="external", revision_id="r1")
        self.assertEqual(caught.exception.code, "external-authorization")
        self.assertFalse((self.active / "evidence").exists())

    def test_r3_b1_evidence_parent_symlink_cannot_escape_archive(self):
        from archive_contract.capture import begin_invocation
        from archive_contract.model import ArchiveError
        outside = self.root / "outside"; outside.mkdir()
        evidence = self.active / "evidence"
        try:
            os.symlink(outside, evidence, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"directory symlink unavailable: {exc}")
        with self.assertRaises(ArchiveError):
            begin_invocation(self.active, invocation_kind="spawn", role="worker", phase="x",
                round_number=1, attempt=1, reservation_id="r1")
        self.assertEqual(list(outside.rglob("*")), [])

    def test_r3_b1_workspace_containment_precedes_source_open(self):
        from archive_contract.capture import capture_artifact
        from archive_contract.model import ArchiveError
        workspace = self.root / "workspace"; workspace.mkdir()
        source = self.root / "outside.txt"; source.write_bytes(b"outside")
        original = Path.open
        def guarded(path, *args, **kwargs):
            if Path(path) == source:
                raise AssertionError("outside source opened before containment")
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", guarded):
            with self.assertRaises(ArchiveError) as caught:
                capture_artifact(self.active, source, artifact_id="a", revision_id="r1",
                    workspace_root=workspace, workspace_id="w")
        self.assertEqual(caught.exception.code, "artifact-outside-workspace")

    def test_b2_spawn_requires_reservation_before_event_creation(self):
        from archive_contract.capture import begin_invocation
        from archive_contract.model import ArchiveError

        with self.assertRaises(ArchiveError) as caught:
            begin_invocation(self.active, invocation_kind="spawn", role="reviewer",
                             phase="review", round_number=1, attempt=1)
        self.assertEqual(caught.exception.code, "spawn-reservation-required")
        self.assertFalse((self.active / "evidence").exists())

    def test_b2_worker_cannot_own_reviewer_verdict(self):
        from archive_contract.model import ArchiveError, validate_event_graph

        events = self._minimal_event_graph(role="worker")
        with self.assertRaises(ArchiveError) as caught:
            validate_event_graph(events)
        self.assertEqual(caught.exception.code, "decision-reviewer-authority")

    def test_b2_continue_terminal_must_use_parent_instance(self):
        from archive_contract.model import ArchiveError, validate_event_graph

        events = self._minimal_event_graph(role="reviewer", include_decision=False)
        spawn_start, spawn_terminal = events[:2]
        cont_start = self._event("invocation-started", 3, invocation_id="00000000-0000-4000-8000-000000000103",
            invocation_kind="continue", role="reviewer", phase="inner", round=1, attempt=2,
            parent_event_id=spawn_start["event_id"], parent_instance_id="instance-1", reservation_id=None,
            started_at="2026-07-12T00:00:02+00:00", requested_provider=None, requested_model=None,
            prompt_evidence=self._evidence(b""))
        cont_terminal = self._event("invocation-terminal", 4, invocation_id=cont_start["invocation_id"],
            started_event_id=cont_start["event_id"], completed_at="2026-07-12T00:00:03+00:00",
            terminal_status="succeeded", instance_id="different-instance", receipt="receipt-2",
            settlement_ref=None, resolved_provider=None, resolved_model=None, resolved_family=None,
            backend=None, backend_version=None, host_evidence_ref=None, evidence_level="unavailable",
            resolution_source="none", resolution_reason_code="backend-does-not-expose",
            output_evidence=self._evidence(b"ok"), failure_reason_code=None, failure_detail=None,
            legacy_source_path=None)
        with self.assertRaises(ArchiveError) as caught:
            validate_event_graph([spawn_start, spawn_terminal, cont_start, cont_terminal])
        self.assertEqual(caught.exception.code, "continue-instance-conflict")

    def test_b3_observed_without_bound_host_evidence_is_rejected(self):
        from archive_contract.model import ArchiveError, validate_event

        event = self._minimal_event_graph(role="reviewer", include_decision=False)[1]
        event.update({"evidence_level": "observed", "resolution_source": "host_receipt",
                      "resolution_reason_code": None, "receipt": None,
                      "resolved_provider": None, "resolved_model": None, "resolved_family": None})
        with self.assertRaises(ArchiveError) as caught:
            validate_event(event)
        self.assertEqual(caught.exception.code, "provenance-host-evidence")

    def test_r3_b3_failed_before_resolution_reason_rejected_on_success(self):
        from archive_contract.model import ArchiveError, validate_event
        event = self._minimal_event_graph(role="reviewer", include_decision=False)[1]
        event.update({"evidence_level": "configured", "resolution_source": "agent_config",
                      "resolution_reason_code": "invocation-failed-before-resolution"})
        with self.assertRaises(ArchiveError) as caught:
            validate_event(event)
        self.assertEqual(caught.exception.code, "provenance-reason")

    def test_r3_b4_owner_scalar_types_fail_with_archive_error(self):
        from archive_contract.model import ArchiveError, validate_event
        for field, value in (("reservation_id", {"bad": 1}), ("requested_provider", {"bad": 1}),
                             ("requested_model", ["bad"])):
            event = self._minimal_event_graph(role="reviewer", include_decision=False)[0]
            event[field] = value
            with self.assertRaises(ArchiveError, msg=field):
                validate_event(event)

    def test_r3_b2_user_decision_requires_canonical_message_and_exact_degradations(self):
        from archive_contract.model import ArchiveError, validate_event_graph
        events = self._minimal_event_graph(role="reviewer", include_decision=False)
        events.append(self._event("terminal-decision", 3, decision_type="user-decision",
            generated_at="2026-07-12T00:00:02+00:00", decision_kind="accept-terminal-b",
            user_quote="accept", source_ref="fabricated:missing",
            presented_degradations=["fabricated"], accepted_state="anything",
            supersedes_decision_event_id=None))
        with self.assertRaises(ArchiveError):
            validate_event_graph(events)

    def test_r3_b2_user_decision_binds_prior_message_and_current_degradations(self):
        from archive_contract.model import validate_event, validate_event_graph
        events = self._minimal_event_graph(role="reviewer", include_decision=False)
        message = self._event("user-message", 3, host_message_id="host-42", user_quote="accept",
            recorded_at="2026-07-12T00:00:02+00:00")
        decision = self._event("terminal-decision", 4, decision_type="user-decision",
            generated_at="2026-07-12T00:00:03+00:00", decision_kind="accept-terminal-b",
            user_quote="accept", source_ref=message["event_id"],
            presented_degradations=["model-provenance:unavailable"],
            accepted_state="accepted-degraded-result", supersedes_decision_event_id=None)
        for event in (*events, message, decision):
            validate_event(event)
        validate_event_graph([*events, message, decision])

    def test_b4_unknown_event_field_is_rejected(self):
        from archive_contract.model import ArchiveError, validate_event

        event = self._minimal_event_graph(role="reviewer", include_decision=False)[0]
        event["unowned_fact"] = "silently accepted today"
        with self.assertRaises(ArchiveError) as caught:
            validate_event(event)
        self.assertEqual(caught.exception.code, "event-fields")

    def test_b4_orphan_blob_is_imported_as_auxiliary_evidence_not_an_owner_fact(self):
        # Behavior deliberately changed by the Phase 5 auxiliary-evidence addendum
        # (orchestrator-directed extension, "契约端扩展"): a file under `evidence/` whose top
        # segment is not one of the reserved event-derived subdirectories (events/,
        # invocations/, artifacts/, revisions/) is no longer a fatal `evidence-orphan` — it is
        # imported, hashed, and disclosed as `auxiliary_evidence`, but it still never becomes
        # an event-owned fact (not in `blobs`, not referenced by any invocation/artifact).
        from archive_contract.model import project_manifest

        events = self.active / "evidence" / "events"; events.mkdir(parents=True)
        orphan = self.active / "evidence" / "orphan.txt"; orphan.write_text("orphan", encoding="utf-8")
        manifest = project_manifest(self.active)
        self.assertEqual(manifest["blobs"], [])
        self.assertEqual([item["path"] for item in manifest.get("auxiliary_evidence", [])], ["evidence/orphan.txt"])

    def test_b5_concurrent_complete_creates_exactly_one_terminal(self):
        from archive_contract.capture import begin_invocation, complete_invocation
        from archive_contract.model import ArchiveError, load_events

        started = begin_invocation(self.active, invocation_kind="spawn", role="reviewer",
            phase="review", round_number=1, attempt=1, reservation_id="r1")
        barrier = threading.Barrier(3); outcomes = []
        def finish(number):
            barrier.wait()
            try:
                outcomes.append(complete_invocation(self.active, started["invocation_id"],
                    terminal_status="succeeded", instance_id="i1", receipt=f"receipt-{number}",
                    settlement_ref="gate-ledger.jsonl:r1", evidence_level="unavailable",
                    resolution_source="none", resolution_reason_code="backend-does-not-expose",
                    output_bytes=f"out-{number}".encode()))
            except ArchiveError as exc:
                outcomes.append(exc)
        threads = [threading.Thread(target=finish, args=(n,)) for n in (1, 2)]
        for thread in threads: thread.start()
        barrier.wait()
        for thread in threads: thread.join()
        terminals = [e for e in load_events(self.active) if e["event_type"] == "invocation-terminal"]
        self.assertEqual(len(terminals), 1)
        self.assertEqual(sum(isinstance(x, ArchiveError) for x in outcomes), 1)

    def test_b6_check_preserves_first_validator_diagnostic(self):
        from archive_contract.presentation import check_view

        (self.active / "manifest.json").write_text(
            '{"schema_id":"converge.archive","schema_version":"1.0"}\n', encoding="utf-8")
        diagnostic = check_view(self.active)["diagnostics"][0]
        self.assertNotEqual(diagnostic["summary"], "Recognized v1 archive fails its integrity closure.")

    def test_b6_pre_push_is_nul_safe_and_checks_any_done_change(self):
        hook = (SCRIPTS / "hooks" / "pre-push").read_text(encoding="utf-8")
        self.assertNotIn("for path in $changed", hook)
        invocation = '"$python_exe" "$top/scripts/archive_convergence.py" check-push-range'
        self.assertEqual(hook.count(invocation), 3)
        self.assertNotIn('"$top/scripts/archive_convergence.py" --check-push-range', hook)
        cli = (SCRIPTS / "archive_convergence.py").read_text(encoding="utf-8")
        self.assertIn('"--name-only", "-z"', cli)
        self.assertIn('"git", "archive"', cli)

    def _close_review_for_transaction(self):
        from archive_contract.capture import begin_invocation, complete_invocation, record_terminal_decision
        self._append_ledger_pair("r1", 1, "recovery-instance")
        started = begin_invocation(self.active, invocation_kind="spawn", role="outer-reviewer",
            phase="final-review", round_number=1, attempt=1, reservation_id="r1")
        terminal = complete_invocation(self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="recovery-instance", receipt="recovery-receipt",
            settlement_ref="gate-ledger.jsonl:r1", evidence_level="unavailable",
            resolution_source="none", resolution_reason_code="backend-does-not-expose",
            output_bytes=b"executable")
        decision = record_terminal_decision(self.active, {
            "decision_type": "reviewer-verdict", "reviewer_event_id": terminal["event_id"],
            "review_kind": "fresh", "verdict": "executable", "verdict_output_ref": terminal["event_id"],
        })
        marker = f"terminal_decision_event_id: {decision['event_id']}\nterminal_decision_value: executable\n"
        (self.active / "round-1.md").write_text(marker, encoding="utf-8", newline="\n")
        (self.active / "retrospective.md").write_text(marker, encoding="utf-8", newline="\n")

    def test_b5_archive_retry_recovers_after_source_backup_journal_failure(self):
        import archive_convergence
        from archive_contract import transaction

        self._close_review_for_transaction()
        done = self.root / "done"; done.mkdir()
        original = transaction._write_journal
        failed = False
        def injected(path, state, **extra):
            nonlocal failed
            if state == "source-backed-up" and not failed:
                failed = True
                raise OSError("injected journal failure")
            return original(path, state, **extra)
        with mock.patch.object(transaction, "_write_journal", injected):
            with self.assertRaises(OSError):
                transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        result, status = transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(result, done / "case")
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        self.assertFalse(self.active.exists())
        self.assertFalse(any((self.root / "active").glob(".archive-*.journal.json")))

    def test_b5_reopen_retry_finishes_after_move_journal_failure(self):
        import archive_convergence
        from archive_contract import transaction

        self._close_review_for_transaction()
        done = self.root / "done"; done.mkdir()
        transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        original = transaction._write_journal
        failed = False
        def injected(path, state, **extra):
            nonlocal failed
            if state == "reopen-moved" and not failed:
                failed = True
                raise OSError("injected reopen journal failure")
            return original(path, state, **extra)
        with mock.patch.object(transaction, "_write_journal", injected):
            with self.assertRaises(OSError):
                transaction.reopen(self.root / "active", done, "case")
        reopened = transaction.reopen(self.root / "active", done, "case")
        self.assertEqual(reopened, self.root / "active" / "case")
        self.assertTrue((reopened / ".reopen-state.json").exists())
        self.assertFalse((done / "case").exists())

    # ---- plan Phase1 step1: 调用前阻止越权角色被登记为 terminal owner -------------------
    def test_l2_gate_reviewer_rejected_before_persist_by_record_terminal_decision(self):
        from archive_contract.capture import begin_invocation, complete_invocation, record_terminal_decision
        from archive_contract.model import ArchiveError

        self._append_ledger_pair("r1", 1, "l2-1")
        started = begin_invocation(
            self.active, invocation_kind="spawn", role="l2-gate-reviewer", phase="gate",
            round_number=1, attempt=1, reservation_id="r1", requested_provider=None, requested_model=None,
        )
        terminal = complete_invocation(
            self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="l2-1", receipt="receipt-l2", evidence_level="unavailable",
            resolution_source="none", resolution_reason_code="backend-does-not-expose",
            output_bytes=b"gate_findings: []\n",
        )
        events_before = len(list((self.active / "evidence" / "events").glob("*.json")))
        with self.assertRaises(ArchiveError) as caught:
            record_terminal_decision(self.active, {
                "decision_type": "reviewer-verdict", "reviewer_event_id": terminal["event_id"],
                "review_kind": "fresh", "verdict": "executable", "verdict_output_ref": terminal["event_id"],
            })
        # l2-gate-reviewer 不在 REVIEWER_AUTHORITIES["fresh"] 中——门控角色不能被登记为终局 owner。
        self.assertEqual(caught.exception.code, "decision-reviewer-authority")
        # 关键：这个事实在写入**之前**就被拒绝——ledger 上事件数不应增加。
        events_after = len(list((self.active / "evidence" / "events").glob("*.json")))
        self.assertEqual(events_before, events_after)

    def test_outer_reviewer_accepted_by_record_terminal_decision(self):
        # 正对照：outer-reviewer 在 REVIEWER_AUTHORITIES["fresh"] 内，应被正常接受并落盘。
        from archive_contract.capture import begin_invocation, complete_invocation, record_terminal_decision

        self._append_ledger_pair("r1", 1, "review-1")
        started = begin_invocation(
            self.active, invocation_kind="spawn", role="outer-reviewer", phase="final-review",
            round_number=1, attempt=1, reservation_id="r1", requested_provider=None, requested_model=None,
        )
        terminal = complete_invocation(
            self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="review-1", receipt="receipt-1", evidence_level="unavailable",
            resolution_source="none", resolution_reason_code="backend-does-not-expose",
            output_bytes=b"verdict: executable\n",
        )
        decision = record_terminal_decision(self.active, {
            "decision_type": "reviewer-verdict", "reviewer_event_id": terminal["event_id"],
            "review_kind": "fresh", "verdict": "executable", "verdict_output_ref": terminal["event_id"],
        })
        self.assertEqual(decision["event_type"], "terminal-decision")
        # settlement_ref 也验证了自动生成（见下方专门测试），此处只确认 complete_invocation
        # 已经绑定了规范值，terminal owner 校验才有真实的 succeeded invocation 可引用。
        self.assertEqual(terminal["settlement_ref"], "gate-ledger.jsonl:r1")

    # ---- plan Phase1 step2: Round 0 单一规范表示 --------------------------------------
    def test_begin_invocation_round_zero_normalized_to_null(self):
        from archive_contract.capture import begin_invocation

        started = begin_invocation(
            self.active, invocation_kind="spawn", role="contract-proposer", phase="round-0-propose",
            round_number=0, attempt=1, reservation_id="r0", requested_provider=None, requested_model=None,
        )
        self.assertIsNone(started["round"])   # 字面 0 被归一化为 null，与 budget_gate 的 canonical_round 一致

    def test_begin_invocation_negative_round_rejected(self):
        from archive_contract.capture import begin_invocation
        from archive_contract.model import ArchiveError

        with self.assertRaises(ArchiveError) as caught:
            begin_invocation(
                self.active, invocation_kind="spawn", role="contract-proposer", phase="round-0-propose",
                round_number=-1, attempt=1, reservation_id="r0", requested_provider=None, requested_model=None,
            )
        self.assertEqual(caught.exception.code, "invocation-round")

    # ---- plan Phase1 step3: settlement_ref 自动生成 ------------------------------------
    def test_complete_invocation_auto_generates_canonical_settlement_ref(self):
        from archive_contract.capture import begin_invocation, complete_invocation

        started = begin_invocation(
            self.active, invocation_kind="spawn", role="reviewer", phase="review",
            round_number=1, attempt=1, reservation_id="r9", requested_provider=None, requested_model=None,
        )
        terminal = complete_invocation(
            self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="i9", receipt="p9", evidence_level="unavailable",
            resolution_source="none", resolution_reason_code="backend-does-not-expose",
            output_bytes=b"ok",
        )   # settlement_ref 未传——调用方不得手拼
        self.assertEqual(terminal["settlement_ref"], "gate-ledger.jsonl:r9")

    def test_complete_invocation_explicit_settlement_ref_override_kept(self):
        from archive_contract.capture import begin_invocation, complete_invocation

        started = begin_invocation(
            self.active, invocation_kind="spawn", role="reviewer", phase="review",
            round_number=1, attempt=1, reservation_id="r10", requested_provider=None, requested_model=None,
        )
        terminal = complete_invocation(
            self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="i10", receipt="p10", settlement_ref="custom-ref-1",
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"ok",
        )
        self.assertEqual(terminal["settlement_ref"], "custom-ref-1")   # 显式覆盖保留，不强制改写为规范值

    def test_complete_invocation_settlement_ref_format_rejected(self):
        from archive_contract.capture import begin_invocation, complete_invocation
        from archive_contract.model import ArchiveError

        started = begin_invocation(
            self.active, invocation_kind="spawn", role="reviewer", phase="review",
            round_number=1, attempt=1, reservation_id="r11", requested_provider=None, requested_model=None,
        )
        with self.assertRaises(ArchiveError) as caught:
            complete_invocation(
                self.active, started["invocation_id"], terminal_status="succeeded",
                instance_id="i11", receipt="p11", settlement_ref="",   # 空串，格式非法
                evidence_level="unavailable", resolution_source="none",
                resolution_reason_code="backend-does-not-expose", output_bytes=b"ok",
            )
        self.assertEqual(caught.exception.code, "settlement-ref-format")

    def test_continue_invocation_settlement_ref_stays_none_without_reservation(self):
        from archive_contract.capture import begin_invocation, complete_invocation

        spawn_start = begin_invocation(
            self.active, invocation_kind="spawn", role="reviewer", phase="review",
            round_number=1, attempt=1, reservation_id="r12", requested_provider=None, requested_model=None,
        )
        spawn_terminal = complete_invocation(
            self.active, spawn_start["invocation_id"], terminal_status="succeeded",
            instance_id="i12", settlement_ref="gate-ledger.jsonl:r12", evidence_level="unavailable",
            resolution_source="none", resolution_reason_code="backend-does-not-expose", output_bytes=b"ok",
        )
        cont_start = begin_invocation(
            self.active, invocation_kind="continue", role="reviewer", phase="inner",
            round_number=1, attempt=2, parent_event_id=spawn_start["event_id"],
            requested_provider=None, requested_model=None,
        )
        cont_terminal = complete_invocation(
            self.active, cont_start["invocation_id"], terminal_status="succeeded",
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"ok2",
        )   # continue 没有 reservation_id → 无可自动生成的规范值，settlement_ref 保持 None（既有语义不变）
        self.assertIsNone(cont_terminal["settlement_ref"])

    @staticmethod
    def _evidence(data):
        import hashlib
        return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data), "evidence_mode": "metadata-only"}

    @staticmethod
    def _event(kind, sequence, **fields):
        return {"schema_id": "converge.archive", "schema_version": "1.0", "event_type": kind,
                "event_id": f"00000000-0000-4000-8000-{sequence:012d}", "sequence": sequence, **fields}

    def _minimal_event_graph(self, role="reviewer", include_decision=True):
        start = self._event("invocation-started", 1, invocation_id="00000000-0000-4000-8000-000000000101",
            invocation_kind="spawn", role=role, phase="final-review", round=1, attempt=1,
            parent_event_id=None, parent_instance_id=None, reservation_id="r1",
            started_at="2026-07-12T00:00:00+00:00", requested_provider=None, requested_model=None,
            prompt_evidence=self._evidence(b""))
        terminal = self._event("invocation-terminal", 2, invocation_id=start["invocation_id"],
            started_event_id=start["event_id"], completed_at="2026-07-12T00:00:01+00:00",
            terminal_status="succeeded", instance_id="instance-1", receipt="receipt-1",
            settlement_ref="gate-ledger.jsonl:r1", resolved_provider=None, resolved_model=None,
            resolved_family=None, backend=None, backend_version=None, host_evidence_ref=None,
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_evidence=self._evidence(b"verdict"),
            failure_reason_code=None, failure_detail=None, legacy_source_path=None)
        result = [start, terminal]
        if include_decision:
            result.append(self._event("terminal-decision", 3, decision_type="reviewer-verdict",
                generated_at="2026-07-12T00:00:02+00:00", reviewer_event_id=terminal["event_id"],
                review_kind="fresh", verdict="executable", verdict_output_ref=terminal["event_id"],
                supersedes_decision_event_id=None))
        return result

    # ---- Phase 5: Archive Contract / Windows-OneDrive reliability -----------------------

    # -- (a) non-ASCII slug charset ------------------------------------------------------

    def test_p5_unicode_slug_archives_successfully(self):
        from archive_contract import transaction
        from archive_contract.presentation import check_view
        import archive_convergence

        self._close_review_for_transaction()
        slug = "20260724-OCSR-converge薄编排"
        (self.root / "active" / "case").rename(self.root / "active" / slug)
        done = self.root / "done"; done.mkdir()
        target, status = transaction.archive(self.root / "active", done, slug, archive_convergence._prepare)
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        self.assertEqual(target, done / slug)
        self.assertTrue(check_view(target)["valid"])

    def test_p5_unicode_slug_still_rejects_separators_device_names_and_trailing_dot(self):
        from archive_contract.model import ArchiveError, validate_identifier

        for bad in ("a/b", "a\\b", "CON", "con.md", "薄.", "薄 ", "a:b", "​薄"):
            with self.assertRaises(ArchiveError, msg=bad):
                validate_identifier(bad, "slug", charset="unicode-safe")
        validate_identifier("20260724-OCSR-converge薄编排与成本控制修复", "slug", charset="unicode-safe")

    def test_p5_artifact_id_charset_stays_ascii_only(self):
        from archive_contract.model import ArchiveError, validate_identifier

        validate_identifier("legacy-reference-materials", "artifact_id")
        with self.assertRaises(ArchiveError):
            validate_identifier("薄编排", "artifact_id")

    # -- (b) supersession chain relaxation for superseded reviewer-verdict decisions ----

    def test_p5_final_reviewer_verdict_bad_ref_still_fails_closed(self):
        from archive_contract.model import ArchiveError, validate_event_graph

        events = self._minimal_event_graph(role="reviewer", include_decision=False)
        start, terminal = events
        bad_final = self._event("terminal-decision", 3, decision_type="reviewer-verdict",
            generated_at="2026-07-12T00:00:02+00:00", reviewer_event_id=start["event_id"],
            review_kind="fresh", verdict="executable", verdict_output_ref=start["event_id"],
            supersedes_decision_event_id=None)
        with self.assertRaises(ArchiveError) as caught:
            validate_event_graph(events + [bad_final])
        self.assertEqual(caught.exception.code, "decision-reviewer-ref")

    def test_p5_superseded_reviewer_verdict_bad_ref_downgrades_to_degradation(self):
        from archive_contract.model import validate_event_graph

        events = self._minimal_event_graph(role="reviewer", include_decision=False)
        start, terminal = events
        bad = self._event("terminal-decision", 3, decision_type="reviewer-verdict",
            generated_at="2026-07-12T00:00:02+00:00", reviewer_event_id=start["event_id"],
            review_kind="fresh", verdict="executable", verdict_output_ref=start["event_id"],
            supersedes_decision_event_id=None)
        good = self._event("terminal-decision", 4, decision_type="reviewer-verdict",
            generated_at="2026-07-12T00:00:03+00:00", reviewer_event_id=terminal["event_id"],
            review_kind="fresh", verdict="executable", verdict_output_ref=terminal["event_id"],
            supersedes_decision_event_id=bad["event_id"])
        degradations = validate_event_graph(events + [bad, good])
        self.assertTrue(any(d.startswith(f"decision:superseded-ref-unverified:{bad['event_id']}:") for d in degradations))

    def test_p5_decision_chain_integrity_still_enforced_regardless_of_ref_validity(self):
        from archive_contract.model import ArchiveError, validate_event_graph

        events = self._minimal_event_graph(role="reviewer", include_decision=False)
        start, terminal = events
        bad = self._event("terminal-decision", 3, decision_type="reviewer-verdict",
            generated_at="2026-07-12T00:00:02+00:00", reviewer_event_id=start["event_id"],
            review_kind="fresh", verdict="executable", verdict_output_ref=start["event_id"],
            supersedes_decision_event_id=None)
        good = self._event("terminal-decision", 4, decision_type="reviewer-verdict",
            generated_at="2026-07-12T00:00:03+00:00", reviewer_event_id=terminal["event_id"],
            review_kind="fresh", verdict="executable", verdict_output_ref=terminal["event_id"],
            supersedes_decision_event_id="00000000-0000-4000-8000-999999999999")
        with self.assertRaises(ArchiveError) as caught:
            validate_event_graph(events + [bad, good])
        self.assertEqual(caught.exception.code, "decision-chain")

    def test_p5_archive_succeeds_end_to_end_with_superseded_bad_ref_decision(self):
        from archive_contract.capture import begin_invocation, complete_invocation, append_event, record_terminal_decision
        from archive_contract import transaction
        import archive_convergence

        self._append_ledger_pair("r1", 1, "inst-1")
        started = begin_invocation(self.active, invocation_kind="spawn", role="outer-reviewer",
            phase="final-review", round_number=1, attempt=1, reservation_id="r1")
        terminal = complete_invocation(self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="inst-1", receipt="r", settlement_ref="gate-ledger.jsonl:r1",
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"executable")
        # Written via append_event directly (bypassing record_terminal_decision's write-time
        # gate) to simulate a bad ref that landed through a non-capture.py write path — e.g.
        # legacy migration tooling, matching the mis-recorded historical incident this fix
        # targets.
        bad = append_event(self.active, {
            "event_type": "terminal-decision", "generated_at": "2026-07-24T00:00:00+00:00",
            "decision_type": "reviewer-verdict", "reviewer_event_id": started["event_id"],
            "review_kind": "fresh", "verdict": "executable", "verdict_output_ref": started["event_id"],
            "supersedes_decision_event_id": None,
        })
        good = record_terminal_decision(self.active, {
            "decision_type": "reviewer-verdict", "reviewer_event_id": terminal["event_id"],
            "review_kind": "fresh", "verdict": "executable", "verdict_output_ref": terminal["event_id"],
            "supersedes_decision_event_id": bad["event_id"],
        })
        marker = f"terminal_decision_event_id: {good['event_id']}\nterminal_decision_value: executable\n"
        (self.active / "round-1.md").write_text(marker, encoding="utf-8", newline="\n")
        (self.active / "retrospective.md").write_text(marker, encoding="utf-8", newline="\n")
        done = self.root / "done"; done.mkdir()
        target, status = transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        manifest = json.loads((target / "manifest.json").read_bytes())
        self.assertTrue(any(d.startswith(f"decision:superseded-ref-unverified:{bad['event_id']}:") for d in manifest["degradations"]))
        self.assertEqual(manifest["final_decision"]["event_id"], good["event_id"])

    # -- (c) explicit opt-in orphan-reservation degraded archive -------------------------

    def test_p5_orphan_reservation_fails_closed_by_default(self):
        from archive_contract.capture import begin_invocation, complete_invocation
        from archive_contract.model import ArchiveError, load_events, validate_ledger

        self._append_ledger_pair("r1", 1, "inst-1")
        started = begin_invocation(self.active, invocation_kind="spawn", role="outer-reviewer",
            phase="review", round_number=1, attempt=1, reservation_id="r1")
        complete_invocation(self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="inst-1", receipt="r", settlement_ref="gate-ledger.jsonl:r1",
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"ok")
        self._append_ledger_pair("orphan-r1", 2, "inst-x")
        with self.assertRaises(ArchiveError) as caught:
            validate_ledger(self.active, load_events(self.active))
        self.assertEqual(caught.exception.code, "ledger-invocation-orphan")

    def test_p5_orphan_reservation_declared_becomes_degradation(self):
        from archive_contract.capture import begin_invocation, complete_invocation
        from archive_contract.model import load_events, validate_ledger

        self._append_ledger_pair("r1", 1, "inst-1")
        started = begin_invocation(self.active, invocation_kind="spawn", role="outer-reviewer",
            phase="review", round_number=1, attempt=1, reservation_id="r1")
        complete_invocation(self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="inst-1", receipt="r", settlement_ref="gate-ledger.jsonl:r1",
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"ok")
        self._append_ledger_pair("orphan-r1", 2, "inst-x")
        degradations = validate_ledger(self.active, load_events(self.active),
            acknowledged_orphan_reservations=frozenset({"orphan-r1"}))
        self.assertEqual(degradations, ["ledger:orphan-reservation:orphan-r1"])

    def test_p5_orphan_acknowledgement_of_non_orphan_rejected(self):
        from archive_contract.capture import begin_invocation, complete_invocation
        from archive_contract.model import ArchiveError, load_events, validate_ledger

        self._close_review_for_transaction()
        with self.assertRaises(ArchiveError) as caught:
            validate_ledger(self.active, load_events(self.active),
                acknowledged_orphan_reservations=frozenset({"r1"}))
        self.assertEqual(caught.exception.code, "ledger-orphan-acknowledgement-invalid")

    def test_p5_find_orphan_reservations_lists_only_true_orphans(self):
        from archive_contract.capture import begin_invocation, complete_invocation
        from archive_contract.model import find_orphan_reservations

        self._append_ledger_pair("r1", 1, "inst-1")
        started = begin_invocation(self.active, invocation_kind="spawn", role="outer-reviewer",
            phase="review", round_number=1, attempt=1, reservation_id="r1")
        complete_invocation(self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="inst-1", receipt="r", settlement_ref="gate-ledger.jsonl:r1",
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"ok")
        self._append_ledger_pair("orphan-r1", 2, "inst-x")
        self.assertEqual(find_orphan_reservations(self.active), ["orphan-r1"])

    def test_p5_acknowledged_orphan_reservations_omitted_from_manifest_when_empty(self):
        self._close_review_for_transaction()
        from archive_contract.model import project_manifest

        manifest = project_manifest(self.active)
        self.assertNotIn("acknowledged_orphan_reservations", manifest)

    def test_p5_archive_cli_declare_orphan_reservation_end_to_end(self):
        import archive_convergence
        from archive_contract.capture import begin_invocation, complete_invocation, record_terminal_decision

        self._append_ledger_pair("r1", 1, "inst-1")
        started = begin_invocation(self.active, invocation_kind="spawn", role="outer-reviewer",
            phase="final-review", round_number=1, attempt=1, reservation_id="r1")
        terminal = complete_invocation(self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="inst-1", receipt="r", settlement_ref="gate-ledger.jsonl:r1",
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_bytes=b"executable")
        decision = record_terminal_decision(self.active, {
            "decision_type": "reviewer-verdict", "reviewer_event_id": terminal["event_id"],
            "review_kind": "fresh", "verdict": "executable", "verdict_output_ref": terminal["event_id"],
        })
        marker = f"terminal_decision_event_id: {decision['event_id']}\nterminal_decision_value: executable\n"
        (self.active / "round-1.md").write_text(marker, encoding="utf-8", newline="\n")
        (self.active / "retrospective.md").write_text(marker, encoding="utf-8", newline="\n")
        self._append_ledger_pair("orphan-r1", 2, "inst-x")
        done = self.root / "done"; done.mkdir()
        rc = archive_convergence.main(["archive", str(self.root / "active"), str(done), "case"])
        self.assertEqual(rc, 3)
        self.assertFalse((done / "case").exists())
        rc = archive_convergence.main([
            "archive", str(self.root / "active"), str(done), "case",
            "--declare-orphan-reservation", "orphan-r1",
        ])
        self.assertEqual(rc, 0)
        manifest = json.loads((done / "case" / "manifest.json").read_bytes())
        self.assertEqual(manifest.get("acknowledged_orphan_reservations"), ["orphan-r1"])
        self.assertIn("ledger:orphan-reservation:orphan-r1", manifest["degradations"])

    # -- (d) root allowlist unification ---------------------------------------------------

    def test_p5_root_allowlist_accepts_scope_product_and_ocsr_ledger_files(self):
        from archive_contract import transaction
        import archive_convergence

        self._close_review_for_transaction()
        (self.active / "uv-init-1.md").write_text("initial review\n", encoding="utf-8", newline="\n")
        (self.active / "uv-init-1-inner-1.md").write_text("inner review\n", encoding="utf-8", newline="\n")
        (self.active / "blind-recheck-1.md").write_text("blind review\n", encoding="utf-8", newline="\n")
        (self.active / "ocsr-dispatch-ledger.jsonl").write_text('{"a":1}\n', encoding="utf-8", newline="\n")
        done = self.root / "done"; done.mkdir()
        target, status = transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        manifest = json.loads((target / "manifest.json").read_bytes())
        names = {r["path"] for r in manifest["records"]}
        self.assertTrue({"uv-init-1.md", "uv-init-1-inner-1.md", "blind-recheck-1.md",
                          "ocsr-dispatch-ledger.jsonl"} <= names)

    def test_p5_root_allowlist_still_rejects_unknown_root_file(self):
        from archive_contract import transaction
        from archive_contract.model import ArchiveError
        import archive_convergence

        self._close_review_for_transaction()
        (self.active / "random-notes.md").write_text("nope\n", encoding="utf-8", newline="\n")
        done = self.root / "done"; done.mkdir()
        with self.assertRaises(ArchiveError) as caught:
            transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(caught.exception.code, "root-clutter")

    def test_p5_is_root_allowed_name_matches_budget_gate_scope_product_templates(self):
        """Cross-module consistency check standing in for a shared import (budget_gate.py
        cannot import archive_contract.model without a cycle, since model.validate_ledger
        imports budget_gate) — every SCOPE_PRODUCT template instantiation must satisfy the
        archive root allowlist, or the two modules have silently diverged."""
        import budget_gate
        from archive_contract.model import is_root_allowed_name

        for template in budget_gate.SCOPE_PRODUCT.values():
            for n in (1, 2, 10, 123):
                name = template.format(n=n)
                self.assertTrue(is_root_allowed_name(name), name)

    # -- archive() cleanup-pending distinguishable status (step 2) -----------------------

    def test_p5_archive_returns_cleanup_pending_when_only_backup_removal_fails(self):
        from archive_contract import transaction
        from archive_contract.presentation import check_view
        import archive_convergence

        self._close_review_for_transaction()
        done = self.root / "done"; done.mkdir()
        original_rmtree = transaction.shutil.rmtree
        calls = {"n": 0}
        def flaky_rmtree(path, *a, **kw):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError(2, "Access is denied", None, 5)
            return original_rmtree(path, *a, **kw)
        with mock.patch.object(transaction.shutil, "rmtree", side_effect=flaky_rmtree):
            target, status = transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(status, transaction.STATUS_CLEANUP_PENDING)
        self.assertTrue(check_view(target)["valid"])
        self.assertTrue(any((self.root / "active").glob(".archive-*.journal.json")))
        target2, status2 = transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(target2, target)
        self.assertEqual(status2, transaction.STATUS_COMMITTED)
        self.assertFalse(any((self.root / "active").glob(".archive-*.journal.json")))

    # -- Windows relative-path subpath false positive (step 4) ---------------------------

    def test_p5_check_relative_root_path_does_not_misfire(self):
        from archive_contract import transaction
        from archive_contract.presentation import check_view
        import archive_convergence

        self._close_review_for_transaction()
        done = self.root / "done"; done.mkdir()
        transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        cwd = os.getcwd()
        try:
            os.chdir(str(done))
            view = check_view(Path("case"))
            self.assertTrue(view["valid"], view["diagnostics"])
        finally:
            os.chdir(cwd)

    # -- newline / CRLF policy (step 5) ---------------------------------------------------

    def test_p5_root_records_normalized_to_lf_before_hashing(self):
        from archive_contract import transaction
        from archive_contract.presentation import check_view
        import archive_convergence

        self._close_review_for_transaction()
        data = (self.active / "round-1.md").read_bytes()
        (self.active / "round-1.md").write_bytes(data.replace(b"\n", b"\r\n"))
        done = self.root / "done"; done.mkdir()
        target, status = transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        committed = (target / "round-1.md").read_bytes()
        self.assertNotIn(b"\r\n", committed)
        self.assertTrue(check_view(target)["valid"])

    def test_p5_evidence_blobs_are_not_line_ending_normalized(self):
        from archive_contract.capture import begin_invocation, complete_invocation, record_terminal_decision
        from archive_contract import transaction
        import archive_convergence

        self._append_ledger_pair("r1", 1, "inst-1")
        started = begin_invocation(self.active, invocation_kind="spawn", role="outer-reviewer",
            phase="final-review", round_number=1, attempt=1, reservation_id="r1")
        payload = b"line1\r\nline2\r\n"
        terminal = complete_invocation(self.active, started["invocation_id"], terminal_status="succeeded",
            instance_id="inst-1", receipt="r", settlement_ref="gate-ledger.jsonl:r1",
            evidence_level="unavailable", resolution_source="none",
            resolution_reason_code="backend-does-not-expose", output_bytes=payload, evidence_mode="exact")
        decision = record_terminal_decision(self.active, {
            "decision_type": "reviewer-verdict", "reviewer_event_id": terminal["event_id"],
            "review_kind": "fresh", "verdict": "executable", "verdict_output_ref": terminal["event_id"],
        })
        marker = f"terminal_decision_event_id: {decision['event_id']}\nterminal_decision_value: executable\n"
        (self.active / "round-1.md").write_text(marker, encoding="utf-8", newline="\n")
        (self.active / "retrospective.md").write_text(marker, encoding="utf-8", newline="\n")
        done = self.root / "done"; done.mkdir()
        target, status = transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        blob_path = next((target / "evidence" / "invocations").rglob("output.bin"))
        self.assertEqual(blob_path.read_bytes(), payload)

    def test_p5_check_git_ref_reverifies_from_git_commit(self):
        import archive_convergence
        from archive_contract import transaction

        self._close_review_for_transaction()
        done_root = self.root / ".converge" / "done"
        done_root.mkdir(parents=True)
        target, status = transaction.archive(self.root / "active", done_root, "case", archive_convergence._prepare)
        self.assertEqual(status, transaction.STATUS_COMMITTED)

        def git(*args):
            return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True)
        git("init", "-q")
        git("config", "user.email", "test@example.com")
        git("config", "user.name", "test")
        # Match this repo's own .gitattributes convention (`* text=auto eol=lf`) — without it,
        # a throwaway repo falls back to whatever `core.autocrlf` the host's system-level Git
        # config declares (commonly true on Windows installs), which would make `git archive`
        # re-introduce CRLF independently of anything this test is trying to verify.
        (self.root / ".gitattributes").write_text("* text=auto eol=lf\n", encoding="utf-8", newline="\n")
        git("add", "-A")
        git("commit", "-q", "-m", "archive case")
        rc = archive_convergence.main(["check-git-ref", str(self.root), "case", "--format", "json"])
        self.assertEqual(rc, 0)

    # -- ACL/ReadOnly/reparse precise-path safe removal (step 6) --------------------------

    def test_p5_safe_remove_tree_rejects_shallow_path(self):
        from archive_contract import transaction
        from archive_contract.model import ArchiveError

        shallow = Path(self.root.anchor)
        with self.assertRaises(ArchiveError) as caught:
            transaction.safe_remove_tree(shallow)
        self.assertEqual(caught.exception.code, "cleanup-root-guard")

    def test_p5_safe_remove_tree_rejects_unexpected_parent(self):
        from archive_contract import transaction
        from archive_contract.model import ArchiveError

        victim = self.root / "active" / "case"
        with self.assertRaises(ArchiveError) as caught:
            transaction.safe_remove_tree(victim, expected_parent=self.root)
        self.assertEqual(caught.exception.code, "cleanup-path-unsafe")
        self.assertTrue(victim.exists())

    def test_p5_safe_remove_tree_removes_readonly_file_via_retry(self):
        from archive_contract import transaction
        import stat as _stat

        victim = self.root / "active" / "case"
        ro_file = victim / "readonly.md"
        ro_file.write_text("x", encoding="utf-8")
        os.chmod(ro_file, _stat.S_IREAD)
        transaction.safe_remove_tree(victim, expected_parent=self.root / "active")
        self.assertFalse(victim.exists())

    def test_p5_safe_remove_tree_unlinks_real_junction_without_touching_target(self):
        from archive_contract import transaction

        target_dir = self.root / "junction-target"
        target_dir.mkdir()
        (target_dir / "keep.md").write_text("keep me\n", encoding="utf-8")
        link = self.root / "active" / "junction-link"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target_dir)],
            capture_output=True, text=True)
        if result.returncode != 0:
            self.skipTest(f"mklink /J unavailable in this environment: {result.stderr or result.stdout}")
        self.assertTrue(link.exists())
        transaction.safe_remove_tree(link, expected_parent=self.root / "active")
        self.assertFalse(link.exists())
        self.assertTrue((target_dir / "keep.md").exists())

    # -- OneDrive/reparse workaround: detection + local staging (step 1) -----------------

    def test_p5_probe_delete_blocked_false_for_normal_directory(self):
        from archive_contract import transaction

        self.assertFalse(transaction._probe_delete_blocked(self.root))

    def test_p5_probe_delete_blocked_true_on_injected_winerror5(self):
        from archive_contract import transaction

        real_rmdir = Path.rmdir
        def fake_rmdir(self_path):
            if self_path.name.startswith(".archive-probe-"):
                raise OSError(2, "Access is denied", None, 5)
            return real_rmdir(self_path)
        with mock.patch.object(Path, "rmdir", fake_rmdir):
            self.assertTrue(transaction._probe_delete_blocked(self.root))

    def test_p5_onedrive_workaround_needed_detects_reparse_attribute_via_injected_adapter(self):
        from archive_contract import transaction
        import types

        real_lstat = Path.lstat
        def fake_lstat(self_path):
            if self_path == self.root:
                return types.SimpleNamespace(st_file_attributes=0x400)
            return real_lstat(self_path)
        with mock.patch.object(Path, "lstat", fake_lstat):
            self.assertTrue(transaction.onedrive_workaround_needed(self.root, self.root, probe=False))

    def test_p5_archive_reliable_defaults_to_plain_archive_when_not_reparse_blocked(self):
        from archive_contract import transaction
        import archive_convergence

        self._close_review_for_transaction()
        done = self.root / "done"; done.mkdir()
        target, status = transaction.archive_reliable(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        self.assertFalse(any((self.root / "active").glob(".archive-*.onedrive-journal.json")))

    def test_p5_archive_reliable_routes_through_local_staging_when_forced(self):
        from archive_contract import transaction
        from archive_contract.presentation import check_view
        import archive_convergence

        self._close_review_for_transaction()
        done = self.root / "done"; done.mkdir()
        target, status = transaction.archive_reliable(self.root / "active", done, "case",
            archive_convergence._prepare, workaround=True)
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        self.assertEqual(target, done / "case")
        self.assertFalse(self.active.exists())
        self.assertTrue(check_view(target)["valid"])

    def test_p5_archive_reliable_idempotent_when_source_already_gone(self):
        from archive_contract import transaction
        import archive_convergence

        self._close_review_for_transaction()
        done = self.root / "done"; done.mkdir()
        target, status = transaction.archive_reliable(self.root / "active", done, "case",
            archive_convergence._prepare, workaround=True)
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        target2, status2 = transaction.archive_reliable(self.root / "active", done, "case",
            archive_convergence._prepare, workaround=True)
        self.assertEqual(status2, transaction.STATUS_COMMITTED)
        self.assertEqual(target2, target)

    def test_p5_archive_reliable_done_conflict_when_no_journal_but_both_copies_exist(self):
        from archive_contract import transaction
        from archive_contract.model import ArchiveError
        import archive_convergence

        self._close_review_for_transaction()
        done = self.root / "done"; done.mkdir()
        (done / "case").mkdir()
        (done / "case" / "foreign.txt").write_text("not ours\n", encoding="utf-8")
        with self.assertRaises(ArchiveError) as caught:
            transaction.archive_reliable(self.root / "active", done, "case", archive_convergence._prepare,
                workaround=True)
        self.assertEqual(caught.exception.code, "done-conflict")

    def test_p5_archive_reliable_cleanup_pending_then_idempotent_retry(self):
        from archive_contract import transaction
        from archive_contract.presentation import check_view
        import archive_convergence

        self._close_review_for_transaction()
        done = self.root / "done"; done.mkdir()
        original = transaction.safe_remove_tree
        calls = {"n": 0}
        def flaky(path, **kw):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError(2, "Access is denied", None, 5)
            return original(path, **kw)
        with mock.patch.object(transaction, "safe_remove_tree", side_effect=flaky):
            target, status = transaction.archive_reliable(self.root / "active", done, "case",
                archive_convergence._prepare, workaround=True)
        self.assertEqual(status, transaction.STATUS_CLEANUP_PENDING)
        self.assertTrue(self.active.exists())
        self.assertTrue(check_view(target)["valid"])
        target2, status2 = transaction.archive_reliable(self.root / "active", done, "case",
            archive_convergence._prepare, workaround=True)
        self.assertEqual(status2, transaction.STATUS_COMMITTED)
        self.assertFalse(self.active.exists())

    # ---- Phase 5 addendum: auxiliary (non-event-derived) evidence import ----------------
    # Orchestrator裁决 2026-07-24："契约端扩展"——evidence/ 下非保留子路径的文件默认导入并
    # 披露（不是放宽校验，是"归档器不应拒绝合法生成器的既定产物"哲学的延伸，见 step 3）。

    def test_p5b_auxiliary_evidence_imported_and_disclosed(self):
        from archive_contract import transaction
        from archive_contract.presentation import check_view
        import archive_convergence

        self._close_review_for_transaction()
        (self.active / "evidence").mkdir(exist_ok=True)
        (self.active / "evidence" / "phase3-report.md").write_text("# report\n", encoding="utf-8", newline="\n")
        (self.active / "evidence" / "notes").mkdir(parents=True, exist_ok=True)
        (self.active / "evidence" / "notes" / "sub.md").write_text("nested\n", encoding="utf-8", newline="\n")
        done = self.root / "done"; done.mkdir()
        target, status = transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        manifest = json.loads((target / "manifest.json").read_bytes())
        paths = {item["path"] for item in manifest.get("auxiliary_evidence", [])}
        self.assertEqual(paths, {"evidence/phase3-report.md", "evidence/notes/sub.md"})
        # not projected as an owner fact — absent from blobs/invocations
        self.assertNotIn("evidence/phase3-report.md", {b["path"] for b in manifest["blobs"]})
        index = (target / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("Auxiliary Evidence", index)
        self.assertIn("non-event-derived", index)
        self.assertIn("evidence/phase3-report.md", index)
        self.assertTrue(check_view(target)["valid"])

    def test_p5b_auxiliary_file_cannot_shadow_reserved_subdir_name(self):
        from archive_contract import transaction
        from archive_contract.model import ArchiveError
        import archive_convergence

        self._close_review_for_transaction()
        (self.active / "evidence" / "artifacts").mkdir(parents=True, exist_ok=True)
        (self.active / "evidence" / "artifacts" / "not-a-real-artifact.txt").write_text("x", encoding="utf-8")
        done = self.root / "done"; done.mkdir()
        with self.assertRaises(ArchiveError) as caught:
            transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(caught.exception.code, "evidence-orphan")

    def test_p5b_auxiliary_evidence_refuses_secret_basenames(self):
        from archive_contract import transaction
        from archive_contract.model import ArchiveError
        import archive_convergence

        self._close_review_for_transaction()
        (self.active / "evidence").mkdir(exist_ok=True)
        (self.active / "evidence" / ".env").write_text("SECRET=1\n", encoding="utf-8")
        done = self.root / "done"; done.mkdir()
        with self.assertRaises(ArchiveError) as caught:
            transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(caught.exception.code, "auxiliary-evidence-secret-refused")

    def test_p5b_check_detects_auxiliary_evidence_hash_drift(self):
        from archive_contract import transaction
        from archive_contract.presentation import check_view
        import archive_convergence

        self._close_review_for_transaction()
        (self.active / "evidence").mkdir(exist_ok=True)
        (self.active / "evidence" / "phase3-report.md").write_text("original\n", encoding="utf-8", newline="\n")
        done = self.root / "done"; done.mkdir()
        target, status = transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(status, transaction.STATUS_COMMITTED)
        self.assertTrue(check_view(target)["valid"])
        (target / "evidence" / "phase3-report.md").write_bytes(b"tampered\n")
        view = check_view(target)
        self.assertFalse(view["valid"])
        self.assertEqual(view["diagnostics"][0]["code"], "content-mismatch")

    def test_p5b_auxiliary_evidence_omitted_from_manifest_when_absent(self):
        from archive_contract.model import project_manifest

        self._close_review_for_transaction()
        manifest = project_manifest(self.active)
        self.assertNotIn("auxiliary_evidence", manifest)

    def test_p5b_secret_names_shared_between_capture_and_model(self):
        from archive_contract import capture, model

        self.assertIs(capture.SECRET_NAMES, model.SECRET_NAMES)


if __name__ == "__main__":
    unittest.main()
