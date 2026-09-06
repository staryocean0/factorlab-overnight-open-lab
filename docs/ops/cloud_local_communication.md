# 云端—本地沟通记录

## OHR-01 — 高开漏判机制诊断（开发阶段，不打开 2026）

**状态：待本地执行并回写。**

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
