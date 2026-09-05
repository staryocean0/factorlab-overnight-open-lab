#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
SELECTION_PREREG = ROOT / "docs/governance/domestic_night_causal_contract_selection_preregistration.json"
SAMPLE_FREEZE = ROOT / "docs/governance/domestic_night_source_crosscheck_sample_freeze.json"
SOURCE_RECEIPT = ROOT / "docs/governance/domestic_night_shfe_source_validation_receipt.json"
OUT = ROOT / "artifacts/research/domestic_night_shfe_volume_integrity_results.json"

BASE_SPEC = importlib.util.spec_from_file_location(
    "night_base", ROOT / "scripts/audit_domestic_night_source_crosscheck.py"
)
base = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(base)

MIGRATED_SPEC = importlib.util.spec_from_file_location(
    "night_shfe", ROOT / "scripts/audit_domestic_night_shfe_migrated_crosscheck.py"
)
shfe = importlib.util.module_from_spec(MIGRATED_SPEC)
assert MIGRATED_SPEC.loader is not None
MIGRATED_SPEC.loader.exec_module(shfe)


def select_exchange_trading_day_rows(df: pd.DataFrame, day: pd.Timestamp, product: str) -> pd.DataFrame:
    """Reproduce the already-validated exchange-day clock and expose selected rows.

    This deliberately mirrors base.aggregate_trading_day rather than introducing a
    second clock implementation with different economics.
    """
    day = pd.Timestamp(day).normalize()
    end_hhmmss, crosses_midnight = base.clock_for(product, day)
    dates = df["datetime"].dt.normalize()
    times = df["datetime"].dt.strftime("%H%M%S")

    earlier = df.loc[
        (dates < day)
        & (dates >= day - pd.Timedelta(days=4))
        & (times >= "210000")
    ]
    night_date = earlier["datetime"].dt.normalize().max() if not earlier.empty else None

    pieces: list[pd.DataFrame] = []
    if night_date is not None:
        nd = dates == night_date
        if crosses_midnight:
            pieces.append(df.loc[nd & (times >= "210000")].copy())
        else:
            pieces.append(df.loc[nd & (times >= "210000") & (times <= end_hhmmss)].copy())
    if crosses_midnight:
        pieces.append(df.loc[(dates == day) & (times <= end_hhmmss)].copy())
    daybars = df.loc[(dates == day) & (times >= "090000") & (times <= "150000")].copy()
    pieces.append(daybars)

    nonempty = [p for p in pieces if not p.empty]
    if not nonempty or daybars.empty:
        return df.iloc[0:0].copy()
    selected = pd.concat(nonempty, ignore_index=True).sort_values("datetime").reset_index(drop=True)

    invalid: list[str] = []
    for ts in selected["datetime"]:
        ts = pd.Timestamp(ts)
        t, d = ts.strftime("%H%M%S"), ts.normalize()
        valid = d == day and "090000" <= t <= "150000"
        valid = valid or (
            night_date is not None
            and d == night_date
            and t >= "210000"
            and (crosses_midnight or t <= end_hhmmss)
        )
        valid = valid or (crosses_midnight and d == day and t <= end_hhmmss)
        if not valid:
            invalid.append(str(ts))
    if invalid:
        raise AssertionError(("volume gate selected bars outside frozen clock", product, str(day.date()), invalid[:10]))
    return selected


def transport_volume_summary(df: pd.DataFrame, day: pd.Timestamp, product: str) -> dict[str, Any] | None:
    selected = select_exchange_trading_day_rows(df, day, product)
    if selected.empty:
        return None
    volume = pd.to_numeric(selected["volume"], errors="raise")
    if (volume < 0).any() or not np.isfinite(volume.to_numpy(dtype=float)).all():
        raise AssertionError("invalid selected volume")
    return {
        "trading_day": str(pd.Timestamp(day).date()),
        "selected_bar_count": int(len(selected)),
        "zero_volume_bar_count": int((volume == 0).sum()),
        "positive_volume_bar_count": int((volume > 0).sum()),
        "first_selected_datetime": str(selected["datetime"].min()),
        "last_selected_datetime": str(selected["datetime"].max()),
        "transport_volume_sum": float(volume.sum()),
    }


