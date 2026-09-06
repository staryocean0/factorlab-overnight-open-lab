# OHR-07 cloud review — 2026-09-06

## Decision

OHR-07 completed successfully as a frozen one-candidate development selection, but the candidate failed the preregistered eligibility gates.

Decision: `retain_incumbent_ohr07_candidate_rejected`.

The 2026 repeat blackbox remains sealed and OHR-03 remains unopened.

## Execution

Cloud run: `34026047565`.

- exact OHR-05 source SHA passed;
- theme validator passed;
- pytest: 24 passed;
- exactly one candidate was evaluated;
- no parameter, quantile, threshold, class-weight, ticker, representation or trading-return search occurred;
- common OOF inventory: 2,424 rows;
- `2026_rows_loaded=false`, `2026_blackbox_opened=false`;
- aggregate receipt committed as `docs/research/cloud_session_20260906_cloud_offshore_china_ohr07_dev_receipt_v1.json`.

## Candidate result

Candidate: `broad_china_specific_tail_weak_piecewise`.

Common-inventory incumbent versus candidate:

- recall_up: `0.625663 -> 0.627784` (+0.21 percentage points);
- direction hit: `0.717409 -> 0.712459` (-0.50 pp);
- balanced accuracy: `0.700745 -> 0.697079` (-0.37 pp);
- recall_down: `0.775827 -> 0.766374` (-0.95 pp);
- >10bp high-open recall: unchanged at `0.658375`;
- >30bp high-open recall: `0.711921 -> 0.708609` (-0.33 pp);
- annual recall_up improvement: 5/10 years, below the frozen 6/10 gate.

The candidate therefore failed direction-hit, balanced-accuracy, >30bp material-recall and 6/10-year gates.

Paired disagreements were unfavorable:

- candidate correct / incumbent wrong: 15;
- incumbent correct / candidate wrong: 27;
- net correct-count change: -12.

Prediction-flip morphology explains the loss:

- incumbent-down -> candidate-up: 29;
- rescued highs: 8;
- new false highs: 21;
- added-up precision: 27.6%;
- incumbent-up -> candidate-down: 13;
- lost highs: 6;
- repaired false highs: 7.

So the offshore signal is not strong enough to justify directly flipping many low-open calls.

## Important mathematical failure mode

The candidate feature was zero whenever `prev_last_hour >= 0`, but the model refit all 14 coefficients jointly. Therefore adding one piecewise feature altered the original 13 coefficients and changed predictions even outside the financial state that OHR-06 supported.

Outside prior-tail-weakness:

- incumbent hit: `0.712848`;
- candidate hit: `0.706656`;
- incumbent balanced accuracy: `0.712833`;
- candidate balanced accuracy: `0.707677`.

Those changes cannot be attributed to the offshore feature's direct value, because its value is zero there. They are coefficient-refit spillover.

Inside prior-tail-weakness the direct effect was also weak:

- recall_up: `0.503817 -> 0.506361` (+0.25 pp);
- direction hit: `0.722615 -> 0.719081`;
- >30bp recall: `0.605442 -> 0.598639`.

Therefore OHR-07 itself is rejected.

## One final low-degree-of-freedom mathematical test is justified

The OHR-06 mechanism evidence remains valid: `broad_china_specific_vs_spy` separated actual high versus low opens in the preregistered unresolved slice across 8/10 years. OHR-07 shows that **jointly refitting the entire Median model is a poor way to isolate that new information**.

A final development candidate may therefore test a frozen-base residual overlay:

1. fit the incumbent 13-feature Median model exactly as before on each training fold;
2. freeze its fitted coefficients for that fold;
3. form `g = broad_china_specific_vs_spy * 1(prev_last_hour < 0)`;
4. fit exactly one no-intercept median-regression coefficient `beta` to training residuals `gap - incumbent_score` using `g`;
5. candidate score = `incumbent_score + beta * g`.

When `g=0`, candidate and incumbent scores must be bitwise/numerically identical by construction. No original coefficient may move. This is not a new data-source or feature search; it is a one-parameter isolation test motivated by the observed OHR-07 coefficient-refit failure.

No beta grid, clipping rule, sign threshold, intercept, alternative quantile or regularization may be searched. If this frozen-base overlay also fails the existing non-sacrifice gates, the offshore-China route closes for the current research identity.

2026 remains sealed throughout this test.
