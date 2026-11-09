# Troubleshooting and limitations

## LAN device not discovered

Enable LAN Control for the device in the Govee app. Check UDP ports, return
routes, Wi-Fi isolation and multicast. If needed, assign a fixed device IP and
use `scan`. See [LAN](LAN.md).

## Devices unavailable in Home Assistant

Check the broker connection and bridge/Home Assistant logs for `gv2mqtt` or
`mqtt`. Then use the bridge device's “Purge Caches” button.
Remove stale MQTT devices and rediscover them only if needed.

## Segments cannot be switched off

Govee's segment API exposes color and brightness but no separate power state.
Home Assistant still shows a switch. Support for brightness 0 and independent
segment brightness also depends on the device.

## Video effects are missing

Create a Tap-to-Run or Snapshot for the mode in the Govee app, then use
“Purge Caches”. With a configured Govee account, Tap-to-Run entries appear as
scenes and Snapshots as device effects where the API exposes them.

## Missing model or “devices not belong you”

Check [device support](SKUS.md). BLE-only devices are unsupported and may cause
the Platform API to return “devices not belong you”. For unexpected failures,
open an issue in the fork with the model, version and sanitized logs.
Remove passwords, tokens and personal device data.

## Device ID does not match a network MAC

Govee device IDs are not reliable network MAC addresses. Use the IP address
from DHCP or your router for LAN scans.
