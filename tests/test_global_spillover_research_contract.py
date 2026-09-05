from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_global_spillover_preregistration_is_bounded() -> None:
    p = json.loads((ROOT / "docs/governance/global_spillover_v1_preregistration.json").read_text())
    assert p["multiplicity_attempts"] == 5
    assert len(p["candidate_family"]) == 5
    assert p["model_contract"]["ridge_alpha"] == 1.0
    assert p["model_contract"]["no_hyperparameter_search"] is True
    assert "total_return" in p["selection_forbidden"]
    assert p["authority"]["fresh_oos"] is False
    assert p["authority"]["production"] is False


def test_external_markets_are_data_requests_not_v1_features() -> None:
    p = json.loads((ROOT / "docs/governance/global_spillover_v1_preregistration.json").read_text())
    requested = set(p["future_data_requests_not_admitted_in_v1"])
    assert "KOSPI_same_day_pre_0930_return" in requested
    assert "Nikkei_same_day_pre_0930_return" in requested
    assert "USDCNH_overnight_return" in requested
    assert "SGX_FTSE_China_A50_overnight_or_preopen_return" in requested

    added = {
        feature
        for candidate in p["candidate_family"]
        for feature in candidate.get("added_features", [])
    }
    assert not any("kospi" in x.lower() or "nikkei" in x.lower() or "cnh" in x.lower() or "a50" in x.lower() for x in added)
