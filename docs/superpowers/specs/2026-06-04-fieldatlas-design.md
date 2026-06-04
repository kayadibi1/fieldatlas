# FieldAtlas — Design Spec

**A robust, reliable, automated literature-review + research-ideation system for the AI-safety ∩ AI-policy field.**

- **Date:** 2026-06-04
- **Status:** Design — pending user review, then implementation plan(s)
- **Working name:** FieldAtlas (rename anytime)
- **Author:** drafted with Claude (Opus 4.8), connector catalog verified against live docs via a 13-agent + 5-agent retry research sweep on 2026-06-04

---

## 1. Purpose & goals

FieldAtlas continuously scans the literature of a target field — **here: the intersection of AI safety and AI policy** — builds a verified map of it, tracks trends and live controversies, and proposes grounded, novelty-checked research directions.

The user's five goals, verbatim intent:

1. **Scan all the literature** in the field, including preprints and grey literature.
2. **Map it out with awareness of the full context of each (read) paper.**
3. **Suggest new research:** past methods transplanted to new areas (and vice versa), cross-domain combinations, and original directions.
4. **Stay aware of current trends, contentious topics, and relevant discussions.**
5. (Implicit, and the spine of this design) **Be reliable** — fix three concrete past failures:
   - F1. The model *said it read something but hadn't*, and missed critical details.
   - F2. The model *fabricated references*.
   - F3. The model *couldn't gather all the relevant work* in a field.

### 1.1 The reliability thesis

All three failures share one root cause: **an LLM was trusted to do a job it cannot be trusted to do** — to exhaustively *gather*, to *cite* from memory, and to *attest* that it read. FieldAtlas removes those three jobs from the model and gives them to **deterministic, auditable machinery**. The model is left to do only what it is good at — reading comprehension, synthesis, and ideation — and only ever operates on inputs that have already been verified.

| Past failure | Root cause | Structural guardrail (see §4) |
|---|---|---|
| F1 — fake reading | No *proof* of reading | **Evidence-span verification** — every recorded claim carries a verbatim quote that is deterministically string-matched back into the retrieved full text; no match → rejected. Plus chunk-coverage accounting + an adversarial faithfulness check. |
| F2 — fabricated refs | Free-text citation generation | **Citation grounding + linter** — outputs may cite only by internal ID from the database; a linter rejects any unresolved ID and any claim lacking a supporting evidence span. No free-text citation ever reaches output. |
| F3 — incomplete gathering | LLM-driven "search" | **Deterministic multi-source harvest + recall accounting** — real scholarly APIs + grey-lit connectors, citation-snowball to convergence, cross-source gap detection. The model never decides what exists. |

### 1.2 What this system does and does **not** guarantee (honesty up front)

