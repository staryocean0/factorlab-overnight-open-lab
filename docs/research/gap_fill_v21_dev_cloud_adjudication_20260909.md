# Gap-Fill V2.1 V21-DEV — restored cloud adjudication — 2026-09-09

Research identity: `gap_fill_v2_1_regime_conditioned_successor`.

## Decision

**`V21_DEV_no_P2_successor`**

The frozen V21 DEV execution is accepted as valid Overnight evidence. No P2 candidate is eligible for promotion. No V21 parameter freeze exists. **Audit A remains sealed and is not authorized to open.** Audit B and the external reserve remain sealed as well.

This is not a trading or production result. `production_authority=false`.

## Why this evidence is valid after repository scope restoration

The Overnight repository was later contaminated by a broad reversal / mean-reversion scope change and was subsequently restored to its pre-switch Overnight tree. That restoration also removed one legitimate Overnight result commit that had been written after the scope switch.

The legitimate result commit is:

`c34c74809d19211124c4e66f1afb29ade86b6cb3`

Its commit message records that the authorized frozen 2015-2018 CSI300/CSI500 DEV runner completed, no P2 candidate was eligible, no parameter freeze was written, and Audit A/B remained sealed.

That result commit added exactly two files and changed no protocol, runner, gate, model family, source contract, RMR artifact or future-data state:

- `docs/research/local_gap_fill_v21_dev_selection_receipt_v1.json`
- `docs/governance/local_gap_fill_v21_dev_data_usage_v1.json`

The original Git blobs from that commit were restored byte-for-byte into the current Overnight `main` at commit:

`c4fab7a175cab34dce8fd09f215545e9083c2c7b`

No empirical rerun was performed during restoration.

## Execution identity audit

The restored DEV receipt records:

- execution/code commit: `b4063a1509c609986d8351598136eb5024fc7fc6`;
- frozen source parent SHA256: `25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`;
- candidate order unchanged;
- attempted candidate count: `3`;
- selected candidate: `null`;
- full-DEV parameter freeze written: `false`;
- feature search: `false`;
- candidate addition/reordering: `false`;
- model-class search: `false`;
- hyperparameter search: `false`;
- beta-bound/regularizer search: `false`;
- probability calibration: `false`;
- binary threshold selection: `false`;
- trading return used: `false`;
- raw/row-level outputs written to repository: `false`;
- Audit A opened: `false`;
- Audit B opened: `false`;
- external reserve opened: `false`;
- 2014Q4 supporting crosscheck opened: `false`;
- CSI1000 post-2026-08-21 outcomes opened: `false`.

The execution code commit `b4063a...` is one commit after the frozen execution point `2ec24962b592d93025a15a7251712ebe163ef21f`. The only change in `b4063a...` is the local execution handoff document; scientific code and frozen gate blobs were not modified.

## Frozen sample-sufficiency gate

The primary DEV cell is:

`CSI500 high, abs_gap > 10bp`, evaluated at 15m and 60m.

The preregistered DEV rule requires:

- pooled primary rows >= `60`; and
- primary rows >= `20` in **each** validation year 2016, 2017 and 2018.

The actual frozen V21 DEV primary inventory is:

- 2016: `68`;
- 2017: `15`;
- 2018: `52`;
- pooled: `135`.

The pooled minimum passes, but 2017 fails the per-year minimum. Therefore sample sufficiency is `false`.

The pure frozen evaluation kernel explicitly returns `status=evidence_insufficient`, `eligible=false`, and does not evaluate promotion gates when this sample gate fails.

All three frozen candidates therefore remain ineligible:

1. `P2_XI_SHARED_1B` — `evidence_insufficient`;
2. `P2_CSI500_SHARED_1B` — `evidence_insufficient`;
3. `P2_CSI500_STAGE_2B` — `evidence_insufficient`.

The cross-index shared candidate additionally failed its CSI300 non-harm checks, but that does not change the decisive family-level result: the primary frozen sample gate already prevents promotion.

## Scientific interpretation

The V2.1 P2 mechanism remains plausible mechanism material from the earlier consumed RD1 diagnosis, but this preregistered successor family did not obtain enough year-by-year primary DEV evidence to support a promotable successor under its own frozen contract.

The correct conclusion is **not** that P2 was disproved. The correct conclusion is:

> the frozen 2015-2018 V21 DEV design is evidence-insufficient for selecting any P2 successor.

Because the protocol predeclared fail-closed handling for insufficient yearly primary sample, the project must not rescue this identity by:

- lowering the `20`-row yearly minimum;
- changing the `>10bp` primary threshold;
- moving or extending DEV dates;
- pooling away the weak 2017 year;
- adding candidates;
- reordering the candidate ladder;
- changing model class or beta bounds;
- opening Audit A to compensate for insufficient DEV evidence.

Any materially different continuation would require a new independently preregistered identity and evidence plan.

## Data boundary after adjudication

Opened/consumed for this identity:

- V21 DEV CSI300/CSI500 `2015-01-01 .. 2018-12-31`.

Remain sealed:

- V21 Audit A `2019-01-01 .. 2021-12-31`;
- V21 Audit B `2022-01-01 .. 2024-12-31`;
- V21 External Reserve `2025-01-01 .. 2026-08-21`;
- 2014Q4 supporting crosscheck;
- CSI1000 post-2026-08-21 true-fresh outcomes.

The separate frozen CSI1000 Gap-Fill V2 v1 true-fresh challenge remains independent of this V2.1 closeout and stays unopened under its own protocol.

## Final authority

- V21 P2 candidate family: **closed at DEV without successor**;
- Audit A open authorization: **false**;
- Audit B open authorization: **false**;
- parameter freeze: **none**;
- production authority: **false**.
