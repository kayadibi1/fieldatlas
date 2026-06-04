"""Cross-source deduplication — collapses the same work harvested from arXiv, OpenAlex,
Crossref, Semantic Scholar, CORE, etc. into one canonical document.

Records are joined transitively (union-find) when they share ANY external id, or share a
normalized (title, year). This is what makes "found by 4 sources" count as one item in
recall stats rather than four — and gives every output a single stable id to cite.
"""
from __future__ import annotations

import hashlib
import re

from .connectors.base import ID_PRIORITY, RawRecord

_TITLE_WS = re.compile(r"[^a-z0-9 ]+")
_WS = re.compile(r"\s+")


def title_key(title: str) -> str:
    t = (title or "").lower()
    t = _TITLE_WS.sub(" ", t)
    t = _WS.sub(" ", t).strip()
    return t


class _UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def _keys(rec: RawRecord) -> list:
    keys = [("id", s, v) for s, v in rec.external_ids.items()]
    tk = title_key(rec.title)
    if tk and rec.year:
        keys.append(("ty", tk, rec.year))
    elif tk:
        keys.append(("t", tk))
    return keys


def _canonical_id(ids: dict, title: str) -> str:
    for scheme in ID_PRIORITY:
        if scheme in ids:
            return f"{scheme}:{ids[scheme]}"
    h = hashlib.sha1(title_key(title).encode()).hexdigest()[:12]
    return f"title:{h}"


def dedup(records: list[RawRecord]) -> list[dict]:
    """Return canonical documents, each merging the metadata of its source records."""
    uf = _UF()
    rec_node = []
    for i, rec in enumerate(records):
        node = ("rec", i)
        rec_node.append(node)
        uf.find(node)
        for k in _keys(rec):
            uf.union(node, k)

    groups: dict = {}
    for i, rec in enumerate(records):
        root = uf.find(("rec", i))
        groups.setdefault(root, []).append(rec)

    docs = []
    for members in groups.values():
        ids: dict = {}
        for r in members:
            for s, v in r.external_ids.items():
                ids.setdefault(s, v)
        # richest non-empty field wins; prefer longer abstract, earliest year
        best_title = max((r.title for r in members if r.title), key=len, default="")
        abstract = max((r.abstract or "" for r in members), key=len) or None
        years = [r.year for r in members if r.year]
        authors = max((r.authors for r in members), key=len, default=[])
        venue = next((r.venue for r in members if r.venue), None)
        pub_date = next((r.pub_date for r in members if r.pub_date), None)
        doc_type = next((r.doc_type for r in members if r.doc_type), None)
        oa_pdf = next((r.oa_pdf_url for r in members if r.oa_pdf_url), None)
        landing = next((r.landing_url for r in members if r.landing_url), None)
        docs.append({
            "canonical_id": _canonical_id(ids, best_title),
            "title": best_title,
            "abstract": abstract,
            "year": min(years) if years else None,
            "pub_date": pub_date,
            "venue": venue,
            "doc_type": doc_type,
            "authors": authors,
            "external_ids": ids,
            "sources": sorted({r.source for r in members}),
            "source_tiers": sorted({r.source_tier for r in members}),
            "oa_pdf_url": oa_pdf,
            "landing_url": landing,
            "n_source_records": len(members),
        })
    return docs
