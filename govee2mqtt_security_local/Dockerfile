# Build the authoritative sources inside the Home Assistant context.
# No published govee image and no precompiled host binary are inputs.
ARG BUILD_ARCH
FROM ghcr.io/home-assistant/amd64-base-debian:bookworm@sha256:2ac5052621ce75d8af64e07a1c7fe2315c763b21fcd9bbe6843455b3a09ea001 AS runtime-amd64
FROM ghcr.io/home-assistant/aarch64-base-debian:bookworm@sha256:d4b28f55cbd80f6547f95c288cec6106fc7642894905f71928627ee92acf16d0 AS runtime-aarch64

# Runs on TARGET platform: native builder or already configured QEMU.
FROM rust:1.99.1-bookworm@sha256:e6f2cff35d0f309acf8433b4f05878ed77092602c5065cc81801177da0bb3a9c AS source-builder
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \
    && printf '%s\n' 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261107T000000Z bookworm main' > /etc/apt/sources.list \
    && apt-get update \
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
    && printf '%s\n' 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261107T000000Z bookworm main' > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libstdc++6 libssl3 \
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
