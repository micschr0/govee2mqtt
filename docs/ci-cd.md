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
Cargo Audit also runs weekly. Pushes to `stable/*` run the release candidate
checks on the pushed SHA without a pull request, tag or publishing workflow.
Renovate is maintenance automation, not a candidate gate; do not dispatch it
just to verify a candidate.

## Update rules

- Rust toolchain and store builder are aligned on 1.100.0.
- Actions are pinned to commit SHAs.
- Both container recipes use Debian 13 (Trixie). Its main, updates and security
  snapshots are pinned; APT verifies signatures and fails if any index is missing.
- The primary `Cargo.lock` pins the application's complete dependency graph,
  including the local SQLite patch. Its standalone upstream benches and
  development-only dependencies are not built by the application.
- Renovate owns Cargo and GitHub Actions version updates; automerge is disabled.
- Update Docker base images and the pinned Rust toolchain manually.
- After reviewing a Cargo update, regenerate add-on metadata before rerunning CI.

Store updates must keep sources, manifests, versions and checksums consistent.
All checks and build contexts use the same authoritative application sources.
Local commands and provenance: [development](DEVELOPMENT.md).
