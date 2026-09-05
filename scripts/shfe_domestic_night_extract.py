#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests

PINNED_COMMIT = "1a402721d639432875504a343e2b9ffe9508cd36"
PINNED_TREE = "0bfff729be22e053f259eeda48adff85b0105f0d"
TREE_URL = f"https://api.github.com/repos/Freddy-Hexas/china-futures-5min-2015-2025/git/trees/{PINNED_TREE}?recursive=1"
RAW_BASE = f"https://raw.githubusercontent.com/Freddy-Hexas/china-futures-5min-2015-2025/{PINNED_COMMIT}/{{path}}"
END = pd.Timestamp("2020-12-31 23:59:59")
START = pd.Timestamp("2015-01-01 00:00:00")
RB_QUARANTINE_START = pd.Timestamp("2016-04-26")
RB_QUARANTINE_END = pd.Timestamp("2016-05-03")


@dataclass(frozen=True)
class SourceFile:
    product: str
    contract: str
    delivery_year: int
    delivery_month: int
    path: str
    blob_sha: str
    size: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def contract_delivery(contract: str, product: str) -> tuple[int, int]:
    m = re.fullmatch(rf"{re.escape(product.upper())}(\d{{2}})(\d{{2}})", contract.upper())
    if not m:
        raise ValueError(("unexpected contract code", product, contract))
    year = 2000 + int(m.group(1))
    month = int(m.group(2))
    if not 1 <= month <= 12:
        raise ValueError(("invalid delivery month", contract))
    return year, month


def enumerate_source_files(tree_payload: dict[str, Any], product: str) -> list[SourceFile]:
    product = product.upper()
    prefix = f"5min/SHFE/{product}/"
    out: list[SourceFile] = []
    for item in tree_payload.get("tree", []):
        path = str(item.get("path", ""))
        if item.get("type") != "blob" or not path.startswith(prefix) or not path.endswith(".csv"):
            continue
        contract = Path(path).stem.upper()
        try:
            year, month = contract_delivery(contract, product)
        except ValueError:
            continue
        # A December-2020 selection can legitimately choose a 2021 delivery.
        # Contracts beyond 2021 cannot be the nearest listed horizon required by
        # this bounded experiment and are excluded before any market bytes are fetched.
        if (year, month) < (2015, 1) or (year, month) > (2021, 12):
            continue
        out.append(SourceFile(product, contract, year, month, path, str(item["sha"]), int(item.get("size", 0))))
    if not out:
        raise AssertionError(("no source files enumerated", product))
    return sorted(out, key=lambda x: (x.delivery_year, x.delivery_month, x.contract))


def fetch_json(session: requests.Session, url: str) -> dict[str, Any]:
    last: Exception | None = None
    for attempt in range(4):
        try:
            r = session.get(url, timeout=60)
            if r.status_code != 200:
                raise RuntimeError(("http", r.status_code, url, r.text[:120]))
            payload = r.json()
            if not isinstance(payload, dict):
                raise RuntimeError("unexpected JSON payload")
            return payload
        except Exception as exc:
            last = exc
            time.sleep(1 + attempt)
    assert last is not None
    raise last


def fetch_raw(session: requests.Session, source: SourceFile) -> tuple[bytes, dict[str, Any]]:
    url = RAW_BASE.format(path=source.path)
    last: Exception | None = None
    for attempt in range(4):
        try:
            r = session.get(url, timeout=90)
            if r.status_code != 200:
                raise RuntimeError(("http", r.status_code, url, r.text[:120]))
            raw = r.content
            actual = git_blob_sha(raw)
            if actual != source.blob_sha:
                raise AssertionError(("Git blob identity mismatch", source.path, actual, source.blob_sha))
            return raw, {"url": url, "bytes": len(raw), "git_blob_sha": actual, "sha256": sha256_bytes(raw)}
        except Exception as exc:
            last = exc
            time.sleep(1 + attempt)
    assert last is not None
    raise last


def _parse_timestamp_prefix(line: str) -> pd.Timestamp:
    first = line.split(",", 1)[0].strip()
    return pd.Timestamp(first)


