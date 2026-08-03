"""
Integration tests for logsum CLI.
All tests drive the CLI via subprocess; src/logsum.py is never imported directly.
"""
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
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 1

    def test_two_rows_same_key_produce_one_group(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CO_INFO_2])
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 1

    def test_two_rows_different_service_produce_two_groups(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CART_INFO])
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 2

    def test_two_rows_different_level_produce_two_groups(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CO_ERROR])
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 2

    def test_grouping_key_is_service_and_level_combined(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CO_INFO_2, R_CO_ERROR, R_CART_INFO, R_CART_WARN])
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 4


# ── Aggregation ───────────────────────────────────────────────────────────────

class TestAggregation:
    def test_count_reflects_number_of_rows_in_group(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CO_INFO_2])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["count"] == "2"

    def test_first_seen_is_earliest_timestamp(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_2, R_CO_INFO_1])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["first_seen"] == "2024-01-01T10:00:00"

    def test_last_seen_is_latest_timestamp(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CO_INFO_2])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["last_seen"] == "2024-01-01T11:00:00"

    def test_first_seen_equals_last_seen_for_single_row_group(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["first_seen"] == rows[0]["last_seen"]

    def test_output_has_five_columns(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        run_logsum(f, out)
        rows = read_summary(out)
        assert set(rows[0].keys()) == {"service", "level", "count", "first_seen", "last_seen"}

    def test_service_and_level_preserved_in_output(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_ERROR])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["service"] == "checkout-service"
        assert rows[0]["level"] == "ERROR"


# ── Sort order ────────────────────────────────────────────────────────────────

class TestSortOrder:
    def test_output_sorted_by_service_then_level(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CART_WARN, R_CO_INFO_1, R_CART_INFO, R_CO_ERROR])
        run_logsum(f, out)
        rows = read_summary(out)
        keys = [(r["service"], r["level"]) for r in rows]
        assert keys == sorted(keys)


# ── Normalisation ─────────────────────────────────────────────────────────────

