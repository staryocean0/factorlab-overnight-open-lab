# Offshore ETF development pack, 2015-01-02 through 2025-12-31

This pack is a user-authorized, byte-identical copy of the frozen OHR-05
Yahoo Finance chart v8 source so the cloud workspace can point
`OVERNIGHT_OFFSHORE_ETF_DAILY` at a repository path.

It is **not** a 2026 open and **not** a new source identity.

- Included: ASHS, ASHR, FXI, MCHI, SPY regular-session daily
  `date, symbol, open, close, volume` through 2025-12-31.
- Excluded: any row after 2025-12-31; 2026-01-05 through 2026-08-21
  sealed repeat-blackbox rows; post-2026-08-21 unread fresh rows.
- SHA256 matches the OHR-05 freeze receipt:
  `045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd`.
- Provider remains `Yahoo Finance chart v8 (query1.finance.yahoo.com)`.
- Production authority is false.

The original local cache file remains at
`~/.cache/overnight-open-lab/ohr05_offshore_etf_daily_yahoo_chart_v8_2015_2025.parquet`.
Cloud machines should use this pack.
