# FieldAtlas — Validation & Pressure-Testing Record

A record of how FieldAtlas was adversarially tested, what was found, and what was fixed.
Companion to the design spec (`docs/superpowers/specs/2026-06-04-fieldatlas-design.md`) and
the runbook (`docs/RUNBOOK.md`).

---

## Context

FieldAtlas is a reliability-first automated literature-review + research-ideation system for
the AI-safety ∩ AI-policy field. Its thesis: the three classic LLM-research failures are
removed from the model and given to deterministic, auditable machinery —

- **F1 fake reading** → evidence-span verifier (every recorded claim carries a verbatim quote
  string-matched back into the parsed full text).
- **F2 fabricated references** → citation linter (outputs may cite only `[[canonical_id]]`s
  that resolve in the corpus; grounded claims need a verified span).
- **F3 incomplete gathering** → multi-source harvest + dedup + recall accounting.

The verifier and linter sit on the boundary every model output must cross. Pressure-testing
asked: do those guarantees actually hold, and where is the system weak?

---

## Methodology

Two adversarial patterns, both run as multi-agent **workflows** (reusable harnesses live in
`fieldatlas/workflows/` and the session workflow scripts):

1. **Dimension audits** — parallel agents, each owning one failure dimension, probe the code +
   the real corpus/outputs **read-only** (pure-function tests, temp-DB copies, live DB queries,
   web search). High-severity findings then pass an **adversarial verify** stage (reproduce-or-
   refute) to filter false positives before anything is trusted or fixed.
2. **Ground-truth validation** (`fieldatlas/workflows/validate.workflow.js`) — a fresh expert
   reader deep-reads each sampled paper's full text **blind to the system**, then an auditor
   compares the system's stored extraction + report claims against that independent reading.

Safety rules for every audit: never write to `data/`/`work/`/`artifacts/`, never run the
pipeline or re-harvest, never commit — read-only inspection + safe probes only.

---

## Rounds & findings

### Round 1 — Code robustness (44 findings; 16 high/critical verified)
Crashes, idempotency, error handling, encoding, security. **All fixed.**
- **Cross-field (critical):** scope path was hardcoded → `$FIELDATLAS_SCOPE`/`$FIELDATLAS_DB`
  env plumbing; connectors/prompts made scope-driven.
- **Idempotency:** `ingest`/`build_outputs` were duplicating rows on re-run → replace-per-paper /
  per-run (proven: ideas 27→18 on idempotent re-run).
- **Crash guards** (empty corpus, 1-doc map), **HTTP** (stopped retrying non-retryable 4xx),
  **HTML report XSS** (escaped + scheme-validated hrefs; neutralized raw HTML), plus all
  mediums/lows (robust JSON loading, dedup of unusable records, lazy OA recovery, cache magic
  bytes, deterministic tiebreaks, harvest-error surfacing).

### Round 2 — Literature depth (51 findings; the corpus was query-only)
The spec's core recall mechanism — **citation snowballing** — was never implemented. **Fixed.**
- `snowball.py`: seed-fetch (canon anchors, date-exempt) + bounded backward (`referenced_works`)
  + forward (`cites:`) expansion to convergence; convergence curve in the manifest.
- Synthesis depth: `make_synth_args` now forwards the **full** extraction + a citation-graph
  block (was passing a thin subset); report prompt authorizes the deep `verified_corpus`.
- Extraction schema gained typed `relations` + quantitative `metrics`; citation-centrality
  tiering force-reads the most-cited anchors; authors surfaced in the map.
- **Measured on the real corpus (before → after a depth-enhanced run):** documents 2,977 →
  5,310; citation edges 791 → 14,330; earliest work 2018 → 1911 (2,012 pre-2018 docs);
  citation-isolated 83% → 45%.

### Round 3 — Output faithfulness & ranking precision (36 findings)
- **Faithfulness: SOUND.** 23/36 findings were "sound" — agents re-read sources and confirmed
  specific synthesis claims verbatim/accurate (safetywashing stats, the 250-poisoned-documents
  result, AGORA figures, eval-coverage numbers, keyword counts). No fabrication/misrepresentation.
- **Ranking (fixed):** the 0.55 threshold sat in noise and the embedder confused "AI safety as a
  field" with "AI applied to a safety-named domain." Fix: wire the (dead) `exclude` rules in as a
  **semantic penalty** (`relevance = sim(doc,scope) − w·sim(doc,exclude)`); verified to drop an
  application paper 0.67 → 0.38 below cutoff. Threshold raised to 0.6.

