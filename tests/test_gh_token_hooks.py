import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / ".claude" / "hooks"
INJECT = HOOKS / "inject-gh-token.sh"
CLEANUP = HOOKS / "cleanup-gh-token.sh"
TOKEN = "tok-123"

# `gh auth token`にはTOKENを返し、それ以外の呼び出しでは受け取ったGH_TOKENを表示する偽gh
FAKE_GH = """#!/bin/bash
if [ "$1 $2" = "auth token" ]; then
  [ -n "${FAKE_GH_AUTH_FAIL:-}" ] && exit 1
  printf '%s' "$FAKE_GH_TOKEN"
  exit 0
fi
echo "gh-saw-token=${GH_TOKEN:-}"
"""


class GhTokenHookTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        fake = bin_dir / "gh"
        fake.write_text(FAKE_GH)
        fake.chmod(0o755)
        self.token_dir = self.tmp / "tokens"
        self.token_dir.mkdir()
        self.env = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "FAKE_GH_TOKEN": TOKEN,
            "CLAUDE_GH_TOKEN_DIR": str(self.token_dir),
        }
        self.env.pop("GH_TOKEN", None)

    def run_hook(self, script, payload, env=None):
        result = subprocess.run(
            ["bash", str(script)],
            input=json.dumps(payload),
            env=env or self.env,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def inject(self, command, tool_use_id="toolu_1", **extra_input):
        payload = {
            "tool_name": "Bash",
            "tool_use_id": tool_use_id,
            "tool_input": {"command": command, **extra_input},
        }
        return self.run_hook(INJECT, payload)

    def rewritten(self, command, **kwargs):
        out = self.inject(command, **kwargs)
        self.assertTrue(out, "gh を含むコマンドなのに書き換えが出力されなかった")
        return json.loads(out)["hookSpecificOutput"]["updatedInput"]

    def execute(self, command):
        result = subprocess.run(
            ["bash", "-c", command], env=self.env, capture_output=True, text=True
        )
        return result.stdout


class TestInjectGhToken(GhTokenHookTestCase):
    def test_command_without_gh_outputs_nothing(self):
        self.assertEqual(self.inject("ls -la"), "")

    def test_gh_command_is_rewritten_so_gh_receives_token(self):
        cmd = self.rewritten("gh api user")["command"]
        self.assertIn(f"gh-saw-token={TOKEN}", self.execute(cmd))

    def test_non_gh_process_in_same_command_does_not_receive_token(self):
        cmd = self.rewritten('gh api user; echo "other-saw-token=$(printenv GH_TOKEN)"')[
            "command"
        ]
        self.assertIn("other-saw-token=\n", self.execute(cmd))

    def test_gh_after_variable_assignment_receives_token(self):
        cmd = self.rewritten("S=1; gh api user")["command"]
        self.assertIn(f"gh-saw-token={TOKEN}", self.execute(cmd))

    def test_gh_after_cd_and_receives_token(self):
        cmd = self.rewritten(f"cd {self.tmp} && gh api user")["command"]
        self.assertIn(f"gh-saw-token={TOKEN}", self.execute(cmd))

    def test_gh_inside_loop_receives_token(self):
        cmd = self.rewritten("for i in 1; do gh api user; done")["command"]
        self.assertIn(f"gh-saw-token={TOKEN}", self.execute(cmd))

    def test_gh_inside_command_substitution_receives_token(self):
        cmd = self.rewritten('echo "$(gh api user)"')["command"]
        self.assertIn(f"gh-saw-token={TOKEN}", self.execute(cmd))

    def test_token_is_read_even_if_cat_is_overridden(self):
        cmd = self.rewritten("gh api user")["command"]
        overridden = "cat() { echo WRONG; }; " + cmd
        self.assertIn(f"gh-saw-token={TOKEN}", self.execute(overridden))

    def test_gh_as_part_of_word_is_not_detected(self):
        self.assertEqual(self.inject("git push origin gh-pages"), "")

    def test_output_has_no_permission_decision(self):
        out = json.loads(self.inject("gh api user"))
        self.assertNotIn("permissionDecision", out["hookSpecificOutput"])

    def test_updated_input_keeps_other_tool_input_fields(self):
        updated = self.rewritten(
            "gh api user", run_in_background=True, description="fetch user"
        )
        self.assertEqual(updated["run_in_background"], True)
        self.assertEqual(updated["description"], "fetch user")

    def test_token_file_is_separate_per_call(self):
        self.inject("gh api user", tool_use_id="toolu_A")
        self.inject("gh api user", tool_use_id="toolu_B")
        names = sorted(p.name for p in self.token_dir.iterdir())
        self.assertEqual(names, [".claude-gh-token-toolu_A", ".claude-gh-token-toolu_B"])

    def test_inject_removes_token_files_older_than_one_hour(self):
        stale = self.token_dir / ".claude-gh-token-toolu_old"
        stale.write_text("x")
        two_hours_ago = time.time() - 7200
        os.utime(stale, (two_hours_ago, two_hours_ago))
        self.inject("gh api user", tool_use_id="toolu_new")
        self.assertFalse(stale.exists())
        self.assertTrue((self.token_dir / ".claude-gh-token-toolu_new").exists())

    def test_auth_failure_outputs_nothing(self):
        env = {**self.env, "FAKE_GH_AUTH_FAIL": "1"}
        payload = {
            "tool_name": "Bash",
            "tool_use_id": "toolu_1",
            "tool_input": {"command": "gh api user"},
        }
        self.assertEqual(self.run_hook(INJECT, payload, env=env), "")


class TestCleanupGhToken(GhTokenHookTestCase):
    def test_cleanup_removes_only_own_token_file(self):
        self.inject("gh api user", tool_use_id="toolu_A")
        self.inject("gh api user", tool_use_id="toolu_B")
        self.run_hook(CLEANUP, {"tool_name": "Bash", "tool_use_id": "toolu_A"})
        names = [p.name for p in self.token_dir.iterdir()]
        self.assertEqual(names, [".claude-gh-token-toolu_B"])

    def test_cleanup_keeps_token_file_of_background_call(self):
        self.inject("gh api user", tool_use_id="toolu_bg", run_in_background=True)
        self.run_hook(
            CLEANUP,
            {
                "tool_name": "Bash",
                "tool_use_id": "toolu_bg",
                "tool_input": {"command": "gh api user", "run_in_background": True},
            },
        )
        self.assertTrue((self.token_dir / ".claude-gh-token-toolu_bg").exists())


if __name__ == "__main__":
    unittest.main()
