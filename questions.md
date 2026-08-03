# questions.md

## Where is the grouping rule?

**Files read:** `spec.md`, `src/logsum.py`

Rows are grouped by the composite key `(service, level)` after normalisation. The spec defines this rule at `spec.md:53`. In code, `process()` accumulates rows into a `defaultdict` keyed on `(service, level)` at `src/logsum.py:62`. Output is sorted by `service` ascending then `level` ascending (`src/logsum.py:83`, `spec.md:37`).

---

## How is missing level handled?

**Files read:** `spec.md`, `src/logsum.py`

A blank `level` field (empty or whitespace-only) is replaced with the sentinel `UNKNOWN` and the row is still counted in the output. A warning is written to stderr.

- The rule is stated in `spec.md:46` and the edge cases table at `spec.md:74`.
- In code: `_normalise_row` strips the field at `src/logsum.py:30`, checks for blank at `src/logsum.py:31`, emits the warning at `src/logsum.py:33`, and returns `UNKNOWN` via `raw_level.upper() or UNKNOWN_LEVEL` at `src/logsum.py:36`.
- The rationale is in `spec.md:120–122`: a missing level is recoverable; a malformed timestamp is not, so the asymmetry is intentional.

---

## How do I run tests and CI locally?

**Files read:** `CLAUDE.md`, `.github/workflows/ci.yml`

First, install the two dev dependencies (mirrors what CI does, `ci.yml:17`):

```bash
pip install ruff pytest
```

Then run lint and tests the same way CI does:

```bash
python3 -m ruff check .          # lint (CLAUDE.md:15)
python3 -m pytest -v             # all tests (CLAUDE.md:18)
```

To run a single test class or case:

```bash
python3 -m pytest tests/test_logsum.py::TestGrouping::test_single_row_produces_one_group -v   # CLAUDE.md:21
```

CI runs these two steps in order on Python 3.11 (`CLAUDE.md:28`, `.github/workflows/ci.yml:20,23`). Running them locally in the same order reproduces the CI check exactly.

**Nothing could not be verified** — all claims above are directly traceable to lines in the files listed.

---

## Verification

| Citation | Verdict |
|---|---|
| `spec.md:53` | correct — "Group rows by the composite key `(service, level)` after normalisation has been applied." |
| `src/logsum.py:62` | correct — `g = groups[(service, level)]` is the key lookup |
| `src/logsum.py:31–36` | correct — blank check at 31, stderr warning at 33, `raw_level.upper() or UNKNOWN_LEVEL` return at 36 |
| `spec.md:120–122` | correct — "Blank-level rows are counted (assigned to `UNKNOWN`); malformed-timestamp rows are not counted at all." |
| `CLAUDE.md:15,18,21,28` | correct — line 15 `ruff check`, line 18 `pytest -v`, line 21 single-test command, line 28 CI description |
