# OFP-B4 Driver Coherence reusable BLACKBOX — cloud adjudication

Date: 2026-09-12

Research identity: `overnight_driver_coherence_open_gap_v1`

Decision: **PASS**

Query ID: `33ccb040dd0d1822f3b6`

## Scope

This is the separately frozen reusable-BLACKBOX successor of the six-year development identity `overnight_driver_coherence_v1`.

The frozen factor is the continuous driver-coherence coordinate built from three causally available normalized channel families:

- global risk: NASDAQ and sign-aligned VIX complete-clock information;
- China-specific offshore: same-contract SGX FTSE China A50 pre-auction/holiday closure return under the frozen cutoff rules;
- FX: sign-aligned HKMA-derived USD/CNY closure return.

The target is normalized CSI1000 opening gap, `gap / rvol20`. The comparator is the same frozen OLS baseline without the nonlinear `driver_coherence` increment.

## Receipt and provenance review

The compact receipt was committed at `ea6799bb81c73cd54351ea68e6eb293e96b07368` and contains only the allowed decision plus non-outcome provenance.

It records:

- decision `PASS`;
- no public detail release;
- no internal metrics persisted;
- no yearly results persisted;
- no counts persisted;
- no failure attribution persisted;
- reuse is not independent OOS;
- production authority remains false.

The receipt commit changes only the compact receipt. The query ID recomputes exactly from the frozen candidate/comparator/window and the recorded protocol/source/reconstruction hashes.

## Scientific authority granted

The exact continuous `driver_coherence` coordinate is validated as an OFP-B4 factor product for its frozen pre-open/open-gap semantics.

This validation does **not** authorize:

- thresholded agreement/disagreement labels;
- high/low coherence buckets;
- alternate driver weights;
- pairwise channel variants;
- alternate normalization windows/scales;
- hidden BLACKBOX decomposition;
- downstream strategy PnL tuning;
- production/live execution.

The 2021-2025 physical window remains reusable but is not a new independent OOS sample. Hidden behavior from this query may not be used to design or rescue later variants.

`production_authority=false`.
