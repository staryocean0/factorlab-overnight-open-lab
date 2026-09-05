# CSI1000 次日开盘缺口：全球市场传导与候选因子预研究（2026-09-05）

## 结论先行

本轮目标不是堆全球指数，而是寻找在中国 09:31 之前已经可见、且能在 `us_nasdaq` 之外提供独立信息的变量。

当前冻结 receipt 有一个必须正视的事实：2019-2020 `us_nasdaq` 单变量 IC=0.48416，高于 13 因子 Ridge 的 IC=0.45698。因此新增因子的有效门槛不是“相关”，而是 **在严格 PIT 时钟下对 NASDAQ 单变量产生增量**。

### 研究优先级

**Tier A：当前仓库即可验证**

1. 中国休市期间“尚未被 A 股吸收”的累计 NASDAQ 变化，而非只取最后一个美国交易日。
2. 美国上涨/下跌冲击不对称。
3. 美国冲击与中国自身波动/弱势状态的交互。

**Tier B：需要本地控制器未来补入 2015-2020 PIT 历史后才允许验证**

1. SGX FTSE China A50 夜盘/中国开盘前收益：直接指向中国资产，优先级最高。
2. USDCNH 中国开盘前变化：离岸人民币是跨市场信息传递的重要载体。
3. KOSPI 当日开盘至中国 09:30 前收益：韩国比日本更值得优先验证。
4. 中国商品期货夜盘：全球商品冲击在中国夜盘中的本地吸收。
5. 日本 Nikkei/TOPIX 08:00-09:30（北京时间）收益：只作为增量候选，文献对 Japan -> China 很不乐观。
6. 欧洲前一日收盘收益：时间上可用，但很可能已被更晚结束的美国市场吸收，应先残差化/做增量检验。
7. 09:15-09:25/09:30 开盘集合竞价不平衡、指示价格偏离等：最接近目标，但当前仓库没有订单簿数据。

## 文献证据

### 1. 美国 -> 中国次日开盘：高置信度

**The interactions between China and US stock markets: New perspectives**，Journal of International Financial Markets, Institutions and Money, 2014，DOI: `10.1016/j.intfin.2014.04.008`。

研究明确利用中美交易时段不重叠这一结构，并发现美国市场日收益对中国市场下一交易日开盘具有预测能力，金融危机后尤其明显。这与本项目 target 的时间方向完全一致。

**Half-day trading and spillovers between the U.S. and Chinese stock markets**（2010-2020 数据）。结论重点是美国到中国的收益溢出主要体现在中国下一交易日的上午，而不是下午。对本项目而言，这比泛泛的 close-to-close 联动更直接。

**Effect of the U.S.-China Trade War on Stock Markets: A Financial Contagion Perspective** 进一步提示负跳跃/坏消息可能成为不同于连续波动的传染通道，因此把美股正负冲击完全线性对称处理未必充分。

工程含义：
- 保留 NASDAQ 为强基准；
- 只增加低自由度的非对称项与状态交互；
- 不把 S&P、Dow、NASDAQ 三个高度共线指数机械并列。

### 2. 全球市场预测 opening gap：时间顺序比“国家列表”更重要

De Gooijer, Diks & Gatarek, **Information Flows Around the Globe: Predicting Opening Gaps from Overnight Foreign Stock Price Patterns**，2009/2012，SSRN 1510069。

研究直接预测 close-to-open gap，使用目标市场开盘前已经发生的外国市场高频价格路径；非参数模型总体更好，尤其欧洲和亚洲信息显示非线性价值，而北美/澳洲最后可见信息用线性模型已经较有效。

2026 年 Borsa Istanbul Review 的 **When ‘overnight’ is not simultaneous: Turning cross index overnight returns into feasible forecasts of morning gaps** 对 24 个全球指数显式统一到 UTC+8，并只允许目标市场开盘前的信息进入预测；结果强调预测价值取决于市场在全球交易时钟中的位置，而不是简单的同步相关。

工程含义：
- 每一个外盘变量都必须定义 `information_available_at`；
- 日韩因当天早于 A 股开盘，真正有价值的是“同日开盘后至 09:30 的已发生价格发现”，而非只看昨收；
- 欧洲和美国都已结束，但欧洲信息必须证明没有被随后美国交易时段完全吸收。

### 3. 日本：不应因为地理接近就高权重

Nishimura, Tsutsui & Hirayama, **The Chinese Stock Market Does not React to the Japanese Market: Using Intraday Data to Analyse Return and Volatility Spillover Effects**，Japanese Economic Review, 2016，DOI: `10.1111/jere.12086`。

5 分钟重叠时段研究得到的核心结果是收益影响主要为 **China -> Japan** 单向，而非 Japan -> China。

工程含义：
- Nikkei/TOPIX 只能作为待证伪的低优先级增量变量；
- 若未来获取 08:00-09:30 数据，应先检验其对 NASDAQ/A50/CNH 后的 partial IC，而不是直接入主模型。

### 4. 韩国：比日本更值得做中国开盘前同日 price discovery

