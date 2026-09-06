from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "combine_external_sgx_a50_ordinary",
    ROOT / "scripts/combine_external_sgx_a50_ordinary.py",
)
combine = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(combine)


def test_discover_year_files_recurses_through_download_artifact_internal_paths(tmp_path: Path) -> None:
    years = [2019, 2020]
    for year in years:
        nested = tmp_path / "artifacts" / "staging" / "a50_ordinary"
        nested.mkdir(parents=True, exist_ok=True)
        (nested / f"a50_ordinary_endpoints_{year}.csv").write_text("trading_day\n")
    found = combine.discover_year_files(tmp_path, "a50_ordinary_endpoints_", ".csv", years=years)
    assert [p.name for p in found] == [
        "a50_ordinary_endpoints_2019.csv",
        "a50_ordinary_endpoints_2020.csv",
    ]


def test_discover_year_files_rejects_duplicate_year_artifacts(tmp_path: Path) -> None:
    (tmp_path / "one").mkdir()
    (tmp_path / "two").mkdir()
    (tmp_path / "one" / "a50_ordinary_manifest_2019.json").write_text("{}")
    (tmp_path / "two" / "a50_ordinary_manifest_2019.json").write_text("{}")
    with pytest.raises(AssertionError):
        combine.discover_year_files(tmp_path, "a50_ordinary_manifest_", ".json", years=[2019])


def test_repeated_archive_allows_dynamic_http_headers_when_stable_identity_matches() -> None:
    dst: dict = {}
    base = {
        "key": 4537,
        "url": "https://links.sgx.com/1.0.0/derivatives-historical/4537/WEBPXTICK_DT.zip",
        "bytes": 6798830,
        "sha256": "ccfde188",
        "member": "WEBPXTICK_DT-20191231.csv",
        "schema_id": "compact",
        "eligible_trade_rows": 30576,
    }
    combine.merge_archive_records(dst, {"20191231": {**base, "headers": {"date": "first", "set-cookie": "a"}}}, 2019)
    combine.merge_archive_records(dst, {"20191231": {**base, "headers": {"date": "second", "set-cookie": "b"}}}, 2020)
    assert dst["20191231"]["sha256"] == "ccfde188"
    assert [x["source_year"] for x in dst["20191231"]["retrieval_observations"]] == [2019, 2020]
    assert dst["20191231"]["retrieval_observations"][0]["headers"] != dst["20191231"]["retrieval_observations"][1]["headers"]


def test_repeated_archive_rejects_stable_identity_conflict() -> None:
    dst: dict = {}
    base = {"key": 4537, "url": "u", "sha256": "same", "member": "m", "schema_id": "compact"}
    combine.merge_archive_records(dst, {"20191231": {**base, "headers": {"date": "first"}}}, 2019)
    with pytest.raises(AssertionError):
        combine.merge_archive_records(
            dst,
            {"20191231": {**base, "sha256": "DIFFERENT", "headers": {"date": "second"}}},
            2020,
        )
