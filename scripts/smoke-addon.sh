#!/bin/sh
# Called under timeout by verify-packaging.sh.
set -eu
platform=$1
image=$2

# The shipped Bashio reads options from the Supervisor API.
options='{"result":"ok","data":{"mqtt_host":"127.0.0.1","mqtt_port":21883,"no_multicast":true}}'
fixture=$(docker run -d --network none --platform "$platform" --entrypoint s6-tcpserver \
    "$image" 127.0.0.1 80 sh -ec '
        read -r method path _
        [ "$method $path" = "GET /addons/self/options/config" ]
        printf "HTTP/1.0 200 OK\r\nContent-Length: %s\r\n\r\n%s" "${#1}" "$1"
        cat >/dev/null
    ' sh "$options")
addon=
trap '
    if [ "$?" -ne 0 ] && [ -n "$addon" ]; then
        docker logs --tail 50 "$addon" >&2 || :
    fi
    docker rm -fv ${addon:+"$addon"} "$fixture" >/dev/null
' EXIT
trap 'exit 1' INT TERM

until docker exec "$fixture" curl -fsS http://127.0.0.1/addons/self/options/config >/dev/null; do
    sleep 1
done
addon=$(docker run -d --network "container:$fixture" --platform "$platform" \
    --env SUPERVISOR_API=http://127.0.0.1 "$image")
while [ "$(docker inspect --format '{{.State.Running}}' "$addon")" = true ]; do
    if docker logs "$addon" 2>&1 | grep -Fq 'Attempting connection to mqtt broker 127.0.0.1:21883...'; then
        echo "PASS: add-on launcher started the bridge with the fixture MQTT endpoint"
        exit 0
    fi
    sleep 1
done
echo "Add-on exited before the bridge attempted MQTT" >&2
exit 1
