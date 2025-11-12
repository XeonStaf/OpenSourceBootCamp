from pydantic import BaseModel


class Query(BaseModel):
    """Base pydantic model for input query.

    Attributes:
        query: user's query
    """

    query: str
