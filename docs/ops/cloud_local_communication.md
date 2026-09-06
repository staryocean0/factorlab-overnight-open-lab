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

**状态：云端已复核通过，任务关闭。无增量 successor。OHR-03 未打开。**

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

---

## OHR-04 — last-hour rebound conditioning 诊断（开发阶段，不打开 2026，不选 successor）

**状态：本地已反馈，待云端复核。**

### 目标

解释被拒绝的 progression candidate `weakness_last_hour_piecewise` 为何能救回一部分实际高开，同时又制造过多新的高开误报。此任务只做诊断，不选择新模型、不冻结候选族、不打开 OHR-03 / 2026。

### 冻结输入

- Cloud OHR-02 复核：`docs/research/high_open_recall_phase2_cloud_review_20260906.md`
- 诊断协议：`docs/governance/cloud_session_20260906_high_open_rebound_conditioning_protocol_v1.json`
- 诊断器：`scripts/diagnose_last_hour_rebound_conditioning_dev.py`
- Incumbent：`median_quantile_sign`，spec SHA256 `9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465`
- 诊断用 progression candidate：`weakness_last_hour_piecewise`，spec SHA256 `1a37a46c4c66026f6abe33b84a9d7704ab7c7513312ef15b25607dcfa694392d`（仍为 rejected successor）

### 本地执行反馈（2026-09-06）

- 执行身份：本地 Codex controller；工作目录 `/home/starryocean/桌面/量化/factorlab-overnight-open-lab`。
- 执行时代码 SHA：`0a1aee02ac082a97e8ce2d310618f52f7600cc9f`（`Index OHR-04 rebound-conditioning handoff [skip ci]`）。
- 未设置路径覆盖环境变量；沿用既有本地默认源。
- 未读取 2026-01-05..2026-08-21 黑箱结果；post-2026-08-21 仍 unread；未打开 OHR-03。

| 命令 | 退出码 |
|---|---|
| `python3 scripts/validate_theme_package.py` | 0 |
| `python3 -m pytest -q` | 0（13 passed） |
| `python3 scripts/diagnose_last_hour_rebound_conditioning_dev.py` | 0 |

输出文件：

- `docs/research/cloud_session_20260906_local_last_hour_rebound_conditioning_receipt_v1.json` sha256 `ad5c5cb280f4c8da3de61aeccffbe16d0f7dc6229d25f0c5497514044cdc5008`
- `docs/governance/local_session_20260906_last_hour_rebound_conditioning_data_usage.json` sha256 `6956db15c8a9ae083d75f2139fa09b48aea1a8ff8d4e27b878908b0fe1ac8d0e`

终端摘要：`LAST_HOUR_REBOUND_CONDITIONING_RESULT` → `n_oof=2426`，`added_up_total=38`，`added_up_precision=0.42105263157894735`，`2026_blackbox_opened=false`，`candidate_selection_performed=false`。

本地对照 OHR-04 验收：

1. 执行代码 SHA 为 OHR-04 交接提交 `0a1aee02`；protocol / runner / tests 未在看到结果后修改。
2. validator / pytest / diagnostic 三条命令均退出 0。
3. `development_window.end == 2025-12-31`；`oof_years == [2016..2025]`；`n_oof == 2426`，与 OHR-02 库存一致。
4. incumbent / last-hour spec SHA 与冻结身份一致；runner 先 replay OHR-02 指标后才做 conditioning，退出码 0 表示 replay 通过。
5. disagreement 四类计数与 OHR-02 last-hour paired disagreements 完全对上：rescue+repaired=22，new-false-high+lost-high=30，total=52。
6. `2026_rows_loaded == false`，`2026_blackbox_opened == false`，`ohr_03_opened == false`。
7. `candidate_selection_performed == false`，`parameter_search_performed == false`，`threshold_search_performed == false`，`quantile_search_performed == false`，`trading_return_used == false`。
8. 2015–2020 reconstruction 全部字段 max-abs 为 `0.0`。
9. 预注册 12 个 continuous probes 与 3 个 binary probes 均有 pooled / annual / quartile 或 state 聚合；receipt 不含 `trading_day` 或逐日 OOF prediction。
10. `source_hashes` 完整（8 项）；其中 annotated_panel / datahub_1m_export / fred_nasdaq / fred_vix / family / phase2_receipt 与 OHR-02 一致；raw rows 未写入 bounded repo；`production_authority == false`。

source hashes：

