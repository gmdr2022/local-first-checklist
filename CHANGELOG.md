# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-07-22

### Added

- Versioned JSON schema with strict validation and legacy list migration.
- Atomic persistence with a validated last-known-good backup.
- Explicit `doctor` and `recover` workflows.
- `edit`, `reopen`, and confirmed `remove` operations.
- Machine-readable JSON output and installable console command.
- Windows and Ubuntu validation across Python 3.11 through 3.14.

### Changed

- Data failures now produce concise domain errors instead of raw tracebacks.
- Documentation now states storage guarantees, limits, and recovery semantics.

[1.0.0]: https://github.com/gmdr2022/local-first-checklist/releases/tag/v1.0.0
