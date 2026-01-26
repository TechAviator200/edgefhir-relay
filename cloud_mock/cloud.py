from fastapi import FastAPI
from typing import Any, Dict

app = FastAPI(title="Mock Cloud Ingest")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest")
def ingest(payload: Dict[str, Any]):
    bundle = payload.get("fhir_bundle", {}) if isinstance(payload, dict) else {}
    entry = bundle.get("entry", [])
    return {
        "received": True,
        "bundleType": bundle.get("resourceType"),
        "entries": len(entry) if isinstance(entry, list) else 0,
    }
