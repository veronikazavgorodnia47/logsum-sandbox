"""logsum — aggregate events.csv into summary.csv grouped by (service, level)."""

import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime

REQUIRED_COLUMNS = {"timestamp", "level", "service", "message"}
UNKNOWN_LEVEL = "UNKNOWN"


def _valid_iso8601(value):
    try:
        datetime.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def _normalise_row(row, lineno):
    """Return (service, level, ts) for a valid row, or None to skip."""
    ts = row["timestamp"].strip()
    if not _valid_iso8601(ts):
        print(
            f"warning: line {lineno}: malformed timestamp {ts!r} — row skipped",
            file=sys.stderr,
        )
        return None
    raw_level = row["level"].strip()
    if not raw_level:
        print(
            f"warning: line {lineno}: blank level replaced with {UNKNOWN_LEVEL}",
            file=sys.stderr,
        )
    return row["service"].strip(), raw_level.upper() or UNKNOWN_LEVEL, ts


def process(input_path, output_path):
    skipped = 0
    groups = defaultdict(lambda: {"count": 0, "first_seen": None, "last_seen": None})

    try:
        with open(input_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames  # triggers header read
            if not fieldnames:
                return _write_output(output_path, [])
            missing = REQUIRED_COLUMNS - {f.strip() for f in fieldnames}
            if missing:
                print(
                    f"error: missing required columns: {', '.join(sorted(missing))}",
                    file=sys.stderr,
                )
                return 1
            for lineno, row in enumerate(reader, start=2):
                result = _normalise_row(row, lineno)
                if result is None:
                    skipped += 1
                    continue
                service, level, ts = result
                g = groups[(service, level)]
                g["count"] += 1
                if g["first_seen"] is None or ts < g["first_seen"]:
                    g["first_seen"] = ts
                if g["last_seen"] is None or ts > g["last_seen"]:
                    g["last_seen"] = ts
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    rows = sorted(
        [
            {
                "service": service,
                "level": level,
                "count": g["count"],
                "first_seen": g["first_seen"],
                "last_seen": g["last_seen"],
            }
            for (service, level), g in groups.items()
        ],
        key=lambda r: (r["service"], r["level"]),
    )

    if skipped:
        print(
            f"info: {skipped} row(s) skipped due to malformed timestamps",
            file=sys.stderr,
        )

    return _write_output(output_path, rows)


def _write_output(output_path, rows):
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["service", "level", "count", "first_seen", "last_seen"],
            )
            writer.writeheader()
            writer.writerows(rows)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate events.csv by (service, level)."
    )
    parser.add_argument(
        "--input",
        default="data/events.csv",
        metavar="PATH",
        help="Input events CSV (default: data/events.csv)",
    )
    parser.add_argument(
        "--output",
        default="data/summary.csv",
        metavar="PATH",
        help="Output summary CSV (default: data/summary.csv)",
    )
    args = parser.parse_args()
    sys.exit(process(args.input, args.output))


if __name__ == "__main__":
    main()
