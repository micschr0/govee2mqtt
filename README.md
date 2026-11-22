# govee2mqtt

Independently maintained fork of [wez/govee2mqtt](https://github.com/wez/govee2mqtt).
Connects Govee devices to Home Assistant through MQTT. Start with local control
over your LAN; opt into Govee cloud features only if you need them.

## Features and fork improvements

- LAN control for supported models without a Govee account or API key in the bridge.
- [H60C1 RGB segment control over LAN](docs/LAN.md#h60c1-rgb-segments).
- Optional Govee Platform API for additional device functions, effects and segments.
- Optional Govee account for IoT status updates, rooms and Tap-to-Run scenes.
- HTTP API and WebUI disabled by default; require an explicit bind address.
- Login fallback for Govee error 454, updated dependencies and a local SQLite cache patch.
- Locally built Home Assistant add-on with pinned build dependencies and checksums.

Available functions depend on the device model and Govee APIs. BLE-only devices
are unsupported. H60C1 RGB segments do not control the dedicated white channel.
The HTTP API has no authentication when enabled.

## Setup

1. Set up an MQTT broker and the MQTT integration in Home Assistant.
2. Choose [Docker](docs/DOCKER.md) or the [Home Assistant add-on](docs/ADDON.md).
3. Enable LAN Control in the Govee app for each supported device. Configure only
   MQTT in the bridge to start; leave Govee credentials and HTTP bind unset.
4. For features your device does not expose locally, see
   [Govee cloud opt-in](docs/CONFIG.md#govee-cloud-opt-in).

| Topic | Documentation |
| --- | --- |
| Networking and discovery | [LAN](docs/LAN.md) |
| Devices and limitations | [Device support](docs/SKUS.md), [FAQ](docs/FAQ.md) |
| Data and credentials | [Privacy](docs/PRIVACY.md) |
| Development and source trees | [Development](docs/DEVELOPMENT.md) |
| Automated checks | [CI](docs/ci-cd.md) |
| Security reporting and acceptance | [Report privately](SECURITY.md), [acceptance status](docs/security/README.md) |
| Releases and rollback | [Release procedure](docs/RELEASE.md) |

Automated checks do not replace acceptance testing with Home Assistant, MQTT
and real devices. See the [stable release gates](docs/RELEASE.md).

## Credits and license

MIT; see [LICENSE.md](LICENSE.md). Originally by Wez Furlong, building on
[Govee LAN Control](https://github.com/wez/govee-lan-hass/).
AWS IoT support draws on work from
[bwp91/homebridge-govee](https://github.com/bwp91/homebridge-govee/).

Development, Docker and the Home Assistant store use the sole application tree
at `govee2mqtt_security_local/local-source/`. See [source layout](docs/SOURCE-LAYOUT.md)
and [development commands](docs/DEVELOPMENT.md).
