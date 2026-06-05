"""CORE (core.ac.uk) connector — open-access full-text aggregator (legitimate OA source)."""
from __future__ import annotations

from .base import RawRecord
from .http import get

API = "https://api.core.ac.uk/v3/search/works"
NAME = "core"


def _to_record(it: dict) -> RawRecord:
    ids = {}
    if it.get("doi"):
        ids["doi"] = it["doi"]
    if it.get("id"):
        ids["url"] = f"core:{it['id']}"
    if it.get("arxivId"):
        ids["arxiv"] = it["arxivId"]
    authors = [a.get("name") for a in (it.get("authors") or []) if a.get("name")]
    return RawRecord(
        source=NAME, source_tier="peer_reviewed", title=it.get("title") or "",
        abstract=it.get("abstract"), year=it.get("yearPublished"),
        pub_date=it.get("publishedDate"), venue=it.get("publisher"),
        doc_type=it.get("documentType"), authors=authors, external_ids=ids,
        oa_pdf_url=it.get("downloadUrl"),
    )


def search(scope: dict, settings, limit: int = 200) -> list[RawRecord]:
    key = settings.core_api_key
    if not key:
        return []
    hv = scope.get("harvest", {})
    since = int((hv.get("since_date") or "").split("-")[0]) if hv.get("since_date") else hv.get("since_year", 2018)
    headers = {"Authorization": f"Bearer {key}"}
    out, seen = [], set()
    for q in scope.get("queries", []):
        query = f'({q}) AND yearPublished>={since}'
        try:
            r = get(API, params={"q": query, "limit": min(100, limit)}, headers=headers)
        except Exception:
            continue
        for it in r.json().get("results", []):
            rec = _to_record(it)
            k = rec.external_ids.get("doi") or rec.external_ids.get("url")
            if k and k not in seen:
                seen.add(k)
                out.append(rec)
    return out
