"""Semantic Scholar (S2AG) connector — citation graph + metadata + SPECTER2 vectors.

Throttled to ~1 RPS (the post-2024 default even with a key). Uses the bulk search
endpoint for corpus assembly.
"""
from __future__ import annotations

from .base import RawRecord
from .http import get

API = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
NAME = "semantic_scholar"
FIELDS = ("title,abstract,year,publicationDate,venue,externalIds,openAccessPdf,"
          "publicationTypes,authors,citationCount,tldr")


def _tier(types) -> str:
    types = types or []
    if "JournalArticle" in types or "Conference" in types:
        return "peer_reviewed"
    return "preprint"


def _to_record(p: dict) -> RawRecord:
    ext = p.get("externalIds") or {}
    ids = {}
    if p.get("paperId"):
        ids["s2"] = p["paperId"]
    if ext.get("DOI"):
        ids["doi"] = ext["DOI"]
    if ext.get("ArXiv"):
        ids["arxiv"] = ext["ArXiv"]
    if ext.get("CorpusId"):
        ids["corpusid"] = str(ext["CorpusId"])
    abstract = p.get("abstract") or ((p.get("tldr") or {}) or {}).get("text")
    return RawRecord(
        source=NAME, source_tier=_tier(p.get("publicationTypes")),
        title=p.get("title") or "", abstract=abstract, year=p.get("year"),
        pub_date=p.get("publicationDate"), venue=p.get("venue"),
        doc_type=(p.get("publicationTypes") or [None])[0],
        authors=[a.get("name") for a in (p.get("authors") or []) if a.get("name")],
        external_ids=ids,
        oa_pdf_url=(p.get("openAccessPdf") or {}).get("url"),
        extra={"citationCount": p.get("citationCount")},
    )


def search(scope: dict, settings, limit: int = 200) -> list[RawRecord]:
    since = scope.get("harvest", {}).get("since_year", 2018)
    headers = {}
    if settings.semantic_scholar_api_key:
        headers["x-api-key"] = settings.semantic_scholar_api_key
    out, seen = [], set()
    for q in scope.get("queries", []):
        token, got = None, 0
        while got < limit:
            params = {"query": q, "fields": FIELDS,
                      "publicationDateOrYear": f"{since}:"}
            if token:
                params["token"] = token
            try:
                r = get(API, params=params, headers=headers)
            except Exception:
                break
            data = r.json()
            papers = (data.get("data") or [])[: max(0, limit - got)]
            if not papers:
                break
            for p in papers:
                rec = _to_record(p)
                sid = rec.external_ids.get("s2")
                if sid and sid not in seen:
                    seen.add(sid)
                    out.append(rec)
            got += len(papers)
            token = data.get("token")
            if not token:
                break
    return out
