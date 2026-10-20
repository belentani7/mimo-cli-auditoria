import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from git_manager import GitManager


class GitManagerSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.repo_path = Path(self.temporary_directory.name)
        self._run_git("init")
        self._run_git("config", "user.email", "tests@example.invalid")
        self._run_git("config", "user.name", "GitManager tests")
        (self.repo_path / "tracked.txt").write_text("base\n", encoding="utf-8")
        self._run_git("add", "--", "tracked.txt")
        self._run_git("commit", "-m", "initial")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _run_git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def test_commit_requires_explicit_paths(self) -> None:
        (self.repo_path / "tracked.txt").write_text("changed\n", encoding="utf-8")

        with self.assertRaises(ValueError):
            GitManager(str(self.repo_path)).commit("must not stage everything")

        self.assertEqual("", self._run_git("diff", "--cached", "--name-only"))
        self.assertEqual(" M tracked.txt", self._run_git("status", "--porcelain"))

    def test_commit_stages_only_selected_paths(self) -> None:
        (self.repo_path / "tracked.txt").write_text("selected\n", encoding="utf-8")
        (self.repo_path / "other.txt").write_text("leave unstaged\n", encoding="utf-8")

        GitManager(str(self.repo_path)).commit("commit one file", paths=["tracked.txt"])

        committed = self._run_git("show", "--pretty=format:", "--name-only", "HEAD").splitlines()
        unstaged = self._run_git("diff", "--name-only").splitlines()
        self.assertEqual(["tracked.txt"], committed)
        self.assertEqual(["other.txt"], unstaged)

    def test_commit_rejects_paths_outside_repository(self) -> None:
        with self.assertRaises(ValueError):
            GitManager(str(self.repo_path)).commit("reject traversal", paths=["../outside.txt"])

        self.assertEqual("", self._run_git("diff", "--cached", "--name-only"))

    def test_rollback_requires_confirmation_and_preserves_history(self) -> None:
        (self.repo_path / "added.txt").write_text("keep history\n", encoding="utf-8")
        self._run_git("add", "--", "added.txt")
        self._run_git("commit", "-m", "add file")
        original_head = self._run_git("rev-parse", "HEAD")
        manager = GitManager(str(self.repo_path))

        with self.assertRaises(PermissionError):
            manager.rollback()

        self.assertEqual(original_head, self._run_git("rev-parse", "HEAD"))
        manager.rollback(confirm=True)

        self.assertEqual(3, len(self._run_git("rev-list", "--count", "HEAD").splitlines()))
        self.assertFalse((self.repo_path / "added.txt").exists())
        self.assertEqual("", self._run_git("status", "--porcelain"))


if __name__ == "__main__":
    unittest.main()