- `annotated_panel`: `4f093c51add311ade37634a1548a0c22b5f26b3390008d398a36b006c2f8ce69`
- `datahub_1m_export`: `aeacff04b268c166faac333ec7ab9d840abcd347d82cb3bcee0218d058fc7423`
- `fred_nasdaq`: `fad2f5f848d0acd4a9c86eebb75bc0d4f8fe18c1c6852bae3bb5c3a3c1a7bf5e`
- `fred_vix`: `37f565c00b758ebae9ef2144dc102b3a8560b0ce5941baf7bac21210aa9815d6`
- `family`: `f06c43009de9e0b6844a45392caf740144b74fd9fca08bae904001c44ef2168c`
- `phase2_receipt`: `6a65180eaef2b1ef38ed5da52504f3f11018b802cc0aee2d7b83328938c113f5`
- `protocol`: `22f00dea7b9daa7d49399e6012954c68fe6de31ec02184bdef1357ffafeb0a44`
- `runner`: `8296eb8f79e430848943475189027c4bc49cff053cbd305354dd6e56083c43a7`

Disagreement morphology：

| 类型 | 计数 |
|---|---|
| incumbent down → candidate up, actual up（rescue） | 16 |
| incumbent down → candidate up, actual down（new false high） | 22 |
| incumbent up → candidate down, actual up（lost high） | 8 |
| incumbent up → candidate down, actual down（repaired false high） | 6 |
| added-up total / precision | 38 / 0.42105 |
| removed-up total | 14 |
| total disagreements | 52 |

年度 rescue vs new-false-high：rescue>FP 仅 3/10 年（2019、2020、2024），FP>rescue 5/10 年（2016、2017、2018、2021、2025），平 2/10 年（2022、2023）。

连续探针（rescue mean − false-high mean，标准化；年度差分为正/负年数）：

| probe | std diff | posY | negY |
|---|---|---|---|
| `prev_last_hour_weakness` | +0.502 | 4 | 1 |
| `prev_daytime_weakness` | +0.297 | 2 | 2 |
| `rvol20` | +0.285 | 3 | 2 |
| `r20` | +0.228 | 3 | 2 |
| `prev_afternoon_weakness` | +0.215 | 2 | 3 |
| `abs_r1` | +0.131 | 2 | 3 |
| `prev_gap_negative` | +0.090 | 2 | 2 |
| `prev_gap_positive` | −0.024 | 3 | 2 |
| `prev_gap` | −0.086 | 3 | 2 |
| `last_hour_minus_afternoon_weakness` | −0.090 | 4 | 1 |
| `r1` | −0.203 | 1 | 4 |
| `last_hour_minus_daytime_weakness` | −0.242 | 3 | 2 |

`prev_last_hour_weakness` 分位：Q1/Q2 added-up precision 均为 0.25（probe mean≈0，16 次翻转里 12 次新误报）；Q3=0.55（20 次，11 rescue / 9 FP）；Q4 n=2。也就是说，hinge 在 last-hour weakness 接近 0 时仍大量改判，而这些改判以新误报为主。

二元状态：

| state | n_added_up | precision | rescue | new FP | state1 better years |
|---|---|---|---|---|---|
| `tail_only_weakness=1` | 15 | 0.600 | 9 | 6 | 3/10 |
| `tail_only_weakness=0` | 23 | 0.304 | 7 | 16 | — |
| `tail_with_broad_afternoon_weakness=1` | 11 | 0.636 | 7 | 4 | 3/10 |
| `tail_with_broad_day_weakness=1` | 2 | 1.000 | 2 | 0 | 1/10（样本过少） |

诊断观察（不是候选选择，也不是机制录取）：

- 无条件 last-hour hinge 的 added-up precision 只有 0.42，净效果是多制造误报。
- 预注册探针里，最能分开 rescue 与 new FP 的是 `prev_last_hour_weakness` 本身（std +0.50，4/10 年同向），且低分位（weakness≈0）误报密集。
- `tail_only_weakness` / `tail_with_broad_afternoon_weakness` 的 pooled precision 更高，但年度支持弱（各仅 3 年更好），不能单独构成录取。
- 没有探针达到“稳定多年、干净分开 rescue 与 new false high”的机制录取门槛。本地不冻结任何新 family。

未验证 / 未做事项：

- 未打开 2026-01-05..2026-08-21 黑箱，也未读取其逐日明细。
- 未做候选 ranking、参数 / 分位 / 阈值搜索、新的 US 交互搜索或收益优化。
- 未打开 OHR-03，不授予 production / fresh-OOS authority。
- 未上传 2015+ 原始行情或逐日 OOF prediction。

