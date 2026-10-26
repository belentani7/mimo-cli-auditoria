import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from transactional_edit import resolve_source, apply_verified_edit
from ghost_state import GhostStateEngine


class SymlinkAliasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / '.git').mkdir()
        (self.root / '.git' / 'config').write_text('private = true\n')
        (self.root / 'code').mkdir()
        (self.root / 'code' / 'example.py').write_text('x = 1\n')
        try:
            (self.root / 'alias').symlink_to(self.root / '.git', target_is_directory=True)
            (self.root / 'code-alias').symlink_to(self.root / 'code', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unsupported')

    def tearDown(self):
        self.tmp.cleanup()

    def test_rejects_alias_to_git_metadata(self):
        with self.assertRaises(ValueError):
            resolve_source(self.root, 'alias/config')
        with self.assertRaises(ValueError):
            apply_verified_edit(self.root, 'alias/config', 'overwrite\n', lambda _: [])
        self.assertEqual('private = true\n', (self.root / '.git' / 'config').read_text())

    def test_rejects_parent_symlink_even_inside_root(self):
        with self.assertRaises(ValueError):
            resolve_source(self.root, 'code-alias/example.py')

    def test_regular_nested_source_still_edits(self):
        self.assertTrue(apply_verified_edit(
            self.root, 'code/example.py', 'x = 2\n', lambda _: []
        ))
        self.assertEqual('x = 2\n', (self.root / 'code' / 'example.py').read_text())

    def test_parent_replaced_during_analysis_aborts_edit(self):
        def replace_parent(_candidate):
            (self.root / 'code').rename(self.root / 'code-old')
            (self.root / 'code').symlink_to(self.root / '.git', target_is_directory=True)
            return []
        with self.assertRaises(ValueError):
            apply_verified_edit(self.root, 'code/example.py', 'x = 2\n', replace_parent)
        self.assertEqual('x = 1\n', (self.root / 'code-old' / 'example.py').read_text())

    def test_static_analyzer_does_not_follow_symlink_parent(self):
        engine = GhostStateEngine(str(self.root))
        with patch('ghost_state.subprocess.run') as runner:
            with self.assertRaises(ValueError):
                engine.run_analysis('alias/config')
            runner.assert_not_called()


if __name__ == '__main__':
    unittest.main()
