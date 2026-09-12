#!/usr/bin/env python3
"""One-use metadata/source maintenance. Never read market/account rows or run research."""
from __future__ import annotations
import ast
import collections
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
BASE = '0e28a6285745552a665d5b1cba11c9da73fbacd7'
ARCHIVE = 'archive/repository_retirement_20260912'
sys.path.insert(0, str(ROOT/'scripts'))
import check_repository_consistency as qa


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def put(path, value):
    p = ROOT/path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def bump(obj):
    stem, v = obj['schema_id'].rsplit('@',1)
    major, minor = v.split('.')
    obj['schema_id'] = stem+'@'+major+'.'+str(int(minor)+1)


original = read('docs/maintenance/20260912_inventory_before.json')['files']
original_by = {e['path']:e for e in original}
assert len(original_by) == 606
ledger = read(qa.LEDGER)
authority = read(qa.AUTH)
registry = read(qa.REGISTRY)
assert authority['schema_id'] == 'overnight_open_current_authority@1.33'
assert ledger['query_count'] == 12 and authority['active_research'] is None
# Every source protocol is located by its recorded exact SHA256, not inferred from a filename.
protocol_hashes = {}
for path in original_by:
    if path.startswith(('docs/','archive/')) and path.endswith('.json'):
        protocol_hashes.setdefault(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), []).append(path)

specs = [
    ('V6A',1,'docs/governance/global_spillover_v6a_blackbox_state_v1.json','scripts/run_v6a_reusable_blackbox_local.py','Frozen V6A_plus_ordinary_A50_preauction_closure model identity; see its exact protocol','next-open model under the frozen V6A comparator/source contract'),
    ('OFP-B1',8,'docs/governance/global_risk_open_gap_blackbox_state_v1.json','scripts/run_global_risk_open_gap_blackbox.py','0.5 * (us_nasdaq / RMS60_prev(us_nasdaq) - us_vix_chg / RMS60_prev(us_vix_chg))','continuous global-risk coordinate for opening_gap_rvol'),
    ('OFP-B2',9,'docs/governance/china_offshore_open_gap_blackbox_state_v1.json','scripts/run_single_external_driver_blackbox.py','a50_channel_return / RMS60_prev(a50_channel_return)','continuous same-contract China-offshore coordinate for opening_gap_rvol'),
    ('OFP-C1',2,'docs/governance/trend_conditioned_open_state_15m_state_v1.json','scripts/diagnose_trend_conditioned_open_state_dev.py','(gap / rvol20) * (r20 / (sqrt(20) * rvol20))','continuous trend-gap interaction; 09:35 to 09:50 return, not a trading sign rule'),
    ('OFP-C2',7,'docs/governance/volatility_conditioned_open_state_60m_state_v1.json','scripts/diagnose_volatility_conditioned_open_state_dev.py','(gap / rvol20) * log(rvol20)','continuous volatility-gap interaction; 09:35 to 10:35 return with C1 control'),
    ('OFP-B4',3,'docs/governance/driver_coherence_open_gap_v1_state.json','scripts/diagnose_driver_agreement_disagreement_dev.py','(global_risk_z + china_offshore_z + fx_cny_z) / (abs(global_risk_z) + abs(china_offshore_z) + abs(fx_cny_z))','continuous coherence coordinate for opening_gap_rvol; zero denominator remains missing'),
]
components = []
for cid,ordinal,state,implementation,definition,scope in specs:
    q = ledger['queries'][ordinal-1]
    assert q['decision'] == 'PASS'
    assert state in original_by and implementation in original_by
    candidates = protocol_hashes.get(q['protocol_sha256'],[])
    assert candidates, 'Unresolved exact protocol digest for '+cid+': '+q['protocol_sha256']
    protocol = sorted(candidates,key=lambda p:('protocol' not in p,p))[0]
    components.append({'component_id':cid,'research_identity':q['research_identity'],'ledger_ordinal':ordinal,'query_id':q['query_id'],'scientific_status':'PASS','state':state,'protocol':protocol,'protocol_sha256':q['protocol_sha256'],'receipt':q['receipt'],'implementation':implementation,'definition':definition,'evidence_scope':scope,'software_status':'frozen_reference_implementation_not_production_service','tests':['tests/test_repository_consistency.py']+([] if cid=='V6A' else ['tests/test_frozen_coordinate_regression.py']),'production_authority':False})

