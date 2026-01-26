from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import state, agent, storage
from app.schemas import Vitals

app = FastAPI(title="EdgeFHIR Relay")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_MODES = {"normal", "desat", "fever", "tachy"}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/status")
def get_status():
    storage.list_outbox_files()
    return state.get_status()


@app.get("/history")
def get_history():
    return {"series": state.get_history()}


@app.get("/mode")
def get_mode():
    return {"mode": state.get_mode()}


@app.post("/simulate/{mode_name}")
def simulate(mode_name: str):
    if mode_name not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Choose from: {VALID_MODES}")
    state.trigger_mode(mode_name, ttl_seconds=30)
    return {"mode": mode_name, "ttl_seconds": 30}


@app.post("/connectivity/{conn_state}")
def connectivity(conn_state: str):
    if conn_state not in ("on", "off"):
        raise HTTPException(status_code=400, detail="Use 'on' or 'off'")
    on = conn_state == "on"
    state.set_connectivity(on)
    retry_result = None
    if on:
        retry_result = storage.retry_on_reconnect()
    return {"connectivity_on": on, "retry": retry_result}


@app.post("/flush")
def flush():
    state.set_phase("syncing")
    result = storage.flush_to_cloud()
    state.set_phase("idle")
    return result


@app.post("/ingest")
def ingest(vitals: Vitals):
    state.set_phase("ingesting")

    state.set_phase("validating")
    # Pydantic already validated via Vitals model

    state.set_phase("interpreting")
    state.record_vitals(vitals.model_dump())
    output = agent.run(vitals)

    state.set_phase("writing-outbox")
    filename = storage.write_outbox(payload=output.model_dump())
    state.set_latest_outputs(output.decision.model_dump(), output.fhir_bundle)

    sync_result = None
    status = state.get_status()
    if status["connectivity_on"]:
        state.set_phase("syncing")
        sync_result = storage.flush_to_cloud()

    state.set_phase("idle")

    return {
        "stored": filename,
        "decision": output.decision.model_dump(),
        "sync": sync_result,
    }
