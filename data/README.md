# Development data

Only `000852.SH` and supporting US prints through 2020-12-31.

- `csi1000_open_pit_panel.parquet`: one row per China session being predicted. Target `gap` is that session's overnight open vs previous 15:00 close. All `prev_*`, `r*`, `us_*`, `holiday_reopen`, `weekend` columns are known before 09:31.
- `1m_official.parquet`: DataHub 1-minute bars 2015-01-05 through 2020-12-31. `timestamp_source_serialized` keeps the original `Z`-wrapped Shanghai clock.
- `us_nasdaq_vix.parquet`: FRED NASDAQCOM and VIXCLS. Use the last US session strictly before the China trading day.

No 2021+ rows. Index path, not a tradable fill. Do not resample new wall-clock frequencies.

## High-open development pack

`high_open_dev_2015_2025/` extends the cloud workspace with `000852.SH` rows through
2025-12-31 so high-open recall development scripts can run without local FactorLab
absolute paths.

- 2026-01-05 through 2026-08-21 remains excluded from this development pack.
- post-2026-08-21 remains excluded.
- The 2015-2020 files above stay frozen and unmodified.

## Gap-Fill V2 2026 repeat pack

`gap_fill_repeat_2026/` is a user-authorized public copy of the frozen
repeat-only inputs:

- annotated panel `2025-10-09` through `2026-08-21` (214 rows; 154 in the
  2026 validation window)
- `000852.SH` one-minute bars `2026-01-05` through `2026-08-21` (36960 rows)

This pack is not fresh OOS. Post-2026-08-21 remains excluded. See
`data/gap_fill_repeat_2026/README.md`.

