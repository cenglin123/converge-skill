#!/usr/bin/env python3
"""Antipattern 蒸馏器 —— 把真实收敛日志编译成反模式注册表的 status。

raw source : .converge/done/*/retrospective.md 的「## 3. Antipattern 巡查」表
compiled   : refs/antipatterns.md 的 status / last_confirmed / confirmed_count /
             zero_streak / last_distilled_at 字段

设计边界（确定性，零 LLM，禁止越界）：
  - 本脚本只做机械统计：某个【已知 id】在某次收敛中是否出现。
  - 不判断 `new:xxx` 是否为某个 dormant 反模式的复活（语义判断 → 人工 + resurrection_log）。
  - 不判断两个不同 `new:` 描述是否同一模式（语义判断）。
  - 对 `new:` 的唯一动作是按描述文本原样计数，达阈值则在报告中列出供人工裁定。
  - 只读 done/，绝不读 active/——对运行中任务零干扰。
  - 不自动 commit，不自动改写 antipatterns.md 之外的任何文件；--write 才落盘，
    默认 dry-run 仅打印报告，人保留否决权。

计数单位（已确认，决策 1）：
  - 一份 retrospective = 一次收敛。zero_streak 按任务级计数：同份 retrospective 里
    同一 id 跨多轮命中多次，对 zero_streak 只算「这次收敛命中过」（归零一次）。
  - confirmed_count 按 round 级累加：表里出现几行就加几次（总命中次数统计）。

状态机（阈值见 antipatterns.md frontmatter，非硬编码于此）：
  active --(连续 dormant_threshold 次收敛零命中)--> dormant
  dormant --(连续 archive_threshold 次收敛零命中)--> archived
  任意一次收敛命中 --> zero_streak 归零（active/dormant 状态由本次全量重算）
  archived 不自动复活；dormant 复活是人工动作（改 status + resurrection_log）。

Usage:
    python distill_antipatterns.py                 # dry-run，打印报告
    python distill_antipatterns.py --write         # 回写 antipatterns.md
    python distill_antipatterns.py --done DIR --registry FILE

Exit code: 0 正常（含「有条目降级」）；1 仅在 registry 解析失败时。
parse 失败的单份 retrospective → skip + warning，不中断其余（defensive parsing）。

注：当前（2026-06）retrospective < 10，dormant_threshold=5 意味着尚无条目达到
衰减窗口。本脚本现阶段的主要价值是 dry-run 观测：每次新收敛归档后跑一遍，
看 confirmed_count / zero_streak 快照，积累「哪些反模式真在命中、哪些在变冷」的经验。
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# -- 路径默认值（相对 SKILL 根，可被 CLI 覆盖）-----------------------------
DEFAULT_DONE_DIR = ".converge/done"
DEFAULT_REGISTRY = "refs/antipatterns.md"

# -- 格式契约（与 state-schema.md §3 / antipatterns.md 锁定）---------------
SECTION_HEADER = "## 3. Antipattern 巡查"      # 精确匹配
EXPECTED_COLS = ["Round", "类型", "对象", "触发结果"]
NEW_PREFIX = "new:"                             # 未知反模式占位（state-schema 定义；暂无真实样本）

# -- Rule Activity 蒸馏常量 -------------------------------------------------
RULE_SECTION_HEADER = "## Rule Activity"
RULE_EXPECTED_COLS = ["rule", "triggered", "zero_streak", "status"]

KNOWN_RULES = {
    "boundary_guard": "guard",
    "reviewer_boundary_audit": "guard",
    "intent_drift_check": "guard",
    "gate_l1": "guard",
    "design_review_trigger": "guard",
}


# ========================================================================
# raw source 解析
# ========================================================================
def parse_section3(md_text: str, slug: str) -> tuple[set[str], list[str], list[str]]:
    """解析单份 retrospective 的 §3 表。

    返回 (hit_ids_task_level, hit_ids_round_level, new_descriptions)：
      - hit_ids_task_level : 本次收敛命中过的已知 id 去重集合（用于 zero_streak）
      - hit_ids_round_level : 逐行的已知 id 列表，含重复（用于 confirmed_count）
      - new_descriptions    : `new:` 前缀的原始描述列表（人工裁定用）
    解析失败抛 ValueError，由调用方 skip + warning。
    """
    lines = md_text.splitlines()

    # 1. 定位 §3 节标题
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == SECTION_HEADER:
            start = i
            break
    if start is None:
        raise ValueError(f"未找到节标题 '{SECTION_HEADER}'")

    # 2. 节内截到下一个 '## ' 或文件尾
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    section = lines[start + 1:end]

    # 3. 抓表格行：以 '|' 开头。跳过表头、分隔行(---)、以及 '>' 引用注释
    table_rows = []
    for ln in section:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        # 表头行
        if cells[:len(EXPECTED_COLS)] == EXPECTED_COLS:
            continue
        # 分隔行 |---|---|
        if all(set(c) <= set("-: ") for c in cells if c):
            continue
        table_rows.append(cells)

    # 4. 逐行取「类型」列（索引 1）
    task_hits: set[str] = set()
    round_hits: list[str] = []
    new_descs: list[str] = []
    for cells in table_rows:
        if len(cells) < 2:
            continue  # 残行，跳过
        type_cell = cells[1].strip()
        if not type_cell:
            continue
        if type_cell.startswith(NEW_PREFIX):
            new_descs.append(type_cell[len(NEW_PREFIX):].strip())
        else:
            task_hits.add(type_cell)
            round_hits.append(type_cell)
    return task_hits, round_hits, new_descs


def collect_convergences(done_dir: Path) -> list[dict]:
    """扫描 done/ 下每份 retrospective，按 slug 升序（≈时间序）返回。

    每个元素：{slug, task_hits, round_hits, new_descs}。
    单份解析失败 → 打 warning 并跳过（defensive parsing），不计入序列。
    """
    convs = []
    retro_paths = sorted(done_dir.glob("*/retrospective.md"))
    if not retro_paths:
        print(f"warning: {done_dir} 下未找到任何 retrospective.md", file=sys.stderr)
    for p in retro_paths:
        slug = p.parent.name
        try:
            task_hits, round_hits, new_descs = parse_section3(p.read_text(encoding="utf-8"), slug)
        except (ValueError, OSError) as e:
            print(f"warning: 跳过 {slug}（§3 解析失败：{e}）", file=sys.stderr)
            continue
        convs.append({"slug": slug, "task_hits": task_hits,
                      "round_hits": round_hits, "new_descs": new_descs})
    return convs


# ========================================================================
# Rule Activity 解析 & 聚合
# ========================================================================
def parse_rule_activity_section(md_text: str, slug: str) -> list[dict]:
    """解析单份 retrospective 的 Rule Activity 表。

    返回 [{rule, triggered, zero_streak, status}, ...]。
    解析失败抛 ValueError，由调用方 skip + warning。
    """
    lines = md_text.splitlines()

    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == RULE_SECTION_HEADER:
            start = i
            break
    if start is None:
        raise ValueError(f"未找到节标题 '{RULE_SECTION_HEADER}'")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    section = lines[start + 1:end]

    table_rows = []
    for ln in section:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cells[:len(RULE_EXPECTED_COLS)] == RULE_EXPECTED_COLS:
            continue
        if all(set(c) <= set("-: ") for c in cells if c):
            continue
        table_rows.append(cells)

    rows = []
    for idx, cells in enumerate(table_rows):
        try:
            if len(cells) < 4:
                print(f"warning: {slug} Rule Activity 第 {idx+1} 行列数不足（{len(cells)}），跳过",
                      file=sys.stderr)
                continue
            rule = cells[0].strip()
            triggered_raw = cells[1].strip().lower()
            zero_streak_raw = cells[2].strip()
            status = cells[3].strip()
            if triggered_raw in ("true", "yes", "1"):
                triggered = True
            elif triggered_raw in ("false", "no", "0"):
                triggered = False
            else:
                print(f"warning: {slug} Rule Activity 规则 '{rule}' triggered 值无法识别 "
                      f"'{cells[1].strip()}'，跳过", file=sys.stderr)
                continue
            zero_streak = int(zero_streak_raw)
            rows.append({
                "rule": rule,
                "triggered": triggered,
                "zero_streak": zero_streak,
                "status": status,
            })
        except (ValueError, IndexError) as e:
            print(f"warning: {slug} Rule Activity 第 {idx+1} 行解析失败（{e}），跳过",
                  file=sys.stderr)
            continue
    return rows


def collect_rule_activities(done_dir: Path) -> list[dict]:
    """扫描 done/ 下每份 retrospective 的 Rule Activity 节。

    每个元素：{slug, rules: [{rule, triggered, zero_streak, status}, ...]}。
    单份解析失败 → 打 warning 并跳过（defensive parsing）。
    """
    convs = []
    retro_paths = sorted(done_dir.glob("*/retrospective.md"))
    if not retro_paths:
        print(f"warning: {done_dir} 下未找到任何 retrospective.md", file=sys.stderr)
    for p in retro_paths:
        slug = p.parent.name
        try:
            rules = parse_rule_activity_section(p.read_text(encoding="utf-8"), slug)
        except (ValueError, OSError) as e:
            print(f"warning: 跳过 {slug}（Rule Activity 解析失败：{e}）", file=sys.stderr)
            continue
        convs.append({"slug": slug, "rules": rules})
    return convs


def aggregate_rules(rule_convs: list[dict]) -> dict[str, dict]:
    """跨收敛聚合每条 rule 的统计。

    返回 {rule_key: {
        max_zero_streak, triggered_count, total_convergences,
        classification, advisory_status, per_convergence: [{slug, triggered, zero_streak, status}, ...]
    }}
    """
    total = len(rule_convs)
    agg: dict[str, dict] = {}

    for conv in rule_convs:
        slug = conv["slug"]
        for r in conv["rules"]:
            key = r["rule"]
            if key not in agg:
                agg[key] = {
                    "max_zero_streak": 0,
                    "triggered_count": 0,
                    "total_convergences": total,
                    "classification": KNOWN_RULES.get(key, "unknown"),
                    "advisory_status": "",
                    "per_convergence": [],
                }
            agg[key]["per_convergence"].append({
                "slug": slug,
                "triggered": r["triggered"],
                "zero_streak": r["zero_streak"],
                "status": r["status"],
            })
            if r["zero_streak"] > agg[key]["max_zero_streak"]:
                agg[key]["max_zero_streak"] = r["zero_streak"]
            if r["triggered"]:
                agg[key]["triggered_count"] += 1

    return agg


def classify_rule_status(agg: dict[str, dict],
                         guard_dormant_th: int, guard_archive_th: int,
                         core_dormant_th: int, core_archive_th: int) -> None:
    """根据分类和阈值，原地更新每条 rule 的 advisory_status。"""
    for key, info in agg.items():
        cls = info["classification"]
        streak = info["max_zero_streak"]
        if cls == "guard":
            if streak >= guard_archive_th:
                info["advisory_status"] = "archived"
            elif streak >= guard_dormant_th:
                info["advisory_status"] = "dormant"
            else:
                info["advisory_status"] = "active"
        elif cls == "core":
            if streak >= core_archive_th:
                info["advisory_status"] = "archived"
            elif streak >= core_dormant_th:
                info["advisory_status"] = "dormant"
            else:
                info["advisory_status"] = "active"
        else:
            info["advisory_status"] = "active"


def print_rule_report(rule_convs: list[dict], agg: dict[str, dict]) -> None:
    """打印 Rule Activity 蒸馏报告（仅报告，不写文件）。"""
    n_conv = len(rule_convs)
    print("=" * 64)
    print("Rule Activity 蒸馏报告（advisory，不自动修改任何文件）")
    print("=" * 64)
    print(f"扫描收敛数（成功解析 Rule Activity 节）: {n_conv}")
    print()

    print("── 跨收敛汇总 ──")
    print(f"  {'rule':30s} {'class':8s} {'max_streak':>10s} {'triggered':>9s} {'total':>5s}  {'advisory':9s}")
    for key in sorted(agg.keys()):
        info = agg[key]
        print(f"  {key:30s} {info['classification']:8s} {info['max_zero_streak']:>10d} "
              f"{info['triggered_count']:>9d} {info['total_convergences']:>5d}  "
              f"{info['advisory_status']:9s}")
    print()

    print("── 逐收敛明细 ──")
    for conv in rule_convs:
        print(f"  [{conv['slug']}]")
        for r in conv["rules"]:
            trig = "✓" if r["triggered"] else "✗"
            print(f"    {r['rule']:30s} triggered={trig}  zero_streak={r['zero_streak']:>3d}  "
                  f"status={r['status']}")
    print()

    dormant_or_archived = {k: v for k, v in agg.items()
                           if v["advisory_status"] in ("dormant", "archived")}
    print("── 建议操作 ──")
    if dormant_or_archived:
        for key in sorted(dormant_or_archived.keys()):
            info = dormant_or_archived[key]
            status = info["advisory_status"]
            if status == "archived":
                print(f"  {key}: 建议归档（{info['classification']} 类，"
                      f"max_zero_streak={info['max_zero_streak']}，"
                      f"命中 {info['triggered_count']}/{info['total_convergences']} 次）")
            else:
                print(f"  {key}: 建议休眠（{info['classification']} 类，"
                      f"max_zero_streak={info['max_zero_streak']}，"
                      f"命中 {info['triggered_count']}/{info['total_convergences']} 次）")
        print("  ↑ 以上为建议，需人工确认后再操作")
    else:
        print("  所有规则状态良好，无需降级")
    print("=" * 64)


# ========================================================================
# compiled 产物（antipatterns.md）读写
# ========================================================================
def split_registry(text: str) -> tuple[str, dict, str, str]:
    """切出 (frontmatter_raw, frontmatter_dict, body_before_yaml, yaml_block)。

    antipatterns.md 结构：--- frontmatter --- ... ```yaml <antipatterns 列表> ```
    本脚本只改 frontmatter 的 last_distilled_at 和 yaml_block 内的条目字段，
    其余正文（字段说明、初始值约定等）原样保留。
    """
    fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not fm_match:
        raise ValueError("antipatterns.md 缺少 YAML frontmatter")
    fm_raw = fm_match.group(1)
    fm = _parse_simple_yaml(fm_raw)

    yaml_match = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    if not yaml_match:
        raise ValueError("antipatterns.md 缺少 ```yaml 反模式列表块")
    return fm_raw, fm, text, yaml_match.group(1)


def _parse_simple_yaml(block: str) -> dict:
    """极简 YAML（仅 key: value，value 可带行内 # 注释）。不依赖第三方库。"""
    out = {}
    for ln in block.splitlines():
        if ":" not in ln or ln.lstrip().startswith("#"):
            continue
        k, v = ln.split(":", 1)
        v = v.split("#", 1)[0].strip().strip('"').strip("'")
        out[k.strip()] = v
    return out


