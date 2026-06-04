"""Regression tests for stress-test fixes: empty-corpus, tiny k-means, ingest idempotency."""
import numpy as np

from fieldatlas import db
from fieldatlas.graph import _kmeans
from fieldatlas.ingest import ingest_extraction
from fieldatlas.rank import assign_tiers, rank_documents


def test_rank_documents_empty_no_crash():
    assert rank_documents([], {}) == []
    assert assign_tiers([], {})["tier1"] == 0


def test_kmeans_single_cluster():
    X = np.array([[1.0, 0.0], [0.9, 0.1]], dtype=np.float32)
    labels = _kmeans(X, 1)
    assert len(labels) == 2 and set(labels.tolist()) == {0}


def test_ingest_is_idempotent(tmp_path):
    con = db.connect(tmp_path / "t.sqlite")
    db.init_db(con)
    cid = "doi:test/1"
    md = tmp_path / "ft.md"
    md.write_text("Reinforcement learning from human feedback aligns language models.", encoding="utf-8")
    con.execute("INSERT INTO documents(canonical_id,title) VALUES(?,?)", (cid, "t"))
    con.execute("INSERT INTO fulltext(canonical_id,parsed_md_path) VALUES(?,?)", (cid, str(md)))
    con.commit()
    extraction = {"canonical_id": cid, "problem": "p",
                  "spans": [{"field": "problem",
                             "quote": "Reinforcement learning from human feedback aligns language models.",
                             "section": "x"}]}
    ingest_extraction(con, extraction, "run1")
    r2 = ingest_extraction(con, extraction, "run1")   # re-ingest must REPLACE, not duplicate
    n_ext = con.execute("SELECT COUNT(*) FROM extractions WHERE canonical_id=?", (cid,)).fetchone()[0]
    n_sp = con.execute("SELECT COUNT(*) FROM evidence_spans WHERE canonical_id=?", (cid,)).fetchone()[0]
    assert n_ext == 1 and n_sp == 1 and r2["status"] == "verified"
