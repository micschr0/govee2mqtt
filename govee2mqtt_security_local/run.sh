#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

export RUST_BACKTRACE=full
export RUST_LOG_STYLE=always
export XDG_CACHE_HOME=/data

wait_for_mqtt() {
  local max_attempts=30
  local attempt=1
  local host port

  bashio::log.info "mqtt_host was not explicitly configured, waiting for the Mosquitto broker Add-on to become available"

  while [ $attempt -le $max_attempts ]; do
    if bashio::services.available mqtt &&
      host="$(bashio::services mqtt host)" &&
      port="$(bashio::services mqtt port)" &&
      timeout 2 bash -c 'exec 3<>"/dev/tcp/$1/$2"' bash "$host" "$port" 2>/dev/null; then
      bashio::log.info "MQTT broker is ready!"
      return 0
    fi

    bashio::log.info "MQTT broker not ready yet (attempt ${attempt}/${max_attempts}), waiting 2 seconds..."
    sleep 2
    attempt=$((attempt + 1))
  done

  bashio::log.error "MQTT broker did not become available after ${max_attempts} attempts"
  return 1
}

set_option() {
  if bashio::config.has_value "$1"; then
    local value
    value="$(bashio::config "$1")" || bashio::exit.nok "Cannot read add-on option $1"
    export "$2=$value"
  fi
}

if bashio::config.has_value mqtt_host; then
  set_option mqtt_host GOVEE_MQTT_HOST
else
  if ! wait_for_mqtt; then
    bashio::exit.nok "Mosquitto MQTT broker is not available"
  fi
  GOVEE_MQTT_HOST="$(bashio::services mqtt host)" &&
    GOVEE_MQTT_PORT="$(bashio::services mqtt port)" &&
    GOVEE_MQTT_USER="$(bashio::services mqtt username)" &&
    GOVEE_MQTT_PASSWORD="$(bashio::services mqtt password)" ||
    bashio::exit.nok "Cannot read the MQTT service configuration"
  export GOVEE_MQTT_HOST GOVEE_MQTT_PORT GOVEE_MQTT_USER GOVEE_MQTT_PASSWORD
fi

set_option mqtt_port GOVEE_MQTT_PORT
set_option mqtt_username GOVEE_MQTT_USER
set_option mqtt_password GOVEE_MQTT_PASSWORD
set_option http_bind GOVEE_HTTP_BIND
set_option debug_level RUST_LOG
set_option govee_email GOVEE_EMAIL
set_option govee_password GOVEE_PASSWORD
set_option govee_api_key GOVEE_API_KEY
set_option no_multicast GOVEE_LAN_NO_MULTICAST
set_option broadcast_all GOVEE_LAN_BROADCAST_ALL
set_option global_broadcast GOVEE_LAN_BROADCAST_GLOBAL
set_option scan GOVEE_LAN_SCAN
set_option temperature_scale GOVEE_TEMPERATURE_SCALE

cd /app || bashio::exit.nok "Cannot enter the application directory"
exec /app/govee serve
