from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_rmr_stage1_parallel_screen.py"
DATA_ROLE = ROOT / "docs/governance/reversal_mean_reversion_stage1_common_data_role_v1.json"
PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_stage1_execution_protocol_v1.json"

spec = spec_from_file_location("rmr_stage1", RUNNER)
assert spec and spec.loader
mod = module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def synthetic_path(n: int = 1000) -> pd.DataFrame:
    x = np.arange(n)
    logp = np.log(100.0) + 0.006 * np.sin(x / 25.0) + 0.00001 * x
    abs_move = np.r_[0.0, np.abs(np.diff(logp))]
    return pd.DataFrame({
        "log_close": logp,
        "log_high": logp + 0.0002,
        "log_low": logp - 0.0002,
        "sigma20": np.full(n, 0.002),
        "segment_id": np.zeros(n, dtype=int),
        "short_to_parent_volatility_ratio": np.ones(n),
        "cum_abs_move_segment": np.cumsum(abs_move),
        "session_ord": x // 240,
        "trading_day": [f"2020-01-{1 + i // 240:02d}" for i in range(n)],
        "abs_1m_move": abs_move,
    })


def test_common_data_is_fixed_consumed_development_only_and_2026_forbidden():
    role = load(DATA_ROLE)
    assert role["common_dataset"]["instrument"] == "000852.SH"
    assert role["common_dataset"]["sha256"] == mod.EXPECTED_SOURCE_SHA256
    assert role["evidence_roles"]["2015-01-05_to_2025-12-31"]["role"] == "development_material_only"
    assert role["evidence_roles"]["2026-01-05_to_2026-08-21"]["role"] == "forbidden_for_broad_stage1"
    assert role["evidence_roles"]["2026-08-24_to_2026-12-31"]["role"] == "forbidden_for_broad_stage1"
    assert mod.END == "2025-12-31"


def test_scale_pairings_are_exact_two_fixed_three_to_one_measurement_scales():
    role = load(DATA_ROLE)
    pairs = role["first_pass_scale_pairings"]
    assert [(p["id"], p["lower_wave_reversal_threshold_sigma"], p["parent_wave_reversal_threshold_sigma"]) for p in pairs] == [
        ("PAIR_A", 0.50, 1.50),
        ("PAIR_B", 0.75, 2.25),
    ]
    assert all(p["parent_to_lower_threshold_ratio"] == 3.0 for p in pairs)
    assert role["scale_policy"]["pairing_addition_after_results"] is False
    assert role["scale_policy"]["choose_best_pairing_for_lane"] is False


def test_event_thresholds_and_horizon_are_literal_and_not_searchable():
    protocol = load(PROTOCOL)
    assert protocol["R2"]["excursion_trigger_fraction_of_range_width"] == 0.10
    assert protocol["R3"]["minimum_abs_residual_sigma"] == 0.50
    assert mod.R2_TRIGGER_FRAC == 0.10
    assert mod.R3_MIN_RESID == 0.50
    assert mod.MAX_SESSION_HORIZON == 5
    text = json.dumps(protocol)
    assert "search_model_hyperparameters" in text
    assert protocol["common_first_pass_model"]["binary_threshold"] is None


def test_directional_change_pivots_are_only_available_after_reversal_confirmation():
    path = synthetic_path()
    waves = mod.generate_waves(path, 0.50)
    assert len(waves) >= 4
    for wave in waves:
        assert wave.confirm_idx > wave.end_idx
        assert wave.start_confirm_idx is not None
        assert wave.start_confirm_idx < wave.confirm_idx
        assert wave.direction in {-1, 1}
        assert wave.abs_move > 0.0


def test_parent_state_uses_only_parent_waves_confirmed_by_information_cutoff():
    path = synthetic_path()
    parent = mod.generate_waves(path, 1.50)
    assert len(parent) >= 3
    confirms = [w.confirm_idx for w in parent]
    info_idx = parent[2].confirm_idx - 1
    state = mod.parent_state(path, parent, confirms, info_idx)
    assert state is not None
    used = [w for w in parent if w.confirm_idx <= info_idx]
    assert len(used) >= 2
    assert parent[2].confirm_idx > info_idx
    assert np.isfinite(state.signed_drift_ratio)
    assert 0.0 <= state.overlap_ratio <= 1.0


def test_first_passage_is_structural_and_same_bar_tie_is_censored():
    path = synthetic_path(200)
    event_idx = 20
    cur = float(path.iloc[event_idx]["log_close"])
    # Force an unambiguous upper hit on the next bar.
    path.loc[event_idx + 1, "log_high"] = cur + 0.01
    path.loc[event_idx + 1, "log_low"] = cur - 0.0001
    result = mod.first_passage(path, event_idx, cur + 0.005, cur - 0.005, "up", "down")
    assert result["status"] == "resolved"
    assert result["outcome"] == "up"
    # If both structural boundaries hit in one minute, ordering is unknowable and must censor.
    path.loc[event_idx + 1, "log_low"] = cur - 0.01
    tie = mod.first_passage(path, event_idx, cur + 0.005, cur - 0.005, "up", "down")
    assert tie["status"] == "censored_same_bar_tie"
    assert tie["outcome"] is None


def test_stage1_is_equal_budget_no_pnl_and_no_deep_model():
    protocol = load(PROTOCOL)
    assert protocol["lane_comparison_after_execution"]["compare_only_after_R1_R2_R3_all_complete"] is True
    assert protocol["lane_comparison_after_execution"]["no_PnL"] is True
    assert protocol["R3"]["deep_model"] is False
    assert protocol["R3"]["regime_count_search"] is False
    source = RUNNER.read_text(encoding="utf-8")
    assert "trading_return_used\": False" in source
    assert "2026_rows_loaded\": False" in source
