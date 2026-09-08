from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_rmr_stage1_common_probe as probe


def test_directional_change_waves_are_confirmed_after_extreme():
    pattern = np.tile([0.001] * 8 + [-0.001] * 8, 30)
    prices = 100.0 * np.exp(np.cumsum(np.r_[0.0, pattern]))
    waves = probe.detect_waves(prices, 0.004)
    assert len(waves) > 10
    assert {w.direction for w in waves} == {-1, 1}
    assert all(w.confirm_idx > w.end_idx >= w.start_idx for w in waves)
    assert all(a.confirm_idx <= b.confirm_idx for a, b in zip(waves, waves[1:]))


def test_parent_scores_make_range_and_trend_distinguishable_without_hard_threshold():
    prices = np.array([100, 110, 101, 120, 119], dtype=float)
    up1 = probe.Wave(1, 0, 1, 2, 100.0, 110.0)
    down = probe.Wave(-1, 1, 2, 3, 110.0, 101.0)
    trend = probe.parent_features(up1, probe.Wave(1, 2, 3, 4, 101.0, 120.0), prices)
    range_like = probe.parent_features(up1, down, prices)
    assert trend["abs_drift"] > range_like["abs_drift"]
    assert range_like["overlap"] > 0.0


def test_first_passage_is_structural_and_censored_when_neither_boundary_hits():
    prices = np.array([100.0, 101.0, 102.0, 103.0])
    outcome, idx = probe.first_passage(prices, 0, recovery=102.0, failure=98.0, parent_sign=1, horizon=3)
    assert outcome == "recovery" and idx == 2
    outcome, _ = probe.first_passage(prices, 0, recovery=110.0, failure=90.0, parent_sign=1, horizon=3)
    assert outcome == "censored"


def test_r3_state_uses_previous_close_not_same_day_future_path():
    # Parent waves are confirmed well before each daily close. The function must
    # look up the state at the prior close index, not the current close.
    rows = []
    idx = 0
    for day_no in range(30):
        day = f"2019-01-{day_no + 1:02d}" if day_no < 28 else f"2019-02-{day_no - 27:02d}"
        for clock, close in [("09:31", 100 + day_no), ("15:00", 100.5 + day_no)]:
            rows.append({"symbol": "000852.SH", "trading_day": day, "timestamp": f"{day}T{clock}:00Z", "close": close, "_idx": idx})
            idx += 1
    frame = pd.DataFrame(rows)
    prices = frame.close.to_numpy(float)
    waves = [
        probe.Wave(1, 0, 5, 6, prices[0], prices[5]),
        probe.Wave(-1, 5, 10, 11, prices[5], prices[10]),
        probe.Wave(1, 10, 20, 21, prices[10], prices[20]),
        probe.Wave(-1, 20, 30, 31, prices[20], prices[30]),
    ]
    out = probe.daily_frame(frame, prices, waves)
    assert not out.empty
    assert set(["signed_drift", "parent_eff", "short_parent_vol"]).issubset(out.columns)


def test_frozen_boundaries_do_not_open_program_reserve():
    assert probe.DEV_END == "2019-12-31"
    assert probe.STAB_START == "2020-01-01"
    assert probe.STAB_END == "2022-12-31"
    assert probe.HORIZON_BARS == 1200
    assert probe.EXPECTED_SHA == "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
