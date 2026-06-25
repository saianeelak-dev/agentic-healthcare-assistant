from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from .config import settings

class RunLogger:
    def __init__(self) -> None:
        self.logs_dir = Path(settings.logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.run_log = self.logs_dir / 'runs.jsonl'

    def log(self, payload: Dict[str, Any]) -> None:
        payload = {**payload, 'logged_at': datetime.utcnow().isoformat()}
        with self.run_log.open('a', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False) + '\n')
