# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

Tiny CLI that reads synthetic `events.csv` logs (`timestamp`, `level`, `service`, `message`)
and writes a counted summary to `summary.csv`. Services are named after Meridian Retail Group
components (`checkout-service`, `cart-api`). No real data — synthetic logs only.

## Commands

```bash
# Lint
python3 -m ruff check .

# Run all tests
python3 -m pytest -v

# Run a single test
python3 -m pytest tests/test_logsum.py::TestGrouping::test_single_row_produces_one_group -v

# Run the CLI
PYTHONPATH=src python3 -m logsum --input data/sample_events.csv --output data/summary.csv
python3 -m logsum --help   # when run from src/
```

CI runs `ruff check .` then `pytest -v` on Python 3.11 (`.github/workflows/ci.yml`).

## Architecture

Single module: `src/logsum.py`. Three functions form the pipeline:

```
_normalise_row(row, lineno) → (service, level, ts) | None
        ↓
process(input_path, output_path, min_count=1) → int (exit code)
        ↓
_write_output(output_path, rows) → int (exit code)
```

- `_normalise_row` strips fields, validates the ISO-8601 timestamp (skip on failure), uppercases level, and replaces blank level with `UNKNOWN`. All per-row warnings are emitted here.
- `process` reads the CSV, checks required columns (`timestamp`, `level`, `service`, `message`), accumulates groups into a `defaultdict`, applies `--min-count` filter, then delegates to `_write_output`.
- `_write_output` writes the five-column summary CSV and is also called directly for empty-input cases.

`PYTHONPATH=src` is required to run `python3 -m logsum` from the project root. The test helpers in `tests/conftest.py` set this automatically via `subprocess.env`.

## Test helpers (tests/conftest.py)

- `run_logsum(input_path, output_path, extra_args=())` — runs the CLI via subprocess; use `extra_args=["--min-count", "2"]` to pass flags.
- `run_logsum_defaults(cwd)` — runs with no path flags from a given working directory.
- `write_csv(path, lines)` / `read_summary(path)` — write and read CSV fixtures.
- `HEADER`, `R_CO_INFO_1`, `R_CO_INFO_2`, `R_CO_ERROR`, `R_CART_INFO`, `R_CART_WARN` — reusable well-formed row strings.

## Conventions

- Source in `src/`, tests in `tests/`, sample data in `data/`
- Python 3.11 stdlib only (`csv`, `argparse`, `collections`, `datetime`); use `python3` (not `python`)
- No third-party dependencies (no pandas, no FastAPI, no cloud SDKs)

## Escalation gates

- Stop and ask before adding any dependency not in the standard library
- Use synthetic data only — never paste real logs, emails, tokens, or customer records
- Never overwrite `spec.md` after sign-off without asking
- Ask before any file deletion or destructive operation
