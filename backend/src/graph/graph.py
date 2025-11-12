from langgraph.graph import END, START, StateGraph

from src.graph.nodes.pro import pro_mode
from src.graph.nodes.simple import simple_mode
from src.graph.router.router import llm_call_router, route_decision
from src.graph.states.state import State

router_builder = StateGraph(State)

router_builder.add_node("pro", pro_mode)
router_builder.add_node("simple", simple_mode)
router_builder.add_node("llm_call_router", llm_call_router)

router_builder.add_edge(START, "llm_call_router")
router_builder.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {"pro": "pro", "simple": "simple"},
)
router_builder.add_edge("pro", END)
router_builder.add_edge("simple", END)

router_workflow = router_builder.compile()
