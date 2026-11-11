# Disposable add-on build and upgrade checks

Issue #2 delivers this procedure and offline fixture checks. It does not establish
migration acceptance. Issue #1 owns successful candidate packaging on **both**
amd64 and aarch64 and an actual isolated Home Assistant (HA) upgrade.

## Inputs and evidence

Use Linux, Python 3.9+, GNU `timeout`, Docker Engine and Buildx/BuildKit.
Record immutable baseline and candidate Git SHAs, package `SOURCE.json`,
`SOURCE_TAG`, checksums, Docker/Buildx versions, architecture and command exit
codes in private test evidence. Keep full failure logs. Never use production or
real user data. No release script, tag, image push or publication is needed.

Set `BASELINE_PACKAGE` and `CANDIDATE_PACKAGE` to absolute paths of complete,
reviewed add-on packages at those revisions. For today's layout, obtain each
with `git archive <SHA> govee2mqtt_security_local | tar -x -C <new-directory>`;
the package is `<new-directory>/govee2mqtt_security_local`. Do not copy root
sources over the snapshot. For a future #1 layout, use its reviewed package
preparation command and record it. The existing `prepare-local-addon.py` rejects
HEADs other than its pinned baseline; do not remove that guard to make a test run.

Create a fresh run directory outside the checkout:

```sh
RUN_DIR=$(mktemp -d)
cp -R tests/fixtures/addon "$RUN_DIR/before"
cp -R "$RUN_DIR/before" "$RUN_DIR/after"
python3 scripts/verify-addon-fixtures.py "$RUN_DIR/after"
python3 -m unittest discover -s tests -v
```

Expected: `PASS` and unittest `OK`. The CLI compares saved field **types and
values** and both marker bytes, tolerates additional options, and fails with exit
1 for a missing/changed field or marker. Tests deliberately remove `mqtt_port`
and `/data`'s marker. Fixtures contain fake credentials and no `http_bind`;
`mqtt.invalid` cannot be used as a real broker. Never start serve with these
options. For a live smoke run the operator supplies an isolated disposable broker,
keeps its credentials private, and takes a new baseline of those actual options.

## Bounded readiness, before any expensive build

Read the project's runtime recovery notes and private runner configuration first.
Choose `BUILDER` and `TEST_NETWORK` there; no runner-specific paths, packages,
network names or authentication belong in public instructions. Each probe below
has a 60-second outer deadline. Failure or timeout means **readiness failed**:
stop, preserve logs and fix the environment before running a full build.

```sh
timeout 60 docker info
timeout 60 docker buildx inspect "$BUILDER" --bootstrap
timeout 60 docker network inspect "$TEST_NETWORK"
(cd "$BASELINE_PACKAGE" && timeout 60 sha256sum --strict -c SHA256SUMS)
(cd "$CANDIDATE_PACKAGE" && timeout 60 sha256sum --strict -c SHA256SUMS)
```

The builder must run `linux/amd64` and `linux/arm64` natively or with working
QEMU/binfmt, and resolve/pull the applicable pinned FROM images in each package's
Dockerfile with trusted registry CAs. For each platform, probe its Rust base and
matching HA runtime base: `timeout 60 docker pull --platform <platform> <pinned-image>`.
Probe target execution using the matching HA runtime base (set `RUNTIME_BASE` to
its pinned FROM reference and `PLATFORM` to that architecture):

```sh
timeout 60 docker run --rm --platform "$PLATFORM" --network "$TEST_NETWORK" \
  --entrypoint /bin/sh "$RUNTIME_BASE" -ec 'uname -m; test -d /tmp'
timeout 60 docker run --rm --platform "$PLATFORM" --network "$TEST_NETWORK" \
  --mount "type=bind,src=$RUN_DIR/after,dst=/probe" \
  --entrypoint /bin/sh "$RUNTIME_BASE" -ec \
  'test -f /probe/options.json; touch /probe/data/mount-probe; rm /probe/data/mount-probe'
```

Expect `x86_64` or `aarch64` respectively and exit 0. Bind paths must exist on the
Docker daemon host and be writable; mount directories, not single config files.
Build RUN steps also need DNS/TLS access to the pinned Debian snapshot and Cargo
registries, C/C++ tools, CMake and pkg-config (provided by the Dockerfile). Set `RUST_BASE` and `SNAPSHOT_URL` from the package Dockerfile's pinned Rust
FROM and Debian snapshot URL. Probe actual build networking and consecutive RUNs:

