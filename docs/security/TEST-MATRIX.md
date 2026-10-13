# Test-Matrix – govee2mqtt-Security-Fork

Stand: 2026-10-13 · Version: 1.1 · Status: PRÜFPLAN FREIGEGEBEN; ABNAHMEN OFFEN

Jede Zeile verknüpft eine Anforderung mit einem Szenario, einer Prüfmethode
und dem Nachweis. Eine Anforderung gilt erst als erfüllt, wenn Evidenz vorliegt.

## Abnahmen

| Req | Szenario | Prüfmethode | Ergebnis | Evidenz |
|-----|----------|-------------|----------|---------|
| SEC-01 | Dienst startet ohne HTTP-Opt-in; MQTT verbunden; LAN-Gerät schaltet | Test: Port-Scan + MQTT-Verifikation + Schalttest | OFFEN | – |
| SEC-01 | Dienst läuft stabil über 5 Minuten ohne HTTP-Listener | Test: Prozess-Monitoring | LOKAL PASS; HA-Zielumgebung OFFEN | [300 Sekunden](evidence/patch-smoke.json) |
| SEC-02 | HTTP-Opt-in gesetzt; Listener startet nur auf konfigurierter Adresse | Test: Konfiguration + Port-Bind prüfen | CLI/ENV LOKAL PASS; HA-App OFFEN | [Bind-/API-Prüfung](evidence/patch-smoke.json) |
| SEC-02 | HTTP-Opt-in nicht gesetzt; kein Listener trotz Neustart | Test: Neustart + Port-Scan | LOKAL PASS; HA-App OFFEN | [Neustart](evidence/patch-smoke.json) |
| MQTT-01 | Discovery-Payload identisch mit Upstream-Baseline | Vergleich: MQTT-Payload-Diff | OFFEN | – |
| MQTT-01 | Neuinstallation erzeugt die erwarteten Entities; Neustart erzeugt keine Duplikate | Test: Discovery und HA-Entity-Zählung bei Erststart und Neustart | OFFEN | – |
| LAN-01 | LAN-Gerät schaltet ohne Cloud-Zugangsdaten | Test: Gerät ohne GOVEE_*_ENV schalten | OFFEN | – |
| LAN-01 | LAN-Gerät schaltet ohne Internetverbindung | Test: Netz isolieren, Gerät schalten | OFFEN | – |
| ROB-01 | Dienst läuft weiter, wenn Cloud nicht erreichbar | Test: DNS/Route zur Cloud blockieren | OFFEN | – |
| ROB-01 | Dienst crash-loopt nicht bei wiederholtem Cloud-Ausfall | Test: Mehrfacher Ausfall simulieren | OFFEN | – |
| CLOUD-01 | 454 vom Primär-Login → Fallback auf Community-Login; Unit-Tests JWT/454-Erkennung; lokale Suite grün | Test: `cargo test` (49 PASS inkl. 7 neuer PR-Tests), clippy `-D warnings` clean, fmt clean, Smoke 9/9 PASS am gepatchten Baum | LOKAL PASS (Commit `458c2e5`) | [patch-smoke.json](evidence/patch-smoke.json); Testlauf 13.10. 23:2x |
| CLOUD-01 | E2E: Start mit echten Govee-Credentials trotz 2FA-Mauer im Test-HA; Log zeigt Fallback-Warnung; H60C1 steuerbar | Demonstration am Test-HA | OFFEN | – |

## Prüfarten

- **Test:** Automatisierter Test oder reproduzierbare manuelle Prüfung
- **Demonstration:** Sichtbare Ausführung am vereinbarten Gerät
- **Inspektion:** Code-Lesung mit dokumentiertem Befund
- **Analyse:** Schlussfolgerung aus Code oder Konfiguration

## Voraussetzungen

