from app.schemas import Vitals, Decision, AgentOutput
from app import fhir

PATIENT_ID = "patient-001"
DEVICE_ID = "device-ox-001"

OBS_DEFS = [
    ("hr", "8867-4", "Heart rate", "bpm"),
    ("spo2", "2708-1", "Oxygen saturation", "%"),
    ("temp_c", "8310-5", "Body temperature", "Cel"),
    ("rr", "9279-1", "Respiratory rate", "/min"),
]


def _interpret(name: str, value: float) -> str:
    if name == "spo2":
        if value < 90:
            return "critical-low"
        if value < 92:
            return "low"
        return "normal"
    if name == "hr":
        if value > 130:
            return "critical-high"
        if value > 110:
            return "high"
        if value < 50:
            return "low"
        return "normal"
    if name == "temp_c":
        if value >= 39.5:
            return "critical-high"
        if value >= 38.0:
            return "high"
        return "normal"
    if name == "rr":
        if value > 30:
            return "critical-high"
        if value > 24:
            return "high"
        return "normal"
    return "normal"


def _severity_confidence(vitals: Vitals) -> float:
    """Compute confidence 0.5–0.95 based on how far vitals exceed thresholds."""
    severity = 0.0
    if vitals.spo2 < 92:
        severity += min((92 - vitals.spo2) / 10.0, 1.0)  # 0–1 as spo2 drops 92→82
    if vitals.hr > 110:
        severity += min((vitals.hr - 110) / 50.0, 1.0)    # 0–1 as hr rises 110→160
    if vitals.temp_c >= 38.0:
        severity += min((vitals.temp_c - 38.0) / 2.0, 1.0)  # 0–1 as temp rises 38→40
    if vitals.rr > 24:
        severity += min((vitals.rr - 24) / 12.0, 1.0)     # 0–1 as rr rises 24→36
    # Normalize: max possible severity = 4.0 → confidence 0.95
    return round(min(0.5 + severity * 0.1125, 0.95), 2)


def run(vitals: Vitals) -> AgentOutput:
    score = 0
    reasons: list[str] = []

    if vitals.spo2 < 92:
        score += 2
        reasons.append(f"spo2={vitals.spo2} < 92")
    if vitals.hr > 110:
        score += 1
        reasons.append(f"hr={vitals.hr} > 110")
    if vitals.temp_c >= 38.0:
        score += 1
        reasons.append(f"temp_c={vitals.temp_c} >= 38.0")
    if vitals.rr > 24:
        score += 1
        reasons.append(f"rr={vitals.rr} > 24")

    confidence = _severity_confidence(vitals)

    if score >= 3:
        triage, next_action = "urgent review", "notify_clinician_queue"
    elif score == 2:
        triage, next_action = "watch", "notify_clinician_queue"
    else:
        triage, next_action = "ok", "log only"

    decision = Decision(
        triage=triage,
        reasons=reasons if reasons else ["all vitals within range"],
        confidence=confidence,
        next_action=next_action,
    )

    # Build FHIR observations
    observations = []
    for attr, code, display, unit in OBS_DEFS:
        value = getattr(vitals, attr)
        interp = _interpret(attr, value)
        observations.append(
            fhir.observation(code, display, value, unit, vitals.ts, PATIENT_ID, DEVICE_ID, interp)
        )

    task = fhir.triage_task(triage, decision.reasons, vitals.ts, PATIENT_ID)

    resources = [
        fhir.patient_resource(PATIENT_ID),
        fhir.device_resource(DEVICE_ID),
        *observations,
        task,
    ]

    return AgentOutput(
        decision=decision,
        fhir_bundle=fhir.bundle(resources),
    )
