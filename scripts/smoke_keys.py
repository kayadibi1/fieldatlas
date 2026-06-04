"""Live smoke test of API keys + key deps. Run: .venv/Scripts/python scripts/smoke_keys.py"""
import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows console is cp1252

from fieldatlas.config import settings
from fieldatlas.connectors.http import get

s = settings()
print("deps:", end=" ")
import fastembed, pymupdf4llm, numpy, feedparser, yaml  # noqa
print("ok (fastembed, pymupdf4llm, numpy, feedparser, yaml)")

# OpenAlex (freemium key)
r = get("https://api.openalex.org/works",
        params={"search": "AI safety", "per_page": 1, "api_key": s.openalex_api_key})
j = r.json()
print(f"OpenAlex: {r.status_code} total={j['meta']['count']} cost_usd={j['meta'].get('cost_usd')}")

# CORE (OA full-text aggregator)
r2 = get("https://api.core.ac.uk/v3/search/works",
         params={"q": "AI safety governance", "limit": 1},
         headers={"Authorization": f"Bearer {s.core_api_key}"})
res = r2.json().get("results", [])
print(f"CORE: {r2.status_code} got={len(res)} sample={(res[0].get('title') if res else None)!r:.70}")

# arXiv (keyless)
r3 = get("https://export.arxiv.org/api/query",
         params={"search_query": "cat:cs.AI AND abs:\"AI safety\"", "max_results": 1})
print(f"arXiv: {r3.status_code} bytes={len(r3.text)}")
print("SMOKE OK")