def parse_entries(yaml_block: str) -> list[dict]:
    """把 ```yaml 列表块解析成条目 dict 列表。

    仅解析本脚本关心的标量字段；description 等多行字段不动（回写时按 id 定位整段替换）。
    """
    entries = []
    cur = None
    for ln in yaml_block.splitlines():
        m_id = re.match(r"\s*-\s*id:\s*(\S+)", ln)
        if m_id:
            if cur:
                entries.append(cur)
            cur = {"id": m_id.group(1).strip()}
            continue
        if cur is None:
            continue
        m_kv = re.match(r"\s+(\w+):\s*(.*)$", ln)
        if m_kv and m_kv.group(1) in (
            "layer", "status", "last_confirmed", "confirmed_count",
            "zero_streak", "detection_constraint",
        ):
            cur[m_kv.group(1)] = m_kv.group(2).split("#", 1)[0].strip().strip('"')
    if cur:
        entries.append(cur)
    return entries


# ========================================================================
# 蒸馏核心（全量重算）
# ========================================================================
def distill(entries: list[dict], convs: list[dict],
            dormant_th: int, archive_th: int) -> tuple[list[dict], list[dict]]:
    """对每个已知 id 全量重算 status/last_confirmed/confirmed_count/zero_streak。

    返回 (new_entries, changes)：changes 记录 status 变化供报告。
    人工管理的字段（resurrection_log、description、layer、detection_constraint）不动。
    archived 条目：保持 archived（不自动复活），但仍刷新 confirmed_count 等统计。
    """
    seq = convs
    changes = []
    new_entries = []

    for e in entries:
        eid = e["id"]
        cur_status = e.get("status", "active")

        # confirmed_count：round 级累加
        confirmed_count = sum(c["round_hits"].count(eid) for c in seq)
        # last_confirmed：最后一次命中的 slug
        last_confirmed = ""
        for c in seq:
            if eid in c["task_hits"]:
                last_confirmed = c["slug"]
        # zero_streak：从序列末尾往前数，连续多少次收敛未命中（任务级）
        zero_streak = 0
        for c in reversed(seq):
            if eid in c["task_hits"]:
                break
            zero_streak += 1

        # 状态机（archived 不自动复活；dormant→active 只能人工，故此处不升）
        new_status = cur_status
        if cur_status == "active" and zero_streak >= dormant_th:
            new_status = "dormant"
        elif cur_status == "dormant" and zero_streak >= archive_th:
            new_status = "archived"
        # 命中导致 zero_streak=0 时，active/dormant 维持原状（不擅自把 dormant 升回）

        if new_status != cur_status:
            changes.append({"id": eid, "from": cur_status, "to": new_status,
                            "zero_streak": zero_streak})

        merged = dict(e)
        merged.update({
            "status": new_status,
            "last_confirmed": last_confirmed,
            "confirmed_count": str(confirmed_count),
            "zero_streak": str(zero_streak),
        })
        new_entries.append(merged)

    return new_entries, changes


