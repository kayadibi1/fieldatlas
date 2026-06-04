"""PDF -> section-structured markdown (PyMuPDF4LLM; born-digital faithful for arXiv PDFs).

Faithful verbatim text is essential: the evidence-span verifier string-matches quotes
back into this output, so we must NOT use any OCR/LLM rewriting path.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .config import WORK_DIR

FT_DIR = WORK_DIR / "fulltext"
FT_DIR.mkdir(parents=True, exist_ok=True)
_HEADER = re.compile(r"^#{1,4}\s+(.*)$", re.MULTILINE)


def extract_sections(md: str) -> list[dict]:
    """Split markdown into (header, text) sections by ATX headers."""
    out, last_end, last_title = [], 0, "PREAMBLE"
    matches = list(_HEADER.finditer(md))
    for i, m in enumerate(matches):
        if i == 0 and m.start() > 0:
            out.append({"section": last_title, "text": md[:m.start()].strip()})
        title = m.group(1).strip()
        nxt = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        out.append({"section": title, "text": md[m.end():nxt].strip()})
    if not matches:
        out.append({"section": "BODY", "text": md.strip()})
    return [s for s in out if s["text"]]


def parse_pdf(pdf_path: str, canonical_id: str, safe: str) -> dict:
    import pymupdf4llm
    try:
        md = pymupdf4llm.to_markdown(pdf_path, show_progress=False)
    except Exception as e:
        return {"canonical_id": canonical_id, "parse_status": "failed", "error": str(e)[:200]}
    md_path = FT_DIR / f"{safe}.md"
    md_path.write_text(md, encoding="utf-8")
    return {
        "canonical_id": canonical_id,
        "parse_status": "parsed",
        "parsed_md_path": str(md_path),
        "char_count": len(md),
        "parse_tool": "pymupdf4llm",
        "content_hash": hashlib.sha1(md.encode("utf-8", "ignore")).hexdigest()[:16],
        "sections": [s["section"] for s in extract_sections(md)],
    }
