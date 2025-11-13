from fastapi import APIRouter

from src.api.schemas.query import Query
from src.api.schemas.response import Answer, Mode
from src.graph.graph import router_workflow

mode_router = APIRouter()


@mode_router.post("/get-mode")
async def get_mode(request: Query) -> Mode:
    state = router_workflow.invoke({"input": request.query})
    return Mode(mode=state["decision"])


@mode_router.post("/answer")
async def answer(request: Query) -> Answer:
    state = router_workflow.invoke({"input": request.query})
    return Answer(answer=state["output"], router=state["decision"])
