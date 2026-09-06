# 云端—本地沟通记录

## OHR-01 — 高开漏判机制诊断（开发阶段，不打开 2026）

**状态：云端已复核通过，任务关闭。**

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

### 本地执行反馈（2026-09-06）

- 本地执行时代码 SHA：`266a5d97df35899e23ca14c88eb4da9b4bfaf969`。
- `python3 scripts/validate_theme_package.py`：退出码 0。
- `python3 -m pytest -q`：退出码 0，9 passed。
- `python3 scripts/diagnose_high_open_false_negatives_dev.py`：退出码 0。
- 回传 commit：`cfadb9c0d106952a4915c125bf1b6fee4d72e846`。
- 输出：
  - `docs/research/cloud_session_20260906_local_high_open_recall_diagnostic_receipt_v1.json`
  - `docs/governance/local_session_20260906_high_open_recall_data_usage.json`
- 本地未打开 2026 黑箱；未做候选、参数、quantile、threshold 或收益搜索；未上传原始开发行情或逐日 OOF prediction。

### 云端复核（2026-09-06）

复核结论：**通过**。

完整性检查：

1. `266a5d9..cfadb9c` 之间仅新增/修改 aggregate receipt、data-usage、communication、INDEX；冻结诊断脚本、协议和测试没有在看到结果后被修改。
2. `development_window.end == 2025-12-31`；`oof_years == [2016..2025]`；`n_oof == 2426`。
3. `2026_rows_loaded == false`；`2026_blackbox_opened == false`。
4. `candidate_selection_performed == false`；`parameter_search_performed == false`；`threshold_search_performed == false`；`trading_return_used == false`。
5. 2015–2020 reconstruction 全字段 max-abs = 0；source hashes 与既有本地源身份一致。
6. raw development rows 未写入 bounded repo；production authority=false。

机制裁决已写入：`docs/research/high_open_recall_phase1_adjudication_20260906.md`。

核心裁决：

- H1 边界噪声只能解释一部分，不是主因；205/353 个 FN 是 >10bp 高开，87/353 是 >30bp，高开漏判不能靠轻微阈值平移解决。
- H2 慢 opening regime 状态不稳定，不进入候选族。
- H3 正向 US risk-on 通道并不缺失：NASDAQ interval Q4 的实际高开 recall 已达约 0.884；剩余错误主要发生在没有强正向 US 信息却仍高开的日子，因此不新增正向 US terms。
- H4 原预注册的“中国弱势 × US-up”交互不稳定，拒绝。
- H5 US-session-count / holiday-reopen 不支持作为方向 recall successor。
- H6 **prior-China-weakness nonlinear rebound** 获得支持：full-day / afternoon / last-hour weakness 在 FN 相对 TP 的差异均为 10/10 年同方向，其中 full-day 与 last-hour 最强。允许用 negative-part piecewise basis 测试负收益侧单独斜率。

OHR-01 到此关闭。2026 黑箱仍未打开。

---

## OHR-02 — 高开漏判 Phase-2 分段弱势候选选择（开发阶段，不打开 2026）

**状态：本地已反馈，待云端复核。**

### 目标

在 Phase-1 唯一获支持的金融机制 `prior_china_weakness_nonlinear_rebound` 上，比较一个严格有界的低容量候选族，判断是否存在能提高 high-open recall、同时不牺牲 incumbent 总体方向质量的 successor。

这一步是 **development selection**，不是 2026 黑箱，也不是 fresh validation。

### 冻结输入

- Phase-1 裁决：`docs/research/high_open_recall_phase1_adjudication_20260906.md`
- Phase-2 family：`docs/governance/cloud_session_20260906_high_open_recall_phase2_family_v1.json`
- Selector：`scripts/select_high_open_recall_phase2_dev.py`
- Incumbent：`median_quantile_sign`，spec SHA256 `9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`

### 冻结数学形式

Estimator 保持不变：

`StandardScaler + QuantileRegressor(quantile=0.5, alpha=0.0, solver=highs)`

