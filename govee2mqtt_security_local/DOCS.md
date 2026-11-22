# In-context source build

Add `https://github.com/micschr0/govee2mqtt` as a Supervisor add-on repository.
Select Govee to MQTT Bridge and configure a reachable MQTT broker. Start it
manually the first time to check logs and MQTT devices. Enable LAN Control on
supported devices; independent H60C1 zones are not supported. Govee account/API
credentials are optional. HTTP/WebUI stay disabled without `http_bind`; an
enabled API has no authentication. AppArmor and host networking remain enabled.

The sole application lives in `local-source/`. Both amd64 and aarch64 build it
locally with pinned Rust/HA bases, signed Debian snapshots and `Cargo.lock`. Docker calls
aarch64 `linux/arm64`; native execution or configured emulation is required.
The default `verification` Cargo profile is a dev build with debug info and
incremental compilation off. Release builds require separate human approval.

The store context is this whole directory. There is no export script or parent
source dependency. `SHA256SUMS` verifies inputs before compilation; SOURCE.json
records content hashes and historical origin, and SOURCE_TAG matches config.yaml.
From the repository root, refresh generated metadata after source or package edits:
`python3 scripts/check-store-source.py --write`. This is not a release or acceptance.

The store URL and app slug are preserved across updates. Supervisor `/data` options and the writable
`addon_config` mount at `/app/config` retain their existing meanings; do not delete
or recreate them during an upgrade. Automatic startup is enabled by default and
can be disabled in Supervisor. A previously saved startup setting takes precedence;
check the switch after updating. The launcher waits briefly for the
Supervisor-provided MQTT broker; an explicit `mqtt_host` uses that configuration.

- [Configuration](../docs/CONFIG.md)
- [Development](../docs/DEVELOPMENT.md)
- [Source comparison and rationale](../docs/SOURCE-LAYOUT.md)
- [Build and isolated upgrade verification](../docs/ADDON-VERIFICATION.md)
- [Security acceptance](../docs/security/TEST-MATRIX.md)

Installation and a help smoke run do not establish HA/MQTT/device acceptance.
Never use real devices or user data for disposable upgrade verification.
