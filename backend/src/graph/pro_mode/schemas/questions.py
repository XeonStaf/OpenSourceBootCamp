from typing import List

from pydantic import BaseModel, Field


class SubQuestion(BaseModel):
    text: str = Field(
        ...,
        description="A focused subquery that helps answer the main question",
    )


class QuestionBreakdown(BaseModel):
    reasoning: str = Field(
        ...,
        description="The logical process for decomposing the main question into subquestions",
    )
    total_subquestions: int = Field(
        ...,
        description="The number of subquestions generated",
    )
    subquestions: List[SubQuestion] = Field(
        ...,
        description="List of sequential, focused subquestions whose answers will solve the main question",
    )
