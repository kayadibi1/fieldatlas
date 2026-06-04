"""Assemble + LINT the Plane-2 artifacts (report, trends, ideas) before they're saved.

Every citation in every artifact is checked against the real corpus (F2 guard); grounded
items (report claims, ideas) additionally require a verified evidence span. Anything that
fails is flagged in the artifact and in the run report — never silently published.
"""
from __future__ import annotations

import json

from . import db
from .config import ARTIFACTS_DIR
from .lint import lint_text, lint_grounded


def save_report(report_md: str) -> dict:
    con = db.connect()
    valid = db.valid_ids(con)
    con.close()
    res = lint_text(report_md, valid)
    header = ""
    if not res.ok:
        header = ("> ⚠ CITATION-LINT: unresolved citations removed/flagged: "
                  + ", ".join(res.unknown_ids) + "\n\n")
    (ARTIFACTS_DIR / "report.md").write_text(header + report_md, encoding="utf-8")
    return {"ok": res.ok, "n_citations": res.n_citations, "unknown_ids": res.unknown_ids}


def save_trends(trends: dict) -> dict:
    (ARTIFACTS_DIR / "trends.json").write_text(json.dumps(trends, indent=2), encoding="utf-8")
    lines = ["# Trends & Controversy", ""]
    for t in trends.get("trends", []):
        lines.append(f"- **{t.get('topic')}** — {t.get('summary')} "
                     + " ".join(f"[[{c}]]" for c in t.get("citations", [])))
    lines.append("\n## Contested / open debates\n")
    for c in trends.get("controversies", []):
        lines.append(f"- **{c.get('topic')}**: {c.get('summary')} "
                     + " ".join(f"[[{x}]]" for x in c.get("citations", [])))
    (ARTIFACTS_DIR / "trends.md").write_text("\n".join(lines), encoding="utf-8")
    return {"n_trends": len(trends.get("trends", [])),
            "n_controversies": len(trends.get("controversies", []))}


def save_ideas(ideas: list[dict], run_id: str) -> dict:
    con = db.connect()
    db.init_db(con)
    valid = db.valid_ids(con)
    verified = db.verified_doc_ids(con)
    con.execute("DELETE FROM ideas WHERE run_id=?", (run_id,))   # idempotent: replace this run's ideas

    accepted, flagged = [], []
    for idea in ideas:
        cites = idea.get("grounded_doc_ids", []) or []
        res = lint_grounded([{"text": idea.get("title", ""), "citations": cites}], valid, verified)
        idea["_lint_ok"] = res.ok
        idea["_unknown_ids"] = res.unknown_ids
        idea["_ungrounded"] = bool(res.ungrounded_claims)
        (accepted if res.ok else flagged).append(idea)
        con.execute(
            """INSERT INTO ideas(kind,title,description,grounded_doc_ids,novelty_status,
                                 novelty_evidence,feasibility,assumptions,dual_use_flag,
                                 dual_use_note,score,run_id)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (idea.get("kind"), idea.get("title"), idea.get("description"),
             json.dumps(cites), idea.get("novelty_status"), idea.get("novelty_evidence"),
             idea.get("feasibility"), idea.get("assumptions"),
             int(bool(idea.get("dual_use_flag"))), idea.get("dual_use_note"),
             idea.get("score"), run_id),
        )
    con.commit()
    con.close()

    lines = ["# Research Proposals", "",
             f"_{len(accepted)} grounded ideas (citations verified); "
             f"{len(flagged)} flagged for ungrounded/unknown citations._", ""]
    for i, idea in enumerate(sorted(accepted, key=lambda x: -(x.get("score") or 0)), 1):
        lines += [f"## {i}. {idea.get('title')}  _({idea.get('kind')}, score={idea.get('score')})_",
                  idea.get("description", ""), "",
                  f"- **Builds on:** " + " ".join(f"[[{c}]]" for c in idea.get('grounded_doc_ids', [])),
                  f"- **Novelty:** {idea.get('novelty_status')} — {idea.get('novelty_evidence','')}",
                  f"- **Feasibility:** {idea.get('feasibility','')}",
                  f"- **Assumptions:** {idea.get('assumptions','')}"]
        if idea.get("dual_use_flag"):
            lines.append(f"- **⚠ Dual-use note:** {idea.get('dual_use_note','')}")
        lines.append("")
    (ARTIFACTS_DIR / "ideas.md").write_text("\n".join(lines), encoding="utf-8")
    (ARTIFACTS_DIR / "ideas.json").write_text(json.dumps(ideas, indent=2), encoding="utf-8")
    return {"accepted": len(accepted), "flagged": len(flagged)}
