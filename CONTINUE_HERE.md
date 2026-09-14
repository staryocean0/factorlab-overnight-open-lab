# CONTINUE HERE

当前权威：`overnight_open_current_authority@1.34`。BLACKBOX 查询数：12。

当前 outcome-bearing 研究：null（没有获准执行的 outcome-bearing identity）。

先读 `docs/governance/current_authority_v1.json`、`docs/CURRENT_STATUS.md`、`docs/governance/component_bindings_v1.json`，再读身份对应的冻结证据。

当前允许：维护、元数据一致性、合成回归测试与冻结字节核验。
当前不自动允许：旧 DEV/BLACKBOX 重跑、账户回测、新 successor 或生产执行。

执行维护：`python scripts/check_repository_consistency.py` 与 `python -m pytest`。

历史 state 的 next_action 是当时快照，不可覆盖 canonical authority。查旧路径使用整理清单，完整历史复现使用清单中的 baseline commit。

Gap-Fill true-fresh 不得早于中国日期 2027-01-01，且必须符合完整冻结窗口协议。
