# Layer 2 隐含日内反转 K 线属性

> **第 2 层 · K 线测量。** V1.2 普通日主桶：|涨跌幅|≤1% 且振幅≤2%；再按周线上涨 / 普通 / 下跌拆成三桶。不算方向，不改闸，不选合约。不修改 `timing_layer2_measurement_plane@2.3` current pointer。

这是该属性的**唯一渐进入口**。第 1 层时钟仍走 [`market_state_session_clock_reference_workflow.md`](market_state_session_clock_reference_workflow.md)。

## 五位一体

| 角色 | 权威入口 |
|---|---|
| 文档 | 本文 |
| 白皮书 | [`../ops/timing_layer2_implied_intraday_reversal_whitepaper.md`](../ops/timing_layer2_implied_intraday_reversal_whitepaper.md) |
| 代码 | `src/factor_lab/market_state/timing_layer2_implied_intraday_reversal.py` |
| 测试 | `tests/unit/test_timing_layer2_implied_intraday_reversal.py` |
| 工作流 | 本文的重建与消费顺序 |

当前合同：[`../ops/timing_layer2_implied_intraday_reversal@1.2.json`](../ops/timing_layer2_implied_intraday_reversal@1.2.json)。  
历史：[`@1.1`](../ops/timing_layer2_implied_intraday_reversal@1.1.json)、[`@1.0`](../ops/timing_layer2_implied_intraday_reversal@1.0.json)。  
属性池 overlay（未并入默认 publish）：[`../ops/market_state_attribute_pool_overlay_timing_layer2_implied_intraday_reversal@1.0.json`](../ops/market_state_attribute_pool_overlay_timing_layer2_implied_intraday_reversal@1.0.json)。

## 本步

```text
docs/ops/timing_layer2_implied_intraday_reversal@1.2.json
docs/ops/timing_layer2_implied_intraday_reversal_whitepaper.md
src/factor_lab/market_state/timing_layer2_implied_intraday_reversal.py
tests/unit/test_timing_layer2_implied_intraday_reversal.py
scripts/build_timing_layer2_implied_intraday_reversal.py
docs/ops/evidence/timing_layer2_implied_intraday_reversal_v1_2_20260905/
```

验证：

```bash
PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_timing_layer2_implied_intraday_reversal.py tests/unit/test_documentation_consistency.py -k implied_intraday_reversal
PYTHONPATH=src .venv/bin/python scripts/build_timing_layer2_implied_intraday_reversal.py --overwrite
```

## 四个桶

1. `daily_main`：|close-to-close|≤1% 且 (high-low)/昨收 ≤2%。
2. `main_weekly_up`：主桶 ∩ 周净涨 >2.5%。
3. `main_weekly_ordinary`：主桶 ∩ 周 |净涨跌|≤2.5% 且周振幅≤5%。
4. `main_weekly_down`：主桶 ∩ 周净跌 < -2.5%。

振幅按涨跌幅两倍冻结。15 分钟仍只作过细对照。2025+ 读取 0 行。`production_authority=false`。

## 当前形状（周线普通 ∩ 日线主桶）

净涨跌 ≈ 0。平均路径是：上午涨 → 13:00–14:00 回吐 → 14:00–15:00 再抬 → 隔夜再吐。隔夜和上午跨年更稳；13:00–14:00 变负是 2018 年后的换挡，不是永恒下跌腿。这是测量结论，不是盘中闸。

## 1.0 补充账本

隔夜高低开的日子单独建账，不改上面四个桶。入口：[`timing_layer2_overnight_gap_ledger_workflow.md`](timing_layer2_overnight_gap_ledger_workflow.md)。合同 [`../ops/timing_layer2_overnight_gap_ledger@1.2.json`](../ops/timing_layer2_overnight_gap_ledger@1.2.json)。
