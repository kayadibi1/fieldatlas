"""Ingest + verify Plane-2 deep-read extractions. Reads work/extractions_raw.json."""
import json
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows console is cp1252
from fieldatlas import db
from fieldatlas.ingest import ingest_all
from fieldatlas.config import WORK_DIR

con = db.connect()
run_id = con.execute("SELECT run_id FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()[0]
con.close()

try:
    extractions = json.loads((WORK_DIR / "extractions_raw.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as e:
    print(f"ERROR reading work/extractions_raw.json: {e}")
    sys.exit(1)
if not isinstance(extractions, list):
    print("ERROR: extractions_raw.json must be a JSON array of extractions")
    sys.exit(1)
out = ingest_all(extractions, run_id)
print(json.dumps(out["summary"], indent=2))
for r in out["results"]:
    flag = "" if r.get("status") == "verified" else f"  <-- {r.get('status')}"
    print(f"  {r.get('canonical_id')}: {r.get('status')} "
          f"spans {r.get('n_verified','?')}/{r.get('n_spans','?')} cov={r.get('coverage','?')}{flag}")
    for f in (r.get("failures") or [])[:3]:
        print(f"      REJECTED span [{f[0]}] ({f[2]}): {f[1]!r}")
