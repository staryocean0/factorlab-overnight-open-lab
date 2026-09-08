from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_rmr_mechanism_to_execution_diagnostic_v1.py"
SPEC = importlib.util.spec_from_file_location("diagnostic_v1", RUNNER_PATH)
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def test_frozen_diagnostic_constants_and_no_selection_surface():
    assert m.COST == 0.0010
    assert m.HORIZON == 1200
    assert m.MARKOUTS == [1, 5, 15, 30, 60, 120, 240]
    assert m.BINS == [0.0, 0.2, 0.4, 0.6, 0.8, 1.0000001]
    assert m.DEV_END == "2020-12-31"
    assert m.VAL_START == "2021-01-01"
    assert m.VAL_END == "2025-12-31"

    text = RUNNER_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "--cost",
        "--horizon",
        "--threshold",
        "--entry-delay",
        "gridsearch",
        "randomizedsearch",
        "optuna",
        "reusable_blackbox_query_ledger",
        "gap_fill_repeat_2026/csi1000",
        "certify_rmr_",
    ):
        assert forbidden not in text


def test_break_even_probability_is_frozen_binary_geometry():
    got = m.break_even_probability(0.010, -0.005)
    assert got == pytest.approx(0.4)
    assert np.isnan(m.break_even_probability(-0.001, -0.002))


def test_next_bar_execution_fields_boundary_accounting():
    prices = np.asarray([100.0, 100.5, 101.0, 101.2], dtype=float)
    row = {"certified_probability": 0.60}
    m.add_execution_fields(
        row=row,
        prices=prices,
        confirm_idx=0,
        resolved=2,
        direction=1,
        target=101.0,
        failure=99.0,
        outcome="recovery",
        restoration_label="recovery",
        failure_label="failure",
    )
    assert row["entry_invalid"] is False
    assert row["entry_idx"] == 1
    assert row["holding_bars"] == 1
    assert row["target_gross"] == pytest.approx(101.0 / 100.5 - 1.0)
    assert row["failure_gross"] == pytest.approx(99.0 / 100.5 - 1.0)
    expected = 0.60 * row["target_gross"] + 0.40 * row["failure_gross"] - 0.0010
    assert row["binary_structural_expected_net_10bp"] == pytest.approx(expected)
    assert row["realized_gross"] == pytest.approx(row["target_gross"])
    assert row["target_overshoot"] == pytest.approx(0.0)
    assert np.isnan(row["failure_overshoot"])
    assert row["target_reward_consumed_fraction"] > 0.0
    assert set(f"markout_{h}" for h in m.MARKOUTS).issubset(row)


def test_next_bar_boundary_cross_is_not_tradeable():
    prices = np.asarray([100.0, 101.5, 101.7], dtype=float)
    row = {"certified_probability": 0.75}
    m.add_execution_fields(
        row=row,
        prices=prices,
        confirm_idx=0,
        resolved=2,
        direction=1,
        target=101.0,
        failure=99.0,
        outcome="recovery",
        restoration_label="recovery",
        failure_label="failure",
    )
    assert row["entry_invalid"] is True
    assert "realized_net" not in row


def test_read_source_rejects_any_2026_rows(monkeypatch, tmp_path):
    fake = pd.DataFrame(
        {
            "symbol": [m.SYMBOL, m.SYMBOL],
            "trading_day": ["2025-12-31", "2026-01-05"],
            "timestamp": ["2025-12-31 15:00:00", "2026-01-05 09:31:00"],
            "close": [100.0, 101.0],
        }
    )
    monkeypatch.setattr(m, "sha256", lambda _: m.EXPECTED_SHA)
    monkeypatch.setattr(m.pd, "read_parquet", lambda *args, **kwargs: fake.copy())
    with pytest.raises(RuntimeError):
        m.read_source(tmp_path / "fake.parquet")


def test_summary_reports_required_fixed_diagnostics_without_filtering():
    rows = []
    for p, net in [(0.10, -0.002), (0.30, -0.001), (0.50, 0.0), (0.70, 0.001), (0.90, 0.002)]:
        row = {
            "entry_invalid": False,
            "realized_net": net,
            "restoration": float(net >= 0),
            "certified_probability": p,
            "target_gross": 0.004,
            "failure_gross": -0.006,
            "reward_loss_abs_ratio": 2.0 / 3.0,
            "break_even_restoration_probability_10bp": 0.7,
            "binary_structural_expected_net_10bp": p * 0.004 + (1 - p) * -0.006 - 0.001,
            "realized_gross": net + 0.001,
            "win": net > 0,
            "censored": False,
            "holding_bars": 30,
            "entry_move_from_confirmation": -0.0002,
            "target_reward_consumed_by_entry": 0.0002,
            "target_reward_consumed_fraction": 0.05,
            "boundary_overshoot": 0.0,
            "target_overshoot": 0.0,
            "failure_overshoot": np.nan,
        }
        for h in m.MARKOUTS:
            row[f"markout_{h}"] = net + 0.001
        rows.append(row)
    out = m.summarize(pd.DataFrame(rows))
    assert out["events"] == 5
    assert out["tradeable"] == 5
    assert out["next_minute_tradeable_fraction"] == 1.0
    assert out["mean_binary_structural_expected_net_10bp"] is not None
    assert len(out["fixed_probability_bins"]) == 5
    assert [x["n"] for x in out["fixed_probability_bins"]] == [1, 1, 1, 1, 1]
    assert out["probability_bin_mean_net_monotonic_non_decreasing"] is True
    for h in m.MARKOUTS:
        assert f"mean_markout_{h}" in out
        assert f"positive_share_markout_{h}" in out
