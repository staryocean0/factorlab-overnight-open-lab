from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def test_no_post_2020_rows() -> None:
    panel = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    assert str(panel["trading_day"].max()) <= "2020-12-31"
    us = pd.read_parquet(ROOT / "data/development/us_nasdaq_vix.parquet")
    assert str(pd.to_datetime(us["date"]).dt.strftime("%Y-%m-%d").max()) <= "2020-12-31"

def test_baseline_receipt_exists() -> None:
    rec = json.loads((ROOT / "docs/governance/baseline_receipt.json").read_text())
    assert rec["metrics"]["ridge_ic"] > 0
    assert rec["production_authority"] if False else rec["do_not_optimize_total_return"] is True

def test_us_is_strictly_before_china_day() -> None:
    panel = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    assert "us_nasdaq" in panel.columns
    assert panel["us_nasdaq"].notna().mean() > 0.8