---

## DATA-PACK-01 — 给云端补 2015–2025 开发包（仍不含 2026）

**状态：本地已推送，等待云端改用该 pack 自行跑开发诊断。**

云端原先只有 2015-01-05..2020-12-31。OHR-01/02/04 需要 2015-01-05..2025-12-31，所以才反复交接本地。缺口本身不大：

- 新增 `000852.SH` 1m 2021-2025：约 9.2MB；整段 2015-2025 1m pack 约 15.5MB
- 新增 annotated panel 2015-2025：0.20MB（2674 行）
- FRED NASDAQ/VIX 截到 2025-12-31：约 0.11MB
- **2026-01-05..2026-08-21 未放入仓库**（154 个交易日 / 约 1.4MB 1m 仍 sealed）
- post-2026-08-21 仍 unread

现已新增 `data/high_open_dev_2015_2025/`。原 `data/development/` 2015-2020 冻结包未改。本地若仍有 FactorLab/DataHub 绝对路径，则继续用原文件以保持既有 receipt source hash；云端缺这些路径时自动回退到该 pack。

用 pack 对 2015-2020 frozen panel 的 reconstruction max-abs 为 0。不打开 OHR-03，不授予 production / fresh-OOS。

---

## OHR-05 — Offshore-China ETF 源准入（只做源/日历质量，不打开中国目标诊断，不打开 2026）

**状态：本地已反馈，等待云端复核。预测诊断未授权。**

### 目标

在加载任何 CSI1000 / 中国目标诊断之前，冻结一个开发期-only 日线源身份，并证明 ASHS / ASHR / FXI / MCHI / SPY 的美国 regular-session 日历与价格可被审计。本任务不检验这些 ticker 是否预测 CSI1000 gap。

### 本地源检索（先 DataHub/cache，后单一外部源）

本地已有 cache / DataHub **不能**同时提供这五个 ticker 的 2015–2025 美国 regular-session 日线 `date, symbol, open, close, volume`：

- DataHub 产品目录与 `repository_assets.v1.json` 无美股/US-listed ETF 产品；`/api/v1` 本机 8400/8000 为 502，不能作为本任务取数面。
- overnight 开发包只有 FRED NASDAQ/VIX（及 FactorLab tmp 中的 FRED SP500 收盘），不是五 ticker OHLCV。
- FactorLab / overnight / `~/.cache` 无 ASHS/ASHR/FXI/MCHI/SPY 行情落盘。

因此从**同一个**外部供应商拉取全部五个 ticker。未按预测结果选源。尝试过但未能作为完整单源使用的接口：

- Yahoo Finance v8 chart：本机 IP 429。
- Stooq `.us` 日线 CSV：返回 JS 校验页，不是 CSV。
- 东方财富美股 K 线：ASHS/ASHR/FXI/MCHI 有 secid，SPY 探测被断开，不能五 ticker 齐套。
- Nasdaq historical API：2015 窗口 `totalRecords=0`。

唯一一次五 ticker 齐套成功的单源是新浪美股日线 `https://finance.sina.com.cn/staticdata/us/{symbol}`，经 `akshare.stock_us_daily(..., adjust="")` 读取。冻结该供应商，不再混源。

### 冻结身份

- 执行时代码 SHA：`50c8b47be3d0702c713f286f181407a0d8f937d8`（其后 `48e81fa` 只改 `package_scope` 可见性；protocol / runner blob 未变）
- 回传 commit：`341e25d3574fd761ed1ef659e6040cbab0038a82`
- provider：`Sina Finance US daily staticdata via akshare.stock_us_daily`
- provider_id：`finance.sina.com.cn/staticdata/us/{symbol}; akshare==1.18.64; adjust=''; development export 2015-01-01..2025-12-31`
- price_convention：`raw unadjusted regular-session OHLC from Sina US daily; close/open-1 is same-session return; qfq unused`
- 本地源（不入库）：`/home/starryocean/桌面/量化/.local_overnight_data/ohr05_offshore_etf_daily_2015_2025.parquet`
- local source SHA256：`a0cddb61230510d6e5e2a2eef44b5ecfceb18adeed26b9f2c86a8e7d09472f15`
- 源文件最大日期 `2025-12-31`；远端原始文件含 2026 行，导出时已截断。未上传原始行。

### 命令与退出码

| 命令 | 退出码 |
|---|---|
| `python3 scripts/validate_theme_package.py` | 0 |
| `python3 -m pytest -q` | 0（18 passed） |
| `python3 scripts/probe_offshore_china_source_quality.py` | 0 |

