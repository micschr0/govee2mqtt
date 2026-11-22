#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

: "${TAG_NAME:?Set TAG_NAME to the approved release version}"
export TAG_NAME
git check-ref-format "refs/tags/$TAG_NAME"
if [ -n "$(git status --porcelain)" ] || git show-ref --verify --quiet "refs/tags/$TAG_NAME"; then
    echo "Release requires a clean checkout and an unused tag." >&2
    exit 1
fi

git cliff --tag "$TAG_NAME" --output govee2mqtt_security_local/CHANGELOG.md \
    --config scripts/cliff.toml
./scripts/apply-tag.sh
python3 scripts/check-store-source.py
git add govee2mqtt_security_local/config.yaml govee2mqtt_security_local/CHANGELOG.md \
  govee2mqtt_security_local/SOURCE.json govee2mqtt_security_local/SOURCE_TAG \
  govee2mqtt_security_local/SHA256SUMS govee2mqtt_security_local/.dockerignore
git commit -m "Tag $TAG_NAME"
git tag -- "$TAG_NAME"
