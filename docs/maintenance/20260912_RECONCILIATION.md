# 全仓一致性整理报告 — 2026-09-12

## 审计范围

基线 `0e28a6285745552a665d5b1cba11c9da73fbacd7`：606 个文件，73 个脚本、26 个测试文件、42 个旧工作流。每个原路径均有处理记录，不读取行情/账户结果行，不更改科学判决。

## 主要问题与修正

AGENTS 和 ops 仍停在旧 E1/C2 阶段；历史白皮书不是当前因子产品白皮书；旧 workflow 可被误触发；阶段状态测试和当前 authority 冲突；E3 最新 DEV 身份可能继承前一验证身份的 query 元数据。现已统一入口、隔离历史层、清理错误继承，并补齐源实现/协议/receipt/测试绑定。

## 处理统计

- archived: 127
- deleted_completed_one_shot: 13
- retained_immutable: 455
- retired_with_redirect: 2
- updated_current_entry: 9

保留冻结源码依赖闭包 23 个脚本；保留原测试 7 个模块，并补入当前状态/公式合成回归。所有冻结源码、原始证据、参数和数据载体通过 Git blob 核验；更新的入口原文另存。

## 测试口径

旧安全测试基线为 124 项，其中 120 通过、4 个过期阶段断言失败，另有 3 个真实数据集成模块因本次无 outcome 访问而未运行。历史分支测试整体按生命周期归档；当前测试覆盖范围明确列在 `tests/README.md`，不能把 QA 通过称为新科学 PASS。

当前最终检查以 GitHub Actions `Repository consistency and synthetic regression` 的对应提交为准。`docs/maintenance/20260912_verification.json` 保存本轮初次整理后的运行收据；后续提交还须独立通过 CI。

## 真实交付边界

V6A/B1/B2/C1/C2/B4 是限定身份下的科学 PASS 与冻结参考实现，不是生产信号 API。E1/E2/E3 没有 validated downstream product。Gap-Fill V2 true-fresh 不早于中国日期 2027-01-01，且完整窗口仍必须满足原协议。`production_authority=false`，BLACKBOX 仍为 12 次。

## 文件级追溯

- `docs/maintenance/20260912_inventory_before.json`：原始全树及 blob；
- `docs/maintenance/20260912_reconciliation.json`：逐文件处理与理由；
- `docs/governance/repository_lifecycle_v1.json`：现树逐文件身份及冻结约束；
- `docs/governance/component_bindings_v1.json`：组件与实现、证据、测试对应；
- `docs/maintenance/20260912_baseline_tests.json`：未掩盖的基线测试发现。

档案中旧路径按冻结时根目录解释，完整复现请检出基线版本；不改变历史内容来伪造当前一致。
