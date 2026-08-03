"""
Shared helpers and fixtures for logsum tests.
All spec-derived; src/logsum.py is not imported here.
"""
import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
PYTHON = sys.executable

# ── Canonical CSV header (any column order is valid per spec) ─────────────────
HEADER = "timestamp,level,service,message"

# ── Well-formed rows used across multiple tests ───────────────────────────────
R_CO_INFO_1  = "2024-01-01T10:00:00,INFO,checkout-service,order placed"
R_CO_INFO_2  = "2024-01-01T11:00:00,INFO,checkout-service,payment ok"
R_CO_ERROR   = "2024-01-01T12:00:00,ERROR,checkout-service,timeout"
R_CART_INFO  = "2024-01-02T09:00:00,INFO,cart-api,item added"
R_CART_WARN  = "2024-01-02T10:00:00,WARN,cart-api,slow query"


# ── Helper functions (not pytest fixtures) ────────────────────────────────────

def _env() -> dict:
    e = os.environ.copy()
    e["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    return e


def write_csv(path: Path, lines: list) -> Path:
    """Write *lines* joined by newlines to *path*; return *path*."""
    path.write_text("\n".join(lines) + "\n")
    return path


def read_summary(path: Path) -> list:
    """Return all rows from a summary CSV as a list of dicts."""
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def run_logsum(input_path: Path, output_path: Path) -> subprocess.CompletedProcess:
    """Invoke `python -m logsum` with explicit --input / --output paths."""
    return subprocess.run(
        [PYTHON, "-m", "logsum", "--input", str(input_path), "--output", str(output_path)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=_env(),
        check=False,
    )


def run_logsum_defaults(cwd: Path) -> subprocess.CompletedProcess:
    """Invoke `python -m logsum` with no path flags from *cwd*."""
    return subprocess.run(
        [PYTHON, "-m", "logsum"],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=_env(),
        check=False,
    )


# ── Pytest fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def out(tmp_path):
    """Pre-resolved output path inside a temp directory."""
    return tmp_path / "summary.csv"


@pytest.fixture
def inp(tmp_path):
    """Pre-resolved input path inside a temp directory."""
    return tmp_path / "events.csv"