closed_specs = {
    'E1v1':'downstream_timing_adapter_validation_v1_state.json',
    'E1v2':'downstream_c1_c2_timing_agreement_adapter_v1_state.json',
    'E2v1':'downstream_stock_selection_adapter_v1_state.json',
    'E2v2':'downstream_c2_stock_selection_risk_adapter_v1_state.json',
    'E2v3':'downstream_b2_stock_selection_offshore_risk_adapter_v1_state.json',
    'E3v1':'downstream_portfolio_risk_adapter_v1_state.json',
    'E3v2':'downstream_b1_forward_cycle_portfolio_risk_adapter_validation_v1_state.json',
    'E3v3':'downstream_c2_forward_cycle_portfolio_risk_adapter_v1_state.json',
}
closed = []
for name,file in closed_specs.items():
    path = 'docs/governance/'+file
    s = read(path)
    closed.append({'name':name,'research_identity':s['research_identity'],'state':path,'status':s.get('status',s.get('current_status')),'decision':s.get('development_decision',s.get('blackbox_result',s.get('blackbox_decision'))),'execution_authorized':False,'production_authority':False})

keep_tests = {
    'tests/test_gap_fill_prediction_v2_protocol.py',
    'tests/test_gap_fill_v2_2026_repeat_protocol.py',
    'tests/test_gap_fill_v2_final_fit_protocol.py',
    'tests/test_gap_fill_v2_phase2_hazard_family.py',
    'tests/test_gap_fill_v2_true_fresh_protocol.py',
    'tests/test_local_2026_direction_receipt.py',
    'tests/test_local_two_head_receipt.py',
}
keep_scripts = {c['implementation'] for c in components} | {
    'scripts/build_runtime_text_carrier.py','scripts/build_driver_runtime_text_carrier.py',
    'scripts/build_v6a_frozen_base_panel.py','scripts/run_driver_coherence_open_gap_blackbox.py',
    'scripts/run_trend_conditioned_open_state_15m_blackbox_local.py',
    'scripts/run_volatility_conditioned_open_state_60m_blackbox_local.py',
    'scripts/evaluate_gap_fill_v2_true_fresh_2026q4.py',
    'scripts/evaluate_local_gap_fill_v2_2026_repeat.py',
}
modules = {Path(p).stem:p for p in original_by if p.startswith('scripts/') and p.endswith('.py')}
# Retain the transitive import and literal Python-loader dependency closure.
changed = True
while changed:
    changed = False
    for path in sorted(keep_scripts | keep_tests):
        text = (ROOT/path).read_text()
        tree = ast.parse(text)
        names = {n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)} | {a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
        names |= set(re.findall(r"['\"](?:scripts/)?([A-Za-z0-9_]+)\.py['\"]",text))
        for name in names & modules.keys():
            if modules[name] not in keep_scripts:
                keep_scripts.add(modules[name]); changed=True

transitions = []
archive_blobs = {}
for entry in original:
    path = entry['path']
    action = 'retained_immutable'
    reason = 'Frozen research evidence, source provenance, or contract retained at its original path; not a current execution instruction.'
    dest = path
    if path.startswith('.github/workflows/'):
        if '_once.' in path:
            action = 'deleted_completed_one_shot'; reason = 'Completed one-shot execution/registration surface; exact bytes recoverable at baseline commit.'; dest=None
        else:
            action = 'archived'; reason = 'Superseded execution/static-check workflow; the current read-only QA workflow replaces its active entry point.'
    elif path.startswith('scripts/') and path not in keep_scripts:
        action = 'archived'; reason = 'Closed/dormant research runner or launcher outside the retained component dependency closure; not authorized for current execution.'
    elif path.startswith('tests/') and path not in keep_tests:
        action = 'archived'; reason = 'Historical experiment-stage or real-carrier integration test; retain original expectations with the frozen baseline, not as current-state CI.'
    elif path.startswith(('docs/ops/','docs/user/')) and path.endswith('.md') and path != 'docs/ops/README.md':
        action = 'archived'; reason = 'Historical whitepaper/handoff belongs to its original measurement or research phase, not the current operating plan.'
    if action == 'archived':
        dest = ARCHIVE+'/'+path
        (ROOT/dest).parent.mkdir(parents=True,exist_ok=True)
        shutil.move(str(ROOT/path),str(ROOT/dest))
        archive_blobs[dest] = entry['blob']
    elif action == 'deleted_completed_one_shot':
        (ROOT/path).unlink()
    transitions.append({'original_path':path,'baseline_blob':entry['blob'],'action':action,'current_path':dest,'reason':reason})

# Back up every mutable entry before replacing it. Never edit historical evidence to match current code.
def replace_current(path, content):
    if path in original_by:
        backup = ARCHIVE+'/superseded_entrypoints/'+path
        (ROOT/backup).parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/path,ROOT/backup)
        archive_blobs[backup]=original_by[path]['blob']
        row = next(t for t in transitions if t['original_path']==path)
        row.update(action='updated_current_entry',current_path=path,archived_original=backup,reason='Mutable entrypoint/config synchronized; original bytes preserved separately.')
    put(path,content)

