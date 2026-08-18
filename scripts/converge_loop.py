#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
converge_loop.py — converge 循环驱动器：声明式 loop spec 驱动的派发阶段全机械调度

设计（plan: docs/plans/active/20260818-converge-loop-driver.md）：
  判断（prompt 内容、verdict 裁决、修复指令、retrospective）留给 agent——
  全部以文件在 pause/resume 边界交接；搬运（轮号推导、预约、派发、落账、
  产物三方对齐、归档）零手工，由本驱动器机械执行。

  本驱动器只做**组合**：以 subprocess 调用 orchest.py 六命令（记账合同的唯一
  事实源）与 ocsr_dispatch.py（派发后端），不重新实现预算/归档/角色语义。

退出码（沿用 ocsr run-spec 约定）：
  0  全流程完成（finish 归档成功）
  1  步骤失败（orchest/dispatch 非零且无法机械恢复，或 agent 选择 abort）
  2  spec 非法或用法错误
  10 暂停待裁决（已写 pause-request.json）
  11 resume 状态不确定（journal 损坏 / 答案缺失 / 输入文件未就位），停机
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_PAUSE = 10
EXIT_RESUME_UNCERTAIN = 11

VERDICTS = ("可执行", "阻断需修复", "需重新设计")
REALIZED_RE = re.compile(r"^round-(\d+)\.md$")
UV_RE = re.compile(r"^uv-init-(\d+)\.md$")
BLIND_RE = re.compile(r"^blind-recheck-(\d+)\.md$")

# spec 中禁止出现的字段（回归钉死：轮号只能由 driver 从 realized 产物推导——
# 20260818 outer 轮号误用事故的机制化防护）
FORBIDDEN_SPEC_KEYS = {"round", "round_number", "target_round"}

MAX_INNER_LOOPS_DEFAULT = 3


class LoopFail(Exception):
    """机械层不可恢复错误（→ exit 1）。"""


class SpecError(Exception):
    """spec 非法（→ exit 2）。"""


class ResumeUncertain(Exception):
    """resume 输入缺失/状态不确定（→ exit 11）。"""


# ─── spec 加载与校验 ──────────────────────────────────────────────────────────

