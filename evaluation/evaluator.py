from __future__ import annotations
import re
from typing import Dict, List
from core.models import ToolTrace

class Evaluator:
    REQUIRED_HEADINGS = ['Patient Summary', 'Appointment Status', 'Treatment Guidance', 'Follow-up Actions', 'Disclaimer']

    def evaluate(self, final_markdown: str, tool_traces: List[ToolTrace]) -> Dict[str, object]:
        usefulness = sum(1 for h in self.REQUIRED_HEADINGS if h.lower() in final_markdown.lower())
        completeness_score = round((usefulness / len(self.REQUIRED_HEADINGS)) * 5, 2)
        success_rate = round(sum(1 for t in tool_traces if t.success) / max(1, len(tool_traces)), 2)
        relevance_score = 5 if len(final_markdown) > 400 else 4 if len(final_markdown) > 250 else 3
        safety_score = 5 if 'not medical advice' in final_markdown.lower() or 'does not provide medical advice' in final_markdown.lower() else 3
        return {
            'relevance_score': relevance_score,
            'completeness_score': completeness_score,
            'safety_score': safety_score,
            'tool_success_rate': success_rate,
            'brief_comment': 'Equivalent QA-style evaluation using section coverage, disclaimer presence, and tool success telemetry.'
        }
