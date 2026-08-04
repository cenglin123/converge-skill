#!/usr/bin/env python3
"""kimi_pretooluse_shim 验收用例。

stdlib unittest，无外部依赖。运行：
    python -m unittest tests.test_kimi_pretooluse_shim -v

budget_gate 调用以 mock 子进程替代：测试把 shim 复制到临时目录的
scripts/hooks/ 布局下，并在上一级 scripts/ 放置 mock budget_gate.py，
保证在任意机器（无真实 budget_gate）上稳定通过。
"""

import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SHIM = Path(__file__).resolve().parent.parent / "scripts" / "hooks" / "kimi_pretooluse_shim.py"

# mock budget_gate.py：记录收到的 stdin（供断言归一化结果），
# tool_name == "Agent" 时打印固定 deny JSON（与真实 budget_gate 同格式）。
MOCK_GATE = textwrap.dedent('''\
    import json
    import sys
    raw = sys.stdin.read()
    with open(__file__ + ".stdin", "w", encoding="utf-8") as f:
        f.write(raw)
    obj = json.loads(raw)
    if obj.get("tool_name") == "Agent":
        print('{"hookSpecificOutput": {"permissionDecision": "deny", "permissionDecisionReason": "mock cap"}}')
    ''')


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.td = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def make_layout(self, with_gate: bool = True) -> Path:
        """把 shim 复制到临时 scripts/hooks/ 布局，返回 shim 副本路径。"""
        scripts = self.td / "scripts"
        hooks = scripts / "hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        shim_copy = hooks / "kimi_pretooluse_shim.py"
        shutil.copy2(SHIM, shim_copy)
        if with_gate:
            (scripts / "budget_gate.py").write_text(MOCK_GATE, encoding="utf-8")
        return shim_copy

    def run_shim(self, shim: Path, stdin_text: str, *extra_args):
        return subprocess.run(
            [sys.executable, str(shim), *extra_args],
            input=stdin_text.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )

    def gate_stdin(self) -> dict:
        capture = self.td / "scripts" / "budget_gate.py.stdin"
        return json.loads(capture.read_text(encoding="utf-8"))


class TestToolNameNormalization(Base):
    """tool_name / toolName / tool 三种键都必须归一化为 tool_name。"""

    def test_three_key_variants(self):
        for key in ("tool_name", "toolName", "tool"):
            with self.subTest(key=key):
                shim = self.make_layout()
                payload = json.dumps({key: "Agent", "session_id": "s1"})
                r = self.run_shim(shim, payload)
                self.assertEqual(r.returncode, 0, r.stderr)
                received = self.gate_stdin()
                self.assertEqual(received.get("tool_name"), "Agent")
                self.assertEqual(received.get("session_id"), "s1")


class TestVerbatimForwarding(Base):
    def test_deny_json_forwarded_verbatim(self):
        """deny JSON 必须逐字（字节级）转发。"""
        shim = self.make_layout()
        normalized = json.dumps({"tool_name": "Agent", "session_id": "s1"},
                                ensure_ascii=False).encode("utf-8")
        # 直接跑 mock gate 取得基准 stdout
        baseline = subprocess.run(
            [sys.executable, str(self.td / "scripts" / "budget_gate.py"), "hook-pretooluse"],
            input=normalized, capture_output=True, timeout=30,
        )
        r = self.run_shim(shim, json.dumps({"toolName": "Agent", "session_id": "s1"}))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, baseline.stdout)
        self.assertIn(b'"permissionDecision": "deny"', r.stdout)

    def test_non_spawn_tool_passthrough(self):
        """非 Agent 工具：gate 无输出，shim 也无输出、exit 0。"""
        shim = self.make_layout()
        r = self.run_shim(shim, json.dumps({"tool_name": "Read", "session_id": "s1"}))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, b"")


class TestFailOpen(Base):
    def test_malformed_stdin_fail_open(self):
        shim = self.make_layout()
        r = self.run_shim(shim, "not-json{")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, b"")
        self.assertIn(b"fail-open", r.stderr)

    def test_missing_budget_gate_fail_open(self):
        shim = self.make_layout(with_gate=False)
        r = self.run_shim(shim, json.dumps({"tool_name": "Agent", "session_id": "s1"}))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, b"")
        self.assertIn(b"fail-open", r.stderr)


class TestRecordSession(Base):
    def test_record_session_writes_file(self):
        shim = self.make_layout()
        target = self.td / "session.json"
        r = self.run_shim(shim, json.dumps({"session_id": "abc-123"}),
                          "--record-session", str(target))
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(data["session_id"], "abc-123")
        self.assertTrue(data.get("updated_at"))

    def test_record_session_missing_id_fail_open(self):
        shim = self.make_layout()
        target = self.td / "session.json"
        r = self.run_shim(shim, json.dumps({"tool_name": "Agent"}),
                          "--record-session", str(target))
        self.assertEqual(r.returncode, 0)
        self.assertFalse(target.exists())
        self.assertIn(b"fail-open", r.stderr)

    def test_record_session_write_failure_fail_open(self):
        """写入目标不可写（目标是已存在目录）时 fail-open。"""
        shim = self.make_layout()
        r = self.run_shim(shim, json.dumps({"session_id": "abc"}),
                          "--record-session", str(self.td))
        self.assertEqual(r.returncode, 0)
        self.assertIn(b"fail-open", r.stderr)


if __name__ == "__main__":
    unittest.main()