Target 保持 `gap`，判定保持 `prediction >= 0`。

原 13 个 direction features 全部保留。唯一允许增加的是：

- `prev_daytime_weakness = max(-prev_daytime, 0)`
- `prev_afternoon_weakness = max(-prev_afternoon, 0)`
- `prev_last_hour_weakness = max(-prev_last_hour, 0)`

候选严格只有四个：

1. `weakness_daytime_piecewise`
2. `weakness_afternoon_piecewise`
3. `weakness_last_hour_piecewise`
4. `weakness_three_horizon_piecewise`

不得加入任何其他组合或数据源。

### 冻结开发选择

- 原始开发窗口：2015-01-05..2025-12-31。
- OOF：2016..2025 expanding natural-year。
- 每个候选使用与 incumbent 相同 complete-row mask。

候选有资格被选择必须同时满足：

1. pooled `recall_up` 严格高于 incumbent；
2. pooled `direction_hit >= incumbent`；
3. pooled `balanced_accuracy >= incumbent`；
4. pooled `recall_down > 0.5`；
5. 10 个 OOF 年里至少 6 年 `recall_up` delta > 0；
6. 年度 `recall_up` delta 中位数 >= 0；
7. actual gap >10bp 的 high-open recall 不低于 incumbent；
8. actual gap >30bp 的 high-open recall 不低于 incumbent。

若多个候选通过，依次按 pooled recall_up、balanced accuracy、direction hit 降序，再按 extra feature 数量、名称排序。

如果没有候选通过：保留 incumbent，**不要打开 2026 repeat blackbox**。

如果有候选通过：本地只回传开发 selection receipt；**仍然不要打开 2026**。由云端先复核并冻结 exact successor identity，之后才另立 OHR-03 黑箱协议。

### 本地执行命令

```bash
python3 scripts/validate_theme_package.py
python3 -m pytest -q
python3 scripts/select_high_open_recall_phase2_dev.py
```

如本地源路径移动，只允许使用已有四个 path override 环境变量；不得修改 family、selector、OOF 年份、gate 或模型语义来适配结果。

### 2026 denylist

OHR-02 期间不得为了候选设计/选择读取或引用：

- `docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json`
- `docs/research/cloud_session_20260906_local_2026_direction_result.md`
- 任何 2026-01-05..2026-08-21 逐日 target/prediction/trade 数据
- post-2026-08-21 任何 target 或结果材料

治理文件中“2026 已消费/必须封存”的边界信息允许读取；结果内容禁止用于本轮选择。

### 预期输出

Selector 应只新增：

- `docs/research/cloud_session_20260906_local_high_open_recall_phase2_dev_receipt_v1.json`
- `docs/governance/local_session_20260906_high_open_recall_phase2_data_usage.json`

并在终端打印 `HIGH_OPEN_RECALL_PHASE2_SELECTION_RESULT ...`。

不要提交 2015+ 原始行情、逐日 OOF prediction 或 2026 数据。

### 云端验收条件

至少检查：

1. 本地执行代码 SHA 是本 OHR-02 冻结后的代码版本；
2. validator / pytest / selector 三条命令均退出 0；
3. family multiplicity = 4，实际 attempts 恰好 4；
4. `development_window.end == 2025-12-31`，OOF 只覆盖 2016–2025，`n_oof` 与 incumbent 库存一致；
5. `2026_rows_loaded == false`、`2026_blackbox_opened == false`；
6. `parameter_search_performed == false`、`threshold_search_performed == false`、`quantile_search_performed == false`；
7. same complete-row mask 检查通过；
8. 每个 attempt 的 eligibility gates、annual recall-up deltas、material >10bp/>30bp recall、paired disagreements 完整；
9. selected 结果严格由冻结排序规则产生；若无人 eligible，decision 必须是 retain incumbent；
10. source hashes 完整且 raw rows 未写入 bounded repo；production authority=false。

