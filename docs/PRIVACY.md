# Data and credentials

The bridge processes device information and control commands locally and through
the configured MQTT broker. When cloud functions are enabled, credentials are
sent to Govee for authentication and device requests go to its services.
Cloud credentials remain optional for LAN operation.

Device lists and configuration are cached locally to reduce API calls.
Depending on deployment, cache data and IoT keys live under `/data` or the
add-on configuration directory `/app/config`.

The bridge contains no usage telemetry sent to project maintainers.
Treat credentials, keys, cache files and logs as confidential.
When enabled, the HTTP API exposes data and control functions without
authentication on the configured bind address.
