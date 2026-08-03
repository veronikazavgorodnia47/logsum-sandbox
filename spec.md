# logsum-sandbox — CLI specification

## Goal

Read `events.csv`, group rows by `(service, level)`, and write an aggregated
`summary.csv` containing a count and timestamp range for each group.

---

## Inputs

| Field       | Type   | Notes                              |
|-------------|--------|------------------------------------|
| `timestamp` | string | Expected ISO-8601; malformed rows are skipped (see Edge cases) |
| `level`     | string | e.g. `INFO`, `WARN`, `ERROR`       |
| `service`   | string | e.g. `checkout-service`, `cart-api` |
| `message`   | string | Free text; not used in grouping    |

- File must contain a header row with exactly the four columns above (any order).
- If any of `timestamp`, `level`, or `service` columns are absent, the program
  exits with code 1 and a descriptive message on stderr.

---

## Outputs

`summary.csv` — one row per unique `(service, level)` pair.

| Column       | Type   | Notes                                    |
|--------------|--------|------------------------------------------|
| `service`    | string | Stripped; preserved as-is               |
| `level`      | string | Uppercased after normalisation           |
| `count`      | int    | Number of input rows in this group       |
| `first_seen` | string | ISO-8601 timestamp of earliest row       |
| `last_seen`  | string | ISO-8601 timestamp of latest row         |

Rows are sorted by `service` (ascending) then `level` (ascending).

---

## Normalisation rules

1. Strip leading and trailing whitespace from every field before processing.
2. Uppercase `level` (`error` → `ERROR`, `warn` → `WARN`, etc.).
3. `service` is left as-is after stripping (synthetic names are already lowercase).
4. A blank `level` after stripping is replaced with the sentinel `UNKNOWN`; a
   warning is written to stderr.

---

## Grouping rule

Group rows by the composite key `(service, level)` after normalisation has been applied.
Each unique pair produces exactly one row in the output.

---

## Aggregation

For each group:
- `count` — total number of input rows in the group (malformed-timestamp rows
  excluded)
- `first_seen` — the lexicographically smallest valid ISO-8601 timestamp in
  the group
- `last_seen` — the lexicographically largest valid ISO-8601 timestamp in the
  group

---

## Edge cases

| Scenario | Behaviour |
|---|---|
| **Missing level** | Replace with `UNKNOWN`; warn to stderr; include in output |
| **Malformed timestamp** | Skip row; warn to stderr with 1-based line number; report total skipped count at end |
| **Empty input** (header only or zero-byte file) | Write header-only `summary.csv`; exit 0 |
| **Duplicate header row** | Treated as a data row; will produce a skipped-timestamp warning |

---

## CLI

```
python -m logsum [--input PATH] [--output PATH]
```

| Flag | Default | Description |
|---|---|---|
| `--input PATH` | `data/events.csv` | Path to the input events file |
| `--output PATH` | `data/summary.csv` | Path for the written summary file |

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Success (including empty-input case) |
| `1` | I/O error, missing required columns, or unrecoverable failure |

Warnings and the final skip-count line are written to **stderr**; no user-facing
text goes to stdout.

---

## Out of scope

- Filtering by date range, level, or service
- Deduplication of identical rows
- Any output format other than CSV (no JSON, no SQLite)
- Streaming / chunked processing for files that do not fit in memory
- Internationalisation or locale-aware timestamp parsing
- Remote or database I/O
- A watch / tail mode for live log files

---

## Signed off

VZ — 2026-08-03
