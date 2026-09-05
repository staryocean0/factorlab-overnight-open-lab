#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import urllib.request

PROBES = [
    {"date": "2016-01-04", "key": 3479},
    {"date": "2018-04-02", "key": 4079},
    {"date": "2019-04-04", "key": 4344},
]
BASE = "https://links.sgx.com/1.0.0/derivatives-historical/{key}/{name}"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 factorlab-research"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        if r.status != 200:
            raise RuntimeError((url, r.status))
        return data


def main() -> None:
    out = {"schema_id": "sgx_historical_source_probe@1.0", "probes": []}
    for p in PROBES:
        item = dict(p)
        for name in ["TC_structure.dat", "TC.txt"]:
            url = BASE.format(key=p["key"], name=name)
            try:
                data = fetch(url)
                text = data.decode("utf-8", errors="replace")
                item[name] = {
                    "url": url,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "first_2000_chars": text[:2000],
                    "line_count": text.count("\n") + 1,
                }
            except Exception as exc:
                item[name] = {"url": url, "error": repr(exc)}
        out["probes"].append(item)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
