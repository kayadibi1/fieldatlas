"""Publisher TDM (Text & Data Mining) connector — the SANCTIONED route to automated
full text under an institutional license.

This is the legitimate alternative to scraping a paywall with session cookies: the
publisher issues the institution a TDM token that grants programmatic full-text access
under agreed terms and rate limits. It is INERT by default — with no tokens configured
it returns nothing, so the pipeline simply falls back to OA / NOT-READ.

To activate (after JHU Library confirms TDM entitlement and issues tokens), set in .env:
  ELSEVIER_API_KEY   + ELSEVIER_INSTTOKEN     (dev.elsevier.com; institutional TDM token)
  WILEY_TDM_TOKEN                              (Wiley Online Library TDM client token)

Endpoints (verify against current publisher docs before production use):
  Elsevier Article Retrieval: GET https://api.elsevier.com/content/article/doi/{DOI}
      headers: X-ELS-APIKey, X-ELS-Insttoken, Accept: application/pdf
  Wiley TDM:                  GET https://api.wiley.com/onlinelibrary/tdm/v1/articles/{DOI}
      header: Wiley-TDM-Client-Token  (302 -> PDF; follow redirect)

Respect each publisher's TDM rate limits and terms. Do NOT use without a confirmed
institutional TDM agreement.
"""
from __future__ import annotations

import requests

from .connectors.http import UA, _throttle

# DOI-prefix -> publisher (common prefixes; unknown prefixes try all configured providers)
PREFIX_PUBLISHER = {
    "10.1016": "elsevier", "10.1006": "elsevier", "10.1053": "elsevier",
    "10.1002": "wiley", "10.1111": "wiley", "10.1046": "wiley", "10.1029": "wiley",
}


def providers_configured(settings) -> list[str]:
    out = []
    if settings.elsevier_api_key and settings.elsevier_insttoken:
        out.append("elsevier")
    if settings.wiley_tdm_token:
        out.append("wiley")
    return out


def _provider_order(doi: str, configured: list[str]) -> list[str]:
    prefix = doi.split("/", 1)[0]
    pref = PREFIX_PUBLISHER.get(prefix)
    if pref in configured:
        return [pref] + [p for p in configured if p != pref]
    return list(configured)


def _get_pdf(url: str, headers: dict) -> bytes | None:
    _throttle(url)
    h = {"User-Agent": UA, "Accept": "application/pdf"}
    h.update(headers)
    try:
        r = requests.get(url, headers=h, timeout=90, allow_redirects=True)
    except requests.RequestException:
        return None
    if r.status_code == 200 and (r.content[:5] == b"%PDF-"
                                 or "pdf" in r.headers.get("Content-Type", "").lower()):
        return r.content
    return None


def _elsevier(doi: str, settings) -> bytes | None:
    return _get_pdf(
        f"https://api.elsevier.com/content/article/doi/{doi}",
        {"X-ELS-APIKey": settings.elsevier_api_key,
         "X-ELS-Insttoken": settings.elsevier_insttoken},
    )


def _wiley(doi: str, settings) -> bytes | None:
    return _get_pdf(
        f"https://api.wiley.com/onlinelibrary/tdm/v1/articles/{doi}",
        {"Wiley-TDM-Client-Token": settings.wiley_tdm_token},
    )


_FETCHERS = {"elsevier": _elsevier, "wiley": _wiley}


def fetch_pdf(doi: str, settings) -> tuple[bytes, str] | None:
    """Return (pdf_bytes, provider) via a configured publisher TDM API, or None.

    Inert (returns None) when no TDM tokens are configured.
    """
    configured = providers_configured(settings)
    if not doi or not configured:
        return None
    for provider in _provider_order(doi.lower(), configured):
        data = _FETCHERS[provider](doi, settings)
        if data:
            return data, provider
    return None
