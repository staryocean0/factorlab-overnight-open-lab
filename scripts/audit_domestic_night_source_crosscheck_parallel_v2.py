#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "night_audit_parallel",
    ROOT / "scripts/audit_domestic_night_source_crosscheck_parallel.py",
)
parallel = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(parallel)

_orig_shfe = parallel.base.fetch_shfe
_orig_dce = parallel.base.fetch_dce


def _shfe_date_absence(result: dict[str, Any]) -> bool:
    """True only when the official service answered in a way consistent with no row/date.

    Network/TLS/403/5xx/timeouts are infrastructure failures and must not consume
    the frozen five-day fallback budget. A 404 daily file or an HTTP-200 payload
    with zero exact-contract rows is a date/row absence and may use the frozen fallback.
    """
    for e in result.get("errors", []):
        msg = str(e.get("error", ""))
        if "exact contract rows=" in msg:
            return True
        if "'http', 404" in msg or '"http", 404' in msg or "http', 404" in msg:
            return True
    return False


def _dce_date_absence(result: dict[str, Any]) -> bool:
    """HTTP-200 official payloads that parse but contain no exact row may fallback."""
    return any("response" in e for e in result.get("errors", []))


def fail_fast_shfe(*args: Any, **kwargs: Any) -> dict[str, Any]:
    result = _orig_shfe(*args, **kwargs)
    if not result.get("ok") and not _shfe_date_absence(result):
        raise RuntimeError(("SHFE_official_endpoint_infrastructure_unavailable", result))
    return result


def fail_fast_dce(*args: Any, **kwargs: Any) -> dict[str, Any]:
    result = _orig_dce(*args, **kwargs)
    if not result.get("ok") and not _dce_date_absence(result):
        raise RuntimeError(("DCE_official_endpoint_infrastructure_unavailable", result))
    return result


parallel.base.fetch_shfe = fail_fast_shfe
parallel.base.fetch_dce = fail_fast_dce

if __name__ == "__main__":
    parallel.main()
