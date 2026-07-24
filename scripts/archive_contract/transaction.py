"""Single-writer staging, archive, reopen, and recovery transactions."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .model import (
    ARCHIVE_TOTAL_LIMIT, ArchiveError, canonical_json_bytes, ensure_safe_root,
    ensure_safe_tree, owner_process_liveness, strict_json_bytes, validate_archive,
    validate_identifier,
)

# Distinguishable terminal statuses returned by `archive()`/`archive_reliable()`. Both mean
# the archive body at `done_root/slug` is already committed and independently `valid-v1` —
# callers must never treat "cleanup_pending" as an overall failure (plan Phase 5 step 2).
STATUS_COMMITTED = "committed"
STATUS_CLEANUP_PENDING = "archive_valid_cleanup_pending"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _same_volume(left: Path, right: Path) -> bool:
    return os.stat(left).st_dev == os.stat(right).st_dev


class SlugLock:
    def __init__(self, root: Path, slug: str):
        self.path = root / f".archive-{slug}.lock"
        self.fd = None

    def __enter__(self):
        for _ in range(2):
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.write(self.fd, canonical_json_bytes({"pid": os.getpid(), "nonce": uuid.uuid4().hex, "started_at": _now()}))
                os.fsync(self.fd)
                return self
            except FileExistsError as exc:
                try:
                    before = self.path.lstat()
                    owner_bytes = self.path.read_bytes()
                    owner = strict_json_bytes(owner_bytes)
                    pid = owner.get("pid") if isinstance(owner, dict) else None
                except (OSError, ValueError):
                    pid = None
                if owner_process_liveness(pid) == "dead":
                    after = self.path.lstat()
                    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) or self.path.read_bytes() != owner_bytes:
                        raise ArchiveError("archive-lock-conflict", "Lock identity changed during dead-owner recovery.", self.path.name) from exc
                    self.path.unlink(missing_ok=True)
                    continue
                raise ArchiveError("archive-lock-conflict", "Archive/reopen lock is live or cannot be safely reclaimed.", self.path.name) from exc
        raise ArchiveError("archive-lock-conflict", "Archive/reopen lock recovery could not acquire ownership.", self.path.name)

    def __exit__(self, exc_type, exc, tb):
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def _durable_write(path: Path, data: bytes) -> None:
    temp = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb", closefd=False) as handle:
                handle.write(data); handle.flush()
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(temp, path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def _write_journal(path: Path, state: str, **extra) -> None:
    _durable_write(path, canonical_json_bytes({"state": state, "updated_at": _now(), **extra}))


def _remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _recover_archive(journal: Path, active_root: Path, done_root: Path, slug: str) -> tuple[Path, str] | None:
    """Resolve an interrupted archive to one authoritative copy, then retry/return.

    Returns `None` when recovery determined no committed archive exists yet (caller should
    proceed with a fresh attempt), or `(target, status)` when a valid `done_root/slug` already
    exists — `status` is `STATUS_CLEANUP_PENDING` when the committed archive is valid but
    residual backup/staging cleanup could not complete (e.g. OneDrive reparse WinError 5),
    `STATUS_COMMITTED` otherwise. A cleanup failure here must never be reported as recovery
    failure: the archive body's validity has already been independently re-verified.
    """
    if not journal.exists():
        return None
    try:
        record = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise ArchiveError("journal-malformed", "Archive transaction journal is malformed.", journal.name) from exc
    if record.get("operation", "archive") != "archive" or record.get("slug") != slug:
        raise ArchiveError("journal-owner-conflict", "Transaction journal does not belong to this archive.", journal.name)
    source, target = active_root / slug, done_root / slug
    staging = active_root / record.get("staging", "__invalid__")
    backup = active_root / record.get("backup", "__invalid__")
    state = record.get("state")
    if state == "committed" and target.is_dir():
        validate_archive(target)
        try:
            _remove_tree(backup); _remove_tree(staging); journal.unlink()
        except OSError:
            return target, STATUS_CLEANUP_PENDING
        return target, STATUS_COMMITTED
    if source.is_dir():
        _remove_tree(staging); _remove_tree(backup); journal.unlink()
        return None
    if backup.is_dir():
        if target.exists():
            _remove_tree(target)
        os.replace(backup, source)
        _remove_tree(staging); journal.unlink()
        return None
    if target.is_dir():
        validate_archive(target)
        try:
            _remove_tree(staging); journal.unlink()
        except OSError:
            return target, STATUS_CLEANUP_PENDING
        return target, STATUS_COMMITTED
    raise ArchiveError("journal-authority-missing", "Recovery found no authoritative active, backup, or done copy.", journal.name)


def _finish_reopen(journal: Path, active_root: Path, done_root: Path, slug: str) -> Path:
    record = json.loads(journal.read_text(encoding="utf-8"))
    if record.get("operation") != "reopen" or record.get("slug") != slug:
        raise ArchiveError("journal-owner-conflict", "Transaction journal does not belong to this reopen.", journal.name)
    source, target = done_root / slug, active_root / slug
    if source.is_dir() and not target.exists():
        os.replace(source, target)
        _write_journal(journal, "reopen-moved", **{k: v for k, v in record.items() if k not in ("state", "updated_at")})
    if not target.is_dir() or source.exists():
        raise ArchiveError("journal-authority-conflict", "Reopen recovery cannot identify one authoritative copy.", journal.name)
    committed_manifest = target / "manifest.json"
    stored_manifest = target / "evidence" / "revisions" / record["parent_revision_id"] / "manifest.json"
    if committed_manifest.exists():
        old_bytes = committed_manifest.read_bytes()
    elif stored_manifest.exists():
        old_bytes = stored_manifest.read_bytes()
    else:
        raise ArchiveError("reopen-parent-missing", "Reopen recovery cannot find the parent manifest bytes.", "manifest.json")
    if hashlib.sha256(old_bytes).hexdigest() != record["parent_sha256"]:
        raise ArchiveError("reopen-parent-mismatch", "Reopen parent manifest changed during recovery.", "manifest.json")
    revision_dir = target / "evidence" / "revisions" / record["parent_revision_id"]
    revision_dir.mkdir(parents=True, exist_ok=True)
    revision_manifest = revision_dir / "manifest.json"
    if revision_manifest.exists() and revision_manifest.read_bytes() != old_bytes:
        raise ArchiveError("reopen-revision-conflict", "Stored parent revision conflicts with the committed manifest.", str(revision_manifest))
    if not revision_manifest.exists():
        _durable_write(revision_manifest, old_bytes)
    _write_journal(journal, "reopen-parent-stored", **{k: v for k, v in record.items() if k not in ("state", "updated_at")})
    (target / "INDEX.md").unlink(missing_ok=True)
    (target / "manifest.json").unlink(missing_ok=True)
    marker = {k: record[k] for k in ("revision_id", "parent_revision_id", "parent_path", "parent_sha256", "reopened_at")}
    marker_path = target / ".reopen-state.json"
    if marker_path.exists() and marker_path.read_bytes() != canonical_json_bytes(marker):
        raise ArchiveError("reopen-marker-conflict", "Reopen marker conflicts with journal state.", marker_path.name)
    if not marker_path.exists():
        _durable_write(marker_path, canonical_json_bytes(marker))
    _write_journal(journal, "reopen-marker-stored", **{k: v for k, v in record.items() if k not in ("state", "updated_at")})
    journal.unlink()
    return target


def _copy_tree_safe(source: Path, target: Path) -> None:
    """Copy regular files through verified handles; never follow filesystem links."""
    files = ensure_safe_tree(source)
    target.mkdir(mode=0o700)
    for current, dirs, _ in os.walk(source, followlinks=False):
        relative = Path(current).relative_to(source)
        for name in dirs:
            (target / relative / name).mkdir(mode=0o700)
    total = 0
    for original in files:
        relative = original.relative_to(source)
        before = original.lstat()
        with original.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise ArchiveError("copy-toctou", "Source identity changed before capture.", relative.as_posix())
            chunks = []
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > ARCHIVE_TOTAL_LIMIT:
                    raise ArchiveError("archive-too-large", "Archive exceeds the configured total byte limit.", relative.as_posix())
                chunks.append(chunk)
        after = original.lstat()
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if identity_before != identity_after or not stat.S_ISREG(after.st_mode):
            raise ArchiveError("copy-toctou", "Source changed while staging was captured.", relative.as_posix())
        destination = target / relative
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb", closefd=False) as handle:
                for chunk in chunks:
                    handle.write(chunk)
                handle.flush()
            os.fsync(fd)
        finally:
            os.close(fd)


def _restrict_permissions(root: Path) -> None:
    for path in ensure_safe_tree(root):
        try:
            path.chmod(0o600)
        except OSError:
            pass
    for current, dirs, _ in os.walk(root):
        for name in dirs:
            try:
                (Path(current) / name).chmod(0o700)
            except OSError:
                pass


def archive(active_root: Path, done_root: Path, slug: str,
            prepare: Callable[[Path], None]) -> tuple[Path, str]:
    """Returns `(target, status)`. `status` is `STATUS_CLEANUP_PENDING` when the archive body
    is committed and independently re-validated at `target` but residual backup/staging
    cleanup failed (never treated as an overall failure — plan Phase 5 step 2); a later call
    with the same arguments safely retries only the pending cleanup via `_recover_archive`,
    without re-copying or re-validating the already-committed body."""
    validate_identifier(slug, "slug", charset="unicode-safe")
    active_root, done_root = ensure_safe_root(Path(active_root)), ensure_safe_root(Path(done_root))
    source, target = active_root / slug, done_root / slug
    if not _same_volume(active_root, done_root):
        raise ArchiveError("cross-volume", "Cross-volume atomic archive is unsupported.", None)
    with SlugLock(active_root, slug):
        journal = active_root / f".archive-{slug}.journal.json"
        recovered = _recover_archive(journal, active_root, done_root, slug)
        if recovered is not None:
            return recovered
        ensure_safe_root(source)
        if target.exists():
            raise ArchiveError("done-conflict", "Done target already exists; archive never overwrites.", None)
        staging = active_root / f".{slug}.staging-{uuid.uuid4().hex}"
        backup = active_root / f".{slug}.backup-{uuid.uuid4().hex}"
        try:
            _write_journal(journal, "preparing", operation="archive", slug=slug,
                           staging=staging.name, backup=backup.name)
            ensure_safe_tree(source)
            _copy_tree_safe(source, staging)
            prepare(staging)
            _restrict_permissions(staging)
            validate_archive(staging)
            os.replace(source, backup)
            _write_journal(journal, "source-backed-up", operation="archive", slug=slug,
                           staging=staging.name, backup=backup.name)
            os.replace(staging, target)
            _write_journal(journal, "committed", operation="archive", slug=slug,
                           staging=staging.name, backup=backup.name)
            try:
                validate_archive(target)
            except Exception:
                os.replace(target, staging)
                os.replace(backup, source)
                _write_journal(journal, "rolled-back", operation="archive", slug=slug,
                               staging=staging.name, backup=backup.name)
                raise
            # The archive body is now committed and independently re-validated at `target`.
            # Everything from here on is best-effort backup cleanup — its failure (e.g.
            # OneDrive marking `backup` reparse within minutes of creation, WinError 5) must
            # never be reported as if the archive itself had failed (plan Phase 5 step 2).
            try:
                shutil.rmtree(backup)
                journal.unlink(missing_ok=True)
            except OSError:
                return target, STATUS_CLEANUP_PENDING
            return target, STATUS_COMMITTED
        except Exception:
            # Preserve journal and transaction copies for deterministic retry.
            raise


def reopen(active_root: Path, done_root: Path, slug: str) -> Path:
    validate_identifier(slug, "slug", charset="unicode-safe")
    active_root, done_root = ensure_safe_root(Path(active_root)), ensure_safe_root(Path(done_root))
    source, target = done_root / slug, active_root / slug
    if not _same_volume(active_root, done_root):
        raise ArchiveError("cross-volume", "Cross-volume atomic reopen is unsupported.")
    with SlugLock(active_root, slug):
        journal = active_root / f".archive-{slug}.journal.json"
        if journal.exists():
            return _finish_reopen(journal, active_root, done_root, slug)
        if target.exists():
            raise ArchiveError("active-conflict", "Active target already exists; reopen never overwrites.")
        manifest = validate_archive(source)
        old_bytes = (source / "manifest.json").read_bytes()
        old_revision = manifest["revision_id"]
        new_number = int(old_revision[1:]) + 1 if old_revision.startswith("r") and old_revision[1:].isdigit() else 2
        marker = {
            "revision_id": f"r{new_number}", "parent_revision_id": old_revision,
            "parent_path": f"evidence/revisions/{old_revision}/manifest.json",
            "parent_sha256": hashlib.sha256(old_bytes).hexdigest(), "reopened_at": _now(),
        }
        _write_journal(journal, "reopen-prepared", operation="reopen", slug=slug, **marker)
        return _finish_reopen(journal, active_root, done_root, slug)


# ---- OneDrive / reparse-point reliability workaround (plan Phase 5 step 1) -------------------
#
# Root cause (see .meta/memory/workflows/converge-archive-onedrive-workaround.md): OneDrive
# Files On-Demand marks a synced directory as a Windows reparse point within minutes of
# creation; `os.rmdir`/`shutil.rmtree` against a reparse-marked directory then fails with
# WinError 5 ("Access is denied"). `archive()`'s in-place transaction always ends by removing
# `backup` (the old `active_root/slug`, renamed) — so once `active_root` lives under
# OneDrive, in-place archive eventually cannot complete its own cleanup. The workaround below
# performs the entire copy/prepare/validate/commit sequence against a plain local temp
# directory pair (never reparse-marked, since it is fresh and never OneDrive-synced), then
# copies only the already-validated result back into `done_root`, and finally removes the
# original `active_root/slug` — the one unavoidable deletion against a possibly reparse-marked
# path — via `safe_remove_tree`'s precise-path, retrying, fail-closed removal.

def _probe_delete_blocked(root: Path) -> bool:
    """Mechanical, general-purpose probe: create then remove a throwaway marker directory
    inside `root` and report whether the removal failed with the exact "Access is denied"
    (WinError 5) signature OneDrive's reparse conversion produces. This is a live filesystem
    behavior probe, not a hardcoded `"OneDrive" in str(path)` heuristic — it equally detects
    any other filesystem/policy layer that blocks deletion the same way (Bitter Lesson: a
    general mechanism over a specific prior)."""
    try:
        marker = Path(root) / f".archive-probe-{uuid.uuid4().hex}"
        marker.mkdir(mode=0o700)
    except OSError:
        return False
    try:
        marker.rmdir()
        return False
    except OSError as exc:
        return getattr(exc, "winerror", None) == 5
    finally:
        if marker.exists():
            try:
                marker.rmdir()
            except OSError:
                pass


def onedrive_workaround_needed(active_root: Path, done_root: Path, *, probe: bool = True) -> bool:
    """Automatic reparse/OneDrive environment detection. Checks each root's own reparse-point
    attribute first (cheap, no side effect); falls back to the delete-probe above when neither
    root is itself already reparse-marked. `probe=False` skips the side-effecting probe (e.g.
    for a read-only caller)."""
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    for root in (Path(active_root), Path(done_root)):
        try:
            st = root.lstat()
        except OSError:
            continue
        if getattr(st, "st_file_attributes", 0) & reparse:
            return True
    return probe and _probe_delete_blocked(Path(active_root))


def _clear_readonly_and_retry(func, path, exc_info):
    """`shutil.rmtree` onerror hook: clear the read-only attribute of the one failing path
    (never a broader scan) and retry the exact same operation once."""
    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError:
        pass
    func(path)


def safe_remove_tree(path: Path, *, expected_parent: Path | None = None,
                      retries: int = 3, sleep_seconds: float = 0.5) -> None:
    """Precise-path, fail-closed tree removal for ACL/ReadOnly/reparse cleanup (plan Phase 5
    step 6). Refuses to operate unless `path`'s resolved parent is exactly `expected_parent`
    (when given), and refuses any path too shallow to plausibly be a `<active_root>/<slug>`
    leaf — this is never a recursive/glob-based sweep and must never reach a vault or
    filesystem root. A reparse point is unlinked directly via `os.rmdir` (which drops the
    junction/symlink itself without ever traversing into its target); a normal directory goes
    through `shutil.rmtree` with a read-only-clearing retry hook. Retries with a short backoff,
    then raises `ArchiveError` (fail closed) — never silently gives up, never falls back to a
    broader or less precise removal."""
    # Deliberately `os.path.abspath`, never `Path.resolve()`: resolve() follows symlinks and
    # reparse points, which — when the reparse point is `path` itself (the exact case this
    # function exists to handle) — would silently substitute the link's *target* path for the
    # link's own path, and every check and OS call below would then operate on the wrong
    # object entirely (defeating the "unlink the reparse point, never traverse into it"
    # contract). abspath only normalizes the string; it never dereferences anything.
    resolved = Path(os.path.abspath(str(Path(path))))
    if expected_parent is not None and resolved.parent != Path(os.path.abspath(str(Path(expected_parent)))):
        raise ArchiveError("cleanup-path-unsafe", "Refusing to remove a path outside its expected parent.", str(resolved))
    if len(resolved.parts) < 4:
        raise ArchiveError("cleanup-root-guard", "Refusing to remove a path too close to a filesystem root.", str(resolved))
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    last_exc: OSError | None = None
    for attempt in range(retries):
        try:
            attrs = getattr(resolved.lstat(), "st_file_attributes", 0)
        except OSError:
            # Nothing at this path (already removed, or a dangling reparse point whose own
            # lstat still failed) — treat as already-clean rather than raising.
            return
        try:
            if attrs & reparse:
                os.rmdir(resolved)
            else:
                shutil.rmtree(resolved, onerror=_clear_readonly_and_retry)
            return
        except OSError as exc:
            last_exc = exc
            if attempt + 1 < retries:
                time.sleep(sleep_seconds)
    raise ArchiveError("cleanup-failed", f"Could not remove path after {retries} attempts: {last_exc}", str(resolved))


def _finish_source_cleanup(source: Path, active_root: Path, journal: Path) -> str:
    if not source.exists():
        journal.unlink(missing_ok=True)
        return STATUS_COMMITTED
    try:
        safe_remove_tree(source, expected_parent=active_root)
    except (ArchiveError, OSError):
        return STATUS_CLEANUP_PENDING
    journal.unlink(missing_ok=True)
    return STATUS_COMMITTED


def _archive_via_local_staging(active_root: Path, done_root: Path, slug: str,
                                prepare: Callable[[Path], None]) -> tuple[Path, str]:
    source = active_root / slug
    final_target = done_root / slug
    journal = active_root / f".archive-{slug}.onedrive-journal.json"
    with SlugLock(active_root, slug):
        if journal.exists():
            try:
                record = json.loads(journal.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError) as exc:
                raise ArchiveError("journal-malformed", "OneDrive-workaround transaction journal is malformed.", journal.name) from exc
            if record.get("slug") != slug:
                raise ArchiveError("journal-owner-conflict", "OneDrive-workaround journal does not belong to this archive.", journal.name)
            if not final_target.is_dir():
                raise ArchiveError("journal-authority-missing", "OneDrive-workaround journal has no committed done target to recover.", journal.name)
            validate_archive(final_target)
            return final_target, _finish_source_cleanup(source, active_root, journal)
        if final_target.exists():
            if source.exists():
                raise ArchiveError("done-conflict", "Done target already exists; archive never overwrites.", None)
            # No journal and no source left: an earlier run already fully committed and
            # cleaned up. Idempotent no-op re-run.
            validate_archive(ensure_safe_root(final_target))
            return final_target, STATUS_COMMITTED
        ensure_safe_root(source)
        ensure_safe_tree(source)
        with tempfile.TemporaryDirectory(prefix=f"converge-archive-{slug}-") as td:
            tmp_root = Path(td)
            tmp_active, tmp_done = tmp_root / "active", tmp_root / "done"
            tmp_active.mkdir(mode=0o700); tmp_done.mkdir(mode=0o700)
            _copy_tree_safe(source, tmp_active / slug)
            tmp_target, tmp_status = archive(tmp_active, tmp_done, slug, prepare)
            if tmp_status != STATUS_COMMITTED:
                raise ArchiveError("onedrive-staging-cleanup-failed", "Local staging archive could not fully commit.", str(tmp_target))
            # Absolute-path re-verify #1 (plan Phase 5 step 1): local, non-synced storage,
            # independent of the in-process state `archive()` just built.
            validate_archive(ensure_safe_root(tmp_target))
            _copy_tree_safe(tmp_target, final_target)
        # Absolute-path re-verify #2: the final on-disk copy actually living under the
        # (possibly OneDrive-managed) `done_root` — the copy Git will actually see.
        validate_archive(ensure_safe_root(final_target))
        _write_journal(journal, "done-copied", operation="archive-onedrive", slug=slug)
        return final_target, _finish_source_cleanup(source, active_root, journal)


def archive_reliable(active_root: Path, done_root: Path, slug: str,
                      prepare: Callable[[Path], None], *,
                      workaround: bool | None = None) -> tuple[Path, str]:
    """`archive()` with automatic OneDrive/reparse workaround (plan Phase 5 step 1). When the
    environment is not reparse-blocked, delegates directly to `archive()` — identical atomic
    in-place semantics, no extra copying. When it is (or `workaround=True` forces it
    regardless of the probe, e.g. for tests), the whole copy/prepare/validate/commit sequence
    runs against a local temp workspace via `_archive_via_local_staging`. `workaround=False`
    forces the in-place path even if the probe would otherwise trigger."""
    validate_identifier(slug, "slug", charset="unicode-safe")
    active_root = ensure_safe_root(Path(active_root))
    done_root = ensure_safe_root(Path(done_root))
    if workaround is None:
        workaround = onedrive_workaround_needed(active_root, done_root)
    if not workaround:
        return archive(active_root, done_root, slug, prepare)
    return _archive_via_local_staging(active_root, done_root, slug, prepare)


JOURNAL_STATES = frozenset({"preparing", "source-backed-up", "committed", "rolled-back", "reopen-prepared", "reopen-moved", "reopen-parent-stored", "reopen-marker-stored"})


def journal_state(active_root: Path, slug: str) -> str | None:
    path = Path(active_root) / f".archive-{slug}.journal.json"
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))["state"]
    except (OSError, ValueError, KeyError):
        return "recoverable"
    return state if state in JOURNAL_STATES else "recoverable"
