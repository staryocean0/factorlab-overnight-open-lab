from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
MODULE_PATH = ROOT / "scripts/run_rmr_R1_parent_integrity_v2_selection.py"
spec = spec_from_file_location("r1v2", MODULE_PATH)
assert spec and spec.loader
mod = module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_protocol_is_results_blind_and_candidate_budget_is_exact():
    p = json.loads((ROOT / "docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_selection_protocol_v1.json").read_text())
    assert p["source"]["holdout_2023_2025_open_for_selection"] is False
    assert p["source"]["all_2026_open"] is False
    assert [x["candidate_id"] for x in p["candidate_ladder"]] == [
        "R1_PARENT_COMPOSITE_1D", "R1_PARENT_ORIGINAL_3D"
    ]
    assert p["event_and_outcome"]["severity"] == "abs(lower_wave_move)/DEV_median_rvol20_exact_broad_R1_definition"


def test_composite_orientation_is_exact():
    train = pd.DataFrame({
        "abs_drift": [0.0, 1.0, 2.0, 3.0],
        "overlap": [3.0, 2.0, 1.0, 0.0],
        "parent_eff": [0.0, 1.0, 2.0, 3.0],
    })
    sc = StandardScaler().fit(train[["abs_drift", "overlap", "parent_eff"]])
    out = mod.add_composite(train, sc)
    assert out["parent_integrity"].iloc[-1] > out["parent_integrity"].iloc[0]
    z = sc.transform(train[["abs_drift", "overlap", "parent_eff"]])
    expected = (z[:, 0] - z[:, 1] + z[:, 2]) / 3.0
    assert np.allclose(out["parent_integrity"], expected)


def test_resolved_binary_keeps_only_recovery_failure():
    frame = pd.DataFrame({
        "day": ["2020-01-01"] * 4,
        "severity": [1, 1, 1, 1],
        "abs_drift": [1, 1, 1, 1],
        "overlap": [0, 0, 0, 0],
        "parent_eff": [1, 1, 1, 1],
        "outcome": ["recovery", "failure", "censored", "tie"],
    })
    out = mod.resolved_binary(frame)
    assert list(out["y"]) == [1, 0]


def test_json_digest_is_deterministic():
    a = {"b": 1, "a": [2, 3]}
    b = {"a": [2, 3], "b": 1}
    assert mod.json_digest(a) == mod.json_digest(b)


def test_runner_source_is_bounded_before_holdout():
    text = MODULE_PATH.read_text(encoding="utf-8")
    assert 'STAB_END = "2022-12-31"' in text
    assert 'filters=[("trading_day", "<=", STAB_END)]' in text
    assert 'holdout_2023_2025_opened": False' in text
    assert "trading_return_used\": False" in text
    assert "CANDIDATE_ORDER = (\"R1_PARENT_COMPOSITE_1D\", \"R1_PARENT_ORIGINAL_3D\")" in text
