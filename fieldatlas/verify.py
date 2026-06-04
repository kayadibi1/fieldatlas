"""Evidence-span verifier — the deterministic guard against fake reading (F1).

A deep-read extraction is only accepted if every evidence span's verbatim quote is
found (after shared normalization) in the document's parsed full text. A model that
did not actually read the paper cannot produce quotes that exist in it.
"""
from __future__ import annotations

from dataclasses import dataclass

from .textnorm import normalize, word_count

MIN_QUOTE_WORDS = 4     # below this a match is too trivial to count as evidence
ACCEPT_THRESHOLD = 0.85  # fraction of spans that must verify verbatim to accept a reading


@dataclass
class SpanResult:
    verified: bool
    reason: str          # "matched" | "not_found" | "too_short" | "empty"


def verify_span(quote: str, source_norm: str) -> SpanResult:
    """source_norm must already be normalize()-d (do it once per document)."""
    if not quote or not quote.strip():
        return SpanResult(False, "empty")
    if word_count(quote) < MIN_QUOTE_WORDS:
        return SpanResult(False, "too_short")
    q = normalize(quote)
    return SpanResult(True, "matched") if q in source_norm else SpanResult(False, "not_found")


@dataclass
class ExtractionVerdict:
    accepted: bool
    n_spans: int
    n_verified: int
    coverage_sections: set            # sections that yielded >=1 verified span
    failures: list                    # list[(field, quote, reason)]


def verify_extraction(spans: list[dict], full_text: str) -> ExtractionVerdict:
    """spans: list of {field, quote, section}. full_text: raw parsed markdown.

    Policy is PER-CLAIM, not all-or-nothing: each span is verified independently; failed
    spans are dropped (never usable as evidence). A reading is ACCEPTED if at least
    ACCEPT_THRESHOLD of its spans verify verbatim. Either way, only verified spans become
    citable evidence, so no unverifiable claim can ground an output.
    """
    source_norm = normalize(full_text)
    failures, covered, n_ok = [], set(), 0
    for s in spans:
        r = verify_span(s.get("quote", ""), source_norm)
        if r.verified:
            n_ok += 1
            if s.get("section"):
                covered.add(s["section"])
        else:
            failures.append((s.get("field"), s.get("quote", "")[:80], r.reason))
    accepted = len(spans) > 0 and (n_ok / len(spans)) >= ACCEPT_THRESHOLD
    return ExtractionVerdict(accepted, len(spans), n_ok, covered, failures)