def load_spec(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        return _MiniYaml(text).parse()
    except SpecError:
        raise
    except Exception as e:  # noqa: BLE001
        raise SpecError(f"spec 解析失败: {e}") from e


class _MiniYaml:
    """极简 YAML 子集（map/list/scalar/inline map+list）。stdlib-only 约定，不引 pyyaml。"""

    def __init__(self, text: str):
        self.lines = []
        for raw in text.splitlines():
            if not raw.strip() or raw.strip().startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            self.lines.append((indent, raw.strip()))
        self.pos = 0

    def parse(self) -> dict:
        if not self.lines:
            raise SpecError("spec 为空")
        out = self._block(self.lines[0][0])
        if not isinstance(out, dict):
            raise SpecError("spec 顶层必须是 map")
        return out

    def _block(self, indent: int):
        if self.pos >= len(self.lines):
            return {}
        if self.lines[self.pos][1].startswith("- "):
            return self._list(indent)
        return self._map(indent)

    def _map(self, indent: int) -> dict:
        out = {}
        while self.pos < len(self.lines):
            ind, content = self.lines[self.pos]
            if ind < indent or content.startswith("- "):
                break
            if ind > indent:
                raise SpecError(f"缩进错误: {content}")
            if ":" not in content:
                raise SpecError(f"缺少冒号: {content}")
            key, _, val = content.partition(":")
            key = key.strip()
            val = val.strip()
            self.pos += 1
            if val == "":
                if self.pos < len(self.lines) and self.lines[self.pos][0] > indent:
                    out[key] = self._block(self.lines[self.pos][0])
                else:
                    out[key] = None
            else:
                out[key] = self._scalar(val)
        return out

    def _list(self, indent: int) -> list:
        out = []
        while self.pos < len(self.lines):
            ind, content = self.lines[self.pos]
            if ind != indent or not content.startswith("- "):
                break
            item = content[2:].strip()
            self.pos += 1
            if item == "":
                out.append(self._block(self.lines[self.pos][0]))
            elif ":" in item and not item.startswith(("{", "[")):
                key, _, val = item.partition(":")
                m = {key.strip(): self._scalar(val.strip()) if val.strip() else None}
                if self.pos < len(self.lines) and self.lines[self.pos][0] > indent:
                    m.update(self._map(self.lines[self.pos][0]))
                out.append(m)
            else:
                out.append(self._scalar(item))
        return out

    def _scalar(self, val: str):
        if val.startswith("{") and val.endswith("}"):
            inner = val[1:-1].strip()
            if not inner:
                return {}
            out = {}
            for part in inner.split(","):
                k, _, v = part.partition(":")
                out[k.strip()] = self._scalar(v.strip())
            return out
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                return []
            return [self._scalar(p.strip()) for p in inner.split(",")]
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            return val[1:-1]
        if val in ("true", "True"):
            return True
        if val in ("false", "False"):
            return False
        if val in ("null", "~"):
            return None
        try:
            return int(val)
        except ValueError:
            return val


def validate_spec(spec: dict) -> list[str]:
    errs: list[str] = []

    def _walk(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if str(k) in FORBIDDEN_SPEC_KEYS:
                    errs.append(f"spec 禁止字段 {path}{k}（轮号只能由 driver 推导）")
                _walk(v, f"{path}{k}.")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                _walk(v, f"{path}{i}.")

    _walk(spec)
    for k in ("slug", "active_dir", "orchest", "ocsr_dispatch", "phases"):
        if not spec.get(k):
            errs.append(f"缺少必填字段: {k}")
    if spec.get("mode", "standard") not in ("standard", "ultraverge"):
        errs.append("mode 必须是 standard | ultraverge")
    phases = spec.get("phases") or []
    if not isinstance(phases, list) or not phases:
        errs.append("phases 必须是非空列表")
    for i, ph in enumerate(phases):
        if not isinstance(ph, dict):
            errs.append(f"phases[{i}] 必须是 map")
            continue
        t = ph.get("type")
        if t not in ("parallel-review", "outer-loop", "blind-recheck", "design-review"):
            errs.append(f"phases[{i}].type 非法: {t}")
            continue
        if t == "parallel-review":
            revs = ph.get("reviewers") or []
            if not revs:
                errs.append(f"phases[{i}]: parallel-review 需要非空 reviewers")
            if not ph.get("prompt_template"):
                errs.append(f"phases[{i}]: parallel-review 需要 prompt_template")
            for j, r in enumerate(revs):
                if not isinstance(r, dict) or not r.get("model") or not r.get("label"):
                    errs.append(f"phases[{i}].reviewers[{j}] 需要 model + label")
        if t == "outer-loop":
            if not ph.get("reviewer_models"):
                errs.append(f"phases[{i}]: outer-loop 需要 reviewer_models")
            if not ph.get("executor_model"):
                errs.append(f"phases[{i}]: outer-loop 需要 executor_model")
        if t in ("blind-recheck", "design-review") and not ph.get("prompt_template"):
            errs.append(f"phases[{i}]: {t} 需要 prompt_template")
    return errs


# ─── 机械推导（轮号 / verdict 解析 / 骨架合并） ────────────────────────────────

def realized_rounds(active_dir: Path, pattern: re.Pattern = REALIZED_RE) -> list[int]:
    nums = []
    if active_dir.is_dir():
        for p in active_dir.iterdir():
            m = pattern.match(p.name)
            if m:
                nums.append(int(m.group(1)))
    return sorted(nums)


def next_round(active_dir: Path, pattern: re.Pattern = REALIZED_RE) -> int:
    nums = realized_rounds(active_dir, pattern)
    return (max(nums) + 1) if nums else 1


def render_prompt(template: Path, mapping: dict[str, str], dest: Path) -> Path:
    text = template.read_text(encoding="utf-8")
    for k, v in mapping.items():
        text = text.replace("{" + k + "}", v)
    leftover = re.findall(r"\{[a-z_]+\}", text)
    if leftover:
        raise LoopFail(f"prompt 模板存在未替换占位符 {leftover}: {template}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8", newline="\n")
    return dest


def parse_verdict(product: Path) -> dict:
    """从产物（或原始报告）机械解析 verdict 与 blocking 严重度。

    只认 reviewer prompt 模板规定的 ```yaml 块格式；解析不出 → verdict=None
    （调用方按 pause 处理，不做语义猜测）。
    """
    text = product.read_text(encoding="utf-8")
    m = re.search(r"```yaml\s*\n(.*?)```", text, re.S)
    block = m.group(1) if m else text
    vm = re.search(r"^verdict:\s*(\S+)", block, re.M)
    verdict = vm.group(1).strip() if vm else None
    if verdict not in VERDICTS:
        verdict = None
    severities = re.findall(r"severity:\s*(conceptual|architectural|structural|implementation)", block)
    ids = re.findall(r"^\s+- id:\s*(\S+)", block, re.M)
    return {"verdict": verdict, "severities": severities, "issue_ids": ids}


def merge_into_skeleton(skel_path: Path, report_path: Path, orchestrator_note: str) -> None:
    skel = skel_path.read_text(encoding="utf-8")
    rep = report_path.read_text(encoding="utf-8").strip()
    skel = skel.replace("reviewer_backend: unknown", "reviewer_backend: ocsr")
    skel = skel.replace("## Reviewer 完整输出\n\n(pending)", "## Reviewer 完整输出\n\n" + rep)
    skel = skel.replace("## Orchestrator 处理记录\n\n(pending)",
                        "## Orchestrator 处理记录\n\n" + orchestrator_note)
    skel_path.write_text(skel, encoding="utf-8", newline="\n")


# ─── journal（断点续跑状态） ──────────────────────────────────────────────────

def journal_path(active_dir: Path) -> Path:
    return active_dir / ".loop-journal.json"


def load_journal(active_dir: Path) -> dict:
    p = journal_path(active_dir)
    if not p.is_file():
        return {"version": 1, "phase_index": 0, "phase_state": {},
                "paused": None, "aborted": False, "history": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise LoopFail(f"journal 损坏: {e}")


def save_journal(active_dir: Path, journal: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(active_dir), prefix=".loop-journal.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        json.dump(journal, f, ensure_ascii=False, indent=2)
    os.replace(tmp, journal_path(active_dir))


def _run(cmd: list[str], env: dict | None = None) -> tuple[int, str, str]:
    e = {**os.environ, "PYTHONUTF8": "1"}
    if env:
        e.update(env)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=e)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


# ─── Driver ───────────────────────────────────────────────────────────────────

class Driver:
    def __init__(self, spec: dict, spec_path: Path, timeout_min: int | None = None):
        self.spec = spec
        self.spec_path = spec_path
        self.spec_dir = spec_path.resolve().parent
        self.active = Path(spec["active_dir"]).resolve()
        self.active.mkdir(parents=True, exist_ok=True)
        (self.active / "reports").mkdir(exist_ok=True)
        self.orchest = Path(spec["orchest"]).resolve()
        self.ocsr = Path(spec["ocsr_dispatch"]).resolve()
        self.harness = spec.get("harness", "opencode")
        self.timeout = timeout_min or int(spec.get("timeout_min", 20))
        self.plan_ref = spec.get("plan", "")
        self.journal = load_journal(self.active)
        # consumes=none 角色（executor）的 register --output 需要 attempts.md 存在非空
        attempts = self.active / "attempts.md"
        if not attempts.is_file():
            attempts.write_text(f"# Attempts · {spec.get('slug', self.active.name)}\n\n"
                                "> 跨轮 attempt log。历史 entry 不改写，只追加 annotation。\n",
                                encoding="utf-8", newline="\n")

    # ── orchest 封装 ──
    def _orchest(self, *args: str) -> tuple[int, str, str]:
        return _run([sys.executable, str(self.orchest), *args])

    def reserve(self, role: str, round_n: int | None, phase: str, attempt: int,
                prompt: Path, model: str) -> str:
        provider, _, mname = model.partition("/")
        cmd = ["reserve-round", "--active-dir", str(self.active), "--role", role,
               "--phase", phase, "--attempt", str(attempt),
               "--prompt-file", str(prompt),
               "--requested-provider", provider, "--requested-model", mname or model]
        if round_n is not None:
            cmd += ["--round", str(round_n)]
        rc, out, err = self._orchest(*cmd)
        if rc != 0:
            raise LoopFail(f"reserve-round 失败 rc={rc}: {out} {err}")
        m = re.search(r"reservation_id:\s*(\w+)", out)
        if not m:
            raise LoopFail(f"reserve-round 输出无 reservation_id: {out}")
        return m.group(1)

    def register(self, rid: str, instance: str, output: str | None = None) -> None:
        cmd = ["register-round", "--active-dir", str(self.active),
               "--reservation-id", rid, "--instance-id", instance]
        if output:
            cmd += ["--output", output]
        rc, out, err = self._orchest(*cmd)
        if rc != 0:
            raise LoopFail(f"register-round 失败 rc={rc}: {out} {err}")

    def cancel(self, rid: str, reason: str, detail: str) -> None:
        rc, out, err = self._orchest("cancel-round", "--active-dir", str(self.active),
                                     "--reservation-id", rid, "--reason-code", reason,
                                     "--detail", detail)
        if rc != 0:
            raise LoopFail(f"cancel-round 失败 rc={rc}: {out} {err}")

    def record_verdict(self, round_n: int, product: str, verdict: str, severities: list[str]) -> None:
        cmd = ["record-verdict", "--active-dir", str(self.active), "--round", str(round_n),
               "--product", product, "--verdict", verdict]
        if severities:
            cmd += ["--severities", ",".join(severities)]
        rc, out, err = self._orchest(*cmd)
        if rc != 0:
            raise LoopFail(f"record-verdict 失败 rc={rc}: {out} {err}")

    def finish(self, verdict: str) -> None:
        cmd = ["finish", "--active-dir", str(self.active), "--verdict", verdict]
        if self.spec.get("done_root"):
            done_root = Path(self.spec["done_root"]).resolve()
            done_root.mkdir(parents=True, exist_ok=True)
            cmd += ["--done-root", str(done_root)]
        rc, out, err = self._orchest(*cmd)
        if rc != 0:
            raise LoopFail(f"finish 失败 rc={rc}: {out} {err}")

    # ── 派发封装（单 worker；并行由调用方拆成多次调用外的 batch） ──
    def dispatch(self, workers: list[dict], output_dir: Path, pattern: str) -> tuple[int, str, str]:
        cmd = [sys.executable, str(self.ocsr), "dispatch"]
        for w in workers:
            cmd += ["--worker", f"{w['prompt']}|{w['model']}|{w['label']}"]
        cmd += ["--output-dir", str(output_dir), "--output-pattern", pattern,
                "--watch", "--timeout", str(self.timeout),
                "--harness", self.harness,
                "--ledger-dir", str(self.active),
                "--stagger", str(self.spec.get("stagger", 8))]
        metas = list(self.spec.get("meta") or [])
        if self.plan_ref:
            metas.append(f"plan_ref={self.plan_ref}")
        for kv in metas:
            cmd += ["--meta", kv]
        for fp in (self.spec.get("forbid_paths") or []):
            cmd += ["--forbid-paths", str(fp)]
        return _run(cmd)

    # ── pause / resume ──
    def pause(self, question: str, decision: dict, expect: dict, options: list[str]) -> int:
        pj = {"question": question, "decision": decision, "expect_inputs": expect,
              "options": options,
              "resume_hint": f"converge_loop.py resume --spec {self.spec_path} [--answer k=v]..."}
        (self.active / "pause-request.json").write_text(
            json.dumps(pj, ensure_ascii=False, indent=2), encoding="utf-8")
        self.journal["paused"] = {"question": question, "decision": decision,
                                  "expect": expect, "options": options}
        save_journal(self.active, self.journal)
        print(f"[driver] PAUSE: {question}")
        print(f"[driver] 详情见 {self.active / 'pause-request.json'}")
        return EXIT_PAUSE

    def require_inputs(self, expect: dict, answers: dict) -> dict:
        out: dict = {}
        missing: list[str] = []
        for key, meta in (expect or {}).items():
            if meta.get("kind") == "choice":
                if key in answers:
                    if meta.get("options") and answers[key] not in meta["options"]:
                        missing.append(f"--answer {key} 取值 {answers[key]} 不在 {meta['options']}")
                    else:
                        out[key] = answers[key]
                elif meta.get("required", True):
                    missing.append(f"--answer {key}={ '|'.join(meta.get('options', [])) }")
            else:
                p = Path(meta["path"])
                if not p.is_file() or p.stat().st_size == 0:
                    if meta.get("required", True):
                        missing.append(f"输入文件未就位: {p}（{meta.get('description', key)}）")
                else:
                    out[key] = p
        if missing:
            for m_ in missing:
                print(f"[driver] resume 输入缺失: {m_}", file=sys.stderr)
            raise ResumeUncertain()
        return out

    def resolve(self, p: str | Path) -> Path:
        p = Path(p)
        return p if p.is_absolute() else (self.spec_dir / p).resolve()


# ─── phase 执行 ───────────────────────────────────────────────────────────────

def _reviewer_one(drv: Driver, role: str, round_n: int | None, phase_name: str,
                  model: str, label: str, prompt: Path, report_name: str,
                  product_name: str | None, attempt: int = 1) -> dict:
    """单个 reviewer/executor spawn 的机械全链：reserve→dispatch→register/cancel→merge→verdict。"""
    rid = drv.reserve(role, round_n, phase_name, attempt, prompt, model)
    rc, out, err = drv.dispatch(
        [{"prompt": str(prompt), "model": model, "label": label}],
        drv.active / "reports", report_name)
    report = drv.active / "reports" / report_name
    if rc != 0 and not (report.is_file() and report.stat().st_size > 0):
        drv.cancel(rid, "backend-error", f"dispatch rc={rc} 且产物缺失: {out[-300:]} {err[-300:]}")
        return {"ok": False, "rid": rid, "label": label,
                "error": f"dispatch rc={rc}: {out[-300:]} {err[-300:]}"}
    note = ""
    if rc != 0:
        note = f"dispatch rc={rc} 但产物已落盘（watcher 虚报类）——以文件系统实证回收"
    drv.register(rid, f"ocsr:{label}",
                 output="attempts.md" if role == "executor" else None)
    result: dict = {"ok": True, "rid": rid, "label": label, "note": note,
                    "report": str(report)}
    if product_name:
        merge_into_skeleton(
            drv.active / product_name, report,
            f"driver 机械合并（label={label}）{('；' + note) if note else ''}")
        result["product"] = product_name
        result["parsed"] = parse_verdict(drv.active / product_name)
    return result


def do_parallel_review(drv: Driver, phase: dict) -> int:
    """ultraverge 初审：N reviewer 批量并行（单批 dispatch，stagger 错峰）。"""
    reviewers = phase["reviewers"]
    tmpl = drv.resolve(phase["prompt_template"])
    reserved = []
    workers = []
    for i, r in enumerate(reviewers, 1):
        label = r["label"]
        report_name = f"uv-report-{label}.md"
        prompt = render_prompt(tmpl, {
            "label": label, "round": str(i),
            "report_path": str(drv.active / "reports" / report_name)},
            drv.active / f"prompt-uv-init-{i}.md")
        rid = drv.reserve("ultraverge-initial", i, "review", 1, prompt, r["model"])
        reserved.append({"rid": rid, "label": label, "model": r["model"],
                         "report": report_name, "round": i})
        workers.append({"prompt": str(prompt), "model": r["model"], "label": label})
    rc, out, err = drv.dispatch(workers, drv.active / "reports", "uv-report-{label}.md")
    verdicts = []
    for r in reserved:
        report = drv.active / "reports" / r["report"]
        if not (report.is_file() and report.stat().st_size > 0):
            drv.cancel(r["rid"], "backend-error", f"dispatch rc={rc} 且产物缺失")
            verdicts.append({"label": r["label"], "verdict": None, "error": "产物缺失"})
            continue
        drv.register(r["rid"], f"ocsr:{r['label']}")
        product = f"uv-init-{r['round']}.md"
        merge_into_skeleton(drv.active / product, report,
                            f"driver 机械合并（label={r['label']}）")
        parsed = parse_verdict(drv.active / product)
        if parsed["verdict"]:
            drv.record_verdict(r["round"], product, parsed["verdict"], parsed["severities"])
        verdicts.append({"label": r["label"], "round": r["round"], **parsed})
    drv.journal["history"].append({"phase": phase["id"], "verdicts": verdicts})
    save_journal(drv.active, drv.journal)
    blocked = [v for v in verdicts if v.get("verdict") != "可执行"]
    q = (f"初审完成：{len(verdicts) - len(blocked)}/{len(verdicts)} 可执行"
         + (f"，{len(blocked)} 个 reviewer 阻断或产物异常" if blocked else "，零阻断"))
    decision = {"kind": "phase_verdict", "phase_id": phase["id"],
                "phase_type": "parallel-review", "verdicts": verdicts, "blocked": blocked}
    expect = {"action": {"kind": "choice", "options": ["proceed", "repair", "abort"]}}
    if blocked:
        ep = drv.active / "prompt-executor-1.md"
        expect["executor_prompt"] = {"kind": "file", "path": str(ep),
                                     "description": "executor 修复指令（含 blocking 清单）",
                                     "required": False}
    return drv.pause(q, decision, expect, ["proceed", "repair", "abort"])


def do_outer_round(drv: Driver, phase: dict, reviewer_prompt: Path) -> int:
    round_n = next_round(drv.active, REALIZED_RE)
    models = phase["reviewer_models"]
    model = models[(round_n - 1) % len(models)]
    label = f"reviewer-r{round_n}"
    report_name = f"round{round_n}-report.md"
    st = drv.journal["phase_state"].setdefault(phase["id"], {})
    st["inner_streak"] = 0  # 新 reviewer 轮开始，inner loop 计数清零
    res = _reviewer_one(drv, "outer-reviewer", round_n, "review", model, label,
                        reviewer_prompt, report_name, f"round-{round_n}.md")
    if not res["ok"]:
        return drv.pause(f"outer round {round_n} spawn 失败",
                         {"kind": "spawn_failed", "phase_id": phase["id"], **res},
                         {"action": {"kind": "choice", "options": ["retry", "abort"]}},
                         ["retry", "abort"])
    parsed = res["parsed"]
    if not parsed["verdict"]:
        return drv.pause(f"outer round {round_n} 产物 verdict 解析失败（格式不符）",
                         {"kind": "verdict_parse_failed", "phase_id": phase["id"], **res},
                         {"action": {"kind": "choice", "options": ["proceed", "repair", "abort"]}},
                         ["proceed", "repair", "abort"])
    verdicts = drv.journal["phase_state"].setdefault(phase["id"], {}).setdefault("verdicts", [])
    verdicts.append({"round": round_n, **parsed})
    save_journal(drv.active, drv.journal)
    q = f"outer round {round_n} verdict={parsed['verdict']}"
    decision = {"kind": "phase_verdict", "phase_id": phase["id"],
                "phase_type": "outer-loop", "round": round_n, **parsed}
    expect = {"action": {"kind": "choice", "options": ["proceed", "repair", "abort"]}}
    if parsed["verdict"] == "阻断需修复":
        attempt = drv.journal.get("exec_global", 0) + 1
        ep = drv.active / f"prompt-executor-{attempt}.md"
        expect["executor_prompt"] = {"kind": "file", "path": str(ep),
                                     "description": "executor 修复指令", "required": False}
    return drv.pause(q, decision, expect, ["proceed", "repair", "abort"])


def do_blind(drv: Driver, phase: dict) -> int:
    outer_rounds = realized_rounds(drv.active, REALIZED_RE)
    if len(outer_rounds) < 2:
        drv.journal["history"].append({"phase": phase["id"], "skipped": "outer<2 轮，盲审不触发"})
        drv.journal["phase_index"] += 1
        save_journal(drv.active, drv.journal)
        return _advance(drv)
    blind_n = next_round(drv.active, BLIND_RE)
    tmpl = drv.resolve(phase["prompt_template"])
    label = f"blind-r{blind_n}"
    report_name = f"blind-{blind_n}-report.md"
    prompt = render_prompt(tmpl, {"label": label, "round": str(blind_n),
                                  "report_path": str(drv.active / "reports" / report_name)},
                           drv.active / f"prompt-blind-{blind_n}.md")
    res = _reviewer_one(drv, "blind-reviewer", blind_n, "review", phase["model"],
                        label, prompt, report_name, f"blind-recheck-{blind_n}.md")
    if not res["ok"]:
        return drv.pause(f"blind {blind_n} spawn 失败",
                         {"kind": "spawn_failed", "phase_id": phase["id"], **res},
                         {"action": {"kind": "choice", "options": ["retry", "abort"]}},
                         ["retry", "abort"])
    parsed = res["parsed"]
    verdict = parsed["verdict"] or "阻断需修复"
    if parsed["verdict"]:
        drv.record_verdict(blind_n, f"blind-recheck-{blind_n}.md", verdict, parsed["severities"])
    return drv.pause(f"blind-recheck-{blind_n} verdict={verdict}",
                     {"kind": "phase_verdict", "phase_id": phase["id"],
                      "phase_type": "blind-recheck", "round": blind_n, **parsed},
                     {"action": {"kind": "choice", "options": ["proceed", "repair", "abort"]}},
                     ["proceed", "repair", "abort"])


def do_design_review(drv: Driver, phase: dict) -> int:
    tmpl = drv.resolve(phase["prompt_template"])
    label = "design-reviewer"
    out_name = phase.get("output_name", "design-review.md")
    prompt = render_prompt(tmpl, {"label": label, "round": "0",
                                  "report_path": str(drv.active / out_name)},
                           drv.active / "prompt-design-review.md")
    rid = drv.reserve("design-reviewer", None, "design-review", 1, prompt, phase["model"])
    rc, out, err = drv.dispatch([{"prompt": str(prompt), "model": phase["model"], "label": label}],
                                drv.active, out_name)
    product = drv.active / out_name
    if not (product.is_file() and product.stat().st_size > 0):
        drv.cancel(rid, "backend-error", f"dispatch rc={rc} 且产物缺失: {out[-300:]}")
        return drv.pause("design-review spawn 失败",
                         {"kind": "spawn_failed", "phase_id": phase["id"], "rid": rid},
                         {"action": {"kind": "choice", "options": ["retry", "abort"]}},
                         ["retry", "abort"])
    drv.register(rid, f"ocsr:{label}", output=out_name)
    drv.journal["history"].append({"phase": phase["id"], "product": out_name})
    drv.journal["phase_index"] += 1
    save_journal(drv.active, drv.journal)
    return _advance(drv)


def do_executor(drv: Driver, phase_id: str, prompt: Path, model: str) -> int:
    attempt = drv.journal["exec_global"] = drv.journal.get("exec_global", 0) + 1
    st = drv.journal["phase_state"].setdefault(phase_id, {})
    st["inner_streak"] = st.get("inner_streak", 0) + 1
    label = f"executor-r{attempt}"
    report_name = f"executor-r{attempt}-report.md"
    res = _reviewer_one(drv, "executor", None, "repair", model,
                        label, prompt, report_name, None, attempt=attempt)
    save_journal(drv.active, drv.journal)
    if not res["ok"]:
        return drv.pause(f"executor attempt {attempt} spawn 失败",
                         {"kind": "spawn_failed", "phase_id": phase_id, **res},
                         {"action": {"kind": "choice", "options": ["retry", "abort"]}},
                         ["retry", "abort"])
    checks = _run_declared_checks(drv)
    inner = drv.journal["phase_state"][phase_id].get("inner_streak", 1)
    decision = {"kind": "executor_done", "phase_id": phase_id, "attempt": attempt,
                "inner_streak": inner, "report": res["report"], "checks": checks}
    rp = drv.active / f"prompt-reviewer-next-{attempt}.md"
    return drv.pause(f"executor attempt {attempt} 完成，验收？（声明核对: {checks or '无'}）",
                     decision,
                     {"action": {"kind": "choice", "options": ["accepted", "repair", "abort"]},
                      "reviewer_prompt": {"kind": "file", "path": str(rp),
                                          "description": "下一轮 reviewer prompt（accepted 时必填）",
                                          "required": False}},
                     ["accepted", "repair", "abort"])


def _run_declared_checks(drv: Driver) -> list[str]:
    """执行 spec 可选声明的确定性核对（checks: [{type: hash_equal|grep_count, ...}]）。"""
    results = []
    for chk in (drv.spec.get("checks") or []):
        t = chk.get("type")
        try:
            if t == "hash_equal":
                import hashlib
                files = [drv.resolve(f) for f in chk["files"]]
                hashes = [hashlib.md5(f.read_bytes()).hexdigest() for f in files]
                ok = len(set(hashes)) == 1
                results.append(f"hash_equal({len(files)} files)={'PASS' if ok else 'FAIL'}")
            elif t == "grep_count":
                text = drv.resolve(chk["file"]).read_text(encoding="utf-8")
                n = len(re.findall(chk["pattern"], text))
                expect = chk.get("expect")
                ok = (n == expect) if isinstance(expect, int) else (n > 0)
                results.append(f"grep_count({chk['pattern'][:30]})={n}({'PASS' if ok else 'FAIL'})")
        except Exception as e:  # noqa: BLE001
            results.append(f"{t}=ERROR({e})")
    return results


# ─── 主状态机 ─────────────────────────────────────────────────────────────────

def _advance(drv: Driver) -> int:
    phases = drv.spec["phases"]
    while drv.journal["phase_index"] < len(phases):
        idx = drv.journal["phase_index"]
        phase = phases[idx]
        t = phase["type"]
        if t == "parallel-review":
            return do_parallel_review(drv, phase)
        if t == "outer-loop":
            st = drv.journal["phase_state"].get(phase["id"], {})
            rp = st.get("pending_reviewer_prompt")
            if not rp:
                # outer 轮的首个 prompt 必须由上一段 pause 答案提供
                return drv.pause(
                    f"outer-loop 需要首个 reviewer prompt（写入 {drv.active / 'prompt-outer-1.md'} 后以 action=provide 续跑）",
                    {"kind": "need_prompt", "phase_id": phase["id"]},
                    {"action": {"kind": "choice", "options": ["provide", "abort"]},
                     "reviewer_prompt": {"kind": "file",
                                         "path": str(drv.active / "prompt-outer-1.md"),
                                         "description": "outer round 1 的 reviewer prompt"}},
                    ["provide", "abort"])
            st.pop("pending_reviewer_prompt")
            save_journal(drv.active, drv.journal)
            return do_outer_round(drv, phase, Path(rp))
        if t == "blind-recheck":
            return do_blind(drv, phase)
        if t == "design-review":
            return do_design_review(drv, phase)
        raise LoopFail(f"未知 phase type: {t}")
    # 全部 phase 完成 → 待 retrospective 后 finish
    retro = drv.active / "retrospective.md"
    return drv.pause(
        "全部 phase 完成。写 retrospective.md 后以 action=finish 续跑归档",
        {"kind": "before_finish"},
        {"action": {"kind": "choice", "options": ["finish", "abort"]},
         "retrospective": {"kind": "file", "path": str(retro),
                           "description": "复盘（orchestrator 撰写）"}},
        ["finish", "abort"])


def _handle_resume(drv: Driver, answers: dict) -> int:
    paused = drv.journal.get("paused")
    if not paused:
        raise LoopFail("journal 无 paused 状态——无暂停可续（应使用 run 或 status）")
    decision = paused["decision"]
    inputs = drv.require_inputs(paused["expect"], answers)
    action = inputs.get("action")
    drv.journal["paused"] = None
    save_journal(drv.active, drv.journal)

    if action == "abort":
        drv.journal["aborted"] = True
        save_journal(drv.active, drv.journal)
        print("[driver] 已按 agent 裁决终止（aborted）")
        return EXIT_ERROR

    kind = decision.get("kind")
    if kind == "phase_verdict":
        phase_id = decision["phase_id"]
        if action == "repair":
            ep = inputs.get("executor_prompt")
            if not ep:
                print("[driver] action=repair 需要 executor_prompt 文件", file=sys.stderr)
                raise ResumeUncertain()
            return do_executor(drv, phase_id, ep, _phase_executor_model(drv, phase_id))
        # proceed：当前 phase 完成；可选 skip=<id,id> 跳过后续 phase（如 uv-init
        # 全过时跳过 outer-loop/blind——是否跳过属 agent 判断，driver 只机械执行）
        _complete_phase(drv, phase_id)
        skip_set = {s.strip() for s in answers.get("skip", "").split(",") if s.strip()}
        phases = drv.spec["phases"]
        while drv.journal["phase_index"] < len(phases) and \
                phases[drv.journal["phase_index"]].get("id") in skip_set:
            skipped = phases[drv.journal["phase_index"]]["id"]
            drv.journal["history"].append({"phase_skipped": skipped})
            drv.journal["phase_index"] += 1
        save_journal(drv.active, drv.journal)
        return _advance(drv)

    if kind == "executor_done":
        phase_id = decision["phase_id"]
        if action == "repair":
            ep = inputs.get("executor_prompt")
            if not ep:
                print("[driver] action=repair 需要 executor_prompt 文件", file=sys.stderr)
                raise ResumeUncertain()
            max_inner = int((drv.spec.get("budget_config") or {}).get(
                "max_inner_loops", MAX_INNER_LOOPS_DEFAULT))
            if decision.get("inner_streak", 1) >= max_inner:
                print(f"[driver] inner loop 已达上限 {max_inner}，禁止继续 repair", file=sys.stderr)
                raise ResumeUncertain()
            return do_executor(drv, phase_id, ep, _phase_executor_model(drv, phase_id))
        # accepted：
        # - executor 服务的是 outer-loop 的阻断 → 同 phase 下一轮（不 complete，轮号推导 +1）
        # - 否则（uv/blind 的 executor）→ 当前 phase 完成；若下一 phase 是 outer-loop 且
        #   答案带了 reviewer_prompt 则直接喂给首轮，否则走 need_prompt pause
        phase = _find_phase(drv, phase_id)
        if phase and phase["type"] == "outer-loop":
            rp = inputs.get("reviewer_prompt")
            if not rp:
                print("[driver] outer-loop 修复验收后需要下一轮 reviewer_prompt 文件", file=sys.stderr)
                raise ResumeUncertain()
            st = drv.journal["phase_state"].setdefault(phase_id, {})
            st["pending_reviewer_prompt"] = str(rp)
            save_journal(drv.active, drv.journal)
            return _advance(drv)
        _complete_phase(drv, phase_id)
        phases = drv.spec["phases"]
        idx = drv.journal["phase_index"]
        rp = inputs.get("reviewer_prompt")
        if rp and idx < len(phases) and phases[idx].get("type") == "outer-loop":
            st = drv.journal["phase_state"].setdefault(phases[idx]["id"], {})
            st["pending_reviewer_prompt"] = str(rp)
            save_journal(drv.active, drv.journal)
        return _advance(drv)

    if kind == "spawn_failed":
        if action == "retry":
            return _advance(drv)  # 重跑当前 phase（reserve 幂等拒绝重复活跃 reservation）
        print("[driver] spawn_failed 未选 retry，按 abort 处理", file=sys.stderr)
        raise ResumeUncertain()

    if kind == "need_prompt":
        rp = inputs.get("reviewer_prompt")
        if action != "provide" or not rp:
            raise ResumeUncertain()
        phase_id = decision["phase_id"]
        st = drv.journal["phase_state"].setdefault(phase_id, {})
        st["pending_reviewer_prompt"] = str(rp)
        save_journal(drv.active, drv.journal)
        return _advance(drv)

    if kind == "before_finish":
        if action != "finish":
            raise ResumeUncertain()
        # retrospective 已由 require_inputs 校验存在
        verdict = drv.spec.get("final_verdict", "可执行")
        drv.journal["history"].append({"finish": verdict})
        save_journal(drv.active, drv.journal)
        _stash_driver_artifacts(drv)
        drv.finish(verdict)
        print(f"[driver] 完成：finish --verdict {verdict} 已归档")
        return EXIT_OK

    raise LoopFail(f"未知 decision kind: {kind}")


def _find_phase(drv: Driver, phase_id: str) -> dict | None:
    for ph in drv.spec["phases"]:
        if ph.get("id") == phase_id:
            return ph
    return None


def _stash_driver_artifacts(drv: Driver) -> None:
    """finish 前把 driver 自身的过程产物移出 active 根（archive 根 allowlist 只认
    合同文件；报告已并入产物骨架，journal/pause-request 为运行时状态）。
    归位目标 = <active 父目录>/tmp/<slug>-driver/（与 orchest prompt 归位同级的 tmp 约定）。
    注意：移动后 journal 不在原处——finish 若失败需人工移回（finish 失败属终态异常）。
    """
    dest = drv.active.parent / "tmp" / f"{drv.spec.get('slug', drv.active.name)}-driver"
    dest.mkdir(parents=True, exist_ok=True)
    for name in (".loop-journal.json", "pause-request.json"):
        p = drv.active / name
        if p.is_file():
            p.replace(dest / name)
    reports = drv.active / "reports"
    if reports.is_dir():
        import shutil
        shutil.move(str(reports), str(dest / "reports"))


def _phase_executor_model(drv: Driver, phase_id: str) -> str:
    ph = _find_phase(drv, phase_id)
    if ph and ph.get("executor_model"):
        return ph["executor_model"]
    for ph in drv.spec["phases"]:
        if ph.get("executor_model"):
            return ph["executor_model"]
    raise LoopFail("spec 未声明 executor_model")


def _complete_phase(drv: Driver, phase_id: str) -> None:
    idx = drv.journal["phase_index"]
    phases = drv.spec["phases"]
    if idx < len(phases) and phases[idx].get("id") == phase_id:
        drv.journal["phase_index"] = idx + 1
        drv.journal["history"].append({"phase_completed": phase_id})
        save_journal(drv.active, drv.journal)
    else:
        raise LoopFail(f"phase 完成登记与当前 phase_index 不一致: {phase_id} vs idx={idx}")


def run_loop(drv: Driver, answers: dict, resumed: bool) -> int:
    if drv.journal.get("aborted"):
        print("[driver] journal 标记 aborted——清理后重跑", file=sys.stderr)
        return EXIT_USAGE
    if drv.journal.get("paused"):
        if not resumed:
            print("[driver] 存在未决 pause——用 resume 续跑", file=sys.stderr)
            return EXIT_USAGE
        return _handle_resume(drv, answers)
    return _advance(drv)


def _init_budget_config(drv: Driver) -> None:
    """把 spec.budget_config 写入 _budget-state.json（首次 run；已存在则合并覆盖 config 键）。

    与 budget_gate 的状态结构一致：{"config": {...}, "extensions": [], "fsm": {...}}。
    """
    cfg = drv.spec.get("budget_config") or {}
    if not cfg:
        return
    p = drv.active / "_budget-state.json"
    if p.is_file():
        try:
            state = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            raise LoopFail(f"_budget-state.json 损坏: {e}")
    else:
        state = {"config": {}, "extensions": [], "fsm": {"mode": "standard", "severities": {}}}
    state.setdefault("config", {}).update(cfg)
    state.setdefault("extensions", [])
    state.setdefault("fsm", {"mode": "standard", "severities": {}})
    fd, tmp = tempfile.mkstemp(dir=str(drv.active), prefix=".budget-state.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(prog="converge_loop",
                                 description="converge 循环驱动器：spec 驱动的派发阶段全机械调度")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("run", "resume", "validate", "status"):
        p = sub.add_parser(name)
        p.add_argument("--spec", required=True)
        if name in ("run", "resume"):
            p.add_argument("--timeout-min", type=int)
        if name == "resume":
            p.add_argument("--answer", action="append", default=[])
    args = ap.parse_args()

    spec_path = Path(args.spec).resolve()
    if not spec_path.is_file():
        print(f"spec 不存在: {spec_path}", file=sys.stderr)
        return EXIT_USAGE
    try:
        spec = load_spec(spec_path)
    except SpecError as e:
        print(str(e), file=sys.stderr)
        return EXIT_USAGE
    errs = validate_spec(spec)
    if errs:
        for e in errs:
            print(f"spec 错误: {e}", file=sys.stderr)
        return EXIT_USAGE

    if args.command == "validate":
        print("spec 合法")
        print(f"  phases: {[p.get('id') for p in spec['phases']]}")
        return EXIT_OK

    answers = {}
    for kv in getattr(args, "answer", []):
        if "=" in kv:
            k, v = kv.split("=", 1)
            answers[k.strip()] = v.strip()

    drv = Driver(spec, spec_path, timeout_min=getattr(args, "timeout_min", None))
    try:
        if args.command == "run":
            if journal_path(drv.active).is_file():
                print("journal 已存在——用 resume 续跑，或清理后重跑", file=sys.stderr)
                return EXIT_USAGE
            _init_budget_config(drv)
            return run_loop(drv, answers={}, resumed=False)
        if args.command == "resume":
            return run_loop(drv, answers=answers, resumed=True)
        if args.command == "status":
            j = drv.journal
            print(json.dumps({"phase_index": j.get("phase_index"),
                              "paused": bool(j.get("paused")),
                              "aborted": j.get("aborted", False),
                              "history": j.get("history", [])},
                             ensure_ascii=False, indent=2))
            return EXIT_OK
    except ResumeUncertain:
        return EXIT_RESUME_UNCERTAIN
    except LoopFail as e:
        print(f"[driver] FAIL: {e}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
