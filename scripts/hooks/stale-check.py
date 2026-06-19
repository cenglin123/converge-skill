#!/usr/bin/env python3
"""pre-push hook: check for stale content in active/ directories.

Scans .converge/active/ and docs/plans/active/ for items that appear
completed or abandoned but were not archived to done/.

Three tiers:
  CRITICAL — structural staleness (slug in done/, state=completed,
             all [x] checked, or frontmatter status=done|landed)
  WARNING  — age-based staleness (mtime > STALE_AGE_DAYS, default 7)
  NOTE     — in-progress items, informational

Default: informational (exit 0). Set CONVERGE_STRICT=1 to block push
on CRITICAL items (exit 1).
"""

import os
import re
import subprocess
import sys
import time

_AGE_UNKNOWN = float("inf")
_CRITICAL_STATUSES = frozenset({"done", "landed"})


def _is_strict():
    return os.environ.get("CONVERGE_STRICT", "").strip() in ("1", "true", "yes")


def _safe_stale_days():
    raw = os.environ.get("CONVERGE_STALE_AGE_DAYS", "7")
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return 7
    return max(val, 1)


STALE_AGE_DAYS = _safe_stale_days()


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


def _frontmatter_status(text):
    m = re.search(r"^status:\s*(\S+)", text, re.MULTILINE)
    return m.group(1).lower() if m else None


def _age_days(path):
    try:
        return (time.time() - os.path.getmtime(path)) / 86400
    except OSError:
        return _AGE_UNKNOWN


def _newest_age_days(directory):
    try:
        entries = os.listdir(directory)
    except OSError:
        return _AGE_UNKNOWN
    visible = [e for e in entries if not e.startswith(".")]
    if not visible:
        return _age_days(directory)
    mtimes = []
    for e in visible:
        p = os.path.join(directory, e)
        try:
            mtimes.append(os.path.getmtime(p))
        except OSError:
            pass
    if not mtimes:
        return _AGE_UNKNOWN
    return (time.time() - max(mtimes)) / 86400


def _scan_converge(repo_root):
    critical = []
    warning = []
    note = []

    converge_active = os.path.join(repo_root, ".converge", "active")
    converge_done = os.path.join(repo_root, ".converge", "done")
    done_slugs = set()
    if os.path.isdir(converge_done):
        try:
            done_slugs = {d for d in os.listdir(converge_done)
                          if os.path.isdir(os.path.join(converge_done, d))}
        except OSError:
            pass

    if not os.path.isdir(converge_active):
        return critical, warning, note

    try:
        slugs = os.listdir(converge_active)
    except OSError:
        return critical, warning, note

    for slug in slugs:
        slug_dir = os.path.join(converge_active, slug)
        if not os.path.isdir(slug_dir):
            continue

        if slug in done_slugs:
            critical.append(
                f"  .converge/active/{slug}/ — also exists in done/, remove active copy"
            )
            continue

        state_file = os.path.join(slug_dir, "_orchestrator-state.md")
        if os.path.isfile(state_file):
            try:
                with open(state_file, encoding="utf-8") as f:
                    text = f.read()
                if re.search(r"^current_phase:\s*completed", text, re.MULTILINE):
                    critical.append(
                        f"  .converge/active/{slug}/ — current_phase: completed, archive to done/"
                    )
                    continue
            except OSError:
                pass

        try:
            contents = [f for f in os.listdir(slug_dir) if not f.startswith(".")]
        except OSError:
            contents = []

        if not contents:
            note.append(
                f"  .converge/active/{slug}/ — empty, consider removing"
            )
            continue

        age = _newest_age_days(slug_dir)
        if age == _AGE_UNKNOWN or age > STALE_AGE_DAYS:
            warning.append(
                f"  .converge/active/{slug}/ — "
                + ("age unknown, " if age == _AGE_UNKNOWN else f"no activity for {age:.0f} days, ")
                + f"likely abandoned (threshold: {STALE_AGE_DAYS})"
            )
        else:
            note.append(
                f"  .converge/active/{slug}/ — in-progress ({len(contents)} files, "
                f"last activity {age:.1f} days ago)"
            )

    return critical, warning, note


