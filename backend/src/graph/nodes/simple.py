import logging

from langchain_core.messages import HumanMessage

from src.graph.states.state import State
from src.searches.simple.llm_with_search import llm_with_search
from src.utils.token_callback import TokenUsageCallback

logger = logging.getLogger(__name__)


async def simple_mode(state: State):
    """Handles simple questions using the straightforward knowledge QA system"""
    query_preview = state["input"][:100] + ("..." if len(state["input"]) > 100 else "")
    logger.info(f"[SIMPLE] Processing query: {query_preview}")
    
    callback = TokenUsageCallback()
    result = await llm_with_search.ainvoke(
        {"messages": [HumanMessage(content=state["input"])]},
        config={"callbacks": [callback]}
    )
    
    token_usage = callback.get_token_usage()
    raw_response = type("Response", (), {"response_metadata": {"token_usage": token_usage}})()
    
    output = result["messages"][-1].content
    logger.info(f"[SIMPLE] Answer generated. Length: {len(output)} chars")
    return {"output": output, "_raw_response": raw_response}
