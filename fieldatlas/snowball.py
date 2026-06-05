"""Citation snowball expansion — the spec's F3 recall-depth mechanism.

After the keyword-query round, this:
  1. Fetches the scope's seed_corpus anchors directly (id-based, DATE-EXEMPT) so the field's
     canon is guaranteed present.
  2. Expands the citation neighborhood: backward (referenced_works) + forward (cites:) from
     the seed + most-cited query nodes, fetching those works as new corpus members. Cited
     works are date-exempt, so this breaches the since_year wall toward the field's roots.
  3. Repeats for snowball_rounds or until per-round new-unique yield < convergence_pct.

Bounded by design (frontier cap, per-node forward cap, per-round new cap) so it stays within
OpenAlex's freemium budget. OpenAlex provides BOTH directions (referenced_works + cites:).
"""
from __future__ import annotations

from .connectors import arxiv, openalex
from .connectors.base import norm_doi

FRONTIER_CAP = 80      # nodes to expand per round (highest cited_by_count)
FWD_PER_NODE = 50      # forward citers fetched per frontier node
BACK_CAP = 2000        # backward reference ids fetched per round
NEW_PER_ROUND = 1200   # cap on new docs added per round


def _oa(rec) -> str | None:
    return rec.external_ids.get("openalex")


def _cited(rec) -> int:
    return (rec.extra or {}).get("cited_by_count") or 0


def fetch_seeds(scope: dict, settings) -> list:
    """Direct id-based fetch of the seed_corpus anchors (bypasses search + date filter)."""
    seed = scope.get("seed_corpus") or {}
    recs = []
    if seed.get("arxiv_ids"):
        recs += arxiv.fetch_by_ids(seed["arxiv_ids"])
    dois = [norm_doi(d) for d in seed.get("dois", [])]
    if dois:
        recs += openalex.fetch_by_dois(dois, settings)
    return recs


def expand(query_records: list, scope: dict, settings) -> tuple[list, list]:
    """Return (extra_records, convergence_curve). query_records = round-0 query hits."""
    h = scope.get("harvest", {})
    rounds = int(h.get("snowball_rounds", 0) or 0)
    conv_pct = float(h.get("snowball_convergence_pct", 2.0))
    seen = {_oa(r) for r in query_records if _oa(r)}
    extra, curve = [], []

    for r in fetch_seeds(scope, settings):     # seeds (canon anchors)
        oid = _oa(r)
        if oid and oid in seen:
            continue
        if oid:
            seen.add(oid)
        extra.append(r)

    if rounds <= 0:
        return extra, curve

    oa_query = [r for r in query_records if r.source == "openalex" and _oa(r)]
    frontier = ([r for r in extra if _oa(r)] + sorted(oa_query, key=_cited, reverse=True))[:FRONTIER_CAP]

    for rnd in range(rounds):
        back_ids = []
        for r in frontier:
            for ref in (r.extra or {}).get("referenced_works", []):
                s = ref.rsplit("/", 1)[-1]
                if s and s not in seen:
                    back_ids.append(s)
        back_ids = list(dict.fromkeys(back_ids))[:BACK_CAP]
        candidates = openalex.fetch_by_openalex_ids(back_ids, settings)        # backward
        for r in frontier:                                                     # forward
            candidates += openalex.fetch_citing(_oa(r), settings, limit=FWD_PER_NODE)

        new = []
        for r in candidates:
            oid = _oa(r)
            if oid and oid not in seen:
                seen.add(oid)
                new.append(r)
                if len(new) >= NEW_PER_ROUND:
                    break
        extra += new
        total = len(query_records) + len(extra)
        yld = round(100.0 * len(new) / max(1, total), 2)
        curve.append({"round": rnd + 1, "new": len(new), "yield_pct": yld})
        if not new or yld < conv_pct:
            break
        frontier = sorted(new, key=_cited, reverse=True)[:FRONTIER_CAP]

    return extra, curve
