# Context load check — K 5.W.1

**Session:** fresh Claude Code session opened at repo root
**File cited:** `CLAUDE.md`

## Agent summary by section

**Project context** — A CLI tool that reads synthetic events.csv logs and writes a counted
summary to summary.csv. Services are fictional Meridian Retail Group components; no real data
is used.

**Conventions** — Source in `src/`, tests in `tests/`, sample data in `data/`. One file per
logical unit, no nested packages.

**Utilities to prefer** — Python 3.11 stdlib only (`csv`, `argparse`, `collections`); ruff for
linting; pytest for tests; no third-party dependencies.

**Escalation gates** — Four hard stops: ask before adding non-stdlib dependencies, use synthetic
data only, never overwrite `spec.md` post-sign-off without asking, and ask before any file
deletion or destructive operation.

## Verdict
All four sections loaded and cited correctly. Context active.