class TestNormalisation:
    def test_level_uppercased(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "2024-01-01T10:00:00,info,checkout-service,msg"])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["level"] == "INFO"

    def test_mixed_case_level_uppercased(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "2024-01-01T10:00:00,WaRn,checkout-service,msg"])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["level"] == "WARN"

    def test_whitespace_stripped_from_service(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "2024-01-01T10:00:00,INFO, checkout-service ,msg"])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["service"] == "checkout-service"

    def test_whitespace_stripped_from_level(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "2024-01-01T10:00:00, INFO ,checkout-service,msg"])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["level"] == "INFO"

    def test_blank_level_replaced_with_unknown(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "2024-01-01T10:00:00,,checkout-service,msg"])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["level"] == "UNKNOWN"

    def test_blank_level_warning_on_stderr(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "2024-01-01T10:00:00,,checkout-service,msg"])
        result = run_logsum(f, out)
        assert "blank level" in result.stderr

    def test_blank_level_row_counted_in_output(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "2024-01-01T10:00:00,,checkout-service,msg"])
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 1
        assert rows[0]["count"] == "1"

    def test_explicit_unknown_level_and_blank_level_merge_into_one_group(self, tmp_path, out):
        lines = [
            HEADER,
            "2024-01-01T10:00:00,UNKNOWN,checkout-service,explicit",
            "2024-01-01T11:00:00,,checkout-service,blank",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 1
        assert rows[0]["level"] == "UNKNOWN"
        assert rows[0]["count"] == "2"

    def test_mixed_case_levels_merge_into_one_group(self, tmp_path, out):
        lines = [
            HEADER,
            "2024-01-01T10:00:00,info,checkout-service,a",
            "2024-01-01T11:00:00,INFO,checkout-service,b",
            "2024-01-01T12:00:00,Info,checkout-service,c",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 1
        assert rows[0]["count"] == "3"

    def test_whitespace_only_level_treated_as_blank(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "2024-01-01T10:00:00,   ,checkout-service,msg"])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["level"] == "UNKNOWN"

    def test_message_column_not_used_in_grouping(self, tmp_path, out):
        lines = [
            HEADER,
            "2024-01-01T10:00:00,INFO,checkout-service,first message",
            "2024-01-01T11:00:00,INFO,checkout-service,second message",
        ]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 1


# ── Malformed timestamps ──────────────────────────────────────────────────────

class TestMalformedTimestamp:
    def test_malformed_timestamp_row_skipped(self, tmp_path, out):
        lines = [HEADER, "not-a-date,INFO,checkout-service,msg", R_CO_INFO_1]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 1

    def test_malformed_timestamp_warning_on_stderr(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "not-a-date,INFO,checkout-service,msg"])
        result = run_logsum(f, out)
        assert "malformed timestamp" in result.stderr

    def test_malformed_timestamp_warning_includes_line_number(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "not-a-date,INFO,checkout-service,msg"])
        result = run_logsum(f, out)
        assert "line 2" in result.stderr

    def test_skip_count_reported_on_stderr(self, tmp_path, out):
        lines = [HEADER, "bad,INFO,checkout-service,a", "bad,INFO,checkout-service,b"]
        f = write_csv(tmp_path / "e.csv", lines)
        result = run_logsum(f, out)
        assert "2 row(s) skipped" in result.stderr

    def test_malformed_timestamp_row_not_counted_in_group(self, tmp_path, out):
        lines = [HEADER, "bad,INFO,checkout-service,a", R_CO_INFO_1]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows[0]["count"] == "1"

    def test_duplicate_header_row_skipped_as_malformed(self, tmp_path, out):
        lines = [HEADER, HEADER, R_CO_INFO_1]
        f = write_csv(tmp_path / "e.csv", lines)
        result = run_logsum(f, out)
        assert "malformed timestamp" in result.stderr

    def test_malformed_timestamp_and_blank_level_row_skipped_not_counted_as_unknown(self, tmp_path, out):
        lines = [HEADER, "bad,,checkout-service,msg", R_CO_INFO_1]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out)
        rows = read_summary(out)
        assert not any(r["level"] == "UNKNOWN" for r in rows)
        assert len(rows) == 1

    def test_exit_0_when_all_rows_malformed(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "bad,INFO,checkout-service,msg"])
        result = run_logsum(f, out)
        assert result.returncode == 0

    def test_header_only_output_when_all_rows_malformed(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "bad,INFO,checkout-service,msg"])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows == []


# ── Empty input ───────────────────────────────────────────────────────────────

