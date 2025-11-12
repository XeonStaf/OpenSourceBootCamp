from fastapi import APIRouter

from src.api.endpoints.router import mode_router

api_router = APIRouter()

api_router.include_router(mode_router, prefix="/debug", tags=["debug"])
