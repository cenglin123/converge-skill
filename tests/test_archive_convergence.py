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

    def test_b4_orphan_blob_is_not_projected_as_owner_fact(self):
        from archive_contract.model import ArchiveError, project_manifest

        events = self.active / "evidence" / "events"; events.mkdir(parents=True)
        orphan = self.active / "evidence" / "orphan.txt"; orphan.write_text("orphan", encoding="utf-8")
        with self.assertRaises(ArchiveError) as caught:
            project_manifest(self.active)
        self.assertEqual(caught.exception.code, "evidence-orphan")

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
        result = transaction.archive(self.root / "active", done, "case", archive_convergence._prepare)
        self.assertEqual(result, done / "case")
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


if __name__ == "__main__":
    unittest.main()
