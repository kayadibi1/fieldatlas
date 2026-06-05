"""Connector + key health check — detects silent breakage (APIs change, keys expire, feeds rot).
Run periodically: .venv/Scripts/python scripts/health_check.py
"""
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from fieldatlas.config import settings
from fieldatlas.connectors import REGISTRY, run_connector

PROBE = {"queries": ["AI safety"], "arxiv_categories": ["cs.AI"],
         "harvest": {"since_year": 2020, "per_query_limit": 3}}
s = settings()
print("connector health (probe = 1 query, limit 3):")
bad = 0
for name in REGISTRY:
    try:
        recs = run_connector(name, PROBE, s, 3)
        ok = len(recs) > 0
        print(f"  {'OK ' if ok else 'WARN'} {name:18} -> {len(recs)} records")
        if not ok:
            bad += 1
    except Exception as e:
        print(f"  FAIL {name:18} -> {type(e).__name__}: {str(e)[:70]}")
        bad += 1
print(f"\nkeys: openalex={'set' if s.openalex_api_key else 'MISSING'} "
      f"core={'set' if s.core_api_key else 'MISSING'} "
      f"s2={'set' if s.semantic_scholar_api_key else 'unset'} "
      f"firecrawl={'set' if s.firecrawl_api_key else 'unset'}")
sys.exit(1 if bad else 0)
