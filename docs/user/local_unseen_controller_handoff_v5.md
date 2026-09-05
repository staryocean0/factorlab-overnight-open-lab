# V5 SGX A50 候选：2021–2025 本地未见样本确认交接

## 当前唯一允许进入未见确认的候选

锁定为：`V5A_plus_A50_closure`。

它是在 v4（完整美国信息时钟 + HKMA 中国外汇价格发现代理）基础上，只增加一个经济含义明确的变量：

`a50_holiday_closure_return`

该变量只在 `holiday_reopen == 1` 时激活，表示 **A 股休市期间，同一张 SGX FTSE China A50 期货合约从前一 A 股交易日 15:00 前最后成交，到目标交易日 09:24:59 前最后成交的累计价格变化**。

V5B 增加的目标日上午 `09:00–09:24:59` A50 pre-open 分量已经按预注册规则失败，不能在 2021–2025 结果出来后重新捞回，也不能通过调参复活。

## 为什么 V5A 进入下一关

正式 GitHub Actions run `33972732993` 全链成功，job `101324004506`，18 项测试全过，冻结 baseline 精确重放。

在 v5 预注册共同样本上（2019–2020 已消费内部 holdout，`n=484`）：

- v4 IC：`0.5203513424`
- V5A IC：`0.5268402182`
- IC 增量：`+0.0064888758`
- v4 SSE：`0.0226752921`
- V5A SSE：`0.0223571763`
- SSE 改善：`+0.0003181158`
- sign hit：`72.5207% -> 72.7273%`

真正对应金融机制的可用节后重开样本只有 11 个：

- v4 holiday IC：`0.5183248174`
- V5A holiday IC：`0.6593272455`
- IC 增量：`+0.1410024281`
- sign hit：`81.8182% -> 90.9091%`
- holiday SSE 改善：`+0.0003199472`

固定预测 leave-one-holiday-event-out 共 11 次：

- 11/11 次 IC 增量为正；最小 `+0.04762`
- 11/11 次 SSE 改善为正；最小 `+0.00008550`

但事件贡献仍明显集中：最大一个事件占正向事件 SSE 改善约 `67.27%`，前两个约 `89.68%`。因此这些结果只能说明“值得进入未见确认”，不能授权运行时 holiday route 或正式 baseline。

## 本地控制器必须怎么做

完整机器可执行约束见：

`docs/governance/global_spillover_v5_unseen_local_controller_contract.json`

核心规则如下：

1. **2021–2025 数据只能由本地控制器读取。** 不上传本分支、不发给云端模型、不写 GitHub artifact。
2. 在看任何 2021–2025 结果前，先冻结本地数据 manifest：来源、文件 hash、日期范围、交易时钟、节假日日历版本、SGX 每个事件 archive/key/hash。
3. 模型仍为 `StandardScaler + Ridge(alpha=1.0)`；训练只使用 `2015–2018`。不能用 2021–2025 重拟合、调 alpha、加特征、调阈值。
4. V5A 和 v4 必须使用完全相同的未见共同样本比较。A50 某个节假日事件按冻结同合约规则确实取不到数据时，两者共同排除，并报告原因；不能插值、换合约或用未来成交量选合约。
5. A50 目标端必须严格截止 `09:24:59`；`09:25:00` 及以后任何 tick 禁止进入特征。
6. 必须同时报告：全 2021–2025、逐年 2021/22/23/24/25、节后重开子集、固定预测 LOO、事件贡献集中度，以及 frozen baseline / NASDAQ single / always-low-open 三个描述性 benchmark。
7. 禁止用 PnL、收益、Sharpe 选择候选。

## 未见确认门槛

只有以下条件全部满足，V5A 才能进入“单独的 baseline replacement review”，而不是直接升级：

- 全 2021–2025：V5A IC > v4；V5A SSE < v4；符号命中率恶化不超过 1 个百分点。
- 节后重开子集：V5A SSE < v4；IC 不低于 v4；符号命中率恶化不超过 1 个百分点。
- 五个年度中至少 3 年：年度 SSE 改善非负；至少 3 年年度 IC 增量非负。
- 如果可用未见 holiday 事件至少 10 个：固定预测 leave-one-event-out 中至少 80% 仍保持 holiday SSE 改善为正，且 LOO IC 增量中位数为正。

若因数据/时钟违反因果约束，整次未见执行作废，只能修数据层再跑；若是性能门槛失败，则保留失败结果，不得用 2021–2025 调参救活 V5A。

## 当前权威边界

当前 operational baseline 不变。

V5A 的状态是：

`A50_holiday_closure_progression_material_confirmed_by_fixed_prediction_LOO_waiting_genuinely_unseen_2021_2025_local_controller_confirmation`

本分支、Draft PR 和所有当前结果均不具有：生产、registry mutation、holiday runtime routing、baseline replacement 或 merge-main 权限。
