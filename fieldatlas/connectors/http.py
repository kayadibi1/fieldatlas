"""Polite HTTP with per-host throttling + retry/backoff (respects verified rate limits)."""
from __future__ import annotations

import time
from urllib.parse import urlparse

import requests
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

UA = "FieldAtlas/0.1 (academic literature review; mailto:sidarvig@gmail.com)"

# minimum seconds between requests per host (from verified connector limits)
HOST_MIN_INTERVAL = {
    "export.arxiv.org": 3.0,
    "api.openalex.org": 0.2,
    "api.crossref.org": 0.2,
    "api.semanticscholar.org": 1.1,    # 1 RPS default even with a key
    "api.core.ac.uk": 1.0,
    "api.elsevier.com": 1.0,           # TDM — respect publisher quotas
    "api.wiley.com": 3.5,              # Wiley TDM is strictly rate-limited
}
_last: dict = {}


def _throttle(url: str) -> None:
    host = urlparse(url).netloc
    gap = HOST_MIN_INTERVAL.get(host, 0.3)
    now = time.monotonic()
    wait = gap - (now - _last.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.monotonic()


class RateLimited(Exception):
    pass


@retry(retry=retry_if_exception_type((RateLimited, requests.ConnectionError, requests.Timeout)),
       wait=wait_exponential(multiplier=2, min=2, max=60),
       stop=stop_after_attempt(5), reraise=True)
def get(url: str, params: dict | None = None, headers: dict | None = None,
        timeout: int = 60):
    _throttle(url)
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    r = requests.get(url, params=params, headers=h, timeout=timeout)
    if r.status_code in (429, 500, 502, 503, 504):
        raise RateLimited(f"{r.status_code} for {url}")
    r.raise_for_status()
    return r
