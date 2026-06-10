from fastapi import FastAPI

from app.api.api_v1.routers import api_router
from app.core.config import settings

app = FastAPI(
    title="AI-Augmented Vulnerability Scanner",
    version="0.1.0",
    description="FastAPI backend for AI-augmented scan orchestration and analysis.",
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": "ai-augmented-vuln-scanner",
        "version": settings.project_name,
        "status": "ready",
    }
