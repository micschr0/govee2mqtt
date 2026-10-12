# Security fork specification

This fork's security work is specified and acceptance-tested against a
versioned specification. The authoritative working copies live in the
development workspace; these snapshots are published for traceability.

- `SPEC.md` — requirements (SEC-01/SEC-02, MQTT-01, LAN-01, ROB-01),
  scope, baseline and authorization records. Commit messages in
  `security/http-opt-in` reference these requirement IDs.
- `TEST-MATRIX.md` — local verification matrix (LOCAL-0x, PKG-0x) with
  evidence references. Real HA/device acceptance is tracked as OPEN;
  no real acceptance is claimed as passed.

Internal coordination documents (DECISIONS, WORKBOARD, handover notes)
stay in the development workspace: they contain operational and
infrastructure context that is not part of the published repository.

The add-on app in `govee2mqtt_security_local/` is the local source-build
export; see its `DOCS.md` for build/install limits.