```sh
cat > "$RUN_DIR/readiness.Dockerfile" <<'DOCKER'
ARG RUST_BASE
FROM ${RUST_BASE}
ARG SNAPSHOT_URL
WORKDIR /probe
COPY local-source/ ./
RUN test -x /bin/sh
RUN curl --fail --max-time 20 "${SNAPSHOT_URL}/dists/bookworm/Release" -o /tmp/Release \
    && cargo metadata --locked --format-version 1 > /tmp/metadata.json
DOCKER
timeout 60 docker buildx build --builder "$BUILDER" --platform "$PLATFORM" \
  --build-arg "RUST_BASE=$RUST_BASE" --build-arg "SNAPSHOT_URL=$SNAPSHOT_URL" \
  --file "$RUN_DIR/readiness.Dockerfile" "$CANDIDATE_PACKAGE"
```

Repeat for both platforms and any baseline with different pinned inputs.
The builder's build network must be provisioned in private configuration.
Keep probe logs private. A manifest
inspection alone does not prove target execution or working build mounts.

The `--help` smoke below uses `--network none` and needs no published port.
A later live HA run needs host networking/LAN permissions, AppArmor support,
Supervisor-managed writable `/data` and `addon_config` mounts, MQTT service and
its actual published MQTT endpoint reachable. Before that run, the operator
performs a bounded MQTT CONNECT/CONNACK probe with the actual fixture broker and
credentials and checks Supervisor reachability. TCP reachability alone is not
MQTT acceptance. Readiness success never counts as packaging or upgrade success.

## Verification-profile builds, baseline then candidate

The current package Dockerfile hardcodes `--release`. Use **disposable copies**
with a separate Cargo `verification` profile; never modify either input package.
The following prepares both contexts, verifies their original integrity, and
recomputes only the scratch manifest after the explicit profile changes:

```sh
export RUN_DIR BASELINE_PACKAGE CANDIDATE_PACKAGE
python3 - <<'PY'
import hashlib, os, pathlib, shutil, subprocess
for role in ('baseline', 'candidate'):
    source = pathlib.Path(os.environ[role.upper() + '_PACKAGE'])
    subprocess.run(['sha256sum', '--strict', '-c', 'SHA256SUMS'], cwd=source, check=True)
    target = pathlib.Path(os.environ['RUN_DIR']) / role
    shutil.copytree(source, target)  # Refuses an existing destination.
    dockerfile = target / 'Dockerfile'
    text = dockerfile.read_text()
    assert text.count('cargo build --locked --release --bin govee') == 1
    assert text.count('target/release/govee') == 1
    text = text.replace('cargo build --locked --release --bin govee',
                        'cargo build --locked --profile verification --bin govee')
    dockerfile.write_text(text.replace('target/release/govee', 'target/verification/govee'))
    cargo = target / 'local-source/Cargo.toml'
    with cargo.open('a') as stream:
        stream.write('\n[profile.verification]\ninherits = "dev"\ndebug = 0\nincremental = false\n')
    manifest = target / 'SHA256SUMS'
    names = [line.split('  ', 1)[1] for line in manifest.read_text().splitlines()]
    manifest.write_text(''.join(hashlib.sha256((target / n).read_bytes()).hexdigest()
                               + '  ' + n + '\n' for n in names))
PY
```

Expect two new contexts; a changed Dockerfile shape or an existing verification
profile fails rather than silently using release. Under #1, adapt this preparation
to its reviewed layout and retain the separate profile. `SOURCE.json` still
identifies the **original input**; scratch checksums describe the modified test
context. Neither directory is a distributable package or release artifact; use them only for local tests.

Run each role and architecture separately, saving stdout/stderr and the exit
code for each invocation. Do not hide a build failure behind `tee` without
`set -o pipefail`. Example in Bash, repeated for both roles and architectures:

```sh
ROLE=baseline # Repeat with candidate.
ARCH=amd64    # Repeat with aarch64.
PLATFORM=linux/amd64
# For ARCH=aarch64 set PLATFORM=linux/arm64.
IMAGE="govee-addon-verify:$ROLE-$ARCH"
docker buildx build --builder "$BUILDER" --platform "$PLATFORM" --load \
  --build-arg "BUILD_ARCH=$ARCH" --build-arg BUILD_VERSION=verification \
  --progress plain --tag "$IMAGE" "$RUN_DIR/$ROLE"
timeout 60 docker run --rm --platform "$PLATFORM" --network none \
  --entrypoint /app/govee "$IMAGE" --help
```

