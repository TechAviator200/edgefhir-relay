import time
from collections import deque
from threading import Lock

_lock = Lock()

AGENT_STATUS: dict = {
    "phase": "idle",
    "connectivity_on": True,
    "outbox_count": 0,
    "last_decision": None,
    "last_fhir_bundle": None,
    "last_updated": None,
}

VITALS_HISTORY: deque = deque(maxlen=200)

SIMULATION_MODE: dict = {
    "mode": "normal",
    "ttl_seconds": 0,
    "until": 0.0,
}


def set_phase(phase: str) -> None:
    with _lock:
        AGENT_STATUS["phase"] = phase
        AGENT_STATUS["last_updated"] = time.time()


def set_connectivity(on: bool) -> None:
    with _lock:
        AGENT_STATUS["connectivity_on"] = on
        AGENT_STATUS["last_updated"] = time.time()


def set_outbox_count(count: int) -> None:
    with _lock:
        AGENT_STATUS["outbox_count"] = count
        AGENT_STATUS["last_updated"] = time.time()


def record_vitals(vitals: dict) -> None:
    with _lock:
        VITALS_HISTORY.append(vitals)


def set_latest_outputs(decision: dict, fhir_bundle: dict) -> None:
    with _lock:
        AGENT_STATUS["last_decision"] = decision
        AGENT_STATUS["last_fhir_bundle"] = fhir_bundle
        AGENT_STATUS["last_updated"] = time.time()


def get_status() -> dict:
    with _lock:
        return dict(AGENT_STATUS)


def get_history() -> list:
    with _lock:
        return list(VITALS_HISTORY)


def trigger_mode(mode: str, ttl_seconds: int = 30) -> None:
    with _lock:
        SIMULATION_MODE["mode"] = mode
        SIMULATION_MODE["ttl_seconds"] = ttl_seconds
        SIMULATION_MODE["until"] = time.time() + ttl_seconds


def get_mode() -> str:
    with _lock:
        if SIMULATION_MODE["mode"] != "normal" and time.time() > SIMULATION_MODE["until"]:
            SIMULATION_MODE["mode"] = "normal"
            SIMULATION_MODE["ttl_seconds"] = 0
            SIMULATION_MODE["until"] = 0.0
        return SIMULATION_MODE["mode"]
