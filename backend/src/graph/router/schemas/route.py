from pydantic import BaseModel, Field
from typing_extensions import Literal


class Route(BaseModel):
    reasoning: str = Field(
        ...,
        description="Brief explanation of why this routing decision was made based on question complexity analysis",
    )
    step: Literal["pro", "simple"] = Field(
        ...,
        description="""Routing decision for processing the user's question:
        **PRO MODE** (Researcher):
        - Complex questions requiring multi-step reasoning
        - Analytical queries with comparisons or calculations
        - Research questions needing information synthesis
        - Multi-faceted problems requiring decomposition

        **SIMPLE MODE** (Direct QA):
        - Straightforward factual questions
        - Single-answer knowledge queries
        - Direct information lookups
        - Simple definitions or facts""",
    )
