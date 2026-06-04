"""The evidence-span verifier is the F1 guard — these tests are its acceptance criteria."""
from fieldatlas.verify import verify_span, verify_extraction
from fieldatlas.textnorm import normalize

SOURCE = """## Introduction
Reinforcement learning from human feedback (RLHF) is widely used to align large
language models. However, reward mis-
specification can lead to deceptive behaviour under distribution shift.
"""


def test_real_quote_matches():
    sn = normalize(SOURCE)
    r = verify_span("reward misspecification can lead to deceptive behaviour", sn)
    assert r.verified and r.reason == "matched"


def test_dehyphenation_and_case():
    # quote spans the "mis-\nspecification" line break and differs in case
    sn = normalize(SOURCE)
    assert verify_span("REWARD MISSPECIFICATION CAN LEAD", sn).verified


def test_fabricated_quote_rejected():
    sn = normalize(SOURCE)
    r = verify_span("the authors prove alignment is fully solved", sn)
    assert not r.verified and r.reason == "not_found"


def test_too_short_rejected():
    sn = normalize(SOURCE)
    assert verify_span("RLHF is", sn).reason == "too_short"


def test_extraction_all_must_verify():
    good = [{"field": "method", "quote": "reinforcement learning from human feedback", "section": "Introduction"}]
    v = verify_extraction(good, SOURCE)
    assert v.accepted and v.n_verified == 1 and "Introduction" in v.coverage_sections

    bad = good + [{"field": "claim", "quote": "this paper solves deceptive alignment entirely", "section": "X"}]
    v2 = verify_extraction(bad, SOURCE)
    assert not v2.accepted and v2.failures  # one fake span rejects the whole extraction
