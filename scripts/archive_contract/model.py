"""Executable schema, ownership rules, projection, and validation for archive v1."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
import unicodedata
import uuid
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

SCHEMA_ID = "converge.archive"
SCHEMA_VERSION = "1.0"
ARCHIVE_TOTAL_LIMIT = 64 * 1024 * 1024
EVENT_TYPES = frozenset({
    "invocation-started", "invocation-terminal", "artifact-captured",
    "terminal-decision", "design-review-completion", "user-message",
})
TERMINAL_STATUSES = frozenset({"succeeded", "failed", "cancelled", "timeout"})
FAILURE_REASONS = frozenset({"backend-error", "cancelled-by-host", "timeout", "process-interrupted"})
EVIDENCE_MODES = frozenset({"metadata-only", "redacted", "exact"})
EVIDENCE_LEVELS = frozenset({"observed", "host-reported", "configured", "inherited", "unavailable"})
RESOLUTION_SOURCES = frozenset({"host_receipt", "tool_response", "cli_argument", "agent_config", "parent_instance", "none"})
RESOLUTION_REASONS = frozenset({
    "backend-does-not-expose", "receipt-missing", "inherited-concrete-model-hidden",
    "invocation-failed-before-resolution",
})
# Shared authority for common-secret basename refusal — used both at capture time
# (capture.py `_read_regular_file`/`capture_artifact`) and, since Phase 5's auxiliary-evidence
# import (see `EVIDENCE_RESERVED_SUBDIRS`/`project_manifest`), at archive-time for any
# non-event-derived file swept in from `evidence/`. Single source so the two call sites cannot
# silently diverge on what counts as an obvious secret.
SECRET_NAMES = frozenset({".env", ".netrc", "id_rsa", "id_ed25519", "credentials", "credentials.json"})
# Reserved `evidence/` top-level segments: only these carry event-derived, provenance-bearing
# content (`events/` = the append-only event log itself; `invocations/`, `artifacts/`,
# `revisions/` = blobs whose identity is owned by a specific event's evidence reference, see
# `validate_evidence_ref`). Any other top-level segment under `evidence/` is eligible as
# "auxiliary evidence" (plan Phase 5 addendum) — imported, hashed, and disclosed in the
# manifest's `auxiliary_evidence` section, but never claims provenance and never participates
# in event-graph validation. Because membership in this reserved set routes a path into the
# strict `allowed_blobs` comparison instead of the auxiliary bucket, an attacker/generator
# cannot use an auxiliary file to "shadow" a reserved subpath — any path whose top segment
# collides with one of these names is compared against the exact event-derived closure and
# fails `evidence-orphan` the same as before, it is never silently accepted as auxiliary.
EVIDENCE_RESERVED_SUBDIRS = frozenset({"events", "invocations", "artifacts", "revisions"})
ROOT_FIXED = frozenset({
    "INDEX.md", "manifest.json", "plan.md", "contract.md", "attempts.md",
    "retrospective.md", "design-review.md", "_orchestrator-state.md",
    "gate-ledger.jsonl", "_budget-state.json",
    # Vault-side dispatch adapter's fixed ledger name (CONVERGE_LEDGER_NAME in
    # .meta/scripts/ocsr_dispatch.py). Literal, not templated — one fixed basename,
    # unlike the round-numbered generator products below.
    "ocsr-dispatch-ledger.jsonl",
})
ROUND_RE = re.compile(r"round-[1-9][0-9]*\.md\Z")
# Canonical root-record patterns for `budget_gate.SCOPE_PRODUCT` generator output
# (`uv-init-{n}.md` / `blind-recheck-{n}.md`). Kept here as the single allowlist
# authority; `tests/test_budget_gate.py` cross-checks that every SCOPE_PRODUCT
# template instantiation matches one of these patterns, so the two modules cannot
# silently diverge (budget_gate.py cannot import this module without a cycle, since
# this module's ledger validation imports budget_gate).
UV_INIT_RE = re.compile(r"uv-init-[1-9][0-9]*(-inner-[1-9][0-9]*)?\.md\Z")
BLIND_RECHECK_RE = re.compile(r"blind-recheck-[1-9][0-9]*\.md\Z")
HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")
EVENT_NAME_RE = re.compile(r"([0-9]{8})-([0-9a-f-]{36})\.json\Z")
SAFE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SAFE_ID_UNICODE_MAX_LEN = 150
REVISION_ID_RE = re.compile(r"r[1-9][0-9]*\Z")


def is_root_allowed_name(name: str) -> bool:
    """Single-source root allowlist check, shared by `project_manifest`'s root-clutter
    guard and (indirectly, via the same patterns) archive-time line-ending normalization.
    A name is permitted at archive root when it is one of the fixed `ROOT_FIXED` files, an
    outer-loop `round-N.md`, or one of the two SCOPE_PRODUCT generator conventions
    (`uv-init-N[.md]` / `blind-recheck-N.md`)."""
    return bool(
        name in ROOT_FIXED
        or ROUND_RE.fullmatch(name)
        or UV_INIT_RE.fullmatch(name)
        or BLIND_RECHECK_RE.fullmatch(name)
    )
WINDOWS_RESERVED = frozenset({"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))})
REVIEWER_AUTHORITIES = {
    "fresh": frozenset({"reviewer", "outer-reviewer", "ultraverge-initial"}),
    "blank-slate": frozenset({"blank-slate-reviewer", "blind-reviewer"}),
}
PROVENANCE_MATRIX = {
    "observed": {"sources": frozenset({"host_receipt", "tool_response"}), "reasons": frozenset({None})},
    "host-reported": {"sources": frozenset({"host_receipt", "tool_response"}), "reasons": frozenset({None})},
    "configured": {"sources": frozenset({"cli_argument", "agent_config"}), "reasons": frozenset({"backend-does-not-expose", "receipt-missing"})},
    "inherited": {"sources": frozenset({"parent_instance"}), "reasons": frozenset({"inherited-concrete-model-hidden"})},
    "unavailable": {"sources": frozenset({"none"}), "reasons": frozenset({"backend-does-not-expose", "receipt-missing", "invocation-failed-before-resolution"})},
}


def canonical_round(value: Any) -> int | None:
    """Single canonical Round 0 representation, reused by ledger (`budget_gate.py` reserve),
    invocation capture (`begin_invocation`), and this module's own event schema (`round` must
    be null or a positive integer, see `EVENT_FIELDS`/`validate_event`). Round 0 (no round /
    contract-negotiation phase) is represented as ``None`` everywhere; a literal ``0`` is
    accepted as an alias here and normalized to ``None`` so no caller (ledger or invocation)
    ever persists a literal 0 — closing the "one place writes 0, one place requires null" gap.
    Any other non-null, non-positive-int input is rejected.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("round must be null or a non-negative integer")
    return None if value == 0 else value


def validate_reviewer_verdict_authority(events: list[dict[str, Any]], decision: dict[str, Any]) -> None:
    """Shared reviewer-verdict authority check.

    Reused at two points: (1) early, inside `capture.record_terminal_decision`, **before** the
    terminal-decision fact is ever persisted — so a role outside `REVIEWER_AUTHORITIES` for the
    claimed `review_kind` (e.g. `l2-gate-reviewer`, an advisory-only Dynamic Workflows gate per
    `refs/quality-gate.md` — it never appears in `REVIEWER_AUTHORITIES`) is refused *before* it
    can be registered as a terminal decision owner, not only detected later when the archive is
    checked; and (2) at archive-time inside `validate_event_graph`, as a structural re-check over
    the full closed event graph. Both call sites must reject the exact same set of illegal facts.
    """
    by_id = {e["event_id"]: e for e in events}
    terminal = by_id.get(decision.get("reviewer_event_id"))
    if not terminal or terminal.get("event_type") != "invocation-terminal" or terminal.get("terminal_status") != "succeeded":
        raise ArchiveError("decision-reviewer-ref", "Final reviewer verdict does not reference a successful invocation terminal.", "evidence/events")
    started = by_id.get(terminal.get("started_event_id"))
    allowed_roles = REVIEWER_AUTHORITIES.get(decision.get("review_kind"), frozenset())
    if not started or started.get("invocation_kind") != "spawn" or started.get("role") not in allowed_roles:
        raise ArchiveError("decision-reviewer-authority", "Final verdict owner is not an authorized fresh reviewer Spawn.", "evidence/events")
    if decision.get("verdict_output_ref") != terminal.get("event_id") or not terminal.get("output_evidence"):
        raise ArchiveError("decision-output-binding", "Reviewer verdict does not bind the referenced invocation output.", "evidence/events")


