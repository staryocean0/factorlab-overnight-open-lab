#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data/development/csi1000_open_pit_panel.parquet"
CSV_OUT = ROOT / "data/external/shfe_cu_rb_night_endpoints_2015_2020.csv"
PARQUET_OUT = ROOT / "data/development/shfe_cu_rb_night_endpoints.parquet"
MANIFEST_OUT = ROOT / "docs/governance/external_shfe_cu_rb_night_2015_2020_manifest.json"
PACKAGE_MANIFEST = ROOT / "data/manifest.json"
PREREG = ROOT / "docs/governance/global_spillover_v7_domestic_night_preregistration.json"
SCOPE_CORRECTION = ROOT / "docs/governance/global_spillover_v7_domestic_night_holiday_scope_correction.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", default="artifacts/staging/domestic_night_combined")
    args = ap.parse_args()
    indir = ROOT / args.input_dir

    prereg = json.loads(PREREG.read_text())
    correction = json.loads(SCOPE_CORRECTION.read_text())
    if prereg["composite_feature"]["weights"] != {"SHFE_CU": 0.5, "SHFE_RB": 0.5}:
        raise AssertionError("v7 composite weights drift")
    if correction["corrected_event_scope"]["eligible_target_rows"] != "holiday_reopen == 0 only":
        raise AssertionError("v7 ordinary scope drift")

    cu_csv = indir / "shfe_cu_night_endpoints_2015_2020.csv"
    rb_csv = indir / "shfe_rb_night_endpoints_2015_2020.csv"
    cu_man_path = indir / "shfe_cu_night_manifest_2015_2020.json"
    rb_man_path = indir / "shfe_rb_night_manifest_2015_2020.json"
    for p in [cu_csv, rb_csv, cu_man_path, rb_man_path]:
        if not p.is_file():
            raise AssertionError(("missing product artifact", str(p)))
    cu = pd.read_csv(cu_csv)
    rb = pd.read_csv(rb_csv)
    cu["trading_day"] = pd.to_datetime(cu["trading_day"], errors="raise").dt.normalize()
    rb["trading_day"] = pd.to_datetime(rb["trading_day"], errors="raise").dt.normalize()
    if cu["trading_day"].duplicated().any() or rb["trading_day"].duplicated().any():
        raise AssertionError("duplicate product target day")

    cu = cu.add_prefix("cu_").rename(columns={"cu_trading_day": "trading_day", "cu_previous_china_day": "previous_china_day_cu"})
    rb = rb.add_prefix("rb_").rename(columns={"rb_trading_day": "trading_day", "rb_previous_china_day": "previous_china_day_rb"})
    joint = cu.merge(rb, on="trading_day", how="inner", validate="one_to_one")
    if joint.empty:
        raise AssertionError("no joint CU/RB night rows")
    if not pd.to_datetime(joint["previous_china_day_cu"]).equals(pd.to_datetime(joint["previous_china_day_rb"])):
        raise AssertionError("CU/RB previous China day mismatch")
    joint["previous_china_day"] = pd.to_datetime(joint["previous_china_day_cu"]).dt.normalize()
    joint["domestic_night_cyclical_return"] = 0.5 * pd.to_numeric(joint["cu_cu_night_return"], errors="raise") + 0.5 * pd.to_numeric(joint["rb_rb_night_return"], errors="raise")
    joint = joint.drop(columns=["previous_china_day_cu", "previous_china_day_rb"])
    if joint["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 joint endpoint")

    panel = pd.read_parquet(PANEL, columns=["trading_day", "holiday_reopen"]).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    ordinary = (pd.to_numeric(panel["holiday_reopen"], errors="raise") == 0) & panel["trading_day"].between(pd.Timestamp("2015-01-01"), pd.Timestamp("2020-12-31"))
    eligible = panel.loc[ordinary, ["trading_day"]].drop_duplicates().copy()
    joint_days = set(joint["trading_day"])
    coverage = {}
    for label, lo, hi in [
        ("train_2015_2018", pd.Timestamp("2015-01-01"), pd.Timestamp("2018-12-31")),
        ("holdout_2019_2020", pd.Timestamp("2019-01-01"), pd.Timestamp("2020-12-31")),
    ]:
        g = eligible.loc[eligible["trading_day"].between(lo, hi)]
        n = int(len(g)); u = int(g["trading_day"].isin(joint_days).sum())
        coverage[label] = {"events_total": n, "joint_usable": u, "coverage": float(u / n) if n else None}
    if coverage["train_2015_2018"]["coverage"] < 0.80 or coverage["holdout_2019_2020"]["coverage"] < 0.80:
        raise AssertionError(("v7 preregistered joint coverage gate failed", coverage))

    joint = joint.sort_values("trading_day").reset_index(drop=True)
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    csv = joint.copy()
    csv["trading_day"] = csv["trading_day"].dt.strftime("%Y-%m-%d")
    csv["previous_china_day"] = csv["previous_china_day"].dt.strftime("%Y-%m-%d")
    csv.to_csv(CSV_OUT, index=False, float_format="%.12g", lineterminator="\n")
    PARQUET_OUT.parent.mkdir(parents=True, exist_ok=True)
    joint.to_parquet(PARQUET_OUT, index=False)

    cu_man = json.loads(cu_man_path.read_text())
    rb_man = json.loads(rb_man_path.read_text())
    manifest = {
        "schema_id": "external_shfe_cu_rb_night_2015_2020_manifest@1.0",
        "frozen_date": "2026-09-06",
        "scope": "ordinary China target sessions only; both CU and RB must be independently available",
        "source_validation": "docs/governance/domestic_night_shfe_source_validation_receipt.json",
        "volume_integrity": "docs/governance/domestic_night_shfe_volume_integrity_receipt.json",
        "v7_preregistration": str(PREREG.relative_to(ROOT)),
        "holiday_scope_correction": str(SCOPE_CORRECTION.relative_to(ROOT)),
        "composite": "0.5 * cu_night_return + 0.5 * rb_night_return",
        "joint_rows": int(len(joint)),
        "coverage": coverage,
        "products": {"CU": cu_man, "RB": rb_man},
        "assets": {
            str(CSV_OUT.relative_to(ROOT)): {"sha256": sha256_file(CSV_OUT), "bytes": CSV_OUT.stat().st_size},
            str(PARQUET_OUT.relative_to(ROOT)): {"sha256": sha256_file(PARQUET_OUT), "bytes": PARQUET_OUT.stat().st_size},
        },
        "guards": {
            "CSI1000_gap_column_read": false,
            "post_2020_market_fields_parsed": 0,
            "joint_missing_component_renormalization": false,
            "zero_fill_missing_night": false,
            "holiday_rows_in_joint_dataset": 0,
            "DCE_I_included": false,
        },
    }
    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    package = json.loads(PACKAGE_MANIFEST.read_text())
    rel = str(PARQUET_OUT.relative_to(ROOT))
    item = {
        "path": rel,
        "rows": int(len(joint)),
        "bytes": int(PARQUET_OUT.stat().st_size),
        "sha256": sha256_file(PARQUET_OUT),
        "min_day": str(joint["trading_day"].min().date()),
        "max_day": str(joint["trading_day"].max().date()),
    }
    package["products"] = [x for x in package["products"] if x["path"] != rel] + [item]
    PACKAGE_MANIFEST.write_text(json.dumps(package, indent=2) + "\n")
    print(json.dumps({"joint_rows": len(joint), "coverage": coverage, "assets": manifest["assets"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
