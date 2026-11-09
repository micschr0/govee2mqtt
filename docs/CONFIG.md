# Configuration

Home Assistant requires an MQTT broker. Govee credentials are optional;
enable LAN Control in the Govee app for each device.

## HTTP API and WebUI

No HTTP listener starts by default. MQTT and LAN do not require it.

| CLI (`serve`) | Environment | Add-on |
| --- | --- | --- |
| `--http-bind 127.0.0.1:8056` | `GOVEE_HTTP_BIND=127.0.0.1:8056` | `http_bind: "127.0.0.1:8056"` |

- Format: IP and port; for IPv6, use brackets, e.g. `[::1]:8056`.
- CLI takes precedence over ENV; an explicit CLI value skips ENV validation.
- Alternatively, use `GOVEE_HTTP_BIND_FILE=/path/to/file`; invalid or unreadable content fails startup.
- Empty or invalid CLI/ENV values are errors. An empty add-on field counts as unset.
- To disable HTTP, remove the option and environment value. `--http-port` is no longer supported.

The enabled API has **no authentication**. Use loopback for local access only.
`0.0.0.0:8056` binds all IPv4 interfaces; `[::]:8056` binds all IPv6 interfaces
and, depending on the system, IPv4 as well. Non-loopback bindings produce a
startup warning.

## Govee Credentials

Account email and password enable additional metadata and IoT functions.
A Platform API key enables further device functions and scenes, depending on
the model. Set credentials only as needed; see [privacy](PRIVACY.md).

|CLI|ENV|Add-on|Purpose|
|---|---|-----|-------|
|`--govee-email`|`GOVEE_EMAIL`|`govee_email`|Govee account email|
|`--govee-password`|`GOVEE_PASSWORD`|`govee_password`|Govee account password|
|`--api-key`|`GOVEE_API_KEY`|`govee_api_key`|Govee Platform API key|

## LAN API Control

LAN is the preferred control method. Without cloud access, only locally
exposed device functions are available. Network details: [LAN](LAN.md).

|CLI|ENV|Add-on|Purpose|
|---|---|-----|-------|
|`--no-multicast`|`GOVEE_LAN_NO_MULTICAST=true`|`no_multicast`|Disable multicast discovery; requires a suitable alternative|
|`--broadcast-all`|`GOVEE_LAN_BROADCAST_ALL=true`|`broadcast_all`|Send discovery to the broadcast address of each non-loopback interface|
|`--global-broadcast`|`GOVEE_LAN_BROADCAST_GLOBAL=true`|`global_broadcast`|Send discovery to `255.255.255.255`|
|`--scan`|`GOVEE_LAN_SCAN=10.0.0.1,10.0.0.2`|`scan`|Probe comma-separated device IPs or network broadcast addresses; use fixed DHCP assignments|

## MQTT Configuration

Use the same broker as the Home Assistant MQTT integration.

|CLI|ENV|Add-on|Purpose|
|---|---|-----|-------|
|`--mqtt-host`|`GOVEE_MQTT_HOST`|`mqtt_host`|Broker hostname or IP|
|`--mqtt-port`|`GOVEE_MQTT_PORT`|`mqtt_port`|Broker port, default `1883`|
|`--mqtt-username`|`GOVEE_MQTT_USER`|`mqtt_username`|Broker username|
|`--mqtt-password`|`GOVEE_MQTT_PASSWORD`|`mqtt_password`|Broker password|

## Operation

`GOVEE_TEMPERATURE_SCALE=C` or `F` sets the temperature unit
(add-on: `temperature_scale`). `TZ=Europe/Berlin` sets the log timezone.
For diagnostics, use `RUST_LOG=govee=trace` (add-on: `debug_level`);
check logs for sensitive data before sharing.
CLI reference: `govee --help` and `govee serve --help`.
