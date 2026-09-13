from pathlib import Path
p=Path(__file__).resolve().parents[1]/'aarogyamitra_local.db'
if p.exists(): p.unlink(); print(f'Removed {p}')
else: print('No local database file found.')
