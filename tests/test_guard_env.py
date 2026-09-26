import json
import subprocess
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "guard-env.sh"


def blocked(command):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    result = subprocess.run(
        ["bash", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True
    )
    return result.returncode == 2


class TestGuardEnv(unittest.TestCase):
    def test_blocks_dotenv(self):
        self.assertTrue(blocked("cat .env"))

    def test_blocks_named_dotenv_in_path(self):
        self.assertTrue(blocked("cat backend/.env.dev"))

    def test_blocks_dotenv_in_quotes(self):
        self.assertTrue(blocked("python -c 'open(\".env.local\").read()'"))

    def test_blocks_envrc(self):
        self.assertTrue(blocked("cat .envrc"))

    def test_allows_dotenv_example(self):
        self.assertFalse(blocked("cat .env.example"))

    def test_allows_os_environ(self):
        self.assertFalse(blocked("python -c 'import os; os.environ.get(\"X\")'"))

    def test_allows_attribute_named_env(self):
        self.assertFalse(blocked("python -c 'print(self.env_name)'"))

    def test_allows_venv(self):
        self.assertFalse(blocked(".venv/bin/python -V"))

    def test_blocks_dotenv_alongside_false_positive_word(self):
        self.assertTrue(blocked("python -c 'import os; os.environ' && cat .env"))


if __name__ == "__main__":
    unittest.main()
