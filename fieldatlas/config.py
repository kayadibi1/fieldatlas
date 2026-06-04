"""Configuration & paths. Loads secrets from the gitignored .env at the repo root."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
WORK_DIR = ROOT / "work"
ARTIFACTS_DIR = ROOT / "artifacts"
EMB_DIR = ROOT / "embeddings"
for _d in (DATA_DIR, WORK_DIR, ARTIFACTS_DIR, EMB_DIR,
           WORK_DIR / "fulltext", WORK_DIR / "extractions"):
    _d.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / (os.getenv("FIELDATLAS_DB") or "fieldatlas.sqlite")
DEFAULT_SCOPE = ROOT / "scope" / "ai_safety_policy.yaml"


@dataclass(frozen=True)
class Settings:
    contact_email: str
    core_api_key: str | None
    openalex_api_key: str | None
    semantic_scholar_api_key: str | None
    firecrawl_api_key: str | None
    elsevier_api_key: str | None
    elsevier_insttoken: str | None
    wiley_tdm_token: str | None


def settings() -> Settings:
    return Settings(
        contact_email=os.getenv("CONTACT_EMAIL", "anonymous@example.com"),
        core_api_key=os.getenv("CORE_API_KEY") or None,
        openalex_api_key=os.getenv("OPENALEX_API_KEY") or None,
        semantic_scholar_api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY") or None,
        firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY") or None,
        elsevier_api_key=os.getenv("ELSEVIER_API_KEY") or None,
        elsevier_insttoken=os.getenv("ELSEVIER_INSTTOKEN") or None,
        wiley_tdm_token=os.getenv("WILEY_TDM_TOKEN") or None,
    )


def load_scope(path: str | Path | None = None) -> dict:
    """Scope precedence: explicit path > $FIELDATLAS_SCOPE > default AI-safety∩policy file."""
    path = path or os.getenv("FIELDATLAS_SCOPE") or DEFAULT_SCOPE
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
