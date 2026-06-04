"""Ingest Plane-2 extractions and VERIFY them deterministically before they enter the corpus.

This is the boundary every reader-agent output must cross: each evidence span's quote is
string-matched into the parsed full text. Extractions with any unverifiable span are
rejected (verify_status='rejected') and surfaced for re-read — they never contribute
claims to the map/report/ideas.
"""
from __future__ import annotations

import json

from . import db
from .verify import verify_extraction


def _fulltext_for(con, cid: str) -> str | None:
    row = con.execute("SELECT parsed_md_path FROM fulltext WHERE canonical_id=?", (cid,)).fetchone()
    if not row or not row[0]:
        return None
    try:
        with open(row[0], "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def ingest_extraction(con, extraction: dict, run_id: str, reader_model: str = "claude") -> dict:
    cid = extraction.get("canonical_id")
    spans = extraction.get("spans", []) or []
    full_text = _fulltext_for(con, cid)
    if full_text is None:
        return {"canonical_id": cid, "status": "no_fulltext"}

    verdict = verify_extraction(spans, full_text)
    n_sections = max(1, len(set(s.get("section") for s in spans if s.get("section"))) or 1)
    coverage = round(len(verdict.coverage_sections) / n_sections, 3) if spans else 0.0
    if verdict.accepted:
        status = "verified"          # >= threshold of spans verified verbatim
    elif verdict.n_verified > 0:
        status = "partial"           # some verified evidence, but below threshold
    else:
        status = "rejected"          # nothing verifiable — barred from outputs

    fields = {k: v for k, v in extraction.items() if k not in ("spans", "canonical_id")}
    cur = con.execute(
        """INSERT INTO extractions(canonical_id,schema_version,fields_json,coverage_score,
                                   verify_status,reader_model,run_id)
           VALUES(?,?,?,?,?,?,?)""",
        (cid, "v1", json.dumps(fields), coverage, status, reader_model, run_id),
    )
    eid = cur.lastrowid
    for s in spans:
        ok = verify_extraction([s], full_text).accepted
        con.execute(
            "INSERT INTO evidence_spans(extraction_id,canonical_id,field,quote,section,verified) VALUES(?,?,?,?,?,?)",
            (eid, cid, s.get("field"), s.get("quote"), s.get("section"), int(ok)),
        )
    con.commit()
    return {"canonical_id": cid, "status": status, "n_spans": verdict.n_spans,
            "n_verified": verdict.n_verified, "coverage": coverage,
            "failures": verdict.failures}


def ingest_all(extractions: list[dict], run_id: str) -> dict:
    con = db.connect()
    db.init_db(con)
    results = [ingest_extraction(con, e, run_id) for e in extractions]
    con.close()
    summary = {
        "total": len(results),
        "verified": sum(1 for r in results if r.get("status") == "verified"),
        "rejected": sum(1 for r in results if r.get("status") == "rejected"),
        "no_fulltext": sum(1 for r in results if r.get("status") == "no_fulltext"),
    }
    return {"summary": summary, "results": results}
