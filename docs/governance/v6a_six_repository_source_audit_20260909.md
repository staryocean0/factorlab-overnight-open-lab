# V6A six-repository source audit — 2026-09-09

## Purpose

Search all six accessible FactorLab GitHub repositories for source material that can satisfy the frozen V6A reusable BLACKBOX source contract for `2021-01-01..2025-12-31`, especially:

- HKMA `usdcny_hk` history;
- SGX FTSE China A50 ordinary pre-auction same-contract endpoints with target cutoff `<09:15:00`;
- SGX FTSE China A50 holiday endpoints preserving the frozen V5A holiday semantics with target cutoff `<09:25:00`.

The audit does not open BLACKBOX outcomes.

## Repositories checked

1. `staryocean0/factorlab-overnight-open-lab`
2. `staryocean0/factorlab-multifactor-stock-lab`
3. `staryocean0/factorlab-two-wave-strategy-lab`
4. `staryocean0/factorlab-trend-reversion-regime-lab`
5. `staryocean0/factorlab-star50-filter-lab`
6. `staryocean0/factorlab-overnight-gap-fill-repeat-2026`

Checks included current/default trees, repository branch inventories, relevant non-default branches, and exact/content-keyword searches for `HKMA`, `usdcny_hk`, `SGX A50`, `sgx_a50`, `FTSE China A50`, `Singapore Exchange`, `ordinary_preauction`, and holiday endpoint identities.

## Findings

### factorlab-overnight-open-lab

Historical Overnight A50 branches contain the frozen V5/V6 source family only through 2020, including:

- `data/development/hkma_usdcny_cross.parquet`;
- `data/development/sgx_a50_holiday_endpoints.parquet`;
- `data/development/sgx_a50_ordinary_preauction_endpoints.parquet`;
- 2014-2020 source manifests.

The A50 nonlinearity and auction-source branches do not contain 2021-2025 extensions of those endpoint files.

Current `main` already has CSI1000 2015-2025 and FRED histories, so those inputs are not the blocker.

### factorlab-multifactor-stock-lab

No HKMA/USDCNY-HK or SGX A50 endpoint source was found on `main` or the non-main foundation-audit branch. SGX references observed elsewhere in this project family are not the V6A FTSE China A50 source identity.

### factorlab-two-wave-strategy-lab

No HKMA/USDCNY-HK or SGX A50 endpoint source was found on `main`, `codex/two-wave-phase1-20260905`, or `codex/broad-reversal-authority-reset-20260908`.

### factorlab-trend-reversion-regime-lab

This repository does contain substantial CSI1000 (`000852.SH`) 2021-2025 minute/3-second/5-minute market data, including on the historical `research/reversal-overnight-gap-v0-12` branch. Those rows are not the missing external V6A source and are unnecessary because Overnight already has the CSI1000 2015-2025 target-side pack.

No HKMA/USDCNY-HK or SGX A50 endpoint source matching the frozen V6A semantics was found.

### factorlab-star50-filter-lab

No HKMA/USDCNY-HK or SGX FTSE China A50 endpoint source was found on `main` or the local takeover branch. SGX-like references belonging to STAR50/other research objects are not interchangeable with the frozen FTSE China A50 contract and were not imported.

### factorlab-overnight-gap-fill-repeat-2026

The retired repository has only one current branch (`master`) and is a repeat-data/migration surface. It contains no 2021-2025 HKMA or SGX A50 endpoint source matching V6A.

## Import decision

`NO_VALID_CROSS_REPOSITORY_SOURCE_TO_IMPORT`

No file was copied merely because it looked similar. In particular, the following are not valid substitutes:

- CSI1000 market bars from another repository;
- SGX data for a different instrument;
- continuous/rolled A50 series;
- A50 ETF/CFD/index proxies;
- endpoint data without same-contract proof;
- endpoint data using target observations at or after the frozen cutoffs;
- a different FX proxy in place of frozen HKMA semantics.

## BLACKBOX status after audit

- V6A query opened: `false`
- reusable BLACKBOX ledger query count: `0`
- public BLACKBOX result: none
- BLACKBOX data consumed: `false`
- production authority: `false`

The remaining physical source blocker is specifically the frozen-semantics 2021-2025 HKMA and SGX A50 endpoint package. Once an authoritative source for those inputs is available, the already-frozen low-bandwidth controller may execute and release only `PASS / FAIL / INSUFFICIENT`.
