#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/research/domestic_official_daily_endpoint_probe.json"
UA = "Mozilla/5.0 factorlab-official-endpoint-probe"


def meta(r: requests.Response) -> dict[str, Any]:
    return {
        "status": r.status_code,
        "final_url": r.url,
        "content_type": r.headers.get("content-type"),
        "bytes": len(r.content),
        "prefix": r.text[:500],
    }


def main() -> None:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "*/*"})
    out: dict[str, Any] = {
        "schema_id": "domestic_official_daily_endpoint_protocol_probe@1.0",
        "role": "result-neutral protocol probe; no CSI1000 target or third-party market values are read",
        "SHFE": {},
        "DCE": {},
    }

    for ymd, contract in [("20160615", "cu1607"), ("20200615", "cu2007")]:
        url = f"https://www.shfe.com.cn/data/dailydata/kx/kx{ymd}.dat"
        try:
            r = s.get(url, timeout=15, allow_redirects=True)
            m = meta(r)
            m["contract_token_present"] = contract.lower() in r.text.lower()
            try:
                p = r.json()
                m["json_type"] = type(p).__name__
                m["json_keys"] = list(p)[:30] if isinstance(p, dict) else None
                rows = p.get("o_curinstrument", []) if isinstance(p, dict) else []
                m["o_curinstrument_rows"] = len(rows)
                # Structure only; do not copy OHLC values into this protocol probe.
                matches = [x for x in rows if contract.lower() in json.dumps(x, ensure_ascii=False).lower()]
                m["rows_containing_contract_token"] = len(matches)
                m["sample_row_keys"] = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else None
            except Exception as exc:
                m["json_error"] = repr(exc)
            out["SHFE"][ymd] = m
        except Exception as exc:
            out["SHFE"][ymd] = {"error": repr(exc)}

    dce_urls = {
        "https_export": "https://www.dce.com.cn/publicweb/quotesdata/exportDayQuotesChData.html",
        "http_export": "http://www.dce.com.cn/publicweb/quotesdata/exportDayQuotesChData.html",
        "https_html": "https://www.dce.com.cn/publicweb/quotesdata/dayQuotesCh.html",
    }
    for ymd, contract in [("20160615", "i1609"), ("20200615", "i2009")]:
        year, month, day = ymd[:4], str(int(ymd[4:6]) - 1), ymd[6:]
        forms = [
            {
                "dayQuotes.variety": "all",
                "dayQuotes.trade_type": "0",
                "year": year,
                "month": month,
                "day": day,
            },
            {
                "dayQuotes.variety": "i",
                "dayQuotes.trade_type": "0",
                "year": year,
                "month": month,
                "day": day,
                "contract.contract_id": "all",
                "contract.variety_id": "i",
                "contract": "",
            },
        ]
        out["DCE"][ymd] = {}
        for label, url in dce_urls.items():
            attempts = []
            for fi, form in enumerate(forms):
                try:
                    headers = {"Referer": "https://www.dce.com.cn/publicweb/quotesdata/dayQuotesCh.html"}
                    r = s.post(url, data=form, headers=headers, timeout=15, allow_redirects=True)
                    m = meta(r)
                    m["form_variant"] = fi
                    m["contract_token_present"] = contract.lower() in r.text.lower()
                    attempts.append(m)
                    if r.status_code == 200 and m["contract_token_present"]:
                        break
                except Exception as exc:
                    attempts.append({"form_variant": fi, "error": repr(exc)})
            out["DCE"][ymd][label] = attempts

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
