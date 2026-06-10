# AI-Augmented Vulnerability Scanner

A self-hosted security scanning platform that combines **Nmap** with an **AI reasoning layer** (Ollama/Mistral 7B) to interpret results, chain findings into attack paths, and generate actionable intelligence.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│                  React + Recharts (Port 80)                  │
│         Dashboard ─ New Scan ─ Scan Detail                  │
│         Findings Table ─ Attack Chain Viz                   │
└──────────┬──────────────────────────────────────────────────┘
           │ /api/* proxy via nginx
           ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Port 8000)              │
│  POST /api/v1/scans/   → Create & launch scan              │
│  GET  /api/v1/scans/   → List scans with stats             │
│  GET  /api/v1/scans/:id → Scan detail                     │
│  GET  /api/v1/scans/:id/findings → Findings w/ AI data    │
│  GET  /api/v1/scans/:id/chains  → Attack chains           │
└──────┬──────────────────────────────────────────────────────┘
       │
       ├── Celery Worker ─── async scan orchestration
       │     ├── NmapScanner ─── XML parse → findings
       │     ├── RagService  ─── CVE knowledge base (ChromaDB)
       │     └── OllamaClient ── AI analysis → CVSS + chains
       │
       ├── PostgreSQL ─── scans, findings, attack_chains, audit_logs
       └── Redis ──────── Celery broker + result backend
```

## Data Flow: From Target to Actionable Intelligence

```
Step 1: User creates scan via API or Dashboard
        POST /api/v1/scans/ { target_scope, profile, authorized }
        └── Scope validated (CIDR check)
        └── Scan record created (status: "queued")
        └── Celery task dispatched

Step 2: Celery worker picks up the task
        └── Status → "running"
        └── Audit log: scan_started

Step 3: Nmap scans the target
        └── nmap -oX - -sV {profile_flags} {target_scope}
        └── XML parsed → structured findings [{host, port, service, version}]
        └── Status → findings extracted

Step 4: RAG service retrieves CVE context
        └── Matches services against built-in CVE knowledge base
        └── 17+ real CVEs (OpenSSH regreSSHion, HTTP/2 Rapid Reset, etc.)
        └── Returns: [{host, port, service, cve_contexts: [{cve, cvss, description}]}]

Step 5: Ollama (Mistral 7B) performs AI analysis
        └── Prompt: "You are a senior penetration tester..."
        └── Findings + CVE context sent to LLM
        └── AI returns structured JSON:

        {
          "findings": [{
            "host": "192.168.1.1",
            "port": 22,
            "cvss_score": 8.1,
            "severity": "high",
            "false_positive_reasoning": "...",
            "exploitation_notes": "...",
            "attack_chain_id": 1
          }],
          "attack_chains": [{
            "chain_id": 1,
            "description": "OpenSSH RCE → container escape",
            "hosts": ["192.168.1.1", "192.168.1.2"],
            "severity": "critical",
            "likelihood": "medium",
            "mitre_technique_id": "T1190"
          }]
        }

Step 6: Results persisted to PostgreSQL
        └── Findings stored with: severity, cvss_score, fp_reasoning, exploitation_notes
        └── Attack chains stored with: description, steps, severity, likelihood, MITRE ID
        └── Status → "completed"
        └── Audit log: scan_completed

Step 7: User views results in Dashboard
        └── Scan Detail page: findings table with CVSS bars, FP reasoning
        └── Attack Chains tab: visualized multi-step exploitation paths
        └── Auto-refresh while scan is running
```

## Quick Start

```bash
# 1. Start all services
docker compose up --build -d

# 2. Wait for migrations and Ollama model download (~2-5 minutes)

# 3. Open the dashboard
#    http://localhost:5173

# 4. Or use the API directly
#    http://localhost:8000/docs
#    http://localhost:8000
```

## Create a Scan (via PowerShell)

```powershell
$headers = @{"Content-Type" = "application/json"}
$body = @{
    target_scope = "127.0.0.1/32"
    profile = "normal"
    authorized = $true
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

Then visit `http://localhost:5173` to see results in the dashboard.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/scans/` | Launch a new scan |
| GET | `/api/v1/scans/` | List all scans (with finding/chain counts) |
| GET | `/api/v1/scans/{id}` | Get scan detail |
| GET | `/api/v1/scans/{id}/findings` | List findings with AI analysis |
| GET | `/api/v1/scans/{id}/chains` | List attack chains |
| GET | `/` | Service health check |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/api_v1/endpoints/   ← REST endpoints
│   │   ├── core/                    ← Config, Celery app
│   │   ├── db/                      ← SQLAlchemy models, session
│   │   ├── services/                ← NmapScanner, RagService, OllamaClient
│   │   ├── tasks/                   ← Celery scan task
│   │   ├── utils/                   ← Scope enforcement
│   │   ├── crud.py                  ← Database queries
│   │   ├── schemas.py               ← Pydantic models
│   │   └── main.py                  ← FastAPI app
│   ├── alembic/                     ← Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/              ← React components
│   │   │   ├── ScanDashboard.jsx    ← Stats + scan list
│   │   │   ├── NewScan.jsx          ← Scan creation form
│   │   │   ├── ScanDetail.jsx       ← Scan detail with tabs
│   │   │   ├── FindingsTable.jsx    ← AI-enriched findings
│   │   │   └── ChainsView.jsx       ← Attack chain visualization
│   │   ├── api.js                   ← API client
│   │   ├── App.jsx                  ← Router + layout
│   │   └── styles.css               ← Dark theme
│   ├── Dockerfile                   ← Multi-stage build + nginx
│   ├── nginx.conf                   ← API proxy + SPA routing
│   └── package.json
└── docker-compose.yml               ← Full stack orchestration
```

## Key Design Decisions

- **AI output is structured JSON, not keyword search** — the Ollama prompt instructs strict JSON output with CVSS scores, false positive reasoning, exploitation notes, and attack chains with MITRE ATT&CK IDs
- **CVE context via RAG** — built-in knowledge base of 17+ real CVEs matched by service/port, with ChromaDB support for semantic search when available
- **Attack chain persistence** — chains are stored in their own DB table with resolved finding references, severity, likelihood, and MITRE technique IDs
- **Scope enforcement** — CIDR-based subnet validation prevents scanning outside authorized ranges
- **Authorization guard** — scans require explicit `authorized: true` flag and are rejected without it
- **Full audit trail** — every scan action is logged (started, completed, failed, rejected) with timestamps
- **Async architecture** — async DB sessions throughout, Celery worker for long-running scans

## Next Steps (Future Work)

- [ ] Add JWT authentication and user management
- [ ] WebSocket real-time scan progress updates
- [ ] PDF/Markdown report generation (weasyprint + jinja2 in requirements)
- [ ] Nuclei scanner integration for CVE-specific probing
- [ ] False positive feedback loop (learning from user feedback)
- [ ] NVD/ChromaDB ingestion pipeline for up-to-date CVE data
- [ ] Service dependency graph visualization