# govee2mqtt-Security-Fork – Spezifikation

Stand: 2026-10-13 · Version: 1.0 · Status: FREIGEGEBEN ZUR LOKALEN ENTWICKLUNG

Diese Spezifikation ist die versionierte Quelle der Wahrheit für den Fork.
Jede Anforderung hat eine ID, eine Begründung und eine messbare Abnahme.
Offene Punkte sind ausdrücklich als solche markiert und werden nicht erfunden.

## Ziel

Den govee2mqtt Home-Assistant-App-Fork sicherer machen, ohne die bestehende
MQTT-/LAN-Funktionalität für Michaels Heimnetz zu beeinträchtigen.

## Nicht-Ziele

- Kein Redesign, keine Framework-Migration, keine ungefragten Umbauten
- Keine Cloud-Funktionen neu implementieren oder verschärfen
- Keine Veröffentlichung oder Releases ohne separate Freigabe

## Anforderungen

### SEC-01: HTTP-Steuerung standardmäßig deaktiviert

- **Soll:** Ohne ausdrückliches Opt-in startet der govee-Dienst keinen
  HTTP-Listener auf Port 8056 oder einem anderen Port.
- **Begründung:** Die HTTP-API hat keine Authentifizierung und erlaubt
  Gerätesteuerung ohne HA-Anmeldung. Sie ist für den HA-Betrieb über MQTT
  nicht erforderlich.
- **Abnahme:** Der Prozess läuft, MQTT verbindet sich – und währenddessen
  existiert kein TCP-Listener des Dienstes auf Port 8056 oder einem anderen
  Port (Listener-Prüfung, geräteunabhängig). Die Schaltbestätigung des
  vereinbarten LAN-Geräts wird als eigener Schritt unter LAN-01 abgenommen
  und blockiert diese Kernprüfung nicht (Astra ASTRA-02).
- **Quelle:** Analyse vom 11.10.2026 (src/service/http.rs, Port-Bind 0.0.0.0:8056)
- **Priorität:** MUSS

### SEC-02: HTTP nur mit expliziter Konfiguration aktivierbar

- **Soll:** HTTP-Steuerung ist nur über eine ausdrückliche Konfigurationsoption
  startbar, die standardmäßig nicht gesetzt ist.
- **Begründung:** Bestehende Nutzer, die die API brauchen, sollen sie
  weiterverwenden können – aber nie versehentlich.
- **Abnahme:** Ohne die Option startet kein Listener; mit der Option startet
  der Listener nur auf der konfigurierten Adresse. Der CLI-Wert geht vor
  ENV; ungültige oder leere Werte sind Startfehler ohne Fallback. Der
  HA-App-Pfad (http_bind → ENV) wird in der realen Abnahme je gesetzt und
  ungesetzt geprüft (Astra ASTRA-03/ASTRA-10). Zeigt das Opt-in auf eine
  Nicht-Loopback-Adresse, protokolliert der Dienst beim Start eine Warnung
  (F5-Entscheidung 12.10.2026, WB-17; Semantik unverändert).
- **Priorität:** SOLL (erster Release)

### MQTT-01: MQTT-Discovery und Entity-IDs bleiben erhalten

- **Soll:** Die MQTT-Discovery-Nachrichten (unique_id, Device-Identifier,
  Entity-Namen) sind gegenüber dem definierten Upstream-Baseline-Commit
  unverändert.
- **Begründung:** Bestehende HA-Installationen dürfen durch den Fork keine
  doppelten oder verwaisten Entities erhalten.
- **Abnahme:** Vorher-Nachher-Vergleich der Discovery-Payloads für die
  vereinbarten Geräte; keine neuen oder verschwundenen Entities in HA.
- **Priorität:** MUSS

### LAN-01: LAN-Steuerung ohne Cloud-Zugangsdaten funktionsfähig

