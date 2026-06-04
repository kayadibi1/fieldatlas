"""Shared text normalization used by the evidence-span verifier.

Normalization must be applied IDENTICALLY to source full text and to candidate quotes,
so that a quote which truly occurs in the source matches, while a fabricated quote cannot.
It tolerates the lossy realities of PDF extraction (hyphenation across line breaks,
ligatures, dash variants, collapsed whitespace, case) WITHOUT being so loose that
invented text could pass — every word must still be present, in order.
"""
from __future__ import annotations

import re
import unicodedata

_DASHES = {"‐": "-", "‑": "-", "‒": "-", "–": "-",
           "—": "-", "−": "-"}
_DEHYPHEN = re.compile(r"-\s*\n\s*")          # "align-\nment" -> "alignment"
_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = t.replace("­", "")               # soft hyphen
    t = _DEHYPHEN.sub("", t)                   # de-hyphenate line breaks
    for d, r in _DASHES.items():
        t = t.replace(d, r)
    t = t.replace("’", "'").replace("‘", "'")
    t = t.replace("“", '"').replace("”", '"')
    t = _WS.sub(" ", t)
    return t.strip().lower()


def word_count(text: str) -> int:
    return len(normalize(text).split())
