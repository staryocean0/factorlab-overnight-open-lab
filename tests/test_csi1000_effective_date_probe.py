import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_csi1000_pit_effective_date as probe


class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.exact = json.loads(probe.EXACT.read_text())
        self.month = json.loads(probe.MONTH.read_text())

    def test_successful_empty_exact_query_rejects_month_end_backdating(self):
        result = probe.adjudicate(self.exact, self.month)
        self.assertEqual(result['month_snapshot_dates'], ['2020-12-31'])
        self.assertFalse(result['frozen_exact_date_necessary_gate_pass'])
        self.assertFalse(result['backdating_month_end_snapshot_allowed'])

    def test_timeout_or_sql_error_is_not_a_negative_scientific_verdict(self):
        bad = copy.deepcopy(self.exact)
        bad['query_execution_status'] = 'Error'
        with self.assertRaisesRegex(AssertionError, 'did not succeed'):
            probe.adjudicate(bad, self.month)

    def test_post2020_result_is_rejected(self):
        bad = copy.deepcopy(self.month)
        bad['rows'].append({'trade_date': '2021-01-01', 'n': '1000'})
        with self.assertRaisesRegex(AssertionError, 'out-of-window'):
            probe.adjudicate(self.exact, bad)


if __name__ == '__main__':
    unittest.main()
