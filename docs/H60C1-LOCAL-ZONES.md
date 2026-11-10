# H60C1 local white and color zones

Research for [#3](https://github.com/micschr0/govee2mqtt/issues/3), reviewed
2026-11-11. Hardware execution and physical acceptance belong to
[#10](https://github.com/micschr0/govee2mqtt/issues/10).

## Conclusion: inconclusive

No H60C1 firmware 1.01.27 command capture or physical test result is available
in this investigation. Independent bottom dedicated-white and side RGB control
over LAN is neither established nor disproved. No implementation follow-up is
justified yet. Do not register speculative controls or copy another model's
commands into a production profile.

This report completes desk research, not hardware acceptance. #10 awaits the
owner's hardware/captures, an agreed supervised window and explicit physical
observations. No lamp discovery, control or network-isolation operation was
performed for this report.

## Evidence inventory

**Reported** means supplied by the owner in #3; **vendor** means product
literature; **code** means inspected source; **other model** means a project's
author reports support for different hardware; **hypothesis** means untested on
the target. None is a direct H60C1 physical observation by this worker.

| Function / fact | Evidence and class | H60C1 / firmware 1.01.27 status |
| --- | --- | --- |
| Model, firmware, connectivity | Owner reports H60C1, 1.01.27, LAN and Bluetooth in [#3](https://github.com/micschr0/govee2mqtt/issues/3). **Reported**; no capture supplied. | Reconfirm label and available firmware fields before execution. |
| Three sections, white hardware | [Govee][product] lists independent side, curved and bottom sections, RGB+RGBWW and 2700–6500 K white. **Vendor**, not firmware-specific. | Product capability; no LAN encoding or dedicated-bottom-white observation. |
| Bottom white temperature | H60B0 lower-temperature frame in [source][bridge-code]. **Other model**. | Unknown section selector, opcode and units; unverified on H60C1. |
| Bottom white brightness | H60B0 lower brightness is separate from master brightness. **Other model**, [source][bridge-code]. | Unknown range, dimming behavior and independence. |
| Side RGB | H60B0 side RGB/mask commands and H60B2 RGB segments. **Other models**, [bridge][bridge-code] / [fork][segments]. | Unknown zone mapping and command family. |
| Side brightness | H60B0 side brightness frame; H60B2 RGB scaling. **Other models**, [bridge][bridge-code] / [fork][segments]. | Unknown whether separate dimming or RGB scaling applies. |
| Simultaneous white + RGB, independent changes | Plausible from hardware and other-model LAN transport. **Hypothesis**. | Unknown overwrite, mode-switch and initialization behavior. |
| Offline operation and restart recovery | No H60C1 run supplied. **Unsupported claim**, not a proven device limitation. | Unknown internet dependency, persistence and reinitialization. |
| Zone state readback | Current [LAN status structure][local-lan] contains whole-device power, brightness, color and temperature. **Code**. | No zone readback in this client; firmware replies remain unexamined. |
| Current MQTT segment path | [mqtt_light_segment_command][local-hass] calls Platform API or errors, with no LAN fallback or white-temperature handling. **Code**. | This checkout does not implement the requested local zones. |
| Music, DreamView, DIY, app parity | Excluded by #3. | Unsupported by this investigation; no device-capability conclusion. |

### Other-model leads and their limits

The [H60B0 bridge README][bridge-readme] reports Bluetooth-derived commands
verified over LAN. H60C1 is absent from its built-in model table. Its source
pads frames to 20 bytes including XOR checksum, base64 encodes them in
`msg.cmd = ptReal`, `msg.data.command = [...]`, and sends them to UDP 4003.
These are research leads, **not H60C1 send instructions**:

| H60B0 operation | Unpadded data, hexadecimal |
| --- | --- |
| Enable section | `33 30 <section> 01` (side 02, lower 03) |
| Lower temperature | `33 05 2c 03 01 <kelvin high> <kelvin low>` |
| Lower brightness | `33 05 2c 03 02 <percent>` |
| Side RGB | `33 05 2c 02 01 <r> <g> <b> 00 00 <mask>` |
| Side brightness | `33 05 2c 02 02 <percent> <mask>` |

Its lower-white builder omits RGB bytes. Its README reports a two-active-section
limit and packet loss with short spacing. Neither behavior nor its selectors
and masks can be transferred to H60C1 without observation.

The [H60B2 fork][segments] documents `33 05 15 01` RGB/mask frames, brightness
through RGB scaling and session-local last-sent colors. This does not identify
dedicated-white control. Its expectation of compatibility with other devices
is a hypothesis. White-looking RGB cannot close #10.

The official [LAN guide][lan-guide] linked from this repository's client did
not expose readable protocol text to the research browser. No H60C1 zone
opcode claim is based on that page. The product page supplies hardware facts,
not a protocol contract. Searches for H60C1 with `ptReal`, LAN white control
and Bluetooth commands produced no additional H60C1 protocol evidence used here;
this bounded search does not establish that no such evidence exists.

## Reproducible protocol for #10

### Preparation and command discovery

1. Agree the owner-operated window, stop signal, safe power switch, network
   rollback and private storage location. Record controller OS, govee commit,
   app version, lamp label, firmware (including Wi-Fi/BLE versions if exposed)
   and LAN setting. Preserve current settings; never factory reset.
2. If captures are missing, the owner records app/Bluetooth traffic while
   changing one setting at a time: bottom white 3000 K then 5000 K, bottom
   60% then 30%, side red then blue, side 40% then 20%. Keep curved off.
   Timestamp physical effects for each action. Acquisition is discovery
   evidence, not offline LAN acceptance.
3. Workers map those H60C1 captures to labeled frames, distinguishing section
   enable, initialization, white temperature, per-zone brightness and RGB.
   Repeat app actions to distinguish constant fields from counters/checksums.
   Do not brute-force opcodes or replay pairing/authentication/reset writes.
4. Before replay, prepare an ordered, owner-reviewed manifest: step ID,
   source capture/time, model/firmware, intended zone/value, exact unpadded
   bytes, padded/checksummed bytes, base64, expected unchanged zone, timeout
   and recovery action. Validate length/checksum offline; compare encoded
   output to the captured frame. Include initialization only when evidenced.
   Unknown bytes or LED identity keep the corresponding result inconclusive.

There is intentionally no executable H60C1 payload here: its bytes have not
been captured. #10 must prepare and validate the manifest before replay.
Existing [LAN CLI][local-cli] `lan-control --ip <lamp-ip> command <bytes...>`
can send a captured single frame; [with_bytes][local-ble] pads/checksums input.
Supply at most 19 **unpadded data bytes**, with `0x` prefixes for hex, without
checksum; never supply a complete 20-byte frame to this command. Compare its
encoded output to the manifest. This CLI also starts default multicast
discovery; use it only on the agreed isolated fixture network. Multi-frame
transactions need a reviewed sender in #10 preserving order and boundaries.
#3 ships no sender or profile.

### Worker automation and capture plan

- Stop competing controllers and HA automations. After acquisition, disconnect
  the phone, including Bluetooth/cellular paths. Use a dedicated controller
  without cloud credentials. Fix master brightness and curved state; record
  every prerequisite write.
- The owner blocks WAN for **lamp and controller**, IPv4 and IPv6, while
  allowing needed local DHCP/ARP/NDP and UDP 4001/4003 to the lamp, 4002 back
  to the controller. Save sanitized firewall rules/counters and direct-IP
  egress checks; DNS failure alone is insufficient. Router-specific commands
  and rollback must be agreed before isolation.
- Capture only the designated interface and fixture traffic, for example:

  ```sh
  tcpdump -i <interface> -nn -s 0 -w <private-path>/lan.pcap \
    'host <lamp-ip> and udp and (port 4001 or port 4002 or port 4003)'
  ```

  Keep raw captures private with owner-only access. Record isolation evidence
  separately; this filter cannot prove WAN blocking.
- Run each manifest step once; timestamp outgoing bytes and replies. Wait one
  second between transactions and five seconds for observations. These are
  conservative test intervals, not established H60C1 requirements. Do not
  silently retry a failed write; record it and agree a new trial.
- After each step, send `{"msg":{"cmd":"devStatus","data":{}}}` to UDP 4003
  and listen on 4002 for up to five seconds. Record timeout as timeout, not
  unsupported. Store raw replies separately from interpretations. A UDP send
  proves neither delivery nor LED behavior.
- Label last-sent state **intent**, parsed replies **device report**, and
  signed owner observations **physical result**. The client's whole-device
  status cannot verify zones. Preserve unknown reply fields for inspection
  without assuming their meaning.

### Numbered owner observation checklist

For each row record UTC time, manifest step IDs, bottom temperature/brightness,
side color/brightness, curved state, unintended changes and pass/fail/inconclusive.
Use fixed camera exposure/white balance for comparisons; photographs alone
cannot identify emitters or calibrate temperature/brightness.

1. Confirm H60C1 / 1.01.27 (record deviations), LAN enabled, safe recovery and
   the agreed window. Confirm WAN blocks for both endpoints and no phone,
   Bluetooth or cloud fallback.
2. With captured initialization only, set bottom **dedicated white** 3000 K /
   60%, side red / 40%, curved off. Observe both together. Explain LED identity
   using app white-channel control/capture mapping and safe non-invasive
   emitter observation or suitable measurement. If identity is unresolved,
   mark dedicated white inconclusive even if it looks white.
3. Change only bottom temperature to 5000 K; confirm side red / 40% remains.
4. Change only bottom brightness to 30%; confirm side color/brightness remains.
5. Change only side color to blue; confirm bottom white 5000 K / 30% remains.
6. Change only side brightness to 20%; confirm bottom temperature/brightness
   remains. Check curved state after every step for accidental writes.
7. Reverse setup order: side red / 40% first, then bottom 3000 K / 60%.
   Repeat 3–6. Observe both after every write; do not resend the unchanged zone
   to hide overwrites.
8. Still offline, power-cycle the lamp once with the safe switch; avoid rapid
   cycling/reset sequences. Record persistence **before writes**, rediscover
   and repeat 2–7. Record any required initialization separately.
9. Still offline, restart the controller with last-sent state cleared and
   retained-command replay disabled. Observe before writes; repeat 2–7.
   Restart both and repeat again. Record discovery/status failures and all
   recovery dependencies. Reconfirm isolation for each restart trial.
10. Stop capture, restore settings/connectivity by the agreed rollback, and
    confirm normal operation. Explicitly confirm each observation in #10;
    worker logs and simulations cannot replace owner signoff.

Stop on unexpected modes, flicker, loss of control or owner request. Preserve
failures and use agreed recovery instead of trying other models' payloads.
A failed candidate does not prove LAN control impossible.

### Redaction and result record

Never commit raw pcaps, Bluetooth snoop logs, account/device dumps or secrets.
Remove keys, tokens, passwords, pairing material, SSIDs, account/MQTT topics,
device IDs, MAC/BLE/IP addresses, names/rooms and unrelated traffic before
sharing. Use stable aliases (`lamp-A`, `controller-A`) for correlation; preserve
byte positions, units, order and timing. Review payloads as well as headers,
and image metadata/backgrounds as well as visible labels. Distinguish private
raw hashes from redacted-artifact hashes.

Each trial needs: inventory version, controller commit, model/firmware,
manifest hash, isolation evidence, command/reply log, checklist 1–10,
restart/initialization notes, redaction review and restoration confirmation.
For each capability use **verified**, **unsupported in the observed trial** or
**inconclusive**, citing evidence IDs. Unexecuted steps remain open. Physical
acceptance and implementation are separate outcomes.

## Delivery to #10 and implementation gate

This inventory and protocol are the handoff to #10. Current automated result:
source inspection only; zero H60C1 sends, replies, readbacks or physical trials.
All manual observations are pending. #10 awaits owner hardware/captures and
supervised acceptance even after #3 completes.

Only when H60C1 evidence supports both zones should an implementation ticket
cover a firmware-scoped profile, captured-frame encoding tests, the existing
LAN/MQTT path and explicit readback limits. It must preserve the other zone
and existing models, without a cloud fallback presented as local support.
Link #10 evidence and keep its physical acceptance separate. No implementation
ticket is created by this research.

[product]: https://eu.govee.com/es-es/products/govee-pendant-light
[lan-guide]: https://app-h5.govee.com/user-manual/wlan-guide
[bridge-readme]: https://github.com/SamWiIIiams/govee-lan-bridge/blob/e4551b33b86fd32ae9bb2e47dedd637b230be411/README.md#protocol-notes
[bridge-code]: https://github.com/SamWiIIiams/govee-lan-bridge/blob/e4551b33b86fd32ae9bb2e47dedd637b230be411/bridge.py#L107-L182
[segments]: https://github.com/alexluckett/govee2mqtt-segment-control/blob/30a8392865cf28c763e0d10d6edf921d9b2052ab/docs/SEGMENT_CONTROL.md
[local-hass]: https://github.com/micschr0/govee2mqtt/blob/f0c9ce4e9e3fe3b5293b31c22dc14418a6336182/src/service/hass.rs#L353-L400
[local-lan]: https://github.com/micschr0/govee2mqtt/blob/f0c9ce4e9e3fe3b5293b31c22dc14418a6336182/src/lan_api.rs#L300-L326
[local-cli]: https://github.com/micschr0/govee2mqtt/blob/f0c9ce4e9e3fe3b5293b31c22dc14418a6336182/src/commands/lan_control.rs
[local-ble]: https://github.com/micschr0/govee2mqtt/blob/f0c9ce4e9e3fe3b5293b31c22dc14418a6336182/src/ble.rs#L460-L492
