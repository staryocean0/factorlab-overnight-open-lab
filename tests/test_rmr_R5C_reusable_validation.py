import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_R5C_reusable_validation as r5c
import certify_rmr_R5C_reusable_blackbox as bb


def test_protocol_freezes_one_geometry_baseline_and_one_augmented_model():
    p = json.loads((ROOT / "docs/governance/reversal_mean_reversion_R5C_reusable_validation_protocol_v1.json").read_text())
    fam = p["model_family"]
    assert fam["exact_model_count"] == 2
    assert fam["baseline_features"] == r5c.BASE_FEATURES
    assert fam["candidate_features"] == r5c.CAND_FEATURES
    assert fam["hyperparameter_search"] is False
    assert p["event_density"]["trailing_bars"] == 240
    assert p["event_density"]["normalization"]["history"] == "preceding_100_same_scale_property_observations"
    assert p["scales"]["co_primary"] == ["S1", "S2"]
    assert p["VALIDATION_pass_requires_both_scales"] is True


def test_density_counts_current_confirmation_in_trailing_240_bars():
    confirms = [0, 100, 239, 240, 300]
    d = r5c.density_series(confirms)
    assert np.isclose(d[0], 1 / 240)
    assert np.isclose(d[2], 3 / 240)
    # at index 240, confirmation 0 is outside [1,240], leaving 100,239,240
    assert np.isclose(d[3], 3 / 240)
    # at 300, trailing window [61,300] contains 100,239,240,300
    assert np.isclose(d[4], 4 / 240)


def test_past100_median_mad_normalization_excludes_current():
    past = np.array(([0.0, 1.0] * 50) + [2.0], dtype=float)
    z = r5c.causal_mad_z(past, history=100)
    assert np.isnan(z[99])
    # past median=.5, MAD=.5; current=2 => z=3
    assert np.isclose(z[100], 3.0)


def test_first_passage_reversion_extension_and_role_end_cap():
    # Up completed wave: down move is reversion, up move is extension.
    prices = np.array([100.0, 100.2, 98.9, 102.0], dtype=float)
    outcome, idx = r5c.first_passage_symmetric(prices, 0, 1, 0.01, 3)
    assert outcome == "reversion"
    assert idx == 2

    prices2 = np.array([100.0, 100.2, 101.2], dtype=float)
    outcome2, idx2 = r5c.first_passage_symmetric(prices2, 0, 1, 0.01, 2)
    assert outcome2 == "extension"
    assert idx2 == 2

    # The reversion happens only after the role boundary; it must remain censored.
    prices3 = np.array([100.0, 100.0, 100.0, 98.0], dtype=float)
    outcome3, idx3 = r5c.first_passage_symmetric(prices3, 0, 1, 0.01, 2)
    assert outcome3 == "censored"
    assert idx3 == 2


def test_validation_runner_cannot_read_reusable_blackbox():
    source = (ROOT / "scripts/run_rmr_R5C_reusable_validation.py").read_text(encoding="utf-8")
    assert "archive/data/gap_fill_repeat_2026" not in source
    assert 'filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)]' in source
    assert "R5-C DEV/VALIDATION runner read BLACKBOX" in source


def test_blackbox_decision_is_three_state_only():
    assert bb.decide({"S1": (True, True), "S2": (True, True)}) == "PASS"
    assert bb.decide({"S1": (True, False), "S2": (True, True)}) == "FAIL"
    assert bb.decide({"S1": (False, False), "S2": (True, True)}) == "INSUFFICIENT"


def test_blackbox_receipt_source_is_low_bandwidth():
    source = (ROOT / "scripts/certify_rmr_R5C_reusable_blackbox.py").read_text(encoding="utf-8")
    receipt = source.split("receipt = {", 1)[1].split("args.receipt.parent", 1)[0].lower()
    for forbidden in (
        "brier_base",
        "brier_cand",
        "ll_base",
        "ll_cand",
        "event_rate",
        "resolved",
        "by_year",
        "by_month",
        "event_density_z",
    ):
        assert forbidden not in receipt
    assert '"decision": decision' in receipt
    assert '"exact_metrics_released": false' in receipt
    assert '"counts_released": false' in receipt