def tally_new_prefix(convs: list[dict], window: int, promote_th: int) -> list[tuple[str, int]]:
    """统计最近 window 次收敛里 new: 描述出现频率，达阈值的列为人工固化候选。

    注意：纯文本精确计数。不做任何语义聚类（不同措辞视为不同候选）。
    """
    recent = convs[-window:] if window > 0 else convs
    freq: dict[str, int] = {}
    for c in recent:
        for d in c["new_descs"]:
            freq[d] = freq.get(d, 0) + 1
    return sorted(((d, n) for d, n in freq.items() if n >= promote_th),
                  key=lambda x: -x[1])


# ========================================================================
# 回写 & 报告
# ========================================================================
def write_registry(path: Path, new_entries: list[dict], now_iso: str) -> None:
    """就地替换：对每个条目，按 id 定位其字段块，只改脚本维护的 5 个标量字段，
    其余行（description 多行块、resurrection_log、layer 等）逐字保留。
    同时更新 frontmatter 的 last_distilled_at。
    """
    text = path.read_text(encoding="utf-8")

    # 1. frontmatter last_distilled_at
    text = re.sub(r'(last_distilled_at:\s*)"[^"]*"',
                  rf'\g<1>"{now_iso}"', text, count=1)

    # 2. 逐条目就地改标量字段
    by_id = {e["id"]: e for e in new_entries}
    lines = text.splitlines(keepends=True)
    cur_id = None
    for idx, ln in enumerate(lines):
        m_id = re.match(r"(\s*-\s*id:\s*)(\S+)", ln)
        if m_id:
            cur_id = m_id.group(2).strip()
            continue
        if cur_id is None or cur_id not in by_id:
            continue
        for field in ("status", "last_confirmed", "confirmed_count", "zero_streak"):
            m = re.match(rf"(\s+{field}:\s*)(.*?)(\s*(#.*)?)$", ln)
            if m:
                val = by_id[cur_id][field]
                # last_confirmed 用引号包裹（可能为空串），数值字段不包
                rendered = f'"{val}"' if field == "last_confirmed" else val
                lines[idx] = f"{m.group(1)}{rendered}\n"
                break
    path.write_text("".join(lines), encoding="utf-8")


