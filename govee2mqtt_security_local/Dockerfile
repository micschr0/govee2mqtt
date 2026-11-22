# Build the authoritative sources inside the Home Assistant context.
# No published govee image and no precompiled host binary are inputs.
ARG BUILD_ARCH
FROM ghcr.io/home-assistant/amd64-base-debian:trixie@sha256:a2a09d3983b771953c53a3a8c871f2c1d6d28bcf0ebaab09bc0eb80ffa5f4041 AS runtime-amd64
FROM ghcr.io/home-assistant/aarch64-base-debian:trixie@sha256:3f64e58a4169792bdb28ae0a587cc26030a242e95ac3b76fe8f35a28fee7072d AS runtime-aarch64

# Runs on TARGET platform: native builder or already configured QEMU.
FROM rust:1.100.0-trixie@sha256:223cc32ddca8f3ee90c436dbc94b6b5f052ea7f9653c5201e9612f08ad7d21b8 AS source-builder
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \
    && printf '%s\n' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261122T000000Z trixie main' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261122T000000Z trixie-updates main' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20261122T000000Z trixie-security main' \
        > /etc/apt/sources.list \
    && apt-get -o APT::Update::Error-Mode=any update \
    && apt-get install -y --no-install-recommends cmake pkg-config \
    && rm -rf /var/lib/apt/lists/*
ARG CARGO_PROFILE=verification
ENV CARGO_BUILD_JOBS=2
WORKDIR /context
COPY . .
RUN sha256sum --strict -c SHA256SUMS
WORKDIR /context/local-source
RUN GOVEE_CI_TAG="$(cat ../SOURCE_TAG)" cargo build --locked --profile "$CARGO_PROFILE" --bin govee \
    && cp "target/$CARGO_PROFILE/govee" /context/govee

FROM runtime-${BUILD_ARCH}
ARG BUILD_ARCH
ARG BUILD_VERSION
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \
    && printf '%s\n' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261122T000000Z trixie main' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261122T000000Z trixie-updates main' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20261122T000000Z trixie-security main' \
        > /etc/apt/sources.list \
    && apt-get -o APT::Update::Error-Mode=any update \
    && apt-get install -y --no-install-recommends ca-certificates libstdc++6 libssl3t64 zlib1g \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=source-builder /context/govee /app/govee
COPY --from=source-builder /context/local-source/assets /app/assets
COPY --from=source-builder /context/local-source/AmazonRootCA1.pem /app/AmazonRootCA1.pem
COPY --from=source-builder /context/SOURCE.json /app/SOURCE.json
COPY --from=source-builder /context/SHA256SUMS /app/BUILD-INPUT-SHA256SUMS
COPY --from=source-builder /context/run.sh /run.sh
# Check target loader/shared libraries without starting serve.
RUN chmod 0755 /run.sh && /app/govee --help > /dev/null
LABEL io.hass.type="app" io.hass.arch="${BUILD_ARCH}" io.hass.version="${BUILD_VERSION}"
CMD ["/run.sh"]
