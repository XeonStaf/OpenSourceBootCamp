from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.router.schemas.route import Route
from src.graph.states.state import State
from src.models.llm import llm

router = llm.with_structured_output(Route)


async def llm_call_router(state: State):
    """
    Routes the user input to either pro-mode or simple-mode based on complexity.

    Args:
        state: The current state object containing user input and conversation context.

    Returns:
        dict: A dictionary containing the routing decision with key 'decision' and value
            being either 'pro' or 'simple'.
    """

    decision = await router.ainvoke(
        [
            SystemMessage(
                content="""You are a routing classifier that determines the complexity of user questions.

                **Routing Guidelines:**

                **PRO-MODE** (Researcher Mode) - Use for:
                - Complex analytical questions requiring multi-step reasoning
                - Questions involving comparisons, calculations, or data analysis
                - Queries that need information synthesis from multiple sources
                - Research-oriented or in-depth investigation questions

                **SIMPLE-MODE** (Knowledge QA) - Use for:
                - Straightforward factual questions with single answers
                - Direct lookups of specific information
                - Definitions, simple facts, or basic knowledge queries
                - Questions answerable with a single piece of information

                **Output Format:** Respond with ONLY "pro" or "simple" - no additional text."""
            ),
            HumanMessage(content=state["input"]),
        ]
    )
    print(f"Decision: {decision}")
    return {"decision": decision.step}


def route_decision(state: State) -> str:
    """
    Determines the next node based on the routing decision.

    This function examines the routing decision made by llm_call_router and returns
    the appropriate node identifier for the graph to route to.

    Args:
        state: The current state object containing the routing decision.
            Expected to have a 'decision' key with value 'pro' or 'simple'.

    Returns:
        The node identifier to route to - either 'pro' or 'simple'.
    """
    if state["decision"] == "pro":
        return "pro"
    elif state["decision"] == "simple":
        return "simple"
