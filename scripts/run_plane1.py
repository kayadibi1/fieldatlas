"""Run the deterministic Plane-1 pipeline. Usage:
   .venv/Scripts/python scripts/run_plane1.py [per_query_limit] [max_acquire]
"""
import json
import sys

sys.path.insert(0, ".")
from fieldatlas.config import load_scope, settings
from fieldatlas.pipeline import run_plane1

per_query_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 40
max_acquire = int(sys.argv[2]) if len(sys.argv) > 2 else 12

# Verified-run sources: the three fast, reliable APIs. OpenAlex already indexes arXiv
# preprints, so preprint coverage is preserved. arXiv's live query API (slow + rate-limits)
# and Semantic Scholar (keyless throttle) are wired + registered; add them once you accept
# the slower run / provide the S2 key. Override via argv[3] as a comma list.
DEFAULT_SOURCES = ["openalex", "crossref", "core"]
if len(sys.argv) > 3:
    DEFAULT_SOURCES = sys.argv[3].split(",")

scope = load_scope()
m = run_plane1(scope, settings(),
               sources=DEFAULT_SOURCES,
               per_query_limit=per_query_limit, acquire_tiers=(1, 2),
               max_acquire=max_acquire)
print(json.dumps(m, indent=2))
