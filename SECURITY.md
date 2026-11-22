# Security

Report suspected vulnerabilities privately via **Security → Report a
vulnerability** on [GitHub](https://github.com/micschr0/govee2mqtt/security).
If that button is unavailable, open an issue requesting a private contact
channel without describing the vulnerability. Keep credentials, device IDs,
logs and network details out of public issues.

HTTP and the WebUI are disabled by default. If enabled, they are
unauthenticated. Prefer a loopback bind and do not expose them to the internet.
See [configuration](docs/CONFIG.md) and [data and credentials](docs/PRIVACY.md).
