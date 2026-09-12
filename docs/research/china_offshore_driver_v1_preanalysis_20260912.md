# OFP-B2 China-offshore driver v1 — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_china_offshore_driver_v1`

Question: does the causal same-contract A50 pre-auction return carry incremental information about normalized CSI1000 opening gap beyond domestic causal context?

Frozen coordinate:

`china_offshore_z = a50_channel_return / RMS60_prev(a50_channel_return)`

The A50 channel keeps the already-governed ordinary/holiday clock semantics. RMS normalization is trailing 60 China trading days, `shift(1)`, minimum 20 observations. Positive means offshore China risk-on.

Target: `opening_gap_rvol = gap / rvol20`.

Baseline controls: `r1, r20, abs_r1, prev_gap, overnight_trend_5, prev_daytime, prev_last_hour, prev_afternoon, log_rvol20, weekend, holiday_reopen`.

B1 global risk, B3 FX and B4 coherence are excluded. Expected incremental direction is positive.

Development: 2015-01-05..2020-12-31. Sufficiency pooled >=900 and each year >=150. Progression requires pooled partial correlation >0, pooled standardized coefficient >0, >=4/6 annual coefficients >0, median annual coefficient >0, pooled delta R² >0 and >=4/6 annual delta R² >0.

No A50 threshold, magnitude bucket, ordinary/holiday split search, alternate clock, lookback, weighting, target or channel combination is authorized. 2021–2025 remains unopened until a separately frozen successor protocol.

`production_authority=false`.
