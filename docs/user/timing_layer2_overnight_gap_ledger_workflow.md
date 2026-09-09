# Layer 2 隔夜高低开账本

> **第 2 层 · K 线测量补充。** 中证1000 隔夜缺口 ±30bp 为普通开盘。消息只记第一天；长于周末的闭市复牌另建节假日账本；剩下才是普通高低开。不算方向，不改闸，不选合约。不修改 `timing_layer2_implied_intraday_reversal@1.2`，不修改 `timing_layer2_measurement_plane@2.3`。

这是该账本的**唯一渐进入口**。父属性仍走 [`timing_layer2_implied_intraday_reversal_workflow.md`](timing_layer2_implied_intraday_reversal_workflow.md)。第 1 层时钟仍走 [`market_state_session_clock_reference_workflow.md`](market_state_session_clock_reference_workflow.md)。

## 五位一体

| 角色 | 权威入口 |
|---|---|
| 文档 | 本文 |
| 白皮书 | [`../ops/timing_layer2_overnight_gap_ledger_whitepaper.md`](../ops/timing_layer2_overnight_gap_ledger_whitepaper.md) |
| 代码 | `src/factor_lab/market_state/timing_layer2_overnight_gap_ledger.py` |
| 测试 | `tests/unit/test_timing_layer2_overnight_gap_ledger.py` |
| 工作流 | 本文的重建与消费顺序 |

当前合同：[`../ops/timing_layer2_overnight_gap_ledger@1.2.json`](../ops/timing_layer2_overnight_gap_ledger@1.2.json)。  
消息表：[`../ops/timing_layer2_overnight_gap_news_events@1.1.json`](../ops/timing_layer2_overnight_gap_news_events@1.1.json)。  
历史：[`../ops/timing_layer2_overnight_gap_ledger@1.1.json`](../ops/timing_layer2_overnight_gap_ledger@1.1.json)、[`../ops/timing_layer2_overnight_gap_ledger@1.0.json`](../ops/timing_layer2_overnight_gap_ledger@1.0.json)、[`../ops/timing_layer2_overnight_gap_news_events@1.0.json`](../ops/timing_layer2_overnight_gap_news_events@1.0.json)。

## 本步

```text
docs/ops/timing_layer2_overnight_gap_ledger@1.2.json
docs/ops/timing_layer2_overnight_gap_news_events@1.1.json
docs/ops/timing_layer2_overnight_gap_ledger_whitepaper.md
src/factor_lab/market_state/timing_layer2_overnight_gap_ledger.py
tests/unit/test_timing_layer2_overnight_gap_ledger.py
scripts/build_timing_layer2_overnight_gap_ledger.py
docs/ops/evidence/timing_layer2_overnight_gap_ledger_v1_2_20260905/
```

验证：

```bash
PYTHONPATH=src .venv/bin/pytest -q tests/unit/test_timing_layer2_overnight_gap_ledger.py tests/unit/test_documentation_consistency.py -k overnight_gap_ledger
PYTHONPATH=src .venv/bin/python scripts/build_timing_layer2_overnight_gap_ledger.py --overwrite
```

## 优先级

1. `high_open_news` / `low_open_news`：该离散标题的第一个交易日。
2. `high_open_holiday` / `low_open_holiday`：非消息、且上一个交易日到本日日历间隔 ≥ 4 天（长于标准周末）。停牌期间攒下的趋势在复牌计提。
3. `high_open_normal` / `low_open_normal`：剩下的非节假日高低开。

2024-10-08 进 holiday，不进 news。`production_authority=false`。
