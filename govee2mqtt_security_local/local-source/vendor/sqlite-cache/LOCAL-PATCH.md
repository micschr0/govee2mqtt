# Local security patch

Source: sqlite-cache 0.1.4 from crates.io, Apache-2.0 (see LICENSE).
The package is vendored because 0.1.4 pins rusqlite 0.32, which bundles an
SQLite version affected by RUSTSEC-2026-0459. The dependency is raised to
rusqlite 0.41.1 to use libsqlite3-sys 0.39.1 / SQLite 3.54.1. The upstream u64 SQLite conversions were adapted to checked i64
conversions as required by rusqlite 0.41, and Rustfmt was applied. Keep this patch
until upstream provides a compatible fixed release. The project's cache
round-trip test verifies the bundled SQLite version and cache operations.
