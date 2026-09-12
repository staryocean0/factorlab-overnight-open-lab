# OFP-B3 FX/CNY driver v1 — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_fx_cny_driver_v1`

Question: does the causal HKMA-derived overnight USD/CNY closure move carry incremental information about normalized CSI1000 opening gap beyond domestic causal context?

Frozen coordinate:

`fx_cny_z = -hkma_usdcny_closure_return / RMS60_prev(hkma_usdcny_closure_return)`

The minus sign makes positive values correspond to CNY strength / risk-on. RMS normalization is trailing 60 China trading days, `shift(1)`, minimum 20 observations.

Target: `opening_gap_rvol = gap / rvol20`.

Baseline controls: `r1, r20, abs_r1, prev_gap, overnight_trend_5, prev_daytime, prev_last_hour, prev_afternoon, log_rvol20, weekend, holiday_reopen`.

B1 global risk, B2 A50 and B4 coherence are excluded. Expected incremental direction is positive.

Development: 2015-01-05..2020-12-31. Sufficiency pooled >=900 and each year >=150. Progression requires pooled partial correlation >0, pooled standardized coefficient >0, >=4/6 annual coefficients >0, median annual coefficient >0, pooled delta R² >0 and >=4/6 annual delta R² >0.

No FX threshold, bucket, alternate sign, lookback, interpolation, target or channel combination is authorized. 2021–2025 remains unopened until a separately frozen successor protocol.

`production_authority=false`.
