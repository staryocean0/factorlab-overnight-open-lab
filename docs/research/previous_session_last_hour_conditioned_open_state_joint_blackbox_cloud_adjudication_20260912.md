# C3 joint 30m+60m reusable BLACKBOX — cloud adjudication

Date: 2026-09-12

Research identity: `overnight_previous_session_last_hour_conditioned_open_state_joint_30m_60m_v1`

Parent development identity: `overnight_previous_session_last_hour_conditioned_open_state_v1`

Product family: `OFP-C3_previous_china_session_shape_x_OFP-A2_observed_open_geometry`

## Frozen identity

The successor retained exactly the previously adjudicated continuous coordinate:

`(prev_last_hour / rvol20) * (gap / rvol20)`

with the frozen baseline controls and the joint 30m + 60m targets. The 15m horizon remained rejected and was not revived. No unique 30m/60m winner selection, alternate session window, `prev_afternoon` rescue, threshold, bucket, alternate volatility window, alternate clock, or strategy-return optimization was authorized.

## Validation channel

The 2021-2025 validation used the frozen reusable compact BLACKBOX protocol. Physical raw clocks were reconstructed in the cloud from the already accepted CSI1000 raw-clock carrier plus the minimal exact-14:00 supplement. Before scientific adjudication, the controller required 2020 overlap reconstruction parity for `gap`, `r1`, `r20`, `rvol20`, `prev_daytime`, `prev_last_hour`, and `holiday_reopen`.

Technical reconstruction parity: `PASS`.

The compact receipt persisted no hidden metrics, annual results, counts, bootstrap results, or failure attribution.

## Result

`FAIL`

Query id: `6370829e0cb0b084badd`

Reusable BLACKBOX ledger ordinal: `5`

This FAIL applies to the frozen **joint 30m+60m successor identity as a whole**. It does not authorize decomposition of the hidden result to determine which horizon, year, gate, or bootstrap condition failed.

## Authority consequence

Decision: `C3_JOINT_BLACKBOX_FAIL_CLOSE_NO_VALIDATED_PRODUCT`

Consequences:

- no validated C3 factor-product authority is granted;
- the 2015-2020 parent DEV result remains historical progression material only;
- no 15m revival is allowed;
- no post-hoc 30m/60m winner may be selected;
- no rescue search may use hidden BLACKBOX behavior;
- `prev_afternoon`, alternate session windows, thresholds, buckets, alternate clocks, alternate volatility windows, and strategy PnL remain unauthorized rescue axes;
- reuse of the same physical 2021-2025 period is not independent OOS;
- `production_authority=false`.

The next program step should return to a separately preregistered downstream adapter experiment using only already validated upstream factor products. C2 remains frozen/unopened/deferred unless explicitly reactivated by authority.
