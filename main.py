
from __future__ import annotations
from dataclasses import asdict
from typing import Any, Dict, List
from core.config import settings
from core.memory import MemoryStore
from core.logging_utils import RunLogger
from core.models import AgentResponse, AppointmentResult, ToolTrace, RetrievalHit
from data.loaders import load_all_data
from rag.chunking import build_documents, chunk_documents
from rag.vector_store import FaissVectorStore
from tools.ehr_tool import EHRTool
from tools.doctor_schedule_tool import DoctorScheduleTool
from tools.medical_search_tool import MedicalSearchTool
from agents.planner import PlannerAgent
from agents.history_agent import HistoryAgent
from agents.appointment_agent import AppointmentAgent
from agents.medical_agent import MedicalAgent
from agents.final_agent import FinalAgent
from evaluation.evaluator import Evaluator


class HealthcareAssistant:
    def __init__(self) -> None:
        self.memory = MemoryStore()
        self.logger = RunLogger()
        loaded = load_all_data(settings.data_dir)
        self.records_df = loaded['records']
        self.pdf_texts = loaded['pdf_texts']

        self.vector_store = FaissVectorStore()
        if not self.vector_store.load():
            docs = build_documents(self.records_df, self.pdf_texts)
            chunks = chunk_documents(docs)
            self.vector_store.build(chunks)

        self.ehr_tool = EHRTool(self.records_df)
        self.doctor_tool = DoctorScheduleTool(settings.data_dir,consume_bookings=True)
        self.medical_search_tool = MedicalSearchTool()

        patient_names = []
        if not self.records_df.empty and "Name" in self.records_df.columns:
            patient_names = (
                self.records_df["Name"]
                .dropna()
                .astype(str)
                .tolist()
            )

        self.planner = PlannerAgent(patient_names=patient_names)
        #self.planner = PlannerAgent()
        self.history_agent = HistoryAgent(self.ehr_tool, self.vector_store)
        self.appointment_agent = AppointmentAgent(self.doctor_tool)
        self.medical_agent = MedicalAgent(self.medical_search_tool, self.vector_store)
        self.final_agent = FinalAgent()
        self.evaluator = Evaluator()

    def run(self, user_query: str) -> AgentResponse:
        plan = self.planner.plan(user_query)
        print ("PLAN:", plan)
        tool_traces: List[ToolTrace] = []
        patient_summary = ''
        medical_summary = ''
        appointment = AppointmentResult(False, message='No appointment action taken.')
        retrieved_context: List[RetrievalHit] = []

        if 'history' in plan.steps:
            hist_summary, hist_hits, hist_traces = self.history_agent.run(plan.patient_name, user_query)
            patient_summary = hist_summary
            retrieved_context.extend(hist_hits)
            tool_traces.extend(hist_traces)
            if plan.patient_name and hist_summary and hist_summary != 'No matching patient history found.':
                self.memory.upsert_patient_memory(plan.patient_name, hist_summary[:2000])

        if 'appointment' in plan.steps:
            appointment, appt_traces = self.appointment_agent.run(plan.patient_name, plan.doctor_specialty)
            tool_traces.extend(appt_traces)

        if 'medical' in plan.steps:
            med_query = user_query
            if plan.patient_name and patient_summary:
                med_query = f"{user_query}\n\nPatient context: {patient_summary[:500]}"
            med_summary, med_hits, med_traces = self.medical_agent.run(med_query, patient_name=plan.patient_name)
            medical_summary = med_summary
            retrieved_context.extend(med_hits)
            tool_traces.extend(med_traces)

        final_markdown = self.final_agent.compose(user_query, patient_summary, appointment, medical_summary, retrieved_context)
        evaluation = self.evaluator.evaluate(final_markdown, tool_traces)

        payload = {
            'user_query': user_query,
            'plan': asdict(plan),
            'tool_traces': [asdict(t) for t in tool_traces],
            'evaluation': evaluation,
            'appointment': asdict(appointment),
        }
        self.memory.append_session(payload)
        self.logger.log(payload)

        return AgentResponse(
            final_markdown=final_markdown,
            plan=plan,
            patient_summary=patient_summary,
            medical_summary=medical_summary,
            appointment=appointment,
            retrieved_context=retrieved_context,
            tool_traces=tool_traces,
            evaluation=evaluation,
        )
