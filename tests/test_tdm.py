"""TDM connector must be INERT unless institutional tokens are configured."""
from dataclasses import dataclass

from fieldatlas import tdm


@dataclass
class FakeSettings:
    elsevier_api_key: str | None = None
    elsevier_insttoken: str | None = None
    wiley_tdm_token: str | None = None


def test_inert_without_tokens():
    s = FakeSettings()
    assert tdm.providers_configured(s) == []
    # must not attempt any network call when nothing is configured
    assert tdm.fetch_pdf("10.1016/j.artint.2021.103535", s) is None


def test_providers_detected():
    s = FakeSettings(elsevier_api_key="k", elsevier_insttoken="t", wiley_tdm_token="w")
    assert set(tdm.providers_configured(s)) == {"elsevier", "wiley"}


def test_provider_order_prefers_doi_prefix():
    cfg = ["elsevier", "wiley"]
    assert tdm._provider_order("10.1002/widm.1234", cfg)[0] == "wiley"   # Wiley prefix
    assert tdm._provider_order("10.1016/j.artint.x", cfg)[0] == "elsevier"  # Elsevier prefix
