# 全仓一致性整理报告 — 2026-09-12

## 审计范围

基线 `0e28a6285745552a665d5b1cba11c9da73fbacd7`：606 个文件，73 个脚本、26 个测试文件、42 个旧工作流。每个原路径均有处理记录，不读取行情/账户结果行，不更改科学判决。

## 主要问题与修正

AGENTS 和 ops 仍停在旧 E1/C2 阶段；历史白皮书不是当前因子产品白皮书；旧 workflow 可被误触发；阶段状态测试和当前 authority 冲突。现已统一入口、隔离历史层，并补齐源实现/协议/receipt/测试绑定。E3 最新 DEV 身份不能再携带上一验证身份的通用 query 元数据。

V6A 第一个 compact receipt 使用原始 `candidate` 字段，后续 schema 使用 `research_identity`。检查器仅针对原始 V6A schema 做精确字段兼容，不修改旧回执、不允许其他格式随意回退到 candidate 字段。

## 处理统计

| 处理方式 | 原文件数 |
|---|---:|
| 归档 | 127 |
| 删除已完成的一次性工作流，保留 Git 历史锚点 | 13 |
| 原路径、原字节保留 | 455 |
| 旧白皮书退役，原文归档并保留重定向入口 | 2 |
| 更新当前入口，另存原文 | 9 |
| 合计 | 606 |

原 73 个脚本中，保留冻结源码及其依赖闭包 23 个，其他 50 个归档。原 26 个测试模块中保留 7 个当前契约模块，其他 19 个归档，并新增当前状态/公式合成回归与 I/O 屏障。

原 42 个工作流中，29 个归档、13 个已完成 one-shot 删除；当前执行目录仅保留一个只读的一致性与合成回归 workflow。

整理后共有 625 个受版本管理文件，全部完成生命周期登记。总文件数增加是因为保存了入口原文和新增审计/测试，不代表活动组件增多。冻结源码、原始证据、参数和数据载体通过 Git blob 核验；更新的入口原文另存。

## 实际测试与验收

旧安全测试基线为 124 项，其中 120 通过、4 个过期阶段断言失败，另有 3 个真实数据集成模块因本次不访问 outcome 而未运行。历史分支测试整体按生命周期归档；当前测试覆盖范围明确列在 `tests/README.md`，不能把 QA 通过称为新科学 PASS。

整理后首次完整验收通过：

- GitHub Actions run：`34691074373`；
- 被验证源码提交：`7ad7fb766cd11d85a8ce545905afdb823f1124a8`；
- Python：3.11.16；
- 当前回归测试：**79 passed**；
- 全仓一致性：**PASS**，625/625 文件分类；
- Python 源文件静态解析：100 个（含历史源码）；
- 已验证组件的绑定：6 个；
- 新科学 query：0；行情/账户结果行读取：0。

`docs/maintenance/20260912_verification.json` 保存实际运行收据，并嵌入此前第一个旧格式兼容失败的记录。没有删除失败记录或将 skipped 当成通过。

最终合并前与 main 上的检查以 GitHub Actions `Repository consistency and synthetic regression` 对应提交为准；该 workflow 在 Python 3.11 和 3.12 上分别运行同一套只读维护检查。它不允许重跑 DEV、BLACKBOX、账户结果或修改仓库。

## 真实交付边界

V6A/B1/B2/C1/C2/B4 是限定身份下的科学 PASS 与冻结参考实现，不是生产信号 API。E1/E2/E3 没有 validated downstream product。Gap-Fill V2 true-fresh 不早于中国日期 2027-01-01，且完整窗口仍必须满足原协议。`production_authority=false`，BLACKBOX 仍为 12 次。

此次没有重新消费科学窗口，没有回测收益验证、生产服务负载测试或历史全环境重放。工程维护通过只说明本报告列明的检查通过，不替代这些独立授权与验证。

## 文件级追溯

- `docs/maintenance/20260912_inventory_before.json`：原始全树及 blob；
- `docs/maintenance/20260912_reconciliation.json`：逐文件处理与理由；
- `docs/governance/repository_lifecycle_v1.json`：现树逐文件身份及冻结约束；
- `docs/governance/component_bindings_v1.json`：组件与实现、证据、测试对应；
- `docs/maintenance/20260912_baseline_tests.json`：基线测试发现。

档案中旧路径按冻结时根目录解释，完整复现请检出基线版本；不改变历史内容来伪造当前一致。
