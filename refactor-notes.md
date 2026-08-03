# refactor-notes.md

## Removed by AI in the refactor

- `ts = row["timestamp"].strip()` (inline in loop). AI reason: moved into `_normalise_row` to consolidate field normalisation.
  My decision: keep removed — behaviour preserved, now lives in the helper.

- `if not _valid_iso8601(ts): print(...warning...); skipped += 1; continue` (inline in loop). AI reason: moved into `_normalise_row`; caller checks `result is None` and increments `skipped`.
  My decision: keep removed — skip logic intact, warning still emitted with correct line number.

- `raw_level = row["level"].strip()` (inline in loop). AI reason: moved into `_normalise_row`.
  My decision: keep removed — behaviour preserved.

- `if not raw_level: print(...warning...)` (inline in loop). AI reason: moved into `_normalise_row`.
  My decision: keep removed — blank-level warning still emitted before normalisation.

- `level = raw_level.upper() if raw_level else UNKNOWN_LEVEL` (inline in loop). AI reason: replaced by `raw_level.upper() or UNKNOWN_LEVEL` in `_normalise_row`; equivalent because `"".upper() == ""` which is falsy.
  My decision: keep removed — equivalence verified: non-empty string `.upper()` is always truthy; empty string `.upper()` is always falsy, so `or UNKNOWN_LEVEL` fires in exactly the same cases.

- `service = row["service"].strip()` (inline in loop). AI reason: moved into `_normalise_row` return value.
  My decision: keep removed — behaviour preserved.

- `key = (service, level)` (inline in loop). AI reason: inlined as `groups[(service, level)]`; no semantic change.
  My decision: keep removed — one less intermediate variable, clearer.
