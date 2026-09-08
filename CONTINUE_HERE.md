# CONTINUE HERE — canonical project authority

This file is the first authority for deciding what this repository should do next.

## Permanent data rule

Historical data is reusable, not a one-shot consumable:

- **DEV** — `2015-01-05 .. 2020-12-31`: unrestricted development and diagnosis.
- **VALIDATION** — `2021-01-01 .. 2025-12-31`: reusable detailed validation; year/event/regime diagnostics are allowed.
- **BLACKBOX** — `2026-01-05 .. 2026-08-21`: reusable low-bandwidth certification only; public output is restricted to `PASS / FAIL / INSUFFICIENT`.

Controlling policy: `docs/governance/reusable_three_role_data_policy_v1.json`.

Repeated BLACKBOX queries are allowed only for separately frozen candidates and are not independent new OOS samples. Never release exact BLACKBOX metrics, counts, dates, subperiods, regimes, event examples, probabilities, attribution or failure examples. Every completed query is append-only in `docs/governance/reusable_blackbox_query_ledger_v1.json`.

## Certified mechanisms

### R1 — trend-parent pullback recovery

`rmr_cross_scale_pullback_parent_integrity_v2`

- detailed VALIDATION PASS;
- BLACKBOX query #1 `a9ba75c39e675ae6be17`: `PASS`;
- final bundle: `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`.

### R2 — range-parent boundary re-entry

`rmr_range_boundary_parent_integrity_v2`

- detailed VALIDATION PASS on both co-primary cells;
- BLACKBOX query #3 `a7e7f0208512aa7c1f31`: `PASS`;
- final bundle: `08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`.

R1 and R2 are complementary parent-normal-state mechanisms, but they are not one interchangeable scalar signal.

## Closed identities and synthesis

### R5-C event density

`rmr_event_density_state_reversal_v2` passed detailed VALIDATION and then BLACKBOX query #2 returned `FAIL`. No BLACKBOX detail was released. Same-identity rescue is prohibited.

### Economic translations

No tested trading implementation is certified.

- R1 economic v1/v2/v3 failed detailed VALIDATION before BLACKBOX.
- R2 economic v1 failed detailed VALIDATION before BLACKBOX.
- no economic BLACKBOX query has occurred.

### Unified parent-state router v1

`rmr_unified_parent_normal_state_router_v1` is **closed at VALIDATION**.

The scale-alignment implementation bug was fixed without changing protocol. The corrected router improved pooled results via the R1 lane but worsened both R2 cells. Therefore R1/R2 cannot be compressed into the tested common standardized state-consistency axis.

No BLACKBOX query occurred. Router v2 rescue is not authorized.

Evidence:

- `docs/research/rmr_unified_parent_state_router_v1_validation_adjudication_20260908.md`
- `docs/research/rmr_unified_parent_state_router_v1_closeout_20260908.md`
- `docs/archive/rmr_unified_parent_state_router_v1_history_anchor_20260908.md`

## Mechanism → execution diagnostic — complete

`rmr_mechanism_to_execution_diagnostic_v1` completed successfully on DEV+VALIDATION only. It did not refit the certified mechanisms, did not select thresholds/horizons, and did not open BLACKBOX.

Decisive VALIDATION result:

- R1_A binary structural expected net: about `-23.42bp`; realized net `-13.21bp`.
- R1_B binary structural expected net: about `-18.06bp`; realized gross `+2.67bp`, realized net `-7.33bp`.
- R2_A binary structural expected net: about `-11.79bp`; realized net `-12.68bp`.
- R2_B binary structural expected net: about `-12.32bp`; realized net `-12.52bp`.

Interpretation:

1. payoff geometry is the primary bridge failure;
2. next-minute confirmation delay is too small to explain the failure and must not be tuned as a rescue;
3. failure-side overshoot aggravates losses but binary geometry is already negative before overshoot;
4. restoration probability is not monotonic with realized net return;
5. R2 directional markouts become increasingly adverse with horizon under the current execution family;
6. R1_B alone shows a broad delayed positive markout term structure and very slow resolution, creating independent motivation for a temporal-path theory review.

Evidence:

- `docs/research/rmr_mechanism_to_execution_diagnostic_v1_adjudication_20260908.md`
- `docs/research/rmr_mechanism_to_execution_diagnostic_v1_decisive_receipt_20260908.json`
- `docs/archive/rmr_mechanism_to_execution_diagnostic_v1_history_anchor_20260908.md`

## Exact next action

Do **not** resume broad indicator discovery. Do **not** create another threshold/entry/stop/cost/scale/horizon variant of the closed economic families.

The next allowed research task is a results-blind **R1_B temporal execution theory review**.

Scientific question:

> If the higher-scale trend parent remains intact, is the certified lower-scale restoration probability expressed as a distributed path over time rather than as immediate next-minute structural-boundary capture, and can that temporal mechanism be defined causally before any outcome-driven execution choice is opened?

The review may authorize at most one new temporal execution identity and must obey all of the following:

1. start from the certified R1_B mechanism and frozen S2-inside-S3 scale identity; do not refit or alter R1 itself;
2. use the completed fixed-horizon term structure only as motivation, **not** to select 120 or 240 bars;
3. formulate the temporal/path mechanism before looking at a new outcome-driven parameterization;
4. no probability threshold, entry-delay search, stop/target search, cost search, scale search, year/regime selection or time-of-day selection;
5. no automatic `R1 economic v4`; a genuinely new identity requires independent timing theory and a new preregistration;
6. DEV first, then detailed reusable VALIDATION only after freezing;
7. no BLACKBOX access is authorized for this next review or its initial DEV/VALIDATION work;
8. production authority remains false.

R1_A and R2 current index-level economic translation are closed under present evidence. Instrument mapping is not the selected next direction because this diagnostic contains no instrument-specific spread/basis/carry/liquidity/convexity evidence; it requires its own independent theory if later proposed.

## BLACKBOX state

The append-only ledger remains exactly **3** completed queries:

1. R1 — PASS;
2. R5-C — FAIL;
3. R2 — PASS.

There is **no query #4**, and none is currently scheduled or authorized.

## Optional future data

Do not wait for future data. Continue DEV/VALIDATION research under the authority above. If the user later supplies newer data, version the three-role map forward rather than declaring existing history consumed.

## Authority order

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. active certified-mechanism states/protocols listed in `docs/INDEX.md`
5. `docs/INDEX.md`

Production authority remains `false`.
