from pydantic import BaseModel, Field
from typing_extensions import Literal


class Route(BaseModel):
    step: Literal["pro", "simple"] = Field(
        None,
        description="""The system mode to use for answering the user's question:
        - pro (researcher)
        - simple (just search with llm)""",
    )
