# 云端—本地沟通记录

## OHR-01 — 高开漏判机制诊断（开发阶段，不打开 2026）

**状态：本地已反馈，待云端复核。**

### 目标

解释当前 `median_quantile_sign` 方向头为何仍系统性漏判实际高开，并为下一阶段候选族提供金融机制证据。此任务只做诊断，不选择新模型、不调参数、不调阈值。

### 云端已完成

- 冻结证据边界：`docs/governance/cloud_session_20260906_high_open_recall_research_protocol_v1.json`
- 完成金融/数学预分析：`docs/research/high_open_recall_preanalysis_20260906.md`
- 实现开发诊断器：`scripts/diagnose_high_open_false_negatives_dev.py`
- 诊断器固定使用 2015-01-05 至 2025-12-31，并通过 expanding natural-year OOF 生成 2016–2025 的 incumbent 预测。
- 诊断器显式禁止加载 2026；不执行 candidate ranking、parameter search、threshold search 或 trading-return optimization。

### 证据边界

- `2015-01-05 .. 2020-12-31`：development material。
- `2021-01-01 .. 2025-12-31`：上一轮已经消耗，本轮新身份可作为 development material；不得再称 fresh。
- `2026-01-05 .. 2026-08-21`：**sealed repeat black-box validation only**。本任务严禁读取、加载、诊断或用于任何特征/候选设计。
- `post-2026-08-21`：继续保持 unread，留作新 integrated successor 的真正 fresh challenge。

注意：因为 2026-01-05..08-21 已在上一轮打开，而且这轮研究动机本身来自已知的 high-open recall 弱点，所以它不能科学上重新变 fresh。后续可以在候选完全冻结后做一次黑箱复核，但只能提供复现/反证权，不能单独授予新的 fresh-OOS authority。

### 本地执行要求

本地 controller 原样执行：

```bash
python scripts/validate_theme_package.py
pytest -q
python scripts/diagnose_high_open_false_negatives_dev.py
```

如果本地源路径移动，只允许设置以下环境变量：

- `OVERNIGHT_ANNOTATED_PANEL`
- `OVERNIGHT_DATAHUB_1M`
- `OVERNIGHT_FRED_NASDAQ`
- `OVERNIGHT_FRED_VIX`

不得修改模型语义、开发截止日、OOF 年份、诊断分桶或 probe 定义来适配结果。

### 本地执行时的 denylist

在完成 OHR-01 开发诊断前，本地执行代理不要读取或引用以下 2026 结果材料来做机制判断或候选设计：

- `docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json`
- `docs/research/cloud_session_20260906_local_2026_direction_result.md`
- 任何 2026-01-05..2026-08-21 的逐日 target/prediction/trade 明细。

协议文件中关于“2026 已经被消费、必须封存”的治理信息可以读取；不得读取其结果内容来调整研究设计。

### 预期输出

脚本应生成：

- `docs/research/cloud_session_20260906_local_high_open_recall_diagnostic_receipt_v1.json`
- `docs/governance/local_session_20260906_high_open_recall_data_usage.json`

只提交聚合诊断和 source hashes；不要提交 2015+ 原始行情、逐日 OOF prediction、2026 数据或本地大文件。

### 验收条件

云端复核时至少检查：

1. `development_window.end == 2025-12-31`；
2. `2026_rows_loaded == false`、`2026_blackbox_opened == false`；
3. `candidate_selection_performed == false`；
4. `parameter_search_performed == false`；
5. `threshold_search_performed == false`；
6. 2015–2020 reconstruction 与冻结包逐字段 max-abs 为 0；
7. OOF 仅覆盖 2016–2025；
8. 输出包含 high-open gap magnitude、false-negative margin、slow-state、asymmetric-US、catch-up interaction、US-session-count 等聚合诊断；
9. source hashes 完整；
10. `production_authority == false`。

### 本地完成后回写

本地代理请在本节末尾追加：实际 commit SHA、三条命令的退出码、输出文件路径、关键聚合结果，以及任何失败/未验证事项。云端收到后先复核，再决定 Phase 2 候选族；在此之前不打开 2026 黑箱。

### 本地执行反馈（2026-09-06）

- 执行身份：本地 controller；工作目录 `/home/starryocean/桌面/量化/factorlab-overnight-open-lab`。
- 执行时代码 SHA：`266a5d9`（`Add fail-closed tests for high-open research boundary [skip ci]`）。
- 未设置路径覆盖环境变量；沿用既有本地默认源。
- 未读取 2026 黑箱结果材料做机制判断或候选设计；未打开 Phase 2 候选族。

| 命令 | 退出码 |
|---|---|
| `python3 scripts/validate_theme_package.py` | 0 |
| `python3 -m pytest -q` | 0（9 passed） |
| `python3 scripts/diagnose_high_open_false_negatives_dev.py` | 0 |