bump(authority)
authority['maintenance_contract'] = qa.LIFECYCLE
authority['component_bindings'] = qa.COMPONENTS
authority['delivery_status'] = {'scientific_scope':'validated_factor_reference_components_only','software_scope':'frozen_reference_implementations_with_metadata_and_synthetic_QA','stable_production_signal_API_delivered':False,'validated_downstream_adapter_delivered':False,'production_authority':False}
authority['next_action'] = 'Maintain the synchronized repository via the metadata/synthetic QA gate. No outcome-bearing research is active. New independently motivated research requires separate result-free preregistration; Gap-Fill V2 remains under its original complete-window and 2027-01-01 China-date gate.'
replace_current(qa.AUTH,authority)
bump(registry)
e3 = next(p for p in registry['products'] if p['product_id']=='OFP-E3')
assert e3['latest_identity'] == 'overnight_c2_forward_cycle_portfolio_risk_abstention_v1'
stale = {k:e3.pop(k) for k in ['blackbox_query_id','blackbox_ledger_ordinal','latest_parent_development_identity'] if k in e3}
if stale:
    e3['historical_v2_validation_metadata'] = stale
registry['component_bindings'] = qa.COMPONENTS
registry['next_research_identity'] = None
registry['next_research_note'] = 'No active outcome-bearing identity. Consult canonical authority and generated CURRENT_STATUS; historical state next_action fields do not reopen completed research.'
replace_current(qa.REGISTRY,registry)
put(qa.COMPONENTS,{'schema_id':'overnight_component_bindings@1.0','baseline_commit':BASE,'validated_components':components,'closed_downstream':closed,'normalization_note':'RMS60_prev uses shift(1), rolling window 60, min_periods 20; input units and clocks remain frozen.','production_authority':False})

