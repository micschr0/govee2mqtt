"""Exercise the comparison CLI using disposable baseline/upgrade observations."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/addon"
CHECK = ROOT / "scripts/verify-addon-fixtures.py"


class FixtureComparison(unittest.TestCase):
    def test_upgrade_preserves_options_and_markers(self):
        with tempfile.TemporaryDirectory() as temporary:
            observed = Path(temporary) / "observed"
            shutil.copytree(FIXTURE, observed)
            command = [sys.executable, str(CHECK), str(observed)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PASS", result.stdout)

            options = observed / "options.json"
            original = options.read_text()
            changed = json.loads(original)
            del changed["mqtt_port"]
            options.write_text(json.dumps(changed))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("mqtt_port", result.stderr)
            self.assertNotIn("1883", result.stderr)  # Never print option values.
            options.write_text(original)

            marker = observed / "data/persistence-marker.txt"
            marker.unlink()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("data/persistence-marker.txt", result.stderr)

    def test_invalid_observations_fail_without_exposing_values(self):
        for defect in ("type", "value", "http", "json", "config-marker", "changed-marker"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temporary:
                observed = Path(temporary) / "observed"
                shutil.copytree(FIXTURE, observed)
                options = json.loads((observed / "options.json").read_text())
                if defect == "type":
                    options["broadcast_all"] = 0
                if defect == "value":
                    options["mqtt_password"] = "DO-NOT-PRINT-THIS"
                if defect == "http":
                    options["http_bind"] = "0.0.0.0:8056"
                (observed / "options.json").write_text(json.dumps(options))
                if defect == "json":
                    (observed / "options.json").write_text('{"DO-NOT-PRINT-THIS":')
                if defect == "config-marker":
                    (observed / "addon_config/persistence-marker.txt").unlink()
                if defect == "changed-marker":
                    (observed / "data/persistence-marker.txt").write_text("changed")
                result = subprocess.run([sys.executable, str(CHECK), str(observed)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn("FAIL", result.stderr)
                self.assertNotIn("DO-NOT-PRINT-THIS", result.stderr)

    def test_live_options_can_be_compared_without_using_fake_broker_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            baseline = Path(temporary) / "before"
            observed = Path(temporary) / "after"
            shutil.copytree(FIXTURE, baseline)
            options = json.loads((baseline / "options.json").read_text())
            options["mqtt_host"] = "isolated-broker.invalid"
            (baseline / "options.json").write_text(json.dumps(options))
            shutil.copytree(baseline, observed)
            command = [sys.executable, str(CHECK), str(observed), "--baseline", str(baseline)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for directory in (baseline, observed):
                (directory / "options.json").write_text("{}")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("baseline", result.stderr)


if __name__ == "__main__":
    unittest.main()
