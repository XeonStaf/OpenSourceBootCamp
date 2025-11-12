from src.graph.states.state import State


def simple_mode(state: State):
    """Handles simple questions using the straightforward knowledge QA system"""

    # result = llm.invoke(state["input"])
    return {"output": f"Simple-mode!"}