- **Strongly delivers:** F1, F2, F3 are structurally addressed (not "mitigated by a better prompt"); near-complete *gathering*; trend/controversy awareness.
- **Delivers for the core, partial for the long tail by design:** "full-paper context" is guaranteed for the deep-read tier (see §6's data-driven cap). Items below the cap are mapped at abstract level — a complete map, but not a full-text-deep one. This is a cost choice, surfaced in stats, and tunable per run.
- **Improves the odds, cannot manufacture genius:** the idea engine reliably produces *grounded, non-hallucinated, novelty-checked* suggestions and raises the hit-rate of useful ideas. It cannot guarantee a breakthrough. You supply the final judgment.
- **Honest gaps:** paywalled / DOI-less items whose full text can't be obtained are marked **NOT-READ** and structurally barred from contributing deep claims — visible in the manifest, never silently faked. Deep reads are lossy compressions (rich extractions, not raw papers); the idea engine re-opens source text for the specific papers it combines.
- **The single highest-leverage variable is the scope/relevance boundary** (§6), not the cap. A bad boundary deep-reads the wrong papers. Run-1 includes a calibration checkpoint.

---

## 2. Configuration decisions (locked)

| Decision | Choice |
|---|---|
| Build target | **Hybrid:** standalone Python + local SQLite data layer (deterministic, persistent) driven & analyzed by Claude Code agents/workflows. |
| Source coverage | **Maximal recall, tiered trust** — academic + safety-community + policy/governance + select discourse, each tagged with a credibility tier. |
| Cadence | **Living system** — persistent corpus, incremental delta runs, change-monitoring. |
| Outputs | All four: **(a) literature map/knowledge graph, (b) novel research proposals, (c) synthesis report, (d) trends & controversy briefing.** |
| Read depth | **3-tier** (§6.4): Tier 1 full deep-read+verify; Tier 2 full-text + key-claims; Tier 3 abstract-level map. |
| Deep-read cap | **Data-driven: relevance-threshold OR top-300, whichever comes first**, revisited at the scope gate with the real relevance histogram. Plus a **recency-protected fresh-preprint lane** (citation-blind, content-relevance only) so new work is never buried. |
| Execution model | **Keyless-local default.** Relevance ranking = free local embeddings; deep reads/synthesis/ideation = Claude Code agents (Sonnet/Opus). An Anthropic API key is documented as an **optional** accelerator (cheap Haiku first-pass) if the cap is ever raised into the thousands — off by default. |
| Idea engine model | **Strongest model (Opus), multi-agent, no cheap tier.** Only the deterministic scaffolding (retrieval for novelty check, citation linter) is non-Claude. |
| Idea safety | **Flag-only** — dual-use/info-hazard concerns noted beside each idea, never withheld. |
| Infra available | Python + local SQLite on Windows; **Semantic Scholar API key** (user has it); **Firecrawl** (already available in this environment); free-tier scholarly APIs. No Anthropic API key (not required by default). |

---

## 3. Architecture

Two planes with a single, file-and-DB interface between them.

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PLANE 1 — DETERMINISTIC DATA LAYER  (Python CLI, local, no LLM)          │
│                                                                          │
│  harvest ─▶ normalize+dedup ─▶ SQLite corpus ─▶ relevance-rank (embed)   │
│     │                                              │                     │
│  recall manifest                              scope gate (preview)       │
│     │                                              │                     │
│  full-text acquire (Unpaywall/arXiv/firecrawl) ─▶ parse (Docling/GROBID) │
│     │                                              │                     │
│  evidence-span VERIFIER (string match) ◀── ingest extractions            │
│  citation LINTER ◀── ingest artifacts                                    │
└───────────────────────────────▲───────────────────┬─────────────────────┘
                                 │  work/ queue       │  SQLite + JSON
                                 │  (markdown + JSON) │  (extractions, artifacts)
┌────────────────────────────────┴───────────────────▼─────────────────────┐
│ PLANE 2 — REASONING LAYER  (Claude Code agents / Workflow tool)           │
│                                                                          │
│  deep-read+extract (Sonnet/Opus) ─▶ adversarial faithfulness check       │
│  map/graph reasoning ─▶ synthesis report ─▶ trends/controversy           │
│  idea engine (Opus, multi-agent: generate→novelty→critique→rank)         │
└──────────────────────────────────────────────────────────────────────────┘
```

**Interface contract (the only coupling between planes):**
- Plane 1 writes a **work queue**: for each document to be read, a parsed-markdown file (`work/fulltext/<canonical_id>.md`) + an extraction-schema descriptor.
- Plane 2 (a Claude Code workflow) reads those, emits one **schema-validated extraction JSON** per document (`work/extractions/<canonical_id>.json`).
- Plane 1 **ingests + verifies** each extraction (evidence-span string match, coverage accounting), writes to SQLite, and re-queues failures.
- Same pattern for artifacts (report/ideas): Plane 2 emits, Plane 1 lints citations, rejects+re-queues on failure.

This separation is *why* the system is reliable: the verifier and linter are deterministic Python that the model cannot talk its way past, and they sit on the boundary every model output must cross.

**Why Python + SQLite + local embeddings (not a heavier stack):** at this field's scale (low tens of thousands of candidates, hundreds deep-read), a single SQLite file with FTS5 + a NumPy embedding matrix (brute-force cosine is trivially fast for <100k vectors) needs no server, no vector DB, runs entirely on the user's Windows machine, and gives a portable, inspectable, reproducible corpus. Reach for a real vector store only if the corpus later exceeds ~500k items.

---

## 4. The three reliability guarantees (detailed)

### G1 — No fabricated references (citation grounding + linter)

- **Citable = exists in `documents`.** Every citable entity is a row with ≥1 verified external ID (arXiv ID, DOI, OpenAlex ID, S2 paperId, DBLP key, or — for grey-lit — a fetched URL + content hash). IDs come from connectors, never from a model.
- **Outputs cite only by internal `canonical_id`.** Prompts give the model a *working set* of documents (with IDs); it may cite only from that set. It is never asked to "provide references."
- **Citation linter (deterministic, runs on every artifact):**
  1. Parse all citation markers `[[canonical_id]]`.
  2. Reject any ID not present in `documents`. *(catches invented refs)*
  3. For each *claim↔citation* pair, require ≥1 `evidence_span` on that document whose verbatim quote supports the claim (span must itself be verified, see G2). *(catches real-paper-wrong-claim)*
  4. Failure → artifact rejected with the offending markers, regenerated (bounded retries), then escalated to the manifest.

### G2 — No fake reading (proof-of-reading)

- **Structured extraction with mandatory evidence.** A deep read yields an `extraction` with required fields (problem, contributions, methods, claims, data/setup, results, limitations, relations to other corpus items). **Every non-trivial field carries `evidence_spans`:** `{quote (verbatim, ≤40 words), section, char_offset}`.
- **Verbatim verification (deterministic).** Python normalizes whitespace/hyphenation/ligatures on both sides and asserts each quote is a substring of the parsed full text. Non-matching quote → extraction **rejected**, re-queued (max 2 retries), then flagged NOT-VERIFIED in the manifest. *This is the core anti-F1 mechanism: a hallucinated read cannot produce quotes that exist in the text.*
- **Coverage accounting.** The full text is chunked (by section). The system records which chunks contributed ≥1 evidence span and computes a `coverage_score`. Documents where large/important sections produced nothing are flagged as possible skims for re-read.
- **Adversarial faithfulness check.** A second agent (distinct "skeptic" prompt) receives the extraction + full text and must surface misrepresentations, overclaims, or dropped limitations. Material disagreements re-queue the read.
- **NOT-READ honesty.** Documents with no obtainable full text get `fulltext_status = metadata_only` and are **structurally barred** from contributing deep claims to map/report/ideas (there is no full-text row to quote, so G1 step 3 can't pass for them). They appear in coverage stats. The model cannot pretend to have read what isn't there.

### G3 — Complete gathering (recall accounting)

- **Deterministic harvest** across all connectors (§5) — never LLM-driven.
- **Citation-snowball to convergence.** Seed set → expand backward (Crossref/OpenAlex/S2 references) and forward (OpenAlex `cites:` / S2 citations) → repeat until per-round new-unique yield drops below a threshold (default <2%). The convergence curve is logged.
- **Cross-source gap detection.** Core queries run across arXiv + OpenAlex + S2 + Crossref + DBLP; items found by some sources but missed by others are flagged as recall-risk signals and as connector-health signals.
- **Recall manifest.** Per-source counts, dedup/overlap stats, convergence curve, and the list of single-source items — so completeness is *visible as data*, not asserted.

---

## 5. Connector catalog (verified 2026-06-04)

All facts below were verified against live official docs/APIs. **Connectors are adapters behind a common interface** (`search`, `fetch_metadata`, `fetch_citations`, `fetch_fulltext_url`), each tagged with a **source tier** used to weight synthesis.

### 5.1 Academic backbone (recall + citation graph + metadata)

| Source | Role | Auth | Key constraints (verified) |
|---|---|---|---|
| **arXiv** | Primary preprint harvest | None | Query API: 3 s delay, ≤2000/page, 30000 cap. **Bulk/incremental via OAI-PMH** (base moved to `oaipmh.arxiv.org/oai`, Mar 2025; `arXivRaw` = full version history). Full-text bulk via **free GCS `gs://arxiv-dataset`** (S3 is requester-pays). Harvest sets `cs.AI, cs.CY, cs.LG, stat.ML` **+ all cross-lists**. No citations (join out). |
| **OpenAlex** | Recall + citation-graph backbone, dedup join key | Free key (`api_key=`) | **⚠ Now freemium (2026): $1/day free** (~10k list / ~1k search calls). `cited_by_api_url` **removed** → use `filter=cites:<id>` (forward) + `referenced_works` (backward). Abstracts = inverted index (reconstruct). For a full-field build prefer the **CC0 S3 snapshot** loaded locally; use live API for deltas. |
| **Semantic Scholar (S2AG)** | Citation graph + metadata + **precomputed SPECTER2 vectors** | User's key (`x-api-key`) | **⚠ Even with a key, default may be 1 RPS** (post-2024 redesign) — throttle + backoff. Use `/paper/search/bulk` (boolean over title+abstract) for assembly; relevance search capped at offset+limit ≤1000. Springer abstracts withheld. **Reuse `embedding.specter_v2`** to avoid re-embedding indexed papers. |
| **Crossref** | DOI authority, dedup (preprint→version-of-record), journal coverage arXiv misses, backward refs | None (send `mailto`) | Polite pool w/ `mailto=sidarvig@gmail.com` = 10 req/s, 3 concurrent (Dec 2025 change — read `x-rate-limit-*` headers, don't hardcode). `message.reference[]` only where publisher-deposited (partial); forward = count only. |
| **DBLP** | Venue completeness + author disambiguation | None | 1–2 s between calls; `h`≤1000/page; prefer XML dump for bulk. Clean CS-venue metadata (incl. FAccT/AIES); no abstracts/citations. |
| **Papers with Code** | Method↔code↔dataset↔benchmark enrichment | HF (optional token) | **⚠ Live API dead (sunset ~Jul 2025).** Use the **frozen `pwc-archive` HF dumps** (snapshot ~Jul 2025) as static enrichment; join on arXiv ID. |
| **OpenReview** | Peer-review discourse (reviews/rebuttals/decisions = contentious-topic signal) | None for public | Detect v1 (`api.openreview.net`) vs v2 (`api2.openreview.net`) per venue via `domain` field. ICLR/NeurIPS/ICML reviews largely public. **⚠ FAccT (only a nascent 2026 group, nothing public) and AIES (not on OpenReview) → get full text from ACM DL.** |

### 5.2 Open-access full text

| Source | Role | Auth | Notes |
|---|---|---|---|
| **Unpaywall** | DOI → legal OA PDF resolver | `email=` required | ≤100k/day. `is_oa=true` ≠ fetchable PDF (`url_for_pdf` can be null → fall back to landing page). Closed items → **NOT-READ**. Expect a meaningful NOT-READ tail from DOI-less grey lit. |
| arXiv / GCS | Preprint full text | None | Per-paper PDF/LaTeX or bulk GCS. |
| Firecrawl `scrape`/`parse` | HTML + non-OA grey-lit full text | Firecrawl key | See §5.4. |

### 5.3 Grey literature & policy (per-source adapters; prefer feed/API → sitemap → JS crawl)

Verified access surfaces:
- **WordPress REST + RSS + sitemap (easiest):** **CSET** (`/wp-json/wp/v2/posts`, `/document-sitemap.xml`), **AI Now**, **OECD.AI "wonk" pubs** (`wp.oecd.ai`).
- **Atom/sitemap (browser UA + throttle):** **RAND** (`/pubs/new.xml`; CloudFront 403s bot UAs; AI topic feed empty → use firehose + filter).
- **Sitemap-only (scrape landing pages):** **Brookings** (RSS disabled, REST locked → Yoast sitemap), **CNAS**, **NIST AIRC** (`airc.nist.gov/sitemap.xml`), **UK AISI** (also gov.uk org `.atom`).
- **Official legal APIs:** **EU AI Act** via EUR-Lex CELEX `32024R1689` (stable HTML/Formex XML + Cellar SPARQL).
- **No structured access → Firecrawl JS crawl:** **GovAI** (Webflow SPA; no feed/sitemap).
- **Safety-community discourse:** **LessWrong / Alignment Forum** GraphQL (`/graphql`; `af` flag isolates AF; full markdown bodies + karma + tags). **⚠ Vercel bot-challenge** on naive POSTs → descriptive User-Agent + `>=0.5s` cooldown, **GreaterWrong fallback** (email admin before bulk), and **reuse the maintained `StampyAI/alignment-research-dataset` (HF)** for backfill.

### 5.4 Firecrawl (web tooling layer)

Requires `FIRECRAWL_API_KEY`. Capabilities verified: `search` (web + full content, `--sources news`, `--tbs qdr:*` for recency, `--categories research,pdf`), `scrape` (JS-rendered → markdown; the WebFetch replacement), `crawl` / `map` (section enumeration), `parse` (local files → markdown; cloud upload), `interact` (clicks/forms/pagination/login), `agent` (structured-JSON multi-page extraction), **`monitor`** (server-side change detection with an AI judge + webhook/email — the living-system engine). Per-plan rate/credit budgets are real cost ceilings: scope crawls with `--include-paths`/`--limit`/`--max-credits`.

### 5.5 Added Tier-1 sources (from the completeness critic — high unique value)

These fill the gaps the academic APIs miss and are scheduled into the harvester as adapters:

- **Emerging Technology Observatory (ETO) / AGORA** (eto.tech) — AI-policy-curated science map + AI-law/standards database. Web tools (scrape; corpus not downloadable).
- **OECD.AI Policy Navigator + AI Incidents Monitor (AIM)** — 1,300+ national policy initiatives; live incident feed. Mostly web (verify export).
- **AI Incident Database (AIID)** — 750+ incidents, **public GraphQL + open export** (github.com/responsible-ai-collaborative/aiid).
- **Stanford HAI AI Index** — open datasets (CSV) for trend ground-truth.
- **Epoch AI** — compute/capability trends; **`pip install epochai`** (Airtable-backed).
- **Government registers (live policy):** **Federal Register API** (no key), **Congress.gov API** (free key), **GovInfo**, Regulations.gov dockets.
- **First-party lab safety blogs:** Anthropic (`alignment.anthropic.com`), DeepMind, OpenAI — Firecrawl + community RSS.
- **Independent evaluators:** **METR**, **Apollo Research** (reports often not on arXiv).
- **AISI / CAISI** — **naming corrected:** UK = **AI Security Institute** (`aisi.gov.uk`); US = **NIST CAISI** (Center for AI Standards & Innovation, `nist.gov/caisi`).
- **Newsletter discovery layer (recency + editorial signal):** Import AI, CAIS AI Safety Newsletter, ML Safety Newsletter, ChinAI — Substack RSS (`/feed`).
- **Other orgs:** IAPS, MIRI, Redwood, ARC, AI Impacts, FLI (+ `artificialintelligenceact.eu` tracker), GCRI, CAIS.
- **Incident redundancy:** AIAAIC.

**Source-tier tags** (drive synthesis weighting): `peer_reviewed`, `preprint`, `standards_gov` (NIST/EU/OECD), `think_tank` (CSET/RAND/GovAI/…), `lab_primary` (Anthropic/DeepMind/…/METR/Apollo), `community` (LW/AF), `discourse` (newsletters/news), `dataset_tracker` (Epoch/HAI/AIID).

---

## 6. Relevance, scope gate & read tiers

### 6.1 Relevance ranking (keyless, local)
- Embed each candidate's `title + abstract` once with **`BAAI/bge-small-en-v1.5`** (384-dim, CPU-fast; default) — prepend the BGE query instruction to the *query* side only, L2-normalize. **Higher-quality option:** `bge-base-en-v1.5` (768-dim, ~3× slower).
- **Reuse Semantic Scholar's precomputed `embedding.specter_v2`** for indexed papers; only locally embed what S2 lacks. **Never mix embedding spaces in one ranking pass.**
- Composite relevance = semantic similarity to the scope centroid/seed set **(primary)** + light deterministic signals (venue tier, keyword hits). **Citation count is a *secondary* signal only** — it must not gate new work.

### 6.2 Scope boundary (the highest-leverage component)
The `scope_config` (§12) defines the AI-safety ∩ AI-policy boundary as concrete include/exclude rules + a hand-picked **seed corpus** (seed papers, authors, venues). Run-1 has a **calibration checkpoint**: the user reviews the ranked boundary (a sample around the threshold) and tunes inclusion before any deep reading.

### 6.3 Fresh-preprint lane (recency protection)
Items published within a configurable window (default 60 days) are scored on **content relevance only** (citation-blind) and routed to a **separate guaranteed deep-read quota** (default up to 40), so brand-new highly-relevant work is never crowded out by established, heavily-cited papers.

### 6.4 Read tiers
- **Tier 1 — full deep-read + full verification (G2):** everything above the relevance threshold **OR top-300, whichever comes first** (revisited at the scope gate), **plus** the fresh lane.
- **Tier 2 — full-text retrieved + key-claims extraction (lighter verify):** the next relevance band — keeps the map honest well past 300 at low cost.
- **Tier 3 — abstract-level map:** the remainder. Complete coverage, no deep read.

### 6.5 Scope gate (hard, with preview)
After ranking, the system prints the **relevance histogram**, the projected Tier-1/2/3 counts, estimated reads, and the recall/convergence stats, then **waits for confirmation** (or an auto-threshold the user sets). If run-1's relevant core turns out far larger than 300, that's the signal to raise the cap, widen Tier 2, or enable the optional Anthropic-key Haiku first-pass — decided with real numbers, not guessed.

---

## 7. Data model (SQLite)

Core tables (abridged):

- **`documents`** — `canonical_id` (PK), `type`, `title`, `abstract`, `year`, `pub_date`, `venue`, `source_tier`, `oa_status`, `fulltext_status` (`none|metadata_only|fetched|parsed`), `relevance_score`, `read_tier`, `first_seen_run`, `last_seen_run`.
- **`external_ids`** — `canonical_id`, `scheme` (`arxiv|doi|openalex|s2|dblp|url`), `value` — the dedup keys (unique per scheme+value).
- **`authors`**, **`document_authors`**.
- **`citations`** — `citing_id`, `cited_id`, `source` (which connector), `intent` (where available). Deterministic, from APIs.
- **`fulltext`** — `canonical_id`, `format`, `parsed_md_path`, `sections` (JSON), `char_count`, `parse_tool`, `parse_status`, `content_hash`.
- **`extractions`** — `id`, `canonical_id`, `schema_version`, `fields` (JSON), `coverage_score`, `verify_status` (`pending|verified|rejected|not_verified`), `reader_model`, `run_id`.
- **`evidence_spans`** — `extraction_id`, `field`, `quote`, `section`, `char_offset`, `verified` (bool).
- **`graph_nodes`** / **`graph_edges`** — typed nodes (paper, method, claim, problem, position, author, org) + typed edges (`cites`, `extends`, `contradicts`, `applies_method_to`, `addresses_problem`, `proposes`, `evaluates`). Built from verified extractions + API citations.
- **`ideas`** — `id`, `kind` (`transplant|combination|original`), `title`, `description`, `grounded_doc_ids` (JSON), `novelty_status`, `novelty_evidence`, `feasibility`, `assumptions`, `dual_use_flag`, `dual_use_note`, `score`, `run_id`.
- **`runs`** — `run_id`, `started_at`, `watermark`, `manifest` (JSON), `scope_config_version`.
- **`harvest_log`** — `run_id`, `source`, `query`, `n_returned`, `n_new`, `round`.
- **`scope_config`** — versioned (see §12).
- **Embeddings** — a NumPy matrix file + `canonical_id` index (not in SQLite); one matrix per embedding model.

---

## 8. Pipeline stages

1. **Scope config** (versioned) → 2. **Harvest** (all connectors, query expansion, snowball-to-convergence, recall manifest) → 3. **Normalize + dedup** (canonical IDs via external-ID join) → 4. **Relevance rank** (local embeddings / S2 SPECTER2; two lanes) → 5. **Scope gate** (preview + confirm) → 6. **Full-text acquire** (Unpaywall/arXiv/GCS/Firecrawl) → 7. **Parse** (Docling primary; GROBID for references; PyMuPDF4LLM quick fallback) → 8. **Deep read + verify** (Plane 2 extract → Plane 1 evidence-span verify + coverage + adversarial check) → 9. **Map/graph build** → 10. **Synthesis report** (citation-linted) → 11. **Trends + controversy** → 12. **Idea engine** → 13. **Persist + delta** (watermark, changelog, Firecrawl monitors).

### 8.1 Parsing toolchain (verified)
- **Primary: Docling** (`pip install docling`, Windows-native, no Docker/Java) — section-structured markdown, uses the embedded PDF text layer so **verbatim text is faithful** (critical for evidence-span matching; OCR only for scanned pages).
- **References: GROBID** (Docker) — best-in-class parsed bibliography (~0.87–0.90 F1) for backward-citation harvesting where Crossref/S2 lack refs.
- **Quick fallback: PyMuPDF4LLM** (pure-Python) for born-digital PDFs.
- **Avoid as default:** `marker --use_llm`/forced-OCR (can paraphrase → breaks quote-matching); Firecrawl `/parse` (cloud upload — use only for HTML/occasional fallback).
- **Normalize** whitespace/hyphenation/ligatures before string-matching (handles multi-column reading-order + line-break hyphenation mismatches).

### 8.2 Deep-read orchestration (Plane 2)
A Claude Code **Workflow** pipelines Tier-1/2 documents (concurrency ≤16): each reader agent (Sonnet/Opus) reads `work/fulltext/<id>.md`, emits a schema-forced extraction JSON with evidence spans; a second agent runs the adversarial faithfulness pass. Plane 1 then verifies + ingests. Failures re-queue into the next workflow batch (bounded retries → NOT-VERIFIED).

---

## 9. Outputs

### 9.1 Literature map / knowledge graph
Clusters/sub-areas (embedding + citation co-clustering), methods, key claims, the citation network, open problems & gaps (nodes with no `addresses_problem` in-edges), and contested claims (nodes with `contradicts` edges). Exportable as JSON + a navigable summary.

### 9.2 Synthesis / survey report
Narrative state-of-the-field; **every sentence with a claim carries `[[canonical_id]]` citations**, all passed through the linter (G1). Sections weighted by source tier.

### 9.3 Trends & controversy briefing
- **Trends:** deterministic surge detection over publication/discussion volume by sub-topic and time (uses Epoch/HAI/OECD trackers as quantitative anchors).
- **Controversy:** position-mapping — who argues what, where positions conflict — built from `contradicts` edges + OpenReview review disagreement + incident-DB evidence. Each contested point links the opposing sources.

### 9.4 Novel research proposals (idea engine — §10).

---

## 10. Idea engine (Opus, multi-agent, grounded)

A Claude Code workflow, strongest model, no cheap tier:

1. **Generate** (3 parallel modes, each seeded with specific graph nodes):
   - **Method-transplant** — method node X (from paper/cluster A) → problem/domain node Y (cluster B).
   - **Cross-domain combination** — combine ≥2 methods/findings across clusters.
   - **Original / gap-filling** — target open-problem nodes with no current approach.
   Each candidate **must** name its `grounded_doc_ids` (the real papers/methods it builds on).
2. **Novelty check (adversarial)** — a skeptic agent searches the **corpus** (embeddings + FTS) *and* the **web** (Firecrawl `search`) to find prior work that already does it. If found → demote/kill or force a reframe. Records `novelty_status` + `novelty_evidence` (the prior-art it checked against).
3. **Critique** — feasibility, key assumptions, what would falsify it, resources required.
4. **Dual-use flag (flag-only)** — note info-hazard/dual-use considerations beside the idea; never withhold.
5. **Rank** — score = novelty × tractability × field-relevance × potential impact.

Output: ranked structured ideas; **every grounding citation is linted** (G1) — an idea cannot cite a paper that doesn't exist or make a claim about it without a verified evidence span.

---

## 11. Living system (delta runs)

- **Watermarks** per connector (arXiv OAI `from`, OpenAlex `from_publication_date`, S2 dates, RSS/sitemap `lastmod`, GraphQL `after`). Delta runs harvest only new-since-watermark.
- New items are ranked; those clearing the threshold (or in the fresh lane) are deep-read and merged; the map/report/ideas update with a **changelog** ("what's new, what changed, what's newly contested").
- **Firecrawl `monitor`** watches publication-index/changelog/regulatory pages for sources without clean feeds (GovAI, lab blogs, AISI/CAISI), with the AI judge filtering formatting noise → webhook/email triggers a delta run.
- First run is the expensive one; deltas are cheap.

---

## 12. Scope config (the control surface)

A versioned YAML/JSON, e.g.:

```yaml
field: "AI safety ∩ AI policy"
include_rules:
  must_match_any: ["alignment", "AI governance", "frontier model regulation",
                   "interpretability", "AI risk", "compute governance", "evals", ...]
  boundary_note: "Work must bear on BOTH technical safety AND its governance/policy dimension,
                  OR be a primary input to that intersection (e.g. an eval used in policy)."
exclude_rules: ["pure ML capability with no safety/policy framing", ...]
seed_corpus:
  papers: [arxiv:2212.08073, doi:10.1145/3442188.3445922, ...]
  authors: [...]
  venues: [NeurIPS, ICML, ICLR, FAccT, AIES, "GovAI reports", ...]
sources:
  academic: [arxiv, openalex, semantic_scholar, crossref, dblp, openreview, papers_with_code]
  grey_lit: [cset, govai, rand, brookings, cnas, ai_now, nist_caisi, eu_ai_act, oecd_ai, uk_aisi, eto, iaps, ...]
  community: [lesswrong_af, ...]
  discourse: [import_ai, cais_newsletter, ml_safety, chinai, ...]
  trackers: [epoch, hai_ai_index, aiid, oecd_aim, aiaaic]
  labs: [anthropic, deepmind, openai, metr, apollo, ...]
ranking:
  embedding_model: "BAAI/bge-small-en-v1.5"
  fresh_window_days: 60
read_tiers:
  tier1_threshold: auto        # relevance-threshold OR top-N
  tier1_cap: 300
  fresh_lane_quota: 40
  tier2_band: 700
limits:
  snowball_convergence_pct: 2.0
  semantic_scholar_rps: 1      # verify actual key tier
```

---

## 13. Error handling & failure modes

- **Rate limits / 429:** per-connector token-bucket sized to *verified* limits (§5); read `x-rate-limit-*` (Crossref) / `X-RateLimit-*` (OpenAlex) headers; exponential backoff; respect arXiv's 3 s and S2's 1 RPS.
- **OpenAlex freemium budget:** track `meta.cost_usd`; for full-field builds use the **CC0 S3 snapshot locally**, live API for deltas only.
- **Parse failure:** Docling → GROBID → PyMuPDF4LLM cascade; persistent failure → `parse_status=failed`, item degrades to metadata_only.
- **Full text unobtainable (paywall / DOI-less):** `metadata_only` → NOT-READ, visible in manifest.
- **Bot challenges (RAND CloudFront, LW Vercel):** descriptive User-Agent, throttle, documented fallbacks (GreaterWrong, StampyAI dataset).
- **Schema drift (OpenAlex/S2 churn, LW undocumented API):** pin to OpenAPI specs; nightly health-check probes; alert on field disappearance.
- **Extraction verify failure:** re-queue (≤2) → NOT-VERIFIED (excluded from outputs, surfaced).
- **Citation lint failure:** regenerate artifact (bounded) → escalate.
- **Idea novelty false-negative risk:** adversarial check + web search reduce but don't eliminate; ideas carry their novelty_evidence so the user can judge.

---

## 14. Testing & verification strategy (testing the reliability machine itself)

- **Golden recall set:** a hand-curated list of N known-key AI-safety∩policy papers; assert harvest finds ≥95%. *(tests F3)*
- **Citation-linter unit tests:** artifacts with invented IDs and real-ID-wrong-claim → assert rejection; valid → pass. *(tests F2)*
- **Evidence-span verifier tests:** extractions with fabricated quotes → reject; verbatim quotes → pass; near-miss (hyphenation/whitespace) → pass after normalization. *(tests F1)*
- **Coverage-accounting test:** a doc with a deliberately-skipped section → low coverage flag.
- **Dedup test:** same paper from arXiv+OpenAlex+Crossref+S2 → one `canonical_id`.
- **Parse-fidelity test:** known PDF → section headers recovered + sampled quotes verbatim-matchable.
- **Adversarial-check test:** an extraction with a planted overclaim → flagged.
- **Idea-novelty test:** feed an idea that is actually an existing paper → novelty checker catches it.
- **Reproducibility:** same `scope_config` + frozen snapshot → identical corpus + manifest.

Adopt the repo's prevailing test style; these are the acceptance criteria the implementation must satisfy.

---

## 15. Build phases (decomposition → separate implementation plans)

This spec is the master design; it is **too large for one implementation plan**. Build in independently-testable phases, each its own plan:

- **Phase 0 — Scaffolding:** repo, config loader, SQLite schema, run manifest, connector interface.
- **Phase 1 — Deterministic data layer** *(recommended first plan)*: academic connectors (arXiv, OpenAlex, S2, Crossref, DBLP) → normalize/dedup → snowball + recall manifest. Acceptance: golden-recall test passes; dedup test passes. **This alone solves F3 and is fully testable without any LLM.**
- **Phase 2 — Relevance + scope gate:** embeddings (+ S2 SPECTER2 reuse), two-lane ranking, 3-tier assignment, scope-gate preview.
- **Phase 3 — Full-text acquisition + parsing:** Unpaywall/arXiv/GCS/Firecrawl + Docling/GROBID; `fulltext_status`.
- **Phase 4 — Deep read + verification** *(the reliability core)*: reader workflow + evidence-span verifier + coverage + adversarial check. Solves F1.
- **Phase 5 — Map/graph + synthesis + citation linter:** solves F2 at output time.
- **Phase 6 — Trends & controversy.**
- **Phase 7 — Idea engine.**
- **Phase 8 — Living system:** watermarks, delta runs, Firecrawl monitors.
- **Grey-lit & added-source adapters** (§5.3, §5.5) land incrementally across Phases 1/3 (academic first, then think-tank/gov/discourse).

---

## 16. Open questions / risks

1. **OpenAlex freemium economics** — confirm whether the $1/day free tier suffices for delta runs, or commit to the local snapshot early. (Snapshot is ~330 GB compressed — disk check on the Windows machine.)
2. **S2 key tier** — verify the user's actual RPS (1 vs 10); it bounds harvest throughput.
3. **GROBID dependency** — requires Docker Desktop on Windows. Acceptable, or restrict to Docling-only and accept weaker reference extraction?
4. **Firecrawl credits** — grey-lit crawls + monitors consume credits; confirm plan/budget.
5. **Idea-engine evaluation** — how to measure "useful idea" hit-rate over time (a feedback loop where the user rates ideas would calibrate the ranker).
6. **Anthropic key** — keep off unless/until the cap is raised past ~1000 deep reads.

---

## 17. Glossary

- **canonical_id** — FieldAtlas's internal stable ID after cross-source dedup.
- **evidence span** — a verbatim quote + location proving an extracted claim is grounded in the source text.
- **NOT-READ / metadata_only** — a document whose full text couldn't be obtained; barred from contributing deep claims.
- **read tier** — Tier 1 (full deep-read+verify), Tier 2 (full-text+key-claims), Tier 3 (abstract map).
- **source tier** — credibility tag used to weight synthesis.
- **fresh lane** — recency-protected, citation-blind deep-read quota for new preprints.
