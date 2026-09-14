#!/usr/bin/env python3
"""Metadata-only repository QA. No market loads, model fitting or research execution."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUTH = 'docs/governance/current_authority_v1.json'
REGISTRY = 'docs/governance/overnight_factor_product_registry_v1.json'
LEDGER = 'docs/governance/overnight_reusable_blackbox_query_ledger_v1.json'
LIFECYCLE = 'docs/governance/repository_lifecycle_v1.json'
COMPONENTS = 'docs/governance/component_bindings_v1.json'
TRANSITIONS = 'docs/maintenance/20260912_reconciliation.json'


def load(root: Path, path: str) -> Any:
    return json.loads((root / path).read_text(encoding='utf-8'))


def canonical_hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def receipt_identity(receipt: dict) -> str | None:
    """Only the exact original V6A schema uses candidate as its identity field."""
    if receipt.get('schema_id') == 'overnight_v6a_reusable_blackbox_receipt@1.0':
        return receipt.get('candidate')
    return receipt.get('research_identity')


def ledger_errors(ledger: dict, authority: dict, registry: dict) -> list[str]:
    errors: list[str] = []
    queries = ledger.get('queries', [])
    count = len(queries)
    if ledger.get('query_count') != count:
        errors.append('ledger query_count does not equal its actual entries')
    if [q.get('ordinal') for q in queries] != list(range(1, count + 1)):
        errors.append('ledger ordinals are not contiguous and unique')
    ids = [q.get('query_id') for q in queries]
    if len(set(ids)) != count or any(not v for v in ids):
        errors.append('ledger query identities are missing or duplicated')
    for label, obj in [('authority', authority), ('registry', registry)]:
        if obj.get('blackbox_ledger_query_count') != count:
            errors.append(f'{label} ledger count differs from ledger')
        if obj.get('production_authority') is not False:
            errors.append(f'{label} improperly grants production authority')
    for q in queries:
        if q.get('production_authority') is not False or q.get('public_detail_release') is not False:
            errors.append(f'query {q.get("ordinal")} violates publication/production boundary')
    return errors


def resolve_reference(root: Path, path: str, transitions: dict | None = None) -> Path | None:
    """Resolve an original repository path, including a documented archival move."""
    p = root / path
    if p.exists():
        return p
    if transitions is None:
        transitions = load(root, TRANSITIONS)
    row = next((r for r in transitions['files'] if r['original_path'] == path), None)
    if row and row.get('current_path') and (root / row['current_path']).exists():
        return root / row['current_path']
    return None


def render_views(root: Path) -> dict[str, str]:
    a = load(root, AUTH)
    r = load(root, REGISTRY)
    ledger = load(root, LEDGER)
    catalog = load(root, COMPONENTS)
    products = {p['product_id']: p for p in r['products']}
    count = ledger['query_count']
    active = a.get('active_research')
    active_text = json.dumps(active, ensure_ascii=False, sort_keys=True) if active else 'null（没有获准执行的 outcome-bearing identity）'
    planned = a.get('planned_research') or {}
    rows = []
    for c in catalog['validated_components']:
        rows.append(f"| {c['component_id']} | `{c['research_identity']}` | PASS / #{c['ledger_ordinal']} | {c['evidence_scope']} |")
    recent = []
    for name, item in a.get('recent_downstream_research', {}).items():
        recent.append(f"| {name} | `{item['identity']}` | `{item['status']}` |")
    status = '\n'.join([
        '# 当前状态（自动生成，不手工编辑）', '',
        f"Authority：`{a['schema_id']}`；Registry：`{r['schema_id']}`。", '',
        f'BLACKBOX 逻辑查询数：**{count}**。', '', f'`active_research`：{active_text}。', '',
        '**交付边界：已验证因子的冻结参考实现与可复现证据，不是生产信号服务，也不是已通过验证的交易适配器。**', '',
        '`production_authority = false`。维护测试通过不增加科学、账户执行或生产权限。', '',
        '## 已验证组件', '', '| 组件 | 冻结身份 | 科学结论 | 有效范围 |', '|---|---|---|---|', *rows, '',
        '## 下游研究状态', '', '| 身份 | 研究对象 | 当前结论 |', '|---|---|---|', *recent, '',
        '## 独立日期门', '',
        'Gap-Fill V2 只达到冻结 / repeat-confirmed。true-fresh 窗口为 **2026-08-24 至 2026-12-31**，且不得早于 **2027-01-01（中国日期）**开启；日期达到本身不替代完整数据与原协议检查。', '',
        '## 权威来源', '', f'- `{AUTH}`', f'- `{REGISTRY}`', f'- `{LEDGER}`', f'- `{COMPONENTS}`',
        '- `docs/governance/gap_fill_v2_true_fresh_state_v1.json`', '',
        '本文件由 `python scripts/check_repository_consistency.py --write-views` 生成。', ''
    ])
    readme = '\n'.join([
        '# FactorLab Overnight Open Lab', '',
        'Overnight/Open 因子研究与冻结参考实现仓库。研究开盘信息、短周期条件信息与严格限定的下游适配；不把市场层面的信号当作个股排名 alpha。', '',
        f"当前权威：`{a['schema_id']}`；BLACKBOX 查询数：**{count}**；`production_authority=false`。", '',
        '**当前不是 production-ready 信号 API 或自动交易工具。** 科学上验证通过的组件、未通过/证据不足的下游试验、软件维护测试是三个不同层次。', '',
        '## 从这里开始', '',
        '- [接续入口](CONTINUE_HERE.md)',
        '- [自动生成的当前状态](docs/CURRENT_STATUS.md)',
        '- [项目白皮书](docs/WHITEPAPER.md)',
        '- [代码与组件映射](scripts/README.md)',
        '- [测试范围](tests/README.md)',
        '- [本轮整理报告](docs/maintenance/20260912_RECONCILIATION.md)', '',
        '## 安全维护命令', '',
        '```bash', 'python -m pip install -r requirements-ci.txt',
        'python scripts/check_repository_consistency.py', 'python -m pytest', '```', '',
        '这些命令只检查元数据、冻结源码与合成输入。默认测试有行情/账户数据和网络访问屏障；不会重算 DEV、BLACKBOX 或账户回测。', '',
        '## 代码与证据如何保存', '',
        '`scripts/` 保留组件所需的冻结实现和依赖闭包；其中历史研究 main() 不是当前授权入口。过期研究流程、阶段测试和 handoff 已登记退役/归档。', '',
        '冻结协议、参数、科学 receipt、已封存证据与数据载体不为适配今天的文档而改写。历史路径通过 `docs/governance/repository_lifecycle_v1.json` 和 `docs/maintenance/20260912_reconciliation.json` 追踪。', '',
        '新研究必须独立预注册；不得从失败或证据不足的试验自动调阈值、改时点、改符号或复活旧实验。', '',
        '本入口由一致性检查器生成；不要手工复制另一套状态。', ''
    ])
    cont = '\n'.join([
        '# CONTINUE HERE', '',
        f"当前权威：`{a['schema_id']}`。BLACKBOX 查询数：{count}。", '',
        f'当前 outcome-bearing 研究：{active_text}。', '',
        '先读 `docs/governance/current_authority_v1.json`、`docs/CURRENT_STATUS.md`、`docs/governance/component_bindings_v1.json`，再读身份对应的冻结证据。', '',
        '当前允许：维护、元数据一致性、合成回归测试与冻结字节核验。',
        '当前不自动允许：旧 DEV/BLACKBOX 重跑、账户回测、新 successor 或生产执行。', '',
        '执行维护：`python scripts/check_repository_consistency.py` 与 `python -m pytest`。', '',
        '历史 state 的 next_action 是当时快照，不可覆盖 canonical authority。查旧路径使用整理清单，完整历史复现使用清单中的 baseline commit。', '',
        'Gap-Fill true-fresh 不得早于中国日期 2027-01-01，且必须符合完整冻结窗口协议。', ''
    ])
    matrix = []
    for c in catalog['validated_components']:
        matrix.extend([f"### {c['component_id']}", '', f"冻结身份：`{c['research_identity']}`。", '', f"范围：{c['evidence_scope']}。", '', f"数学定义：`{c['definition']}`。", '', f"实现：`{c['implementation']}`。", f"证据：`{c['receipt']}`；协议：`{c['protocol']}`。", f"状态：`{c['state']}`。", ''])
    planned_section = []
    if planned:
        preopen = '、'.join(planned.get('first_generation_preopen_coordinates', []))
        postopen = '、'.join(planned.get('first_generation_postopen_coordinates', []))
        phase_order = ' → '.join(planned.get('phase_order', []))
        planned_section = [
            '## 7. vNext：极端开盘条件状态转移', '',
            f"计划身份：`{planned.get('program_id')}`；状态：`{planned.get('status')}`。当前 `active_research`：{active_text}；结果型执行权限为 `{planned.get('active_execution_authority')}`。", '',
            '这一代不再把 Overnight 当作一个覆盖每天的宽泛方向桶，而把产品改造成稀疏的可调用条件组件：只有某个冻结状态对条件分布产生足够大、足够稳定的分离时才输出状态；其他日期统一 `ABSTAIN`。这不是对已关闭 A3/C3/D1/E1/E2/E3 身份的救援，也不得利用已完成 BLACKBOX 的隐藏行为反推阈值。', '',
            f"首代物质事件门槛固定为 **±{planned.get('primary_event_threshold_bp')} bp**：09:31 gap >= +30bp 为 `EXTREME_UP`，<= -30bp 为 `EXTREME_DOWN`。开盘后固定同时观察 **09:35→09:50** 与 **09:35→10:35**，两者均报告、不得事后选赢家。高开后正收益为 continuation、负收益为 fade；低开后负收益为 continuation、正收益为 rebound。", '',
            '研究严格拆成两个因果时钟：pre-open 只回答“大幅高开/低开在什么条件下更可能发生”，不得使用目标日当前 gap；post-open 只有在 09:31 gap 已观察后，才回答“大幅高开/低开之后更可能延续还是反转”，且不得使用未来路径。', '',
            f"首代 pre-open 坐标只允许：{preopen}。首代 post-open 坐标只允许：{postopen}。连续 shelf product 本身不等于桶授权；本计划只是冻结新身份的候选输入边界。", '',
            f"开发细节窗口固定为 `{planned.get('development_detail_window')}`；特征分桶边界仅用 `{planned.get('feature_boundary_fit_window')}` 的特征分布冻结，并明确不查看本计划 target outcome；条件结果与所有 promotion 决策只在 `{planned.get('conditional_outcome_evaluation_window')}` 评估。2021-2025 reusable BLACKBOX 逐行细节仍不得打开。", '',
            'Phase 1 只做单变量状态；Phase 2 只允许在 Phase-1 survivor 中预注册少量两两交叉，禁止笛卡尔积工厂。可调用桶必须在 2018-2020 评估面至少有 30 个观测、且每个自然年至少 5 个观测；效果量要求 **12.5pct 绝对概率 lift 或 1.5x risk ratio（可定义时）至少满足一个**，同时 95% 概率差区间排除 0、2018/2019/2020 三年全部同方向、每个候选族 BH q<=0.10，并且开盘后概率解释与平均收益差方向一致。只在 pooled 上显著不能升级。', '',
            f"冻结顺序：{phase_order}。在 P0 元数据、时钟、来源 lineage、result-free bucket builder 与 synthetic/parity gate 落地前，不允许 P1/P2 读取 outcome；DEV 通过后也必须另冻身份才能进入 reusable validation。", '',
            '未来调用对象应返回 phase/as_of/event_class/transition_class/bucket_id/expected_probability/probability_lift/mean_return/coverage/sample_n/confidence/version/risk_flags，而不是把整组连续因子暴露给消费者。该接口不包含仓位、账户执行、品种映射或生产权限。', ''
        ]
    whitepaper = '\n'.join([
        '# Overnight/Open 项目白皮书', '',
        '## 1. 定位与本次封版边界', '',
        '本项目产出可引用的开盘因子定义、冻结参考实现及研究证据。三层问题分别是：开盘状态、开盘后短周期条件信息、冻结下游消费者的适配效用。它们不能互相替代。', '',
        '这里的“validated”仅指指定数学身份、目标、比较基准和样本协议下的科学结论；不是收益保证、个股 alpha、稳定服务 API 或生产上线许可。当前软件以研究脚本和冻结参数为主，并未宣称具备生产数据刷新、服务 SLA、实时监控或交易执行适配。', '',
        f"状态基于 `{a['schema_id']}`，唯一动态状态页是 `docs/CURRENT_STATUS.md`；查询总数为 {count}。", '',
        '## 2. 已验证组件及精确追溯', '', *matrix,
        'B4 的冻结公式包含 FX 项，并不意味着独立 B3 产品验证通过；也不能因为 B3 单项未通过而删掉 B4 的 FX 项。C1/C2 的连续交互项验证不授予“正负号即交易开关”的权限。', '',
        '## 3. 下游适配器与 Gap-Fill', '',
        'E1/E2/E3 当前没有 validated downstream product。具体已结束身份逐一列在当前状态页。DEV_NO_PROGRESS、DEV_INSUFFICIENT 与 BLACKBOX FAIL 分别保留原结论；证据不足不等于上游因子失败，更不允许用不完整效用结果重设计该身份。', '',
        'Gap-Fill V2 已冻结并通过重复检验；其 true-fresh 窗口是 2026-08-24..2026-12-31，最早中国日期 2027-01-01。现在不读取该窗口结果，也不以已有 repeat 代替 fresh。', '',
        '## 4. 数据与因果时钟', '',
        '因子必须服从各自协议的源截止时刻、同合约口径、滞后归一化和目标时钟。市场指数不是可直接执行的账户；qfq 的信号语义不赋予 qfq 成交权限。', '',
        '本库 2021-2025 reusable BLACKBOX 的细节保持封存；重复使用不产生新的独立 OOS。历史研究可能拥有不同的已消费窗口，不能用一个全局标签覆盖所有历史协议。代码维护只核对载体的 Git 对象与元数据，不重新消费市场行。', '',
        '## 5. 文档、代码、测试、工作流一致性', '',
        '当前 authority、registry、component bindings、ledger、生命周期清单共同定义维护面。README、接续入口、本白皮书和当前状态页由同一检查器生成；手工改动导致生成内容漂移会使 CI 失败。', '',
        '默认 CI 仅执行一致性检查和无行情的回归测试。冻结源码的字节完整性、被归档代码的原始 blob、ledger 前缀不可变性、组件与 receipt/protocol 的绑定、日期门和权限边界均接受自动核验。', '',
        '这些是工程检查，不是新一轮因子检验。新增的合成测试覆盖归一化滞后、方向/公式一致性、缺失/零分母、时钟与不完整输入；原有保留测试继续保护冻结 Gap-Fill 和架构证据。', '',
        '## 6. 历史保存与后续变更', '',
        '过期 one-shot workflow 从当前执行面删除；其他旧流程、已关闭实验的独立 runner 和阶段测试按清单归档。仍被当前组件依赖的历史实现保留原路径与字节，但不因此重新取得执行权。', '',
        '档案内的相对路径按冻结时仓库根解释。需要完整历史环境时，应在独立目录检出清单 baseline commit，不能直接将档案里的脚本当作今天的运行入口。', '',
        '新组件或新研究须先完成独立预注册与输入/目标/消费者边界冻结，再同步 registry、component bindings、状态页、测试和 workflow。生产权限持续为 false。', '',
        *planned_section
    ])
    return {'README.md': readme, 'CONTINUE_HERE.md': cont, 'docs/CURRENT_STATUS.md': status, 'docs/WHITEPAPER.md': whitepaper}


def check(root: Path = ROOT) -> dict:
    errors: list[str] = []
    a, registry, ledger = (load(root, p) for p in [AUTH, REGISTRY, LEDGER])
    life, catalog, transitions = (load(root, p) for p in [LIFECYCLE, COMPONENTS, TRANSITIONS])
    errors.extend(ledger_errors(ledger, a, registry))
    index = {}
    for line in subprocess.check_output(['git', 'ls-files', '-s'], cwd=root, text=True).splitlines():
        meta, path = line.split('\t', 1)
        mode, sha, stage = meta.split()
        if stage != '0':
            errors.append(f'unmerged file: {path}')
        index[path] = sha
    declared = {e['path']: e for e in life['files']}
    if set(declared) != set(index):
        errors.append('lifecycle inventory drift: ' + json.dumps({'unclassified': sorted(set(index)-set(declared)), 'missing': sorted(set(declared)-set(index))}))
    for path, row in declared.items():
        if row.get('frozen_blob') and index.get(path) != row['frozen_blob']:
            errors.append(f'frozen bytes changed: {path}')
    prefix = life['ledger_baseline']
    if len(ledger['queries']) < prefix['count'] or canonical_hash(ledger['queries'][:prefix['count']]) != prefix['queries_sha256']:
        errors.append('append-only BLACKBOX history changed')
    by_id = {q['query_id']: q for q in ledger['queries']}
    if (a.get('active_research') or {}).get('identity') != registry.get('active_research_identity'):
        errors.append('authority/registry active identity mismatch')
    planned = a.get('planned_research') or {}
    if planned:
        expected_phases = [
            'P0_infrastructure_parity',
            'P1_preopen_univariate_extreme_event_states',
            'P2_postopen_univariate_extreme_transition_states',
            'P3_sparse_survivor_intersections',
            'P4_rule_list_and_abstain_packaging',
            'P5_separately_frozen_reusable_validation',
            'P6_independent_consumer_integration',
        ]
        if planned.get('program_id') != 'overnight_extreme_open_conditional_transition_program_v1':
            errors.append('unexpected planned research identity')
        if planned.get('primary_event_threshold_bp') != 30:
            errors.append('extreme-open material event threshold drift')
        if planned.get('frozen_transition_horizons') != ['09:35_to_09:50', '09:35_to_10:35']:
            errors.append('extreme-open frozen transition horizon drift')
        if planned.get('development_detail_window') != '2015-01-05_to_2020-12-31':
            errors.append('extreme-open DEV detail window drift')
        if planned.get('feature_boundary_fit_window') != '2015-01-05_to_2017-12-31' or planned.get('conditional_outcome_evaluation_window') != '2018-01-01_to_2020-12-31':
            errors.append('extreme-open result-free bucket split drift')
        if planned.get('feature_boundary_fit_outcomes_inspected') is not False:
            errors.append('extreme-open feature-boundary stage may not inspect target outcomes')
        if planned.get('reusable_blackbox_2021_2025_open_authorized') is not False:
            errors.append('extreme-open plan improperly opens reusable BLACKBOX detail')
        plan_status = planned.get('status')
        if plan_status == 'route_frozen_docs_first_p0_infrastructure_required_before_outcome_execution':
            if planned.get('active_execution_authority') is not False or a.get('active_research') is not None:
                errors.append('extreme-open docs-first plan improperly grants outcome execution')
        elif plan_status == 'P0_COMPLETE_P1_P2_DEV_ADJUDICATION_AUTHORIZED':
            active = a.get('active_research') or {}
            if planned.get('active_execution_authority') is not True or active.get('identity') != 'overnight_extreme_open_univariate_dev_v1':
                errors.append('extreme-open P1/P2 authority identity drift')
            if active.get('protocol') != 'docs/governance/extreme_open_univariate_dev_v1_protocol.json' or active.get('state') != 'docs/governance/extreme_open_univariate_dev_v1_state.json':
                errors.append('extreme-open P1/P2 protocol/state binding drift')
            if active.get('carrier_sha256') != 'd38483d9ef37e65506f858f6155482de32766a619c44ce799442d303c74cc321':
                errors.append('extreme-open P0 carrier binding drift')
            if active.get('P3_authorized') is not False or active.get('reusable_blackbox_2021_2025_open_authorized') is not False or active.get('production_authority') is not False:
                errors.append('extreme-open P1/P2 authority exceeds frozen DEV boundary')
        elif plan_status == 'P1_COMPLETE_6_SURVIVORS_P2_COMPLETE_NO_SURVIVOR_P3_FREEZE_REQUIRED':
            if planned.get('active_execution_authority') is not False or a.get('active_research') is not None:
                errors.append('extreme-open closed P1/P2 identity improperly remains active')
            if planned.get('P1_survivor_count') != 6 or planned.get('P2_survivor_count') != 0:
                errors.append('extreme-open P1/P2 closeout count drift')
            if planned.get('P2_postopen_intersection_authorized') is not False or planned.get('P3_preopen_successor_freeze_permitted') is not True:
                errors.append('extreme-open P3 closeout boundary drift')
            if planned.get('P3_candidate_construction_rule') != 'all two-way intersections among same-target P1 survivors only; exactly 3 EXTREME_UP plus 3 EXTREME_DOWN candidates':
                errors.append('extreme-open P3 candidate-construction drift')
        elif plan_status == 'P3_PREOPEN_INTERSECTIONS_AUTHORIZED_NOT_YET_EXECUTED':
            active=a.get('active_research') or {}
            if planned.get('active_execution_authority') is not True or active.get('identity') != 'overnight_extreme_open_preopen_survivor_intersections_dev_v1':
                errors.append('extreme-open P3 authority identity drift')
            if active.get('protocol') != 'docs/governance/extreme_open_preopen_intersections_dev_v1_protocol.json' or active.get('state') != 'docs/governance/extreme_open_preopen_intersections_dev_v1_state.json':
                errors.append('extreme-open P3 protocol/state binding drift')
            if active.get('candidate_count') != 6 or planned.get('P3_candidate_count') != 6:
                errors.append('extreme-open P3 candidate-count drift')
            if active.get('P2_postopen_intersections_authorized') is not False or active.get('P4_authorized') is not False or active.get('reusable_blackbox_2021_2025_open_authorized') is not False or active.get('production_authority') is not False:
                errors.append('extreme-open P3 authority exceeds frozen boundary')
        elif plan_status == 'P3_COMPLETE_6_OF_6_INCREMENTAL_PREOPEN_STATES_P4_FREEZE_REQUIRED':
            if planned.get('active_execution_authority') is not False or a.get('active_research') is not None:
                errors.append('extreme-open closed P3 identity improperly remains active')
            if planned.get('P3_complete') is not True or planned.get('P3_survivor_count') != 6:
                errors.append('extreme-open P3 closeout count drift')
            if planned.get('P3_carrier_sha256') != '0c97062e9b4d96570098ba97d1465de384387f6d6dab7a052e89483ad4a30c77':
                errors.append('extreme-open P3 carrier closeout drift')
            if planned.get('P3_set_valued_overlap_semantics_required') is not True or planned.get('P3_three_way_probability_authority') is not False:
                errors.append('extreme-open P3 overlap interpretation drift')
            if planned.get('P4_packaging_freeze_permitted') is not True or planned.get('P4_authorized') is not False:
                errors.append('extreme-open P4 pre-freeze boundary drift')
        elif plan_status == 'P4_CALLABLE_STATE_PACKAGING_FROZEN_P5_FREEZE_REQUIRED':
            if planned.get('active_execution_authority') is not False or a.get('active_research') is not None:
                errors.append('extreme-open P4 packaging improperly grants outcome execution')
            if planned.get('P4_complete') is not True or planned.get('P4_callable_state_count') != 6 or planned.get('P4_set_valued_interface') is not True:
                errors.append('extreme-open P4 packaging identity drift')
            if planned.get('P4_target_conflict_action') != 'ABSTAIN_TARGET_CONFLICT' or planned.get('P4_no_state_action') != 'ABSTAIN_NO_P3_STATE' or planned.get('P4_postopen_transition_action') != 'ABSTAIN_NO_VALIDATED_P2_STATE':
                errors.append('extreme-open P4 abstention/conflict semantics drift')
            if planned.get('P4_combined_probability_authority') is not False or planned.get('P4_three_way_state_authority') is not False:
                errors.append('extreme-open P4 improperly synthesizes overlap evidence')
            if planned.get('P5_reusable_validation_freeze_permitted') is not True or planned.get('P5_reusable_validation_open_authorized') is not False:
                errors.append('extreme-open P5 pre-freeze boundary drift')
        elif plan_status == 'P5_REUSABLE_VALIDATION_FROZEN_QUERY_NOT_YET_AUTHORIZED':
            if planned.get('active_execution_authority') is not False or a.get('active_research') is not None:
                errors.append('extreme-open frozen P5 improperly grants query execution')
            if planned.get('P5_identity') != 'overnight_extreme_open_callable_state_reusable_validation_v1' or planned.get('P5_exact_state_count') != 6:
                errors.append('extreme-open P5 identity/state-count drift')
            if planned.get('P5_public_output') != 'PASS_FAIL_INSUFFICIENT_only' or planned.get('P5_blackbox_window') != '2021-01-01_to_2025-12-31':
                errors.append('extreme-open P5 output/window drift')
            if planned.get('P5_reusable_validation_open_authorized') is not False or planned.get('reusable_blackbox_2021_2025_open_authorized') is not False:
                errors.append('extreme-open P5 freeze improperly opens reusable BLACKBOX')
            if planned.get('P4_combined_probability_authority') is not False or planned.get('P4_three_way_state_authority') is not False:
                errors.append('extreme-open P5 freeze mutates P4 overlap boundary')
        else:
            errors.append('unexpected extreme-open planned research status')
        if planned.get('phase_order') != expected_phases:
            errors.append('extreme-open phase order drift')
        policy = planned.get('bucket_policy', {})
        if any(policy.get(k) is not False for k in ['outcome_optimized_threshold_search', 'material_gap_threshold_search', 'clock_search', 'cartesian_feature_factory']):
            errors.append('extreme-open result-free bucket policy drift')
        if policy.get('default_action_outside_certified_bucket') != 'ABSTAIN':
            errors.append('extreme-open default abstention drift')
        gates = planned.get('progression_gates', {})
        if gates.get('minimum_bucket_evaluation_observations') != 30 or gates.get('minimum_evaluation_observations_each_year') != 5 or gates.get('evaluation_years') != [2018, 2019, 2020]:
            errors.append('extreme-open sample/time progression gate drift')
        if gates.get('effect_size_gate_operator') != 'OR' or gates.get('minimum_absolute_probability_lift_pp') != 12.5 or gates.get('minimum_risk_ratio_when_defined') != 1.5:
            errors.append('extreme-open effect-size progression gate drift')
        if gates.get('probability_difference_interval') != '95pct_excludes_zero' or gates.get('all_evaluation_years_same_direction') is not True or gates.get('family_fdr') != 'BH_q<=0.10':
            errors.append('extreme-open statistical progression gate drift')
        if gates.get('postopen_return_direction_must_agree') is not True or gates.get('pooled_significance_alone_is_insufficient') is not True:
            errors.append('extreme-open interpretation/stability gate drift')
    registry_products = {p['product_id']: p for p in registry['products']}
    for component in catalog['validated_components']:
        cid = component['component_id']
        if cid != 'V6A':
            product = registry_products.get(cid, {})
            if product.get('research_identity') != component['research_identity'] or product.get('blackbox_query_id') != component['query_id'] or not product.get('status', '').startswith('validated_BLACKBOX_PASS'):
                errors.append('registry/component identity or status mismatch: ' + cid)
        for test_path in component['tests']:
            if test_path not in declared or not (root/test_path).is_file():
                errors.append('missing component regression binding: ' + test_path)
    for q in ledger['queries']:
        try:
            receipt = load(root, q['receipt'])
            for key in ['query_id', 'decision', 'research_identity', 'protocol_sha256']:
                actual = receipt_identity(receipt) if key == 'research_identity' else receipt.get(key)
                if actual != q.get(key):
                    errors.append(f'ledger/receipt mismatch #{q["ordinal"]}: {key}')
        except (OSError, ValueError, KeyError) as exc:
            errors.append(f'invalid receipt #{q.get("ordinal")}: {exc}')
    for c in catalog['validated_components']:
        q = by_id.get(c['query_id'], {})
        if q.get('decision') != 'PASS' or q.get('research_identity') != c['research_identity'] or q.get('ordinal') != c['ledger_ordinal']:
            errors.append('component evidence mismatch: ' + c['component_id'])
        for key in ['state', 'protocol', 'receipt', 'implementation']:
            if not (root / c[key]).is_file():
                errors.append(f'missing current component {key}: {c[key]}')
        if (root / c['protocol']).is_file() and hashlib.sha256((root/c['protocol']).read_bytes()).hexdigest() != q.get('protocol_sha256'):
            errors.append('frozen protocol hash mismatch: ' + c['component_id'])
        state = load(root, c['state'])
        if state.get('production_authority') is not False:
            errors.append('component state grants production authority: ' + c['component_id'])
    fresh = load(root, 'docs/governance/gap_fill_v2_true_fresh_state_v1.json')['first_true_fresh_challenge']
    if fresh['not_before_china_date'] != '2027-01-01' or fresh['window'] != '2026-08-24_to_2026-12-31' or fresh['fresh_window_opened'] is not False:
        errors.append('Gap-Fill frozen fresh gate changed')
    for c in catalog['closed_downstream']:
        state = load(root, c['state'])
        if state.get('research_identity') != c['research_identity']:
            errors.append('downstream state identity mismatch: '+c['name'])
        decision = state.get('development_decision', state.get('blackbox_result', state.get('blackbox_decision')))
        if c.get('decision') and decision and decision != c['decision']:
            errors.append('downstream decision mismatch: '+c['name'])
        if state.get('production_authority') is not False:
            errors.append('downstream production authority drift: '+c['name'])
    for path, expected in render_views(root).items():
        if not (root/path).exists() or (root/path).read_text(encoding='utf-8') != expected:
            errors.append('generated document drift: ' + path)
    workflows = sorted(p for p in index if p.startswith('.github/workflows/'))
    if workflows != ['.github/workflows/repository-consistency.yml']:
        errors.append('unreviewed executable workflow surface: '+str(workflows))
    if workflows == ['.github/workflows/repository-consistency.yml']:
        import yaml
        wf = yaml.safe_load((root/workflows[0]).read_text())
        events = wf.get('on', wf.get(True, {}))
        if set(events) != {'push', 'pull_request', 'workflow_dispatch'}:
            errors.append('workflow event drift / outcome schedule detected')
        if wf.get('permissions') != {'contents':'read'}:
            errors.append('QA workflow must be read-only')
        for job in wf.get('jobs', {}).values():
            for step in job.get('steps', []):
                if 'uses' in step and not re.fullmatch(r'[^@]+@[0-9a-f]{40}', step['uses']):
                    errors.append('unpinned workflow action')
                command = step.get('run','')
                if re.search(r'run_.*blackbox|evaluate_.*(?:fresh|holdout)|git\s+push', command):
                    errors.append('QA workflow contains research/write execution')
    modules = {Path(p).stem for p in index if p.startswith('scripts/') and p.endswith('.py')}
    original_modules = {Path(e['original_path']).stem for e in transitions['files'] if e['original_path'].startswith('scripts/') and e['original_path'].endswith('.py')}
    syntax_count = 0
    for p in sorted(index):
        if p.endswith('.py'):
            try:
                tree = ast.parse((root/p).read_text(encoding='utf-8'), filename=p)
                syntax_count += 1
                if p.startswith(('scripts/', 'tests/')):
                    imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {x.name for n in ast.walk(tree) if isinstance(n, ast.Import) for x in n.names}
                    for module in imports & original_modules:
                        if module not in modules:
                            errors.append(f'missing retained source dependency: {p} -> {module}')
            except SyntaxError as exc:
                errors.append(f'Python syntax: {p}:{exc.lineno}: {exc.msg}')
    # Check repository-path references only in maintained documents; historical references use the transition map.
    for p, row in declared.items():
        if row['lifecycle'] not in {'maintained', 'generated_current', 'current_redirect'} or not p.endswith('.md'):
            continue
        text = (root/p).read_text()
        refs = set(re.findall(r'(?:docs|scripts|tests|data|\.codex|\.github)/[A-Za-z0-9_./@+\-]+\.(?:md|json|py|sh|ya?ml|toml)', text))
        for ref in refs:
            if not (root/ref).exists():
                errors.append(f'broken current reference: {p} -> {ref}')
    return {'status':'PASS' if not errors else 'FAIL', 'tracked_files':len(index), 'classified_files':len(declared), 'python_sources_parsed':syntax_count, 'validated_component_bindings':len(catalog['validated_components']), 'ledger_query_count':ledger['query_count'], 'active_outcome_research':a.get('active_research'), 'production_authority':False, 'market_rows_opened':False, 'errors':errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-views', action='store_true', help='Regenerate current documents from authority/registry/catalog; no research execution.')
    parser.add_argument('--resolve', metavar='ORIGINAL_PATH', help='Resolve a retained or archived original path.')
    args = parser.parse_args()
    if args.resolve:
        path = resolve_reference(ROOT, args.resolve)
        print(str(path.relative_to(ROOT)) if path else 'retired to baseline history only')
        return 0 if path else 1
    if args.write_views:
        for name, text in render_views(ROOT).items():
            (ROOT/name).parent.mkdir(parents=True, exist_ok=True)
            (ROOT/name).write_text(text, encoding='utf-8')
        return 0
    report = check()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
