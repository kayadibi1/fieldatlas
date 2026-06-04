"""Acquire + parse all unread, acquirable Tier-1 documents (full OA deep-read prep).

Targets docs already in the corpus (no re-harvest): read_tier=1, not yet parsed, with a
DOI/arXiv/OA handle. Writes the newly-parsed set to work/deepread_full.json. Honestly
marks the rest metadata_only. Usage: acquire_tier1.py [max_attempts]
"""
import json
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from fieldatlas import db
from fieldatlas.acquire import acquire_one, safe_name
from fieldatlas.config import WORK_DIR, settings
from fieldatlas.parse import parse_pdf

limit = int(sys.argv[1]) if len(sys.argv) > 1 else 400
con = db.connect()
rows = con.execute(
    """SELECT d.canonical_id, d.oa_pdf_url FROM documents d
       WHERE d.read_tier=1 AND d.fulltext_status!='parsed'
         AND (d.oa_pdf_url IS NOT NULL OR EXISTS(
              SELECT 1 FROM external_ids e WHERE e.canonical_id=d.canonical_id
                AND e.scheme IN ('doi','arxiv')))
       ORDER BY d.relevance DESC LIMIT ?""", (limit,)).fetchall()
s = settings()
parsed = []
for i, (cid, oa) in enumerate(rows, 1):
    ids = {sch: val for sch, val in
           con.execute("SELECT scheme,value FROM external_ids WHERE canonical_id=?", (cid,))}
    res = acquire_one({"canonical_id": cid, "external_ids": ids, "oa_pdf_url": oa}, s)
    if res["status"] != "fetched":
        con.execute("UPDATE documents SET fulltext_status='metadata_only' WHERE canonical_id=?", (cid,))
        con.commit()
        continue
    p = parse_pdf(res["path"], cid, safe_name(cid))
    if p["parse_status"] != "parsed":
        con.execute("UPDATE documents SET fulltext_status='fetched' WHERE canonical_id=?", (cid,))
        con.commit()
        continue
    con.execute(
        """INSERT INTO fulltext(canonical_id,format,parsed_md_path,char_count,parse_tool,parse_status,content_hash)
           VALUES(?,?,?,?,?,?,?)
           ON CONFLICT(canonical_id) DO UPDATE SET parsed_md_path=excluded.parsed_md_path,
             char_count=excluded.char_count, parse_status=excluded.parse_status,
             content_hash=excluded.content_hash""",
        (cid, "pdf", p["parsed_md_path"], p["char_count"], "pymupdf4llm", "parsed", p["content_hash"]))
    con.execute("UPDATE documents SET fulltext_status='parsed' WHERE canonical_id=?", (cid,))
    con.commit()
    parsed.append({"canonical_id": cid, "md_path": p["parsed_md_path"]})
    if len(parsed) % 10 == 0:
        print(f"  parsed {len(parsed)} (attempt {i}/{len(rows)})", flush=True)

(WORK_DIR / "deepread_full.json").write_text(json.dumps(parsed, indent=1), encoding="utf-8")
print(f"DONE: parsed {len(parsed)} of {len(rows)} attempted")
