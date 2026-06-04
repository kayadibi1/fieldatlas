"""Extract a workflow's `result` from its task output file. Usage: save_result.py <src> <dest>"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if len(sys.argv) < 3:
    print("usage: save_result.py <src> <dest>")
    sys.exit(1)
src, dest = sys.argv[1], sys.argv[2]

try:
    with open(src, encoding="utf-8") as f:
        obj = json.load(f)
except (OSError, json.JSONDecodeError) as e:
    print(f"ERROR reading {src}: {e}")
    sys.exit(1)

data = obj.get("result", obj) if isinstance(obj, dict) else obj
if data is None:
    print("WARN: result is null (workflow likely failed) -> writing []")
    data = []
if not isinstance(data, (list, dict)):
    print(f"ERROR: result is a {type(data).__name__}, expected list/dict")
    sys.exit(1)

with open(dest, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
n = len(data) if isinstance(data, list) else len(data.keys())
print(f"saved {n} {'items' if isinstance(data, list) else 'keys'} to {dest}")
