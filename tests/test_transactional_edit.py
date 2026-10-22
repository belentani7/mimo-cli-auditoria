import os
import stat
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from transactional_edit import apply_verified_edit, resolve_source


class TransactionalEditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "module.py"
        self.source.write_text("answer = 1\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def candidates(self):
        return list(self.root.glob(".*-candidate-*"))

    def test_validated_candidate_commits_after_analysis(self):
        seen = []

        def verify(candidate):
            seen.append(candidate)
            self.assertEqual("answer = 1\n", self.source.read_text())
            self.assertEqual("answer = 2\n", (self.root / candidate).read_text())
            return []

        self.assertTrue(apply_verified_edit(self.root, "module.py", "answer = 2\n", verify))
        self.assertEqual("answer = 2\n", self.source.read_text())
        self.assertEqual([], self.candidates())
        self.assertEqual(1, len(seen))

    def test_analysis_diagnostics_leave_original_unchanged(self):
        result = apply_verified_edit(
            self.root, "module.py", "answer = ???\n",
            lambda _: [{"severity": "error", "message": "invalid"}],
        )
        self.assertFalse(result)
        self.assertEqual("answer = 1\n", self.source.read_text())
        self.assertEqual([], self.candidates())

    def test_missing_analyzer_fails_closed_without_writing(self):
        def fail(_):
            raise RuntimeError("Pyright did not execute")

        with self.assertRaisesRegex(RuntimeError, "Pyright"):
            apply_verified_edit(self.root, "module.py", "answer = 2\n", fail)
        self.assertEqual("answer = 1\n", self.source.read_text())
        self.assertEqual([], self.candidates())

    def test_concurrent_change_aborts_instead_of_overwriting_it(self):
        def concurrent(_):
            self.source.write_text("external editor was here\n", encoding="utf-8")
            return []

        with self.assertRaisesRegex(RuntimeError, "changed during"):
            apply_verified_edit(self.root, "module.py", "answer = 2\n", concurrent)
        self.assertEqual("external editor was here\n", self.source.read_text())
        self.assertEqual([], self.candidates())

    def test_preserves_original_permissions(self):
        os.chmod(self.source, 0o640)
        self.assertTrue(apply_verified_edit(self.root, "module.py", "x = 2\n", lambda _: []))
        self.assertEqual(0o640, stat.S_IMODE(self.source.stat().st_mode))

    def test_rejects_traversal_absolute_and_git_directory(self):
        for candidate in ["../outside.py", "/etc/passwd", ".git/config"]:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    resolve_source(self.root, candidate)
        self.assertEqual("answer = 1\n", self.source.read_text())

    def test_rejects_final_symlink(self):
        link = self.root / "link.py"
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable in this environment")
        with self.assertRaises(ValueError):
            apply_verified_edit(self.root, "link.py", "bad\n", lambda _: [])
        self.assertEqual("answer = 1\n", self.source.read_text())

    def test_invalid_new_content_fails_without_temp_file(self):
        with self.assertRaises(ValueError):
            apply_verified_edit(self.root, "module.py", None, lambda _: [])
        self.assertEqual([], self.candidates())


if __name__ == "__main__":
    unittest.main()
