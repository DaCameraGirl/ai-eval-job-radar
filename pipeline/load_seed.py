"""Load the tracked source-of-truth files into the DuckDB ``raw`` schema.

This never writes back to the source files. It only reads them into the
disposable warehouse so dbt can build the analytics marts on top.
"""
from __future__ import annotations

import yaml

from .db import DATA_DIR, connect


def _platform_rows() -> list[dict]:
    with open(DATA_DIR / "platforms.yml", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    rows = []
    for p in doc.get("platforms", []):
        rows.append(
            {
                "id": p["id"],
                "name": p["name"],
                "url": p["url"],
                "signup_url": p.get("signup_url", p["url"]),
                "category": p["category"],
                "tier": int(p["tier"]),
                "fit_notes": p.get("fit_notes", ""),
                "pay_notes": p.get("pay_notes", ""),
                "tags": ",".join(p.get("tags", [])),
            }
        )
    return rows


def _discovered_rows() -> list[dict]:
    path = DATA_DIR / "discovered_candidates.yml"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    return doc.get("candidates", []) or []


def load() -> None:
    con = connect()
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")

        # platforms (always present)
        platforms = _platform_rows()
        con.register("platforms_df", _as_relation(con, platforms))
        con.execute("CREATE OR REPLACE TABLE raw.platforms AS SELECT * FROM platforms_df")
        con.unregister("platforms_df")

        # status snapshot (optional; create an empty typed table if missing)
        snap = DATA_DIR / "status_snapshot.csv"
        if snap.exists():
            con.execute(
                "CREATE OR REPLACE TABLE raw.status_snapshot AS "
                f"SELECT * FROM read_csv_auto('{snap.as_posix()}', header=true)"
            )
        else:
            con.execute(
                "CREATE OR REPLACE TABLE raw.status_snapshot ("
                "id VARCHAR, link_ok BOOLEAN, status_code INTEGER, "
                "signup_status VARCHAR, checked_at TIMESTAMP)"
            )

        # discovered candidates (optional)
        discovered = _discovered_rows()
        if discovered:
            con.register("discovered_df", _as_relation(con, discovered))
            con.execute(
                "CREATE OR REPLACE TABLE raw.discovered AS SELECT * FROM discovered_df"
            )
            con.unregister("discovered_df")
        else:
            con.execute(
                "CREATE OR REPLACE TABLE raw.discovered ("
                "domain VARCHAR, name VARCHAR, source_query VARCHAR, found_at TIMESTAMP)"
            )

        n = con.execute("SELECT count(*) FROM raw.platforms").fetchone()[0]
        print(f"[load_seed] loaded {n} platforms into raw.platforms")
    finally:
        con.close()


def _as_relation(con, rows: list[dict]):
    """Turn a list of dicts into something DuckDB can SELECT from."""
    import pandas as pd

    return pd.DataFrame(rows)


if __name__ == "__main__":
    load()
