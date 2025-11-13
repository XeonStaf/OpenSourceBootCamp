from fastapi import APIRouter, HTTPException

from src.api.schemas.query import Query
from src.api.schemas.response import TaskCreationResponse, TaskStatusResponse
from src.api.services.task_manager import task_manager

mode_router = APIRouter()


@mode_router.post("/get-mode")
async def enqueue_mode_detection(request: Query) -> TaskCreationResponse:
    task_id = await task_manager.create_task(request.query)
    return TaskCreationResponse(task_id=task_id)


@mode_router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> TaskStatusResponse:
    try:
        payload = await task_manager.get_task_payload(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    return TaskStatusResponse(**payload)
