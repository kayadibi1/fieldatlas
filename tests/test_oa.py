"""OA recovery: arXiv-from-DOI extraction (pure, no network)."""
from fieldatlas.oa import _arxiv_from_doi


def test_arxiv_doi_extraction():
    assert _arxiv_from_doi("10.48550/arXiv.2307.03718") == "2307.03718"
    assert _arxiv_from_doi("10.48550/arxiv.2405.19524") == "2405.19524"


def test_non_arxiv_doi_returns_none():
    assert _arxiv_from_doi("10.1145/3442188.3445922") is None
    assert _arxiv_from_doi(None) is None
