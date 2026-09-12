# E1 downstream timing adapter v1 — result-free preanalysis

Date: 2026-09-12

Research identity: `overnight_c1_b4_timing_confidence_adapter_v1`

Product family: `OFP-E1_timing_adapter`

## Question

Can the already-validated B4 pre-open driver-coherence coordinate improve the utility of the already-validated C1 15-minute timing direction by acting only as a causal abstention overlay after the opening gap is observed?

This is deliberately not a new alpha-model search. C1 remains the only directional source. B4 is allowed only to say whether the C1 direction may be acted on; it may not create an alternate direction, fitted weight, threshold family, or multi-factor score.

## Authority-bearing inputs

The adapter may consume only:

1. OFP-A2 observed opening geometry: `observed_gap_rvol = gap / rvol20`, available after the opening observation.
2. Validated C1 15m continuous product: `trend_gap_interaction = trend20_rvol * observed_gap_rvol`, whose validated target is 09:35→09:50 and whose frozen scientific direction is negative.
3. Validated B4 continuous `driver_coherence`, using exactly the frozen lagged-60-China-trading-day RMS normalization and equal three-channel coherence formula from `docs/governance/driver_coherence_open_gap_blackbox_protocol_v1.json`.

Excluded from v1 by design:

- A1 expected-open model outputs: not required for this first adapter identity;
- A4 Gap-Fill: still carries its existing evidence label / true-fresh wait and is not needed to answer this mechanism question;
- C2: frozen but unopened/deferred;
- C3 and D1: both joint BLACKBOX FAIL and provide no validated product authority;
- Opening Surprise A3 and V2.1 P2: closed identities;
- any hidden BLACKBOX behavior from queries 1–5.

## Frozen mechanism

C1 supplies a raw directional score for the validated 15-minute horizon:

`c1_direction_score = -trend_gap_interaction`

with the deterministic action mapping:

- positive score → `+1`
- negative score → `-1`
- exactly zero → `0`

B4 is not used as a direction predictor for the 09:35→09:50 return. Instead it is compared with the realized opening-gap direction:

`driver_alignment = driver_coherence * sign(observed_gap_rvol)`

Interpretation:

- `driver_alignment >= 0`: the pre-open driver-coherence direction is not opposed to the realized opening-gap direction;
- `driver_alignment < 0`: broad driver direction is opposed to the realized opening-gap direction.

The only new adapter action is therefore:

`candidate_action = c1_action if driver_alignment >= 0 else 0`

The comparator is:

`comparator_action = c1_action`

This is a single low-capacity abstention route. The zero boundary is semantic and frozen before any adapter outcome is read. No magnitude threshold, quantile, fitted weight, alternate sign rule, or alternate horizon is eligible.

## Causal clock

Decision clock: 09:35 China time.

By 09:35:

- the opening gap used by A2/C1 is already observed;
- trailing trend and volatility inputs are causal;
- B4 uses only frozen pre-open external-source cutoffs;
- the 09:35→09:50 outcome has not occurred.

## Development evidence

Detailed adapter development is limited to 2015–2020 and is explicitly retrospective development material, not fresh OOS. Results must be reported by natural year 2015, 2016, 2017, 2018, 2019, 2020 plus pooled.

No year may be used to alter the frozen formula. This is a fixed-formula diagnostic, not a sequential parameter rebuild.

2009–2014 cannot be manufactured as Strategy Slice Rebuild sessions because authority-bearing CSI1000 opening-state inputs did not contemporaneously exist. Therefore this identity cannot acquire strategy/account authority from this repository's development exercise. Any later executable consumer strategy must be a separate identity under the then-current Strategy Slice Rebuild + SSA + account-audit contract.

## Utility target and diagnostics

Only target:

`ret_0935_0950 = close_0950 / close_0935 - 1`

This target is chosen solely because C1 is validated only for this horizon. There is no 30m/60m search.

This phase measures factor-adapter utility, not executable PnL. For each complete-case day define:

`comparator_signed_utility = comparator_action * ret_0935_0950`

`candidate_signed_utility = candidate_action * ret_0935_0950`

Primary progression quantity:

`delta_mean_signed_utility = mean(candidate_signed_utility) - mean(comparator_signed_utility)`

Additional preregistered diagnostics:

- complete-case count;
- candidate active-day count and coverage;
- comparator active-day count;
- candidate active-day hit rate;
- comparator hit rate;
- annual and pooled mean signed utility;
- annual and pooled delta mean signed utility.

These are index-return diagnostics. They are not trade PnL, do not include costs, and do not claim that the cash index is directly tradable.

## Progression rule

Sufficiency gates:

- each natural year complete cases >= 150;
- each natural year candidate active days >= 30.

Scientific progression requires all of:

- pooled `delta_mean_signed_utility > 0`;
- at least 4 of 6 annual deltas > 0;
- median annual delta >= 0.

There is no minimum economic effect-size threshold beyond strict positivity for progression. If the gates fail, close this adapter identity. Do not rescue it with a different coherence threshold, B4 magnitude weighting, alternate horizon, A4, A1, C2, C3, D1, or PnL-guided redesign.

If the gates pass, the maximum authority is:

`retrospective_factor_utility_adapter_candidate`

It still grants no strategy, instrument mapping, position sizing, account, routing, production, or fresh-OOS authority.

## Stock-selection boundary

OFP-E2 is not part of this identity. A market-level adapter may later scale or abstain an already-frozen stock-selection strategy, but it may not become stock-specific ranking alpha inside this repository. Any E2 experiment requires its own result-free identity, frozen downstream baseline, stock universe, execution/cost contract, and consumer-side evidence workflow.

`production_authority=false`.
