"""Register a PDF you obtained yourself (e.g. via your own JHU individual access) so the
pipeline can read it. This keeps the license-permitted *individual* access with YOU, and
only the reading/analysis with the tool — no automated access to any paywall.

Usage:
   .venv/Scripts/python scripts/add_manual_pdf.py <id> <path-to.pdf>
where <id> is a canonical_id already in the corpus, or a doi:/arxiv: id, e.g.
   ... add_manual_pdf.py doi:10.1016/j.artint.2021.103535  "C:/Users/Sidar/Downloads/paper.pdf"
If the id isn't in the corpus yet, the PDF is still registered under that id.
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, ".")
from fieldatlas import db
from fieldatlas.acquire import PDF_DIR, safe_name
from fieldatlas.parse import parse_pdf

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(1)
raw_id, src_pdf = sys.argv[1], sys.argv[2]
src = Path(src_pdf)
if not src.exists() or src.suffix.lower() != ".pdf":
    print(f"ERROR: {src} is not a readable .pdf")
    sys.exit(1)

con = db.connect()
db.init_db(con)

# resolve to a canonical_id: direct hit, or via external_ids (doi:.../arxiv:... -> scheme,value)
cid = None
if con.execute("SELECT 1 FROM documents WHERE canonical_id=?", (raw_id,)).fetchone():
    cid = raw_id
elif ":" in raw_id:
    scheme, value = raw_id.split(":", 1)
    row = con.execute("SELECT canonical_id FROM external_ids WHERE scheme=? AND value=?",
                      (scheme, value.lower() if scheme == "doi" else value)).fetchone()
    cid = row[0] if row else raw_id
cid = cid or raw_id

dest = PDF_DIR / f"{safe_name(cid)}.pdf"
if PDF_DIR.resolve() not in dest.resolve().parents:   # belt-and-suspenders vs path traversal
    print("ERROR: unsafe destination path")
    sys.exit(1)
shutil.copyfile(src, dest)
p = parse_pdf(str(dest), cid, safe_name(cid))
if p["parse_status"] != "parsed":
    print(f"parse failed: {p.get('error')}")
    sys.exit(1)

con.execute(
    """INSERT INTO fulltext(canonical_id,format,parsed_md_path,char_count,parse_tool,parse_status,content_hash)
       VALUES(?,?,?,?,?,?,?)
       ON CONFLICT(canonical_id) DO UPDATE SET parsed_md_path=excluded.parsed_md_path,
         char_count=excluded.char_count, parse_status=excluded.parse_status,
         content_hash=excluded.content_hash""",
    (cid, "pdf", p["parsed_md_path"], p["char_count"], "pymupdf4llm", "parsed", p["content_hash"]),
)
# ensure it exists as a Tier-1 doc so the deep-read picks it up
con.execute(
    """INSERT INTO documents(canonical_id,title,read_tier,fulltext_status,source_tiers,sources)
       VALUES(?,?,?,?,?,?)
       ON CONFLICT(canonical_id) DO UPDATE SET read_tier=1, fulltext_status='parsed'""",
    (cid, cid, 1, "parsed", '["manual"]', '["manual"]'),
)
con.commit()
con.close()
print(f"registered {cid}: parsed {p['char_count']} chars -> {p['parsed_md_path']}")
print("Add it to work/deepread_queue.json (canonical_id + md_path) and re-run the deep-read workflow.")