def owner_process_liveness(pid: int) -> str:
    """Non-signalling owner probe; unknown callers must fail closed."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid < 1:
        return "unknown"
    if pid == os.getpid():
        return "alive"
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        open_process = kernel32.OpenProcess
        open_process.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        open_process.restype = wintypes.HANDLE
        wait = kernel32.WaitForSingleObject
        wait.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        wait.restype = wintypes.DWORD
        close = kernel32.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL
        handle = open_process(0x00100000 | 0x00001000, False, pid)
        if not handle:
            return "dead" if ctypes.get_last_error() == 87 else "unknown"
        try:
            result = wait(handle, 0)
            return "dead" if result == 0 else ("alive" if result == 0x102 else "unknown")
        finally:
            close(handle)
    proc_root = Path("/proc")
    return ("alive" if (proc_root / str(pid)).exists() else "dead") if proc_root.is_dir() else "unknown"

COMMON_EVENT_FIELDS = frozenset({"schema_id", "schema_version", "event_type", "event_id", "sequence"})
EVENT_FIELDS = {
    "invocation-started": COMMON_EVENT_FIELDS | frozenset({
        "invocation_id", "invocation_kind", "role", "phase", "round", "attempt",
        "parent_event_id", "parent_instance_id", "reservation_id", "started_at",
        "requested_provider", "requested_model", "prompt_evidence",
    }),
    "invocation-terminal": COMMON_EVENT_FIELDS | frozenset({
        "invocation_id", "started_event_id", "completed_at", "terminal_status",
        "instance_id", "receipt", "settlement_ref", "resolved_provider", "resolved_model",
        "resolved_family", "backend", "backend_version", "host_evidence_ref",
        "evidence_level", "resolution_source", "resolution_reason_code", "output_evidence",
        "failure_reason_code", "failure_detail", "legacy_source_path",
    }),
    "artifact-captured": COMMON_EVENT_FIELDS | frozenset({
        "artifact_id", "revision_id", "captured_at", "sha256", "size", "evidence_mode",
        "reproduction_capability", "source_locator", "snapshot",
    }),
    "terminal-decision": COMMON_EVENT_FIELDS | frozenset({
        "decision_type", "generated_at", "reviewer_event_id", "review_kind", "verdict",
        "verdict_output_ref", "decision_kind", "user_quote", "source_ref",
        "presented_degradations", "accepted_state", "supersedes_decision_event_id",
    }),
    "design-review-completion": COMMON_EVENT_FIELDS | frozenset({
        "invocation_event_id", "completion_status", "highlights_ref", "completed_at",
    }),
    "user-message": COMMON_EVENT_FIELDS | frozenset({"host_message_id", "user_quote", "recorded_at"}),
}


@dataclass(frozen=True)
class ArchiveError(Exception):
    code: str
    summary: str
    path: str | None = None
    next_action: str = "Inspect the referenced archive record and correct the source facts."

    def diagnostic(self) -> dict[str, str | None]:
        return {"code": self.code, "summary": self.summary, "path": self.path, "next_action": self.next_action}

    def __str__(self) -> str:
        return f"{self.code}: {self.summary}"


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite number: {value}")


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def strict_json_bytes(data: bytes) -> Any:
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is forbidden")
    text = data.decode("utf-8", errors="strict")
    return json.loads(text, object_pairs_hook=_pairs_no_duplicates, parse_constant=_reject_constant)


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def sha256_size(data: bytes) -> tuple[str, int]:
    return hashlib.sha256(data).hexdigest(), len(data)


def normalize_relative(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ArchiveError("path-invalid", "Path must be a non-empty POSIX relative path.", value or None)
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise ArchiveError("path-escape", "Path escapes or ambiguously addresses the archive root.", value)
    for part in pure.parts:
        if part.endswith((".", " ")) or ":" in part or part.split(".", 1)[0].upper() in WINDOWS_RESERVED:
            raise ArchiveError("path-ambiguous", "Path uses a reserved or ambiguous Windows name.", value)
    return pure.as_posix()


def validate_identifier(value: Any, label: str = "identifier", *, charset: str = "ascii") -> str:
    """Validate a filesystem-safe basename identifier (slug, artifact_id, ...).

    `charset="ascii"` (default) keeps the original strict `[A-Za-z0-9][A-Za-z0-9._-]*`
    shape — used for `artifact_id` and anywhere no non-ASCII need has been established.
    `charset="unicode-safe"` additionally accepts any Unicode letter/digit (via
    `str.isalnum()`, which is True for CJK and most other scripts but False for
    whitespace, path separators, punctuation, symbols, and Unicode format/control
    characters such as bidi overrides or zero-width joiners) — used for `slug`, so this
    vault's established Chinese-slug convention for `docs/plans`/`.converge` objects is
    not rejected. Both variants still reject path separators, Windows device names, and
    trailing dot/space, and both require NFC-normalized input (no combining-mark or
    normalization ambiguity)."""
    if charset not in ("ascii", "unicode-safe"):
        raise ValueError(f"unsupported identifier charset: {charset}")
    if not isinstance(value, str) or not value:
        raise ArchiveError("identifier-invalid", f"{label} must be a non-empty safe basename.", str(value) if value is not None else None)
    if charset == "ascii":
        ok = bool(SAFE_ID_RE.fullmatch(value))
    else:
        ok = (
            len(value) <= SAFE_ID_UNICODE_MAX_LEN
            and value[0].isalnum()
            and all(ch.isalnum() or ch in "._-" for ch in value)
            and unicodedata.normalize("NFC", value) == value
        )
    if not ok:
        raise ArchiveError("identifier-invalid", f"{label} must be a safe basename (letters/digits from any script, plus '.', '_', '-', not leading).", value)
    if value.split(".", 1)[0].upper() in WINDOWS_RESERVED or value.endswith((".", " ")):
        raise ArchiveError("identifier-invalid", f"{label} uses a reserved or ambiguous basename.", value)
    return value


def _uuid(value: Any, label: str) -> None:
    try:
        parsed = uuid.UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ArchiveError("event-uuid", f"{label} must be a canonical UUID.", "evidence/events") from exc
    if str(parsed) != value:
        raise ArchiveError("event-uuid", f"{label} must be a canonical UUID.", "evidence/events")


def _timestamp(value: Any, label: str) -> None:
    if not isinstance(value, str):
        raise ArchiveError("event-time", f"{label} must be an ISO timestamp.", "evidence/events")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ArchiveError("event-time", f"{label} must be an ISO timestamp.", "evidence/events") from exc


def validate_evidence_ref(ref: Any, *, owner_kind: str, owner_id: str, required: bool) -> None:
    if ref is None:
        if required:
            raise ArchiveError("evidence-ref-missing", f"{owner_kind} requires evidence identity.", "evidence/events")
        return
    if not isinstance(ref, dict) or set(ref) not in ({"sha256", "size", "evidence_mode"}, {"sha256", "size", "evidence_mode", "path"}):
        raise ArchiveError("evidence-ref-fields", "Evidence reference has forbidden or missing fields.", "evidence/events")
    if not isinstance(ref["sha256"], str) or not HEX64_RE.fullmatch(ref["sha256"]):
        raise ArchiveError("evidence-ref-hash", "Evidence reference digest is invalid.", "evidence/events")
    if not isinstance(ref["size"], int) or isinstance(ref["size"], bool) or ref["size"] < 0 or ref["evidence_mode"] not in EVIDENCE_MODES:
        raise ArchiveError("evidence-ref-schema", "Evidence size or mode is invalid.", "evidence/events")
    mode = ref["evidence_mode"]
    has_path = "path" in ref
    if (mode == "metadata-only") == has_path:
        raise ArchiveError("evidence-ref-mode", "Only redacted/exact evidence may own a blob path.", "evidence/events")
    if has_path:
        rel = normalize_relative(ref["path"])
        expected = f"evidence/invocations/{owner_id}/{owner_kind}.bin"
        if rel != expected:
            raise ArchiveError("evidence-ref-path", "Invocation evidence path does not match its owner.", rel)


def ensure_safe_root(path: Path) -> Path:
    raw = str(path)
    if raw.startswith(("\\\\", "\\\\?\\")):
        raise ArchiveError("root-unsafe", "UNC and extended-device roots are not supported.", None)
    resolved = path.resolve(strict=True)
    if not resolved.is_dir():
        raise ArchiveError("root-not-directory", "Canonical root is not a directory.", None)
    return resolved


def ensure_safe_tree(root: Path) -> list[Path]:
    root = ensure_safe_root(root)
    seen: dict[str, str] = {}
    files: list[Path] = []
    for current, dirs, names in os.walk(root, followlinks=False):
        base = Path(current)
        entries = [*(base / d for d in dirs), *(base / n for n in names)]
        for entry in entries:
            rel = entry.relative_to(root).as_posix()
            normalize_relative(rel)
            key = unicodedata.normalize("NFC", rel).casefold()
            if key in seen and seen[key] != rel:
                raise ArchiveError("path-collision", "Case or Unicode normalization collision detected.", rel)
            seen[key] = rel
            st = entry.lstat()
            attrs = getattr(st, "st_file_attributes", 0)
            reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            sparse = getattr(stat, "FILE_ATTRIBUTE_SPARSE_FILE", 0x200)
            if stat.S_ISLNK(st.st_mode) or attrs & (reparse | sparse):
                raise ArchiveError("filesystem-link", "Links and reparse points are forbidden.", rel)
            if entry.is_file():
                if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
                    raise ArchiveError("filesystem-alias", "Only regular single-link files are permitted.", rel)
                files.append(entry)
            elif not entry.is_dir():
                raise ArchiveError("filesystem-special", "Special filesystem objects are forbidden.", rel)
    return files


def schema_state(root: Path) -> tuple[str, str | None]:
    manifest_path = Path(root) / "manifest.json"
    if not manifest_path.exists():
        return "missing", "legacy-unverifiable"
    try:
        obj = strict_json_bytes(manifest_path.read_bytes())
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return "malformed", "malformed-json"
    if not isinstance(obj, dict):
        return "malformed", "manifest-not-object"
    schema_id, version = obj.get("schema_id"), obj.get("schema_version")
    if schema_id is None or version is None:
        return "unsupported", "unversioned"
    if schema_id != SCHEMA_ID:
        return "unsupported", "foreign-schema"
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+", version):
        return "unsupported", "unversioned"
    major, minor = map(int, version.split("."))
    if major != 1 or minor > 0:
        return "unsupported", "newer-version"
    try:
        validate_archive(Path(root), obj)
    except ArchiveError as exc:
        return "invalid", exc.code
    return "valid", None


def load_events(root: Path) -> list[dict[str, Any]]:
    events_dir = root / "evidence" / "events"
    if not events_dir.is_dir():
        raise ArchiveError("events-missing", "Append-only event directory is missing.", "evidence/events")
    events: list[dict[str, Any]] = []
    for path in sorted(events_dir.iterdir(), key=lambda p: p.name):
        if not path.is_file():
            raise ArchiveError("event-not-file", "Event entry is not a regular file.", path.relative_to(root).as_posix())
        try:
            event = strict_json_bytes(path.read_bytes())
        except Exception as exc:
            raise ArchiveError("event-malformed", f"Event JSON is malformed: {exc}", path.relative_to(root).as_posix()) from exc
        validate_event(event, path.name)
        events.append(event)
    sequences = [e["sequence"] for e in events]
    if sequences != list(range(1, len(events) + 1)):
        raise ArchiveError("sequence-gap", "Event sequence must be globally continuous from 1.", "evidence/events")
    ids = [e["event_id"] for e in events]
    if len(ids) != len(set(ids)):
        raise ArchiveError("event-id-duplicate", "Event identifiers must be unique.", "evidence/events")
    return events


def _require(event: dict[str, Any], fields: Iterable[str]) -> None:
    missing = [field for field in fields if field not in event]
    if missing:
        raise ArchiveError("event-field-missing", f"Event is missing fields: {', '.join(missing)}.", "evidence/events")


def _text(value: Any, label: str, *, optional: bool = False, limit: int = 4096) -> None:
    if value is None and optional:
        return
    if not isinstance(value, str) or not value or len(value) > limit or "\x00" in value:
        raise ArchiveError("event-value-type", f"{label} must be a bounded non-empty string.", "evidence/events")


def validate_event(event: Any, filename: str | None = None) -> None:
    if not isinstance(event, dict):
        raise ArchiveError("event-schema", "Event must be a JSON object.", "evidence/events")
    _require(event, ("schema_id", "schema_version", "event_type", "event_id", "sequence"))
    if not isinstance(event["event_type"], str) or event["schema_id"] != SCHEMA_ID or event["schema_version"] != SCHEMA_VERSION or event["event_type"] not in EVENT_TYPES:
        raise ArchiveError("event-schema", "Event schema identity or type is unsupported.", "evidence/events")
    kind = event["event_type"]
    expected_fields = EVENT_FIELDS[kind]
    if kind == "terminal-decision":
        if event.get("decision_type") == "reviewer-verdict":
            expected_fields = COMMON_EVENT_FIELDS | frozenset({
                "decision_type", "generated_at", "reviewer_event_id", "review_kind", "verdict",
                "verdict_output_ref", "supersedes_decision_event_id",
            })
        elif event.get("decision_type") == "user-decision":
            expected_fields = COMMON_EVENT_FIELDS | frozenset({
                "decision_type", "generated_at", "decision_kind", "user_quote", "source_ref",
                "presented_degradations", "accepted_state", "supersedes_decision_event_id",
            })
    if set(event) != set(expected_fields):
        extra = sorted(set(event) - set(expected_fields)); missing = sorted(set(expected_fields) - set(event))
        raise ArchiveError("event-fields", f"Event fields are not closed; extra={extra}, missing={missing}.", "evidence/events")
    if not isinstance(event["sequence"], int) or isinstance(event["sequence"], bool) or event["sequence"] < 1:
        raise ArchiveError("event-sequence", "Event sequence must be a positive integer.", "evidence/events")
    _uuid(event["event_id"], "event_id")
    if filename and filename != f"{event['sequence']:08d}-{event['event_id']}.json":
        raise ArchiveError("event-filename", "Event filename does not match its identity.", f"evidence/events/{filename}")
    if kind == "invocation-started":
        _uuid(event["invocation_id"], "invocation_id")
        if event["invocation_kind"] not in ("spawn", "continue"):
            raise ArchiveError("invocation-kind", "Invocation kind must be spawn or continue.")
        if not isinstance(event["role"], str) or not event["role"] or not isinstance(event["phase"], str) or not event["phase"]:
            raise ArchiveError("invocation-owner", "Invocation role and phase must be non-empty strings.")
        if event["round"] is not None and (not isinstance(event["round"], int) or isinstance(event["round"], bool) or event["round"] < 1):
            raise ArchiveError("invocation-round", "Invocation round must be null or a positive integer.")
        if not isinstance(event["attempt"], int) or isinstance(event["attempt"], bool) or event["attempt"] < 1:
            raise ArchiveError("invocation-attempt", "Invocation attempt must be a positive integer.")
        _timestamp(event["started_at"], "started_at")
        for field in ("requested_provider", "requested_model", "parent_instance_id", "reservation_id"):
            _text(event[field], field, optional=True)
        validate_evidence_ref(event["prompt_evidence"], owner_kind="prompt", owner_id=event["invocation_id"], required=True)
        if event["invocation_kind"] == "spawn":
            if not event["reservation_id"]:
                raise ArchiveError("spawn-reservation-required", "Every Spawn requires a budget reservation.", "evidence/events")
            if event["parent_event_id"] is not None or event["parent_instance_id"] is not None:
                raise ArchiveError("spawn-parent-forbidden", "Spawn cannot claim a Continue parent.", "evidence/events")
        else:
            if not event["parent_event_id"] or not event["parent_instance_id"] or event["reservation_id"] is not None:
                raise ArchiveError("invocation-parent", "Continue requires its Spawn parent event and instance, without a reservation.")
            _uuid(event["parent_event_id"], "parent_event_id")
    elif kind == "invocation-terminal":
        _uuid(event["invocation_id"], "invocation_id"); _uuid(event["started_event_id"], "started_event_id")
        _timestamp(event["completed_at"], "completed_at")
        for field in ("instance_id", "receipt", "settlement_ref", "resolved_provider", "resolved_model",
                      "resolved_family", "backend", "backend_version", "host_evidence_ref",
                      "resolution_reason_code", "failure_reason_code", "failure_detail", "legacy_source_path"):
            _text(event[field], field, optional=True)
        if not isinstance(event["terminal_status"], str) or event["terminal_status"] not in TERMINAL_STATUSES:
            raise ArchiveError("terminal-status", "Terminal status is outside the closed enum.")
        if not isinstance(event["evidence_level"], str) or not isinstance(event["resolution_source"], str) or event["evidence_level"] not in EVIDENCE_LEVELS or event["resolution_source"] not in RESOLUTION_SOURCES:
            raise ArchiveError("provenance-combination", "Model provenance uses an unsupported evidence combination.")
        if event["evidence_level"] in ("configured", "inherited", "unavailable") and event.get("resolution_reason_code") not in RESOLUTION_REASONS:
            raise ArchiveError("provenance-reason", "Partial/unavailable provenance requires a closed reason code.")
        if event["resolution_reason_code"] == "invocation-failed-before-resolution" and event["terminal_status"] == "succeeded":
            raise ArchiveError("provenance-reason", "Failure-before-resolution reason is forbidden on succeeded invocations.")
        if event["terminal_status"] != "succeeded" and event["evidence_level"] == "unavailable" and event["resolution_reason_code"] != "invocation-failed-before-resolution":
            raise ArchiveError("provenance-reason", "Failed invocations without provenance require the failure-before-resolution reason.")
        if event["evidence_level"] in ("configured", "inherited") and event.get("resolved_model"):
            raise ArchiveError("provenance-escalation", "Configured/inherited provenance cannot claim a resolved model.")
        variant = PROVENANCE_MATRIX[event["evidence_level"]]
        if event["resolution_source"] not in variant["sources"] or event["resolution_reason_code"] not in variant["reasons"]:
            raise ArchiveError("provenance-combination", "Evidence level and resolution source are inconsistent.")
        if event["evidence_level"] in ("observed", "host-reported"):
            host_bound = (event["resolution_source"] == "host_receipt" and event["receipt"]) or (
                event["resolution_source"] == "tool_response" and event["host_evidence_ref"] == f"invocation:{event['invocation_id']}:tool-response")
            resolved = event["resolved_provider"] and (event["resolved_model"] or event["resolved_family"])
            if not host_bound or not resolved:
                raise ArchiveError("provenance-host-evidence", "Observed/host-reported provenance requires bound host evidence and concrete resolved fields.", "evidence/events")
            if event["resolution_reason_code"] is not None:
                raise ArchiveError("provenance-reason", "Complete host provenance cannot carry a degradation reason.")
        else:
            if any(event[field] is not None for field in ("resolved_provider", "resolved_model", "resolved_family", "host_evidence_ref")):
                raise ArchiveError("provenance-escalation", "Degraded provenance cannot claim resolved host facts.")
        validate_evidence_ref(event["output_evidence"], owner_kind="output", owner_id=event["invocation_id"], required=event["terminal_status"] == "succeeded")
        if event["terminal_status"] != "succeeded" and event.get("failure_reason_code") not in FAILURE_REASONS:
            raise ArchiveError("failure-reason", "Non-success invocation requires a closed failure reason.")
        if event["terminal_status"] == "succeeded" and (event["failure_reason_code"] is not None or event["failure_detail"] is not None):
            raise ArchiveError("failure-fields", "Succeeded invocation cannot carry failure fields.")
    elif kind == "artifact-captured":
        validate_identifier(event["artifact_id"], "artifact_id")
        if not isinstance(event["revision_id"], str) or not REVISION_ID_RE.fullmatch(event["revision_id"]):
            raise ArchiveError("revision-id", "Artifact revision id is invalid.")
        _timestamp(event["captured_at"], "captured_at")
        if not isinstance(event["evidence_mode"], str) or event["evidence_mode"] not in EVIDENCE_MODES or not isinstance(event["sha256"], str) or not HEX64_RE.fullmatch(event["sha256"]):
            raise ArchiveError("artifact-schema", "Artifact evidence mode or digest is invalid.")
        if not isinstance(event["size"], int) or isinstance(event["size"], bool) or event["size"] < 0:
            raise ArchiveError("artifact-schema", "Artifact size is invalid.")
        expected_capability = {"metadata-only": "identity-only", "redacted": "redacted-copy", "exact": "snapshot"}[event["evidence_mode"]]
        if event["reproduction_capability"] != expected_capability:
            raise ArchiveError("artifact-capability", "Artifact capability conflicts with its evidence mode.")
        validate_locator(event["source_locator"])
        snapshot = event["snapshot"]
        if event["evidence_mode"] == "metadata-only":
            if snapshot is not None:
                raise ArchiveError("artifact-snapshot", "Metadata-only artifact cannot own a snapshot.")
        else:
            if not isinstance(snapshot, dict) or set(snapshot) != {"path", "sha256", "size"}:
                raise ArchiveError("artifact-snapshot", "Snapshot reference is incomplete.")
            expected_path = f"evidence/artifacts/{event['artifact_id']}/snapshot"
            if normalize_relative(snapshot["path"]) != expected_path or not isinstance(snapshot["sha256"], str) or not HEX64_RE.fullmatch(snapshot["sha256"]) or not isinstance(snapshot["size"], int) or isinstance(snapshot["size"], bool) or snapshot["size"] < 0:
                raise ArchiveError("artifact-snapshot", "Snapshot identity conflicts with its owner.")
    elif kind == "terminal-decision":
        _timestamp(event["generated_at"], "generated_at")
        if event["decision_type"] == "reviewer-verdict":
            if event["review_kind"] not in ("fresh", "blank-slate"):
                raise ArchiveError("decision-review-kind", "Final reviewer must be fresh or blank-slate.")
            _uuid(event["reviewer_event_id"], "reviewer_event_id")
            _uuid(event["verdict_output_ref"], "verdict_output_ref")
            _text(event["verdict"], "verdict"); _text(event["verdict_output_ref"], "verdict_output_ref")
            if not event["verdict"] or not event["verdict_output_ref"]:
                raise ArchiveError("decision-review-evidence", "Reviewer decision requires verdict and output binding.")
        elif event["decision_type"] == "user-decision":
            expected_state = {"accept-terminal-b": "accepted-degraded-result", "accept-terminal-c": "accepted-stop"}
            if event["decision_kind"] not in expected_state or not isinstance(event["presented_degradations"], list) or event["accepted_state"] != expected_state.get(event["decision_kind"]):
                raise ArchiveError("user-decision-evidence", "User decision lacks fresh quote or auditable source.")
            _text(event["user_quote"], "user_quote"); _text(event["source_ref"], "source_ref")
            _uuid(event["source_ref"], "source_ref")
            if any(not isinstance(item, str) or not item for item in event["presented_degradations"]) or event["presented_degradations"] != sorted(set(event["presented_degradations"])):
                raise ArchiveError("user-decision-degradations", "Presented degradations must be a sorted unique string list.")
        else:
            raise ArchiveError("decision-type", "Terminal decision type is unsupported.")
    elif kind == "design-review-completion":
        _uuid(event["invocation_event_id"], "invocation_event_id"); _timestamp(event["completed_at"], "completed_at")
        _text(event["completion_status"], "completion_status"); _text(event["highlights_ref"], "highlights_ref")
        if not event["completion_status"] or not event["highlights_ref"]:
            raise ArchiveError("design-review-schema", "Design review completion requires status and highlights.")
    elif kind == "user-message":
        _timestamp(event["recorded_at"], "recorded_at")
        _text(event["host_message_id"], "host_message_id"); _text(event["user_quote"], "user_quote")


def validate_locator(locator: Any) -> None:
    if not isinstance(locator, dict) or locator.get("kind") not in ("workspace-relative", "external"):
        raise ArchiveError("locator-schema", "Source locator must use a closed tagged union.")
    if locator["kind"] == "workspace-relative":
        if set(locator) != {"kind", "workspace_id", "path"}:
            raise ArchiveError("locator-fields", "Workspace locator has forbidden or missing fields.")
        _text(locator["workspace_id"], "workspace_id"); normalize_relative(locator["path"])
    else:
        if set(locator) != {"kind", "display_locator", "portable", "authorization_ref"} or locator["portable"] is not False:
            raise ArchiveError("locator-fields", "External locator has forbidden or missing fields.")
        display = locator["display_locator"]
        _text(display, "display_locator"); _text(locator["authorization_ref"], "authorization_ref")
        if re.search(r"(?:^[A-Za-z]:[\\/]|^[/\\]{1,2})", display):
            raise ArchiveError("locator-secret", "External display locator must be redacted and non-resolvable.")


def validate_ledger(root: Path, events: list[dict[str, Any]], *,
                     acknowledged_orphan_reservations: frozenset[str] = frozenset()) -> list[str]:
    """Returns a sorted list of degradation strings for explicitly acknowledged orphan
    reservations (see the `ledger-invocation-orphan` handling below); empty when nothing
    was acknowledged. Every other integrity failure still raises `ArchiveError` — this
    function's default (`acknowledged_orphan_reservations=frozenset()`) reproduces the
    prior unconditional fail-closed behavior exactly."""
    path = root / "gate-ledger.jsonl"
    spawns = [e for e in events if e["event_type"] == "invocation-started" and e["invocation_kind"] == "spawn"]
    if not path.exists():
        if spawns:
            raise ArchiveError("ledger-missing", "Every Spawn requires the canonical reservation ledger.", "gate-ledger.jsonl")
        return []
    ledger: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_bytes().splitlines(), 1):
        try:
            item = strict_json_bytes(line)
        except Exception as exc:
            raise ArchiveError("ledger-malformed", f"Ledger line {number} is malformed: {exc}", "gate-ledger.jsonl") from exc
        if not isinstance(item, dict) or "event" not in item:
            raise ArchiveError("ledger-schema", f"Ledger line {number} is invalid.", "gate-ledger.jsonl")
        ledger.append(item)
    try:
        import budget_gate
        budget_gate.validate_integrity(root, ledger, budget_gate.read_state(root))
    except ImportError as exc:
        raise ArchiveError("ledger-validator-unavailable", "Canonical budget ledger validator is unavailable.", "gate-ledger.jsonl") from exc
    except Exception as exc:
        if exc.__class__.__name__ == "FailClosed":
            raise ArchiveError("ledger-strict-invalid", f"Canonical budget validator rejected the ledger: {exc}", "gate-ledger.jsonl") from exc
        raise
    reserves: dict[str, dict[str, Any]] = {}
    settles: dict[str, dict[str, Any]] = {}
    for item in ledger:
        if item["event"] == "reserved":
            rid = item.get("reservation_id")
            if not rid or rid in reserves:
                raise ArchiveError("ledger-reservation-duplicate", "Ledger reservation is missing or duplicated.", "gate-ledger.jsonl")
            reserves[rid] = item
        elif item["event"] in ("spawn_succeeded", "spawn_failed", "cancelled"):
            rid = item.get("reservation_id")
            if rid not in reserves or rid in settles:
                raise ArchiveError("ledger-settlement-orphan", "Ledger settlement is orphaned or duplicated.", "gate-ledger.jsonl")
            settles[rid] = item
    started = spawns
    by_reservation = {e["reservation_id"]: e for e in started}
    if len(by_reservation) != len(started):
        raise ArchiveError("invocation-reservation-duplicate", "Multiple invocations use one reservation.", "evidence/events")
    for rid, invocation in by_reservation.items():
        if rid not in reserves or rid not in settles:
            raise ArchiveError("ledger-binding-missing", "Invocation reservation is not fully settled.", "gate-ledger.jsonl")
        if reserves[rid].get("target_role") != invocation["role"]:
            raise ArchiveError("ledger-role-conflict", "Ledger role conflicts with invocation owner fact.", "gate-ledger.jsonl")
        if reserves[rid].get("target_round") != invocation["round"]:
            raise ArchiveError("ledger-round-conflict", "Ledger round conflicts with invocation owner fact.", "gate-ledger.jsonl")
    orphan_degradations: list[str] = []
    actually_orphaned: set[str] = set()
    for rid in reserves:
        if rid not in settles:
            raise ArchiveError("ledger-open", "Ledger contains an unsettled reservation.", "gate-ledger.jsonl")
        if rid not in by_reservation:
            actually_orphaned.add(rid)
            if rid in acknowledged_orphan_reservations:
                # Explicit, caller-declared degradation (opt-in only — see
                # `archive` CLI's `--declare-orphan-reservation`). The event stream stays
                # untouched (no invocation-started backfill); this only records, at the
                # manifest level, that a settled reservation's Spawn invocation was never
                # captured — an honest disclosure of a recording gap, not a fabricated fact.
                orphan_degradations.append(f"ledger:orphan-reservation:{rid}")
            else:
                raise ArchiveError("ledger-invocation-orphan", "Ledger reservation has no Spawn invocation.", "gate-ledger.jsonl")
    unused_acknowledgements = set(acknowledged_orphan_reservations) - actually_orphaned
    if unused_acknowledgements:
        raise ArchiveError("ledger-orphan-acknowledgement-invalid",
                            "Declared orphan reservation is not actually orphaned.", "gate-ledger.jsonl")
    terminals = {e["started_event_id"]: e for e in events if e["event_type"] == "invocation-terminal"}
    instances: set[str] = set()
    for rid, started_event in by_reservation.items():
        terminal = terminals.get(started_event["event_id"])
        if terminal is None:
            raise ArchiveError("ledger-invocation-open", "Budget-bound Spawn has no terminal event.", "evidence/events")
        settlement = settles[rid]
        expected = {"spawn_succeeded": {"succeeded"}, "spawn_failed": {"failed", "timeout"}, "cancelled": {"cancelled"}}[settlement["event"]]
        if terminal["terminal_status"] not in expected:
            raise ArchiveError("ledger-status-conflict", "Ledger settlement conflicts with invocation terminal status.", "gate-ledger.jsonl")
        if terminal.get("settlement_ref") != f"gate-ledger.jsonl:{rid}":
            raise ArchiveError("ledger-settlement-ref", "Invocation terminal does not bind the canonical settlement.", "evidence/events")
        if settlement["event"] == "spawn_succeeded":
            instance = settlement.get("instance_id")
            if not instance or terminal.get("instance_id") != instance or instance in instances:
                raise ArchiveError("ledger-instance-conflict", "Spawn instance is missing, duplicated, or conflicts with the ledger.", "gate-ledger.jsonl")
            instances.add(instance)
        elif terminal.get("instance_id") is not None and settlement.get("instance_id") not in (None, terminal.get("instance_id")):
            raise ArchiveError("ledger-instance-conflict", "Failed/cancelled Spawn instance conflicts with the ledger.", "gate-ledger.jsonl")
    return sorted(orphan_degradations)


def find_orphan_reservations(root: Path) -> list[str]:
    """Read-only diagnostic: which settled ledger reservations have no matching Spawn
    invocation-started event (candidates for `archive --declare-orphan-reservation`). Best
    effort and lenient by design — malformed ledger lines are skipped rather than raised, since
    this is an operator aid for deciding what to acknowledge, not part of the fail-closed
    validation path (`validate_ledger` remains the sole strict authority)."""
    root = Path(root)
    ledger_path = root / "gate-ledger.jsonl"
    if not ledger_path.exists():
        return []
    reserves: dict[str, dict[str, Any]] = {}
    settles: dict[str, dict[str, Any]] = {}
    for line in ledger_path.read_bytes().splitlines():
        if not line.strip():
            continue
        try:
            item = strict_json_bytes(line)
        except Exception:
            continue
        if not isinstance(item, dict) or "event" not in item:
            continue
        rid = item.get("reservation_id")
        if not rid:
            continue
        if item["event"] == "reserved":
            reserves[rid] = item
        elif item["event"] in ("spawn_succeeded", "spawn_failed", "cancelled"):
            settles[rid] = item
    started_rids: set[str] = set()
    try:
        for event in load_events(root):
            if event.get("event_type") == "invocation-started" and event.get("invocation_kind") == "spawn" and event.get("reservation_id"):
                started_rids.add(event["reservation_id"])
    except ArchiveError:
        pass
    return sorted(rid for rid in reserves if rid in settles and rid not in started_rids)


def project_manifest(root: Path, revision_id: str = "r1", parent: dict[str, Any] | None = None,
                      acknowledged_orphan_reservations: Iterable[str] = ()) -> dict[str, Any]:
    ack = frozenset(acknowledged_orphan_reservations)
    if any(not isinstance(rid, str) or not rid for rid in ack):
        raise ArchiveError("orphan-acknowledgement-invalid", "Acknowledged orphan reservation ids must be non-empty strings.", "gate-ledger.jsonl")
    events = load_events(root)
    graph_degradations = validate_event_graph(events)
    ledger_degradations = validate_ledger(root, events, acknowledged_orphan_reservations=ack)
    records = []
    for path in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
        if path.is_file() and path.name not in ("INDEX.md", "manifest.json"):
            if not is_root_allowed_name(path.name):
                raise ArchiveError("root-clutter", "Root file is outside the canonical allowlist.", path.name)
            data = path.read_bytes()
            digest, size = sha256_size(data)
            records.append({"path": path.name, "sha256": digest, "size": size})
    event_refs = []
    invocations, artifacts, decisions, advisories = [], [], [], []
    for event in events:
        rel = f"evidence/events/{event['sequence']:08d}-{event['event_id']}.json"
        data = (root / rel).read_bytes()
        digest, size = sha256_size(data)
        event_refs.append({"event_id": event["event_id"], "sequence": event["sequence"], "event_type": event["event_type"], "path": rel, "sha256": digest, "size": size})
        if event["event_type"] == "invocation-started":
            invocations.append({key: event[key] for key in (
                "event_id", "invocation_id", "event_type", "invocation_kind", "role", "phase",
                "round", "attempt", "parent_event_id", "parent_instance_id", "reservation_id",
                "requested_provider", "requested_model",
            )})
        elif event["event_type"] == "invocation-terminal":
            invocations.append({key: event[key] for key in (
                "event_id", "invocation_id", "event_type", "started_event_id", "terminal_status",
                "instance_id", "receipt", "settlement_ref", "resolved_provider", "resolved_model",
                "resolved_family", "backend", "backend_version", "host_evidence_ref",
                "evidence_level", "resolution_source", "resolution_reason_code",
            )})
        elif event["event_type"] == "artifact-captured":
            artifacts.append({key: event[key] for key in ("event_id", "artifact_id", "revision_id", "sha256", "size", "evidence_mode", "reproduction_capability", "source_locator")})
        elif event["event_type"] == "terminal-decision":
            decisions.append(event["event_id"])
        elif event["event_type"] == "design-review-completion":
            advisories.append(event["event_id"])
    final_ref = decisions[-1] if decisions else None
    final_event = next((e for e in events if e["event_id"] == final_ref), None)
    final_decision = None
    if final_event:
        final_decision = {
            "event_id": final_event["event_id"],
            "type": final_event["decision_type"],
            "value": final_event.get("verdict", final_event.get("accepted_state")),
        }
    allowed_blobs: set[str] = set()
    for event in events:
        for field in ("prompt_evidence", "output_evidence", "snapshot"):
            ref = event.get(field)
            if isinstance(ref, dict) and ref.get("path"):
                allowed_blobs.add(normalize_relative(ref["path"]))
    cursor = parent
    revision_chain = []
    seen_revisions: set[str] = set()
    while cursor is not None:
        if not isinstance(cursor, dict) or set(cursor) != {"revision_id", "path", "sha256"}:
            raise ArchiveError("revision-schema", "Parent revision reference is invalid.", "manifest.json")
        rel = normalize_relative(cursor["path"])
        revision_chain.append({"revision_id": cursor["revision_id"], "path": rel, "sha256": cursor["sha256"]})
        if rel in seen_revisions:
            raise ArchiveError("revision-cycle", "Revision history contains a cycle.", rel)
        seen_revisions.add(rel); allowed_blobs.add(rel)
        try:
            old_manifest = strict_json_bytes((root / rel).read_bytes())
        except Exception as exc:
            raise ArchiveError("revision-malformed", "Revision owner manifest is missing or malformed.", rel) from exc
        cursor = old_manifest.get("parent_revision")
    blobs = []
    auxiliary_evidence = []
    evidence_root = root / "evidence"
    if evidence_root.exists():
        reserved_files: list[Path] = []
        auxiliary_files: list[Path] = []
        for path in evidence_root.rglob("*"):
            if not path.is_file():
                continue
            top = path.relative_to(evidence_root).parts[0]
            if top == "events":
                continue  # event log itself; tracked via `event_refs`, never a blob
            (reserved_files if top in EVIDENCE_RESERVED_SUBDIRS else auxiliary_files).append(path)
        actual_blobs = {path.relative_to(root).as_posix() for path in reserved_files}
        if actual_blobs != allowed_blobs:
            extra, missing = sorted(actual_blobs - allowed_blobs), sorted(allowed_blobs - actual_blobs)
            problem = extra[0] if extra else missing[0]
            raise ArchiveError("evidence-orphan", f"Evidence owner closure differs; extra={extra}, missing={missing}.", problem)
        for rel in sorted(allowed_blobs, key=str.casefold):
            path = root / rel
            data = path.read_bytes()
            digest, size = sha256_size(data)
            blobs.append({"path": rel, "sha256": digest, "size": size})
        # Auxiliary evidence (plan Phase 5 addendum, orchestrator-directed extension): any file
        # under `evidence/` whose top segment is not one of the reserved, event-derived
        # subdirectories. Imported and disclosed by default (no opt-in flag) — this is a
        # capability grant matching "the archiver must not reject a legitimate generator's
        # established product" (the same philosophy as step 3's root allowlist unification),
        # not a validation relaxation: nothing that used to pass now passes differently, and
        # everything imported is hashed and listed, never silently dropped. It still goes
        # through every existing path-safety check (`ensure_safe_tree`'s symlink/reparse/
        # device-name/Unicode-collision guards run over the whole tree unconditionally) and,
        # defensively, the same common-secret basename refusal `capture_artifact`/
        # `_read_regular_file` already apply at capture time — reused here rather than
        # reinvented, so an obvious credential file cannot slip in through this newer, broader
        # import path just because it bypasses the narrower capture-time API.
        for path in sorted(auxiliary_files, key=lambda p: p.relative_to(root).as_posix().casefold()):
            rel = path.relative_to(root).as_posix()
            if path.name.casefold() in SECRET_NAMES:
                raise ArchiveError("auxiliary-evidence-secret-refused", "Common secret files are refused by default.", rel)
            data = path.read_bytes()
            digest, size = sha256_size(data)
            auxiliary_evidence.append({"path": rel, "sha256": digest, "size": size})
    degradations = sorted({
        f"model-provenance:{e['evidence_level']}" for e in events
        if e["event_type"] == "invocation-terminal" and e["evidence_level"] != "observed"
    } | {
        f"artifact:{e['artifact_id']}:{e['reproduction_capability']}" for e in events
        if e["event_type"] == "artifact-captured" and e["reproduction_capability"] != "snapshot"
    } | set(graph_degradations) | set(ledger_degradations))
    if os.name == "nt":
        degradations.append("permissions:acl-confidentiality-not-verified")
        degradations.sort()
    result = {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "revision_id": revision_id,
        "parent_revision": parent,
        "revision_chain": revision_chain,
        "records": records,
        "events": event_refs,
        "blobs": blobs,
        "invocations": invocations,
        "artifacts": artifacts,
        "final_verdict_ref": final_ref,
        "final_decision": final_decision,
        "design_review_completion_refs": advisories,
        "degradations": degradations,
        "risks": ["same-writer-rewrite-undetectable"],
        "source_resolution": "disabled",
    }
    if ack:
        # Only present when at least one orphan reservation was explicitly acknowledged —
        # omitted (rather than an empty list) in the overwhelmingly common default case so
        # every archive predating this field, and every archive that never uses the opt-in
        # `--declare-orphan-reservation` escape hatch, keeps byte-identical manifest shape.
        # Schema version is not bumped for this addition: it is purely additive and
        # self-consistently derived (`validate_archive` reads this same key back out of the
        # stored manifest before recomputing `project_manifest`), so it never breaks
        # `manifest-projection-mismatch` re-validation of pre-existing schema 1.0 archives.
        result["acknowledged_orphan_reservations"] = sorted(ack)
    if auxiliary_evidence:
        # Same omit-when-empty convention as `acknowledged_orphan_reservations` above: keeps
        # every archive with no auxiliary evidence byte-identical to pre-Phase-5 manifests, no
        # schema version bump needed.
        result["auxiliary_evidence"] = sorted(auxiliary_evidence, key=lambda item: item["path"].casefold())
    return result


def validate_event_graph(events: list[dict[str, Any]]) -> list[str]:
    by_id = {e["event_id"]: e for e in events}
    started_by_invocation: dict[str, dict[str, Any]] = {}
    terminals: set[str] = set()
    terminal_by_start: dict[str, dict[str, Any]] = {}
    receipts: set[str] = set()
    artifact_revisions: set[tuple[str, str]] = set()
    for event in events:
        if event["event_type"] == "invocation-started":
            if event["invocation_id"] in started_by_invocation:
                raise ArchiveError("invocation-id-duplicate", "Invocation id is duplicated.", "evidence/events")
            started_by_invocation[event["invocation_id"]] = event
            if event["invocation_kind"] == "continue":
                parent = by_id.get(event["parent_event_id"])
                if not parent or parent.get("event_type") != "invocation-started" or parent.get("invocation_kind") != "spawn":
                    raise ArchiveError("invocation-parent", "Continue parent is not a Spawn start event.", "evidence/events")
                if parent["sequence"] >= event["sequence"]:
                    raise ArchiveError("invocation-parent-order", "Continue parent must precede the child.", "evidence/events")
        elif event["event_type"] == "invocation-terminal":
            sid = event["started_event_id"]
            if sid in terminals or sid not in by_id or by_id[sid].get("invocation_id") != event["invocation_id"]:
                raise ArchiveError("terminal-duplicate-or-orphan", "Invocation terminal is duplicated or orphaned.", "evidence/events")
            terminals.add(sid)
            terminal_by_start[sid] = event
            receipt = event.get("receipt")
            if receipt and receipt in receipts:
                raise ArchiveError("receipt-duplicate", "Host receipt is duplicated.", "evidence/events")
            if receipt:
                receipts.add(receipt)
        elif event["event_type"] == "artifact-captured":
            key = (event["artifact_id"].casefold(), event["revision_id"].casefold())
            if key in artifact_revisions:
                raise ArchiveError("artifact-revision-duplicate", "Artifact revision identity is duplicated.", "evidence/events")
            artifact_revisions.add(key)
    open_events = [e["event_id"] for e in started_by_invocation.values() if e["event_id"] not in terminals]
    if open_events:
        raise ArchiveError("invocation-open", "Archive contains unclosed invocations.", "evidence/events")
    for started in started_by_invocation.values():
        if started["invocation_kind"] != "continue":
            continue
        parent_terminal = terminal_by_start.get(started["parent_event_id"])
        terminal = terminal_by_start[started["event_id"]]
        if not parent_terminal or not parent_terminal.get("instance_id"):
            raise ArchiveError("continue-parent-open", "Continue parent has no closed instance identity.", "evidence/events")
        if started["parent_instance_id"] != parent_terminal["instance_id"] or terminal.get("instance_id") != parent_terminal["instance_id"]:
            raise ArchiveError("continue-instance-conflict", "Continue must bind the same instance as its Spawn parent.", "evidence/events")
    decisions = [e for e in events if e["event_type"] == "terminal-decision"]
    previous = None
    graph_degradations: list[str] = []
    for index, decision in enumerate(decisions):
        if decision.get("supersedes_decision_event_id") != previous:
            raise ArchiveError("decision-chain", "Terminal decisions must form one append-only supersession chain.", "evidence/events")
        previous = decision["event_id"]
        is_final = index == len(decisions) - 1
        if decision["decision_type"] == "reviewer-verdict":
            # Chain integrity (the `supersedes_decision_event_id` check above) and the final,
            # non-superseded decision's authority are validated at full strength unconditionally.
            # A decision that a *later* decision has already superseded no longer determines
            # `final_decision` (see `project_manifest`'s `final_ref = decisions[-1]`) — so an
            # invalid `reviewer_event_id` ref on a superseded entry can never again make the
            # archive assert an unauthorized owner. Requiring it to still resolve would mean a
            # single mis-recorded historical decision permanently fail-closes the archive with
            # no compliant repair path other than superseding it — exactly the defect this
            # relaxation removes. The failure is not hidden: it is surfaced as an auditable
            # `degradations` entry (rendered in INDEX.md) instead of raising.
            if is_final:
                validate_reviewer_verdict_authority(events, decision)
            else:
                try:
                    validate_reviewer_verdict_authority(events, decision)
                except ArchiveError as exc:
                    graph_degradations.append(f"decision:superseded-ref-unverified:{decision['event_id']}:{exc.code}")
        else:
            prior = [e for e in events if e["sequence"] < decision["sequence"]]
            message = by_id.get(decision["source_ref"])
            if not message or message.get("event_type") != "user-message" or message["sequence"] >= decision["sequence"] or message["user_quote"] != decision["user_quote"]:
                raise ArchiveError("user-decision-source", "User decision must bind a prior canonical user-message event with the exact quote.", "evidence/events")
            actual = sorted({
                f"model-provenance:{e['evidence_level']}" for e in prior
                if e["event_type"] == "invocation-terminal" and e["evidence_level"] != "observed"
            } | {
                f"artifact:{e['artifact_id']}:{e['reproduction_capability']}" for e in prior
                if e["event_type"] == "artifact-captured" and e["reproduction_capability"] != "snapshot"
            })
            if decision["presented_degradations"] != actual:
                raise ArchiveError("user-decision-degradations", "User decision must present exactly the degradations present at decision time.", "evidence/events")
    return sorted(graph_degradations)


def _verify_evidence_bytes(root: Path, events: list[dict[str, Any]]) -> None:
    for event in events:
        references = []
        for field in ("prompt_evidence", "output_evidence", "snapshot"):
            ref = event.get(field)
            if isinstance(ref, dict) and ref.get("path"):
                references.append(ref)
        for ref in references:
            rel = normalize_relative(ref["path"])
            try:
                data = (root / rel).read_bytes()
            except OSError as exc:
                raise ArchiveError("evidence-bytes-missing", "Event-owned evidence bytes are missing.", rel) from exc
            if sha256_size(data) != (ref.get("sha256"), ref.get("size")):
                raise ArchiveError("evidence-bytes-mismatch", "Event-owned evidence bytes differ from their identity.", rel)


def _anchor_slug(value: str) -> str:
    value = value.strip().casefold()
    value = re.sub(r"[^\w\- \u4e00-\u9fff]", "", value)
    return re.sub(r"[\s]+", "-", value)


def _validate_markdown_links(root: Path, records: list[dict[str, Any]]) -> None:
    link_re = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
    for record in records:
        rel = record["path"]
        if not rel.endswith(".md"):
            continue
        text = (root / rel).read_text(encoding="utf-8")
        for raw_target in link_re.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith(("/", "\\")) or ".converge/active/" in target:
                raise ArchiveError("markdown-link-absolute", "Canonical Markdown uses an absolute or active-path link.", rel)
            path_part, marker, anchor = target.partition("#")
            if path_part:
                combined = (PurePosixPath(rel).parent / path_part).as_posix()
                normalized = normalize_relative(combined)
                target_path = root / normalized
            else:
                target_path = root / rel
                normalized = rel
            if not target_path.is_file():
                raise ArchiveError("markdown-link-missing", "Canonical Markdown link target does not exist.", rel)
            if marker and anchor and target_path.suffix.casefold() == ".md":
                headings = {
                    _anchor_slug(match.group(1))
                    for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", target_path.read_text(encoding="utf-8"), re.MULTILINE)
                }
                if anchor.casefold() not in headings:
                    raise ArchiveError("markdown-anchor-missing", "Canonical Markdown link anchor does not exist.", rel)


def _validate_decision_cross_refs(root: Path, manifest: dict[str, Any]) -> None:
    decision = manifest.get("final_decision")
    if not decision:
        raise ArchiveError("final-decision-missing", "A valid archive requires one terminal decision.", "evidence/events")
    rounds = [r["path"] for r in manifest["records"] if ROUND_RE.fullmatch(r["path"])]
    final_round = max(rounds, key=lambda p: int(p[6:-3])) if rounds else None
    for rel in (final_round, "retrospective.md"):
        if rel is None or not (root / rel).is_file():
            raise ArchiveError("decision-summary-missing", "Final round and retrospective are both required.", rel)
        text = (root / rel).read_text(encoding="utf-8")
        id_marker = f"terminal_decision_event_id: {decision['event_id']}"
        value_marker = f"terminal_decision_value: {decision['value']}"
        if id_marker not in text or value_marker not in text:
            raise ArchiveError("decision-cross-ref", "Final round/retrospective do not reference the manifest decision id and value.", rel)


def _validate_revision(root: Path, manifest: dict[str, Any]) -> None:
    parent = manifest.get("parent_revision")
    if parent is None:
        return
    if not isinstance(parent, dict) or set(parent) != {"revision_id", "path", "sha256"}:
        raise ArchiveError("revision-schema", "Parent revision reference is invalid.", "manifest.json")
    rel = normalize_relative(parent["path"])
    if rel != f"evidence/revisions/{parent['revision_id']}/manifest.json":
        raise ArchiveError("revision-path", "Parent revision path does not match its id.", rel)
    data = (root / rel).read_bytes()
    if hashlib.sha256(data).hexdigest() != parent["sha256"]:
        raise ArchiveError("revision-hash", "Parent revision manifest hash differs.", rel)
    try:
        old = strict_json_bytes(data)
    except Exception as exc:
        raise ArchiveError("revision-malformed", "Parent revision manifest is malformed.", rel) from exc
    if old.get("revision_id") != parent["revision_id"] or old.get("schema_id") != SCHEMA_ID:
        raise ArchiveError("revision-identity", "Parent revision identity differs.", rel)


def _declared_file_refs(manifest: dict[str, Any]) -> dict[str, tuple[str, int]]:
    refs: dict[str, tuple[str, int]] = {}
    # `auxiliary_evidence` may be entirely absent (omit-when-empty convention) — `or []`
    # normalizes that to an empty collection rather than tripping the type check below.
    for collection in (manifest.get("records"), manifest.get("events"), manifest.get("blobs"),
                       manifest.get("auxiliary_evidence") or []):
        if not isinstance(collection, list):
            raise ArchiveError("manifest-schema", "Manifest record/event collections must be arrays.", "manifest.json")
        for item in collection:
            try:
                rel = normalize_relative(item["path"])
                digest, size = item["sha256"], item["size"]
            except (KeyError, TypeError) as exc:
                raise ArchiveError("manifest-schema", "Manifest file reference is incomplete.", "manifest.json") from exc
            if rel in refs or not isinstance(digest, str) or not HEX64_RE.fullmatch(digest) or not isinstance(size, int):
                raise ArchiveError("manifest-file-ref", "Manifest file reference is duplicated or invalid.", rel)
            refs[rel] = (digest, size)
    return refs


def validate_archive(root: Path, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    # Resolve once, up front, and reuse the resolved root everywhere below — `ensure_safe_tree`
    # always returns absolute resolved file paths internally, so comparing them against an
    # unresolved (possibly relative, e.g. from a CLI caller passing a relative `root`) `Path`
    # via `.relative_to()` raises "... is not in the subpath of ..." even though the archive
    # itself is perfectly valid. This was the "Windows relative path subpath 误报" bug: it
    # reproduces on any OS, not only Windows, whenever `root` is passed as a relative path.
    root = ensure_safe_root(Path(root))
    ensure_safe_tree(root)
    if manifest is None:
        try:
            manifest = strict_json_bytes((root / "manifest.json").read_bytes())
        except Exception as exc:
            raise ArchiveError("manifest-malformed", f"Manifest cannot be parsed: {exc}", "manifest.json") from exc
    if manifest.get("schema_id") != SCHEMA_ID or manifest.get("schema_version") != SCHEMA_VERSION:
        raise ArchiveError("manifest-unsupported", "Manifest schema identity/version is unsupported.", "manifest.json")
    refs = _declared_file_refs(manifest)
    actual_files = {p.relative_to(root).as_posix() for p in ensure_safe_tree(root)}
    permitted = set(refs) | {"manifest.json", "INDEX.md"}
    if actual_files != permitted:
        extra, missing = sorted(actual_files - permitted), sorted(permitted - actual_files)
        raise ArchiveError("tree-closure", f"Archive tree differs from manifest; extra={extra}, missing={missing}.", extra[0] if extra else missing[0])
    for rel, (digest, size) in refs.items():
        data = (root / rel).read_bytes()
        if sha256_size(data) != (digest, size):
            raise ArchiveError("content-mismatch", "Committed content hash or byte size differs.", rel)
    acknowledged = frozenset(manifest.get("acknowledged_orphan_reservations") or ())
    events = load_events(root)
    validate_event_graph(events)
    _verify_evidence_bytes(root, events)
    validate_ledger(root, events, acknowledged_orphan_reservations=acknowledged)
    _validate_markdown_links(root, manifest["records"])
    _validate_decision_cross_refs(root, manifest)
    _validate_revision(root, manifest)
    projected = project_manifest(root, manifest["revision_id"], manifest.get("parent_revision"),
                                  acknowledged_orphan_reservations=acknowledged)
    if projected != manifest:
        raise ArchiveError("manifest-projection-mismatch", "Manifest differs from immutable owner facts.", "manifest.json")
    if (root / "INDEX.md").read_bytes() != render_index_bytes(manifest):
        raise ArchiveError("index-mismatch", "INDEX.md is not the deterministic manifest projection.", "INDEX.md", "Regenerate INDEX.md from the validated manifest.")
    return manifest


def render_index_bytes(manifest: dict[str, Any]) -> bytes:
    decision = manifest.get("final_decision")
    if decision:
        decision_line = f"- value: {decision['value']}\n- type: {decision['type']}\n- event: [event](evidence/events/{next(e['path'].split('/')[-1] for e in manifest['events'] if e['event_id'] == decision['event_id'])})"
    else:
        decision_line = "- none (archive is not eligible until a terminal decision exists)"
    degradations = manifest.get("degradations") or []
    deg_lines = "\n".join(f"- {item}" for item in degradations) if degradations else "- none"
    parent = manifest.get("parent_revision")
    revisions = f"- current: {manifest['revision_id']}"
    for prior in manifest.get("revision_chain", []):
        revisions += f"\n- prior: [{prior['revision_id']}]({prior['path']}) sha256={prior['sha256']}"
    timeline = "\n".join(
        f"- {event['sequence']:04d} `{event['event_type']}` [{event['event_id']}]({event['path']})"
        for event in manifest.get("events", [])
    ) or "- none"
    provenance = "\n".join(
        "- `{event_id}` {kind}: requested={requested}; resolved={resolved}; "
        "evidence={level}; source={source}; reason={reason}".format(
            event_id=item["event_id"], kind=item["event_type"],
            requested="/".join(filter(None, (item.get("requested_provider"), item.get("requested_model")))) or "unavailable",
            resolved="/".join(filter(None, (item.get("resolved_provider"), item.get("resolved_model"), item.get("resolved_family")))) or "unavailable",
            level=item.get("evidence_level", "pending"), source=item.get("resolution_source", "pending"),
            reason=item.get("resolution_reason_code") or "none",
        ) for item in manifest.get("invocations", [])
    ) or "- none"
    artifacts = "\n".join(
        f"- `{item['artifact_id']}@{item['revision_id']}` mode={item['evidence_mode']}; capability={item['reproduction_capability']}; locator={json.dumps(item['source_locator'], ensure_ascii=False, sort_keys=True)}; sha256={item['sha256']}"
        for item in manifest.get("artifacts", [])
    ) or "- none"
    auxiliary_evidence = "\n".join(
        f"- [{item['path']}]({item['path']}) sha256={item['sha256']} size={item['size']}"
        for item in manifest.get("auxiliary_evidence") or []
    ) or "- none"
    risks = "\n".join(f"- {item}" for item in manifest.get("risks", [])) or "- none"
    records = {item["path"] for item in manifest.get("records", [])}
    next_reads = []
    rounds = sorted((p for p in records if ROUND_RE.fullmatch(p)), key=lambda p: int(p[6:-3]))
    if rounds:
        next_reads.append(f"- [Final round]({rounds[-1]})")
    if "retrospective.md" in records:
        next_reads.append("- [Retrospective](retrospective.md)")
    if decision:
        event_path = next(e["path"] for e in manifest["events"] if e["event_id"] == decision["event_id"])
        next_reads.append(f"- [Terminal decision evidence]({event_path})")
    if "design-review.md" in records:
        next_reads.append("- [Design-review highlights](design-review.md)")
    if not next_reads:
        next_reads.append("- none")
    text = f"""# Converge Archive Index

