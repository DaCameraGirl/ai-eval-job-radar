"""Check that each platform URL is still alive.

Reliable and cheap. This is the baseline weekly signal: did a platform move,
rebrand, or go dark.
"""
from __future__ import annotations

import requests

UA = {"User-Agent": "ai-eval-job-radar/1.0 (+https://github.com/DaCameraGirl)"}
TIMEOUT = 15


def check_url(url: str) -> tuple[bool, int | None]:
    """Return (alive, status_code). Tries HEAD, falls back to GET."""
    try:
        r = requests.head(url, headers=UA, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code >= 400 or r.status_code == 405:
            # Some sites reject HEAD; retry with GET.
            r = requests.get(url, headers=UA, timeout=TIMEOUT, allow_redirects=True)
        return (r.status_code < 400, r.status_code)
    except requests.RequestException:
        return (False, None)


def check_all(platforms: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in platforms:
        alive, code = check_url(p["url"])
        out[p["id"]] = {"link_ok": alive, "status_code": code}
        flag = "ok " if alive else "DEAD"
        print(f"[links] {flag} {p['id']:<16} {code} {p['url']}")
    return out
