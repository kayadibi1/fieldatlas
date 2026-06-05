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


def _fetch_filter(filter_str: str, settings, per_page: int = 100, max_results: int = 200) -> list[RawRecord]:
    """Generic OpenAlex works fetch by a filter string (date-exempt). For snowball/seed fetch."""
    key = settings.openalex_api_key
    out, seen, cursor, got = [], set(), "*", 0
    while got < max_results and cursor:
        params = {"filter": filter_str, "per_page": min(per_page, max_results - got), "cursor": cursor}
        if key:
            params["api_key"] = key
        try:
            data = get(API, params=params).json()
        except Exception:
            break
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


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def fetch_by_dois(dois: list[str], settings) -> list[RawRecord]:
    out = []
    for ch in _chunks([d for d in dois if d], 50):
        out += _fetch_filter("doi:" + "|".join(ch), settings, max_results=len(ch) + 5)
    return out


def fetch_by_openalex_ids(oa_ids: list[str], settings) -> list[RawRecord]:
    short = [i.rsplit("/", 1)[-1] for i in oa_ids if i]   # accept full URLs or bare W-ids
    out = []
    for ch in _chunks(short, 50):
        out += _fetch_filter("openalex_id:" + "|".join(ch), settings, max_results=len(ch) + 5)
    return out


def fetch_citing(oa_id: str, settings, limit: int = 60) -> list[RawRecord]:
    """Forward citations: works that cite oa_id."""
    return _fetch_filter(f"cites:{oa_id.rsplit('/', 1)[-1]}", settings, max_results=limit)


def search(scope: dict, settings, limit: int = 200) -> list[RawRecord]:
    hv = scope.get("harvest", {})
    since_date = hv.get("since_date") or f"{hv.get('since_year', 2018)}-01-01"   # delta runs set since_date
    key = settings.openalex_api_key
    out, seen = [], set()
    for q in scope.get("queries", []):
        cursor, got = "*", 0
        while got < limit and cursor:
            params = {
                "search": q,
                "filter": f"from_publication_date:{since_date}",
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
