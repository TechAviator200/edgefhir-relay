import asyncio
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import state, agent, storage
from app.schemas import Vitals


# --- Built-in Simulator ---
def generate_vitals(mode: str) -> dict:
    """Generate vitals based on current mode."""
    if mode == "desat":
        return {
            "hr": random.randint(95, 125),
            "spo2": random.randint(85, 93),
            "temp_c": round(random.uniform(36.5, 37.5), 1),
            "rr": random.randint(22, 32),
        }
    elif mode == "fever":
        return {
            "hr": random.randint(90, 115),
            "spo2": random.randint(93, 98),
            "temp_c": round(random.uniform(37.8, 39.8), 1),
            "rr": random.randint(20, 28),
        }
    elif mode == "tachy":
        return {
            "hr": random.randint(105, 155),
            "spo2": random.randint(93, 99),
            "temp_c": round(random.uniform(36.5, 37.8), 1),
            "rr": random.randint(18, 26),
        }
    else:  # normal
        return {
            "hr": random.randint(60, 90),
            "spo2": random.randint(95, 100),
            "temp_c": round(random.uniform(36.2, 37.2), 1),
            "rr": random.randint(12, 18),
        }


async def simulator_loop():
    """Background task that generates and ingests vitals every 2 seconds."""
    while True:
        try:
            mode = state.get_mode()
            vitals_data = generate_vitals(mode)
            vitals_data["ts"] = datetime.now(timezone.utc).isoformat()

            # Process vitals through the pipeline
            vitals = Vitals(**vitals_data)
            state.set_phase("ingesting")
            state.set_phase("validating")
            state.set_phase("interpreting")
            state.record_vitals(vitals.model_dump())
            output = agent.run(vitals)

            state.set_phase("writing-outbox")
            storage.write_outbox(payload=output.model_dump())
            state.set_latest_outputs(output.decision.model_dump(), output.fhir_bundle)

            status = state.get_status()
            if status["connectivity_on"]:
                state.set_phase("syncing")
                storage.flush_to_cloud()

            state.set_phase("idle")
        except Exception as e:
            print(f"[simulator] error: {e}")

        await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start simulator on app startup."""
    task = asyncio.create_task(simulator_loop())
    yield
    task.cancel()


app = FastAPI(title="EdgeFHIR Relay", lifespan=lifespan)

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
