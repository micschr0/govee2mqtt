# Add-on template

This template builds the bridge from `local-source/` rather than an upstream image.
`scripts/prepare-local-addon.py` adds sources, provenance, version and checksums.
The `addon/` directory alone does not contain those build inputs.

## Operation

- Requires an MQTT broker and the Home Assistant MQTT integration.
- Enable LAN Control per device; host networking supports UDP discovery.
- Govee account and API key are only needed for additional cloud functions.
- HTTP/WebUI stay disabled without `http_bind`; the enabled API has no authentication.
- AppArmor enabled; persistent configuration at `/app/config`.
- Experimental with `boot: manual_only`; real acceptance is partly pending.

## Development

Run `python3 scripts/prepare-local-addon.py --help` from the repository root.
The exporter accepts only its reviewed `BASELINE` commit and a new output
directory outside the checkout. Review the pin and acceptance status before
preparing a new export. Checksums establish integrity, not a signature.

The Dockerfile uses pinned Rust/Debian bases and a Debian snapshot.
Docker calls the ARM platform `linux/arm64`; Home Assistant calls it `aarch64`.
Builds need access to package and container registries and a native builder
or suitable emulation.

Current repository guides:

- [Installation](../docs/ADDON.md)
- [Configuration](../docs/CONFIG.md)
- [Development and exports](../docs/DEVELOPMENT.md)
- [Security acceptance](../docs/security/TEST-MATRIX.md)

After exporting, read this documentation in the source repository's context.
Release builds and publishing require explicit human approval.
