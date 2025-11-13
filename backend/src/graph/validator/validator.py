from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from src.graph.states.state import State
from src.graph.validator.schemas.validate import Validate
from src.models.llm import llm


def define_validating_agent(state: State):
    """
    Defines valiting agent to validate multi-agent system's response.

    Args:
        state: State - the current state object containing user input and conversation context.

    Returns:
        A dictionary with key 'answer' with infomation about MAS answer: was the user's question answered or not.
    """
    validator = llm.with_structured_output(Validate)

    answer = validator.invoke(
        [
            SystemMessage(
                content="""You are a very attentive validation agent. Your aim is to validate your collegues response.
                You will also perceive initial user's query. Compare initial user's query and your collegues response
                to it. Return was the user's question answered or not. If question was answered - return only 'yes',
                    else - return only 'no'. Return only one word. Think!"""
            ),
            HumanMessage(content=state["input"]),
            AIMessage(content=state["output"]),
        ]
    )
    return {"validation_result": answer.step}


def validator_answer(state: State) -> str:
    """
    Defines was the response relevant to user's query or not.

    Args:
        state: State - the current state object containing user input and conversation context.

    Returns:
        String with valirdator's answer: either 'yes' or 'no'.
    """
    if state["validation_result"] == "yes":
        return "yes"
    elif state["validation_result"] == "no":
        return "no"
