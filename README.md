# FactorLab Overnight Open Lab

Overnight/Open 因子研究与冻结参考实现仓库。研究开盘信息、短周期条件信息与严格限定的下游适配；不把市场层面的信号当作个股排名 alpha。

当前权威：`overnight_open_current_authority@1.34`；BLACKBOX 查询数：**12**；`production_authority=false`。

**当前不是 production-ready 信号 API 或自动交易工具。** 科学上验证通过的组件、未通过/证据不足的下游试验、软件维护测试是三个不同层次。

## 从这里开始

- [接续入口](CONTINUE_HERE.md)
- [自动生成的当前状态](docs/CURRENT_STATUS.md)
- [项目白皮书](docs/WHITEPAPER.md)
- [代码与组件映射](scripts/README.md)
- [测试范围](tests/README.md)
- [本轮整理报告](docs/maintenance/20260912_RECONCILIATION.md)

## 安全维护命令

```bash
python -m pip install -r requirements-ci.txt
python scripts/check_repository_consistency.py
python -m pytest
```

这些命令只检查元数据、冻结源码与合成输入。默认测试有行情/账户数据和网络访问屏障；不会重算 DEV、BLACKBOX 或账户回测。

## 代码与证据如何保存

`scripts/` 保留组件所需的冻结实现和依赖闭包；其中历史研究 main() 不是当前授权入口。过期研究流程、阶段测试和 handoff 已登记退役/归档。

冻结协议、参数、科学 receipt、已封存证据与数据载体不为适配今天的文档而改写。历史路径通过 `docs/governance/repository_lifecycle_v1.json` 和 `docs/maintenance/20260912_reconciliation.json` 追踪。

新研究必须独立预注册；不得从失败或证据不足的试验自动调阈值、改时点、改符号或复活旧实验。

本入口由一致性检查器生成；不要手工复制另一套状态。
