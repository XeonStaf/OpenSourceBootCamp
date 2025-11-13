from typing import List, TypedDict

from src.graph.pro_mode.schemas.facts import Facts
from src.graph.pro_mode.schemas.questions import SubQuestion


class State(TypedDict):
    input: str
    decision: str
    output: str
    validation_attempts: int = 0
    validation_result: str
    sub_queries: List[SubQuestion]
    facts: List[Facts]
