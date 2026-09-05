#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
END = "2020-12-31"

def sha256(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as h:
        for b in iter(lambda: h.read(1024 * 1024), b""):
            d.update(b)
    return d.hexdigest()

def main() -> int:
    man = json.loads((ROOT / "data/manifest.json").read_text())
    assert man["post_2020_rows_included"] is False
    assert man["production_authority"] is False
    for item in man["products"]:
        path = ROOT / item["path"]
        assert path.is_file()
        assert sha256(path) == item["sha256"]
        frame = pd.read_parquet(path)
        col = "trading_day" if "trading_day" in frame.columns else "date"
        days = pd.to_datetime(frame[col]).dt.strftime("%Y-%m-%d")
        assert str(days.max()) <= END
    panel = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    assert panel["gap"].notna().mean() > 0.9
    print("ok", len(man["products"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
