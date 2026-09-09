# Overnight repository scope restoration — 2026-09-09

## Active repository identity

`factorlab-overnight-open-lab` is an **Overnight/Open-specific** research repository.

In-scope research includes only work whose scientific object is directly tied to the overnight/open process, including:

- CSI1000 previous-close -> next-open direction and gap magnitude;
- high-open / low-open prediction and bounded successors;
- post-open Gap-Fill identities defined from the observed opening gap;
- offshore-China / US-market predictors only when used to explain or predict the overnight/open object;
- data, clocks, provenance, validation, receipts, tests, and workflows required by those identities.

The existing Gap-Fill V2 / V2.1, OHR, and overnight direction/magnitude evidence therefore remains native Overnight evidence.

## Explicitly out of scope

This repository must not again become a general trend-reversal / mean-reversion laboratory. In particular, do not create current authority here for generic:

- parent-trend pullback recovery;
- range-boundary re-entry;
- regime-conditioned residual mean reversion;
- generic multiscale reversal routing;
- intraday HighVol state routing unrelated to the overnight/open object;
- broad RMR payoff-object or execution research not anchored to an Overnight identity.

Such work belongs in the active trend-reversal / mean-reversion repository/project and may only be referenced here when strictly necessary to document historical contamination or an explicit cross-project boundary.

## Restoration provenance

The repository identity was changed by commit
`58dfe8ff8095033c8c2d0c4ce0b60cce20f1bd2a` from a bounded Overnight specialist repository into a broad reversal / mean-reversion program. That was a scope error.

The last mainline state immediately before that identity switch is commit
`b4063a1509c609986d8351598136eb5024fc7fc6`.

On 2026-09-09 the working tree was restored to that pre-switch tree by commit
`91b9023e09b3a8f7630807d60e9f223a6c771932`. The later misrouted RMR commits remain in Git history for auditability but are not current repository authority.

Scientifically useful RMR evidence from the contaminated period was migrated to `staryocean0/factorlab-star50-filter-lab` under `docs/archive/misrouted_rmr_from_overnight_20260909/`, with an active synthesis at `docs/research/migrated_rmr_findings_20260909.md`.

## Legitimate Overnight result recovered from post-switch history

One post-switch commit was **not** RMR contamination: `c34c74809d19211124c4e66f1afb29ade86b6cb3` contains only the authorized local V2.1 DEV result for the already-frozen Overnight identity `gap_fill_v2_1_regime_conditioned_successor`.

The receipt itself records execution on pre-switch Overnight code commit `b4063a1509c609986d8351598136eb5024fc7fc6`, whose parent is the V21 DEV execution-freeze commit `2ec24962b592d93025a15a7251712ebe163ef21f`; `b4063a...` only added the local execution handoff and changed no frozen scientific code.

Commit `c34c748...` added exactly two legitimate Overnight output files:

- `docs/research/local_gap_fill_v21_dev_selection_receipt_v1.json`;
- `docs/governance/local_gap_fill_v21_dev_data_usage_v1.json`.

Those exact historical Git blobs were restored byte-for-byte to current `main` by commit `c4fab7a175cab34dce8fd09f215545e9083c2c7b`. No empirical rerun occurred during restoration.

Cloud re-adjudication is recorded in `docs/research/gap_fill_v21_dev_cloud_adjudication_20260909.md`. The result is `V21_DEV_no_P2_successor`: the frozen primary yearly sample-sufficiency gate failed because 2017 had only 15 CSI500-high >10bp primary rows versus the preregistered minimum of 20. No parameter freeze was written and Audit A/B remain sealed.

This is the only post-switch result explicitly restored by this scope-recovery review. A post-switch commit must not be imported merely because it contains something scientifically interesting; it must first be proven to belong to a pre-existing Overnight identity and to preserve its frozen evidence boundary.

## Authority boundary

This restoration changes repository scope, not scientific evidence labels or production permissions.

- Existing Overnight/Gap-Fill evidence labels remain as recorded in their native receipts.
- Misrouted RMR state, BLACKBOX ledgers, next actions, and production statements are not Overnight authority.
- The restored V21 DEV result is Overnight authority only for its own frozen V2.1 identity.
- `production_authority=false` remains unchanged.
