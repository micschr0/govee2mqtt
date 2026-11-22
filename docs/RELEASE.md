# Release and rollback

The Home Assistant package version comes from `govee2mqtt_security_local/config.yaml`.
`SOURCE_TAG`, `SOURCE.json`, `.dockerignore` and `SHA256SUMS` are generated from
the package inputs. The embedded build version comes from `SOURCE_TAG` in both
Docker builds. The authoritative changelog is in the add-on directory.

## Stable release gates

1. Run `make verify` and `make runtime` in a disposable test environment against
   the same clean candidate commit. Both honor `CARGO_TARGET_DIR`; the runtime
   checks use local fixtures, not real devices or cloud services.
2. Record GitHub Rust, Store integrity, Security and Package verification runs
   for that commit. Package verification builds both formats on amd64 and
   arm64, checks image architecture and embedded CalVer, and does not push images.
   The operator then runs the [same-ID Supervisor upgrade and restoration](qa/stable-supervisor-upgrade.md).
3. Record [manual acceptance](qa/manual-acceptance.md) for an actual supported
   device, including an offline restart with cloud disabled. If shipping
   cloud opt-in, record LAN continuity with the opted-in cloud unreachable.
4. The operator enables and verifies the private reporting route in
   [SECURITY.md](../SECURITY.md).

A `stable/*` candidate branch can carry `stage: stable` for verification without
changing the regular store. The stage flag is metadata, not approval. Keep the
candidate version distinct from the regular store's current version. Changes to
the tested candidate invalidate affected evidence; record the new revision and
repeat the affected checks before approving it.

## After explicit maintainer approval

### Regular Home Assistant store update

The regular store repository URL follows `main`, not Git tags or GitHub
Releases. Use an unused `YYYY.MM.DD` version and publish only the approved tree.
Keep the URL and app slug unchanged. Record the published commit and package
version, then reload the store and update the existing app without uninstalling.

### Optional Git tag

Use a clean checkout, an unused version and `git-cliff`. With `TAG_NAME` set to
the approved version, `scripts/tag-release.sh` generates the changelog, updates
the add-on version and checksums, commits that metadata, and only then creates
the local tag. It does not push or publish. Check that the tag resolves to that
commit and that `config.yaml`, `SOURCE_TAG` and `SOURCE.json` in the tagged tree
all carry the same version. Preserve the reviewed revision and image digest.

## Rollback

Before upgrading, back up options and the persistent `/data` and `/app/config`
mounts (Docker uses `/data` only). Keep the previous verified image or package and
its identity. If an upgrade fails, stop the new bridge and restore the matching
old version and data together on a disposable instance first. Keep the same
add-on slug; do not uninstall to downgrade. An image rollback alone does not
roll back stored data, and arbitrary downgrades are not supported.
