# OFP-C3 Previous China Session Shape — six-year DEV adjudication

Date: 2026-09-12

Research identity: `overnight_previous_session_last_hour_conditioned_open_state_v1`

Receipt: `docs/research/cloud_previous_session_shape_dev_diagnostic_v1.json`

Protocol: `docs/governance/previous_china_session_shape_v1_protocol.json`

## Frozen question

Does the previous mainland session's final-hour return change the short-horizon meaning of the same normalized CSI1000 opening gap, after controlling for simpler causal parents and the validated C1 trend-gap interaction?

Frozen candidate:

`last_hour_gap_interaction = (prev_last_hour / rvol20) * (gap / rvol20)`

No `prev_afternoon` search, alternate session-window search, threshold/bucket search, horizon search, trading-return optimization, or 2021-2025 BLACKBOX opening occurred.

## Evidence boundary

Detailed development only: `2015-01-05..2020-12-31`.

The parity-validated runtime text carrier was used. The receipt records `target_rows_after_2020_loaded=false` and `reusable_blackbox_2021_2025_opened=false`.

## Pre-registered progression rule

A horizon may be retained only if all are true:

1. pooled partial correlation and pooled standardized candidate coefficient share a sign;
2. at least 4 of 6 annual standardized candidate coefficients share the pooled sign;
3. the median annual standardized candidate coefficient shares the pooled sign;
4. pooled delta R2 is positive;
5. at least 4 of 6 annual delta R2 values are positive.

Passing this rule creates development progression material only. It does not validate a product, authorize a reusable BLACKBOX query, authorize a categorical session-shape view, or grant production authority.

## Results

### 09:35 -> 09:50

- pooled partial correlation: `+0.0186368471`
- pooled standardized candidate coefficient: `+0.0191634143`
- pooled delta R2: `+0.0003321276`
- annual coefficient signs: `- - - + + -`
- annual coefficients matching pooled positive sign: `2/6`
- median annual standardized coefficient: approximately `-0.00504`
- annual positive delta R2 count: `6/6`

Verdict: **FAIL**.

The pooled sign is not supported by the required annual sign count, and the annual median has the opposite sign.

### 09:35 -> 10:05

- pooled partial correlation: `+0.0532898010`
- pooled standardized candidate coefficient: `+0.0545627398`
- pooled delta R2: `+0.0026924738`
- annual coefficient signs: `- + - + + +`
- annual coefficients matching pooled positive sign: `4/6`
- median annual standardized coefficient: approximately `+0.02688`
- annual positive delta R2 count: `6/6`

Verdict: **PASS progression gate**.

### 09:35 -> 10:35

- pooled partial correlation: `+0.0494553421`
- pooled standardized candidate coefficient: `+0.0508874869`
- pooled delta R2: `+0.0023419691`
- annual coefficient signs: `- + + + - +`
- annual coefficients matching pooled positive sign: `4/6`
- median annual standardized coefficient: approximately `+0.01097`
- annual positive delta R2 count: `6/6`

Verdict: **PASS progression gate**.

## Main-agent adjudication

Formal decision:

`C3_DEV_PROGRESS_30M_AND_60M_SHARED_CONTINUOUS_COORDINATE`

The evidence supports retaining the same continuous previous-session-final-hour x opening-gap interaction as development progression material at both 30m and 60m. The 15m horizon is rejected for this identity.

The preregistration did not define a result-free tie-breaker for choosing exactly one horizon if multiple horizons passed. Therefore no post-hoc 30m-vs-60m winner is selected. Any successor validation must preserve this fact rather than cherry-picking the larger pooled metric.

Magnitude is uneven across years, with 2018 visibly stronger than several other years. This is recorded as a stability caution only; concentration was not a preregistered rejection gate and is not added after seeing results.

## Authority consequences

- retain C3 continuous coordinate as **30m + 60m DEV progression material**;
- reject the C3 15m horizon;
- do not create high/low session-shape buckets;
- do not search `prev_afternoon` or alternate session clocks as a rescue;
- do not select a unique 30m or 60m winner post hoc;
- do not open 2021-2025 reusable BLACKBOX under the parent identity;
- a later BLACKBOX requires a separately frozen successor identity and result-free protocol;
- C2 60m BLACKBOX remains frozen, unopened, and deferred;
- production authority remains false.
