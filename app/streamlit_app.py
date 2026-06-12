"""AI Eval Job Radar - Streamlit dashboard.

Reads the dbt marts out of the DuckDB warehouse. If the warehouse is missing,
it tells you how to build it instead of crashing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.db import WAREHOUSE  # noqa: E402

st.set_page_config(page_title="AI Eval Job Radar", page_icon="🛰️", layout="wide")

st.title("🛰️ AI Eval Job Radar")
st.caption(
    "A self-updating tracker of AI evaluation / training / annotation platforms. "
    "Pay and fit notes are hand-curated. Link health and signup status refresh weekly."
)

if not WAREHOUSE.exists():
    st.warning(
        "No warehouse yet. Build it from the repo root with:\n\n"
        "```\npython -m scripts.refresh --skip-network\n```\n\n"
        "(add `--skip-discovery` to check links without Tavily, or run plain "
        "`python -m scripts.refresh` for a full refresh)."
    )
    st.stop()


@st.cache_data(ttl=300)
def load_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    try:
        status = con.execute("select * from main.mart_platform_status").df()
        summary = con.execute("select * from main.mart_category_summary").df()
    finally:
        con.close()
    return status, summary


status, summary = load_tables()

last_checked = status["checked_at"].dropna()
if not last_checked.empty:
    st.info(f"Link/signup data last refreshed: **{last_checked.max()}**")
else:
    st.info("Link/signup data has not been refreshed yet. Run a full refresh to populate it.")

# ---- Category summary ----
st.subheader("By category")
st.dataframe(summary, use_container_width=True, hide_index=True)

# ---- Filters ----
st.subheader("Platforms")
c1, c2, c3 = st.columns(3)
with c1:
    tier_opts = sorted(status["tier"].unique())
    tiers = st.multiselect("Tier", tier_opts, default=tier_opts)
with c2:
    cat_opts = sorted(status["category"].unique())
    cats = st.multiselect("Category", cat_opts, default=cat_opts)
with c3:
    signup_opts = sorted(status["signup_status"].unique())
    signups = st.multiselect("Signup status", signup_opts, default=signup_opts)

view = status[
    status["tier"].isin(tiers)
    & status["category"].isin(cats)
    & status["signup_status"].isin(signups)
]


def _badge(row: pd.Series) -> str:
    link = "🟢" if row["link_ok"] else "🔴"
    signup = {"open": "✅ open", "waitlist": "🟡 waitlist", "closed": "⛔ closed"}.get(
        row["signup_status"], "❔ unknown"
    )
    return f"{link} link · {signup}"


view = view.copy()
view["health"] = view.apply(_badge, axis=1)

st.dataframe(
    view[["tier", "name", "category", "health", "pay_notes", "fit_notes", "url"]],
    use_container_width=True,
    hide_index=True,
    column_config={"url": st.column_config.LinkColumn("link")},
)

st.caption(
    "Signup status is a best-effort heuristic from each site's page text, not a guarantee. "
    "Always confirm on the platform itself."
)
