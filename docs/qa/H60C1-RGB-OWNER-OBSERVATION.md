# H60C1 owner observation: three RGB segments over LAN

[Issue #10](https://github.com/micschr0/govee2mqtt/issues/10) · Owner report
received 2026-11-22. This adds evidence to the original
[acceptance kit](H60C1-ACCEPTANCE.md); it does not replace its pending checks.

An H60C1 on firmware `1.01.27` showed red, green and blue simultaneously after
one IPv4 UDP-unicast datagram to port `4003`. The datagram contained three RGB
frames in `msg.data.command` under `msg.cmd = "ptReal"`. The owner reported the
visible result; no raw capture or device status reply was supplied.

| Logical segment | RGB | Mask bytes | XOR | Base64 |
| --- | --- | --- | --- | --- |
| 1 | `255, 0, 0` | `01 00` | `dc` | `MwUVAf8AAAAAAAAAAQAAAAAAANw=` |
| 2 | `0, 255, 0` | `02 00` | `df` | `MwUVAQD/AAAAAAAAAgAAAAAAAN8=` |
| 3 | `0, 0, 255` | `04 00` | `d9` | `MwUVAQAA/wAAAAAABAAAAAAAANk=` |

Each frame contains `33 05 15 01` at offsets 0–3, RGB at 4–6, zero padding
at 7–11, a little-endian 16-bit mask at 12–13, zero padding at 14–18 and XOR
of bytes 0–18 at offset 19. Each tested frame has one mask bit set. Offline
validation reproduced all three frames in order; it did not test the device.

The trial did not establish physical zone mapping, preservation of other
segments after a single-segment write, multi-bit masks in a single frame,
dedicated white, per-zone brightness, segment readback, or persistence after
an offline restart. The observation predates the bridge implementation.
