
from __future__ import annotations
import re
from typing import Any, List

from core.config import settings
from core.models import Plan

try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False


PLANNER_SYSTEM = """
You are a planner for an Agentic Healthcare Assistant.
Return ONLY valid minified JSON, no markdown, no explanation.
Schema:
{"steps":["appointment","history","medical"],"patient_name":null,"doctor_specialty":null,"reasoning":""}
Rules:
- Include appointment if the user wants to book/schedule/see a doctor.
- Include history if the user asks for history/summary/records/diagnosis/medications or mentions an existing patient.
- Include medical if the user asks for disease information, treatment options, latest methods, or external medical knowledge.
- doctor_specialty should only be filled if the specialty is explicitly stated or inferable from disease text.
"""


SPECIALTY_HINTS = {
    "kidney": "nephrologist",
    "renal": "nephrologist",
    "cough": "pulmonologist",
    "fever": "general physician",
    "hypertension": "cardiologist",
    "diabetes": "endocrinologist",
}


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return str(content)


class PlannerAgent:
    def __init__(self, patient_names: List[str] | None = None) -> None:
        self.llm = None
        self.patient_names = patient_names or []

        if GROQ_AVAILABLE and settings.groq_api_key:
            self.llm = ChatGroq(
                model=settings.groq_model,
                temperature=0,
            )

    def _safe_plan(self, user_query: str) -> Plan:
        q = user_query.lower()
        steps: List[str] = []

        if any(k in q for k in ["book", "schedule", "appointment", "see a doctor", "consult"]):
            steps.append("appointment")

        if any(k in q for k in ["history", "summary", "record", "diagnosis", "medication", "patient", "report", "reports", "pdf"]):
            steps.append("history")

        if any(k in q for k in ["disease", "treatment", "latest", "methods", "info", "information"]):
            steps.append("medical")

        if not steps:
            steps = ["history"]

        patient_name = None

        # # Dynamic name detection from records.xlsx
        # for full_name in self.patient_names:
        #     if full_name and full_name.lower() in q:
        #         patient_name = full_name
        #         break
                    
        # Partial-name fallback: "Anjali" should match "Anjali Mehra"
        if patient_name is None:
            for full_name in self.patient_names:
                first_token = full_name.split()[0].strip().lower()
                if first_token and re.search(rf"\b{re.escape(first_token)}\b", q):
                    patient_name = full_name
                    break

        if patient_name and "history" not in steps:
            steps.append("history")

        for full_name in self.patient_names:
            if full_name and full_name.lower() in q:
                patient_name = full_name
                break
                    
        specialty = None
        for hint, sp in SPECIALTY_HINTS.items():
            if hint in q:
                specialty = sp
                break

        msp = re.search(r"(nephrologist|pulmonologist|cardiologist|endocrinologist|general physician)", q)
        if msp:
            specialty = msp.group(1)

        return Plan(
            steps=steps,
            patient_name=patient_name,
            doctor_specialty=specialty,
            reasoning="rule-based fallback planner",
        )

    def plan(self, user_query: str) -> Plan:
        if not self.llm:
            return self._safe_plan(user_query)

        try:
            msg = self.llm.invoke(
                [
                    ("system", PLANNER_SYSTEM),
                    ("human", user_query),
                ]
            )
            content = _content_to_text(msg.content)
            data = json.loads(content)

            return Plan(
                steps=data.get("steps", []) or ["history"],
                patient_name=data.get("patient_name"),
                doctor_specialty=data.get("doctor_specialty"),
                reasoning=data.get("reasoning", "llm planner"),
            )
        except Exception:
            return self._safe_plan(user_query)

import json
