# Home Assistant add-on

The fork provides the experimental `govee2mqtt_security_local` add-on for
Home Assistant with Supervisor. Container/Core installations without Supervisor
should use [Docker](DOCKER.md).

## Installation and configuration

1. Set up an MQTT broker and the MQTT integration.
2. Add `https://github.com/micschr0/govee2mqtt` as an add-on repository.
3. Select the experimental Govee add-on and let Supervisor build it locally.
4. Configure the MQTT connection. Govee credentials are optional for LAN devices.
5. Enable LAN Control in the Govee app for each LAN device.
6. After manually starting the add-on, check its logs and devices in the MQTT integration.

HTTP and WebUI are disabled by default. Set `http_bind` only when needed;
the enabled API has no authentication. See [configuration](CONFIG.md).
The package uses host networking, AppArmor and `/app/config` for persistent data.
`boot: manual_only` prevents automatic startup at boot.

## Package snapshot

`govee2mqtt_security_local/` contains a versioned export with its own source copy,
`SOURCE.json`, `SOURCE_TAG` and `SHA256SUMS`. Changes at the repository root do
not automatically update this package. Its metadata and documentation describe
the exported snapshot; some links still point to upstream.

Real HA/device acceptance is partly pending; see the
[test matrix](security/TEST-MATRIX.md). Installation alone does not establish acceptance.
See [development and export notes](DEVELOPMENT.md) before preparing a new package.
