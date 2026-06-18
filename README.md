<div align="center">
  <br/>
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version 1.0.0"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"/>
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/react-18-blue" alt="React 18"/>
  <br/>
  <h1>🔬 VulnAI Scanner</h1>
  <p>
    <strong>AI-Powered Vulnerability Assessment Platform</strong><br/>
    <em>Intelligent scanning. LLM triage. Automated remediation.</em>
  </p>
  <p>
    <a href="#-key-differentiators">Features</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-quick-start-docker">Quick Start</a> •
    <a href="#-api-endpoints">API</a> •
    <a href="#-environment-variables">Configuration</a> •
    <a href="#-legal-disclaimer">Legal</a>
  </p>
  <br/>
</div>

---

VulnAI Scanner wraps traditional security scanning primitives (nmap, Semgrep, Nuclei, HTTP analysis) with an **LLM reasoning layer** (Ollama or Anthropic Claude) that provides intelligent triage, false-positive filtering, contextual remediation advice, and natural-language executive summaries. Findings are enriched via a **RAG pipeline** against live CVE/CWE/OWASP knowledge bases stored in ChromaDB.

## ✨ Key Differentiators

| Capability | VulnAI | Traditional Scanners |
|-----------|--------|---------------------|
| **LLM Triage** | Contextualises findings by network topology, attack surface, and exploitability | Raw CVSS scores only, no context |
| **RAG Knowledge** | Queries live CVE/CWE/OWASP vector store per finding — matches real exploit patterns | No enrichment; static signature matching |
| **AI Remediation** | Generates specific code diffs, config patches, and verification commands per tech stack | Generic textbook advice |
| **False Positive Filter** | LLM classifies FP probability (0.0–1.0) with reasoning — auto-skips likely FPs | Manual review required for every finding |
| **Delta Diffing** | Shows new / fixed / regressed findings by comparing against previous scan | No historical comparison |
| **PDF Reports** | Professional report with cover page, severity bar, executive summary, full findings, audit log | Raw HTML or no report |

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VULNAI SCANNER PIPELINE                         │
│                                                                         │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌──────────────────┐   │
│  │Pre-flight│──▶│Discovery │──▶│Enumeration│──▶│   Detection       │   │
│  │ (Auth    │   │ (nmap    │   │ (Crawler  │   │ ┌────┐ ┌───────┐  │   │
│  │  Check)  │   │  Ports)  │   │  URLs)    │   │ │Nuc.│ │Hdrs.  │  │   │
│  └──────────┘   └──────────┘   └───────────┘   │ │SSL │ │Semgr.│  │   │
│                                                  │ └────┘ └───────┘  │   │
│                                                  └────────┬─────────┘   │
│                                                           │              │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌────────▼─────────┐   │
│  │Finalise  │◀──│ Summary  │◀──│   Delta   │◀──│   AI Processing   │   │
│  │(Complete │   │ (LLM     │   │ (Diff vs  │   │ ┌────┐ ┌──────┐  │   │
│  │ / Failed)│   │  Report) │   │ Previous) │   │ │FP  │ │Triage│  │   │
│  └──────────┘   └──────────┘   └───────────┘   │ │Rem.│ │RAG   │  │   │
│                                                  │ └────┘ └──────┘  │   │
│                                                  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────┐   ┌─────────────────────────┐
│     Frontend (React)   │   │    Backend (FastAPI)     │
│  ┌──────────────────┐  │   │  ┌───────────────────┐  │
│  │  Dashboard       │  │   │  │ REST API          │  │
│  │  Scan Detail     │──┼───┼──│ Scan Orchestrator │  │
│  │  Findings View   │  │   │  │ PDF Generator     │  │
│  │  PDF Download    │  │   │  │ RAG Pipeline      │  │
│  └──────────────────┘  │   │  └───────────────────┘  │
│  Port: 5173 (Vite)     │   │  Port: 8000 (uvicorn)    │
└────────────────────────┘   └─────────────────────────┘
                                     │          │
                            ┌────────▼──┐ ┌────▼────┐
                            │  Redis    │ │ChromaDB │
                            │ (Celery   │ │(Vector  │
                            │  Queue)   │ │ Store)  │
                            └───────────┘ └─────────┘
