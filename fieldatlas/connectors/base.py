"""Normalized record type + ID normalization shared by all connectors."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# scheme priority for choosing a canonical id
ID_PRIORITY = ["doi", "arxiv", "openalex", "s2", "dblp", "pmid", "corpusid", "url"]


def norm_doi(v: str | None) -> str | None:
    if not v:
        return None
    v = v.strip().lower()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v)
    v = v.replace("doi:", "").strip()
    return v or None


def norm_arxiv(v: str | None) -> str | None:
    if not v:
        return None
    v = v.strip().lower()
    v = re.sub(r"^https?://arxiv\.org/abs/", "", v)
    v = v.replace("arxiv:", "").strip()
    v = re.sub(r"v\d+$", "", v)        # drop version for canonical join
    return v or None


def norm_openalex(v: str | None) -> str | None:
    if not v:
        return None
    v = v.strip()
    v = re.sub(r"^https?://openalex\.org/", "", v)
    return v.upper() or None


NORMALIZERS = {"doi": norm_doi, "arxiv": norm_arxiv, "openalex": norm_openalex}


def normalize_ids(ids: dict) -> dict:
    out = {}
    for scheme, val in (ids or {}).items():
        if not val:
            continue
        fn = NORMALIZERS.get(scheme)
        v = fn(str(val)) if fn else str(val).strip()
        if v:
            out[scheme] = v
    return out


@dataclass
class RawRecord:
    source: str
    source_tier: str
    title: str
    abstract: str | None = None
    year: int | None = None
    pub_date: str | None = None
    venue: str | None = None
    doc_type: str | None = None
    authors: list = field(default_factory=list)
    external_ids: dict = field(default_factory=dict)
    oa_pdf_url: str | None = None
    landing_url: str | None = None
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        self.external_ids = normalize_ids(self.external_ids)
