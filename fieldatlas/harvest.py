"""Harvest orchestration + recall accounting (the F3 guard).

Runs every connector deterministically, dedups across sources, and produces a recall
manifest so completeness is visible as data (per-source counts, dedup ratio, how many
items are corroborated by multiple sources vs found by only one).
"""
from __future__ import annotations

from collections import Counter

from .connectors import REGISTRY, run_connector
from .dedup import dedup


def harvest(scope: dict, settings, sources: list[str] | None = None,
            per_query_limit: int | None = None) -> tuple[list[dict], dict]:
    sources = sources or list(REGISTRY)
    limit = per_query_limit or scope.get("harvest", {}).get("per_query_limit", 200)
    all_records, per_source = [], {}
    for name in sources:
        try:
            recs = run_connector(name, scope, settings, limit)
        except Exception as e:  # a connector failure must not sink the whole harvest
            per_source[name] = {"raw": 0, "error": str(e)[:200]}
            continue
        per_source[name] = {"raw": len(recs)}
        all_records.extend(recs)

    docs = dedup(all_records)

    # capture OpenAlex backward-citation edges (raw ids) for the knowledge graph
    edges_raw = []
    for r in all_records:
        if r.source == "openalex":
            citing = r.external_ids.get("openalex")
            for ref in (r.extra or {}).get("referenced_works", []):
                if citing and ref:
                    edges_raw.append((citing, ref))

    src_membership = Counter()
    for d in docs:
        src_membership[len(d["sources"])] += 1
    manifest = {
        "sources": per_source,
        "raw_records": len(all_records),
        "unique_documents": len(docs),
        "dedup_ratio": round(1 - len(docs) / max(1, len(all_records)), 3),
        "multi_source_documents": sum(v for k, v in src_membership.items() if k >= 2),
        "single_source_documents": src_membership.get(1, 0),
        "documents_with_oa_pdf": sum(1 for d in docs if d.get("oa_pdf_url")),
        "documents_with_abstract": sum(1 for d in docs if d.get("abstract")),
        "citation_edges_openalex": edges_raw,
    }
    return docs, manifest
