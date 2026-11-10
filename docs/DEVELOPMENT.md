# Development

## Source trees

| Path | Purpose |
| --- | --- |
| `src/`, `assets/`, `vendor/` | Current bridge development sources |
| `addon/` | Template for local Home Assistant packages |
| `govee2mqtt_security_local/` | Versioned store export with checksums and its own `local-source/` |
| `docs/security/` | Security requirements, test matrix and historical evidence |

The store export is a package snapshot, not an automatically synchronized mirror.
Its old project links remain until a consistent new export is prepared.
Historical issue links in code still point to the original reports.
License texts and third-party documentation retain their attribution.

## Local checks

Requires Rust, C/C++ build tools, CMake, pkg-config and OpenSSL build prerequisites.
From the repository root:

```sh
cargo fmt --all -- --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
cargo build --locked
```

Run the same commands from `govee2mqtt_security_local/local-source/` to check the
packaged source. CLI reference: `cargo run --locked -- --help` and
`cargo run --locked -- serve --help`.

Check package integrity from the repository root:

```sh
(cd govee2mqtt_security_local && sha256sum --strict -c SHA256SUMS)
python3 scripts/check-store-source.py
```

## Add-on exports and releases

`scripts/prepare-local-addon.py` exports working-tree contents and checks a fixed
Git HEAD pin (`BASELINE`). The pin does not automatically follow new commits;
do not bypass a rejected export by removing the check. Review and deliberately
update the export baseline and acceptance status before preparing a new package.
Output paths must be new and outside the checkout.
CLI: `python3 scripts/prepare-local-addon.py --help`.

The add-on builds from local sources for amd64/aarch64 rather than downloading an
upstream binary. An image build does not replace HA/MQTT/device acceptance;
see the [test matrix](security/TEST-MATRIX.md).

Release builds, tags and publishing require explicit human approval, including
`scripts/tag-release.sh` and release build scripts.

For disposable offline fixtures, verification-profile builds on both architectures,
and the owner-operated HA upgrade procedure, see [add-on verification](ADDON-VERIFICATION.md).
Readiness and fixture checks do not establish migration acceptance.
