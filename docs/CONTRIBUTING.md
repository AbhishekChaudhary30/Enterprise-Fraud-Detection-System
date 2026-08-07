# Contributing Guide

1. Create a focused branch for the change.
2. Preserve the established package boundaries and configuration ownership.
3. Add or update a focused test for behavior changes.
4. Run the quality gate:

```powershell
ruff check src scripts dashboard tests
black --check src scripts dashboard tests
mypy src
pytest -q
```

5. Keep secrets, datasets, model binaries, logs, and generated artifacts out of commits.
6. Explain architectural impact and operational verification in the pull request.
