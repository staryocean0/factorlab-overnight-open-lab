# Overnight 研究续接点（2026-09-06）

`main` 是初始包。请先读取本文件和
`docs/research/global_spillover_v9_conclusion_20260906.md`，不要因 main
的旧 README 重新执行已完成的外盘数据收集和 V1–V6 研究。

本轮已经完成 v9 预注册留下的实现、首次执行、GitHub 独立复现与固定
预测诊断。V9 虽有整体小幅增量，但年度、季度和假期条件不通过，不是
新候选；保留有效增量材料，继续保留 V6A 的原有独立未见确认身份。

复现：

```bash
python -m pytest -q
python scripts/validate_theme_package.py
python scripts/validate_v9_closeout.py
```

只需要检查结果时运行最后一条；它不重拟合。正式执行器和工作流仍可
用于相同公式的复现，不能借复现更换参数或候选。

两条后续路径：

1. V6A：仅本地控制器按 `global_spillover_v6_unseen_local_controller_contract.json`
   打开 2021–2025。云端继续禁止读取，不新增针对该区间的参数搜索。
2. 集合竞价：在 `codex/overnight-auction-source-20260906` 读取
   `docs/governance/opening_auction_pit_effective_date_followup_receipt.json`。
   原 GitHub runner 阻塞已解除，原全量查询仍超时，但同源小范围成功查询
   已证明 2020-12-14 无快照、当月只有 12 月 31 日快照，故不能作为精确
   历史成分股口径。下一步应核验独立初始快照及中证官方调整事件，不得
   倒填月底快照，不得把审计超时说成科学否定，也不得重复等待同一失败作业。

新一轮方法选择必须先做金融需求与数学方法的预分析，再登记候选预算。
不能在 V9 失败后继续换幂次、换 alpha、方向拆分或删除贡献日挽救它。
2021+、生产注册表、实盘执行、合并 main 的权限均未开放。
