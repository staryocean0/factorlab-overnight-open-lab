from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

MODULE_PATH = ROOT / "scripts/run_rmr_R7_stage1.py"
spec = spec_from_file_location("run_rmr_R7_stage1", MODULE_PATH)
assert spec and spec.loader
mod = module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R7_stage1_protocol_v1.json"


def protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_protocol_freezes_one_score_and_reserve():
    p = protocol()
    assert p["research_identity"] == "R7_directional_path_energy_asymmetry_stage1_v1"
    assert p["market_outcomes_opened_for_protocol_design"] is False
    assert p["state_measurement"]["score_id"] == "R7_directional_energy_balance"
    assert p["state_measurement"]["trailing_observed_1m_bars"] == 240
    assert p["state_measurement"]["minimum_valid_within_session_returns"] == 120
    assert p["normalization"]["reference_window"] == 100
    assert p["event_scales"]["reported_scales"] == ["S1", "S2"]
    assert p["model_budget"]["objects_per_scale"] == [
        "severity_only", "severity_plus_directional_energy_z"
    ]
    assert p["evidence_roles"]["RESERVE"]["open"] is False
    assert p["candidate_for_program_review_gate"]["third_mechanism_auto_promotion"] is False


def test_trailing_returns_exclude_cross_session_jump():
    logp = np.asarray([0.00, 0.01, 0.02, 1.00, 1.01, 1.02, 1.03, 1.04])
    days = np.asarray(["2020-01-02"] * 3 + ["2020-01-03"] * 5)
    vals = mod.trailing_within_session_returns(logp, days, end_idx=7, window=8)
    assert len(vals) == 6
    assert np.allclose(vals, 0.01)


def test_directional_energy_balance_aligns_with_wave_direction():
    returns = np.asarray([0.01, 0.02, -0.01, -0.01] * 40)
    logp = np.r_[0.0, np.cumsum(returns)]
    days = np.asarray(["2020-01-02"] * len(logp))
    up = mod.directional_energy_balance(logp, days, len(logp) - 1, 1)
    down = mod.directional_energy_balance(logp, days, len(logp) - 1, -1)
    expected = (0.0005 - 0.0002) / (0.0005 + 0.0002)
    assert np.isclose(up, expected)
    assert np.isclose(down, -expected)
    assert -1.0 <= up <= 1.0
    assert -1.0 <= down <= 1.0


def test_directional_energy_balance_requires_frozen_minimum_history():
    returns = np.asarray([0.01, -0.01] * 40)
    logp = np.r_[0.0, np.cumsum(returns)]
    days = np.asarray(["2020-01-02"] * len(logp))
    value = mod.directional_energy_balance(logp, days, len(logp) - 1, 1)
    assert np.isnan(value)


def test_runner_boundary_and_no_search_surfaces():
    text = MODULE_PATH.read_text(encoding="utf-8")
    assert mod.DEV_END == "2019-12-31"
    assert mod.STAB_END == "2022-12-31"
    assert mod.WINDOW == 240
    assert mod.MIN_VALID_RETURNS == 120
    assert mod.REFERENCE_WINDOW == 100
    assert mod.SCALES == ("S1", "S2")
    assert 'filters=[("trading_day", "<=", STAB_END)]' in text
    assert "GridSearch" not in text
    assert "RandomizedSearch" not in text
    assert "third_mechanism_auto_promoted\": True" not in text
    assert "alternative_asymmetry_definition_search_performed\": True" not in text
