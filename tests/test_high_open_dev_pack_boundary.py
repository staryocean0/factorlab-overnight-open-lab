from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data/high_open_dev_2015_2025"


def test_high_open_dev_pack_excludes_2026() -> None:
    manifest = json.loads((PACK / "manifest.json").read_text())
    assert manifest["window"] == {"start": "2015-01-05", "end": "2025-12-31"}
    assert manifest["2026_rows_included"] is False
    assert manifest["2026_blackbox_opened"] is False
    assert manifest["post_2026-08-21_included"] is False
    assert manifest["production_authority"] is False
    assert manifest["does_not_replace_frozen_2015_2020_pack"] is True

    annotated = pd.read_parquet(PACK / "annotated_panel.parquet")
    minutes = pd.read_parquet(PACK / "1m_official.parquet")
    nasdaq = pd.read_csv(PACK / "fred_nasdaq.csv")
    vix = pd.read_csv(PACK / "fred_vix.csv")

    assert str(annotated["trading_day"].min()) == "2015-01-05"
    assert str(annotated["trading_day"].max()) == "2025-12-31"
    assert int((pd.to_datetime(annotated["trading_day"]).dt.year >= 2026).sum()) == 0
    assert len(annotated) == 2674

    assert set(minutes["symbol"].unique()) == {"000852.SH"}
    assert str(minutes["trading_day"].min()) == "2015-01-05"
    assert str(minutes["trading_day"].max()) == "2025-12-31"
    assert int((pd.to_datetime(minutes["trading_day"]).dt.year >= 2026).sum()) == 0

    assert str(nasdaq["observation_date"].max()) == "2025-12-31"
    assert str(vix["observation_date"].max()) == "2025-12-31"
    assert int((nasdaq["observation_date"] >= "2026-01-01").sum()) == 0
    assert int((vix["observation_date"] >= "2026-01-01").sum()) == 0

    frozen = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    assert str(frozen["trading_day"].max()) == "2020-12-31"


def test_source_resolver_falls_back_to_dev_pack(tmp_path, monkeypatch) -> None:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import evaluate_local_2021_2025_two_head as local

    missing = tmp_path / "does-not-exist.parquet"
    resolved = local.resolve_source(
        "OVERNIGHT_ANNOTATED_PANEL_TEST_UNSET",
        missing,
        "data/high_open_dev_2015_2025/annotated_panel.parquet",
    )
    assert resolved == ROOT / "data/high_open_dev_2015_2025/annotated_panel.parquet"
    monkeypatch.delenv("OVERNIGHT_ANNOTATED_PANEL_TEST_UNSET", raising=False)
