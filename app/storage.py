import json
import logging
import os
import time
from pathlib import Path

import requests

from app.config import settings
from app import state

logger = logging.getLogger(__name__)


def ensure_outbox(outbox_dir: str = settings.OUTBOX_DIR) -> None:
    Path(outbox_dir).mkdir(parents=True, exist_ok=True)


def list_outbox_files(outbox_dir: str = settings.OUTBOX_DIR) -> list[str]:
    ensure_outbox(outbox_dir)
    files = sorted(f for f in os.listdir(outbox_dir) if f.endswith(".json"))
    state.set_outbox_count(len(files))
    return files


def write_outbox(outbox_dir: str = settings.OUTBOX_DIR, payload: dict = None) -> str:
    ensure_outbox(outbox_dir)
    filename = f"{int(time.time() * 1000)}.json"
    filepath = os.path.join(outbox_dir, filename)
    with open(filepath, "w") as f:
        json.dump(payload, f)
    list_outbox_files(outbox_dir)
    return filename


def _quarantine(outbox_dir: str, filename: str) -> None:
    """Move malformed files out of the queue so they don't block FIFO processing."""
    bad_dir = os.path.join(outbox_dir, ".quarantine")
    Path(bad_dir).mkdir(exist_ok=True)
    src = os.path.join(outbox_dir, filename)
    dst = os.path.join(bad_dir, filename)
    os.rename(src, dst)
    logger.warning("Quarantined malformed file: %s", filename)


def flush_to_cloud(outbox_dir: str = settings.OUTBOX_DIR) -> dict:
    """Forward outbox files in FIFO order. Malformed files are quarantined."""
    files = list_outbox_files(outbox_dir)
    sent = 0
    failed = 0

    for filename in files:
        filepath = os.path.join(outbox_dir, filename)

        # Parse — quarantine if malformed
        try:
            with open(filepath) as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Malformed outbox file %s: %s", filename, e)
            _quarantine(outbox_dir, filename)
            failed += 1
            continue

        # Transmit — leave in queue on network failure for next retry
        try:
            resp = requests.post(settings.CLOUD_URL, json=payload, timeout=3)
            resp.raise_for_status()
            os.remove(filepath)
            sent += 1
        except Exception as e:
            logger.error("Failed to send %s: %s", filename, e)
            failed += 1

    remaining = len(list_outbox_files(outbox_dir))
    return {"sent": sent, "failed": failed, "remaining": remaining}


def retry_on_reconnect(outbox_dir: str = settings.OUTBOX_DIR) -> dict | None:
    """Called when connectivity toggles ON. Flushes pending outbox if any."""
    files = list_outbox_files(outbox_dir)
    if not files:
        return None
    logger.info("Connectivity restored — retrying %d queued bundles", len(files))
    return flush_to_cloud(outbox_dir)
