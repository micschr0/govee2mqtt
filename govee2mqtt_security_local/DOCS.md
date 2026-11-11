# In-context source build

Add `https://github.com/micschr0/govee2mqtt` as a Supervisor add-on repository.
Select this experimental add-on, configure an isolated or appropriate MQTT broker,
and start it manually. Enable LAN Control on LAN devices. Govee account/API
credentials are optional. HTTP/WebUI stay disabled without `http_bind`; an enabled
API has no authentication. AppArmor and host networking remain enabled.

The sole application lives in `local-source/`. Both amd64 and aarch64 build it
locally with pinned Rust/HA bases, a Debian snapshot and Cargo.lock. Docker calls
aarch64 `linux/arm64`; native execution or configured emulation is required.
The default `verification` Cargo profile is a dev build with debug info and
incremental compilation off. Release builds require separate human approval.

The store context is this whole directory. There is no export script or parent
source dependency. `SHA256SUMS` verifies inputs before compilation; SOURCE.json
records content hashes and historical origin, and SOURCE_TAG matches config.yaml.
From the repository root, refresh generated metadata after source or package edits:
`python3 scripts/check-store-source.py --write`. This is not a release or acceptance.

The slug and version are preserved. Supervisor `/data` options and the writable
`addon_config` mount at `/app/config` retain their existing meanings; do not delete
or recreate them during an upgrade. Startup remains manual.

- [Configuration](../docs/CONFIG.md)
- [Development](../docs/DEVELOPMENT.md)
- [Source comparison and rationale](../docs/SOURCE-LAYOUT.md)
- [Build and isolated upgrade verification](../docs/ADDON-VERIFICATION.md)
- [Security acceptance](../docs/security/TEST-MATRIX.md)

Installation and a help smoke run do not establish HA/MQTT/device acceptance.
Never use real devices or user data for disposable upgrade verification.
