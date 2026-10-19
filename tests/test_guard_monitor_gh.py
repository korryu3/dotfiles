import json
import subprocess
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "guard-monitor-gh.sh"


def exit_code(tool_input):
    payload = {"tool_name": "Monitor", "tool_input": tool_input}
    result = subprocess.run(
        ["bash", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True
    )
    return result.returncode


def monitor(command):
    return exit_code({"command": command, "description": "x", "timeout_ms": 1000})


class TestGuardMonitorGh(unittest.TestCase):
    def test_blocks_gh_command(self):
        self.assertEqual(monitor("gh pr checks 123"), 2)

    def test_blocks_gh_inside_loop(self):
        self.assertEqual(monitor("while true; do gh api x; sleep 30; done"), 2)

    def test_allows_command_starting_with_gh(self):
        self.assertEqual(monitor("ghq list"), 0)

    def test_allows_path_containing_gh(self):
        self.assertEqual(monitor("tail -f gh.log"), 0)

    def test_allows_ws_source(self):
        self.assertEqual(
            exit_code({"ws": {"url": "wss://example.com"}, "description": "x", "timeout_ms": 1000}), 0
        )


if __name__ == "__main__":
    unittest.main()
