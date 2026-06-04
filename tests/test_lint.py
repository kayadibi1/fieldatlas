"""The citation linter is the F2 guard — these tests are its acceptance criteria."""
from fieldatlas.lint import extract_citations, lint_text, lint_grounded

VALID = {"arxiv:2212.08073", "doi:10.1145/3442188.3445922"}
VERIFIED = {"arxiv:2212.08073"}


def test_extract():
    assert extract_citations("As shown [[arxiv:2212.08073]] and [[doi:10.1/x]].") == \
        ["arxiv:2212.08073", "doi:10.1/x"]


def test_unknown_citation_fails():
    r = lint_text("Per [[arxiv:9999.99999]] this is true.", VALID)
    assert not r.ok and "arxiv:9999.99999" in r.unknown_ids


def test_known_citations_pass():
    assert lint_text("See [[arxiv:2212.08073]] and [[doi:10.1145/3442188.3445922]].", VALID).ok


def test_grounded_requires_verified_support():
    # cites a real + verified doc -> ok
    ok = lint_grounded([{"text": "claim", "citations": ["arxiv:2212.08073"]}], VALID, VERIFIED)
    assert ok.ok
    # cites a real but UNVERIFIED doc -> ungrounded
    ung = lint_grounded([{"text": "claim", "citations": ["doi:10.1145/3442188.3445922"]}], VALID, VERIFIED)
    assert not ung.ok and ung.ungrounded_claims
    # cites a nonexistent doc -> unknown
    unk = lint_grounded([{"text": "claim", "citations": ["fake:1"]}], VALID, VERIFIED)
    assert not unk.ok and "fake:1" in unk.unknown_ids