### 本地完成后回写

在本节末尾追加：执行 commit SHA、三条命令退出码、两个输出路径、四个候选的核心指标/gate、selected/decision、source hashes，以及任何失败或未验证事项。云端复核前不得打开 2026。

### 本地执行反馈（2026-09-06）

- 执行身份：本地 controller；工作目录 `/home/starryocean/桌面/量化/factorlab-overnight-open-lab`。
- 执行时代码 SHA：`5c734f36f49a80dc46ebdd67b66895740c807b1e`（`Index OHR-02 execution freeze [skip ci]`）。
- 未设置路径覆盖环境变量；沿用既有本地默认源。
- 未读取 2026 黑箱结果材料做候选设计或选择；未打开 OHR-03。

| 命令 | 退出码 |
|---|---|
| `python3 scripts/validate_theme_package.py` | 0 |
| `python3 -m pytest -q` | 0（11 passed） |
| `python3 scripts/select_high_open_recall_phase2_dev.py` | 0 |

输出文件：

- `docs/research/cloud_session_20260906_local_high_open_recall_phase2_dev_receipt_v1.json`
- `docs/governance/local_session_20260906_high_open_recall_phase2_data_usage.json`

终端摘要：`HIGH_OPEN_RECALL_PHASE2_SELECTION_RESULT` → `eligible_candidate_count=0`，`selected=null`，`decision=retain_incumbent_do_not_open_repeat_blackbox`，`2026_blackbox_opened=false`。

本地对照 OHR-02 验收：

1. 执行代码 SHA 为 OHR-02 冻结后的 `5c734f36`；family/selector blob 与 execution freeze 一致。
2. validator / pytest / selector 三条命令均退出 0。
3. family multiplicity = 4，实际 attempts 恰好 4。
4. `development_window.end == 2025-12-31`；`oof_years == [2016..2025]`；`n_oof == 2426`，与 incumbent / OHR-01 库存逐字段一致。
5. `2026_rows_loaded == false`，`2026_blackbox_opened == false`。
6. `parameter_search_performed == false`，`threshold_search_performed == false`，`quantile_search_performed == false`，`trading_return_used == false`。
7. 2015–2020 reconstruction 全部字段 max-abs 为 `0.0`；same complete-row mask 未触发 runner 失败。
8. 每个 attempt 含 eligibility gates、年度 `recall_up` delta、material >10bp/>30bp recall、paired disagreements。
9. 独立重算 4 组门禁与 receipt 完全一致；`eligible_candidate_count == 0`，因此 `selected == null`，decision 必须是 retain incumbent。
10. `source_hashes` 完整（7 项）；raw rows 未写入 bounded repo；`production_authority == false`。

source hashes：

- `annotated_panel`: `4f093c51add311ade37634a1548a0c22b5f26b3390008d398a36b006c2f8ce69`
- `datahub_1m_export`: `aeacff04b268c166faac333ec7ab9d840abcd347d82cb3bcee0218d058fc7423`
- `fred_nasdaq`: `fad2f5f848d0acd4a9c86eebb75bc0d4f8fe18c1c6852bae3bb5c3a3c1a7bf5e`
- `fred_vix`: `37f565c00b758ebae9ef2144dc102b3a8560b0ce5941baf7bac21210aa9815d6`
- `incumbent`: `6fe8b600d35c599c55516a10db78e660473d5992c34b52ce471fdf12ab231b95`
- `family`: `f06c43009de9e0b6844a45392caf740144b74fd9fca08bae904001c44ef2168c`
- `runner`: `ad171ecdd374ee2bd4543da1f7830754329d1cf0533876b51c17388aaa55d18a`

Incumbent OOF（与 OHR-01 完全相同）：`direction_hit=0.7176422093981863`，`balanced_accuracy=0.7010188647956266`，`recall_up=0.6260593220338984`，`recall_down=0.7759784075573549`，`tp=591`，`fn=353`，`tn=1150`，`fp=332`，`material>10bp recall=0.6600331674958541`，`material>30bp recall=0.7119205298013245`。

