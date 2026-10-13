# CI/CD im Security-Fork

Stand: 2026-10-14 (Review-Runde 3: Store-Integritäts-Gate, Renovate-Cargo-Scoping, Gitleaks-Verengung, Rust-Cache-Ziel, Doku-Korrekturen — EXP-CICD-01/03/05/07/08/09). Vorbild ist der CI/CD-Stack von
[`micschr0/claudebar`](https://github.com/micschr0/claudebar), übertragen und
für dieses Rust-Home-Assistant-Repo angepasst.

## Was läuft

| Datei | Aufgabe |
| --- | --- |
| `.github/workflows/rust.yml` | `push`/`pull_request` auf `main`: `cargo fmt --check`, `cargo clippy --locked --all-targets -- -D warnings`, `cargo doc`, `cargo test --locked`, `cargo build --locked`, Coverage via `cargo-llvm-cov` + PR-Kommentar (`scttnlsn/covrs`) — **alles gegen die Store-Quelle `govee2mqtt_security_local/local-source`** (das veröffentlichte Produkt), nicht gegen den toten Upstream-Baseline-Spiegel auf oberster Ebene (der unter dem gepinnten 1.94.0-Toolchain klernt 10 Clippy-Basisfehler, die nur auf dem Security-Branch gefixt sind). Toolchain: **Rust 1.94.0** (bis zur SEC-Abnahme gepinnt). `rust-cache` seit Runde 3 explizit auf `govee2mqtt_security_local/local-source` gerichtet + `cache-on-failure` (EXP-CICD-05; das Default-Root-Workspace traf den eigentlichen Build nicht). Trigger nur bei Änderungen an Store-Quelle oder Workflow. |
| `.github/workflows/security.yml` | `push`/`pull_request` auf `main` + wöchentlicher Schedule (Mo 03:00 UTC — neue RUSTSEC-Funde sollen nicht bis zum nächsten Push warten, EXP-CICD-06) + manueller Trigger: `actionlint` (lintet auch `run:`-Blöcke; Glob über alle `workflows/*.yml` — seit 550e20e sind alle Workflows unsere, EXP-CICD-09), `shellcheck` auf `scripts/*.sh`, `cargo audit` (RUSTSEC-Advisories gegen das Lock des Store-Spiegels `govee2mqtt_security_local/local-source` — das Top-Level-Lock ist der unveränderte Upstream-Baseline-Spiegel mit bekannten Funden und bleibt bewusst unverändert), `gitleaks` über die komplette Historie (`fetch-depth: 0`) mit `.gitleaks.toml`. |
| `.github/workflows/store-integrity.yml` | **Runde 3 (EXP-CICD-01):** Gate gegen 353efef-Klassen-Zwischenfälle. Bei Änderungen unter `govee2mqtt_security_local/**`: `sha256sum -c SHA256SUMS` über den gesamten Store-Spiegel + Kohärenzcheck `SOURCE.json`/`SOURCE_TAG` (`scripts/check-store-source.py`). Am Stand 344f60f lokal verifiziert grün. |
| `.github/workflows/renovate.yml` | Self-hosted Renovate (cron `0 3 * * *` — UTC, 05:00 Berlin zur Sommerzeit — + manueller Trigger; die `timezone` in `renovate.json` steuert nur Renovate-interne Schedules, nicht den Workflow-Cron — EXP-CICD-08). Benötigt die Secrets `RENOVATE_APP_ID` + `RENOVATE_PRIVATE_KEY` einer GitHub App — ein vorgeschalteter Guard-Step (job-level `if` kennt den `secrets`-Kontext nicht) skipped den Lauf grün mit Notice, bis Michael diese anlegt. Alternative: gehostete „Renovate GitHub App“ installieren und diese Workflow wieder entfernen. |
| `renovate.json` | Renovate-Konfiguration (Details unten). Cargo-Manager seit Runde 3 auf `govee2mqtt_security_local/local-source/Cargo.toml` beschränkt (EXP-CICD-03) — der eingefrorene Top-Level-Baseline-Spiegel bleibt für Renovate unsichtbar. |
| `.gitleaks.toml` | Gitleaks-Allowlist: `Cargo.lock` und `govee2mqtt_security_local/SOURCE.json` (deren SHA256-Datei-Hashes `generic-api-key`-Falschpositive auslösen — verifiziert 2026-10-13: alle 7 Vollhistorie-Funde lagen in dieser Datei). Seit Runde 3 bewusst auf genau diese Datei verengt (EXP-CICD-07); der Rest des Store-Spiegels bleibt im Secret-Scan. |

## Entfernte Upstream-Workflows (Fork, 2026-10-13)

`build.yml` (Container Build), `pr.yml` und `no-response.yml` wurden am Fork
gelöscht (Michaels Auftrag): Der Fork-Container-Build erzeugte ein Image des
ungepatchten Upstream-Baseline-Spiegels, das von nichts referenziert wird
(unser Store-Add-on baut bewusst lokal ohne `image:`) — und failte am Fork
ohnehin. `pr.yml`/`no-response.yml` sind Upstream-Community-Tools ohne
Fork-Bezug. Bei Upstream-Rebase fallen die Löschungen als Konflikte auf und
werden bewusst so gehalten (Dokumentation statt .gitattributes-Maskierung).
## Bewusste Auslassungen (Stand heute)

* **Rust 1.94.0 statt stable** in `rust.yml` — der Pin ist Abnahme-Basis
  (Bestätigung Michael 2026-10-12). Nach der Abnahme auf `stable` umstellen oder
  weiter pinnen.
* **Renovate: kein automerge.** Cargo-Updates (patch/minor, serde-Gruppe) und
  `lockFileMaintenance` erzeugen nur Vorschlags-PRs, die manuell gemerged
  werden. Grund: die gepinnten Lockfile/Docker-Digests sind bis zur Abnahme
  (WB-16/WB-08) die verifizierte Abnahme-Basis und dürfen nicht automatisch
  verschoben werden.
* **Renovate: dockerfile/docker-compose-Manager deaktiviert** — Docker-Basis-
  Images (`Dockerfile`, `addon/Dockerfile`, `docker-compose.yml`) bleiben
  unverändert.
* **Renovate: `dtolnay/rust-toolchain`-Aktualisierung deaktiviert** — schützt
  den Toolchain-Pin in `rust.yml` vor automatischen Verschiebungen.
* **Nicht übertragen aus dem claudebar-Vorbild** (claudebar-Produkt-spezifisch):
  `release*.yml`/`dist` (cargo-dist), `npm-release.yml`, `pages.yml`
  (Doku-Deploy), `openwiki-update.yml`, `verify-install.yml`, `ruff`/`bats`
  (Python/npm-Projekt), `semgrep`-Job, `zizmor`-Job (braucht im Vorbild das
  Secret `ZIZMOR_PAT` plus `zizmor.yml`-Suppressions — nachrüstbar), mold,
  `--no-default-features`-TUI-Matrix, `cargo auditable build --release`.
* **`shellcheck` nur auf `scripts/*.sh`** — `addon/run.sh` ist der Upstream-
  HA-Add-on-Starter mit bashio-Shebang und würde SC1008/SC2155/SC2164-Funde
  liefern; kein Änderungsbedarf am Addon für Lint-Ästhetik.
* **`.github/dependabot.yml` (Upstream) bleibt vorerst liegen.** Sobald
  Renovate aktiv ist, sollte Michael Dependabot-Version-Updates deaktivieren
  (Settings → Code security → Dependabot), sonst gibt es doppelte
  Abhängigkeits-PRs mit anderen Guardrails.

## Umschalten nach der Abnahme (WB-16/WB-08)

1. `rust.yml`: `toolchain: '1.94.0'` → `stable` (oder bewusst weiter pinnen).
2. `renovate.json`:
   * serde-Regel: `automerge: true`
   * Cargo patch/minor-Regel: `automerge: true`
   * `lockFileMaintenance`: `automerge: true`
   * dockerfile/docker-compose-Regel entfernen (Digest-Updates frei)
   * `dtolnay/rust-toolchain`-Regel entfernen
   * optional `platformAutomerge: true`
3. Dependabot-Version-Updates deaktivieren oder `dependabot.yml` löschen.