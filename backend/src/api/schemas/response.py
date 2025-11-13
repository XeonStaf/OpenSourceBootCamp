from typing import Literal

from pydantic import BaseModel


class Mode(BaseModel):
    """Pydantic model for system mode output.

    Attributes:
        mode: the system mode to use for answering the user's question (pro or simple)
    """

    mode: Literal["pro", "simple"]


class Answer(BaseModel):
    """Pydantic model for answer.

    Attributes:
        answer: answer for user's question
        router: the system mode to use for answering the user's question (pro or simple)
    """

    answer: str
    router: Literal["pro", "simple"]
