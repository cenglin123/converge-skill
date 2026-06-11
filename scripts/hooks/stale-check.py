#!/usr/bin/env python3
"""post-merge hook: check for stale content in active/ directories.

Scans .converge/active/ and docs/plans/active/ for items that appear
completed or abandoned but were not archived to done/.

Three tiers:
  CRITICAL — structural staleness (slug in done/, state=completed, all [x])
  WARNING  — age-based staleness (mtime > STALE_AGE_DAYS, default 7)
  NOTE     — in-progress items, informational

Informational only — post-merge hooks cannot block the merge.
"""

import os
import re
import subprocess
import sys
import time

STALE_AGE_DAYS = int(os.environ.get("CONVERGE_STALE_AGE_DAYS", "7"))


def _repo_root():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _slug_of(fname):
    base = os.path.splitext(fname)[0]
    return re.sub(r"^\d{8}-", "", base)


def _age_days(path):
    try:
        return (time.time() - os.path.getmtime(path)) / 86400
    except OSError:
        return 0


def _newest_age_days(directory):
    try:
        entries = os.listdir(directory)
    except OSError:
        return 0
    if not entries:
        return _age_days(directory)
    mtimes = []
    for e in entries:
        p = os.path.join(directory, e)
        try:
            mtimes.append(os.path.getmtime(p))
        except OSError:
            pass
    if not mtimes:
        return _age_days(directory)
    return (time.time() - max(mtimes)) / 86400


REPO_ROOT = _repo_root()

critical_items = []
warning_items = []
note_items = []

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

        if slug in done_slugs:
            critical_items.append(
                f"  .converge/active/{slug}/ — also exists in done/, remove active copy"
            )
            continue

        state_file = os.path.join(slug_dir, "_orchestrator-state.md")
        if os.path.isfile(state_file):
            try:
                with open(state_file, encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                text = ""
            if re.search(r"^current_phase:\s*completed", text, re.MULTILINE):
                critical_items.append(
                    f"  .converge/active/{slug}/ — current_phase: completed, archive to done/"
                )
                continue

        contents = [f for f in os.listdir(slug_dir) if not f.startswith(".")]
        if not contents:
            note_items.append(
                f"  .converge/active/{slug}/ — empty, consider removing"
            )
            continue

        age = _newest_age_days(slug_dir)
        if age > STALE_AGE_DAYS:
            warning_items.append(
                f"  .converge/active/{slug}/ — no activity for {age:.0f} days "
                f"(threshold: {STALE_AGE_DAYS}), likely abandoned"
            )
        else:
            note_items.append(
                f"  .converge/active/{slug}/ — in-progress ({len(contents)} files, "
                f"last activity {age:.1f} days ago)"
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

        if any(_slug_of(d) == slug for d in done_plans):
            critical_items.append(
                f"  docs/plans/active/{fname} — matching plan in done/, remove active copy"
            )
            continue

        try:
            with open(fpath, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        checks = re.findall(r"^- \[([ xX])\]", text, re.MULTILINE)
        if len(checks) >= 2 and all(c.lower() == "x" for c in checks):
            critical_items.append(
                f"  docs/plans/active/{fname} — all items [x], archive to done/"
            )
            continue

        age = _age_days(fpath)
        if age > STALE_AGE_DAYS:
            warning_items.append(
                f"  docs/plans/active/{fname} — no activity for {age:.0f} days "
                f"(threshold: {STALE_AGE_DAYS}), likely abandoned"
            )
        else:
            note_items.append(
                f"  docs/plans/active/{fname} — in-progress (last activity {age:.1f} days ago)"
            )

# ── Report ──────────────────────────────────────────────────────────────
if not critical_items and not warning_items and not note_items:
    sys.exit(0)

print("=" * 60)
if critical_items:
    print("CRITICAL: structurally stale items found in active/:")
    print()
    for item in critical_items:
        print(item)
    print()

if warning_items:
    print(f"WARNING: items idle > {STALE_AGE_DAYS} days (set CONVERGE_STALE_AGE_DAYS to adjust):")
    print()
    for item in warning_items:
        print(item)
    print()

if note_items:
    print("NOTE: in-progress items:")
    for item in note_items:
        print(item)
    print()

print("=" * 60)
