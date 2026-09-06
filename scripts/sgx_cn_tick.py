#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import subprocess
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable

import pandas as pd

MONTH = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6, "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
OFFICIAL_TRADE_CODES = {"Y", "T"}


def normalize_price(raw: str) -> float:
    x = float(str(raw).strip())
    if x > 100000:
        x /= 100.0
    if not 1000 <= x <= 50000:
        raise AssertionError(("CN price outside frozen sanity range", raw, x))
    return x


def _norm_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower().lstrip("\ufeff"))


ALIASES = {
    "comm": "commodity",
    "commodity": "commodity",
    "commoditycode": "commodity",
    "contracttype": "contract_type",
    "mthcode": "month_code",
    "monthcode": "month_code",
    "deliverymonth": "month_code",
    "year": "year",
    "deliveryyear": "year",
    "strike": "strike",
    "strikeprice": "strike",
    "tradedate": "trade_date",
    "businessdate": "trade_date",
    "logtime": "log_time",
    "matchtime": "log_time",
    "priceind": "price_indicator",
    "priceindicator": "price_indicator",
    "price": "price",
    "msgcode": "msg_code",
    "messagecode": "msg_code",
    "amendcode": "amend_code",
    "volume": "volume",
}

REQUIRED = {"commodity", "contract_type", "month_code", "year", "trade_date", "log_time", "price", "msg_code"}


def parse_header(header_line: str) -> dict:
    delimiter = "\t" if "\t" in header_line else ","
    fields = next(csv.reader([header_line.rstrip("\r\n")], delimiter=delimiter))
    canonical: dict[str, int] = {}
    unknown: list[dict] = []
    for idx, raw in enumerate(fields):
        key = ALIASES.get(_norm_header(raw))
        if key is None:
            unknown.append({"index": idx, "raw": raw})
            continue
        if key in canonical:
            raise AssertionError(("duplicate canonical SGX header", key, fields))
        canonical[key] = idx
    missing = REQUIRED - set(canonical)
    if missing:
        raise AssertionError(("missing required SGX header fields", sorted(missing), fields))
    schema_id = "legacy_price_indicator_amend" if {"price_indicator", "amend_code"} <= set(canonical) else "compact"
    return {
        "delimiter": delimiter,
        "delimiter_name": "tab" if delimiter == "\t" else "comma",
        "fields": fields,
        "canonical_indices": canonical,
        "unknown_fields": unknown,
        "schema_id": schema_id,
    }


def _new_contract(year: int, month: int, mcode: str) -> dict:
    return {
        "delivery_year": year,
        "delivery_month": month,
        "month_code": mcode,
        "last_le_150000": None,
        "last_le_091459": None,
        "last_le_092459": None,
        "trade_count": 0,
    }


