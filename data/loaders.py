from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from pypdf import PdfReader


def load_records_xlsx(path: str | Path) -> pd.DataFrame:
    return pd.read_excel(path, engine='openpyxl')


def load_pdf_text(path: str | Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ''
        parts.append(f'[PAGE {i}]\n{text.strip()}')
    return '\n\n'.join(parts).strip()


def load_all_data(data_dir: str | Path) -> Dict[str, Any]:
    data_dir = Path(data_dir)
    excel_path = data_dir / 'records.xlsx'
    pdf_paths = [
        data_dir / 'sample_patient.pdf',
        data_dir / 'sample_report_anjali.pdf',
        data_dir / 'sample_report_david.pdf',
        data_dir / 'sample_report_ramesh.pdf',
    ]
    result = {'records': pd.DataFrame(), 'pdf_texts': {}}
    if excel_path.exists():
        result['records'] = load_records_xlsx(excel_path)
    for p in pdf_paths:
        if p.exists():
            result['pdf_texts'][p.name] = load_pdf_text(p)
    return result