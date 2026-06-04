"""Render a single self-contained HTML report from the artifacts + corpus.

Output: artifacts/report.html (no server, no external assets, no JS deps). Sections:
Overview (reliability accounting) · Report · Trends · Ideas · Map · Audit.
Citation markers [[id]] become clickable chips (DOI/arXiv/OpenAlex) with title tooltips.
"""
import html
import json
import re
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, ".")
import markdown as md

from fieldatlas.config import ARTIFACTS_DIR, DB_PATH

con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
TITLE = {r["canonical_id"]: r["title"] for r in con.execute("SELECT canonical_id,title FROM documents")}


def q1(sql):
    return con.execute(sql).fetchone()[0]


def resolve(cid: str):
    """Return (display, href) for a canonical_id citation."""
    if cid.startswith("doi:"):
        return cid.split("/")[-1], "https://doi.org/" + cid[4:]
    if cid.startswith("arxiv:"):
        x = cid[6:]
        return x, "https://arxiv.org/abs/" + x
    if cid.startswith("openalex:"):
        x = cid[9:]
        return x, "https://openalex.org/" + x
    return cid.split(":")[-1][:12], None


def chip(cid: str) -> str:
    disp, href = resolve(cid)
    t = TITLE.get(cid, "")
    tip = html.escape((t + "  ·  " if t else "") + cid, quote=True)
    inner = html.escape(disp)
    if href and href.startswith(("https://", "http://")):   # escape + scheme-validate (no javascript:)
        return (f'<a class="cite" href="{html.escape(href, quote=True)}" target="_blank" '
                f'rel="noopener noreferrer" title="{tip}">{inner}</a>')
    return f'<span class="cite" title="{tip}">{inner}</span>'


_CITE = re.compile(r"\[\[([^\]\[]+)\]\]")


def linkify(html_str: str) -> str:
    return _CITE.sub(lambda m: chip(m.group(1).strip()), html_str)


def md2html(text: str) -> str:
    # neutralize raw HTML in model/corpus-generated markdown (no <script> etc. survives);
    # markdown syntax (#, *, |, [[id]]) is unaffected. linkify then injects our own chips.
    safe = (text or "").replace("<", "&lt;").replace(">", "&gt;")
    return linkify(md.markdown(safe, extensions=["tables", "fenced_code", "sane_lists"]))


# ---- gather data
load = lambda n: (ARTIFACTS_DIR / n).read_text(encoding="utf-8") if (ARTIFACTS_DIR / n).exists() else ""


def loadj(n):
    try:
        s = load(n)
        return json.loads(s) if s else None
    except json.JSONDecodeError:
        return None   # degrade to a partial report rather than crashing
report_md = load("report.md")
runrep_md = load("RUN_REPORT.md")
trends = loadj("trends.json") or {"trends": [], "controversies": []}
ideas = loadj("ideas.json") or []
if isinstance(ideas, dict):
    ideas = ideas.get("ideas", [])
if not isinstance(ideas, list):
    ideas = []
mp = loadj("map.json") or {}

