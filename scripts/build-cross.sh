#!/bin/bash
set -e
set -x

TARGETPLATFORM=$1

case "$TARGETPLATFORM" in
  "linux/amd64")
    TARGET=x86_64-unknown-linux-musl
    ;;
  "linux/arm64")
    TARGET=aarch64-unknown-linux-musl
    ;;
  *)
    echo "$TARGETPLATFORM needs to map to a rust target";
    exit 1
    ;;
esac

SOURCE_DIR=govee2mqtt_security_local/local-source
cross build --manifest-path "$SOURCE_DIR/Cargo.toml" --target "$TARGET" --locked --profile verification --bin govee

mkdir -p docker-target/$TARGETPLATFORM
cp "${CARGO_TARGET_DIR:-$SOURCE_DIR/target}/$TARGET/verification/govee" "docker-target/$TARGETPLATFORM"

