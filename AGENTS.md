# Overnight Open Lab — agent instructions

This repository is the **Overnight/Open factor-product laboratory and downstream
factor adapter** for FactorLab.

Before doing anything substantial, read:

1. `docs/governance/current_authority_v1.json`
2. `docs/governance/overnight_factor_product_registry_v1.json`
3. the active identity's state + protocol

For any model, factor-family, routing, strategy, robustness, account, or
cross-period change, also read and follow:

`.codex/skills/strategy-slice-rebuild/SKILL.md`

## 1. Scope

In scope:

- CSI1000 / related-index Overnight and opening-state research;
- expected opening direction and magnitude;
- observed opening-gap geometry;
- opening surprise / residual information;
- gap-fill hazards;
- global / offshore-China / FX Overnight drivers;
- causal trend/volatility/session-shape context;
- relative-index opening leadership under a new preregistered identity;
- frozen factor adapters for timing, stock-selection, execution, and risk.

Out of scope:

- generic reversal / RMR / parent-trend strategies;
- broad HighVol routing unrelated to Overnight/Open;
- two-wave strategy logic;
- using downstream strategy PnL to tune upstream factor definitions;
- pretending the CSI1000 cash index is directly shortable;
- live registry mutation or production deployment.

Production authority is false.

## 2. Current active task

The only active research identity is:

`overnight_open_surprise_factor_v1`

Current status:

`mechanism_diagnostic_frozen_pending_local_2019_2020_execution`

Authority:

- protocol: `docs/governance/opening_surprise_factor_v1_protocol.json`
- state: `docs/governance/opening_surprise_factor_v1_state.json`
- preanalysis: `docs/research/opening_surprise_factor_preanalysis_20260910.md`
- handoff: `docs/ops/opening_surprise_factor_dev_handoff_20260910.md`
- runner: `scripts/run_opening_surprise_factor_dev.sh`

Current scientific question:

`opening_surprise_rvol = (observed_gap - frozen_V6A_expected_gap) / rvol20`

Does this coordinate add short-horizon post-open information beyond raw gap and
simple causal context?

Detailed outcomes are currently authorized only for `2019-01-01..2020-12-31`.
For this identity:

- do not read detailed 2021-2025 outcomes;
- do not read 2026 outcomes;
- do not run trading-return optimization;
- do not invent trend buckets or thresholds;
- do not open a reusable BLACKBOX until cloud review freezes a later protocol.

## 3. Product-shelf rule

This repo is not a Cartesian feature factory.

Prefer reusable coordinates with clear economic meaning and causal availability:

- expected open;
- observed gap;
- opening surprise;
- gap-fill probability;
- driver attribution;
- trend / volatility / session-shape context;
- relative-index opening state.

A categorical interaction such as `uptrend × high-open` is not automatically a
product. First prove that the base continuous coordinate adds information. Then
freeze a bounded context family before looking at new outcomes.

Downstream strategy performance may validate a frozen adapter, but may not teach
or retune the upstream factor.

## 4. Stable authority that must not be casually reopened

### Next-open architecture

Repository-wide accepted architecture remains:

`median_quantile_sign + abs_frozen_clock_signed_prediction`

### Global-spillover lineage

Current single-head signed-gap baseline:

`V6A_plus_ordinary_A50_preauction_closure`

Its one reusable 2021-2025 BLACKBOX query returned `PASS`. Do not decompose that
BLACKBOX or use hidden behavior to design a successor.

The V6A controller library remains active because current factor research imports
its frozen causal feature/source functions. The completed one-command execution
entrypoint itself has been archived.

### Gap-Fill V2

Frozen and repeat-confirmed. 2026-01-05..2026-08-21 is repeat-only, not fresh.
True-fresh `2026-08-24..2026-12-31` remains sealed until the complete block and
protocol date gate permit execution.

### V2.1 P2

Closed at DEV with no successor due the frozen per-year sample sufficiency rule.
Do not rescue by changing years, thresholds, candidate order, model class, or
opening sealed Audit A/B outcomes.

## 5. BLACKBOX policy

`2021-01-01..2025-12-31` is a **reusable aggregate BLACKBOX**, not a one-time
physical consumable.

Rules:

- each identity must be fully frozen before a query;
- public output is whatever that identity preregisters, typically a low-bandwidth
  aggregate state;
- do not release hidden years, quarters, events, trade rows, or failure clues when
  the protocol forbids them;
- reuse never creates a new independent OOS sample;
- a failed technical execution does not authorize changing the scientific query;
- record actual completed logical queries in the append-only ledger.

Authority:

`docs/governance/overnight_reusable_blackbox_policy_v1.json`

## 6. Archive semantics

Read `archive/README.md`.

Archived files are provenance, not active execution surfaces. In particular:

- `archive/v6a_short0935_to_close_20260910/` is closed before DEV;
- `archive/v6a_reusable_blackbox_completed_20260910/` contains a completed
  execution wrapper/handoff.

Do not revive archived scripts by merely moving or copying them back. A revival
requires a new result-free protocol and identity.

Historical handoffs still under `docs/ops/` are not automatically active. Read
`docs/ops/README.md` first.

## 7. Data / causal timing

- Signal views may use causal pre-open / observed-open information only according
  to the identity contract.
- Never use post-target data to define a pre-target factor.
- SGX A50 frozen semantics require same-contract handling and frozen cutoffs;
  continuous/CFD substitutes are not interchangeable.
- Do not fabricate missing clocks or forward-fill source events when the protocol
  forbids it.
- Do not resample new wall-clock products in FactorLab when DataHub clock products
  are required by the project contract.
- Index prices may be used as research targets/coordinates, not fictitious live
  fills unless an explicit research-proxy contract says so.

## 8. GitHub / execution discipline

- Re-read current HEAD and target files immediately before writes.
- No force push.
- Use `[skip ci]` for documentation/governance commits when applicable.
- Do not rerun GitHub Actions merely to save documentation; Actions are last
  resort while quota is constrained.
- Never claim an execution happened unless an actual runner produced and persisted
  the expected receipt.
- Keep raw/large data boundaries explicit.
- Preserve historical bytes/digests rather than rewriting old evidence to match
  current files.

## 9. Cloud-local collaboration protocol

This protocol is active when the user sends work to this cloud repository and
asks this cloud session to continue.

Execution priority:

1. execute directly in the current cloud session when the required data/tools are
   genuinely available;
2. if cloud lacks local-only data or binary execution access, write a minimal,
   executable handoff and ask the local model to run it;
3. GitHub Actions are last resort.

When handing off locally:

- give one bounded task, exact command, evidence boundary, expected output, and
  forbidden actions;
- do not ask the local model to redesign formulas after seeing errors/results;
- local large data stays local unless a bounded repo copy is explicitly admitted;
- local model should commit only the requested small receipt/evidence with
  `[skip ci]`;
- cloud must re-read and independently adjudicate the returned receipt before
  opening any downstream gate.

The active local task is already documented at:

`docs/ops/opening_surprise_factor_dev_handoff_20260910.md`

## 10. Current next action

Local controller runs exactly:

```bash
git pull
bash scripts/run_opening_surprise_factor_dev.sh
```

Expected output:

`docs/research/local_opening_surprise_factor_dev_diagnostic_v1.json`

After that output is committed, cloud reviews the 2019-2020 diagnostic and decides
whether Opening Surprise deserves a bounded factor family. Do not jump ahead to
trend buckets, downstream backtests, or a new BLACKBOX query.
