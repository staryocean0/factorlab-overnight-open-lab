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

Reusable detailed validation for separately frozen low-capacity identities. Do not open VALIDATION for an identity that failed its preregistered DEV gate.

### BLACKBOX

`2026-01-05 .. 2026-08-21`

Reusable certification only. Public output is limited to `PASS / FAIL / INSUFFICIENT`.

Never release exact BLACKBOX metrics, counts, dates, subperiods, regimes, event examples, probabilities, feature attribution or failure analysis. Hidden BLACKBOX behavior may never justify a feature, threshold, scale, rule, instrument or model change.

Current completed BLACKBOX query count is exactly **3**. There is no query #4.

## 4. Certified mechanisms

### R1

`rmr_cross_scale_pullback_parent_integrity_v2`

Trend-like intact-parent pullback recovery. BLACKBOX query #1 `a9ba75c39e675ae6be17`: `PASS`.

### R2

`rmr_range_boundary_parent_integrity_v2`

Range-like intact-parent boundary re-entry. BLACKBOX query #3 `a7e7f0208512aa7c1f31`: `PASS`.

R1 and R2 are complementary state-restoration mechanisms, not generic interchangeable signals and not one automatically shared scalar axis.

### R5-C

`rmr_event_density_state_reversal_v2` passed detailed VALIDATION but BLACKBOX query #2 `4fa9bfa2ec38f16cd65f` returned `FAIL`. The identity is closed and may not be rescued from hidden-period behavior.

## 5. Closed synthesis and economic identities

### Unified parent-state router v1

`rmr_unified_parent_normal_state_router_v1` is closed at VALIDATION. Do not create router v2 by lane-specific scaling, axis-weight tuning, interaction search or automatic rescue.

### Existing simple economic translation

No tested trading implementation is certified.

- R1 economic v1/v2/v3 failed detailed VALIDATION before BLACKBOX.
- R2 economic v1 failed detailed VALIDATION before BLACKBOX.
- R1_A and R2 simple index-level execution were closed by the completed mechanism-to-execution diagnostic.
- probability-filter rescue is closed because frozen restoration probability is not a monotonic realized-return score.

### R1_B temporal impulse completion v1

`rmr_R1B_temporal_impulse_completion_v1` is **closed on DEV**.

The single preregistered temporal candidate used:

- certified R1_B S2-inside-S3 events only;
- unchanged next-bar entry;
- first subsequent parent-aligned S2 **confirmation close** as causal temporal completion;
- original S3 failure boundary;
- fixed 10bp cost;
- inherited 1200-bar safety cap;
- no probability filter or parameter search.

DEV result:

- mean net `+10.59bp`;
- mean improvement over structural baseline `+11.87bp`;
- positive mean-net years `5/6`;
- median net **`-32.11bp`**;
- win rate `37.10%`.

The preregistered positive-median gate failed. Therefore:

- identity decision = `DEV_CLOSE`;
- VALIDATION must remain unopened;
- do not delete or weaken the failed gate after the result;
- do not exit at the unobservable S2 extreme;
- do not add a probability filter to isolate right-tail events;
- do not choose 30/60/120/240 bars;
- do not tune entry, stop, target, cost, scale, year, regime or time of day;
- no automatic temporal v2 or R1 economic v4.

## 6. Current research boundary

There is currently **no empirical economic candidate authorized**.

If economic research continues, the next step must be a separate results-blind **payoff-object or instrument-theory program review**. A new identity must be materially independent of the closed temporal rule and must be preregistered before any new empirical output is opened.

Instrument mapping is only theory-eligible at present. Before any ETF/futures/options empirical study, freeze an instrument-specific source and cost-model contract covering relevant spread, basis, carry, liquidity, convexity/premium and execution conventions. Do not infer instrument viability from index-level price paths alone.

Broad R8/R9 indicator generation remains paused.

## 7. BLACKBOX and final-fit rules

No current economic research has BLACKBOX authority. Query #4 is neither scheduled nor authorized.

A future candidate may reach BLACKBOX only after its own explicitly authorized DEV/VALIDATION process and a separate governance decision. BLACKBOX may never participate in fitting, threshold selection, scale selection, timing selection, instrument selection or strategy rescue.

## 8. Optional future data

Do not wait for future data. Continue only work authorized by current authority. If newer data is later supplied, version the three-role map forward rather than declaring existing history consumed.

## 9. Repository hygiene

- Keep current authority concise and non-duplicative.
- Keep BLACKBOX receipts low-bandwidth.
- Do not copy BLACKBOX detail into docs, logs, charts or issues.
- Remove completed Actions workflows after bounded execution.
- Remove completed runners/tests/protocols/preanalysis from the current surface when no longer active; preserve them through execution commits plus compact history anchors.
- Keep decisive adjudications and compact receipts on the current surface.
- Do not create a second active repository.
- After substantial work, synchronize canonical `main` by fast-forward when the research branch is clean and a descendant of `main`.

Production authority remains `false`.
