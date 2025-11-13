from fastapi import APIRouter

from src.api.schemas.query import Query
from src.api.schemas.response import Answer
from src.graph.graph import router_workflow

answer_router = APIRouter()


@answer_router.post("/answer")
async def answer(request: Query) -> Answer:
    state = router_workflow.invoke({"input": request.query})
    return Answer(answer=state["output"], router=state["decision"])
