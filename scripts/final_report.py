"""Assemble artifacts/RUN_REPORT.md — the auditability manifest (completeness + reading as data)."""
import json
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows console is cp1252
from fieldatlas import db
from fieldatlas.config import ARTIFACTS_DIR

con = db.connect()
run = con.execute("SELECT run_id, manifest_json FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()
run_id, manifest = run[0], json.loads(run[1])

def q(sql):
    return con.execute(sql).fetchone()[0]

stats = {
    "documents": q("SELECT COUNT(*) FROM documents"),
    "tier1": q("SELECT COUNT(*) FROM documents WHERE read_tier=1"),
    "tier2": q("SELECT COUNT(*) FROM documents WHERE read_tier=2"),
    "tier3": q("SELECT COUNT(*) FROM documents WHERE read_tier=3"),
    "parsed_fulltext": q("SELECT COUNT(*) FROM documents WHERE fulltext_status='parsed'"),
    "metadata_only": q("SELECT COUNT(*) FROM documents WHERE fulltext_status='metadata_only'"),
    "extractions_verified": q("SELECT COUNT(*) FROM extractions WHERE verify_status='verified'"),
    "extractions_rejected": q("SELECT COUNT(*) FROM extractions WHERE verify_status='rejected'"),
    "evidence_spans_verified": q("SELECT COUNT(*) FROM evidence_spans WHERE verified=1"),
    "evidence_spans_failed": q("SELECT COUNT(*) FROM evidence_spans WHERE verified=0"),
    "citation_edges": q("SELECT COUNT(*) FROM citations"),
    "ideas": q("SELECT COUNT(*) FROM ideas"),
}
con.close()

h = manifest.get("harvest", {})
rk = manifest.get("ranking", {})
ac = manifest.get("acquisition", {})

L = [f"# FieldAtlas Run Report — {run_id}", "",
     f"**Field:** {manifest.get('scope')}  ·  **Sources:** {manifest.get('sources_used')}", "",
     "## F3 — Gathering (recall accounting)",
     f"- Raw records harvested: **{h.get('raw_records')}**  →  unique documents after cross-source dedup: **{stats['documents']}** (dedup ratio {h.get('dedup_ratio')})",
     f"- Corroborated by ≥2 sources: **{h.get('multi_source_documents')}**  ·  single-source: **{h.get('single_source_documents')}**",
     f"- Per-source raw counts: `{json.dumps(h.get('sources', {}))}`",
     f"- With abstract: {h.get('documents_with_abstract')}  ·  with an OA PDF link: {h.get('documents_with_oa_pdf')}", "",
     "## Ranking & read tiers",
     f"- Tier 1 (deep-read+verify): **{stats['tier1']}**  ·  Tier 2: {stats['tier2']}  ·  Tier 3 (abstract map): {stats['tier3']}",
     f"- Relevance threshold {rk.get('threshold')} / cap {rk.get('cap')}; fresh-lane added {rk.get('fresh_lane')}", "",
     "## F1 — Reading (proof, not assertion)",
     f"- Full text parsed: **{stats['parsed_fulltext']}**  ·  NOT-READ (metadata_only): {stats['metadata_only']}",
     f"- Deep-read extractions VERIFIED: **{stats['extractions_verified']}**  ·  rejected (unverifiable span): {stats['extractions_rejected']}",
     f"- Evidence spans string-matched into source: **{stats['evidence_spans_verified']} verified**, {stats['evidence_spans_failed']} failed", "",
     "## F2 — Citations (grounded)",
     f"- In-corpus citation edges: {stats['citation_edges']}",
     "- Every artifact citation linted against the corpus; unresolved ids flagged in each file.", "",
     "## Outputs",
     "- `artifacts/map.md` / `map.json` — literature map / knowledge graph",
     "- `artifacts/report.md` — state-of-the-field synthesis (citation-linted)",
     "- `artifacts/trends.md` / `trends.json` — trends & controversy",
     f"- `artifacts/ideas.md` / `ideas.json` — {stats['ideas']} research proposals (grounded + novelty-checked)", "",
     "## Honesty notes",
     "- Items with no obtainable OA full text are NOT-READ and contribute no deep claims (shown above).",
     "- Shadow-library sources excluded by design; OA coverage via arXiv/CORE/Unpaywall only.",
     ]
(ARTIFACTS_DIR / "RUN_REPORT.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
