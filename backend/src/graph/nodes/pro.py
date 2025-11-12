from src.graph.states.state import State


def pro_mode(state: State):
    """Handles complex questions using the pro-mode researcher system"""

    # result = llm.invoke(state["input"])
    return {"output": f"Pro-mode!"}
