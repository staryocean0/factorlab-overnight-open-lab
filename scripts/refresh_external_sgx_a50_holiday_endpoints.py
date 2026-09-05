#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
NAV_COMMIT = "303df3f2c6a71b84cab3c5354c9bf936fb6ef082"
NAV_URL = f"https://raw.githubusercontent.com/blurridge/sgx-derivative-downloader/{NAV_COMMIT}/db/indexes.json"
SGX_URL = "https://links.sgx.com/1.0.0/derivatives-historical/{key}/WEBPXTICK_DT.zip"
RAW_ENDPOINTS = ROOT / "data/external/sgx_a50_holiday_endpoints_2015_2020.csv"
PARQUET_OUT = ROOT / "data/development/sgx_a50_holiday_endpoints.parquet"
NAV_OUT = ROOT / "data/external/sgx_historical_date_index_used_2015_2020.json"
MANIFEST_OUT = ROOT / "docs/governance/external_sgx_a50_holiday_2015_2020_manifest.json"
PACKAGE_MANIFEST = ROOT / "data/manifest.json"
START = pd.Timestamp("2015-01-01")
END = pd.Timestamp("2020-12-31")
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MONTH = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6, "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_json(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "factorlab-overnight-open-lab/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_archive(date: str, key: int) -> tuple[str, dict, bytes]:
    url = SGX_URL.format(key=key)
    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 factorlab-research"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read(MAX_ARCHIVE_BYTES + 1)
                if int(r.status) != 200:
                    raise RuntimeError((date, key, r.status))
                if len(data) > MAX_ARCHIVE_BYTES:
                    raise RuntimeError(("archive too large", date, len(data)))
                headers = {k.lower(): v for k, v in r.headers.items()}
            return date, {"key": int(key), "url": url, "bytes": len(data), "sha256": sha256_bytes(data), "headers": headers}, data
        except Exception as exc:
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    assert last_exc is not None
    raise last_exc


def normalize_price(raw: str) -> float:
    x = float(raw.strip())
    if x > 100000:
        x /= 100.0
    if not 1000 <= x <= 50000:
        raise AssertionError(("CN price outside frozen sanity range", raw, x))
    return x


def parse_cn_summary(data: bytes, expected_date: str) -> dict:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members = z.namelist()
        if len(members) != 1:
            raise AssertionError(("unexpected SGX archive members", expected_date, members))
        member = members[0]
        with z.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
            header = text.readline().strip("\r\n")
            delimiter = "\t" if "\t" in header else ","
            reader = csv.reader(text, delimiter=delimiter)
            contracts: dict[str, dict] = {}
            cn_rows = 0
            cn_trades = 0
            for row in reader:
                if len(row) < 10 or row[0].strip() != "CN" or row[1].strip() != "F":
                    continue
                cn_rows += 1
                mcode = row[2].strip()
                if mcode not in MONTH:
                    continue
                year = int(row[3])
                trade_date = row[5].strip()
                log_time = row[6].strip().zfill(6)
                msg = row[8].strip()
                if trade_date != expected_date or msg != "T":
                    continue
                cn_trades += 1
                price = normalize_price(row[7])
                cid = f"{year:04d}-{MONTH[mcode]:02d}"
                c = contracts.setdefault(cid, {
                    "delivery_year": year,
                    "delivery_month": MONTH[mcode],
                    "month_code": mcode,
                    "last_le_150000": None,
                    "last_le_092459": None,
                    "first_090000_092459": None,
                    "last_090000_092459": None,
                    "trade_count": 0,
                })
                c["trade_count"] += 1
                point = {"time": log_time, "price": price}
                if log_time <= "150000":
                    if c["last_le_150000"] is None or log_time >= c["last_le_150000"]["time"]:
                        c["last_le_150000"] = point
                if log_time <= "092459":
                    if c["last_le_092459"] is None or log_time >= c["last_le_092459"]["time"]:
                        c["last_le_092459"] = point
                if "090000" <= log_time <= "092459":
                    if c["first_090000_092459"] is None or log_time < c["first_090000_092459"]["time"]:
                        c["first_090000_092459"] = point
                    if c["last_090000_092459"] is None or log_time >= c["last_090000_092459"]["time"]:
                        c["last_090000_092459"] = point
    return {
        "member": member,
        "delimiter": "tab" if delimiter == "\t" else "comma",
        "cn_rows": int(cn_rows),
        "cn_trade_rows": int(cn_trades),
        "contracts": contracts,
    }


def choose_contract(summary: dict, prev_day: pd.Timestamp) -> tuple[str, dict] | None:
    eligible = []
    floor = (prev_day.year, prev_day.month)
    for cid, c in summary["contracts"].items():
        if c["last_le_150000"] is None:
            continue
        ym = (int(c["delivery_year"]), int(c["delivery_month"]))
        if ym < floor:
            continue
        eligible.append((ym, cid, c))
    if not eligible:
        return None
    _, cid, c = min(eligible, key=lambda x: x[0])
    return cid, c


