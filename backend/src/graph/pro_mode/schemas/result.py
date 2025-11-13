from typing import List

from pydantic import BaseModel, Field


class SubQueryAnswer(BaseModel):
    answer: str = Field(None, description="""Answer for each short subquery""")


class Result(BaseModel):
    answers: List[SubQueryAnswer] = Field(
        None,
        description="""List with all answers for each subquery""",
    )
    full_answer: str = Field(
        None,
        description="""Provide a complete full answer to the user's question""",
    )
