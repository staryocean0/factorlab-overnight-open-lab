from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_rmr_R5_stage1.py"
PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R5_stage1_protocol_v1.json"

spec = spec_from_file_location("rmr_r5_stage1", RUNNER)
assert spec and spec.loader
mod = module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_protocol_has_exact_three_properties_and_two_scales():
    p = protocol()
    assert set(p["properties"]) == {
        "R5_A_path_efficiency",
        "R5_B_volatility_state_displacement",
        "R5_C_event_density",
    }
    assert p["wave_scales"]["reported_scales"] == ["S1", "S2"]
    assert tuple(mod.PROPERTY_IDS) == (
        "R5_A_path_efficiency",
        "R5_B_volatility_state_displacement",
        "R5_C_event_density",
    )
    assert tuple(mod.SCALES) == ("S1", "S2")


def test_normalization_is_prior_100_only_and_excludes_current():
    values = [float(i) for i in range(1, 102)]
    z = mod.rolling_median_mad_z(values, window=100)
    assert all(v is None for v in z[:100])
    ref = np.asarray(values[:100], dtype=float)
    med = np.median(ref)
    mad = np.median(np.abs(ref - med))
    assert np.isclose(z[100], (values[100] - med) / mad)


def test_path_efficiency_is_one_for_monotone_path_and_below_one_for_chop():
    common = mod.common
    mono = np.array([100.0, 101.0, 102.0, 103.0])
    wave = common.Wave(1, 0, 3, 4, 100.0, 103.0)
    assert np.isclose(mod.wave_path_efficiency(mono, wave), 1.0)
    chop = np.array([100.0, 102.0, 101.0, 103.0])
    assert 0.0 < mod.wave_path_efficiency(chop, wave) < 1.0


def test_volatility_ratio_uses_past_path_ending_at_confirmation():
    x = np.linspace(0.0, 0.02, 300)
    x[-30:] += 0.002 * np.sin(np.arange(30))
    ratio = mod.volatility_ratio(x, 299)
    assert np.isfinite(ratio)
    assert ratio > 0.0


def test_event_density_counts_confirmations_in_trailing_240_bars():
    confirms = [10, 100, 200, 260, 300]
    density, duration = mod.event_density(confirms, 4)
    assert np.isclose(density, 4 / 240)
    assert duration == 40


def test_first_passage_reversion_and_extension_are_symmetric():
    prices = np.array([100.0, 99.0, 98.0, 101.0])
    outcome, end = mod.first_passage_close(prices, 0, 1, 0.01, horizon=3)
    assert outcome == "reversion"
    assert end == 1
    prices2 = np.array([100.0, 101.5, 99.0])
    outcome2, end2 = mod.first_passage_close(prices2, 0, 1, 0.01, horizon=2)
    assert outcome2 == "extension"
    assert end2 == 1


def test_protocol_reserve_and_search_boundaries_are_fail_closed():
    p = protocol()
    assert p["source"]["read_through"] == "2022-12-31"
    assert p["source"]["reserve_2023_2025_open"] is False
    assert p["normalization"]["reference_window"] == 100
    assert p["model_comparison"]["hyperparameter_search"] is False
    assert p["model_comparison"]["binary_threshold"] is None
    text = json.dumps(p)
    for phrase in [
        "read_2023_2025_reserve",
        "add_fourth_property",
        "search_z_threshold",
        "search_wave_scale",
        "use_trading_return_or_PnL",
    ]:
        assert phrase in text
    source = RUNNER.read_text(encoding="utf-8")
    assert '"2026_rows_loaded": False' in source
    assert '"trading_return_used": False' in source
