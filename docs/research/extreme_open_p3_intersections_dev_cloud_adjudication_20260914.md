# Extreme-open vNext P3 pre-open intersections — cloud adjudication

Date: 2026-09-14

Research identity: `overnight_extreme_open_preopen_survivor_intersections_dev_v1`

Execution run: `34807745692`

Carrier: `data/extreme_open_p3_intersection_sufficient_statistics_v1.json`

Carrier SHA256: `0c97062e9b4d96570098ba97d1465de384387f6d6dab7a052e89483ad4a30c77`

Receipt: `docs/research/extreme_open_p3_intersections_dev_v1_receipt.json`

## Decision

**`P3_DEV_PROGRESS_ALL_6_INCREMENTAL_PREOPEN_INTERSECTION_STATES`**

All six preregistered same-target two-way intersections pass the complete frozen P3 gate. The result is stronger than inherited P1 significance: every survivor also passes the two disjoint incremental comparisons against the non-overlap portions of both constituent buckets, the preregistered BH families, the incremental materiality test versus the stronger full constituent, and positive direction in each of 2018, 2019 and 2020.

P1 reconstruction parity is exact before the P3 carrier is accepted. No bucket edge is refit, no candidate is added/dropped, and no P2/post-open intersection is opened.

`production_authority=false`.

## Frozen six-state result

| callable DEV state | target | intersection probability | parent probability | parent lift | parent RR | incremental lift vs stronger constituent | incremental RR | primary BH q |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `UP_B1_HIGH_X_B2_HIGH` | EXTREME_UP | 44.7761% | 17.3661% | +27.4100pp | 2.5784x | +8.7761pp | 1.2438x | 4.61e-17 |
| `UP_B1_HIGH_X_VOL_HIGH` | EXTREME_UP | 51.6667% | 17.4451% | +34.2216pp | 2.9617x | +19.7826pp | 1.6205x | 1.82e-10 |
| `UP_B2_HIGH_X_VOL_HIGH` | EXTREME_UP | 54.5455% | 17.3160% | +37.2294pp | 3.1500x | +18.5455pp | 1.5152x | 6.59e-11 |
| `DOWN_B1_LOW_X_B2_LOW` | EXTREME_DOWN | 64.3411% | 20.9841% | +43.3570pp | 3.0662x | +15.5148pp | 1.3178x | 1.30e-34 |
| `DOWN_B1_LOW_X_B4_LOW` | EXTREME_DOWN | 57.7381% | 20.9841% | +36.7540pp | 2.7515x | +8.9118pp | 1.1825x | 4.81e-36 |
| `DOWN_B2_LOW_X_B4_LOW` | EXTREME_DOWN | 54.6448% | 20.9841% | +33.6607pp | 2.6041x | +6.5277pp | 1.1357x | 6.28e-35 |

The constituent-increment BH tests also pass for all twelve intersection-versus-exclusive comparisons. Their adjusted q-values range from approximately `6.94e-09` through `1.26e-03`.

## Interpretation

This is the first stage in the Overnight line that directly solves the consumer-interface problem that motivated vNext.

The broad parent event rates are only about 17%-21%. The retained P3 states instead identify sparse pre-open conditions in which the same material opening event occurs roughly 45%-64% of the time on the frozen 2018-2020 DEV surface. The gain is not merely the fact that each underlying P1 bucket was useful: the intersection itself adds another 6.5-19.8 percentage points over the stronger constituent state.

This supports a callable **pre-open material-gap propensity state** product concept. It does not support a post-open continuation/reversal product: P2 remains closed with zero survivor.

## Multi-state overlap semantics

The six states are not mutually exclusive. If all three retained EXTREME_UP parent conditions are high on one day, all three UP pairwise states fire; analogously, all three DOWN pairwise states can fire together.

The DEV evidence does **not** authorize:

- choosing the historically highest-probability pair as a winner;
- synthesizing a new three-way probability from the overlapping pair states;
- averaging or multiplying the pair probabilities;
- converting number-of-fired-pairs into an empirically calibrated probability;
- suppressing one valid state because another valid state also fires.

Therefore P4 must package the result as a **set-valued state interface**. It may expose every exact state that fires, each with its own frozen identity/evidence metadata. If multiple states fire, the consumer receives multiple evidence objects; no combined probability is claimed unless a separately frozen future identity validates one.

## P4 direction

A result-free P4 packaging identity is now permitted. It should be engineering/contract work rather than another outcome search.

The interface should have two layers:

1. `validated_dev_intersection_states`: zero or more of the six exact P3 state IDs that fire before the China open;
2. `supporting_univariate_states`: the six P1 constituent states, exposed for explanation/lineage rather than as a mechanism to override P3.

Required default behavior:

- if no P3 intersection fires: primary action = `ABSTAIN`;
- if one or more P3 intersections fire: return the complete set of fired states and their target direction (`EXTREME_UP` or `EXTREME_DOWN`);
- do not return a post-open continuation/reversal instruction; P2 authority is absent;
- do not map to a position, leverage, security, order or execution clock;
- do not relabel DEV probabilities as live calibrated probabilities.

This creates a stable consumer contract without introducing a post-result winner selection.

## Evidence boundary and next scientific gate

P3 remains **DEV progression material only**. It is not a reusable validated product yet.

After P4 fixes the exact state identifiers, edge definitions, runtime inputs, overlap semantics, abstention behavior and output schema, P5 may separately preregister one low-bandwidth reusable 2021-2025 validation for the exact six-state set. Reuse of 2021-2025 is not independent OOS; the purpose would be reproducibility/stability rejection, not fresh authority.

No P5 query is authorized by this adjudication alone.

`production_authority=false`.
