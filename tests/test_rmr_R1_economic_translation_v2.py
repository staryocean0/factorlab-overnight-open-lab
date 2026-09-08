import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_R1_economic_translation_v2 as v2
import certify_rmr_R1_economic_translation_v2_blackbox as bb


def test_v2_protocol_is_single_structural_expectancy_candidate():
    p = json.loads((ROOT / "docs/governance/reversal_mean_reversion_R1_economic_translation_v2_protocol.json").read_text())
    s = p["strategy_candidate"]
    assert s["id"] == "R1_STRUCTURAL_EXPECTANCY_POSITIVE_NEXT_BAR_10BP"
    assert s["filter_1"] == "p_parent_integrity_augmented_strictly_greater_than_p_severity_only"
    assert s["filter_2"] == "structural_expected_net_return_strictly_greater_than_zero"
    assert s["expectancy_threshold"] == 0.0
    assert s["probability_threshold_search"] is False
    assert s["expectancy_threshold_search"] is False
    assert p["cost_model"]["primary_round_trip_bps"] == 10.0
    assert p["VALIDATION"]["gate_change_from_v1"] is False


def test_dev_validation_runner_physically_stops_before_blackbox():
    source = (ROOT / "scripts/run_rmr_R1_economic_translation_v2.py").read_text(encoding="utf-8")
    assert 'filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)]' in source
    assert "economic v2 DEV/VALIDATION runner read blackbox" in source
    assert "ROUND_TRIP_COST = 0.0010" in source
    assert "expectancy_threshold" in source


def test_structural_expectancy_filter_uses_candidate_probability_and_boundaries():
    events = pd.DataFrame({
        "severity": [1.0, 1.0],
        "abs_drift": [3.0, 0.0],
        "overlap": [0.0, 3.0],
        "parent_eff": [0.0, 0.0],
        "recovery_gross": [0.01, 0.01],
        "failure_gross": [-0.005, -0.005],
        "net_return": [0.01, -0.005],
        "holding_bars": [10, 10],
        "day": ["2024-01-02", "2024-01-03"],
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
        "baseline_object": Model([0.50, 0.50]),
        "candidate_object": Model([0.80, 0.40]),
    }
    out = v2.add_filters(events, bundle)
    expected0 = 0.80 * 0.01 + 0.20 * (-0.005) - 0.001
    assert np.isclose(out.loc[0, "structural_expected_net_return"], expected0)
    assert bool(out.loc[0, "selected_trade"]) is True
    assert bool(out.loc[1, "selected_trade"]) is False


def test_blackbox_decision_rule_is_three_state_only():
    assert bb.decide({"A": (True, True), "B": (True, True)}) == "PASS"
    assert bb.decide({"A": (True, False), "B": (True, True)}) == "FAIL"
    assert bb.decide({"A": (False, False), "B": (True, True)}) == "INSUFFICIENT"


def test_v2_blackbox_receipt_is_low_bandwidth():
    source = (ROOT / "scripts/certify_rmr_R1_economic_translation_v2_blackbox.py").read_text(encoding="utf-8")
    receipt = source.split("receipt = {", 1)[1].split("args.receipt.parent", 1)[0].lower()
    for forbidden in (
        "mean_candidate",
        "mean_all",
        "mean_net_return",
        "win_rate",
        "holding_bars",
        '"resolved"',
        '"n"',
        "by_year",
        "by_month",
        "structural_expected_net_return",
    ):
        assert forbidden not in receipt
    assert '"decision": decision' in receipt
    assert '"exact_metrics_released": false' in receipt
    assert '"counts_released": false' in receipt


def test_blackbox_pairing_gate_uses_both_filters_without_releasing_detail():
    events = pd.DataFrame({
        "day": ["2026-03-02"] * 30,
        "severity": [1.0] * 30,
        "abs_drift": [3.0] * 30,
        "overlap": [0.0] * 30,
        "parent_eff": [0.0] * 30,
        "recovery_gross": [0.02] * 30,
        "failure_gross": [-0.005] * 30,
        "net_return": [0.01] * 30,
    })
    frozen_pair = {
        "parent_feature_scaler": {"mean": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
        "severity_baseline_model": {
            "scaler": {"mean": [0.0], "scale": [1.0]},
            "logistic": {"coef": [0.0], "intercept": 0.0},
        },
        "selected_candidate_model": {
            "scaler": {"mean": [0.0, 0.0], "scale": [1.0, 1.0]},
            "logistic": {"coef": [0.0, 2.0], "intercept": 0.0},
        },
    }
    sample_ok, metric_ok = bb.pairing_gate(events, frozen_pair, minimum=20)
    assert sample_ok is True
    assert metric_ok is True
