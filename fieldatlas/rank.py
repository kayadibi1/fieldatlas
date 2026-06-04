"""Relevance ranking (keyless, local) + read-tier assignment.

Embeds title+abstract with a local ONNX model (bge-small) and scores cosine similarity
to the scope description. Two lanes: a global relevance ranking and a recency-protected
fresh-preprint lane (citation-blind) so brand-new work is never buried.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

_MODEL = None


def _model(name="BAAI/bge-small-en-v1.5"):
    global _MODEL
    if _MODEL is None:
        from fastembed import TextEmbedding
        _MODEL = TextEmbedding(model_name=name)
    return _MODEL


def _norm(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return m / n


def scope_text(scope: dict) -> str:
    return (scope.get("boundary", "") + " Topics: " + "; ".join(scope.get("queries", []))).strip()


def _days_old(pub_date: str | None) -> float | None:
    if not pub_date:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            d = datetime.strptime(pub_date[:len(fmt) + 2 if "%d" in fmt else 7], fmt)
            return (datetime.now(timezone.utc).replace(tzinfo=None) - d).days
        except ValueError:
            continue
    return None


def rank_documents(docs: list[dict], scope: dict) -> list[dict]:
    """Annotate each doc with `relevance` (cosine) and `is_fresh`. Returns docs sorted desc."""
    if not docs:                       # empty corpus: nothing to rank (avoid embed/_norm crash)
        return []
    model = _model(scope.get("ranking", {}).get("embedding_model", "BAAI/bge-small-en-v1.5"))
    texts = [((d.get("title") or "") + ". " + (d.get("abstract") or "")).strip() for d in docs]
    doc_vecs = _norm(np.array(list(model.embed(texts)), dtype=np.float32))
    q_vec = _norm(np.array(list(model.query_embed([scope_text(scope)])), dtype=np.float32))
    sims = (doc_vecs @ q_vec[0]).tolist()

    fresh_days = scope.get("ranking", {}).get("fresh_window_days", 60)
    for d, s in zip(docs, sims):
        d["relevance"] = float(s)
        age = _days_old(d.get("pub_date") or (str(d["year"]) if d.get("year") else None))
        d["is_fresh"] = bool(age is not None and age <= fresh_days)
    return sorted(docs, key=lambda d: d["relevance"], reverse=True)


def assign_tiers(ranked: list[dict], scope: dict) -> dict:
    """Assign read_tier in place. Tier1 = relevance>=threshold OR top-cap (whichever is
    fewer) PLUS fresh-lane docs above the fresh content threshold (up to quota)."""
    rt = scope.get("read_tiers", {})
    thresh = rt.get("tier1_threshold", 0.55)
    cap = rt.get("tier1_cap", 300)
    fresh_quota = rt.get("fresh_lane_quota", 40)
    tier2_band = rt.get("tier2_band", 700)

    above = [d for d in ranked if d["relevance"] >= thresh]
    tier1 = above[:cap]
    tier1_ids = {d["canonical_id"] for d in tier1}

    # fresh lane: recent, content-relevant items not already in tier1
    fresh = [d for d in ranked if d["is_fresh"] and d["canonical_id"] not in tier1_ids
             and d["relevance"] >= thresh * 0.8][:fresh_quota]
    for d in fresh:
        tier1_ids.add(d["canonical_id"])

    rest = [d for d in ranked if d["canonical_id"] not in tier1_ids]
    tier2 = rest[:tier2_band]
    tier2_ids = {d["canonical_id"] for d in tier2}

    for d in ranked:
        if d["canonical_id"] in tier1_ids:
            d["read_tier"] = 1
        elif d["canonical_id"] in tier2_ids:
            d["read_tier"] = 2
        else:
            d["read_tier"] = 3
    return {"tier1": len(tier1_ids), "tier2": len(tier2_ids),
            "tier3": len(ranked) - len(tier1_ids) - len(tier2_ids),
            "fresh_lane": len(fresh), "threshold": thresh, "cap": cap}
