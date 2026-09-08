# R7 Stage-1 preanalysis — directional path-energy asymmetry

Research identity: `R7_directional_path_energy_asymmetry_stage1_v1`

This is a new broad-program lane, not an R6 repair and not an R1/R5-C combination.

## Question

For two completed waves with similar severity, does the **directional balance of realized movement before the wave began** change the probability that the wave next reverts rather than extends?

The motivating distinction is simple: a sharp down-wave can arrive after a path that was already dominated by downward movement, or after a path with substantial opposing movement. The completed wave can look equally severe in both cases, while the pre-wave state is different.

## Frozen event context

- instrument: CSI1000 `000852.SH`;
- common 1m source and SHA remain unchanged;
- DEV: 2015-01-05..2019-12-31;
- chronological stability: 2020-01-01..2022-12-31, not fresh;
- 2023-2025 internal reserve remains unopened;
- only common frozen directional-change scales `S1` and `S2` are reported;
- outcome remains the symmetric same-scale first-passage event used by R5/R6.

## One score only

For each completed wave with direction `d in {-1,+1}`:

1. take the **240 observed 1m rows immediately before the wave start**, not before confirmation;
2. form only within-session one-bar log returns; overnight/session-boundary returns are excluded;
3. require at least 120 valid within-session returns;
4. split squared-return energy by whether the one-bar return sign agrees with `d`;
5. define

`raw_energy_imbalance = (E_same - E_opposite) / (E_same + E_opposite)`.

The current wave itself contributes zero rows to this score. No future extremum is used.

The raw score is normalized with the preceding 100 completed same-scale score observations using median/MAD, excluding the current observation. The continuous robust z-score is the only primary R7 state variable.

## Tiny model budget

At each of S1 and S2, compare exactly:

- severity-only;
- severity + directional-energy-z.

Use the same `StandardScaler + LogisticRegression(C=1,l2,lbfgs,max_iter=1000)` family used by the common shallow program. No hyperparameter search, probability calibration or binary threshold.

## Frozen review gate

R7 may become **candidate for cross-lane program review only** if the augmented model:

- has at least 200 resolved stability events at each scale;
- has at least 50 resolved events in each of 2020/2021/2022 at each scale;
- improves pooled Brier at both S1 and S2;
- improves pooled log loss at both S1 and S2;
- improves annual Brier in at least 2 of 3 years at each scale;
- has the same non-zero fitted score-coefficient sign at S1 and S2.

A pass does not auto-promote a third mechanism. It only triggers explicit comparison against R1 and R5-C.

## Explicitly forbidden

Do not, after seeing results:

- change the 240-row pre-wave window;
- use current-wave rows inside the state score;
- add L1/path-efficiency alternatives;
- add exponential decay or sign-count variants;
- search score thresholds;
- use S1 only if S2 fails;
- combine with R1, R5-C, R6-A or R6-B;
- search directional-change scales;
- open 2023-2025;
- optimize trading PnL;
- use a deep model to rescue failure.

If the frozen score fails, close R7 Stage-1 v1 and return to broad direction discovery.

Production authority: `false`.
