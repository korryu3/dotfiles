import json
import subprocess
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "guard-pr-create.sh"


def exit_code(command):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    result = subprocess.run(
        ["bash", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True
    )
    return result.returncode


class TestGuardPrCreate(unittest.TestCase):
    def test_allows_draft_with_assignee(self):
        self.assertEqual(exit_code('gh pr create --draft --assignee @me --title "t" --body "b"'), 0)

    def test_allows_short_flags(self):
        self.assertEqual(exit_code('gh pr create -d -a @me -t "t" -b "b"'), 0)

    def test_allows_assignee_with_equals(self):
        self.assertEqual(exit_code('gh pr create --draft --assignee=@me --title "t"'), 0)

    def test_blocks_without_draft(self):
        self.assertEqual(exit_code('gh pr create --assignee @me --title "t" --body "b"'), 2)

    def test_allows_other_commands(self):
        self.assertEqual(exit_code("mv a.md archive/"), 0)

    def test_blocks_pr_create_after_cd(self):
        self.assertEqual(exit_code('cd repo && gh pr create --title "t"'), 2)

    def test_blocks_without_assignee(self):
        self.assertEqual(exit_code('gh pr create --draft --title "t" --body "b"'), 2)


if __name__ == "__main__":
    unittest.main()
