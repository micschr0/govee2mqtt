#!/bin/bash
set -euo pipefail
TARGETPLATFORM=${1:?Usage: build-docker.sh linux/amd64|linux/arm64 [buildx options]}
shift
case "$TARGETPLATFORM" in
  linux/amd64|linux/arm64) ;;
  *) echo "Unsupported platform: $TARGETPLATFORM" >&2; exit 1 ;;
esac
cd "$(dirname "$0")/.."
python3 scripts/check-store-source.py
docker buildx build --platform "$TARGETPLATFORM" --build-arg CARGO_PROFILE=verification "$@" .
