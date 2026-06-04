"""Open-access PDF recovery — aggregate EVERY legal full-text candidate for a document.

Beyond `best_oa_location`, this pulls all Unpaywall `oa_locations`, OpenAlex `locations[]`,
Semantic Scholar `openAccessPdf`, and the arXiv copy of any 10.48550/arXiv.* DOI. The goal
is to shrink the automated NOT-READ tail as far as legitimately possible (green/repository
copies count) before anything is marked metadata_only. All sources are free + OA.
"""
from __future__ import annotations

import re

from .connectors.http import get

_ARXIV_DOI = re.compile(r"^10\.48550/arxiv\.(.+)$")


def _arxiv_from_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    m = _ARXIV_DOI.match(doi.lower())
    return m.group(1) if m else None


def _unpaywall_locations(doi: str, email: str) -> list[str]:
    try:
        j = get("https://api.unpaywall.org/v2/" + doi, params={"email": email}).json()
    except Exception:
        return []
    if not j.get("is_oa"):
        return []
    locs = j.get("oa_locations") or []
    # prefer publisher + published version + has-pdf
    def rank(loc):
        return (loc.get("host_type") == "publisher", loc.get("version") == "publishedVersion",
                bool(loc.get("url_for_pdf")))
    urls = []
    for loc in sorted(locs, key=rank, reverse=True):
        u = loc.get("url_for_pdf") or loc.get("url")
        if u:
            urls.append(u)
    return urls


def _openalex_locations(idstr: str, key: str | None) -> list[str]:
    params = {"api_key": key} if key else {}
    try:
        w = get("https://api.openalex.org/works/" + idstr, params=params).json()
    except Exception:
        return []
    urls = []
    for loc in (w.get("locations") or []):
        if loc.get("pdf_url"):
            urls.append(loc["pdf_url"])
    boa = w.get("best_oa_location") or {}
    if boa.get("pdf_url"):
        urls.append(boa["pdf_url"])
    if (w.get("open_access") or {}).get("oa_url"):
        urls.append(w["open_access"]["oa_url"])
    return urls


def _s2_oa_pdf(ids: dict, key: str | None) -> str | None:
    s2id = (f"DOI:{ids['doi']}" if ids.get("doi") else
            f"ARXIV:{ids['arxiv']}" if ids.get("arxiv") else ids.get("s2"))
    if not s2id:
        return None
    headers = {"x-api-key": key} if key else {}
    try:
        j = get(f"https://api.semanticscholar.org/graph/v1/paper/{s2id}",
                params={"fields": "openAccessPdf"}, headers=headers).json()
    except Exception:
        return None
    return (j.get("openAccessPdf") or {}).get("url")


def candidate_pdf_urls(doc: dict, settings) -> list[tuple[str, str]]:
    """Return ordered (via, url) PDF candidates from all OA sources, de-duplicated."""
    ids = doc.get("external_ids", {})
    out, seen = [], set()

    def add(via, url):
        if url and url not in seen:
            seen.add(url)
            out.append((via, url))

    axid = ids.get("arxiv") or _arxiv_from_doi(ids.get("doi"))
    if axid:
        add("arxiv", f"https://arxiv.org/pdf/{axid}.pdf")
    add("oa_url", doc.get("oa_pdf_url"))

    doi = ids.get("doi")
    if doi:
        for u in _unpaywall_locations(doi, settings.contact_email):
            add("unpaywall", u)
    oaid = ids.get("openalex")
    if oaid or doi:
        for u in _openalex_locations(oaid or f"doi:{doi}", settings.openalex_api_key):
            add("openalex_loc", u)
    # S2 OA lookup only with a key — the keyless pool 429-storms on bulk acquisition
    if settings.semantic_scholar_api_key:
        s2u = _s2_oa_pdf(ids, settings.semantic_scholar_api_key)
        if s2u:
            add("s2_oa", s2u)
    return out
