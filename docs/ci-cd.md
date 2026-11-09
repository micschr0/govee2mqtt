# CI and dependencies

| Workflow | Checks |
| --- | --- |
| `rust.yml` | Formatting, Clippy, Rustdoc, tests, build and coverage of the store source |
| `security.yml` | Actionlint, ShellCheck for `scripts/*.sh`, Cargo Audit of the store source and Gitleaks across Git history |
| `store-integrity.yml` | Package checksums and consistency of `SOURCE.json` / `SOURCE_TAG` |
| `renovate.yml` | Scheduled or manual Renovate runs; requires `RENOVATE_APP_ID` and `RENOVATE_PRIVATE_KEY` |

Rust CI runs when `govee2mqtt_security_local/local-source/` or the Rust workflow
changes. Root-source changes need additional local checks. Cargo Audit also runs
weekly. There is no automatic container release workflow.

## Update rules

- Rust toolchain and store builder are aligned on 1.99.1.
- Actions are pinned to commit SHAs.
- Renovate manages Cargo in the store source tree; automerge is disabled.
- Docker and toolchain updates are disabled in Renovate.
- Dependabot configuration also exists; avoid duplicate version PRs when enabling Renovate.

Store updates must keep sources, manifests, versions and checksums consistent.
Root and store sources are not automatically synchronized.
Local commands and export constraints: [development](DEVELOPMENT.md).
