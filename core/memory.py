from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from .config import settings

class MemoryStore:
    def __init__(self) -> None:
        self.base = Path(settings.memory_dir)
        self.base.mkdir(parents=True, exist_ok=True)
        self.session_file = self.base / 'session_memory.jsonl'
        self.patient_memory_file = self.base / 'patient_memory.json'
        if not self.patient_memory_file.exists():
            self.patient_memory_file.write_text(json.dumps({}, indent=2), encoding='utf-8')

    def append_session(self, payload: Dict[str, Any]) -> None:
        payload = {**payload, 'timestamp': datetime.utcnow().isoformat()}
        with self.session_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False) + '\n')

    def upsert_patient_memory(self, patient_name: str, summary: str) -> None:
        data = json.loads(self.patient_memory_file.read_text(encoding='utf-8'))
        data[patient_name] = {
            'summary': summary,
            'updated_at': datetime.utcnow().isoformat()
        }
        self.patient_memory_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

    def get_patient_memory(self, patient_name: str) -> Dict[str, Any]:
        data = json.loads(self.patient_memory_file.read_text(encoding='utf-8'))
        return data.get(patient_name, {})

    def load_session(self) -> List[Dict[str, Any]]:
        if not self.session_file.exists():
            return []
        return [json.loads(line) for line in self.session_file.read_text(encoding='utf-8').splitlines() if line.strip()]