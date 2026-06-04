"""arXiv connector — primary preprint harvest (cs.AI/cs.CY/cs.LG/cs.CL/stat.ML + cross-lists)."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from .base import RawRecord
from .http import get

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
NAME = "arxiv"
TIER = "preprint"


def _entry_to_record(e) -> RawRecord:
    def txt(p):
        el = e.find(p, NS)
        return el.text.strip() if el is not None and el.text else None

    raw_id = txt("a:id") or ""
    arxiv_id = raw_id.rsplit("/abs/", 1)[-1] if "/abs/" in raw_id else raw_id
    cats = [c.get("term") for c in e.findall("a:category", NS)]
    authors = [a.text.strip() for a in e.findall("a:author/a:name", NS) if a.text]
    pdf = None
    for ln in e.findall("a:link", NS):
        if ln.get("title") == "pdf":
            pdf = ln.get("href")
    published = txt("a:published")
    year = int(published[:4]) if published else None
    ids = {"arxiv": arxiv_id}
    doi = txt("arxiv:doi")
    if doi:
        ids["doi"] = doi
    return RawRecord(
        source=NAME, source_tier=TIER, title=txt("a:title") or "",
        abstract=txt("a:summary"), year=year, pub_date=published,
        venue="arXiv", doc_type="preprint", authors=authors, external_ids=ids,
        oa_pdf_url=pdf, landing_url=raw_id, extra={"categories": cats},
    )


def search(scope: dict, settings, limit: int = 200) -> list[RawRecord]:
    cats = scope.get("arxiv_categories", ["cs.AI", "cs.CY", "cs.LG"])
    cat_clause = "(" + " OR ".join(f"cat:{c}" for c in cats) + ")"
    out, seen = [], set()
    for q in scope.get("queries", []):
        term = f'(abs:"{q}" OR ti:"{q}")'
        start, page = 0, 100
        while start < limit:
            try:
                r = get(API, params={
                    "search_query": f"{term} AND {cat_clause}",
                    "start": start, "max_results": min(page, limit - start),
                    "sortBy": "submittedDate", "sortOrder": "descending",
                }, timeout=90)   # arXiv query API is legitimately slow (~15s+)
            except Exception:
                break
            root = ET.fromstring(r.text)
            entries = root.findall("a:entry", NS)
            if not entries:
                break
            for e in entries:
                rec = _entry_to_record(e)
                aid = rec.external_ids.get("arxiv")
                if aid and aid not in seen:
                    seen.add(aid)
                    out.append(rec)
            start += page
    return out
