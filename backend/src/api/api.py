from fastapi import APIRouter

from src.api.endpoints.answer import answer_router
from src.api.endpoints.router import mode_router

api_router = APIRouter()

api_router.include_router(mode_router, prefix="/debug", tags=["debug"])
api_router.include_router(answer_router, tags=["answer"])
