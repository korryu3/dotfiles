"""filter-sessions.pyのテスト。

実行: python3 -m unittest test_filter_sessions -v （scripts/ディレクトリで）
"""

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "filter_sessions", Path(__file__).parent / "filter-sessions.py"
)
fs = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fs)


def epoch_ms(date_str: str, hh: int = 12) -> int:
    """ローカルTZの日時をhistory.jsonl形式のエポックミリ秒に変換する。"""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=hh)
    return int(dt.timestamp() * 1000)


def write_history(path: Path, entries: list[dict]) -> None:
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


class TestSessionIdsForDate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.history = Path(self.tmp.name) / "history.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_指定日のsessionIdを重複なく抽出する(self):
        write_history(self.history, [
            {"display": "a", "timestamp": epoch_ms("2026-07-06", 9), "sessionId": "sid-1"},
            {"display": "b", "timestamp": epoch_ms("2026-07-06", 10), "sessionId": "sid-1"},
            {"display": "c", "timestamp": epoch_ms("2026-07-06", 11), "sessionId": "sid-2"},
            {"display": "d", "timestamp": epoch_ms("2026-07-05", 23), "sessionId": "sid-other-day"},
            {"display": "e", "timestamp": epoch_ms("2026-07-07", 0), "sessionId": "sid-next-day"},
        ])
        ids = fs.session_ids_for_date(self.history, "2026-07-06")
        self.assertEqual(ids, ["sid-1", "sid-2"])


def write_session(path: Path, entries: list[dict]) -> None:
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


class TestExtractMessages(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = Path(self.tmp.name) / "sid-1.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_typeがuserとassistant以外のエントリを捨てる(self):
        write_session(self.session, [
            {"type": "user", "message": {"content": "こんにちは"}},
            {"type": "attachment", "message": {"content": "添付"}},
            {"type": "system", "content": "system msg"},
            {"type": "ai-title", "title": "タイトル"},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "応答です"}]}},
        ])
        messages = fs.extract_messages(self.session)
        self.assertEqual(messages, [
            {"role": "user", "text": "こんにちは"},
            {"role": "assistant", "text": "応答です"},
        ])


    def test_command系タグを含むuserメッセージを除外する(self):
        write_session(self.session, [
            {"type": "user", "message": {"content": "<command-name>/clear</command-name>"}},
            {"type": "user", "message": {"content": "<command-message>foo</command-message>\n<command-args></command-args>"}},
            {"type": "user", "message": {"content": "<local-command-caveat>注意</local-command-caveat>"}},
            {"type": "user", "message": {"content": "<local-command-stdout>コマンド出力</local-command-stdout>"}},
            {"type": "user", "message": {"content": "普通の発言"}},
        ])
        messages = fs.extract_messages(self.session)
        self.assertEqual(messages, [{"role": "user", "text": "普通の発言"}])


    def test_isMetaがtrueのuserエントリを除外する(self):
        write_session(self.session, [
            {"type": "user", "isMeta": True, "message": {"content": "メタエントリ"}},
            {"type": "user", "message": {"content": "本人の発言"}},
        ])
        messages = fs.extract_messages(self.session)
        self.assertEqual(messages, [{"role": "user", "text": "本人の発言"}])


    def test_userのlistコンテンツはtext要素のみ採用しtool_resultを捨てる(self):
        write_session(self.session, [
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "content": "ツール実行結果"},
            ]}},
            {"type": "user", "message": {"content": [
                {"type": "text", "text": "listの中の発言"},
                {"type": "tool_result", "content": "結果"},
            ]}},
        ])
        messages = fs.extract_messages(self.session)
        self.assertEqual(messages, [{"role": "user", "text": "listの中の発言"}])


    def test_assistantのthinkingとtool_useを捨てtextのみ連結する(self):
        write_session(self.session, [
            {"type": "assistant", "message": {"content": [
                {"type": "thinking", "thinking": "思考の中身"},
                {"type": "text", "text": "前半。"},
                {"type": "tool_use", "name": "Bash", "input": {}},
                {"type": "text", "text": "後半。"},
            ]}},
            {"type": "assistant", "message": {"content": [
                {"type": "thinking", "thinking": "思考のみ"},
            ]}},
        ])
        messages = fs.extract_messages(self.session)
        self.assertEqual(messages, [{"role": "assistant", "text": "前半。\n後半。"}])


    def test_maxメッセージ数を超えた分は切り捨てる(self):
        write_session(self.session, [
            {"type": "user", "message": {"content": f"発言{i}"}} for i in range(150)
        ])
        messages = fs.extract_messages(self.session, max_messages=100)
        self.assertEqual(len(messages), 100)
        self.assertEqual(messages[-1], {"role": "user", "text": "発言99"})


