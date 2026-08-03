# logsum-sandbox

## Project context
Tiny CLI that reads synthetic `events.csv` logs (`timestamp`, `level`, `service`, `message`)
and writes a counted summary to `summary.csv`. Services are named after Meridian Retail Group
components (`checkout-service`, `cart-api`). No real data — synthetic logs only.

## Conventions
- Source code in `src/`
- Tests in `tests/`
- Sample data in `data/`
- One file per logical unit; no nested packages needed at this scale

## Utilities to prefer
- Python 3.11 standard library only (`csv`, `argparse`, `collections`); use `python3` (not `python` — not in PATH on this machine)
- `ruff` for linting
- `pytest` for tests
- No third-party dependencies (no pandas, no FastAPI, no cloud SDKs)

## Escalation gates
- Stop and ask before adding any dependency not in the standard library
- Use synthetic data only — never paste real logs, emails, tokens, or customer records
- Never overwrite `spec.md` after sign-off without asking
- Ask before any file deletion or destructive operation