- **Soll:** Der Dienst entdeckt und steuert LAN-fähige Geräte ohne
  GOVEE_EMAIL, GOVEE_PASSWORD oder GOVEE_API_KEY.
- **Begründung:** LAN-only ist der sicherste Betrieb; er erfordert keine
  Cloud-Zugangsdaten im Heimnetz.
- **Abnahme:** Vereinbartes LAN-Gerät führt eine Schaltoperation aus,
  während keine Cloud-Zugangsdaten konfiguriert sind und keine
  Internetverbindung zum Govee-Cloud-Dienst besteht.
- **Quelle:** docs/CONFIG.md: „govee2mqtt can run without any govee credentials"
- **Priorität:** MUSS
- **Entscheidungsregel:** Unterstützt die verifizierte SKU die LAN-API
  nicht, erfolgt Eskalation an Michael, bevor Cloud-Zugangsdaten
  konfiguriert werden. LAN-only bleibt Standardpfad; Cloud nur als
  ausdrücklich autorisierte Ausnahme (Astra ASTRA-07).

### ROB-01: Dienst bleibt bei Cloud-Ausfall funktionsfähig

- **Soll:** Fällt die Cloud-Erreichbarkeit aus, funktionieren LAN-Geräte
  weiterhin. Der Dienst stürzt nicht ab und crash-loopt nicht.
- **Abnahme:** Internetzugang zur Govee-Cloud unterbinden, vereinbartes
  LAN-Gerät schalten. Messbar: Der Dienst läuft nach Ausfallende ohne
  Neustart weiter (Beobachtungsfenster ≥ 10 min), die MQTT-Sitzung stellt
  sich wieder her, und innerhalb von 15 min tritt keine Neustart-Serie auf
  (Astra ASTRA-06). Lokal bereits simuliert: LOCAL-12, 3 Ausfallzyklen.
- **Priorität:** SOLL

## Freigabe und Abnahmegrenzen

Michael autorisierte am 11.10.2026: „ok alles so machen“. Die beschriebene
lokale Entwicklung darf starten: festen Upstream-Stand auschecken, Build und
Tests prüfen, SEC-01/SEC-02 minimal umsetzen und Regressionen prüfen.
SKU/LAN-Fähigkeit sowie exakte HA-Versionen bleiben Voraussetzungen für die
reale Abnahme, nicht für den lokalen Code-Patch. Keine reale Geräteabnahme
als bestanden melden. Kein GitHub-Fork, Push, Release oder produktive
Installation. Der HTTP-Patch darf seit der F2-Freigabe (11.10.2026, 23:02)
als lokaler Commit auf `security/http-opt-in` festgehalten werden; umgesetzt
als `59d3b12`.

**Nachträge (12.10.2026):** Später erteilte Freigaben erweiterten den Rahmen
schrittweise: F2 — lokaler Commit `59d3b12`; F5 — Commit `7faf2eb`;
Expertenteam-Review — Commit `eac6a3e`; Freigabe A — Push des Branches
`security/http-opt-in` auf den Fork `micschr0/govee2mqtt` (20:49); Freigabe
„der fork darf ruhig angepasst werden“ — fork-main als lokale
HA-Custom-Store-Quelle (`e72848f`: `repository.yaml` +
`govee2mqtt_security_local/`-Export; `00c946f`: `docs/security/` mit
SPEC- und TEST-MATRIX-Snapshots). Kein PR zu Upstream, kein Release, keine
produktive Installation; reale Abnahmen bleiben OFFEN. F3 (12.10.2026): Image-Builds laufen auf dem Test-Host, nicht
auf diesem Gateway; rootless Docker hier ist verworfen. F4 (12.10.2026):
Reale Abnahme läuft in einem separaten Test-HA; produktives HA ist kein
Abnahmeziel. F5 (12.10.2026): Warn-Log bei Nicht-Loopback-Bind umgesetzt
(WB-17). Kein Push, kein Release, keine produktive Installation.

## Bestätigte Umgebung und Umfang