输出文件：

- `docs/research/cloud_session_20260906_local_offshore_china_source_freeze_v1.json` sha256 `45bfa20bdd3b0401e346349ce3c738adea0077218e0abb4b510a44b5f5695eb6`
- `docs/governance/local_session_20260906_offshore_china_source_data_usage.json` sha256 `66adb2b9685b745bfb831c114eb2d98ef14d94e3f56f2120be49fe839b971aef`

receipt 字段：`predictive_target_loaded=false`，`candidate_selection_performed=false`，`2026_rows_loaded=false`，`2026_blackbox_opened=false`。

### 相对 SPY 的覆盖（SPY 锚点 2765 个 regular session）

| symbol | first | last | present / SPY | missing | coverage | invalid price/vol | zero volume | zero return | session ret min / max |
|---|---|---|---|---|---|---|---|---|---|
| SPY | 2015-01-02 | 2025-12-31 | 2765 / 2765 | 0 | 1.000 | 0 / 0 | 0 | 12 | −5.66% / +11.18% |
| FXI | 2015-01-02 | 2025-12-31 | 2765 / 2765 | 0 | 1.000 | 0 / 0 | 0 | 50 | −5.67% / +8.53% |
| ASHR | 2015-03-31 | 2025-12-31 | 2703 / 2765 | 62 | 0.978 | 0 / 0 | 0 | 86 | −5.21% / +5.11% |
| ASHS | 2015-03-31 | 2025-12-31 | 2690 / 2765 | 75 | 0.973 | 0 / 0 | 0 | 98 | −14.37% / +6.10% |
| MCHI | 2016-02-02 | 2025-12-31 | 2494 / 2765 | 271 | 0.902 | 0 / 0 | 0 | 23 | −5.63% / +7.47% |

`abs_session_return_gt_20pct_rows` 全部为 0。ASHS 最大同日回撤是 2015-08-24 的 −14.37%（开 43.07 / 收 36.88），属价格极端诊断，不是拆分跳空。2015–2025 未见拆分不连续；`adjust=""` 的开收盘作为同一口径使用。

### 显著年度缺口

这些缺口是新浪历史截断/漏行，不是上市日约束（ASHS 2014-05、ASHR 2013-11、MCHI 2011-03 均早于 2015）。

- ASHR：全部 62 个缺失都在 2015-01-02..2015-03-30；2016–2025 对 SPY 覆盖 1.0。
- ASHS：2015 同样缺 62 天（2015-01-02..2015-03-30）；另有 2016-12-08；2023-10-27 / 11-15 / 11-24 / 11-27；2024-04-05 / 04-25 / 05-01 / 05-08 / 05-13 / 05-23 / 06-10；2025-03-28。
- MCHI：2015 全年 251/251 缺失（coverage 0）；2016-01-04..2016-02-01 再缺 20 天；2016-02-02 起至 2025-12-31 对 SPY 覆盖 1.0。
- FXI / SPY：2015–2025 无相对缺口。

### 本地对照 OHR-05 验收

1. 执行代码 SHA 为交接前提交 `50c8b47`；protocol / runner / tests 未在看到源质量后修改。
2. validator / pytest / source probe 三条命令均退出 0。
3. 源文件与 receipt 均截到 `2025-12-31`；未加载中国目标、annotated panel、CSI1000 gap，也未打开 OHR-03。
4. `2026_rows_loaded == false`，`2026_blackbox_opened == false`。
5. 未改固定 ticker 集合，未按 ticker 拼接不同供应商。
6. raw ETF 行未写入 bounded repo；`production_authority == false`。

### 未决测量问题（供云端源复核，不是预测结论）

- 新浪是本机唯一能五 ticker 齐套的单源，但 **MCHI 缺整个 2015 和 2016-01**，ASHR/ASHS 缺 2015Q1。这是供应商历史截断。MCHI 上市远早于 2015，不能解释为 inception。
- ASHS 在 2016/2023/2024/2025 另有 13 个零星相对 SPY 缺失；协议要求 SPY 有会话而源行缺失时不得 silently 当 0。
- Yahoo / Stooq / 东方财富未能在本机作为完整单源使用。若云端认为日历完整性未解决，状态应为 `infrastructure_or_measurement_gap`，另立新源身份后再取；本地不在看到质量后换 ticker 或混源。
- 未打开 2026-01-05..2026-08-21 黑箱，未读取 post-2026-08-21 目标，未做候选 / 参数 / 阈值 / 收益搜索。
