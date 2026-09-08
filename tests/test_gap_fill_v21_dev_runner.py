from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_gap_fill_v21_dev_selection as run

AUTH = ROOT / "docs/governance/cloud_session_20260908_gap_fill_v21_dev_open_authorization_v1.json"
FAMILY = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_candidate_family_v1.json"
STATE = ROOT / "docs/governance/gap_fill_v21_state_v1.json"


def test_dev_authorization_is_separate_from_historical_family_freeze():
    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    family = json.loads(FAMILY.read_text(encoding="utf-8"))
    state = json.loads(STATE.read_text(encoding="utf-8"))
    assert family["V21_DEV_outcomes_open_authorized"] is False
    assert auth["V21_DEV_outcomes_open_authorized"] is True
    assert auth["Audit_A_outcomes_open_authorized"] is False
    assert auth["Audit_B_outcomes_open_authorized"] is False
    assert state["DEV_open_authorization"] == str(AUTH.relative_to(ROOT))
    assert state["sealed"]["V21_DEV_outcomes"] is False
    assert state["sealed"]["V21_AUDIT_A_outcomes"] is True
    assert state["sealed"]["V21_AUDIT_B_outcomes"] is True
    assert state["sealed"]["V21_EXTERNAL_RESERVE_outcomes"] is True


def test_target_clock_path_uses_optional_1459_without_synthesizing_it():
    without = run.target_clocks_for_day(False)
    with_optional = run.target_clocks_for_day(True)
    assert len(without["15m"]) == 15
    assert len(without["60m"]) == 60
    assert len(without["eod"]) == 239
    assert "14:59" not in without["eod"]
    assert "15:00" in without["eod"]
    assert len(with_optional["eod"]) == 240
    assert "14:59" in with_optional["eod"]


def test_metadata_inventory_uses_named_239_gate_for_both_symbols():
    clocks = list(run.gate.required_session_complete_239_clocks())
    rows = []
    for symbol in run.SYMBOLS.values():
        for clock in clocks:
            rows.append({
                "symbol": symbol,
                "trading_day": "2017-01-03",
                "timestamp": f"2017-01-03 {clock}:00",
            })
    frame = pd.DataFrame(rows)
    audit = run.metadata_inventory(frame)
    for symbol in run.SYMBOLS.values():
        info = audit["by_symbol"][symbol]
        assert info["observed_days"] == 1
        assert info["session_complete_days"] == 1
        assert info["incomplete_days"] == 0
        assert info["optional_1459_present_days"] == 0


def test_local_csi500_candidate_leaves_csi300_control_unchanged():
    h15 = np.array([0.30, 0.40])
    h60 = np.array([0.20, 0.25])
    heod = np.array([0.10, 0.15])
    control = run.p2.cumulative_probs(h15, h60, heod)
    base = {
        "valid_hazards": (h15, h60, heod),
        "valid_z": np.array([-1.0, 1.0]),
        "control_probs": control,
    }
    got = run.candidate_probs(
        "P2_CSI500_SHARED_1B",
        "CSI300",
        base,
        {"shared": {"beta": 0.8}},
    )
    for left, right in zip(got, control):
        assert np.allclose(left, right)


def test_cross_index_shared_candidate_applies_same_beta_to_15m_and_60m():
    h15 = np.array([0.30, 0.30, 0.30])
    h60 = np.array([0.20, 0.20, 0.20])
    heod = np.array([0.10, 0.10, 0.10])
    z = np.array([-1.0, 0.0, 1.0])
    control = run.p2.cumulative_probs(h15, h60, heod)
    base = {
        "valid_hazards": (h15, h60, heod),
        "valid_z": z,
        "control_probs": control,
    }
    got = run.candidate_probs(
        "P2_XI_SHARED_1B",
        "CSI300",
        base,
        {"shared": {"beta": 1.0}},
    )
    assert got[0][0] < control[0][0]
    assert got[0][2] > control[0][2]
    assert got[1][0] < control[1][0]
    assert got[1][2] > control[1][2]
    assert run.p2.monotonicity_violations(*got) == 0


def test_runner_boundaries_are_exactly_frozen_dev():
    assert run.DEV_START == "2015-01-01"
    assert run.DEV_END == "2018-12-31"
    assert run.DEV_VALIDATION_YEARS == (2016, 2017, 2018)
    assert tuple(run.p2.CANDIDATE_LADDER) == (
        "P2_XI_SHARED_1B",
        "P2_CSI500_SHARED_1B",
        "P2_CSI500_STAGE_2B",
    )
