from __future__ import annotations
from tools.doctor_schedule_tool import DoctorScheduleTool
from core.models import AppointmentResult, ToolTrace

class AppointmentAgent:
    def __init__(self, schedule_tool: DoctorScheduleTool) -> None:
        self.schedule_tool = schedule_tool

    def run(self, patient_name: str | None, specialty: str | None) -> tuple[AppointmentResult, list[ToolTrace]]:
        if not specialty:
            result = AppointmentResult(False, specialty=None, message='No doctor specialty provided or inferred')
            trace = ToolTrace('appointment_agent', {'patient_name': patient_name, 'specialty': specialty}, False, result.message)
            return result, [trace]
        return self.schedule_tool.book(patient_name or 'patient', specialty)
