"""Append-only fact capture. This module owns no schema definitions."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import (
    ARCHIVE_TOTAL_LIMIT, ArchiveError, EVIDENCE_LEVELS, EVIDENCE_MODES, FAILURE_REASONS, RESOLUTION_REASONS,
    RESOLUTION_SOURCES, SCHEMA_ID, SCHEMA_VERSION, SECRET_NAMES, TERMINAL_STATUSES, canonical_json_bytes,
    ROOT_FIXED, ROUND_RE, ensure_safe_root, ensure_safe_tree, normalize_relative, sha256_size, strict_json_bytes,
    validate_event,
    validate_identifier,
    validate_reviewer_verdict_authority,
    canonical_round,
    owner_process_liveness,
)

DEFAULT_FILE_LIMIT = 16 * 1024 * 1024
DEFAULT_TOTAL_LIMIT = 64 * 1024 * 1024
LEDGER_FILENAME = "gate-ledger.jsonl"


def _canonical_settlement_ref(reservation_id: str) -> str:
    return f"{LEDGER_FILENAME}:{reservation_id}"


def _validate_settlement_ref_format(value: Any) -> None:
    """Format check for an explicit `--settlement-ref` override. Callers may still override
    (e.g. legacy/bootstrap flows), but the value must at least be a well-formed bounded string —
    the same shape `validate_event`'s `_text(...)` enforces downstream. This does not force the
    override to equal the canonical `gate-ledger.jsonl:<reservation_id>` value (that stronger
    cross-check already exists at archive time in `model.validate_ledger`); it only rejects
    obviously malformed hand-typed input early, at capture time."""
    if not isinstance(value, str) or not value or len(value) > 4096 or "\x00" in value:
        raise ArchiveError("settlement-ref-format", "Settlement reference must be a bounded non-empty string.", "evidence/events")


_owner_process_liveness = owner_process_liveness


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventLock:
    def __init__(self, root: Path):
        self.path = root / ".archive-event.lock"
        self.fd: int | None = None

    def __enter__(self):
        for _ in range(2):
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.write(self.fd, canonical_json_bytes({"pid": os.getpid(), "nonce": uuid.uuid4().hex, "started_at": _now()}))
                os.fsync(self.fd)
                return self
            except FileExistsError as exc:
                try:
                    owner = strict_json_bytes(self.path.read_bytes())
                    pid = owner.get("pid") if isinstance(owner, dict) else None
                    if not isinstance(pid, int) or pid < 1:
                        raise ArchiveError("lock-owner-invalid", "Event lock owner record is malformed.", self.path.name) from exc
                    liveness = _owner_process_liveness(pid)
                    if liveness == "dead":
                        self.path.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    self.path.unlink(missing_ok=True)
                    continue
                raise ArchiveError("lock-conflict", "Another live archive writer owns the event lock.", self.path.name) from exc
        raise ArchiveError("lock-conflict", "Event lock recovery could not acquire ownership.", self.path.name)

    def __exit__(self, exc_type, exc, tb):
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def _read_existing(root: Path) -> list[dict[str, Any]]:
    directory = root / "evidence" / "events"
    if not directory.exists():
        return []
    result = []
    for path in sorted(directory.glob("*.json")):
        result.append(strict_json_bytes(path.read_bytes()))
    return result


def _prune_empty(path: Path, stop: Path) -> None:
    while path != stop:
        try:
            path.rmdir()
        except OSError:
            return
        path = path.parent


def _commit_event(root: Path, fields: dict[str, Any], blobs: list[tuple[Path, bytes]] | None = None) -> dict[str, Any]:
    root = ensure_safe_root(Path(root))
    ensure_safe_tree(root)
    blobs = blobs or []
    with EventLock(root):
        existing = _read_existing(root)
        event = {"schema_id": SCHEMA_ID, "schema_version": SCHEMA_VERSION, **fields}
        event["sequence"] = len(existing) + 1
        event["event_id"] = str(uuid.uuid4())
        if event["event_type"] == "invocation-terminal":
            if any(e.get("event_type") == "invocation-terminal" and e.get("invocation_id") == event["invocation_id"] for e in existing):
                raise ArchiveError("invocation-already-terminal", "Invocation already has a terminal event.", "evidence/events")
        validate_event(event)
        target = root / "evidence" / "events" / f"{event['sequence']:08d}-{event['event_id']}.json"
        event_bytes = canonical_json_bytes(event)
        current_total = sum(path.stat().st_size for path in root.rglob("*") if path.is_file() and path != root / ".archive-event.lock")
        if current_total + len(event_bytes) + sum(len(data) for _, data in blobs) > ARCHIVE_TOTAL_LIMIT:
            raise ArchiveError("archive-too-large", "Capture would exceed the configured archive total limit.", "evidence")
        written: list[Path] = []
        try:
            for blob_path, data in blobs:
                try:
                    blob_path.relative_to(root)
                except ValueError as exc:
                    raise ArchiveError("path-escape", "Evidence target escapes the archive root.", str(blob_path)) from exc
                _exclusive_write(blob_path, data, root)
                written.append(blob_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            _exclusive_write(target, event_bytes, root)
        except Exception:
            for path in reversed(written):
                path.unlink(missing_ok=True)
                _prune_empty(path.parent, root)
            _prune_empty(target.parent, root)
            raise
        return event


def append_event(root: Path, fields: dict[str, Any]) -> dict[str, Any]:
    return _commit_event(root, fields)


def _identity(data: bytes, mode: str, path: str | None = None) -> dict[str, Any]:
    digest, size = sha256_size(data)
    result: dict[str, Any] = {"sha256": digest, "size": size, "evidence_mode": mode}
    if path:
        result["path"] = path
    return result


def _exclusive_write(path: Path, data: bytes, root: Path | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if root is not None:
        ensure_safe_tree(root)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as handle:
            handle.write(data)
            handle.flush()
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_regular_file(source: Path, max_bytes: int = DEFAULT_FILE_LIMIT) -> bytes:
    source = Path(source)
    if source.name.casefold() in SECRET_NAMES:
        raise ArchiveError("secret-refused", "Common secret files are refused by default.")
    before = source.lstat()
    attrs = getattr(before, "st_file_attributes", 0)
    rejected = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400) | getattr(stat, "FILE_ATTRIBUTE_SPARSE_FILE", 0x200)
    if stat.S_ISLNK(before.st_mode) or attrs & rejected or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ArchiveError("capture-filetype", "Capture source must be a regular single-link non-sparse file.", str(source))
    if before.st_size > max_bytes:
        raise ArchiveError("capture-too-large", "Capture source exceeds the configured file limit.", str(source))
    fd = os.open(source, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ArchiveError("capture-toctou", "Capture source identity changed before read.", str(source))
        with os.fdopen(fd, "rb", closefd=False) as handle:
            data = handle.read(max_bytes + 1)
    finally:
        os.close(fd)
    after = source.lstat()
    if len(data) > max_bytes or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        raise ArchiveError("capture-toctou", "Capture source changed or exceeded limits during read.", str(source))
    return data


def begin_invocation(root: Path, *, invocation_kind: str, role: str, phase: str,
                     round_number: int | None, attempt: int, reservation_id: str | None = None,
                     parent_event_id: str | None = None, requested_provider: str | None = None,
                     requested_model: str | None = None, prompt_bytes: bytes | None = None,
                     prompt_path: Path | None = None,
                     evidence_mode: str = "metadata-only") -> dict[str, Any]:
    if evidence_mode not in EVIDENCE_MODES:
        raise ArchiveError("evidence-mode", "Unsupported evidence mode.")
    if invocation_kind not in ("spawn", "continue") or not isinstance(role, str) or not role or not isinstance(phase, str) or not phase:
        raise ArchiveError("invocation-input", "Invocation kind, role, and phase are invalid.")
    try:
        round_number = canonical_round(round_number)
    except ValueError as exc:
        raise ArchiveError("invocation-round", "Invocation round must be null or a positive integer.") from exc
    if invocation_kind == "spawn" and not reservation_id:
        raise ArchiveError("spawn-reservation-required", "Every Spawn requires a budget reservation before capture.")
    if invocation_kind == "continue" and (not parent_event_id or reservation_id is not None):
        raise ArchiveError("invocation-parent", "Continue requires a parent Spawn event and no reservation.")
    root = ensure_safe_root(Path(root))
    if prompt_bytes is not None and prompt_path is not None:
        raise ArchiveError("capture-input-conflict", "Pass prompt bytes or a prompt path, not both.")
    if prompt_path is not None:
        prompt_bytes = _read_regular_file(prompt_path)
    invocation_id = str(uuid.uuid4())
    prompt = prompt_bytes or b""
    prompt_ref = _identity(prompt, evidence_mode)
    target = None
    if evidence_mode != "metadata-only" and prompt_bytes is not None:
        rel = f"evidence/invocations/{invocation_id}/prompt.bin"
        target = root / rel
        prompt_ref["path"] = rel
    parent_instance_id = None
    if invocation_kind == "continue":
        events = _read_existing(root)
        parent = next((e for e in events if e.get("event_id") == parent_event_id), None)
        if not parent or parent.get("event_type") != "invocation-started" or parent.get("invocation_kind") != "spawn":
            raise ArchiveError("invocation-parent", "Continue parent must be a Spawn start event.", "evidence/events")
        parent_terminal = next((e for e in events if e.get("event_type") == "invocation-terminal" and e.get("started_event_id") == parent_event_id), None)
        if not parent_terminal or not parent_terminal.get("instance_id"):
            raise ArchiveError("continue-parent-open", "Continue parent must have a terminal instance identity.", "evidence/events")
        parent_instance_id = parent_terminal["instance_id"]
    blobs = [(target, prompt_bytes)] if target is not None and prompt_bytes is not None else []
    return _commit_event(root, {
        "event_type": "invocation-started", "invocation_id": invocation_id,
        "invocation_kind": invocation_kind, "role": role, "phase": phase,
        "round": round_number, "attempt": attempt, "parent_event_id": parent_event_id,
        "parent_instance_id": parent_instance_id,
        "reservation_id": reservation_id, "started_at": _now(),
        "requested_provider": requested_provider, "requested_model": requested_model,
        "prompt_evidence": prompt_ref,
    }, blobs)


def _find_started(root: Path, invocation_id: str) -> dict[str, Any]:
    events = _read_existing(Path(root))
    starts = [e for e in events if e.get("event_type") == "invocation-started" and e.get("invocation_id") == invocation_id]
    if len(starts) != 1:
        raise ArchiveError("invocation-not-found", "Invocation start event is missing or duplicated.", "evidence/events")
    if any(e.get("event_type") == "invocation-terminal" and e.get("invocation_id") == invocation_id for e in events):
        raise ArchiveError("invocation-already-terminal", "Invocation already has a terminal event.", "evidence/events")
    return starts[0]


def complete_invocation(root: Path, invocation_id: str, *, terminal_status: str,
                        instance_id: str | None = None, receipt: str | None = None,
                        settlement_ref: str | None = None, resolved_provider: str | None = None,
                        resolved_model: str | None = None, resolved_family: str | None = None,
                        backend: str | None = None, backend_version: str | None = None,
                        evidence_level: str = "unavailable", resolution_source: str = "none",
                        resolution_reason_code: str | None = None, output_bytes: bytes | None = None,
                        output_path: Path | None = None,
                        evidence_mode: str = "metadata-only", failure_reason_code: str | None = None,
                        failure_detail: str | None = None, host_evidence_ref: str | None = None,
                        legacy_source_path: str | None = None) -> dict[str, Any]:
    root = ensure_safe_root(Path(root))
    if output_bytes is not None and output_path is not None:
        raise ArchiveError("capture-input-conflict", "Pass output bytes or an output path, not both.")
    if output_path is not None:
        output_bytes = _read_regular_file(output_path)
    started = _find_started(root, invocation_id)
    if settlement_ref is None:
        # settlement_ref 由 API 自动生成规范值——调用方不得手拼（plan Phase1 step3）。仅当
        # started invocation 绑定了 reservation_id（即 spawn，非 continue）时才有对应 ledger
        # 记录可引用；continue 没有 reservation，settlement_ref 保持 None（既有语义不变）。
        rid = started.get("reservation_id")
        if rid:
            settlement_ref = _canonical_settlement_ref(rid)
    else:
        _validate_settlement_ref_format(settlement_ref)
    if terminal_status not in TERMINAL_STATUSES or evidence_level not in EVIDENCE_LEVELS or resolution_source not in RESOLUTION_SOURCES:
        raise ArchiveError("terminal-enum", "Terminal or provenance enum is invalid.")
    if evidence_mode not in EVIDENCE_MODES:
        raise ArchiveError("evidence-mode", "Unsupported evidence mode.")
    if terminal_status == "succeeded" and output_bytes is None:
        raise ArchiveError("output-missing", "Succeeded invocation requires output bytes or identity.")
    output_ref = None
    target = None
    if output_bytes is not None:
        output_ref = _identity(output_bytes, evidence_mode)
        if evidence_mode != "metadata-only":
            rel = f"evidence/invocations/{invocation_id}/output.bin"
            target = root / rel
            output_ref["path"] = rel
    if started["invocation_kind"] == "continue":
        if instance_id is None:
            instance_id = started["parent_instance_id"]
        elif instance_id != started["parent_instance_id"]:
            raise ArchiveError("continue-instance-conflict", "Continue terminal must use the parent Spawn instance.")
    blobs = [(target, output_bytes)] if target is not None and output_bytes is not None else []
    return _commit_event(root, {
        "event_type": "invocation-terminal", "invocation_id": invocation_id,
        "started_event_id": started["event_id"], "completed_at": _now(),
        "terminal_status": terminal_status, "instance_id": instance_id, "receipt": receipt,
        "settlement_ref": settlement_ref, "resolved_provider": resolved_provider,
        "resolved_model": resolved_model, "resolved_family": resolved_family,
        "backend": backend, "backend_version": backend_version,
        "host_evidence_ref": host_evidence_ref,
        "evidence_level": evidence_level, "resolution_source": resolution_source,
        "resolution_reason_code": resolution_reason_code, "output_evidence": output_ref,
        "failure_reason_code": failure_reason_code, "failure_detail": failure_detail,
        "legacy_source_path": legacy_source_path,
    }, blobs)


def recover_invocation(root: Path, invocation_id: str, *, terminal_status: str,
                       failure_reason_code: str, failure_detail: str | None = None,
                       instance_id: str | None = None, settlement_ref: str | None = None) -> dict[str, Any]:
    if terminal_status not in ("failed", "cancelled", "timeout"):
        raise ArchiveError("recovery-status", "Recovery may only append a non-success terminal.")
    return complete_invocation(
        root, invocation_id, terminal_status=terminal_status,
        instance_id=instance_id, settlement_ref=settlement_ref,
        evidence_level="unavailable", resolution_source="none",
        resolution_reason_code="invocation-failed-before-resolution",
        failure_reason_code=failure_reason_code, failure_detail=failure_detail,
    )


def capture_artifact(root: Path, source: Path, *, artifact_id: str, revision_id: str,
                     evidence_mode: str = "metadata-only", workspace_root: Path | None = None,
                     workspace_id: str | None = None, external_authorization_ref: str | None = None,
                     display_locator: str | None = None, redacted_bytes: bytes | None = None,
                     max_bytes: int = DEFAULT_FILE_LIMIT) -> dict[str, Any]:
    validate_identifier(artifact_id, "artifact_id")
    if not isinstance(revision_id, str) or not revision_id.startswith("r") or not revision_id[1:].isdigit() or revision_id[1:] == "0":
        raise ArchiveError("revision-id", "Artifact revision id must be r followed by a positive integer.")
    if evidence_mode not in EVIDENCE_MODES:
        raise ArchiveError("evidence-mode", "Unsupported evidence mode.")
    root = ensure_safe_root(Path(root))
    source = Path(source)
    if workspace_root is None and not external_authorization_ref:
        raise ArchiveError("external-authorization", "External artifact capture requires fresh explicit authorization before source access.")
    if workspace_root is not None and not workspace_id:
        raise ArchiveError("workspace-id", "Workspace-relative capture requires a workspace identity.")
    if evidence_mode == "redacted" and redacted_bytes is None:
        raise ArchiveError("redacted-copy-missing", "Redacted mode requires caller-confirmed redacted bytes.")
    if source.name.casefold() in SECRET_NAMES:
        raise ArchiveError("secret-refused", "Common secret files are refused by default.")
    if workspace_root is not None:
        workspace = Path(workspace_root).resolve(strict=True)
        resolved = source.resolve(strict=True)
        try:
            rel = resolved.relative_to(workspace).as_posix()
        except ValueError as exc:
            raise ArchiveError("artifact-outside-workspace", "Source is outside the declared workspace.") from exc
        locator = {"kind": "workspace-relative", "workspace_id": workspace_id, "path": normalize_relative(rel)}
    else:
        locator = {"kind": "external", "display_locator": display_locator or "external-artifact", "portable": False, "authorization_ref": external_authorization_ref}
    st_before = source.lstat()
    attrs = getattr(st_before, "st_file_attributes", 0)
    sparse = getattr(stat, "FILE_ATTRIBUTE_SPARSE_FILE", 0x200)
    if stat.S_ISLNK(st_before.st_mode) or attrs & (getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400) | sparse) or not stat.S_ISREG(st_before.st_mode) or st_before.st_nlink != 1:
        raise ArchiveError("artifact-filetype", "Artifact must be a regular single-link file.")
    if st_before.st_size > max_bytes:
        raise ArchiveError("artifact-too-large", "Artifact exceeds the configured single-file limit.")
    with source.open("rb") as handle:
        data = handle.read(max_bytes + 1)
        st_handle = os.fstat(handle.fileno())
    st_after = source.lstat()
    identity_before = (st_before.st_dev, st_before.st_ino, st_before.st_size, st_before.st_mtime_ns)
    identity_after = (st_after.st_dev, st_after.st_ino, st_after.st_size, st_after.st_mtime_ns)
    if identity_before != identity_after or (st_handle.st_dev, st_handle.st_ino) != (st_before.st_dev, st_before.st_ino):
        raise ArchiveError("artifact-toctou", "Artifact changed while being captured.")
    digest, size = sha256_size(data)
    capability = {"metadata-only": "identity-only", "redacted": "redacted-copy", "exact": "snapshot"}[evidence_mode]
    snapshot = None
    if evidence_mode != "metadata-only":
        captured = redacted_bytes if evidence_mode == "redacted" else data
        if evidence_mode == "redacted" and redacted_bytes is None:
            raise ArchiveError("redacted-copy-missing", "Redacted mode requires caller-confirmed redacted bytes.")
        rel = f"evidence/artifacts/{artifact_id}/snapshot"
        target = root / rel
        copy_hash, copy_size = sha256_size(captured)
        snapshot = {"path": rel, "sha256": copy_hash, "size": copy_size}
    else:
        target = None; captured = None
    blobs = [(target, captured)] if target is not None and captured is not None else []
    return _commit_event(root, {
        "event_type": "artifact-captured", "artifact_id": artifact_id,
        "revision_id": revision_id, "captured_at": _now(), "sha256": digest,
        "size": size, "evidence_mode": evidence_mode,
        "reproduction_capability": capability, "source_locator": locator,
        "snapshot": snapshot,
    }, blobs)


def record_terminal_decision(root: Path, fields: dict[str, Any]) -> dict[str, Any]:
    root = Path(root)
    values = {"event_type": "terminal-decision", "generated_at": _now(), **fields}
    values.setdefault("supersedes_decision_event_id", None)
    if values.get("decision_type") == "reviewer-verdict":
        # 调用前阻止：把 REVIEWER_AUTHORITIES 授权检查前移到落盘之前，而不是只在归档时
        # (validate_event_graph) 才发现——一个越权角色（如 l2-gate-reviewer，只是
        # refs/quality-gate.md 定义的 advisory 门控，从不在 REVIEWER_AUTHORITIES 中）
        # 永远不能被登记为 terminal owner，这个事实本身都不应该被写入 ledger。
        validate_reviewer_verdict_authority(_read_existing(root), values)
    return append_event(root, values)


def record_design_review_completion(root: Path, *, invocation_event_id: str,
                                    completion_status: str, highlights_ref: str) -> dict[str, Any]:
    return append_event(Path(root), {
        "event_type": "design-review-completion", "invocation_event_id": invocation_event_id,
        "completion_status": completion_status, "highlights_ref": highlights_ref,
        "completed_at": _now(),
    })


def record_user_message(root: Path, *, host_message_id: str, user_quote: str) -> dict[str, Any]:
    return append_event(Path(root), {
        "event_type": "user-message", "host_message_id": host_message_id,
        "user_quote": user_quote, "recorded_at": _now(),
    })


def bootstrap_import_legacy(staging: Path) -> None:
    """Import uniquely ledger/state-bound legacy evidence inside a staging copy."""
    staging = Path(staging)
    if (staging / "evidence" / "events").exists():
        return
    ledger_path = staging / "gate-ledger.jsonl"
    if not ledger_path.exists():
        return
    ledger = [strict_json_bytes(line) for line in ledger_path.read_bytes().splitlines() if line]
    reservations = {e["reservation_id"]: e for e in ledger if e.get("event") == "reserved"}
    settlements = {e["reservation_id"]: e for e in ledger if e.get("event") in ("spawn_succeeded", "spawn_failed", "cancelled")}
    candidates = [p for p in staging.iterdir() if p.is_file() and p.name not in ROOT_FIXED and not ROUND_RE.fullmatch(p.name)]
    bound: dict[Path, str] = {}
    for path in candidates:
        text = path.read_text(encoding="utf-8", errors="replace")
        matches = []
        for rid, reservation in reservations.items():
            instance = settlements.get(rid, {}).get("instance_id")
            round_no = reservation.get("target_round")
            role = reservation.get("target_role")
            if any(token and token in text for token in (rid, instance)):
                matches.append(rid)
            elif role == "ultraverge-initial" and round_no and path.name.startswith(f"uv-init-{round_no}"):
                matches.append(rid)
            elif role == "executor" and "plan-amend" in path.name and "plan-amend" in rid:
                matches.append(rid)
        if len(set(matches)) == 1:
            bound[path] = matches[0]
        elif path.name != "reference-materials.md":
            raise ArchiveError("legacy-binding-ambiguous", "Legacy raw evidence cannot be uniquely bound.", path.name, "Provide content/state references that identify exactly one ledger reservation.")
    starts: dict[str, dict[str, Any]] = {}
    invocation_counts: dict[str, int] = {}
    for path, rid in sorted(bound.items(), key=lambda pair: (pair[1], "-inner-" in pair[0].name, pair[0].name)):
        reservation, settlement = reservations[rid], settlements.get(rid)
        if settlement is None:
            raise ArchiveError("legacy-ledger-open", "Legacy evidence references an unsettled reservation.", path.name)
        count = invocation_counts.get(rid, 0)
        if count == 0:
            started = begin_invocation(staging, invocation_kind="spawn", role=reservation["target_role"],
                phase="bootstrap-import", round_number=reservation.get("target_round"), attempt=1,
                reservation_id=rid, requested_provider=None, requested_model=None)
            starts[rid] = started
        else:
            started = begin_invocation(staging, invocation_kind="continue", role=reservation["target_role"],
                phase="bootstrap-import-inner", round_number=reservation.get("target_round"), attempt=count + 1,
                parent_event_id=starts[rid]["event_id"], requested_provider=None, requested_model=None)
        invocation_counts[rid] = count + 1
        status = "succeeded" if settlement["event"] == "spawn_succeeded" else ("cancelled" if settlement["event"] == "cancelled" else "failed")
        if status == "succeeded":
            complete_invocation(staging, started["invocation_id"], terminal_status=status,
                instance_id=settlement.get("instance_id"), settlement_ref=f"gate-ledger.jsonl:{rid}",
                evidence_level="unavailable", resolution_source="none", resolution_reason_code="receipt-missing",
                output_bytes=path.read_bytes(), evidence_mode="exact", legacy_source_path=path.name)
        else:
            recover_invocation(staging, started["invocation_id"], terminal_status=status,
                               failure_reason_code="backend-error", instance_id=settlement.get("instance_id"),
                               settlement_ref=f"gate-ledger.jsonl:{rid}")
        path.unlink()
    reference = staging / "reference-materials.md"
    if reference.exists():
        capture_artifact(staging, reference, artifact_id="legacy-reference-materials", revision_id="r1",
            evidence_mode="exact", workspace_root=staging, workspace_id="archive-staging")
        reference.unlink()
