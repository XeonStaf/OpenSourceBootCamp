import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.pro_mode.schemas.result import Result
from src.graph.states.state import State
from src.models.llm import llm
from src.utils.token_callback import TokenUsageCallback

logger = logging.getLogger(__name__)

llm_aggregator = llm.with_structured_output(Result)


async def aggregator(state: State):
    facts_count = sum(len(facts.facts) for facts in state["facts"])
    logger.info(f"[AGGREGATOR] Starting aggregation: {len(state['sub_queries'])} subqueries, {facts_count} total facts")
    
    messages = [
        SystemMessage(
            content="""You are an expert research analyst tasked with synthesizing information from multiple sources.

        **YOUR ROLE:**
        - Carefully analyze all collected facts and subquery answers
        - Synthesize information to provide a comprehensive, accurate final answer
        - Ensure your response directly addresses the user's original question
        - Maintain factual accuracy and logical coherence

        **PROCESSING INSTRUCTIONS:**
        1. Review each subquery and its corresponding facts
        2. Synthesize the information to form a complete understanding
        3. Construct a well-structured, comprehensive answer
        4. Ensure all relevant facts are incorporated appropriately
        5. Provide clear reasoning based on the evidence collected

        **OUTPUT REQUIREMENTS:**
        - Answer must be based exclusively on the provided facts
        - Include relevant details and contextual information
        - Present information in a logical, easy-to-follow structure
        - Be thorough yet concise in your final response"""
        ),
        HumanMessage(
            content=f"""**RESEARCH TASK**

        **ORIGINAL QUESTION:**
        {state["input"]}

        **SUBQUERIES TO ANSWER:**
        {chr(10).join([f"• {query.text}" for query in state["sub_queries"]])}

        **COLLECTED FACTS BY SUBQUERY:**
        {'---'.join([
                    f"SUBQUERY {i + 1}: {query.text}{chr(10)}FACTS: {' | '.join([fact.text for fact in facts.facts])}"
                    for i, (query, facts) in enumerate(zip(state["sub_queries"], state["facts"]))
                ])}

        **YOUR TASK:**
        1. Analyze all subqueries and their corresponding facts
        2. Synthesize this information to answer the original question comprehensively
        3. Provide a complete, evidence-based final answer"""
        ),
    ]
    
    callback = TokenUsageCallback()
    answer = await llm_aggregator.ainvoke(messages, config={"callbacks": [callback]})
    
    token_usage = callback.get_token_usage()
    raw_response = type("Response", (), {"response_metadata": {"token_usage": token_usage}})()

    logger.info(f"[AGGREGATOR] Aggregation completed. Answer length: {len(answer.full_answer)} chars")
    return {"output": answer.full_answer, "_raw_response": raw_response}
