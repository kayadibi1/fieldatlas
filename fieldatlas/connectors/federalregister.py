"""US Federal Register connector — live AI rulemaking/regulatory primary source (no key)."""
from __future__ import annotations

from .base import RawRecord
from .http import get

API = "https://www.federalregister.gov/api/v1/documents.json"
NAME = "federal_register"


def search(scope: dict, settings, limit: int = 100) -> list[RawRecord]:
    out = []
    try:
        r = get(API, params={
            "conditions[term]": "artificial intelligence",
            "per_page": min(limit, 100), "order": "newest",
            "fields[]": ["title", "abstract", "publication_date", "html_url",
                         "document_number", "agencies", "type"],
        })
    except Exception:
        return out
    for d in r.json().get("results", []):
        pub = d.get("publication_date")
        agencies = ", ".join(a.get("name", "") for a in (d.get("agencies") or []))
        out.append(RawRecord(
            source=NAME, source_tier="standards_gov", title=d.get("title") or "",
            abstract=d.get("abstract"), year=int(pub[:4]) if pub else None, pub_date=pub,
            venue=agencies or "US Federal Register", doc_type=d.get("type") or "regulation",
            external_ids={"url": f"fedreg:{d.get('document_number')}"},
            landing_url=d.get("html_url"),
        ))
    return out
