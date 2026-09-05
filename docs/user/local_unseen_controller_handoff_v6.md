# V6A 2021–2025 本地未见确认交接

## 目的

本交接只负责一次真正未见确认：验证已经冻结的 `V6A_plus_ordinary_A50_preauction_closure` 是否在 2021–2025 继续稳定优于 `V5A_common_sample_comparator`。

云端研究已经停止读取 2020 年之后的数据。2021–2025 的 CSI1000、SGX、FRED/HKMA 等市场行不得上传回当前云端研究仓库。

权威合同：

`docs/governance/global_spillover_v6_unseen_local_controller_contract.json`

正式 v6 receipt：

`docs/governance/global_spillover_v6_daily_a50_receipt.json`

## 已冻结候选

- 候选：`V6A_plus_ordinary_A50_preauction_closure`
- 比较器：`V5A_common_sample_comparator`
- 模型：`StandardScaler + Ridge(alpha=1.0)`
- 训练期：2015–2018，仅按正式 v6 的共同样本/complete-case 规则训练
- 2021–2025：只能预测和评价，禁止用于 scaler、系数、参数、缺失处理、cutoff、合约规则或特征定义
- 正式候选代码 SHA：`2ffec2a2ebfc3490ff0805e9b14680aa076a320e`
- 正式外部数据冻结 SHA：`0ae33649208805937dd41549f6874496319ae911`

## A50 时钟必须原样复刻

普通交易日：

- `holiday_reopen == 0`
- 上一 A 股交易日 15:00 前，选择最近的、不早于当月且已有成交的 SGX `CN` 期货合约
- start = 同一合约上一 A 股交易日 `<=15:00:00` 的最后成交
- end = 同一合约目标日 `<=09:14:59` 的最后成交
- `return = end/start - 1`
- 目标日 09:15:00 及以后 SGX 行禁止进入该变量

长假重开：

- 保持冻结 V5A 的 holiday A50 定义不变
- 目标 cutoff 仍为 `09:24:59`
- 不允许用 v6 普通日规则重写历史 V5A 定义

SGX 老格式：

- 按 header 识别字段，不用固定列号
- legacy `Y=Traded`，后续格式 `T=Traded`
- `S=Settlement` 不能当成交
- Amend Code 非空记录保守排除
- 官方允许的空价 trade-status 记录逐行跳过，不得让其成为价格端点，也不得因此报废整天其它有效成交

## 本地执行顺序

1. 在读取任何 2021–2025 目标指标之前，先冻结本地数据 manifest：文件 SHA、日期范围、交易日历、SGX 每个档案 URL/key/SHA、schema、时钟断言。
2. 用 2015–2018 复刻 V5A comparator 与 V6A 训练；不得使用 2021–2025 重拟合。
3. 构建 2021–2025 完全相同的 unseen common sample。任何 A50 缺失行必须同时从 V5A/V6A 比较中移除并报告原因。
4. 一次性生成固定预测。
5. 报告 2021–2025 全期、逐年、逐季度、普通日、长假子集指标与固定预测 SSE 贡献集中度。
6. 按 governance contract 中的 gate 原样裁决，不得看到结果后修改 gate。

## 必报核心指标

全期必须同时报告：

- V5A / V6A `R²`
- V5A / V6A `SSE`
- V5A / V6A `IC`
- V5A / V6A `sign_hit`
- `delta_R²`
- `SSE improvement`
- `delta_IC`
- `sign_hit_delta`

还要报告 2021、2022、2023、2024、2025 各年上述指标，以及所有季度，不允许删除表现差的年份或季度。

普通日 A50 覆盖率必须至少 90%。

## 通过含义

只有所有选择性 gate 都通过，V6A 才能变成：

`eligible_for_separate_baseline_replacement_review`

这仍然不代表自动替换 baseline，也不代表生产、registry 或 runtime route 权限。

如果未见确认失败：保留失败，不得使用 2021–2025 调参救活 V6A，也不得用这批数据重新搜索 cutoff、regime 或替代因子。

## 当前 consumed-holdout 结果仅用于校验复刻

2019–2020 共同样本正式结果：

- V5A comparator：`R² 0.1715573`，`IC 0.5107176`，sign `0.7180043`
- V6A：`R² 0.3830170`，`IC 0.6537331`，sign `0.7592191`

这个 `38.30%` **不是 fresh OOS 解释度**。它只说明 V6A 值得进入真正未见确认。

法证检查还确认：普通日 450 个 holdout 端点中，09:15 及以后为 0；同日 A50 与目标相关约 `0.619`，错位一日只有约 `+0.019/-0.023`；去掉最大 10 个正贡献日后固定预测 SSE 总改善仍为正。

另一个必须保留的 caveat：共同样本重拟合后，11 个已消费长假事件的 sign hit 从 V5A 的 `90.91%` 降到 V6A 的 `72.73%`，尽管 IC/SSE 改善。未见确认中必须如实报告 holiday 子集，不能围绕这 11 个旧事件调模型。
