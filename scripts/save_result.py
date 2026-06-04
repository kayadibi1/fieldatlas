"""Extract a workflow's `result` array from its task output file. Usage: save_result.py <src> <dest>"""
import json
import sys

src, dest = sys.argv[1], sys.argv[2]
obj = json.load(open(src, encoding="utf-8"))
data = obj["result"] if isinstance(obj, dict) and "result" in obj else obj
json.dump(data, open(dest, "w", encoding="utf-8"), indent=2)
print(f"saved {len(data)} items to {dest}")
