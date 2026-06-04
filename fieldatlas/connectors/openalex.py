"""OpenAlex connector — recall + citation-graph backbone (freemium API key)."""
from __future__ import annotations

from .base import RawRecord
from .http import get

API = "https://api.openalex.org/works"
NAME = "openalex"


def _abstract(inv: dict | None) -> str | None:
    if not inv:
        return None
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos)) or None


def _tier(work: dict) -> str:
    t = work.get("type")
    src = ((work.get("primary_location") or {}).get("source") or {}).get("display_name", "")
    if t == "preprint" or "arxiv" in (src or "").lower():
        return "preprint"
    return "peer_reviewed"


def _to_record(w: dict) -> RawRecord:
    ids = {}
    wid = (w.get("ids") or {}).get("openalex") or w.get("id")
    if wid:
        ids["openalex"] = wid
    doi = (w.get("ids") or {}).get("doi")
    if doi:
        ids["doi"] = doi
    if (w.get("ids") or {}).get("pmid"):
        ids["pmid"] = w["ids"]["pmid"]
    boa = w.get("best_oa_location") or {}
    authors = [(a.get("author") or {}).get("display_name")
               for a in (w.get("authorships") or [])]
    return RawRecord(
        source=NAME, source_tier=_tier(w),
        title=w.get("display_name") or "",
        abstract=_abstract(w.get("abstract_inverted_index")),
        year=w.get("publication_year"), pub_date=w.get("publication_date"),
        venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
        doc_type=w.get("type"), authors=[a for a in authors if a], external_ids=ids,
        oa_pdf_url=boa.get("pdf_url"), landing_url=boa.get("landing_page_url"),
        extra={"cited_by_count": w.get("cited_by_count"),
               "referenced_works": w.get("referenced_works", [])},
    )


def search(scope: dict, settings, limit: int = 200) -> list[RawRecord]:
    since = scope.get("harvest", {}).get("since_year", 2018)
    key = settings.openalex_api_key
    out, seen = [], set()
    for q in scope.get("queries", []):
        cursor, got = "*", 0
        while got < limit and cursor:
            params = {
                "search": q,
                "filter": f"from_publication_date:{since}-01-01",
                "per_page": min(100, limit - got), "cursor": cursor,
            }
            if key:
                params["api_key"] = key
            try:
                r = get(API, params=params)
            except Exception:
                break
            data = r.json()
            results = data.get("results", [])
            if not results:
                break
            for w in results:
                rec = _to_record(w)
                wid = rec.external_ids.get("openalex")
                if wid and wid not in seen:
                    seen.add(wid)
                    out.append(rec)
            got += len(results)
            cursor = (data.get("meta") or {}).get("next_cursor")
    return out
