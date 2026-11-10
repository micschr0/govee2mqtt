# H60C1 owner acceptance kit

Preparation for [#10](https://github.com/micschr0/govee2mqtt/issues/10), using
[#3's inventory and protocol](../H60C1-LOCAL-ZONES.md). Research remains
**inconclusive**. No H60C1 command bytes, owner-supervised window or physical
observations have been supplied. This is portable tooling and a blank handoff,
not an execution report. Mandatory hardware checks remain pending.

## Offline preparation

The public interfaces under test are the Python CLI's `plan` and `sanitize`
stdin/stdout modes. Tests use deliberately synthetic bytes, never another
model's commands. Python 3 standard library only; neither mode opens sockets,
discovers lamps, changes networks or runs the application.

```sh
python3 -m unittest discover -s scripts -p test_h60c1_acceptance.py -v
```

Store all actual manifests, plans, pcaps, decoded packets and execution reports
outside Git, with owner-only permissions (`umask 077`). Set `PRIVATE_DIR` to an
existing owner-approved private directory before using the commands below.
Never use a public CI artifact store. Review sanitized output manually before
sharing; this kit does not authorize publishing captures.

### Capture-backed command manifest

Workers can validate future owner-supplied H60C1 captures offline. Create
`$PRIVATE_DIR/manifest.json` with this schema; the empty fields deliberately
fail validation. There is no sendable example without H60C1 evidence.

```json
{
  "model": "H60C1",
  "firmware": "1.01.27",
  "steps": [{
    "id": "trial-1-bottom-temperature",
    "source": "",
    "purpose": "",
    "unchanged": "",
    "frames": [{"data_hex": "", "captured_base64": ""}]
  }]
}
```

For each step, fill `source` with a private capture ID/time and the actual model,
firmware and action provenance. `purpose` specifies zone/value, `unchanged`
names the other zone and curved state. `data_hex` is 1–19 unpadded bytes as
space-separated two-digit hex without `0x`. `captured_base64` is the complete
20-byte frame independently obtained from that same H60C1 capture. Frames in
one step form one ordered `ptReal` command array; keep original transaction
boundaries. Use distinct step IDs. Do not combine unrelated captures or guess
unknown bytes. Stop for a protocol revision if the actual firmware differs.

```sh
umask 077
python3 scripts/h60c1-acceptance.py plan \
  < "$PRIVATE_DIR/manifest.json" > "$PRIVATE_DIR/plan.json"
```

The validator pads to 19 bytes, adds XOR checksum, compares all 20 captured
bytes, then base64 encodes each frame. It rejects oversize/empty frames,
duplicate step IDs, other models/firmware and mismatched captures. The format
matches `src/ble.rs::finish` and `src/lan_api.rs::Request::PtReal`.

A valid encoding proves **representation only**. It cannot prove capture
provenance, identify opcodes/LEDs, or detect reset/authentication writes. Owner
and investigator must review every frame before execution; never brute-force
or replay pairing, authentication or reset commands. No initialization is
included unless evidenced by H60C1 captures. No H60B0/H60B2 substitutions.

Each planned step contains exact `intent` JSON for UDP 4003 and a separate
`devStatus` query, with five-second reply timeout on UDP 4002, five-second
observation wait, at least one second between transactions and zero retries.
These are conservative protocol intervals, not measured firmware limits.
A future owner-reviewed sender must preserve frame order/boundaries and log
actual timestamps, errors, timeouts and replies. **This kit does not send.**
Do not pipe a plan into a shell or run the general LAN CLI casually: it starts
multicast discovery. An agreed supervised network window is required first.

### Capture and redaction tooling for the future window

Only after agreeing interface, fixture addresses, isolated window and rollback,
the owner may capture the designated fixture traffic using #3's `tcpdump`
filter. Raw captures preserve unknown fields for private investigation.
The following is an offline conversion of an already acquired pcap; it does
not start capture. `tshark` is an optional owner-side decoder, not a Python
dependency. The [official tshark manual](https://www.wireshark.org/docs/man-pages/tshark.html)
documents offline `-r`, display filtering with `-Y`, and tab-separated `-T fields`
with repeated `-e`. Its filter excludes unrelated UDP traffic; confirm the pcap itself
was restricted to the fixture. The sanitizer consumes four tab-separated
fields: relative seconds, UDP source port, destination port and hex payload.

```sh
umask 077
tshark -r "$PRIVATE_DIR/lan.pcap" \
  -Y 'udp.dstport == 4001 || udp.dstport == 4002 || udp.dstport == 4003' \
  -T fields -e frame.time_relative -e udp.srcport -e udp.dstport -e udp.payload \
  > "$PRIVATE_DIR/udp.tsv"
python3 scripts/h60c1-acceptance.py sanitize \
  < "$PRIVATE_DIR/udp.tsv" > "$PRIVATE_DIR/summary.json"
```

Do not use an output file after a nonzero exit. The sanitizer emits record
numbers/timing, payload lengths, a fixed command vocabulary, and only bounded
numeric whole-device `devStatus` fields. It drops command bodies, identifiers,
tokens, unknown fields and unparsed payload bytes. Invalid JSON remains an
`unparsed` event; malformed TSV is rejected without echoing input. Empty input
is rejected, never interpreted as successful capture. Preserve full raw data
privately; the allowlist intentionally omits unknown zone fields.

Destination port 4002 labels **device report**, 4001/4003 **sent intent**. This
is a capture-direction convention, not sender authentication or proof of
delivery. Neither is a physical result. Whole-device status cannot verify
zones. Missing replies are timeouts, not proof of unsupported capabilities;
record query windows/timeouts separately. Correlate record numbers and actual
times with the private raw capture and manifest IDs. Hash original and redacted
artifacts separately in the private evidence index. Review images/metadata and
isolation evidence separately; UDP filtering cannot prove WAN isolation.

## Numbered owner handoff

Use the [copyable report](manual-acceptance.md#copyable-report) privately. Record
full tested source SHA, clean/dirty tree, binary/version/digest, controller
OS/version, app version, lamp label/firmware including BLE/Wi-Fi if exposed,
LAN setting, operator, UTC window, stop signal, manifest hash, evidence IDs and
original settings. Do not fill observed results from expected values.

| Step | Owner action and expected observation | Actual result / evidence |
| --- | --- | --- |
| 1 | Agree window and safe rollback; confirm H60C1/1.01.27 and LAN enabled. Preserve original settings, stop competing controllers and automations. | pending |
| 2 | Acquire missing H60C1 app/BLE captures one setting at a time as specified in #3; workers map and validate the manifest, owner reviews it. Acquisition is discovery, not offline acceptance. | pending |
| 3 | Verify WAN isolation for lamp AND controller, IPv4 AND IPv6, with sanitized firewall rules/counters and direct-IP egress checks. Disconnect phone/BLE/cellular paths. DNS failure alone is insufficient. | pending |
| 4 | With evidenced initialization only, hold master brightness fixed and curved off. Set dedicated bottom white 3000 K/60% and side red/40%. Observe both simultaneously. Explain dedicated LED identity through capture mapping and safe non-invasive observation/measurement; unresolved identity is inconclusive. | pending |
| 5 | Change only bottom to 5000 K, then only bottom brightness to 30%; after EACH write observe both zones and curved state. Side must remain red/40%. Never resend the unchanged zone to conceal overwrites. | pending |
| 6 | Change only side to blue, then only side brightness to 20%; after EACH write observe both zones and curved state. Bottom must remain dedicated white 5000 K/30%. | pending |
| 7 | Reverse setup order: side red/40% first, then bottom 3000 K/60%. Repeat steps 5–6; record both zones after every write. | pending |
| 8 | Still offline, safely power-cycle lamp once. Record persistence BEFORE writes, discovery/status failures and required initialization; repeat 4–7. Avoid rapid cycling/reset sequences. | pending |
| 9 | Still offline, restart controller with last-sent state cleared and retained replay disabled. Observe BEFORE writes; repeat 4–7. Restart BOTH and repeat again. Reconfirm isolation for EACH trial; record initialization/recovery requirements. | pending |
| 10 | Stop capture, restore original settings/connectivity via agreed rollback; confirm normal operation. Explicitly confirm observations and safe restoration in #10, with redacted evidence references. | pending |

After every command, record actual send outcome, reply/query/timeout separately
from last-sent intent, then owner timestamped physical effects on bottom, side
and curved. Stop on flicker, unexpected mode, loss of control or owner request;
record failures and use the agreed recovery without silently retrying.

## Capability matrix to complete with the owner

Link each row to #3's inventory and private evidence IDs: manifest/command,
actual readback (or unavailable), owner observations and confirmation. Initial
`inconclusive — unexecuted` is a pending investigation, not an observed finding.

| Capability | Current disposition | Owner confirmation / evidence |
| --- | --- | --- |
| Simultaneous dedicated bottom white + side RGB; emitter identity | inconclusive — unexecuted | pending |
| Bottom temperature independent of side | inconclusive — unexecuted | pending |
| Bottom brightness independent of side | inconclusive — unexecuted | pending |
| Side RGB independent of bottom white | inconclusive — unexecuted | pending |
| Side brightness independent of bottom white | inconclusive — unexecuted | pending |
| Reverse setup order without overwrites; curved unchanged | inconclusive — unexecuted | pending |
| Offline lamp/controller/both restarts; persistence/initialization | inconclusive — unexecuted | pending |
| Zone readback and its limits | inconclusive — unexecuted; client has whole-device fields only | pending |
| Safe restoration | inconclusive — unexecuted | pending |

After execution, use **verified**, **unsupported in the observed trial**, or
**inconclusive**, with actual effects/limitations. An owner-observed failed or
inconclusive investigation can finish #10 when every mandatory action was
executed and preserved; unexecuted steps cannot. Keep support acceptance and
implementation separate. No feature/profile follows without supporting H60C1
evidence. Do not modify historical results: append a new report and assess its
applicability to each new source/artifact/firmware version.
