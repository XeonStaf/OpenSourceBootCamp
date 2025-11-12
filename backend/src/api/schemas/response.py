from typing import Literal

from pydantic import BaseModel


class Mode(BaseModel):
    """Pydantic model for system mode output.

    Attributes:
        mode: the system mode to use for answering the user's question (pro or simple)
    """

    mode: Literal["pro", "simple"]
