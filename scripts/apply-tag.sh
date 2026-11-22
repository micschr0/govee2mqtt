#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
: "${TAG_NAME:?Set TAG_NAME to the approved release version}"
case "$TAG_NAME" in
    [!0-9]* | *[!0-9a-zA-Z._+-]*) echo "Invalid add-on version." >&2; exit 1 ;;
esac
sed -i "s/^version:.*/version: \"$TAG_NAME\"/" govee2mqtt_security_local/config.yaml

python3 scripts/check-store-source.py --write
