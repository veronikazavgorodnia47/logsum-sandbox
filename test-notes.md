# test-notes.md

## Overview

52 pytest tests across `tests/test_logsum.py`, derived from `spec.md` only.
All tests drive the CLI via subprocess (`python -m logsum`); `src/logsum.py` is not imported directly.

## Test classes

| Class | Tests | What it covers |
|---|---|---|
| `TestGrouping` | 5 | Rows grouped by `(service, level)`; any column order in header |
| `TestAggregation` | 6 | `count`, `first_seen`, `last_seen`, output column names |
| `TestSortOrder` | 1 | service asc → level asc |
| `TestNormalisation` | 11 | Whitespace strip, level uppercase, blank/whitespace-only → `UNKNOWN`, stderr warning |
| `TestMalformedTimestamp` | 9 | Row skipped, 1-based line number in warning, end total, duplicate header row |
| `TestEmptyInput` | 7 | Header-only and zero-byte file → exit 0 + header-only output |
| `TestMissingRequiredColumns` | 5 | Each of `timestamp`/`level`/`service` absent → exit 1 + stderr |
| `TestCLI` | 8 | Custom paths, default paths, missing input, bad output dir, exit codes, no stdout |

## Hard edge cases

| Test | Risk it guards against |
|---|---|
| `test_explicit_unknown_level_and_blank_level_merge_into_one_group` | Grouping on raw value before normalisation → two groups instead of one |
| `test_mixed_case_level_variants_all_merge_into_one_group` | Uppercasing output but grouping on original value → three groups instead of one |
| `test_malformed_timestamp_with_blank_level_skipped_not_counted_in_unknown` | Assigning `UNKNOWN` before validating timestamp → discarded row counted in output |
| `test_output_directory_does_not_exist_exits_1` | Guarding only input I/O → unhandled exception instead of clean exit 1 |

## Running

```
python3 -m pytest -v
```

Requires `pytest` (`pip3 install pytest`). No other dependencies beyond the standard library.
