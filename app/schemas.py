from typing import Optional
from pydantic import BaseModel, Field


class Vitals(BaseModel):
    ts: str
    hr: int = Field(ge=20, le=250)
    spo2: int = Field(ge=50, le=100)
    temp_c: float = Field(ge=30.0, le=45.0)
    rr: int = Field(ge=5, le=60)
    motion: Optional[float] = Field(default=None, ge=0)


class Decision(BaseModel):
    triage: str
    reasons: list[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
    next_action: str


class AgentOutput(BaseModel):
    decision: Decision
    fhir_bundle: dict
