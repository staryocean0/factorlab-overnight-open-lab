# AGENTS.md — repository operating rules

## 1. One canonical repository

`staryocean0/factorlab-overnight-open-lab` is the only active repository for this project.

## 2. Current authority

Read in this order:

1. `CONTINUE_HERE.md`
2. `docs/governance/reusable_three_role_data_policy_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/INDEX.md`

Historical `next_action` fields never override these files.

## 3. Reusable three-role data governance

### DEV

`2015-01-05 .. 2020-12-31`

Full development/diagnostic access.

### VALIDATION

`2021-01-01 .. 2025-12-31`

Reusable detailed validation. Year/event/regime diagnostics are allowed, but repeated VALIDATION variants must remain low-capacity and scientifically motivated.

### BLACKBOX

`2026-01-05 .. 2026-08-21`

Reusable certification only. Public output is limited to `PASS / FAIL / INSUFFICIENT`.

Never release exact BLACKBOX metrics, counts, dates, subperiods, regimes, event examples, probabilities, feature attribution or failure analysis. Repeated BLACKBOX queries are allowed only for separately frozen candidates and are not independent new OOS samples. Append every completed query to `docs/governance/reusable_blackbox_query_ledger_v1.json`.

A BLACKBOX FAIL/INSUFFICIENT returns research to DEV/VALIDATION without a breakdown. Hidden BLACKBOX behavior may never justify a feature, threshold, scale, rule or model change.

Current completed BLACKBOX query count is exactly **3**. There is no query #4.

## 4. Final-fit rule

A mechanism candidate may receive one preregistered DEV+VALIDATION final refit only after detailed VALIDATION passes. BLACKBOX may never participate in fitting, candidate selection, thresholds or feature choice.

No current temporal-execution research has BLACKBOX authority. Future BLACKBOX access, if ever appropriate, requires separate explicit governance after a newly frozen identity passes its authorized DEV/VALIDATION process.

## 5. Certified mechanisms

### R1

`rmr_cross_scale_pullback_parent_integrity_v2`

Trend-like intact-parent pullback recovery. BLACKBOX query #1 `a9ba75c39e675ae6be17`: `PASS`.

### R2

`rmr_range_boundary_parent_integrity_v2`

Range-like intact-parent boundary re-entry. BLACKBOX query #3 `a7e7f0208512aa7c1f31`: `PASS`.

R1 and R2 are complementary state-restoration mechanisms, not generic interchangeable signals and not one automatically shared scalar axis.

### R5-C

`rmr_event_density_state_reversal_v2` passed detailed VALIDATION but BLACKBOX query #2 `4fa9bfa2ec38f16cd65f` returned `FAIL`. The identity is closed and may not be rescued using hidden recent-period behavior.

## 6. Closed router and economic boundaries

### Unified parent-state router v1

`rmr_unified_parent_normal_state_router_v1` is closed at VALIDATION. After the scale-identity implementation bug was fixed without changing research protocol, both R2 cells worsened. Do not create router v2 by lane-specific scaling, axis-weight tuning, interaction search or other automatic rescue.

### Economic translation

No tested trading implementation is certified.

- R1 economic v1/v2/v3 failed detailed VALIDATION before BLACKBOX.
- R2 economic v1 failed detailed VALIDATION before BLACKBOX.
- no economic BLACKBOX query has occurred.

The completed `rmr_mechanism_to_execution_diagnostic_v1` found that payoff geometry is the primary bridge failure, next-minute delay is secondary, overshoot is secondary, and frozen restoration probability is not a monotonic realized-return score.

Do not create automatic follow-on economic versions by changing probability thresholds, expected-return thresholds, entry delays, stops, targets, costs, scales, horizons, years/regimes, time filters or portfolio weights against VALIDATION.

## 7. Current next research

Automatic broad R8/R9 indicator generation remains paused.

The next allowed task is a results-blind **R1_B temporal execution theory review**.

The review may authorize at most one materially new temporal identity and must obey:

- start from certified R1_B / frozen S2-inside-S3 identity without changing R1;
- treat completed fixed markouts `[1,5,15,30,60,120,240]` as motivation only, never as a horizon-selection menu;
- state the causal temporal/path theory before outcome-driven parameterization;
- no probability-threshold search;
- no entry-delay, stop, target, cost, scale or horizon search;
- no year/regime/time-of-day selection;
- no automatic `R1 economic v4` naming or rescue logic;
- DEV first, then freeze before detailed reusable VALIDATION;
- no BLACKBOX access under the current next-stage authority;
- production authority remains false.

R1_A and R2 simple index-level economic translation are closed under current evidence.

Instrument mapping is not the current selected direction because the diagnostic provides no instrument-specific spread, basis, carry, liquidity or convexity evidence. ETF/futures/options research requires a separate independently motivated instrument theory.

## 8. Optional future data

Do not wait for future data. Continue authorized DEV/VALIDATION research. If the user later supplies newer data, version the three-role map forward rather than declaring existing history consumed.

## 9. Repository hygiene

- Keep current authority concise and non-duplicative.
- Keep BLACKBOX receipts low-bandwidth.
- Do not copy BLACKBOX detail into docs, logs, charts or issues.
- Remove completed Actions workflows after bounded execution.
- Remove completed runners/tests/protocols/preanalysis from current surface when no longer active; preserve them through execution commits plus compact history anchors.
- Do not create a second active repository for this project.
- After substantial work, synchronize the canonical `main` by fast-forward when the research branch is clean and descendant of `main`.

Production authority remains `false`.
