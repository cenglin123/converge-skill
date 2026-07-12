#!/usr/bin/env python3
"""Thin standard-library CLI facade for Converge Archive Contract v1."""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from archive_contract import ArchiveError
from archive_contract import capture, model, presentation, transaction


def _json_object(value: str):
    try:
        result = json.loads(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if not isinstance(result, dict):
        raise argparse.ArgumentTypeError("expected JSON object")
    return result


def _output(value, fmt: str) -> None:
    if fmt == "json":
        sys.stdout.buffer.write(presentation.json_bytes(value))
    else:
        print(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2))


def _bootstrap_import(staging: Path) -> None:
    capture.bootstrap_import_legacy(staging)


def _prepare(staging: Path) -> None:
    _bootstrap_import(staging)
    reopen_state = staging / ".reopen-state.json"
    revision_id, parent = "r1", None
    if reopen_state.exists():
        state = model.strict_json_bytes(reopen_state.read_bytes())
        revision_id = state["revision_id"]
        parent = {
            "revision_id": state["parent_revision_id"], "path": state["parent_path"],
            "sha256": state["parent_sha256"],
        }
        reopen_state.unlink()
    manifest = model.project_manifest(staging, revision_id=revision_id, parent=parent)
    if not manifest["final_verdict_ref"]:
        raise ArchiveError("final-decision-missing", "Archive requires exactly one closed terminal decision.", "evidence/events")
    (staging / "manifest.json").write_bytes(model.canonical_json_bytes(manifest))
    (staging / "INDEX.md").write_bytes(presentation.render_index(manifest))