replace_current('AGENTS.md', '''# Overnight/Open — agent instructions

Read `CONTINUE_HERE.md`, `docs/governance/current_authority_v1.json`, `docs/CURRENT_STATUS.md`, and `docs/governance/component_bindings_v1.json` before substantial work.

This repository maintains Overnight/Open research and frozen reference implementations. Generic RMR/HighVol discovery, trading production, and downstream-PnL tuning of upstream factors are out of scope. Validated science is not a production API or executable-account authorization.

## Current execution authority

Only `docs/governance/current_authority_v1.json` may grant current research execution. Do not copy its counters/statuses here. Historical state files and their `next_action` fields are immutable as-of evidence, not today's instructions. Consult `docs/governance/repository_lifecycle_v1.json` and `docs/maintenance/20260912_reconciliation.json` for every retained, retired, moved, or deleted path.

When active research is null, run only the metadata/synthetic maintenance checks. Never execute an old handoff or workflow just because it remains in Git history or because a frozen implementation contains main(). Source preservation does not reopen a query.

## Maintenance

Run `python scripts/check_repository_consistency.py` and `python -m pytest` after installing `requirements-ci.txt`. Default tests deliberately block real market/account carriers and network access. Do not disable this barrier to make tests pass. Historical data integration belongs to an independently authorized replay, not ordinary CI.

README, CONTINUE_HERE, CURRENT_STATUS and WHITEPAPER are generated from the same authority/registry/component bindings. After legitimate metadata changes use `python scripts/check_repository_consistency.py --write-views`, then update the per-file lifecycle inventory and run all checks. Additions or deletions not classified in the lifecycle manifest fail CI.

Never rewrite sealed protocols, original parameter bundles, scientific receipts, or data provenance to make hashes agree with new code. Preserve the original blob and trace legitimate changes through the archive/history mapping. BLACKBOX query history is append-only, and repeated physical periods are not independent OOS. Incomplete Development surfaces cannot design rescue candidates.

For actual model/factor/strategy/account changes also read `.codex/skills/strategy-slice-rebuild/SKILL.md` and its project contract. Its inherited strategy procedures do not turn this maintenance request into a new experiment.

`production_authority=false`.
''')
replace_current('docs/ops/README.md', '''# Current operations

There is no active outcome-bearing handoff. Use `docs/CURRENT_STATUS.md` and canonical `docs/governance/current_authority_v1.json`.

The current maintenance commands are:

```bash
python -m pip install -r requirements-ci.txt
python scripts/check_repository_consistency.py
python -m pytest
```

All former handoff documents and workflow instructions are historical. Their original paths resolve through `docs/maintenance/20260912_reconciliation.json`; archived material is not executable authority. In particular, do not rerun completed C1/C2 or other reusable BLACKBOX identities.

The active GitHub workflow is read-only metadata/synthetic QA. Gap-Fill V2 remains under its separately frozen full-window/date protocol, not an active CI evaluation.

`production_authority=false`.
''')
replace_current('docs/governance/overnight_factor_product_program_v1.md', '''# Overnight Factor Product Program

## Stable charter

This repository researches causal China opening-state information and bounded short-horizon conditions, and maintains exact frozen factor definitions, implementation lineage and evidence. Downstream timing, stock-selection and portfolio-risk adapters require independently frozen consumers and protocols. Market-level factors are not stock-specific ranking alpha.

Current statuses are generated in `docs/CURRENT_STATUS.md` from `docs/governance/current_authority_v1.json`, `docs/governance/overnight_factor_product_registry_v1.json`, and `docs/governance/component_bindings_v1.json`. This charter intentionally contains no independently maintained active experiment list or query counter.

## Boundaries

Continuous coordinates do not authorize buckets, sign-based trading, reweighting, new horizons or account execution. New identities must have an independent result-free motivation, causal availability, explicit source and comparator, an evidence-sufficiency rule, and a frozen protocol before relevant outcomes are read.

Development progression, validation, account execution and production are separate claims. A downstream failure does not invalidate an upstream component. An insufficient surface is not selection or rescue authority. Never decompose completed reusable BLACKBOX behavior to design a successor; reused periods are not independent OOS.

## Software and evidence maintenance

The authoritative engineering explanation is `docs/WHITEPAPER.md`. Component-to-source/protocol/receipt/test links are in the component bindings. The lifecycle manifest classifies every tracked file and prevents unrecorded drift. Preserve immutable research evidence, parameter identities and provenance; archive obsolete stages rather than rewrite them.

Current production-service packaging and trading authorization are not implied by passing the repository QA suite.

`production_authority=false`.
''')
replace_current('data/README.md', '''# Data carriers — evidence boundaries

Carrier names and physical availability do not authorize outcome access. Consult the exact frozen protocol, `docs/governance/current_authority_v1.json`, and `docs/governance/repository_lifecycle_v1.json` before any scientific read.

This maintenance pass preserves every original data/carrier/manifest blob except this navigational README. It does not modify rows, regenerate factors, rebuild accounts, or consume any new scientific window. Per-file original Git objects are recorded in `docs/maintenance/20260912_inventory_before.json`.

Connector-readable Development carriers and raw reconstruction carriers have different roles; year ranges in directory names are not a single repository-wide data permission. The 2021-2025 reusable BLACKBOX remains governed by its compact-public-output policy. Historical audits keep their own original boundaries.

Gap-Fill V2 true-fresh remains unopened: the complete 2026-08-24..2026-12-31 block and not-before China date 2027-01-01 are both required. Do not open partial-window outcomes as a housekeeping step.

Default CI reads only metadata/contracts and synthetic inputs; real CSV/parquet/account loads are blocked. Original subdirectory READMEs are provenance snapshots, not current execution orders.

`production_authority=false`.
''')
replace_current('archive/README.md', '''# Historical archive

Archives preserve prior source, contracts, whitepapers, handoffs and tests as historical evidence, not current execution authority. Start at `CONTINUE_HERE.md` for today's repository.

The 2026-09-12 reconciliation is indexed by `docs/maintenance/20260912_reconciliation.json`. Every original path has a disposition and a baseline blob. Complete historical replay uses baseline commit `0e28a6285745552a665d5b1cba11c9da73fbacd7` in a separate worktree and its original environment/authorization, not direct execution of relocated scripts.

Archive file bodies and relative paths retain freeze-time meaning. Resolve original repository paths with `python scripts/check_repository_consistency.py --resolve ORIGINAL_PATH`. Completed one-shot workflows were removed from the current tree but remain recoverable at the baseline anchor.

Do not relabel old results fresh, turn old next_action text into current authority, or alter frozen evidence to match present code. `production_authority=false`.
''')
replace_current('pyproject.toml', '''[project]
name = "factorlab-overnight-open-lab"
version = "0.1.0"
description = "Frozen Overnight/Open research reference implementations; not a production signal service"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
norecursedirs = ["archive", ".git", ".maintenance"]
addopts = "-ra"
''')
put('requirements-ci.txt','numpy==1.26.4\npandas==2.2.3\nscipy==1.14.1\nscikit-learn==1.5.2\npyarrow==18.1.0\npytest==8.3.5\nPyYAML==6.0.2\n')
put('docs/governance/README.md', '''# Governance: live pointers versus frozen evidence

Live pointers are current_authority_v1.json, overnight_factor_product_registry_v1.json, component_bindings_v1.json and repository_lifecycle_v1.json. The append-only overnight_reusable_blackbox_query_ledger_v1.json is reconciled against each public compact receipt.

Other original governance files are retained freeze-time evidence unless explicitly bound as a current component or the unopened Gap-Fill date gate. A parent state that once said “waiting for validation” remains an as-of snapshot; its completed child in current authority supersedes that execution instruction. Never edit an old state hash just to update such historical text.

See `docs/CURRENT_STATUS.md` for current decisions, `docs/WHITEPAPER.md` for scope and `docs/maintenance/20260912_reconciliation.json` for historical path resolution. Closed/insufficient downstream identities remain closed; historical blocks are not independent OOS.
''')
put('scripts/README.md', '# Source implementations and execution boundary\n\nCurrent metadata CLI: `python scripts/check_repository_consistency.py`.\n\nThe following frozen reference implementations/dependencies retain their original bytes and paths. Their historical main() entry points do not constitute an active research authorization; none is run by default CI. The source list is dependency-closed, while independent retired experiments live in the indexed archive.\n\n'+'\n'.join('- `'+p+'`' for p in sorted(keep_scripts))+'\n\nComponent mappings: `docs/governance/component_bindings_v1.json`. Historical path resolver: `python scripts/check_repository_consistency.py --resolve ORIGINAL_PATH`.\n')
put('tests/README.md', '# Current QA test scope\n\nDefault tests have a collection-time data/network barrier. They verify metadata, frozen bytes, selected reference functions on synthetic inputs, and retained Gap-Fill/architecture contracts. They do not measure factor performance or run backtests.\n\nRetained original tests:\n\n'+'\n'.join('- `'+p+'`' for p in sorted(keep_tests))+'\n\nNew regression suites: `tests/test_repository_consistency.py` and `tests/test_frozen_coordinate_regression.py`; barrier: `tests/conftest.py`.\n\nOther original tests are archived by experiment scope, not deleted to hide a failing computation. The baseline run recorded 124 cases, 120 passing and 4 obsolete stage-state assertions failing; three real-carrier integration modules were intentionally excluded from that run. Numerical/synthetic assertions for archived experiments remain in the baseline archive and are not represented as current-product QA coverage.\n')
put('.github/README.md','# Current automation\n\nOnly `workflows/repository-consistency.yml` is active: read-only metadata/synthetic QA on Python 3.11 and 3.12. No scheduled research, account replay, BLACKBOX reopening, self-committing workflow or auto-promotion remains in the active Actions directory. Historical workflows are indexed in `docs/maintenance/20260912_reconciliation.json`.\n')
put('.github/workflows/repository-consistency.yml', '''name: Repository consistency and synthetic regression
on:
  push:
    branches: [main, 'maintenance/**']
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: repository-qa-${{ github.ref }}
  cancel-in-progress: true
jobs:
  consistency:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
        with:
          python-version: ${{ matrix.python }}
      - name: Install exact QA dependencies
        run: python -m pip install -r requirements-ci.txt
      - name: Cross-surface metadata and frozen-byte checks
        run: python scripts/check_repository_consistency.py
      - name: Guarded synthetic and metadata regression
        env:
          PYTEST_DISABLE_PLUGIN_AUTOLOAD: '1'
        run: python -m pytest -q
''')

