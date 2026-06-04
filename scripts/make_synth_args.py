"""Build the args payload for the synthesis/idea workflow from the verified corpus."""
import json
import sys
from collections import Counter

sys.path.insert(0, ".")
from fieldatlas import db
from fieldatlas.config import WORK_DIR, ARTIFACTS_DIR, load_scope

con = db.connect()
scope = load_scope()

verified = []
for r in con.execute(
    "SELECT e.canonical_id, e.fields_json, d.title, d.year FROM extractions e "
    # idea grounding requires FULLY verified extractions (>=85% spans verbatim), not 'partial'
    "JOIN documents d ON d.canonical_id=e.canonical_id WHERE e.verify_status='verified' "
    "ORDER BY d.relevance DESC LIMIT 80"):
    f = json.loads(r[1])
    verified.append({"id": r[0], "title": r[2], "year": r[3],
                     "problem": f.get("problem"), "methods": f.get("methods", []),
                     "key_claims": f.get("key_claims", []), "limitations": f.get("limitations"),
                     "topics": f.get("topics", [])})

report_corpus = []
for r in con.execute(
    "SELECT canonical_id,title,year,venue,abstract FROM documents "
    "WHERE relevance IS NOT NULL ORDER BY relevance DESC LIMIT 60"):
    report_corpus.append({"id": r[0], "title": r[1], "year": r[2], "venue": r[3],
                          "abstract": (r[4] or "")[:600]})

year_hist = dict(Counter(r[0] for r in con.execute(
    "SELECT year FROM documents WHERE read_tier<=2 AND year IS NOT NULL")))

clusters = []
mp = ARTIFACTS_DIR / "map.json"
if mp.exists():
    for c in json.loads(mp.read_text(encoding="utf-8")).get("clusters", []):
        clusters.append({"label": c["label"], "ids": [m["canonical_id"] for m in c["members"]]})

con.close()
args = {"field": scope.get("field"), "report_corpus": report_corpus,
        "verified_corpus": verified, "clusters": clusters, "year_hist": year_hist}
(WORK_DIR / "synth_args.json").write_text(json.dumps(args, indent=2), encoding="utf-8")
print(f"verified_corpus={len(verified)} report_corpus={len(report_corpus)} clusters={len(clusters)}")