def print_report(convs, changes, new_entries, new_candidates, wrote: bool):
    n_conv = len(convs)
    print("=" * 64)
    print(f"distill_antipatterns 报告  ({'已回写' if wrote else 'dry-run，未落盘'})")
    print("=" * 64)
    print(f"扫描收敛数（成功解析）: {n_conv}")
    print()

    print("── status 变化 ──")
    if changes:
        for c in changes:
            print(f"  {c['id']:28s} {c['from']} → {c['to']}  (zero_streak={c['zero_streak']})")
    else:
        print("  无变化")
    print()

    print("── 当前快照 ──")
    print(f"  {'id':28s} {'layer':12s} {'status':9s} {'count':>5s} {'streak':>6s}  last_confirmed")
    for e in new_entries:
        print(f"  {e['id']:28s} {e.get('layer',''):12s} {e['status']:9s} "
              f"{e['confirmed_count']:>5s} {e['zero_streak']:>6s}  {e.get('last_confirmed','')}")
    print()

    print("── new: 人工固化候选 ──")
    if new_candidates:
        for desc, n in new_candidates:
            print(f"  [{n}×] {desc}")
        print("  ↑ 需人工评估是否新增为正式条目（脚本不自动创建）")
    else:
        print(f"  无（无 new: 达阈值，或 {n_conv} 份样本中 new: 从未出现）")
    print("=" * 64)


