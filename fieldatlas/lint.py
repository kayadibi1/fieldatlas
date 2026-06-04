"""Citation linter — the deterministic guard against fabricated references (F2).

Every artifact (report, idea, map note) may cite documents ONLY by internal id, using
the marker form [[canonical_id]]. The linter rejects:
  * any cited id that does not resolve to a real document in the corpus, and
  * (for grounded/claim-bearing items) any claim whose cited documents have no
    verified evidence span backing it.
A model literally cannot smuggle an invented reference past this — the id must exist.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

CITE_RE = re.compile(r"\[\[([^\]\[]+)\]\]")


def extract_citations(text: str) -> list[str]:
    return [m.group(1).strip() for m in CITE_RE.finditer(text or "")]


@dataclass
class LintResult:
    ok: bool
    unknown_ids: list = field(default_factory=list)      # cited but not in corpus
    ungrounded_claims: list = field(default_factory=list)  # claim text w/o verified support
    n_citations: int = 0


def lint_text(text: str, valid_ids: set) -> LintResult:
    """Check that every [[id]] in free text resolves to a real document."""
    cites = extract_citations(text)
    unknown = sorted({c for c in cites if c not in valid_ids})
    return LintResult(ok=not unknown, unknown_ids=unknown, n_citations=len(cites))


def lint_grounded(items: list[dict], valid_ids: set,
                  verified_doc_ids: set) -> LintResult:
    """Check grounded items (e.g. report claims, ideas).

    Each item: {text, citations: [ids]}. Requires every citation to resolve AND at
    least one cited document to carry a verified evidence span (be in verified_doc_ids).
    """
    unknown, ungrounded = set(), []
    n = 0
    for it in items:
        cites = it.get("citations", []) or []
        n += len(cites)
        for c in cites:
            if c not in valid_ids:
                unknown.add(c)
        if not any(c in verified_doc_ids for c in cites):
            ungrounded.append((it.get("text", "")[:120]))
    return LintResult(
        ok=(not unknown and not ungrounded),
        unknown_ids=sorted(unknown),
        ungrounded_claims=ungrounded,
        n_citations=n,
    )
