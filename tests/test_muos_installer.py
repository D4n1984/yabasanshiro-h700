import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'packaging/muos-h700/install-muos.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.app = self.root / m.APP
        self.app.mkdir(parents=True)
        for name in (*m.BINARIES, 'run-game.sh', *m.ADAPTERS):
            self.put(self.app / name, 'binary or script')
        for name in ('stage.sh', 'display.sh', 'launch.sh'):
            self.put(self.root / 'opt/muos/script/var' / name, '')
        (self.root / m.LAUNCH).mkdir(parents=True)
        (self.root / 'proc').mkdir()
        self.original = {'Sega Saturn': {'default': 'original', 'external': {'other': {'core': 'other'}}}, 'Other': {'untouched': True}}
        self.put(self.root / m.BUNDLE, json.dumps(self.original))
        self.probe = lambda path: None

    @staticmethod
    def put(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8')

    def run_install(self):
        return m.install(self.root, self.app, self.probe)

    def test_bundle_and_preservation(self):
        backup = self.run_install()
        result = json.loads((self.root / m.CUSTOM).read_text(encoding='utf-8'))
        self.assertEqual(result['Sega Saturn']['default'], 'original')
        self.assertEqual(result['Other'], self.original['Other'])
        self.assertEqual(result['Sega Saturn']['external']['other'], {'core': 'other'})
        self.assertEqual(result['Sega Saturn']['external']['yabasanshiro-h700-lto']['core'], 'ext-yabasanshiro-h700-lto')
        self.assertTrue((backup / 'core.bundle.json').is_file())

    def test_custom_malformed_leaves_files_untouched(self):
        self.put(self.root / m.CUSTOM, '{bad')
        with self.assertRaises(RuntimeError):
            self.run_install()
        self.assertEqual((self.root / m.CUSTOM).read_text(), '{bad')
        self.assertFalse((self.app / 'backups').exists())
        self.assertFalse((self.root / m.LAUNCH / m.ADAPTERS[0]).exists())

    def test_reinstall_backups_and_existing_saves(self):
        self.put(self.app / 'home/save', 'new')
        self.put(self.root / m.OLD / 'home/save', 'old')
        first = self.run_install()
        second = self.run_install()
        self.assertNotEqual(first, second)
        self.assertTrue((second / 'core.json').is_file())
        self.assertTrue((second / m.ADAPTERS[0]).is_file())
        self.assertEqual((self.app / 'home/save').read_text(), 'new')
        self.assertEqual((self.root / m.OLD / 'home/save').read_text(), 'old')

    def test_copy_old_save(self):
        self.put(self.root / m.OLD / 'home/save', 'save')
        self.run_install()
        self.assertEqual((self.app / 'home/save').read_text(), 'save')
        self.assertTrue((self.root / m.OLD / 'home/save').exists())

    def test_active_emulator_aborts(self):
        proc = self.root / 'proc/123'
        proc.mkdir()
        (proc / 'cmdline').write_bytes(b'/tmp/yabasanshiro-h700\0')
        try:
            os.symlink('/tmp/yabasanshiro-h700', proc / 'exe')
        except OSError:
            self.skipTest('symlinks unavailable')
        with self.assertRaises(RuntimeError):
            self.run_install()
        self.assertFalse((self.root / m.CUSTOM).exists())
        self.assertFalse((self.app / 'backups').exists())

    def test_failed_probe_aborts(self):
        def fail(path):
            raise RuntimeError('probe failed')
        self.probe = fail
        with self.assertRaises(RuntimeError):
            self.run_install()
        self.assertFalse((self.root / m.CUSTOM).exists())
        self.assertFalse((self.app / 'backups').exists())

    def test_pickles_running_aborts(self):
        proc = self.root / 'proc/456'
        proc.mkdir()
        (proc / 'cmdline').write_bytes(b'/opt/muos/frontend/muxretro\0')
        with self.assertRaises(RuntimeError):
            self.run_install()
        self.assertFalse((self.app / 'backups').exists())

    def test_valid_custom_manifest_is_preserved(self):
        custom = dict(self.original, Extra={'data': [1, 2, 3]})
        self.put(self.root / m.CUSTOM, json.dumps(custom))
        backup = self.run_install()
        result = json.loads((self.root / m.CUSTOM).read_text())
        self.assertEqual(result['Extra'], custom['Extra'])
        self.assertEqual(result['Sega Saturn']['default'], 'original')
        self.assertEqual(json.loads((backup / 'core.json').read_text()), custom)


if __name__ == '__main__':
    unittest.main()
