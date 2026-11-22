# LAN control

Enable LAN Control in the Govee app for each supported device.
The bridge uses UDP:

| Destination | Port | Purpose |
| --- | --- | --- |
| Govee device | 4001 | Discovery; multicast `239.255.255.250` by default |
| Govee device | 4003 | Control commands |
| Bridge | 4002 | Device replies and status |

Port 4002 must be available for a local bind. Devices reply to the bridge's
source IP on port 4002; firewall rules and VLAN routing must allow this return path.

The bridge uses the UDP sender IP for discovery. The IP field in a reply can be
missing, empty, or unspecified (`0.0.0.0` or `::`). Any other IP must match the
sender. The next valid discovery reply can update a device's IP after a DHCP
change without restarting the bridge. If you use an explicit IP in `scan`,
update it after an address change or reserve a DHCP address.

Govee LAN discovery does not authenticate replies or device IDs. The bridge
trusts discovery replies from the networks that can reach it. Use LAN control
only on trusted networks and restrict access to UDP port 4002 accordingly.

## If discovery fails

1. Check LAN Control, the device IP and firewall rules.
2. Check Wi-Fi client isolation and multicast filtering between Wi-Fi and LAN.
3. Try `broadcast_all` for broadcasts on each network interface.
4. Alternatively, reserve a DHCP address and use `scan` with the device IP.

Multicast DNS is a different protocol; working mDNS does not establish working
Govee discovery. Targeted unicast with `scan` is often more suitable across VLANs.
The supplied Docker setup uses host networking.

Options and syntax: [LAN configuration](CONFIG.md#lan-api-control).

## H60C1 RGB segments

When the bridge discovers an H60C1 over IPv4, Home Assistant discovers three RGB
segment entities without a Govee account or API key. The numbering is logical,
not a physical map. The [owner's test on firmware 1.01.27](qa/H60C1-RGB-OWNER-OBSERVATION.md)
showed all three colors at once; it did not establish single-segment isolation
or behavior on other firmware versions. Discovery checks the model, not the
firmware version.

Use the original light entity for power, whole-lamp brightness and white
temperature. The bridge ignores segment MQTT commands without an RGB color.
Home Assistant may still show power and brightness controls for RGB lights,
and may scale the RGB values it sends. The bridge sends no separate power or
brightness command. RGB white does not address dedicated white LEDs. Segment
colors shown by Home Assistant are optimistic; they may be stale after batch
commands, whole-lamp changes or changes in the Govee app. The bridge has no
segment readback.

To set one to three colors as one LAN datagram, publish a JSON array to
`gv2mqtt/light/<device-id>/segments/command`. Use the ID from the whole-light
command topic. For example, from a Home Assistant action:

```yaml
action: mqtt.publish
data:
  topic: gv2mqtt/light/<device-id>/segments/command
  retain: false
  payload: >-
    [{"segment":1,"color":{"r":255,"g":0,"b":0}},
     {"segment":2,"color":{"r":0,"g":255,"b":0}},
     {"segment":3,"color":{"r":0,"g":0,"b":255}}]
```

Segment numbers are distinct integers from 1 to 3; each RGB channel is an
integer from 0 to 255. An invalid entry rejects the entire batch. The bridge
sends the frames in order with no cloud fallback. It ignores retained
command replays; a successful UDP send is not a device acknowledgment.

The separate [white and color-zone investigation](H60C1-LOCAL-ZONES.md) remains open.