# Generated current views preserve their superseded entrypoint versions as well.
views = qa.render_views(ROOT)
for path,text in views.items():
    if path in original_by:
        replace_current(path,text)
    else:
        put(path,text)

# Leave pointer stubs only at the two previous whitepaper names, not at obsolete command handoffs.
for path in [p for p in original_by if 'whitepaper' in p and p.endswith('.md')]:
    row = next(t for t in transitions if t['original_path']==path)
    if row['action']=='archived':
        archived = row['current_path']
        put(path,'# Historical whitepaper — retired current entrypoint\n\nThe current Overnight/Open whitepaper is `docs/WHITEPAPER.md`; current authority is `docs/governance/current_authority_v1.json`.\n\nThis former document describes a historical measurement/ledger phase. Its exact original text is retained at `'+archived+'` and the baseline commit. Its rules, buckets, target periods and execution instructions do not define the current component product.\n')
        row['action']='retired_with_redirect'; row['archived_original']=archived; row['current_path']=path

counts = dict(collections.Counter(t['action'] for t in transitions))
transition_document = {'schema_id':'overnight_repository_reconciliation@1.0','baseline_commit':BASE,'scope':'metadata_source_test_workflow_maintenance_only','scientific_outcomes_opened':False,'scientific_decisions_changed':False,'blackbox_query_count_before':12,'blackbox_query_count_after':12,'counts':counts,'retained_frozen_script_count':len(keep_scripts),'retained_original_test_modules':len(keep_tests),'files':transitions}
put(qa.TRANSITIONS,transition_document)
put('docs/maintenance/20260912_RECONCILIATION.md', '# 全仓一致性整理报告 — 2026-09-12\n\n## 审计范围\n\n基线 `'+BASE+'`：606 个文件，73 个脚本、26 个测试文件、42 个旧工作流。每个原路径均有处理记录，不读取行情/账户结果行，不更改科学判决。\n\n## 主要问题与修正\n\nAGENTS 和 ops 仍停在旧 E1/C2 阶段；历史白皮书不是当前因子产品白皮书；旧 workflow 可被误触发；阶段状态测试和当前 authority 冲突；E3 最新 DEV 身份可能继承前一验证身份的 query 元数据。现已统一入口、隔离历史层、清理错误继承，并补齐源实现/协议/receipt/测试绑定。\n\n## 处理统计\n\n'+ '\n'.join('- '+k+': '+str(v) for k,v in sorted(counts.items()))+'\n\n保留冻结源码依赖闭包 '+str(len(keep_scripts))+' 个脚本；保留原测试 '+str(len(keep_tests))+' 个模块，并补入当前状态/公式合成回归。所有冻结源码、原始证据、参数和数据载体通过 Git blob 核验；更新的入口原文另存。\n\n## 测试口径\n\n旧安全测试基线为 124 项，其中 120 通过、4 个过期阶段断言失败，另有 3 个真实数据集成模块因本次无 outcome 访问而未运行。历史分支测试整体按生命周期归档；当前测试覆盖范围明确列在 `tests/README.md`，不能把 QA 通过称为新科学 PASS。\n\n当前最终检查以 GitHub Actions `Repository consistency and synthetic regression` 的对应提交为准。`docs/maintenance/20260912_verification.json` 保存本轮初次整理后的运行收据；后续提交还须独立通过 CI。\n\n## 真实交付边界\n\nV6A/B1/B2/C1/C2/B4 是限定身份下的科学 PASS 与冻结参考实现，不是生产信号 API。E1/E2/E3 没有 validated downstream product。Gap-Fill V2 true-fresh 不早于中国日期 2027-01-01，且完整窗口仍必须满足原协议。`production_authority=false`，BLACKBOX 仍为 12 次。\n\n## 文件级追溯\n\n- `docs/maintenance/20260912_inventory_before.json`：原始全树及 blob；\n- `docs/maintenance/20260912_reconciliation.json`：逐文件处理与理由；\n- `docs/governance/repository_lifecycle_v1.json`：现树逐文件身份及冻结约束；\n- `docs/governance/component_bindings_v1.json`：组件与实现、证据、测试对应；\n- `docs/maintenance/20260912_baseline_tests.json`：未掩盖的基线测试发现。\n\n档案中旧路径按冻结时根目录解释，完整复现请检出基线版本；不改变历史内容来伪造当前一致。\n')
put('docs/maintenance/20260912_verification.json',{'status':'PENDING_ACTUAL_QA','baseline_commit':BASE,'maintenance_only':True,'production_authority':False})

