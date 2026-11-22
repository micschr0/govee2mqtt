"""Verify release ordering in a disposable tree with Git replaced by a fixture."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STORE = "govee2mqtt_security_local"
GIT = """#!/bin/sh
printf '%s\\n' "$*" >> "$TRACE"
case "$1" in
    check-ref-format|status|add|tag) exit 0 ;;
    show-ref) exit 1 ;;
    cliff) echo 'Synthetic release notes' > govee2mqtt_security_local/CHANGELOG.md ;;
    commit) [ "$FAIL_COMMIT" = false ] ;;
    *) exit 2 ;;
esac
"""


class ReleaseScriptTest(unittest.TestCase):
    def release_fixture(self, fail_commit=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / STORE, root / STORE,
                            ignore=shutil.ignore_patterns("target", ".env*", "__pycache__"))
            (root / "scripts").mkdir()
            for name in ("apply-tag.sh", "check-store-source.py", "tag-release.sh"):
                shutil.copy2(ROOT / "scripts" / name, root / "scripts" / name)
            shim = root / "git"
            shim.write_text(GIT)
            shim.chmod(0o700)
            trace = root / "git-trace"
            result = subprocess.run(
                ["sh", "scripts/tag-release.sh"], cwd=root,
                env={"PATH": str(root) + os.pathsep + os.environ["PATH"], "TAG_NAME": "1.2.3",
                     "TRACE": str(trace), "FAIL_COMMIT": str(fail_commit).lower()},
                capture_output=True, text=True, timeout=15,
            )
            calls = trace.read_text().splitlines()
            version = (root / STORE / "SOURCE_TAG").read_text().strip()
            metadata = json.loads((root / STORE / "SOURCE.json").read_text())
            return result, calls, version, metadata["version"]

    def test_tags_after_committing_final_version_metadata(self):
        result, calls, version, metadata = self.release_fixture()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((version, metadata), ("1.2.3", "1.2.3"))
        self.assertEqual(calls[-2:], ["commit -m Tag 1.2.3", "tag -- 1.2.3"])

    def test_commit_failure_does_not_tag_anything(self):
        result, calls, _, _ = self.release_fixture(fail_commit=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(call.startswith("tag ") for call in calls))
