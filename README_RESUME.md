# EdgeFHIR Relay — Resume Notes

## What Works

- **Vitals Ingestion**: `POST /ingest` accepts HR, SpO2, Temp, RR, Motion
- **Rules-Based Triage**: Severity-weighted scoring with dynamic confidence (0.50–0.95)
- **FHIR R4 Bundling**: Collection bundles (Patient, Device, 4 Observations, Task) with LOINC codes
- **Store-and-Forward Outbox**: Filesystem queue with FIFO, quarantine, auto-retry on reconnect
- **Cloud Mock**: Receives and acknowledges bundles on port 9000
- **Simulator**: Mode-aware vitals generator (normal/desat/fever/tachy) polling every 2s
- **Dashboard UI**: Next.js + Tailwind with Summary/Structured toggle, live polling, mode buttons

## Local URLs

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| Relay API | http://127.0.0.1:8000 |
| Cloud Mock | http://127.0.0.1:9000 |

## How to Resume

```bash
cd ~/edgefhir-relay
source .venv/bin/activate

# Start services (3 terminals)
uvicorn cloud_mock.cloud:app --port 9000
uvicorn app.main:app --port 8000
python -m simulator.stream

# Start UI (4th terminal)
cd ui && npm run dev
```

## Where We Left Off

- All backend endpoints functional and tested
- UI dashboard complete with Summary/Structured views
- LOINC codes updated to clinical standards (2708-1, 8310-5, 8867-4, 9279-1)
- Outbox retry manager wired into connectivity toggle
- README.md and docs/screenshots/ directory created (screenshots not yet captured)

## Potential Next Steps

- Capture dashboard screenshots for README
- Add unit tests (pytest)
- WebSocket for real-time UI updates instead of polling
- Docker Compose for single-command startup
