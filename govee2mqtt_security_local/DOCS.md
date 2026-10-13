# Local security development app – SPEC v0.3

This is an **unpublished local source-build recipe**, not an accepted security
release. The local Rust patch disables HTTP unless an explicit bind address is
configured. Packaging alone does not prove this behavior: real HA/device
acceptance is still pending. No production installation is authorized.

Leave `http_bind` unset for MQTT/LAN-only operation. To explicitly enable the
unauthenticated API, set e.g. `http_bind: "127.0.0.1:8056"`. The address and port
are validated by the service; there is no default listener or default WebUI.

There is deliberately no `image:` registry reference. The Dockerfile compiles
`local-source/` with `cargo build --locked --release`. It never copies a govee
binary from Upstream or the development host. MQTT options, LAN host networking,
AppArmor and the existing `/app/config` mount remain unchanged. There is no
Ingress or default WebUI link. Cloud credentials are optional and absent from
the default options. `boot: manual_only` prevents automatic boot startup; it is
not a substitute for the HTTP patch or permission to start this app.

## Export from the local checkout

From the project directory (Python 3.9+; Git; no Python third-party modules):

```sh
python3 source/scripts/prepare-local-addon.py \
  --output local-package/new/govee2mqtt_security_local \
  --archive local-package/new/govee2mqtt-security-local.tar.gz
cd local-package/new/govee2mqtt_security_local
sha256sum --strict -c SHA256SUMS
```

Use a new destination for each export; existing paths are not overwritten.
The exporter requires the full SPEC baseline SHA and includes **working-tree**
source changes, not just HEAD. Source/package contents determine the local app
version and embedded `GOVEE_CI_TAG`. `SOURCE.json` records provenance and pending
security acceptance. `.env`, `.git`, `target`, toolchains and host binaries are
not top-level export inputs. Symlink inputs are rejected. Source and asset
directories are copied recursively: never put secrets there.

The archive is deterministic for identical input bytes: sorted entries, fixed
ownership, permissions and timestamps, gzip timestamp zero. This is **not** a
claim of byte-identical container images or compiled binaries; neither has
been demonstrated. SHA256SUMS checks integrity, not publisher authenticity.

## Local image build, no push

Docker with daemon access and Buildx is required. Build each platform separately:

```sh
docker buildx build --platform linux/amd64 --build-arg BUILD_ARCH=amd64 \
  --build-arg BUILD_VERSION="$(cat SOURCE_TAG)" \
  --load -t "govee2mqtt-security-local:$(cat SOURCE_TAG)-amd64" .
docker buildx build --platform linux/arm64 --build-arg BUILD_ARCH=aarch64 \
  --build-arg BUILD_VERSION="$(cat SOURCE_TAG)" \
  --load -t "govee2mqtt-security-local:$(cat SOURCE_TAG)-aarch64" .
```

HA calls the ARM architecture `aarch64`; Docker/OCI calls it `arm64`. Build stages
run on the target platform. Use native amd64/aarch64 builders or preconfigured
QEMU/binfmt emulation for the other architecture. No binfmt installation, Docker
permission change or privileged helper is part of this task. BUILD_ARCH is
required; unknown values fail rather than select another architecture.

Rust 1.94.0 and both Debian Bookworm HA bases are digest-pinned in Dockerfile.
APT uses the fixed Debian snapshot 20261010T000000Z (signature verification stays
enabled; only expired Release-time checks are disabled). Cargo.lock is honored.
Internet access is still needed for registry layers, the Debian snapshot and
Cargo crate downloads. This is not an air-gapped build; freezing dependencies
does not establish their security. Expected native tools: C/C++ compiler and
make from the Rust image, plus CMake/pkg-config installed in the build stage.
OpenSSL/Mosquitto/SQLite dependencies are built as selected by Cargo.lock.
The actual target runtime must run `/app/govee --help` successfully during build
to detect loader/shared-library issues. This does not exercise MQTT/LAN or HA.

## Later installation – isolated test HA only, separately authorized

Use the **whole exported directory**, not `source/addon/` by itself: Supervisor
builds only the app's directory and cannot COPY its parent source checkout.
The raw recipe intentionally fails without the prepared local source/manifest.

On a separately authorized disposable HA OS/Supervisor test system, place the
exported folder under the system's local-app directory, refresh the app store,
and install the experimental `govee2mqtt_security_local` app. Current official
docs use `/local_apps` (Samba share `local_apps`); older installations call it
`/addons`/`addons`. Verify the actual mount and Supervisor version, do not guess.
HA Container/Core-only deployments have no Supervisor app installation path.
Installing builds locally because `image:` is absent; a `docker --load` on this
development machine does not install an app on HA.

Current HA docs (Supervisor >=2026.04) no longer promise an implicit BUILD_FROM;
this recipe does not rely on it. Older Supervisor acceptance of the app label,
mount alias and `manual_only` has not been verified. Record exact versions.
No real installation/start, broker credential access or device control has
been performed by preparing this package. Before a test-system start, verify
the HTTP patch, exact HA/MQTT versions and the device SKU/LAN capability; then
run the SPEC acceptance tests. No full HA acceptance can be inferred from a
successful image build.

Official documentation checked 2026-10-11:

- https://developers.home-assistant.io/docs/apps/tutorial/
- https://developers.home-assistant.io/docs/apps/configuration/