def parse_bounded_contract(raw: bytes, expected_blob_sha: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    if git_blob_sha(raw) != expected_blob_sha:
        raise AssertionError("bounded parser blob mismatch")
    text = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8-sig", errors="strict", newline="")
    header_line = text.readline().rstrip("\r\n")
    header = next(csv.reader([header_line]))
    expected = ["datetime", "open", "high", "low", "close", "volume", "money", "open_interest"]
    if header != expected:
        raise AssertionError(("unexpected transport schema", header))

    rows: list[list[str]] = []
    post_2020_boundary_timestamp: str | None = None
    prior_ts: pd.Timestamp | None = None
    for line in text:
        if not line.strip():
            continue
        # Parse only the datetime field first. If the sorted contract file has
        # crossed the 2020 boundary, stop before CSV-tokenizing/parsing OHLCV.
        ts = _parse_timestamp_prefix(line)
        if prior_ts is not None and ts < prior_ts:
            raise AssertionError(("contract rows not time-sorted", str(prior_ts), str(ts)))
        prior_ts = ts
        if ts > END:
            post_2020_boundary_timestamp = str(ts)
            break
        if ts < START:
            continue
        row = next(csv.reader([line]))
        if len(row) != len(expected):
            raise AssertionError(("unexpected row width", len(row), row[:2]))
        rows.append(row)

    df = pd.DataFrame(rows, columns=expected)
    if df.empty:
        return df, {
            "bounded_rows": 0,
            "post_2020_boundary_timestamp": post_2020_boundary_timestamp,
            "post_2020_market_fields_parsed": 0,
        }
    df["datetime"] = pd.to_datetime(df["datetime"], errors="raise")
    for col in ["open", "high", "low", "close", "volume", "open_interest"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
    if df["datetime"].max() > END:
        raise AssertionError("post-2020 parsed row")
    bad = (
        (df["low"] > df["open"]) | (df["low"] > df["close"])
        | (df["high"] < df["open"]) | (df["high"] < df["close"])
        | (df["low"] > df["high"])
    )
    if bad.any():
        raise AssertionError("OHLC inequality failure")
    if (df["volume"] < 0).any() or (df["open_interest"] < 0).any():
        raise AssertionError("negative volume/open_interest")
    duplicated = df[df["datetime"].duplicated(keep=False)]
    exact_duplicate_groups = 0
    if not duplicated.empty:
        compare_cols = [c for c in df.columns if c != "datetime"]
        for _, group in duplicated.groupby("datetime"):
            if len(group[compare_cols].drop_duplicates()) != 1:
                raise AssertionError("conflicting duplicate contract-datetime rows")
            exact_duplicate_groups += 1
        df = df.drop_duplicates().reset_index(drop=True)
    return df.sort_values("datetime").reset_index(drop=True), {
        "bounded_rows": int(len(df)),
        "min_datetime": str(df["datetime"].min()),
        "max_datetime": str(df["datetime"].max()),
        "zero_volume_rows": int((df["volume"] == 0).sum()),
        "exact_duplicate_groups_collapsed": int(exact_duplicate_groups),
        "post_2020_boundary_timestamp": post_2020_boundary_timestamp,
        "post_2020_market_fields_parsed": 0,
    }


def daytime_stats(df: pd.DataFrame) -> dict[pd.Timestamp, dict[str, Any]]:
    if df.empty:
        return {}
    dates = df["datetime"].dt.normalize()
    times = df["datetime"].dt.strftime("%H%M%S")
    mask = (times >= "090000") & (times <= "145500")
    work = df.loc[mask].copy()
    if work.empty:
        return {}
    work["day"] = work["datetime"].dt.normalize()
    out: dict[pd.Timestamp, dict[str, Any]] = {}
    for day, group in work.groupby("day"):
        group = group.sort_values("datetime")
        exact_start = group.loc[group["datetime"].dt.strftime("%H%M%S") == "145500"]
        out[pd.Timestamp(day)] = {
            "observed_bar_count": int(len(group)),
            "day_volume_0900_1455": float(group["volume"].sum()),
            "start_1455_close": float(exact_start.iloc[-1]["close"]) if not exact_start.empty else None,
            "start_1455_volume": float(exact_start.iloc[-1]["volume"]) if not exact_start.empty else None,
        }
    return out


def _night_window_mask(df: pd.DataFrame, previous_day: pd.Timestamp, product: str) -> pd.Series:
    previous_day = pd.Timestamp(previous_day).normalize()
    dates = df["datetime"].dt.normalize()
    times = df["datetime"].dt.strftime("%H%M%S")
    if product == "CU":
        return ((dates == previous_day) & (times >= "210000")) | (
            (dates == previous_day + pd.Timedelta(days=1)) & (times <= "010000")
        )
    if product == "RB":
        if RB_QUARANTINE_START <= previous_day <= RB_QUARANTINE_END:
            return pd.Series(False, index=df.index)
        if previous_day < RB_QUARANTINE_START:
            return ((dates == previous_day) & (times >= "210000")) | (
                (dates == previous_day + pd.Timedelta(days=1)) & (times <= "010000")
            )
        return (dates == previous_day) & (times >= "210000") & (times <= "230000")
    raise KeyError(product)


def night_stats(df: pd.DataFrame, previous_days: Iterable[pd.Timestamp], product: str) -> dict[pd.Timestamp, dict[str, Any]]:
    out: dict[pd.Timestamp, dict[str, Any]] = {}
    for previous_day in previous_days:
        previous_day = pd.Timestamp(previous_day).normalize()
        if product == "RB" and RB_QUARANTINE_START <= previous_day <= RB_QUARANTINE_END:
            out[previous_day] = {"quarantined": True, "positive_volume_bar_count": 0, "night_end_datetime": None, "night_end_close": None}
            continue
        mask = _night_window_mask(df, previous_day, product)
        window = df.loc[mask].sort_values("datetime")
        positive = window.loc[window["volume"] > 0].copy()
        if positive.empty:
            out[previous_day] = {"quarantined": False, "positive_volume_bar_count": 0, "night_end_datetime": None, "night_end_close": None}
        else:
            last = positive.iloc[-1]
            out[previous_day] = {
                "quarantined": False,
                "positive_volume_bar_count": int(len(positive)),
                "night_end_datetime": str(last["datetime"]),
                "night_end_close": float(last["close"]),
            }
    return out


def choose_contract(candidates: list[dict[str, Any]], previous_day: pd.Timestamp) -> dict[str, Any] | None:
    previous_day = pd.Timestamp(previous_day).normalize()
    floor = (previous_day.year, previous_day.month)
    eligible = [
        x for x in candidates
        if (int(x["delivery_year"]), int(x["delivery_month"])) >= floor
        and int(x["observed_bar_count"]) > 0
    ]
    if not eligible:
        return None
    return sorted(
        eligible,
        key=lambda x: (
            -float(x["day_volume_0900_1455"]),
            int(x["delivery_year"]),
            int(x["delivery_month"]),
            str(x["contract"]),
        ),
    )[0]
