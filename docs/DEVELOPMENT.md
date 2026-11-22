# Development

The sole application tree is `govee2mqtt_security_local/local-source/`: Rust
sources, assets, test data, vendored patches, manifest and lockfile. The enclosing
directory is the complete Home Assistant build context. There is no root source
copy or `addon/` template. See [layout and comparison](SOURCE-LAYOUT.md).

Requires Rust 1.100.0, C/C++ build tools, CMake, pkg-config and OpenSSL prerequisites.
From the repository root, run `make verify` (format, Clippy, tests, ordinary build,
package integrity and Python fixture tests). Set `CARGO=/path/to/cargo` if needed.
Equivalent Cargo checks:

```sh
cd govee2mqtt_security_local/local-source
cargo fmt --all -- --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
cargo build --locked
cargo run --locked -- --help
```

Run CLI commands from that directory so the relative `assets/` path resolves.
HTTP remains disabled without explicit configuration; running `--help` starts no
services. Historical issue links and third-party attribution remain unchanged.

Run `make runtime` on a disposable Linux runner with Python 3, OpenSSL, GNU
`timeout` and free UDP ports 4001–4003. It checks launcher failures, the Rust
cloud refresh worker over three outage/recovery cycles, and the bridge process
with a simulated MQTT broker, LAN lamp and HTTPS proxy. The process check
covers MQTT reconnect, five pinned discovery identities across bridge
restarts, LAN commands/readback, HTTP bind failures and startup while cloud
is unavailable. It compares MQTT payloads, not the Supervisor entity registry.
For network isolation, fetch the locked dependencies first:

```sh
unshare -Urn sh -c 'ip link set lo up && CARGO_NET_OFFLINE=true exec make runtime'
```

For an already built binary, `python3 scripts/verify-runtime.py <binary>` runs
only the process checks. The proxy observes requests it receives, not all egress.

For contributions, report the smallest reproducible case, then add a regression
test at the affected layer where practical. Include the tested revision,
commands, outcomes and limits in the PR. For real devices use the separate
[manual acceptance handoff](qa/manual-acceptance.md).

After changing package inputs, from the repository root:

```sh
python3 scripts/check-store-source.py --write
python3 scripts/check-store-source.py
(cd govee2mqtt_security_local && sha256sum --strict -c SHA256SUMS)
```

Review and commit the regenerated metadata with the change. Only metadata is
generated, never a second source tree. Keep the package version unchanged except
when preparing a distinct candidate or an approved update. No exporter or fixed-HEAD export pin
is needed; Git revisions plus content hashes record provenance.

[Docker](DOCKER.md) and [add-on verification](ADDON-VERIFICATION.md) use the
non-release `verification` profile (dev, debug info off, incremental off).
See [release and rollback](RELEASE.md); release builds, scripts, tags and
publication require explicit human approval.
Image and fixture checks do not replace an isolated Supervisor upgrade or device
acceptance; see the [security matrix](security/TEST-MATRIX.md).
