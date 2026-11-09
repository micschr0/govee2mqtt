# Docker

The Compose file uses a locally built fork image. An upstream image does not
include this project's changes.

## Prerequisites

Requires Docker with Buildx, Rust and `cross` for the existing cross-build.
From the repository root, for an amd64 host:

```sh
./scripts/build-docker.sh linux/amd64 --load -t govee2mqtt:local
```

For ARM64, use `linux/arm64`. The script first creates the binary at
`docker-target/<platform>/govee`; running `docker build .` directly requires that
prepared binary. This is a local deployment build, not a publication.

## Configuration

Create a local `.env` and adjust the values:

```dotenv
GOVEE_MQTT_HOST=192.168.1.10
GOVEE_MQTT_PORT=1883
GOVEE_MQTT_USER=govee
GOVEE_MQTT_PASSWORD=replace-me
GOVEE_TEMPERATURE_SCALE=C
TZ=Europe/Berlin
```

LAN devices do not require Govee credentials. Optional:
`GOVEE_EMAIL`, `GOVEE_PASSWORD`, `GOVEE_API_KEY`.
HTTP stays disabled without `GOVEE_HTTP_BIND`. See [configuration](CONFIG.md).
Keep `.env` and persistent data out of Git; they contain sensitive information.

## Start and logs

```sh
docker compose up -d
docker compose logs -f govee2mqtt
```

Host networking enables UDP discovery on Linux. The broker must be reachable
from the host; `localhost` refers to the host here. A Docker service name such as
`mqtt` only works with suitable DNS resolution.
Cache data and IoT keys live in the Docker volume at `/data`.
Network requirements: [LAN](LAN.md).
