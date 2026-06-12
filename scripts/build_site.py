"""Build a static radar page for GitHub Pages from the tracked data files.

No database needed. Reads data/platforms.yml plus data/status_snapshot.csv (if it
exists) and writes a single self-contained site/index.html. Runs in CI; the output
is gitignored.
"""
from __future__ import annotations

import csv
import html
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SITE = ROOT / "site"

CATEGORY_LABELS = {
    "expert_match": "Expert match",
    "eval_platform": "Eval platform",
    "research_fellowship": "Research / fellowship",
    "microtask": "Microtask",
    "contest": "Contest",
}

SIGNUP_BADGE = {
    "open": ("open", "#1f9d55"),
    "waitlist": ("waitlist", "#b7791f"),
    "closed": ("closed", "#b91c1c"),
    "unknown": ("not checked", "#4b5563"),
}


def _load_platforms() -> list[dict]:
    with open(DATA / "platforms.yml", encoding="utf-8") as f:
        return yaml.safe_load(f).get("platforms", [])


def _load_status() -> tuple[dict[str, dict], str | None]:
    path = DATA / "status_snapshot.csv"
    if not path.exists():
        return {}, None
    rows: dict[str, dict] = {}
    latest: str | None = None
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows[row["id"]] = row
            latest = row.get("checked_at") or latest
    return rows, latest


def _row_html(p: dict, status: dict) -> str:
    e = html.escape
    link_ok = str(status.get("link_ok", "")).lower() == "true"
    dot = "🟢" if link_ok else ("🔴" if status else "⚪")
    signup = status.get("signup_status", "unknown") or "unknown"
    label, color = SIGNUP_BADGE.get(signup, SIGNUP_BADGE["unknown"])
    badge = f'<span class="badge" style="background:{color}">{label}</span>'
    return f"""
      <tr>
        <td class="dot">{dot}</td>
        <td><a href="{e(p['url'])}" target="_blank" rel="noopener">{e(p['name'])}</a></td>
        <td>{badge}</td>
        <td class="notes">{e(p.get('pay_notes', ''))}</td>
        <td class="notes">{e(p.get('fit_notes', ''))}</td>
      </tr>"""


def build() -> Path:
    platforms = _load_platforms()
    status, latest = _load_status()
    refreshed = latest or "not yet refreshed"

    sections = []
    for tier in (1, 2, 3):
        rows = [p for p in platforms if int(p["tier"]) == tier]
        if not rows:
            continue
        tier_name = {1: "Tier 1 - best fit", 2: "Tier 2 - solid", 3: "Tier 3 - long shots"}[tier]
        body = "".join(_row_html(p, status.get(p["id"], {})) for p in rows)
        sections.append(
            f"""
    <h2>{tier_name}</h2>
    <table>
      <thead><tr><th></th><th>Platform</th><th>Signup</th><th>Pay notes</th><th>Why it fits</th></tr></thead>
      <tbody>{body}
      </tbody>
    </table>"""
        )

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Eval Job Radar</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
         background: #0b0e14; color: #e6e9ef; line-height: 1.5; }}
  .wrap {{ max-width: 980px; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }}
  h1 {{ font-size: 2rem; margin: 0 0 .25rem; }}
  .tag {{ color: #8b93a7; font-size: .95rem; max-width: 60ch; }}
  .meta {{ margin: 1rem 0 2rem; font-size: .85rem; color: #8b93a7; }}
  h2 {{ margin: 2rem 0 .5rem; font-size: 1.1rem; color: #c8d0e0; border-bottom: 1px solid #1c2230; padding-bottom: .35rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .9rem; }}
  th {{ text-align: left; color: #8b93a7; font-weight: 600; padding: .5rem .6rem; }}
  td {{ padding: .55rem .6rem; border-top: 1px solid #161b26; vertical-align: top; }}
  td.dot {{ width: 1.5rem; text-align: center; }}
  a {{ color: #6ea8fe; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .notes {{ color: #aeb6c6; font-size: .82rem; }}
  .badge {{ display: inline-block; padding: .1rem .5rem; border-radius: 999px; color: #fff;
           font-size: .72rem; font-weight: 600; }}
  footer {{ margin-top: 3rem; font-size: .8rem; color: #6b7280; }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>🛰️ AI Eval Job Radar</h1>
    <p class="tag">Where to actually get AI evaluation work. Pay and fit notes are hand-curated
       and honest. Link and signup status refresh weekly. This is a read-only snapshot.</p>
    <p class="meta">Status last refreshed: {html.escape(str(refreshed))} &middot;
       <a href="https://github.com/DaCameraGirl/ai-eval-job-radar">source on GitHub</a></p>
    {''.join(sections)}
    <footer>
      Signup status is a best-effort heuristic, not a guarantee. Always confirm on the platform.
      Built from data/platforms.yml. The interactive version runs on Streamlit.
    </footer>
  </div>
</body>
</html>
"""
    SITE.mkdir(parents=True, exist_ok=True)
    out = SITE / "index.html"
    out.write_text(page, encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    print(f"[build_site] wrote {out} ({len(platforms)} platforms)")
    return out


if __name__ == "__main__":
    build()
