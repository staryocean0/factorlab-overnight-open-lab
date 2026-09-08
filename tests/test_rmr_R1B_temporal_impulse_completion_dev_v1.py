from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "r1b_temporal",
    ROOT / "scripts/run_rmr_R1B_temporal_impulse_completion_dev_v1.py",
)
m = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(m)


def wave(direction, start_idx, end_idx, confirm_idx, start_price, end_price):
    return m.common.Wave(direction, start_idx, end_idx, confirm_idx, start_price, end_price)


def test_frozen_identity_and_constants():
    p = m.validate_protocol()
    assert p["research_identity"] == "rmr_R1B_temporal_impulse_completion_v1"
    assert p["candidate_id"] == "R1B_S2_PARENT_IMPULSE_CONFIRM_EXIT"
    assert m.S2 == pytest.approx(0.006891654009228464)
    assert m.S3 == pytest.approx(0.013783308018456928)
    assert m.HORIZON == 1200
    assert m.COST == pytest.approx(0.0010)
    assert p["execution"]["probability_threshold"] is None


def test_parent_aligned_impulse_exit_uses_causal_confirmation_close():
    prices = np.asarray([100.0, 99.0, 99.5, 100.0, 101.0, 102.0, 101.5, 101.0, 100.8])
    waves = [
        wave(-1, 0, 1, 2, 100.0, 99.0),
        wave(+1, 1, 5, 7, 99.0, 102.0),
    ]
    event = {"confirm_idx": 2, "parent_sign": 1, "failure": 95.0, "lower_wave_pos": 0}
    klass, idx = m.candidate_exit(prices, event, waves)
    assert klass == "parent_aligned_S2_impulse_confirmed"
    assert idx == 7
    assert prices[idx] == pytest.approx(101.0)
    assert prices[5] == pytest.approx(102.0)  # noncausal wave extreme must not be used


def test_parent_failure_preempts_later_impulse_confirmation():
    prices = np.asarray([100.0, 99.0, 99.5, 99.2, 98.8, 94.5, 96.0, 97.0])
    waves = [
        wave(-1, 0, 1, 2, 100.0, 99.0),
        wave(+1, 1, 6, 7, 99.0, 96.0),
    ]
    event = {"confirm_idx": 2, "parent_sign": 1, "failure": 95.0, "lower_wave_pos": 0}
    klass, idx = m.candidate_exit(prices, event, waves)
    assert klass == "parent_failure"
    assert idx == 5


def test_candidate_censors_without_confirmed_parent_aligned_impulse():
    prices = np.asarray([100.0, 99.0, 99.5, 99.8, 100.1, 100.0])
    waves = [wave(-1, 0, 1, 2, 100.0, 99.0)]
    event = {"confirm_idx": 2, "parent_sign": 1, "failure": 95.0, "lower_wave_pos": 0}
    klass, idx = m.candidate_exit(prices, event, waves)
    assert klass == "censored"
    assert idx == len(prices) - 1


def test_entry_validity_is_symmetric_by_parent_direction():
    assert m.entry_valid(100.0, recovery=102.0, failure=98.0, direction=1)
    assert not m.entry_valid(102.0, recovery=102.0, failure=98.0, direction=1)
    assert m.entry_valid(100.0, recovery=98.0, failure=102.0, direction=-1)
    assert not m.entry_valid(98.0, recovery=98.0, failure=102.0, direction=-1)


def test_dev_gate_is_exactly_the_four_preregistered_conditions():
    rows = []
    for year in range(2015, 2021):
        for _ in range(2):
            rows.append(
                {
                    "day": f"{year}-06-01",
                    "entry_invalid": False,
                    "candidate_gross": 0.003,
                    "candidate_net": 0.002,
                    "candidate_win": True,
                    "candidate_exit_class": "parent_aligned_S2_impulse_confirmed",
                    "candidate_holding_bars": 30,
                    "baseline_gross": 0.001,
                    "baseline_net": 0.0,
                    "baseline_win": False,
                    "baseline_holding_bars": 10,
                }
            )
    out = m.summarize(pd.DataFrame(rows))
    assert out["DEV_gate"] == {
        "pooled_candidate_mean_net_gt_zero": True,
        "pooled_candidate_mean_net_gt_pooled_baseline_mean_net": True,
        "pooled_candidate_median_net_gt_zero": True,
        "positive_candidate_mean_net_years_ge_4_of_6": True,
        "passed": True,
    }


def test_runner_has_no_hidden_recent_data_or_certifier_path():
    text = (ROOT / "scripts/run_rmr_R1B_temporal_impulse_completion_dev_v1.py").read_text(encoding="utf-8")
    for forbidden in (
        "gap_fill_repeat_2026",
        "csi1000_1m_2026",
        "reusable_blackbox_query_ledger",
        "certify_rmr_",
        "optuna",
    ):
        assert forbidden not in text
