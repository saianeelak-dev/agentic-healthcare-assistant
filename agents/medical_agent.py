from __future__ import annotations
from typing import List
from core.models import ToolTrace, RetrievalHit
from tools.medical_search_tool import MedicalSearchTool
from rag.vector_store import FaissVectorStore

class MedicalAgent:
    def __init__(self, search_tool: MedicalSearchTool, vector_store: FaissVectorStore) -> None:
        self.search_tool = search_tool
        self.vector_store = vector_store

    def run(self, query: str, patient_name: str | None = None) -> tuple[str, list[RetrievalHit], list[ToolTrace]]:
        traces: list[ToolTrace] = []
        local_hits = self.vector_store.search(query, patient_name=patient_name)
        if local_hits:
            traces.append(ToolTrace('rag_medical_search', {'query': query, 'patient_name': patient_name}, True, f'Retrieved {len(local_hits)} local knowledge chunks'))
        pubmed_items, pubmed_trace = self.search_tool.pubmed_search(query)
        traces.append(pubmed_trace)
        who_items, who_trace = self.search_tool.who_stub(query)
        traces.append(who_trace)

        sections = []
        if local_hits:
            sections.append('Local retrieved context:\n' + '\n\n'.join([f"- ({h.source_file}, score={h.score:.3f}) {h.text[:350]}" for h in local_hits]))
        if pubmed_items:
            sections.append('PubMed/Medline summaries:\n' + '\n'.join([f"- {x['title']} ({x['source']}, {x['pubdate']})" for x in pubmed_items]))
        if who_items:
            sections.append('WHO summaries:\n' + '\n'.join([f"- {x}" for x in who_items]))
        if not sections:
            sections.append('No external medical search results were retrieved. The assistant can still answer using local patient knowledge and general cautionary guidance.')
        return '\n\n'.join(sections), local_hits, traces