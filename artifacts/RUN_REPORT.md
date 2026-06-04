# FieldAtlas Run Report — run-20260604-024848

**Field:** AI safety ∩ AI policy  ·  **Sources:** ['openalex', 'crossref', 'core']

## F3 — Gathering (recall accounting)
- Raw records harvested: **1161**  →  unique documents after cross-source dedup: **1116** (dedup ratio 0.039)
- Corroborated by ≥2 sources: **27**  ·  single-source: **1089**
- Per-source raw counts: `{"openalex": {"raw": 479}, "crossref": {"raw": 470}, "core": {"raw": 212}}`
- With abstract: 756  ·  with an OA PDF link: 463

## Ranking & read tiers
- Tier 1 (deep-read+verify): **300**  ·  Tier 2: 700  ·  Tier 3 (abstract map): 116
- Relevance threshold 0.55 / cap 300; fresh-lane added 0

## F1 — Reading (proof, not assertion)
- Full text parsed: **5**  ·  NOT-READ (metadata_only): 5
- Deep-read extractions VERIFIED: **5**  ·  rejected (unverifiable span): 0
- Evidence spans string-matched into source: **120 verified**, 3 failed

## F2 — Citations (grounded)
- In-corpus citation edges: 276
- Every artifact citation linted against the corpus; unresolved ids flagged in each file.

## Outputs
- `artifacts/map.md` / `map.json` — literature map / knowledge graph
- `artifacts/report.md` — state-of-the-field synthesis (citation-linted)
- `artifacts/trends.md` / `trends.json` — trends & controversy
- `artifacts/ideas.md` / `ideas.json` — 9 research proposals (grounded + novelty-checked)

## Honesty notes
- Items with no obtainable OA full text are NOT-READ and contribute no deep claims (shown above).
- Shadow-library sources excluded by design; OA coverage via arXiv/CORE/Unpaywall only.