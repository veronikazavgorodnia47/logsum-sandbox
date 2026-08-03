# ci-notes.md

## PR

https://github.com/veronikazavgorodnia47/logsum-sandbox/pull/new/add-ci-workflow

Branch: `add-ci-workflow` → `main`

## Workflow

File: `.github/workflows/ci.yml`
Triggers: push, pull_request
Steps: `ruff check .` then `pytest -v` on Python 3.11 / ubuntu-latest

## Run history

| Commit  | Result  | Notes |
|---------|---------|-------|
| `6e68b05` | FAIL | 8 ruff errors: PLW1510 (missing `check=False`), F401 (unused imports), I001 (unsorted imports) |
| `b9d52ce` | PASS | Fixed all 8 errors; `ruff check .` and `pytest -v` (52 tests) both clean locally |
| `7d186f6` | PASS | Merge to main — all checks green |

## CI runs

https://github.com/veronikazavgorodnia47/logsum-sandbox/actions