Expect build exit 0, a locally loaded image for the selected architecture, and
help text with exit 0 (no serve, no broker, no credentials). Inspect with
`docker image inspect "$IMAGE" --format '{{.Architecture}}'`; expect `amd64` or
`arm64`. Preserve image IDs and scratch input hashes. A passing baseline or a
native-only run does not pass the candidate matrix. This profile checks source,
loader, libraries and packaging; it does not measure release performance.

## Isolated Supervisor baseline, upgrade and reset

**Availability: pending; no isolated HA target has been designated.** The
repository owner provides/designates the target **and is the test operator**.
Keep address, host paths, tokens and broker credentials in private configuration.
If an API tool is used, its credential key is `SUPERVISOR_TOKEN`; never log it.
A plain Docker `--help` run cannot validate Bashio or Supervisor upgrade behavior.

1. The owner records the disposable target's HA OS/Supervisor and CLI versions,
   architecture and reset snapshot. Confirm no production devices or user data.
   Use `ha apps --help` (older CLI: `ha addons --help`) and `ha store --help`
   to check installed syntax.
2. Copy the **baseline verification context** from `$RUN_DIR/baseline`
   into the target's local apps directory as `govee2mqtt_security_local`. Reload
   the store (`ha store reload`). Expect config slug `govee2mqtt_security_local`
   and installed local slug `local_govee2mqtt_security_local`. A remote repository
   prefix differs; do not switch repositories midway through this test.
3. Install with `ha apps install local_govee2mqtt_security_local`. Expect the
   baseline version from `config.yaml`/`SOURCE_TAG`, both declared architectures,
   manual boot, host network, AppArmor, HTTP off and no registry `image` key.
4. On the Configuration tab apply disposable fixture options (substitute the
   isolated broker). Save and read back via the tab or Supervisor info API.
   Store the resulting options as private `before/options.json`. Never include
   actual values in public evidence. Do not enable HTTP for this test.
5. Start and stop the baseline once to create its container. Through the owner's
   private target access, copy the two fixture markers into
   the installed container at `/data/persistence-marker.txt` and
   `/app/config/persistence-marker.txt`. Confirm `/app/config` is the writable
   `addon_config` mapping. Copy both back to `before/data/` and
   `before/addon_config/`. `/data` and `/app/config` are distinct persistent mounts.
6. Start (`ha apps start local_govee2mqtt_security_local`), inspect logs privately,
   expect successful isolated MQTT connection, then stop (`ha apps stop ...`,
   replacing `...` with the full slug). Confirm options and both markers remain.
7. Replace only the local **package files** with `$RUN_DIR/candidate`,
   keeping slug and persistent mounts. Both are disposable verification builds. Reload the store. Use the UI Update action
   when a new version is offered; otherwise use
   `ha apps rebuild --force local_govee2mqtt_security_local` for a local rebuild.
   Expect candidate version/source identity; never uninstall between versions.
8. Start the candidate and read back options and both marker files to private
   `after/` with the same structure as `before/`. Run the comparison CLI against
   the saved baseline with
   `python3 scripts/verify-addon-fixtures.py after --baseline before`. Expect no option or marker loss,
   correct mount destinations, HTTP still off, MQTT connected and no new errors.
9. Save command exits, versions, architecture and redacted results. Record
   packaging and live upgrade independently as pass/fail/pending. A failure stays
   failed even if readiness passed. #1 may claim upgrade acceptance only after
   this actual installation and upgrade have completed.
10. Stop only the test add-on. Restore the owner's disposable target snapshot
    for repeat runs (or uninstall only this local test slug and remove its local
    package directory using the owner's test access). Remove only identified
    run-owned images/directories after evidence is retained. Never prune shared
    Docker state. Restore baseline before testing the next candidate.

Reference semantics: [HA testing](https://contributors.home-assistant.io/apps/guides/testing/),
[HA configuration/mounts](https://contributors.home-assistant.io/apps/reference/configuration/),
[Supervisor app API](https://contributors.home-assistant.io/apps/supervisor-api/apps/),
[HA CLI store reload](https://github.com/home-assistant/cli/blob/master/cmd/store_reload.go),
and [Buildx platform/load](https://docs.docker.com/reference/cli/docker/buildx/build/).
The [Cargo profile reference](https://doc.rust-lang.org/cargo/reference/profiles.html)
defines custom profiles and their required `inherits` setting.