## Decision

{decision_line}

## Integrity & Threat Boundary

- schema: `{manifest['schema_id']} {manifest['schema_version']}`
- status: archived only when this directory is under the canonical done root and `check` reports valid
- guarantee: archive-time internal consistency, structural integrity, and traceable declared provenance
- does not guarantee: historical truth or resistance to a same-permission writer rewriting the whole archive and Git history

## Degradations

{deg_lines}

## Revision Timeline

{revisions}

## Event Timeline

{timeline}

## Model Provenance

{provenance}

## Artifact Provenance

{artifacts}

## Auxiliary Evidence (non-event-derived)

Imported and hash-verified, but not part of the event graph and not carrying any provenance
claim — see `EVIDENCE_RESERVED_SUBDIRS` in the Archive Contract for what *is* event-derived.

{auxiliary_evidence}

## Residual Risks

{risks}

## Next Reads

{chr(10).join(next_reads)}
"""
    return text.encode("utf-8")


def check_archive(root: Path) -> list[dict[str, str | None]]:
    manifest_path = Path(root) / "manifest.json"
    if not manifest_path.exists():
        return [{"code": "legacy-unverifiable", "summary": "No Archive Contract manifest is present.", "path": None,
                 "next_action": "Use archive for active content; do not rewrite legacy archives in place."}]
    try:
        manifest = strict_json_bytes(manifest_path.read_bytes())
    except Exception as exc:
        return [ArchiveError("manifest-malformed", f"Manifest exists but is not strict JSON: {exc}", "manifest.json",
                             "Correct the strict JSON encoding or restore the committed manifest.").diagnostic()]
    if not isinstance(manifest, dict):
        return [ArchiveError("manifest-malformed", "Manifest must be a JSON object.", "manifest.json").diagnostic()]
    schema_id, version = manifest.get("schema_id"), manifest.get("schema_version")
    if schema_id != SCHEMA_ID or version != SCHEMA_VERSION:
        reason = "unversioned" if schema_id is None or version is None else ("foreign-schema" if schema_id != SCHEMA_ID else "newer-version")
        return [ArchiveError(f"manifest-unsupported:{reason}", "Manifest schema is unsupported.", "manifest.json",
                             "Use a reader that supports this schema; do not downgrade or rewrite it.").diagnostic()]
    try:
        validate_archive(Path(root), manifest)
        return []
    except ArchiveError as exc:
        return [exc.diagnostic()]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [ArchiveError("archive-validation-error", f"Archive validation could not complete: {exc}", None,
                             "Correct the filesystem/input condition and retry read-only check.").diagnostic()]
