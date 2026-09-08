import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_unified_parent_state_router_v1 as router
import certify_rmr_unified_parent_state_router_v1_blackbox as bb


def test_protocol_is_one_low_capacity_signed_axis_without_search():
    p = json.loads((ROOT / "docs/governance/reversal_mean_reversion_unified_parent_state_router_v1_protocol.json").read_text())
    assert p["research_identity"] == "rmr_unified_parent_normal_state_router_v1"
    assert p["parent_state"]["features"] == ["abs_drift", "overlap", "parent_eff"]
    assert p["parent_state"]["trend_axis"] == "(z(abs_drift)-z(overlap)+z(parent_eff))/3"
    assert p["parent_state"]["state_consistency"] == {"R1": "+trend_axis", "R2": "-trend_axis"}
    assert p["pooled_models"]["baseline_features"] == ["base_logit", "lane_R2", "pair_B"]
    assert p["pooled_models"]["candidate_features"] == ["base_logit", "lane_R2", "pair_B", "state_consistency"]
    assert p["pooled_models"]["interactions_allowed"] is False
    assert p["pooled_models"]["hyperparameter_search_allowed"] is False
    assert p["BLACKBOX"]["query_number_if_reached"] == 4
    forbidden = set(p["forbidden"])
    assert "new_indicator_family" in forbidden
    assert "state_consistency_threshold_search" in forbidden
    assert "PnL_entry_exit_cost_or_portfolio_optimization" in forbidden


def test_same_parent_structure_has_opposite_lane_consistency():
    scaler = StandardScaler().fit(np.array([
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
        [2.0, 2.0, 2.0],
    ]))
    frame = pd.DataFrame({
        "abs_drift": [2.0],
        "overlap": [0.0],
        "parent_eff": [2.0],
    })
    r1 = router.add_state_consistency(frame, scaler, "R1")["state_consistency"].iloc[0]
    r2 = router.add_state_consistency(frame, scaler, "R2")["state_consistency"].iloc[0]
    assert r1 > 0
    assert np.isclose(r1, -r2)


def test_runner_physically_stops_before_blackbox():
    source = (ROOT / "scripts/run_rmr_unified_parent_state_router_v1.py").read_text(encoding="utf-8")
    assert 'filters=[("trading_day", "<=", VAL_END)]' in source
    assert "router DEV/VALIDATION runner read BLACKBOX rows" in source
    assert 'VAL_END = "2025-12-31"' in source
    assert "DEFAULT_BLACKBOX" not in source


def test_frozen_prediction_matches_manual_logistic():
    snapshot = {
        "features": ["x1", "x2"],
        "scaler": {"mean": [1.0, 2.0], "scale": [2.0, 4.0]},
        "logistic": {"coef": [0.5, -1.0], "intercept": 0.25},
    }
    frame = pd.DataFrame({"x1": [3.0], "x2": [6.0]})
    p = bb.frozen_predict(snapshot, frame)[0]
    z1, z2 = 1.0, 1.0
    logit = 0.5 * z1 - 1.0 * z2 + 0.25
    expected = 1.0 / (1.0 + np.exp(-logit))
    assert np.isclose(p, expected)


def test_blackbox_decision_is_three_state_only():
    assert bb.decide(False, False) == "INSUFFICIENT"
    assert bb.decide(True, False) == "FAIL"
    assert bb.decide(True, True) == "PASS"


def test_blackbox_receipt_source_is_low_bandwidth():
    source = (ROOT / "scripts/certify_rmr_unified_parent_state_router_v1_blackbox.py").read_text(encoding="utf-8")
    receipt = source.split("receipt = {", 1)[1].split("args.receipt.parent", 1)[0].lower()
    for forbidden in (
        "brier",
        "log_loss",
        "sample_ok",
        "metric_ok",
        '"n"',
        "by_year",
        "by_month",
        "state_consistency_coefficient",
    ):
        assert forbidden not in receipt
    assert '"decision": decision' in receipt
    assert '"exact_metrics_released": false' in receipt
    assert '"counts_released": false' in receipt
    assert '"subperiods_released": false' in receipt
    assert '"event_rows_released": false' in receipt


def test_router_cells_are_exactly_certified_r1_r2_geometries():
    p = json.loads((ROOT / "docs/governance/reversal_mean_reversion_unified_parent_state_router_v1_protocol.json").read_text())
    assert set(p["cells"]) == {"R1_A", "R1_B", "R2_A", "R2_B"}
    assert p["cells"]["R1_A"]["local_baseline_features"] == ["severity"]
    assert p["cells"]["R1_B"]["local_baseline_features"] == ["severity"]
    assert p["cells"]["R2_A"]["local_baseline_features"] == ["outside_ratio", "break_speed", "local_vol_ratio"]
    assert p["cells"]["R2_B"]["local_baseline_features"] == ["outside_ratio", "break_speed", "local_vol_ratio"]