# Remove temporary orchestration and redundant raw audit expansions from the final tree.
for p in list((ROOT/'.maintenance').glob('*.py')):
    p.unlink()
for name in ['20260912_audit_before.json','20260912_before_workflows.json','20260912_before_test_io_review.json','20260912_before_governance_states.json','20260912_before_source_imports.json','20260912_before_missing_literal_references.json']:
    (ROOT/'docs/maintenance'/name).unlink(missing_ok=True)
(ROOT/'.github/workflows/repository-maintenance-once.yml').unlink(missing_ok=True)
(ROOT/'tools/reconcile_repository_20260912.py').unlink()

# Classify every retained path. Scientific/data files keep their exact original Git object.
put(qa.LIFECYCLE, {})
subprocess.run(['git','add','-A'],check=True)
index = {}
for line in subprocess.check_output(['git','ls-files','-s'],text=True).splitlines():
    meta,path = line.split('\t',1); index[path]=meta.split()[1]
current_entries = []
mutable_paths = {t['original_path'] for t in transitions if t['action'] in {'updated_current_entry','retired_with_redirect'}}
for path in sorted(index):
    if path in archive_blobs:
        row={'path':path,'lifecycle':'archived_immutable','frozen_blob':archive_blobs[path]}
    elif path in views:
        row={'path':path,'lifecycle':'generated_current'}
    elif path in mutable_paths or path not in original_by:
        row={'path':path,'lifecycle':'current_redirect' if any(t['original_path']==path and t['action']=='retired_with_redirect' for t in transitions) else 'maintained'}
    elif path == qa.LEDGER:
        row={'path':path,'lifecycle':'append_only_ledger'}
    else:
        kind = 'frozen_implementation' if path in keep_scripts else ('current_contract_regression' if path in keep_tests else ('data_provenance_only' if path.startswith('data/') else 'historical_immutable'))
        row={'path':path,'lifecycle':kind,'frozen_blob':original_by[path]['blob']}
    current_entries.append(row)
put(qa.LIFECYCLE,{'schema_id':'overnight_repository_lifecycle@1.0','baseline_commit':BASE,'rules':['Current authority is the sole execution pointer.','Historical next_action values are freeze-time evidence.','Frozen implementation preservation does not authorize its main().','No automatic outcome workflow is active.','Archived relative paths use the baseline-root semantics.'],'ledger_baseline':{'count':12,'queries_sha256':qa.canonical_hash(ledger['queries'])},'files':current_entries,'production_authority':False})
subprocess.run(['git','add','-A'],check=True)
print(json.dumps({'original_files':len(original),'counts':counts,'retained_scripts':len(keep_scripts),'current_classified_files':len(current_entries),'production_authority':False},sort_keys=True))