- [x] TBD-01 geklärt: konkretes Gerät benannt — Govee Pendelleuchte **H60C1** (Variante 51797089779896, 11.10. 23:16); LAN-API laut HA-Local-API-Doku unterstützt; LAN-Schalter in Govee-App + UDP-Erreichbarkeit bleiben Abnahmevorbedingung
- [x] TBD-02 Nutzerangabe erfasst: neueste HA-Version, Mosquitto Broker 7.1.1
- [ ] Exakte HA-Core-/Supervisor- und Broker-Daemon-/App-Versionen im Testnachweis protokolliert
- [x] TBD-05 geklärt: Upstream-Baseline 6f5a8449ca63da8bdc7cc696288a993681ff2a69 (SPEC v0.3)
- [x] Lokaler Entwicklungscheckout mit lauffähigem Build vorhanden (Fork `micschr0/govee2mqtt` seit 12.10. veröffentlicht: Branch-Push per Freigabe A, fork-main per Freigabe 23:02 als lokale HA-Store-Quelle)

## Änderungshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 0.1 | 2026-10-11 | Erster Entwurf |
| 0.2 | 2026-10-11 | LOCAL-07 nach Clippy-Bereinigung aktualisiert; LOCAL-08 bis LOCAL-11 ergänzt |
| 0.3 | 2026-10-11 | Autonomer Vollständigkeitspass: LOCAL-12/LOCAL-13 ergänzt (Astra ASTRA-06/09), Grenzen aktualisiert |
| 0.4 | 2026-10-11 | F2-Commit `59d3b12` auf `security/http-opt-in` dokumentiert (Branchstatus; kein Push) |
| 0.5 | 2026-10-11 | TBD-01 erledigt: Gerät H60C1 benannt (F1-Antwort); Abnahmevorbedingung LAN-Enablement dokumentiert |
| 0.6 | 2026-10-12 | WB-17 (F5) umgesetzt: LOCAL-14 ergänzt; LOCAL-05 auf MQTT-01-Identitätsfelder präzisiert (sw_version ist Build-Metadatum; Erstfehllauf erhalten); F3 (Test-Host-Build) und F4 (Test-HA) dokumentiert |
| 0.7 | 2026-10-12 | Expertenteam-Review eingearbeitet: LOCAL-15 (Commit `eac6a3e`), Präambel/PKG-06/Abschluss true-up, PKG-03/04-F3-Hinweis |
| 0.8 | 2026-10-12 | Autonome Fortführung (Auftrag 20:51): LOCAL-16 ergänzt (EXP-H08 Cloud-503-Phase), H06-Fixture-Dedup umgesetzt (lan-regression nutzt lan_fixture), [TEST-HOST-RUNBOOK.md](TEST-HOST-RUNBOOK.md) angelegt (WB-19), WB-13-Inventar erstellt |
| 0.9 | 2026-10-13 | Expert-Review-Runde 2 (3 Fach-Reviewer, [research/expert-review-2026-10-13-*.md](research/expert-review-2026-10-13-sdlc.md)): Grenzsatz Push/Fork true-upet (EXP-SD-01), Versionszeile im Header (SD-02), LOCAL-14/15-Provenanz-Fußnoten (SD-04), LOCAL-17 (RB-Top-3-Fixes, Commit `7545597`) |
| 1.0 | 2026-10-13 | Nachtrag: Kopf stand bereits auf 1.0 ( Historie lief bis 0.9 hinterher); Zeile gleicht an SPEC 1.0 an (Abnahme-Basis = Lock aus `16ebe55`, M6=B) |
| 1.1 | 2026-10-13 | CLOUD-01 ergänzt (PR #689-Übernahme, Commit `458c2e5`): lokale Abnahme PASS, E2E am Test-HA OFFEN |
| 1.0 | 2026-10-13 | M6=B umgesetzt: LOCAL-18 (Deps-Adoption `16ebe55`, Audit 0 Funde, Suite+Harness komplett PASS, neuer Store-Export `http-deps-m6b`) |

## Lokale Patchprüfungen – keine reale Geräte-/HA-Abnahme

Prüfdatum 2026-10-13; laufend nachgezogen (ursprünglich 2026-10-11, SPEC v0.3-Ära). Umgebung:
[environment.json](evidence/environment.json). Baseline-SHA vollständig fixiert,
Cargo.lock unverändert. `security/http-opt-in` ist ein lokaler Branch mit F2-Commit `59d3b12`
(Elternteil von `59d3b12`: Baseline `6f5a8449…`); kein Push. Lokale Commits:
`59d3b12` (SEC-01/02, F2), `7faf2eb` (WB-17, F5), `eac6a3e` (Review-Fixes).
Die Clippy-Lint-Bereinigung
(WB-10) und die lokalen Paketierungsänderungen liegen bewusst als
uncommittierte Arbeitsbaumänderungen vor.

| Prüf-ID / Req | Szenario / Methode | Ergebnis | Evidenz |
|---|---|---|---|
| LOCAL-01 / alle | Unveränderter Upstream: Build, Unit-Tests und Formatcheck | PASS: Build, 31 Tests, fmt | [Build](evidence/baseline-build.log), [Tests](evidence/baseline-test.log), [fmt](evidence/baseline-fmt.log) |
| LOCAL-02 / SEC-01/02 | Patchbuild, Default-aus, IPv4/IPv6-/Fehler-/Legacy-CLI-Unit-Tests, bisherige Tests | PASS: Build, 35 Tests, fmt | [Build](evidence/patch-build.log), [Tests](evidence/patch-test.log), [fmt](evidence/patch-fmt.log) |
| LOCAL-03 / SEC-01 | Echtes gepatchtes Binary: MQTT verbunden, 300 Sekunden Prozessmonitoring ohne irgendeinen eigenen TCP-Listener, anschließend Neustart | PASS, lokale Ausführung; Stand 12.10.: 11 Smoke-Fälle (s. LOCAL-15) | [11 Runtimefälle](evidence/patch-smoke.json), [Meta](evidence/patch-smoke-meta.json), [Lauf](evidence/patch-smoke-run.log) |
| LOCAL-04 / SEC-02 | Echtes Binary: CLI/ENV-Opt-in, genaue Loopback-Bindadresse, API erreichbar, CLI vor ENV; ungültige/leere Werte und Legacy-Port vor Dienststart abgewiesen | PASS, lokale Ausführung; Stand 12.10.: 11 Smoke-Fälle inkl. CLI-über-gültige-ENV (EXP-H01) | [11 Runtimefälle](evidence/patch-smoke.json), [Meta](evidence/patch-smoke-meta.json), [Lauf](evidence/patch-smoke-run.log) |
| LOCAL-05 / MQTT-01 | Fünf vollständige Discovery-Payloads einer synthetischen H6022-Fixture vor/nach Patch vergleichen | PASS: alle fünf Payloads in MQTT-01-Identitätsfeldern (unique_id, identifiers, Topics, Namen) identisch; `sw_version` meldet korrekt den Fork-Build (build.rs: %cd-%h von HEAD). Vergleich seit 12.10. auf Identitätsfelder begrenzt, Erstfehllauf nach dem F2-Commit erhalten | [Baseline](evidence/baseline-discovery.json), [Patch](evidence/patch-discovery.json), [Erstfehllauf](evidence/wb17-lan-first-attempt.log) |
| LOCAL-06 / LAN-01, SEC-01 | MQTT ON/OFF an Loopback-Fixture; keine Cloud-Credentials; HTTP(S)-Proxy nicht erreichbar; kein eigener TCP-Listener | PASS als Simulation: LAN turn 1/0, Prozess aktiv | [Ergebnis](evidence/patch-lan-result.json), [Protokoll](evidence/patch-lan-service.log), [Baseline](evidence/baseline-lan-result.json) |
| LOCAL-07 / alle | Strenges Clippy: workspace/all-targets/all-features, -D warnings | Vorher NICHT PASS: 10 identische, vorhandene Upstream-Testlints; nach begrenzter Bereinigung (nur `&`-Entfernungen in drei Testmodulen) PASS | [Bereinigungslauf](evidence/baseline-review-2026-10-11/README.md), [Diff](evidence/baseline-review-2026-10-11/post-cleanup.diff), [Historie](evidence/clippy-comparison.json) |
| LOCAL-08 / SEC-01/02 | HA-App-Schema und ENV-Weitergabe inspiziert; bash -n addon/run.sh | PASS als Syntaxprüfung/Inspektion; HA-Ausführung OFFEN | [HTTP-Patch](evidence/first-http.patch), source/addon/config.yaml und run.sh |
| LOCAL-09 / alle | Paketierungsregression nach Patch und erneuter vollständiger Quellpaketexport | PASS: 7 Tests; 82 Hashchecks; HTTP-Code enthalten; kein Imagebuild | [Tests](evidence/patch-package-tests.log), [Exportprüfung](evidence/http-package-inspection.json), [Quellarchiv](local-package/http-patch/govee2mqtt-security-local.tar.gz) |
| LOCAL-10 / SEC-01/02 | Produktiv-Binary mit -D warnings linten, ohne Testtargets | PASS | [Binary-Clippy](evidence/patch-clippy-binary.log) |
| LOCAL-11 / ROB-01 (lokal) | Cloud während des gesamten 300-s-Laufs nicht erreichbar (Proxy auf geschlossenen Port); MQTT verbunden, Prozess läuft ohne Ausfall, kein Listener | PASS als lokale Simulation; wiederholte Ausfälle und reale Netzisolation OFFEN | [11 Runtimefälle](evidence/patch-smoke.json), [Lauf](evidence/patch-http-off.log) |
| LOCAL-12 / ROB-01 (lokal) | Echtes gepatchtes Binary: 3 komplette MQTT-Ausfall-/Erholungszyklen (je 8 s Broker-Stop) bei dauerhaft fehlender Cloud (Proxy geschlossen, keine Credentials); je Zyklus Prozess lebt, MQTT verbindet sich neu, MQTT→LAN ON/OFF erreicht die Fixture; kein eigener Listener; 10 Cloud-Fehler ohne Absturz | PASS als lokale Simulation; echte Cloud-Ausfälle/reale Netzisolation OFFEN | [Ergebnis](evidence/cycles-result.json), [Lauf](evidence/cycles-service.log), [Skript](cloud_cycles.py) |
| LOCAL-13 / MQTT-01 (lokal) | Zwei aufeinanderfolgende Dienstläufe gegen dieselbe synthetische H6022-Fixture: identische Discovery-Payload-Mengen (Topics, Payloads bytegleich, unique_ids eindeutig) und identisch mit Upstream-Baseline | PASS als lokaler Vor-Check (Astra ASTRA-09); reale HA-Entity-Zählung OFFEN; mit WB-17-Binary wiederholt PASS | [Ergebnis](evidence/discovery-restart.json), [Skript](discovery_restart.py) |
| LOCAL-14 / SEC-02 | WB-17 (F5): Warn-Log bei Nicht-Loopback-Bind — zwei Klassifikationstests (Unit) + Laufzeitfall `http-nonloopback-warn` mit unbindbarer TEST-NET-1-Adresse (kein Listener entsteht, Prozess scheitert am Bind, Warnung im Log); Loopback-Fall bleibt still; 10/10 Smoke-Fälle (Provenanz EXP-SD-04: Stand `7faf2eb` nur prose erhalten; aktuelle 11-Fälle-JSON s. LOCAL-15) | PASS, lokale Ausführung; Commit `7faf2eb` auf `security/http-opt-in` (kein Push); 37 Tests, fmt, strenges Clippy all-targets+Binary, LAN-Regression, LOCAL-12/13 mit WB-17 wiederholt PASS | [Smoke 10 Fälle (Stand `7faf2eb`)](evidence/patch-smoke.json), [Warn-Log](evidence/patch-nonloopback-warn.log), [Tests](evidence/wb17-test.log), [fmt](evidence/wb17-fmt.log), [Clippy](evidence/wb17-clippy.log), [Export](evidence/wb17-package-inspection.json) |
| LOCAL-15 / SEC-01/02, MQTT-01, ROB-01 | Expertenteam-Review-Fixes (EXP-R01/R02/R03/R05/R06, EXP-H01/H02/H03): mapped-IPv6-Loopback-Klassifikation, ENV-/FILE-Unit-Tests (fail-closed), `[::]`-Parse-Test, `_FILE`-Doku + Kurzschluss-Satz, build.rs-HEAD-Rebuild-Trigger, Präzedenz-Zweitportfall, Proxy-Scrub beider Schreibweisen, XDG-Cache pro Label, git_head/dirty/sw_version in allen Result-JSONs | PASS: Commit `eac6a3e` (kein Push); 42 Tests, fmt, strenges Clippy all-targets+Binary, 11/11 Smoke-Fälle, LAN-Regression, LOCAL-12/13 wiederholt PASS; Pakettests 7/7; Export `http-review/` 82 Hashchecks. Provenanz (EXP-SD-04): Suite lief unmittelbar vor dem Commit am identischen dirty tree (meta-JSON belegt git_head `7faf2eb` + dirty); historische 9-/10-Fälle-Stände nur prose erhalten | [Tests](evidence/exp-test.log), [fmt](evidence/exp-fmt.log), [Clippy](evidence/exp-clippy.log), [Smoke+Meta](evidence/patch-smoke.json), [Pakettests](evidence/exp-package-tests.log), [Exportprüfung](evidence/http-review-package-inspection.json) |
| LOCAL-16 / ROB-01 (lokal) | cloud_cycles.py `--cloud-error-phase 20`: nach 3 MQTT-Ausfallzyklen läuft 20 s ein 503-Responder auf dem reservierten Loopback-Proxy-Port (Cloud –erreichbar, aber fehlernd“), danach Rückkehr auf geschlossenen Port; je prüfen: Dienst lebt, MQTT bleibt verbunden, LAN ON/OFF erreicht die Fixture während und nach der Phase, kein eigener TCP-Listener | PASS als lokale Simulation (4 503-Requests beobachtet, turns [1,0,1], reconnects 5); echte Cloud-Recovery (mit Credentials) und reale Netzisolation OFFEN (EXP-H08) | [Ergebnis](evidence/cycles-result.json), [Servicelog](evidence/cycles-service.log), [Skript](cloud_cycles.py) |

| LOCAL-17 / SEC-02, alle | Expert-Review-Runde 2, gefahrlose Fixes (research/expert-review-2026-10-13-rust.md): EXP-RB-02 PID-Suffix für `_FILE`-Test-Temp-Pfade, In-tree-Test „bindet exakt auf konfigurierter Loopback-Adresse", EXP-RB-03 build.rs `.git/refs`-Trigger + Grenz-Kommentar | PASS: Commit `7545597` (kein Push); 43 Tests, fmt, strenges Clippy all-targets+Binary | [Tests](evidence/exp2-test.log), [Clippy](evidence/exp2-clippy.log), [Build](evidence/exp2-build.log), [Review](research/expert-review-2026-10-13-rust.md) |

| LOCAL-18 / alle (M6=B-Basis) | Deps-Adoption `16ebe55` (Michael 13.10. 19:23 „2 B“): geprüftes Lock aus `deps/2026-10-13` auf den Security-Zweig; Suite build/fmt/strenges Clippy all-targets+Binary/43 Tests; cargo-audit **0 Vulnerabilities, 0 Unsound** (vorher 12+3 gegen altes Lock); volle Harness-Suite am committeten Stand: 300-s-Smoke 11/11, LAN-Regression, Cloud-Zyklen inkl. 503-Phase, Discovery-Restart — alles PASS, Result-JSONs belegen git_head `16ebe55` | PASS: Commit `16ebe55` (Branch auf Fork gepusht per Freigabe A); neuer Store-Export `local-package/http-deps-m6b/` (0.3.0-local-611251d511d3) | [Suite](evidence/deps3-test.log), [Audit](evidence/cargo-audit-new-lock.log), [Smoke+Meta](evidence/patch-smoke.json), [Zyklen](evidence/cycles-result.json), [Discovery](evidence/discovery-restart.json), [Export](local-package/http-deps-m6b/) |

Grenzen: H6022 ist ausschließlich eine Testfixture, **nicht Michaels SKU**.
HTTP(S)-Proxy-Verweigerung ist keine vollständige Netznamespace-Isolation.
Keine reale HA-Installation, kein echter Geräteschalttest, keine abschließende
ROB-01-Abnahme. LOCAL-12 simulierte Broker-Ausfälle, keine echten Cloud-Ausfälle;
LOCAL-13 ist lokaler Vor-Check und ersetzt keine reale HA-Entity-Prüfung.
Erster Fixtureversuch scheiterte am fehlenden Cacheverzeichnis im Testharness;
korrigiert und mit demselben gesicherten Baseline-Binary wiederholt
([erster Versuch](evidence/baseline-lan-first-attempt.log)). Erste LOCAL-12/13-Läufe
scheiterten an Testharness-Mängeln (zu frühes Discovery-Lesen, falscher
Reconnect-Zähler) — Skripte korrigiert, Fehlläufe im appendenden Servicelog
als Evidenz erhalten ([cycles-service.log](evidence/cycles-service.log)).

## Paketierungsnachweise – lokale Entwicklung, SPEC v0.3

Paketierungs-Prüf-IDs PKG-* sind unterstützende Prüfungen, **keine neuen
SPEC-Anforderungen** und kein Ersatz für reale SEC-/MQTT-/LAN-/ROB-Abnahmen.
Prüfdatum 2026-10-11. Details: [Paketierungsbericht](local-package/PACKAGING-REPORT.md).

| Prüf-ID / Req-Bezug | Szenario / Prüfmethode | Ergebnis | Evidenz |
|---|---|---|---|
| PKG-01 / SEC-01, SEC-02 | App verwendet lokalen Arbeitsbaum statt veröffentlichtem Upstream-Binary; Source-Patch ändert Exportversion; Registry-Fallback abgewiesen | PASS, lokale Paketierungsregression; Security-Verhalten OFFEN | [7 Tests](evidence/local-package-tests.log), [Export-Provenienz](local-package/final/govee2mqtt_security_local/SOURCE.json) |
| PKG-02 / alle Req | Identische Inputs erzeugen byteidentische Quellarchive; SHA256SUMS erkennt Source-Manipulation | PASS; keine Behauptung byteidentischer Images | [Tests](evidence/local-package-tests.log), [82 Hashchecks / Archivhash](local-package/evidence/package-inspection.json) |
| PKG-03 / SEC-01, SEC-02 | amd64-Ziel: Rust-/HA-OCI-Digests und Architektur prüfen; Imagebuild linux/amd64 | Manifeste PASS; Gateway-Build verworfen (F3, 12.10.); Ausführung auf dem Test-Host OFFEN (dort zusätzlich QEMU/binfmt nötig) | [Manifeste](local-package/evidence/architecture-manifests.json), [Historie](local-package/PACKAGING-REPORT.md) |
| PKG-04 / SEC-01, SEC-02 | aarch64-Ziel: Rust-/HA-OCI-Digests und Architektur prüfen; Imagebuild linux/arm64 | Manifeste PASS; Gateway-Build verworfen (F3, 12.10.); nativer Build auf dem Test-Host OFFEN | [Manifeste](local-package/evidence/architecture-manifests.json), [Historie](local-package/PACKAGING-REPORT.md) |
| PKG-05 / MQTT-01, LAN-01 | App-Konfiginspektion: MQTT service/schema, LAN host_network, AppArmor bleiben; Cloud-Credentials nicht Default; WebUI/Ingress nicht Standard | PASS als Inspektion; HA-/Discovery-/Geräteverhalten OFFEN | [Konfiginspektion](local-package/evidence/package-inspection.json), [Grenzen](local-package/PACKAGING-REPORT.md) |
| PKG-06 / alle Req | Frisch exportiertes HTTP-gepatchtes Image in separat autorisiertem Test-HA installieren und SPEC-Abnahmen ausführen | OFFEN / NICHT AUSGEFÜHRT; designierter F3-Buildinput seit M6=B (13.10. 19:23): [local-package/http-deps-m6b/](local-package/http-deps-m6b/) (0.3.0-local-611251d511d3, Quell-HEAD `16ebe55`, enthält HTTP-Patch + WB-17 + Review-Fixes + audit-sauberes Lock, 82 Hashchecks; `http-review/` überholt) | [Exportprüfung](evidence/http-review-package-inspection.json), [Anleitung](local-package/PACKAGING-REPORT.md) |

Unverändert: alle realen SPEC-Abnahmen bleiben OFFEN. Keine produktive
HA-Installation, kein Release. Kein Push zu `origin`/Upstream (wez) und
kein PR; Pushes ausschließlich auf den per Freigaben autorisierten Fork
`micschr0/govee2mqtt`: Branch `security/http-opt-in` = `eac6a3e`
(`59d3b12` F2 + `7faf2eb` F5 + `eac6a3e` Review-Fixes), fork-main als
HA-Store-Quelle (`e72848f`/`00c946f`/`3472055`).
