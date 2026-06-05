"""Plane-1 orchestration: one deterministic run end-to-end (no LLM).

harvest -> persist -> rank -> assign tiers -> acquire OA full text -> parse ->
build citation subgraph -> write the Plane-2 deep-read queue -> emit a run manifest.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta

from . import db
from .acquire import acquire_one, safe_name
from .config import WORK_DIR, ARTIFACTS_DIR
from .connectors.base import norm_openalex
from .harvest import harvest
from .parse import parse_pdf
from .rank import assign_tiers, rank_documents

QUEUE_PATH = WORK_DIR / "deepread_queue.json"


def new_run_id() -> str:
    return "run-" + datetime.now().strftime("%Y%m%d-%H%M%S")


def _persist_ranking(con, ranked):
    for d in ranked:
        con.execute(
            "UPDATE documents SET relevance=?, read_tier=?, is_fresh=? WHERE canonical_id=?",
            (d.get("relevance"), d.get("read_tier"), int(d.get("is_fresh", False)), d["canonical_id"]),
        )
    con.commit()


def _persist_citation_edges(con, edges_raw) -> int:
    rows = con.execute("SELECT value, canonical_id FROM external_ids WHERE scheme='openalex'")
    oa2can = {v: c for v, c in rows}
    n = 0
    for citing, ref in edges_raw:
        a = oa2can.get(norm_openalex(citing))
        b = oa2can.get(norm_openalex(ref))
        if a and b and a != b:
            con.execute("INSERT OR IGNORE INTO citations(citing_id,cited_id,source) VALUES(?,?,?)",
                        (a, b, "openalex"))
            n += 1
    con.commit()
    return n


def _set_fulltext(con, cid, status):
    con.execute("UPDATE documents SET fulltext_status=? WHERE canonical_id=?", (status, cid))


def run_plane1(scope, settings, sources=None, per_query_limit=None,
               acquire_tiers=(1, 2), max_acquire=None, delta=False) -> dict:
    con = db.connect()
    db.init_db(con)
    run_id = new_run_id()

    # delta/living-system mode: harvest only works published since the last run (minus a buffer)
    if delta:
        last = con.execute("SELECT started_at FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()
        if last and last[0]:
            since = (datetime.fromisoformat(last[0]) - timedelta(days=7)).strftime("%Y-%m-%d")
            scope = {**scope, "harvest": {**scope.get("harvest", {}), "since_date": since}}

    # 1-2. harvest + persist
    docs, hmanifest = harvest(scope, settings, sources, per_query_limit)
    edges_raw = hmanifest.pop("citation_edges_openalex", [])
    n_new = db.upsert_documents(con, docs, run_id)

    # 3-4. rank + tiers
    ranked = rank_documents(docs, scope)
    tier_stats = assign_tiers(ranked, scope)
    # citation-centrality: force the most-cited in-corpus nodes into Tier-1 so the field's
    # heavily-cited anchors (which the snowball pulls in) get deep-read, not left at abstract level
    oa2can = {v: c for v, c in con.execute("SELECT value, canonical_id FROM external_ids WHERE scheme='openalex'")}
    indeg = Counter()
    for _citing, ref in edges_raw:
        b = oa2can.get(norm_openalex(ref))
        if b:
            indeg[b] += 1
    force_n = scope.get("read_tiers", {}).get("centrality_force", 60)
    top_cited = {cid for cid, _ in indeg.most_common(force_n)}
    n_forced = 0
    for d in ranked:
        if d["canonical_id"] in top_cited and d.get("read_tier") != 1:
            d["read_tier"] = 1
            n_forced += 1
    tier_stats["centrality_forced"] = n_forced
    _persist_ranking(con, ranked)
    n_edges = _persist_citation_edges(con, edges_raw)

    # 5. acquire + parse full text for the deep-read tiers. Only attempt docs with an
    # obtainable full-text handle (DOI/arXiv/OA PDF); URL-only grey-lit enriches the map
    # and synthesis at abstract level rather than burning deep-read attempts.
    def _acquirable(d):
        ids = d.get("external_ids", {})
        return bool(ids.get("doi") or ids.get("arxiv") or d.get("oa_pdf_url"))

    to_read = [d for d in ranked if d.get("read_tier") in acquire_tiers and _acquirable(d)]
    to_read.sort(key=lambda d: (d.get("read_tier", 9), -(d.get("relevance") or 0)))  # Tier-1 (incl forced canon) first
    if max_acquire:
        to_read = to_read[:max_acquire]
    acq = {"fetched": 0, "metadata_only": 0, "parsed": 0, "parse_failed": 0}
    queue = []
    for d in to_read:
        cid = d["canonical_id"]
        res = acquire_one(d, settings)
        if res["status"] != "fetched":
            _set_fulltext(con, cid, "metadata_only")
            acq["metadata_only"] += 1
            continue
        acq["fetched"] += 1
        p = parse_pdf(res["path"], cid, safe_name(cid))
        if p["parse_status"] != "parsed":
            _set_fulltext(con, cid, "fetched")
            acq["parse_failed"] += 1
            continue
        con.execute(
            """INSERT INTO fulltext(canonical_id,format,parsed_md_path,char_count,parse_tool,
                                    parse_status,content_hash)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(canonical_id) DO UPDATE SET parsed_md_path=excluded.parsed_md_path,
                 char_count=excluded.char_count, parse_status=excluded.parse_status,
                 content_hash=excluded.content_hash""",
            (cid, "pdf", p["parsed_md_path"], p["char_count"], p["parse_tool"],
             p["parse_status"], p["content_hash"]),
        )
        _set_fulltext(con, cid, "parsed")
        acq["parsed"] += 1
        queue.append({"canonical_id": cid, "title": d.get("title"),
                      "read_tier": d["read_tier"], "md_path": p["parsed_md_path"],
                      "sections": p["sections"], "venue": d.get("venue"),
                      "year": d.get("year")})
    con.commit()

    QUEUE_PATH.write_text(json.dumps(queue, indent=2), encoding="utf-8")

    manifest = {
        "run_id": run_id, "scope": scope.get("field"),
        "new_documents": n_new, "harvest": hmanifest,
        "ranking": tier_stats, "citation_edges": n_edges,
        "acquisition": acq, "deepread_queued": len(queue),
        "sources_used": sources or "all",
    }
    con.execute(
        "INSERT OR REPLACE INTO runs(run_id,started_at,manifest_json,scope_version) VALUES(?,?,?,?)",
        (run_id, datetime.now().isoformat(timespec="seconds"), json.dumps(manifest), scope.get("field")),
    )
    con.commit()
    (ARTIFACTS_DIR / f"{run_id}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    con.close()
    return manifest
