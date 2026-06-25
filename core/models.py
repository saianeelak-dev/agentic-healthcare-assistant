from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

@dataclass
class Plan:
    steps: List[str]
    patient_name: Optional[str] = None
    doctor_specialty: Optional[str] = None
    reasoning: str = ""

@dataclass
class ChunkRecord:
    chunk_id: str
    source_file: str
    patient_name: Optional[str]
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RetrievalHit:
    chunk_id: str
    score: float
    source_file: str
    patient_name: Optional[str]
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AppointmentResult:
    success: bool
    doctor_name: Optional[str] = None
    specialty: Optional[str] = None
    slot: Optional[str] = None
    message: str = ""

@dataclass
class ToolTrace:
    tool_name: str
    input_payload: Dict[str, Any]
    success: bool
    output_summary: str

@dataclass
class AgentResponse:
    final_markdown: str
    plan: Plan
    patient_summary: str
    medical_summary: str
    appointment: AppointmentResult
    retrieved_context: List[RetrievalHit]
    tool_traces: List[ToolTrace]
    evaluation: Dict[str, Any]