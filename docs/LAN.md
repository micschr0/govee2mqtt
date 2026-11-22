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

Model-specific research: [H60C1 local white and color zones](H60C1-LOCAL-ZONES.md)
contains the evidence inventory and hardware protocol; physical LAN support
remains inconclusive.
