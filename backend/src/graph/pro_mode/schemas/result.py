from typing import List

from pydantic import BaseModel, Field


class SubQueryAnswer(BaseModel):
    answer: str = Field(
        ...,
        description="""Comprehensive answer to an individual subquery, incorporating all relevant facts \
        and providing complete context for that specific aspect of the main question.""",
    )


class Result(BaseModel):
    answers: List[SubQueryAnswer] = Field(
        ...,
        description="""Complete set of answers for each subquery, serving as the foundational evidence \
        and building blocks for the final comprehensive response. Each answer should stand on its own \
        while contributing to the overall understanding.""",
    )
    full_answer: str = Field(
        ...,
        description="""Comprehensive response to the user's original question that integrates \
        all subquery answers into a coherent, well-structured final answer. Should directly address the \
        main question.""",
    )
