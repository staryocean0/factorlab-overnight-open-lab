# R5-C event-density promotion handoff — 2026-09-08

Promotion source: broad-program R5 Stage-1 shallow screen.

Suggested dedicated successor identity:

`rmr_event_density_state_reversal_v2`

## Scientific idea carried forward

The broad screen found that a causal same-scale event-density state adds a small but directionally consistent amount of information about subsequent symmetric price reversal versus extension beyond completed-wave severity alone.

The claim is deliberately narrow:

> Event-density state appears to contain weak but repeatable price-path state information across the two preregistered directional-change scales.

Do not simplify this to “high event density means reversal” or “event density is a trading signal.” Stage-1 did not establish the sign, threshold, economic value, or optimal scale for a trading decision.

## Carried evidence

Source:

- `data/high_open_dev_2015_2025/1m_official.parquet`
- SHA256 `11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce`

Evidence roles:

- DEV: 2015–2019;
- chronological stability: 2020–2022, not fresh;
- 2023–2025 internal reserve: unopened and not fresh.

Frozen property:

`event_density = count_same_scale_wave_confirmations_in_trailing_240_observed_1m_bars / 240`

Frozen normalization used in Stage-1:

- preceding 100 completed same-scale observations;
- median center;
- MAD scale;
- current observation excluded.

### S1

- stability resolved events: 2,329;
- pooled Brier: severity `0.2501610` → severity+event-density-z `0.2494158`;
- pooled log-loss: `0.6934787` → `0.6919783`;
- annual Brier improvement: 2020, 2021, 2022.

### S2

- stability resolved events: 831;
- pooled Brier: `0.2489933` → `0.2489006`;
- pooled log-loss: `0.6911356` → `0.6909486`;
- annual Brier improvement: 2020 and 2022; small deterioration in 2021.

Event density itself is highly persistent rather than strongly mechanically reverting:

- S1 current/next z correlation `0.9383`, abs-z contraction share `0.5079`;
- S2 correlation `0.8669`, contraction share `0.5246`.

That makes the price-path increment more interesting as state information, while the small effect size means the identity still requires strict confirmation.

## What is not established

Stage-1 did not establish:

- whether high or low event density is the economically relevant side;
- a useful z-score threshold;
- an optimal trailing event-density window;
- an optimal directional-change scale;
- a trading entry/exit;
- transaction-cost viability;
- fresh out-of-sample confirmation;
- production authority.

## Reserve boundary

`2023-01-01 .. 2025-12-31` remains unopened for this mechanism in the broad program.

Before any reserve outcome is opened, the dedicated identity must freeze:

1. exact event-density representation;
2. whether the Stage-1 240-bar density window is retained unchanged or replaced by one single theory-driven alternative chosen **without** reserve inspection;
3. exact scale family and whether both S1/S2 remain co-primary;
4. the severity baseline;
5. the smallest bounded candidate family;
6. sample-sufficiency and success/failure gates;
7. the role of the 2023–2025 reserve.

The reserve is not scientifically fresh because the raw period was consumed by other historical identities. It can be a clean mechanism holdout only after the dedicated identity is frozen.

## Bounded next questions

### Q1 — Direction and shape

Without selecting a trading threshold, establish whether event-density z has a stable monotonic or otherwise low-capacity relation with reversal-first probability after controlling for completed-wave severity.

### Q2 — Increment beyond nearby event geometry

Test whether event density contributes beyond the minimum event-geometry baseline needed to avoid confusing density with simple wave duration/severity. Keep this family tiny and preregistered.

### Q3 — Cross-scale coherence

Determine whether S1 and S2 represent the same underlying state mechanism or whether the S2 effect is too small to retain as co-primary.

Do not choose the scale from reserve performance.

### Q4 — Untouched 2023–2025 mechanism holdout

Only after Q1–Q3 representation/gates are frozen.

### Q5 — Truly fresh confirmation

Reserve a later complete period/source after the dedicated model identity is frozen.

## Forbidden rescue behavior

- add many statistical indicators;
- search event-density windows on 2020–2025 outcomes;
- search wave scales on reserve results;
- select a z threshold by PnL;
- add interactions until Brier improves;
- relabel 2023–2025 as fresh;
- open a genuinely fresh period before the dedicated family is frozen;
- convert this weak Stage-1 effect directly into production authority.

Production authority remains false.
