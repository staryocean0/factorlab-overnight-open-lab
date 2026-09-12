# Timing Layer 2 隔夜高低开账本 @1.2

状态：中证1000 隔夜缺口 ±30bp 为普通开盘；尾部建账。消息只记**该条信息落地后的第一个交易日**。  
合同：[`timing_layer2_overnight_gap_ledger@1.2.json`](timing_layer2_overnight_gap_ledger@1.2.json)  
父合同：[`timing_layer2_overnight_gap_ledger@1.1.json`](timing_layer2_overnight_gap_ledger@1.1.json)  
历史：[`timing_layer2_overnight_gap_ledger@1.0.json`](timing_layer2_overnight_gap_ledger@1.0.json)  
消息表：[`timing_layer2_overnight_gap_news_events@1.1.json`](timing_layer2_overnight_gap_news_events@1.1.json)  
入口：[`../user/timing_layer2_overnight_gap_ledger_workflow.md`](../user/timing_layer2_overnight_gap_ledger_workflow.md)  
权限：测量；无策略、路由、参数或生产权

这是隐含日内反转 1.0 的**补充账本**，不是 2.0，也不改 `@1.2` 四个桶，不改 `timing_layer2_measurement_plane@2.3`。

## 1. 隔夜是什么

`overnight_gap = 09:31 open / 昨 15:00 close − 1`。与 `@1.2` 时段件同一把尺子。平开（落在切刀内）不进尾部账本。

## 2. 分布不是干净正态

2015–2024 中证1000 隔夜：中位 |gap| 约 19bp，稳健 σ 约 27bp，中心更瘦、崩溃日把峰度拉肥。刀切在肩膀上，而不是被崩溃日撑大的样本标准差。

## 3. 切刀冻在 30bp

`|overnight_gap| ≤ 30bp` 记为 `ordinary_open`。禁止再网格。切刀只看 2015–2024；2025–2026-08-21 只套用。

## 4. 账本与优先级

尾部仍是 |隔夜| > 30bp。优先级：

1. **消息第一天** → `high_open_news` / `low_open_news`
2. **节假日复牌** → `high_open_holiday` / `low_open_holiday`
3. **剩下的非节假日高低开** → `high_open_normal` / `low_open_normal`

## 5. 消息只算第一天

同一条信息如果还在第二天、第三天、第四天制造高开或低开，那已经不是消息，是趋势。

重大信息不可能连续多天仍只是“标题”。若缺口持续，唯一解释是信息改变了市场的持续性方向：消息 → 趋势 → 高低开。后续高低开记入市场/趋势，不记入 news。

因此：

- 只保留该离散标题能够进入隔夜缺口的**第一个 A 股交易日**
- `widely_documented_cluster` 不再进 news
- 924 政策包的第一夜不是 2024-10-08，也不是 09-30；那两天是政策变成趋势之后的缺口
- 2015-07-06 救市只留 07-06；07-07/08/13/14 是救市后的趋势
- 2020-02-03 疫情开市只留 02-03；02-04 是第二天
- 黑色星期一只留 2015-08-24；08-25 是第二天

消息表按设计不完整。没对上的尾部日保持 `unannotated`，不等于没有消息，也不等于要把后续趋势日补进 news。


## 5b. 节假日高低开

市场停牌时趋势仍在走。国庆、春节这种长假，哪怕没有新标题，复牌那天也会把停牌期间攒下来的方向一次性计提进隔夜缺口。2024-10-08 不是 924 的“新消息日”，是 924 已经给出方向后、长假把趋势攒进开盘。

机械定义：上一个交易日到本日的日历间隔 **≥ 4 天**。标准周末是周五收到周一开 = 3 天，不算节假日。4 是刚好比周末长的整数，不网格 5/7/10。

消息优先于节假日：2020-02-03 疫情开市仍在 news，不进 holiday。holiday 只收非消息的长假复牌。

## 6. @1.0 审计

@1.0 有 40 条 news。@1.1 留下 17 条第一天，移出 23 条后续日。移出清单在消息表 `removed_from_v1_0_because_follow_through`。

官方 1 分钟序列里 2016-01-04、2016-01-07 熔断日是在的。01-04 隔夜普通，盘中熔断；news 只留 01-05 这一个隔夜首日。01-07 是熔断第二天，进市场，不进 news。

## 7. 权威

`production_authority=false`。不改 `@2.3` pointer。标注不是因果标签，不能当交易规则。
