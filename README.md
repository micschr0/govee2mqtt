# govee2mqtt

Independently maintained fork of [wez/govee2mqtt](https://github.com/wez/govee2mqtt).
Connects Govee devices to Home Assistant through MQTT. Source and issue tracker:
[micschr0/govee2mqtt](https://github.com/micschr0/govee2mqtt).

## Features and fork improvements

- LAN control preferred; supported devices work without cloud credentials.
- Govee Platform API for additional device functions, effects and segments.
- Optional Govee account for IoT status updates, rooms and Tap-to-Run scenes.
- HTTP API and WebUI disabled by default; require an explicit bind address.
- Login fallback for Govee error 454, updated dependencies and a local SQLite cache patch.
- Locally built Home Assistant add-on with pinned build dependencies and checksums.

Available functions depend on the device model and Govee APIs. BLE-only devices
are unsupported. The HTTP API has no authentication when enabled.

## Setup

1. Set up an MQTT broker and the MQTT integration in Home Assistant.
2. Choose [Docker](docs/DOCKER.md) or the [Home Assistant add-on](docs/ADDON.md).
3. Apply the [configuration](docs/CONFIG.md); enable LAN Control on each LAN device.

| Topic | Documentation |
| --- | --- |
| Networking and discovery | [LAN](docs/LAN.md) |
| Devices and limitations | [Device support](docs/SKUS.md), [FAQ](docs/FAQ.md) |
| Data and credentials | [Privacy](docs/PRIVACY.md) |
| Development and source trees | [Development](docs/DEVELOPMENT.md) |
| Automated checks | [CI](docs/ci-cd.md) |
| Security requirements and pending acceptance | [Security](docs/security/README.md) |

The store package remains experimental. Local checks do not replace full
acceptance testing with Home Assistant, MQTT and real devices.

## Credits and license

MIT; see [LICENSE.md](LICENSE.md). Originally by Wez Furlong, building on
[Govee LAN Control](https://github.com/wez/govee-lan-hass/).
AWS IoT support draws on work from
[bwp91/homebridge-govee](https://github.com/bwp91/homebridge-govee/).

Development, Docker and the Home Assistant store use the sole application tree
at `govee2mqtt_security_local/local-source/`. See [source layout](docs/SOURCE-LAYOUT.md)
and [development commands](docs/DEVELOPMENT.md).
