"""Discover NEW AI-eval platforms via web search (optional).

Needs TAVILY_API_KEY in the environment. If the key or the client is missing,
this degrades gracefully to a no-op so the rest of the pipeline still runs.

Output is a list of *candidates*, never auto-trusted. A human reviews
``data/discovered_candidates.yml`` and promotes the good ones into
``data/platforms.yml`` by hand.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

# Generic domains that are never the platform itself.
IGNORE_DOMAINS = {
    "reddit.com", "linkedin.com", "glassdoor.com", "indeed.com", "medium.com",
    "youtube.com", "twitter.com", "x.com", "facebook.com", "quora.com",
    "trustpilot.com", "wikipedia.org", "github.com", "substack.com",
    "g2.com", "crunchbase.com", "betterteam.com", "ziprecruiter.com",
}

QUERIES = [
    "best AI data labeling platforms for freelancers 2026",
    "LLM evaluation freelance platforms hire experts",
    "RLHF annotation jobs remote expert platform",
    "AI training contractor platforms like Outlier",
]


def _registrable_domain(url: str) -> str | None:
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return None
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return None
    parts = host.split(".")
    if len(parts) >= 2:
        host = ".".join(parts[-2:])
    return host


def discover(known_domains: set[str]) -> list[dict]:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("[discover] TAVILY_API_KEY not set; skipping discovery")
        return []
    try:
        from tavily import TavilyClient
    except ImportError:
        print("[discover] tavily-python not installed; skipping discovery")
        return []

    from datetime import UTC, datetime

    client = TavilyClient(api_key=api_key)
    seen: dict[str, dict] = {}
    for q in QUERIES:
        try:
            resp = client.search(q, max_results=10)
        except Exception as exc:  # noqa: BLE001 - external API, stay resilient
            print(f"[discover] query failed ({q!r}): {exc}")
            continue
        for item in resp.get("results", []):
            domain = _registrable_domain(item.get("url", ""))
            if not domain or domain in IGNORE_DOMAINS or domain in known_domains:
                continue
            if domain in seen:
                continue
            seen[domain] = {
                "domain": domain,
                "name": domain.split(".")[0].replace("-", " ").title(),
                "source_query": q,
                "found_at": datetime.now(UTC).isoformat(timespec="seconds"),
            }
    print(f"[discover] found {len(seen)} new candidate domain(s)")
    return list(seen.values())
