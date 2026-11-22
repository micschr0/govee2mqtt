"""Synthetic offline CLI checks; none of these bytes are lamp commands."""

import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h60c1-acceptance.py"


def run_cli(mode, value, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), mode, *args], input=value, text=True,
        capture_output=True, check=False,
    )


def manifest():
    # Arbitrary synthetic data with independently worked XOR 01 ^ 02 = 03.
    frame = bytes([1, 2] + [0] * 17 + [3])
    return {"model": "H60C1", "firmware": "1.01.27", "steps": [{
        "id": "trial-1", "source": "synthetic-only", "purpose": "encoding test",
        "unchanged": "no physical observation", "frames": [{
            "data_hex": "01 02", "captured_base64": base64.b64encode(frame).decode(),
        }],
    }]}


def verify_capture(value, rows):
    with tempfile.TemporaryDirectory() as directory:
        capture = Path(directory) / "capture.tsv"
        capture.write_text("".join(rows), encoding="ascii")
        return run_cli("verify", json.dumps(value), str(capture))


def udp_row(time, port, cmd, data):
    payload = json.dumps({"msg": {"cmd": cmd, "data": data}}).encode().hex()
    return f"{time}\t4002\t{port}\t{payload}\n"


FRAME_A = "AQIAAAAAAAAAAAAAAAAAAAAAAAM="
FRAME_B = "AAAAAAAAAAAAAAAAAAAAAAAAAAA="