def _systematic_scale_detected(samples: list[dict[str, Any]]) -> dict[str, Any]:
    mismatches = [s for s in samples if s.get("official_volume") not in (None, 0) and not s.get("exact_volume_match", False)]
    ratios = [float(s["transport_volume_sum"] / s["official_volume"]) for s in mismatches]
    systematic = False
    if len(ratios) >= 2:
        spread = max(ratios) - min(ratios)
        systematic = bool(spread <= 1e-9 and abs(float(np.median(ratios)) - 1.0) > 1e-9)
    return {
        "mismatch_count": len(mismatches),
        "mismatch_ratios": ratios,
        "repeated_exact_scale_ratio_detected": systematic,
    }


def evaluate_sample(product: str, anchor_s: str, cfg: dict[str, Any], expected_official_sha: str) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 factorlab-shfe-volume-integrity", "Accept": "*/*"})
    raw_url = base.RAW_BASE.format(path=cfg["path"])
    try:
        transport_raw, transport_http = shfe.get_bytes(session, raw_url)
        df, transport_parse = base.parse_transport(transport_raw, cfg["git_blob_sha"])
    except Exception as exc:
        return {
            "anchor_date": anchor_s,
            "contract": cfg["contract"],
            "sample_pass": False,
            "unavailable": True,
            "failure_class": "transport_infrastructure_or_schema",
            "error": repr(exc),
        }

    day = pd.Timestamp(anchor_s)
    summary = transport_volume_summary(df, day, product)
    if summary is None:
        return {
            "anchor_date": anchor_s,
            "contract": cfg["contract"],
            "sample_pass": False,
            "unavailable": True,
            "failure_class": "transport_trading_day_unavailable",
            "transport_file_validation": {"http": transport_http, **transport_parse},
        }

    official = shfe.fetch_official_shfe(session, day, cfg["contract"])
    if not official.get("ok"):
        return {
            "anchor_date": anchor_s,
            "contract": cfg["contract"],
            "sample_pass": False,
            "unavailable": True,
            "failure_class": official.get("failure_class", "official_unavailable"),
            "transport_file_validation": {"http": transport_http, **transport_parse},
            "transport_volume": summary,
            "official": official,
        }
    actual_official_sha = official["response"]["sha256"]
    if actual_official_sha != expected_official_sha:
        raise AssertionError(("historical SHFE official response drift", anchor_s, cfg["contract"], actual_official_sha, expected_official_sha))
    official_volume = official["values"].get("volume")
    if official_volume is None or not np.isfinite(float(official_volume)):
        return {
            "anchor_date": anchor_s,
            "contract": cfg["contract"],
            "sample_pass": False,
            "unavailable": True,
            "failure_class": "official_volume_missing_or_non_numeric",
            "transport_file_validation": {"http": transport_http, **transport_parse},
            "transport_volume": summary,
            "official": official,
        }

    transport_volume = float(summary["transport_volume_sum"])
    official_volume = float(official_volume)
    diff = transport_volume - official_volume
    exact = bool(diff == 0.0)
    ratio = float(transport_volume / official_volume) if official_volume != 0 else None
    return {
        "anchor_date": anchor_s,
        "chosen_date": anchor_s,
        "contract": cfg["contract"],
        "path": cfg["path"],
        "frozen_git_blob_sha": cfg["git_blob_sha"],
        "transport_file_validation": {"http": transport_http, **transport_parse},
        "transport_volume": summary,
        "transport_volume_sum": transport_volume,
        "official_volume": official_volume,
        "official_response_sha256": actual_official_sha,
        "difference": diff,
        "ratio_transport_to_official": ratio,
        "exact_volume_match": exact,
        "sample_pass": exact,
        "unavailable": False,
    }


def main() -> None:
    selection = json.loads(SELECTION_PREREG.read_text())
    freeze = json.loads(SAMPLE_FREEZE.read_text())
    receipt = json.loads(SOURCE_RECEIPT.read_text())

    if selection["status"] != "result_free_with_respect_to_volume_integrity_audit_and_all_CSI1000_target_metrics":
        raise AssertionError("volume-integrity gate was not frozen result-free")
    if selection["required_volume_integrity_gate_before_bulk_selection"]["tolerance"] != 0.0:
        raise AssertionError("volume gate tolerance drift")
    if not receipt["adjudication"]["SHFE_CU_transport_admitted"] or not receipt["adjudication"]["SHFE_RB_transport_admitted"]:
        raise AssertionError("SHFE price transport not admitted before volume gate")
    if receipt["data_boundary"]["CSI1000_target_rows_read"] != 0:
        raise AssertionError("source validation unexpectedly consumed CSI1000 targets")

    receipt_by_product = {"SHFE_CU": receipt["SHFE_CU"], "SHFE_RB": receipt["SHFE_RB"]}
    products: dict[str, Any] = {}
    for product in ["SHFE_CU", "SHFE_RB"]:
        frozen = freeze["sample_design"]["products"][product]["contracts_by_date"]
        prior_samples = {s["date"]: s for s in receipt_by_product[product]["samples"]}
        rows: list[dict[str, Any]] = []
        for anchor_s in sorted(frozen):
            if anchor_s not in prior_samples:
                raise AssertionError(("source receipt sample missing", product, anchor_s))
            prior = prior_samples[anchor_s]
            if prior["contract"] != frozen[anchor_s]["contract"]:
                raise AssertionError(("source receipt contract drift", product, anchor_s))
            rows.append(evaluate_sample(product, anchor_s, frozen[anchor_s], prior["official_response_sha256"]))
        pass_count = sum(bool(r.get("sample_pass")) for r in rows)
        scale = _systematic_scale_detected(rows)
        unresolved_clock_or_scale = bool(scale["repeated_exact_scale_ratio_detected"])
        product_pass = bool(pass_count >= 2 and not unresolved_clock_or_scale)
        products[product] = {
            "samples": rows,
            "sample_pass_count": int(pass_count),
            "sample_total": len(rows),
            "systematic_scale_diagnostic": scale,
            "product_pass": product_pass,
        }

    gate_pass = all(products[p]["product_pass"] for p in ["SHFE_CU", "SHFE_RB"])
    report = {
        "schema_id": "overnight_open_domestic_night_shfe_volume_integrity_results@1.0",
        "selection_preregistration": str(SELECTION_PREREG.relative_to(ROOT)),
        "source_validation_receipt": str(SOURCE_RECEIPT.relative_to(ROOT)),
        "data_boundary": {
            "CSI1000_target_rows_read": 0,
            "predictive_model_execution": False,
            "post_2020_transport_rows_read": 0,
        },
        "measurement": "sum pinned 5-minute volume over the already-validated exchange trading-day clock and compare to exact-contract SHFE official daily VOLUME",
        "tolerance": 0.0,
        "products": products,
        "adjudication": {
            "SHFE_CU_pass": bool(products["SHFE_CU"]["product_pass"]),
            "SHFE_RB_pass": bool(products["SHFE_RB"]["product_pass"]),
            "volume_integrity_gate_pass": bool(gate_pass),
            "scientific_status": "CU_RB_volume_ranking_contract_selection_admitted_for_separate_predictive_preregistration" if gate_pass else "volume_ranking_contract_selection_not_admitted",
        },
        "forbidden_post_result_actions": [
            "rescale transport volume",
            "multiply or divide by two to force reconciliation",
            "change trading-day allocation",
            "switch products or sample dates",
            "read CSI1000 target metrics to choose a repair",
        ],
        "authority": {
            "predictive_model_execution": False,
            "fresh_oos": False,
            "baseline_replacement": False,
            "production": False,
            "registry_mutation": False,
            "merge_main": False,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({
        "SHFE_CU_pass": report["adjudication"]["SHFE_CU_pass"],
        "SHFE_RB_pass": report["adjudication"]["SHFE_RB_pass"],
        "volume_integrity_gate_pass": report["adjudication"]["volume_integrity_gate_pass"],
        "CU_matches": products["SHFE_CU"]["sample_pass_count"],
        "RB_matches": products["SHFE_RB"]["sample_pass_count"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
