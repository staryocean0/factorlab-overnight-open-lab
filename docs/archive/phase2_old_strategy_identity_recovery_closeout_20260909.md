# Phase II old-strategy identity recovery — fail-closed closeout

Date: 2026-09-09

Original task: GitHub issue #11, `P2 old strategy identity recovery and paper-core lineage completion`.

## Decision

`INSUFFICIENT_EVIDENCE_TO_RECOVER_EXACT_IDENTITY`

This provenance task is complete and closed. The acceptance gate was **not** met, so no empirical redevelopment is authorized from it.

`production_authority = false`.

No DEV/VALIDATION experiment was created or run for this task. No BLACKBOX source was opened and no BLACKBOX query was created.

## What had to be recovered

The original acceptance contract required both:

1. one uniquely recoverable historical strategy contract covering financial target, factor universe, universe/filter, rebalance clock, label, fill semantics, score normalization/direction, ranking, TopN/weighting, holding period, blocked buy/sell semantics, T+1, costs and benchmark; and
2. a `CORE_SPATIAL_H20` lineage manifest with 48 auditable paper-core identities, each carrying factor id, paper identity, source artifact, implementation mapping, Stage6 position and validation status, without mixing teacher/context channels.

Partial recollection or reconstruction by inference was explicitly insufficient because the requested output was a reproducible historical identity.

## Evidence reviewed

The related historical source repository was inspected at:

- repository: `staryocean0/factorlab-multifactor-stock-lab`
- source main commit observed during closeout: `af2e478aaff5c8ef7f753424b57fd2d19019f248`
- tree: `633fde90a3351bf981a87bbe38c4bb06eb9957ed`

High-authority/current source artifacts examined included:

- `docs/INDEX.md`
- `docs/ops/reaka_strategy_authority_registry@113.0.json`
- `docs/ops/reaka_multifactor_current_manifest@1.2.json`
- `docs/ops/reaka_multifactor_semantic_ontology@1.0.json`
- `docs/ops/post_training_account_audit@1.1.json`
- `docs/ops/reaka_current_k1_account_ledgers@1.3.json`
- `docs/ops/reaka_factor_parallel_consumed_formula_registry@2.0.json`
- `docs/ops/reaka_paper_v1_whitepaper.md`
- `docs/user/strategy_slice_rebuild_workflow.md`

Repository code/search and commit search were also attempted for the exact historical names `CORE_SPATIAL_H20`, `CORE_SPATIAL`, `H20`, `paper-core`, `REAKA`, and related strategy-contract terms.

## What can be established without inference

The surviving source does contain auditable **current** REAKA account identity. In particular, `reaka_current_k1_account_ledgers@1.3.json` names:

- strategy: `REAKA_D5_H20_R5_CURRENT_GENERATION_V1`
- model: `d8-h8-K1-r0_fit_prefix_successor_incumbent`
- account policy: `N30_equal_backfill_unconstrained`
- decision clocks: `14:30`, `14:45`
- slippage multiplier: `1.0`

Those fields are useful provenance, but the artifact explicitly describes the current/new strategy. They cannot be substituted for the requested **old** strategy identity without creating an unsupported historical equivalence.

The current semantic authority also separates factor, observable context, latent Stage6 representation/operator capacity, score and account objects. This means teacher/context channels may not be silently relabeled as paper-core factor identities.

The consumed-formula registry currently exposes 36 formula identities across two completed rounds. It does not establish a 48-row `CORE_SPATIAL_H20` paper-core lineage.

The paper whitepaper documents a paper-faithful architecture and distinguishes a paper daily Alpha158 benchmark contract from a project monthly adapter with 172 stock-level nonfinancial features. Neither is an auditable 48-identity `CORE_SPATIAL_H20` manifest.

## Missing decisive evidence

No source artifact located in the accessible repository state establishes all of the following simultaneously:

- the requested historical object named `CORE_SPATIAL_H20`;
- exactly 48 paper-core factor identities;
- their paper identities and source artifacts;
- implementation mappings;
- Stage6 positions;
- validation statuses;
- a unique mapping back to one complete old account/strategy contract.

Likewise, the available current account contracts do not prove that their TopN, clocks, costs, execution semantics, model and target are identical to the old strategy requested by issue #11.

## Why this is fail-closed rather than reconstructed

Filling the gaps from current REAKA conventions, from the 36 consumed formulas, from Alpha158, or from names such as `H20` would manufacture lineage. That would violate the task's own acceptance requirement that the historical identity be uniquely recovered and auditable.

Therefore the historical identity is not declared recovered.

## Governance disposition

- issue #11: close as completed provenance investigation with insufficient exact evidence;
- old `IN PROGRESS` progress note: remove from the current research surface; Git history preserves it;
- do not create an empirical candidate from this task;
- do not open Stage5/Stage6 or model/account execution in the REAKA source project merely to manufacture missing provenance;
- do not read BLACKBOX for this task;
- if an original authoritative artifact containing the exact 48-row lineage and old strategy freeze is later supplied, it may support a **new provenance-only reopening**, not automatic empirical redevelopment.

This closeout resolves the stale design without pretending the missing identity was recovered.
