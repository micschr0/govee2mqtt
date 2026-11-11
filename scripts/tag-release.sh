#!/bin/sh
# This script sets things up to make a release,
# creating a tag based on the current commit.
TAG_NAME=${TAG_NAME:-$(git -c "core.abbrev=8" show -s "--format=%cd-%h" "--date=format:%Y.%m.%d")}
git tag $TAG_NAME
./scripts/apply-tag.sh
docker run -t -v "$(pwd)":/app/ "ghcr.io/orhun/git-cliff/git-cliff:${TAG:-latest}" -o govee2mqtt_security_local/CHANGELOG.md -c scripts/cliff.toml
python3 scripts/check-store-source.py --write
git add govee2mqtt_security_local/config.yaml govee2mqtt_security_local/CHANGELOG.md \
  govee2mqtt_security_local/SOURCE.json govee2mqtt_security_local/SOURCE_TAG \
  govee2mqtt_security_local/SHA256SUMS govee2mqtt_security_local/.dockerignore
git commit -m "Tag $TAG_NAME"
