#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_OUT = ROOT / "data/external/fred_us_nasdaq_vix_2014_2020.csv"
PARQUET_OUT = ROOT / "data/development/us_nasdaq_vix.parquet"
MANIFEST_OUT = ROOT / "docs/governance/external_us_fred_2014_2020_manifest.json"
START = pd.Timestamp("2014-01-01")
END = pd.Timestamp("2020-12-31")
URLS = {
    "NASDAQCOM": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM&cosd=2014-01-01&coed=2020-12-31",
    "VIXCLS": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&cosd=2014-01-01&coed=2020-12-31",
}


def _load_series(name: str, url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    if "observation_date" not in df.columns or name not in df.columns:
        raise AssertionError((name, list(df.columns)))
    out = df[["observation_date", name]].copy()
    out["date"] = pd.to_datetime(out.pop("observation_date"), errors="raise").dt.normalize()
    out[name] = pd.to_numeric(out[name], errors="coerce")
    out = out.loc[(out["date"] >= START) & (out["date"] <= END)].copy()
    if out.empty:
        raise AssertionError(f"FRED returned no rows for {name}")
    if out["date"].duplicated().any():
        raise AssertionError(f"duplicate dates for {name}")
    return out.sort_values("date").reset_index(drop=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    nas = _load_series("NASDAQCOM", URLS["NASDAQCOM"])
    vix = _load_series("VIXCLS", URLS["VIXCLS"])
    df = nas.merge(vix, on="date", how="outer", validate="one_to_one").sort_values("date")
    df = df.loc[(df["date"] >= START) & (df["date"] <= END)].reset_index(drop=True)
    df["nasdaq_observed"] = df["NASDAQCOM"].notna()
    df["vix_observed"] = df["VIXCLS"].notna()
    df["joint_observed"] = df["nasdaq_observed"] & df["vix_observed"]

    if df["date"].min() != START:
        raise AssertionError(("unexpected min date", df["date"].min()))
    if df["date"].max() != END:
        raise AssertionError(("unexpected max date", df["date"].max()))
    if bool((df["date"] > END).any()):
        raise AssertionError("post-2020 row detected")

    # Calendar sentinels: retain U.S. market holidays as explicit missing observations.
    indexed = df.set_index("date")
    for holiday in ["2014-01-01", "2019-01-01", "2020-01-01", "2020-12-25"]:
        d = pd.Timestamp(holiday)
        if d not in indexed.index:
            raise AssertionError(("expected holiday row missing", holiday))
        if bool(indexed.loc[d, "joint_observed"]):
            raise AssertionError(("expected holiday unexpectedly observed", holiday))
    for session in ["2018-12-26", "2018-12-28", "2019-01-02", "2020-01-02", "2020-12-31"]:
        d = pd.Timestamp(session)
        if d not in indexed.index or not bool(indexed.loc[d, "joint_observed"]):
            raise AssertionError(("expected U.S. session missing", session))

    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    raw = df.copy()
    raw["date"] = raw["date"].dt.strftime("%Y-%m-%d")
    raw.to_csv(RAW_OUT, index=False, float_format="%.10g", lineterminator="\n")

    PARQUET_OUT.parent.mkdir(parents=True, exist_ok=True)
    pq = df[["date", "NASDAQCOM", "VIXCLS"]].copy()
    pq.to_parquet(PARQUET_OUT, index=False)

    manifest = {
        "schema_id": "external_us_fred_manifest@1.0",
        "frozen_retrieval_date": "2026-09-05",
        "window": [str(START.date()), str(END.date())],
        "provider": "Federal Reserve Bank of St. Louis FRED",
        "series": {
            "NASDAQCOM": {
                "source_url": URLS["NASDAQCOM"],
                "reported_source": "Nasdaq, Inc.",
                "frequency": "Daily, Close"
            },
            "VIXCLS": {
                "source_url": URLS["VIXCLS"],
                "reported_source": "Chicago Board Options Exchange",
                "frequency": "Daily, Close"
            }
        },
        "calendar_semantics": "Rows with missing observations are retained in the raw CSV; research trading sessions are nonmissing observations only; no forward fill.",
        "row_counts": {
            "calendar_rows": int(len(df)),
            "nasdaq_observed": int(df["nasdaq_observed"].sum()),
            "vix_observed": int(df["vix_observed"].sum()),
            "joint_observed": int(df["joint_observed"].sum()),
            "joint_missing": int((~df["joint_observed"]).sum())
        },
        "assets": {
            str(RAW_OUT.relative_to(ROOT)): {"sha256": _sha256(RAW_OUT)},
            str(PARQUET_OUT.relative_to(ROOT)): {"sha256": _sha256(PARQUET_OUT)}
        },
        "guards": {
            "post_2020_rows": 0,
            "holiday_rows_retained": True,
            "forward_fill": False
        }
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
