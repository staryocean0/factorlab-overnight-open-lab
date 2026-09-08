# CONTINUE HERE — canonical project authority

This file is the first authority for deciding what this repository should do next.

## Permanent data rule

Historical data is reusable, not a one-shot consumable:

- **DEV** — `2015-01-05 .. 2020-12-31`: unrestricted development and diagnosis.
- **VALIDATION** — `2021-01-01 .. 2025-12-31`: reusable detailed validation; year/event/regime diagnostics are allowed.
- **BLACKBOX** — `2026-01-05 .. 2026-08-21`: reusable low-bandwidth certification only; public output is restricted to `PASS / FAIL / INSUFFICIENT`.

Controlling policy:

`docs/governance/reusable_three_role_data_policy_v1.json`

Repeated BLACKBOX queries are allowed for separately frozen candidates but are not independent new OOS samples. Never release exact BLACKBOX metrics, counts, dates, subperiods, events, probabilities or failure examples. Every completed query is append-only in `docs/governance/reusable_blackbox_query_ledger_v1.json`.

## Certified mechanisms

### R1 — trend-parent pullback recovery

`rmr_cross_scale_pullback_parent_integrity_v2`

- detailed VALIDATION PASS;
- BLACKBOX query #1 `a9ba75c39e675ae6be17`: **PASS**;
- final mechanism bundle: `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`.

### R2 — range-parent boundary re-entry

`rmr_range_boundary_parent_integrity_v2`

- geometry-baseline detailed VALIDATION PASS on both co-primary scales;
- BLACKBOX query #3 `a7e7f0208512aa7c1f31`: **PASS**;
- final mechanism bundle: `08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`.

R1 and R2 are complementary views of parent normal-state integrity: trend-like intact state versus range-like intact state.

## Closed evidence

### R5-C event density

`rmr_event_density_state_reversal_v2`

- detailed VALIDATION PASS;
- BLACKBOX query #2 `4fa9bfa2ec38f16cd65f`: **FAIL**;
- no BLACKBOX detail released;
- v2 identity closed with no hidden-period rescue.

### Economic translation

No tested economic implementation is certified.

- R1 economic v1/v2/v3: all failed detailed VALIDATION before BLACKBOX.
- R2 economic v1: failed detailed VALIDATION before BLACKBOX; query #4 did **not** occur.
- therefore the BLACKBOX ledger remains at exactly **3** completed queries.

R2 economic-v1 closeout:

`docs/research/rmr_R2_economic_translation_v1_closeout_20260908.md`

The common conclusion is:

> Certified state-transition probability information is real, but the tested index-level next-minute / structural-boundary / 10bp execution families do not establish trading viability.

Do not create automatic R1/R2 economic v2/v3/v4 variants by changing thresholds, costs, entry delays, stops, scales or time filters against VALIDATION. A new economic identity requires materially new execution or instrument theory.

## Exact next action

Do **not** resume broad indicator discovery and do **not** immediately tune another trading rule.

The next research task is a results-blind **unified parent-state router review** built only from the two certified mechanisms.

Scientific question:

> Can one common signed parent-state axis coherently route trend-like deviations to R1 and range-like deviations to R2, while adding restoration-probability information beyond each lane's own local geometry baseline?

The review may approve at most one low-capacity router identity. Any approved router must:

1. use only the already-certified R1/R2 parent features and event geometries;
2. introduce no new indicator family, scale search, threshold search or PnL objective;
3. fit on DEV and require detailed cross-lane / cross-year VALIDATION stability;
4. receive at most one preregistered DEV+VALIDATION final refit;
5. access BLACKBOX only after full VALIDATION PASS, as query #4, with three-state output only;
6. close on BLACKBOX FAIL/INSUFFICIENT without hidden breakdown.

This router is a synthesis of certified mechanisms, not a new broad R8/R9 lane and not an economic rescue.

## Optional future data

The preregistered complete-2026Q4 R1 challenge remains an optional future experiment, not a current blocker. When the user supplies newer data, version the three-role map forward rather than declaring existing history consumed.

## Authority order

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. active certified-mechanism states/protocols listed in `docs/INDEX.md`
5. `docs/INDEX.md`

Production authority remains `false`.