class AcceptanceCLI(unittest.TestCase):
    def test_plan_preserves_frame_order_and_queries_actual_status(self):
        value = manifest()
        value["steps"][0]["frames"].append({
            "data_hex": "00", "captured_base64": "AAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        })
        result = run_cli("plan", json.dumps(value))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertFalse(plan["executed"])
        step = plan["steps"][0]
        self.assertEqual(step["intent"]["msg"]["cmd"], "ptReal")
        self.assertEqual(step["intent"]["msg"]["data"]["command"], [
            "AQIAAAAAAAAAAAAAAAAAAAAAAAM=", "AAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        ])
        self.assertEqual(step["readback_query"], {"msg": {"cmd": "devStatus", "data": {}}})
        self.assertEqual(step["physical_result"], "pending")

    def test_rejects_unmatched_captures_and_invalid_manifests_without_echo(self):
        for change in ("base64", "checksum", "length", "empty", "frames", "model", "firmware", "duplicate"):
            value = manifest()
            if change == "base64":
                value["steps"][0]["frames"][0]["captured_base64"] = "secret-token"
            elif change == "checksum":
                value["steps"][0]["frames"][0]["captured_base64"] = base64.b64encode(bytes([1, 2] + [0] * 18)).decode()
            elif change == "length":
                value["steps"][0]["frames"][0]["data_hex"] = " ".join(["01"] * 20)
            elif change == "empty":
                value["steps"] = []
            elif change == "frames":
                value["steps"][0]["frames"] = []
            elif change == "firmware":
                value["firmware"] = "1.01.28"
            elif change == "model":
                value["model"] = "H60B0"
            else:
                value["steps"] *= 2
            with self.subTest(change=change):
                result = run_cli("plan", json.dumps(value))
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("secret-token", result.stderr)

    def test_sanitizer_keeps_readback_separate_and_removes_unknown_data(self):
        packet = {"msg": {"cmd": "devStatus", "data": {
            "brightness": 60, "onOff": 1, "color": {"r": 255, "g": 0, "b": 0},
            "colorTemInKelvin": 3000, "token": "secret-token",
            "unknown": {"ip": "192.0.2.1"},
        }}, "device": "private-device"}
        sent = {"msg": {"cmd": "ptReal", "data": {"command": ["secret-token"]}}}
        def row(port, payload):
            return "1.25\t4003\t" + str(port) + "\t" + json.dumps(payload).encode().hex() + "\n"
        result = run_cli("sanitize", row(4002, packet) + row(4003, sent))
        self.assertEqual(result.returncode, 0, result.stderr)
        events = json.loads(result.stdout)
        self.assertEqual(events[0]["evidence_type"], "device-report")
        self.assertEqual(events[0]["whole_device_state"]["brightness"], 60)
        self.assertEqual(events[1]["evidence_type"], "sent-intent")
        self.assertNotIn("whole_device_state", events[1])
        for secret in ("secret-token", "private-device", "192.0.2.1", "unknown"):
            self.assertNotIn(secret, result.stdout)
        self.assertNotIn("physical_result", result.stdout)

    def test_sanitizer_keeps_unparsed_events_and_never_exports_invalid_state(self):
        packet = {"msg": {"cmd": "devStatus", "data": {
            "brightness": 101, "onOff": True, "colorTemInKelvin": "secret-token",
            "color": {"r": -1, "g": 0, "b": 0},
        }}}
        row = "2\t4003\t4002\t" + json.dumps(packet).encode().hex() + "\n"
        result = run_cli("sanitize", row + "3\t4003\t4002\t7365637265742d746f6b656e\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        events = json.loads(result.stdout)
        self.assertEqual(events[0]["whole_device_state"], {})
        self.assertEqual(events[1]["command"], "unparsed")
        self.assertNotIn("secret-token", result.stdout + result.stderr)

    def test_sanitizer_rejects_malformed_rows_without_partial_output(self):
        for value in ("", "secret-token", "nan\t4003\t4002\t00\n", "0\t4003\t1234\t00\n"):
            with self.subTest(value=value):
                result = run_cli("sanitize", value)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("secret-token", result.stderr)

    def test_verify_keeps_matched_writes_and_unpaired_readback_separate(self):
        result = verify_capture(manifest(), [
            udp_row(1, 4003, "ptReal", {"command": [FRAME_A]}),
            udp_row(2, 4003, "devStatus", {}),
            udp_row(3, 4002, "devStatus", {"brightness": 42, "token": "private-token"}),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["events"][0]["manifest_step"], 1)
        self.assertEqual(report["events"][1]["evidence_type"], "sent-intent")
        self.assertEqual(report["events"][2]["whole_device_state"], {"brightness": 42})
        self.assertNotIn("manifest_step", report["events"][2])
        self.assertEqual(report["device_readback"], "observed-unpaired")
        self.assertEqual(report["physical_result"], "pending")
        for private in (FRAME_A, "private-token", "synthetic-only", "trial-1"):
            self.assertNotIn(private, result.stdout)

    def test_verify_does_not_infer_readback_from_intent_or_invalid_state(self):
        result = verify_capture(manifest(), [
            udp_row(1, 4003, "ptReal", {"command": [FRAME_A]}),
            udp_row(2, 4003, "devStatus", {"brightness": 42}),
            udp_row(3, 4002, "devStatus", {"brightness": -1}),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["device_readback"], "not-observed")
        self.assertNotIn("whole_device_state", report["events"][1])

    def test_verify_requires_exact_frame_bytes_order_and_transaction_boundaries(self):
        value = manifest()
        frame = {"data_hex": "00", "captured_base64": FRAME_B}
        value["steps"][0]["frames"].append(frame)
        value["steps"].append({**value["steps"][0], "id": "trial-2", "frames": [frame]})

        def observed(*transactions):
            return [udp_row(i, 4003, "ptReal", {"command": frames})
                    for i, frames in enumerate(transactions, 1)]

        result = verify_capture(value, observed([FRAME_A, FRAME_B], [FRAME_B]))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([e["manifest_step"] for e in json.loads(result.stdout)["events"]], [1, 2])
        for label, rows in {
            "changed-frames": observed([FRAME_A, FRAME_A], [FRAME_B]),
            "reordered-frames": observed([FRAME_B, FRAME_A], [FRAME_B]),
            "reordered-transactions": observed([FRAME_B], [FRAME_A, FRAME_B]),
            "different-boundaries": observed([FRAME_A], [FRAME_B, FRAME_B]),
            "extra-transaction": observed([FRAME_A, FRAME_B], [FRAME_B], [FRAME_B]),
            "missing-transaction": observed([FRAME_A, FRAME_B]),
            "invalid-timeline": observed([FRAME_A, FRAME_B], [FRAME_B])[::-1],
        }.items():
            with self.subTest(label=label):
                result = verify_capture(value, rows)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertNotIn(FRAME_A, result.stderr)

    def test_verify_rejects_nonmatching_model_and_missing_or_malformed_writes(self):
        good_write = udp_row(1, 4003, "ptReal", {"command": [FRAME_A]})
        for value, rows in (
            ({**manifest(), "model": "H60B0"}, [good_write]),
            ({**manifest(), "firmware": "1.01.28"}, [good_write]),
            (manifest(), [udp_row(1, 4002, "ptReal", {"command": [FRAME_A]})]),
            (manifest(), [udp_row(1, 4003, "ptReal", {"command": "private-token"})]),
        ):
            with self.subTest():
                result = verify_capture(value, rows)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("private-token", result.stderr)

    def test_verify_rejects_ambiguous_control_datagram(self):
        ambiguous = (f'{{"msg":{{"cmd":"ptReal","data":{{"command":["{FRAME_B}"],'
                     f'"command":["{FRAME_A}"]}}}}}}').encode().hex()
        result = verify_capture(manifest(), [f"1\t4002\t4003\t{ambiguous}\n"])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertNotIn(FRAME_A, result.stderr)

    def test_verify_does_not_ignore_an_undecodable_control_datagram(self):
        result = verify_capture(manifest(), [
            udp_row(1, 4003, "ptReal", {"command": [FRAME_A]}),
            "2\t4002\t4003\t7b\n",
        ])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_verify_rejects_non_json_numeric_constants(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                datagram = (f'{{"msg":{{"cmd":"ptReal","data":{{"command":["{FRAME_A}"],'
                            f'"unknown":{constant}}}}}}}').encode().hex()
                result = verify_capture(manifest(), [f"1\t4002\t4003\t{datagram}\n"])
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
