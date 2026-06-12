"""Best-effort signup-status detection.

This is a heuristic, not truth. It fetches each platform's signup/careers page
and scans the visible text for phrases that suggest the door is open, gated, or
shut. When nothing matches, it honestly returns ``unknown`` rather than guessing.
"""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "ai-eval-job-radar/1.0 (+https://github.com/DaCameraGirl)"}
TIMEOUT = 20

CLOSED_CUES = [
    "applications are closed",
    "not currently hiring",
    "not currently accepting",
    "no open roles",
    "no open positions",
    "currently full",
    "applications are paused",
    "check back later",
]
WAITLIST_CUES = [
    "waitlist",
    "join the list",
    "notify me",
    "coming soon",
    "request access",
    "request an invite",
    "by invitation",
    "invite only",
]
OPEN_CUES = [
    "apply now",
    "sign up",
    "get started",
    "create an account",
    "create account",
    "start earning",
    "join now",
    "open roles",
    "open positions",
    "we're hiring",
    "we are hiring",
    "apply today",
]


def _page_text(url: str) -> str | None:
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code >= 400:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True).lower()
    except requests.RequestException:
        return None


def detect(url: str) -> str:
    """Return one of: open, waitlist, closed, unknown."""
    text = _page_text(url)
    if text is None:
        return "unknown"
    if any(cue in text for cue in CLOSED_CUES):
        return "closed"
    if any(cue in text for cue in WAITLIST_CUES):
        return "waitlist"
    if any(cue in text for cue in OPEN_CUES):
        return "open"
    return "unknown"


def detect_all(platforms: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in platforms:
        status = detect(p.get("signup_url", p["url"]))
        out[p["id"]] = status
        print(f"[signup] {status:<8} {p['id']}")
    return out
