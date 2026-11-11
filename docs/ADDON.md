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

## Authoritative package

`govee2mqtt_security_local/` is the complete store build context and contains the
only application source tree. Supervisor builds it directly for amd64 or aarch64;
no source download, prebuilt application image or export is required.
`SOURCE.json`, `SOURCE_TAG` and `SHA256SUMS` record its inputs and version.
The slug, option schema, `/data`, `/app/config` mapping and manual startup policy
are preserved by consolidation. See [layout](SOURCE-LAYOUT.md) and
[development](DEVELOPMENT.md) for metadata updates.

Real HA/device acceptance is partly pending; see the
[test matrix](security/TEST-MATRIX.md). Follow [isolated upgrade verification](ADDON-VERIFICATION.md)
before claiming compatibility; an image build alone does not establish it.
