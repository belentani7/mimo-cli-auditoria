import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ghost_state import GhostStateEngine


class GhostStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.path = Path(self.directory.name)
        (self.path / "example.py").write_text("x = 1\n", encoding="utf-8")
        self.engine = GhostStateEngine(str(self.path))

    def tearDown(self):
        self.directory.cleanup()

    def test_missing_pyright_is_not_reported_as_success(self):
        with patch("ghost_state.subprocess.run", side_effect=FileNotFoundError("pyright")):
            with self.assertRaisesRegex(RuntimeError, "did not execute"):
                self.engine.run_analysis("example.py")

    def test_invalid_json_is_not_reported_as_success(self):
        with patch("ghost_state.subprocess.run", return_value=subprocess.CompletedProcess([], 1, stdout="not-json")):
            with self.assertRaisesRegex(RuntimeError, "JSON"):
                self.engine.run_analysis("example.py")

    def test_pyright_error_diagnostics_are_preserved(self):
        raw = {"generalDiagnostics": [{"range": {"start": {"line": 3}}, "message": "Type mismatch", "severity": "error"}]}
        with patch("ghost_state.subprocess.run", return_value=subprocess.CompletedProcess([], 1, stdout=json.dumps(raw))):
            self.assertEqual([{"line": 4, "message": "Type mismatch", "severity": "error"}], self.engine.run_analysis("example.py"))

    def test_clean_pyright_result_is_allowed(self):
        with patch("ghost_state.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout='{"generalDiagnostics":[]}')):
            self.assertEqual([], self.engine.run_analysis("example.py"))

    def test_symlink_and_traversal_do_not_run_analyzer(self):
        with patch("ghost_state.subprocess.run") as task:
            with self.assertRaises(ValueError):
                self.engine.run_analysis("../outside.py")
            task.assert_not_called()

    def test_pyright_crash_without_diagnostics_is_error(self):
        with patch("ghost_state.subprocess.run", return_value=subprocess.CompletedProcess([], 2, stdout="")):
            with self.assertRaisesRegex(RuntimeError, "failed without"):
                self.engine.run_analysis("example.py")


    def test_pyright_error_exit_with_empty_diagnostics_never_approves_edit(self):
        raw = '{"generalDiagnostics":[]}'
        with patch("ghost_state.subprocess.run", return_value=subprocess.CompletedProcess([], 1, stdout=raw)):
            with self.assertRaisesRegex(RuntimeError, "provided no diagnostics"):
                self.engine.run_analysis("example.py")

    def test_pyright_summary_errors_without_diagnostics_do_not_pass(self):
        raw = '{"generalDiagnostics":[],"summary":{"errorCount":2}}'
        with patch("ghost_state.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout=raw)):
            with self.assertRaisesRegex(RuntimeError, "reported errors"):
                self.engine.run_analysis("example.py")

    def test_symlink_input_is_rejected_without_running_pyright(self):
        link = self.path / "alias.py"
        try:
            link.symlink_to(self.path / "example.py")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unsupported")
        with patch("ghost_state.subprocess.run") as task:
            with self.assertRaises(ValueError):
                self.engine.run_analysis("alias.py")
            task.assert_not_called()



if __name__ == "__main__":
    unittest.main()
