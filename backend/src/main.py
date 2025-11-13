import uvicorn
from fastapi import APIRouter, FastAPI
from src.api.api import api_router

root_router = APIRouter()


def prepare_app() -> FastAPI:
    app = FastAPI(title="Researcher")
    app.include_router(api_router)
    app.include_router(root_router)
    return app

app = prepare_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
