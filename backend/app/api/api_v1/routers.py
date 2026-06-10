from fastapi import APIRouter
from app.api.api_v1.endpoints import scans

api_router = APIRouter()
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
