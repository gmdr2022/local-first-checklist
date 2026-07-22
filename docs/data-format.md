# Data format v1

The default primary file is `~/.local-first-checklist/tasks.json`. A custom path can be selected with `--data`. The last-known-good backup is the primary filename with `.bak` appended.

```json
{
  "schema_version": 1,
  "items": [
    {
      "id": 1,
      "title": "Verify the release package",
      "done": false,
      "created_at": "2026-07-22T12:00:00+00:00",
      "completed_at": null
    }
  ]
}
```

## Invariants

- `schema_version` is exactly `1`.
- Item IDs are unique positive integers and are not reused automatically.
- Titles are non-empty strings without leading or trailing whitespace.
- `done` is a JSON boolean.
- Timestamps are ISO 8601 values with a UTC offset.
- Open items have a null `completed_at`; completed items have a timestamp.
- Unknown top-level or item fields are rejected so accidental format drift is visible.

## Legacy migration

The pre-v1 bare array of item objects remains readable. Reading it has no side effect. The next successful mutation writes schema v1 and stores the original legacy bytes in the `.bak` file.

Unknown future schema versions fail closed. Downgrading or rewriting them is never attempted automatically.
