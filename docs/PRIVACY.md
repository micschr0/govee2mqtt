# Data and credentials

The bridge processes device information and control commands locally and through
the configured MQTT broker. When cloud functions are enabled, credentials are
sent to Govee for authentication and device requests go to its services.
Cloud credentials remain optional for LAN operation.

The online scene catalog receives the device model (SKU) and does not require
credentials itself. See [cloud opt-in](CONFIG.md#govee-cloud-opt-in) for when
this catalog is used.

Device lists and configuration are cached locally to reduce API calls.
Depending on deployment, cache data and IoT keys live under `/data` or the
add-on configuration directory `/app/config`.

The bridge contains no usage telemetry sent to project maintainers.
Treat credentials, keys, cache files and logs as confidential.
When enabled, the HTTP API exposes data and control functions without
authentication on the configured bind address.

The MQTT connection does not configure TLS: credentials and commands are
visible to anyone able to observe its network traffic. Use a trusted, isolated
network or an independently encrypted tunnel; choosing port 8883 alone does
not enable encryption. LAN discovery is unauthenticated and can be spoofed by
another host on the network. Limit access to trusted devices.

The optional HTTP API also accepts state-changing GET requests without
authentication or CSRF protection. Even a loopback bind can be reached by a
browser visiting an untrusted page. Leave it disabled unless this risk is
acceptable. Restrict access to cache directories: cached account tokens and
IoT credentials may be present, and sharing a cache across accounts can reuse
previous credentials.
