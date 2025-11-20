import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.pro_mode.llm_decomposer import llm_decomposer
from src.graph.states.state import State
from src.utils.token_callback import TokenUsageCallback

logger = logging.getLogger(__name__)


async def decomposer(state: State):
    """Handles complex questions using the pro-mode researcher system"""
    query_preview = state["input"][:100] + ("..." if len(state["input"]) > 100 else "")
    logger.info(f"[DECOMPOSER] Starting decomposition for query: {query_preview}")
    
    messages = [
        SystemMessage(
            content="""Role: You are an expert in logical decomposition and information retrieval.
                Your task is to break down complex questions into a series of simpler, sequential sub-questions.

Principles for Decomposition:
1. Identify the Core Goal: Start by understanding the final, specific piece of information the question is asking for.
2. Work Backwards: Determine the fundamental facts needed to calculate or arrive at that final answer. Treat it like a math word problem or a logic puzzle.
3. Sequential Dependency: Order the sub-questions so that the answer to one may be needed to understand or find the next. They should form a logical chain.
4. Atomicity: Each sub-question should target a single, atomic fact. Avoid combining multiple unrelated queries into one.
5. Neutral Framing: Phrase sub-questions neutrally without presuming the answer. Do not include calculations (e.g., don't write "subtract X from Y").
6. Maintain Context: Use the same terminology, timeframes, and entities as the original question to preserve context."""
        ),
        HumanMessage(content=state["input"]),
    ]
    
    callback = TokenUsageCallback()
    result = await llm_decomposer.ainvoke(messages, config={"callbacks": [callback]})
    
    token_usage = callback.get_token_usage()
    raw_response = type("Response", (), {"response_metadata": {"token_usage": token_usage}})()
    
    logger.info(f"[DECOMPOSER] Decomposition completed: {result.total_subquestions} subquestions generated")
    logger.debug(f"[DECOMPOSER] Reasoning: {result.reasoning}")
    for i, subq in enumerate(result.subquestions, 1):
        logger.debug(f"[DECOMPOSER] Subquestion {i}: {subq.text}")

    return {
        "sub_queries": result.subquestions,
        "decomposition_info": {
            "reasoning": result.reasoning,
            "total_subquestions": result.total_subquestions,
            "subquestions": result.subquestions,
        },
        "_raw_response": raw_response,
    }
