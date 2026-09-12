# OFP-E1 v2 C1/C2 timing-agreement adapter — cloud development adjudication

Date: 2026-09-12

Research identity: `overnight_c1_c2_timing_agreement_adapter_v1`

Phase: retrospective factor-utility diagnostic only.

Development window: `2015-01-05..2020-12-31`.

## Frozen identity

C1 is the only direction source:

`c1_direction_score = -(gap / rvol20) * (r20 / (sqrt(20) * rvol20))`

C2 is agreement-veto only:

`c2_direction_score = -(gap / rvol20) * log(rvol20)`

Comparator:

`c1_action = sign(c1_direction_score)`

Candidate:

`candidate_action = c1_action if sign(c1_direction_score) * sign(c2_direction_score) > 0 else 0`

Target:

`ret_0935_0950 = close_0950 / close_0935 - 1`

No threshold, weight, magnitude bucket, alternate horizon or upstream add/drop search was performed.

## Development result

All six annual sufficiency gates pass.

Pooled complete cases: **1440**.

Pooled candidate active days: **732**.

Pooled candidate coverage: **0.508333**.

Pooled comparator mean signed utility: **-0.0000777626**.

Pooled candidate mean signed utility: **-0.0000501464**.

Pooled delta mean signed utility: **+0.0000276162**.

Annual delta mean signed utility:

- 2015: `+0.0003063191`
- 2016: `+0.0002085234`
- 2017: `+0.0000408189`
- 2018: `-0.0001528266`
- 2019: `-0.0001788030`
- 2020: `-0.0000346011`

Preregistered gate result:

- pooled delta > 0 — PASS;
- median annual delta = `+0.0000031089` — PASS;
- positive annual delta count = **3 / 6** — **FAIL** versus required 4 / 6;
- all annual sufficiency gates — PASS.

## Decision

**`E1V2_DEV_NO_PROGRESS`**

The exact C1/C2 zero-boundary agreement veto does not progress. The pooled relative improvement is positive but annual dispersion fails the frozen 4-of-6 requirement. No reusable validation successor is authorized.

This does not alter C1 or C2 upstream product authority. It only closes this downstream adapter identity.

No threshold/weight/horizon rescue is authorized under this identity.

`production_authority=false`.
