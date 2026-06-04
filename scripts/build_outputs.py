"""Lint + assemble the Plane-2 synthesis/trends/ideas. Reads work/plane2_outputs.json."""
import json
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from fieldatlas import db
from fieldatlas.config import WORK_DIR
from fieldatlas.outputs import save_ideas, save_report, save_trends

con = db.connect()
run_id = con.execute("SELECT run_id FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()[0]
con.close()

try:
    data = json.loads((WORK_DIR / "plane2_outputs.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as e:
    print(f"ERROR reading work/plane2_outputs.json: {e}")
    sys.exit(1)
if not isinstance(data, dict):
    print("ERROR: plane2_outputs.json must be a JSON object {report_md, trends, ideas}")
    sys.exit(1)
r = save_report(data.get("report_md", ""))
t = save_trends(data.get("trends", {}))
i = save_ideas(data.get("ideas", []), run_id)
print("report:", json.dumps(r))
print("trends:", json.dumps(t))
print("ideas :", json.dumps(i))
