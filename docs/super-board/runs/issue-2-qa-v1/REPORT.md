# Issue #2 QA v1

Reviewed application head: `b26b7af5b0f111c3cc9a24c5bc6479b117a15f22` against `origin/main`.
Host: Codex. Independent review, Standards/Spec review, test-gap review and security filtering performed inline as requested.

## Result

Pass for the five procedure/offline-fixture acceptance criteria of #2.
Actual candidate packaging on amd64/aarch64 and the isolated HA upgrade were not run and remain owned by #1. No HA target has been designated; the repository owner provides the target and operates the test. No container readiness, release, publishing or hardware result is asserted.

## Independent hypotheses and evidence

1. Lost/changed options or either persistent marker must fail through the public CLI. Three unittest methods pass, covering removed mqtt_port, removed data/config markers, changed marker bytes, wrong types, changed values, enabled HTTP, invalid JSON and a separate saved baseline. Diagnostics omit the synthetic secret witness. `fixtures.log` records the fresh run.
2. Verification-profile preparation must preserve original packages and create internally consistent contexts. The exact Python block from the documentation was executed against both current-layout inputs in a new disposable directory. Both scratch manifests validate; Dockerfile command/output paths select verification; profile inherits dev with debug/incremental disabled; all original package bytes remain equal. Repeating preparation refuses existing destinations. All shell blocks parse with bash -n. `procedure.log` records results. This is preparation validation, never a container build.
3. Readiness must never become migration acceptance. Each documented probe has an outer timeout of 60 seconds; platform execution, image pulls, directory mounts and actual build networking are identified separately. The build/help matrix explicitly covers both roles and both platform names without image publication or release scripts. Documentation assigns completed packaging/upgrade acceptance to #1.
4. The HA procedure must retain identity and both persistent mounts. Reviewed against current package config/Dockerfile/run script and official HA references below: local_govee2mqtt_security_local, /data and writable addon_config mapped at /app/config; baseline install, candidate replacement/rebuild without uninstall, saved options comparison, reset and owner responsibilities are explicit. Live availability remains pending.

## Acceptance and test-gap ledger

| AC | Unit / CLI rung | Component rung | E2E / procedure evidence |
|---|---|---|---|
| 1: architecture/profile/help commands | n/a: documentation | n/a: documentation | ADDON-VERIFICATION.md:5-18,107-170; shell parse and exact scratch preparation pass; actual matrix belongs to #1 |
| 2: representative options and markers | tests/test_addon_fixtures.py:16,42,67; CLI: scripts/verify-addon-fixtures.py:11-28 | n/a: no component | unchanged passes, deliberate losses fail; fixtures.log |
| 3: isolated HA lifecycle | n/a: procedure | n/a: no component | ADDON-VERIFICATION.md:172-222; config/source and official-doc review; target pending |
| 4: bounded readiness and offline execution | CLI/unittest fresh pass | n/a: no component | ADDON-VERIFICATION.md:41-105; every probe bounded; readiness/live execution not claimed |
| 5: acceptance ownership | n/a: prose | n/a: no component | ADDON-VERIFICATION.md:3-5,211-214; DEVELOPMENT.md link and explicit boundary |

No High gaps for #2. No Medium/Low gaps requiring new tests were identified within its stated scope. Dynamic container and HA evidence remain future acceptance work, not skipped #2 assertions. No project-specific verifier map exists; the framework template is not executable project coverage. Screenshots are omitted because all ACs concern procedures/CLI fixtures and no UI changed.

The tests were challenged in disposable source copies: dropping option preservation makes the existing suite fail; dropping marker preservation also makes it fail. Mutations never touched the issue source or reached a commit. The custom-baseline test rejects a required field missing from both observations.

## Standards, Spec and security

Standards: no findings against repository English/scope/privacy/security-default requirements. No production/runtime source or workflow changed. Spec: all five #2 requirements are covered; no future acceptance is claimed. Truth-check: read actual checks and their negative witnesses, executed the exact preparation block and checked original bytes independently; no unsupported builder claim carried forward.

pr-security-review: 0 kept findings. Reviewed the complete base-relative diff and connected fixture/config/run interfaces. New execution is a local maintainer CLI reading explicitly supplied files, parsing JSON without evaluation and comparing bytes/types/values. Tests invoke subprocess with argument arrays and no shell. No new lower-trust input crosses an authorization or execution boundary. Documentation/test-only exclusions were applied; no vulnerability candidate survived for a finding thread.

## Fresh verification

- python3 -m unittest discover -s tests -v: 3 passed.
- python3 scripts/verify-addon-fixtures.py tests/fixtures/addon: PASS.
- Configured cargo fmt --all -- --check: exit 0.
- Configured cargo clippy --locked --all-targets -- -D warnings: exit 0.
- Configured cargo test --locked: 54 passed, 0 failed.
- Configured cargo build --locked: exit 0, ordinary dev profile.

All Cargo invocations used the owner-required absolute serialized wrapper with the recovery environment; full Cargo logs and runner details remain private. No release build was invoked.

Reviewer feature rerun command:

```sh
python3 -m unittest discover -s tests -v && python3 scripts/verify-addon-fixtures.py tests/fixtures/addon
```

## Primary reference spot-checks

- [HA testing](https://contributors.home-assistant.io/apps/guides/testing/): local rebuild, architecture naming and limits of plain Docker.
- [HA configuration](https://contributors.home-assistant.io/apps/reference/configuration/): distinct private data and writable configuration mapping; legacy addon_config remains accepted.
- [HA CLI rebuild implementation](https://github.com/home-assistant/cli/blob/master/cmd/apps_rebuild.go): rebuild slug and force flag.
- [Cargo custom profiles](https://doc.rust-lang.org/cargo/reference/profiles.html): custom profile inheritance.

References were checked during this run; they support procedure review only.