# ========================================================================
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="蒸馏 antipattern 命中频率 → 更新 registry status")
    ap.add_argument("--done", default=DEFAULT_DONE_DIR, help="done/ 目录")
    ap.add_argument("--registry", default=DEFAULT_REGISTRY, help="antipatterns.md 路径")
    ap.add_argument("--write", action="store_true", help="回写 registry（默认 dry-run）")
    ap.add_argument("--rules", action="store_true",
                    help="同时（或单独）运行 Rule Activity 蒸馏报告")
    ap.add_argument("--guard-dormant-threshold", type=int, default=5,
                    help="guard 类规则休眠阈值（默认 5）")
    ap.add_argument("--guard-archive-threshold", type=int, default=10,
                    help="guard 类规则归档阈值（默认 10）")
    ap.add_argument("--core-dormant-threshold", type=int, default=20,
                    help="core 类规则休眠阈值（默认 20）")
    ap.add_argument("--core-archive-threshold", type=int, default=40,
                    help="core 类规则归档阈值（默认 40）")
    args = ap.parse_args()

    run_antipattern = not args.rules or args.write
    run_rules = args.rules

    # -- antipattern 蒸馏（默认行为，或 --write 时始终运行）--
    if run_antipattern:
        registry_path = Path(args.registry)
        try:
            text = registry_path.read_text(encoding="utf-8")
            _, fm, _, yaml_block = split_registry(text)
            entries = parse_entries(yaml_block)
        except (ValueError, OSError) as e:
            print(f"error: registry 解析失败：{e}", file=sys.stderr)
            sys.exit(1)

        dormant_th = int(fm.get("dormant_threshold", 5))
        archive_th = int(fm.get("archive_threshold", 12))
        window = int(fm.get("new_prefix_window", 5))
        promote_th = int(fm.get("new_prefix_promote_threshold", 3))

        convs = collect_convergences(Path(args.done))
        new_entries, changes = distill(entries, convs, dormant_th, archive_th)
        new_candidates = tally_new_prefix(convs, window, promote_th)

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if args.write:
            write_registry(registry_path, new_entries, now_iso)

        print_report(convs, changes, new_entries, new_candidates, wrote=args.write)

    # -- Rule Activity 蒸馏（仅 --rules 时运行）--
    if run_rules:
        rule_convs = collect_rule_activities(Path(args.done))
        agg = aggregate_rules(rule_convs)
        classify_rule_status(agg,
                             args.guard_dormant_threshold,
                             args.guard_archive_threshold,
                             args.core_dormant_threshold,
                             args.core_archive_threshold)
        print_rule_report(rule_convs, agg)


if __name__ == "__main__":
    main()
