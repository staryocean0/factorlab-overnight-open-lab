# E1 timing adapter v1 — cloud development handoff

Date: 2026-09-12

Identity: `overnight_c1_b4_timing_confidence_adapter_v1`

This handoff begins only after the result-free preregistration files exist. It does not authorize account PnL, strategy backtests, 2021–2025 detailed rows, or any change to upstream factors.

## Frozen files

- data usage: `docs/governance/downstream_timing_adapter_v1_data_usage.json`
- preanalysis: `docs/research/downstream_timing_adapter_v1_preanalysis_20260912.md`
- protocol: `docs/governance/downstream_timing_adapter_v1_protocol.json`
- state: `docs/governance/downstream_timing_adapter_v1_state.json`
- global downstream boundary: `docs/governance/downstream_adapter_research_boundary_v1.json`

## Development carrier plan

Cloud may reconstruct the frozen inputs from connector-readable 2015–2020 text carriers:

- A2/C1 domestic inputs from `data/runtime_text_2015_2025/`;
- B4 external channels from `data/driver_runtime_text_2015_2020/` plus the domestic factor carrier, using exactly the validated B4 lagged-RMS formula.

Before any adapter outcome is read, the development runner must:

1. bind the exact protocol SHA256;
2. verify the 2015–2020 carrier manifests/hashes;
3. verify reconstructed C1 fields against the existing development carrier on overlapping rows;
4. verify reconstructed B4 `driver_coherence` against the exact frozen B4 formula, not a new normalization;
5. assert zero 2021+ rows loaded;
6. assert the only candidate is the zero-boundary B4 abstention overlay;
7. refuse account/PnL/cost/instrument outputs.

## Allowed output

A development receipt may contain only preregistered factor-utility diagnostics by natural year 2015–2020 plus pooled. It may not contain candidate searches, threshold surfaces, alternate horizons, trade paths, position sizes, costs, account returns, or stock-selection results.

## Adjudication

Pass/fail of the development progression gates is owned by the cloud main agent. No automatic promotion is authorized.

If progression fails: close the identity; no outcome-guided rescue.

If progression passes: mark only `retrospective_factor_utility_adapter_candidate`; then stop. Any executable timing strategy requires a separate consumer-side identity satisfying the then-current Strategy Slice Rebuild, strategy science acceptance, and post-training account audit contracts.

`production_authority=false`.
