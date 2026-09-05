#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/research/sgx_legacy_schema_probe.json"
BASE_URL = "https://links.sgx.com/1.0.0/derivatives-historical/{key}/{name}"

CASES = {
    "legacy_2015_02_17": {
        "date": "20150217",
        "key": 3248,
        "expected_sha256": "991a155c434ece40456f6a65d2800d5eee444d0676872b8feb876faea63df9bb",
    },
    "known_2016_01_04": {
        "date": "20160104",
        "key": 3479,
        "expected_sha256": "728954b0bb2cd31e25471c52c64c26d09ccafc61dd00d29c963a5823c8884c74",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(key: int, name: str) -> bytes:
    req = urllib.request.Request(
        BASE_URL.format(key=key, name=name),
        headers={"User-Agent": "Mozilla/5.0 factorlab-research-schema-probe"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        if int(r.status) != 200:
            raise RuntimeError(("http", key, name, r.status))
        return r.read()


def fetch_optional_text(key: int, name: str) -> dict:
    try:
        data = fetch_bytes(key, name)
        return {
            "available": True,
            "sha256": sha256_bytes(data),
            "text": data.decode("utf-8", errors="replace"),
        }
    except Exception as exc:
        return {"available": False, "error": repr(exc)}


def probe_archive(data: bytes, expected_date: str) -> dict:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members = z.namelist()
        if len(members) != 1:
            raise AssertionError(("unexpected archive members", members))
        member = members[0]
        with z.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
            header_line = text.readline().rstrip("\r\n")
            delimiter = "\t" if "\t" in header_line else ","
            header = next(csv.reader([header_line], delimiter=delimiter))
            reader = csv.reader(text, delimiter=delimiter)

            cn_rows = 0
            row_lengths: Counter[int] = Counter()
            field_bat_counts: dict[int, Counter[str]] = defaultdict(Counter)
            field_small_value_counts: dict[int, Counter[str]] = defaultdict(Counter)
            first_cn_rows: list[list[str]] = []
            first_rows_with_any_message_symbol: list[list[str]] = []
            date_field_candidates: Counter[int] = Counter()
            time_field_candidates: Counter[int] = Counter()

            for row in reader:
                if not row or row[0].strip() != "CN":
                    continue
                cn_rows += 1
                clean = [x.strip() for x in row]
                row_lengths[len(clean)] += 1
                if len(first_cn_rows) < 20:
                    first_cn_rows.append(clean)

                has_message_symbol = False
                for idx, value in enumerate(clean):
                    if value in {"B", "A", "T"}:
                        field_bat_counts[idx][value] += 1
                    if value in {"B", "A", "T", "Y", "S"}:
                        has_message_symbol = True
                    if len(value) <= 3 and value:
                        field_small_value_counts[idx][value] += 1
                    if value == expected_date:
                        date_field_candidates[idx] += 1
                    if len(value) == 6 and value.isdigit() and "000000" <= value <= "235959":
                        time_field_candidates[idx] += 1
                if has_message_symbol and len(first_rows_with_any_message_symbol) < 30:
                    first_rows_with_any_message_symbol.append(clean)

    compact_small = {}
    for idx, counts in field_small_value_counts.items():
        if idx >= 15:
            continue
        compact_small[str(idx)] = counts.most_common(20)

    return {
        "member": member,
        "header_line": header_line,
        "header_fields": header,
        "delimiter": "tab" if delimiter == "\t" else "comma",
        "cn_rows": cn_rows,
        "row_lengths": {str(k): v for k, v in sorted(row_lengths.items())},
        "BAT_by_field_index": {
            str(idx): dict(counts) for idx, counts in sorted(field_bat_counts.items())
        },
        "small_values_by_field_index_top20": compact_small,
        "date_field_candidates": {str(k): v for k, v in sorted(date_field_candidates.items())},
        "time_field_candidates": {str(k): v for k, v in sorted(time_field_candidates.items())},
        "first_20_CN_rows": first_cn_rows,
        "first_30_CN_rows_containing_message_symbols": first_rows_with_any_message_symbol,
    }


def main() -> None:
    result = {
        "schema_id": "sgx_legacy_tick_schema_probe@1.1",
        "role": "result-neutral data-contract probe; no target labels or model metrics are read",
        "cases": {},
    }
    for name, cfg in CASES.items():
        data = fetch_bytes(int(cfg["key"]), "WEBPXTICK_DT.zip")
        digest = sha256_bytes(data)
        if digest != cfg["expected_sha256"]:
            raise AssertionError((name, "archive sha mismatch", digest, cfg["expected_sha256"]))
        result["cases"][name] = {
            "date": cfg["date"],
            "key": cfg["key"],
            "sha256": digest,
            "official_TickData_structure_dat": fetch_optional_text(int(cfg["key"]), "TickData_structure.dat"),
            "official_TC_structure_dat": fetch_optional_text(int(cfg["key"]), "TC_structure.dat"),
            **probe_archive(data, cfg["date"]),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
