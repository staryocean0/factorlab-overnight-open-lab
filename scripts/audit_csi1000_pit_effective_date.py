#!/usr/bin/env python3
"""Replay two bounded source responses; never backdate a monthly snapshot."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXACT = ROOT / 'data/external/csi1000_pit_exact_20201214_response.json'
MONTH = ROOT / 'data/external/csi1000_pit_december_2020_response.json'
OUT = ROOT / 'artifacts/research/pit_membership_effective_date_probe/results.json'


def rows(obj):
    if obj.get('query_execution_status') != 'Success':
        raise AssertionError('source query did not succeed; empty rows are not evidence of absence')
    if not isinstance(obj.get('rows'), list):
        raise AssertionError('missing source rows')
    return obj['rows']


def adjudicate(exact, month):
    exact_rows, month_rows = rows(exact), rows(month)
    expected = "SELECT stock_code, weight FROM ts_index_weight WHERE index_code = '000852.SH' AND trade_date = '2020-12-14' ORDER BY stock_code LIMIT 2000"
    expected_month = "SELECT trade_date, COUNT(*) AS n, ROUND(SUM(weight),8) AS weight_sum FROM ts_index_weight WHERE index_code = '000852.SH' AND trade_date >= '2020-12-01' AND trade_date <= '2020-12-31' GROUP BY trade_date ORDER BY trade_date"
    if exact.get('sql_query') != expected or month.get('sql_query') != expected_month:
        raise AssertionError('source query scope drift')
    for obj in [exact, month]:
        if (obj['repository_owner'], obj['repository_name']) != ('chenditc', 'investment_data'):
            raise AssertionError('source repository drift')
    if any(not '2020-12-01' <= r['trade_date'] <= '2020-12-31' for r in month_rows):
        raise AssertionError('out-of-window source row')
    dates = [r['trade_date'] for r in month_rows]
    if len(dates) != len(set(dates)):
        raise AssertionError('duplicate summary date')
    if bool(exact_rows) != ('2020-12-14' in dates):
        raise AssertionError('exact query and month summary disagree')
    return {
        'exact_effective_date': '2020-12-14', 'exact_snapshot_rows': len(exact_rows),
        'month_snapshot_dates': dates, 'month_summary': month_rows,
        'source_queries_successful': True,
        'exact_effective_date_snapshot_exists': bool(exact_rows),
        'frozen_exact_date_necessary_gate_pass': bool(exact_rows),
        'full_PIT_source_approved': False,
        'status': 'requires_remaining_full_source_audit' if exact_rows else 'rejected_as_exact_PIT_transport_at_frozen_event',
        'other_full_source_health_gates': 'not_evaluated_by_this_bounded_probe',
        'backdating_month_end_snapshot_allowed': False,
        'target_rows_read': 0, 'post_2020_rows_read': 0,
        'new_model_executions': 0, 'selection_authority': False,
    }


def main():
    result = adjudicate(json.loads(EXACT.read_text()), json.loads(MONTH.read_text()))
    result['schema_id'] = 'overnight_csi1000_pit_effective_date_probe@1.0'
    result['source_response_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [EXACT, MONTH]}
    result['upstream_ref'] = 'master (mutable); raw successful responses are frozen by SHA256'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