stats = {
    "documents": q1("SELECT COUNT(*) FROM documents"),
    "deepread": q1("SELECT COUNT(DISTINCT canonical_id) FROM extractions WHERE verify_status IN ('verified','partial')"),
    "spans_ok": q1("SELECT COUNT(*) FROM evidence_spans WHERE verified=1"),
    "spans_caught": q1("SELECT COUNT(*) FROM evidence_spans WHERE verified=0"),
    "edges": q1("SELECT COUNT(*) FROM citations"),
    "notread": q1("SELECT COUNT(*) FROM documents WHERE fulltext_status='metadata_only'"),
    "ideas": len(ideas),   # this run's rendered ideas (matches the cards), not all-time table count
}
run = con.execute("SELECT run_id, manifest_json FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()
manifest = json.loads(run["manifest_json"]) if run else {}


def metric(label, value, sub=""):
    return f'<div class="m"><div class="mv">{value}</div><div class="ml">{html.escape(label)}</div>{f"<div class=ms>{sub}</div>" if sub else ""}</div>'


# ---- sections
overview = '<div class="cards">' + "".join([
    metric("documents gathered", f'{stats["documents"]:,}'),
    metric("deep-read & verified", stats["deepread"]),
    metric("evidence spans verbatim", f'{stats["spans_ok"]:,}', f'{stats["spans_caught"]} caught & dropped'),
    metric("citation edges", stats["edges"]),
    metric("NOT-READ (no legal OA)", stats["notread"]),
    metric("research proposals", stats["ideas"]),
]) + "</div>"

trend_html = "".join(
    f'<div class="trend"><b>{html.escape(t.get("topic",""))}</b> — {html.escape(t.get("summary",""))} '
    + " ".join(chip(c) for c in t.get("citations", [])) + "</div>"
    for t in trends.get("trends", []))
contro_html = "".join(
    f'<div class="trend contro"><b>{html.escape(c.get("topic",""))}</b> — {html.escape(c.get("summary",""))} '
    + " ".join(chip(x) for x in c.get("citations", [])) + "</div>"
    for c in trends.get("controversies", []))

idea_html = ""
for i, idea in enumerate(sorted(ideas, key=lambda x: -(x.get("score") or 0)), 1):
    nov = (idea.get("novelty_status") or "").lower()
    novcls = "ok" if "novel" in nov and "exist" not in nov else ("warn" if "incremental" in nov else "bad")
    grounds = " ".join(chip(c) for c in idea.get("grounded_doc_ids", []))
    dual = (f'<div class="dual">⚠ Dual-use (flag-only): {html.escape(idea.get("dual_use_note","") or "")}</div>'
            if idea.get("dual_use_flag") else "")
    idea_html += f'''<details class="idea"><summary><span class="rank">{i}</span>
      <span class="ititle">{html.escape(idea.get("title",""))}</span>
      <span class="badge">{html.escape(idea.get("kind",""))}</span>
      <span class="badge {novcls}">{html.escape(idea.get("novelty_status",""))}</span>
      <span class="score">{idea.get("score","")}</span></summary>
      <p>{html.escape(idea.get("description","") or "")}</p>
      <div class="meta"><b>Builds on:</b> {grounds}</div>
      <div class="meta"><b>Novelty:</b> {html.escape(idea.get("novelty_evidence","") or "")}</div>
      <div class="meta"><b>Feasibility:</b> {html.escape(idea.get("feasibility","") or "")}</div>
      <div class="meta"><b>Assumptions:</b> {html.escape(idea.get("assumptions","") or "")}</div>{dual}</details>'''

map_html = ""
for cl in mp.get("clusters", []):
    members = "".join(
        f'<li>{"📖 " if m.get("verified_read") else ""}{html.escape(m.get("title") or "")} '
        f'<span class=muted>({m.get("year")}, rel {m.get("relevance")}, cited×{m.get("cited_in_corpus",0)})</span> '
        + chip(m["canonical_id"]) + "</li>"
        for m in cl.get("members", [])[:12])
    map_html += (f'<details class="cluster"><summary><b>{html.escape(cl.get("label",""))}</b> '
                 f'<span class=muted>· {cl.get("size")} papers</span></summary><ul>{members}</ul></details>')

gen = datetime.now().strftime("%Y-%m-%d %H:%M")
CSS = """
:root{--bg:#0f1419;--panel:#1a212b;--ink:#e6edf3;--mut:#8b98a8;--acc:#4ea1ff;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--line:#2a3441}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--acc)}header{padding:28px 40px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:10}
h1{margin:0;font-size:22px}.sub{color:var(--mut);font-size:13px;margin-top:4px}
nav{display:flex;gap:18px;margin-top:14px;flex-wrap:wrap}nav a{text-decoration:none;color:var(--mut);font-size:14px;font-weight:600}nav a:hover{color:var(--ink)}
main{max-width:980px;margin:0 auto;padding:32px 40px 120px}
section{margin:40px 0;scroll-margin-top:120px}h2{border-bottom:1px solid var(--line);padding-bottom:8px;font-size:20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}
.m{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px}
.mv{font-size:28px;font-weight:700}.ml{color:var(--mut);font-size:13px;margin-top:2px}.ms{color:var(--warn);font-size:11px;margin-top:4px}
.prose{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px 28px}
.prose table{border-collapse:collapse;width:100%;margin:14px 0}.prose th,.prose td{border:1px solid var(--line);padding:6px 10px;text-align:left;font-size:14px}
.prose code{background:#0b0f14;padding:2px 5px;border-radius:4px;font-size:13px}
.cite{display:inline-block;background:#15324f;color:#9cd0ff;border-radius:5px;padding:0 5px;margin:0 1px;font-size:11px;text-decoration:none;vertical-align:1px}
.cite:hover{background:#1d4a78}
.trend{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:8px;padding:12px 16px;margin:10px 0}
.trend.contro{border-left-color:var(--warn)}
.idea{background:var(--panel);border:1px solid var(--line);border-radius:10px;margin:12px 0;padding:4px 18px}
.idea summary{cursor:pointer;padding:12px 0;font-weight:600;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.rank{background:var(--acc);color:#001;border-radius:50%;width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;font-size:13px;flex:none}
.ititle{flex:1;min-width:220px}.score{color:var(--mut);font-variant-numeric:tabular-nums}
.badge{background:#243041;color:var(--mut);border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600}
.badge.ok{background:#14331f;color:var(--ok)}.badge.warn{background:#33280c;color:var(--warn)}.badge.bad{background:#3a1418;color:var(--bad)}
.idea .meta{font-size:14px;color:var(--mut);margin:6px 0}.idea .meta b{color:var(--ink)}
.dual{background:#33280c;border-radius:6px;padding:8px 12px;color:var(--warn);font-size:13px;margin-top:8px}
.cluster{background:var(--panel);border:1px solid var(--line);border-radius:8px;margin:8px 0;padding:4px 16px}
.cluster summary{cursor:pointer;padding:10px 0}.cluster ul{margin:0 0 10px;padding-left:20px}.cluster li{font-size:14px;margin:4px 0}
.muted{color:var(--mut);font-size:12px}
"""

HTML = f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>FieldAtlas — {html.escape(manifest.get('scope','report'))}</title><style>{CSS}</style></head><body>
<header><h1>🧭 FieldAtlas — {html.escape(manifest.get('scope','AI safety ∩ AI policy'))}</h1>
<div class=sub>run {html.escape(manifest.get('run_id',''))} · generated {gen} · {stats['deepread']} papers deep-read & claim-verified ·
every citation linted against the corpus</div>
<nav><a href="#overview">Overview</a><a href="#report">Report</a><a href="#trends">Trends</a>
<a href="#ideas">Ideas</a><a href="#map">Map</a><a href="#audit">Audit</a></nav></header>
<main>
<section id=overview><h2>Overview</h2>{overview}</section>
<section id=report><h2>State of the field</h2><div class=prose>{md2html(report_md)}</div></section>
<section id=trends><h2>Trends &amp; controversy</h2><h3>Trends</h3>{trend_html}<h3>Contested / open debates</h3>{contro_html}</section>
<section id=ideas><h2>Research proposals <span class=muted>({len(ideas)} grounded &amp; novelty-checked)</span></h2>{idea_html}</section>
<section id=map><h2>Literature map <span class=muted>· {mp.get('n_documents','?')} docs, {mp.get('n_verified_read','?')} deep-read, {mp.get('n_citation_edges','?')} citation edges</span></h2>{map_html}</section>
<section id=audit><h2>Audit manifest</h2><div class=prose>{md2html(runrep_md)}</div></section>
</main></body></html>"""

out = ARTIFACTS_DIR / "report.html"
out.write_text(HTML, encoding="utf-8")
print(f"wrote {out} ({len(HTML):,} bytes)")
