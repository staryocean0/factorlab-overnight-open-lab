#!/usr/bin/env python3
"""Metadata/source-only audit. Never import project code or read market/account carriers."""
import ast
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path.cwd()
BASE = '0e28a6285745552a665d5b1cba11c9da73fbacd7'
OUT = ROOT / 'docs/maintenance'
OUT.mkdir(parents=True, exist_ok=True)
raw = subprocess.check_output(['git', 'ls-tree', '-r', '-l', BASE], text=True)
entries = []
for line in raw.splitlines():
    meta, path = line.split('\t', 1)
    mode, kind, sha, size = meta.split()
    entries.append({'path': path, 'mode': mode, 'blob': sha, 'bytes': int(size) if size.isdigit() else None})
paths = {x['path'] for x in entries}
summary = {'baseline_commit': BASE, 'file_count': len(entries), 'top_level_counts': dict(collections.Counter(x['path'].split('/')[0] for x in entries)), 'suffix_counts': dict(collections.Counter(Path(x['path']).suffix for x in entries)), 'market_or_account_rows_read': False, 'project_code_executed': False}
summary['root_files'] = sorted(p for p in paths if '/' not in p)
summary['whitepapers_and_indexes'] = sorted(p for p in paths if 'whitepaper' in p.lower() or p.endswith('README.md') or p.endswith('CONTINUE_HERE.md'))
summary['python_files'] = sorted(p for p in paths if p.endswith('.py') and not p.startswith('archive/'))
summary['test_files'] = sorted(p for p in paths if p.startswith('tests/'))
summary['syntax_errors'] = []
summary['json_errors'] = []
summary['workflows'] = []
summary['governance_states'] = []
summary['test_io_review'] = []
summary['source_imports'] = {}
summary['missing_literal_references'] = []
for item in entries:
    p = item['path']
    # No data, output, artifact, CSV, parquet, spreadsheet, PDF, model, or archive payloads are read.
    if p.startswith(('data/', 'output/', 'artifacts/', 'archive/')):
        continue
    file = ROOT / p
    if file.suffix not in {'.py', '.json', '.md', '.toml', '.yml', '.yaml', '.sh'}:
        continue
    text = file.read_text(encoding='utf-8')
    if file.suffix == '.py':
        try:
            tree = ast.parse(text, filename=p)
            imports = sorted({n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
            summary['source_imports'][p] = imports
            if p.startswith('tests/'):
                hits = [{'line': i, 'text': line.strip()[:220]} for i, line in enumerate(text.splitlines(), 1) if re.search(r'read_(csv|parquet|json|text|bytes)|subprocess|requests\.|urlopen|load\(|open\(|import_module|exec\(', line)]
                summary['test_io_review'].append({'path': p, 'imports': imports, 'io_lines': hits})
        except SyntaxError as e:
            summary['syntax_errors'].append({'path': p, 'line': e.lineno, 'error': e.msg})
    if file.suffix == '.json':
        try:
            obj = json.loads(text)
            if p.startswith('docs/governance/') and isinstance(obj, dict) and ('state' in p or 'current' in p or 'baseline' in p):
                summary['governance_states'].append({'path': p, **{k: obj[k] for k in ['schema_id', 'status', 'research_identity', 'next_action', 'blackbox_query_opened', 'outcome_opened', 'production_authority'] if k in obj}})
        except Exception as e:
            summary['json_errors'].append({'path': p, 'error': str(e)})
    if p.startswith('.github/workflows/'):
        summary['workflows'].append({'path': p, 'content': text})
    if p in {'README.md', 'AGENTS.md', 'pyproject.toml'} or 'whitepaper' in p.lower() or p.endswith('README.md'):
        refs = set(re.findall(r'(?:docs|scripts|tests|data|\.codex|\.github)/[A-Za-z0-9_./@+\-]+\.(?:md|json|py|sh|ya?ml|toml)', text))
        for target in sorted(refs):
            if target not in paths:
                summary['missing_literal_references'].append({'source': p, 'target': target})
summary['test_count'] = len(summary['test_files'])
(OUT/'20260912_inventory_before.json').write_text(json.dumps({'baseline_commit': BASE, 'files': entries}, indent=2)+'\n')
(OUT/'20260912_audit_before.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
# Split human review surfaces to avoid huge connector responses.
for key in ['workflows', 'test_io_review', 'governance_states', 'source_imports', 'missing_literal_references']:
    (OUT/f'20260912_before_{key}.json').write_text(json.dumps(summary[key], ensure_ascii=False, indent=2)+'\n')
(OUT/'20260912_before_summary.json').write_text(json.dumps({k:v for k,v in summary.items() if k not in ['workflows','test_io_review','governance_states','source_imports','missing_literal_references']}, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k: summary[k] for k in ['baseline_commit','file_count','top_level_counts','test_count','syntax_errors','json_errors','market_or_account_rows_read','project_code_executed']}, sort_keys=True))
