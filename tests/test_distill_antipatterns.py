#!/usr/bin/env python3
"""distill_antipatterns --calibration 模式验收用例（plan r2 D7）。

覆盖：样本解析、唯一性、unavailable/unverifiable 语义、绑定交叉核验、
evidence_refs 强制 unavailable、corpus digest、事件 high-water、排除规则、
确定性 canonical 输出（sorted keys / compact / UTF-8 / 单 LF）、CRLF 污染拒绝。

运行：
    python -m unittest tests.test_distill_antipatterns -v
"""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import distill_antipatterns as da  # noqa: E402

DISTILL = SCRIPTS / "distill_antipatterns.py"

UUID_1 = "b6f4e8a3-13f6-4e33-a273-353d930a23b4"


def canon_bytes(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def retro_text(sample: dict) -> str:
    return ("# Retrospective · x\n\n## 7. 经验教训\n\n```json\n"
            + json.dumps(sample, indent=2, ensure_ascii=False) + "\n```\n")


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.done = self.root / ".converge" / "done"
        self.done.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def slug_dir(self, slug="20260901-task-a") -> Path:
        d = self.done / slug
        d.mkdir(parents=True, exist_ok=True)
        return d

    def write_bindings(self, d: Path, high_watermark=17):
        """在 slug 目录写入四份绑定记录，返回 {binding_key: (path, sha256)}。"""
        files = {}
        bs = d / "_budget-state.json"
        bs.write_bytes(b'{"config": {}}\n')
        files["budget_state"] = ("_budget-state.json", sha(bs.read_bytes()))
        gl = d / "gate-ledger.jsonl"
        gl.write_bytes(b'{"event": "reserved"}\n')
        files["gate_ledger"] = ("gate-ledger.jsonl", sha(gl.read_bytes()))
        r1 = d / "round-1.md"
        r1.write_bytes("# Round 1\n".encode("utf-8"))
        files["rounds"] = ("round-1.md", sha(r1.read_bytes()))
        at = d / "attempts.md"
        at.write_bytes("# attempts\n".encode("utf-8"))
        files["attempts"] = ("attempts.md", sha(at.read_bytes()))
        return files

    def make_sample(self, files, *, high_watermark=17, outer_usage=7,
                    blind_usage=3, productive_outer=True, productive_blind=True,
                    outer_evidence=None, blind_evidence=None):
        def prod(v, ev):
            if v == "unavailable":
                return {"value": "unavailable", "evidence_refs": []}
            return {"value": v,
                    "evidence_refs": ev if ev is not None else ["round-1.md"]}
        return {
            "schema": "converge.calibration-sample/v1",
            "revision_id": "r1",
            "bindings": {
                "budget_state": {"path": files["budget_state"][0],
                                 "sha256": files["budget_state"][1]},
                "gate_ledger": {"path": files["gate_ledger"][0],
                                "sha256": files["gate_ledger"][1],
                                "high_watermark": high_watermark},
                "rounds": [{"path": files["rounds"][0],
                            "sha256": files["rounds"][1],
                            "invocation_id": UUID_1}],
                "attempts": {"path": files["attempts"][0],
                             "sha256": files["attempts"][1]},
            },
            "configured_limits": {"outer": 8, "blind": 3, "inner": 3,
                                  "task_envelope": "unavailable"},
            "usage": {"outer": outer_usage, "blind": blind_usage,
                      "inner_max_per_outer": 1},
            "productive_at_or_after_limit": {
                "outer": prod(productive_outer, outer_evidence),
                "blind": prod(productive_blind, blind_evidence),
                "inner": {"value": "unavailable", "evidence_refs": []},
            },
            "accounting_scope": "instrumented_dispatch_only",
            "accounting_coverage": "unavailable",
            "model_invocations": "unavailable",
            "terminal": {"value": "可执行", "reviewer_terminal_event_id": UUID_1},
        }

    def build(self):
        return da.build_calibration_report(self.root)

    def build_bytes(self):
        return da.canonical_json_bytes(self.build())

    def entry(self, report, ref):
        for e in report["corpus"]:
            if e["ref"] == ref:
                return e
        return None


class TestSampleParsing(Base):
    def test_missing_sample_unavailable(self):
        d = self.slug_dir()
        (d / "retrospective.md").write_bytes("# Retrospective\n无样本。\n"
                                             .encode("utf-8"))
        rep = self.build()
        e = self.entry(rep, "done:20260901-task-a")
        self.assertIsNotNone(e)
        self.assertEqual(e["quantitative_status"], "unavailable")
        self.assertEqual(e["reason"], "no_sample")
        self.assertEqual(rep["quantitative_aggregates"]["eligible_samples"], 0)
        self.assertEqual(rep["quantitative_aggregates"]["status"], "unavailable")

    def test_valid_bound_sample_eligible(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        sample = self.make_sample(files, outer_usage=7, blind_usage=3)
        (d / "retrospective.md").write_bytes(retro_text(sample).encode("utf-8"))
        rep = self.build()
        e = self.entry(rep, "done:20260901-task-a")
        self.assertEqual(e["quantitative_status"], "eligible")
        self.assertEqual(e["sample_digest"], sha(canon_bytes(sample)))
        self.assertEqual(e["bindings"]["budget_state"], files["budget_state"][1])
        self.assertEqual(e["bindings"]["gate_ledger"]["sha256"],
                         files["gate_ledger"][1])
        self.assertEqual(e["bindings"]["gate_ledger"]["high_watermark"], 17)
        self.assertEqual(e["usage"]["outer"], 7)
        self.assertTrue(e["productive"]["outer"])
        agg = rep["quantitative_aggregates"]
        self.assertEqual(agg["eligible_samples"], 1)
        self.assertEqual(agg["status"], "available")
        self.assertEqual(agg["outer"]["max_productive_usage"], 7)
        self.assertEqual(agg["blind"]["max_productive_usage"], 3)
        self.assertEqual(rep["freshness"]["source_event_high_watermark"], 17)

    def test_corpus_digest_matches_corpus_bytes(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        sample = self.make_sample(files)
        (d / "retrospective.md").write_bytes(retro_text(sample).encode("utf-8"))
        rep = self.build()
        self.assertEqual(rep["corpus_digest"], sha(canon_bytes(rep["corpus"])))

    def test_duplicate_sample_same_revision_excluded(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        sample = self.make_sample(files)
        text = retro_text(sample) + "\n```json\n" + \
            json.dumps(sample, indent=2, ensure_ascii=False) + "\n```\n"
        (d / "retrospective.md").write_bytes(text.encode("utf-8"))
        e = self.entry(self.build(), "done:20260901-task-a")
        self.assertEqual(e["quantitative_status"], "excluded")
        self.assertEqual(e["reason"], "duplicate_sample")

    def test_older_revision_sample_ignored_current_is_last(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        old = self.make_sample(files, outer_usage=5)
        old["revision_id"] = "r1"
        cur = self.make_sample(files, outer_usage=7)
        cur["revision_id"] = "r2"
        text = ("# R\n\n```json\n" + json.dumps(old, indent=2) + "\n```\n"
                + "\n## 修订 2\n\n```json\n" + json.dumps(cur, indent=2) + "\n```\n")
        (d / "retrospective.md").write_bytes(text.encode("utf-8"))
        e = self.entry(self.build(), "done:20260901-task-a")
        self.assertEqual(e["quantitative_status"], "eligible")
        self.assertEqual(e["revision_id"], "r2")
        self.assertEqual(e["usage"]["outer"], 7)

    def test_malformed_sample_excluded(self):
        d = self.slug_dir()
        (d / "retrospective.md").write_bytes(
            "# R\n\n```json\n{\"schema\": \"converge.calibration-sample/v1\", broken\n```\n"
            .encode("utf-8"))
        e = self.entry(self.build(), "done:20260901-task-a")
        self.assertEqual(e["quantitative_status"], "excluded")
        self.assertTrue(e["reason"].startswith("malformed"), e["reason"])

    def test_missing_required_field_excluded(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        sample = self.make_sample(files)
        del sample["usage"]
        (d / "retrospective.md").write_bytes(retro_text(sample).encode("utf-8"))
        e = self.entry(self.build(), "done:20260901-task-a")
        self.assertEqual(e["quantitative_status"], "excluded")
        self.assertTrue(e["reason"].startswith("bad_schema"), e["reason"])

    def test_unknown_field_excluded(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        sample = self.make_sample(files)
        sample["surprise"] = 1
        (d / "retrospective.md").write_bytes(retro_text(sample).encode("utf-8"))
        e = self.entry(self.build(), "done:20260901-task-a")
        self.assertEqual(e["quantitative_status"], "excluded")
        self.assertTrue(e["reason"].startswith("bad_schema"), e["reason"])


class TestBindings(Base):
    def test_binding_hash_mismatch_excluded(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        sample = self.make_sample(files)
        sample["bindings"]["attempts"]["sha256"] = "0" * 64
        (d / "retrospective.md").write_bytes(retro_text(sample).encode("utf-8"))
        e = self.entry(self.build(), "done:20260901-task-a")
        self.assertEqual(e["quantitative_status"], "excluded")
        self.assertTrue(e["reason"].startswith("binding_mismatch"), e["reason"])

    def test_binding_records_absent_unverifiable(self):
        d = self.slug_dir()
        # 声明绑定但不创建任何文件
        ghost = ("_ghost.json", "0" * 64)
        sample = self.make_sample(
            {"budget_state": ghost, "gate_ledger": ghost,
             "rounds": ghost, "attempts": ghost})
        (d / "retrospective.md").write_bytes(retro_text(sample).encode("utf-8"))
        e = self.entry(self.build(), "done:20260901-task-a")
        self.assertEqual(e["quantitative_status"], "unverifiable")

    def test_legacy_sample_without_bindings_unverifiable(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        sample = self.make_sample(files)
        del sample["bindings"]
        (d / "retrospective.md").write_bytes(retro_text(sample).encode("utf-8"))
        e = self.entry(self.build(), "done:20260901-task-a")
        self.assertEqual(e["quantitative_status"], "unverifiable")
        # 不可绑定样本列入报告但不进定量聚合
        self.assertEqual(self.build()["quantitative_aggregates"]
                         ["eligible_samples"], 0)


class TestProductivityEvidence(Base):
    def test_productive_true_without_evidence_forced_unavailable(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        sample = self.make_sample(files, outer_usage=12, productive_outer=True,
                                  outer_evidence=[])
        (d / "retrospective.md").write_bytes(retro_text(sample).encode("utf-8"))
        rep = self.build()
        e = self.entry(rep, "done:20260901-task-a")
        # 样本本身可绑定（eligible），但 outer 推进证据被强制 unavailable
        self.assertEqual(e["quantitative_status"], "eligible")
        self.assertEqual(e["productive"]["outer"], "unavailable")
        self.assertIsNone(rep["quantitative_aggregates"]["outer"]
                          ["max_productive_usage"])
        self.assertEqual(rep["quantitative_aggregates"]["outer"]
                         ["productive_samples"], 0)

    def test_productive_false_without_evidence_forced_unavailable(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        sample = self.make_sample(files, productive_blind=False, blind_evidence=[])
        (d / "retrospective.md").write_bytes(retro_text(sample).encode("utf-8"))
        e = self.entry(self.build(), "done:20260901-task-a")
        self.assertEqual(e["productive"]["blind"], "unavailable")


class TestCanonicalOutput(Base):
    def test_deterministic_bytes(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        (d / "retrospective.md").write_bytes(
            retro_text(self.make_sample(files)).encode("utf-8"))
        self.assertEqual(self.build_bytes(), self.build_bytes())

    def test_canonical_form(self):
        d = self.slug_dir()
        (d / "retrospective.md").write_bytes("# R\n".encode("utf-8"))
        raw = self.build_bytes()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertFalse(raw.endswith(b"\n\n"))
        self.assertNotIn(b"\r", raw)
        # sorted keys + compact separators 可复算
        self.assertEqual(raw, canon_bytes(json.loads(raw.decode("utf-8"))))

    def test_crlf_payload_rejected(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        text = retro_text(self.make_sample(files))
        (d / "retrospective.md").write_bytes(text.replace("\n", "\r\n")
                                             .encode("utf-8"))
        e = self.entry(self.build(), "done:20260901-task-a")
        self.assertEqual(e["quantitative_status"], "excluded")
        self.assertIn("crlf", e["reason"])

    def test_cli_output_file_and_stdout(self):
        d = self.slug_dir()
        files = self.write_bindings(d)
        (d / "retrospective.md").write_bytes(
            retro_text(self.make_sample(files)).encode("utf-8"))
        out_path = self.root / "report.json"
        r = subprocess.run(
            [sys.executable, str(DISTILL), "--calibration",
             "--root", str(self.root), "--output", str(out_path)],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        written = out_path.read_bytes()
        self.assertEqual(written, self.build_bytes())
        # 缺省打印：stdout 与文件字节一致
        r2 = subprocess.run(
            [sys.executable, str(DISTILL), "--calibration",
             "--root", str(self.root)],
            capture_output=True)
        self.assertEqual(r2.returncode, 0, r2.stderr.decode("utf-8", "replace"))
        self.assertEqual(r2.stdout, written)

    def test_excluded_samples_not_in_aggregates(self):
        # 一个 eligible（outer 7 有推进），一个 binding_mismatch（outer 12）——
        # 聚合只反映 eligible 样本。
        d1 = self.slug_dir("20260901-task-a")
        f1 = self.write_bindings(d1)
        (d1 / "retrospective.md").write_bytes(
            retro_text(self.make_sample(f1, outer_usage=7)).encode("utf-8"))
        d2 = self.slug_dir("20260902-task-b")
        f2 = self.write_bindings(d2)
        bad = self.make_sample(f2, outer_usage=12)
        bad["bindings"]["attempts"]["sha256"] = "0" * 64
        (d2 / "retrospective.md").write_bytes(retro_text(bad).encode("utf-8"))
        rep = self.build()
        self.assertEqual(rep["quantitative_aggregates"]["eligible_samples"], 1)
        self.assertEqual(rep["quantitative_aggregates"]["outer"]
                         ["max_productive_usage"], 7)
        # corpus 排序确定
        refs = [e["ref"] for e in rep["corpus"]]
        self.assertEqual(refs, sorted(refs))


if __name__ == "__main__":
    unittest.main(verbosity=2)
