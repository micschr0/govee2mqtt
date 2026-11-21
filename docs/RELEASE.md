# Release and rollback

The Home Assistant package version comes from `govee2mqtt_security_local/config.yaml`.
`SOURCE_TAG`, `SOURCE.json`, `.dockerignore` and `SHA256SUMS` are generated from
the package inputs. The embedded build version comes from `SOURCE_TAG` in both
Docker builds. The authoritative changelog is in the add-on directory.

## Verify before asking for approval

1. Run `make verify` and `make runtime` in a disposable test environment.
   Both commands honor `CARGO_TARGET_DIR`; runtime checks use local fixtures,
   not real devices or cloud services.
2. Complete [container and upgrade checks](ADDON-VERIFICATION.md) for the same
   source revision. Keep amd64 and aarch64 results separate from the isolated
   Supervisor upgrade.
3. Record [manual acceptance](qa/manual-acceptance.md) for an actual supported
   device, including an offline restart with cloud disabled. If shipping
   cloud opt-in, record LAN continuity with the opted-in cloud unreachable.
4. Enable and verify the private reporting route in [SECURITY.md](../SECURITY.md).

## After explicit maintainer approval

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