```

## 🚀 Quick Start (Docker)

### Prerequisites

- Docker & Docker Compose v2+
- Ollama (on **host** machine — runs outside Docker)

### Step 1 — Pull the LLM model

```powershell
# Windows (PowerShell)
ollama pull llama3.2:3b
```

### Step 2 — Configure environment

```powershell
cp .env.example .env
# Edit .env — at minimum set these:
#   OLLAMA_MODEL=llama3.2:3b
#   LLM_PROVIDER=ollama
```

### Step 3 — Launch the stack

```powershell
docker compose build backend worker --no-cache
docker compose up -d
```

This starts 5 services:
| Service | Port | Purpose |
|---------|------|---------|
| `redis` | 6379 | Celery task queue |
| `chromadb` | 8001 | Vector store for CVE/CWE knowledge |
| `backend` | 8000 | FastAPI REST API |
| `worker` | — | Celery worker (executes scans asynchronously) |
| `frontend` | 5173 | React dashboard (Vite dev server) |

### Step 4 — Access the UI

Open **http://localhost:5173** in your browser. From the dashboard you can:
- View scan statistics and charts
- Start a new scan with configurable scan types
- Browse all scans with status, findings counts, and dates
- Click any scan to see detailed findings with AI triage and remediation
- Download professional PDF reports

### Step 5 — Try demo mode

Click the **"⚡ View Demo"** button on the dashboard to load 8 pre-populated realistic findings including SQL injection, XSS, exposed admin panels, and SSL issues — no scan required.

## 🔧 Manual Setup

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Seed the knowledge base (CVE/CWE/OWASP vectors)
python scripts/seed_knowledge_base.py

# Start API server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# In a separate terminal, start Celery worker
celery -A backend.pipeline.tasks worker --loglevel=info -Q scans
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📋 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | Yes | `ollama` | LLM provider: `ollama`, `anthropic`, `groq`, `gemini` |
| `OLLAMA_MODEL` | Yes* | `llama3.2:3b` | Ollama model name (only used with `ollama` provider) |
| `OLLAMA_BASE_URL` | Yes* | `http://host.docker.internal:11434` | Ollama server URL |
| `ANTHROPIC_API_KEY` | Yes* | — | Claude API key (only used with `anthropic` provider) |
| `SECRET_KEY` | Yes | — | 256-bit secret for signing audit tokens |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./vulnai.db` | Database connection string |
| `REDIS_URL` | No | `redis://redis:6379/0` | Redis for Celery task queue |
| `CHROMA_HOST` | No | `chromadb` | ChromaDB server hostname |
| `CHROMA_PORT` | No | `8001` | ChromaDB server port |
| `NVD_API_KEY` | No | — | NVD API key (higher rate limits for CVE ingestion) |
| `MAX_SCAN_RATE` | No | `10` | Max outbound HTTP requests/second |
| `CORS_ORIGINS` | No | `["http://localhost:5173"]` | Allowed CORS origins for frontend |
| `ANONYMIZED_TELEMETRY` | No | `False` | Disable ChromaDB telemetry |

*\* Required when using the corresponding LLM provider*

## 📡 API Endpoints

### Scans

```http
POST /api/scans                     # Create and queue a new scan
GET  /api/scans                     # List all scans
GET  /api/scans/{id}                # Get scan details
GET  /api/scans/{id}/status         # Poll scan status (pending/running/completed/failed)
DELETE /api/scans/{id}/cancel       # Cancel a running scan
```

### Findings

```http
GET   /api/findings?scan_id={id}    # List findings for a scan
GET   /api/findings/{id}            # Get finding details
PATCH /api/findings/{id}            # Update finding (e.g. mark as FP)
```

### Reports

```http
GET   /api/reports/{scan_id}/pdf    # Download PDF security assessment report
```

### Demo Mode (no scan required)

```http
GET   /api/demo/scan                # Returns pre-populated scan with 8 findings
GET   /api/demo/findings            # Returns 8 realistic findings with AI triage
GET   /api/demo/summary             # Returns dashboard statistics
```

### System

```http
GET   /api/health                   # Health check — returns { status: "healthy" }
GET   /                             # Root — returns service info
```

### Example: Start a scan

```powershell
$body = @{
    target = "http://testphp.vulnweb.com"
    scope = @("testphp.vulnweb.com")
    scan_types = @("port", "web", "headers", "ssl")
    authorisation_confirmed = $true
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/scans" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

Write-Host "Scan ID: $($response.id)"
```

## 🛡 Security Features

### Authorisation Gate
Every scan **requires** explicit confirmation (`authorisation_confirmed=true`). Without this, the pipeline refuses to execute. This is enforced at the API level — not just the UI.

### Scope Enforcement
The scope validator runs before every outbound request. It checks:
- **IP targets**: Falls within declared CIDR ranges (e.g. `10.0.0.0/8`)
- **Domain targets**: Exact match, subdomain match, or wildcard (`*.example.com`)
- **DNS resolution**: Resolves hostnames and checks resolved IP against CIDR scopes
- Returns `403 ScopeViolationError` for any out-of-scope target

### Audit Logging
Every scan action writes an immutable audit log entry with:
- Timestamp, actor, action type
- Target, scope, scan configuration
- Authorisation confirmation status
- Error details on failure

### Rate Limiting
- Token bucket algorithm: default 10 req/s
- nmap runs in polite mode (`-T2`) with limited port range
- Playwright replaced with lightweight httpx crawler

