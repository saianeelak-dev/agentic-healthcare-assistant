from __future__ import annotations
from typing import List, Any
from core.models import AppointmentResult, RetrievalHit
from core.config import settings

try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False

FINAL_SYSTEM = """
You are an Agentic Healthcare Assistant.
Create a concise markdown response with headings:
- Patient Summary
- Appointment Status
- Treatment Guidance
- Follow-up Actions
- Disclaimer
Rules:
- Use only the provided context.
- If the patient is not found, clearly say so and avoid assigning identity.
- Keep the disclaimer explicit that this is not medical advice.
"""


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return str(content)


class FinalAgent:
    def __init__(self) -> None:
        self.llm = None

        if GROQ_AVAILABLE and settings.groq_api_key:
            self.llm = ChatGroq( model =settings.groq_model,temperature=0.2,)

    @staticmethod
    def _format_context(hits: List[RetrievalHit]) -> str:
        if not hits:
            return 'No retrieved context.'
        return '\n'.join([f"- [{h.source_file}] {h.text[:350]}" for h in hits])

    def compose(self, user_query: str, patient_summary: str, appointment: AppointmentResult, 
        medical_summary: str, all_hits: List[RetrievalHit]) -> str:
        if not self.llm:
            appointment_md = appointment.message if appointment and appointment.message else 'No appointment action taken.'
            follow_up = []
            if appointment and appointment.success:
                follow_up.append(f"Bring prior reports to the visit scheduled at **{appointment.slot}**.")
            follow_up.append('Review the retrieved history and validate it before making administrative updates.')
            follow_up.append('Escalate to a clinician for diagnosis or treatment confirmation.')
            return (
                f"## Patient Summary\n"
                f"{patient_summary or 'No matching patient history found.'}\n\n"
                f"##Appointment Status\n"               
                f"{appointment_md}\n\n"
                f"## Treatment Guidance\n"
                f"{medical_summary}\n\n"
                f"## Follow-up Actions\n"
                f"- " + "\n- ".join(follow_up) + "\n\n"
                f"## Disclaimer\n"
                f"This assistant supports administrative and information-retrieval tasks only. "
                f"It does not provide medical advice, diagnosis, or emergency triage.")
        
        context = self._format_context(all_hits)
        prompt = (
            f"User query: {user_query}\n\n"
            f"Patient summary:\n{patient_summary}\n\n"
            f"Appointment result:\n{appointment.message if appointment else 'None'}\n\n"
            f"Medical summary:\n{medical_summary}\n\n"
            f"Retrieved context:\n{context}")
        msg = self.llm.invoke([('system', FINAL_SYSTEM), ('human', prompt)])
        return _content_to_text(msg.content)