既有中韩高频溢出研究发现，美股同时影响中国和韩国，并有证据表明 KOSPI 的开盘价格收益会向中国市场传递。由于韩国现金市场北京时间约 08:00 已开盘，它在中国 09:31 之前形成了一段真实、可交易时钟上的亚洲价格发现窗口。

工程含义：未来优先请求：
- `kospi_ret_open_to_0900_cn`
- `kospi_ret_open_to_0920_cn`
- 最终只冻结一个不越过 09:30 的机制派生点，不做 cutoff 网格搜索。

### 5. 离岸人民币 CNH：高优先级跨市场传导变量

Chen, Mo, Qin & Yang, **Return spillover across China's financial markets**，Pacific-Basin Finance Journal, 2023，DOI: `10.1016/j.pacfin.2023.102057`。

文献发现汇率市场，尤其离岸人民币，具有重要的信息传递作用，能向股票和债券市场传输信息；2015 汇改等阶段会改变传导。

工程含义：未来若补 PIT 数据，优先构造：
- 前一 A 股收盘后到 09:30 的 `USDCNH` 方向与幅度；
- 极端贬值/升值非对称项；
- 与 VIX/NASDAQ 的正交残差，而不是简单多列共线输入。

### 6. SGX FTSE China A50：比欧美广义指数更贴近中国资产本身

Han, Ryu, Guo & Liu, **A Tale of Two Index Futures: The Intraday Price Discovery and Volatility Transmission Processes between the China Financial Futures Exchange and the Singapore Exchange**。

2011 年 1/5 分钟数据表明，CSI300 股指期货主导价格发现，但 SGX A50 仍贡献约 26%-37% 的信息份额。

工程含义：如果目标是“明天中国怎么开”，A50 夜盘/开盘前收益在经济机制上比再加一个欧洲宽基指数更直接。它应当与 CNH 一起成为下一批外部数据请求的最高优先级。

### 7. 中国商品夜盘：全球冲击的本地吸收器

中国商品期货夜盘文献表明，境外交易时段信息会进入中国商品夜盘/隔夜收益，夜盘机制本身提升了信息吸收。对于 CSI1000，它未必是直接 beta，但能代表风险偏好、工业周期与人民币资产夜间定价。

工程含义：未来优先研究一个小型经济组合，而不是几十个品种：
- 铜/原油/铁矿等全球-中国工业风险代理；
- 只保留明确在 09:31 前完成的夜盘信息。

### 8. 开盘集合竞价：最靠近 target，但当前缺数据

开盘集合竞价承担隔夜信息聚合和价格发现。相关研究显示，开盘竞价中的订单分歧、订单积极度和隔夜公共信息会影响开盘效率与隔夜收益。

工程含义：若未来取得 09:15-09:25/09:30 逐笔/快照，优先考虑：
- indicative-price vs previous close；
- buy/sell imbalance；
- cancel/submit imbalance；
- dispersion/disagreement。

严格禁止把 09:31 open 本身或任何其后字段作为 predictor。

## 本轮立即验证的四个机制候选

候选已在 `docs/governance/global_spillover_v1_preregistration.json` 预注册，结果前冻结：

- C0：现有 frozen 13-factor Ridge；
- C1：**US closure accrual**：累计尚未被 A 股吸收的多日 NASDAQ/VIX 变化；
- C2：**US asymmetry**：NASDAQ 正/负冲击和负冲击×VIX 上行；
- C3：**state dependence**：NASDAQ × 中国自身 rvol20、NASDAQ × 昨日 A 股下跌；
- C4：上述三个低 DOF 机制的有界组合。

所有候选固定 `StandardScaler + Ridge(alpha=1.0)`，禁止参数搜索，禁止用收益/PnL/Sharpe 选模型。

## 最重要的可证伪问题

1. 中国长假后，`last US session` 是否遗漏了休市期间多个 US session 的累计信息？
2. 美股下跌是否比上涨对 CSI1000 次日缺口传递更强？
3. 美股冲击是否在中国自身高波动/弱势状态下放大？
4. 任一改进是否同时超过 frozen Ridge 和 `us_nasdaq` 单变量，而非仅在 2020 疫情样本贡献？

只有第 4 条成立，才有资格称为这一轮的 retrospective research progress；仍不是 fresh OOS，也没有生产权。

## 主要公开来源

- JIFMIM 2014, *The interactions between China and US stock markets: New perspectives*, DOI `10.1016/j.intfin.2014.04.008`
- De Gooijer, Diks & Gatarek, *Information Flows Around the Globe: Predicting Opening Gaps from Overnight Foreign Stock Price Patterns*, SSRN `1510069`
- Borsa Istanbul Review 2026, *When “overnight” is not simultaneous: Turning cross index overnight returns into feasible forecasts of morning gaps*, DOI `10.1016/j.bir.2026.100871`
- Nishimura et al. 2016, *The Chinese Stock Market Does not React to the Japanese Market*, DOI `10.1111/jere.12086`
- Chen et al. 2023, *Return spillover across China's financial markets*, DOI `10.1016/j.pacfin.2023.102057`
- Han et al., *A Tale of Two Index Futures*, SSRN `2025274`

