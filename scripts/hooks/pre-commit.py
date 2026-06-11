#!/usr/bin/env python3
"""pre-commit hook: check for stale content in active/ directories.

Scans .converge/active/ and docs/plans/active/ for items that appear
completed but were not archived to done/.

Exit 1 (block commit) if stale items found, unless CONVERGE_SKIP_ARCHIVE_CHECK=1.
Exit 0 otherwise.
"""

import os
import re
import subprocess
import sys

SKIP_ENV = "CONVERGE_SKIP_ARCHIVE_CHECK"


def _repo_root():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


REPO_ROOT = _repo_root()

stale_items = []
warn_items = []
info_items = []


def _slug_of(fname):
    base = os.path.splitext(fname)[0]
    return re.sub(r"^\d{8}-", "", base)


# ── Check .converge/active/<slug>/ ──────────────────────────────────────
converge_active = os.path.join(REPO_ROOT, ".converge", "active")
converge_done = os.path.join(REPO_ROOT, ".converge", "done")
done_slugs = set()
if os.path.isdir(converge_done):
    done_slugs = set(os.listdir(converge_done))

if os.path.isdir(converge_active):
    for slug in os.listdir(converge_active):
        slug_dir = os.path.join(converge_active, slug)
        if not os.path.isdir(slug_dir):
            continue

        # Rule 1: slug exists in both active/ and done/ → definitely stale
        if slug in done_slugs:
            stale_items.append(
                f"  .converge/active/{slug}/ — also exists in done/, remove active copy"
            )
            continue

        # Rule 2: state file shows completed
        state_file = os.path.join(slug_dir, "_orchestrator-state.md")
        if os.path.isfile(state_file):
            try:
                with open(state_file, encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                text = ""
            if re.search(r"^current_phase:\s*completed", text, re.MULTILINE):
                stale_items.append(
                    f"  .converge/active/{slug}/ — current_phase: completed, archive to done/"
                )
                continue

        # Rule 3: empty directory → nudge cleanup
        contents = [f for f in os.listdir(slug_dir) if not f.startswith(".")]
        if not contents:
            info_items.append(
                f"  .converge/active/{slug}/ — empty, consider removing"
            )
        else:
            warn_items.append(
                f"  .converge/active/{slug}/ — in-progress ({len(contents)} files), "
                f"verify this is intentional"
            )

# ── Check docs/plans/active/ ────────────────────────────────────────────
plans_active = os.path.join(REPO_ROOT, "docs", "plans", "active")
plans_done = os.path.join(REPO_ROOT, "docs", "plans", "done")
done_plans = set()
if os.path.isdir(plans_done):
    done_plans = {f for f in os.listdir(plans_done) if os.path.isfile(os.path.join(plans_done, f))}

if os.path.isdir(plans_active):
    for fname in os.listdir(plans_active):
        fpath = os.path.join(plans_active, fname)
        if not os.path.isfile(fpath):
            continue

        slug = _slug_of(fname)

        # Rule 1: same slug exists in done/ (date-stripped exact match)
        in_done = any(_slug_of(d) == slug for d in done_plans)
        if in_done:
            stale_items.append(
                f"  docs/plans/active/{fname} — matching plan in done/, remove active copy"
            )
            continue

        # Rule 2: all checkboxes checked
        try:
            text = open(fpath, encoding="utf-8").read()
        except OSError:
            continue
        checks = re.findall(r"^- \[([ xX])\]", text, re.MULTILINE)
        if len(checks) >= 2 and all(c.lower() == "x" for c in checks):
            stale_items.append(
                f"  docs/plans/active/{fname} — all items [x], archive to done/"
            )
        else:
            warn_items.append(
                f"  docs/plans/active/{fname} — in-progress, verify intentional"
            )

# ── Report ──────────────────────────────────────────────────────────────
if not stale_items and not warn_items and not info_items:
    sys.exit(0)

print("=" * 60)
if stale_items:
    print("BLOCKED: stale items in active/ should be archived first:")
    print()
    for item in stale_items:
        print(item)
    print()

if warn_items:
    print("WARNING: active/ has in-progress items — verify intentional:")
    print()
    for item in warn_items:
        print(item)
    print()

if info_items:
    print("NOTE: minor cleanup suggestions:")
    for item in info_items:
        print(item)
    print()

if os.environ.get(SKIP_ENV) == "1":
    print(f"{SKIP_ENV}=1 set, proceeding anyway.")
    print("=" * 60)
    sys.exit(0)

if stale_items:
    print("To proceed anyway:")
    print(f"  {SKIP_ENV}=1 git commit ...")
    print("Or archive/remove first, then commit.")
    print("=" * 60)
    sys.exit(1)

print("=" * 60)
sys.exit(0)
