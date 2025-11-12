from fastapi import APIRouter, FastAPI

from src.api.api import api_router

root_router = APIRouter()
app = FastAPI(title="Researcher")

app.include_router(api_router)
app.include_router(root_router)
