"""Crossref connector — DOI authority, journal coverage arXiv misses, backward refs."""
from __future__ import annotations

import re

from .base import RawRecord
from .http import get

API = "https://api.crossref.org/works"
NAME = "crossref"
_TAG = re.compile(r"<[^>]+>")


def _strip(s: str | None) -> str | None:
    return _TAG.sub("", s).strip() if s else None


def _to_record(it: dict) -> RawRecord:
    title = (it.get("title") or [""])[0]
    authors = [" ".join(x for x in [a.get("given"), a.get("family")] if x)
               for a in it.get("author", [])]
    year = None
    dp = (it.get("issued") or {}).get("date-parts") or [[None]]
    if dp and dp[0] and dp[0][0]:
        year = dp[0][0]
    ids = {}
    if it.get("DOI"):
        ids["doi"] = it["DOI"]
    return RawRecord(
        source=NAME, source_tier="peer_reviewed", title=title,
        abstract=_strip(it.get("abstract")), year=year,
        venue=(it.get("container-title") or [None])[0], doc_type=it.get("type"),
        authors=[a for a in authors if a], external_ids=ids,
        landing_url=it.get("URL"),
        extra={"reference_count": it.get("reference-count"),
               "references": [r.get("DOI") for r in it.get("reference", []) if r.get("DOI")]},
    )


def search(scope: dict, settings, limit: int = 200) -> list[RawRecord]:
    hv = scope.get("harvest", {})
    since_date = hv.get("since_date") or f"{hv.get('since_year', 2018)}-01-01"
    out, seen = [], set()
    for q in scope.get("queries", []):
        cursor, got = "*", 0
        while got < limit and cursor:
            try:
                r = get(API, params={
                    "query.bibliographic": q,
                    "filter": f"from-pub-date:{since_date},type:journal-article",
                    "rows": min(100, limit - got), "cursor": cursor,
                    "mailto": settings.contact_email,
                })
            except Exception:
                break
            msg = r.json().get("message", {})
            items = msg.get("items", [])
            if not items:
                break
            for it in items:
                rec = _to_record(it)
                doi = rec.external_ids.get("doi")
                if doi and doi not in seen:
                    seen.add(doi)
                    out.append(rec)
            got += len(items)
            cursor = msg.get("next-cursor")
    return out
