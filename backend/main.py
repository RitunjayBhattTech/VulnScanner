import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.database import create_all_tables
from backend.core.exceptions import VulnAIException, AuthorisationRequiredError, ScopeViolationError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info("Starting VulnAI Scanner backend...")

    # Validate required env vars
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY is not set. AI features will be disabled.")
    if settings.SECRET_KEY == "change_this_to_a_random_256_bit_secret":
        logger.warning("SECRET_KEY is still the default. Change it in production.")

    # Create database tables
    try:
        await create_all_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.warning(f"Could not create database tables: {e}")

    yield

    logger.info("Shutting down VulnAI Scanner backend...")


app = FastAPI(
    title="VulnAI Scanner",
    description="AI-powered vulnerability assessment platform with LLM triage and RAG pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Exception handlers
@app.exception_handler(VulnAIException)
async def vulnai_exception_handler(request: Request, exc: VulnAIException):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(AuthorisationRequiredError)
async def auth_exception_handler(request: Request, exc: AuthorisationRequiredError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(ScopeViolationError)
async def scope_exception_handler(request: Request, exc: ScopeViolationError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


# Import and register routers
from backend.api.routes.health import router as health_router
from backend.api.routes.scans import router as scans_router
from backend.api.routes.findings import router as findings_router
from backend.api.routes.reports import router as reports_router

app.include_router(health_router)
app.include_router(scans_router)
app.include_router(findings_router)
app.include_router(reports_router)


@app.get("/")
async def root():
    return {
        "service": "VulnAI Scanner",
        "version": "1.0.0",
        "status": "ready",
    }