# Local-first Checklist

A dependency-free Python CLI for checklists that should remain usable without an account, a server, or an internet connection.

The project is deliberately small, but its storage behavior is not casual: writes are atomic, existing valid data is retained as a last-known-good backup, persisted input is validated before use, and recovery is always an explicit operator action.

## Why it exists

Small local tools often write JSON directly. A process interruption at the wrong moment can then turn a useful offline workflow into an unreadable file. Local-first Checklist demonstrates a compact alternative with clear failure behavior and a documented on-disk contract.

## Install

Python 3.11 or newer is required.

```bash
python -m pip install .
local-first-checklist --version
```

The package has no runtime dependencies.

## Use

```bash
local-first-checklist add "Verify the release package"
local-first-checklist list
local-first-checklist done 1
local-first-checklist list --all
local-first-checklist reopen 1
local-first-checklist edit 1 "Verify both release packages"
```

Data is stored at `~/.local-first-checklist/tasks.json` by default. Select another file with a global option placed before the command:

```bash
local-first-checklist --data ./team-tasks.json add "Review the handoff"
```

Machine-readable output is available for scripting:

```bash
local-first-checklist --json list --all
```

Permanent removal and recovery require explicit confirmation:

```bash
local-first-checklist remove 1 --yes
local-first-checklist doctor
local-first-checklist recover --yes
```

`doctor` only reads the primary and backup files. It never repairs, migrates, or replaces data.

## Storage guarantees

- A complete temporary file is flushed before it replaces the primary file.
- The previous valid primary is copied to `tasks.json.bak` before a mutation.
- Corrupt or unsupported data fails closed with an actionable error.
- Legacy list-based files remain readable and are migrated only on the next successful mutation.
- Recovery accepts only a backup that passes the same validation as the primary.
- No telemetry, sync, login, or network request is present.

These guarantees reduce common corruption risks; they are not a substitute for independent backups when the checklist is important.

See [the data format](docs/data-format.md) and [design notes](docs/design.md) for the exact contract and failure model.

## Commands

| Command | Purpose |
| --- | --- |
| `add TITLE` | Create an open item |
| `list [--all]` | List open items or the complete history |
| `done ID` | Complete an item |
| `reopen ID` | Return an item to the open state |
| `edit ID TITLE` | Replace an item's title |
| `remove ID --yes` | Permanently remove an item |
| `doctor` | Inspect primary and backup health without writing |
| `recover --yes` | Replace the primary with its validated backup |

Domain and data errors return exit code `1`; invalid usage or missing confirmation returns `2`.

## Validate

```bash
python -m compileall -q local_first_checklist tests
python -m unittest discover -s tests -v
python -m pip install .
local-first-checklist --version
```

CI runs the same behavior on Windows and Ubuntu with every supported Python version.

## Security and privacy

Checklist contents never leave the selected local file. Do not commit real task data. Security reports should use GitHub's private vulnerability reporting flow described in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
