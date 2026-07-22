# Contributing

Changes should preserve the project's local-first contract and make failure behavior easier to understand, not more implicit.

## Before opening a pull request

- Keep runtime code dependency-free unless a dependency has a documented operational benefit.
- Do not add telemetry, mandatory accounts, or network access.
- Add tests for behavior changes, including negative and interruption paths where relevant.
- Update the data-format document when the persisted contract changes.
- Never commit real checklist data.

Run:

```bash
python -m compileall -q local_first_checklist tests
python -m unittest discover -s tests -v
python -m pip install .
local-first-checklist --version
```

Pull requests should explain the user-visible behavior, failure modes, and validation performed.
