# Security and acceptance

The fork disables HTTP by default. An explicit `http_bind` enables the API,
which still has no authentication; see [configuration](../CONFIG.md).
Cloud credentials are optional for LAN control.

The following documents preserve requirements and evidence from the security
project. Dates, commits and approvals refer to their recorded state, not
automatically to the current development tree.

- [SPEC.md](SPEC.md): requirements, scope and baseline.
- [TEST-MATRIX.md](TEST-MATRIX.md): test cases, results and evidence.

Real HA/MQTT/device acceptance is partly pending. Passing local tests or package
checksums does not replace these checks.
The versioned store package is in `govee2mqtt_security_local/`;
[development](../DEVELOPMENT.md) explains source trees and export constraints.
