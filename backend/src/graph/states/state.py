from typing import TypedDict


class State(TypedDict):
    input: str
    decision: str
    output: str
    validation_attempts: int = 0
    validation_result: str
