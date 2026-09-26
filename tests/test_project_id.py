import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".claude" / "scripts" / "project-id.sh"

# 利用者のgit設定に左右されないよう、グローバル・システム設定を読ませない
GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, env=GIT_ENV, check=True, capture_output=True)


def project_id(cwd):
    # bashがPWDを実行ディレクトリから決めるよう、親プロセスのPWDを渡さない
    env = {k: v for k, v in GIT_ENV.items() if k != "PWD"}
    result = subprocess.run(
        ["bash", str(SCRIPT)], cwd=cwd, env=env, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def id_of(path):
    return str(path).replace("/", "-")


class TestProjectId(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        # macOSの/varは/private/varへのリンクなので実体のパスに揃える
        self.tmp = Path(tmp.name).resolve()

    def make_repo(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        git("init", "-q", cwd=repo)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
        return repo

    def make_worktree(self, repo):
        worktree = repo / ".claude" / "worktrees" / "wt"
        git("worktree", "add", "-q", "-b", "wt", str(worktree), cwd=repo)
        return worktree

    def test_repo_root_returns_root_path_id(self):
        repo = self.make_repo()
        self.assertEqual(project_id(repo), id_of(repo))

    def test_subdirectory_returns_same_id_as_root(self):
        repo = self.make_repo()
        sub = repo / "frontend" / "app"
        sub.mkdir(parents=True)
        self.assertEqual(project_id(sub), id_of(repo))

    def test_linked_worktree_returns_main_checkout_id(self):
        repo = self.make_repo()
        worktree = self.make_worktree(repo)
        self.assertEqual(project_id(worktree), id_of(repo))

    def test_linked_worktree_subdirectory_returns_main_checkout_id(self):
        repo = self.make_repo()
        worktree = self.make_worktree(repo)
        sub = worktree / "backend"
        sub.mkdir()
        self.assertEqual(project_id(sub), id_of(repo))

    def test_outside_git_returns_pwd_id(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        self.assertEqual(project_id(plain), id_of(plain))

    def test_common_dir_not_named_dotgit_uses_worktree_root(self):
        repo = self.tmp / "repo"
        git("init", "-q", "--separate-git-dir", str(self.tmp / "gitdir"), str(repo), cwd=self.tmp)
        sub = repo / "sub"
        sub.mkdir()
        self.assertEqual(project_id(sub), id_of(repo))


if __name__ == "__main__":
    unittest.main()
