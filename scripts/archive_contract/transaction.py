"""Single-writer staging, archive, reopen, and recovery transactions."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .model import (
    ARCHIVE_TOTAL_LIMIT, ArchiveError, canonical_json_bytes, ensure_safe_root,
    ensure_safe_tree, owner_process_liveness, strict_json_bytes, validate_archive,
    validate_identifier,
)


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


def _recover_archive(journal: Path, active_root: Path, done_root: Path, slug: str) -> Path | None:
    """Resolve an interrupted archive to one authoritative copy, then retry/return."""
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
        _remove_tree(backup); _remove_tree(staging); journal.unlink()
        return target
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
        _remove_tree(staging); journal.unlink()
        return target
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
            prepare: Callable[[Path], None]) -> Path:
    validate_identifier(slug, "slug")
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
            shutil.rmtree(backup)
            journal.unlink(missing_ok=True)
            return target
        except Exception:
            # Preserve journal and transaction copies for deterministic retry.
            raise


def reopen(active_root: Path, done_root: Path, slug: str) -> Path:
    validate_identifier(slug, "slug")
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
