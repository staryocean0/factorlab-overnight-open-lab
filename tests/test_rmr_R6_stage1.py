from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

MODULE_PATH = ROOT / "scripts/run_rmr_R6_stage1.py"
spec = spec_from_file_location("run_rmr_R6_stage1", MODULE_PATH)
assert spec and spec.loader
mod = module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R6_stage1_protocol_v1.json"


def protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_protocol_freezes_exact_band_budget_and_reserve():
    p = protocol()
    assert p["research_identity"] == "R6_multiscale_amplitude_state_stage1_v1"
    assert p["market_outcomes_opened_for_protocol_design"] is False
    assert p["amplitude_measurement"]["fixed_horizons_bars"] == [4, 16, 64]
    assert p["amplitude_measurement"]["lookback_observed_1m_bars"] == 240
    assert p["normalization"]["reference_window"] == 100
    assert p["event_scales"]["reported_scales"] == ["S1", "S2"]
    assert p["model_budget"]["objects_per_scale"] == [
        "severity_only",
        "severity_plus_short_mid_z",
        "severity_plus_mid_parent_z",
    ]
    assert p["model_budget"]["combined_two_score_model"] is False
    assert p["evidence_roles"]["RESERVE"]["open"] is False
    assert p["candidate_for_program_review_gate"]["third_mechanism_auto_promotion"] is False


def test_within_session_k_returns_exclude_cross_day_jump():
    prices = np.exp(np.asarray([0.0, 0.01, 0.02, 1.00, 1.01, 1.02, 1.03, 1.04]))
    logp = np.log(prices)
    days = np.asarray(["2020-01-02"] * 3 + ["2020-01-03"] * 5)
    vals = mod.valid_k_bar_returns(logp, days, end_idx=7, k=2, lookback=8)
    # One valid two-bar return exists on day 1 and three on day 2. The huge
    # cross-day jump is excluded, so every retained return is only 0.02.
    assert len(vals) == 4
    assert np.allclose(vals, 0.02)


def test_robust_amplitude_scales_by_sqrt_k():
    # One long same-day monotone path with constant log increment.
    logp = np.arange(0, 0.01 * 400, 0.01)
    days = np.asarray(["2020-01-02"] * len(logp))
    a4 = mod.robust_amplitude(logp, days, end_idx=399, k=4)
    a16 = mod.robust_amplitude(logp, days, end_idx=399, k=16)
    a64 = mod.robust_amplitude(logp, days, end_idx=399, k=64)
    assert np.isclose(a4, 0.04 / np.sqrt(4))
    assert np.isclose(a16, 0.16 / np.sqrt(16))
    assert np.isclose(a64, 0.64 / np.sqrt(64))
    scores = mod.amplitude_scores(logp, days, end_idx=399)
    assert np.isclose(scores["R6_A_short_mid"], np.log(a4 / a16))
    assert np.isclose(scores["R6_B_mid_parent"], np.log(a16 / a64))


def test_amplitude_scores_fail_closed_when_history_is_short():
    logp = np.arange(50, dtype=float) * 0.001
    days = np.asarray(["2020-01-02"] * 50)
    scores = mod.amplitude_scores(logp, days, end_idx=49)
    assert np.isnan(scores["R6_A_short_mid"])
    assert np.isnan(scores["R6_B_mid_parent"])


def _cell(local_pass=True, brier_improvement=0.001, ll_improvement=0.001):
    return {
        "scale_local_gate_passed": local_pass,
        "price_path_model_comparison": {
            "pooled_stability": {
                "baseline": {"status": "scored", "brier": 0.25, "log_loss": 0.69},
                "augmented": {
                    "status": "scored",
                    "brier": 0.25 - brier_improvement,
                    "log_loss": 0.69 - ll_improvement,
                },
            }
        },
    }


def test_candidate_gate_requires_both_scales():
    results = {
        "S1": {"scores": {
            "R6_A_short_mid": _cell(True, 0.002, 0.003),
            "R6_B_mid_parent": _cell(True, 0.001, 0.002),
        }},
        "S2": {"scores": {
            "R6_A_short_mid": _cell(True, 0.001, 0.002),
            "R6_B_mid_parent": _cell(False, 0.005, 0.005),
        }},
    }
    gate = mod.aggregate_candidate_gate(results)
    assert gate["by_score"]["R6_A_short_mid"]["qualifies_for_program_review"] is True
    assert gate["by_score"]["R6_B_mid_parent"]["qualifies_for_program_review"] is False
    assert gate["qualified_score_ids"] == ["R6_A_short_mid"]
    assert gate["third_mechanism_auto_promotion"] is False


def test_if_both_qualify_ranking_prefers_mean_brier_improvement():
    results = {
        "S1": {"scores": {
            "R6_A_short_mid": _cell(True, 0.002, 0.002),
            "R6_B_mid_parent": _cell(True, 0.001, 0.004),
        }},
        "S2": {"scores": {
            "R6_A_short_mid": _cell(True, 0.002, 0.002),
            "R6_B_mid_parent": _cell(True, 0.001, 0.004),
        }},
    }
    gate = mod.aggregate_candidate_gate(results)
    assert gate["ranked_for_review"] == ["R6_A_short_mid", "R6_B_mid_parent"]


def test_runner_source_boundary_and_no_search_surfaces():
    text = MODULE_PATH.read_text(encoding="utf-8")
    assert mod.DEV_END == "2019-12-31"
    assert mod.STAB_END == "2022-12-31"
    assert 'filters=[("trading_day", "<=", STAB_END)]' in text
    assert "GridSearch" not in text
    assert "RandomizedSearch" not in text
    assert "combined_score_model_used\": True" not in text
    assert "FFT_or_wavelet_family_search_performed\": True" not in text
    assert "third_mechanism_auto_promoted\": True" not in text
