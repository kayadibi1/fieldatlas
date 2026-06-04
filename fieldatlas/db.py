"""SQLite access layer."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .config import DB_PATH

SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def connect(path=DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    con.commit()


def upsert_documents(con: sqlite3.Connection, docs: list[dict], run_id: str) -> int:
    """Insert/merge canonical documents + their external ids + authors. Returns #new."""
    new = 0
    for d in docs:
        exists = con.execute(
            "SELECT 1 FROM documents WHERE canonical_id=?", (d["canonical_id"],)
        ).fetchone()
        if not exists:
            new += 1
        con.execute(
            """INSERT INTO documents
               (canonical_id,title,abstract,year,pub_date,venue,doc_type,sources,
                source_tiers,n_source_records,oa_pdf_url,landing_url,first_seen_run,last_seen_run)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(canonical_id) DO UPDATE SET
                 abstract=COALESCE(excluded.abstract, documents.abstract),
                 venue=COALESCE(excluded.venue, documents.venue),
                 oa_pdf_url=COALESCE(excluded.oa_pdf_url, documents.oa_pdf_url),
                 landing_url=COALESCE(excluded.landing_url, documents.landing_url),
                 sources=excluded.sources,
                 source_tiers=excluded.source_tiers,
                 n_source_records=excluded.n_source_records,
                 last_seen_run=excluded.last_seen_run
            """,
            (d["canonical_id"], d.get("title"), d.get("abstract"), d.get("year"),
             d.get("pub_date"), d.get("venue"), d.get("doc_type"),
             json.dumps(d.get("sources", [])), json.dumps(d.get("source_tiers", [])),
             d.get("n_source_records", 1), d.get("oa_pdf_url"), d.get("landing_url"),
             run_id, run_id),
        )
        for scheme, value in d.get("external_ids", {}).items():
            con.execute(
                "INSERT OR IGNORE INTO external_ids(canonical_id,scheme,value) VALUES(?,?,?)",
                (d["canonical_id"], scheme, value),
            )
        con.execute("DELETE FROM authors WHERE canonical_id=?", (d["canonical_id"],))
        for pos, name in enumerate(d.get("authors", [])):
            con.execute(
                "INSERT INTO authors(canonical_id,name,position) VALUES(?,?,?)",
                (d["canonical_id"], name, pos),
            )
    con.commit()
    return new


def valid_ids(con: sqlite3.Connection) -> set:
    return {r[0] for r in con.execute("SELECT canonical_id FROM documents")}


def verified_doc_ids(con: sqlite3.Connection) -> set:
    return {r[0] for r in con.execute(
        "SELECT DISTINCT canonical_id FROM evidence_spans WHERE verified=1")}
