import uuid
from datetime import datetime, timezone

TRIAGE_TO_PRIORITY = {
    "routine": "routine",
    "urgent": "urgent",
    "critical": "asap",
    "urgent review": "asap",
    "watch": "urgent",
    "ok": "routine",
}


def _id() -> str:
    return str(uuid.uuid4())


def patient_resource(patient_id: str) -> dict:
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "active": True,
    }


def device_resource(device_id: str) -> dict:
    return {
        "resourceType": "Device",
        "id": device_id,
        "status": "active",
    }


def observation(
    code: str,
    display: str,
    value: float,
    unit: str,
    ts: str,
    patient_id: str,
    device_id: str,
    interpretation: str = "normal",
) -> dict:
    return {
        "resourceType": "Observation",
        "id": _id(),
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": code, "display": display}]},
        "valueQuantity": {"value": value, "unit": unit, "system": "http://unitsofmeasure.org"},
        "effectiveDateTime": ts,
        "subject": {"reference": f"Patient/{patient_id}"},
        "device": {"reference": f"Device/{device_id}"},
        "interpretation": [{"text": interpretation}],
    }


def triage_task(triage: str, reasons: list[str], ts: str, patient_id: str) -> dict:
    return {
        "resourceType": "Task",
        "id": _id(),
        "status": "requested",
        "intent": "order",
        "priority": TRIAGE_TO_PRIORITY.get(triage, "urgent"),
        "description": f"Triage: {triage}",
        "reasonCode": [{"text": r} for r in reasons],
        "authoredOn": ts,
        "for": {"reference": f"Patient/{patient_id}"},
    }


def bundle(resources: list[dict]) -> dict:
    return {
        "resourceType": "Bundle",
        "id": _id(),
        "type": "collection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry": [{"resource": r} for r in resources],
    }
