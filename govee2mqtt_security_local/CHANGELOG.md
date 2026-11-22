# Changes

## 2026.11.26

- Add LAN RGB controls for the three logical H60C1 segments and a batched
  MQTT command. Dedicated white and device-reported segment state remain
  unsupported.

## 2026.11.25

- Refresh the Store package version. Application behavior is unchanged.
- The repository adds an offline H60C1 acceptance kit. Independent H60C1 zones
  are not included in the add-on.

## 2026.11.24

- Advertise the H60C1 whole-light white temperature range of 2700–6500 K in
  Home Assistant. Round the cool end inward so slider values stay in range.
- Update the `url` dependency for RUSTSEC-2026-0592 and install the fixed Debian
  `zlib1g` in the add-on image (DSA-6613-1).
- Keep Git revision identifiers in local builds and package versions in
  container builds.
- Independent H60C1 zones are not included.

## 2026.11.23

- Use Rust 1.100.0, updated direct dependencies and pinned Debian 13 build and
  runtime images for amd64 and aarch64.
- Keep the existing store entry, options, data paths and MQTT discovery IDs.
- Verify LAN startup and control with synthetic fixtures, including unreachable
  opted-in cloud, MQTT reconnect and HTTP bind errors.
- Independent H60C1 zones are not supported.

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
