# 🛰️ AI Eval Job Radar

**A self-updating data app that tracks where to actually get AI-evaluation work.**

Most "best AI gig sites" lists are stale the day they're published and stuffed with
invented pay numbers. This one is a small data pipeline instead: a curated registry of
AI evaluation / training / annotation platforms, refreshed weekly for link health and
signup status, with new platforms discovered automatically and queued for human review.

Pay and fit notes are **hand-curated and deliberately honest**. The robot checks what it
can verify (is the link alive? does the page look open or closed?) and leaves judgment to a person.

## What it does

| Step | Tool | Job |
|------|------|-----|
| Registry | `data/platforms.yml` | Hand-curated source of truth (name, tier, fit, pay notes) |
| Link health | Python + `requests` | Is each platform URL still alive? |
| Signup status | Python + `BeautifulSoup` | Best-effort open / waitlist / closed / unknown |
| Discovery | Tavily (optional) | Surface new platforms, queued in `discovered_candidates.yml` |
| Warehouse | DuckDB | Disposable analytics store, rebuilt from tracked files |
| Modeling | dbt (`dbt-duckdb`) | Staging + marts |
| Dashboard | Streamlit | Filter by tier, category, and signup status |

```
data/platforms.yml ──▶ link + signup checks ──▶ data/status_snapshot.csv
                  └──▶ Tavily discovery ──────▶ data/discovered_candidates.yml
                                                        │
                                   load into DuckDB ◀───┘
                                          │
                                     dbt build (marts)
                                          │
                                   Streamlit dashboard
```

### Why DuckDB instead of Snowflake?

This dataset is ~50 rows refreshed weekly. Snowflake would bill warehouse credits to
sit idle. DuckDB gives the same SQL/dbt workflow for free and in-process. The dbt models
are written so they port to a Snowflake target with almost no changes if the data ever
outgrows a laptop.

## Quick start

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Build the dashboard from the tracked data, no network calls:
python -m scripts.refresh --skip-network

# Or a full refresh (checks links + signup status; discovery needs a Tavily key):
python -m scripts.refresh

# View it:
streamlit run app/streamlit_app.py
```

### Tavily key (optional)

Discovery is the only part that needs a key.

```powershell
Copy-Item .env.example .env
# then open .env and paste your Tavily key after TAVILY_API_KEY=
```

No key means discovery simply skips itself. **No Snowflake, OpenAI, Anthropic, or quantum
keys are used anywhere in this project.** Never commit `.env`.

## How updates happen (no raw commits to main)

A GitHub Action runs every Monday, refreshes the data, and **opens a pull request** with
the changes instead of pushing to `main`. You review the diff in `status_snapshot.csv`
and `discovered_candidates.yml` and merge if it looks right. CI lint-checks and rebuilds
the whole pipeline on every PR. The robot proposes; you approve.

## Adding a platform

Edit `data/platforms.yml` (the only source of truth), open a PR, and let CI verify it.
Promote a discovered candidate by moving it from `discovered_candidates.yml` into
`platforms.yml` with real fit and pay notes.

## License

MIT. See [LICENSE](LICENSE).