def _scan_plans(repo_root):
    critical = []
    warning = []
    note = []

    plans_active = os.path.join(repo_root, "docs", "plans", "active")
    plans_done = os.path.join(repo_root, "docs", "plans", "done")

    done_plan_slugs = set()
    if os.path.isdir(plans_done):
        try:
            done_plan_slugs = {_slug_of(f) for f in os.listdir(plans_done)
                               if os.path.isfile(os.path.join(plans_done, f))}
        except OSError:
            pass

    if not os.path.isdir(plans_active):
        return critical, warning, note

    try:
        fnames = os.listdir(plans_active)
    except OSError:
        return critical, warning, note

    for fname in fnames:
        fpath = os.path.join(plans_active, fname)
        if not os.path.isfile(fpath):
            continue

        slug = _slug_of(fname)

        if slug in done_plan_slugs:
            critical.append(
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
            critical.append(
                f"  docs/plans/active/{fname} — all items [x], archive to done/"
            )
            continue

        fm_status = _frontmatter_status(text)
        if fm_status in _CRITICAL_STATUSES:
            critical.append(
                f"  docs/plans/active/{fname} — frontmatter status: {fm_status}, archive to done/"
            )
            continue

        age = _age_days(fpath)
        if age == _AGE_UNKNOWN or age > STALE_AGE_DAYS:
            warning.append(
                f"  docs/plans/active/{fname} — "
                + ("age unknown, " if age == _AGE_UNKNOWN else f"no activity for {age:.0f} days, ")
                + f"likely abandoned (threshold: {STALE_AGE_DAYS})"
            )
        else:
            note.append(
                f"  docs/plans/active/{fname} — in-progress (last activity {age:.1f} days ago)"
            )

    return critical, warning, note


def _has_spawn_evidence(active):
    """active 目录是否存在 spawn 产物（round/blind/uv），即应当有 gate ledger。"""
    import glob
    for pat in ("round-*.md", "blind-recheck-*.md", "uv-init-*.md"):
        if glob.glob(os.path.join(active, pat)):
            return True
    return False


def _scan_budget(repo_root):
    """CRITICAL: 预算 gate 突破 / 未结孤儿 / 损坏状态 / 有 spawn 却无 ledger。

    复用 budget_gate 自身逻辑，确保 hook 与 gate 判定不分叉。**fail-closed**：
    导入失败、扫描异常、有 spawn 证据却缺 ledger，均上报 CRITICAL（不静默吞掉）。
    """
    critical = []
    active_root = os.path.join(repo_root, ".converge", "active")
    if not os.path.isdir(active_root):
        return critical

    scripts_dir = os.path.join(repo_root, "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        import budget_gate as bg
    except Exception as e:
        # 无法验证 ≠ 没问题：fail-closed 上报，strict 下阻断。
        critical.append(f"  budget_gate import failed — cannot verify budget ({e})")
        return critical

    import pathlib
    for slug in sorted(os.listdir(active_root)):
        active = pathlib.Path(active_root) / slug
        if not active.is_dir():
            continue
        ledger_exists = (active / bg.LEDGER_NAME).exists()
        if not ledger_exists:
            # 有 spawn 产物却无 ledger = 预算 gate 被绕过（finding 5）
            if _has_spawn_evidence(str(active)):
                critical.append(
                    f"  .converge/active/{slug}/ — spawn artifacts present but no gate-ledger "
                    f"(budget gate bypassed)"
                )
            continue
        try:
            events = bg.read_ledger(active)
            state = bg.read_state(active)
            bg.validate_integrity(active, events, state)
            res = bg._reservation_status(events)
            orphans = [rid for rid, r in res.items() if r["status"] == "reserved"]
            if orphans:
                critical.append(
                    f"  .converge/active/{slug}/ — {len(orphans)} unsettled orphan reservation(s)"
                )
            for scope in ("outer", "blind", "ultraverge"):
                if bg.effective_usage(active, events, scope) > bg.ceiling(state, scope):
                    critical.append(
                        f"  .converge/active/{slug}/ — budget breach: {scope} usage > ceiling"
                    )
            if bg.total_reservations_issued(events) > bg.ceiling(state, "total"):
                critical.append(f"  .converge/active/{slug}/ — total spawn cap breached")
        except bg.FailClosed as e:
            critical.append(f"  .converge/active/{slug}/ — budget state FAIL_CLOSED: {e.reason}")
        except Exception as e:
            # 扫描异常同样 fail-closed 上报，不静默 continue。
            critical.append(f"  .converge/active/{slug}/ — budget scan error: {e}")
    return critical


def main():
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, OSError):
        pass

    repo_root = _repo_root()

    c1, w1, n1 = _scan_converge(repo_root)
    c2, w2, n2 = _scan_plans(repo_root)
    c3 = _scan_budget(repo_root)

    critical_items = c1 + c2 + c3
    warning_items = w1 + w2
    note_items = n1 + n2

    if not critical_items and not warning_items and not note_items:
        return

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

    if critical_items and _is_strict():
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[stale-check] unexpected error: {exc}")
        sys.exit(1 if _is_strict() else 0)
