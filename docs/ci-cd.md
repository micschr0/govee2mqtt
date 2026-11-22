# CI and dependencies

| Workflow | Checks |
| --- | --- |
| `rust.yml` | Formatting, Clippy, Rustdoc, tests, build, fixture runtime checks and coverage |
| `security.yml` | Actionlint, ShellCheck for the launcher and scripts, Cargo Audit and Gitleaks |
| `store-integrity.yml` | Package checksums and consistency of `SOURCE.json` / `SOURCE_TAG` |
| `package-verify.yml` | Ordinary Docker and add-on verification builds on native amd64 and arm64 runners; offline CLI smoke checks, no registry push |
| `renovate.yml` | Scheduled or manual Renovate runs; requires `RENOVATE_APP_ID` and `RENOVATE_PRIVATE_KEY` |

Rust CI runs on application and add-on packaging changes, root Dockerfile and
ignore rules, Makefile, scripts, tests and its workflow. Integrity CI checks the
same package and exercises stale-input/version and persistence regressions.
Cargo Audit also runs weekly. There is no automatic container release workflow.

## Update rules

- Rust toolchain and store builder are aligned on 1.99.1.
- Actions are pinned to commit SHAs.
- Renovate owns Cargo and GitHub Actions version updates; automerge is disabled.
- Update Docker base images and the pinned Rust toolchain manually.
- Review the pinned Debian `bookworm` and `bookworm-security` snapshots for
  both Dockerfiles together. Builds fail if either signed index is unavailable.
- After reviewing a Cargo update, regenerate add-on metadata before rerunning CI.

Store updates must keep sources, manifests, versions and checksums consistent.
All checks and build contexts use the same authoritative application sources.
Local commands and provenance: [development](DEVELOPMENT.md).
