# 当前状态（自动生成，不手工编辑）

Authority：`overnight_open_current_authority@1.34`；Registry：`overnight_factor_product_registry@1.16`。

BLACKBOX 逻辑查询数：**12**。

`active_research`：null（没有获准执行的 outcome-bearing identity）。

**交付边界：已验证因子的冻结参考实现与可复现证据，不是生产信号服务，也不是已通过验证的交易适配器。**

`production_authority = false`。维护测试通过不增加科学、账户执行或生产权限。

## 已验证组件

| 组件 | 冻结身份 | 科学结论 | 有效范围 |
|---|---|---|---|
| V6A | `V6A_plus_ordinary_A50_preauction_closure` | PASS / #1 | next-open model under the frozen V6A comparator/source contract |
| OFP-B1 | `overnight_global_risk_open_gap_v1` | PASS / #8 | continuous global-risk coordinate for opening_gap_rvol |
| OFP-B2 | `overnight_china_offshore_open_gap_v1` | PASS / #9 | continuous same-contract China-offshore coordinate for opening_gap_rvol |
| OFP-C1 | `overnight_trend_conditioned_open_state_15m_v1` | PASS / #2 | continuous trend-gap interaction; 09:35 to 09:50 return, not a trading sign rule |
| OFP-C2 | `overnight_volatility_conditioned_open_state_60m_v1` | PASS / #7 | continuous volatility-gap interaction; 09:35 to 10:35 return with C1 control |
| OFP-B4 | `overnight_driver_coherence_open_gap_v1` | PASS / #3 | continuous coherence coordinate for opening_gap_rvol; zero denominator remains missing |

## 下游研究状态

| 身份 | 研究对象 | 当前结论 |
|---|---|---|
| E1v2 | `overnight_c1_c2_timing_agreement_adapter_v1` | `DEV_NO_PROGRESS_closed_no_successor` |
| E2v2 | `overnight_c2_stock_selection_risk_abstention_adapter_v1` | `DEV_INSUFFICIENT_closed_no_successor` |
| E3v2_parent | `overnight_b1_forward_cycle_portfolio_risk_abstention_v1` | `DEV_progression_closed_by_reusable_BLACKBOX_FAIL` |
| E3v2_validation | `overnight_b1_forward_cycle_portfolio_risk_abstention_validation_v1` | `BLACKBOX_FAIL_closed_no_validated_E3v2_product` |
| E2v3 | `overnight_b2_stock_selection_offshore_risk_abstention_adapter_v1` | `DEV_NO_PROGRESS_closed_no_successor` |
| E3v3 | `overnight_c2_forward_cycle_portfolio_risk_abstention_v1` | `DEV_INSUFFICIENT_closed_no_successor` |

## 独立日期门

Gap-Fill V2 只达到冻结 / repeat-confirmed。true-fresh 窗口为 **2026-08-24 至 2026-12-31**，且不得早于 **2027-01-01（中国日期）**开启；日期达到本身不替代完整数据与原协议检查。

## 权威来源

- `docs/governance/current_authority_v1.json`
- `docs/governance/overnight_factor_product_registry_v1.json`
- `docs/governance/overnight_reusable_blackbox_query_ledger_v1.json`
- `docs/governance/component_bindings_v1.json`
- `docs/governance/gap_fill_v2_true_fresh_state_v1.json`

本文件由 `python scripts/check_repository_consistency.py --write-views` 生成。
