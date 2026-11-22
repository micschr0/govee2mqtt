#!/usr/bin/env python3
"""Offline H60C1 manifest validation and allowlisted capture summaries. No I/O to devices."""

import argparse
import base64
import binascii
import functools
import json
import math
import operator
import re
import sys


def require(condition):
    if not condition:
        raise ValueError("invalid input")


def plan(value):
    require(value["model"] == "H60C1" and value["firmware"] == "1.01.27")
    require(isinstance(value["steps"], list) and 0 < len(value["steps"]) <= 100)
    steps, ids = [], set()
    for step in value["steps"]:
        require(isinstance(step["id"], str) and re.fullmatch(r"[a-zA-Z0-9_-]{1,40}", step["id"]))
        require(step["id"] not in ids)
        ids.add(step["id"])
        for field in ("source", "purpose", "unchanged"):
            require(isinstance(step[field], str) and 0 < len(step[field]) <= 500)
        require(isinstance(step["frames"], list) and 0 < len(step["frames"]) <= 20)
        commands = []
        for frame in step["frames"]:
            require(isinstance(frame["data_hex"], str))
            require(re.fullmatch(r"[0-9a-fA-F]{2}(?: [0-9a-fA-F]{2}){0,18}", frame["data_hex"]))
            data = bytes.fromhex(frame["data_hex"])
            padded = data.ljust(19, b"\0") + bytes([functools.reduce(operator.xor, data, 0)])
            captured = base64.b64decode(frame["captured_base64"], validate=True)
            require(captured == padded)
            commands.append(base64.b64encode(padded).decode("ascii"))
        steps.append({
            "id": step["id"], "source": step["source"], "purpose": step["purpose"],
            "expected_unchanged": step["unchanged"],
            "intent": {"msg": {"cmd": "ptReal", "data": {"command": commands}}},
            "readback_query": {"msg": {"cmd": "devStatus", "data": {}}},
            "readback_timeout_s": 5, "observation_wait_s": 5,
            "minimum_transaction_spacing_s": 1, "retries": 0,
            "device_report": "pending", "physical_result": "pending",
        })
    return {"model": "H60C1", "firmware": "1.01.27", "executed": False, "steps": steps}


def sanitize(lines):
    events = []
    for index, line in enumerate(lines, 1):
        if not line.strip():
            continue
        elapsed, source_port, destination_port, payload = line.rstrip("\n").split("\t")
        elapsed = float(elapsed)
        require(math.isfinite(elapsed) and elapsed >= 0)
        require(0 < int(source_port) <= 65535)
        require(destination_port in ("4001", "4002", "4003"))
        raw = bytes.fromhex(payload.replace(":", ""))
        require(len(raw) <= 65507)
        event = {"record": index, "elapsed_s": elapsed,
                 "evidence_type": "device-report" if destination_port == "4002" else "sent-intent",
                 "command": "unparsed", "payload_bytes": len(raw)}
        try:
            msg = json.loads(raw)["msg"]
            cmd, data = msg["cmd"], msg.get("data", {})
            if cmd in ("scan", "devStatus", "ptReal", "turn", "brightness", "colorwc"):
                event["command"] = cmd
            else:
                event["command"] = "other"
            # Only bounded numeric whole-device status can leave the private capture.
            if destination_port == "4002" and cmd == "devStatus" and isinstance(data, dict):
                state = {}
                for key, maximum in (("onOff", 1), ("brightness", 100), ("colorTemInKelvin", 10000)):
                    number = data.get(key)
                    if type(number) is int and 0 <= number <= maximum:
                        state[key] = number
                color = data.get("color")
                if isinstance(color, dict) and all(type(color.get(c)) is int and 0 <= color[c] <= 255 for c in "rgb"):
                    state["color"] = {c: color[c] for c in "rgb"}
                event["whole_device_state"] = state
        except (ValueError, KeyError, TypeError, AttributeError, UnicodeDecodeError):
            pass  # Keep the record/time, never copy undecoded payload bytes.
        events.append(event)
    require(events)
    return events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["plan", "sanitize"])
    args = parser.parse_args()
    try:
        if args.mode == "plan":
            result = plan(json.load(sys.stdin))
        else:
            result = sanitize(sys.stdin)
    except (ValueError, KeyError, TypeError, AttributeError, binascii.Error):
        # Never echo raw input or exception values: either may contain credentials.
        print("Rejected input; inspect the private source against the documented schema.", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
