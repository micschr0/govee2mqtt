# One application source tree

Issue #1 retains the application in `govee2mqtt_security_local/local-source/`.
Home Assistant builds with the add-on directory as its context, so this layout
keeps every source input available to Supervisor without downloads, a registry
image, or a separately maintained export. Ordinary Docker builds copy the same
package from the repository context. Root Make targets enter that source directory.

## Reconciliation at 87fc74b36fe574957d17da08bada0345e4160182

Both trees were compared recursively, including path membership and file bytes:

| Input group | Files | Result and retained choice |
| --- | ---: | --- |
| `src/` (including snapshots) | 57 | One difference: `hass_mqtt/base.rs` project URL. Retain the root fork URL `https://github.com/micschr0/govee2mqtt`. |
| `assets/` | 9 | Identical; retain in-context assets. |
| `vendor/` | 7 | Identical, including SQLite patch, tests, README and license. |
| `test-data/` | 16 | Identical, including historical issue fixtures. |
| `Cargo.toml`, `Cargo.lock`, `build.rs`, `AmazonRootCA1.pem` | 4 | Identical; retain in-context files. |

All 93 inputs existed in both trees; there were no unpaired application files.
This comparison is reproducible against the pinned Git revision, before root
copies were removed. The only application behavior change from the old store
copy is its discovery project URL; all fork security and dependency fixes survive.

The `addon/` template was compared separately: Dockerfile, run.sh and English
translations were identical. config.yaml differed only in the version and URL;
the existing store version, slug, schema, network/security settings and mounts
are retained, with the URL corrected. build.yaml differed only in its source URL.
README/DOCS contained obsolete export instructions and are replaced by current
in-context instructions. The template's fork changelog is retained; the store's
old changelog was byte-identical to `docs/history/UPSTREAM-CHANGELOG.md`, where
that history remains. The MIT license and vendored attribution remain intact.

The root Dockerfile formerly consumed a host cross-built binary. It now builds
these same sources. Build/cross scripts and Make targets use the authoritative
manifest; release scripts refer to the retained package. The exporter and its
embedded PREPARE-SCRIPT copy are removed. No export or download is needed for
store installation. Release actions still require separate human approval.

## Integrity and provenance

`config.yaml` owns the installation version; consolidation does not bump it.
`SOURCE_TAG`, `SOURCE.json`, `SHA256SUMS` and the package `.dockerignore` are
mechanically derived with `python3 scripts/check-store-source.py --write`.
Run the command after changing package inputs and commit the resulting metadata.
It does not build, publish, copy sources, change the version or grant acceptance.
The checker without `--write` rejects changed, added or removed inputs and stale
metadata. Docker also verifies all recorded checksums before compiling.

SOURCE.json spec 1 hashes the actual inputs, including config.yaml. Its `baseline`
is the historical fork origin, not the candidate commit or a build approval;
`content_id` identifies the current inputs. Git identifies the reviewed revision.
The old version's hash-like suffix is retained for installation compatibility,
not interpreted as a current content hash. Checksums detect drift, not malicious
changes or signatures. Security and isolated HA acceptance remain separate.
