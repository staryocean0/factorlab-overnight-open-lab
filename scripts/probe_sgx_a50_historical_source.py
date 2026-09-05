#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/research/sgx_a50_primary_tick_probe.json"
PROBES = [
    {"date": "2016-01-04", "key": 3479},
    {"date": "2018-04-02", "key": 4079},
    {"date": "2019-04-04", "key": 4344},
]
BASE = "https://links.sgx.com/1.0.0/derivatives-historical/{key}/{name}"
MAX_ZIP_BYTES = 100 * 1024 * 1024


def request(url: str, method: str = "GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "Mozilla/5.0 factorlab-research"})
    return urllib.request.urlopen(req, timeout=45)


def fetch(url: str) -> tuple[bytes, dict]:
    with request(url) as r:
        data = r.read(MAX_ZIP_BYTES + 1)
        if r.status != 200:
            raise RuntimeError((url, r.status))
        if len(data) > MAX_ZIP_BYTES:
            raise RuntimeError(("SGX file exceeds probe safety limit", url, len(data)))
        return data, {k.lower(): v for k, v in r.headers.items()}


def head(url: str) -> dict:
    try:
        with request(url, method="HEAD") as r:
            return {"status": int(r.status), "headers": {k.lower(): v for k, v in r.headers.items()}}
    except Exception as exc:
        return {"error": repr(exc)}


def inspect_zip(data: bytes) -> dict:
    result: dict = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        result["members"] = z.namelist()
        previews = []
        for name in z.namelist()[:5]:
            raw = z.read(name)
            text = raw.decode("utf-8", errors="replace")
            lines = text.splitlines()
            cn_lines = [line for line in lines if line.startswith("CN\t") or line.startswith("CN,") or line.startswith("CN ")]
            previews.append({
                "member": name,
                "uncompressed_bytes": len(raw),
                "line_count": len(lines),
                "first_lines": lines[:8],
                "CN_line_count": len(cn_lines),
                "CN_first_lines": cn_lines[:8],
            })
        result["previews"] = previews
    return result


def main() -> None:
    out: dict = {
        "schema_id": "sgx_historical_primary_tick_probe@1.0",
        "market_data_source": "Singapore Exchange official links.sgx.com historical files",
        "third_party_index_role": "navigation only; no third-party market prices used",
        "expected_A50_commodity_code_from_contract_specification": "CN",
        "probes": [],
    }
    for p in PROBES:
        item = dict(p)
        for name in ["TickData_structure.dat", "TC_structure.dat", "TC.txt"]:
            url = BASE.format(key=p["key"], name=name)
            try:
                data, headers = fetch(url)
                text = data.decode("utf-8", errors="replace")
                item[name] = {
                    "url": url,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "headers": headers,
                    "first_4000_chars": text[:4000],
                    "line_count": text.count("\n") + 1,
                }
            except Exception as exc:
                item[name] = {"url": url, "error": repr(exc)}
        tick_url = BASE.format(key=p["key"], name="WEBPXTICK_DT.zip")
        item["WEBPXTICK_DT_head"] = {"url": tick_url, **head(tick_url)}
        if p["date"] in {"2016-01-04", "2019-04-04"}:
            try:
                data, headers = fetch(tick_url)
                item["WEBPXTICK_DT"] = {"url": tick_url, "headers": headers, **inspect_zip(data)}
            except Exception as exc:
                item["WEBPXTICK_DT"] = {"url": tick_url, "error": repr(exc)}
        out["probes"].append(item)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
