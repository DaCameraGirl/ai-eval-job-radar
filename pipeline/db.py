"""DuckDB connection helper.

The warehouse file is disposable. It is rebuilt from the tracked text files in
``data/`` (``platforms.yml``, ``status_snapshot.csv``, ``discovered_candidates.yml``),
so it is gitignored on purpose.
"""
from __future__ import annotations

import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
WAREHOUSE = Path(os.environ.get("RADAR_DUCKDB", ROOT / "warehouse" / "radar.duckdb"))


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open (and if needed create) the radar DuckDB warehouse."""
    WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(WAREHOUSE), read_only=read_only)
