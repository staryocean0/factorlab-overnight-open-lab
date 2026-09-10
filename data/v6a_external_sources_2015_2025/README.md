# V6A external sources, 2015-2025

Frozen-column HKMA and SGX FTSE China A50 same-contract endpoint files for the
already-frozen V6A reusable BLACKBOX controller.

This pack does **not** open BLACKBOX outcomes. `production_authority=false`.

## Files

- `sgx_a50_ordinary_preauction_endpoints.parquet`
  - frozen columns used by the controller: `trading_day`, `a50_ordinary_preauction_closure_return`, `target_end_time`
  - ordinary cutoff `<09:15:00`; same contract; 2473 rows, 2015-01-06 .. 2025-12-30
- `sgx_a50_holiday_endpoints.parquet`
  - frozen columns used by the controller: `trading_day`, `a50_holiday_closure_return`, `target_end_time`
  - holiday cutoff `<09:25:00`; same contract; 63 rows, 2015-09-07 .. 2025-10-09
- `hkma_usdcny_cross.parquet`
  - frozen columns used by the controller: `date`, `usdcny_hk`
  - HKMA official USD/HKD and CNY/HKD cross; 3539 rows, 2014-01-02 .. 2025-12-31

`source_assertions.json` contains the exact assertion block required by
`scripts/run_v6a_reusable_blackbox_local.py`.

## Assembly

- 2015-2020 (A50) / 2014-2020 (HKMA): frozen overnight pack on
  `codex/overnight-next-explained-20260905`.
- 2021-2025: DataHub research products
  `sgx_ftse_china_a50_same_contract_endpoints_20210104_20251231_v1_20260910`
  and `hkma_usdcny_cross_official_20210102_20251231_v1_20260910`.
  DataHub lake used generic `closure_return`; this export renames it to the
  frozen V6A names. No continuous/CFD A50 and no BIS EER.

Holiday 2015-2020 extra preopen columns were not carried forward; the frozen
V6A controller does not read them, and the 2021-2025 same-contract product
does not extract preopen.

## Not substitutes

- Sina `CHA50CFD` continuous/vendor daily
- BIS official NEER/REER
- volume/OI rolls or mid-window contract changes
- target ticks at or after the frozen cutoffs
