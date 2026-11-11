#!/usr/bin/env python3
"""Compare a disposable add-on observation with the repository fixture."""
import argparse
import json
from pathlib import Path
import sys

FIXTURE = Path(__file__).resolve().parents[1] / "tests/fixtures/addon"


def compare(observed, baseline):
    required = json.loads((FIXTURE / "options.json").read_text())
    expected = json.loads((baseline / "options.json").read_text())
    if not isinstance(expected, dict):
        raise ValueError("baseline options.json must contain an object")
    for key, value in required.items():
        if key not in expected or type(expected[key]) is not type(value):
            raise ValueError(f"baseline options.json: missing or invalid field {key}")
    actual = json.loads((observed / "options.json").read_text())
    if not isinstance(actual, dict):
        raise ValueError("options.json must contain an object")
    for key, value in expected.items():
        if key not in actual or type(actual[key]) is not type(value) or actual[key] != value:
            raise ValueError(f"options.json: missing or changed field {key}")
    if actual.get("http_bind"):
        raise ValueError("options.json: http_bind must remain disabled")
    for relative in ("data/persistence-marker.txt", "addon_config/persistence-marker.txt"):
        if (observed / relative).read_bytes() != (baseline / relative).read_bytes():
            raise ValueError(f"changed marker {relative}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observed", type=Path, help="directory with options.json, data/, addon_config/")
    parser.add_argument("--baseline", type=Path, default=FIXTURE, help="saved baseline (default: repository fixture)")
    args = parser.parse_args()
    try:
        compare(args.observed, args.baseline)
    except (OSError, ValueError) as exc:
        # Do not include JSON parser input or option values in diagnostics.
        message = str(exc) if not isinstance(exc, json.JSONDecodeError) else "invalid options.json"
        print(f"FAIL: {message}", file=sys.stderr)
        return 1
    print("PASS: required options and both persistent markers unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
