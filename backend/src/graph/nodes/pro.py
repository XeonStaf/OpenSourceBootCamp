from src.graph.states.state import State


async def pro_mode(state: State):
    """Handles complex questions using the pro-mode researcher system"""

    # result = llm.ainvoke(state["input"])
    return {"output": f"Pro-mode!"}
