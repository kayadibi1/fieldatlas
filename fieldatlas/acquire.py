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
UNPAYWALL = "https://api.unpaywall.org/v2/{doi}"


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


def _unpaywall_pdf(doi: str, email: str) -> str | None:
    try:
        r = get(UNPAYWALL.format(doi=doi), params={"email": email})
    except Exception:
        return None
    j = r.json()
    if not j.get("is_oa"):
        return None
    best = j.get("best_oa_location") or {}
    return best.get("url_for_pdf") or best.get("url")


def acquire_one(doc: dict, settings) -> dict:
    cid = doc["canonical_id"]
    dest = PDF_DIR / f"{safe_name(cid)}.pdf"
    if dest.exists() and dest.stat().st_size > 1000:
        return {"canonical_id": cid, "status": "fetched", "path": str(dest), "via": "cache"}

    ids = doc.get("external_ids", {})
    candidates = []
    if ids.get("arxiv"):
        candidates.append(("arxiv", f"https://arxiv.org/pdf/{ids['arxiv']}.pdf"))
    if doc.get("oa_pdf_url"):
        candidates.append(("oa_url", doc["oa_pdf_url"]))
    if ids.get("doi"):
        up = _unpaywall_pdf(ids["doi"], settings.contact_email)
        if up:
            candidates.append(("unpaywall", up))

    for via, url in candidates:
        if _download_pdf(url, dest):
            return {"canonical_id": cid, "status": "fetched", "path": str(dest), "via": via}
    return {"canonical_id": cid, "status": "metadata_only", "path": None, "via": None}


def acquire(docs: list[dict], settings) -> list[dict]:
    return [acquire_one(d, settings) for d in docs]