### Round 4 — Ops / living-system
- **Delta/incremental harvest** implemented (was a dead feature: each run re-harvested fully).
  `run_plane1(delta=True)` / `$FIELDATLAS_DELTA` sets `since_date` from the last run; connectors
  honor it.
- **Connector health-check** (`scripts/health_check.py`) detects silent API breakage — correctly
  WARNs the flaky arXiv query API and the inactive S2 key.
- Scale: SQLite + brute-force cosine fine to ~50k docs; the binding limit is OpenAlex's $1/day
  freemium budget (use the offline snapshot for very large builds).

### Round 5 — Empirical cross-field generalization
Ran a completely different field — **CRISPR / gene-editing governance** — in its own DB.
- Corpus 4,609 docs, 15,487 edges, earliest work **1959** (snowball breached the 2012 cutoff
  domain-agnostically).
- **Ranking generalized first try:** top-12 by relevance are all genuine gene-editing-governance
  papers; off-field CS/ML papers the snowball pulled in as citation neighbours were correctly
  demoted to the floor (~0.41). No AI-specific assumptions leaked into ranking.

### Round 6 — Ground-truth validation (the strongest test)
Independent expert re-read of a **wide 15-paper sample** (foundational primers, frontier
governance, evaluation, alignment, policy/legal, critical/meta, a dataset paper; 2021–2026;
arXiv/journals/CSET/conf), blind to the system.
- **Extractions: 15/15 faithful.** Zero misrepresentations, zero fabrications, zero material
  errors. Report claims faithful wherever cited (0 overclaims/wrong-attributions).
- Overall: 5 system-correct / 10 minor-gaps / **0 material-error**. Severity: 0 high, 5 medium,
  52 low.
- **Single consistent weakness = thinness, not error:** the system captures a paper's core
  structure and claims faithfully but drops the long tail — specific *numbers* and complete
  *enumerations* (e.g. a paper's "five hallmarks", a secondary contrast case).

**Fix — the omission guard (completeness critic).** The verifier guards *fabrication* (F1) but
nothing guarded *omission*. Added a third deep-read stage (read → **completeness** → adversarial):
a critic re-reads the full text and recovers relevant missed specifics, EACH with a verbatim span,
merged into the extraction — so the additions pass the same deterministic verifier (completeness
up, F1 intact). **Proven on the 3 papers the validation flagged:** regulatory-capture claims
8→31 / metrics 0→12 / verified spans 26→56 (five hallmarks + Bootleggers-and-Baptists recovered;
non-verbatim quotes correctly dropped); Concrete-Problems-Revisited 8→21 (IBM-Watson success case);
Frontier-what-form 8→46 (full adversarial-threat taxonomy). The existing 144 extractions predate
this stage and would gain it on a re-read.

---

## Net outcome

| Guarantee / property | Status under testing |
|---|---|
| F1 no fake reading | held (verifier attacked + ground-truth-validated; 15/15 reads faithful) |
| F2 no fabricated refs | held (linter attacked; report citations re-verified) |
| F3 gathering completeness | **was weak (query-only) → fixed** (snowball: edges 18×, canon + prehistory pulled in) |
| Synthesis faithfulness | held (sound vs sources on independent re-read) |
| Ranking precision | **was weak → fixed** (semantic exclusion; verified cross-domain) |
| Extraction completeness | **faithful but thin on specifics → improved** (metrics/enumeration prompt) |
| Cross-field generalization | works (CRISPR, first try) |
| Robustness / ops | hardened (idempotency, crashes, encoding, XSS, delta, health-check) |

**Residual / inherent limits** (documented, not bugs): document-level (not per-claim) citation
grounding; grey-lit read at excerpt level (bodies not fetched); novelty checks can miss the
closest prior art; the S2 key is inactive (403); idea quality raises the hit-rate but cannot
guarantee a breakthrough.

---

## Re-running the audits

The audit harnesses are reusable workflows (launch via the Workflow tool, read-only):
- `fieldatlas/workflows/validate.workflow.js` — ground-truth validation over a paper sample.
- The dimension-audit scripts persist under the session `workflows/scripts/` directory
  (stress-test, depth-audit, faithfulness-audit) and can be re-invoked by `scriptPath`.
- `scripts/health_check.py` — quick connector/key liveness check.
