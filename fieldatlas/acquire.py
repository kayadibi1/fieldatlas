"""Full-text acquisition — legal OA sources only (arXiv, CORE, OA via Unpaywall).

Items with no obtainable OA full text are marked metadata_only (NOT-READ) and are
structurally barred from contributing deep claims. No shadow-library sources.
"""
from __future__ import annotations

import re
from pathlib import Path

from .config import WORK_DIR
from .connectors.http import get

PDF_DIR = WORK_DIR / "pdf"
PDF_DIR.mkdir(parents=True, exist_ok=True)


def safe_name(cid: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", cid)


def _download_pdf(url: str, dest: Path) -> bool:
    try:
        r = get(url, timeout=90)
    except Exception:
        return False
    ct = r.headers.get("Content-Type", "")
    body = r.content
    if "pdf" in ct.lower() or body[:5] == b"%PDF-":
        dest.write_bytes(body)
        return True
    return False


def acquire_one(doc: dict, settings) -> dict:
    cid = doc["canonical_id"]
    dest = PDF_DIR / f"{safe_name(cid)}.pdf"
    if dest.exists() and dest.stat().st_size > 1000:
        with open(dest, "rb") as f:
            if f.read(5) == b"%PDF-":     # validate magic bytes, not just size (catch truncated cache)
                return {"canonical_id": cid, "status": "fetched", "path": str(dest), "via": "cache"}

    from . import oa
    ids = doc.get("external_ids", {})
    # cheap (no-network) candidates first; only hit networked OA locators if those fail
    for via, url in oa.cheap_pdf_urls(doc):
        if _download_pdf(url, dest):
            return {"canonical_id": cid, "status": "fetched", "path": str(dest), "via": via}
    for via, url in oa.networked_pdf_urls(doc, settings):
        if _download_pdf(url, dest):
            return {"canonical_id": cid, "status": "fetched", "path": str(dest), "via": via}

    # Sanctioned publisher TDM fallback — inert unless institutional TDM tokens are set.
    if ids.get("doi"):
        from . import tdm
        res = tdm.fetch_pdf(ids["doi"], settings)
        if res:
            data, provider = res
            dest.write_bytes(data)
            return {"canonical_id": cid, "status": "fetched", "path": str(dest), "via": f"tdm:{provider}"}

    return {"canonical_id": cid, "status": "metadata_only", "path": None, "via": None}


def acquire(docs: list[dict], settings) -> list[dict]:
    return [acquire_one(d, settings) for d in docs]
