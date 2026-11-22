# Changes

## 2026.11.22 — Home Assistant test package

- Build Docker and Home Assistant packages from one application source tree.
- Use LAN and MQTT without Govee credentials; cloud features are opt-in.
- Support optional MQTT TLS with certificate and hostname verification.
- Keep HTTP disabled by default; the optional WebUI uses only local assets.
- Isolate cloud cache data by account or API key and leave the old cache untouched.
- Validate LAN discovery responses and use the current IP after DHCP changes.
- Enable automatic startup by default for new Supervisor installations.

This is an experimental store update for testing. It does not include
independent LAN control of the H60C1 zones.

## Fork development state

- HTTP and WebUI require an explicitly configured bind address.
- Optional cloud credentials and login fallback for error 454.
- Updated dependencies and a local SQLite cache patch.
- Local add-on source build with pinned build dependencies and provenance.

This is not a release approval. An exported package records its version and
sources in `SOURCE_TAG` and `SOURCE.json`.
Earlier upstream history is preserved in the source repository at
`docs/history/UPSTREAM-CHANGELOG.md`.
