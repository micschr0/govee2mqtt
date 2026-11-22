# Operator acceptance for the regular store app

Run this on a disposable Home Assistant OS/Supervisor instance that you control,
not production. Use only a disposable MQTT broker and synthetic options and data.
The maintainer performs all Supervisor, network and device steps. For
`2026.11.23` the published experimental baseline is `2026.11.22` at
`5769efa74ac67bd17f9b204fb79249c5ca063f50`. Use the full candidate SHA from the
CI handoff, never a moving branch head. Copy the [evidence template](manual-acceptance.md)
and record versions, architecture, dated results and redacted evidence separately.

## Serve both exact trees without changing the app ID

1. Keep the Supervisor's configured repository URL exactly
   `https://github.com/micschr0/govee2mqtt` (no `.git` or branch suffix). Verify
   the full app ID `5f8616cb_govee2mqtt_security_local` before each step. A
   local app, a branch URL or a differently spelled repository can be useful
   for rehearsal, but does not pass this gate.
2. Prepare an access-controlled Git mirror reachable only by the disposable host.
   Verify both commit IDs and their package checksums
   (`python3 scripts/check-store-source.py --store <archived-app-directory>`).
   Set the mirror's default branch `main` to the exact baseline; keep the exact
   candidate commit available without changing the public repository. Both
   objects must be unmodified and the mirror must retain the baseline for recovery.
3. In a Supervisor test environment that allows Git configuration, use an
   exact URL rewrite (`url.<private-mirror-URL>.insteadOf` with the registered
   URL as its value) for the **Supervisor's Git process only**. Use normal
   HTTPS TLS trust, no authentication bypass and no global DNS/TLS change.
   From that Git environment, `git ls-remote <registered-store-URL> refs/heads/main`
   must return the baseline SHA. The mirror preserves the configured store
   URL and therefore the Supervisor ID; manually replacing the cache or
   changing its `origin` is not equivalent. Supervisor 2026.11.0
   [synchronizes `origin` and fetches the current branch](https://github.com/home-assistant/supervisor/blob/2026.11.0/supervisor/store/git.py).
   If your target cannot safely route the registered URL, stop: a local-app
   rehearsal cannot stand in for this regular-ID upgrade.

## Update and restore under the same ID

1. Reload the store, install and start the baseline from the regular store
   entry. Confirm the full ID, version and working MQTT. Save typed options
   and distinct byte markers under `/data` and `/app/config` as described in
   [the fixture procedure](../ADDON-VERIFICATION.md#isolated-supervisor-baseline-upgrade-and-reset).
   Record existing Home Assistant entity IDs, MQTT discovery unique IDs, and
   the Supervisor Start on boot setting. Take a full restorable baseline
   snapshot, including the MQTT/HA state used for the test, and keep the
   baseline package and its checksums.
2. Move **only the private mirror's** `main` to the candidate without changing
   the configured URL or app options. Check `git ls-remote` in the Supervisor
   environment for the candidate SHA, reload the store, and verify the exact
   candidate version is offered for the existing full app ID. Select
   **Update**, not **Rebuild**, and never uninstall. Record the installed App
   version, the build's source metadata and startup log version.
3. Read back options and both mounts. Run
   `python3 scripts/verify-addon-fixtures.py <after> --baseline <before>`
   with your private observations. Confirm MQTT reconnects, the existing
   entity IDs remain and no duplicate entities appear. Confirm the saved
   Start on boot override was preserved; enable it if necessary, reboot the
   entire test host, and verify automatic start and MQTT reconnection without
   manual intervention. If testing disabled startup, restore the saved setting
   afterwards. Record each result against the candidate.
4. While the candidate is installed, perform the device tests below. Then stop
   the test bridge, restore the mirror to the baseline and restore the full
   baseline snapshot. Confirm the original app ID/version, options, both
   marker files, MQTT/entity identity and the original boot setting. Leave the
   test host restored and remove the test-only URL rewrite. An image-only
   rollback or a reinstall is not a restoration result.

## Device acceptance and reporting

1. Use a supported lamp with LAN enabled and record model and firmware. With
   credentials unset, establish physical on/off, brightness and one supported
   color or color-temperature control via Home Assistant.
2. Block internet (IPv4 and IPv6) for both bridge and device while preserving
   LAN and MQTT. Verify isolation, restart the bridge offline and repeat the
   same physical controls. Record device-originated readback when available;
   do not count MQTT echo or optimistic state as physical proof.
3. On the disposable setup, explicitly opt into cloud and make the opted-in
   cloud services unreachable, including during a cold bridge start. Verify
   MQTT and the same LAN controls during the outage. Restore the route and
   record LAN continuity and cloud recovery separately. Restore network and
   credential settings. Independent H60C1 zones are out of scope.
4. Enable **Private vulnerability reporting** in GitHub repository settings
   and verify **Security → Report a vulnerability** is available. Do not
   submit a fake vulnerability. Return the redacted test evidence with the
   commit, CalVer, architecture, app ID, Supervisor version and rollback
   outcome. Until then, these gates are pending, not passed.
