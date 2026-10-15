# Local source build only. Prepare with scripts/prepare-local-addon.py.
# No published govee image and no precompiled host binary are inputs.
ARG BUILD_ARCH
FROM ghcr.io/home-assistant/amd64-base-debian:bookworm@sha256:7da3f90a8e2fdc3095cc93b0dfb751c9c21356e11b30a6493c7ac15270b4e809 AS runtime-amd64
FROM ghcr.io/home-assistant/aarch64-base-debian:bookworm@sha256:68f4c1a11d10facc5442ff11509a164463f98b154c80dc1dfeedbc267dd71665 AS runtime-aarch64

# Runs on TARGET platform: native builder or already configured QEMU.
FROM rust:1.94.0-bookworm@sha256:365468470075493dc4583f47387001854321c5a8583ea9604b297e67f01c5a4f AS source-builder
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \
    && printf '%s\n' 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261010T000000Z bookworm main' > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends cmake pkg-config \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /context
COPY . .
RUN sha256sum --strict -c SHA256SUMS
WORKDIR /context/local-source
RUN GOVEE_CI_TAG="$(cat ../SOURCE_TAG)" cargo build --locked --release --bin govee

FROM runtime-${BUILD_ARCH}
ARG BUILD_ARCH
ARG BUILD_VERSION
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \
    && printf '%s\n' 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261010T000000Z bookworm main' > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libstdc++6 libssl3 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=source-builder /context/local-source/target/release/govee /app/govee
COPY --from=source-builder /context/local-source/assets /app/assets
COPY --from=source-builder /context/local-source/AmazonRootCA1.pem /app/AmazonRootCA1.pem
COPY --from=source-builder /context/SOURCE.json /app/SOURCE.json
COPY --from=source-builder /context/SHA256SUMS /app/BUILD-INPUT-SHA256SUMS
COPY --from=source-builder /context/run.sh /run.sh
# Check target loader/shared libraries without starting serve.
RUN chmod 0755 /run.sh && /app/govee --help > /dev/null
LABEL io.hass.type="app" io.hass.arch="${BUILD_ARCH}" io.hass.version="${BUILD_VERSION}"
CMD ["/run.sh"]