### LLM Fallbacks
All AI components have safe defaults:
- **Triage**: Returns default `TriagedFinding` with `recommended_priority=5` on LLM failure
- **FP Filter**: Returns `probability=0.1` on failure
- **Remediation**: Returns structured guidance text on failure
- **PDF**: Returns error PDF with message instead of crashing the API

## 🧪 Running Tests

```bash
cd backend
pytest -v

# Specific test suites
pytest tests/test_scope_validator.py -v
pytest tests/test_delta_engine.py -v
pytest tests/test_triage_agent.py -v
pytest tests/test_port_scanner.py -v
```

## 📁 Project Structure

```
vulnai-scanner/
├── backend/
│   ├── main.py                    # FastAPI entry point + middleware
│   ├── config.py                  # pydantic-settings configuration
│   ├── database.py                # SQLAlchemy async engine
│   ├── models/                    # ORM: Scan, Finding, AuditLog
│   ├── schemas/                   # Pydantic: RawFinding, TriagedFinding, etc.
│   ├── api/routes/                # REST endpoints (scans, findings, reports, demo)
│   ├── core/                      # Security, scope validator, rate limiter
│   ├── scanners/                  # nmap, Nuclei, SSL, headers, web crawler
│   ├── ai/                        # LLM client, triage agent, FP filter, remediation
│   ├── knowledge/                 # ChromaDB vector store + CVE/CWE/OWASP ingesters
│   ├── pipeline/                  # Orchestrator, delta engine, Celery tasks
│   ├── reporting/                 # ReportLab PDF generator
│   └── tests/                     # pytest test suite
├── frontend/
│   ├── src/
│   │   ├── components/            # FindingCard, Dashboard, Sidebar, etc.
│   │   ├── pages/                 # HomePage, ScanPage, ScansList, Findings
│   │   ├── hooks/                 # useScans, useFindings
│   │   ├── types/                 # TypeScript interfaces
│   │   └── api/                   # Axios API client
│   ├── tailwind.config.ts
│   └── vite.config.ts
├── scripts/                       # Knowledge base seed, run dev, test scripts
├── docker-compose.yml             # 5-service Docker Compose
├── Dockerfile.backend             # Python + Go + nuclei image
├── Dockerfile.frontend            # Nginx-served React build
└── README.md
```

## 🐛 Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `playwright install chromium --with-deps` fails | Docker build can't install large Chromium deps | Removed Playwright — crawler now uses `httpx` instead |
| Dashboard shows 0 findings | Scan counts not saved to DB | Orchestrator now calls `_update_scan_counts()` after AI processing |
| "greenlet_spawn has not been called" error | Missing `await` on DB call | All `db.execute()`, `db.commit()` now properly awaited |
| Scans fail on non-TryHackMe sites | Strict scope validator rejecting resolved IPs | Scope validator now resolves hostnames and allows CIDR matching |
| Frontend shows blank black screen | `t.reduce is not a function` — API returns `{scans:[...]}` not `[]` | API client now returns plain arrays; ErrorBoundary catches crashes |
| Tailwind styles not applied | PurgeCSS removes unused classes | All styles moved to inline `style={}` objects — no Tailwind class dependency |
| ChromaDB telemetry errors in logs | Default telemetry enabled | Disabled with `CHROMA_TELEMETRY=False` and `anonymized_telemetry=False` |

## 📜 Legal Disclaimer

> **⚠️ IMPORTANT — READ BEFORE USE**
>
> This tool is designed exclusively for **authorised security testing**. Unauthorised use may violate:
>
> - **United States**: Computer Fraud and Abuse Act (CFAA)
> - **United Kingdom**: Computer Misuse Act 1990
> - **European Union**: GDPR Article 32 (security testing requires authorisation)
> - **Other jurisdictions**: Equivalent computer crime laws
>
> By using this software, you **must**:
> 1. Obtain **written authorisation** from the system owner before scanning
> 2. Define the scope precisely in the scan configuration
> 3. Never scan targets outside the declared scope
> 4. Handle findings and reports as confidential information
>
> The authors provide this software as-is for legitimate security research and authorised testing only. They assume **no liability** for any damages arising from misuse.

## 🤝 Contributing

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'feat: add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Conventions

- **Backend**: Python 3.11+, async/await throughout, SQLAlchemy 2.0 async, pydantic v2
- **Frontend**: React 18, TypeScript strict mode, inline styles (no Tailwind), Recharts for charts
- **Scanners**: Each scanner extends `BaseScanner` and returns `List[RawFinding]`
- **AI**: All AI components have try/except with safe default return values
- **Testing**: pytest for backend, at minimum test scope validation and delta engine

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Built with ❤️ for security researchers and red teams</sub>
</div>