from __future__ import annotations
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)
for name in ['records.xlsx', 'sample_patient.pdf', 'sample_report_anjali.pdf', 'sample_report_david.pdf','sample_report_ramesh.pdf']:
    src = Path(name)
    if src.exists() and not (DATA / name).exists():
        shutil.copy2(src, DATA / name)
        print(f'Copied {name} -> data/{name}')
print('Bootstrap complete.')