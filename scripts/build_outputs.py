"""Lint + assemble the Plane-2 synthesis/trends/ideas. Reads work/plane2_outputs.json."""
import json
import sys

sys.path.insert(0, ".")
from fieldatlas import db
from fieldatlas.config import WORK_DIR
from fieldatlas.outputs import save_ideas, save_report, save_trends

con = db.connect()
run_id = con.execute("SELECT run_id FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()[0]
con.close()

data = json.loads((WORK_DIR / "plane2_outputs.json").read_text(encoding="utf-8"))
r = save_report(data.get("report_md", ""))
t = save_trends(data.get("trends", {}))
i = save_ideas(data.get("ideas", []), run_id)
print("report:", json.dumps(r))
print("trends:", json.dumps(t))
print("ideas :", json.dumps(i))
