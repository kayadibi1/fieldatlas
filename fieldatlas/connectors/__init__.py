"""Connector registry. Each connector exposes search(scope, settings, limit) -> [RawRecord]."""
from __future__ import annotations

from . import arxiv, core, crossref, openalex, semantic_scholar

REGISTRY = {
    "arxiv": arxiv,
    "openalex": openalex,
    "crossref": crossref,
    "semantic_scholar": semantic_scholar,
    "core": core,
}


def run_connector(name: str, scope: dict, settings, limit: int):
    mod = REGISTRY[name]
    return mod.search(scope, settings, limit)
