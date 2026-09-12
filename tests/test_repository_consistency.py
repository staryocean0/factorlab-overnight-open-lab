from copy import deepcopy
from pathlib import Path
import socket

import pytest
import check_repository_consistency as qa

ROOT = Path(__file__).resolve().parents[1]


def test_whole_repository_is_consistent():
    result = qa.check(ROOT)
    assert result['status'] == 'PASS', result['errors']
    assert result['tracked_files'] == result['classified_files']
    assert result['market_rows_opened'] is False


@pytest.mark.parametrize('path', ['README.md', 'CONTINUE_HERE.md', 'docs/CURRENT_STATUS.md', 'docs/WHITEPAPER.md'])
def test_current_documents_are_generated_from_one_authority(path):
    assert (ROOT/path).read_text(encoding='utf-8') == qa.render_views(ROOT)[path]


@pytest.mark.parametrize('mutation', ['authority_count','registry_count','ledger_count','duplicate_id','ordinal_gap','public_release','production'])
def test_ledger_drift_fails_closed(mutation):
    a, r, ledger = [deepcopy(qa.load(ROOT,p)) for p in [qa.AUTH,qa.REGISTRY,qa.LEDGER]]
    if mutation == 'authority_count': a['blackbox_ledger_query_count'] += 1
    elif mutation == 'registry_count': r['blackbox_ledger_query_count'] -= 1
    elif mutation == 'ledger_count': ledger['query_count'] += 1
    elif mutation == 'duplicate_id': ledger['queries'][1]['query_id'] = ledger['queries'][0]['query_id']
    elif mutation == 'ordinal_gap': ledger['queries'][1]['ordinal'] = 100
    elif mutation == 'public_release': ledger['queries'][0]['public_detail_release'] = True
    elif mutation == 'production': a['production_authority'] = True
    assert qa.ledger_errors(ledger,a,r)


def test_canonical_hash_ignores_mapping_order_not_values():
    assert qa.canonical_hash({'a':1,'b':2}) == qa.canonical_hash({'b':2,'a':1})
    assert qa.canonical_hash({'a':1,'b':2}) != qa.canonical_hash({'a':1,'b':3})


def test_complete_original_tree_has_a_disposition():
    before = qa.load(ROOT, 'docs/maintenance/20260912_inventory_before.json')
    moves = qa.load(ROOT, qa.TRANSITIONS)
    assert {x['path'] for x in before['files']} == {x['original_path'] for x in moves['files']}
    for row in moves['files']:
        assert row['reason']
        if row.get('current_path'):
            assert (ROOT/row['current_path']).exists()
        else:
            assert row['action'] == 'deleted_completed_one_shot'
            assert row['baseline_blob']


def test_archive_resolver_preserves_original_path_lookup():
    rows = qa.load(ROOT, qa.TRANSITIONS)['files']
    moved = [r for r in rows if r['action'] == 'archived']
    assert moved
    for row in moved:
        assert qa.resolve_reference(ROOT,row['original_path']) == ROOT/row['current_path']


def test_closed_v21_is_not_current_dev_authority():
    a = qa.load(ROOT,qa.AUTH)
    assert a['active_research'] is None
    assert not any('v21' in str(p.get('latest_identity','')).lower() for p in qa.load(ROOT,qa.REGISTRY)['products'])
    paths = qa.load(ROOT,qa.LIFECYCLE)['files']
    old_tests = [p for p in paths if 'test_' in p['path'] and 'v21' in p['path']]
    assert old_tests and all(p['lifecycle'] == 'archived_immutable' for p in old_tests)


def test_latest_e3_dev_does_not_inherit_v2_blackbox_identity():
    e3 = next(p for p in qa.load(ROOT,qa.REGISTRY)['products'] if p['product_id'] == 'OFP-E3')
    assert e3['latest_identity'] == 'overnight_c2_forward_cycle_portfolio_risk_abstention_v1'
    assert 'INSUFFICIENT' in e3['status']
    assert e3.get('blackbox_query_id') is None
    assert e3.get('blackbox_ledger_ordinal') is None


def test_all_receipts_stay_sealed_and_production_false():
    for query in qa.load(ROOT,qa.LEDGER)['queries']:
        receipt = qa.load(ROOT,query['receipt'])
        assert receipt['public_detail_release'] is False
        assert receipt['production_authority'] is False


def test_fresh_gate_is_not_calendar_only_authorization():
    state = qa.load(ROOT,'docs/governance/gap_fill_v2_true_fresh_state_v1.json')
    fresh = state['first_true_fresh_challenge']
    assert fresh['not_before_china_date'] == '2027-01-01'
    assert fresh['window'] == '2026-08-24_to_2026-12-31'
    assert fresh['fresh_window_opened'] is False
    assert state['partial_window_open_forbidden'] is True


@pytest.mark.parametrize('name',['data/forbidden.csv','data/forbidden.parquet','output/forbidden.json'])
def test_default_test_barrier_blocks_real_data_paths(name):
    with pytest.raises(RuntimeError, match='maintenance_market_or_account_rows_forbidden'):
        (ROOT/name).read_bytes()


def test_default_test_barrier_blocks_network():
    with pytest.raises(RuntimeError, match='maintenance_network_forbidden'):
        socket.getaddrinfo('example.com',443)


def test_exact_v6a_legacy_schema_uses_candidate_identity():
    r = {'schema_id':'overnight_v6a_reusable_blackbox_receipt@1.0','candidate':'frozen_v6a'}
    assert qa.receipt_identity(r) == 'frozen_v6a'

def test_modern_receipt_requires_research_identity():
    assert qa.receipt_identity({'schema_id':'modern@1.0','candidate':'wrong'}) is None

def test_modern_identity_does_not_fall_back_to_candidate():
    assert qa.receipt_identity({'schema_id':'modern@1.0','candidate':'wrong','research_identity':'correct'}) == 'correct'