def _check_push_range(repo: Path, base: str, head: str) -> list[dict]:
    zero = "0" * 40
    if base == zero:
        base = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    changed = subprocess.run(["git", "diff", "--name-only", "-z", base, head], cwd=repo,
        capture_output=True, check=True).stdout.split(b"\0")
    slugs = set()
    for raw in changed:
        if raw.startswith(b".converge/done/"):
            slug = raw.decode("utf-8", errors="strict").split("/", 3)[2]
            model.validate_identifier(slug, "slug"); slugs.add(slug)
    failures = []
    for slug in sorted(slugs, key=str.casefold):
        proc = subprocess.run(["git", "archive", "--format=tar", head, f".converge/done/{slug}"],
            cwd=repo, capture_output=True, check=True)
        with tempfile.TemporaryDirectory() as td, tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as archive:
            root = Path(td).resolve()
            for member in archive.getmembers():
                target = (root / member.name).resolve()
                try: target.relative_to(root)
                except ValueError as exc: raise ArchiveError("git-archive-escape", "Git archive member escapes materialization root.") from exc
                if not (member.isfile() or member.isdir()):
                    raise ArchiveError("git-archive-filetype", "Git archive contains a non-file entry.", member.name)
            archive.extractall(root)
            view = presentation.check_view(root / ".converge" / "done" / slug)
            if not view["valid"]: failures.append(view)
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Converge Archive Contract v1")
    sub = parser.add_subparsers(dest="command", required=True)

    begin = sub.add_parser("begin-invocation")
    begin.add_argument("root", type=Path)
    begin.add_argument("--kind", choices=("spawn", "continue"), required=True)
    begin.add_argument("--role", required=True); begin.add_argument("--phase", required=True)
    begin.add_argument("--round", type=int); begin.add_argument("--attempt", type=int, required=True)
    begin.add_argument("--reservation-id"); begin.add_argument("--parent-event-id")
    begin.add_argument("--requested-provider"); begin.add_argument("--requested-model")
    begin.add_argument("--prompt", type=Path); begin.add_argument("--evidence-mode", choices=tuple(model.EVIDENCE_MODES), default="metadata-only")

    complete = sub.add_parser("complete-invocation")
    complete.add_argument("root", type=Path); complete.add_argument("invocation_id")
    complete.add_argument("--status", choices=tuple(model.TERMINAL_STATUSES), required=True)
    complete.add_argument("--instance-id"); complete.add_argument("--receipt"); complete.add_argument("--settlement-ref")
    complete.add_argument("--resolved-provider"); complete.add_argument("--resolved-model"); complete.add_argument("--resolved-family")
    complete.add_argument("--backend"); complete.add_argument("--backend-version")
    complete.add_argument("--host-evidence-ref")
    complete.add_argument("--evidence-level", choices=tuple(model.EVIDENCE_LEVELS), required=True)
    complete.add_argument("--resolution-source", choices=tuple(model.RESOLUTION_SOURCES), required=True)
    complete.add_argument("--resolution-reason-code", choices=tuple(model.RESOLUTION_REASONS))
    complete.add_argument("--output", type=Path); complete.add_argument("--evidence-mode", choices=tuple(model.EVIDENCE_MODES), default="metadata-only")
    complete.add_argument("--failure-reason-code", choices=tuple(model.FAILURE_REASONS)); complete.add_argument("--failure-detail")

    recover = sub.add_parser("recover-invocation")
    recover.add_argument("root", type=Path); recover.add_argument("invocation_id")
    recover.add_argument("--status", choices=("failed", "cancelled", "timeout"), required=True)
    recover.add_argument("--failure-reason-code", choices=tuple(model.FAILURE_REASONS), required=True)
    recover.add_argument("--failure-detail")
    recover.add_argument("--instance-id"); recover.add_argument("--settlement-ref")

    decision = sub.add_parser("record-terminal-decision")
    decision.add_argument("root", type=Path); decision.add_argument("--data", type=_json_object, required=True)
    design = sub.add_parser("record-design-review-completion")
    design.add_argument("root", type=Path); design.add_argument("--invocation-event-id", required=True)
    design.add_argument("--status", required=True); design.add_argument("--highlights-ref", required=True)
    message = sub.add_parser("record-user-message")
    message.add_argument("root", type=Path); message.add_argument("--host-message-id", required=True); message.add_argument("--user-quote", required=True)

    archive_p = sub.add_parser("archive")
    archive_p.add_argument("active_root", type=Path); archive_p.add_argument("done_root", type=Path); archive_p.add_argument("slug")
    reopen_p = sub.add_parser("reopen")
    reopen_p.add_argument("active_root", type=Path); reopen_p.add_argument("done_root", type=Path); reopen_p.add_argument("slug")
    check = sub.add_parser("check"); check.add_argument("root", type=Path); check.add_argument("--format", choices=("human", "json"), default="human")
    scan = sub.add_parser("scan"); scan.add_argument("done_root", type=Path); scan.add_argument("--format", choices=("human", "json"), default="human")
    changed = sub.add_parser("check-done-changes", aliases=("--check-done-changes",))
    changed.add_argument("done_root", type=Path)
    push = sub.add_parser("check-push-range", aliases=("--check-push-range",))
    push.add_argument("repo", type=Path); push.add_argument("base"); push.add_argument("head")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "begin-invocation":
            result = capture.begin_invocation(args.root, invocation_kind=args.kind, role=args.role, phase=args.phase,
                round_number=args.round, attempt=args.attempt, reservation_id=args.reservation_id,
                parent_event_id=args.parent_event_id, requested_provider=args.requested_provider,
                requested_model=args.requested_model, prompt_path=args.prompt,
                evidence_mode=args.evidence_mode)
            _output(result, "json")
        elif args.command == "complete-invocation":
            result = capture.complete_invocation(args.root, args.invocation_id, terminal_status=args.status,
                instance_id=args.instance_id, receipt=args.receipt, settlement_ref=args.settlement_ref,
                resolved_provider=args.resolved_provider, resolved_model=args.resolved_model,
                resolved_family=args.resolved_family, backend=args.backend, backend_version=args.backend_version,
                host_evidence_ref=args.host_evidence_ref,
                evidence_level=args.evidence_level, resolution_source=args.resolution_source,
                resolution_reason_code=args.resolution_reason_code,
                output_path=args.output, evidence_mode=args.evidence_mode,
                failure_reason_code=args.failure_reason_code, failure_detail=args.failure_detail)
            _output(result, "json")
        elif args.command == "recover-invocation":
            _output(capture.recover_invocation(args.root, args.invocation_id, terminal_status=args.status,
                failure_reason_code=args.failure_reason_code, failure_detail=args.failure_detail,
                instance_id=args.instance_id, settlement_ref=args.settlement_ref), "json")
        elif args.command == "record-terminal-decision":
            _output(capture.record_terminal_decision(args.root, args.data), "json")
        elif args.command == "record-design-review-completion":
            _output(capture.record_design_review_completion(args.root, invocation_event_id=args.invocation_event_id,
                completion_status=args.status, highlights_ref=args.highlights_ref), "json")
        elif args.command == "record-user-message":
            _output(capture.record_user_message(args.root, host_message_id=args.host_message_id,
                user_quote=args.user_quote), "json")
        elif args.command == "archive":
            _output({"archived": str(transaction.archive(args.active_root, args.done_root, args.slug, _prepare))}, "json")
        elif args.command == "reopen":
            _output({"reopened": str(transaction.reopen(args.active_root, args.done_root, args.slug))}, "json")
        elif args.command == "check":
            view = presentation.check_view(args.root)
            _output(view if args.format == "json" else presentation.human_check(view), args.format)
            return 0 if view["valid"] else 2
        elif args.command == "scan":
            result = presentation.scan(args.done_root)
            _output(result if args.format == "json" else "\n".join(f"{x['slug']}: {x['state']} ({x['reason']}) -> {x['next_action']}" for x in result), args.format)
        elif args.command in ("check-done-changes", "--check-done-changes"):
            slugs = set()
            for raw in sys.stdin.buffer.read().split(b"\0"):
                if not raw:
                    continue
                path = raw.decode("utf-8", errors="strict").replace("\\", "/")
                prefix = ".converge/done/"
                if path.startswith(prefix):
                    slug = path[len(prefix):].split("/", 1)[0]
                    model.validate_identifier(slug, "slug")
                    slugs.add(slug)
            failures = []
            for slug in sorted(slugs, key=str.casefold):
                view = presentation.check_view(args.done_root / slug)
                if not view["valid"]:
                    failures.append(view)
            if failures:
                _output({"valid": False, "archives": failures}, "json")
                return 2
        elif args.command in ("check-push-range", "--check-push-range"):
            failures = _check_push_range(args.repo, args.base, args.head)
            if failures:
                _output({"valid": False, "archives": failures}, "json")
                return 2
        return 0
    except ArchiveError as exc:
        _output({"valid": False, "diagnostics": [exc.diagnostic()]}, "json")
        return 3
    except (OSError, ValueError, KeyError) as exc:
        diagnostic = {"code": "io-or-input-error", "summary": str(exc), "path": None, "next_action": "Correct the input or filesystem condition and retry."}
        _output({"valid": False, "diagnostics": [diagnostic]}, "json")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