输出文件：

- `docs/research/cloud_session_20260906_local_high_open_recall_diagnostic_receipt_v1.json`
- `docs/governance/local_session_20260906_high_open_recall_data_usage.json`

本地对照 OHR-01 验收：

1. `development_window.end == 2025-12-31`
2. `2026_rows_loaded == false`，`2026_blackbox_opened == false`
3. `candidate_selection_performed == false`
4. `parameter_search_performed == false`
5. `threshold_search_performed == false`
6. 2015–2020 reconstruction 全部字段 max-abs 为 `0.0`
7. `oof_years == [2016..2025]`，`n_oof == 2426`
8. 回执含 gap magnitude、FN score-margin、slow-state、asymmetric-US、catch-up、US-session-count 聚合诊断
9. `source_hashes` 完整（7 项）
10. `production_authority == false`

source hashes：

- `annotated_panel`: `4f093c51add311ade37634a1548a0c22b5f26b3390008d398a36b006c2f8ce69`
- `datahub_1m_export`: `aeacff04b268c166faac333ec7ab9d840abcd347d82cb3bcee0218d058fc7423`
- `fred_nasdaq`: `fad2f5f848d0acd4a9c86eebb75bc0d4f8fe18c1c6852bae3bb5c3a3c1a7bf5e`
- `fred_vix`: `37f565c00b758ebae9ef2144dc102b3a8560b0ce5941baf7bac21210aa9815d6`
- `incumbent`: `6fe8b600d35c599c55516a10db78e660473d5992c34b52ce471fdf12ab231b95`
- `protocol`: `421a96960d58082804635745ee7c991119db44c6b6146ce2f115b6c5bef8a787`
- `runner`: `2d157956469d2642432c377552e9f1dcabbe8d1aeeab3eed33463ffdeea859fa`

关键聚合（不据此冻结候选）：

- incumbent OOF：`direction_hit=0.71764`，`balanced_accuracy=0.70102`，`recall_up=0.62606`，`recall_down=0.77598`，`pred_up_share=0.38046` vs `actual_up_share=0.38912`，`roc_auc=0.76696`，`tp=591`，`fn=353`，`tn=1150`，`fp=332`。
- 年别 `recall_up`：2016 `0.730`，2017 `0.714`，2018 `0.441`，2019 `0.563`，2020 `0.646`，2021 `0.740`，2022 `0.587`，2023 `0.660`，2024 `0.580`，2025 `0.610`。
- 实际正缺口分桶 recall：`gt0_to_10bp` 340/147 漏判、`0.568`；`gt10_to_30bp` 301/118、`0.608`；`gt30bp` 302/87、`0.712`；`material>10bp` 603/205、`0.660`；`material>30bp` 同 `gt30bp`。
- FN score-margin：353 笔；中位 `10.88bp`，均值 `17.33bp`；`within_5bp` 94（26.6%），`5–15bp` 122（34.6%），`>15bp` 137（38.8%）。
- `holiday_reopen`：`insufficient_variation`。
- slow-state 探针 `fn-tp` 标准化差与年符号：`gap_up_share_20` `-0.044`（5+/5-）；`gap_up_share_60` `+0.037`（6+/4-）；`gap_mean_20` `-0.152`（6+/4-）；`gap_mean_60` `-0.031`（6+/4-）；`overnight_trend_5` `-0.125`（4+/6-）。
- US 不对称：`us_nasdaq_interval` `-0.867`（0+/10-）；`us_nasdaq_interval_pos` `-1.053`（0+/10-）；`us_nasdaq_interval_neg_abs` `+0.343`（10+/0-）；`us_vix_drop` `-0.864`（0+/10-）；`us_vix_rise` `+0.271`（10+/0-）；`global_risk_on_joint` `-0.609`（0+/10-）。Q4 NASDAQ interval 实际高开份额 `0.699`、recall `0.884`；Q1 份额 `0.168`、recall `0.137`。
- catch-up：`catchup_daytime_x_us_up` `-0.050`（3+/7-）；`catchup_afternoon_x_us_up` `-0.190`（3+/7-）；`catchup_last_hour_x_us_up` `-0.049`（3+/7-）。`prev_daytime_weakness` `+0.480`（10+/0-），其 Q4 实际高开 recall 仅 `0.425`。
- `us_session_count` `-0.099`（3+/7-）。

未验证 / 未做事项：

- 未打开 2026-01-05..2026-08-21 黑箱，也未读取其逐日明细。
- 未做候选排序、参数/阈值搜索或收益优化。
- 本地不裁决哪一个金融机制成立，不冻结 Phase 2 候选族。
- 未上传 2015+ 原始行情或逐日 OOF prediction。
