# Extreme-open vNext P1/P2 univariate DEV — cloud adjudication

Date: 2026-09-14

Research identity: `overnight_extreme_open_univariate_dev_v1`

Program: `overnight_extreme_open_conditional_transition_program_v1`

Frozen receipt: `docs/research/extreme_open_univariate_dev_v1_receipt.json`

Execution run: `34807096811`

## Decision

**`P1_DEV_PROGRESS_6_PREOPEN_EXTREME_PROPENSITY_STATES__P2_DEV_NO_TRANSITION_SURVIVOR`**

The result is deliberately split by phase.

- P1 establishes six high-selectivity **pre-open extreme-gap propensity** states on the frozen 2018-2020 DEV evaluation.
- P2 produces **zero** qualifying post-open continuation/reversal states across all 120 preregistered univariate hypotheses.
- No threshold, clock, candidate, bucket, target or multiple-testing rule is changed after seeing the result.
- No 2021-2025 reusable BLACKBOX detail is opened.
- `production_authority=false`.

## Execution integrity

The adjudicator consumed only the immutable P0 sufficient-statistics carrier:

`data/extreme_open_vnext_dev_sufficient_statistics_v1.json`

Carrier SHA256:

`d38483d9ef37e65506f858f6155482de32766a619c44ce799442d303c74cc321`

The result-free protocol and Issue #15 froze before outcome adjudication:

- inference comparator = disjoint `REST = PARENT - tested bucket`;
- product effect baseline = full candidate-specific PARENT cohort;
- raw p-value = two-sided Fisher exact;
- interval = Newcombe hybrid-score 95% probability-difference interval;
- BH q <= 0.10 over the complete preregistered family;
- pooled n >= 30 and each of 2018/2019/2020 n >= 5;
- target probability must exceed PARENT;
- effect size must satisfy `lift >= 12.5pp OR RR >= 1.5`;
- bucket-minus-REST direction must be positive in all three evaluation years;
- P2 additionally requires pooled mean forward-return direction to agree with continuation/reversal semantics.

The statistical-kernel regression suite passed before the receipt was generated. The run opened P1/P2 only; P3 remained false.

`V6A_expected_open_state` was not evaluated because no separately frozen leakage-free V6A prediction carrier exists for the required 2018-2020 window. This is an availability boundary, not negative V6A evidence.

## P1 — six retained DEV states

### Material high-open propensity

1. **B1 global risk — HIGH**
   - bucket probability: `31.8841%`
   - candidate-specific parent probability: `17.4451%`
   - lift: `+14.4390pp`
   - risk ratio: `1.8277x`
   - BH q: `1.4487e-14`

2. **B2 China-offshore — HIGH**
   - bucket probability: `36.0000%`
   - parent probability: `17.3160%`
   - lift: `+18.6840pp`
   - risk ratio: `2.0790x`
   - BH q: `5.3972e-17`

3. **causal prior volatility parent — HIGH**
   - bucket probability: `30.0699%`
   - parent probability: `17.3973%`
   - lift: `+12.6727pp`
   - risk ratio: `1.7284x`
   - BH q: `4.6958e-05`

### Material low-open propensity

4. **B1 global risk — LOW**
   - bucket probability: `49.0991%`
   - parent probability: `20.8791%`
   - lift: `+28.2200pp`
   - risk ratio: `2.3516x`
   - BH q: `2.5385e-32`

5. **B2 China-offshore — LOW**
   - bucket probability: `46.5217%`
   - parent probability: `20.9235%`
   - lift: `+25.5982pp`
   - risk ratio: `2.2234x`
   - BH q: `3.3436e-29`

6. **B4 driver coherence — LOW**
   - bucket probability: `48.1172%`
   - parent probability: `20.9841%`
   - lift: `+27.1331pp`
   - risk ratio: `2.2930x`
   - BH q: `3.3310e-35`

All six passed the complete frozen gate vector, including annual sample sufficiency and positive bucket-minus-REST direction in 2018, 2019 and 2020.

The asymmetry is economically meaningful: the strongest low-open buckets concentrate an approximately 21% parent event into roughly 46.5%-49.1% states, while the retained high-open buckets raise an approximately 17.3%-17.4% parent event into roughly 30.1%-36.0% states.

These are DEV progression states only. They are not yet reusable validated products or live calling rules.

## P2 — no retained post-open transition state

All **120** preregistered P2 hypotheses were evaluated. Survivor count: **0**.

A post-result aggregate, non-selection diagnostic was run only to describe the closed identity's failure structure. It did not rank or redesign candidates.

Failure counts across the 120 hypotheses:

- pooled `n >= 30` failed: **68**;
- each-year `n >= 5` failed: **72**;
- positive enrichment versus parent failed: **84**;
- material effect-size gate failed: **114**;
- Newcombe lower bound > 0 failed: **117**;
- positive bucket-minus-REST direction in every evaluation year failed: **114**;
- BH q <= 0.10 failed: **116**;
- forward-return direction gate failed: **80**.

There were **40** hypotheses with pooled bucket valid-return count equal to zero, largely because the globally frozen feature terciles and the already-conditioned extreme-gap samples need not populate every bucket. That is a consequence of the preregistered feature-only bucket geometry, not permission to refit edges inside event-sign subsets.

Only **1 / 120** hypotheses failed exactly one gate; that sole failure was the frozen **material-effect** gate. This does not authorize weakening the effect threshold.

At the family level, no 15-minute P2 family produced a BH-significant member. At 60 minutes, the two `EXTREME_DOWN` families each contained only two BH-significant members, but none passed the complete preregistered gate vector. The evidence therefore does not support a callable univariate continuation/reversal state at either fixed horizon.

## Interpretation

The new research framing is useful, but it splits the Overnight problem more sharply than the old broad factor view:

1. **Before the open**, extreme-gap propensity can be concentrated into large, stable state differences. This directly addresses the external consumer's need for sparse high-information conditions.
2. **After an extreme open has already occurred**, the current one-dimensional gap geometry / C1 / C2 / B4 shelf does not produce a robust conditional continuation-versus-reversal state under the same strict consumer-oriented standard.

P2 zero-survivor evidence is not a claim that intraday continuation/reversal is impossible. It is a rejection of this exact univariate family under this exact frozen event gate, buckets, clocks and DEV contract.

Do not rescue P2 by:

- refitting terciles only inside `EXTREME_UP` or `EXTREME_DOWN` days;
- lowering the +/-30bp event gate;
- choosing only the better 15m or 60m clock;
- weakening the 12.5pp / 1.5x materiality standard;
- dropping weak years;
- decomposing 2021-2025 BLACKBOX behavior;
- adding ad hoc post-open indicators under this identity.

## Next authorized research direction

A separate P3 identity may be frozen **only for P1 pre-open survivor intersections**.

The result-free candidate-construction rule should be mechanical and small:

- for `EXTREME_UP`, take all two-way intersections among the three same-target P1 survivors: `B1_HIGH`, `B2_HIGH`, `prior_volatility_HIGH`;
- for `EXTREME_DOWN`, take all two-way intersections among the three same-target P1 survivors: `B1_LOW`, `B2_LOW`, `B4_LOW`.

That creates exactly **3 + 3 = 6** candidate intersections, with no candidate search.

A P3 successor should test whether an intersection provides **incremental concentration beyond each constituent bucket**, not merely whether it remains significant versus the unconditional parent. It requires a separately frozen protocol and a new mechanical carrier before any intersection outcome is read.

Because P2 has no survivor, **no P2-derived post-open intersection is authorized** from this result.

Reusable 2021-2025 validation remains sealed. Consumer integration remains premature.

`production_authority=false`.
