# CI/CD im Security-Fork

Stand: 2026-10-13. Vorbild ist der CI/CD-Stack von
[`micschr0/claudebar`](https://github.com/micschr0/claudebar), übertragen und
für dieses Rust-Home-Assistant-Repo angepasst.

## Was läuft

| Datei | Aufgabe |
| --- | --- |
| `.github/workflows/rust.yml` | `push`/`pull_request` auf `main`: `cargo fmt --check`, `cargo clippy --locked --all-targets -- -D warnings`, `cargo doc`, `cargo test --locked`, `cargo build --locked`, Coverage via `cargo-llvm-cov` + PR-Kommentar (`scttnlsn/covrs`). Toolchain: **Rust 1.94.0** (bis zur SEC-Abnahme gepinnt). |
| `.github/workflows/security.yml` | `push`/`pull_request` auf `main` + manueller Trigger: `actionlint` (lintet auch `run:`-Blöcke), `shellcheck` auf `scripts/*.sh`, `cargo audit` (RUSTSEC-Advisories gegen das Lock des Store-Spiegels `govee2mqtt_security_local/local-source` — das Top-Level-Lock ist der unveränderte Upstream-Baseline-Spiegel mit bekannten Funden und bleibt bewusst unverändert), `gitleaks` über die komplette Historie (`fetch-depth: 0`) mit `.gitleaks.toml`. |
| `.github/workflows/renovate.yml` | Self-hosted Renovate (cron 03:00 Europe/Berlin + manueller Trigger). Benötigt die Secrets `RENOVATE_APP_ID` + `RENOVATE_PRIVATE_KEY` einer GitHub App — der Job skipped sich per `if`-Guard selbst, bis Michael diese anlegt. Alternative: gehostete „Renovate GitHub App“ installieren und diese Workflow wieder entfernen. |
| `renovate.json` | Renovate-Konfiguration (Details unten). |
| `.gitleaks.toml` | Gitleaks-Allowlist: `Cargo.lock` und der HA-Store-Spiegel `govee2mqtt_security_local/**` (dort stehen SHA256-Datei-Hashes in `SOURCE.json`, die `generic-api-key`-Falschpositive auslösen — verifiziert 2026-10-13: alle 7 Vollhistorie-Funde lagen in dieser Datei). |

Vorhandene, unangetastete Upstream-Workflows: `build.yml` (Container-Build nach
`ghcr.io/wez/govee2mqtt` — im Fork ohne Schreibrecht auf den wez-Namespace),
`pr.yml` (Cargo build/test/fmt), `no-response.yml` (Issue-Automation).

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