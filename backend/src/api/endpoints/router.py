from fastapi import APIRouter

from src.api.schemas.query import Query
from src.api.schemas.response import Mode
from src.graph.graph import router_workflow

mode_router = APIRouter()


@mode_router.post("/get-mode")
async def get_mode(request: Query) -> Mode:
    state = router_workflow.invoke({"input": request.query})
    return Mode(mode=state["decision"])
