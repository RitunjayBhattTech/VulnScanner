# 🔬 VulnAI Scanner

**AI-Powered Vulnerability Assessment Platform**

VulnAI Scanner wraps traditional security scanning primitives (nmap, Semgrep, Nuclei, web crawlers) with a Claude LLM reasoning layer for intelligent triage, false-positive filtering, remediation advice, and natural-language reporting.

## Key Differentiators

| Feature | VulnAI | Traditional Scanners |
|---------|--------|---------------------|
| **LLM Triage** | Contextualises findings by network topology, not just CVSS | Raw CVSS scores only |
| **RAG Pipeline** | Queries live CVE/CWE knowledge base per finding | No context enrichment |
| **AI Remediation** | Actual code diffs and config patches | Generic text advice |
| **Delta Diffing** | Shows new/fixed/regressed since last scan | No historical comparison |
| **False Positive Filter** | AI classifies FP probability per finding | Manual review required |

```
┌─────────────────────────────────────────────────────┐
│                    Scan Pipeline                      │
│                                                       │
│  Pre-flight → Discovery → Enumeration → Detection    │
│     (Auth)     (nmap)     (Crawler)   (Nuclei,       │
│                                        Headers, SSL, │
│                                        Semgrep)      │
│                                                       │
│  Detection → AI Processing → Delta → Summary → Done  │
│              (FP Filter,     (Diff)   (LLM)          │
│               Triage,                                 │
│               Remediation)                            │
└─────────────────────────────────────────────────────┘
```

## Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Docker & Docker Compose** (for containerized setup)
- **nmap** (for port scanning)
- **nuclei** (for vulnerability template scanning)
- **semgrep** (for SAST scanning)

## Quick Start (Docker Compose)

```bash
# Clone the repository
git clone https://github.com/yourusername/vulnai-scanner.git
cd vulnai-scanner

# Copy environment config
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start all services
docker-compose up -d

# Seed the knowledge base
docker-compose exec backend python scripts/seed_knowledge_base.py

# Access the application
open http://localhost:5173
```

## Manual Setup

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Seed knowledge base
python scripts/seed_knowledge_base.py

# Start backend
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

### Development Script

```bash
chmod +x scripts/run_dev.sh
./scripts/run_dev.sh
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Anthropic Claude API key |
| `SECRET_KEY` | Yes | - | Secret for signing audit tokens |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./vulnai.db` | Database connection string |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis for Celery |
| `NVD_API_KEY` | No | - | NVD API key (higher rate limits) |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB persistence directory |
| `MAX_SCAN_RATE` | No | `10` | Max outbound requests/second |
| `ENABLE_POC_GENERATION` | No | `false` | Enable AI PoC generation |
| `CORS_ORIGINS` | No | `["http://localhost:5173"]` | Allowed CORS origins |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/scans` | Create and queue a scan |
| `GET` | `/api/scans` | List all scans |
| `GET` | `/api/scans/{id}` | Get scan details |
| `GET` | `/api/scans/{id}/status` | Poll scan status |
| `DELETE` | `/api/scans/{id}/cancel` | Cancel a running scan |
| `GET` | `/api/findings?scan_id={id}` | List findings for a scan |
| `GET` | `/api/findings/{id}` | Get finding details |
| `PATCH` | `/api/findings/{id}` | Update finding (analyst workflow) |
| `GET` | `/api/reports/{scan_id}/pdf` | Download PDF report |

## Security Features

### Authorisation Gate
Every scan **requires** explicit confirmation that the user has written authorisation. This is enforced at the API level (not just the UI). Without `authorisation_confirmed=true`, the pipeline will not execute.

### Scope Enforcement
The scope validator runs before every outbound request. It checks:
- **IP targets**: Falls within declared CIDR ranges
- **Domain targets**: Matches or is a subdomain of declared domains
- Raises `ScopeViolationError` for any out-of-scope target

### Audit Logging
Every scan action writes an immutable audit log entry:
- Who initiated the scan
- When the scan was created/started/completed/failed
- Declared scope
- Authorisation confirmation token (SHA256 hash)

### Rate Limiting
All outbound requests are rate-limited via a token bucket algorithm. Default: 10 requests/second. Nmap runs in polite mode (`-T2`).

### Credential Security
- No API keys hardcoded in source code
- All secrets loaded from environment variables
- `.env` file is in `.gitignore`

### PoC Generation
The PoC generation feature is **disabled by default**. Enable it only with `ENABLE_POC_GENERATION=true` and only in authorised testing environments.

## Project Structure

```
vulnai-scanner/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py              # Settings via pydantic-settings
│   ├── database.py            # SQLAlchemy async engine
│   ├── models/                # ORM models (Scan, Finding, AuditLog, User)
│   ├── schemas/               # Pydantic schemas
│   ├── api/routes/            # API endpoints
│   ├── core/                  # Security, rate limiter, exceptions
│   ├── scanners/              # nmap, Nuclei, Semgrep, etc.
│   ├── ai/                    # Claude client, RAG, triage, etc.
│   ├── knowledge/             # ChromaDB vector store, ingesters
│   ├── pipeline/              # Orchestrator, delta engine, Celery tasks
│   ├── reporting/             # PDF report generator
│   └── tests/                 # pytest test suite
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Route pages
│   │   ├── hooks/             # React Query hooks
│   │   ├── types/             # TypeScript definitions
│   │   └── api/               # API client
│   └── ...
├── .github/workflows/         # CI/CD pipeline
├── scripts/                   # Utility scripts
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile.backend         # Backend Dockerfile
├── Dockerfile.frontend        # Frontend Dockerfile
└── README.md
```

## Testing

```bash
cd backend
pytest -v

# Run specific test file
pytest tests/test_scope_validator.py -v
pytest tests/test_delta_engine.py -v
```

## 📜 Legal Disclaimer

> **This tool is for authorised security testing only.**
>
> The authors are not responsible for misuse of this software. Always obtain **written permission** from the system owner before scanning any system you do not own.
>
> Unauthorised scanning may violate:
> - Computer Fraud and Abuse Act (CFAA) in the US
> - Computer Misuse Act in the UK
> - Equivalent laws in other jurisdictions
>
> By using this software, you agree to use it only for lawful purposes and only on systems you have explicit authorisation to test.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - See LICENSE file for details.