from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/v21_p2_overlay.py"
FAMILY = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_candidate_family_v1.json"
STATE = ROOT / "docs/governance/gap_fill_v21_state_v1.json"

spec = spec_from_file_location("v21_p2_overlay", MODULE_PATH)
assert spec and spec.loader
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def family():
    return json.loads(FAMILY.read_text(encoding="utf-8"))


def test_candidate_ladder_is_exact_and_complexity_first():
    f = family()
    ids = [x["id"] for x in f["candidate_ladder"]]
    assert ids == [
        "P2_XI_SHARED_1B",
        "P2_CSI500_SHARED_1B",
        "P2_CSI500_STAGE_2B",
    ]
    assert tuple(ids) == mod.CANDIDATE_LADDER
    assert f["ladder_execution_rule"]["stop_at_first_eligible_candidate"] is True
    assert mod.first_eligible_candidate({
        "P2_XI_SHARED_1B": True,
        "P2_CSI500_SHARED_1B": True,
        "P2_CSI500_STAGE_2B": True,
    }) == "P2_XI_SHARED_1B"
    assert mod.first_eligible_candidate({
        "P2_XI_SHARED_1B": False,
        "P2_CSI500_SHARED_1B": True,
        "P2_CSI500_STAGE_2B": True,
    }) == "P2_CSI500_SHARED_1B"
    assert mod.first_eligible_candidate({}) is None


def test_positive_beta_has_expected_direction_and_preserves_nesting():
    base15 = np.array([0.30, 0.30, 0.30])
    base60 = np.array([0.25, 0.25, 0.25])
    baseeod = np.array([0.20, 0.20, 0.20])
    z = np.array([-1.0, 0.0, 1.0])
    h15 = mod.apply_beta(base15, z, 1.0)
    h60 = mod.apply_beta(base60, z, 1.0)
    assert h15[0] < base15[0]
    assert h15[1] == base15[1]
    assert h15[2] > base15[2]
    assert h60[0] < base60[0]
    assert h60[2] > base60[2]
    p15, p60, peod = mod.cumulative_probs(h15, h60, baseeod)
    assert mod.monotonicity_violations(p15, p60, peod) == 0
    # EOD stage hazard itself stays frozen even though cumulative pEOD changes.
    control = mod.cumulative_probs(base15, base60, baseeod)[2]
    assert not np.allclose(peod, control)


def test_shared_beta_fit_can_recover_positive_residual_direction():
    z = np.array([-2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0])
    base = np.full(len(z), 0.40)
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=float)
    cells = [
        mod.OffsetCell(base, z, y),
        mod.OffsetCell(np.full(len(z), 0.30), z, y),
    ]
    result = mod.fit_shared_beta(cells)
    assert result["success"] is True
    assert result["beta"] > 0.0
    assert -6.0 <= result["beta"] <= 6.0
    assert result["objective"] < mod.shared_beta_objective(0.0, cells)


def test_training_standardizer_is_train_frozen():
    s = mod.fit_standardizer([1.0, 2.0, 3.0, 4.0])
    assert np.isclose(s.mean, 2.5)
    train_z = s.transform([1.0, 2.0, 3.0, 4.0])
    assert np.isclose(np.mean(train_z), 0.0)
    assert np.isclose(np.std(train_z, ddof=0), 1.0)
    valid_z = s.transform([10.0])
    assert valid_z[0] > 1.0


def test_three_year_sign_and_stability_gates_are_literal():
    assert mod.positive_sign_gate([0.2, -0.1, 0.3]) is True
    assert mod.positive_sign_gate([-0.2, -0.1, 0.3]) is False
    assert mod.annual_improvement_gate([0.01, -0.001, 0.02]) is True
    assert mod.annual_improvement_gate([-0.01, -0.001, 0.02]) is False


def test_protocol_uses_only_rd1_admitted_P2_and_keeps_future_sealed():
    f = family()
    assert f["parent_rd1"]["admitted_probe_ids"] == ["P2_relative_gap_excess"]
    assert f["P2_feature"]["expected_beta_sign"] == "positive"
    assert f["target_contract"]["primary_successor_horizons"] == ["fill_15m", "fill_60m"]
    assert f["target_contract"]["eod_role"] == "mandatory_descriptive_only_for_V21_selection_and_confirmation"
    assert f["V21_DEV_outcomes_open_authorized"] is False
    assert f["successor_model_fit_authorized"] is False
    assert f["successor_model_selection_authorized"] is False
    assert all(x["outcomes_open"] is False for x in f["frozen_windows"].values())
    text = json.dumps(f)
    for rejected in ["P1_common_gap_support", "P3_trend20_alignment", "P4_prior_daytime_alignment", "P5_relative_momentum5_alignment"]:
        assert rejected in f["parent_rd1"]["rejected_probe_ids"]
    assert "trading_return" in text


def test_dev_and_future_audit_gates_are_frozen_before_dev_open():
    f = family()
    assert f["V21_DEV_oof"]["validation_years"] == [2016, 2017, 2018]
    assert f["V21_DEV_oof"]["minimum_primary_rows_per_validation_year"] == 20
    assert f["V21_DEV_oof"]["minimum_primary_rows_pooled"] == 60
    assert f["DEV_candidate_eligibility_gates"]["all_required"] is True
    assert f["future_Audit_A_and_Audit_B_primary_gates_frozen_now"]["all_required"] is True
    assert f["future_audit_decision_rule"]["no_combined_A_plus_B_rescue"] is True
    assert f["future_audit_decision_rule"]["external_reserve_cannot_replace_or_rescue_Audit_A_or_Audit_B"] is True


def test_repo_state_still_denies_dev_fit_and_selection():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    assert state["sealed"]["V21_DEV_outcomes"] is True
    assert state["sealed"]["V21_AUDIT_A_outcomes"] is True
    assert state["sealed"]["V21_AUDIT_B_outcomes"] is True
    assert state["successor_model_fit_authorized"] is False
    assert state["successor_model_selection_authorized"] is False