Quelle: Michaels Antworten vom 11.10.2026.

- Geräteumfang: zunächst nur das eine bisher bekannte, aktive Gerät. SKU seit 11.10. 23:16 bekannt: Govee Pendelleuchte **H60C1** (Produkt-URL-Variante 51797089779896, 1-Pack). LAN-API-Fähigkeit: Lights-Familie laut SKUS.md; H60C1 ist in der Home-Assistant-Doku zur lokalen Govee-API gelistet. Geräteindividuelles LAN-Enablement in der Govee-Home-App und UDP-Erreichbarkeit 4001–4003 bleiben Abnahmevorbedingung.
- Home Assistant: laut Michael neueste Version; genaue installierte Core-/Supervisor-Version beim Test protokollieren. Kein automatisches Upgrade beauftragt.
- MQTT: Mosquitto Broker 7.1.1 laut Michael. Vor Tests klären/protokollieren, ob dies die HA-App-Version ist; nicht als Version des Mosquitto-Daemons ausgeben.
- Installation: Neuinstallation, bisher kein govee2mqtt installiert. Keine Bestandsmigration nötig; MQTT-01 bleibt eine Upstream-Regressionsprüfung.

## Offene Punkte und Empfehlungen (TBD)

| ID | Status / Ergebnis | Nächster Schritt / Verantwortlich |
|----|-------------------|----------------------------------|
| TBD-01 | Beantwortet 11.10. 23:16: aktives Gerät ist Govee Pendelleuchte H60C1 (Variante 51797089779896); LAN-API laut HA-Local-API-Doku unterstützt. | Vor Abnahme noch verifizieren: LAN-Schalter in Govee-Home-App aktiv + UDP 4001–4003 erreichbar; Michael prüft App-Schalter, govee-dev protokolliert bei Abnahme |
| TBD-02 | Beantwortet: neueste HA-Version laut Michael; Mosquitto Broker 7.1.1. | Exakte HA- und Daemon-/App-Versionen im Testnachweis erfassen; govee-dev |
| TBD-03 | Beantwortet: Neuinstallation, keine Migration. | Keine Migrationsaufgaben; Discovery-Regression bleibt relevant |
| TBD-04 | Beschlossen am 11.10.2026: HTTP standardmäßig aus; MQTT als HA-Steuerungspfad. Ingress erst bei späterem konkretem WebUI-Bedarf. | Kein Ingress-Ausbau im ersten Patch; kein direkter Netzwerkzugang als Standard |
| TBD-05 | Beschlossen am 11.10.2026: Entwicklungsbaseline 6f5a8449ca63da8bdc7cc696288a993681ff2a69 (Commit-Datum 12.04.2026). | Build-/Testbaseline vor Patch selbst prüfen |

TBD-Review-Rhythmus: Alle offenen TBDs werden bei jeder Arbeitssitzung
geprüft und mit neuem Stand aktualisiert (Astra ASTRA-08). Zieltermine
setzt Michael bei Vergabe.

HTTP meint hier den lokalen Bridge-Server, nicht Govees Cloud-API. Er stellt
Geräte-/Statusdaten, Schalten, Helligkeit, Farbtemperatur, Farbe und Szenen
bereit; zudem One-Click-Aufrufe bei vorhandenen Cloud-/IoT-Clients. Die kleine
WebUI nutzt diesen Server. HTTP schafft keine zusätzliche Gerätefähigkeit und
macht Cloud-Funktionen nicht lokal. MQTT bleibt der normale HA-Steuerungspfad.

Upstream: HTTP-Server bindet an alle IPv4-Interfaces ohne Authentifizierung;
die HA-App nutzt Host-Netzwerk und hat Ingress derzeit auskommentiert.
Die WebUI lädt außerdem JavaScript von externen CDNs. Das ist kein reiner
Offline-Webclient.

