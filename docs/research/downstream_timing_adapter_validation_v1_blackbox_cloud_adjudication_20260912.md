# OFP-E1 timing adapter v1 reusable validation — cloud adjudication

Date: 2026-09-12

Validation identity: `overnight_c1_b4_timing_confidence_adapter_validation_v1`

Parent development identity: `overnight_c1_b4_timing_confidence_adapter_v1`

## Decision

**`FAIL`**

Accepted compact receipt:

`docs/research/local_downstream_timing_adapter_validation_v1_blackbox_receipt.json`

Receipt commit:

`30e01f781544068d1989f3eea167b5b845cc3a08`

Query id:

`1d8e01c69f555a7d721c`

Reusable BLACKBOX ledger ordinal: **6**.

## Provenance acceptance

Cloud review accepts the receipt because:

- the execution commit adds only the compact receipt;
- the frozen 2015-2020 panel reconstruction parity gate passed before validation;
- the 2019-2020 exact 09:35 / 09:50 clock parity gate passed before validation;
- the receipt binds the frozen protocol, high-open source manifest, V6A external-source manifest and reconstruction contract;
- the upstream authority ids remain exactly C1 query 2 and B4 query 3;
- the query id independently recomputes from the frozen identity and recorded provenance hashes;
- no internal metrics, calendar-year results, counts, bootstrap results or failure attribution are persisted;
- no strategy PnL or account results are persisted;
- production authority remains false.

The same 2021-2025 physical block has already been used by other separately frozen identities and is not an independent OOS sample.

## Scientific interpretation

The parent 2015-2020 development result remains valid retrospective evidence that the exact zero-boundary B4 abstention overlay improved mean signed factor utility relative to the C1-only comparator under the preregistered development gates.

The separately frozen 2021-2025 reusable validation identity, however, returns **FAIL**. Therefore the exact adapter contract:

`c1_action if driver_coherence * sign(observed_gap_rvol) >= 0 else 0`

is **not promoted to a validated E1 factor-utility adapter product**.

No inference is authorized about which calendar year, scientific gate, bootstrap component or hidden metric caused the failure. Those details were intentionally not persisted and may not be reconstructed for rescue.

## Authority consequence

Status consequence:

**`E1_VALIDATION_FAIL_CLOSED_NO_VALIDATED_TIMING_ADAPTER_PRODUCT`**

Retained only as historical evidence:

- the exact 2015-2020 retrospective factor-utility progression result;
- the fact that validation failed for the exact frozen zero-boundary adapter.

Not authorized:

- nonzero B4 threshold search;
- B4 magnitude/quantile buckets;
- C1/B4 fitted weights;
- alternate C1 sign conventions;
- alternate target horizons;
- adding A1/A4/C2/C3/D1 under this identity;
- hidden-BLACKBOX attribution or rescue;
- account or strategy backtesting under this identity;
- executable instrument mapping, costs, fills, sizing or production authority.

A future downstream adapter must be a **new result-free identity with an independently motivated mechanism**, not a repair of this failed E1 validation using hidden behavior.

Even a future adapter that validates factor utility would still require a separate executable consumer identity and the applicable Strategy Slice Rebuild, Strategy Science Acceptance and post-training account-audit contracts before any trading or production claim.

`production_authority=false`.
