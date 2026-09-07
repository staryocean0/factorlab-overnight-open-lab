# Gap-Fill V2.1 future-audit source admission — cloud adjudication — 2026-09-07

## Decision

Research identity remains:

`gap_fill_v2_1_regime_conditioned_successor`.

Cloud decision:

**replace `exact_240` as the future V21 source-admission gate with the narrowly defined `session_complete_239_required_v1` contract.**

This decision does **not** rewrite the frozen RD1 protocol, runner, receipt or cloud adjudication. The old `exact_240` inventory remains valid evidence of why the then-current source contract blocked the frozen 2019–2024 audit partitions. The new gate applies prospectively to future V21 source admission and target construction only.

No V21_DEV outcome is opened by this adjudication. No successor model is fitted or selected.

## Why this is not a generic relaxation

The new rule is not `len(day) == 239`, `len(day) >= 239`, or "allow one missing minute".

The legacy expected target-session labels were:

- `09:31 .. 11:30` inclusive;
- `13:01 .. 15:00` inclusive;
- total: 240 labels.

The locally audited future-audit source reports a systematic source-label contract in which **14:59 is absent on every audited day**. Cloud therefore freezes exactly one source-specific change:

`required_239 = legacy_expected_240 - {14:59}`

Every one of those 239 named clocks is mandatory. `14:59` is optional if a later equivalent source actually provides it, but it may not be synthesized. A day missing `13:22`, `10:39`, `09:31`, or any other required clock remains invalid. Duplicate or unexpected target-session clocks also fail closed.

Thus the new gate distinguishes:

1. one structural source-label exception fixed before outcome access; from
2. genuine intraday holes that remain inadmissible.

The implementation is frozen in:

`scripts/v21_session_complete_239_gate.py`

with static tests in:

`tests/test_v21_session_complete_239_gate.py`.

## Owner-reported package identity

Local package:

`data/v21_future_audit_csi_index_1m_session_complete_2019_2024/csi300_csi500_1m.parquet`

Reported rows:

`695,929`

Reported SHA-256:

`3088ff2119ccffce3ff2fb8468a497775bcf64bc78df01008c85390ccd27777c`

Parent HE-00 v8 dataset identity remains:

`25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0`

Reported coverage per symbol is 1,456 trading days:

| symbol | session-complete under required-239 | still incomplete |
|---|---:|---:|
| `000300.SH` | 1,449 | 7 |
| `000905.SH` | 1,448 | 8 |

The incomplete days reportedly miss middle clocks such as `13:22`, `10:39–10:44`, and `09:31–09:34`; they are **not** being rescued by the 14:59 exception and remain fail-closed.

A simple row-count cross-check is internally consistent:

- if all 1,456 days for both symbols had all required 239 labels: `1,456 × 239 × 2 = 695,968` rows;
- reported file rows: `695,929`;
- difference: `39` required-clock rows.

This arithmetic is consistent with a small set of genuine incomplete days plus a source-wide exclusion of 14:59 from the required label set.

## Important verification boundary

At the time this cloud contract is frozen, neither the new parquet nor the stated local receipt is visible on GitHub main/this cloud runtime:

`docs/research/local_gap_fill_v21_future_audit_source_admission_receipt_v1.json`

Therefore cloud records the package SHA and coverage above as **owner-reported**, not independently file-verified.

Before any V21_DEV outcome is opened, one of the following must occur:

1. the local admission receipt is pushed and its package/source identities can be checked; or
2. the parquet is uploaded/made available to cloud and the metadata-only validator reproduces the checksum and coverage.

The required pre-outcome verification may read only `symbol`, `trading_day`, and `timestamp` plus file/provenance metadata. It may not inspect future OHLC, construct future gaps/fill targets, or score a model.

## Scope

The reported package directly remediates the frozen future audit blocks:

- `V21_AUDIT_A`: 2019-01-01 .. 2021-12-31;
- `V21_AUDIT_B`: 2022-01-01 .. 2024-12-31.

Date boundaries remain frozen.

The package does not by itself admit `V21_EXTERNAL_RESERVE` (2025+) and does not eliminate the need to re-inventory the `V21_DEV` source under the new required-239 gate before development outcomes are opened.

## Target semantics and governance

Future V21 runners must use the named-clock required-239 gate, not a row-count shortcut. No missing middle bar may be forward-filled, backfilled or synthesized.

This source-admission decision is made before V21_DEV outcome access. It therefore cannot be based on which missing-day policy produces better model or trading performance.

The already-consumed RD1 evidence and the admitted mechanism remain unchanged:

`P2_relative_gap_excess` only.

Still not authorized by this source-admission stage:

- opening V21_DEV outcomes;
- fitting/selecting a V2.1 successor;
- changing future partition dates;
- reopening rejected RD1 probes;
- changing the V21 predictive horizons or primary cell;
- opening 2014Q4 supporting crosscheck;
- opening the external reserve;
- production use.

## Next action

1. make `local_gap_fill_v21_future_audit_source_admission_receipt_v1.json` visible to cloud or provide the parquet;
2. independently verify the reported SHA/provenance and required-239 coverage using metadata only;
3. re-inventory V21_DEV under the same named-clock gate without opening outcomes;
4. only after those checks may cloud freeze the bounded P2-based V2.1 candidate family and separately authorize the first V21_DEV outcome run.

V21_DEV remains sealed now.
