"""Weekly refresh orchestrator.

Order:
  1. check every platform link is alive
  2. sniff signup status (open / waitlist / closed / unknown)
  3. write a human-readable status snapshot (tracked CSV)
  4. optionally discover new platforms via Tavily (tracked YAML)
  5. rebuild the DuckDB warehouse + dbt marts

Flags let you run it offline (for a quick local dashboard rebuild) or skip the
paid discovery step.

Run from the repo root:
    python -m scripts.refresh
    python -m scripts.refresh --skip-network      # just rebuild marts from tracked files
    python -m scripts.refresh --skip-discovery    # check + sniff, but no Tavily
"""
from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline import check_links, detect_signup, discover, load_seed  # noqa: E402

DATA = ROOT / "data"
SNAPSHOT = DATA / "status_snapshot.csv"
CANDIDATES = DATA / "discovered_candidates.yml"


def _load_platforms() -> list[dict]:
    with open(DATA / "platforms.yml", encoding="utf-8") as f:
        return yaml.safe_load(f).get("platforms", [])


def _registrable_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def run_network(platforms: list[dict], do_discovery: bool) -> None:
    links = check_links.check_all(platforms)
    signups = detect_signup.detect_all(platforms)
    now = datetime.now(UTC).isoformat(timespec="seconds")

    with open(SNAPSHOT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "link_ok", "status_code", "signup_status", "checked_at"])
        for p in platforms:
            link = links.get(p["id"], {})
            writer.writerow(
                [
                    p["id"],
                    link.get("link_ok", False),
                    link.get("status_code", ""),
                    signups.get(p["id"], "unknown"),
                    now,
                ]
            )
    print(f"[refresh] wrote {SNAPSHOT.relative_to(ROOT)}")

    if do_discovery:
        known = {_registrable_domain(p["url"]) for p in platforms}
        candidates = discover.discover(known)
        if candidates:
            with open(CANDIDATES, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    {"reviewed": False, "candidates": candidates},
                    f,
                    sort_keys=False,
                    allow_unicode=True,
                )
            print(f"[refresh] wrote {CANDIDATES.relative_to(ROOT)}")


def run_dbt() -> None:
    dbt_dir = ROOT / "dbt"
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(dbt_dir)
    env["RADAR_DUCKDB"] = str(ROOT / "warehouse" / "radar.duckdb")
    print("[refresh] running dbt build ...")
    result = subprocess.run(
        ["dbt", "build"], cwd=str(dbt_dir), env=env, shell=(os.name == "nt")
    )
    if result.returncode != 0:
        raise SystemExit(f"dbt build failed with code {result.returncode}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Refresh the AI eval job radar.")
    ap.add_argument("--skip-network", action="store_true", help="rebuild marts only")
    ap.add_argument("--skip-discovery", action="store_true", help="no Tavily discovery")
    args = ap.parse_args()

    platforms = _load_platforms()
    if not args.skip_network:
        run_network(platforms, do_discovery=not args.skip_discovery)
    load_seed.load()
    run_dbt()
    print("[refresh] done.")


if __name__ == "__main__":
    main()
