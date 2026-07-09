# Local First Checklist

A small Python checklist app that stores tasks in a local JSON file and works without accounts, cloud services, or internet access.

This repository is intentionally simple: it is a learning project focused on practical local-first behavior, clean structure, validation, and documentation.

## Features

- Add checklist items from the command line.
- Mark items as done.
- List pending and completed items.
- Store data locally in JSON.
- Use the same storage logic from CLI code and tests.
- Run with the Python standard library only.

## Quick start

```bash
python -m local_first_checklist.cli add "Review Python basics"
python -m local_first_checklist.cli add "Write a small README"
python -m local_first_checklist.cli list
python -m local_first_checklist.cli done 1
```

By default, data is stored at:

```text
~/.local-first-checklist/tasks.json
```

Use a custom data file:

```bash
python -m local_first_checklist.cli --data ./tasks.json add "Try local storage"
```

## Project structure

```text
local_first_checklist/
  core.py       data model, JSON storage, checklist operations
  cli.py        command-line interface
tests/
  test_core.py  standard-library unit tests
```

## Validation

```bash
python -m compileall -q local_first_checklist tests
python -m unittest discover -s tests
```

## Technical focus

- Python
- Local-first data
- JSON persistence
- Small CLI tooling
- Automated validation
- Clear documentation

## Status

Learning project. The goal is to keep the code small, readable, and useful as a public example of practical software habits.

## License

No open-source license has been selected yet. Public visibility does not grant reuse rights beyond GitHub platform viewing.
