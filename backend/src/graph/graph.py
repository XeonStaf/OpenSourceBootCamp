from langgraph.graph import END, START, StateGraph

from src.graph.nodes.pro import pro_mode
from src.graph.nodes.simple import simple_mode
from src.graph.router.router import llm_call_router, route_decision
from src.graph.states.state import State
from src.graph.validator.validator import define_validating_agent, validator_answer


def validation_router(state: State):
    # Check number of attempt in state
    if not hasattr(state, "validation_attempts"):
        state["validation_attempts"] = 0

    result = validator_answer(state)
    state["validation_attempts"] += 1

    if state["validation_attempts"] >= 3:
        return "max_attempts_reached"

    if result == "yes":
        return "yes"
    elif result == "no" and state["validation_attempts"] < 3:
        return "retry"


router_builder = StateGraph(State)

router_builder.add_node("pro", pro_mode)
router_builder.add_node("simple", simple_mode)
router_builder.add_node("llm_call_router", llm_call_router)
router_builder.add_node("validator", define_validating_agent)

router_builder.add_edge(START, "llm_call_router")
router_builder.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {"pro": "pro", "simple": "simple"},
)
router_builder.add_edge("pro", "validator")
router_builder.add_edge("simple", "validator")

router_builder.add_conditional_edges(
    "validator",
    validation_router,
    {
        "yes": END,  # End the cycle if user's question was answered
        "retry": "llm_call_router",  # Go back to router, if MAS' response was unsafficient and max_attempts < 3
        "max_attempts_reached": END,  # End if max_attempts > 3
    },
)

router_workflow = router_builder.compile()
