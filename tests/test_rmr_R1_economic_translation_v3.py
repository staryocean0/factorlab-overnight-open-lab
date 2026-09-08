import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_R1_economic_translation_v3 as v3
import certify_rmr_R1_economic_translation_v3_blackbox as bb


def test_v3_protocol_is_one_fixed_direct_return_family():
    p = json.loads((ROOT / "docs/governance/reversal_mean_reversion_R1_economic_translation_v3_protocol.json").read_text())
    fam = p["model_family"]
    assert fam["exact_candidate_count"] == 2
    assert fam["baseline_features"] == v3.BASE_FEATURES
    assert fam["candidate_features"] == v3.CAND_FEATURES
    assert fam["ridge_alpha"] == 1.0
    assert fam["hyperparameter_search"] is False
    assert fam["interaction_terms"] is False
    assert p["strategy_rule"]["predicted_return_threshold"] == 0.0
    assert p["strategy_rule"]["threshold_search"] is False
    assert p["VALIDATION"]["gate_change_from_v1_v2"] is False


def test_v3_runner_physically_stops_before_blackbox():
    source = (ROOT / "scripts/run_rmr_R1_economic_translation_v3.py").read_text(encoding="utf-8")
    assert 'filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)]' in source
    assert "economic v3 DEV/VALIDATION runner read blackbox" in source
    assert "Ridge(alpha=RIDGE_ALPHA)" in source
    assert "RIDGE_ALPHA = 1.0" in source


def test_return_model_snapshot_and_prediction_rule_are_fixed():
    frame = pd.DataFrame({
        "severity": np.linspace(0.5, 1.5, 60),
        "recovery_gross": np.linspace(0.005, 0.02, 60),
        "failure_gross": -np.linspace(0.005, 0.015, 60),
        "parent_integrity": np.linspace(-1.0, 1.0, 60),
    })
    frame["net_return"] = 0.002 * frame["parent_integrity"] + 0.1 * frame["recovery_gross"]
    model = v3.fit_return_model(frame, v3.CAND_FEATURES)
    snap = v3.return_model_snapshot(model, v3.CAND_FEATURES)
    assert snap["ridge"]["alpha"] == 1.0
    assert snap["features"] == v3.CAND_FEATURES
    assert len(snap["ridge"]["coef"]) == 4


def test_blackbox_decision_rule_is_three_state_only():
    assert bb.decide({"A": (True, True), "B": (True, True)}) == "PASS"
    assert bb.decide({"A": (True, False), "B": (True, True)}) == "FAIL"
    assert bb.decide({"A": (False, False), "B": (True, True)}) == "INSUFFICIENT"


def test_v3_blackbox_receipt_is_low_bandwidth():
    source = (ROOT / "scripts/certify_rmr_R1_economic_translation_v3_blackbox.py").read_text(encoding="utf-8")
    receipt = source.split("receipt = {", 1)[1].split("args.receipt.parent", 1)[0].lower()
    for forbidden in (
        "mean_candidate",
        "mean_all",
        "mean_net_return",
        "win_rate",
        "holding_bars",
        '"n"',
        "by_year",
        "by_month",
        "predicted_candidate_net",
        "predicted_baseline_net",
    ):
        assert forbidden not in receipt
    assert '"decision": decision' in receipt
    assert '"exact_metrics_released": false' in receipt
    assert '"counts_released": false' in receipt


def test_frozen_return_prediction_and_pairing_gate():
    selected = pd.DataFrame({
        "day": ["2026-03-02"] * 30,
        "severity": [1.0] * 30,
        "abs_drift": [3.0] * 30,
        "overlap": [0.0] * 30,
        "parent_eff": [0.0] * 30,
        "recovery_gross": [0.02] * 30,
        "failure_gross": [-0.005] * 30,
        "net_return": [0.01] * 30,
    })
    unselected = pd.DataFrame({
        "day": ["2026-03-03"] * 10,
        "severity": [1.0] * 10,
        "abs_drift": [0.0] * 10,
        "overlap": [3.0] * 10,
        "parent_eff": [0.0] * 10,
        "recovery_gross": [0.02] * 10,
        "failure_gross": [-0.005] * 10,
        "net_return": [-0.02] * 10,
    })
    events = pd.concat([selected, unselected], ignore_index=True)
    frozen_pair = {
        "parent_feature_scaler": {"mean": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
        "baseline_return_model": {
            "scaler": {"mean": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
            "ridge": {"coef": [0.0, 0.0, 0.0], "intercept": -0.001, "alpha": 1.0},
        },
        "candidate_return_model": {
            "scaler": {"mean": [0.0, 0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0, 1.0]},
            "ridge": {"coef": [0.0, 0.0, 0.0, 0.01], "intercept": 0.0, "alpha": 1.0},
        },
    }
    sample_ok, metric_ok = bb.pairing_gate(events, frozen_pair, minimum=20)
    assert sample_ok is True
    assert metric_ok is True
