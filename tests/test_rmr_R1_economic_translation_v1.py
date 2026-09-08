import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import certify_rmr_R1_economic_translation_blackbox as bb


def test_protocol_has_one_candidate_and_no_threshold_or_cost_search():
    p = json.loads((ROOT / "docs/governance/reversal_mean_reversion_R1_economic_translation_v1_protocol.json").read_text())
    assert p["strategy_candidate"]["id"] == "R1_EDGE_POSITIVE_NEXT_BAR_10BP"
    assert p["strategy_candidate"]["probability_threshold_search"] is False
    assert p["strategy_candidate"]["entry"] == "next_observed_1m_close_after_R1_event_confirmation"
    assert p["cost_model"]["primary_round_trip_bps"] == 10.0
    assert p["cost_model"]["cost_search_allowed"] is False
    assert p["BLACKBOX"]["public_output_only"] == ["PASS", "FAIL", "INSUFFICIENT"]


def test_blackbox_decision_rule():
    assert bb.decide({"A": (True, True), "B": (True, True)}) == "PASS"
    assert bb.decide({"A": (True, False), "B": (True, True)}) == "FAIL"
    assert bb.decide({"A": (False, False), "B": (True, True)}) == "INSUFFICIENT"


def test_economic_blackbox_receipt_source_is_low_bandwidth():
    source = (ROOT / "scripts/certify_rmr_R1_economic_translation_blackbox.py").read_text(encoding="utf-8")
    receipt = source.split("receipt = {", 1)[1].split("args.receipt.parent", 1)[0].lower()
    for forbidden in ("mean_net_return", "win_rate", "holding_bars", "resolved", "count", "by_year", "by_month"):
        assert forbidden not in receipt
    assert '"decision": decision' in receipt
    assert '"exact_metrics_released": false' in receipt
    assert '"counts_released": false' in receipt


def test_pairing_gate_uses_edge_filter_and_economic_return():
    events = pd.DataFrame([
        {"day": "2026-03-02", "severity": 1.0, "abs_drift": 3.0, "overlap": 0.0, "parent_eff": 0.0, "net_return": 0.01},
        {"day": "2026-03-03", "severity": 1.0, "abs_drift": 0.0, "overlap": 3.0, "parent_eff": 0.0, "net_return": -0.01},
    ] * 30)
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


def test_dev_validation_runner_physically_stops_before_2026():
    source = (ROOT / "scripts/run_rmr_R1_economic_translation_v1.py").read_text(encoding="utf-8")
    assert 'filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)]' in source
    assert "economic DEV/VALIDATION runner read blackbox" in source
    assert "ROUND_TRIP_COST = 0.0010" in source
