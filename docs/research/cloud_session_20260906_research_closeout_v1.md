# 2026-09-06 Research Closeout — CSI1000 Overnight Open

## Acceptance

The current prediction-model research cycle is closed for the accepted identity.

The direction task and magnitude task were deliberately separated because the causal US-clock repair improved shock magnitude/ranking much more reliably than sign. Each component now has its own fresh evidence:

- **Direction:** `median_quantile_sign` was frozen after 2015-2020 expanding OOF and then robustly confirmed on the unseen 2026-01-05 through 2026-08-21 challenge after a 2015-2025 refit. Direction hit improved from 64.29% to 72.08%, balanced accuracy from 64.62% to 72.51%, with 16 candidate-only-correct versus 4 Ridge-only-correct disagreement days.
- **Magnitude:** `abs_frozen_clock_signed_prediction` was frozen before 2021-2025 and confirmed on that fresh window. Pooled corr(|gap|) improved from 0.31994 to 0.52187, while MAE and RMSE also improved.

The accepted research architecture is therefore:

- direction head = frozen conditional-median objective (`median_quantile_sign`);
- magnitude head = absolute value of the frozen clock-aware signed-gap model;
- signed recombination is secondary reporting only, not a new optimization target.

Formal acceptance record: `docs/governance/cloud_session_20260906_research_architecture_acceptance_v1.json`.

## Evidence boundary

All data through 2026-08-21 that has already been opened is consumed for the current identities. No further model search, threshold tuning, feature selection, loss tuning, calendar exceptions or return-based retuning may use these windows.

Post-2026-08-21 remains reserved and unread for the integrated identity. It must not be opened merely to improve the already accepted prediction heads.

## What is and is not confirmed

The two heads are **component-wise fresh confirmed** on their respective primary tasks. The exact combined two-head output has not been subjected to a single common fresh full-model challenge, so no stronger joint-fresh claim is made.

This is sufficient to establish the incumbent **research prediction architecture**, because direction and magnitude are declared separate primary tasks. It is not sufficient to claim a profitable trading strategy or production authority.

## Why production does not start with a return backtest

The target is the CSI1000 index open gap. The index level is not itself a tradable fill, and a fill at the open cannot capture the previous-close-to-open gap that has already occurred. The model can only acquire financial meaning after a causal decision-use contract specifies what tradable instrument consumes the prediction, when the decision and order occur, what fill is feasible, what later outcome is economically targeted, and what costs/risk constraints apply.

Therefore the next stage is **not more model development** and not an unconstrained return search. It is to freeze a financial decision-use contract, then run outcome-neutral strategy science acceptance and, if that passes, a post-training account audit without feeding account results back into the frozen model.

Production-readiness review: `docs/governance/cloud_session_20260906_production_readiness_review_v1.json`.

## Final status of this research cycle

`component_confirmed_incumbent_research_architecture`

Production authority: `false`.
