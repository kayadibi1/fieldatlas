"""FieldAtlas dashboard (Streamlit). Run from the repo root:

   .venv/Scripts/streamlit run fieldatlas/ui.py

Read-only view over the SQLite corpus + artifacts/. Surfaces the reliability data
(verified vs. caught evidence spans, NOT-READ flags, citation accounting), the literature
map + citation graph, and the report / trends / ideas. Nothing leaves your machine.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "fieldatlas.sqlite"
ART = ROOT / "artifacts"

st.set_page_config(page_title="FieldAtlas", page_icon="🧭", layout="wide")


def _conn():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


@st.cache_data
def q(sql: str, params: tuple = ()):
    con = _conn()
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, params)]
    finally:
        con.close()


@st.cache_data
def load_json(name: str):
    p = ART / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


@st.cache_data
def load_text(name: str):
    p = ART / name
    return p.read_text(encoding="utf-8") if p.exists() else None


def scalar(sql, params=()):
    rows = q(sql, params)
    return list(rows[0].values())[0] if rows else 0


if not DB.exists():
    st.error("No corpus yet. Run `scripts/run_plane1.py` first.")
    st.stop()

st.sidebar.title("🧭 FieldAtlas")
if st.sidebar.button("↻ Reload data"):
    st.cache_data.clear()
    st.rerun()
page = st.sidebar.radio("View", ["Overview", "Corpus", "Map", "Report", "Trends", "Ideas"])
st.sidebar.caption(f"DB: {scalar('SELECT COUNT(*) FROM documents')} documents")


# ---------------------------------------------------------------- Overview
def overview():
    st.title("Overview — reliability accounting")
    runs = q("SELECT run_id, manifest_json FROM runs ORDER BY started_at DESC LIMIT 1")
    field = runs[0] if runs else None
    man = json.loads(field["manifest_json"]) if field else {}
    st.caption(f"Field: **{man.get('scope','?')}**  ·  run `{man.get('run_id','?')}`  ·  "
               f"sources: {man.get('sources_used','?')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documents", scalar("SELECT COUNT(*) FROM documents"))
    c2.metric("Deep-read (verified)", scalar("SELECT COUNT(*) FROM extractions WHERE verify_status IN ('verified','partial')"))
    c3.metric("Citation edges", scalar("SELECT COUNT(*) FROM citations"))
    c4.metric("Research ideas", scalar("SELECT COUNT(*) FROM ideas"))

    st.subheader("F3 — gathering")
    h = man.get("harvest", {})
    a, b, c = st.columns(3)
    a.metric("Raw records", h.get("raw_records", "—"))
    b.metric("Unique (after dedup)", scalar("SELECT COUNT(*) FROM documents"))
    c.metric("Corroborated ≥2 sources", h.get("multi_source_documents", "—"))

    st.subheader("F1 — reading (proof, not assertion)")
    sv = scalar("SELECT COUNT(*) FROM evidence_spans WHERE verified=1")
    sf = scalar("SELECT COUNT(*) FROM evidence_spans WHERE verified=0")
    nr = scalar("SELECT COUNT(*) FROM documents WHERE fulltext_status='metadata_only'")
    a, b, c = st.columns(3)
    a.metric("Evidence spans verified verbatim", sv)
    b.metric("Spans caught (paraphrase/unverifiable)", sf,
             help="These quotes did NOT match the source text and were dropped from citable evidence.")
    c.metric("NOT-READ (no legal full text)", nr)

    st.subheader("Read tiers")
    a, b, c = st.columns(3)
    a.metric("Tier 1 (deep-read)", scalar("SELECT COUNT(*) FROM documents WHERE read_tier=1"))
    b.metric("Tier 2", scalar("SELECT COUNT(*) FROM documents WHERE read_tier=2"))
    c.metric("Tier 3 (abstract map)", scalar("SELECT COUNT(*) FROM documents WHERE read_tier=3"))

    rr = load_text("RUN_REPORT.md")
    if rr:
        with st.expander("Full audit manifest (RUN_REPORT.md)"):
            st.markdown(rr)


# ---------------------------------------------------------------- Corpus
def corpus():
    st.title("Corpus browser")
    docs = q("SELECT canonical_id,title,year,venue,relevance,read_tier,fulltext_status,sources,is_fresh "
             "FROM documents ORDER BY relevance DESC")
    f1, f2, f3 = st.columns([2, 1, 1])
    term = f1.text_input("Search title").lower().strip()
    tiers = f2.multiselect("Read tier", [1, 2, 3], default=[1, 2, 3])
    minrel = f3.slider("Min relevance", 0.0, 1.0, 0.0, 0.01)
    only_read = st.checkbox("Only deep-read papers", value=False)

    rows = [d for d in docs
            if (not term or term in (d["title"] or "").lower())
            and d["read_tier"] in tiers
            and (d["relevance"] or 0) >= minrel
            and (not only_read or d["fulltext_status"] == "parsed")]
    st.caption(f"{len(rows)} of {len(docs)} documents")
    st.dataframe(
        [{"relevance": round(d["relevance"] or 0, 3), "tier": d["read_tier"],
          "year": d["year"], "full text": d["fulltext_status"],
          "title": d["title"], "venue": d["venue"]} for d in rows[:500]],
        use_container_width=True, height=320)

    st.subheader("Paper detail")
    read_docs = [d for d in rows if d["fulltext_status"] == "parsed"] or rows
    pick = st.selectbox("Select a paper", [d["canonical_id"] for d in read_docs],
                        format_func=lambda c: next((d["title"] for d in docs if d["canonical_id"] == c), c))
    if pick:
        _paper_detail(pick)


def _paper_detail(cid: str):
    d = q("SELECT * FROM documents WHERE canonical_id=?", (cid,))[0]
    st.markdown(f"### {d['title']}")
    ids = q("SELECT scheme,value FROM external_ids WHERE canonical_id=?", (cid,))
    st.caption(f"`{cid}`  ·  {d.get('year')}  ·  {d.get('venue')}  ·  "
               + "  ".join(f"{r['scheme']}:{r['value']}" for r in ids))
    if d["fulltext_status"] != "parsed":
        st.warning(f"Status: **{d['fulltext_status']}** — not deep-read "
                   "(no obtainable legal full text → contributes no deep claims).")
        if d.get("abstract"):
            st.write(d["abstract"])
        return

    ext = q("SELECT id,fields_json,verify_status,coverage_score FROM extractions "
            "WHERE canonical_id=? ORDER BY id DESC LIMIT 1", (cid,))
    if not ext:
        st.info("Full text parsed; not yet deep-read.")
        return
    f = json.loads(ext[0]["fields_json"])
    st.success(f"Deep-read · verification: **{ext[0]['verify_status']}** · coverage {ext[0]['coverage_score']}")
    if f.get("problem"):
        st.markdown(f"**Problem.** {f['problem']}")
    cols = st.columns(2)
    with cols[0]:
        if f.get("methods"):
            st.markdown("**Methods**"); st.write(f["methods"])
        if f.get("key_claims"):
            st.markdown("**Key claims**"); st.write(f["key_claims"])
    with cols[1]:
        if f.get("limitations"):
            st.markdown("**Limitations**"); st.write(f["limitations"])
        if f.get("topics"):
            st.markdown("**Topics**"); st.write(", ".join(f.get("topics", [])))

    spans = q("SELECT field,section,quote,verified FROM evidence_spans WHERE extraction_id=?", (ext[0]["id"],))
    st.markdown(f"**Evidence spans** — {sum(s['verified'] for s in spans)}/{len(spans)} verified verbatim "
                "(✗ = quote not found in source → dropped from citable evidence)")
    st.dataframe([{"✓": "✓" if s["verified"] else "✗", "field": s["field"],
                   "section": s["section"], "quote": s["quote"]} for s in spans],
                 use_container_width=True, height=260)


# ---------------------------------------------------------------- Map
def map_view():
    st.title("Literature map")
    m = load_json("map.json")
    if not m:
        st.info("No map yet. Run `scripts/build_map.py`.")
        return
    a, b, c = st.columns(3)
    a.metric("Mapped documents", m.get("n_documents"))
    b.metric("Verified deep-reads", m.get("n_verified_read"))
    c.metric("Citation edges", m.get("n_citation_edges"))

    st.subheader("Sub-areas (clusters)")
    for cl in m.get("clusters", []):
        with st.expander(f"**{cl['label']}** — {cl['size']} papers"):
            for mem in cl["members"][:15]:
                tag = "📖" if mem.get("verified_read") else "·"
                st.markdown(f"{tag} {mem['title']} ({mem.get('year')}) — rel={mem.get('relevance')}, "
                            f"cited×{mem.get('cited_in_corpus',0)}")

    mc = m.get("most_cited_in_corpus", [])
    if mc:
        st.subheader("Citation graph (most-cited nodes)")
        top = {r["canonical_id"] for r in mc[:12]}
        edges = q("SELECT citing_id,cited_id FROM citations")
        title = {d["canonical_id"]: (d["title"] or d["canonical_id"])[:38]
                 for d in q("SELECT canonical_id,title FROM documents")}
        dot = ["digraph G { rankdir=LR; node [shape=box,style=rounded,fontsize=9];"]
        shown = 0
        for e in edges:
            if e["cited_id"] in top and shown < 60:
                a_ = title.get(e["citing_id"], e["citing_id"])[:30].replace('"', "'")
                b_ = title.get(e["cited_id"], e["cited_id"])[:30].replace('"', "'")
                dot.append(f'"{a_}" -> "{b_}";'); shown += 1
        dot.append("}")
        if shown:
            st.graphviz_chart("\n".join(dot))
        else:
            st.caption("No citation edges among the most-cited nodes in this run.")


# ---------------------------------------------------------------- Report / Trends / Ideas
def report_view():
    st.title("State-of-the-field report")
    md = load_text("report.md")
    st.caption("Every [[id]] citation was linted against the corpus (F2 guard).")
    st.markdown(md or "_No report yet. Run the synth workflow + `build_outputs.py`._")


def trends_view():
    st.title("Trends & controversy")
    t = load_json("trends.json")
    if not t:
        st.info("No trends yet.")
        return
    st.subheader("Trends")
    for x in t.get("trends", []):
        st.markdown(f"**{x.get('topic')}** — {x.get('summary')}  "
                    + " ".join(f"`{c}`" for c in x.get("citations", [])))
    st.subheader("Contested / open debates")
    for x in t.get("controversies", []):
        st.markdown(f"**{x.get('topic')}** — {x.get('summary')}  "
                    + " ".join(f"`{c}`" for c in x.get("citations", [])))


def ideas_view():
    st.title("Research proposals")
    ideas = load_json("ideas.json")
    if not ideas:
        st.info("No ideas yet.")
        return
    titles = {d["canonical_id"]: d["title"] for d in q("SELECT canonical_id,title FROM documents")}
    for idea in sorted(ideas, key=lambda x: -(x.get("score") or 0)):
        head = f"{idea.get('title')}  ·  {idea.get('kind')}  ·  score {idea.get('score')}  ·  {idea.get('novelty_status')}"
        with st.expander(head):
            st.write(idea.get("description"))
            st.markdown("**Builds on:**")
            for c in idea.get("grounded_doc_ids", []):
                st.markdown(f"- `{c}` — {titles.get(c, '(not in corpus)')}")
            if idea.get("novelty_evidence"):
                st.caption(f"Novelty check: {idea.get('novelty_evidence')}")
            st.caption(f"Feasibility: {idea.get('feasibility','')}")
            if idea.get("dual_use_flag"):
                st.warning(f"⚠ Dual-use (flag-only): {idea.get('dual_use_note','')}")


{"Overview": overview, "Corpus": corpus, "Map": map_view,
 "Report": report_view, "Trends": trends_view, "Ideas": ideas_view}[page]()