四个候选核心指标 / gate（本地独立重算，无人 eligible）：

| 候选 | recall_up | direction_hit | balanced_accuracy | recall_down | pos-year | median Δrecall_up | >10bp | >30bp | eligible |
|---|---|---|---|---|---|---|---|---|---|
| `weakness_daytime_piecewise` | 0.62182 | 0.71476 | 0.69789 | 0.77395 | 2/10 | 0.0 | 0.66003 | 0.70861 | 否 |
| `weakness_afternoon_piecewise` | 0.62288 | 0.71311 | 0.69673 | 0.77058 | 3/10 | 0.0 | 0.66335 | 0.71523 | 否 |
| `weakness_last_hour_piecewise` | 0.63453 | 0.71434 | 0.69986 | 0.76518 | 5/10 | +0.00459 | 0.66998 | 0.71854 | 否 |
| `weakness_three_horizon_piecewise` | 0.62712 | 0.71311 | 0.69750 | 0.76788 | 4/10 | 0.0 | 0.66335 | 0.70861 | 否 |

失败门禁摘要：

- `weakness_daytime_piecewise`：recall_up / hit / BA / 6-year / >30bp 未过。
- `weakness_afternoon_piecewise`：recall_up / hit / BA / 6-year 未过。
- `weakness_last_hour_piecewise`：pooled recall_up 与 material 10/30bp 提高，但 hit、BA 下降，且仅 5/10 年 Δrecall_up>0。
- `weakness_three_horizon_piecewise`：pooled recall_up 略升，但 hit / BA / 6-year / >30bp 未过。

`selected`：无。`decision`：`retain_incumbent_do_not_open_repeat_blackbox`。

未验证 / 未做事项：

- 未打开 2026-01-05..2026-08-21 黑箱，也未读取其逐日明细做选择。
- 未做参数 / 分位 / 阈值搜索或收益优化。
- 本地不冻结新 successor，不打开 OHR-03。
- 未上传 2015+ 原始行情或逐日 OOF prediction。

### Codex controller 独立重跑（2026-09-06）

- 执行身份：本地 Codex controller；工作目录 `/home/starryocean/桌面/量化/factorlab-overnight-open-lab`。
- 重跑时 HEAD：`32e976cfded98463677d2c74b09f33de9c99b761`（已含上一轮本地 selection receipt）。family / selector / tests 相对 OHR-02 冻结提交 `5c734f36f49a80dc46ebdd67b66895740c807b1e` 无 diff。
- 未设置路径覆盖环境变量；未读取 2026 黑箱逐日结果做候选设计或选择；未打开 OHR-03。

| 命令 | 退出码 |
|---|---|
| `python3 scripts/validate_theme_package.py` | 0 |
| `python3 -m pytest -q` | 0（11 passed） |
| `python3 scripts/select_high_open_recall_phase2_dev.py` | 0 |

- selector 终端摘要再次为 `eligible_candidate_count=0`，`selected=null`，`decision=retain_incumbent_do_not_open_repeat_blackbox`，`2026_blackbox_opened=false`。
- 重跑后 receipt / data-usage 相对 `32e976c` 字节级相同：
  - `docs/research/cloud_session_20260906_local_high_open_recall_phase2_dev_receipt_v1.json` sha256 `6a65180eaef2b1ef38ed5da52504f3f11018b802cc0aee2d7b83328938c113f5`
  - `docs/governance/local_session_20260906_high_open_recall_phase2_data_usage.json` sha256 `5712a64c18bd9bd5e6ddc60b19280bc21721e0e665c01b45e577ab506b4df56d`
- 独立重算 4 组 eligibility gates，与 receipt 完全一致；无人 eligible，因此必须保留 `median_quantile_sign`，不得打开 2026。
- 本附记只确认上一轮本地反馈可复现，不新增候选、不改门禁、不授予 production / fresh-OOS authority。
