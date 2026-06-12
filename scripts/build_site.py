"""Build a static radar page for GitHub Pages from the tracked data files.

No database needed. Reads data/platforms.yml plus data/status_snapshot.csv (if it
exists), fills templates/page.html with templates/style.css, and writes a single
self-contained site/index.html. Runs in CI; the output is gitignored.

The HTML and CSS live in real files under templates/ (not buried in this script) so
the page markup is editable on its own and GitHub counts the languages honestly.
"""
from __future__ import annotations

import csv
import html
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
SITE = ROOT / "site"

SIGNUP_BADGE = {
    "open": ("open", "#1f9d55"),
    "waitlist": ("waitlist", "#b7791f"),
    "closed": ("closed", "#b91c1c"),
    "unknown": ("not checked", "#4b5563"),
}

TIER_NAMES = {1: "Tier 1 - best fit", 2: "Tier 2 - solid", 3: "Tier 3 - long shots"}


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
    apply_url = p.get("signup_url") or p["url"]
    return f"""
      <tr>
        <td class="dot">{dot}</td>
        <td><a href="{e(apply_url)}" target="_blank" rel="noopener">{e(p['name'])}</a></td>
        <td>{badge}</td>
        <td class="notes">{e(p.get('pay_notes', ''))}</td>
        <td class="notes">{e(p.get('fit_notes', ''))}</td>
      </tr>"""


def _section_html(tier: int, platforms: list[dict], status: dict[str, dict]) -> str:
    rows = [p for p in platforms if int(p["tier"]) == tier]
    if not rows:
        return ""
    head = (
        "<thead><tr><th></th><th>Platform</th><th>Signup</th>"
        "<th>Pay notes</th><th>Why it fits</th></tr></thead>"
    )
    body = "".join(_row_html(p, status.get(p["id"], {})) for p in rows)
    return f"""
    <h2>{TIER_NAMES[tier]}</h2>
    <table>
      {head}
      <tbody>{body}
      </tbody>
    </table>"""


def build() -> Path:
    platforms = _load_platforms()
    status, latest = _load_status()
    refreshed = latest or "not yet refreshed"

    sections = "".join(_section_html(t, platforms, status) for t in (1, 2, 3))
    meta = (
        f"Status last refreshed: {html.escape(str(refreshed))} &middot; "
        '<a href="https://github.com/DaCameraGirl/ai-eval-job-radar">source on GitHub</a>'
    )

    template = (TEMPLATES / "page.html").read_text(encoding="utf-8")
    css = (TEMPLATES / "style.css").read_text(encoding="utf-8")
    page = (
        template.replace("__STYLE__", css)
        .replace("__META__", meta)
        .replace("__SECTIONS__", sections)
    )

    SITE.mkdir(parents=True, exist_ok=True)
    out = SITE / "index.html"
    out.write_text(page, encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    print(f"[build_site] wrote {out} ({len(platforms)} platforms)")
    return out


if __name__ == "__main__":
    build()
