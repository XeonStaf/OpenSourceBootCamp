from langgraph.prebuilt import create_react_agent
from langchain_core.messages  import SystemMessage, HumanMessage

from src.graph.states.state import State
from src.models.llm import llm
from src.graph.validator.schemas.validate import Validate


def define_validating_agent(state: State):
    '''
    Defines valiting agent to validate multi-agent system's response.

    Args: 
        state: State - the current state object containing user input and conversation context.

    Returns:
        A dictionary with key 'answer' with infomation about MAS answer: was the user's question answered or not.
    '''
    validator = llm.with_structured_output(Validate)

    answer = validator.invoke(
        [
            SystemMessage(
                content="""You are a very attentive agent. Your aims is to validate your collegues response.
                You will also perceive initial user's response. Compare initial user's response and your collegues response
                to it. Return was the user's question answered or not. If question was answered - return only 'yes',
                    else - return only 'no'. Return only one word. Think!"""
            ),
            HumanMessage(content=state["input"]),
        ]
    )
    return {"answer": answer.step}


def validator_answer(state: State) -> str:
    '''
    Defines was the response relevant to user's query or not.

    Args: 
        state: State - the current state object containing user input and conversation context.

    Returns:
        String with valirdator's answer: either 'yes' or 'no'.
    '''
    if state["answer"] == "yes":
        return "yes"
    elif state["answer"] == "no":
        return "no"
