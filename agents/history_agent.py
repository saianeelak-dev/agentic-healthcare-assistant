from __future__ import annotations
from typing import List, Tuple
from core.models import RetrievalHit, ToolTrace
from rag.vector_store import FaissVectorStore
from tools.ehr_tool import EHRTool

class HistoryAgent:
    def __init__(self, ehr_tool: EHRTool, vector_store: FaissVectorStore) -> None:
        self.ehr_tool = ehr_tool
        self.vector_store = vector_store

    def run(self, patient_name: str | None, user_query: str) -> tuple[str, list[RetrievalHit], list[ToolTrace]]:
        traces: list[ToolTrace] = []
        summary_parts: list[str] = []
        record = None
        if patient_name:
            record, trace = self.ehr_tool.find_patient(patient_name)
            traces.append(trace)
        if record:
            summary_parts.append(
                f"Structured record for {record.get('Name')}: age {record.get('Age')}, gender {record.get('Gender')}, address {record.get('Address')}. Summary: {record.get('Summary')}"
            )
        print("HistoryAgent patient:", patient_name)
        hits = self.vector_store.search(user_query,patient_name=patient_name)
        print("Retrieved hits:", len(hits))
        if not patient_name:

            candidates = [
                "Anjali",
                "Ramesh",
                "David",
                "Rahul",
                "Rebeca"
            ]

            for p in candidates:
                if p.lower() in user_query.lower():
                    patient_name = p
                    break
        if hits:
            summary_parts.append('Retrieved record evidence:\n' + '\n\n'.join([f"- ({h.source_file}, score={h.score:.3f}) {h.text[:400]}" for h in hits]))
            traces.append(ToolTrace('rag_patient_search', {'query': user_query, 'patient_name': patient_name}, True, f'Retrieved {len(hits)} patient-history chunks'))
        else:
            traces.append(ToolTrace('rag_patient_search', {'query': user_query, 'patient_name': patient_name}, False, 'No matching patient-history chunks'))
        if not summary_parts:
            return 'No matching patient history found.', hits, traces
        return '\n\n'.join(summary_parts), hits, traces
