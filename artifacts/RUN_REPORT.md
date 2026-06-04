# FieldAtlas Run Report — run-20260604-144712

**Field:** AI safety ∩ AI policy  ·  **Sources:** ['openalex', 'crossref', 'core', 'greylit', 'federal_register']

## F3 — Gathering (recall accounting)
- Raw records harvested: **3102**  →  unique documents after cross-source dedup: **2977** (dedup ratio 0.042)
- Corroborated by ≥2 sources: **95**  ·  single-source: **2877**
- Per-source raw counts: `{"openalex": {"raw": 1177}, "crossref": {"raw": 1174}, "core": {"raw": 539}, "greylit": {"raw": 112}, "federal_register": {"raw": 100}}`
- With abstract: 2065  ·  with an OA PDF link: 1149

## Ranking & read tiers
- Tier 1 (deep-read+verify): **341**  ·  Tier 2: 704  ·  Tier 3 (abstract map): 1932
- Relevance threshold 0.55 / cap 300; fresh-lane added 40

## F1 — Reading (proof, not assertion)
- Full text parsed: **149**  ·  NOT-READ (metadata_only): 149
- Deep-read extractions VERIFIED: **144**  ·  rejected (unverifiable span): 0
- Evidence spans string-matched into source: **3923 verified**, 66 failed

## F2 — Citations (grounded)
- In-corpus citation edges: 791
- Every artifact citation linted against the corpus; unresolved ids flagged in each file.

## Outputs
- `artifacts/map.md` / `map.json` — literature map / knowledge graph
- `artifacts/report.md` — state-of-the-field synthesis (citation-linted)
- `artifacts/trends.md` / `trends.json` — trends & controversy
- `artifacts/ideas.md` / `ideas.json` — 27 research proposals (grounded + novelty-checked)

## Honesty notes
- Items with no obtainable OA full text are NOT-READ and contribute no deep claims (shown above).
- Shadow-library sources excluded by design; OA coverage via arXiv/CORE/Unpaywall only.