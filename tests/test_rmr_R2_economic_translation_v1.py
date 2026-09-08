import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_R2_economic_translation_v1 as econ
import certify_rmr_R2_economic_translation_v1_blackbox as bb


def test_protocol_is_single_candidate_without_search():
    p = json.loads((ROOT / "docs/governance/reversal_mean_reversion_R2_economic_translation_v1_protocol.json").read_text())
    s = p["strategy_candidate"]
    assert s["id"] == "R2_STRUCTURAL_EXPECTANCY_POSITIVE_NEXT_BAR_10BP"
    assert s["entry"] == "next_observed_1m_close_after_R2_event_confirmation"
    assert s["filter_1"] == "p_range_integrity_augmented_strictly_greater_than_p_geometry_baseline"
    assert s["filter_2"] == "candidate_structural_expected_net_return_strictly_greater_than_zero"
    assert s["probability_threshold_search"] is False
    assert s["expectancy_threshold_search"] is False
    assert p["cost_model"]["primary_round_trip_bps"] == 10.0
    assert p["cost_model"]["cost_search_allowed"] is False
    assert p["BLACKBOX"]["public_output_only"] == ["PASS", "FAIL", "INSUFFICIENT"]


def test_runner_physically_stops_before_blackbox():
    source = (ROOT / "scripts/run_rmr_R2_economic_translation_v1.py").read_text(encoding="utf-8")
    assert 'filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)]' in source
    assert "R2 economic DEV/VALIDATION runner read BLACKBOX" in source
    assert "ROUND_TRIP_COST = 0.0010" in source


def test_structural_expectancy_requires_probability_edge_and_positive_expectancy():
    trades = pd.DataFrame({
        "outside_ratio": [1.0, 1.0, 1.0],
        "break_speed": [1.0, 1.0, 1.0],
        "local_vol_ratio": [1.0, 1.0, 1.0],
        "abs_drift": [0.0, 3.0, 0.0],
        "overlap": [3.0, 0.0, 3.0],
        "parent_eff": [0.0, 3.0, 0.0],
        "reward_gross": [0.02, 0.02, 0.002],
        "loss_gross": [-0.005, -0.005, -0.02],
        "net_return": [0.01, -0.01, -0.01],
        "holding_bars": [10, 10, 10],
        "day": ["2024-01-02", "2024-01-03", "2024-01-04"],
    })

    class ParentScaler:
        def transform(self, x):
            return np.asarray(x, dtype=float)

    class Model:
        def __init__(self, probs):
            self.probs = np.asarray(probs, dtype=float)
        def predict_proba(self, x):
            p = self.probs[: len(x)]
            return np.column_stack([1.0 - p, p])

    bundle = {
        "parent_scaler_object": ParentScaler(),
        "baseline_object": Model([0.50, 0.50, 0.50]),
        "candidate_object": Model([0.80, 0.40, 0.55]),
    }
    out = econ.add_filters(trades, bundle)
    expected0 = 0.80 * 0.02 + 0.20 * (-0.005) - 0.001
    assert np.isclose(out.loc[0, "structural_expected_net_return"], expected0)
    assert bool(out.loc[0, "selected_trade"]) is True
    assert bool(out.loc[1, "selected_trade"]) is False
    assert bool(out.loc[2, "selected_trade"]) is False


def test_trade_geometry_reward_loss_orientation_on_both_sides():
    for side, edge, entry, continuation in [
        (1, 100.0, 101.0, 102.0),
        (-1, 100.0, 99.0, 98.0),
    ]:
        direction = -side
        reward = direction * (edge / entry - 1.0)
        loss = direction * (continuation / entry - 1.0)
        assert reward > 0.0
        assert loss < 0.0


def test_blackbox_decision_rule_is_three_state_only():
    assert bb.decide({"A": (True, True), "B": (True, True)}) == "PASS"
    assert bb.decide({"A": (True, False), "B": (True, True)}) == "FAIL"
    assert bb.decide({"A": (False, False), "B": (True, True)}) == "INSUFFICIENT"


def test_blackbox_receipt_source_is_low_bandwidth():
    source = (ROOT / "scripts/certify_rmr_R2_economic_translation_v1_blackbox.py").read_text(encoding="utf-8")
    receipt = source.split("receipt = {", 1)[1].split("args.receipt.parent", 1)[0].lower()
    for forbidden in (
        "mean_selected",
        "mean_all",
        "mean_net_return",
        "win_rate",
        "holding_bars",
        '"n"',
        '"resolved"',
        "by_year",
        "by_month",
        "structural_expected_net_return",
    ):
        assert forbidden not in receipt
    assert '"decision": decision' in receipt
    assert '"exact_metrics_released": false' in receipt
    assert '"counts_released": false' in receipt


def test_blackbox_pairing_gate_can_pass_synthetic_selected_subset():
    rows = []
    for _ in range(30):
        rows.append({
            "day": "2026-03-02",
            "outside_ratio": 1.0,
            "break_speed": 1.0,
            "local_vol_ratio": 1.0,
            "abs_drift": 0.0,
            "overlap": 3.0,
            "parent_eff": 0.0,
            "reward_gross": 0.02,
            "loss_gross": -0.005,
            "net_return": 0.01,
        })
    for _ in range(20):
        rows.append({
            "day": "2026-03-03",
            "outside_ratio": 1.0,
            "break_speed": 1.0,
            "local_vol_ratio": 1.0,
            "abs_drift": 3.0,
            "overlap": 0.0,
            "parent_eff": 3.0,
            "reward_gross": 0.003,
            "loss_gross": -0.02,
            "net_return": -0.01,
        })
    trades = pd.DataFrame(rows)
    frozen_pair = {
        "parent_feature_scaler": {"mean": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
        "baseline_model": {
            "scaler": {"mean": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
            "logistic": {"coef": [0.0, 0.0, 0.0], "intercept": 0.0},
        },
        "candidate_model": {
            "scaler": {"mean": [0.0, 0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0, 1.0]},
            "logistic": {"coef": [0.0, 0.0, 0.0, 2.0], "intercept": 0.0},
        },
    }
    sample_ok, metric_ok = bb.pairing_gate(trades, frozen_pair, minimum=25)
    assert sample_ok is True
    assert metric_ok is True
