# Data and credentials

The bridge processes device information and control commands locally and through
the configured MQTT broker. When cloud functions are enabled, credentials are
sent to Govee for authentication and device requests go to its services.
Cloud credentials remain optional for LAN operation.

The online scene catalog receives the device model (SKU) and does not require
credentials itself. See [cloud opt-in](CONFIG.md#govee-cloud-opt-in) for when
this catalog is used.

Cloud metadata is cached locally to reduce API calls. The Docker and Home
Assistant packages store `govee2mqtt-cache-v2.sqlite` under `/data` by default.
The cache separates entries by configured account or API key. Login results
and downloaded IoT key material are not stored in this database; cloud account
login is refreshed after a restart. IoT also writes a certificate and private
key to separate files (`/dev/shm` by default).

The old `govee2mqtt-cache.sqlite` is not migrated or removed. It and its
SQLite sidecar files may still contain credentials. Keep them private and
remove them only after verifying the upgrade and deciding they are no longer
needed for rollback. Treat cache files, keys, configuration and logs as
confidential. The bridge sends no usage telemetry to project maintainers.

[MQTT TLS](CONFIG.md#mqtt-configuration) is optional. Without it, use a
trusted, isolated network or an encrypted tunnel. Choosing port 8883 alone does
not enable encryption. [LAN discovery](LAN.md) still cannot authenticate
responses, even when MQTT uses TLS.

The optional [HTTP API](CONFIG.md#http-api-and-webui) has no authentication.
Its browser checks do not restrict direct clients. Leave it disabled unless
needed, prefer loopback and never expose it to an untrusted network.
