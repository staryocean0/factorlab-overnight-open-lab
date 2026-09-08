# Gap-Fill V2.1 DEV cloud adjudication — 2026-09-08

Research identity: `gap_fill_v2_1_regime_conditioned_successor`.

Decision: **`V21_DEV_no_P2_successor`**.

This adjudication closes the frozen P2 candidate family. It does not open Audit A, Audit B, the external reserve, the 2014Q4 supporting crosscheck, or CSI1000 post-2026-08-21 outcomes.

## Evidence reviewed

Local execution receipt commit:

`c34c74809d19211124c4e66f1afb29ade86b6cb3`

Receipt:

`docs/research/local_gap_fill_v21_dev_selection_receipt_v1.json`

Data-usage receipt:

`docs/governance/local_gap_fill_v21_dev_data_usage_v1.json`

The local result commit adds only those two allowed compact artifacts. No selected parameter freeze was written.

The authorized runner reported code identity `b4063a1509c609986d8351598136eb5024fc7fc6`. A concurrent repository-wide authority reset occurred after the V21 execution freeze, but comparison against the frozen specialist point found no mutation of the V21 DEV runner, P2 math, evaluation kernel, candidate family, or DEV selection protocol. The broad-program reset therefore does not invalidate this bounded specialist execution.

## Source / boundary integrity

The DEV metadata preflight reproduces the admitted SA2 inventory for both CSI300 and CSI500:

- observed trading days: `975` each;
- `session_complete_239_required_v1` days: `944` each;
- incomplete days: `31` each;
- optional `14:59` present days: `884` each;
- metadata rows: `467094` total.

The parent HE-00 v8 identity remains:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`.

The run kept the frozen boundaries:

- Audit A opened: `false`;
- Audit B opened: `false`;
- External Reserve opened: `false`;
- 2014Q4 supporting crosscheck opened: `false`;
- CSI1000 post-2026-08-21 opened: `false`;
- raw/row-level outputs written to repo: `false`;
- trading return used: `false`;
- probability calibration / binary-threshold / hyperparameter / model-class search: `false`.

## Frozen ladder result

All three preregistered candidates were attempted in the frozen order:

1. `P2_XI_SHARED_1B`;
2. `P2_CSI500_SHARED_1B`;
3. `P2_CSI500_STAGE_2B`.

`selected_candidate = null` and `attempted_candidate_count = 3`.

The decisive gate is not a post-hoc performance judgment. The frozen DEV primary sample-sufficiency contract requires CSI500-high `abs_gap > 10bp` to have:

- at least `60` pooled validation rows; and
- at least `20` rows in **each** validation year 2016, 2017, and 2018.

Observed primary counts were:

- 2016: `68`;
- 2017: **`15`**;
- 2018: `52`;
- pooled: `135`.

Therefore the common primary sample gate is `evidence_insufficient`. The candidate metric gates are not eligible to rescue the family after this failure.

### Descriptive beta histories

These remain development diagnostics only:

- `P2_XI_SHARED_1B`: shared beta `[-0.06920, -0.02054, +0.06877]`; CSI300 non-harm gate also failed.
- `P2_CSI500_SHARED_1B`: shared beta `[+0.09194, -0.02862, -0.00640]`.
- `P2_CSI500_STAGE_2B`:
  - 15m beta `[+0.33435, +0.01736, -0.00064]`;
  - 60m beta `[-0.08631, -0.05906, -0.01043]`.

They do not create promotion authority because the preregistered sample gate already failed.

## Scientific interpretation

RD1 established that relative cross-index opening dislocation was a plausible mechanism on consumed historical evidence. V21 DEV does **not** establish a promotable successor under the frozen new-development contract.

The correct conclusion is deliberately narrow:

> the bounded P2 successor family has no eligible DEV successor under its preregistered evidence contract.

This is not permission to reinterpret the result as a positive signal hidden by the gate, and it is not permission to relax the gate after seeing that 2017 contains only 15 primary events.

## Forbidden rescue actions

The following are not authorized:

- extend or slide the 2015-2018 DEV window;
- lower the per-year minimum below 20;
- lower or change the `abs_gap > 10bp` primary cohort;
- pool 2017 with another year to repair sufficiency;
- promote the same-era geometry control as the V2.1 mechanism successor;
- add a fourth P2 candidate or change the candidate order;
- retune beta bounds, penalties, thresholds, calibration, model class, or horizons;
- open Audit A merely to see whether the candidate would have worked there.

Any future return to this mechanism requires a new research identity and a new result-free protocol with genuinely new evidence.

## Authority after closeout

- V21 P2 family: **closed — no successor**;
- V21 DEV: consumed development evidence;
- Audit A: sealed;
- Audit B: sealed;
- External Reserve: sealed;
- production authority: `false`.

Repository-wide work should continue under the newer broad reversal / mean-reversion discovery authority. The closed V21 result remains an R4 specialist case study and does not block R1/R2/R3 Stage-1 screening.
