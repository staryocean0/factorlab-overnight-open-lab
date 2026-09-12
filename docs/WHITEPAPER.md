# Overnight/Open 项目白皮书

## 1. 定位与本次封版边界

本项目产出可引用的开盘因子定义、冻结参考实现及研究证据。三层问题分别是：开盘状态、开盘后短周期条件信息、冻结下游消费者的适配效用。它们不能互相替代。

这里的“validated”仅指指定数学身份、目标、比较基准和样本协议下的科学结论；不是收益保证、个股 alpha、稳定服务 API 或生产上线许可。当前软件以研究脚本和冻结参数为主，并未宣称具备生产数据刷新、服务 SLA、实时监控或交易执行适配。

状态基于 `overnight_open_current_authority@1.34`，唯一动态状态页是 `docs/CURRENT_STATUS.md`；查询总数为 12。

## 2. 已验证组件及精确追溯

### V6A

冻结身份：`V6A_plus_ordinary_A50_preauction_closure`。

范围：next-open model under the frozen V6A comparator/source contract。

数学定义：`Frozen V6A_plus_ordinary_A50_preauction_closure model identity; see its exact protocol`。

实现：`scripts/run_v6a_reusable_blackbox_local.py`。
证据：`docs/research/local_v6a_reusable_blackbox_receipt_v1.json`；协议：`docs/governance/global_spillover_v6a_reusable_blackbox_protocol_v1.json`。
状态：`docs/governance/global_spillover_v6a_blackbox_state_v1.json`。

### OFP-B1

冻结身份：`overnight_global_risk_open_gap_v1`。

范围：continuous global-risk coordinate for opening_gap_rvol。

数学定义：`0.5 * (us_nasdaq / RMS60_prev(us_nasdaq) - us_vix_chg / RMS60_prev(us_vix_chg))`。

实现：`scripts/run_global_risk_open_gap_blackbox.py`。
证据：`docs/research/local_global_risk_open_gap_blackbox_receipt_v1.json`；协议：`docs/governance/global_risk_open_gap_blackbox_protocol_v1.json`。
状态：`docs/governance/global_risk_open_gap_blackbox_state_v1.json`。

### OFP-B2

冻结身份：`overnight_china_offshore_open_gap_v1`。

范围：continuous same-contract China-offshore coordinate for opening_gap_rvol。

数学定义：`a50_channel_return / RMS60_prev(a50_channel_return)`。

实现：`scripts/run_single_external_driver_blackbox.py`。
证据：`docs/research/local_china_offshore_open_gap_blackbox_receipt_v1.json`；协议：`docs/governance/china_offshore_open_gap_blackbox_protocol_v1.json`。
状态：`docs/governance/china_offshore_open_gap_blackbox_state_v1.json`。

### OFP-C1

冻结身份：`overnight_trend_conditioned_open_state_15m_v1`。

范围：continuous trend-gap interaction; 09:35 to 09:50 return, not a trading sign rule。

数学定义：`(gap / rvol20) * (r20 / (sqrt(20) * rvol20))`。

实现：`scripts/diagnose_trend_conditioned_open_state_dev.py`。
证据：`docs/research/local_trend_conditioned_open_state_15m_blackbox_receipt_v1.json`；协议：`docs/governance/trend_conditioned_open_state_15m_blackbox_protocol_v1.json`。
状态：`docs/governance/trend_conditioned_open_state_15m_state_v1.json`。

### OFP-C2

冻结身份：`overnight_volatility_conditioned_open_state_60m_v1`。

范围：continuous volatility-gap interaction; 09:35 to 10:35 return with C1 control。

数学定义：`(gap / rvol20) * log(rvol20)`。

实现：`scripts/diagnose_volatility_conditioned_open_state_dev.py`。
证据：`docs/research/local_volatility_conditioned_open_state_60m_blackbox_receipt_v1.json`；协议：`docs/governance/volatility_conditioned_open_state_60m_blackbox_protocol_v1.json`。
状态：`docs/governance/volatility_conditioned_open_state_60m_state_v1.json`。

### OFP-B4

冻结身份：`overnight_driver_coherence_open_gap_v1`。

范围：continuous coherence coordinate for opening_gap_rvol; zero denominator remains missing。

数学定义：`(global_risk_z + china_offshore_z + fx_cny_z) / (abs(global_risk_z) + abs(china_offshore_z) + abs(fx_cny_z))`。

实现：`scripts/diagnose_driver_agreement_disagreement_dev.py`。
证据：`docs/research/local_driver_coherence_open_gap_blackbox_receipt_v1.json`；协议：`docs/governance/driver_coherence_open_gap_blackbox_protocol_v1.json`。
状态：`docs/governance/driver_coherence_open_gap_v1_state.json`。

B4 的冻结公式包含 FX 项，并不意味着独立 B3 产品验证通过；也不能因为 B3 单项未通过而删掉 B4 的 FX 项。C1/C2 的连续交互项验证不授予“正负号即交易开关”的权限。

## 3. 下游适配器与 Gap-Fill

E1/E2/E3 当前没有 validated downstream product。具体已结束身份逐一列在当前状态页。DEV_NO_PROGRESS、DEV_INSUFFICIENT 与 BLACKBOX FAIL 分别保留原结论；证据不足不等于上游因子失败，更不允许用不完整效用结果重设计该身份。

Gap-Fill V2 已冻结并通过重复检验；其 true-fresh 窗口是 2026-08-24..2026-12-31，最早中国日期 2027-01-01。现在不读取该窗口结果，也不以已有 repeat 代替 fresh。

## 4. 数据与因果时钟

因子必须服从各自协议的源截止时刻、同合约口径、滞后归一化和目标时钟。市场指数不是可直接执行的账户；qfq 的信号语义不赋予 qfq 成交权限。

本库 2021-2025 reusable BLACKBOX 的细节保持封存；重复使用不产生新的独立 OOS。历史研究可能拥有不同的已消费窗口，不能用一个全局标签覆盖所有历史协议。代码维护只核对载体的 Git 对象与元数据，不重新消费市场行。

## 5. 文档、代码、测试、工作流一致性

当前 authority、registry、component bindings、ledger、生命周期清单共同定义维护面。README、接续入口、本白皮书和当前状态页由同一检查器生成；手工改动导致生成内容漂移会使 CI 失败。

默认 CI 仅执行一致性检查和无行情的回归测试。冻结源码的字节完整性、被归档代码的原始 blob、ledger 前缀不可变性、组件与 receipt/protocol 的绑定、日期门和权限边界均接受自动核验。

这些是工程检查，不是新一轮因子检验。新增的合成测试覆盖归一化滞后、方向/公式一致性、缺失/零分母、时钟与不完整输入；原有保留测试继续保护冻结 Gap-Fill 和架构证据。

## 6. 历史保存与后续变更

过期 one-shot workflow 从当前执行面删除；其他旧流程、已关闭实验的独立 runner 和阶段测试按清单归档。仍被当前组件依赖的历史实现保留原路径与字节，但不因此重新取得执行权。

档案内的相对路径按冻结时仓库根解释。需要完整历史环境时，应在独立目录检出清单 baseline commit，不能直接将档案里的脚本当作今天的运行入口。

新组件或新研究须先完成独立预注册与输入/目标/消费者边界冻结，再同步 registry、component bindings、状态页、测试和 workflow。生产权限持续为 false。
