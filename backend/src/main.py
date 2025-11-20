import logging

import uvicorn
from fastapi import APIRouter, FastAPI

from src.api.api import api_router
from src.config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

root_router = APIRouter()


def prepare_app() -> FastAPI:
    logger.info("Initializing FastAPI application...")
    app = FastAPI(title="Researcher")
    app.include_router(api_router)
    app.include_router(root_router)
    logger.info("FastAPI application initialized")
    return app


app = prepare_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
