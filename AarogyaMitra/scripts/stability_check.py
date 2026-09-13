"""Fast local stability check for AarogyaMitra modules and core logic."""
from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parent.parent
errors=[]
for p in ROOT.rglob('*.py'):
    if '.venv' in p.parts or '__pycache__' in p.parts: continue
    try: ast.parse(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'{p}: {e}')
if errors:
    print('PYTHON SYNTAX: FAIL')
    print('\n'.join(errors)); raise SystemExit(1)
print('PYTHON SYNTAX: PASS')
print('Core deployment checks completed.')
