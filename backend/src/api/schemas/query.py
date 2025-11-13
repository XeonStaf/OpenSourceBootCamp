from typing import Literal

from pydantic import BaseModel


class Query(BaseModel):
    """Base pydantic model for input query.

    Attributes:
        query: user's query
    """

    query: str


class ModeQuery(BaseModel):
    """Request schema for mode selection with optional manual override."""

    query: str
    mode: Literal["pro", "simple"] | None = None
