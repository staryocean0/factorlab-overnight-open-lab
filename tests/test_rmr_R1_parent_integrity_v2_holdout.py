from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
MODULE_PATH = ROOT / "scripts/evaluate_rmr_R1_parent_integrity_v2_holdout.py"
spec = spec_from_file_location("r1holdout", MODULE_PATH)
assert spec and spec.loader
mod = module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_frozen_bundle_digest_and_candidate_identity():
    protocol, freeze = mod.validate_freeze()
    assert protocol["selected_candidate_id"] == "R1_PARENT_COMPOSITE_1D"
    assert freeze["mechanistic_sign_precondition_passed"] is True
    assert freeze["parameter_bundle_sha256"] == "e618a5a06a803f4464267e69e39f98fa316fd572f40efcb3f9e40fc25df2779c"


def test_frozen_predict_matches_manual_logistic():
    snap = {
        "scaler": {"mean": [1.0, 2.0], "scale": [2.0, 4.0]},
        "logistic": {"coef": [0.5, -1.0], "intercept": 0.25},
    }
    x = np.asarray([[3.0, 6.0], [1.0, 2.0]])
    p = mod.frozen_predict(snap, x)
    z = (x - np.asarray([1.0, 2.0])) / np.asarray([2.0, 4.0])
    logits = z @ np.asarray([0.5, -1.0]) + 0.25
    expected = 1.0 / (1.0 + np.exp(-logits))
    assert np.allclose(p, expected)


def test_frozen_integrity_orientation():
    frame = pd.DataFrame({
        "abs_drift": [2.0, 0.0],
        "overlap": [0.0, 2.0],
        "parent_eff": [2.0, 0.0],
    })
    sc = {"mean": [1.0, 1.0, 1.0], "scale": [1.0, 1.0, 1.0]}
    out = mod.add_frozen_integrity(frame, sc)
    assert out["parent_integrity"].iloc[0] > out["parent_integrity"].iloc[1]


def test_holdout_protocol_is_no_refit_and_2026_sealed():
    p = json.loads((ROOT / "docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_holdout_protocol_v1.json").read_text())
    assert p["model_use"]["refit_allowed"] is False
    assert p["source"]["all_2026_rows_open"] is False
    assert p["holdout"]["start"] == "2023-01-01"
    assert p["holdout"]["end"] == "2025-12-31"
    assert p["both_pairings_must_pass"] is True


def test_runner_has_no_fit_surface():
    text = MODULE_PATH.read_text(encoding="utf-8")
    assert ".fit(" not in text
    assert 'filters=[("trading_day", "<=", HOLDOUT_END)]' in text
    assert '"refit_performed": False' in text
    assert '"2026_rows_loaded": False' in text
