"""Integration tests for the prototype core's safe edit transaction.

Use fake AST/analysis adapters: no model calls, network or Pyright binary.
"""
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cli_coder_core import CLI_Coder


class FakeAST:
    def apply_search_replace(self, original, search, replacement):
        if search not in original:
            return {"status": "REJECTED", "reason": "SEARCH_NOT_FOUND"}
        return {"status": "ACCEPTED", "new_content": original.replace(search, replacement, 1)}


class FakeStatic:
    def __init__(self, original, *, diagnostics=None, error=None, concurrent=False):
        self.original = original
        self.diagnostics = diagnostics if diagnostics is not None else []
        self.error = error
        self.concurrent = concurrent
        self.checked_candidate = False

    def run_analysis(self, candidate):
        self.checked_candidate = True
        if "-candidate-" not in candidate:
            raise AssertionError("The original source was passed to static analysis")
        if self.original.read_text(encoding="utf-8") != "answer = 1\n":
            raise AssertionError("The original source changed before analysis completed")
        if self.concurrent:
            self.original.write_text("external change\n", encoding="utf-8")
        if self.error:
            raise RuntimeError(self.error)
        return self.diagnostics


class CoreTransactionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "code.py"
        self.source.write_text("answer = 1\n", encoding="utf-8")
        self.agent = object.__new__(CLI_Coder)
        self.agent.repo_path = self.root
        self.agent.ast_engine = FakeAST()

    def tearDown(self):
        self.tmp.cleanup()

    def test_successful_edit_commits_after_static_analysis(self):
        self.agent.ghost_engine = FakeStatic(self.source)
        self.assertTrue(self.agent.auto_heal_loop("code.py", "answer = 1", "answer = 2"))
        self.assertTrue(self.agent.ghost_engine.checked_candidate)
        self.assertEqual("answer = 2\n", self.source.read_text())

    def test_diagnostics_reject_edit_without_mutation(self):
        self.agent.ghost_engine = FakeStatic(self.source, diagnostics=[{"severity": "error"}])
        self.assertFalse(self.agent.auto_heal_loop("code.py", "answer = 1", "answer = 2"))
        self.assertEqual("answer = 1\n", self.source.read_text())

    def test_analyzer_failure_rejects_edit_without_mutation(self):
        self.agent.ghost_engine = FakeStatic(self.source, error="Pyright unavailable")
        self.assertFalse(self.agent.auto_heal_loop("code.py", "answer = 1", "answer = 2"))
        self.assertEqual("answer = 1\n", self.source.read_text())

    def test_failed_ast_does_not_call_nonexistent_feedback_method(self):
        self.agent.ghost_engine = FakeStatic(self.source)
        self.assertFalse(self.agent.auto_heal_loop("code.py", "absent", "answer = 2"))
        self.assertFalse(self.agent.ghost_engine.checked_candidate)
        self.assertEqual("answer = 1\n", self.source.read_text())

    def test_concurrent_edit_never_gets_overwritten(self):
        self.agent.ghost_engine = FakeStatic(self.source, concurrent=True)
        self.assertFalse(self.agent.auto_heal_loop("code.py", "answer = 1", "answer = 2"))
        self.assertEqual("external change\n", self.source.read_text())

    def test_outside_repository_is_rejected_before_read(self):
        self.agent.ghost_engine = FakeStatic(self.source)
        self.assertFalse(self.agent.auto_heal_loop("../outside.py", "a", "b"))
        self.assertFalse(self.agent.ghost_engine.checked_candidate)


if __name__ == "__main__":
    unittest.main()
