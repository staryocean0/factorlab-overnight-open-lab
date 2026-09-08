import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_R2_range_integrity_v2 as r2
import certify_rmr_R2_range_integrity_v2_blackbox as bb


def test_protocol_is_one_added_range_integrity_feature():
    p = json.loads((ROOT / "docs/governance/reversal_mean_reversion_R2_range_integrity_v2_protocol.json").read_text())
    assert p["research_identity"] == "rmr_range_boundary_parent_integrity_v2"
    assert p["baseline"]["features"] == ["outside_ratio", "break_speed", "local_vol_ratio"]
    assert p["candidate"]["formula"] == "(-z(abs_drift)+z(overlap)-z(parent_eff))/3"
    assert p["candidate"]["interactions_allowed"] is False
    assert p["frozen_scales"]["scale_search_allowed"] is False
    assert p["BLACKBOX"]["public_output_only"] == ["PASS", "FAIL", "INSUFFICIENT"]


def test_runner_physically_stops_before_blackbox():
    source = (ROOT / "scripts/run_rmr_R2_range_integrity_v2.py").read_text(encoding="utf-8")
    assert 'filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)]' in source
    assert "R2 DEV/VALIDATION runner read BLACKBOX" in source
    assert "PnL" not in source


def test_range_integrity_orientation():
    class DummyScaler:
        def transform(self, x):
            return np.asarray(x, dtype=float)
    frame = pd.DataFrame({
        "abs_drift": [0.0, 3.0],
        "overlap": [3.0, 0.0],
        "parent_eff": [0.0, 3.0],
    })
    out = r2.add_range_integrity(frame, DummyScaler())
    assert out.loc[0, "range_integrity"] > out.loc[1, "range_integrity"]
    assert np.isclose(out.loc[0, "range_integrity"], 1.0)
    assert np.isclose(out.loc[1, "range_integrity"], -2.0)


def test_blackbox_decision_rule_is_three_state_only():
    assert bb.decide({"A": (True, True), "B": (True, True)}) == "PASS"
    assert bb.decide({"A": (True, False), "B": (True, True)}) == "FAIL"
    assert bb.decide({"A": (False, False), "B": (True, True)}) == "INSUFFICIENT"


def test_blackbox_receipt_source_is_low_bandwidth():
    source = (ROOT / "scripts/certify_rmr_R2_range_integrity_v2_blackbox.py").read_text(encoding="utf-8")
    receipt = source.split("receipt = {", 1)[1].split("args.receipt.parent", 1)[0].lower()
    for forbidden in (
        "brier_score_loss",
        "log_loss(",
        '"n"',
        '"resolved"',
        "by_year",
        "by_month",
        "range_integrity_coef",
    ):
        assert forbidden not in receipt
    assert '"decision": decision' in receipt
    assert '"details_released": false' in receipt
    assert '"exact_metrics_released": false' in receipt
    assert '"counts_released": false' in receipt


def test_blackbox_pairing_gate_can_pass_on_synthetic_frozen_models():
    rows = []
    for _ in range(25):
        rows.append({
            "day": "2026-03-02",
            "outside_ratio": 1.0,
            "break_speed": 1.0,
            "local_vol_ratio": 1.0,
            "abs_drift": 0.0,
            "overlap": 3.0,
            "parent_eff": 0.0,
            "outcome": "reentry",
        })
        rows.append({
            "day": "2026-03-03",
            "outside_ratio": 1.0,
            "break_speed": 1.0,
            "local_vol_ratio": 1.0,
            "abs_drift": 3.0,
            "overlap": 0.0,
            "parent_eff": 3.0,
            "outcome": "continuation",
        })
    events = pd.DataFrame(rows)
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
    sample_ok, metric_ok = bb.pairing_gate(events, frozen_pair, minimum=40)
    assert sample_ok is True
    assert metric_ok is True
