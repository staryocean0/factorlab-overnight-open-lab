# Cloud execution prompt — broad reversal / mean-reversion program

先完整阅读：

1. `CONTINUE_HERE.md`
2. `docs/governance/reversal_mean_reversion_program_charter_v1.json`
3. `docs/governance/reversal_mean_reversion_program_state_v1.json`
4. `docs/research/reversal_mean_reversion_program_whitepaper_v1.md`
5. `AGENTS.md`
6. `docs/user/handoff_prompt.md`

然后接管**广义反转与均值回归方向发现**，而不是继续把本仓当成单一“次日高开/低开”研究。

## 当前任务

第一阶段同时浅层推进三条路线：

- `R1_cross_scale_pullback`：父级趋势未坏时的低级别急速反向波动；
- `R2_range_boundary_reversion`：父级震荡中的边界过冲 / 假突破；
- `R3_regime_conditioned_residual`：当前状态下实际路径相对正常路径/分布的残差回归。

默认目标不是把某一条策略回测做到最好，而是用**相近的小研究预算**判断三条路线谁更值得深挖。

## 所有方向共用的四个问题

每个假说在看结果前都必须写清：

1. 什么尺度？低级别 / 当前级别 / 父级别分别是什么？
2. 父级状态是什么？趋势、震荡、切换还是无法判断？
3. 偏离了什么？价格、路径、波形、分布、相对关系还是统计属性？
4. 多久内、回到什么状态才算回归？什么情况算状态已经改变？

## 第一阶段的合格输出

每条路线先只回答：

- 现象是否存在；
- 条件是否能在回归发生前观察到；
- 样本是否足够；
- 是否至少跨多个时期、尺度或相邻市场状态稳定；
- 最小可证伪测试需要什么数据；
- 是否值得建立独立深度研究身份。

## 禁止

- 在 R1/R2/R3 尚未得到可比浅层研究前，连续多轮优化一个方向；
- 把“跌得多/涨得多”本身当作均值回归理由；
- 默认均值只能是移动平均线；
- 用样本内交易收益最大化选择方向；
- 看到失败后再增加阈值、状态、模型或样本窗口救结果；
- 因旧 Gap-Fill/V2.1 state 里还有 `next_action` 就自动回去执行那个专题；
- 打开旧专题的 sealed 数据来帮助新方向设计；
- 授予生产权。

## 旧 Overnight / Gap-Fill 工作

旧方向仍然是有效历史证据，统一视为 `R4_relative_value_dislocation` 下的专题案例/委托子项目。

如果用户明确要求恢复它，必须继续遵守原来的 source、consumed、audit、fresh 和 sealed 约束；否则只引用结论，不投入本仓主要研究预算。

## 当前下一步

1. 冻结统一的 scale / parent-state / deviation / recovery 测量词汇；
2. 分别写 R1、R2、R3 的浅层 preanalysis；
3. 为每条路线限定第一轮最多几个定义/候选，避免搜索膨胀；
4. 再根据可用数据执行可比的低成本筛选；
5. 三条路线比较后，最多把少数方向升级为深度研究。

交付时要写清：每条路线看到了什么、没看到什么、还缺什么，以及是否值得升级。生产权限始终为 `false`。
