# Design and failure model

## Write path

1. Validate the in-memory item set.
2. If a primary exists, parse and validate it.
3. Atomically write the valid primary bytes to the backup path.
4. Serialize schema v1 to a temporary file in the primary directory.
5. Flush file contents and ask the operating system to persist them.
6. Atomically replace the primary path.

Keeping the temporary file in the destination directory avoids cross-volume replacement behavior. If replacement fails, the previous primary remains in place and the temporary file is removed.

## Read path

Files are decoded as UTF-8, parsed as JSON, and validated before a `Checklist` is constructed. Errors identify the violated contract without printing checklist contents.

## Recovery

`doctor` reports the health of both files and never writes. `recover --yes` validates the backup before atomically copying it over the primary. Recovery is intentionally operator-controlled because automatically choosing older data can hide corruption or discard newer work.

## Non-goals

- Encryption or secure deletion
- Multi-process transaction coordination
- Cloud synchronization or conflict-free replication
- Authentication or authorization

Those concerns require different product and threat-model decisions than a transparent single-user local file.
