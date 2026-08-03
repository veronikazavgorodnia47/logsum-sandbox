"""
Pytest tests for the logsum CLI.
Derived entirely from spec.md — src/logsum.py is intentionally not read.

Coverage:
  - Grouping by (service, level) after normalisation
  - Normalisation: whitespace stripping, level uppercasing, blank→UNKNOWN
  - Aggregation: count, first_seen, last_seen
  - Sort order: service asc, level asc
  - Malformed timestamp: row skipped, 1-based line warning, end total
  - Empty input: header-only and zero-byte file
  - Missing required columns: exit 1 + stderr
  - Duplicate header row treated as data
  - CLI paths: custom and default
  - Exit codes and stdout silence
"""
import csv

from conftest import (
    HEADER,
    R_CART_INFO,
    R_CART_WARN,
    R_CO_ERROR,
    R_CO_INFO_1,
    R_CO_INFO_2,
    read_summary,
    run_logsum,
    run_logsum_defaults,
    write_csv,
)

# ── Grouping ──────────────────────────────────────────────────────────────────

class TestGrouping:
    def test_single_row_produces_one_group(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        r = run_logsum(f, out)
        assert r.returncode == 0
        rows = read_summary(out)
        assert len(rows) == 1

    def test_two_rows_same_key_merged(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CO_INFO_2])
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 1

    def test_two_rows_different_level_two_groups(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CO_ERROR])
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 2
        keys = {(r["service"], r["level"]) for r in rows}
        assert keys == {("checkout-service", "INFO"), ("checkout-service", "ERROR")}

    def test_two_rows_different_service_two_groups(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CART_INFO])
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 2
        assert {r["service"] for r in rows} == {"checkout-service", "cart-api"}

    def test_columns_accepted_in_any_order(self, tmp_path, out):
        lines = [
            "service,message,level,timestamp",
            "checkout-service,msg,INFO,2024-01-01T10:00:00",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        assert r.returncode == 0
        rows = read_summary(out)
        assert len(rows) == 1
        assert rows[0]["service"] == "checkout-service"


# ── Aggregation ───────────────────────────────────────────────────────────────

class TestAggregation:
    def test_count_single_row(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        run_logsum(f, out)
        assert read_summary(out)[0]["count"] == "1"

    def test_count_multiple_rows_in_group(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CO_INFO_2])
        run_logsum(f, out)
        assert read_summary(out)[0]["count"] == "2"

    def test_first_seen_is_lexicographic_minimum(self, tmp_path, out):
        # Rows supplied in reverse chronological order
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_2, R_CO_INFO_1])
        run_logsum(f, out)
        assert read_summary(out)[0]["first_seen"] == "2024-01-01T10:00:00"

    def test_last_seen_is_lexicographic_maximum(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CO_INFO_2])
        run_logsum(f, out)
        assert read_summary(out)[0]["last_seen"] == "2024-01-01T11:00:00"

    def test_single_row_first_equals_last(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        run_logsum(f, out)
        row = read_summary(out)[0]
        assert row["first_seen"] == row["last_seen"] == "2024-01-01T10:00:00"

    def test_output_has_all_required_columns(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        run_logsum(f, out)
        row = read_summary(out)[0]
        assert set(row.keys()) == {"service", "level", "count", "first_seen", "last_seen"}


# ── Sort order ────────────────────────────────────────────────────────────────

class TestSortOrder:
    def test_sorted_by_service_ascending_then_level_ascending(self, tmp_path, out):
        lines = [
            HEADER,
            "2024-01-01T10:00:00,WARN,checkout-service,msg",
            "2024-01-01T10:00:00,ERROR,checkout-service,msg",
            "2024-01-01T10:00:00,INFO,checkout-service,msg",
            R_CART_INFO,
            R_CART_WARN,
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        keys = [(r["service"], r["level"]) for r in rows]
        assert keys == [
            ("cart-api",         "INFO"),
            ("cart-api",         "WARN"),
            ("checkout-service", "ERROR"),
            ("checkout-service", "INFO"),
            ("checkout-service", "WARN"),
        ]


# ── Normalisation ─────────────────────────────────────────────────────────────

class TestNormalisation:
    def test_level_lowercased_input_is_uppercased(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [
            HEADER, "2024-01-01T10:00:00,error,checkout-service,msg",
        ])
        run_logsum(f, out)
        assert read_summary(out)[0]["level"] == "ERROR"

    def test_level_mixed_case_uppercased(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [
            HEADER, "2024-01-01T10:00:00,WaRn,checkout-service,msg",
        ])
        run_logsum(f, out)
        assert read_summary(out)[0]["level"] == "WARN"

    def test_leading_trailing_whitespace_stripped_from_level(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [
            HEADER, "2024-01-01T10:00:00,  INFO  ,checkout-service,msg",
        ])
        run_logsum(f, out)
        assert read_summary(out)[0]["level"] == "INFO"

    def test_leading_trailing_whitespace_stripped_from_service(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [
            HEADER, "2024-01-01T10:00:00,INFO,  checkout-service  ,msg",
        ])
        run_logsum(f, out)
        assert read_summary(out)[0]["service"] == "checkout-service"

    def test_whitespace_normalised_rows_with_same_key_grouped(self, tmp_path, out):
        lines = [
            HEADER,
            "2024-01-01T10:00:00,  info  ,  checkout-service  ,msg1",
            "2024-01-01T11:00:00,INFO,checkout-service,msg2",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 1
        assert rows[0]["count"] == "2"

    def test_blank_level_becomes_unknown(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [
            HEADER, "2024-01-01T10:00:00,,checkout-service,msg",
        ])
        r = run_logsum(f, out)
        assert r.returncode == 0
        rows = read_summary(out)
        assert any(row["level"] == "UNKNOWN" for row in rows)

    def test_whitespace_only_level_becomes_unknown(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [
            HEADER, "2024-01-01T10:00:00,   ,checkout-service,msg",
        ])
        run_logsum(f, out)
        rows = read_summary(out)
        assert any(row["level"] == "UNKNOWN" for row in rows)

    def test_blank_level_row_is_counted_in_unknown_group(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [
            HEADER,
            "2024-01-01T10:00:00,,checkout-service,first",
            "2024-01-01T11:00:00,,checkout-service,second",
        ])
        run_logsum(f, out)
        rows = read_summary(out)
        unknown = [r for r in rows if r["level"] == "UNKNOWN"]
        assert len(unknown) == 1
        assert unknown[0]["count"] == "2"

    def test_blank_level_warning_written_to_stderr(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [
            HEADER, "2024-01-01T10:00:00,,checkout-service,msg",
        ])
        r = run_logsum(f, out)
        assert r.stderr.strip()

    def test_explicit_unknown_level_and_blank_level_merge_into_one_group(self, tmp_path, out):
        # Spec: blank level → UNKNOWN after normalisation.
        # A row with level="UNKNOWN" and a row with level="" must land in the same group.
        lines = [
            HEADER,
            "2024-01-01T10:00:00,UNKNOWN,checkout-service,explicit",
            "2024-01-01T11:00:00,,checkout-service,blank",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        unknown_rows = [r for r in rows if r["level"] == "UNKNOWN"]
        assert len(unknown_rows) == 1
        assert unknown_rows[0]["count"] == "2"

    def test_mixed_case_level_variants_all_merge_into_one_group(self, tmp_path, out):
        # "error", "ERROR", "Error" must all normalise to ERROR and form one group.
        lines = [
            HEADER,
            "2024-01-01T10:00:00,error,checkout-service,a",
            "2024-01-01T11:00:00,ERROR,checkout-service,b",
            "2024-01-01T12:00:00,Error,checkout-service,c",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        error_rows = [r for r in rows if r["level"] == "ERROR"]
        assert len(error_rows) == 1
        assert error_rows[0]["count"] == "3"


# ── Malformed timestamps ──────────────────────────────────────────────────────

class TestMalformedTimestamp:
    def test_malformed_row_not_included_in_count(self, tmp_path, out):
        lines = [HEADER, "not-a-timestamp,INFO,checkout-service,msg"]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        assert r.returncode == 0
        # Row skipped → no groups produced
        assert read_summary(out) == []

    def test_malformed_row_does_not_produce_group(self, tmp_path, out):
        lines = [HEADER, "????-??-??,INFO,checkout-service,msg"]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        assert read_summary(out) == []

    def test_valid_rows_still_counted_when_others_malformed(self, tmp_path, out):
        lines = [
            HEADER,
            R_CO_INFO_1,
            "bad-timestamp,INFO,checkout-service,msg",
            R_CO_INFO_2,
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["count"] == "2"

    def test_malformed_row_warning_written_to_stderr(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "bad-ts,INFO,checkout-service,msg"])
        r = run_logsum(f, out)
        assert r.stderr.strip()

    def test_warning_includes_1based_line_number_of_bad_row(self, tmp_path, out):
        # Header=line 1, good data=line 2, bad data=line 3
        lines = [HEADER, R_CO_INFO_1, "bad-ts,INFO,checkout-service,msg"]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        assert "3" in r.stderr

    def test_warning_line_number_accounts_for_header(self, tmp_path, out):
        # Header=1, bad row=2 → line number 2 in warning
        f = write_csv(tmp_path / "e.csv", [HEADER, "bad-ts,INFO,checkout-service,msg"])
        r = run_logsum(f, out)
        assert "2" in r.stderr

    def test_total_skipped_count_reported_at_end_of_stderr(self, tmp_path, out):
        # Two malformed rows → final stderr line must mention "2"
        lines = [
            HEADER,
            "bad-1,INFO,checkout-service,a",
            "bad-2,ERROR,cart-api,b",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        last_line = [l for l in r.stderr.splitlines() if l.strip()][-1]
        assert "2" in last_line

    def test_duplicate_header_row_treated_as_data_and_skipped(self, tmp_path, out):
        # Second occurrence of the header has "timestamp" as its timestamp field,
        # which is not valid ISO-8601 → must produce a skip warning.
        lines = [HEADER, HEADER, R_CO_INFO_1]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        assert r.returncode == 0
        assert r.stderr.strip()  # warning for the duplicate header row

    def test_malformed_timestamp_with_blank_level_skipped_not_counted_in_unknown(self, tmp_path, out):
        # Spec asymmetry: malformed timestamp → row discarded entirely.
        # Even though level is blank (→ UNKNOWN), the timestamp failure takes precedence
        # and the row must NOT appear in any group, including UNKNOWN.
        lines = [
            HEADER,
            "bad-ts,,checkout-service,both conditions",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        assert r.returncode == 0
        rows = read_summary(out)
        assert rows == []  # nothing counted; UNKNOWN group must not exist


# ── Empty input ───────────────────────────────────────────────────────────────

class TestEmptyInput:
    def test_header_only_exits_0(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER])
        r = run_logsum(f, out)
        assert r.returncode == 0

    def test_header_only_writes_summary_file(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER])
        run_logsum(f, out)
        assert out.exists()

    def test_header_only_summary_has_no_data_rows(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER])
        run_logsum(f, out)
        assert read_summary(out) == []

    def test_header_only_summary_has_correct_columns(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER])
        run_logsum(f, out)
        with open(out, newline="") as fh:
            col_names = next(csv.reader(fh))
        assert set(col_names) == {"service", "level", "count", "first_seen", "last_seen"}

    def test_zero_byte_file_exits_0(self, tmp_path, out):
        f = tmp_path / "e.csv"
        f.write_bytes(b"")
        r = run_logsum(f, out)
        assert r.returncode == 0

    def test_zero_byte_file_writes_summary_file(self, tmp_path, out):
        f = tmp_path / "e.csv"
        f.write_bytes(b"")
        run_logsum(f, out)
        assert out.exists()

    def test_zero_byte_file_summary_has_no_data_rows(self, tmp_path, out):
        f = tmp_path / "e.csv"
        f.write_bytes(b"")
        run_logsum(f, out)
        assert read_summary(out) == []


# ── Missing required columns ──────────────────────────────────────────────────

class TestMissingRequiredColumns:
    def test_missing_timestamp_column_exits_1(self, tmp_path, out):
        lines = ["level,service,message", "INFO,checkout-service,msg"]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        assert r.returncode == 1

    def test_missing_timestamp_column_message_on_stderr(self, tmp_path, out):
        lines = ["level,service,message", "INFO,checkout-service,msg"]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        assert r.stderr.strip()

    def test_missing_level_column_exits_1(self, tmp_path, out):
        lines = ["timestamp,service,message", "2024-01-01T10:00:00,checkout-service,msg"]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        assert r.returncode == 1

    def test_missing_service_column_exits_1(self, tmp_path, out):
        lines = ["timestamp,level,message", "2024-01-01T10:00:00,INFO,msg"]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        assert r.returncode == 1

    def test_missing_multiple_required_columns_exits_1(self, tmp_path, out):
        lines = ["message", "some log line"]
        f = write_csv(tmp_path / "e.csv", lines)
        r = run_logsum(f, out)
        assert r.returncode == 1
        assert r.stderr.strip()


# ── CLI paths and exit codes ──────────────────────────────────────────────────

class TestCLI:
    def test_custom_input_and_output_paths(self, tmp_path):
        inp = tmp_path / "custom_in.csv"
        out = tmp_path / "custom_out.csv"
        write_csv(inp, [HEADER, R_CO_INFO_1])
        r = run_logsum(inp, out)
        assert r.returncode == 0
        assert out.exists()

    def test_default_input_and_output_paths(self, tmp_path):
        # Spec defaults: --input data/events.csv  --output data/summary.csv
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        write_csv(data_dir / "events.csv", [HEADER, R_CO_INFO_1])
        r = run_logsum_defaults(tmp_path)
        assert r.returncode == 0
        assert (data_dir / "summary.csv").exists()

    def test_missing_input_file_exits_1(self, tmp_path, out):
        nonexistent = tmp_path / "no_such_file.csv"
        r = run_logsum(nonexistent, out)
        assert r.returncode == 1

    def test_missing_input_file_message_on_stderr(self, tmp_path, out):
        nonexistent = tmp_path / "no_such_file.csv"
        r = run_logsum(nonexistent, out)
        assert r.stderr.strip()

    def test_exit_0_on_success(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        r = run_logsum(f, out)
        assert r.returncode == 0

    def test_no_user_facing_text_on_stdout(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        r = run_logsum(f, out)
        assert r.stdout == ""

    def test_warnings_go_to_stderr_not_stdout(self, tmp_path, out):
        # Blank level triggers a warning — must appear on stderr only
        f = write_csv(tmp_path / "e.csv", [
            HEADER, "2024-01-01T10:00:00,,checkout-service,msg",
        ])
        r = run_logsum(f, out)
        assert r.stdout == ""
        assert r.stderr.strip()

    def test_output_directory_does_not_exist_exits_1(self, tmp_path):
        # Spec: "I/O error … exit 1"
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        bad_out = tmp_path / "no_such_dir" / "summary.csv"
        r = run_logsum(f, bad_out)
        assert r.returncode == 1
        assert r.stderr.strip()


# ── --min-count filter ────────────────────────────────────────────────────────

class TestMinCount:
    def test_groups_below_threshold_excluded(self, tmp_path, out):
        # checkout-service/INFO has count=1, cart-api/INFO has count=2
        lines = [
            HEADER,
            R_CO_INFO_1,
            R_CART_INFO,
            "2024-01-02T11:00:00,INFO,cart-api,second",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out, extra_args=["--min-count", "2"])
        rows = read_summary(out)
        assert all(int(r["count"]) >= 2 for r in rows)
        assert not any(r["service"] == "checkout-service" for r in rows)

    def test_groups_at_threshold_included(self, tmp_path, out):
        # count == N exactly must be included (boundary)
        lines = [HEADER, R_CO_INFO_1, R_CO_INFO_2]  # checkout-service/INFO count=2
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out, extra_args=["--min-count", "2"])
        rows = read_summary(out)
        assert len(rows) == 1
        assert rows[0]["count"] == "2"

    def test_groups_above_threshold_included(self, tmp_path, out):
        # count=3 passes --min-count 2
        lines = [
            HEADER,
            R_CO_INFO_1,
            R_CO_INFO_2,
            "2024-01-01T12:00:00,INFO,checkout-service,third",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out, extra_args=["--min-count", "2"])
        rows = read_summary(out)
        assert len(rows) == 1
        assert rows[0]["count"] == "3"

    def test_min_count_1_includes_all_groups(self, tmp_path, out):
        # --min-count 1 is equivalent to the default: nothing filtered
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CART_INFO])
        run_logsum(f, out, extra_args=["--min-count", "1"])
        assert len(read_summary(out)) == 2

    def test_min_count_above_all_counts_produces_header_only_output(self, tmp_path, out):
        # All groups have count=1; --min-count 99 → nothing passes → header-only output
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CART_INFO])
        r = run_logsum(f, out, extra_args=["--min-count", "99"])
        assert r.returncode == 0
        assert read_summary(out) == []
        assert out.exists()

    def test_default_behaviour_unchanged(self, tmp_path, out):
        # Omitting --min-count keeps all groups (regression guard)
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CART_INFO])
        run_logsum(f, out)
        assert len(read_summary(out)) == 2
