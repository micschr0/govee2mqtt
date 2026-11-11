# Ordinary builds compile the same authoritative add-on sources.
FROM rust:1.99.1-bookworm@sha256:e6f2cff35d0f309acf8433b4f05878ed77092602c5065cc81801177da0bb3a9c AS source-builder
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \
    && printf '%s\n' 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261107T000000Z bookworm main' > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends cmake pkg-config \
    && rm -rf /var/lib/apt/lists/*
ARG CARGO_PROFILE=verification
ENV CARGO_BUILD_JOBS=2
WORKDIR /context
COPY govee2mqtt_security_local/ .
RUN sha256sum --strict -c SHA256SUMS
WORKDIR /context/local-source
RUN GOVEE_CI_TAG="$(cat ../SOURCE_TAG)" cargo build --locked --profile "$CARGO_PROFILE" --bin govee \
    && cp "target/$CARGO_PROFILE/govee" /context/govee

RUN useradd --uid 1000 --no-create-home --shell /usr/sbin/nologin govee && mkdir /data

FROM gcr.io/distroless/cc-debian12

# Import from builder.
COPY --from=source-builder /etc/passwd /etc/passwd
COPY --from=source-builder /etc/group /etc/group

WORKDIR /app

COPY --from=source-builder /context/govee /app/govee
COPY --from=source-builder /context/local-source/AmazonRootCA1.pem /app/
COPY --from=source-builder --chown=govee:govee /data /data
COPY --from=source-builder /context/local-source/assets /app/assets
COPY --from=source-builder /context/SOURCE.json /app/SOURCE.json
COPY --from=source-builder /context/SHA256SUMS /app/BUILD-INPUT-SHA256SUMS

USER govee:govee
LABEL org.opencontainers.image.source="https://github.com/micschr0/govee2mqtt"
ENV \
  RUST_BACKTRACE=full \
  PATH=/app:$PATH \
  XDG_CACHE_HOME=/data

VOLUME /data

CMD ["/app/govee", \
  "serve", \
  "--govee-iot-key=/data/iot.key", \
  "--govee-iot-cert=/data/iot.cert", \
  "--amazon-root-ca=/app/AmazonRootCA1.pem"]


