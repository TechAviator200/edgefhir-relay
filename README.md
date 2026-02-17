# EdgeFHIR Relay + Triage Agent

A simulated edge-to-cloud healthcare gateway that ingests patient vitals, applies rules-based triage, generates FHIR R4 bundles, and forwards them to a cloud endpoint with offline store-and-forward capability.

## Architecture

```
Simulator ──► Relay (FastAPI :8000) ──► Cloud Mock (:9000)
                 │                          ▲
                 │  Triage Agent             │
                 │  FHIR Bundler             │
                 ▼                           │
              Outbox/ ──────────────────────►┘
            (offline queue)         (flush on reconnect)
```

## Quick Start

```bash
# Terminal 1 — Cloud Mock
source .venv/bin/activate
uvicorn cloud_mock.cloud:app --port 9000

# Terminal 2 — Relay
source .venv/bin/activate
uvicorn app.main:app --port 8000

# Terminal 3 — Simulator
source .venv/bin/activate
python -m simulator.stream

# Terminal 4 — Dashboard
cd ui && npm run dev
```

## Technical Highlights

- **FHIR R4 Bundles**: Collection bundles with Patient, Device, 4 LOINC-coded Observations, and a Task resource
- **Rules-Based Triage**: Severity-weighted scoring (SpO2, HR, Temp, RR) with dynamic confidence 0.50–0.95
- **Store-and-Forward Outbox**: Filesystem-based queue with FIFO ordering, quarantine for malformed payloads, and auto-retry on reconnect
- **Real-Time Dashboard**: Next.js + Tailwind polling UI with Summary/Structured toggle
- **Simulation Modes**: Normal, Desat, Fever, Tachy — switchable live via UI or API

## System in Action

<div align="center">

### Healthy Baseline (Normal Mode)

The dashboard during normal operations — vitals within range, triage returns "ok" with low confidence, and the relay generates a standard Collection bundle routed directly to the cloud.

<img src="./docs/screenshots/summary_normal.png" alt="Summary View - Normal Vitals" width="800" />

---

### Critical Alert (Desat Event)

A desaturation event triggers elevated triage. SpO2 drops below 92%, confidence rises based on severity, and the FHIR bundle includes a Task resource with priority "asap" for immediate clinical intervention.

<img src="./docs/screenshots/structured_desat.png" alt="Structured View - Desat Event" width="800" />

</div>

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness check |
| `GET` | `/status` | Agent status + outbox count |
| `GET` | `/history` | Rolling vitals history (200 max) |
| `GET` | `/mode` | Current simulation mode |
| `POST` | `/ingest` | Receive vitals, triage, bundle, store/forward |
| `POST` | `/simulate/{mode}` | Set mode (normal/desat/fever/tachy, 30s TTL) |
| `POST` | `/connectivity/{on\|off}` | Toggle connectivity + auto-retry |
| `POST` | `/flush` | Manually flush outbox to cloud |

## Security Posture & Boundaries

[![CI](https://github.com/TechAviator200/edgefhir-relay/actions/workflows/ci.yml/badge.svg)](https://github.com/TechAviator200/edgefhir-relay/actions/workflows/ci.yml)
[![Security](https://github.com/TechAviator200/edgefhir-relay/actions/workflows/security.yml/badge.svg)](https://github.com/TechAviator200/edgefhir-relay/actions/workflows/security.yml)
[![CodeQL](https://github.com/TechAviator200/edgefhir-relay/actions/workflows/codeql.yml/badge.svg)](https://github.com/TechAviator200/edgefhir-relay/actions/workflows/codeql.yml)

This is a **demo/simulator repository** — not a production EHR deployment. All patient data is synthetic.

**Automated checks** run on every push and pull request:
- **Gitleaks** — secret scanning
- **pip-audit** — Python dependency vulnerabilities
- **Bandit** — Python static security analysis
- **npm audit** — Node dependency vulnerabilities
- **CodeQL** — semantic code analysis (Python + JavaScript/TypeScript)
- **Dependabot** — weekly dependency update PRs

**Out of scope** for this portfolio demo (required for production): HIPAA/SOC 2 compliance controls, cryptographic key management, per-tenant isolation, mTLS, and audit logging. See [docs/security.md](docs/security.md) for the full threat model and hardening roadmap.

## Project Structure

```
edgefhir-relay/
├── app/
│   ├── main.py        # FastAPI endpoints
│   ├── agent.py       # Triage logic + FHIR bundle assembly
│   ├── fhir.py        # FHIR R4 resource generators
│   ├── schemas.py     # Pydantic models (Vitals, Decision, AgentOutput)
│   ├── state.py       # In-memory state (thread-safe)
│   ├── storage.py     # Outbox: write, flush, quarantine, retry
│   └── config.py      # Pydantic Settings
├── cloud_mock/
│   └── cloud.py       # Mock cloud FHIR receiver
├── simulator/
│   └── stream.py      # Mode-aware vitals generator
├── ui/                 # Next.js + Tailwind dashboard
├── outbox/             # Filesystem queue (auto-created)
└── docs/screenshots/   # Dashboard screenshots
```
