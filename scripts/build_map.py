"""Build the literature map / knowledge graph from the verified corpus."""
import json
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from fieldatlas.config import load_scope
from fieldatlas.graph import build_map

m = build_map(load_scope())
print(json.dumps({k: v for k, v in m.items() if k != "clusters"}, indent=2))
for c in m.get("clusters", []):
    print(f"  cluster '{c['label']}' ({c['size']} papers)")
