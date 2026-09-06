# High-open recall OHR-04 cloud review — 2026-09-06

## Review decision

Local OHR-04 commit `98fa4109361d53f25138d415f2069269b04951f1` is accepted as a valid development-only diagnostic execution.

The execution is scientifically valid but does **not** admit a new conditioning mechanism or successor family. The incumbent direction head remains `median_quantile_sign`.

Status: `no_incremental_successor_beyond_incumbent_after_rebound_conditioning_diagnostic`.

OHR-03 remains unopened. `2026-01-05..2026-08-21` remains sealed from this research branch and post-2026-08-21 remains unread true-fresh evidence.

## Integrity audit

- Frozen OHR-04 execution parent: `0a1aee02ac082a97e8ce2d310618f52f7600cc9f`.
- Local result commit: `98fa4109361d53f25138d415f2069269b04951f1`.
- The local result commit changed only aggregate receipt/data-usage/communication/index/handoff-status files. It did not modify the frozen protocol, diagnostic runner, model identities, probe definitions, or boundary tests after observing results.
- Validator, pytest, and the OHR-04 diagnostic all exited 0; pytest reported 13 passed.
- Development window ended at `2025-12-31`; expanding OOF inventory is 2016–2025 with `n=2426`.
- `2026_rows_loaded=false`, `2026_blackbox_opened=false`, and `ohr_03_opened=false`.
- No candidate selection, parameter search, threshold search, quantile search, new-US-interaction search, or trading-return optimization occurred.
- 2015–2020 reconstruction remained exact with all reported max-absolute differences equal to 0.
- Raw development rows and row-level OOF predictions were not committed.

## What the rejected last-hour hinge actually did

Relative to the incumbent, the frozen diagnostic progression candidate changed 52 OOF decisions:

- rescued actual high opens: 16;
- newly created false high-open calls: 22;
- lost previously correct high opens: 8;
- repaired prior false high-open calls: 6.

For incumbent-down → candidate-up flips, added-up precision was only `16 / 38 = 0.4210526`. Thus the unconditional negative-side last-hour hinge does contain useful rebound information, but it activates too broadly and creates more new false highs than rescued highs.

The annual morphology is also unstable: rescue counts exceed new-false-high counts in only 3 of 10 years, while the reverse occurs in 5 of 10 years and 2 years tie.

This explains why the Phase-2 candidate improved pooled high-open recall yet failed overall hit and balanced-accuracy gates.

## Preregistered conditioning probes

### Last-hour weakness magnitude

`prev_last_hour_weakness` is the strongest continuous separator in pooled morphology:

- rescue-minus-new-false-high standardized difference: about `+0.502`;
- low-weakness Q1/Q2 added-up precision: `0.25`;
- Q3 added-up precision: `0.55`.

This is economically coherent: the hinge generates many bad flips when last-hour weakness is close to zero, while materially weak tails contain a better rescue/new-FP mix.

However the annual rescue-vs-false-high support is not broad enough for mechanism admission under the frozen protocol. The reported annual difference sign inventory is only 4 positive versus 1 negative among years with usable two-group comparison, not stable support across the full ten-year development atlas.

### Weakness breadth states

The binary states improve pooled precision but do not meet the multi-year requirement:

- `tail_only_weakness=1`: 15 added-up flips, precision `0.600`, 9 rescues / 6 new false highs; better-state evidence in only 3/10 years;
- `tail_with_broad_afternoon_weakness=1`: 11 flips, precision `0.636`, 7 rescues / 4 new false highs; better-state evidence in only 3/10 years;
- `tail_with_broad_day_weakness=1`: 2 flips, precision `1.0`, but sample size is far too small for admission.

These are diagnostics, not admissible runtime routes.

### Prior gap, trend, and volatility context

The other preregistered probes (`prev_gap`, signed/absolute prior gap components, `r1`, `r20`, `rvol20`, `abs_r1`, and breadth/concentration differences) show only modest pooled separation and mixed annual signs. None provides a clean, financially interpretable, multi-year separator between rescued highs and new false highs.

## Scientific adjudication

The OHR-04 question is answered negatively for the bounded information set:

> No preregistered causal pre-open state cleanly and stably conditions the last-hour rebound hinge so that its rescued high opens can be separated from the new false-high calls.

Therefore:

1. do not freeze another candidate family from these OHR-04 probes;
2. do not threshold the last-hour weakness term after seeing these results;
3. do not combine `tail_only` / broad-weakness states into a runtime route;
4. do not open the 2026 repeat blackbox;
5. retain `median_quantile_sign` as the incumbent direction head;
6. retain the last-hour hinge only as progression material showing that a rebound channel exists but is not sufficiently identified by the current feature set.

## Implication for any later research

Further high-open-recall research should not continue by slicing the same domestic weakness variables more finely. A new research identity would need a genuinely new causal information source or state representation capable of distinguishing **rebound demand** from **weakness continuation** before the China open. That future identity must preregister its own bounded family and keep the 2026 blackbox/fresh boundaries unchanged unless a new challenge protocol is explicitly frozen.

Production authority remains false.
