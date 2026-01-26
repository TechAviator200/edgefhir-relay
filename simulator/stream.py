import random
import time
from datetime import datetime, timezone

import requests

RELAY_URL = "http://127.0.0.1:8000"


def normal_vitals() -> dict:
    return {
        "hr": random.randint(60, 90),
        "spo2": random.randint(95, 100),
        "temp_c": round(random.uniform(36.2, 37.2), 1),
        "rr": random.randint(12, 18),
    }


def desat_vitals() -> dict:
    # SpO2 fluctuates around 92 threshold (85–93)
    return {
        "hr": random.randint(95, 125),
        "spo2": random.randint(85, 93),
        "temp_c": round(random.uniform(36.5, 37.5), 1),
        "rr": random.randint(22, 32),
    }


def fever_vitals() -> dict:
    # Temp fluctuates around 38.0 threshold (37.8–39.8)
    return {
        "hr": random.randint(90, 115),
        "spo2": random.randint(93, 98),
        "temp_c": round(random.uniform(37.8, 39.8), 1),
        "rr": random.randint(20, 28),
    }


def tachy_vitals() -> dict:
    # HR fluctuates around 110 threshold (105–155)
    return {
        "hr": random.randint(105, 155),
        "spo2": random.randint(93, 99),
        "temp_c": round(random.uniform(36.5, 37.8), 1),
        "rr": random.randint(18, 26),
    }


MODE_GENERATORS = {
    "normal": normal_vitals,
    "desat": desat_vitals,
    "fever": fever_vitals,
    "tachy": tachy_vitals,
}


def get_mode() -> str:
    try:
        resp = requests.get(f"{RELAY_URL}/mode", timeout=2)
        return resp.json().get("mode", "normal")
    except Exception:
        return "normal"


def run():
    print("Simulator started. Ctrl+C to stop.")
    while True:
        mode = get_mode()
        gen = MODE_GENERATORS.get(mode, normal_vitals)
        vitals = gen()
        vitals["ts"] = datetime.now(timezone.utc).isoformat()

        try:
            resp = requests.post(f"{RELAY_URL}/ingest", json=vitals, timeout=5)
            data = resp.json()
            decision = data.get("decision", {})
            print(
                f"[{mode:>7}] hr={vitals['hr']} spo2={vitals['spo2']} "
                f"temp={vitals['temp_c']} rr={vitals['rr']} "
                f"-> {decision.get('triage', '?')} ({decision.get('confidence', 0):.2f})"
            )
        except Exception as e:
            print(f"[error] {e}")

        time.sleep(2)


if __name__ == "__main__":
    run()
