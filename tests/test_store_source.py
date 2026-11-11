"""Exercise the package integrity CLI against disposable build inputs."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / 'scripts/check-store-source.py'


class StoreIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Path(self.temp.name) / 'package'
        shutil.copytree(ROOT / 'govee2mqtt_security_local', self.store,
                        ignore=shutil.ignore_patterns('target', '.env*', '__pycache__'))

    def run_check(self, *args):
        return subprocess.run(['python3', str(CHECK), '--store', str(self.store), *args],
                              capture_output=True, text=True)

    def test_changed_source_requires_metadata_refresh(self):
        path = self.store / 'local-source/src/main.rs'
        path.write_text(path.read_text() + '\n// synthetic change\n')
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('stale', result.stdout)
        self.assertEqual(self.run_check('--write').returncode, 0)
        self.assertEqual(self.run_check().returncode, 0)

    def test_added_source_is_included_and_removed_source_is_detected(self):
        path = self.store / 'local-source/src/synthetic.rs'
        path.write_text('// fixture\n')
        self.assertNotEqual(self.run_check().returncode, 0)
        self.assertEqual(self.run_check('--write').returncode, 0)
        self.assertIn('!local-source/src/synthetic.rs', (self.store / '.dockerignore').read_text())
        path.unlink()
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_version_mismatch_is_detected(self):
        (self.store / 'SOURCE_TAG').write_text('wrong-version\n')
        self.assertNotEqual(self.run_check().returncode, 0)
        self.assertEqual(self.run_check('--write').returncode, 0)
        metadata = json.loads((self.store / 'SOURCE.json').read_text())
        self.assertEqual((self.store / 'SOURCE_TAG').read_text().strip(), metadata['version'])

    def test_symlink_and_private_inputs_are_refused(self):
        path = self.store / 'local-source/src/synthetic.rs'
        path.symlink_to(self.store / 'local-source/src/main.rs')
        self.assertNotEqual(self.run_check('--write').returncode, 0)
        path.unlink()
        (path.parent / '.env').write_text('SYNTHETIC_ONLY=1\n')
        self.assertNotEqual(self.run_check('--write').returncode, 0)

    def test_refresh_is_deterministic_and_checksums_verify(self):
        self.assertEqual(self.run_check('--write').returncode, 0)
        before = (self.store / 'SHA256SUMS').read_bytes()
        self.assertEqual(self.run_check('--write').returncode, 0)
        self.assertEqual(before, (self.store / 'SHA256SUMS').read_bytes())
        result = subprocess.run(['sha256sum', '--strict', '-c', 'SHA256SUMS'],
                                cwd=self.store, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
