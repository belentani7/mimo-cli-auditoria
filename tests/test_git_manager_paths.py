import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from git_manager import GitManager


class ExplicitPathSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git('init')
        self.git('config', 'user.email', 'tests@example.invalid')
        self.git('config', 'user.name', 'Factory tests')
        (self.root / 'tracked.txt').write_text('initial\n')
        self.git('add', '--', 'tracked.txt')
        self.git('commit', '-m', 'initial')
        self.manager = GitManager(str(self.root))

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def test_directory_path_never_stages_unrelated_files(self):
        (self.root / 'assets').mkdir()
        (self.root / 'assets' / 'feature.txt').write_text('feature\n')
        (self.root / 'assets' / 'secret.txt').write_text('private\n')
        before = self.git('rev-parse', 'HEAD')
        with self.assertRaisesRegex(ValueError, 'directorios'):
            self.manager.commit('unsafe bulk commit', paths=['assets'])
        self.assertEqual(before, self.git('rev-parse', 'HEAD'))
        self.assertEqual('', self.git('diff', '--cached', '--name-only'))
        self.assertTrue((self.root / 'assets' / 'secret.txt').exists())

    def test_symlinked_parent_to_git_metadata_is_rejected(self):
        try:
            (self.root / 'alias').symlink_to(self.root / '.git', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        with self.assertRaises(ValueError):
            self.manager.commit('unsafe git alias', paths=['alias/config'])
        self.assertEqual('', self.git('diff', '--cached', '--name-only'))

    def test_symlink_to_regular_file_is_rejected(self):
        try:
            (self.root / 'alias.txt').symlink_to(self.root / 'tracked.txt')
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        with self.assertRaisesRegex(ValueError, 'simbólicas'):
            self.manager.commit('unsafe symlink', paths=['alias.txt'])
        self.assertEqual('', self.git('diff', '--cached', '--name-only'))

    def test_explicit_new_file_and_tracked_deletion_still_work(self):
        (self.root / 'feature.txt').write_text('feature\n')
        self.manager.commit('add selected', paths=['feature.txt'])
        self.assertEqual(['feature.txt'], self.git('show', '--pretty=format:', '--name-only', 'HEAD').splitlines())
        (self.root / 'tracked.txt').unlink()
        self.manager.commit('delete selected', paths=['tracked.txt'])
        self.assertEqual(['tracked.txt'], self.git('show', '--pretty=format:', '--name-only', 'HEAD').splitlines())


if __name__ == '__main__':
    unittest.main()
