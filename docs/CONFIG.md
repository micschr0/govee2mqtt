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

The enabled WebUI and API have **no authentication**: any client that can
reach the listener can read device data and send control commands. Use
loopback for local access only; do not expose this port to untrusted networks.
`0.0.0.0:8056` binds all IPv4 interfaces; `[::]:8056` binds all IPv6 interfaces
and, depending on the system, IPv4 as well. Non-loopback bindings produce a
startup warning.

Open the WebUI at `http://127.0.0.1:8056/`, or use the address and port you
configured. The listener accepts IP literals and `localhost`, not other DNS
names. The API rejects cross-origin browser requests when it receives
`Origin` or Fetch Metadata headers. Direct HTTP clients do not need these
headers; the browser checks are not access control. The WebUI cannot be
embedded in a frame and loads all assets from the bridge, without internet access.

Device control and One-Click activation now require `POST` on the same URL
(no request body needed). Change any scripts using `GET` for control; `GET`
and `HEAD` on these paths no longer run commands. Read endpoints still use `GET`.

## Govee cloud opt-in

An API key opts into the Platform API. Account email and password together opt
into account metadata and IoT. Leave both options unset for LAN-only control.
Configuring either also allows online scene lookups. See [privacy](PRIVACY.md).

Cloud discovery runs separately from LAN and MQTT and retries after errors.
Cloud-only devices, names, and effects may appear later; existing discovery
identifiers and command topics do not change. A cloud outage can still make
cloud-only functions unavailable.

The bridge does not query the online scene catalog without opt-in. To query
it directly without credentials, run
`govee lan-control --ip <device-ip> scene --allow-cloud --list`.

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
|`--mqtt-port`|`GOVEE_MQTT_PORT`|`mqtt_port`|Broker port, default `1883` without TLS or `8883` with TLS|
|`--mqtt-tls-ca`|`GOVEE_MQTT_TLS_CA`|`mqtt_tls_ca`|Path to a PEM CA file; setting it enables TLS|
|`--mqtt-username`|`GOVEE_MQTT_USER`|`mqtt_username`|Broker username|
|`--mqtt-password`|`GOVEE_MQTT_PASSWORD`|`mqtt_password`|Broker password|

Without a CA file, MQTT uses plaintext. The add-on still uses the internal
MQTT service from Supervisor when `mqtt_host` is not set.

For TLS, use the hostname in the broker certificate and pass the PEM file for
the CA that signed it. CLI options take precedence over environment variables.
The add-on requires `mqtt_host` when `mqtt_tls_ca` is set. Put the CA file in
the add-on configuration directory and use the container path, for example:

```yaml
mqtt_host: "broker.lan"
mqtt_tls_ca: "/app/config/mqtt-ca.pem"
```

The bridge verifies the certificate chain and broker hostname. If TLS setup or
the initial TLS connection fails, startup fails without retrying in plaintext.
This secures the connection to the MQTT broker only; it does not change Govee
LAN discovery or enable Govee Cloud.

## Operation

`GOVEE_TEMPERATURE_SCALE=C` or `F` sets the temperature unit
(add-on: `temperature_scale`). `TZ=Europe/Berlin` sets the log timezone.
For diagnostics, use `RUST_LOG=govee=trace` (add-on: `debug_level`);
check logs for sensitive data before sharing.
CLI reference: `govee --help` and `govee serve --help`.
