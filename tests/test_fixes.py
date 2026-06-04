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


def test_dedup_drops_title_and_id_less_records():
    from fieldatlas.connectors.base import RawRecord
    from fieldatlas.dedup import dedup
    recs = [RawRecord("s", "t", "", external_ids={}),                       # garbage: no title, no id
            RawRecord("s", "t", "Real Paper", year=2020, external_ids={"doi": "10.1/x"})]
    assert len(dedup(recs)) == 1


def test_oa_cheap_is_network_free():
    from fieldatlas import oa
    d = {"external_ids": {"doi": "10.48550/arXiv.2307.03718"}, "oa_pdf_url": None}
    cheap = oa.cheap_pdf_urls(d)                                            # must not call the network
    assert cheap == [("arxiv", "https://arxiv.org/pdf/2307.03718.pdf")]


def test_seed_corpus_forces_tier1():
    from fieldatlas.rank import assign_tiers
    ranked = [{"canonical_id": "doi:10.1/x", "relevance": 0.1, "is_fresh": False, "external_ids": {"doi": "10.1/x"}},
              {"canonical_id": "a", "relevance": 0.9, "is_fresh": False, "external_ids": {}}]
    assign_tiers(ranked, {"read_tiers": {"tier1_threshold": 0.55, "tier1_cap": 300},
                          "seed_corpus": {"dois": ["10.1/x"]}})
    assert next(d["read_tier"] for d in ranked if d["canonical_id"] == "doi:10.1/x") == 1


def test_lint_ignores_empty_citation_marker():
    from fieldatlas.lint import lint_text
    assert lint_text("noise [[   ]] more", {"real:1"}).ok   # empty [[ ]] must not flag as unknown


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
