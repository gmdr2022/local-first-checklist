# Contributing

This is a small learning project. Keep changes practical, readable, and dependency-free unless a dependency clearly improves the project.

## Guidelines

- Preserve local-first behavior.
- Avoid mandatory accounts, cloud services, or internet access.
- Keep code in the Python standard library when possible.
- Add or update tests for behavior changes.

## Validation

```bash
python -m compileall -q local_first_checklist tests
python -m unittest discover -s tests
```
