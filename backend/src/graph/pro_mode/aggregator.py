from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.pro_mode.schemas.result import Result
from src.graph.states.state import State
from src.models.llm import llm

llm_aggregator = llm.with_structured_output(Result)


def aggregator(state: State):
    answer = llm_aggregator.invoke(
        [
            SystemMessage(
                content=f"""You are a helpful assistant!
                Your helpers collected a set of questions and facts about user's question.
                Your task is to answer each subquery and then answer the main question!
                Please, be patient and careful.
                """
            ),
            HumanMessage(
                content=f"""The subqueries (small questions):
                {'---'.join([query.text for query in state["sub_queries"]])}
                The collected facts:
                {'==='.join(['+++'.join([fact.text for fact in facts.facts]) for facts in state["facts"]])}

                User's main question:
                {state["input"]}
                """
            ),
        ]
    )
    print(answer)
    return {"output": answer.full_answer}
