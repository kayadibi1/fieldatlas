"""Cross-source dedup is the F3 guard (correct recall accounting) — acceptance criteria."""
from fieldatlas.connectors.base import RawRecord
from fieldatlas.dedup import dedup, title_key


def test_shared_doi_merges():
    recs = [
        RawRecord("arxiv", "preprint", "Constitutional AI", year=2022,
                  external_ids={"arxiv": "2212.08073", "doi": "10.5555/abc"}),
        RawRecord("crossref", "peer_reviewed", "Constitutional AI", year=2022,
                  external_ids={"doi": "10.5555/abc"}),
    ]
    docs = dedup(recs)
    assert len(docs) == 1
    assert set(docs[0]["sources"]) == {"arxiv", "crossref"}
    assert docs[0]["canonical_id"].startswith("doi:")  # doi wins canonical id


def test_title_year_merges_without_shared_id():
    recs = [
        RawRecord("arxiv", "preprint", "Frontier AI Regulation: Managing Risks", year=2023,
                  external_ids={"arxiv": "2307.03718"}),
        RawRecord("openalex", "peer_reviewed", "Frontier AI Regulation:  Managing Risks!", year=2023,
                  external_ids={"openalex": "W123"}),
    ]
    docs = dedup(recs)
    assert len(docs) == 1
    assert docs[0]["n_source_records"] == 2


def test_distinct_papers_stay_separate():
    recs = [
        RawRecord("arxiv", "preprint", "Paper A", year=2021, external_ids={"arxiv": "1"}),
        RawRecord("arxiv", "preprint", "Paper B", year=2021, external_ids={"arxiv": "2"}),
    ]
    assert len(dedup(recs)) == 2


def test_title_key_normalizes():
    assert title_key("Frontier AI Regulation:  Managing Risks!") == "frontier ai regulation managing risks"