Baseline-Begründung: main liegt zwei Commits nach dem neuesten Tag
2026.03.25-ab9deb66: Versionsfortschreibung und Clippy-Bereinigung.
Vorteil: weniger bestehende Lint-Warnungen für neue Änderungen; Tradeoff:
kein getaggter App-Release. Für Reproduzierbarkeit volle SHA verwenden.
Die im Commit genannten 31 bestandenen Tests sind Upstream-Angaben, keine
von uns ausgeführte Verifikation.

Quellen (Originalabruf 11.10.2026):
- https://github.com/wez/govee2mqtt/blob/6f5a8449ca63da8bdc7cc696288a993681ff2a69/src/service/http.rs
- https://github.com/wez/govee2mqtt/blob/6f5a8449ca63da8bdc7cc696288a993681ff2a69/addon/config.yaml
- https://github.com/wez/govee2mqtt/blob/6f5a8449ca63da8bdc7cc696288a993681ff2a69/assets/index.html
- https://github.com/wez/govee2mqtt/commit/6f5a8449ca63da8bdc7cc696288a993681ff2a69
- https://github.com/wez/govee2mqtt/compare/ab9deb66d7d2ecb4f7e7185123a12771d55f5a11...6f5a8449ca63da8bdc7cc696288a993681ff2a69

## Änderungshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 0.1 | 2026-10-11 | Erster Entwurf basierend auf der Analyse vom 11.10.2026 |
| 0.2 | 2026-10-11 | Nutzerangaben 1–3 ergänzt; HTTP-Nutzen und konkrete Baseline als Empfehlungen dokumentiert |
| 0.3 | 2026-10-11 | Michael bestätigt Empfehlungen und lokale Entwicklung; reale Abnahmen weiter offen |
| 0.4 | 2026-10-11 | Autonomer Vollständigkeitspass (Auftrag Michael): Abnahmetexte an Soll angleichen (SEC-01 beliebiger Port, SEC-02 CLI-vor-ENV/Fehler-ohne-Fallback, ROB-01 messbar), SEC-01/LAN-01-Abnahme getrennt, LAN-01-Entscheidungsregel, TBD-Review-Rhythmus; keine Produktverhaltensänderung |
| 0.5 | 2026-10-11 | F2-Freigabe dokumentiert: lokaler Commit `59d3b12` des HTTP-Patches auf `security/http-opt-in` (kein Push); Freigabegrenze angepasst |
| 0.6 | 2026-10-11 | F1 beantwortet: SKU H60C1 (Pendelleuchte, Variant 51797089779896) nachgetragen; LAN-API-Fähigkeit laut HA-Local-API-Doku, App-Enablement als Abnahmevorbedingung |
| 0.7 | 2026-10-12 | F3 (Test-Host-Build), F4 (Test-HA-Abnahme), F5 (Warn-Log bei Nicht-Loopback-Bind) dokumentiert; SEC-02 um WB-17-Warnung ergänzt |
| 0.8 | 2026-10-12 | Expertenteam-Review (3 Reviewer) eingearbeitet: R01 mapped-IPv6-Klassifikation, R02 ENV/FILE-Unit-Tests, R03/R05/R06 Doku, H01/H02/H03 Harness (Commits `eac6a3e`); Abnahmen unverändert OFFEN |
| 0.9 | 2026-10-12 | Freigabenachträge dokumentiert: Push-Freigabe A (Fork-Branch), fork-main als lokale HA-Store-Quelle (`e72848f`/`00c946f`), SPEC/TEST-MATRIX-Snapshots unter `docs/security/` veröffentlicht |
| 1.0 | 2026-10-13 | M6=B (Michael, 19:23): audit-sauberes Dependency-Update (`deps/2026-10-13`, 213 Pakete) wird VOR der Abnahme eingebracht — Abnahme-Basis ist ab jetzt das Lock aus `16ebe55` (cargo-audit 0 Funde); Toolchain-Pin 1.94.0 unangetastet |