def parse_cn_rows(header_line: str, rows: Iterable[str | list[str]], expected_date: str) -> dict:
    spec = parse_header(header_line)
    delimiter = spec["delimiter"]
    idx = spec["canonical_indices"]
    contracts: dict[str, dict] = {}
    cn_rows = 0
    futures_rows = 0
    eligible_trade_rows = 0
    nonblank_trade_amend_rows = 0
    blank_price_trade_rows = 0
    message_counts: Counter[str] = Counter()
    trade_code_counts: Counter[str] = Counter()
    row_length_counts: Counter[int] = Counter()
    unknown_message_counts: Counter[str] = Counter()

    for item in rows:
        row = next(csv.reader([item], delimiter=delimiter)) if isinstance(item, str) else list(item)
        clean = [str(x).strip() for x in row]
        if not clean:
            continue
        row_length_counts[len(clean)] += 1
        if idx["commodity"] >= len(clean) or clean[idx["commodity"]] != "CN":
            continue
        cn_rows += 1
        if clean[idx["contract_type"]] != "F":
            continue
        futures_rows += 1
        if clean[idx["trade_date"]] != expected_date:
            continue

        msg = clean[idx["msg_code"]]
        message_counts[msg] += 1
        if msg not in {"A", "B", "Y", "T", "S", ""}:
            unknown_message_counts[msg] += 1
        if msg not in OFFICIAL_TRADE_CODES:
            continue
        trade_code_counts[msg] += 1

        amend = clean[idx["amend_code"]] if "amend_code" in idx and idx["amend_code"] < len(clean) else ""
        if amend:
            nonblank_trade_amend_rows += 1
            continue

        raw_price = clean[idx["price"]]
        if raw_price == "":
            # Official legacy TickData_structure.dat explicitly permits a space/blank Price field.
            # Such a trade-status record has no numeric price and therefore cannot define a price endpoint.
            # Count and skip only this record; do not invalidate other valid trades in the archive.
            blank_price_trade_rows += 1
            continue

        mcode = clean[idx["month_code"]]
        if mcode not in MONTH:
            continue
        year = int(clean[idx["year"]])
        log_time = clean[idx["log_time"]].zfill(6)
        if not (len(log_time) == 6 and log_time.isdigit() and "000000" <= log_time <= "235959"):
            raise AssertionError(("invalid SGX log time", expected_date, log_time))
        price = normalize_price(raw_price)
        month = MONTH[mcode]
        cid = f"{year:04d}-{month:02d}"
        c = contracts.setdefault(cid, _new_contract(year, month, mcode))
        c["trade_count"] += 1
        eligible_trade_rows += 1
        point = {"time": log_time, "price": price}
        if log_time <= "150000":
            if c["last_le_150000"] is None or log_time >= c["last_le_150000"]["time"]:
                c["last_le_150000"] = point
        if log_time <= "091459":
            if c["last_le_091459"] is None or log_time >= c["last_le_091459"]["time"]:
                c["last_le_091459"] = point
        if log_time <= "092459":
            if c["last_le_092459"] is None or log_time >= c["last_le_092459"]["time"]:
                c["last_le_092459"] = point

    return {
        "schema_id": spec["schema_id"],
        "delimiter": spec["delimiter_name"],
        "header_fields": spec["fields"],
        "canonical_indices": spec["canonical_indices"],
        "cn_rows": int(cn_rows),
        "cn_futures_rows": int(futures_rows),
        "eligible_trade_rows": int(eligible_trade_rows),
        "nonblank_trade_amend_rows": int(nonblank_trade_amend_rows),
        "blank_price_trade_rows": int(blank_price_trade_rows),
        "message_counts": dict(sorted(message_counts.items())),
        "trade_code_counts": dict(sorted(trade_code_counts.items())),
        "unknown_message_counts": dict(sorted(unknown_message_counts.items())),
        "row_length_counts": {str(k): v for k, v in sorted(row_length_counts.items())},
        "contracts": contracts,
    }


def choose_contract(summary: dict, previous_china_day: pd.Timestamp) -> tuple[str, dict] | None:
    floor = (int(previous_china_day.year), int(previous_china_day.month))
    eligible = []
    for cid, c in summary["contracts"].items():
        start = c.get("last_le_150000")
        if start is None:
            continue
        ym = (int(c["delivery_year"]), int(c["delivery_month"]))
        if ym < floor:
            continue
        eligible.append((ym, cid, c))
    if not eligible:
        return None
    _, cid, c = min(eligible, key=lambda x: x[0])
    return cid, c


def parse_cn_summary_from_zip(zip_path: Path, expected_date: str) -> dict:
    with zipfile.ZipFile(zip_path) as z:
        members = z.namelist()
        if len(members) != 1:
            raise AssertionError(("unexpected SGX archive members", expected_date, members))
        member = members[0]
        with z.open(member) as raw:
            header_line = raw.readline().decode("utf-8", errors="replace").rstrip("\r\n")

    unzip_proc = subprocess.Popen(
        ["unzip", "-p", str(zip_path), member],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert unzip_proc.stdout is not None
    grep_proc = subprocess.Popen(
        ["grep", "-a", "^CN"],
        stdin=unzip_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    unzip_proc.stdout.close()
    assert grep_proc.stdout is not None
    summary = parse_cn_rows(header_line, grep_proc.stdout, expected_date)
    _, grep_err = grep_proc.communicate()
    unzip_err = unzip_proc.stderr.read().decode("utf-8", errors="replace") if unzip_proc.stderr is not None else ""
    unzip_rc = unzip_proc.wait()
    if grep_proc.returncode not in (0, 1):
        raise RuntimeError(("grep failed", expected_date, grep_proc.returncode, grep_err))
    if unzip_rc != 0:
        raise RuntimeError(("unzip failed", expected_date, unzip_rc, unzip_err))
    summary["member"] = member
    return summary
