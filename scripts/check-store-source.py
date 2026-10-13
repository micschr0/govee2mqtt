#!/usr/bin/env python3
"""Coherence check for the published HA store mirror (EXP-CICD-01).

Verifies that SOURCE.json carries a well-formed baseline sha and content_id
and that SOURCE_TAG (the published version string) ends in the content_id
prefix — i.e. the tag actually belongs to this store snapshot. Byte integrity
itself is proven by `sha256sum -c SHA256SUMS` in the same CI job.
"""

import json
import re
import sys
from pathlib import Path


def main() -> int:
    store = Path(__file__).resolve().parent.parent / "govee2mqtt_security_local"

    try:
        src = json.loads((store / "SOURCE.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: SOURCE.json unreadable: {exc}")
        return 1

    baseline = src.get("baseline", "")
    content_id = src.get("content_id", "")
    if not re.fullmatch(r"[0-9a-f]{40}", baseline):
        print(f"FAIL: SOURCE.json baseline is not a 40-hex sha: {baseline!r}")
        return 1
    if not re.fullmatch(r"[0-9a-f]{64}", content_id):
        print(f"FAIL: SOURCE.json content_id is not a 64-hex sha: {content_id!r}")
        return 1

    try:
        tag = (store / "SOURCE_TAG").read_text().strip()
    except OSError as exc:
        print(f"FAIL: SOURCE_TAG unreadable: {exc}")
        return 1

    # The package version (leading digits) may evolve freely; the tag must
    # carry this snapshot's content_id prefix.
    if not tag.endswith(content_id[:12]):
        print(
            f"FAIL: SOURCE_TAG {tag!r} does not end in content_id prefix "
            f"{content_id[:12]!r}"
        )
        return 1

    print(f"store source ok: baseline={baseline[:12]} tag={tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
