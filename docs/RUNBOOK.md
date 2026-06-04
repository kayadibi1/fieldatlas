# FieldAtlas — Runbook

How to run the pipeline again later. Steps marked **[you]** are PowerShell commands you run
yourself; steps marked **[Claude]** must be launched through Claude Code (they spawn the
reader/synthesis agent workflows). Easiest path: open Claude Code in this folder and say
**"run FieldAtlas again"** (fresh) or **"do a delta run"** (incremental) — it drives everything.

> All commands run from the repo root: `C:\Users\Sidar\Desktop\lit review`

---

## One-time setup (only if the machine/venv is gone)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
# .env must contain CORE_API_KEY, OPENALEX_API_KEY, CONTACT_EMAIL (already set).
# Optional: SEMANTIC_SCHOLAR_API_KEY (value), ELSEVIER_API_KEY/INSTTOKEN, WILEY_TDM_TOKEN.
```

---

## Full sequence

**1. [you] Harvest → rank → tier → acquire → parse.** Writes `work/deepread_queue.json`.
```powershell
.venv\Scripts\python scripts\run_plane1.py 100 30 openalex,crossref,core,greylit,federal_register
#                                          ^limit ^acquire ^sources
```

**2. [Claude] Deep-read the queued papers.** Ask: *"run the deep-read workflow on the queue."*
For the FULL Tier-1 core instead, first `[you]` run `python scripts\acquire_tier1.py 400`, then ask
Claude to deep-read the parsed set in batches of ~45. Parallel batches are fine for speed; if a
batch hits a transient **"Server is temporarily limiting requests (not your usage limit)"** overload,
just retry or resume that workflow (`resumeFromRunId` returns cached successes).

**3. [Claude→you] Verify + ingest.** Claude saves the workflow result to
`work/extractions_raw.json`; then:
```powershell
.venv\Scripts\python scripts\ingest_extractions.py     # deterministic span verification
```

**4. [you] Rebuild the map + synthesis inputs.**
```powershell
.venv\Scripts\python scripts\build_map.py
.venv\Scripts\python scripts\make_synth_args.py        # -> work/synth_args.json
```

**5. [Claude] Synthesis + idea engine.** Ask: *"run the synth workflow on work/synth_args.json."*
Claude saves its result to `work/plane2_outputs.json`.

**6. [you] Lint + assemble + reports.**
```powershell
.venv\Scripts\python scripts\build_outputs.py          # citation-lints report/trends/ideas
.venv\Scripts\python scripts\final_report.py           # artifacts/RUN_REPORT.md (audit)
.venv\Scripts\python scripts\build_html.py             # artifacts/report.html
```

---

## Delta / living-system run (cheap, incremental)

Just re-run step 1 — `run_plane1.py` upserts into the existing DB, re-ranks, and only the
**new** documents need deep-reading. Then deep-read only the new queue items (step 2),
ingest (3), and regenerate map/synthesis/reports (4–6). First run is the expensive one;
deltas are small.

---

## View the outputs

- **Markdown:** `artifacts\report.md`, `ideas.md`, `trends.md`, `map.md`, `RUN_REPORT.md`
- **HTML report:** open `artifacts\report.html` (self-contained; copy anywhere)
- **Dashboard:** `.venv\Scripts\streamlit run fieldatlas\ui.py`

---

## Tuning knobs (`scope\ai_safety_policy.yaml`)

| Knob | Effect |
|---|---|
| `harvest.per_query_limit` (CLI arg 1) | how many results per query per source — corpus size |
| `read_tiers.tier1_cap` | size of the deep-read core |
| CLI arg 2 (`max_acquire`) | how many papers to attempt full-text + deep-read this run |
| `queries` / `boundary` / `seed_corpus` | what counts as "in scope" (the highest-leverage setting) |
| sources CSV (CLI arg 3) | which connectors run |

## Add full text for a paywalled paper you obtained yourself
```powershell
.venv\Scripts\python scripts\add_manual_pdf.py doi:10.xxxx\yyyy "C:\path\to\paper.pdf"
```

## Gotchas
- **Deep-read** can run as parallel workflows for speed. Each workflow caps at 16 concurrent
  agents. If you hit a transient "Server is temporarily limiting requests (not your usage limit)"
  overload, retry/resume the affected workflow (or fall back to one-at-a-time).
- **arXiv** live query API is slow/rate-limits — left out of the default source list (OpenAlex covers preprints).
- **Semantic Scholar** keyless pool is throttled — add the key value to use it.
- **OpenAlex** is freemium ($1/day free); a full re-harvest is fine, heavy citation crawls aren't.
