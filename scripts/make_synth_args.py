"""Build the args payload for the synthesis/idea workflow from the verified corpus."""
import json
import sys
from collections import Counter

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from fieldatlas import db
from fieldatlas.config import WORK_DIR, ARTIFACTS_DIR, load_scope

con = db.connect()
scope = load_scope()

verified = []
for r in con.execute(
    "SELECT e.canonical_id, e.fields_json, d.title, d.year FROM extractions e "
    # idea grounding requires FULLY verified extractions (>=85% spans verbatim), not 'partial'
    "JOIN documents d ON d.canonical_id=e.canonical_id WHERE e.verify_status='verified' "
    "ORDER BY d.relevance DESC, e.canonical_id LIMIT 80"):
    f = json.loads(r[1])
    verified.append({"id": r[0], "title": r[2], "year": r[3],
                     "problem": f.get("problem"), "methods": f.get("methods", []),
                     "key_claims": f.get("key_claims", []), "limitations": f.get("limitations"),
                     "topics": f.get("topics", []),
                     # full reading depth — previously dropped, leaving synthesis abstract-thin
                     "results": f.get("results"), "contributions": f.get("contributions", []),
                     "data_setup": f.get("data_setup"), "relation_to_field": f.get("relation_to_field"),
                     "relations": f.get("relations", []), "metrics": f.get("metrics", [])})

report_corpus = []
for r in con.execute(
    "SELECT canonical_id,title,year,venue,abstract FROM documents "
    "WHERE relevance IS NOT NULL ORDER BY relevance DESC, canonical_id LIMIT 60"):
    report_corpus.append({"id": r[0], "title": r[1], "year": r[2], "venue": r[3],
                          "abstract": (r[4] or "")[:600]})

year_hist = dict(Counter(r[0] for r in con.execute(
    "SELECT year FROM documents WHERE read_tier<=2 AND year IS NOT NULL")))

clusters = []
mp = ARTIFACTS_DIR / "map.json"
if mp.exists():
    try:
        mp_data = json.loads(mp.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        mp_data = {}
    for c in mp_data.get("clusters", []):
        ids = [m.get("canonical_id") for m in c.get("members", []) if m.get("canonical_id")]
        clusters.append({"label": c.get("label", ""), "ids": ids})

# citation graph: in-corpus hubs (most cited) + edges among report papers (for lineage tracing)
cg = {"most_cited": [], "edges": []}
for cid, deg in con.execute(
        "SELECT cited_id, COUNT(*) d FROM citations GROUP BY cited_id ORDER BY d DESC LIMIT 15"):
    t = con.execute("SELECT title, year FROM documents WHERE canonical_id=?", (cid,)).fetchone()
    if t:
        cg["most_cited"].append({"id": cid, "title": t[0], "year": t[1], "in_degree": deg})
report_ids = {d["id"] for d in report_corpus}
for a, b in con.execute("SELECT citing_id, cited_id FROM citations"):
    if a in report_ids and b in report_ids:
        cg["edges"].append([a, b])

con.close()
args = {"field": scope.get("field"), "report_corpus": report_corpus,
        "verified_corpus": verified, "clusters": clusters, "year_hist": year_hist,
        "citation_graph": cg}
(WORK_DIR / "synth_args.json").write_text(json.dumps(args, indent=2), encoding="utf-8")
print(f"verified_corpus={len(verified)} report_corpus={len(report_corpus)} clusters={len(clusters)}")
