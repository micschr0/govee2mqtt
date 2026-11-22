# Development

The sole application tree is `govee2mqtt_security_local/local-source/`: Rust
sources, assets, test data, vendored patches, manifest and lockfile. The enclosing
directory is the complete Home Assistant build context. There is no root source
copy or `addon/` template. See [layout and comparison](SOURCE-LAYOUT.md).

Requires Rust 1.99.1, C/C++ build tools, CMake, pkg-config and OpenSSL prerequisites.
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

Run `make runtime` on a disposable Linux runner; it needs free UDP ports
4001–4003. For an already-built binary, use `python3 scripts/verify-runtime.py
<binary>`. The suite uses a loopback-only simulated MQTT broker, LAN lamp and
HTTPS proxy, and temporary cache data. It cuts the MQTT TCP connection without
restarting the broker or bridge, then checks fresh subscriptions, unchanged Home
Assistant discovery identity, and LAN commands and state readback. Separate
checks cover bridge restarts, HTTP binding and startup while cloud is unavailable.
For network isolation, run the fixture in a namespace with only loopback:

```sh
unshare -Urn sh -c 'ip link set lo up && exec python3 scripts/verify-runtime.py "$1"' sh /path/to/govee
```

Rust tests cover repeated HTTP 503/recovery transitions. The fixture and Rust
tests do not replace physical or Supervisor acceptance.

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
generated, never a second source tree. The package version stays unchanged unless
an explicitly approved release changes it. No exporter or fixed-HEAD export pin
is needed; Git revisions plus content hashes record provenance.

[Docker](DOCKER.md) and [add-on verification](ADDON-VERIFICATION.md) use the
non-release `verification` profile (dev, debug info off, incremental off).
See [release and rollback](RELEASE.md); release builds, scripts, tags and
publication require explicit human approval.
Image and fixture checks do not replace an isolated Supervisor upgrade or device
acceptance; see the [security matrix](security/TEST-MATRIX.md).
