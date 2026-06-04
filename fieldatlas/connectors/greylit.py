"""Grey-literature + discourse connector — think tanks, safety community, newsletters.

Uses each source's structured, keyless access (RSS/Atom feeds; verified 2026-06-04). Items
enter the corpus as metadata (title + excerpt + url + date, tagged by source tier) and are
relevance-ranked by the same embedding pass as everything else. Full-text deep-read of HTML
grey-lit needs a Firecrawl key (optional); without it these enrich the map/trends at
abstract level. A browser User-Agent is used (some sites, e.g. RAND, block bot UAs).
"""
from __future__ import annotations

import re

import feedparser
import requests

from .base import RawRecord

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_TAG = re.compile(r"<[^>]+>")

# (source_name, feed_url, source_tier). Failures are skipped gracefully.
FEEDS = [
    ("cset", "https://cset.georgetown.edu/feed/", "think_tank"),
    ("ai_now", "https://ainowinstitute.org/feed", "think_tank"),
    ("rand", "https://www.rand.org/pubs/new.xml", "think_tank"),
    ("brookings", "https://www.brookings.edu/topic/artificial-intelligence/feed/", "think_tank"),
    ("lesswrong", "https://www.lesswrong.com/feed.xml?view=curated-rss", "community"),
    ("alignment_forum", "https://www.alignmentforum.org/feed.xml?view=curated-rss", "community"),
    ("import_ai", "https://importai.substack.com/feed", "discourse"),
    ("cais_newsletter", "https://newsletter.safe.ai/feed", "discourse"),
    ("ml_safety", "https://newsletter.mlsafety.org/feed", "discourse"),
]

# think-tank feeds carry off-topic items; keep only AI/safety/policy-relevant ones.
AI_TERMS = ("ai", "a.i.", "artificial intelligence", "machine learning", "frontier",
            "alignment", "agi", "llm", "language model", "compute", "autonomous",
            "algorithm", "chatbot", "deep learning", "foundation model")
_FILTER_TIERS = {"think_tank"}


def _strip(s: str | None) -> str | None:
    return _TAG.sub("", s).strip() if s else None


def _relevant(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in AI_TERMS)


def _fetch(url: str) -> bytes | None:
    try:
        r = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=40)
        return r.content if r.status_code == 200 else None
    except requests.RequestException:
        return None


def search(scope: dict, settings, limit: int = 200) -> list[RawRecord]:
    per_feed = min(limit, 60)
    out = []
    for name, url, tier in FEEDS:
        raw = _fetch(url)
        if not raw:
            continue
        feed = feedparser.parse(raw)
        for e in feed.entries[:per_feed]:
            title = _strip(getattr(e, "title", "")) or ""
            summary = _strip(getattr(e, "summary", "")) or _strip(getattr(e, "description", ""))
            if tier in _FILTER_TIERS and not _relevant(f"{title} {summary or ''}"):
                continue
            link = getattr(e, "link", None)
            year = None
            pp = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            pub_date = None
            if pp:
                year = pp.tm_year
                pub_date = f"{pp.tm_year:04d}-{pp.tm_mon:02d}-{pp.tm_mday:02d}"
            if not title or not link:
                continue
            out.append(RawRecord(
                source=name, source_tier=tier, title=title, abstract=summary,
                year=year, pub_date=pub_date, venue=name, doc_type="grey_lit",
                external_ids={"url": link}, landing_url=link,
            ))
    return out
