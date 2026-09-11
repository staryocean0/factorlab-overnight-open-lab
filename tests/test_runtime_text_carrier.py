from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_runtime_text_carrier as carrier

PACK = ROOT / "data/runtime_text_2015_2025"
FROZEN = ROOT / "data/development/csi1000_open_pit_panel.parquet"
CLOCK_REF = ROOT / "data/development/trend_open_state_dev_pack_2019_2020/minute_clocks_2019_2020.csv"
RECEIPT = ROOT / "docs/research/runtime_text_carrier_parity_receipt_v1.json"
OPEN_YEARS = list(range(2015, 2021))
BLACKBOX_YEARS = list(range(2021, 2026))


def test_committed_pack_has_no_blackbox_shards() -> None:
    assert PACK.is_dir()
    for year in BLACKBOX_YEARS:
        assert not (PACK / f"factor_panel_{year}.csv").exists()
        assert not (PACK / f"opening_clocks_{year}.csv").exists()


def test_committed_factor_panel_parity_2015_2020() -> None:
    report = carrier.verify_factor_parity(
        carrier.load_frozen_factor_panel(FROZEN),
        PACK,
        OPEN_YEARS,
    )
    assert report["status"] == "PASS"
    assert report["row_count"] == 1462


def test_committed_clock_parity_2019_2020() -> None:
    clocks = carrier.load_published_clocks(PACK, OPEN_YEARS)
    report = carrier.verify_clock_parity(
        ROOT / "data/high_open_dev_2015_2025/1m_official.parquet",
        clocks,
        CLOCK_REF,
    )
    assert report["status"] == "PASS"
    assert report["row_count"] == 487


def test_exact_clock_does_not_nearest_match(tmp_path: Path) -> None:
    bars = pd.DataFrame(
        {
            "symbol": ["000852.SH", "000852.SH"],
            "trading_day": ["2019-01-02", "2019-01-02"],
            "timestamp": ["2019-01-02T09:34:00Z", "2019-01-02T10:34:00Z"],
            "close": [100.0, 101.0],
        }
    )
    path = tmp_path / "minutes.parquet"
    bars.to_parquet(path, index=False)
    wide = carrier.extract_exact_clocks(path, pd.Series(["2019-01-02"]))
    assert list(wide["trading_day"]) == ["2019-01-02"]
    for column in carrier.CLOCK_COLUMNS.values():
        assert bool(np.isnan(float(wide.loc[0, column])))


def test_builder_defaults_stop_before_blackbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(ROOT)
    receipt = tmp_path / "receipt.json"
    out_dir = tmp_path / "pack"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_runtime_text_carrier.py",
            "--annotated-panel",
            str(ROOT / "data/high_open_dev_2015_2025/annotated_panel.parquet"),
            "--minute-bars",
            str(ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"),
            "--out-dir",
            str(out_dir),
            "--receipt",
            str(receipt),
        ],
    )
    assert carrier.main() == 0
    for year in OPEN_YEARS:
        assert (out_dir / f"factor_panel_{year}.csv").is_file()
        assert (out_dir / f"opening_clocks_{year}.csv").is_file()
    for year in BLACKBOX_YEARS:
        assert not (out_dir / f"factor_panel_{year}.csv").exists()
        assert not (out_dir / f"opening_clocks_{year}.csv").exists()
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["factor_panel_parity_2015_2020"]["status"] == "PASS"
    assert payload["clock_parity_2019_2020"]["status"] == "PASS"
    assert payload["scientific_change"] is False
    assert payload["blackbox_window_text_shards"]["generated"] is False


def test_builder_refuses_forced_blackbox_text() -> None:
    with pytest.raises(RuntimeError, match="refusing to emit 2021-2025"):
        sys_argv = [
            "build_runtime_text_carrier.py",
            "--emit-blackbox-window-text",
        ]
        old = sys.argv
        sys.argv = sys_argv
        try:
            carrier.main()
        finally:
            sys.argv = old


def test_manifest_and_receipt_flags() -> None:
    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert manifest["purpose"] == "cloud_readable_minimal_runtime_carrier"
    assert manifest["transform"]["scientific_change"] is False
    assert manifest["transform"]["feature_engineering"] is False
    assert manifest["transform"]["forward_fill"] is False
    assert manifest["transform"]["nearest_clock_match"] is False
    assert manifest["years"] == OPEN_YEARS
    assert manifest["withheld_years"] == BLACKBOX_YEARS
    assert receipt["factor_panel_parity_2015_2020"]["status"] == "PASS"
    assert receipt["clock_parity_2019_2020"]["status"] == "PASS"
    assert receipt["blackbox_window_text_shards"]["generated"] is False
    assert receipt["blackbox_window_text_shards"]["committed"] is False
    assert receipt["scientific_change"] is False
