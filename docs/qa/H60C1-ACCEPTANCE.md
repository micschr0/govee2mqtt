# H60C1 owner acceptance kit

Preparation for [#10](https://github.com/micschr0/govee2mqtt/issues/10), using
[#3's inventory and protocol](../H60C1-LOCAL-ZONES.md). Research remains
**inconclusive**. No H60C1 command bytes, owner-supervised window or physical
observations have been supplied. This is portable tooling and a blank handoff,
not an execution report. Mandatory hardware checks remain pending.

## What the evidence supports

- [Govee's LAN guide][govee-lan] documents whole-device `colorwc`, `brightness`
  and `devStatus`. None identifies a physical zone. The H60C1's
  [product page][govee-product] describes independent side, curved and bottom
  zones, but does not document LAN commands for them.
- [`govee-local-api` registers three segments for H60C1][library-profile] and
  has a [generic segment RGB encoder][library-encoder]. The [device report][library-issue]
  did not verify that encoder or the zone mapping on hardware. H60B0 commands
  in #3 are not H60C1 evidence.
- The [H60C1 LAN temperature report][lan-temperature] describes a dark lamp
  despite an `on` status after a whole-device 2200 K command. The
  [2700–6500 K discovery correction on `main`][temperature-fix] is separate
  and unchanged by this kit. Neither proves dedicated white or side RGB.

**Next evidence to collect:** in an agreed window, capture one H60C1 zone-only
change twice and note the exact settings, times and visible effects on all
zones. Prefer LAN if the controller can already make that change. A
whole-device `colorwc` packet is a useful capture sanity check, not a zone
command. If the controller cannot make a zone-only change, use the #3 app/BLE
acquisition path as discovery evidence; that is not a LAN test.

## Offline preparation

The Python CLI has three modes: `plan` validates a manifest and builds a private
plan, `sanitize` summarizes a capture, and `verify` compares a manifest against
a separate LAN capture. Tests use synthetic bytes, never another model's
commands. The CLI uses only the Python 3 standard library and does not open
sockets, discover lamps, change networks or run the application.

```sh
python3 -m unittest discover -s tests -p test_h60c1_acceptance.py -v
```

Offline verification on 2026-11-22: the documented `tshark` conversion and
all three CLI modes passed against a synthetic
pcap with two transactions, an unpaired status report and unrelated traffic.
These results verify the tooling, not H60C1 support.

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
matches the bridge's `ble.rs::finish` and `lan_api.rs::Request::PtReal`.
If the H60C1 capture uses a different command format, preserve it privately
for analysis instead of forcing it into this schema.

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
This converts an existing pcap without accessing the network. Set
`CONTROLLER_IP` and `LAMP_IP` in the private shell to the two fixture IPv4
addresses. The filter keeps only the expected endpoints and directions for
control and status. Preserve discovery and isolation evidence separately.
`tshark` is an optional decoder, not a Python dependency; see the
[official manual][tshark]. Keep intermediate files private.

```sh
umask 077
tshark -r "$PRIVATE_DIR/lan.pcap" \
  -Y "(ip.src == $CONTROLLER_IP && ip.dst == $LAMP_IP && udp.dstport == 4003) || (ip.src == $LAMP_IP && ip.dst == $CONTROLLER_IP && udp.dstport == 4002)" \
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

### Verify the recorded LAN sequence

Use a single fixture capture window containing the manifest's full sequence of
`ptReal` writes. Supply the entire window in capture order: do not remove extra
writes, reorder rows or join separate UDP transactions. Supply the original
manifest, not the generated plan.

```sh
umask 077
python3 scripts/h60c1-acceptance.py verify "$PRIVATE_DIR/udp.tsv" \
  < "$PRIVATE_DIR/manifest.json" > "$PRIVATE_DIR/verification.json"
```

On success, `verify` confirms that every outgoing `ptReal` datagram has the
expected ordered frame array (including padding and checksum), with none missing
or extra. `manifest_step` is the 1-based step number; `record` is the TSV row
number, not the pcap frame number. Undecodable outgoing control packets block
verification. Other decodable commands are visible in the allowlisted summary
but are not checked against the manifest. The tool checks the
manifest's model and firmware fields, not the capture's provenance: verify the
lamp's actual model, firmware, endpoint and action-to-packet link separately.

`device_readback: observed-unpaired` means valid whole-device status fields were
observed, not that a reply was paired with a write or that the device accepted
it. `not-observed` means no such fields were seen in the supplied window; it
does not prove a timeout or lack of support. Readback and physical effects stay
separate; `physical_result` is always `pending`.

Destination port 4002 labels **device report**, 4001/4003 **sent intent**. This
is a capture-direction convention, not sender authentication or proof of
delivery. Neither is a physical result. Whole-device status cannot verify
zones. Record query windows and measured timeouts separately; do not infer them
from capture silence. Correlate record numbers and actual
times with the private raw capture and manifest IDs. Hash original and redacted
artifacts separately in the private evidence index. Review images/metadata and
isolation evidence separately; UDP filtering cannot prove WAN isolation.

## Numbered owner handoff

Use the [copyable report](manual-acceptance.md#copyable-report) privately. Record
full tested source SHA, clean/dirty tree, binary/version/digest, controller
OS/version, app version, lamp label/firmware including BLE/Wi-Fi if exposed,
LAN setting, operator, UTC window, stop signal, manifest hash, evidence IDs and
original settings. Do not fill observed results from expected values.
Do not run acquisition or live verification without an agreed owner-supervised
window. Physical acceptance runs after a separately approved Store release from
`main`; record the installed version and exact source SHA. This kit does not
build or publish a release or expose zone controls.

| Step | Owner action and expected observation | Actual result / evidence |
| --- | --- | --- |
| 1 | Agree window and safe rollback; confirm H60C1/1.01.27 and LAN enabled. Preserve original settings, stop competing controllers and automations. | pending |
| 2 | Capture one H60C1 zone action at a time across two values; prefer direct LAN if available, otherwise record app/BLE as in #3. Workers map and validate commands; the owner and investigator review each frame before any replay. Acquisition is not offline acceptance. | pending |
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
actual readback (or unavailable), owner observations and confirmation. Keep
unexecuted checks pending; reserve `inconclusive` for an observed result.

| Capability | Evidence so far | Owner confirmation / evidence IDs |
| --- | --- | --- |
| Simultaneous dedicated bottom white + side RGB; emitter identity | Manufacturer lists zones; no H60C1 LAN or emitter observation | Pending, step 4 |
| Bottom temperature independent of side | Whole-device temperature documented; no H60C1 zone packet | Pending, step 5 |
| Bottom brightness independent of side | Whole-device brightness documented; no H60C1 zone packet | Pending, step 5 |
| Side RGB independent of bottom white | Generic library encoding is a lead only; no matching H60C1 capture | Pending, step 6 |
| Side brightness independent of bottom white | Whole-device brightness documented; no H60C1 zone packet | Pending, step 6 |
| Reverse setup order without overwrites; curved unchanged | No H60C1 trial | Pending, step 7 |
| Offline lamp/controller/both restarts; persistence/initialization | No H60C1 trial | Pending, steps 8–9 |
| Zone readback and its limits | Documented status and client fields are whole-device only; no H60C1 zone reply captured | Pending, steps 4–9 |
| Safe restoration | No H60C1 trial | Pending, step 10 |

After execution, use **verified**, **unsupported in the observed trial**, or
**inconclusive**, with actual effects/limitations. An owner-observed failed or
inconclusive investigation can finish #10 when every mandatory action was
executed and preserved; unexecuted steps cannot. Keep support acceptance and
implementation separate. No feature/profile follows without supporting H60C1
evidence. Do not modify historical results: append a new report and assess its
applicability to each new source/artifact/firmware version.

[govee-lan]: https://app-h5.govee.com/user-manual/wlan-guide
[govee-product]: https://eu.govee.com/products/govee-pendant-light?variant=51797089779896
[library-profile]: https://github.com/Galorhallen/govee-local-api/blob/0c228a715b07c111b3b636404c0398f245471160/src/govee_local_api/light_capabilities.py#L161
[library-encoder]: https://github.com/Galorhallen/govee-local-api/blob/0c228a715b07c111b3b636404c0398f245471160/src/govee_local_api/message.py#L125-L134
[library-issue]: https://github.com/Galorhallen/govee-local-api/issues/232
[lan-temperature]: https://github.com/wez/govee2mqtt/issues/742
[temperature-fix]: https://github.com/micschr0/govee2mqtt/commit/6fd813a12650763c78eb4d1f9526cda3527c3300
[tshark]: https://www.wireshark.org/docs/man-pages/tshark.html