class TestEmptyInput:
    def test_header_only_input_produces_header_only_output(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER])
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows == []

    def test_header_only_input_exits_0(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER])
        result = run_logsum(f, out)
        assert result.returncode == 0

    def test_zero_byte_file_exits_0(self, tmp_path, out):
        f = tmp_path / "e.csv"
        f.write_text("")
        result = run_logsum(f, out)
        assert result.returncode == 0

    def test_zero_byte_file_produces_header_only_output(self, tmp_path, out):
        f = tmp_path / "e.csv"
        f.write_text("")
        run_logsum(f, out)
        rows = read_summary(out)
        assert rows == []

    def test_output_csv_has_correct_header_columns(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER])
        run_logsum(f, out)
        with open(out) as fh:
            header_line = fh.readline().strip()
        assert header_line == "service,level,count,first_seen,last_seen"

    def test_no_stdout_on_empty_input(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER])
        result = run_logsum(f, out)
        assert result.stdout == ""

    def test_default_paths_used_when_no_flags_given(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        write_csv(data_dir / "events.csv", [HEADER])
        result = run_logsum_defaults(tmp_path)
        assert result.returncode == 0
        assert (data_dir / "summary.csv").exists()


# ── Missing required columns ──────────────────────────────────────────────────

class TestMissingRequiredColumns:
    def test_missing_timestamp_column_exits_1(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", ["level,service,message", "INFO,checkout-service,msg"])
        result = run_logsum(f, out)
        assert result.returncode == 1

    def test_missing_timestamp_column_message_on_stderr(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", ["level,service,message", "INFO,checkout-service,msg"])
        result = run_logsum(f, out)
        assert "timestamp" in result.stderr

    def test_missing_level_column_exits_1(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", ["timestamp,service,message", "2024-01-01T10:00:00,checkout-service,msg"])
        result = run_logsum(f, out)
        assert result.returncode == 1

    def test_missing_service_column_exits_1(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", ["timestamp,level,message", "2024-01-01T10:00:00,INFO,msg"])
        result = run_logsum(f, out)
        assert result.returncode == 1

    def test_missing_multiple_required_columns_exits_1(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", ["message", "msg"])
        result = run_logsum(f, out)
        assert result.returncode == 1


# ── CLI ───────────────────────────────────────────────────────────────────────

class TestCLI:
    def test_custom_input_and_output_paths(self, tmp_path, out):
        f = write_csv(tmp_path / "custom.csv", [HEADER, R_CO_INFO_1])
        result = run_logsum(f, out)
        assert result.returncode == 0
        assert out.exists()

    def test_default_input_and_output_paths(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        write_csv(data_dir / "events.csv", [HEADER, R_CO_INFO_1])
        result = run_logsum_defaults(tmp_path)
        assert result.returncode == 0
        assert (data_dir / "summary.csv").exists()

    def test_missing_input_file_exits_1(self, tmp_path, out):
        result = run_logsum(tmp_path / "nonexistent.csv", out)
        assert result.returncode == 1

    def test_missing_input_file_message_on_stderr(self, tmp_path, out):
        result = run_logsum(tmp_path / "nonexistent.csv", out)
        assert result.stderr != ""

    def test_exit_0_on_success(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        result = run_logsum(f, out)
        assert result.returncode == 0

    def test_no_user_facing_text_on_stdout(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1])
        result = run_logsum(f, out)
        assert result.stdout == ""

    def test_warnings_go_to_stderr_not_stdout(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, "bad,,checkout-service,msg"])
        result = run_logsum(f, out)
        assert result.stdout == ""
        assert result.stderr != ""

    def test_output_directory_does_not_exist_exits_1(self, tmp_path, inp):
        write_csv(inp, [HEADER, R_CO_INFO_1])
        result = run_logsum(inp, tmp_path / "nonexistent_dir" / "out.csv")
        assert result.returncode == 1


# ── --min-count ───────────────────────────────────────────────────────────────

class TestMinCount:
    def test_groups_below_threshold_excluded(self, tmp_path, out):
        lines = [HEADER, R_CO_INFO_1, R_CART_INFO,
                 "2024-01-02T11:00:00,INFO,cart-api,second"]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out, extra_args=["--min-count", "2"])
        rows = read_summary(out)
        assert all(int(r["count"]) >= 2 for r in rows)
        assert not any(r["service"] == "checkout-service" for r in rows)

    def test_groups_at_threshold_included(self, tmp_path, out):
        lines = [HEADER, R_CO_INFO_1, R_CO_INFO_2]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out, extra_args=["--min-count", "2"])
        rows = read_summary(out)
        assert len(rows) == 1
        assert rows[0]["count"] == "2"

    def test_groups_above_threshold_included(self, tmp_path, out):
        lines = [HEADER, R_CO_INFO_1, R_CO_INFO_2,
                 "2024-01-01T13:00:00,INFO,checkout-service,extra"]
        f = write_csv(tmp_path / "e.csv", lines)
        run_logsum(f, out, extra_args=["--min-count", "2"])
        rows = read_summary(out)
        assert len(rows) == 1
        assert rows[0]["count"] == "3"

    def test_min_count_1_includes_all_groups(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CART_INFO])
        run_logsum(f, out, extra_args=["--min-count", "1"])
        rows = read_summary(out)
        assert len(rows) == 2

    def test_min_count_above_all_counts_produces_header_only_output(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CART_INFO])
        result = run_logsum(f, out, extra_args=["--min-count", "99"])
        assert result.returncode == 0
        rows = read_summary(out)
        assert rows == []

    def test_default_behaviour_unchanged(self, tmp_path, out):
        f = write_csv(tmp_path / "e.csv", [HEADER, R_CO_INFO_1, R_CART_INFO])
        run_logsum(f, out)
        rows = read_summary(out)
        assert len(rows) == 2