class TestSchemaError(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.history = Path(self.tmp.name) / "history.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_historyに必須キーがない場合SchemaErrorを送出する(self):
        write_history(self.history, [
            {"display": "a", "when": 12345, "session": "sid-1"},
        ])
        with self.assertRaises(fs.SchemaError):
            fs.session_ids_for_date(self.history, "2026-07-06")


class TestBuildReport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.history = self.root / "history.jsonl"
        self.projects = self.root / "projects"
        self.projects.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _make_session_file(self, project: str, sid: str, entries: list[dict]) -> None:
        pdir = self.projects / project
        pdir.mkdir(exist_ok=True)
        write_session(pdir / f"{sid}.jsonl", entries)

    def test_jsonl欠損セッションは統計に反映し正常続行する(self):
        write_history(self.history, [
            {"display": "a", "timestamp": epoch_ms("2026-07-06", 9), "sessionId": "sid-exists"},
            {"display": "b", "timestamp": epoch_ms("2026-07-06", 10), "sessionId": "sid-missing"},
        ])
        self._make_session_file("proj-a", "sid-exists", [
            {"type": "user", "message": {"content": "今日の作業について"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "了解です"}]}},
        ])
        report = fs.build_report("2026-07-06", self.history, self.projects)
        self.assertIn("当日2 session中、jsonl現存1件", report)
        self.assertIn("proj-a", report)
        self.assertIn("今日の作業について", report)
        self.assertIn("了解です", report)

    def test_100メッセージ超のセッションは切り捨てた旨を明記する(self):
        write_history(self.history, [
            {"display": "a", "timestamp": epoch_ms("2026-07-06"), "sessionId": "sid-long"},
        ])
        self._make_session_file("proj-a", "sid-long", [
            {"type": "user", "message": {"content": f"発言{i}"}} for i in range(150)
        ])
        report = fs.build_report("2026-07-06", self.history, self.projects)
        self.assertIn("発言99", report)
        self.assertNotIn("発言100", report)
        self.assertIn("以降省略", report)

    def test_該当セッションがない日は該当なしを出力する(self):
        write_history(self.history, [
            {"display": "a", "timestamp": epoch_ms("2026-07-01"), "sessionId": "sid-1"},
        ])
        report = fs.build_report("2026-07-06", self.history, self.projects)
        self.assertIn("該当なし", report)
        self.assertIn("当日0 session", report)


class TestCli(unittest.TestCase):
    SCRIPT = Path(__file__).parent / "filter-sessions.py"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.history = self.root / "history.jsonl"
        self.projects = self.root / "projects"
        self.projects.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *args):
        import subprocess
        return subprocess.run(
            ["python3", str(self.SCRIPT),
             "--history-path", str(self.history),
             "--projects-dir", str(self.projects), *args],
            capture_output=True, text=True,
        )

    def test_データなしでもexit0で該当なしをstdoutに出す(self):
        write_history(self.history, [])
        result = self._run("--date", "2026-07-06")
        self.assertEqual(result.returncode, 0)
        self.assertIn("該当なし", result.stdout)

    def test_date省略時は今日をローカルTZで対象にする(self):
        today = datetime.now().strftime("%Y-%m-%d")
        write_history(self.history, [
            {"display": "a", "timestamp": epoch_ms(today), "sessionId": "sid-today"},
        ])
        result = self._run()
        self.assertEqual(result.returncode, 0)
        self.assertIn("当日1 session", result.stdout)

    def test_スキーマ不一致はexit1でstderrにエラーを出す(self):
        write_history(self.history, [{"display": "a", "when": 1, "session": "x"}])
        result = self._run("--date", "2026-07-06")
        self.assertEqual(result.returncode, 1)
        self.assertIn("スキーマ不一致", result.stderr)


if __name__ == "__main__":
    unittest.main()
