"""Literature map / knowledge graph (deterministic, built from the verified corpus).

Clusters the read corpus into sub-areas (local embeddings + tiny k-means), labels each by
its distinctive title terms, attaches verified key-claims/methods per paper, and includes
the in-corpus citation subgraph. No LLM — every element traces to stored data.
"""
from __future__ import annotations

import json
import re
from collections import Counter

import numpy as np

from . import db
from .config import ARTIFACTS_DIR
from .rank import _model, _norm

# generic English/academic stopwords; domain-specific ones come from scope[cluster_stopwords]
_STOP = {"a", "an", "the", "of", "for", "and", "or", "to", "in", "on", "with", "using",
         "via", "toward", "towards", "based", "approach", "analysis", "study", "from",
         "into", "review", "framework", "model", "models", "learning", "system", "systems",
         "large", "language"}
_WORD = re.compile(r"[a-z][a-z0-9-]{2,}")


def _kmeans(X: np.ndarray, k: int, iters: int = 30) -> np.ndarray:
    rng = np.random.default_rng(0)
    centroids = X[rng.choice(len(X), size=k, replace=False)]
    labels = np.zeros(len(X), dtype=int)
    for _ in range(iters):
        d = ((X[:, None, :] - centroids[None, :, :]) ** 2).sum(2)
        new = d.argmin(1)
        if np.array_equal(new, labels):
            break
        labels = new
        for c in range(k):
            pts = X[labels == c]
            if len(pts):
                centroids[c] = pts.mean(0)
    return labels


def _label(titles: list[str], extra_stop=(), k_terms=3) -> str:
    stop = _STOP | set(extra_stop)
    terms = Counter()
    for t in titles:
        for w in _WORD.findall((t or "").lower()):
            if w not in stop:
                terms[w] += 1
    return ", ".join(w for w, _ in terms.most_common(k_terms)) or "misc"


def build_map(scope: dict, min_tier: int = 2) -> dict:
    con = db.connect()
    rows = con.execute(
        "SELECT canonical_id,title,abstract,year,venue,relevance,read_tier,fulltext_status "
        "FROM documents WHERE read_tier<=? ORDER BY relevance DESC, canonical_id", (min_tier,)
    ).fetchall()
    docs = [dict(r) for r in rows]
    if not docs:
        con.close()
        return {"error": "no documents in map tiers"}

    # verified extractions per doc
    extr = {}
    for r in con.execute("SELECT canonical_id,fields_json FROM extractions WHERE verify_status='verified'"):
        extr[r[0]] = json.loads(r[1])

    # citation subgraph among these docs
    ids = {d["canonical_id"] for d in docs}
    edges = [(a, b) for a, b in con.execute("SELECT citing_id,cited_id FROM citations")
             if a in ids and b in ids]
    indeg = Counter(b for _, b in edges)

    texts = [((d["title"] or "") + ". " + (d["abstract"] or "")) for d in docs]
    vecs = _norm(np.array(list(_model().embed(texts)), dtype=np.float32))
    k = min(8, max(1, len(docs) // 4), len(docs))   # clamp to data (handles 1-3 doc maps)
    labels = _kmeans(vecs, k)

    clusters = []
    for c in range(k):
        members = [docs[i] for i in range(len(docs)) if labels[i] == c]
        if not members:
            continue
        clusters.append({
            "id": c, "label": _label([m["title"] for m in members], scope.get("cluster_stopwords", [])),
            "size": len(members),
            "members": [{"canonical_id": m["canonical_id"], "title": m["title"],
                         "year": m["year"], "relevance": round(m["relevance"] or 0, 3),
                         "verified_read": m["canonical_id"] in extr,
                         "cited_in_corpus": indeg.get(m["canonical_id"], 0),
                         "key_claims": (extr.get(m["canonical_id"], {}) or {}).get("key_claims", []),
                         "methods": (extr.get(m["canonical_id"], {}) or {}).get("methods", [])}
                        for m in sorted(members, key=lambda x: x["relevance"] or 0, reverse=True)],
        })
    most_cited = sorted(indeg.items(), key=lambda x: -x[1])[:10]
    # author centrality (field-structure depth): most prolific authors among mapped docs
    top_authors = [{"name": n, "doc_count": c} for n, c in con.execute(
        "SELECT name, COUNT(DISTINCT canonical_id) c FROM authors WHERE canonical_id IN "
        "(SELECT canonical_id FROM documents WHERE read_tier<=?) AND name IS NOT NULL "
        "GROUP BY name ORDER BY c DESC, name LIMIT 20", (min_tier,))]
    con.close()

    map_obj = {
        "field": scope.get("field"),
        "n_documents": len(docs),
        "n_verified_read": len(extr),
        "n_citation_edges": len(edges),
        "clusters": sorted(clusters, key=lambda c: -c["size"]),
        "most_cited_in_corpus": [{"canonical_id": a, "in_degree": n} for a, n in most_cited],
        "top_authors": top_authors,
    }
    (ARTIFACTS_DIR / "map.json").write_text(json.dumps(map_obj, indent=2), encoding="utf-8")
    _write_map_md(map_obj)
    return map_obj


def _write_map_md(m: dict) -> None:
    lines = [f"# Literature Map — {m['field']}", "",
             f"- Documents mapped: **{m['n_documents']}**  ·  verified deep-reads: "
             f"**{m['n_verified_read']}**  ·  in-corpus citation edges: **{m['n_citation_edges']}**",
             "", "## Sub-areas (clusters)", ""]
    for c in m["clusters"]:
        lines.append(f"### {c['label']}  ({c['size']} papers)")
        for mem in c["members"][:6]:
            v = "✓read" if mem["verified_read"] else "abstract"
            lines.append(f"- [[{mem['canonical_id']}]] {mem['title']} ({mem['year']}) "
                         f"· rel={mem['relevance']} · {v} · cited×{mem['cited_in_corpus']}")
        lines.append("")
    if m.get("top_authors"):
        lines += ["## Central authors (by paper count in the mapped corpus)", ""]
        lines += [f"- {a['name']} — {a['doc_count']} papers" for a in m["top_authors"][:15]]
        lines.append("")
    (ARTIFACTS_DIR / "map.md").write_text("\n".join(lines), encoding="utf-8")
