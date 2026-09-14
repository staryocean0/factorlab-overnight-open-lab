# CONTINUE HERE

当前权威：`overnight_open_current_authority@1.34`。BLACKBOX 查询数：12。

当前 outcome-bearing 研究：{"P6_authorized": false, "account_execution_authority": false, "blackbox_window": "2021-01-01..2025-12-31", "consumer_integration_authority": false, "frozen_bindings": {"p4_protocol_sha256": "8d211b41f39e2c0f67d892b7adbca65cd7235979cb9be8059cf90c7be2600bef", "p4_reference_implementation_sha256": "f400ec6e5e0df0f64174c0ebe427e5f532e458b4f038f75f4e20f6c69136e90d", "protocol_sha256": "c09fcc9d9c79cc987aee9ba1d6b2f1d4a8b59aef840d522a8e1d30714997b39b", "runner_sha256": "a30df8d9821471ee8afa715e8104602e336f82c33b04c03c73b9d101a935ef38"}, "identity": "overnight_extreme_open_callable_state_reusable_validation_v1", "p4_protocol": "docs/governance/extreme_open_callable_state_packaging_v1_protocol.json", "p4_reference_implementation": "scripts/extreme_open_callable_state.py", "production_authority": false, "protocol": "docs/governance/extreme_open_callable_state_reusable_validation_v1_protocol.json", "public_output": ["PASS", "FAIL", "INSUFFICIENT"], "reusable_blackbox_2021_2025_open_authorized": true, "runner": "scripts/run_extreme_open_callable_state_reusable_validation.py", "state": "docs/governance/extreme_open_callable_state_reusable_validation_v1_state.json", "status": "AUTHORIZED_NOT_YET_QUERIED"}。

先读 `docs/governance/current_authority_v1.json`、`docs/CURRENT_STATUS.md`、`docs/governance/component_bindings_v1.json`，再读身份对应的冻结证据。

当前允许：维护、元数据一致性、合成回归测试与冻结字节核验。
当前不自动允许：旧 DEV/BLACKBOX 重跑、账户回测、新 successor 或生产执行。

执行维护：`python scripts/check_repository_consistency.py` 与 `python -m pytest`。

历史 state 的 next_action 是当时快照，不可覆盖 canonical authority。查旧路径使用整理清单，完整历史复现使用清单中的 baseline commit。

Gap-Fill true-fresh 不得早于中国日期 2027-01-01，且必须符合完整冻结窗口协议。
