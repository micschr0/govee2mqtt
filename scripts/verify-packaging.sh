#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

case "${1:-}" in
    amd64) platform=linux/amd64; architecture=amd64 ;;
    aarch64) platform=linux/arm64; architecture=arm64 ;;
    *) echo "Usage: $0 amd64|aarch64" >&2; exit 2 ;;
esac

python3 scripts/check-store-source.py
version=$(cat govee2mqtt_security_local/SOURCE_TAG)
for kind in ordinary addon; do
    image="govee-verification:$kind-$architecture-$$"
    if [ "$kind" = ordinary ]; then
        bash scripts/build-docker.sh "$platform" --load --progress plain -t "$image"
    else
        docker buildx build --platform "$platform" --load --progress plain \
            --build-arg "BUILD_ARCH=$1" --build-arg "BUILD_VERSION=$version" \
            --build-arg CARGO_PROFILE=verification -t "$image" govee2mqtt_security_local
        test "$(docker image inspect "$image" --format '{{ index .Config.Labels "io.hass.version" }}')" = "$version"
    fi
    test "$(docker image inspect "$image" --format '{{.Architecture}}')" = "$architecture"
    docker image inspect "$image" --format '{{.Id}}'
    actual=$(timeout 60 docker run --rm --platform "$platform" --network none \
        --entrypoint /app/govee "$image" --version)
    test "$actual" = "govee $version"
    timeout 60 docker run --rm --platform "$platform" --network none \
        --entrypoint /app/govee "$image" --help
done
