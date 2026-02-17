# Security

This document describes the security posture, threat model, and production hardening roadmap for EdgeFHIR Relay.

## Scope

EdgeFHIR Relay is a **portfolio demonstration** of an edge-to-cloud healthcare gateway. It processes **simulated** vitals data, not real patient information. The cloud endpoint (`cloud_mock/`) is a local stub, not a production EHR or FHIR server.

## Trust Boundaries

```
                  ┌─ UNTRUSTED ──────────────┐
                  │  simulator/stream.py      │
                  │  (generates fake vitals)  │
                  └──────────┬────────────────┘
                             │ POST /ingest
                  ┌──────────▼────────────────┐
                  │  app/ (FastAPI relay)      │
                  │  - validates via Pydantic  │
                  │  - triage + FHIR bundling  │
                  │  - writes to outbox/       │
                  └──────────┬────────────────┘
                             │ POST /receive
                  ┌──────────▼────────────────┐
                  │  cloud_mock/ (stub)        │
                  │  NON-PROD receiver         │
                  └───────────────────────────┘
```

- **Simulator input is untrusted.** The relay validates incoming vitals with Pydantic schemas before processing.
- **cloud_mock is non-production.** It accepts any well-formed payload. A real deployment would require mutual TLS, OAuth 2.0, and server-side validation.
- **The UI polls the relay API.** It renders data from the relay; it does not mutate state beyond simulation mode toggles.

## Secrets Handling

- **No secrets, tokens, or credentials are committed to this repository.**
- `.env` and `.env.*` are gitignored.
- CI uses `GITHUB_TOKEN` (auto-provisioned) only; no additional secrets are required.
- Gitleaks runs on every push and pull request to detect accidental secret commits.

## Outbox Storage Risks

The `outbox/` directory stores JSON files on the local filesystem as a store-and-forward queue.

- **In this demo**, outbox files contain simulated (synthetic) data only.
- **In a real deployment**, outbox files would contain PHI and must be:
  - Encrypted at rest (filesystem-level or application-level encryption)
  - Access-controlled (strict file permissions, dedicated service account)
  - Purged on successful delivery with auditable retention policies
  - Monitored for quarantine buildup (malformed payload alerts)

The `outbox/` directory is gitignored to prevent accidental commits of queue data.

## Automated Security Checks

| Check | Tool | Trigger |
|-------|------|---------|
| Secret scanning | Gitleaks | push, pull_request |
| Python dependency vulnerabilities | pip-audit | push, pull_request |
| Python static security analysis | Bandit | push, pull_request |
| Node dependency vulnerabilities | npm audit | push, pull_request |
| Semantic code analysis | GitHub CodeQL | push, pull_request, weekly |
| Dependency update PRs | Dependabot | weekly |

## Production Hardening Roadmap

The following controls are **out of scope** for this portfolio demo but would be required for a production deployment handling real PHI:

### Authentication & Authorization
- OAuth 2.0 / SMART on FHIR for API access
- mTLS between edge relay and cloud endpoint
- RBAC for dashboard access

### Audit & Compliance
- Immutable audit log for all ingest, triage, and forward events
- HIPAA audit trail requirements (access logging, breach detection)
- SOC 2 Type II control evidence

### Encryption
- TLS 1.3 for all network traffic
- Encryption at rest for outbox queue and any persistent stores
- Key management via HSM or cloud KMS

### Multi-Tenancy & Isolation
- Per-tenant data partitioning
- Network segmentation between edge nodes
- Tenant-scoped API keys and rate limiting

### Observability
- Structured logging with correlation IDs
- Metrics (latency, error rates, queue depth) exported to monitoring stack
- Alerting on quarantine growth, delivery failures, and anomalous triage patterns

### Supply Chain
- Pin all dependency versions (already done for pip; lock file for npm)
- SBOM generation for deployment artifacts
- Container image scanning if Dockerized
