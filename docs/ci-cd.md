# CI and dependencies

| Workflow | Checks |
| --- | --- |
| `rust.yml` | Formatting, Clippy, Rustdoc, tests, build and coverage of the authoritative source |
| `security.yml` | Actionlint, ShellCheck for `scripts/*.sh`, Cargo Audit of the authoritative source and Gitleaks across Git history |
| `store-integrity.yml` | Package checksums and consistency of `SOURCE.json` / `SOURCE_TAG` |
| `renovate.yml` | Scheduled or manual Renovate runs; requires `RENOVATE_APP_ID` and `RENOVATE_PRIVATE_KEY` |

Rust CI runs on application and add-on packaging changes, root Dockerfile and
ignore rules, Makefile, scripts, tests and its workflow. Integrity CI checks the
same package and exercises stale-input/version and persistence regressions.
Cargo Audit also runs weekly. There is no automatic container release workflow.

## Update rules

- Rust toolchain and store builder are aligned on 1.99.1.
- Actions are pinned to commit SHAs.
- Renovate manages Cargo in the authoritative source tree; automerge is disabled.
- Docker and toolchain updates are disabled in Renovate.
- Dependabot configuration also exists; avoid duplicate version PRs when enabling Renovate.

Store updates must keep sources, manifests, versions and checksums consistent.
All checks and build contexts use the same authoritative application sources.
Local commands and provenance: [development](DEVELOPMENT.md).
