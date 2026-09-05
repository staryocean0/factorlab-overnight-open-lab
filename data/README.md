# Development data

Only `000852.SH` and supporting US prints through 2020-12-31.

- `csi1000_open_pit_panel.parquet`: one row per China session being predicted. Target `gap` is that session's overnight open vs previous 15:00 close. All `prev_*`, `r*`, `us_*`, `holiday_reopen`, `weekend` columns are known before 09:31.
- `1m_official.parquet`: DataHub 1-minute bars 2015-01-05 through 2020-12-31. `timestamp_source_serialized` keeps the original `Z`-wrapped Shanghai clock.
- `us_nasdaq_vix.parquet`: FRED NASDAQCOM and VIXCLS. Use the last US session strictly before the China trading day.

No 2021+ rows. Index path, not a tradable fill. Do not resample new wall-clock frequencies.
