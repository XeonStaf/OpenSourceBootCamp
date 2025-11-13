from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.pro_mode.llm_decomposer import llm_decomposer
from src.graph.states.state import State


def decomposer(state: State):
    """Handles complex questions using the pro-mode researcher system"""
    result = llm_decomposer.invoke(
        [
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
    )
    print(f"reasoning: {result.reasoning}")
    print(f"total_subquestions: {result.total_subquestions}")
    print(f"subquestions: {result.subquestions}")

    return {"sub_queries": result.subquestions}
