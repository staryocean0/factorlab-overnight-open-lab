from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_R1_parent_integrity_v2_representation as r1


def test_composite_formula_has_frozen_integrity_directions():
    train = pd.DataFrame({
        "abs_drift": [0.0, 1.0, 2.0],
        "overlap": [0.0, 1.0, 2.0],
        "parent_eff": [0.0, 1.0, 2.0],
    })
    params = r1.fit_parent_standardizer(train)
    probe = pd.DataFrame({
        "abs_drift": [2.0, 0.0],
        "overlap": [0.0, 2.0],
        "parent_eff": [2.0, 0.0],
    })
    out = r1.add_composite(probe, params)
    assert out.loc[0, "parent_integrity"] > 0
    assert out.loc[1, "parent_integrity"] < 0


def test_zero_variance_overlap_matches_standard_scaler_constant_semantics():
    train = pd.DataFrame({
        "abs_drift": [0.0, 1.0, 2.0],
        "overlap": [0.0, 0.0, 0.0],
        "parent_eff": [0.2, 0.5, 0.8],
    })
    params = r1.fit_parent_standardizer(train)
    assert params["zero_variance_features"] == ["overlap"]
    assert params["scale"]["overlap"] == 1.0
    out = r1.add_composite(train, params)
    overlap_z = (train["overlap"] - params["mean"]["overlap"]) / params["scale"]["overlap"]
    assert np.allclose(overlap_z.to_numpy(), 0.0)
    assert np.isfinite(out["parent_integrity"]).all()


def test_binary_events_keeps_only_recovery_and_failure():
    raw = pd.DataFrame([
        {"day": "2020-01-01", "severity": 1.0, "abs_drift": 0.2, "overlap": 0.1, "parent_eff": 0.5, "outcome": "recovery"},
        {"day": "2020-01-02", "severity": 1.0, "abs_drift": 0.2, "overlap": 0.1, "parent_eff": 0.5, "outcome": "failure"},
        {"day": "2020-01-03", "severity": 1.0, "abs_drift": 0.2, "overlap": 0.1, "parent_eff": 0.5, "outcome": "censored"},
    ])
    out = r1.binary_events(raw)
    assert list(out["y"]) == [1, 0]


def test_composite_direction_gate_uses_positive_fitted_coefficient():
    n = 100
    severity = np.linspace(-1.0, 1.0, n)
    integrity = np.linspace(-2.0, 2.0, n)
    y = (integrity > 0).astype(int)
    data = pd.DataFrame({"severity": severity, "parent_integrity": integrity, "y": y})
    model = r1.fit_model(data, ["severity", "parent_integrity"])
    assert model is not None
    assert r1.direction_value(model, "composite_integrity_plus_severity") > 0


def test_protocol_is_complexity_first_and_holdout_sealed():
    p = json.loads((ROOT / "docs/governance/rmr_R1_parent_integrity_v2_representation_protocol_v1.json").read_text())
    assert [x["id"] for x in p["candidate_ladder"]] == list(r1.CANDIDATE_ORDER)
    assert p["selection_rule"]["complexity_first"] is True
    assert p["selection_rule"]["stop_at_first_eligible"] is True
    assert p["source"]["holdout_2023_2025_open_authorized"] is False
    assert p["post_selection_freeze"]["open_2023_2025_in_same_execution"] is False


def test_runner_hard_codes_2022_read_boundary_and_no_pnl():
    source = (ROOT / "scripts/run_rmr_R1_parent_integrity_v2_representation.py").read_text()
    assert 'STAB_END = "2022-12-31"' in source
    assert 'filters=[("trading_day", "<=", STAB_END)]' in source
    assert 'holdout_2023_2025_opened": False' in source
    assert '"trading_return_used": False' in source
