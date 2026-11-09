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

## If discovery fails

1. Check LAN Control, the device IP and firewall rules.
2. Check Wi-Fi client isolation and multicast filtering between Wi-Fi and LAN.
3. Try `broadcast_all` for broadcasts on each network interface.
4. Alternatively, reserve a DHCP address and use `scan` with the device IP.

Multicast DNS is a different protocol; working mDNS does not establish working
Govee discovery. Targeted unicast with `scan` is often more suitable across VLANs.
The supplied Docker setup uses host networking.

Options and syntax: [LAN configuration](CONFIG.md#lan-api-control).
