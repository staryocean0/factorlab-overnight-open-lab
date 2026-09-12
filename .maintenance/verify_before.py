import json
import os
import pathlib
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path.cwd().resolve()
# Hard I/O barrier active before test collection/import. This is a code-maintenance run only.
def audit(event, args):
    if event.startswith('socket.') and event in {'socket.connect', 'socket.getaddrinfo', 'socket.bind'}:
        raise RuntimeError('maintenance_network_forbidden')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        p = pathlib.Path(os.fsdecode(args[0])).resolve()
        if p.is_relative_to(ROOT):
            rel = p.relative_to(ROOT).as_posix()
            if p.suffix in {'.csv', '.parquet', '.feather', '.pkl', '.pickle', '.pt', '.npz'} or rel.startswith(('output/', 'artifacts/')):
                raise RuntimeError('maintenance_market_or_account_rows_forbidden: ' + rel)
sys.addaudithook(audit)
import pytest
excluded = ['tests/test_high_open_dev_pack_boundary.py', 'tests/test_no_future_and_baseline.py', 'tests/test_runtime_text_carrier.py']
xml = ROOT / 'docs/maintenance/20260912_baseline_tests.xml'
code = pytest.main(['-q','--disable-warnings', '--junitxml='+str(xml)] + ['--ignore='+p for p in excluded])
suites = ET.parse(xml).getroot()
failures = []
for case in suites.iter('testcase'):
    for tag in ['failure', 'error', 'skipped']:
        elem = case.find(tag)
        if elem is not None:
            failures.append({'test': case.attrib.get('classname','')+'::'+case.attrib.get('name',''), 'kind': tag, 'reason': elem.attrib.get('message','')[:400]})
report = {'baseline_commit':'0e28a6285745552a665d5b1cba11c9da73fbacd7','pytest_exit_code':int(code),'test_cases':sum(1 for _ in suites.iter('testcase')),'excluded_data_integration_tests':excluded,'exclusion_reason':'These tests parse real market carriers; cleanup does not need outcome rows. Preserve as historical integration tests, replace current boundary coverage with metadata and synthetic checks.','hard_data_and_network_io_barrier':True,'failures':failures}
(ROOT/'docs/maintenance/20260912_baseline_tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
xml.unlink()
print(json.dumps(report,ensure_ascii=False))
# Nonzero scientific assertions are recorded as baseline findings, not hidden or declared green.
