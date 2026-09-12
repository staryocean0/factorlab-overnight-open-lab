# V6A external source pack — 2026-09-10

The previously missing 2021-2025 HKMA and SGX A50 same-contract endpoint files
are now in-repo as frozen-column parquets, concatenated with the historical
2015-2020 overnight pack:

- `data/v6a_external_sources_2015_2025/sgx_a50_ordinary_preauction_endpoints.parquet`
- `data/v6a_external_sources_2015_2025/sgx_a50_holiday_endpoints.parquet`
- `data/v6a_external_sources_2015_2025/hkma_usdcny_cross.parquet`
- assertions: `data/v6a_external_sources_2015_2025/source_assertions.json`

Column names match `scripts/run_v6a_reusable_blackbox_local.py` `attach_a50` /
`add_hkma`. Ordinary target clocks are `<09:15:00`; holiday target clocks are
`<09:25:00`. Same-contract only. No continuous/CFD A50 and no BIS EER.

This note does not open the reusable BLACKBOX. `production_authority=false`.
