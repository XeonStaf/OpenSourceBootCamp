from langchain_core.messages import HumanMessage

from src.graph.states.state import State
from src.searches.simple.llm_with_search import llm_with_search


def simple_mode(state: State):
    """Handles simple questions using the straightforward knowledge QA system"""

    result = llm_with_search.invoke({"messages": [HumanMessage(content=state["input"])]})

    return {"output": result["messages"][-1].content}