def update_package_manifest(frame: pd.DataFrame) -> None:
    package = json.loads(PACKAGE_MANIFEST.read_text())
    rel = str(PARQUET_OUT.relative_to(ROOT))
    product = {
        "path": rel,
        "rows": int(len(frame)),
        "bytes": int(PARQUET_OUT.stat().st_size),
        "sha256": sha256_file(PARQUET_OUT),
        "min_day": str(pd.to_datetime(frame["trading_day"]).min().date()),
        "max_day": str(pd.to_datetime(frame["trading_day"]).max().date()),
    }
    package["products"] = [x for x in package["products"] if x["path"] != rel] + [product]
    PACKAGE_MANIFEST.write_text(json.dumps(package, indent=2) + "\n")


def main() -> None:
    panel = pd.read_parquet(PANEL_PATH).copy().sort_values("trading_day").reset_index(drop=True)
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    panel["previous_china_day"] = panel["trading_day"].shift(1)
    events = panel.loc[(pd.to_numeric(panel["holiday_reopen"], errors="coerce").fillna(0) != 0) & (panel["trading_day"] >= START) & (panel["trading_day"] <= END), ["trading_day", "previous_china_day"]].copy()
    if events.empty:
        raise AssertionError("no holiday_reopen events in bounded panel")
    if events["previous_china_day"].isna().any():
        raise AssertionError("holiday event missing previous China day")

    nav = fetch_json(NAV_URL)
    if not isinstance(nav, dict):
        raise AssertionError("navigation index is not a dict")

    required_dates = sorted({d.strftime("%Y%m%d") for d in pd.concat([events["trading_day"], events["previous_china_day"]])})
    used_index: dict[str, int | None] = {d: int(nav[d]) if d in nav else None for d in required_dates}
    NAV_OUT.parent.mkdir(parents=True, exist_ok=True)
    NAV_OUT.write_text(json.dumps({
        "schema_id": "sgx_date_index_navigation_subset@1.0",
        "role": "navigation only; no market prices",
        "source_repository": "blurridge/sgx-derivative-downloader",
        "pinned_commit": NAV_COMMIT,
        "source_path": "db/indexes.json",
        "used_date_to_key": used_index,
    }, indent=2, sort_keys=True) + "\n")

    fetchable = {d: k for d, k in used_index.items() if k is not None}
    archive_meta: dict[str, dict] = {}
    archive_data: dict[str, bytes] = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(fetch_archive, d, int(k)) for d, k in fetchable.items()]
        for fut in as_completed(futures):
            d, meta, data = fut.result()
            archive_meta[d] = meta
            archive_data[d] = data

    summaries: dict[str, dict] = {}
    for d, data in archive_data.items():
        summaries[d] = parse_cn_summary(data, d)
        archive_meta[d].update({
            "member": summaries[d]["member"],
            "delimiter": summaries[d]["delimiter"],
            "cn_rows": summaries[d]["cn_rows"],
            "cn_trade_rows": summaries[d]["cn_trade_rows"],
        })

    rows = []
    unavailable = []
    for _, ev in events.iterrows():
        target = pd.Timestamp(ev["trading_day"])
        prev = pd.Timestamp(ev["previous_china_day"])
        td = target.strftime("%Y%m%d")
        pd_ = prev.strftime("%Y%m%d")
        reason = None
        if pd_ not in summaries:
            reason = "previous_china_day_SGX_archive_unavailable"
        elif td not in summaries:
            reason = "target_china_day_SGX_archive_unavailable"
        if reason is not None:
            unavailable.append({"trading_day": str(target.date()), "previous_china_day": str(prev.date()), "reason": reason})
            continue
        chosen = choose_contract(summaries[pd_], prev)
        if chosen is None:
            unavailable.append({"trading_day": str(target.date()), "previous_china_day": str(prev.date()), "reason": "no_eligible_CN_contract_trade_by_previous_150000"})
            continue
        cid, start_contract = chosen
        target_contract = summaries[td]["contracts"].get(cid)
        if target_contract is None or target_contract["last_le_092459"] is None:
            unavailable.append({"trading_day": str(target.date()), "previous_china_day": str(prev.date()), "contract": cid, "reason": "same_contract_has_no_target_trade_by_092459"})
            continue
        start = start_contract["last_le_150000"]
        end = target_contract["last_le_092459"]
        assert start is not None and end is not None
        first_morning = target_contract["first_090000_092459"]
        last_morning = target_contract["last_090000_092459"]
        closure_ret = float(end["price"] / start["price"] - 1.0)
        preopen_ret = float(last_morning["price"] / first_morning["price"] - 1.0) if first_morning is not None and last_morning is not None else float("nan")
        rows.append({
            "trading_day": target,
            "previous_china_day": prev,
            "contract": cid,
            "delivery_year": int(start_contract["delivery_year"]),
            "delivery_month": int(start_contract["delivery_month"]),
            "start_time": start["time"],
            "start_price": float(start["price"]),
            "target_end_time": end["time"],
            "target_end_price": float(end["price"]),
            "a50_holiday_closure_return": closure_ret,
            "target_preopen_first_time": first_morning["time"] if first_morning is not None else None,
            "target_preopen_first_price": float(first_morning["price"]) if first_morning is not None else float("nan"),
            "target_preopen_last_time": last_morning["time"] if last_morning is not None else None,
            "target_preopen_last_price": float(last_morning["price"]) if last_morning is not None else float("nan"),
            "a50_holiday_preopen_return": preopen_ret,
            "previous_archive_key": int(archive_meta[pd_]["key"]),
            "previous_archive_sha256": archive_meta[pd_]["sha256"],
            "target_archive_key": int(archive_meta[td]["key"]),
            "target_archive_sha256": archive_meta[td]["sha256"],
        })

    frame = pd.DataFrame(rows).sort_values("trading_day").reset_index(drop=True)
    if frame.empty:
        raise AssertionError("no usable SGX A50 holiday endpoints extracted")
    if pd.to_datetime(frame["trading_day"]).max() > END:
        raise AssertionError("post-2020 A50 event detected")
    if not (frame["target_end_time"] < "092500").all():
        raise AssertionError("A50 target endpoint at or after 09:25")
    if not (frame["start_time"] <= "150000").all():
        raise AssertionError("A50 previous endpoint after 15:00")

    RAW_ENDPOINTS.parent.mkdir(parents=True, exist_ok=True)
    csv_frame = frame.copy()
    csv_frame["trading_day"] = pd.to_datetime(csv_frame["trading_day"]).dt.strftime("%Y-%m-%d")
    csv_frame["previous_china_day"] = pd.to_datetime(csv_frame["previous_china_day"]).dt.strftime("%Y-%m-%d")
    csv_frame.to_csv(RAW_ENDPOINTS, index=False, float_format="%.12g", lineterminator="\n")
    PARQUET_OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(PARQUET_OUT, index=False)
    update_package_manifest(frame)

    event_train = events["trading_day"] <= pd.Timestamp("2018-12-31")
    event_hold = events["trading_day"] >= pd.Timestamp("2019-01-01")
    usable_days = set(pd.to_datetime(frame["trading_day"]).dt.normalize())
    train_total = int(event_train.sum())
    hold_total = int(event_hold.sum())
    train_usable = int(sum(pd.Timestamp(d) in usable_days for d in events.loc[event_train, "trading_day"]))
    hold_usable = int(sum(pd.Timestamp(d) in usable_days for d in events.loc[event_hold, "trading_day"]))
    preopen_usable = int(frame["a50_holiday_preopen_return"].notna().sum())

    manifest = {
        "schema_id": "external_sgx_a50_holiday_endpoints_manifest@1.0",
        "frozen_retrieval_date": "2026-09-05",
        "market_data_provider": "Singapore Exchange official historical derivatives endpoint",
        "commodity_code": "CN",
        "official_file": "WEBPXTICK_DT.zip",
        "navigation": {
            "role": "date-to-key only; no market price content",
            "source_repository": "blurridge/sgx-derivative-downloader",
            "pinned_commit": NAV_COMMIT,
            "source_url": NAV_URL,
            "frozen_subset": str(NAV_OUT.relative_to(ROOT)),
            "frozen_subset_sha256": sha256_file(NAV_OUT),
        },
        "event_definition": "holiday_reopen == 1 in the bounded CSI1000 panel",
        "contract_selection": "nearest non-past CN contract month with an actual trade at or before previous China 15:00; same contract required at target",
        "target_cutoff": "09:24:59 Singapore/Beijing time",
        "price_normalization": "if parsed CN raw price >100000 divide by 100 once; otherwise unchanged; final sanity 1000..50000",
        "coverage": {
            "train_event_total": train_total,
            "train_event_usable": train_usable,
            "train_event_coverage": float(train_usable / train_total) if train_total else 0.0,
            "holdout_event_total": hold_total,
            "holdout_event_usable": hold_usable,
            "holdout_event_coverage": float(hold_usable / hold_total) if hold_total else 0.0,
            "preopen_return_usable_all_events": preopen_usable,
        },
        "used_archives": {d: archive_meta[d] for d in sorted(archive_meta)},
        "unavailable_events": unavailable,
        "assets": {
            str(RAW_ENDPOINTS.relative_to(ROOT)): {"sha256": sha256_file(RAW_ENDPOINTS)},
            str(PARQUET_OUT.relative_to(ROOT)): {"sha256": sha256_file(PARQUET_OUT)},
            str(NAV_OUT.relative_to(ROOT)): {"sha256": sha256_file(NAV_OUT)},
        },
        "guards": {
            "post_2020_rows": 0,
            "future_volume_contract_selection": False,
            "mid_window_roll": False,
            "target_ticks_at_or_after_092500": 0,
            "raw_full_market_archives_committed": False,
            "raw_archive_provenance_frozen_by_url_key_sha256": True,
        },
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
